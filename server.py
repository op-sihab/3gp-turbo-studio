import os
import sys
import json
import time
import uuid
import shutil
import threading
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import webbrowser

import converter_core

PORT = 5000
BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
WEB_DIR.mkdir(exist_ok=True)

# In-memory job store
JOBS = {}
JOBS_LOCK = threading.Lock()

def format_size(bytes_num):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"

def run_conversion_job(job_id, input_path, preset_key, custom_options, original_name):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job["status"] = "converting"
        job["message"] = "Starting conversion..."
        job["progress"] = 2

    def progress_cb(percent, *args):
        msg = args[-1] if args else f"{percent}%"
        speed = args[0] if len(args) >= 3 else ""
        eta = args[1] if len(args) >= 3 else 0
        with JOBS_LOCK:
            if job_id in JOBS:
                JOBS[job_id]["progress"] = percent
                JOBS[job_id]["message"] = msg
                JOBS[job_id]["speed"] = speed
                JOBS[job_id]["eta"] = eta

    try:
        stem = Path(original_name).stem
        safe_stem = "".join(c for c in stem if c.isalnum() or c in (" ", "-", "_")).rstrip()
        if not safe_stem:
            safe_stem = "video"
        
        output_filename = f"{safe_stem}_{preset_key}_{int(time.time())}.3gp"
        output_filepath = str(OUTPUT_DIR / output_filename)

        converter_core.convert_to_3gp(
            input_file=input_path,
            output_file=output_filepath,
            preset_key=preset_key,
            custom_options=custom_options,
            progress_callback=progress_cb
        )

        out_size = os.path.getsize(output_filepath) if os.path.exists(output_filepath) else 0

        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                job["status"] = "completed"
                job["progress"] = 100
                job["message"] = "Conversion successful!"
                job["output_file"] = output_filename
                job["output_size"] = format_size(out_size)
                job["output_size_bytes"] = out_size
                job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                job["status"] = "failed"
                job["progress"] = 0
                job["message"] = f"Failed: {str(e)}"
    finally:
        # Clean up temporary input file if desired
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass

class AppRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Cleaner console logs
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Static index
        if path == "/" or path == "/index.html":
            file_path = WEB_DIR / "index.html"
            self.serve_static_file(file_path, "text/html")
            return
        elif path.startswith("/web/"):
            rel_path = path[len("/web/"):]
            file_path = WEB_DIR / rel_path
            mime = "text/plain"
            if str(file_path).endswith(".css"):
                mime = "text/css"
            elif str(file_path).endswith(".js"):
                mime = "application/javascript"
            elif str(file_path).endswith(".html"):
                mime = "text/html"
            elif str(file_path).endswith(".png"):
                mime = "image/png"
            elif str(file_path).endswith(".svg"):
                mime = "image/svg+xml"
            elif str(file_path).endswith(".ico"):
                mime = "image/x-icon"
            self.serve_static_file(file_path, mime)
            return

        # API: Presets
        if path == "/api/presets":
            self.send_json({
                "presets": converter_core.PRESETS,
                "default": "standard"
            })
            return

        # API: Jobs list
        if path == "/api/jobs":
            with JOBS_LOCK:
                self.send_json(list(JOBS.values()))
            return

        # API: Specific Job
        if path == "/api/job":
            job_id = params.get("id", [""])[0]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
                if job:
                    self.send_json(job)
                else:
                    self.send_json({"error": "Job not found"}, 404)
            return

        # API: List all output files
        if path == "/api/list-outputs":
            files = []
            for p in OUTPUT_DIR.glob("*.3gp"):
                stat = p.stat()
                files.append({
                    "name": p.name,
                    "size": format_size(stat.st_size),
                    "size_bytes": stat.st_size,
                    "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                })
            files.sort(key=lambda x: x["mtime"], reverse=True)
            self.send_json({"files": files})
            return

        # API: Download output file
        if path == "/api/download":
            filename = params.get("file", [""])[0]
            # Prevent directory traversal
            clean_filename = Path(filename).name
            target_path = OUTPUT_DIR / clean_filename

            if not target_path.exists() or not target_path.is_file():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
                return

            self.send_response(200)
            self.send_header("Content-Type", "video/3gpp")
            self.send_header("Content-Disposition", f'attachment; filename="{clean_filename}"')
            self.send_header("Content-Length", str(target_path.stat().st_size))
            self.end_headers()

            with open(target_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # API: Open Output Folder in Windows Explorer
        if path == "/api/open-folder":
            try:
                if os.name == "nt":
                    subprocess.Popen(["explorer.exe", str(OUTPUT_DIR)])
                self.send_json({"success": True, "path": str(OUTPUT_DIR)})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        # API: Upload and convert file
        if path == "/api/upload":
            raw_filename = params.get("filename", ["video.mp4"])[0]
            filename = unquote(raw_filename)
            preset_key = params.get("preset", ["standard"])[0]
            scale_mode = params.get("scale", ["pad"])[0]
            try:
                vol_boost = float(params.get("volume", ["1.2"])[0])
            except ValueError:
                vol_boost = 1.2

            content_len = int(self.headers.get("Content-Length", 0))
            if content_len == 0:
                self.send_json({"error": "Empty upload body"}, 400)
                return

            job_id = str(uuid.uuid4())[:8]
            safe_filename = Path(filename).name
            temp_input_path = str(INPUT_DIR / f"upload_{job_id}_{safe_filename}")

            # Stream incoming bytes to disk in 64KB chunks
            try:
                bytes_left = content_len
                chunk_size = 64 * 1024
                with open(temp_input_path, "wb") as f:
                    while bytes_left > 0:
                        read_bytes = min(bytes_left, chunk_size)
                        buf = self.rfile.read(read_bytes)
                        if not buf:
                            break
                        f.write(buf)
                        bytes_left -= len(buf)
            except Exception as e:
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                self.send_json({"error": f"Upload read failed: {str(e)}"}, 500)
                return

            original_size = os.path.getsize(temp_input_path)

            custom_options = {
                "volume_boost": vol_boost,
                "scale_mode": scale_mode
            }

            job_info = {
                "id": job_id,
                "filename": safe_filename,
                "original_size": format_size(original_size),
                "original_size_bytes": original_size,
                "preset": preset_key,
                "preset_name": converter_core.PRESETS.get(preset_key, {}).get("name", preset_key),
                "status": "queued",
                "progress": 0,
                "message": "Waiting in queue...",
                "output_file": None,
                "output_size": None,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with JOBS_LOCK:
                JOBS[job_id] = job_info

            # Start background conversion thread
            worker = threading.Thread(
                target=run_conversion_job,
                args=(job_id, temp_input_path, preset_key, custom_options, safe_filename),
                daemon=True
            )
            worker.start()

            self.send_json({
                "success": True,
                "job_id": job_id,
                "job": job_info
            })
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/api/delete-output":
            filename = params.get("file", [""])[0]
            clean_filename = Path(filename).name
            target = OUTPUT_DIR / clean_filename
            if target.exists() and target.is_file():
                try:
                    os.remove(target)
                    self.send_json({"success": True})
                    return
                except Exception as e:
                    self.send_json({"error": str(e)}, 500)
                    return
            self.send_json({"error": "File not found"}, 404)
            return

        self.send_response(404)
        self.end_headers()

    def serve_static_file(self, file_path, content_type):
        if not file_path.exists() or not file_path.is_file():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File Not Found")
            return

        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(file_path.stat().st_size))
        self.end_headers()
        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)

def start_server(port=PORT, auto_open=True):
    # Verify ffmpeg upfront
    try:
        ffmpeg_path = converter_core.find_ffmpeg()
        print(f"[✓] Using FFmpeg: {ffmpeg_path}")
    except Exception as e:
        print(f"[!] Warning: {e}")

    server_address = ("", port)
    try:
        httpd = HTTPServer(server_address, AppRequestHandler)
    except OSError:
        # If port 5000 is occupied, try 5050 or next
        port = 5050
        server_address = ("", port)
        httpd = HTTPServer(server_address, AppRequestHandler)

    url = f"http://localhost:{port}"
    print("=" * 65)
    print("   📱 3GP BUTTON PHONE VIDEO CONVERTER SERVER RUNNING")
    print(f"   🌐 Open in Browser: {url}")
    print("   📁 Output folder: D:\\3gp\\output")
    print("   🛑 Press CTRL+C to stop the server")
    print("=" * 65)

    if auto_open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    start_server()

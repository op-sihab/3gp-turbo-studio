import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
BIN_DIR = BASE_DIR / "bin"
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

import converter_core

# ULTRA-TURBO yt-dlp Format Hierarchy:
# 1. 160+139: 144p H.264 (256x144) + 49k AAC (Smallest file ~48MB/hr, Hardware DXVA2 decode, 100x speed!)
# 2. 133+139: 240p H.264 (426x240) + 49k AAC
# 3. 18: 360p pre-merged H.264 MP4
# 4. Fallback to lowest MP4
YTDLP_FORMAT = "160+139/bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/133+139/18/worst[ext=mp4]/worst"

def download_and_convert(url: str, preset="standard"):
    try:
        import yt_dlp
    except ImportError:
        print("[✗] Error: yt-dlp is not installed. Run: pip install yt-dlp")
        return

    ffmpeg_path = str(BIN_DIR / "ffmpeg.exe") if (BIN_DIR / "ffmpeg.exe").exists() else "ffmpeg"

    print("=" * 65)
    print("   ⚡ ULTRA-TURBO YOUTUBE TO 3GP CONVERTER")
    print(f"   URL: {url}")
    print(f"   Target: 144p H.264 Source (Minimum Download, Max DXVA2 Speed)")
    print("=" * 65)

    downloaded_files = []

    def ytdlp_hook(d):
        if d['status'] == 'downloading':
            pct = d.get('_percent_str', '').strip()
            speed = d.get('_speed_str', '').strip()
            eta = d.get('_eta_str', '').strip()
            sys.stdout.write(f"\r    [Downloading] {pct} | Speed: {speed} | ETA: {eta}   ")
            sys.stdout.flush()
        elif d['status'] == 'finished':
            downloaded_files.append(d['filename'])
            print(f"\n[✓] Download finished: {Path(d['filename']).name}")

    ydl_opts = {
        'format': YTDLP_FORMAT,
        'outtmpl': str(INPUT_DIR / '%(title).40s [%(id)s].%(ext)s'),
        'ffmpeg_location': ffmpeg_path,
        'progress_hooks': [ytdlp_hook],
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True
    }

    t_total_start = time.time()
    print("[*] Fetching stream with yt-dlp...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        final_filename = ydl.prepare_filename(info)
        downloaded_files.append(final_filename)

    dl_time = time.time() - t_total_start
    print(f"[✓] Download & Merge took: {dl_time:.1f}s")

    for fpath in downloaded_files:
        if not os.path.exists(fpath):
            continue
        stem = Path(fpath).stem
        out_file = str(OUTPUT_DIR / f"{stem}_turbo.3gp")
        hisss_out = Path(r"D:\hisss\converted_3gp") / f"{stem}_turbo.3gp"

        info = converter_core.get_video_info(ffmpeg_path, fpath)
        dur_str = time.strftime('%H:%M:%S', time.gmtime(info['duration']))

        print("\n" + "-" * 65)
        print(f"[*] STARTING TURBO CONVERSION: {Path(fpath).name}")
        print(f"    Video Length: {dur_str} ({info['duration']:.0f} seconds)")
        print(f"    Source Format: {info['codec'].upper()} {info['width']}x{info['height']}")
        print(f"    Optimizations: DXVA2 GPU Decode + fps=15 First + 4-Thread MPEG-4 + bf=0")
        print("-" * 65)

        c_start = time.time()
        converter_core.convert_to_3gp(
            input_file=fpath,
            output_file=out_file,
            preset_key=preset,
            progress_callback=lambda pct, spd, eta, msg: sys.stdout.write(f"\r    --> {pct:3d}% | {spd} | ETA: {eta}s   ")
        )
        sys.stdout.write("\n")
        c_time = time.time() - c_start

        out_mb = os.path.getsize(out_file) / (1024 * 1024)
        avg_speed = info['duration'] / c_time if c_time > 0 else 0

        print(f"\n[✓] CONVERSION COMPLETED IN ONLY {c_time:.1f} SECONDS! ({c_time/60:.2f} minutes)")
        print(f"    Average Conversion Speed: {avg_speed:.1f}x real-time!")
        print(f"    Output 3GP Size: {out_mb:.2f} MB")
        print(f"    Saved: {out_file}")

        # Also copy to hisss folder if it exists
        if Path(r"D:\hisss\converted_3gp").exists():
            try:
                import shutil
                shutil.copy2(out_file, hisss_out)
                print(f"    Copied to: {hisss_out}")
            except Exception:
                pass

    total_elapsed = time.time() - t_total_start
    print("\n" + "=" * 65)
    print(f"⚡ COMPLETE PROCESS (DOWNLOAD + CONVERT) TOOK {total_elapsed:.1f}s TOTAL!")
    print("=" * 65)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ytdlp_download.py <YouTube_URL>")
        sys.exit(1)
    target_url = sys.argv[1]
    download_and_convert(target_url)

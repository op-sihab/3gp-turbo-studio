import os
import sys
import re
import time
import subprocess
import shutil
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
HISSS_DIR = Path(r"D:\hisss\converted_3gp")

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
if Path(r"D:\hisss").exists():
    HISSS_DIR.mkdir(exist_ok=True)

import converter_core

# Ultra-Fast yt-dlp Format Hierarchy
# 144p H.264 (256x144) + 49k AAC -> only ~40-50MB per hour, 90x-118x conversion speed!
YTDLP_FORMAT = "160+139/bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/133+139/18/worst[ext=mp4]/worst"

def extract_urls(text: str) -> list:
    """Extracts all valid YouTube URLs from input text, arguments, or files."""
    urls = []
    # Check if text is a file path
    if os.path.isfile(text.strip()):
        try:
            with open(text.strip(), "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                return extract_urls(content)
        except Exception:
            pass

    # Regex for standard and short YouTube links
    pattern = re.compile(
        r'(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)[a-zA-Z0-9_\-]+[^\s,]*)',
        re.IGNORECASE
    )
    for match in pattern.finditer(text):
        clean_url = match.group(1).rstrip(".,;")
        if clean_url not in urls:
            urls.append(clean_url)

    # Also handle bare 11-char YouTube IDs
    if not urls:
        id_pattern = re.compile(r'^[a-zA-Z0-9_\-]{11}$')
        for token in text.replace(",", " ").split():
            token = token.strip()
            if id_pattern.match(token):
                urls.append(f"https://youtu.be/{token}")

    return urls

def process_single_video(url: str, ffmpeg_path: str, keep_source=False) -> dict:
    import yt_dlp

    ydl_opts = {
        'format': YTDLP_FORMAT,
        'outtmpl': str(INPUT_DIR / '%(title).40s [%(id)s].%(ext)s'),
        'ffmpeg_location': ffmpeg_path,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
    }

    print(f"\n[*] 📥 Downloading stream from YouTube...")
    t_start = time.time()
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        final_mp4 = ydl.prepare_filename(info)
        title = info.get('title', Path(final_mp4).stem)
        duration = info.get('duration', 0)

    dl_time = time.time() - t_start
    dl_size_mb = os.path.getsize(final_mp4) / (1024 * 1024) if os.path.exists(final_mp4) else 0
    print(f"[✓] Download complete in {dl_time:.1f}s ({dl_size_mb:.1f} MB)")

    # Output paths
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_", "[", "]")).strip()
    if not safe_title:
        safe_title = Path(final_mp4).stem
    
    out_3gp = str(OUTPUT_DIR / f"{safe_title}.3gp")
    hisss_out = HISSS_DIR / f"{safe_title}.3gp"

    dur_str = time.strftime('%H:%M:%S', time.gmtime(duration))
    print(f"[*] ⚡ Starting Turbo 3GP Conversion...")
    print(f"    Length: {dur_str} | Target: 176x144 QCIF | MPEG-4 SP 15fps | AMR-NB 8k")

    c_start = time.time()
    converter_core.convert_to_3gp(
        input_file=final_mp4,
        output_file=out_3gp,
        preset_key="standard",
        progress_callback=lambda pct, spd, eta, msg: sys.stdout.write(f"\r    --> [{pct:3d}%] | {spd:7s} | ETA: {eta}s   ")
    )
    sys.stdout.write("\n")
    c_time = time.time() - c_start

    out_size_mb = os.path.getsize(out_3gp) / (1024 * 1024) if os.path.exists(out_3gp) else 0
    avg_speed = duration / c_time if (c_time > 0 and duration > 0) else 0

    print(f"[✓] Converted in {c_time:.1f}s (Speed: {avg_speed:.1f}x)!")
    print(f"[✓] Final 3GP Size: {out_size_mb:.2f} MB")
    print(f"[✓] Saved: {out_3gp}")

    # Copy to D:\hisss\converted_3gp if that directory exists
    if HISSS_DIR.exists():
        try:
            shutil.copy2(out_3gp, str(hisss_out))
            print(f"[✓] Also copied to: {hisss_out}")
        except Exception:
            pass

    # Clean up intermediate raw downloaded MP4 to save disk space
    if not keep_source and os.path.exists(final_mp4):
        try:
            os.remove(final_mp4)
        except Exception:
            pass

    return {
        "title": title,
        "duration": dur_str,
        "dl_time": dl_time,
        "convert_time": c_time,
        "total_time": dl_time + c_time,
        "speed": avg_speed,
        "size_mb": out_size_mb,
        "output_file": out_3gp
    }

def main():
    print("=" * 68)
    print("   ⚡ TURBO YOUTUBE TO 3GP CONVERTER (For Button Phones)")
    print("      Intel Core i3 / HD 4400 Optimized | 90x-118x Speed")
    print("=" * 68)

    ffmpeg_bin = converter_core.find_ffmpeg()

    # Collect URLs from args or interactive prompt
    raw_input_text = ""
    if len(sys.argv) > 1:
        raw_input_text = " ".join(sys.argv[1:])
    else:
        print("\nPaste YouTube link(s) below.")
        print("(One link, multiple links separated by spaces/commas, or multiple lines).")
        print("Type/paste and press ENTER (leave blank and press Enter when done):\n")
        lines = []
        while True:
            try:
                line = input()
                if not line.strip() and lines:
                    break
                if not line.strip() and not lines:
                    continue
                lines.append(line)
                # If a single line contains URLs, break immediately
                if extract_urls(line):
                    break
            except (EOFError, KeyboardInterrupt):
                break
        raw_input_text = "\n".join(lines)

    urls = extract_urls(raw_input_text)

    if not urls:
        print("\n[!] No valid YouTube links found. Example: https://youtu.be/O7LgZeWLR-A")
        input("\nPress ENTER to exit...")
        sys.exit(1)

    print(f"\n[✓] Found {len(urls)} video link(s) to process:")
    for idx, u in enumerate(urls, 1):
        print(f"    {idx}. {u}")
    print("-" * 68)

    results = []
    overall_start = time.time()

    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] Processing Video: {url}")
        try:
            res = process_single_video(url, ffmpeg_bin)
            results.append(res)
        except Exception as e:
            print(f"[✗] Error processing {url}: {e}")

    overall_time = time.time() - overall_start

    # Summary
    print("\n" + "=" * 68)
    print("   🎉 ALL VIDEOS FINISHED!")
    print("=" * 68)
    for r in results:
        print(f"   • {r['title'][:30]:30s} | {r['duration']} | Conv: {r['convert_time']:.1f}s ({r['speed']:.0f}x) | Size: {r['size_mb']:.2f} MB")
    print("-" * 68)
    print(f"   Total Elapsed Time: {overall_time:.1f}s ({overall_time/60:.2f} minutes)")
    print(f"   Saved in Output Folder: {OUTPUT_DIR}")
    print("=" * 68)

    # Automatically open output folder in Windows Explorer
    if os.name == "nt":
        try:
            subprocess.Popen(["explorer.exe", str(OUTPUT_DIR)])
        except Exception:
            pass

    print("\n[✓] Output folder opened. You can now copy the files to your SD card!")
    if len(sys.argv) <= 1:
        input("\nPress ENTER to finish...")

if __name__ == "__main__":
    main()

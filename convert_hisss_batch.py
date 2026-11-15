import os
import sys
import time
from pathlib import Path
import converter_core

INPUT_DIR = Path(r"D:\hisss")
OUTPUT_DIR = Path(r"D:\hisss\converted_3gp")
WEB_OUTPUT_DIR = Path(r"D:\3gp\output")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WEB_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def print_progress(percent: float, speed: str, eta_sec: int, message: str):
    bar_length = 24
    filled = int(bar_length * percent // 100)
    bar = "=" * filled + "-" * (bar_length - filled)
    eta_str = f"ETA: {eta_sec}s" if eta_sec > 0 else "Finishing..."
    speed_disp = f"Speed: {speed:6s}" if speed else ""
    sys.stdout.write(f"\r    [{bar}] {percent:3d}% | {speed_disp} | {eta_str}   ")
    sys.stdout.flush()
    if percent >= 100:
        sys.stdout.write("\n")

def main():
    files = sorted(list(INPUT_DIR.glob("*.mp4")), key=lambda f: f.stat().st_size)
    print("=" * 65)
    print("   ⚡ SANEE S1123 LITE TURBO 3GP BATCH CONVERTER")
    print("      Intel Core i3-4170 (4-Threads) | MPEG-4 SP | fps=15 First")
    print(f"      Found {len(files)} video(s) in {INPUT_DIR}")
    print("=" * 65)

    total_start = time.time()
    results = []

    for i, f in enumerate(files, 1):
        stem = f.stem
        out_path = str(OUTPUT_DIR / f"{stem}_turbo.3gp")
        web_out_path = str(WEB_OUTPUT_DIR / f"{stem}_turbo.3gp")

        info = converter_core.get_video_info(converter_core.find_ffmpeg(), str(f))
        dur_str = time.strftime('%H:%M:%S', time.gmtime(info['duration']))

        print(f"\n[{i}/{len(files)}] Processing: {f.name}")
        print(f"    Duration: {dur_str} | Source Codec: {info['codec'].upper()} {info['width']}x{info['height']}")
        print(f"    Settings: 176x144 | MPEG-4 4-Threads | fps=15 First | AMR-NB 8k | Vol 130%")

        t0 = time.time()
        try:
            converter_core.convert_to_3gp(
                input_file=str(f),
                output_file=out_path,
                preset_key="standard",
                progress_callback=print_progress
            )
            elapsed = time.time() - t0
            out_size_mb = os.path.getsize(out_path) / (1024 * 1024)
            in_size_mb = f.stat().st_size / (1024 * 1024)
            results.append({
                "name": f.name,
                "duration": dur_str,
                "in_mb": in_size_mb,
                "out_mb": out_size_mb,
                "time_sec": elapsed,
                "speed_avg": info['duration'] / elapsed if elapsed > 0 else 0
            })
            print(f"    [✓] Converted in {elapsed:.1f}s (Avg Speed: {info['duration']/elapsed:.1f}x)!")
            print(f"        Original: {in_size_mb:.1f} MB  -->  3GP: {out_size_mb:.2f} MB")

            # Copy to web outputs
            try:
                import shutil
                shutil.copy2(out_path, web_out_path)
            except Exception:
                pass

        except Exception as e:
            print(f"    [✗] Error: {e}")

    total_time = time.time() - total_start
    print("\n" + "=" * 65)
    print("   📊 PERFORMANCE SUMMARY")
    print("=" * 65)
    for r in results:
        print(f"   • {r['name'][:25]:25s} | Dur: {r['duration']} | Time: {r['time_sec']:.1f}s | Speed: {r['speed_avg']:.1f}x | Size: {r['out_mb']:.2f} MB")
    print("-" * 65)
    print(f"   [✓] All videos finished in {total_time:.1f} seconds ({total_time/60:.2f} minutes) total!")
    print(f"   Output folder: {OUTPUT_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    main()

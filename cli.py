import argparse
import sys
import os
import time
from pathlib import Path
import converter_core

def print_progress(percent: float, speed: str, eta_sec: int, message: str):
    bar_length = 26
    filled = int(bar_length * percent // 100)
    bar = "=" * filled + "-" * (bar_length - filled)
    eta_str = f"ETA: {eta_sec}s" if eta_sec > 0 else "Finishing..."
    speed_disp = f"Speed: {speed:6s}" if speed else ""
    sys.stdout.write(f"\r[{bar}] {percent:3d}% | {speed_disp} | {eta_str}   ")
    sys.stdout.flush()
    if percent >= 100:
        sys.stdout.write("\n")

def main():
    parser = argparse.ArgumentParser(
        description="Turbo 3GP Video Converter for Button Phones (Intel Core i3 / HD 4400 Optimized)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input", nargs="?", help="Input video file or directory (when --batch is used)")
    parser.add_argument(
        "-p", "--preset",
        choices=list(converter_core.PRESETS.keys()),
        default="standard",
        help="""Preset target profile:
  standard: Multi-threaded MPEG-4 (4-threads), 176x144 QCIF, 15fps (Default, Ultra-Fast!)
  h263:     Strict Legacy H.263, 176x144 QCIF, 15fps, AMR-NB 8k
  ultralow: 128x96 sub-QCIF, MPEG-4, 12fps, AMR-NB 8k (Nokia 3310, small screens)
  qvga:     320x240 QVGA, MPEG-4, 15fps, AMR-NB 8k (2.4\"+ screens)"""
    )
    parser.add_argument("-o", "--output", help="Output .3gp file path or output directory")
    parser.add_argument("-b", "--batch", action="store_true", help="Batch convert all video files in directory")
    parser.add_argument("-v", "--volume", default="1.3", help="Audio volume multiplier (e.g. 1.3 = 130%%) [Default: 1.3]")
    parser.add_argument("--scale", choices=["neighbor", "pad", "crop"], default="neighbor",
                        help="Scaling mode: neighbor (fastest nearest-neighbor), pad (letterbox), crop")
    
    args = parser.parse_args()

    print("=" * 65)
    print("   ⚡ TURBO 3GP VIDEO CONVERTER (Intel Core i3 Optimized)")
    print("      Windows DXVA2 | 4-Thread MPEG-4 | fps=15 First | AMR-NB")
    print("=" * 65)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    custom_options = {
        "volume": str(args.volume),
        "scale_mode": args.scale
    }

    if args.batch or os.path.isdir(args.input):
        input_dir = Path(args.input)
        exts = ("*.mp4", "*.mkv", "*.avi", "*.mov", "*.webm", "*.flv", "*.wmv")
        files = []
        for ext in exts:
            files.extend(input_dir.glob(ext))
        
        if not files:
            print(f"[!] No video files found in: {input_dir}")
            sys.exit(1)

        print(f"[*] Found {len(files)} video(s) in {input_dir.name}")
        print(f"[*] Preset: {args.preset.upper()} ({converter_core.PRESETS[args.preset]['description']})")
        print("-" * 65)

        success = 0
        total_start = time.time()
        for idx, f in enumerate(files, 1):
            print(f"\n[{idx}/{len(files)}] Processing: {f.name}")
            t_start = time.time()
            try:
                out_path = converter_core.convert_to_3gp(
                    input_file=str(f),
                    preset_key=args.preset,
                    custom_options=custom_options,
                    progress_callback=print_progress
                )
                elapsed = time.time() - t_start
                out_size = os.path.getsize(out_path) / (1024 * 1024)
                print(f"[✓] Saved in {elapsed:.1f}s: {Path(out_path).name} ({out_size:.2f} MB)")
                success += 1
            except Exception as e:
                print(f"\n[✗] Failed: {e}")

        total_elapsed = time.time() - total_start
        print("=" * 65)
        print(f"[✓] Batch conversion complete: {success}/{len(files)} in {total_elapsed:.1f}s total!")
    else:
        input_file = Path(args.input)
        if not input_file.exists():
            print(f"[✗] Error: Input file '{args.input}' does not exist.")
            sys.exit(1)

        print(f"[*] Input: {input_file.name}")
        print(f"[*] Target Profile: {args.preset.upper()}")
        print(f"[*] Scaling Mode: {args.scale} (fps=15 drop first)")
        print(f"[*] Priority: Windows HIGH_PRIORITY_CLASS")
        print("-" * 65)

        start_time = time.time()
        try:
            out_file = converter_core.convert_to_3gp(
                input_file=str(input_file),
                output_file=args.output,
                preset_key=args.preset,
                custom_options=custom_options,
                progress_callback=print_progress
            )
            elapsed = time.time() - start_time
            file_size_kb = os.path.getsize(out_file) / 1024
            print(f"\n[✓] Converted in {elapsed:.1f} seconds! ({file_size_kb:.1f} KB)")
            print(f"[✓] File ready: {out_file}")
        except Exception as e:
            print(f"\n[✗] Conversion error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()

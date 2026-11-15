import os
import sys
import re
import subprocess
import shutil
import time
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / "bin"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Windows process priority flag
HIGH_PRIORITY_FLAG = subprocess.HIGH_PRIORITY_CLASS if os.name == "nt" else 0

def find_ffmpeg() -> str:
    """Finds the best available ffmpeg binary."""
    local_ffmpeg = BIN_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if local_ffmpeg.exists():
        return str(local_ffmpeg)
    
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    
    raise FileNotFoundError(
        "FFmpeg binary not found! Please place ffmpeg.exe in the bin/ directory or install FFmpeg."
    )

def get_video_info(ffmpeg_bin: str, file_path: str) -> dict:
    """Probes input video duration, resolution, and video codec using FFmpeg."""
    info = {"duration": 0.0, "codec": "unknown", "width": 0, "height": 0}
    try:
        cmd = [ffmpeg_bin, "-i", file_path]
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            errors="ignore",
            creationflags=HIGH_PRIORITY_FLAG
        )
        output = result.stderr

        # Duration: 00:01:23.45
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
        if dur_match:
            h, m, s = dur_match.groups()
            info["duration"] = int(h) * 3600 + int(m) * 60 + float(s)

        # Video stream: Stream #0:0: Video: h264 (...), yuv420p, 1280x720 ...
        vid_match = re.search(r"Stream #\d+:\d+.*?: Video:\s*([a-zA-Z0-9_\-]+).*?(\d{2,5})x(\d{2,5})", output)
        if vid_match:
            info["codec"] = vid_match.group(1).lower()
            info["width"] = int(vid_match.group(2))
            info["height"] = int(vid_match.group(3))
    except Exception as e:
        print(f"Warning: could not get video info: {e}")
    return info

# Intel HD Graphics 4400 DXVA2 supported decode codecs
DXVA2_SUPPORTED_CODECS = {"h264", "avc1", "vc1", "mpeg2video", "wmv3", "msmpeg4v3"}

PRESETS = {
    "standard": {
        "name": "Standard Button Phone (Turbo Multi-Threaded MPEG-4)",
        "name_bn": "স্ট্যান্ডার্ড বাটন ফোন (টার্বো ৪-থ্রেড স্পিড)",
        "description": "Multi-threaded MPEG-4 SP, QCIF 176x144, 15fps, AMR-NB 8k 12.2k (Fastest!)",
        "codec_v": "mpeg4",
        "qscale": 12,
        "resolution": "176x144",
        "fps": 15,
        "codec_a": "libopencore_amrnb",
        "sample_rate": 8000,
        "channels": 1,
        "a_bitrate": "12.2k",
        "volume": "1.3",
        "scale_mode": "neighbor",  # neighbor (ultra fast) or pad (letterbox)
    },
    "h263": {
        "name": "Strict Legacy H.263 (Maximum Compatibility)",
        "name_bn": "ক্লাসিক H.263 (সবচেয়ে প্রাচীন ফোনের জন্য)",
        "description": "Single-threaded H.263 baseline, 176x144 QCIF, 15fps, AMR-NB 8k",
        "codec_v": "h263",
        "v_bitrate": "96k",
        "resolution": "176x144",
        "fps": 15,
        "codec_a": "libopencore_amrnb",
        "sample_rate": 8000,
        "channels": 1,
        "a_bitrate": "12.2k",
        "volume": "1.3",
        "scale_mode": "pad",
    },
    "ultralow": {
        "name": "Ultra-Low / Classic 2G (128x96)",
        "name_bn": "আল্ট্রা-লো ২জি (১২৮×৯৬)",
        "description": "MPEG-4 / H.263 sub-QCIF 128x96, 12fps, AMR-NB 8k 10.2k",
        "codec_v": "mpeg4",
        "qscale": 14,
        "mbd": "rd",
        "resolution": "128x96",
        "fps": 12,
        "codec_a": "libopencore_amrnb",
        "sample_rate": 8000,
        "channels": 1,
        "a_bitrate": "10.2k",
        "volume": "1.3",
        "scale_mode": "neighbor",
    },
    "qvga": {
        "name": "HQ Feature Phone (QVGA 320x240)",
        "name_bn": "এইচকিউ বাটন ফোন (৩২০×২৪০)",
        "description": "MPEG-4 QVGA 320x240, 15fps, AMR-NB 8k (2.4\"+ screens)",
        "codec_v": "mpeg4",
        "qscale": 10,
        "mbd": "rd",
        "resolution": "320x240",
        "fps": 15,
        "codec_a": "libopencore_amrnb",
        "sample_rate": 8000,
        "channels": 1,
        "a_bitrate": "12.2k",
        "volume": "1.3",
        "scale_mode": "neighbor",
    }
}

def build_filtergraph(scale_mode: str, width: int, height: int, fps: int) -> str:
    """
    Builds optimized filtergraph:
    STRICT OPTIMIZATION: Drops frames FIRST (fps=15) so scaler processes only 15 fps.
    Uses ultra-fast 'flags=neighbor' for zero-overhead scaling.
    """
    if scale_mode == "pad":
        # Letterbox: fps first, then downscale with neighbor, then pad with black bars
        return (
            f"fps={fps},"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease:flags=neighbor,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
        )
    elif scale_mode == "crop":
        return f"fps={fps},scale={width}:{height}:force_original_aspect_ratio=increase:flags=neighbor,crop={width}:{height}"
    else:
        # Ultra-fast nearest-neighbor direct scaling
        return f"fps={fps},scale={width}:{height}:flags=neighbor"

def convert_to_3gp(
    input_file: str,
    output_file: str = None,
    preset_key: str = "standard",
    custom_options: dict = None,
    progress_callback = None,
    threads: int = 4
) -> str:
    """
    High-performance 3GP Video Converter optimized for Intel Core i3 (2C/4T + HD 4400).
    Applies:
      1. Hardware-accelerated decoding (-hwaccel dxva2 for H.264/MPEG2/VC1).
      2. Frame drop before scaling (fps=15 first in filtergraph).
      3. Ultra-fast nearest neighbor scaler (flags=neighbor).
      4. Multi-threaded MPEG-4 encoder (-c:v mpeg4 -q:v 12 -mbd rd -threads 4).
      5. Windows HIGH_PRIORITY_CLASS CPU scheduling.
    """
    ffmpeg_bin = find_ffmpeg()
    
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Target output file path
    if not output_file:
        stem = Path(input_file).stem
        output_file = str(OUTPUT_DIR / f"{stem}_{preset_key}.3gp")
    
    # Merge preset with custom options
    config = dict(PRESETS.get(preset_key, PRESETS["standard"]))
    if custom_options:
        config.update(custom_options)

    # Probe input for duration & codec to decide hardware acceleration
    info = get_video_info(ffmpeg_bin, input_file)
    total_duration = info["duration"]
    input_codec = info["codec"]

    width, height = map(int, config["resolution"].split("x"))
    scale_mode = config.get("scale_mode", "neighbor")
    fps = config.get("fps", 15)
    vf = build_filtergraph(scale_mode, width, height, fps)
    
    vol = config.get("volume", "1.3")
    af = f"volume={vol},aresample={config['sample_rate']}"

    # Build optimized FFmpeg command line
    cmd = [ffmpeg_bin, "-y"]

    # Strict Optimization: Add -hwaccel dxva2 when input codec is supported by Intel HD 4400
    # (Avoid crashing on AV1/HEVC which Haswell lacks fixed-function silicon for)
    if any(sup in input_codec for sup in DXVA2_SUPPORTED_CODECS):
        cmd.extend(["-hwaccel", "dxva2"])

    # Input decoding threads
    cmd.extend(["-threads", str(threads)])
    cmd.extend(["-i", input_file])

    # Video filter: fps=15 first, then fast scaling
    cmd.extend(["-vf", vf])

    # Video encoding options
    codec_v = config["codec_v"]
    if codec_v == "mpeg4":
        qscale = config.get("qscale", 12)
        cmd.extend([
            "-c:v", "mpeg4",
            "-q:v", str(qscale),
            "-bf", "0",
            "-threads", str(threads)
        ])
        if config.get("mbd"):
            cmd.extend(["-mbd", config["mbd"]])
    else:  # fallback to h263
        v_bitrate = config.get("v_bitrate", "96k")
        cmd.extend([
            "-c:v", "h263",
            "-b:v", v_bitrate,
            "-r", str(fps)
        ])

    # Audio encoding options
    cmd.extend([
        "-af", af,
        "-c:a", config["codec_a"],
        "-ar", str(config["sample_rate"]),
        "-ac", str(config["channels"]),
        "-b:a", config["a_bitrate"]
    ])

    # Container options
    cmd.extend([
        "-f", "3gp",
        "-movflags", "+faststart",
        output_file
    ])

    def notify_progress(pct, spd, eta, msg):
        if progress_callback:
            try:
                progress_callback(pct, spd, eta, msg)
            except TypeError:
                try:
                    progress_callback(pct, msg)
                except Exception:
                    pass

    notify_progress(1, "0x", 0, "Starting turbo conversion...")

    # Spawn FFmpeg child process with HIGH_PRIORITY_CLASS
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="ignore",
        bufsize=1,
        creationflags=HIGH_PRIORITY_FLAG
    )

    time_regex = re.compile(r"time=\s*(\d+):(\d+):(\d+\.?\d*)")
    speed_regex = re.compile(r"speed=\s*(\d+\.?\d*)x")
    
    last_percent = 1
    start_time = time.time()

    while True:
        line = process.stderr.readline()
        if not line and process.poll() is not None:
            break
        if line and total_duration > 0:
            match = time_regex.search(line)
            if match:
                h, m, s = match.groups()
                current_time = int(h) * 3600 + int(m) * 60 + float(s)
                percent = min(99, int((current_time / total_duration) * 100))
                
                s_match = speed_regex.search(line)
                speed_str = (s_match.group(1) + "x") if s_match else ""
                speed_val = float(s_match.group(1)) if (s_match and float(s_match.group(1)) > 0) else 1.0
                eta_sec = int((total_duration - current_time) / speed_val) if speed_val > 0 else 0

                if percent > last_percent:
                    last_percent = percent
                    notify_progress(percent, speed_str, eta_sec, f"Converting: {percent}% ({speed_str})")

    retcode = process.poll()
    if retcode != 0:
        err_msg = process.stderr.read()
        raise RuntimeError(f"FFmpeg failed with code {retcode}: {err_msg}")

    notify_progress(100, "", 0, "Complete!")

    return output_file

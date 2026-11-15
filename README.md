# 📱 3GP Turbo Studio (Button Phone Video Converter)
> **Ultra-Fast MP4 to 3GP Converter & YouTube Downloader specifically tuned for Feature / Button Phones.**
> 
> *Tested and optimized for Sanee S1123 Lite, Symphony, Walton, Itel, Nokia 105/130/150/216/3310, and Samsung Guru series.*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Hardware%20Accelerated-green.svg)](https://ffmpeg.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Speed](https://img.shields.io/badge/Conversion%20Speed-90x--118x-orange.svg)](#-hardware-performance)

---

## ⚡ Highlights

- 📟 **Global Terminal Command:** Type `3gp` in any CMD, PowerShell, or Windows Terminal to instantly open the interactive Retro TUI Studio.
- 🚀 **Extreme Conversion Speed (90x–118x):** Converts a 1-hour video in **under 45–60 seconds** on budget hardware (e.g. Intel Core i3-4170 + Intel HD 4400 iGPU).
- 🎥 **YouTube Turbo Downloader:** Download single links, multiple links, or entire playlists directly to 3GP without downloading bloated 1080p files.
- 💾 **MicroSD Card Auto-Transfer:** Automatically detects your phone's memory card drive and copies converted files directly into its `Videos/` folder.
- 🎛️ **Dual Interfaces:** Rich Retro Terminal UI (TUI) with ASCII banner and a modern Web Browser GUI (`http://localhost:5000`).
- 🔊 **Clear Loud Audio:** Built-in volume boost (`volume=1.3`) and 8000 Hz AMR-NB mono audio so voices are loud and crisp on tiny button phone speakers.

---

## 🔍 বাটন ফোনের ভিডিও স্পেসিফিকেশন ও রিসার্চ (Button Phone Video Specs)

সাধারণ স্মার্টফোনের MP4 ভিডিও বাটন ফোনে চলে না কারণ বাটন ফোনের চিপসেট (MediaTek MT6261, Spreadtrum SC6531, RDA) এবং RAM খুবই সীমিত (৪ MB – ১৬ MB)।

| প্যারামিটার | Sanee S1123 Lite / স্ট্যান্ডার্ড | আল্ট্রা-লো / ক্লাসিক ২জি | এইচকিউ / বড় ডিসপ্লে |
|---|---|---|---|
| **রেজোলিউশন (Resolution)** | **176×144 (QCIF)** | **128×96 (Sub-QCIF)** | **320×240 (QVGA)** |
| **ভিডিও কোডেক (Video Codec)** | **MPEG-4 SP / H.263** | **H.263 (Profile 0)** | **MPEG-4 Part 2** |
| **ফ্রেমরেট (Framerate)** | **15 FPS** (বেশি দিলে অডিও আউট-অব-সিঙ্ক হয়) | **12 FPS** | **15 FPS** |
| **ভিডিও বিটরেট (Bitrate)** | **96 kbps** | **64 kbps** | **192 kbps** |
| **অডিও কোডেক (Audio Codec)** | **AMR-NB (`amr_nb`)** | **AMR-NB** | **AMR-NB বা AAC** |
| **অডিও স্যাম্পল রেট** | **8000 Hz** (AMR Standard) | **8000 Hz** | **8000 Hz / 16000 Hz** |
| **অডিও চ্যানেল** | **1 Channel (Mono)** | **1 Channel (Mono)** | **1 Channel (Mono)** |
| **ভলিউম বুস্ট** | **+30% (`volume=1.3`)** | **+30%** | **+30%** |
| **এসপেক্ট রেশিও** | **Full Stretch বা Letterbox** | **Full Stretch** | **Letterbox** |

---

## 🛠️ ইন্সটলেশন (Installation)

### ১. রিপোজিটরি ক্লোন করুন
```bash
git clone https://github.com/op-sihab/3gp-turbo-studio.git
cd 3gp-turbo-studio
```

### ২. পাইথন ডিপেন্ডেন্সি ইনস্টল করুন
```bash
pip install -r requirements.txt
```
*(FFmpeg আপনার সিস্টেমে ইনস্টল না থাকলেও `imageio-ffmpeg` এর মাধ্যমে অটো-ডিটেক্ট হয়ে যাবে অথবা `bin/ffmpeg.exe` ফোল্ডারে রাখতে পারেন)*

### ৩. গ্লোবাল `3gp` কমান্ড সেটআপ (Windows)
আপনার কমান্ড প্রম্পটে `D:\3gp` (বা আপনার ক্লোন করা ফোল্ডার) পাথটি System/User `PATH` এ যুক্ত করুন। এরপর যেকোনো টার্মিনালে শুধু `3gp` টাইপ করলেই ওপেন হবে!

---

## 💻 ব্যবহারের নিয়ম (How to Use)

### ১. টার্মিনাল ড্যাশবোর্ড (TUI - সবচেয়ে পাওয়ারফুল)
টার্মিনাল বা পাওয়ারশেলে লিখুন:
```bash
3gp
```
**মেনু অপশনসমূহ:**
- `[1] YouTube Turbo (Single / Multi / Playlist)`: এক বা একাধিক ইউটিউব লিংক পেস্ট করলেই অটো ডাউনলোড ও টার্বো কনভার্ট।
- `[2] Local Video Files / Folder`: লোকাল ভিডিও বা ফোল্ডার ব্যাচ কনভার্ট।
- `[3] Drag & Drop Quick-Convert`: ফাইল টার্মিনালে টেনে এনে ছাড়ুন।
- `[4] SD Card Auto-Transfer Manager`: মেমোরি কার্ড ড্রাইভ অটো-ডিটেক্ট করে `Videos/` ফোল্ডারে কপি।
- `[5] 3GP Explorer & Player`: কনভার্ট করা ভিডিও সরাসরি টার্মিনাল থেকেই ভিউ ও প্লে করার সুবিধা।
- `[6] Studio Settings & Profile Customizer`: কোয়ালিটি ও রেজোলিউশন প্রোফাইল কনফিগারেশন।
- `[7] Live Hardware Benchmark`: প্রসেসর ও জিপিইউ এনকোডিং স্পিড ডায়াগনস্টিক।
- `[8] Web Browser GUI`: লোকাল ব্রাউজারে গ্রাফিক্যাল ইন্টারফেস।
- `[9] Button Phone Playback Guide`: সমস্যা সমাধানের নির্দেশিকা।

### ২. ইউটিউব লিংক সরাসরি কমান্ডে
```bash
3gp "https://youtu.be/O7LgZeWLR-A"
```

### ৩. কমান্ড লাইন ইন্টারফেস (CLI)
```bash
# একক ফাইল কনভার্ট
python cli.py "my_video.mp4"

# পুরো ফোল্ডার ব্যাচ কনভার্ট
python cli.py "D:\hisss" --batch -p standard
```

### ৪. লোকাল ওয়েব সার্ভার (Browser UI)
```bash
python server.py
```
ব্রাউজারে যান: `http://localhost:5000`

---

## 🏎️ Hardware Performance (Intel Core i3-4170 + HD 4400)

- **DXVA2 Hardware Acceleration:** H.264 ইনপুট ডিকোডিং সরাসরি Intel HD Graphics 4400 iGPU-তে অফলোড হয়।
- **Multi-Threaded MPEG-4 SP:** 4টি CPU থ্রেড একযোগে ব্যবহার করে।
- **Drop-Frames First:** `fps=15` ফিল্টারের শুরুতে থাকায় অতিরিক্ত ফ্রেম আগে ডিসকার্ড হয়।
- **Direct Scaling:** `flags=neighbor` ব্যবহার করায় কোনো ব্লারিং ওভারহেড থাকে না।
- **বাস্তব টেস্ট ফলাফল:**
  - **1 ঘণ্টা 01 মিনিটের ভিডিও** কনভার্ট হতে সময় লেগেছে মাত্র **৪৫.৬ সেকেন্ড**!
  - **স্পিড মাল্টিপ্লায়ার:** **83x – 118x Real-Time Speed**!

---

## 📄 License
This project is licensed under the MIT License.

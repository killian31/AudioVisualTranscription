---
title: AudioVisualTranscription
app_file: app.py
sdk: gradio
sdk_version: 4.19.2
---
# Speech to Video Subtitles

Get your synchronized subtitiled video in seconds!

![App screenshot](./app_ex.png)

## Installation

In your terminal, run (requires python<=3.11)

```bash
git clone https://github.com/killian31/AudioVisualTranscription
cd AudioVisualTranscription
pip install -r requirements.txt
```

The app needs ImageMagick and ffmpeg to run. To install them, run

- MacOS: `bash ./install_macos.sh`
- Debian/Ubuntu: `chmod +x install_linux.sh; ./install_linux.sh`

## Usage

Launch the Gradio app with

```bash
python3 app.py
```

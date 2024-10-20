---
title: AudioVisualTranscription
app_file: app.py
sdk: gradio
sdk_version: 5.1.0
---
# Speech to Video Subtitles

Get your synchronized subtitiled video in seconds!

![App screenshot](./app_ex.png)

## Installation

In your terminal, run the following commands

```bash
git clone https://github.com/killian31/AudioVisualTranscription
cd AudioVisualTranscription
pyenv virtualenv 3.11.9 avt
pyenv activate avt
pip install poetry
poetry install
```

The app needs ImageMagick and ffmpeg to run. To install them, run

- MacOS: `bash ./install_macos.sh`
- Debian/Ubuntu: `chmod +x install_linux.sh; ./install_linux.sh`

## Usage

Launch the Gradio app with

```bash
python3 app.py
```

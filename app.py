import subprocess

import cv2
import gradio as gr
import numpy as np
import torch
import whisper
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment


def draw_centered_text(img_pil, text, font_size, frame_size):
    draw = ImageDraw.Draw(img_pil)
    width, height = frame_size

    # Load a basic font
    font = ImageFont.truetype(None, font_size)

    # Calculate text size and position
    text_width, text_height = draw.textsize(text, font=font)
    x = (width - text_width) / 2
    y = (height - text_height) / 2

    # Adjust font size if text is too wide
    while text_width > width - 20:  # Adjust for padding
        font_size -= 1  # Decrease font size
        font = ImageFont.truetype(None, font_size)
        text_width, text_height = draw.textsize(text, font=font)
        x = (width - text_width) / 2
        y = (height - text_height) / 2

    # Draw text
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    return img_pil


def generate_video_cv2(audio_path, language, lag):

    # Transcribe audio
    result = model.transcribe(audio_path, language=language)

    # Video settings
    fps = 6
    frame_size = (1280, 720)
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.75
    font_color = (255, 255, 255)  # White
    background_color = (0, 0, 0)  # Black
    output_path = "./transcribed_video_cv2.mp4"

    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

    # Prepare video frames from transcription segments
    for segment in result["segments"]:
        text = segment["text"]
        duration = segment["end"] - segment["start"]
        frames_count = int(duration * fps)

        for _ in range(frames_count):
            img = np.full(
                (frame_size[1], frame_size[0], 3), background_color, dtype=np.uint8
            )
            # center text
            cv2.putText(
                img,
                text,
                (10, frame_size[1] // 2),
                font_face,
                font_scale,
                font_color,
                2,
                cv2.LINE_AA,
            )

            video.write(img)

    video.release()

    # Add lag if specified
    if lag > 0:
        audio = AudioSegment.silent(duration=lag * 1000) + AudioSegment.from_file(
            audio_path
        )
    else:
        audio = AudioSegment.from_file(audio_path)

    # Export audio
    audio_path_modified = "./modified_audio.mp3"
    audio.export(audio_path_modified, format="mp3")

    # Merge audio and video using FFmpeg
    final_output_path = "./final_transcribed_video.mp4"
    cmd = f"ffmpeg -y -i {output_path} -i {audio_path_modified} -c:v copy -c:a aac {final_output_path}"
    subprocess.run(cmd.split())

    return final_output_path


if __name__ == "__main__":
    # Load Whisper model
    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )
    model = whisper.load_model("base", device=device)
    # Gradio interface
    iface = gr.Interface(
        fn=generate_video_cv2,
        inputs=[
            gr.Audio(
                sources=["upload", "microphone"], type="filepath", label="Audio File"
            ),
            gr.Dropdown(
                ["en", "es", "fr", "de", "it", "nl", "ru", "zh"],
                label="Language",
                value="en",
            ),
            gr.Slider(
                minimum=0,
                maximum=10,
                step=1,
                value=0,
                label="Lag (seconds): delay the transcription by this amount of time.",
            ),
        ],
        outputs=gr.Video(label="Play Video", show_download_button=True),
        title="Audio Transcription Video Generator",
        description="Upload your audio file and select the language for transcription.",
    )

    iface.launch()

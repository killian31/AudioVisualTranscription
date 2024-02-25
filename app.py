import subprocess
import warnings

import cv2
import gradio as gr
import numpy as np
import torch
import whisper
from pydub import AudioSegment
from tqdm import tqdm


def generate_video_cv2(audio_path, language, lag, progress=gr.Progress()):

    # Transcribe audio
    progress(0.0, "Transcribing audio...")
    result = model.transcribe(audio_path, language=language)
    progress(0.30, "Audio transcribed!")

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
    if lag > 0:
        duration = lag
        frames_count = int(duration * fps)
        for _ in range(frames_count):
            img = np.full(
                (frame_size[1], frame_size[0], 3), background_color, dtype=np.uint8
            )
            video.write(img)
    total_segments = len(result["segments"])
    running_progress = 0.0

    for segment in result["segments"]:
        running_progress += 0.4 / total_segments
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
        progress(min(0.3 + running_progress, 0.7), "Generating video frames...")

    video.release()
    progress(0.7, "Video frames generated!")

    # Add lag if specified
    if lag > 0:
        audio = AudioSegment.from_file(audio_path) + AudioSegment.silent(
            duration=lag * 1000
        )
    else:
        audio = AudioSegment.from_file(audio_path)

    progress(0.75, "Merging audio and video...")
    # Export audio
    audio_path_modified = "./modified_audio.mp3"
    audio.export(audio_path_modified, format="mp3")

    # Merge audio and video using FFmpeg
    final_output_path = "./final_transcribed_video.mp4"
    cmd = f"ffmpeg -y -i {output_path} -i {audio_path_modified} -c:v copy -c:a aac {final_output_path}"
    subprocess.run(cmd.split())
    progress(1, "Done!")

    return final_output_path


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    # Load Whisper model
    device = "cuda" if torch.cuda.is_available() else "cpu"
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

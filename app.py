import gradio as gr
import numpy as np
import torch
import whisper
from moviepy.editor import *
from moviepy.video.VideoClip import TextClip

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

model = whisper.load_model("base", device=DEVICE)


def generate_video(audio_path, language):
    # Transcribe audio
    result = model.transcribe(audio_path, language=language)

    # Prepare video clips from transcription segments
    clips = []
    for segment in result["segments"]:
        text_clip = (
            TextClip(
                segment["text"],
                fontsize=24,
                font="Arial",
                color="white",
                bg_color="black",
                size=(1280, 720),
            )
            .set_duration(segment["end"] - segment["start"])
            .set_start(segment["start"])
        )
        clips.append(text_clip)

    # Concatenate clips and set audio
    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(AudioFileClip(audio_path))

    # Export video to a buffer
    output_path = "./transcribed_video.mp4"
    video.write_videofile(output_path, fps=6, codec="libx264", audio_codec="aac")

    return output_path


if __name__ == "__main__":

    print(
        f"Model is {'multilingual' if model.is_multilingual else 'English-only'} "
        f"and has {sum(np.prod(p.shape) for p in model.parameters()):,} parameters."
    )
    # Gradio interface
    iface = gr.Interface(
        fn=generate_video,
        inputs=[
            gr.Audio(
                sources=["upload", "microphone"], type="filepath", label="Audio File"
            ),
            gr.Dropdown(
                ["en", "es", "fr", "de", "it", "nl", "ru", "zh"],
                label="Language",
            ),
        ],
        outputs=gr.Video(label="Play Video", show_download_button=True),
        title="Audio Transcription Video Generator",
        description="Upload your audio file and select the language for transcription.",
    )

    iface.launch()

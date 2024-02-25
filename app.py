import gradio as gr
import torch
import whisper
from moviepy.editor import AudioFileClip, ColorClip, concatenate_videoclips
from moviepy.video.VideoClip import TextClip


def generate_video(audio_path, language, lag, progress=gr.Progress(track_tqdm=True)):
    # Transcribe audio
    progress(0.0, "Transcribing audio...")
    result = model.transcribe(audio_path, language=language)
    progress(0.30, "Audio transcribed!")

    # Prepare video clips from transcription segments
    clips = []
    total_segments = len(result["segments"])
    running_progress = 0.0
    for segment in result["segments"]:
        running_progress += 0.4 / total_segments
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
        progress(min(0.3 + running_progress, 0.7), "Generating video frames...")

    if lag > 0:
        clips.insert(0, ColorClip((1280, 720), color=(0, 0, 0)).set_duration(lag))
    progress(0.7, "Video frames generated!")

    # Concatenate clips and set audio
    progress(0.75, "Concatenating video clips...")
    video = concatenate_videoclips(clips, method="compose")

    # Add audio to the video
    progress(0.85, "Adding audio to video...")
    video = video.set_audio(AudioFileClip(audio_path))

    # Export video to a buffer
    progress(0.90, "Exporting video...")
    output_path = "./transcribed_video.mp4"
    video.write_videofile(output_path, fps=6, codec="libx264", audio_codec="aac")
    progress(1.0, "Video exported!")
    return output_path


if __name__ == "__main__":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=DEVICE)

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

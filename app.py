import os

import gradio as gr
import torch
import whisper
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.VideoClip import TextClip


def generate_srt_file(transcription_result, srt_file_path, lag=0):
    with open(srt_file_path, "w") as file:
        for i, segment in enumerate(transcription_result["segments"], start=1):
            # Adjusting times for lag
            start_time = segment["start"] + lag
            end_time = segment["end"] + lag
            text = segment["text"]

            # Convert times to SRT format (HH:MM:SS,MS)
            start_srt = f"{int(start_time // 3600):02d}:{int((start_time % 3600) // 60):02d}:{int(start_time % 60):02d},{int((start_time % 1) * 1000):03d}"
            end_srt = f"{int(end_time // 3600):02d}:{int((end_time % 3600) // 60):02d}:{int(end_time % 60):02d},{int((end_time % 1) * 1000):03d}"

            file.write(f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n")


def get_srt_filename(video_path, audio_path):
    if video_path is not None:
        return os.path.splitext(os.path.basename(video_path))[0] + ".srt"
    else:
        return os.path.splitext(os.path.basename(audio_path))[0] + ".srt"


def generate_video(
    audio_path, video_path, input, language, lag, progress=gr.Progress(track_tqdm=True)
):
    if audio_path is None and video_path is None:
        raise ValueError("Please upload an audio or video file.")
    if input == "Video" and video_path is None:
        raise ValueError("Please upload a video file.")
    if input == "Audio" and audio_path is None:
        raise ValueError("Please upload an audio file.")
    progress(0.0, "Checking input...")
    if input == "Video":
        progress(0.0, "Extracting audio from video...")
        audio_path = f"./{os.path.splitext(os.path.basename(video_path))[0]}.wav"
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
        progress(0.1, "Audio extracted!")

    # Transcribe audio
    progress(0.1, "Transcribing audio...")
    result = model.transcribe(audio_path, language=language)
    progress(0.30, "Audio transcribed!")

    # Generate SRT file
    progress(0.30, "Generating SRT file...")
    srt_file_path = get_srt_filename(video_path, audio_path)
    generate_srt_file(result, srt_file_path, lag=lag)
    progress(0.40, "SRT file generated!")

    if result["segments"] == []:
        raise gr.Error("No speech detected in the audio.")
    if input == "Video":
        if lag == 0:
            return video_path, srt_file_path
        else:
            # we simply extend the original video with a black screen at the end of duration lag
            video = VideoFileClip(video_path)
            fps = video.fps
            black_screen = ColorClip(
                size=video.size, color=(0, 0, 0), duration=lag
            ).set_fps(1)
            final_video = concatenate_videoclips([video, black_screen])
            output_video_path = "./transcribed_video.mp4"
            final_video.write_videofile(
                output_video_path, codec="libx264", audio_codec="aac"
            )
            return output_video_path, srt_file_path
    else:
        output_video_path = "./transcribed_video.mp4"
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration + lag
        video_clip = ColorClip(
            size=(1280, 720), color=(0, 0, 0), duration=duration
        ).set_fps(1)
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile(
            output_video_path, codec="libx264", audio_codec="aac"
        )
        return output_video_path, srt_file_path


def download_srt(audio_input, video_input):
    srt_file_path = get_srt_filename(video_input, audio_input)
    if os.path.exists(srt_file_path):
        return srt_file_path
    else:
        raise gr.Error("No SRT file found. Please generate subtitles first.")


if __name__ == "__main__":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=DEVICE)

    # Gradio Blocks implementation
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
        <div style="text-align: center;">
            <h1 style="color: #4A90E2; font-size: 3em;">Audio Transcription & Subtitled Video Generator 🎥✨</h1>
            <p style="font-size: 1.2em; color: #333; max-width: 1000px; margin: auto; text-align: left;">
                Transform your audio or video files into subtitled content effortlessly! <br>
                1. Upload your audio or video file, select the language, and receive a video with synchronized subtitles. <br>
                2. You can view the subtitled video directly here or download the subtitles as an SRT file for your use.
            </p>
        </div>
        """
        )

        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    sources=["upload", "microphone"],
                    type="filepath",
                    label="🎵 Upload Audio File",
                )
                video_input = gr.Video(
                    label="📹 Or Upload Video File", sources=["upload", "webcam"]
                )
            with gr.Column():
                file_type = gr.Dropdown(
                    ["Video", "Audio"],
                    label="File Type",
                    value="Video",
                    interactive=True,
                )
                language = gr.Dropdown(
                    ["en", "es", "fr", "de", "it", "nl", "ru", "no", "zh"],
                    label="Select Language",
                    value="en",
                    interactive=True,
                )
                lag_slider = gr.Slider(
                    minimum=0,
                    maximum=10,
                    step=1,
                    value=0,
                    label="⏱ Lag (seconds): delay the transcription by this amount of time.",
                )
                transcribe_button = gr.Button(
                    "🎬 Generate Subtitled Video", variant="primary"
                )
                download_button = gr.Button("💾 Download SRT File", variant="secondary")

            with gr.Column():
                video_output = gr.Video(
                    label="Play Video with Subtitles", show_download_button=False
                )
                srt_file_output = gr.File(label="Download Subtitle (SRT)")

        transcribe_button.click(
            fn=generate_video,
            inputs=[audio_input, video_input, file_type, language, lag_slider],
            outputs=video_output,
        )

        download_button.click(
            fn=download_srt,
            inputs=[audio_input, video_input],
            outputs=srt_file_output,
        )

    demo.launch()

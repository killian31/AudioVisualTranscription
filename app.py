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
        audio_path = "./temp_audio.wav"
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
    srt_file_path = "./temp.srt"
    generate_srt_file(result, srt_file_path, lag=lag)
    progress(0.40, "SRT file generated!")

    if input == "Video":
        # if lag is 0, we can use the original video, else we need to create a new video
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
        ).set_fps(
            1
        )  # Low fps
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile(
            output_video_path, codec="libx264", audio_codec="aac"
        )
        return output_video_path, srt_file_path


if __name__ == "__main__":
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=DEVICE)

    # Gradio interface
    iface = gr.Interface(
        fn=generate_video,
        inputs=[
            gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Audio File",
            ),
            gr.Video(label="Or Video File", sources=["upload", "webcam"]),
            gr.Dropdown(["Video", "Audio"], label="File Type", value="Audio"),
            gr.Dropdown(
                ["en", "es", "fr", "de", "it", "nl", "ru", "no", "zh"],
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

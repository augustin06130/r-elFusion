from moviepy.editor import VideoFileClip, AudioFileClip

def combine_video_audio(video_path, audio_path, output_path="outputs/final_video.mp4"):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path).set_duration(video.duration)
    final_video = video.set_audio(audio)
    final_video.write_videofile(output_path)
    return output_path

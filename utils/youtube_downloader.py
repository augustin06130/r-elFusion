import yt_dlp
from moviepy import VideoFileClip

def download_video(url, output_path="outputs/video_yt.mp4"):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return crop_to_9_16(output_path)


def crop_to_9_16(input_path, output_path="outputs/video.mp4"):
    clip = VideoFileClip(input_path)
    w, h = clip.size
    target_ratio = 9 / 16
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Trop large → crop horizontal (centrer sur la largeur)
        new_width = int(h * target_ratio)
        x_center = w // 2
        x1 = x_center - new_width // 2
        x2 = x_center + new_width // 2
        cropped_clip = clip.cropped(x1=x1, y1=0, x2=x2, y2=h)
    elif current_ratio < target_ratio:
        # Trop haut → crop vertical (centrer sur la hauteur)
        new_height = int(w / target_ratio)
        y_center = h // 2
        y1 = y_center - new_height // 2
        y2 = y_center + new_height // 2
        cropped_clip = clip.cropped(x1=0, y1=y1, x2=w, y2=y2)
    else:
        # Déjà en 9:16
        cropped_clip = clip

    # Exporter la vidéo recadrée
    cropped_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path


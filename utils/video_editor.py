from moviepy.video.VideoClip import TextClip, ImageClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def combine_video_audio(video_path, audio_path, text, output_path="outputs/final_video.mp4"):
    # Charger les médias
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)

    # Synchroniser la durée
    final_duration = min(video.duration, audio.duration)
    video = video.subclipped(0, final_duration)
    audio = audio.subclipped(0, final_duration)
    video = video.with_audio(audio)  # Appliquer l'audio au clip vidéo

    # Gestion des sous-titres
    words = text.split()
    segment_length = 4
    segments = [' '.join(words[i:i+segment_length]) for i in range(0, len(words), segment_length)]
    subtitle_duration = final_duration / len(segments)

    def create_text_image(text, video_width, video_height, font_size=40):
        img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("assets/fronts/Montserrat/static/Montserrat-Bold.ttf", font_size)  # Assure-toi que ce fichier existe
        except:
            font = ImageFont.truetype("Arial.ttf", font_size)  # Police alternative plus universelle

        text_lines = text.split("\n")
        text_width = max([draw.textbbox((0, 0), line, font=font)[2] for line in text_lines])
        position = ((video_width - text_width) // 2, int(video_height * 0.75))

        # --- Ajout de l'ombre ---
        shadow_offset = 4
        shadow_color = (0, 0, 0, 180)  # ombre semi-transparente
        draw.text(
            (position[0] + shadow_offset, position[1] + shadow_offset),
            text,
            font=font,
            fill=shadow_color
        )
        # --- Texte principal en blanc ---
        draw.text(position, text, font=font, fill=(255, 255, 255, 255))

        return np.array(img)

    subtitles = []
    for i, segment in enumerate(segments):
        txt = textwrap.fill(segment, width=30)

        # Méthode alternative - créer un ImageClip à partir d'une image PIL
        # Cette approche devrait fonctionner avec toutes les versions de MoviePy
        txt_img = create_text_image(txt, video.w, video.h, font_size=40)
        subtitle = ImageClip(txt_img, transparent=True) \
                  .with_duration(subtitle_duration) \
                  .with_start(i * subtitle_duration)

        subtitles.append(subtitle)

    # Créer le clip final avec les sous-titres
    final_clip = CompositeVideoClip([video] + subtitles)

    final_clip = final_clip.with_audio(video.audio)

    if final_clip.audio is None:
        final_clip = final_clip.with_audio(audio)

    # Export avec paramètres optimisés
    final_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        bitrate="15M",
        threads=4,
        preset='medium',  # Changed to medium for faster encoding
        ffmpeg_params=["-crf", "22"]
    )

    return output_path

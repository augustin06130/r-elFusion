import os
import math
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip

def text_to_speech(text, filename="voice.mp3", lang='fr'):
    """
    Convertit du texte en fichier audio avec gTTS
    """
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'audio: {e}")
        return None

def create_video(audio_file, background_video="fond.mp4", output="output.mp4"):
    """
    Crée une vidéo en combinant un fichier audio avec une vidéo de fond
    """
    try:
        # Vérifier l'existence des fichiers source
        if not os.path.exists(background_video):
            print(f"❌ Fichier vidéo de fond '{background_video}' introuvable")
            return False

        if not os.path.exists(audio_file):
            print(f"❌ Fichier audio '{audio_file}' introuvable")
            return False

        print(f"🎥 Création de la vidéo {output}...")

        # Charger la vidéo de fond
        video_clip = VideoFileClip(background_video)

        # Charger l'audio
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration

        # Si la vidéo est trop courte, on la boucle
        if video_clip.duration < audio_duration:
            print(f"⚠️ La vidéo de fond ({video_clip.duration:.1f}s) est plus courte que l'audio ({audio_duration:.1f}s)")
            print("🔄 Bouclage de la vidéo pour correspondre à la durée de l'audio...")

            # Calculer combien de fois nous devons répéter la vidéo
            repeat_count = math.ceil(audio_duration / video_clip.duration)
            extended_clip = video_clip

            for _ in range(repeat_count - 1):
                extended_clip = extended_clip.append_clip(video_clip)

            video_clip = extended_clip

        # Découper la vidéo à la longueur de l'audio
        video_clip = video_clip.subclipped(0, audio_duration)

        # Assembler l'audio et la vidéo
        final_clip = video_clip.with_audio(audio_clip)

        # Créer le dossier de sortie si nécessaire
        os.makedirs(os.path.dirname(output) or '.', exist_ok=True)

        # Rendre la vidéo
        final_clip.write_videofile(output, codec="libx264", audio_codec="aac", threads=4)

        # Libérer la mémoire
        video_clip.close()
        audio_clip.close()
        final_clip.close()

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la création de la vidéo: {e}")
        return False

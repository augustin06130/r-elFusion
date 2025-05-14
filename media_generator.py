import os
import math
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip

# Import des modules de gestion d'erreurs
from handle_log_exception.logger import setup_logger
from handle_log_exception.exceptions import RedditVideoError, AudioError, VideoError

# Création d'un logger spécifique pour ce module
logger = setup_logger("audio_video_processor")

def text_to_speech(text, filename="voice.mp3", lang="nt"):
    """
    Convertit du texte en fichier audio avec gTTS

    Args:
        text: Texte à convertir en audio
        filename: Nom du fichier audio de sortie
        lang: Code de langue pour la synthèse vocale

    Returns:
        str: Chemin du fichier audio créé ou None en cas d'erreur

    Raises:
        AudioError: En cas d'erreur lors de la création du fichier audio
    """
    logger.info(f"Conversion du texte en audio ({len(text)} caractères)")

    try:
        # Vérifier que le texte n'est pas vide
        if not text or len(text.strip()) == 0:
            raise AudioError("Impossible de créer un audio à partir d'un texte vide")

        # Créer le dossier de sortie si nécessaire
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

        # Créer l'audio avec gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filename)

        # Vérifier que le fichier a bien été créé
        if not os.path.exists(filename):
            raise AudioError(f"Le fichier audio n'a pas été créé", filename)

        file_size = os.path.getsize(filename)
        logger.info(f"Fichier audio créé avec succès: {filename} ({file_size/1024:.1f} KB)")

        return filename
    except Exception as e:
        error_msg = f"Erreur lors de la création de l'audio: {str(e)}"
        logger.error(error_msg)

        # Convertir l'exception en AudioError si ce n'en est pas déjà une
        if not isinstance(e, AudioError):
            raise AudioError(error_msg, filename) from e
        raise

def create_video(audio_file, background_video="fond.mp4", output="output.mp4"):
    """
    Crée une vidéo en combinant un fichier audio avec une vidéo de fond

    Args:
        audio_file: Chemin vers le fichier audio
        background_video: Chemin vers la vidéo de fond
        output: Chemin du fichier de sortie

    Returns:
        bool: True si la création a réussi, False sinon

    Raises:
        VideoError: En cas d'erreur lors de la création de la vidéo
    """
    logger.info(f"Création d'une vidéo avec l'audio '{audio_file}' et la vidéo de fond '{background_video}'")

    video_clip = None
    audio_clip = None
    final_clip = None

    try:
        # Vérifier l'existence des fichiers source
        if not os.path.exists(background_video):
            raise VideoError(f"Fichier vidéo de fond introuvable", background_video)

        if not os.path.exists(audio_file):
            raise VideoError(f"Fichier audio introuvable", audio_file)

        # Charger la vidéo de fond
        try:
            video_clip = VideoFileClip(background_video)
            logger.debug(f"Vidéo de fond chargée: {background_video} ({video_clip.duration:.1f}s)")
        except Exception as e:
            raise VideoError(f"Impossible de charger la vidéo de fond: {str(e)}", background_video) from e

        # Charger l'audio
        try:
            audio_clip = AudioFileClip(audio_file)
            audio_duration = audio_clip.duration
            logger.debug(f"Audio chargé: {audio_file} ({audio_duration:.1f}s)")
        except Exception as e:
            raise VideoError(f"Impossible de charger l'audio: {str(e)}", audio_file) from e

        # Si la vidéo est trop courte, on la boucle
        if video_clip.duration < audio_duration:
            logger.warning(f"La vidéo de fond ({video_clip.duration:.1f}s) est plus courte que l'audio ({audio_duration:.1f}s)")
            logger.info("Bouclage de la vidéo pour correspondre à la durée de l'audio...")

            # Calculer combien de fois nous devons répéter la vidéo
            repeat_count = math.ceil(audio_duration / video_clip.duration)
            extended_clip = video_clip

            for i in range(repeat_count - 1):
                logger.debug(f"Ajout de la boucle {i+1}/{repeat_count-1}")
                extended_clip = extended_clip.append_clip(video_clip)

            video_clip = extended_clip
            logger.info(f"Vidéo bouclée créée avec succès (nouvelle durée: {video_clip.duration:.1f}s)")

        # Découper la vidéo à la longueur de l'audio
        video_clip = video_clip.subclipped(0, audio_duration)
        logger.debug(f"Vidéo découpée à {audio_duration:.1f}s")

        # Assembler l'audio et la vidéo
        final_clip = video_clip.with_audio(audio_clip)
        logger.debug("Audio et vidéo assemblés avec succès")

        # Créer le dossier de sortie si nécessaire
        os.makedirs(os.path.dirname(output) or '.', exist_ok=True)

        # Rendre la vidéo
        logger.info(f"Rendu de la vidéo finale vers {output}...")
        final_clip.write_videofile(
            output,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None  # Désactiver la journalisation interne de moviepy qui est très verbeuse
        )

        # Vérifier que le fichier a bien été créé
        if not os.path.exists(output):
            raise VideoError("Le fichier vidéo n'a pas été créé", output)

        file_size = os.path.getsize(output)
        logger.info(f"Vidéo créée avec succès: {output} ({file_size/(1024*1024):.1f} MB)")

        return True

    except Exception as e:
        error_msg = f"Erreur lors de la création de la vidéo: {str(e)}"
        logger.error(error_msg)

        # Convertir l'exception en VideoError si ce n'en est pas déjà une
        if not isinstance(e, VideoError):
            raise VideoError(error_msg, output) from e
        raise

    finally:
        # Nettoyer les ressources, même en cas d'erreur
        logger.debug("Nettoyage des ressources...")
        try:
            if video_clip:
                video_clip.close()
            if audio_clip:
                audio_clip.close()
            if final_clip:
                final_clip.close()
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage des ressources: {e}")

def process_video_from_text(text, background_video="fond.mp4", output="output.mp4", lang='fr'):
    """
    Fonction de haut niveau qui traite du texte en une vidéo complète

    Args:
        text: Texte à convertir en voix off
        background_video: Vidéo de fond à utiliser
        output: Fichier vidéo de sortie
        lang: Langue pour la synthèse vocale

    Returns:
        bool: True si le traitement a réussi, False sinon
    """
    logger.info(f"Démarrage du traitement vidéo à partir du texte ({len(text)} caractères)")

    try:
        # Créer un fichier audio temporaire
        temp_audio = "temp_voice.mp3"

        # Convertir le texte en audio
        audio_file = text_to_speech(text, temp_audio, lang)
        if not audio_file:
            return False

        # Créer la vidéo avec l'audio
        result = create_video(audio_file, background_video, output)

        # Supprimer le fichier audio temporaire
        try:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
                logger.debug(f"Fichier audio temporaire supprimé: {temp_audio}")
        except Exception as e:
            logger.warning(f"Impossible de supprimer le fichier audio temporaire: {e}")

        return result

    except RedditVideoError as e:
        logger.error(f"Erreur lors du traitement vidéo: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur inattendue lors du traitement vidéo: {e}")
        return False

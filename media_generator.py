# import os
# import math
# import textwrap
# import numpy as np
# from gtts import gTTS
# from PIL import Image, ImageDraw, ImageFont
# from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip

# # Import des modules de gestion d'erreurs
# from handle_log_exception.logger import setup_logger
# from handle_log_exception.exceptions import RedditVideoError, AudioError, VideoError

# # Création d'un logger spécifique pour ce module
# logger = setup_logger("audio_video_processor")

# def text_to_speech(text, filename="voice.mp3", lang="fr"):
#     """
#     Convertit du texte en fichier audio avec gTTS

#     Args:
#         text: Texte à convertir en audio
#         filename: Nom du fichier audio de sortie
#         lang: Code de langue pour la synthèse vocale

#     Returns:
#         str: Chemin du fichier audio créé ou None en cas d'erreur

#     Raises:
#         AudioError: En cas d'erreur lors de la création du fichier audio
#     """
#     logger.info(f"Conversion du texte en audio ({len(text)} caractères)")

#     try:
#         # Vérifier que le texte n'est pas vide
#         if not text or len(text.strip()) == 0:
#             raise AudioError("Impossible de créer un audio à partir d'un texte vide")

#         # Créer le dossier de sortie si nécessaire
#         os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

#         # Créer l'audio avec gTTS
#         tts = gTTS(text=text, lang=lang, slow=False)
#         tts.save(filename)

#         # Vérifier que le fichier a bien été créé
#         if not os.path.exists(filename):
#             raise AudioError(f"Le fichier audio n'a pas été créé", filename)

#         file_size = os.path.getsize(filename)
#         logger.info(f"Fichier audio créé avec succès: {filename} ({file_size/1024:.1f} KB)")

#         return filename
#     except Exception as e:
#         error_msg = f"Erreur lors de la création de l'audio: {str(e)}"
#         logger.error(error_msg)

#         # Convertir l'exception en AudioError si ce n'en est pas déjà une
#         if not isinstance(e, AudioError):
#             raise AudioError(error_msg, filename) from e
#         raise

# def create_subtitles(text, video_width, video_height, video_duration, font_size=40, font_path=None):
#     """
#     Crée des sous-titres pour une vidéo à partir du texte

#     Args:
#         text: Texte à utiliser pour les sous-titres
#         video_width: Largeur de la vidéo
#         video_height: Hauteur de la vidéo
#         video_duration: Durée de la vidéo en secondes
#         font_size: Taille de la police
#         font_path: Chemin vers la police à utiliser (optionnel)

#     Returns:
#         list: Liste des clips de sous-titres
#     """
#     logger.info(f"Création des sous-titres pour le texte ({len(text)} caractères)")

#     # Découper le texte en segments
#     words = text.split()
#     segment_length = 4  # Nombre de mots par segment
#     segments = [' '.join(words[i:i+segment_length]) for i in range(0, len(words), segment_length)]

#     # Calculer la durée de chaque segment
#     subtitle_duration = video_duration / len(segments)

#     logger.debug(f"Texte divisé en {len(segments)} segments de {subtitle_duration:.2f}s chacun")

#     def create_text_image(text, video_width, video_height, font_size=40):
#         """Crée une image avec du texte centré et une ombre"""
#         img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
#         draw = ImageDraw.Draw(img)

#         # Essayer de charger la police personnalisée, sinon utiliser Arial
#         try:
#             if font_path:
#                 font = ImageFont.truetype(font_path, font_size)
#             else:
#                 # Essayer d'abord la police Montserrat
#                 try:
#                     font = ImageFont.truetype("assets/fonts/Montserrat/static/Montserrat-Bold.ttf", font_size)
#                 except:
#                     font = ImageFont.truetype("Arial.ttf", font_size)
#         except Exception as e:
#             logger.warning(f"Impossible de charger la police, utilisation de la police par défaut: {e}")
#             # Utiliser la police par défaut
#             font = ImageFont.load_default()

#         # Gérer le texte multiligne
#         text_lines = text.split("\n")

#         # Calculer la largeur maximale du texte pour centrage
#         try:
#             text_width = max([draw.textbbox((0, 0), line, font=font)[2] for line in text_lines])
#         except:
#             # Fallback pour les versions antérieures de PIL
#             text_width = max([draw.textsize(line, font=font)[0] for line in text_lines])

#         # Positionner le texte en bas de l'écran
#         position = ((video_width - text_width) // 2, int(video_height * 0.75))

#         # Ajouter l'ombre
#         shadow_offset = 4
#         shadow_color = (0, 0, 0, 180)  # Ombre semi-transparente

#         for line_idx, line in enumerate(text_lines):
#             y_offset = position[1] + line_idx * (font_size + 5)
#             draw.text(
#                 (position[0] + shadow_offset, y_offset + shadow_offset),
#                 line,
#                 font=font,
#                 fill=shadow_color
#             )
#             # Texte principal en blanc
#             draw.text(
#                 (position[0], y_offset),
#                 line,
#                 font=font,
#                 fill=(255, 255, 255, 255)
#             )

#         return np.array(img)

#     # Créer les sous-titres
#     subtitles = []
#     for i, segment in enumerate(segments):
#         # Formater le texte pour qu'il tienne dans la largeur de l'écran
#         formatted_text = textwrap.fill(segment, width=30)

#         # Créer l'image du sous-titre
#         subtitle_img = create_text_image(formatted_text, video_width, video_height, font_size)

#         # Créer le clip du sous-titre
#         start_time = i * subtitle_duration
#         subtitle_clip = ImageClip(subtitle_img, transparent=True) \
#                       .with_duration(subtitle_duration) \
#                       .with_start(start_time)

#         subtitles.append(subtitle_clip)

#     logger.info(f"{len(subtitles)} clips de sous-titres créés avec succès")

#     return subtitles

# def create_video(audio_file, background_video="video.mp4", output="output.mp4", text=None, segment_index=0, total_segments=1):
#     """
#     Crée une vidéo en combinant un fichier audio avec une vidéo de fond et des sous-titres optionnels

#     Args:
#         audio_file: Chemin vers le fichier audio
#         background_video: Chemin vers la vidéo de fond
#         output: Chemin du fichier de sortie
#         text: Texte pour les sous-titres (optionnel)
#         segment_index: Index du segment actuel (utilisé pour choisir la partie de la vidéo)
#         total_segments: Nombre total de segments (utilisé pour calculer la partie de la vidéo)

#     Returns:
#         bool: True si la création a réussi, False sinon

#     Raises:
#         VideoError: En cas d'erreur lors de la création de la vidéo
#     """
#     logger.info(f"Création d'une vidéo avec l'audio '{audio_file}' et la vidéo de fond '{background_video}'")
#     logger.info(f"Segment {segment_index + 1}/{total_segments}")

#     if text:
#         logger.info("Des sous-titres seront ajoutés à la vidéo")

#     video_clip = None
#     audio_clip = None
#     final_clip = None

#     try:
#         # Vérifier l'existence des fichiers source
#         if not os.path.exists(background_video):
#             raise VideoError(f"Fichier vidéo de fond introuvable", background_video)

#         if not os.path.exists(audio_file):
#             raise VideoError(f"Fichier audio introuvable", audio_file)

#         # Charger la vidéo de fond
#         try:
#             full_video_clip = VideoFileClip(background_video)
#             logger.debug(f"Vidéo de fond chargée: {background_video} ({full_video_clip.duration:.1f}s)")
#         except Exception as e:
#             raise VideoError(f"Impossible de charger la vidéo de fond: {str(e)}", background_video) from e

#         # Charger l'audio
#         try:
#             audio_clip = AudioFileClip(audio_file)
#             audio_duration = audio_clip.duration
#             # Ajouter 1.5 secondes à la durée du segment vidéo
#             segment_duration = audio_duration + 1.5
#             logger.debug(f"Audio chargé: {audio_file} ({audio_duration:.1f}s)")
#         except Exception as e:
#             raise VideoError(f"Impossible de charger l'audio: {str(e)}", audio_file) from e

#         # Vérifier si la vidéo est suffisamment longue pour tous les segments
#         total_duration_needed = segment_duration * total_segments

#         if full_video_clip.duration < total_duration_needed:
#             logger.warning(f"La vidéo de fond ({full_video_clip.duration:.1f}s) est plus courte que nécessaire ({total_duration_needed:.1f}s)")
#             logger.info("Bouclage de la vidéo pour obtenir une durée suffisante...")

#             # Calculer combien de fois nous devons répéter la vidéo
#             repeat_count = math.ceil(total_duration_needed / full_video_clip.duration)
#             extended_clip = full_video_clip

#             for i in range(repeat_count - 1):
#                 logger.debug(f"Ajout de la boucle {i+1}/{repeat_count-1}")
#                 extended_clip = extended_clip.append_clip(full_video_clip)

#             full_video_clip = extended_clip
#             logger.info(f"Vidéo bouclée créée avec succès (nouvelle durée: {full_video_clip.duration:.1f}s)")

#         # Extraire le segment vidéo correspondant à ce segment audio
#         start_time = segment_index * segment_duration
#         end_time = start_time + segment_duration

#         # S'assurer que end_time ne dépasse pas la durée de la vidéo
#         end_time = min(end_time, full_video_clip.duration)

#         # Extraire le segment de vidéo correspondant
#         video_clip = full_video_clip.subclipped(start_time, end_time)
#         logger.debug(f"Segment vidéo extrait: {start_time:.1f}s à {end_time:.1f}s (durée: {video_clip.duration:.1f}s)")

#         # Ajuster la durée du clip vidéo si nécessaire
#         if video_clip.duration < segment_duration:
#             logger.warning(f"Le segment vidéo est plus court que nécessaire ({video_clip.duration:.1f}s < {segment_duration:.1f}s)")
#             # On garde la durée actuelle

#         # Assembler l'audio et la vidéo
#         # Assurons-nous que l'audio n'est pas plus long que la vidéo
#         if audio_duration > video_clip.duration:
#             audio_clip = audio_clip.subclipped(0, video_clip.duration)
#             logger.debug(f"Audio ajusté à la durée de la vidéo: {video_clip.duration:.1f}s")

#         video_with_audio = video_clip.with_audio(audio_clip)
#         logger.debug("Audio et vidéo assemblés avec succès")

#         # Si du texte est fourni, ajouter des sous-titres
#         if text:
#             try:
#                 # Récupérer les dimensions de la vidéo
#                 video_width, video_height = video_clip.size

#                 # Créer les sous-titres
#                 subtitles = create_subtitles(text, video_width, video_height, audio_duration)

#                 # Créer le clip final avec les sous-titres
#                 final_clip = CompositeVideoClip([video_with_audio] + subtitles)
#                 logger.info("Sous-titres ajoutés avec succès")
#             except Exception as e:
#                 logger.error(f"Erreur lors de l'ajout des sous-titres: {e}")
#                 logger.warning("Poursuite sans sous-titres")
#                 final_clip = video_with_audio
#         else:
#             final_clip = video_with_audio

#         # Créer le dossier de sortie si nécessaire
#         os.makedirs(os.path.dirname(output) or '.', exist_ok=True)

#         # Rendre la vidéo
#         logger.info(f"Rendu de la vidéo finale vers {output}...")
#         final_clip.write_videofile(
#             output,
#             codec="libx264",
#             audio_codec="aac",
#             threads=4,
#             logger=None  # Désactiver la journalisation interne de moviepy qui est très verbeuse
#         )

#         # Vérifier que le fichier a bien été créé
#         if not os.path.exists(output):
#             raise VideoError("Le fichier vidéo n'a pas été créé", output)

#         file_size = os.path.getsize(output)
#         logger.info(f"Vidéo créée avec succès: {output} ({file_size/(1024*1024):.1f} MB)")

#         return True

#     except Exception as e:
#         error_msg = f"Erreur lors de la création de la vidéo: {str(e)}"
#         logger.error(error_msg)

#         # Convertir l'exception en VideoError si ce n'en est pas déjà une
#         if not isinstance(e, VideoError):
#             raise VideoError(error_msg, output) from e
#         raise

#     finally:
#         # Nettoyer les ressources, même en cas d'erreur
#         logger.debug("Nettoyage des ressources...")
#         try:
#             if video_clip:
#                 video_clip.close()
#             if full_video_clip:
#                 full_video_clip.close()
#             if audio_clip:
#                 audio_clip.close()
#             if final_clip:
#                 final_clip.close()
#         except Exception as e:
#             logger.warning(f"Erreur lors du nettoyage des ressources: {e}")

# def process_video_from_text(text, background_video="video.mp4", output="output.mp4", lang='fr', add_subtitles=True, segment_index=0, total_segments=1):
#     """
#     Fonction de haut niveau qui traite du texte en une vidéo complète avec sous-titres optionnels

#     Args:
#         text: Texte à convertir en voix off et sous-titres
#         background_video: Vidéo de fond à utiliser
#         output: Fichier vidéo de sortie
#         lang: Langue pour la synthèse vocale
#         add_subtitles: Ajouter des sous-titres à la vidéo
#         segment_index: Index du segment actuel
#         total_segments: Nombre total de segments

#     Returns:
#         bool: True si le traitement a réussi, False sinon
#     """
#     logger.info(f"Démarrage du traitement vidéo à partir du texte ({len(text)} caractères)")
#     logger.info(f"Segment {segment_index + 1}/{total_segments}")
#     logger.info(f"Sous-titres: {'Activés' if add_subtitles else 'Désactivés'}")

#     try:
#         # Créer un fichier audio temporaire
#         temp_audio = f"temp_voice_{segment_index}.mp3"

#         # Convertir le texte en audio
#         audio_file = text_to_speech(text, temp_audio, lang)
#         if not audio_file:
#             return False

#         # Créer la vidéo avec l'audio et les sous-titres optionnels
#         result = create_video(
#             audio_file,
#             background_video,
#             output,
#             text=text if add_subtitles else None,
#             segment_index=segment_index,
#             total_segments=total_segments
#         )

#         # Supprimer le fichier audio temporaire
#         try:
#             if os.path.exists(temp_audio):
#                 os.remove(temp_audio)
#                 logger.debug(f"Fichier audio temporaire supprimé: {temp_audio}")
#         except Exception as e:
#             logger.warning(f"Impossible de supprimer le fichier audio temporaire: {e}")

#         return result

#     except RedditVideoError as e:
#         logger.error(f"Erreur lors du traitement vidéo: {e}")
#         return False
#     except Exception as e:
#         logger.error(f"Erreur inattendue lors du traitement vidéo: {e}")
#         return False











import os
import math
import textwrap
import numpy as np
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip

# Import des modules de gestion d'erreurs
from handle_log_exception.logger import setup_logger
from handle_log_exception.exceptions import RedditVideoError, AudioError, VideoError

# Création d'un logger spécifique pour ce module
logger = setup_logger("audio_video_processor")

# Variable globale pour suivre les positions de départ des segments
segment_positions = []

def text_to_speech(text, filename="voice.mp3", lang="fr"):
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

def create_subtitles(text, video_width, video_height, video_duration, font_size=40, font_path=None):
    """
    Crée des sous-titres pour une vidéo à partir du texte

    Args:
        text: Texte à utiliser pour les sous-titres
        video_width: Largeur de la vidéo
        video_height: Hauteur de la vidéo
        video_duration: Durée de la vidéo en secondes
        font_size: Taille de la police
        font_path: Chemin vers la police à utiliser (optionnel)

    Returns:
        list: Liste des clips de sous-titres
    """
    logger.info(f"Création des sous-titres pour le texte ({len(text)} caractères)")

    # Découper le texte en segments
    words = text.split()
    segment_length = 4  # Nombre de mots par segment
    segments = [' '.join(words[i:i+segment_length]) for i in range(0, len(words), segment_length)]

    # Calculer la durée de chaque segment
    subtitle_duration = video_duration / len(segments)

    logger.debug(f"Texte divisé en {len(segments)} segments de {subtitle_duration:.2f}s chacun")

    def create_text_image(text, video_width, video_height, font_size=40):
        """Crée une image avec du texte centré et une ombre"""
        img = Image.new('RGBA', (video_width, video_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Essayer de charger la police personnalisée, sinon utiliser Arial
        try:
            if font_path:
                font = ImageFont.truetype(font_path, font_size)
            else:
                # Essayer d'abord la police Montserrat
                try:
                    font = ImageFont.truetype("assets/fonts/Montserrat/static/Montserrat-Bold.ttf", font_size)
                except:
                    font = ImageFont.truetype("Arial.ttf", font_size)
        except Exception as e:
            logger.warning(f"Impossible de charger la police, utilisation de la police par défaut: {e}")
            # Utiliser la police par défaut
            font = ImageFont.load_default()

        # Gérer le texte multiligne
        text_lines = text.split("\n")

        # Calculer la largeur maximale du texte pour centrage
        try:
            text_width = max([draw.textbbox((0, 0), line, font=font)[2] for line in text_lines])
        except:
            # Fallback pour les versions antérieures de PIL
            text_width = max([draw.textsize(line, font=font)[0] for line in text_lines])

        # Positionner le texte en bas de l'écran
        position = ((video_width - text_width) // 2, int(video_height * 0.75))

        # Ajouter l'ombre
        shadow_offset = 4
        shadow_color = (0, 0, 0, 180)  # Ombre semi-transparente

        for line_idx, line in enumerate(text_lines):
            y_offset = position[1] + line_idx * (font_size + 5)
            draw.text(
                (position[0] + shadow_offset, y_offset + shadow_offset),
                line,
                font=font,
                fill=shadow_color
            )
            # Texte principal en blanc
            draw.text(
                (position[0], y_offset),
                line,
                font=font,
                fill=(255, 255, 255, 255)
            )

        return np.array(img)

    # Créer les sous-titres
    subtitles = []
    for i, segment in enumerate(segments):
        # Formater le texte pour qu'il tienne dans la largeur de l'écran
        formatted_text = textwrap.fill(segment, width=30)

        # Créer l'image du sous-titre
        subtitle_img = create_text_image(formatted_text, video_width, video_height, font_size)

        # Créer le clip du sous-titre
        start_time = i * subtitle_duration
        subtitle_clip = ImageClip(subtitle_img, transparent=True) \
                      .with_duration(subtitle_duration) \
                      .with_start(start_time)

        subtitles.append(subtitle_clip)

    logger.info(f"{len(subtitles)} clips de sous-titres créés avec succès")

    return subtitles

def initialize_segment_tracking():
    """Réinitialise le suivi des segments vidéo"""
    global segment_positions
    segment_positions = []
    logger.info("Suivi des segments vidéo réinitialisé")

def get_segment_position(segment_index, audio_duration=None):
    """
    Obtient la position de départ d'un segment vidéo

    Args:
        segment_index: Index du segment actuel
        audio_duration: Durée du segment audio actuel (pour mise à jour)

    Returns:
        float: Position de départ en secondes
    """
    global segment_positions

    # Si c'est le premier segment, commencer à 0
    if segment_index == 0:
        # Réinitialiser la liste si on commence une nouvelle série
        initialize_segment_tracking()
        logger.info("Premier segment, démarrage à 0 seconde")
        # Ajouter le premier point de repère si audio_duration est fourni
        if audio_duration is not None:
            segment_positions.append(audio_duration + 1.5)  # audio + 1.5s de tampon
        return 0.0

    # Si l'index est valide dans notre liste de positions
    if segment_index - 1 < len(segment_positions):
        # Retourner la somme des durées précédentes
        start_pos = sum(segment_positions[:segment_index])
        logger.info(f"Segment {segment_index+1}: démarrage à {start_pos:.1f} secondes (basé sur {segment_index} segments précédents)")

        # Mettre à jour la liste si audio_duration est fourni
        if audio_duration is not None and segment_index >= len(segment_positions):
            segment_positions.append(audio_duration + 1.5)  # audio + 1.5s de tampon

        return start_pos
    else:
        # Si nous n'avons pas suffisamment d'informations, estimation approximative
        # (cela ne devrait pas arriver avec une utilisation correcte)
        logger.warning(f"Données de segment insuffisantes pour l'index {segment_index}, utilisation d'une estimation")
        if len(segment_positions) > 0:
            # Utiliser la moyenne des durées connues pour estimer
            avg_duration = sum(segment_positions) / len(segment_positions)
            missing_segments = segment_index - len(segment_positions)
            estimated_start = sum(segment_positions) + (avg_duration * missing_segments)

            if audio_duration is not None:
                segment_positions.append(audio_duration + 1.5)

            return estimated_start
        else:
            # Aucune information - utiliser une estimation très approximative
            logger.warning("Aucune donnée de segment disponible, utilisation d'une durée estimée de 60 secondes par segment")
            estimated_start = segment_index * 60

            if audio_duration is not None:
                segment_positions.append(audio_duration + 1.5)

            return estimated_start

def create_video(audio_file, background_video="video.mp4", output="output.mp4", text=None, segment_index=0, total_segments=1):
    """
    Crée une vidéo en combinant un fichier audio avec une vidéo de fond et des sous-titres optionnels

    Args:
        audio_file: Chemin vers le fichier audio
        background_video: Chemin vers la vidéo de fond
        output: Chemin du fichier de sortie
        text: Texte pour les sous-titres (optionnel)
        segment_index: Index du segment actuel (utilisé pour choisir la partie de la vidéo)
        total_segments: Nombre total de segments (utilisé pour calculer la partie de la vidéo)

    Returns:
        bool: True si la création a réussi, False sinon

    Raises:
        VideoError: En cas d'erreur lors de la création de la vidéo
    """
    logger.info(f"Création d'une vidéo avec l'audio '{audio_file}' et la vidéo de fond '{background_video}'")
    logger.info(f"Segment {segment_index + 1}/{total_segments}")

    if text:
        logger.info("Des sous-titres seront ajoutés à la vidéo")

    video_clip = None
    audio_clip = None
    final_clip = None
    full_video_clip = None

    try:
        # Vérifier l'existence des fichiers source
        if not os.path.exists(background_video):
            raise VideoError(f"Fichier vidéo de fond introuvable", background_video)

        if not os.path.exists(audio_file):
            raise VideoError(f"Fichier audio introuvable", audio_file)

        # Charger la vidéo de fond
        try:
            full_video_clip = VideoFileClip(background_video)
            logger.debug(f"Vidéo de fond chargée: {background_video} ({full_video_clip.duration:.1f}s)")
        except Exception as e:
            raise VideoError(f"Impossible de charger la vidéo de fond: {str(e)}", background_video) from e

        # Charger l'audio
        try:
            audio_clip = AudioFileClip(audio_file)
            audio_duration = audio_clip.duration
            # Ajouter 1.5 secondes à la durée du segment vidéo
            segment_duration = audio_duration + 1.5
            logger.debug(f"Audio chargé: {audio_file} ({audio_duration:.1f}s)")
        except Exception as e:
            raise VideoError(f"Impossible de charger l'audio: {str(e)}", audio_file) from e

        # Obtenir le point de départ pour ce segment en utilisant le système de suivi des segments
        start_time = get_segment_position(segment_index, audio_duration)

        # Journaliser le point de départ pour vérification
        logger.info(f"Position de départ pour le segment {segment_index+1}: {start_time:.2f}s")
        logger.info(f"Durée audio: {audio_duration:.2f}s (avec tampon: {segment_duration:.2f}s)")

        # Déboguer la liste complète des positions de segment (uniquement pour le développement)
        global segment_positions
        logger.debug(f"Liste des positions de segment: {[f'{pos:.2f}s' for pos in segment_positions]}")

        # Estimer la durée totale nécessaire
        estimated_end = start_time + segment_duration
        logger.debug(f"Position de fin estimée: {estimated_end:.2f}s")

        # Vérifier si la vidéo est suffisamment longue
        if full_video_clip.duration < estimated_end:
            logger.warning(f"La vidéo de fond ({full_video_clip.duration:.1f}s) est plus courte que nécessaire ({estimated_end:.1f}s)")
            logger.info("Bouclage de la vidéo pour obtenir une durée suffisante...")

            # Calculer combien de fois nous devons répéter la vidéo
            repeat_count = math.ceil(estimated_end / full_video_clip.duration)
            extended_clip = full_video_clip

            for i in range(repeat_count - 1):
                logger.debug(f"Ajout de la boucle {i+1}/{repeat_count-1}")
                extended_clip = extended_clip.append_clip(full_video_clip)

            full_video_clip = extended_clip
            logger.info(f"Vidéo bouclée créée avec succès (nouvelle durée: {full_video_clip.duration:.1f}s)")

        end_time = start_time + segment_duration

        # S'assurer que end_time ne dépasse pas la durée de la vidéo
        end_time = min(end_time, full_video_clip.duration)

        # Extraire le segment de vidéo correspondant
        video_clip = full_video_clip.subclipped(start_time, end_time)
        logger.debug(f"Segment vidéo extrait: {start_time:.1f}s à {end_time:.1f}s (durée: {video_clip.duration:.1f}s)")

        # Ajuster la durée du clip vidéo si nécessaire
        if video_clip.duration < segment_duration:
            logger.warning(f"Le segment vidéo est plus court que nécessaire ({video_clip.duration:.1f}s < {segment_duration:.1f}s)")
            # On garde la durée actuelle

        # Assembler l'audio et la vidéo
        # Assurons-nous que l'audio n'est pas plus long que la vidéo
        if audio_duration > video_clip.duration:
            audio_clip = audio_clip.subclipped(0, video_clip.duration)
            logger.debug(f"Audio ajusté à la durée de la vidéo: {video_clip.duration:.1f}s")

        video_with_audio = video_clip.with_audio(audio_clip)
        logger.debug("Audio et vidéo assemblés avec succès")

        # Si du texte est fourni, ajouter des sous-titres
        if text:
            try:
                # Récupérer les dimensions de la vidéo
                video_width, video_height = video_clip.size

                # Créer les sous-titres
                subtitles = create_subtitles(text, video_width, video_height, audio_duration)

                # Créer le clip final avec les sous-titres
                final_clip = CompositeVideoClip([video_with_audio] + subtitles)
                logger.info("Sous-titres ajoutés avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout des sous-titres: {e}")
                logger.warning("Poursuite sans sous-titres")
                final_clip = video_with_audio
        else:
            final_clip = video_with_audio

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

        # La valeur de retour reste inchangée pour maintenir la compatibilité
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
            if full_video_clip:
                full_video_clip.close()
            if audio_clip:
                audio_clip.close()
            if final_clip:
                final_clip.close()
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage des ressources: {e}")

def process_video_from_text(text, background_video="video.mp4", output="output.mp4", lang='fr', add_subtitles=True, segment_index=0, total_segments=1):
    """
    Fonction de haut niveau qui traite du texte en une vidéo complète avec sous-titres optionnels

    Args:
        text: Texte à convertir en voix off et sous-titres
        background_video: Vidéo de fond à utiliser
        output: Fichier vidéo de sortie
        lang: Langue pour la synthèse vocale
        add_subtitles: Ajouter des sous-titres à la vidéo
        segment_index: Index du segment actuel
        total_segments: Nombre total de segments

    Returns:
        bool: True si le traitement a réussi, False sinon
    """
    logger.info(f"Démarrage du traitement vidéo à partir du texte ({len(text)} caractères)")
    logger.info(f"Segment {segment_index + 1}/{total_segments}")
    logger.info(f"Sous-titres: {'Activés' if add_subtitles else 'Désactivés'}")

    try:
        # Créer un fichier audio temporaire
        temp_audio = f"temp_voice_{segment_index}.mp3"

        # Convertir le texte en audio
        audio_file = text_to_speech(text, temp_audio, lang)
        if not audio_file:
            return False

        # Créer la vidéo avec l'audio et les sous-titres optionnels
        result = create_video(
            audio_file,
            background_video,
            output,
            text=text if add_subtitles else None,
            segment_index=segment_index,
            total_segments=total_segments
        )

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

def process_multi_segment_video(texts, background_video="video.mp4", output_pattern="output_{}.mp4", lang='fr', add_subtitles=True):
    """
    Traite plusieurs segments de texte en vidéos séquentielles

    Args:
        texts: Liste des textes à traiter
        background_video: Vidéo de fond à utiliser
        output_pattern: Modèle pour les noms de fichiers de sortie (doit contenir {})
        lang: Langue pour la synthèse vocale
        add_subtitles: Ajouter des sous-titres aux vidéos

    Returns:
        list: Liste des chemins des vidéos créées
    """
    logger.info(f"Traitement de {len(texts)} segments vidéo")

    # Réinitialiser le suivi des segments
    initialize_segment_tracking()

    created_videos = []

    for i, text in enumerate(texts):
        output_file = output_pattern.format(i)
        logger.info(f"Traitement du segment {i+1}/{len(texts)}: {output_file}")

        # Traiter ce segment
        success = process_video_from_text(
            text,
            background_video=background_video,
            output=output_file,
            lang=lang,
            add_subtitles=add_subtitles,
            segment_index=i,
            total_segments=len(texts)
        )

        if success:
            created_videos.append(output_file)
            logger.info(f"Segment {i+1} traité avec succès")
        else:
            logger.error(f"Échec du traitement du segment {i+1}")

    logger.info(f"{len(created_videos)}/{len(texts)} segments traités avec succès")
    return created_videos

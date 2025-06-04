import yt_dlp
import os
import random
import logging
import re
from moviepy import VideoFileClip

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("video_download.log"),
        logging.StreamHandler()
    ]
)

# Dictionnaire des playlists thématiques
PLAYLIST_THEMES = {
    # Jeux vidéo
    "minecraft": "https://www.youtube.com/playlist?list=PLmSs-0cFIbfVWhkZx0i4UMiZdr2C0Z8w7", # playlist valide
    "gta5": "https://www.youtube.com/playlist?list=PLcpME8j-OMRw5fA_Kkw0-Fo7Gi_7Hstsi", # playlist valide
    "fortnite": "https://www.youtube.com/playlist?list=PL4vrFQwPcb12ticENMiILZoMOC_5fOQxM",
    "valorant": "https://www.youtube.com/playlist?list=PLQwKnV26UMYT78ZOkx8LBGBgm9-x8_l9c",
    "apex": "https://www.youtube.com/playlist?list=PLjT74Nm0e7lfO9skUG9GXMQZPoAZ1p_bj",
    # Films et séries
    "marvel": "https://www.youtube.com/playlist?list=PLxgVGKKuC-gBLCzAC-9bVw3AcfctQYCnA",
    "starwars": "https://www.youtube.com/playlist?list=PLZbXA4lyCtqolaQOAhnkKPZ1KKjxnuOTF",
    "netflix": "https://www.youtube.com/playlist?list=PLZbLQVqNUQVY4R5SoOQ_TJZO0wGwdgkNJ",
    # Genres
    "horreur": "https://www.youtube.com/playlist?list=PLB_IBXxJUjPEr0VkJxz0XpH5u2hqGXltB",
    "comedie": "https://www.youtube.com/playlist?list=PLxj0bWGrshx2S5ZBvM3Qj3-9hB1q9TbZ4",
    "action": "https://www.youtube.com/playlist?list=PLoNv-FQUuVE0q5REvMH2-wAzBKBqYO4uU",
    # Tech
    "tech": "https://www.youtube.com/playlist?list=PLFr3c472VstzAUSTygS7YK0jnpROBiU6i",
    "apple": "https://www.youtube.com/playlist?list=PLHFlHpPjgk72cF4GQ_DsfmF2EnQVbZ5yM",
    "android": "https://www.youtube.com/playlist?list=PLwe1s1XtjPCh-j9Viy3q3lS5mfNaJUmUH",
    # Divers
    "musique": "https://www.youtube.com/playlist?list=PLDxl2H0cCYV-5QT5xdsOLY46lEeG8-v1p",
    "cuisine": "https://www.youtube.com/playlist?list=PL3N_SBgvR3TO9WqVNvI0BnYGXl-Y4Ub2a",
    "voyage": "https://www.youtube.com/playlist?list=PLMJoXNrMC5U2YzQdw5scq5BfHXR_fAPXr",
    "sport": "https://www.youtube.com/playlist?list=PLWSbV7P_GN3StlRK1S9mJCTppxmnrBtm_",
    "animaux": "https://www.youtube.com/playlist?list=PLjLa4ynNn6WYq8hLIH8_0go9FSHyy-_03",
    # Générique (utilisé si aucun thème spécifique n'est trouvé)
    "general": "https://www.youtube.com/playlist?list=PLmSs-0cFIbfVWhkZx0i4UMiZdr2C0Z8w7"
}

class VideoDownloadError(Exception):
    """Exception personnalisée pour les erreurs de téléchargement vidéo"""
    pass

def get_playlist_url_by_theme(theme):
    """
    Récupère l'URL de la playlist correspondant au thème spécifié.
    Si le thème n'existe pas, retourne la playlist générale.
    
    Args:
        theme (str): Le thème demandé
        
    Returns:
        str: URL de la playlist correspondante
    """
    try:
        # Convertir le thème en minuscules pour éviter les problèmes de casse
        theme = theme.lower().strip()
        
        # Vérifier si le thème existe dans le dictionnaire
        if theme in PLAYLIST_THEMES:
            logging.info(f"Thème trouvé: {theme}")
            return PLAYLIST_THEMES[theme]
        else:
            logging.warning(f"Thème non trouvé: {theme}, utilisation du thème général")
            return PLAYLIST_THEMES["general"]
    except Exception as e:
        logging.error(f"Erreur lors de la récupération du thème: {str(e)}")
        return PLAYLIST_THEMES["general"]

def get_videos_from_playlist(playlist_url, max_results=None):
    """
    Récupère les URLs des vidéos d'une playlist YouTube.

    Args:
        playlist_url (str): URL de la playlist YouTube
        max_results (int, optional): Nombre maximum de résultats à retourner

    Returns:
        list: Liste des URLs de vidéos dans la playlist
    """
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'skip_download': True,
        }

        if max_results:
            ydl_opts['playlist_items'] = f"1:{max_results}"

        logging.info(f"Récupération des vidéos de la playlist: {playlist_url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(playlist_url, download=False)

            if not result or 'entries' not in result:
                logging.warning(f"Aucun résultat trouvé pour la playlist: {playlist_url}")
                return []

            # Filtrer les résultats pour obtenir uniquement les URL
            video_urls = []
            for entry in result['entries']:
                if entry and 'id' in entry:
                    video_id = entry['id']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_urls.append(video_url)

            logging.info(f"Trouvé {len(video_urls)} vidéos dans la playlist")
            return video_urls

    except Exception as e:
        error_msg = f"Erreur lors de la récupération des vidéos de la playlist: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def get_video_info(url):
    """
    Récupère les informations d'une vidéo sans la télécharger.

    Args:
        url (str): URL de la vidéo

    Returns:
        dict: Informations sur la vidéo
    """
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info

    except Exception as e:
        error_msg = f"Erreur lors de la récupération des infos vidéo: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def filter_videos_by_duration(video_urls, duration_range):
    """
    Filtre les vidéos par durée.

    Args:
        video_urls (list): Liste des URLs des vidéos à filtrer
        duration_range (tuple): Plage de durée souhaitée en secondes (min, max)

    Returns:
        list: Liste des vidéos filtrées avec leur durée [(url, duration, title), ...]
    """
    min_duration, max_duration = duration_range
    suitable_videos = []

    for video_url in video_urls:
        try:
            info = get_video_info(video_url)

            if not info:
                continue

            video_duration = info.get('duration', 0)
            video_title = info.get('title', 'Sans titre')

            if min_duration <= video_duration <= max_duration:
                suitable_videos.append((video_url, video_duration, video_title))
                logging.info(f"Vidéo compatible trouvée: {video_title} - {video_url} ({video_duration}s)")

        except Exception as e:
            logging.warning(f"Impossible d'obtenir les infos pour {video_url}: {str(e)}")
            continue

    logging.info(f"Vidéos filtrées par durée: {len(video_urls)} → {len(suitable_videos)} vidéos")
    return suitable_videos

def download_video_by_theme(theme, duration_range=(10, 30), output_path="outputs/video_yt.mp4", random_selection=True, max_videos_to_check=50):
    """
    Télécharge une vidéo depuis une playlist thématique en fonction de la durée souhaitée.
    
    Args:
        theme (str): Thème de la vidéo recherchée (ex: "minecraft", "tech", "sport")
        duration_range (tuple): Plage de durée souhaitée en secondes (min, max)
        output_path (str): Chemin de sortie pour la vidéo téléchargée
        random_selection (bool): Si True, sélectionne une vidéo au hasard parmi celles qui correspondent
                               Si False, prend la première vidéo qui correspond
        max_videos_to_check (int): Nombre maximum de vidéos à vérifier dans la playlist
        
    Returns:
        str: Chemin de la vidéo téléchargée et recadrée
        
    Raises:
        VideoDownloadError: Si une erreur survient pendant le téléchargement
    """
    try:
        # Récupérer l'URL de la playlist correspondant au thème
        playlist_url = get_playlist_url_by_theme(theme)
        
        logging.info(f"Téléchargement vidéo pour le thème: {theme} - Playlist: {playlist_url}")
        
        # Utiliser la fonction existante pour télécharger depuis la playlist
        return download_video_from_playlist(
            playlist_url=playlist_url,
            duration_range=duration_range,
            output_path=output_path,
            random_selection=random_selection,
            max_videos_to_check=max_videos_to_check
        )
    except Exception as e:
        error_msg = f"Erreur lors du téléchargement par thème: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def download_video_from_playlist(playlist_url=None, duration_range=(10, 30), output_path="outputs/video_yt.mp4", random_selection=True, max_videos_to_check=50):
    """
    Télécharge une vidéo depuis une playlist en fonction de la durée souhaitée.

    Args:
        playlist_url (str): URL de la playlist YouTube
        duration_range (tuple): Plage de durée souhaitée en secondes (min, max)
        output_path (str): Chemin de sortie pour la vidéo téléchargée
        random_selection (bool): Si True, sélectionne une vidéo au hasard parmi celles qui correspondent
                               Si False, prend la première vidéo qui correspond
        max_videos_to_check (int): Nombre maximum de vidéos à vérifier dans la playlist

    Returns:
        str: Chemin de la vidéo téléchargée et recadrée

    Raises:
        VideoDownloadError: Si une erreur survient pendant le téléchargement
    """
    try:
        # Créer le répertoire de sortie s'il n'existe pas
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not playlist_url:
            raise VideoDownloadError("URL de playlist non fournie")

        # Récupérer les vidéos de la playlist
        video_urls = get_videos_from_playlist(playlist_url, max_results=max_videos_to_check)

        if not video_urls:
            raise VideoDownloadError(f"Aucune vidéo trouvée dans la playlist: {playlist_url}")

        # Filtrer les vidéos par durée
        suitable_videos = filter_videos_by_duration(video_urls, duration_range)

        if not suitable_videos:
            raise VideoDownloadError(
                f"Aucune vidéo compatible avec la durée {duration_range[0]}-{duration_range[1]}s "
                f"trouvée dans la playlist: {playlist_url}"
            )

        # Choisir une vidéo
        if random_selection:
            url, duration, title = random.choice(suitable_videos)
            logging.info(f"Vidéo aléatoire sélectionnée: {title} - {url} ({duration}s)")
        else:
            url, duration, title = suitable_videos[0]
            logging.info(f"Première vidéo compatible sélectionnée: {title} - {url} ({duration}s)")

        # Télécharger la vidéo avec des options plus flexibles
        logging.info(f"Téléchargement de la vidéo: {title} - {url}")

        # Options de téléchargement améliorées
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 
            'merge_output_format': 'mp4',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'noplaylist': True,
            'no-cache-dir': True,  # Désactiver le cache pour éviter les problèmes de fichiers corrompus
            'cookiesfrombrowser': ('chrome',), # Pour les coockies, si nécessaire
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Vérifier que le fichier a bien été téléchargé
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise VideoDownloadError(f"Échec du téléchargement: {url}")

        # Traiter la vidéo pour obtenir le format souhaité
        final_video_path = process_video(output_path, duration_range)
        logging.info(f"Vidéo traitée avec succès: {final_video_path}")

        return final_video_path

    except VideoDownloadError:
        # Relancer les erreurs spécifiques
        raise
    except KeyboardInterrupt:
        logging.info("Téléchargement interrompu par l'utilisateur")
        raise VideoDownloadError("Téléchargement interrompu par l'utilisateur")
    except Exception as e:
        error_msg = f"Erreur lors du téléchargement de la vidéo: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def download_video_by_url(url, duration_range=(10, 30), output_path="outputs/video_yt.mp4"):
    """
    Télécharge une vidéo directement par son URL.

    Args:
        url (str): URL de la vidéo YouTube
        duration_range (tuple): Plage de durée souhaitée en secondes (min, max)
        output_path (str): Chemin de sortie pour la vidéo téléchargée

    Returns:
        str: Chemin de la vidéo téléchargée et recadrée

    Raises:
        VideoDownloadError: Si une erreur survient pendant le téléchargement
    """
    try:
        # Créer le répertoire de sortie s'il n'existe pas
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Vérifier d'abord si la vidéo correspond à la durée souhaitée
        info = get_video_info(url)
        if not info:
            raise VideoDownloadError(f"Impossible d'obtenir les informations pour: {url}")

        video_duration = info.get('duration', 0)
        video_title = info.get('title', 'Sans titre')
        min_duration, max_duration = duration_range

        if video_duration < min_duration:
            logging.warning(f"La vidéo est trop courte: {video_duration}s < {min_duration}s")
            # On continue quand même mais on informe l'utilisateur

        # Options de téléchargement améliorées
        ydl_opts = {
            'format': 'best[height<=720]/best',  # Format plus flexible
            'merge_output_format': 'mp4',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': False,
            'noplaylist': True,
            'retries': 3,
            'fragment_retries': 3,
        }

        logging.info(f"Téléchargement de la vidéo: {video_title} - {url} ({video_duration}s)")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Vérifier que le fichier a bien été téléchargé
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise VideoDownloadError(f"Échec du téléchargement: {url}")

        # Traiter la vidéo pour obtenir le format souhaité
        final_video_path = process_video(output_path, duration_range)
        logging.info(f"Vidéo traitée avec succès: {final_video_path}")

        return final_video_path

    except KeyboardInterrupt:
        logging.info("Téléchargement interrompu par l'utilisateur")
        raise VideoDownloadError("Téléchargement interrompu par l'utilisateur")
    except Exception as e:
        error_msg = f"Erreur lors du téléchargement de la vidéo: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def process_video(video_path, duration_range=(10, 30), aspect_ratio="9:16"):
    """
    Traite une vidéo pour obtenir la durée souhaitée et le bon ratio d'aspect.

    Args:
        video_path (str): Chemin de la vidéo à traiter
        duration_range (tuple): Plage de durée souhaitée (min, max)
        aspect_ratio (str): Format d'image souhaité

    Returns:
        str: Chemin de la vidéo traitée
    """
    try:
        clip = VideoFileClip(video_path)

        # Gérer la durée
        original_duration = clip.duration
        min_duration, max_duration = duration_range

        # Si la vidéo est plus longue que la durée maximale, la découper
        if original_duration > max_duration:
            # Choisir un point de départ aléatoire, mais pas trop proche de la fin
            max_start = max(0, original_duration - max_duration - 1)
            if max_start > 0:
                start_time = random.uniform(0, max_start)
            else:
                start_time = 0

            # Limiter la durée
            end_time = min(start_time + max_duration, original_duration)
            clip = clip.subclip(start_time, end_time)
            logging.info(f"Vidéo découpée: {start_time:.2f}s à {end_time:.2f}s (durée: {end_time-start_time:.2f}s)")

        # Si la vidéo est plus courte que la durée minimale, on la garde telle quelle
        if clip.duration < min_duration:
            logging.warning(f"La vidéo est plus courte que la durée minimale souhaitée: {clip.duration:.2f}s < {min_duration}s")

        # Générer un nom de fichier pour la vidéo traitée
        base_dir = os.path.dirname(video_path)
        base_name = os.path.basename(video_path)
        name_parts = os.path.splitext(base_name)
        processed_path = os.path.join(base_dir, f"{name_parts[0]}_processed{name_parts[1]}")

        # Recadrer au format 9:16 (le seul format supporté maintenant)
        if aspect_ratio != "9:16":
            logging.warning(f"Format {aspect_ratio} non supporté, utilisation du format 9:16 par défaut")

        processed_path = crop_to_9_16(clip=clip, output_path=processed_path)

        # Libérer les ressources
        clip.close()

        return processed_path

    except Exception as e:
        error_msg = f"Erreur lors du traitement de la vidéo: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def crop_to_9_16(input_path=None, output_path=None, clip=None):
    """
    Recadre une vidéo au format 9:16 (vertical).

    Args:
        input_path (str, optional): Chemin d'entrée de la vidéo (si clip n'est pas fourni)
        output_path (str, optional): Chemin de sortie de la vidéo (si on veut sauvegarder directement)
        clip (VideoFileClip, optional): VideoFileClip à recadrer (prioritaire sur input_path)

    Returns:
        VideoFileClip ou str: VideoFileClip recadrée ou chemin de la vidéo recadrée
    """
    try:
        # Si un clip est fourni, l'utiliser directement
        if clip is None and input_path is not None:
            clip = VideoFileClip(input_path)
            close_clip = True  # Fermer le clip à la fin si nous l'avons créé ici
        elif clip is None:
            raise ValueError("Vous devez fournir soit un chemin d'entrée, soit un clip")
        else:
            close_clip = False  # Ne pas fermer le clip s'il a été fourni par l'appelant

        # Dimensions originales
        original_width, original_height = clip.size
        target_ratio = 9 / 16

        # Calcul plus précis du ratio actuel
        current_ratio = original_width / original_height

        # Tolérance pour éviter un recadrage inutile si le ratio est déjà proche de 9:16
        if abs(current_ratio - target_ratio) < 0.01:
            # Déjà en 9:16 (ou très proche)
            cropped_clip = clip
        elif current_ratio > target_ratio:
            # Trop large → crop horizontal (centrer sur la largeur)
            new_width = int(original_height * target_ratio)
            x_center = original_width // 2
            x1 = max(0, x_center - new_width // 2)
            x2 = min(original_width, x_center + new_width // 2 + (new_width % 2))  # Assurer une largeur exacte
            cropped_clip = clip.cropped(x1=x1, y1=0, x2=x2, y2=original_height)
        else:
            # Trop haut → crop vertical (centrer sur la hauteur)
            new_height = int(original_width / target_ratio)
            y_center = original_height // 2
            y1 = max(0, y_center - new_height // 2)
            y2 = min(original_height, y_center + new_height // 2 + (new_height % 2))  # Assurer une hauteur exacte
            cropped_clip = clip.cropped(x1=0, y1=y1, x2=original_width, y2=y2)

        # Si un chemin de sortie est fourni, enregistrer la vidéo
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Optimisations pour l'encodage
            cropped_clip.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=4,
                ffmpeg_params=["-crf", "23"]  # Meilleur compromis qualité/taille
            )

            # Nettoyage des ressources
            if close_clip:
                clip.close()
                cropped_clip.close()

            return output_path

        # Sinon, si nous avons ouvert le clip original, le fermer
        if close_clip:
            clip.close()

        return cropped_clip
        
    except Exception as e:
        error_msg = f"Erreur lors du recadrage: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def list_videos_in_playlist(playlist_url, duration_range=None, max_results=50):
    """
    Liste toutes les vidéos d'une playlist avec leurs informations de durée.
    Optionnellement, filtre par plage de durée.

    Args:
        playlist_url (str): URL de la playlist YouTube
        duration_range (tuple, optional): Plage de durée souhaitée (min, max) en secondes
        max_results (int): Nombre maximum de vidéos à analyser

    Returns:
        list: Liste des vidéos avec leurs informations [(url, duration, title), ...]
    """
    try:
        # Récupérer toutes les URLs de la playlist
        video_urls = get_videos_from_playlist(playlist_url, max_results=max_results)
        
        if not video_urls:
            logging.warning(f"Aucune vidéo trouvée dans la playlist: {playlist_url}")
            return []
            
        # Récupérer les informations pour chaque vidéo
        video_infos = []
        for url in video_urls:
            try:
                info = get_video_info(url)
                if info:
                    duration = info.get('duration', 0)
                    title = info.get('title', 'Sans titre')
                    
                    # Filtrer par durée si spécifié
                    if duration_range:
                        min_duration, max_duration = duration_range
                        if min_duration <= duration <= max_duration:
                            video_infos.append((url, duration, title))
                    else:
                        video_infos.append((url, duration, title))
            except Exception as e:
                logging.warning(f"Erreur lors de la récupération des infos pour {url}: {str(e)}")
                continue
                
        # Trier par durée (croissante)
        video_infos.sort(key=lambda x: x[1])
        
        return video_infos
        
    except Exception as e:
        error_msg = f"Erreur lors de la liste des vidéos: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def list_available_themes():
    """
    Liste tous les thèmes disponibles dans le dictionnaire PLAYLIST_THEMES.
    
    Returns:
        list: Liste des thèmes disponibles
    """
    try:
        # Exclure le thème "general" qui est utilisé par défaut
        themes = [theme for theme in PLAYLIST_THEMES.keys() if theme != "general"]
        return sorted(themes)
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des thèmes: {str(e)}")
        return []

# Exemple d'utilisation avec gestion d'erreurs améliorée
# if __name__ == "__main__":
#     try:
#         # Afficher les thèmes disponibles
#         themes = list_available_themes()
#         print("Thèmes disponibles:")
#         for theme in themes:
#             print(f" - {theme}")
        
#         # Exemple 1: Télécharger une vidéo depuis une playlist thématique
#         theme = "minecraft"  # Choisir un thème parmi les disponibles
#         video_path = download_video_by_theme(
#             theme=theme,
#             duration_range=(60, 300),  # Entre 1 et 5 minutes
#             output_path=f"outputs/video_{theme}.mp4",)
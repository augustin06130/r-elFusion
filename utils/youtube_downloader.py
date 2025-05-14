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

class VideoDownloadError(Exception):
    """Exception personnalisée pour les erreurs de téléchargement vidéo"""
    pass

def search_videos_by_theme(theme, max_results=5, excluded_themes=None):
    """
    Recherche des vidéos YouTube par thème ou hashtag, en excluant certains thèmes.
    
    Args:
        theme (str or list): Thème ou hashtag (sans le symbole #) ou liste de thèmes
        max_results (int): Nombre maximum de résultats à retourner
        excluded_themes (list, optional): Liste des thèmes à exclure
        
    Returns:
        list: Liste des URLs de vidéos correspondant au thème
    """
    try:
        # Vérifier si theme est une liste ou une chaîne
        if isinstance(theme, list):
            # Si c'est une liste, convertir en une chaîne unique pour la recherche
            cleaned_themes = []
            for t in theme:
                if isinstance(t, str):
                    if t.startswith('#'):
                        cleaned_themes.append(t[1:])
                    else:
                        cleaned_themes.append(t)
            theme = " ".join(cleaned_themes)
        elif isinstance(theme, str):
            # Nettoyer le thème s'il s'agit d'une chaîne
            if theme.startswith('#'):
                theme = theme[1:]  # Enlever le symbole # s'il est présent
        else:
            raise ValueError("Le thème doit être une chaîne de caractères ou une liste de chaînes")
            
        # Formatage de la requête de recherche
        search_query = f'"{theme}"'
        
        # Ajouter les exclusions à la requête si spécifiées
        if excluded_themes and isinstance(excluded_themes, list) and len(excluded_themes) > 0:
            for excluded_theme in excluded_themes:
                # Vérifier si le thème exclu est une chaîne
                if isinstance(excluded_theme, str):
                    # Nettoyer le thème exclu
                    if excluded_theme.startswith('#'):
                        excluded_theme = excluded_theme[1:]
                    # Ajouter l'exclusion à la requête
                    search_query += f' -"{excluded_theme}"'
            
            logging.info(f"Recherche avec exclusions: {search_query}")
            
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'noplaylist': True,
            'playlistreverse': False,
            'skip_download': True,
            'format': 'best',
            'max_downloads': max_results,
            'cookiesfrombrowser': ('chrome',),
        }
        
        logging.info(f"Recherche de vidéos sur le thème: {theme}")
        
        # Effectuer la recherche YouTube
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_url = f"ytsearch{max_results}:{search_query}"
            result = ydl.extract_info(search_url, download=False)
            
            if not result or 'entries' not in result:
                logging.warning(f"Aucun résultat trouvé pour le thème: {theme}")
                return []
                
            # Filtrer les résultats pour obtenir uniquement les URL
            video_urls = []
            for entry in result['entries']:
                if entry and 'url' in entry:
                    # Pour YouTube, nous avons besoin de transformer l'URL
                    if 'id' in entry:
                        video_id = entry['id']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_urls.append(video_url)
            
            logging.info(f"Trouvé {len(video_urls)} vidéos pour le thème: {theme}")
            return video_urls
            
    except Exception as e:
        error_msg = f"Erreur lors de la recherche de vidéos: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def filter_videos_by_metadata(video_urls, excluded_keywords=None, included_keywords=None):
    """
    Filtre les vidéos selon leurs métadonnées (titre, description, etc.)
    
    Args:
        video_urls (list): Liste des URLs des vidéos à filtrer
        excluded_keywords (list, optional): Liste des mots-clés à exclure
        included_keywords (list, optional): Liste des mots-clés à inclure (au moins un doit être présent)
        
    Returns:
        list: Liste filtrée des URLs de vidéos
    """
    if not excluded_keywords and not included_keywords:
        return video_urls
        
    filtered_urls = []
    
    for url in video_urls:
        try:
            info = get_video_info(url)
            
            if not info:
                continue
                
            # Vérifier le titre et la description
            title = info.get('title', '').lower()
            description = info.get('description', '').lower()
            tags = [tag.lower() for tag in info.get('tags', [])] if info.get('tags') else []
            
            # Combinons toutes les métadonnées en un seul texte pour simplifier la recherche
            metadata_text = f"{title} {description} {' '.join(tags)}"
            
            # Vérifier si un des mots-clés exclus est présent
            should_exclude = False
            if excluded_keywords:
                for keyword in excluded_keywords:
                    keyword = keyword.lower()
                    if keyword in metadata_text:
                        logging.info(f"Vidéo exclue (contient '{keyword}'): {url}")
                        should_exclude = True
                        break
            
            # Si déjà exclu, passer à la vidéo suivante
            if should_exclude:
                continue
                
            # Vérifier si au moins un des mots-clés inclus est présent (si des mots-clés sont spécifiés)
            should_include = True
            if included_keywords and len(included_keywords) > 0:
                should_include = False
                for keyword in included_keywords:
                    keyword = keyword.lower()
                    if keyword in metadata_text:
                        logging.info(f"Vidéo incluse (contient '{keyword}'): {url}")
                        should_include = True
                        break
                
                if not should_include:
                    logging.info(f"Vidéo non incluse (aucun mot-clé requis trouvé): {url}")
            
            # N'ajouter que si tous les critères sont respectés
            if should_include:
                filtered_urls.append(url)
                
        except Exception as e:
            logging.warning(f"Impossible de filtrer {url}: {str(e)}")
            # En cas d'erreur, on garde la vidéo pour éviter de trop filtrer
            filtered_urls.append(url)
            
    logging.info(f"Filtrage par métadonnées: {len(video_urls)} → {len(filtered_urls)} vidéos")
    return filtered_urls

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
            'format': 'best',
            'skip_download': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'cookiesfrombrowser': ('chrome',),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
            
    except Exception as e:
        error_msg = f"Erreur lors de la récupération des infos vidéo: {str(e)}"
        logging.error(error_msg)
        raise VideoDownloadError(error_msg) from e

def download_video_by_theme(theme=None, url=None, duration_range=(10, 30), output_path="outputs/video_yt.mp4", excluded_themes=None, excluded_keywords=None, included_keywords=None):
    """
    Télécharge une vidéo par thème ou URL directe, avec contrôle de la durée et exclusions/inclusions.
    
    Args:
        theme (str, optional): Thème ou hashtag pour la recherche
        url (str, optional): URL directe de la vidéo (prioritaire sur le thème)
        duration_range (tuple): Plage de durée souhaitée en secondes (min, max)
        output_path (str): Chemin de sortie pour la vidéo téléchargée
        excluded_themes (list, optional): Liste des thèmes à exclure de la recherche
        excluded_keywords (list, optional): Liste des mots-clés à exclure des métadonnées
        included_keywords (list, optional): Liste des mots-clés à inclure dans les métadonnées (au moins un)
        
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
        
        # Si l'URL n'est pas fournie, rechercher par thème
        if not url and theme:
            video_urls = search_videos_by_theme(theme, max_results=10, excluded_themes=excluded_themes)
            
            if not video_urls:
                raise VideoDownloadError(f"Aucune vidéo trouvée pour le thème: {theme}")
            
            # Filtrer les vidéos par métadonnées si nécessaire
            if excluded_keywords or included_keywords:
                video_urls = filter_videos_by_metadata(
                    video_urls, 
                    excluded_keywords=excluded_keywords,
                    included_keywords=included_keywords
                )
                
                if not video_urls:
                    if included_keywords:
                        raise VideoDownloadError(f"Aucune vidéo ne correspond aux critères de mots-clés à inclure/exclure")
                    else:
                        raise VideoDownloadError(f"Aucune vidéo ne correspond après filtrage des mots-clés exclus")
            
            # Filtrer les vidéos par durée
            min_duration, max_duration = duration_range
            suitable_videos = []
            
            for video_url in video_urls:
                try:
                    info = get_video_info(video_url)
                    
                    if not info:
                        continue
                        
                    video_duration = info.get('duration', 0)
                    
                    if min_duration <= video_duration <= max_duration:
                        suitable_videos.append((video_url, video_duration))
                        logging.info(f"Vidéo compatible trouvée: {video_url} ({video_duration}s)")
                        
                    # Si nous avons trouvé au moins 3 vidéos compatibles, arrêter la recherche
                    if len(suitable_videos) >= 3:
                        break
                        
                except Exception as e:
                    logging.warning(f"Impossible d'obtenir les infos pour {video_url}: {str(e)}")
                    continue
            
            if not suitable_videos:
                # Si aucune vidéo ne correspond à la durée exacte, prendre celles qui sont plus longues
                for video_url in video_urls:
                    try:
                        info = get_video_info(video_url)
                        
                        if not info:
                            continue
                            
                        video_duration = info.get('duration', 0)
                        
                        if video_duration > min_duration:
                            suitable_videos.append((video_url, video_duration))
                            logging.info(f"Vidéo partiellement compatible trouvée: {video_url} ({video_duration}s)")
                            
                        # Limiter à 3 vidéos
                        if len(suitable_videos) >= 3:
                            break
                            
                    except Exception as e:
                        continue
            
            if not suitable_videos:
                raise VideoDownloadError(f"Aucune vidéo compatible avec la durée {min_duration}-{max_duration}s trouvée pour le thème: {theme}")
            
            # Choisir une vidéo au hasard parmi les vidéos compatibles
            url, _ = random.choice(suitable_videos)
            logging.info(f"Vidéo sélectionnée: {url}")
        
        elif not url:
            raise VideoDownloadError("Aucun thème ni URL fourni")
        
        # Télécharger la vidéo
        logging.info(f"Téléchargement de la vidéo: {url}")
        
        # Options de téléchargement
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]',
            'merge_output_format': 'mp4',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'noplaylist': True,
            'cookiesfrombrowser': ('chrome',),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Vérifier que le fichier a bien été téléchargé
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise VideoDownloadError(f"Échec du téléchargement: {url}")
        
        # Traiter la vidéo pour obtenir la durée souhaitée
        final_video_path = process_video(output_path, duration_range)
        logging.info(f"Vidéo traitée avec succès: {final_video_path}")
        
        return final_video_path
        
    except VideoDownloadError:
        # Relancer les erreurs spécifiques
        raise
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
            clip = clip.subclipped(start_time, end_time)
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
    # Si un clip est fourni, l'utiliser directement
    if clip is None and input_path is not None:
        clip = VideoFileClip(input_path)
        close_clip = True  # Fermer le clip à la fin si nous l'avons créé ici
    elif clip is None:
        raise ValueError("Vous devez fournir soit un chemin d'entrée, soit un clip")
    else:
        close_clip = False  # Ne pas fermer le clip s'il a été fourni par l'appelant
    
    # Dimensions originales
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

    # Si un chemin de sortie est fourni, enregistrer la vidéo
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        cropped_clip.write_videofile(
            output_path, 
            codec="libx264", 
            audio_codec="aac",
            preset="medium",
            threads=4
        )
        
        if close_clip:
            clip.close()
            cropped_clip.close()
            
        return output_path
    
    # Sinon, si nous avons ouvert le clip original, le fermer
    if close_clip:
        clip.close()
        
    return cropped_clip

# Exemple d'utilisation
if __name__ == "__main__":
    try:
        # Définir les thèmes et mots-clés à exclure
        excluded_themes = ["politics", "violence"]
        excluded_keywords = ["violent"]
        
        # Définir les mots-clés à inclure (au moins un doit être présent)
        included_keywords = ["minecraft", "gameplay", "timelaps", "build"]
        included_themes = ["minecraft"]

        # Télécharger une vidéo par thème avec exclusions et inclusions
        video_path = download_video_by_theme(
            theme=included_themes,          # Thème de recherche
            duration_range=(150, 300),        # Durée souhaitée entre 15 et 30 secondes
            output_path="outputs/video_yt.mp4",
            excluded_themes=excluded_themes,    # Thèmes à exclure
            excluded_keywords=excluded_keywords,  # Mots-clés à exclure des métadonnées
            included_keywords=included_keywords  # Mots-clés à inclure (au moins un)
        )
        print(f"Vidéo téléchargée et traitée avec succès: {video_path}")
        
        # Exemple alternatif avec URL directe
        # video_path = download_video_by_theme(
        #     url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        #     duration_range=(10, 20),
        #     output_path="outputs/video_direct.mp4"
        # )
        
    except VideoDownloadError as e:
        print(f"Erreur lors du téléchargement: {e}")
    except Exception as e:
        print(f"Erreur inattendue: {e}")
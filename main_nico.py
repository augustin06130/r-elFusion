import os
import sys
from openai import OpenAI

# Import des modules personnalisés
from config import parse_arguments, CLIENT_ID_REDDIT, CLIENT_SECRET_REDDIT
from reddit_client import setup_reddit, get_reddit_content
from text_processor import clean_reddit_text, split_text_into_chunks, setup_nltk
from translator import translate_text_with_gpt, detect_language
from media_generator import process_video_from_text
from youtube_downloader import download_video_by_theme

# Import des modules de gestion d'erreurs
from handle_log_exception.logger import setup_logger, default_logger as logger
from handle_log_exception.exceptions import (
    RedditVideoError, ConfigError, RedditError,
    RedditConnectionError, RedditContentError,
    TranslationError, AudioError, VideoError
)


def main():
    """
    Fonction principale du programme

    Orchestre tout le processus de génération de vidéos à partir de posts Reddit
    """
    try:
        # Analyser les arguments
        logger.info("Analyse des arguments de la ligne de commande")
        try:
            args = parse_arguments()
            logger.debug(f"Arguments: {args}")
        except Exception as e:
            raise ConfigError(f"Erreur lors de l'analyse des arguments: {str(e)}") from e

        # Créer le dossier de sortie s'il n'existe pas
        try:
            os.makedirs(args.output_dir, exist_ok=True)
            logger.info(f"Dossier de sortie: {os.path.abspath(args.output_dir)}")
        except Exception as e:
            raise ConfigError(f"Impossible de créer le dossier de sortie {args.output_dir}: {str(e)}") from e

        # Vérifier la clé API OpenAI
        if not args.openai_api_key:
            raise ConfigError("Clé API OpenAI manquante. Utilisez --openai_api_key pour fournir votre clé.")

        # Initialiser le client OpenAI
        logger.info("Initialisation du client OpenAI")
        try:
            client = OpenAI(api_key=args.openai_api_key)
        except Exception as e:
            raise ConfigError(f"Erreur lors de l'initialisation du client OpenAI: {str(e)}") from e

        # Se connecter à Reddit
        logger.info("Connexion à l'API Reddit")
        try:
            reddit = setup_reddit(CLIENT_ID_REDDIT, CLIENT_SECRET_REDDIT)
            if not reddit:
                raise RedditConnectionError()
        except RedditConnectionError as e:
            raise
        except Exception as e:
            raise RedditConnectionError() from e

        # Récupérer le post
        logger.info(f"Recherche de posts dans r/{args.subreddit}")
        try:
            post_id, reddit_text, subreddit, title = get_reddit_content(
                reddit=reddit,
                openai_client=client,  # Le client OpenAI déjà configuré
                subreddit_name=args.subreddit,
                theme="horror",  # Optionnel, si args.subreddit n'est pas spécifié
                # keyword=args.keyword,  # Optionnel
                min_length=1000,  # Optionnel
                # max_length=10000  # Optionnel
            )
            if not post_id:
                raise RedditContentError(args.subreddit)

            logger.info(f"Post trouvé: {post_id} ({len(reddit_text)} caractères)")
        except RedditError as e:
            raise
        except Exception as e:
            raise RedditContentError(args.subreddit) from e

        # Nettoyer le texte
        logger.info("Nettoyage du texte récupéré")
        try:
            cleaned = clean_reddit_text(reddit_text)
            logger.debug(f"Texte nettoyé: {len(cleaned)} caractères")
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage du texte: {str(e)}")
            logger.warning("Utilisation du texte brut non nettoyé")
            cleaned = reddit_text


        try:
            source_language = detect_language(reddit_text, client, args.gpt_model)
            logger.debug(f"Langue détectée: {source_language}")

            if source_language == args.target_language:
                logger.info("Langue source identique à la langue cible. Pas de traduction nécessaire.")
            if args.target_language == "nt":  # No translation
                args.target_language = source_language
        except TranslationError:
            logger.warning("Détection de langue échouée. Tentative de traduction quand même.")


        if args.target_language != "nt": #Ne pas traduire si l'utilsateur ne choisit pas de langue cible
          # Traduire le texte avec GPT
            if source_language != args.target_language:
                logger.info(f"Traduction du texte avec le modèle {args.gpt_model}")
                try:
                    translated = translate_text_with_gpt(
                    text=cleaned,
                    client=client,
                    model=args.gpt_model,
                    max_tokens=4096,
                    source_language=source_language,
                    target_language=args.target_language,
                  )
                    logger.info(f"Traduction effectuée: {len(translated)} caractères")
                except Exception as e:
                    raise TranslationError(f"Erreur lors de la traduction avec GPT: {str(e)}") from e
            else:
                translated = cleaned
        else:
            translated = cleaned

        # Découper le texte en morceaux
        logger.info(f"Découpage du texte en segments de {args.chunk_size} mots")
        try:
            chunks = split_text_into_chunks(translated, args.chunk_size)
            if not chunks:
                raise RedditVideoError("Aucun segment généré après découpage.")

            logger.info(f"{len(chunks)} segments créés")
        except RedditVideoError as e:
            raise
        except Exception as e:
            raise RedditVideoError(f"Erreur lors du découpage du texte: {str(e)}") from e

        # Prévisualiser les segments
        for i, chunk in enumerate(chunks):
            word_count = len(chunk.split())
            preview = chunk[:150] + "..." if len(chunk) > 150 else chunk
            logger.info(f"Segment {i+1}/{len(chunks)} ({word_count} mots): {preview}")

        # Création des vidéos pour chaque segment
        success_count = 0
        failed_segments = []
        total_segments = len(chunks)

        try:
            # Définir les thèmes et mots-clés à exclure
            excluded_themes = ["violence"]
            excluded_keywords = ["violent"]

            # Définir les mots-clés à inclure (au moins un doit être présent)
            included_keywords = args.keywords_youtube
            included_themes = args.theme_youtube

            duration = (len(chunks) * 95) / 60

            # Télécharger une vidéo par thème avec exclusions et inclusions
            video_path = download_video_by_theme(
                theme=included_themes,          # Thème de recherche
                duration_range=(duration, duration * 2),        # Durée souhaitée entre 15 et 30 secondes
                output_path="outputs/video_yt.mp4",
                excluded_themes=excluded_themes,    # Thèmes à exclure
                excluded_keywords=excluded_keywords,  # Mots-clés à exclure des métadonnées
                included_keywords=included_keywords  # Mots-clés à inclure (au moins un)
            )
            print(f"Vidéo téléchargée et traitée avec succès: {video_path}")

        except VideoDownloadError as e:
            print(f"Erreur lors du téléchargement: {e}")
        except Exception as e:
            print(f"Erreur inattendue: {e}")

        for i, chunk in enumerate(chunks):
            segment_num = i + 1
            logger.info(f"Traitement du segment {segment_num}/{len(chunks)}")

            # Fichiers temporaires pour ce segment
            safe_title = ''.join(c if c.isalnum() else '_' for c in title[:20])  # Limiter et sécuriser le titre
            video_file = os.path.join(
                args.output_dir,
                f"video_{post_id}_{safe_title}_segment{segment_num}_{args.target_language}.mp4"
            )

            try:
                # Déterminer la langue pour la voix
                voice_language = args.target_language
                if voice_language == "nt":  # No translation
                    voice_language = "en"

                # Génération de la vidéo à partir du texte
                logger.info(f"Création de la vidéo pour le segment {segment_num}")
                success = process_video_from_text(
                    chunk,
                    video_path,
                    video_file,
                    voice_language,
                    add_subtitles=True,
                    segment_index=i,
                    total_segments=total_segments
                )

                if success:
                    success_count += 1
                    logger.info(f"Vidéo {segment_num} créée avec succès: {video_file}")
                else:
                    failed_segments.append(segment_num)
                    logger.error(f"Échec de la création de la vidéo pour le segment {segment_num}")

            except AudioError as e:
                failed_segments.append(segment_num)
                logger.error(f"Erreur audio pour le segment {segment_num}: {e}")
                continue

            except VideoError as e:
                failed_segments.append(segment_num)
                logger.error(f"Erreur vidéo pour le segment {segment_num}: {e}")
                continue

            except Exception as e:
                failed_segments.append(segment_num)
                logger.error(f"Erreur inattendue pour le segment {segment_num}: {e}")
                continue

        # Résumé final
        logger.info("=== RÉSUMÉ DE L'EXÉCUTION ===")
        logger.info(f"Post: {post_id}")
        logger.info(f"Modèle GPT utilisé: {args.gpt_model}")
        logger.info(f"Segments traités: {len(chunks)}")
        logger.info(f"Vidéos créées avec succès: {success_count}/{len(chunks)}")

        if failed_segments:
            logger.warning(f"Segments en échec: {', '.join(map(str, failed_segments))}")

        logger.info(f"Dossier de sortie: {os.path.abspath(args.output_dir)}")

        # Retourner un code d'erreur si certains segments ont échoué
        if failed_segments and len(failed_segments) == len(chunks):
            raise RedditVideoError("Tous les segments ont échoué lors de la génération des vidéos.")

        return success_count, len(chunks), os.path.abspath(args.output_dir)

    except ConfigError as e:
        logger.critical(f"Erreur de configuration: {e}")
        return None

    except RedditConnectionError as e:
        logger.critical(f"Erreur de connexion à Reddit: {e}")
        return None

    except RedditContentError as e:
        logger.critical(f"Erreur de contenu Reddit: {e}")
        return None

    except TranslationError as e:
        logger.critical(f"Erreur de traduction: {e}")
        return None

    except RedditVideoError as e:
        logger.critical(f"Erreur fatale: {e}")
        return None

    except Exception as e:
        logger.critical(f"Erreur non gérée: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    try:
        # Configuration initiale de NLTK
        setup_nltk()

        # Exécution du programme principal
        result = main()

        # Gestion du code de sortie
        if result is None:
            logger.critical("Le programme s'est terminé avec des erreurs")
            sys.exit(1)
        else:
            success_count, total_count, output_dir = result
            # Si certains segments ont échoué mais pas tous
            if success_count < total_count:
                logger.warning(f"Programme terminé avec des avertissements: {success_count}/{total_count} vidéos créées")
                sys.exit(0)  # On considère que c'est un succès partiel
            else:
                logger.info(f"Programme terminé avec succès: {success_count}/{total_count} vidéos créées")
                sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Programme interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Erreur critique non gérée: {e}", exc_info=True)
        sys.exit(1)

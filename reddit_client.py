import praw
from tqdm import tqdm

# Import des modules de gestion d'erreurs
from handle_log_exception.logger import setup_logger
from handle_log_exception.exceptions import RedditConnectionError, RedditContentError

# Création d'un logger spécifique pour ce module
logger = setup_logger("reddit_client")

def setup_reddit(client_id, client_secret):
    """
    Configure et retourne un client Reddit

    Args:
        client_id: ID client de l'API Reddit
        client_secret: Secret client de l'API Reddit

    Returns:
        Instance configurée du client Reddit

    Raises:
        RedditConnectionError: Si la connexion à Reddit échoue
    """
    if not client_id or not client_secret:
        logger.error("Identifiants Reddit manquants")
        raise RedditConnectionError("Client ID et Client Secret sont requis")

    try:
        logger.info("Tentative de connexion à l'API Reddit")
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent='script by /u/Bidiche49'
        )
        # Tester la connexion
        reddit.user.me()
        logger.info("Connexion à Reddit réussie")
        return reddit
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à l'API Reddit: {str(e)}")
        raise RedditConnectionError(f"Détails: {str(e)}")

def get_reddit_text(reddit, subreddit_name="nosleep", keyword="ghost", limit=20):
    """
    Recherche des posts Reddit selon un mot-clé et retourne le meilleur post

    Args:
        reddit: Instance du client Reddit
        subreddit_name: Nom du subreddit à explorer
        keyword: Mot-clé pour filtrer les posts
        limit: Nombre maximum de posts à vérifier

    Returns:
        tuple: (ID du post, texte du post)

    Raises:
        RedditContentError: Si aucun post correspondant n'est trouvé
    """
    try:
        logger.info(f"Recherche de posts dans r/{subreddit_name} avec le mot-clé '{keyword}'")
        subreddit = reddit.subreddit(subreddit_name)
        posts = []

        # Utiliser la barre de progression tqdm pour le suivi
        for post in tqdm(subreddit.hot(limit=limit), total=limit, desc="Analyse des posts"):
            text = (post.title + " " + post.selftext).lower()
            if keyword.lower() in text:
                posts.append({
                    "title": post.title,
                    "text": post.selftext,
                    "score": post.score,
                    "url": post.url,
                    "id": post.id
                })
                logger.debug(f"Post correspondant trouvé: {post.title} (Score: {post.score})")

        if not posts:
            logger.warning(f"Aucun post trouvé dans r/{subreddit_name} avec le mot-clé '{keyword}'")
            raise RedditContentError(subreddit_name, keyword)

        # Trier par score et prendre le meilleur
        posts.sort(key=lambda x: x["score"], reverse=True)
        best_post = posts[0]

        logger.info(f"Meilleur post trouvé: \"{best_post['title']}\" (Score: {best_post['score']})")
        return best_post["id"], best_post["title"] + ". " + best_post["text"]

    except RedditContentError:
        # Relancer les exceptions déjà typées
        raise
    except Exception as e:
        error_msg = f"Erreur lors de la recherche de posts: {str(e)}"
        logger.error(error_msg)
        raise RedditContentError(subreddit_name, keyword) from e

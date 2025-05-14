# import praw
# from tqdm import tqdm

# # Import des modules de gestion d'erreurs
# from handle_log_exception.logger import setup_logger
# from handle_log_exception.exceptions import RedditConnectionError, RedditContentError

# # Création d'un logger spécifique pour ce module
# logger = setup_logger("reddit_client")

# def setup_reddit(client_id, client_secret):
#     """
#     Configure et retourne un client Reddit

#     Args:
#         client_id: ID client de l'API Reddit
#         client_secret: Secret client de l'API Reddit

#     Returns:
#         Instance configurée du client Reddit

#     Raises:
#         RedditConnectionError: Si la connexion à Reddit échoue
#     """
#     if not client_id or not client_secret:
#         logger.error("Identifiants Reddit manquants")
#         raise RedditConnectionError("Client ID et Client Secret sont requis")

#     try:
#         logger.info("Tentative de connexion à l'API Reddit")
#         reddit = praw.Reddit(
#             client_id=client_id,
#             client_secret=client_secret,
#             user_agent='script by /u/Bidiche49'
#         )
#         # Tester la connexion
#         reddit.user.me()
#         logger.info("Connexion à Reddit réussie")
#         return reddit
#     except Exception as e:
#         logger.error(f"Erreur lors de la connexion à l'API Reddit: {str(e)}")
#         raise RedditConnectionError(f"Détails: {str(e)}")

# def get_reddit_content(reddit, subreddit_name="nosleep", keyword="ghost", limit=20):
#     """
#     Recherche des posts Reddit selon un mot-clé et retourne le meilleur post

#     Args:
#         reddit: Instance du client Reddit
#         subreddit_name: Nom du subreddit à explorer
#         keyword: Mot-clé pour filtrer les posts
#         limit: Nombre maximum de posts à vérifier

#     Returns:
#         tuple: (ID du post, texte du post)

#     Raises:
#         RedditContentError: Si aucun post correspondant n'est trouvé
#     """
#     try:
#         logger.info(f"Recherche de posts dans r/{subreddit_name} avec le mot-clé '{keyword}'")
#         subreddit = reddit.subreddit(subreddit_name)
#         posts = []

#         # Utiliser la barre de progression tqdm pour le suivi
#         for post in tqdm(subreddit.hot(limit=limit), total=limit, desc="Analyse des posts"):
#             text = (post.title + " " + post.selftext).lower()
#             if keyword.lower() in text:
#                 posts.append({
#                     "title": post.title,
#                     "text": post.selftext,
#                     "score": post.score,
#                     "url": post.url,
#                     "id": post.id
#                 })
#                 logger.debug(f"Post correspondant trouvé: {post.title} (Score: {post.score})")

#         if not posts:
#             logger.warning(f"Aucun post trouvé dans r/{subreddit_name} avec le mot-clé '{keyword}'")
#             raise RedditContentError(subreddit_name, keyword)

#         # Trier par score et prendre le meilleur
#         posts.sort(key=lambda x: x["score"], reverse=True)
#         best_post = posts[0]

#         logger.info(f"Meilleur post trouvé: \"{best_post['title']}\" (Score: {best_post['score']})")
#         return best_post["id"], best_post["title"] + ". " + best_post["text"]

#     except RedditContentError:
#         # Relancer les exceptions déjà typées
#         raise
#     except Exception as e:
#         error_msg = f"Erreur lors de la recherche de posts: {str(e)}"
#         logger.error(error_msg)
#         raise RedditContentError(subreddit_name, keyword) from e



import praw
from tqdm import tqdm
import random

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



def validate_content_with_gpt(text, openai_client):
    """
    Vérifie avec GPT-3.5-turbo si le contenu est une histoire ou un article intéressant

    Args:
        text: Texte du post Reddit
        openai_client: Client OpenAI configuré

    Returns:
        tuple: (est_valide, raison)
    """
    try:
        prompt = """
        Évalue si le texte suivant est une histoire narrative ou un article intéressant qui pourrait être lu et publié sur TikTok.
        Ne retiens PAS les textes qui sont principalement:
        - Des questions
        - Des demandes d'aide
        - Des recherches ou requêtes
        - Des sondages
        - Des discussions générales sans contenu narratif

        Réponds uniquement par "OUI" si c'est une histoire/article intéressant, ou "NON" suivi d'une courte raison si ce n'est pas le cas.

        Texte à évaluer:
        """

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant qui évalue le contenu."},
                {"role": "user", "content": prompt + text[:3000]}  # On limite pour économiser des tokens
            ],
            max_tokens=100
        )

        result = response.choices[0].message.content.strip()

        if result.startswith("OUI"):
            return True, "Contenu validé"
        else:
            reason = result[3:].strip() if result.startswith("NON") else result
            return False, reason

    except Exception as e:
        logger.error(f"Erreur lors de la validation avec GPT: {str(e)}")
        # En cas d'erreur, on accepte le contenu pour éviter de bloquer le processus
        return True, f"Erreur de validation: {str(e)}"

def get_theme_subreddits(theme):
    """
    Retourne une liste de subreddits correspondant au thème choisi

    Args:
        theme: Thème général (horror, history, actuality, etc.)

    Returns:
        Liste de noms de subreddits
    """
    theme_mapping = {
        "horror": ["nosleep", "shortscarystories", "creepypasta", "twosentencehorror", "horrorlit"],
        "history": ["history", "askhistorians", "historyanecdotes", "todayilearned", "ancientcivilizations"],
        "actuality": ["news", "worldnews", "politics", "science", "technology"],
        "gaming": ["gaming", "patientgamers", "truegaming", "gamedev", "pcgaming"],
        "science": ["science", "askscience", "futurology", "space", "physics"],
        "story": ["writingprompts", "lifeofnorman", "shortstories", "hfy", "lifestories"],
        "philosophy": ["philosophy", "stoicism", "existentialism", "badphilosophy", "askphilosophy"]
    }

    # Thème par défaut si non reconnu
    return theme_mapping.get(theme.lower(), ["bestof", "defaultdepth", "depthhub"])

def get_reddit_content(reddit, openai_client, subreddit_name=None, theme=None, keyword=None,
                     limit=50, min_length=None, max_length=None, max_attempts=5):
    """
    Recherche des posts Reddit selon un thème ou mot-clé et retourne un post validé par GPT

    Args:
        reddit: Instance du client Reddit
        openai_client: Client OpenAI configuré (déjà configuré dans main.py)
        subreddit_name: Nom du subreddit spécifique (prioritaire sur theme)
        theme: Thème général pour choisir des subreddits appropriés
        keyword: Mot-clé optionnel pour filtrer les posts
        limit: Nombre maximum de posts à vérifier par recherche
        min_length: Longueur minimale en caractères (optionnel)
        max_length: Longueur maximale en caractères (optionnel)
        max_attempts: Nombre maximal de tentatives pour trouver un contenu valide

    Returns:
        tuple: (ID du post, texte du post, subreddit, titre)

    Raises:
        RedditContentError: Si aucun post correspondant n'est trouvé après plusieurs tentatives
    """
    attempts = 0

    while attempts < max_attempts:
        attempts += 1
        logger.info(f"Tentative {attempts}/{max_attempts} de recherche de contenu")

        try:
            # Sélection du subreddit
            if subreddit_name:
                subreddits = [subreddit_name]
            elif theme:
                subreddits = get_theme_subreddits(theme)
                logger.info(f"Subreddits pour le thème '{theme}': {', '.join(subreddits)}")
            else:
                subreddits = ["bestof"]  # Valeur par défaut

            # Sélection aléatoire d'un subreddit dans la liste pour varier
            current_subreddit = random.choice(subreddits)
            logger.info(f"Recherche dans le subreddit: r/{current_subreddit}")

            subreddit = reddit.subreddit(current_subreddit)
            posts = []

            # Récupération des posts
            for post in tqdm(subreddit.hot(limit=limit), total=limit, desc=f"Analyse des posts de r/{current_subreddit}"):
                # Si le post est trop court, on passe
                full_text = post.selftext
                if min_length and len(full_text) < min_length:
                    logger.debug(f"Post ignoré car trop court: {len(full_text)} caractères < {min_length}")
                    continue

                # Si le post est trop long, on passe
                if max_length and len(full_text) > max_length:
                    logger.debug(f"Post ignoré car trop long: {len(full_text)} caractères > {max_length}")
                    continue

                # Si un mot-clé est spécifié, on vérifie sa présence
                if keyword:
                    text_to_search = (post.title + " " + full_text).lower()
                    if keyword.lower() not in text_to_search:
                        continue

                posts.append({
                    "title": post.title,
                    "text": full_text,
                    "score": post.score,
                    "url": post.url,
                    "id": post.id,
                    "subreddit": current_subreddit
                })
                logger.debug(f"Post potentiel trouvé: {post.title} (Score: {post.score})")

            if not posts:
                logger.warning(f"Aucun post correspondant trouvé dans r/{current_subreddit}")
                continue

            # Trier par score et vérifier les meilleurs
            posts.sort(key=lambda x: x["score"], reverse=True)

            for post in posts[:10]:  # On teste les 10 meilleurs posts
                logger.info(f"Validation du post: \"{post['title']}\" (Score: {post['score']})")

                is_valid, reason = validate_content_with_gpt(post["text"], openai_client)

                if is_valid:
                    logger.info(f"Post validé: \"{post['title']}\"")
                    return post["id"], post["text"], post["subreddit"], post["title"]
                else:
                    logger.info(f"Post rejeté: {reason}")

            logger.warning("Aucun post valide trouvé dans cette tentative")

        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            # On continue avec une autre tentative

    # Si on arrive ici, c'est qu'aucune tentative n'a abouti
    error_msg = f"Aucun contenu valide trouvé après {max_attempts} tentatives"
    logger.error(error_msg)
    raise RedditContentError(subreddit_name or theme, keyword, error_msg)


# Exemple d'utilisation:
if __name__ == "__main__":
    # Ces informations devraient être chargées depuis un fichier de configuration ou des variables d'environnement
    REDDIT_CLIENT_ID = "votre_client_id"
    REDDIT_CLIENT_SECRET = "votre_client_secret"

    try:
        # Configuration des clients
        from openai import OpenAI
        import os

        reddit = setup_reddit(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
        openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        # Recherche de contenu par thème
        post_id, content, subreddit, title = get_reddit_content(
            reddit=reddit,
            openai_client=openai_client,
            theme="horror",
            min_length=1000,
            max_length=10000
        )

        print(f"Post trouvé dans r/{subreddit}: {title}")
        print(f"ID: {post_id}")
        print(f"Longueur: {len(content)} caractères")
        print("\nDébut du contenu:")
        print(content[:500] + "...")

    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        print(f"Une erreur est survenue: {str(e)}")

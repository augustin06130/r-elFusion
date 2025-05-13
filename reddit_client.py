import praw
from tqdm import tqdm

def setup_reddit(client_id, client_secret):
    """
    Configure et retourne un client Reddit
    """
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent='script by /u/Bidiche49'
        )
        # Tester la connexion
        reddit.user.me()
        return reddit
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à l'API Reddit: {e}")
        return None

def get_reddit_text(reddit, subreddit_name="nosleep", keyword="ghost", limit=20):
    """
    Recherche des posts Reddit selon un mot-clé et retourne le meilleur post
    """
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = []

        print(f"🔍 Recherche de posts dans r/{subreddit_name} avec le mot-clé '{keyword}'...")
        for post in tqdm(subreddit.hot(limit=limit), total=limit):
            text = (post.title + " " + post.selftext).lower()
            if keyword.lower() in text:
                posts.append({
                    "title": post.title,
                    "text": post.selftext,
                    "score": post.score,
                    "url": post.url,
                    "id": post.id
                })

        if not posts:
            return None, "Pas trouvé."

        # Trier par score et prendre le meilleur
        posts.sort(key=lambda x: x["score"], reverse=True)
        best_post = posts[0]

        print(f"✅ Post trouvé: \"{best_post['title']}\" (Score: {best_post['score']})")
        return best_post["id"], best_post["title"] + ". " + best_post["text"]
    except Exception as e:
        print(f"❌ Erreur lors de la recherche de posts: {e}")
        return None, f"Erreur: {str(e)}"

import os
import argparse
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Récupérer les variables d'environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-3.5-turbo")
MAX_GPT_TOKEN = int(os.getenv("MAX_GPT_TOKEN", 4096))
GPT_RETRY_COUNT = int(os.getenv("GPT_RETRY_COUNT", 3))
GPT_WAIT_TIME = float(os.getenv("GPT_WAIT_TIME", 2.0))
CLIENT_ID_REDDIT = os.getenv("CLIENT_ID_REDDIT")
CLIENT_SECRET_REDDIT = os.getenv("CLIENT_SECRET_REDDIT")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Créer des reels vidéo à partir de posts Reddit")
    parser.add_argument("--subreddit", default="nosleep", help="Nom du subreddit à explorer")
    parser.add_argument("--keyword", default="the", help="Mot-clé pour rechercher des posts")
    parser.add_argument("--limit", type=int, default=20, help="Nombre de posts à vérifier")
    parser.add_argument("--chunk_size", type=int, default=200, help="Nombre de mots par segment vidéo")
    parser.add_argument("--background", default="video.mp4", help="Vidéo de fond à utiliser")
    parser.add_argument("--output_dir", default="output", help="Dossier pour les fichiers de sortie")
    parser.add_argument("--max_chars", type=int, default=3000,
                        help="Nombre maximum de caractères par chunk pour GPT")
    parser.add_argument("--openai_api_key", default=OPENAI_API_KEY,
                        help="Clé API OpenAI à utiliser")
    parser.add_argument("--gpt_model", default=GPT_MODEL,
                        help="Modèle GPT à utiliser (par défaut : gpt-3.5-turbo)")
    parser.add_argument("--target_language", default="nt",
                        help="Langue cible pour la traduction (code ISO 639-1, ex: 'fr', 'en')")
    parser.add_argument("--theme_youtube", default="Minecraft Parkour", help="Titre video youtube")
    parser.add_argument("--keywords_youtube", default="Minecraft Parkour", help="Mots dans la description d'une video youtube")

    return parser.parse_args()

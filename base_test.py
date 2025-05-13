import praw
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip
import os
import re
import math
from deep_translator import GoogleTranslator
from nltk.tokenize import sent_tokenize
import argparse
from tqdm import tqdm
import time
import sys
import random

# ---- 1. Configuration et arguments en ligne de commande ----
def parse_arguments():
    parser = argparse.ArgumentParser(description="Créer des reels vidéo à partir de posts Reddit")
    parser.add_argument("--subreddit", default="nosleep", help="Nom du subreddit à explorer")
    parser.add_argument("--keyword", default="ghost", help="Mot-clé pour rechercher des posts")
    parser.add_argument("--limit", type=int, default=20, help="Nombre de posts à vérifier")
    parser.add_argument("--chunk_size", type=int, default=200, help="Nombre de mots par segment vidéo")
    parser.add_argument("--background", default="fond.mp4", help="Vidéo de fond à utiliser")
    parser.add_argument("--output_dir", default="output", help="Dossier pour les fichiers de sortie")
    return parser.parse_args()

# ---- 2. Config Reddit API ----
def setup_reddit():
    try:
        reddit = praw.Reddit(
            client_id='_FHJq8hZqt_iIv37pOCy4g',
            client_secret='xoLqCTCT_YOV0altU8dl_KsA08Ja8g',
            user_agent='script by /u/Bidiche49'
        )
        # Tester la connexion
        reddit.user.me()
        return reddit
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à l'API Reddit: {e}")
        return None

# ---- 3. Chercher un post selon un mot-clé ----
def get_reddit_text(reddit, subreddit_name="nosleep", keyword="ghost", limit=20):
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

# ---- 4. Nettoyer le texte brut ----
def clean_reddit_text(raw_text):
    print("🧼 Nettoyage du texte...")
    # Supprimer les liens
    text = re.sub(r'\[.*?\]\(.*?\)', '', raw_text)  # markdown [xxx](url)
    text = re.sub(r'http\S+', '', text)             # liens bruts
    # Supprimer les mentions "Edit:", "TLDR", etc.
    text = re.sub(r'(?i)(edit|update|tl;dr|tldr):?.*$', '', text, flags=re.MULTILINE)
    # Supprimer les caractères spéciaux inutiles
    text = re.sub(r'\*+', '', text)
    # Supprimer les lignes vides multiples
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# ---- 5. Traduction automatique EN → FR ----
def translate_text_safely(text, chunk_size=500):
    print("🌐 Traduction en français...")

    # Découpe en phrases
    try:
        sentences = sent_tokenize(text)
    except LookupError:
        # Si l'erreur est due à punkt_tab manquant
        import nltk
        nltk.download('punkt')
        nltk.download('punkt_tab')
        sentences = sent_tokenize(text)

    chunks = []
    current_chunk = ""
    word_count = 0

    for sentence in sentences:
        words = sentence.split()
        if word_count + len(words) > chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            word_count = len(words)
        else:
            current_chunk += sentence + " "
            word_count += len(words)

    if current_chunk:
        chunks.append(current_chunk.strip())

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"  🌐 Traduction du bloc {i+1}/{len(chunks)}...")

        # Ajoutez des tentatives multiples avec délai
        max_retries = 3
        for attempt in range(max_retries):
            try:
                translated = GoogleTranslator(source='en', target='fr').translate(chunk)
                if translated:
                    translated_chunks.append(translated)
                    break
                else:
                    print(f"  ⚠️ Bloc {i+1}: Traduction vide, nouvelle tentative ({attempt+1}/{max_retries})")
                    time.sleep(2)  # Attendre avant de réessayer
            except Exception as e:
                print(f"  ⚠️ Erreur sur le bloc {i+1} (tentative {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)  # Attendre plus longtemps après une erreur
                else:
                    print(f"  ❌ Échec de la traduction du bloc {i+1} après {max_retries} tentatives")
                    # En cas d'échec, conserver le texte original
                    translated_chunks.append(chunk)

    return " ".join(translated_chunks)

# ---- 6. Découper en blocs avec fin logique ----
def split_text_into_chunks(text, words_per_chunk=200):
    print(f"✂️ Découpage du texte en segments d'environ {words_per_chunk} mots...")

    try:
        sentences = sent_tokenize(text)
    except LookupError:
        import nltk
        nltk.download('punkt')
        nltk.download('punkt_tab')
        sentences = sent_tokenize(text)

    chunks = []
    current_chunk = ""
    word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        if word_count + sentence_word_count > words_per_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            word_count = sentence_word_count
        else:
            current_chunk += sentence + " "
            word_count += sentence_word_count

    if current_chunk:
        chunks.append(current_chunk.strip())

    print(f"✅ {len(chunks)} segments créés")
    return chunks

# ---- 7. Convertir texte en audio ----
def text_to_speech(text, filename="voice.mp3", lang='fr'):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filename)
        return filename
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'audio: {e}")
        return None

# ---- 8. Ajouter voix sur fond vidéo ----
def create_video(audio_file, background_video="fond.mp4", output="output.mp4"):
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

# ---- 9. Pipeline principal ----
def main():
    # Analyser les arguments
    args = parse_arguments()

    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(args.output_dir, exist_ok=True)

    # Se connecter à Reddit
    reddit = setup_reddit()
    if not reddit:
        print("❌ Impossible de se connecter à Reddit. Vérifiez vos identifiants.")
        return

    # Récupérer le post
    post_id, reddit_text = get_reddit_text(reddit, args.subreddit, args.keyword, args.limit)
    if not post_id:
        print("❌ Aucun post trouvé correspondant aux critères.")
        return

    # Nettoyer le texte
    cleaned = clean_reddit_text(reddit_text)

    # Traduire le texte
    try:
        translated = translate_text_safely(cleaned)
    except Exception as e:
        print(f"❌ Erreur fatale lors de la traduction: {e}")
        return

    # Découper le texte en morceaux
    chunks = split_text_into_chunks(translated, args.chunk_size)
    if not chunks:
        print("❌ Aucun segment généré après découpage.")
        return

    # Prévisualiser les segments
    for i, chunk in enumerate(chunks):
        word_count = len(chunk.split())
        preview = chunk[:150] + "..." if len(chunk) > 150 else chunk
        print(f"\n--- Segment {i+1}/{len(chunks)} ({word_count} mots) ---")
        print(preview)

    # Création des vidéos pour chaque segment
    success_count = 0
    for i, chunk in enumerate(chunks):
        segment_num = i + 1
        print(f"\n=== Traitement du segment {segment_num}/{len(chunks)} ===")

        # Fichiers temporaires pour ce segment
        audio_file = os.path.join(args.output_dir, f"audio_{post_id}_{segment_num}.mp3")
        video_file = os.path.join(args.output_dir, f"video_{post_id}_{segment_num}.mp4")

        # Génération de l'audio
        print(f"🔊 Création de la voix pour le segment {segment_num}...")
        if not text_to_speech(chunk, audio_file):
            print(f"⚠️ Passé au segment suivant.")
            continue

        # Création de la vidéo
        if create_video(audio_file, args.background, video_file):
            success_count += 1
            print(f"✅ Vidéo {segment_num} créée: {video_file}")
        else:
            print(f"❌ Échec de la création de la vidéo {segment_num}")

    # Résumé final
    print(f"\n====== RÉSUMÉ ======")
    print(f"Post: {post_id}")
    print(f"Segments traités: {len(chunks)}")
    print(f"Vidéos créées avec succès: {success_count}")
    print(f"Dossier de sortie: {os.path.abspath(args.output_dir)}")
    print("===================")

if __name__ == "__main__":
    # Vérification des dépendances NLTK
    import nltk
    nltk.download('punkt')
    try:
        nltk.download('punkt_tab')
    except Exception as e:
        print(f"⚠️ Avertissement: {e}")
        print("Tentative de continuer malgré l'erreur...")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programme interrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur non gérée: {e}")
        sys.exit(1)

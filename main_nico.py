import os
import sys
from openai import OpenAI

# Import des modules personnalisés
from config import parse_arguments, CLIENT_ID_REDDIT, CLIENT_SECRET_REDDIT
from reddit_client import setup_reddit, get_reddit_text
from text_processor import clean_reddit_text, split_text_into_chunks, setup_nltk
from translator import translate_text_safely_gpt
from media_generator import text_to_speech, create_video

def main():
    # Analyser les arguments
    args = parse_arguments()

    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs(args.output_dir, exist_ok=True)

    # Initialiser le client OpenAI
    client = OpenAI(api_key=args.openai_api_key)

    # Se connecter à Reddit
    reddit = setup_reddit(CLIENT_ID_REDDIT, CLIENT_SECRET_REDDIT)
    if not reddit:
        print("❌ Impossible de se connecter à Reddit. Vérifiez vos identifiants.")
        return

    # Récupérer le post
    post_id, reddit_text = get_reddit_text(
        reddit,
        args.subreddit,
        args.keyword,
        args.limit
    )
    if not post_id:
        print("❌ Aucun post trouvé correspondant aux critères.")
        return

    # Nettoyer le texte
    cleaned = clean_reddit_text(reddit_text)

    # Traduire le texte avec GPT
    try:
        # Vérifier que la clé API est présente
        if not args.openai_api_key:
            print("❌ Clé API OpenAI manquante. Utilisez --openai_api_key pour fournir votre clé.")
            return

        translated = translate_text_safely_gpt(
            cleaned,
            client,
            args.gpt_model,
            max_tokens=4096,
            max_chars=args.max_chars
        )
    except Exception as e:
        print(f"❌ Erreur fatale lors de la traduction avec GPT: {e}")
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
    print(f"Modèle GPT utilisé: {args.gpt_model}")
    print(f"Segments traités: {len(chunks)}")
    print(f"Vidéos créées avec succès: {success_count}")
    print(f"Dossier de sortie: {os.path.abspath(args.output_dir)}")
    print("===================")

if __name__ == "__main__":
    # Configuration initiale de NLTK
    setup_nltk()

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programme interrompu par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur non gérée: {e}")
        sys.exit(1)

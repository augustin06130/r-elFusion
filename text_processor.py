import re
from nltk.tokenize import sent_tokenize
import nltk

def setup_nltk():
    """Télécharge les ressources NLTK nécessaires"""
    try:
        nltk.download('punkt')
        try:
            nltk.download('punkt_tab')
        except Exception as e:
            print(f"⚠️ Avertissement lors du téléchargement punkt_tab: {e}")
            print("Tentative de continuer malgré l'erreur...")
    except Exception as e:
        print(f"⚠️ Erreur lors du téléchargement des ressources NLTK: {e}")

def clean_reddit_text(raw_text):
    """
    Nettoie le texte brut d'un post Reddit
    """
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

def split_text_into_chunks(text, words_per_chunk=200):
    """
    Découpe le texte en segments avec une fin logique
    """
    print(f"✂️ Découpage du texte en segments d'environ {words_per_chunk} mots...")

    try:
        sentences = sent_tokenize(text)
    except LookupError:
        # Si les ressources ne sont pas déjà téléchargées
        setup_nltk()
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

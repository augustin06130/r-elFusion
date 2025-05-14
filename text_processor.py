import re
from nltk.tokenize import sent_tokenize
import nltk

# Import des modules de gestion d'erreurs
from handle_log_exception.logger import setup_logger
from handle_log_exception.exceptions import RedditVideoError

# Création d'un logger spécifique pour ce module
logger = setup_logger("text_processor")

def setup_nltk():
    """
    Télécharge les ressources NLTK nécessaires
    """
    try:
        logger.info("Configuration de NLTK")
        # Télécharger punkt pour la tokenisation de phrases
        nltk.download('punkt', quiet=True)
        try:
            nltk.download('punkt_tab', quiet=True)
        except Exception as e:
            logger.warning(f"Avertissement lors du téléchargement de punkt_tab: {e}")
            logger.warning("Tentative de continuer malgré l'erreur")
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de NLTK: {e}")
        logger.warning("Le découpage en phrases pourrait ne pas fonctionner correctement")

def clean_reddit_text(raw_text):
    """
    Nettoie le texte brut d'un post Reddit

    Args:
        raw_text: Texte brut du post Reddit

    Returns:
        str: Texte nettoyé
    """
    logger.info("Nettoyage du texte brut")

    try:
        # Enregistrer la longueur initiale pour statistiques
        initial_length = len(raw_text)

        # Supprimer les liens
        text = re.sub(r'\[.*?\]\(.*?\)', '', raw_text)  # markdown [xxx](url)
        text = re.sub(r'http\S+', '', text)             # liens bruts

        # Supprimer les mentions "Edit:", "TLDR", etc.
        text = re.sub(r'(?i)(edit|update|tl;dr|tldr):?.*$', '', text, flags=re.MULTILINE)

        # Supprimer les caractères spéciaux inutiles
        text = re.sub(r'\*+', '', text)

        # Supprimer les lignes vides multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)

        # Enregistrer la longueur finale pour statistiques
        final_length = len(text.strip())
        reduction = ((initial_length - final_length) / initial_length) * 100 if initial_length > 0 else 0

        logger.info(f"Texte nettoyé: {initial_length} → {final_length} caractères ({reduction:.1f}% de réduction)")

        return text.strip()
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage du texte: {str(e)}")
        # Retourner le texte original en cas d'erreur
        logger.warning("Utilisation du texte original non nettoyé")
        return raw_text

def split_text_into_chunks(text, words_per_chunk=200):
    """
    Découpe le texte en segments avec une fin logique

    Args:
        text: Texte à découper
        words_per_chunk: Nombre approximatif de mots par segment

    Returns:
        list: Liste des segments de texte
    """
    logger.info(f"Découpage du texte en segments d'environ {words_per_chunk} mots")

    if not text:
        logger.warning("Texte vide, impossible de créer des segments")
        return []

    try:
        # Tokenisation en phrases
        try:
            sentences = sent_tokenize(text)
        except LookupError:
            # Si les ressources ne sont pas déjà téléchargées
            logger.warning("Ressources NLTK manquantes, tentative de téléchargement")
            setup_nltk()
            sentences = sent_tokenize(text)

        logger.debug(f"{len(sentences)} phrases trouvées dans le texte")

        chunks = []
        current_chunk = ""
        word_count = 0

        for sentence in sentences:
            sentence_word_count = len(sentence.split())

            if word_count + sentence_word_count > words_per_chunk:
                # Le segment atteint la limite de mots, on le sauvegarde
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
                word_count = sentence_word_count
            else:
                # On ajoute la phrase au segment courant
                current_chunk += sentence + " "
                word_count += sentence_word_count

        # Ajouter le dernier segment s'il n'est pas vide
        if current_chunk:
            chunks.append(current_chunk.strip())

        # Statistiques
        total_words = sum(len(chunk.split()) for chunk in chunks)
        avg_words = total_words / len(chunks) if chunks else 0

        logger.info(f"{len(chunks)} segments créés (moyenne de {avg_words:.1f} mots par segment)")

        return chunks
    except Exception as e:
        logger.error(f"Erreur lors du découpage du texte: {str(e)}")
        # En cas d'erreur, retourner simplement le texte entier comme unique segment
        logger.warning("Création d'un seul segment avec tout le texte")
        return [text] if text else []

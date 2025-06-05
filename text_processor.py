# import re
# from nltk.tokenize import sent_tokenize
# import nltk

# # Import des modules de gestion d'erreurs
# from handle_log_exception.logger import setup_logger
# from handle_log_exception.exceptions import RedditVideoError

# # Création d'un logger spécifique pour ce module
# logger = setup_logger("text_processor")

# def setup_nltk():
#     """
#     Télécharge les ressources NLTK nécessaires
#     """
#     try:
#         logger.info("Configuration de NLTK")
#         # Télécharger punkt pour la tokenisation de phrases
#         nltk.download('punkt', quiet=True)
#         try:
#             nltk.download('punkt_tab', quiet=True)
#         except Exception as e:
#             logger.warning(f"Avertissement lors du téléchargement de punkt_tab: {e}")
#             logger.warning("Tentative de continuer malgré l'erreur")
#     except Exception as e:
#         logger.error(f"Erreur lors de la configuration de NLTK: {e}")
#         logger.warning("Le découpage en phrases pourrait ne pas fonctionner correctement")

# def clean_reddit_text(raw_text):
#     """
#     Nettoie le texte brut d'un post Reddit

#     Args:
#         raw_text: Texte brut du post Reddit

#     Returns:
#         str: Texte nettoyé
#     """
#     logger.info("Nettoyage du texte brut")

#     try:
#         # Enregistrer la longueur initiale pour statistiques
#         initial_length = len(raw_text)

#         # Supprimer les liens
#         text = re.sub(r'\[.*?\]\(.*?\)', '', raw_text)  # markdown [xxx](url)
#         text = re.sub(r'http\S+', '', text)             # liens bruts

#         # Supprimer les mentions "Edit:", "TLDR", etc.
#         text = re.sub(r'(?i)(edit|update|tl;dr|tldr):?.*$', '', text, flags=re.MULTILINE)

#         # Supprimer les caractères spéciaux inutiles
#         text = re.sub(r'\*+', '', text)

#         # Supprimer les lignes vides multiples
#         text = re.sub(r'\n\s*\n', '\n\n', text)

#         # Enregistrer la longueur finale pour statistiques
#         final_length = len(text.strip())
#         reduction = ((initial_length - final_length) / initial_length) * 100 if initial_length > 0 else 0

#         logger.info(f"Texte nettoyé: {initial_length} → {final_length} caractères ({reduction:.1f}% de réduction)")

#         return text.strip()
#     except Exception as e:
#         logger.error(f"Erreur lors du nettoyage du texte: {str(e)}")
#         # Retourner le texte original en cas d'erreur
#         logger.warning("Utilisation du texte original non nettoyé")
#         return raw_text

# def split_text_into_chunks(text, words_per_chunk=200):
#     """
#     Découpe le texte en segments avec une fin logique

#     Args:
#         text: Texte à découper
#         words_per_chunk: Nombre approximatif de mots par segment

#     Returns:
#         list: Liste des segments de texte
#     """
#     logger.info(f"Découpage du texte en segments d'environ {words_per_chunk} mots")

#     if not text:
#         logger.warning("Texte vide, impossible de créer des segments")
#         return []

#     try:
#         # Tokenisation en phrases
#         try:
#             sentences = sent_tokenize(text)
#         except LookupError:
#             # Si les ressources ne sont pas déjà téléchargées
#             logger.warning("Ressources NLTK manquantes, tentative de téléchargement")
#             setup_nltk()
#             sentences = sent_tokenize(text)

#         logger.debug(f"{len(sentences)} phrases trouvées dans le texte")

#         chunks = []
#         current_chunk = ""
#         word_count = 0

#         for sentence in sentences:
#             sentence_word_count = len(sentence.split())

#             if word_count + sentence_word_count > words_per_chunk:
#                 # Le segment atteint la limite de mots, on le sauvegarde
#                 chunks.append(current_chunk.strip())
#                 current_chunk = sentence + " "
#                 word_count = sentence_word_count
#             else:
#                 # On ajoute la phrase au segment courant
#                 current_chunk += sentence + " "
#                 word_count += sentence_word_count

#         # Ajouter le dernier segment s'il n'est pas vide
#         if current_chunk:
#             chunks.append(current_chunk.strip())

#         # Statistiques
#         total_words = sum(len(chunk.split()) for chunk in chunks)
#         avg_words = total_words / len(chunks) if chunks else 0

#         logger.info(f"{len(chunks)} segments créés (moyenne de {avg_words:.1f} mots par segment)")

#         return chunks
#     except Exception as e:
#         logger.error(f"Erreur lors du découpage du texte: {str(e)}")
#         # En cas d'erreur, retourner simplement le texte entier comme unique segment
#         logger.warning("Création d'un seul segment avec tout le texte")
#         return [text] if text else []






import re
from nltk.tokenize import sent_tokenize
import nltk
from openai import OpenAI

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

def optimize_text_for_tts(text, openai_client, model="gpt-3.5-turbo"):
    """
    Optimise le texte pour la synthèse vocale avec GPT

    Args:
        text: Texte à optimiser
        openai_client: Instance du client OpenAI
        model: Modèle GPT à utiliser (par défaut gpt-3.5-turbo)

    Returns:
        str: Texte optimisé pour TTS
    """
    logger.info(f"Optimisation du texte pour TTS avec {model}")

    if not text:
        logger.warning("Texte vide, rien à optimiser")
        return text

    try:
        # Prompt pour optimiser le texte pour TTS
        system_prompt = """
You are an expert in voice narration and speech synthesis. Your task is to transform a given text into a version that sounds fluid, natural, and expressive when read aloud by a TTS engine, especially XTTSv2.

Follow these rules carefully and adapt them based on the emotional and narrative context of the input:

🔹 1. Improve Vocal Flow
- Restructure long or complex sentences into simpler, more breathable units.
- Use commas or ellipses (...) to create natural pauses.
- Split ideas across lines or sentences if that helps rhythm.
- Avoid run-on sentences that feel flat or rushed when spoken.

🔹 2. Handle Short Phrases Intelligently
- If the text includes very short lines like "Footsteps." or "Darkness.":
- If the context is tense, scary, emotional, extend them slightly for dramatic impact:
    Example: "Footsteps..." becomes: "Footsteps... heavy ones. Just outside the door."
- If the context is neutral, you can leave them unchanged or lightly rephrase them.

🔹 3. Clean Formatting
- Remove characters that break XTTSv2 reading, such as:
*asterisks*, [...], smart quotes like « », or weird brackets.
- Use simple narrative dialogue structure:
- Use — or write: He said: before a line of dialogue.

🔹 4. Clarify Dialogue
- Clearly indicate when someone speaks.
- If tone matters, add brief cues like he whispered, she shouted, he said calmly.

🔹 5. Emphasize Rhythm & Emotion
- Use ellipses (...) or soft sentence breaks to create suspense, fear, doubt, or hesitation.
- Convert overly literary phrases into casual or realistic speech patterns.
- Avoid passive voice and generic phrasing when more emotional alternatives exist.

🔹 6. Make It Sound Spoken — Not Written
- Rewrite overly formal or written phrases into how a real person would speak aloud.
Example:
❌ "It is at this precise moment I understood everything."
✅ "That's when it hit me."

🔹 7. Language Flexibility
- Apply all the same vocal flow rules whether the input is in English, French, or any other language.
- Adjust punctuation and sentence structure accordingly, without doing literal translation.

🎯 Final goal:
Return a version of the input text that sounds clean, natural, and emotionally expressive when read by a speech model like XTTSv2 — avoiding robotic pacing, weird pauses, and unnatural phrasing.

Output only the cleaned/adapted text — no commentary, no explanation."""

        # Diviser le texte en morceaux si nécessaire (limite de tokens GPT)
        max_chars = 3000  # Limite sécuritaire pour éviter de dépasser les limites de tokens

        if len(text) > max_chars:
            logger.info(f"Texte trop long ({len(text)} caractères), division en morceaux")

            # Diviser intelligemment par paragraphes ou phrases
            chunks = []
            current_chunk = ""

            # Essayer de diviser par paragraphes d'abord
            paragraphs = text.split('\n\n')

            for para in paragraphs:
                if len(current_chunk) + len(para) + 2 < max_chars:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"

            if current_chunk:
                chunks.append(current_chunk.strip())

            # Traiter chaque morceau
            optimized_chunks = []
            for i, chunk in enumerate(chunks):
                logger.debug(f"Traitement du morceau {i+1}/{len(chunks)}")

                response = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": chunk}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )

                optimized_chunk = response.choices[0].message.content.strip()
                optimized_chunks.append(optimized_chunk)

            # Rejoindre les morceaux optimisés
            optimized_text = "\n\n".join(optimized_chunks)

        else:
            # Texte assez court pour être traité en une fois
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            optimized_text = response.choices[0].message.content.strip()

        # Statistiques
        initial_length = len(text)
        final_length = len(optimized_text)
        change_percent = abs((final_length - initial_length) / initial_length) * 100 if initial_length > 0 else 0

        logger.info(f"Texte optimisé pour TTS: {initial_length} → {final_length} caractères ({change_percent:.1f}% de changement)")

        return optimized_text

    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation TTS: {str(e)}")
        logger.warning("Utilisation du texte non optimisé")
        return text

def process_text_for_tts(raw_text, openai_client=None, model="gpt-3.5-turbo", optimize_for_tts=True):
    """
    Fonction wrapper qui nettoie et optimise le texte pour TTS

    Args:
        raw_text: Texte brut à traiter
        openai_client: Instance du client OpenAI (optionnel si optimize_for_tts=False)
        model: Modèle GPT à utiliser
        optimize_for_tts: Si True, applique l'optimisation TTS après le nettoyage

    Returns:
        str: Texte traité et prêt pour TTS
    """
    logger.info("Traitement du texte pour TTS")

    # Étape 1: Nettoyer le texte Reddit
    cleaned_text = clean_reddit_text(raw_text)

    # Étape 2: Optimiser pour TTS si demandé et si le client OpenAI est fourni
    if optimize_for_tts and openai_client:
        try:
            optimized_text = optimize_text_for_tts(cleaned_text, openai_client, model)
            return optimized_text
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation TTS, utilisation du texte nettoyé: {e}")
            return cleaned_text
    else:
        if optimize_for_tts and not openai_client:
            logger.warning("Optimisation TTS demandée mais client OpenAI non fourni")
        return cleaned_text

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

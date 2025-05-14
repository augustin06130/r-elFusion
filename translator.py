import re
import time
from openai import OpenAI

# Import des modules de gestion d'erreurs
from handle_log_exception.logger import setup_logger
from handle_log_exception.exceptions import TranslationError

# Création d'un logger spécifique pour ce module
logger = setup_logger("translator")


def detect_language(text, client, model="gpt-3.5-turbo"):
    """
    Utilise GPT pour détecter la langue du texte fourni.

    Args:
        text: Texte à analyser
        client: Client OpenAI
        model: Modèle GPT à utiliser

    Returns:
        str: Code langue détectée (ex: 'fr', 'en')
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Tu es un assistant qui détecte la langue d'un texte. Réponds uniquement avec le code ISO 639-1 de la langue (ex: fr, en, es, etc.)."},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=5,
            timeout=30
        )
        language = response.choices[0].message.content.strip().lower()
        if re.match(r"^[a-z]{2}$", language):
            return language
        else:
            raise ValueError(f"Code langue inattendu : {language}")
    except Exception as e:
        logger.error(f"Erreur lors de la détection de la langue : {e}")
        raise TranslationError(f"Erreur détection langue: {e}")


def translate_text_with_gpt(text, client, model, max_tokens, target_language, source_language="en", retry_count=3, wait_time=2):
    """
    Traduit un texte d'une langue source détectée vers une langue cible avec GPT.
    Ignore la traduction si la langue source est identique à la langue cible.

    Args:
        text: Texte à traduire
        client: Client OpenAI
        model: Modèle GPT à utiliser
        max_tokens: Nombre maximal de tokens pour la réponse
        target_language: Langue cible (code ISO 639-1, ex: 'fr', 'en')
        retry_count: Nombre de tentatives en cas d'échec
        wait_time: Temps d'attente entre les tentatives

    Returns:
        str: Texte traduit ou original si la traduction n'est pas nécessaire

    Raises:
        TranslationError: Si la traduction échoue après toutes les tentatives
    """
    # if target_language == "nt": #Ne pas traduire si l'utilsateur ne choisit pas de langue cible
    #     return text
    # try:
    #     source_language = detect_language(text, client, model)
    #     logger.debug(f"Langue détectée: {source_language}")

    # if source_language == target_language:
    #     logger.info("Langue source identique à la langue cible. Pas de traduction nécessaire.")
    #     return text

    # except TranslationError:
    #     logger.warning("Détection de langue échouée. Tentative de traduction quand même.")

    prompt = f"Tu es un expert en traduction depuis 20 ans. Traduis le texte suivant de manière naturelle et fidèle à l’intention de l’auteur. Traduis de {source_language.upper()} vers {target_language.upper()}."

    current_wait = wait_time
    last_error = None

    for attempt in range(retry_count):
        try:
            logger.debug(f"Tentative de traduction {attempt+1}/{retry_count}")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                timeout=120
            )

            translated_text = response.choices[0].message.content.strip()

            if translated_text:
                logger.debug("Traduction réussie")
                return translated_text
            else:
                logger.warning(f"Réponse vide reçue (tentative {attempt+1}/{retry_count})")
                last_error = "Réponse vide de l'API"

        except Exception as e:
            logger.warning(f"Erreur lors de la traduction GPT: {str(e)} (tentative {attempt+1}/{retry_count})")
            last_error = str(e)

        if attempt < retry_count - 1:
            logger.debug(f"Nouvelle tentative dans {current_wait}s")
            time.sleep(current_wait)
            current_wait *= 2

    raise TranslationError(f"Échec de traduction après {retry_count} tentatives: {last_error}")

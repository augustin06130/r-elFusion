import re
import time
from openai import OpenAI

def translate_text_with_gpt(text, client, model, max_tokens, retry_count=3, wait_time=2):
    """
    Traduit un texte anglais en français en utilisant l'API GPT.
    Inclut des mécanismes de retry en cas d'échec.
    """
    prompt = "Tu es un expert de la traduction anglo-française avec 20 ans d'expérience. Traduis le texte suivant de l'anglais vers le français de la manière la plus fluide possible, en évitant une traduction littérale. Comprends bien le contexte pour produire une traduction naturelle et fidèle à l'intention de l'auteur."

    for attempt in range(retry_count):
        try:
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
                return translated_text
            else:
                print(f"⚠️ Réponse vide reçue (tentative {attempt+1}/{retry_count})")

        except Exception as e:
            print(f"⚠️ Erreur lors de la traduction GPT: {e} (tentative {attempt+1}/{retry_count})")

        # Attente avant retry
        if attempt < retry_count - 1:
            print(f"⏳ Attente de {wait_time} secondes avant nouvelle tentative...")
            time.sleep(wait_time)
            wait_time *= 1.5

    # En cas d'échec après toutes les tentatives
    print("❌ Échec de la traduction GPT après plusieurs tentatives")
    return text  # Retourner le texte original en cas d'échec complet

def translate_text_safely_gpt(text, client, model, max_tokens, max_chars=3000):
    """
    Traduit un texte long en le découpant en morceaux pour l'API GPT.
    Affiche la progression et chaque morceau traduit.
    """
    print(f"🌐 Traduction du texte en français avec GPT ({model})...")

    # Découpe le texte en blocs sans couper au milieu des phrases
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""

    # Créer les chunks
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    # Ajouter le dernier chunk s'il contient du texte
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    print(f"  🧩 Le texte a été divisé en {len(chunks)} morceaux pour la traduction")

    # Traduire chaque chunk avec indication de progression
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_number = i + 1
        print(f"\n  🔄 Traduction du morceau {chunk_number}/{len(chunks)} ({len(chunk)} caractères)...")

        # Afficher un aperçu du texte à traduire
        preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
        print(f"  📝 Texte source: {preview}")

        # Traduire le morceau
        translated = translate_text_with_gpt(chunk, client, model, max_tokens)

        # Afficher un aperçu de la traduction
        translated_preview = translated[:100] + "..." if len(translated) > 100 else translated
        print(f"  🇫🇷 Traduction: {translated_preview}")

        translated_chunks.append(translated)

    # Assembler tous les morceaux traduits
    full_translation = " ".join(translated_chunks)
    print(f"\n✅ Traduction terminée ({len(full_translation)} caractères)")

    return full_translation

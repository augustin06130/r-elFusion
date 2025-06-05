from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import time
from TTS.api import TTS
import torch
import json
import logging
import traceback

# Configuration
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Dossiers
AUDIO_OUTPUT = "/app/audio_output"
AUDIO_INPUT = "/app/audio_input"
MODELS_DIR = "/app/models"

# Créer les dossiers s'ils n'existent pas
os.makedirs(AUDIO_OUTPUT, exist_ok=True)
os.makedirs(AUDIO_INPUT, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# Variable globale pour le modèle
tts_model = None

def init_tts():
    """Initialise le modèle TTS"""
    global tts_model
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Utilisation du device: {device}")
        logging.info("Chargement du modèle XTTS v2...")

        # Définir le cache des modèles
        os.environ['TTS_HOME'] = MODELS_DIR

        # tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        tts_model = TTS("xtts-v2-model").to(device)
        logging.info("✓ Modèle chargé avec succès")
        return True
    except Exception as e:
        logging.error(f"Erreur lors du chargement du modèle: {e}")
        logging.error(traceback.format_exc())
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Vérification de santé du service"""
    return jsonify({
        "status": "healthy" if tts_model is not None else "unhealthy",
        "service": "tts-service",
        "model_loaded": tts_model is not None,
        "version": "1.0.0"
    })

@app.route('/generate', methods=['POST'])
def generate_speech():
    """
    Génère un fichier audio à partir du texte

    Body JSON:
    {
        "text": "Texte à synthétiser",
        "language": "fr",  # fr, en, es, de, etc.
        "speaker_wav": "filename.wav"  # Optionnel, pour clonage vocal
    }
    """
    try:
        # Vérifier que le modèle est chargé
        if tts_model is None:
            return jsonify({
                "error": "Model not loaded",
                "message": "Le modèle TTS n'est pas encore chargé. Veuillez réessayer dans quelques instants."
            }), 503

        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        text = data.get('text', '').strip()
        language = data.get('language', 'fr').lower()
        speaker_wav = data.get('speaker_wav')

        # Validation des entrées
        if not text:
            return jsonify({"error": "Text is required", "message": "Le texte ne peut pas être vide"}), 400

        if len(text) > 5000:  # Limite de sécurité
            return jsonify({"error": "Text too long", "message": "Le texte ne doit pas dépasser 5000 caractères"}), 400

        # Validation de la langue
        supported_languages = ['fr', 'en', 'es', 'de', 'it', 'pt', 'pl', 'tr', 'ru', 'nl', 'cs', 'ar', 'zh-cn']
        if language not in supported_languages:
            return jsonify({
                "error": "Unsupported language",
                "message": f"Langue '{language}' non supportée",
                "supported_languages": supported_languages
            }), 400

        # Générer un nom de fichier unique
        output_filename = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(AUDIO_OUTPUT, output_filename)

        # Log de la requête
        logging.info(f"Génération TTS - Langue: {language}, Texte: {len(text)} caractères")

        # Mesurer le temps
        start_time = time.time()

        # Générer l'audio
        if speaker_wav and os.path.exists(os.path.join(AUDIO_INPUT, speaker_wav)):
            # Avec clonage vocal
            logging.info(f"Utilisation du clonage vocal avec: {speaker_wav}")
            tts_model.tts_to_file(
                text=text,
                speaker_wav=os.path.join(AUDIO_INPUT, speaker_wav),
                language=language,
                file_path=output_path
            )
        else:
            # Voix par défaut
            logging.info("Utilisation de la voix par défaut")
            # Pour XTTS v2, on peut utiliser une voix par défaut
            tts_model.tts_to_file(
                text=text,
                speaker=tts_model.speakers[0] if hasattr(tts_model, 'speakers') and tts_model.speakers else None,
                language=language,
                file_path=output_path
            )

        generation_time = time.time() - start_time

        # Obtenir la durée de l'audio de manière plus robuste
        try:
            import wave
            with wave.open(output_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
        except Exception as e:
            logging.warning(f"Impossible de lire la durée du fichier WAV: {e}")
            duration = 0

        file_size = os.path.getsize(output_path)
        logging.info(f"✓ Audio généré: {output_filename} ({file_size/1024:.1f} KB, {duration:.2f}s)")

        return jsonify({
            "success": True,
            "filename": output_filename,
            "generation_time": round(generation_time, 2),
            "audio_duration": round(duration, 2),
            "realtime_factor": round(generation_time / duration, 2) if duration > 0 else 0,
            "file_size_kb": round(file_size / 1024, 1)
        })

    except Exception as e:
        logging.error(f"Erreur lors de la génération: {e}")
        logging.error(traceback.format_exc())

        # Retourner une erreur plus descriptive
        error_message = str(e)
        if "CUDA" in error_message:
            error_message = "Erreur GPU. Le service fonctionne en mode CPU."
        elif "memory" in error_message.lower():
            error_message = "Mémoire insuffisante pour traiter cette requête"

        return jsonify({
            "error": "Generation failed",
            "message": error_message,
            "details": str(e) if app.debug else None
        }), 500

@app.route('/download/<filename>', methods=['GET'])
def download_audio(filename):
    """Télécharge un fichier audio généré"""
    try:
        # Sécurité : s'assurer que le filename ne contient pas de path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({"error": "Invalid filename"}), 400

        file_path = os.path.join(AUDIO_OUTPUT, filename)
        if os.path.exists(file_path):
            # Optionnel : nettoyer les vieux fichiers (plus de 1 heure)
            cleanup_old_files()

            return send_file(
                file_path,
                as_attachment=True,
                mimetype='audio/wav',
                download_name=filename
            )
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/batch', methods=['POST'])
def batch_generate():
    """
    Génère plusieurs audios en batch

    Body JSON:
    {
        "items": [
            {"text": "...", "language": "fr"},
            {"text": "...", "language": "en"}
        ]
    }
    """
    try:
        if tts_model is None:
            return jsonify({"error": "Model not loaded"}), 503

        data = request.json
        items = data.get('items', [])

        if not items:
            return jsonify({"error": "Items list is required"}), 400

        if len(items) > 10:  # Limite pour éviter la surcharge
            return jsonify({"error": "Too many items", "message": "Maximum 10 items par batch"}), 400

        results = []
        errors = []
        total_start = time.time()

        for idx, item in enumerate(items):
            text = item.get('text', '').strip()
            language = item.get('language', 'fr').lower()

            if not text:
                errors.append({
                    "index": idx,
                    "error": "Empty text"
                })
                continue

            try:
                output_filename = f"{uuid.uuid4()}.wav"
                output_path = os.path.join(AUDIO_OUTPUT, output_filename)

                tts_model.tts_to_file(
                    text=text,
                    language=language,
                    file_path=output_path
                )

                results.append({
                    "index": idx,
                    "filename": output_filename,
                    "text_preview": text[:50] + "..." if len(text) > 50 else text,
                    "language": language
                })
            except Exception as e:
                logging.error(f"Erreur batch item {idx}: {e}")
                errors.append({
                    "index": idx,
                    "error": str(e)
                })

        total_time = time.time() - total_start

        return jsonify({
            "success": True,
            "count": len(results),
            "errors_count": len(errors),
            "total_time": round(total_time, 2),
            "results": results,
            "errors": errors if errors else None
        })

    except Exception as e:
        logging.error(f"Erreur batch: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/languages', methods=['GET'])
def get_languages():
    """Retourne les langues supportées"""
    return jsonify({
        "languages": {
            "fr": "Français",
            "en": "English",
            "es": "Español",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "pl": "Polski",
            "tr": "Türkçe",
            "ru": "Русский",
            "nl": "Nederlands",
            "cs": "Čeština",
            "ar": "العربية",
            "zh-cn": "中文"
        },
        "default": "fr"
    })

@app.route('/info', methods=['GET'])
def get_info():
    """Retourne les informations sur le service"""
    return jsonify({
        "service": "XTTS-v2 TTS Service",
        "version": "1.0.0",
        "model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "status": "running" if tts_model is not None else "loading",
        "features": {
            "text_to_speech": True,
            "voice_cloning": True,
            "batch_processing": True,
            "multilingual": True
        },
        "limits": {
            "max_text_length": 5000,
            "max_batch_size": 10,
            "supported_audio_format": "wav"
        }
    })

def cleanup_old_files():
    """Nettoie les fichiers audio de plus d'une heure"""
    try:
        current_time = time.time()
        for filename in os.listdir(AUDIO_OUTPUT):
            file_path = os.path.join(AUDIO_OUTPUT, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > 3600:  # 1 heure
                    os.remove(file_path)
                    logging.debug(f"Fichier supprimé: {filename}")
    except Exception as e:
        logging.warning(f"Erreur lors du nettoyage: {e}")

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Erreur interne: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialiser le modèle au démarrage
    if init_tts():
        # Nettoyer les vieux fichiers au démarrage
        cleanup_old_files()

        # Configuration du serveur
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'

        logging.info(f"Démarrage du serveur sur le port {port}")
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        logging.error("Impossible de démarrer le service - échec du chargement du modèle")
        exit(1)

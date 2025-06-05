import requests
import os
import json
import time

# Configuration
API_URL = "http://localhost:5001"

def test_single_generation():
	"""Test de génération simple"""
	print("=== Test génération simple ===")

	file_path = "text.txt"

	try:
		if not os.path.isfile(file_path):
			raise FileNotFoundError(f"Le fichier '{file_path}' est introuvable.")

		with open(file_path, "r", encoding="utf-8") as file:
			texte = file.read().strip()

		data = {
			"text": texte,
			"language": "fr"
		}

	except FileNotFoundError as e:
		print(f"Erreur : {e}")
		return None
	except IOError as e:
		print(f"Erreur de lecture du fichier : {e}")
		return None
	except Exception as e:
		print(f"Une erreur inattendue est survenue : {e}")
		return None

	response = requests.post(f"{API_URL}/generate", json=data)

	if response.status_code == 200:
		result = response.json()
		print(f"✓ Audio généré: {result['filename']}")
		print(f"  Temps: {result['generation_time']}s")
		print(f"  Durée audio: {result['audio_duration']}s")
		print(f"  Facteur temps réel: {result['realtime_factor']}x")

		# Télécharger le fichier
		audio_response = requests.get(f"{API_URL}/download/{result['filename']}")
		with open(f"test_output_{result['filename']}", 'wb') as f:
			f.write(audio_response.content)
		print(f"✓ Fichier téléchargé: test_output_{result['filename']}")
		return result['filename']
	else:
		print(f"✗ Erreur: {response.text}")
		return None

def test_batch_generation():
	"""Test de génération en batch"""
	print("\n=== Test génération batch ===")

	data = {
		"items": [
			{"text": "Premier texte en français.", "language": "fr"},
			{"text": "Second text in English.", "language": "en"},
			{"text": "Tercer texto en español.", "language": "es"}
		]
	}

	response = requests.post(f"{API_URL}/batch", json=data)

	if response.status_code == 200:
		result = response.json()
		print(f"✓ {result['count']} audios générés en {result['total_time']}s")
		for item in result['results']:
			print(f"  - {item['filename']}: {item['text_preview']}")
	else:
		print(f"✗ Erreur: {response.text}")

def test_languages():
	"""Test récupération des langues"""
	print("\n=== Langues supportées ===")
	response = requests.get(f"{API_URL}/languages")
	if response.status_code == 200:
		languages = response.json()['languages']
		for code, name in languages.items():
			print(f"  {code}: {name}")

def play_audio_on_mac(filename):
	"""Joue l'audio sur macOS"""
	try:
		import subprocess
		subprocess.run(["afplay", filename])
		print(f"♪ Audio joué: {filename}")
	except:
		print(f"ℹ️  Pour écouter l'audio: afplay {filename}")

if __name__ == "__main__":
	# Vérifier que le service est disponible
	try:
		health = requests.get(f"{API_URL}/health")
		if health.json()['status'] == 'healthy':
			print("✓ Service TTS opérationnel\n")

			# Test simple
			filename = test_single_generation()

			# Test batch
			test_batch_generation()

			# Test langues
			test_languages()

			# Jouer l'audio généré
			if filename:
				print("\n=== Lecture audio ===")
				play_audio_on_mac(f"test_output_{filename}")

		else:
			print("✗ Service non prêt")
	except requests.exceptions.ConnectionError:
		print("✗ Impossible de se connecter au service TTS")
		print("  Assurez-vous que Docker est lancé avec: docker-compose up")

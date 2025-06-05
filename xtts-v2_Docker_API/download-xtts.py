from huggingface_hub import snapshot_download
import os

model_dir = "xtts-v2-model"

if not os.path.isdir(model_dir):
	print("Téléchargement du modèle XTTS depuis Hugging Face...")
	snapshot_download(
		repo_id="Bidiche/xtts-v2-model",
		repo_type="model",
		local_dir=model_dir,
		local_dir_use_symlinks=False
	)
	print("Modèle téléchargé dans:", model_dir)
else:
	print("Modèle déjà présent.")

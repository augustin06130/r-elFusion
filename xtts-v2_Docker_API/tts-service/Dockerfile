# Image de base avec Python 3.10
FROM python:3.10-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Créer les dossiers nécessaires
RUN mkdir -p /app/models /app/audio_output /app/audio_input

# Copier l'application
COPY app.py .

# Exposer le port pour l'API
EXPOSE 5000

# Variables d'environnement
ENV CUDA_VISIBLE_DEVICES=""
ENV COQUI_TOS_AGREED="1"

# Commande de démarrage
CMD ["python", "app.py"]

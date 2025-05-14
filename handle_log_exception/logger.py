import logging
import os
from datetime import datetime
logging.getLogger("imageio_ffmpeg").setLevel(logging.WARNING)


def setup_logger(name, level=logging.INFO, log_to_file=True, log_dir="logs"):
    """
    Configure et retourne un logger avec console et fichier

    Args:
        name: Nom du logger (généralement nom du module)
        level: Niveau de journalisation
        log_to_file: Si True, journalise également dans un fichier
        log_dir: Dossier où stocker les fichiers de log

    Returns:
        Logger configuré
    """
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Éviter la duplication des logs

    # Éviter d'ajouter des handlers en double si le logger existe déjà
    if logger.handlers:
        return logger

    # Format de log détaillé pour le débogage
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )

    # Handler pour la console avec émojis pour meilleure lisibilité
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(EmojiFormatter())
    logger.addHandler(console_handler)

    # Handler pour fichier si demandé
    if log_to_file:
        try:
            # Créer le dossier de logs s'il n'existe pas
            os.makedirs(log_dir, exist_ok=True)

            # Nom du fichier avec date
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(log_dir, f"{date_str}_{name}.log")

            # Ajouter handler de fichier
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # Plus détaillé dans le fichier
            logger.addHandler(file_handler)
        except Exception as e:
            # Ne pas planter si impossible de créer le fichier de log
            console_handler.setLevel(logging.WARNING)
            logger.warning(f"Impossible de configurer la journalisation dans un fichier: {e}")

    return logger

class EmojiFormatter(logging.Formatter):
    """Formatter qui ajoute des émojis aux messages de log"""

    FORMATS = {
        logging.DEBUG: '🔍 %(message)s',
        logging.INFO: '✅ %(message)s',
        logging.WARNING: '⚠️ %(message)s',
        logging.ERROR: '❌ %(message)s',
        logging.CRITICAL: '🔥 %(message)s'
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, '%(message)s')
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Logger par défaut pour les imports directs
default_logger = setup_logger("reddit_video")

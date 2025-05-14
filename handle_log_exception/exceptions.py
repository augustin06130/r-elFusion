class RedditVideoError(Exception):
    """Classe de base pour toutes les exceptions de l'application"""
    pass


class ConfigError(RedditVideoError):
    """Erreurs liées à la configuration"""
    pass


class RedditError(RedditVideoError):
    """Erreurs liées à l'API Reddit"""

    def __init__(self, message="Erreur lors de l'accès à Reddit", status_code=None, *args):
        self.status_code = status_code
        self.message = message
        super().__init__(message, *args)

    def __str__(self):
        if self.status_code:
            return f"{self.message} (Code: {self.status_code})"
        return self.message


class RedditConnectionError(RedditError):
    """Erreur de connexion à l'API Reddit"""
    def __init__(self, *args):
        super().__init__("Impossible de se connecter à l'API Reddit", *args)


class RedditContentError(RedditError):
    """Erreur liée au contenu non trouvé sur Reddit"""
    def __init__(self, subreddit=None, keyword=None, *args):
        message = "Contenu introuvable sur Reddit"
        if subreddit and keyword:
            message = f"Aucun post trouvé dans r/{subreddit} avec le mot-clé '{keyword}'"
        elif subreddit:
            message = f"Aucun post trouvé dans r/{subreddit}"
        super().__init__(message, *args)


class TranslationError(RedditVideoError):
    """Erreurs liées à la traduction"""

    def __init__(self, message="Erreur lors de la traduction", chunk_number=None, *args):
        self.message = message
        self.chunk_number = chunk_number
        super().__init__(message, *args)

    def __str__(self):
        if self.chunk_number is not None:
            return f"{self.message} (Chunk #{self.chunk_number})"
        return self.message


class MediaGenerationError(RedditVideoError):
    """Erreurs liées à la génération de médias"""
    pass


class AudioError(MediaGenerationError):
    """Erreurs liées à la génération audio"""
    def __init__(self, message="Erreur lors de la génération audio", filename=None, *args):
        self.filename = filename
        super().__init__(f"{message}{': ' + filename if filename else ''}", *args)


class VideoError(MediaGenerationError):
    """Erreurs liées à la génération vidéo"""
    def __init__(self, message="Erreur lors de la génération vidéo", filename=None, *args):
        self.filename = filename
        super().__init__(f"{message}{': ' + filename if filename else ''}", *args)

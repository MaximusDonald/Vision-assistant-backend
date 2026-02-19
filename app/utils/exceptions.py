"""
Exceptions personnalisées pour l'application
"""


class VisionAssistantException(Exception):
    """Exception de base pour toute l'application"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ModelLoadError(VisionAssistantException):
    """Erreur lors du chargement des modèles ML"""
    pass


class InvalidInputError(VisionAssistantException):
    """Erreur de validation des entrées utilisateur"""
    pass


class ProcessingError(VisionAssistantException):
    """Erreur pendant le traitement (vision, voix, etc.)"""
    pass


class StorageError(VisionAssistantException):
    """Erreur liée au stockage temporaire"""
    pass
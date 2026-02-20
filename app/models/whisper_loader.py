"""
Chargement Whisper via Groq API (pas de modèle local)
"""
from groq import Groq
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_groq_client = None


def get_whisper_model():
    """
    Retourne client Groq pour Whisper
    
    Returns:
        Client Groq
    """
    global _groq_client
    
    if _groq_client is None:
        logger.info("📦 Initialisation Groq API...")
        
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        
        logger.info("✅ Groq API prêt")
    
    return _groq_client
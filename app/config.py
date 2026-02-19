"""
Configuration centralisée de l'application
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Configuration globale chargée depuis .env"""
    
    # === CHEMINS ===
    MODEL_DIR: str = "models"
    TEMP_DIR: str = "temp"
    LOG_DIR: str = "logs"
    
    # === GEMINI ===
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemma-3-27b-it"
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.7
    
    # === STREAM ===
    STREAM_FPS: int = 2
    FRAME_DIFF_THRESHOLD: int = 10
    CACHE_MAX_IMAGES: int = 10
    CACHE_TTL_SECONDS: int = 300
    
    # === LIMITES ===
    MAX_IMAGE_SIZE_MB: int = 4
    MAX_AUDIO_SIZE_MB: int = 5
    
    # === API ===
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # === SÉCURITÉ ===
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # === VOIX ===
    TTS_VOICE_GENDER: str = "female"
    TTS_LANGUAGE: str = "fr"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convertit CORS_ORIGINS en liste"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def model_path(self) -> Path:
        """Chemin absolu vers le dossier models"""
        return Path(self.MODEL_DIR).resolve()
    
    @property
    def temp_path(self) -> Path:
        """Chemin absolu vers le dossier temp"""
        path = Path(self.TEMP_DIR).resolve()
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def log_path(self) -> Path:
        """Chemin absolu vers le dossier logs"""
        path = Path(self.LOG_DIR).resolve()
        path.mkdir(exist_ok=True)
        return path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instance globale (singleton)
settings = Settings()
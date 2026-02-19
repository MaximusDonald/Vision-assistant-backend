"""
Modèles de données pour le cache
"""
import time
import imagehash
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CachedFrame:
    """
    Frame capturée avec métadonnées
    """
    frame_id: str                           # UUID unique
    image_path: Path                        # Chemin vers l'image
    image_hash: imagehash.ImageHash        # Hash perceptuel
    timestamp: float = field(default_factory=time.time)
    
    # Résultats Gemini
    description: Optional[str] = None       # Description automatique
    gemini_processed: bool = False          # Déjà analysé par Gemini ?
    
    # Métadonnées
    width: int = 0
    height: int = 0
    size_bytes: int = 0
    
    def is_expired(self, ttl_seconds: int) -> bool:
        """
        Vérifie si la frame est expirée
        
        Args:
            ttl_seconds: Durée de vie maximale
            
        Returns:
            True si expirée
        """
        return (time.time() - self.timestamp) > ttl_seconds
    
    def age_seconds(self) -> float:
        """Âge de la frame en secondes"""
        return time.time() - self.timestamp
    
    def to_dict(self) -> dict:
        """Conversion en dict pour JSON"""
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "age_seconds": self.age_seconds(),
            "description": self.description,
            "gemini_processed": self.gemini_processed,
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes
        }
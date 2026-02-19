"""
Comparaison intelligente d'images (perceptual hashing)
"""
import imagehash
from PIL import Image
from pathlib import Path
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)


class ImageComparator:
    """
    Compare des images via perceptual hashing
    Détecte changements significatifs sans requête externe
    """
    
    @staticmethod
    def compute_hash(image_path: Path) -> imagehash.ImageHash:
        """
        Calcule le hash perceptuel d'une image
        
        Args:
            image_path: Chemin vers l'image
            
        Returns:
            Hash perceptuel (phash)
        """
        img = Image.open(image_path)
        return imagehash.phash(img)
    
    @staticmethod
    def compute_difference(hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> int:
        """
        Calcule la différence entre deux hashs
        
        Args:
            hash1: Premier hash
            hash2: Deuxième hash
            
        Returns:
            Score de différence (0-64)
            - 0-5   : Identique
            - 6-15  : Légère différence
            - 16+   : Changement significatif
        """
        return hash1 - hash2
    
    @staticmethod
    def is_significant_change(
        image1_path: Path,
        image2_path: Path,
        threshold: int = None
    ) -> tuple[bool, int]:
        """
        Détermine si deux images sont significativement différentes
        
        Args:
            image1_path: Première image
            image2_path: Deuxième image
            threshold: Seuil custom (défaut: config)
            
        Returns:
            (is_different, difference_score)
        """
        threshold = threshold or settings.FRAME_DIFF_THRESHOLD
        
        hash1 = ImageComparator.compute_hash(image1_path)
        hash2 = ImageComparator.compute_hash(image2_path)
        
        diff = ImageComparator.compute_difference(hash1, hash2)
        
        is_different = diff >= threshold
        
        logger.debug(f"Différence images : {diff} (seuil: {threshold}) → {'CHANGEMENT' if is_different else 'SKIP'}")
        
        return is_different, diff
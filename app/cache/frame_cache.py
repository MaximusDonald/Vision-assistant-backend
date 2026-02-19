"""
Cache intelligent pour frames avec gestion TTL
"""
import uuid
import asyncio
from pathlib import Path
from collections import OrderedDict
from typing import Optional, List
from PIL import Image
from app.cache.models import CachedFrame
from app.utils.image_comparison import ImageComparator
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FrameCache:
    """
    Cache FIFO avec TTL automatique
    Stocke les N dernières frames + leurs descriptions Gemini
    """
    
    def __init__(
        self,
        max_size: int = None,
        ttl_seconds: int = None
    ):
        """
        Initialise le cache
        
        Args:
            max_size: Nombre max de frames (défaut: config)
            ttl_seconds: Durée de vie des frames (défaut: config)
        """
        self.max_size = max_size or settings.CACHE_MAX_IMAGES
        self.ttl_seconds = ttl_seconds or settings.CACHE_TTL_SECONDS
        
        # Cache OrderedDict (FIFO)
        self._cache: OrderedDict[str, CachedFrame] = OrderedDict()
        
        # Lock pour thread-safety
        self._lock = asyncio.Lock()
        
        logger.info(f"📦 Cache initialisé : max={self.max_size}, TTL={self.ttl_seconds}s")
    
    async def add_frame(
        self,
        image_path: Path,
        description: Optional[str] = None
    ) -> CachedFrame:
        """
        Ajoute une frame au cache
        
        Args:
            image_path: Chemin vers l'image
            description: Description Gemini (optionnel)
            
        Returns:
            CachedFrame créée
        """
        async with self._lock:
            # Génération ID
            frame_id = str(uuid.uuid4())
            
            # Calcul hash
            img_hash = ImageComparator.compute_hash(image_path)
            
            # Métadonnées image
            img = Image.open(image_path)
            width, height = img.size
            size_bytes = image_path.stat().st_size
            
            # Création frame
            frame = CachedFrame(
                frame_id=frame_id,
                image_path=image_path,
                image_hash=img_hash,
                description=description,
                gemini_processed=description is not None,
                width=width,
                height=height,
                size_bytes=size_bytes
            )
            
            # Ajout au cache
            self._cache[frame_id] = frame
            
            # Éviction si dépassement
            if len(self._cache) > self.max_size:
                oldest_id = next(iter(self._cache))
                evicted = self._cache.pop(oldest_id)
                logger.debug(f"🗑️ Éviction frame : {evicted.frame_id}")
                
                # Suppression fichier
                if evicted.image_path.exists():
                    evicted.image_path.unlink()
            
            logger.debug(f"➕ Frame ajoutée : {frame_id} (cache: {len(self._cache)}/{self.max_size})")
            
            return frame
    
    async def get_latest_frame(self) -> Optional[CachedFrame]:
        """
        Récupère la frame la plus récente
        
        Returns:
            Dernière frame ou None
        """
        async with self._lock:
            if not self._cache:
                return None
            
            # Dernière frame (OrderedDict conserve l'ordre)
            latest_id = next(reversed(self._cache))
            return self._cache[latest_id]
    
    async def get_frame(self, frame_id: str) -> Optional[CachedFrame]:
        """
        Récupère une frame par ID
        
        Args:
            frame_id: ID de la frame
            
        Returns:
            Frame ou None
        """
        async with self._lock:
            return self._cache.get(frame_id)
    
    async def should_process_new_frame(self, new_image_path: Path) -> tuple[bool, int]:
        """
        Détermine si une nouvelle frame nécessite traitement Gemini
        
        Args:
            new_image_path: Chemin vers la nouvelle frame
            
        Returns:
            (should_process, difference_score)
        """
        latest = await self.get_latest_frame()
        
        # Première frame : toujours traiter
        if latest is None:
            logger.info("🆕 Première frame → Traitement Gemini")
            return True, 999
        
        # Comparaison avec dernière frame
        is_different, diff_score = ImageComparator.is_significant_change(
            latest.image_path,
            new_image_path,
            settings.FRAME_DIFF_THRESHOLD
        )
        
        if is_different:
            logger.info(f"🔄 Changement détecté (score: {diff_score}) → Traitement Gemini")
        else:
            logger.debug(f"⏭️ Pas de changement (score: {diff_score}) → SKIP Gemini")
        
        return is_different, diff_score
    
    async def update_frame_description(self, frame_id: str, description: str):
        """
        Met à jour la description d'une frame
        
        Args:
            frame_id: ID de la frame
            description: Nouvelle description
        """
        async with self._lock:
            if frame_id in self._cache:
                self._cache[frame_id].description = description
                self._cache[frame_id].gemini_processed = True
                logger.debug(f"✏️ Description mise à jour : {frame_id}")
    
    async def cleanup_expired(self):
        """
        Nettoie les frames expirées (TTL dépassé)
        """
        async with self._lock:
            expired_ids = [
                frame_id
                for frame_id, frame in self._cache.items()
                if frame.is_expired(self.ttl_seconds)
            ]
            
            for frame_id in expired_ids:
                frame = self._cache.pop(frame_id)
                
                # Suppression fichier
                if frame.image_path.exists():
                    frame.image_path.unlink()
                
                logger.debug(f"🧹 Frame expirée nettoyée : {frame_id}")
            
            if expired_ids:
                logger.info(f"🧹 {len(expired_ids)} frame(s) expirée(s) nettoyée(s)")
    
    async def get_all_frames(self) -> List[CachedFrame]:
        """
        Récupère toutes les frames du cache
        
        Returns:
            Liste des frames (ordre chronologique)
        """
        async with self._lock:
            return list(self._cache.values())
    
    async def clear(self):
        """Vide complètement le cache"""
        async with self._lock:
            # Suppression fichiers
            for frame in self._cache.values():
                if frame.image_path.exists():
                    frame.image_path.unlink()
            
            self._cache.clear()
            logger.info("🗑️ Cache vidé")
    
    def size(self) -> int:
        """Nombre de frames en cache"""
        return len(self._cache)
    
    async def get_stats(self) -> dict:
        """
        Statistiques du cache
        
        Returns:
            Dict avec statistiques
        """
        async with self._lock:
            frames = list(self._cache.values())
            
            return {
                "total_frames": len(frames),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "frames_with_description": sum(1 for f in frames if f.gemini_processed),
                "oldest_frame_age_seconds": frames[0].age_seconds() if frames else 0,
                "newest_frame_age_seconds": frames[-1].age_seconds() if frames else 0,
                "total_size_mb": sum(f.size_bytes for f in frames) / (1024 * 1024)
            }


# Instance globale (singleton)
_frame_cache_instance = FrameCache()


def get_frame_cache() -> FrameCache:
    """
    Factory pour obtenir l'instance du cache
    Utilisé pour dependency injection FastAPI
    """
    return _frame_cache_instance
"""
Tâche background pour nettoyage automatique du cache
"""
import asyncio
from app.cache.frame_cache import get_frame_cache
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def cleanup_expired_frames_task():
    """
    Tâche background : nettoie les frames expirées toutes les 60s
    """
    cache = get_frame_cache()
    
    logger.info("🧹 Tâche de nettoyage démarrée (intervalle: 60s)")
    
    while True:
        try:
            await asyncio.sleep(60)  # Toutes les 60 secondes
            await cache.cleanup_expired()
            
        except asyncio.CancelledError:
            logger.info("🛑 Tâche de nettoyage arrêtée")
            break
        except Exception as e:
            logger.error(f"❌ Erreur tâche nettoyage : {e}", exc_info=True)
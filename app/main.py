"""
Point d'entrée principal de l'application FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.config import settings
from app.utils.logger import setup_logger
from app.cache.cleanup_task import cleanup_expired_frames_task
from app.api.routes import router as api_router
from app.websocket.routes import router as ws_router  # ✅ NOUVEAU

# Logger principal
logger = setup_logger(__name__)

# Référence tâche background
cleanup_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application
    """
    global cleanup_task
    
    # === STARTUP ===
    logger.info("=" * 60)
    logger.info("🚀 VISION ASSISTANT - GEMINI EDITION")
    logger.info("=" * 60)
    logger.info(f"📁 Dossier temporaire : {settings.temp_path}")
    logger.info(f"📁 Dossier logs : {settings.log_path}")
    logger.info(f"🤖 Modèle Gemini : {settings.GEMINI_MODEL}")
    logger.info(f"🔍 Seuil différence : {settings.FRAME_DIFF_THRESHOLD}")
    logger.info(f"📦 Cache : max={settings.CACHE_MAX_IMAGES}, TTL={settings.CACHE_TTL_SECONDS}s")
    
    # Démarrage tâche nettoyage cache
    cleanup_task = asyncio.create_task(cleanup_expired_frames_task())
    
    logger.info("=" * 60)
    logger.info("✅ APPLICATION PRÊTE")
    logger.info("=" * 60)
    
    yield
    
    # === SHUTDOWN ===
    logger.info("🛑 Arrêt de l'application")
    
    # Arrêt tâche nettoyage
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    
    # Nettoyage cache
    from app.cache.frame_cache import get_frame_cache
    await get_frame_cache().clear()
    
    logger.info("👋 Application arrêtée")


# Création de l'app FastAPI
app = FastAPI(
    title="Vision Assistant API (Gemini)",
    description="Assistant vocal multimodal temps réel pour malvoyants",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion routes
app.include_router(api_router)
app.include_router(ws_router)  # ✅ NOUVEAU


# === ROUTES DE BASE ===

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Vision Assistant API (Gemini)",
        "version": "2.0.0",
        "status": "running",
        "model": settings.GEMINI_MODEL,
        "docs": "/docs",
        "endpoints": {
            "rest": {
                "process_frame": "/api/v1/process-frame",
                "ask_question": "/api/v1/ask",
                "current_scene": "/api/v1/current-scene",
                "cache_stats": "/api/v1/cache/stats",
                "health": "/api/v1/health"
            },
            "websocket": {
                "stream": "/ws/stream",
                "stats": "/ws/stats"
            }
        }
    }
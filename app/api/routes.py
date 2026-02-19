"""
Routes API REST
"""
import tempfile
import base64
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import Response
from app.api.schemas import (
    ProcessFrameResponse,
    AskQuestionRequest,
    AskQuestionResponse,
    CacheStatsResponse,
    HealthResponse
)
from app.core.orchestrator import VisionOrchestrator
from app.dependencies import (
    get_gemini_client,
    get_cache,
    get_stt_client,
    get_tts_client
)
from app.utils.validators import FileValidator
from app.utils.exceptions import InvalidInputError, ProcessingError
from app.utils.logger import setup_logger
from app.config import settings
import uuid
from typing import Optional

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["vision"])


def get_orchestrator(
    gemini = Depends(get_gemini_client),
    cache = Depends(get_cache),
    stt = Depends(get_stt_client),
    tts = Depends(get_tts_client)
) -> VisionOrchestrator:
    """Dependency injection orchestrateur"""
    return VisionOrchestrator(gemini, cache, stt, tts)


@router.post("/process-frame", response_model=ProcessFrameResponse)
async def process_frame(
    image: UploadFile = File(..., description="Frame capturée (JPEG/PNG, max 4MB)"),
    force: bool = Form(False, description="Force traitement Gemini même sans changement"),
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## Traitement d'une frame capturée
    
    **Comportement intelligent :**
    - Compare avec dernière frame (perceptual hash)
    - Si différence < seuil → SKIP Gemini (économie quota)
    - Si différence ≥ seuil → Analyse Gemini + TTS
    
    **Force mode :**
    - `force=true` : Ignore la comparaison, traite toujours
    
    **Réponse :**
    - Description textuelle
    - Audio MP3 (si traité)
    - Métadonnées (temps, cache, etc.)
    """
    
    image_path = None
    
    try:
        # Sauvegarde temporaire
        image_path = Path(settings.temp_path / f"{uuid.uuid4()}.jpg")
        with image_path.open("wb") as f:
            f.write(await image.read())
        
        # Validation
        FileValidator.validate_image(image_path)
        
        # Traitement
        result = await orchestrator.process_frame(image_path, force=force)
        
        return result
        
    except InvalidInputError as e:
        logger.error(f"❌ Validation : {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except ProcessingError as e:
        logger.error(f"❌ Traitement : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur serveur interne")
    
    finally:
        # Note : image_path reste dans le cache, nettoyé par TTL
        pass


@router.post("/process-frame/audio")
async def get_frame_audio(
    image: UploadFile = File(...),
    force: bool = Form(False),
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## Variante : Retourne uniquement l'audio
    
    Même comportement que /process-frame mais retourne directement
    le fichier MP3 au lieu de JSON.
    
    Utile pour clients simples (lecteurs audio directs).
    """
    
    image_path = None
    
    try:
        # Sauvegarde temporaire
        image_path = Path(settings.temp_path / f"{uuid.uuid4()}.jpg")
        with image_path.open("wb") as f:
            f.write(await image.read())
        
        FileValidator.validate_image(image_path)
        
        # Traitement
        result = await orchestrator.process_frame(image_path, force=force)
        
        # Si skipped → utilise description précédente pour TTS
        if result["status"] == "skipped":
            if result["description"]:
                tts = get_tts_client()
                audio_bytes = await tts.synthesize(result["description"])
            else:
                raise HTTPException(status_code=204, detail="Aucune description disponible")
        else:
            audio_bytes = result["audio_response"]
        
        # Retour audio direct
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=description.mp3"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    question_text: Optional[str] = Form(None, description="Question en texte"),
    question_audio: Optional[UploadFile] = File(None, description="Question en audio (WAV/MP3)"),
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## Poser une question sur la scène actuelle
    
    **Modes :**
    - `question_text` : Question en texte (prioritaire)
    - `question_audio` : Question en audio (transcrite via Whisper)
    
    **Contexte :**
    - Utilise la dernière frame en cache
    - Inclut la description Gemini précédente comme contexte
    
    **Réponse :**
    - Réponse textuelle
    - Audio MP3
    - Métadonnées
    """
    
    audio_path = None
    
    try:
        # Traitement audio si fourni
        if question_audio and not question_text:
            audio_path = Path(settings.temp_path / f"{uuid.uuid4()}.wav")
            with audio_path.open("wb") as f:
                f.write(await question_audio.read())
            
            FileValidator.validate_audio(audio_path)
        
        # Validation : au moins une question
        if not question_text and not audio_path:
            raise HTTPException(
                status_code=400,
                detail="Fournir question_text OU question_audio"
            )
        
        # Traitement
        result = await orchestrator.ask_question(
            question_text=question_text,
            question_audio_path=audio_path
        )
        
        return result
        
    except ProcessingError as e:
        logger.error(f"❌ Erreur : {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if audio_path and audio_path.exists():
            audio_path.unlink()


@router.post("/ask/audio")
async def ask_question_audio(
    question_text: Optional[str] = Form(None),
    question_audio: Optional[UploadFile] = File(None),
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## Variante : Retourne uniquement l'audio de la réponse
    """
    
    audio_path = None
    
    try:
        if question_audio and not question_text:
            audio_path = Path(settings.temp_path / f"{uuid.uuid4()}.wav")
            with audio_path.open("wb") as f:
                f.write(await question_audio.read())
            FileValidator.validate_audio(audio_path)
        
        if not question_text and not audio_path:
            raise HTTPException(status_code=400, detail="Question requise")
        
        result = await orchestrator.ask_question(
            question_text=question_text,
            question_audio_path=audio_path
        )
        
        return Response(
            content=result["audio_response"],
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=answer.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if audio_path and audio_path.exists():
            audio_path.unlink()


@router.get("/current-scene")
async def get_current_scene(
    cache = Depends(get_cache)
):
    """
    ## Récupère la description de la scène actuelle
    
    Retourne la dernière description Gemini en cache.
    """
    
    latest = await cache.get_latest_frame()
    
    if not latest:
        raise HTTPException(
            status_code=404,
            detail="Aucune frame en cache. Capturez une frame d'abord."
        )
    
    if not latest.description:
        raise HTTPException(
            status_code=404,
            detail="Dernière frame sans description. Attendez traitement Gemini ou forcez avec force=true."
        )
    
    return {
        "description": latest.description,
        "frame_id": latest.frame_id,
        "age_seconds": latest.age_seconds()
    }


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## Statistiques du cache
    
    Infos sur frames stockées, TTL, taille mémoire, etc.
    """
    
    return await orchestrator.get_cache_stats()


@router.delete("/cache/clear")
async def clear_cache(
    cache = Depends(get_cache)
):
    """
    ## Vide complètement le cache
    
    Supprime toutes les frames et descriptions.
    """
    
    await cache.clear()
    
    return {
        "status": "cleared",
        "message": "Cache vidé avec succès"
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## Health check
    
    Vérifie l'état de l'API et du cache.
    """
    
    stats = await orchestrator.get_cache_stats()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "gemini_model": settings.GEMINI_MODEL,
        "cache": stats
    }
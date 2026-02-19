"""
Routes WebSocket
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.manager import get_connection_manager, ConnectionManager
from app.websocket.handlers import StreamHandler
from app.core.orchestrator import VisionOrchestrator
from app.dependencies import (
    get_gemini_client,
    get_cache,
    get_stt_client,
    get_tts_client
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(tags=["websocket"])


def get_orchestrator(
    gemini = Depends(get_gemini_client),
    cache = Depends(get_cache),
    stt = Depends(get_stt_client),
    tts = Depends(get_tts_client)
) -> VisionOrchestrator:
    """Dependency injection orchestrateur"""
    return VisionOrchestrator(gemini, cache, stt, tts)


@router.websocket("/ws/stream")
async def websocket_stream(
    websocket: WebSocket,
    manager: ConnectionManager = Depends(get_connection_manager),
    orchestrator: VisionOrchestrator = Depends(get_orchestrator)
):
    """
    ## WebSocket endpoint pour stream temps réel
    
    **Messages clients → serveur :**
```json
    // 1. Envoi frame
    {
      "type": "frame",
      "image_base64": "base64_string",
      "force": false,
      "timestamp": 1234567890
    }
    
    // 2. Question
    {
      "type": "question",
      "question_text": "Qu'est-ce que tu vois ?"
    }
    
    // 3. Ping (keep-alive)
    {
      "type": "ping"
    }
```
    
    **Messages serveur → client :**
```json
    // 1. Frame traitée
    {
      "type": "frame_processed",
      "status": "processed",
      "frame_id": "uuid",
      "description": "...",
      "audio_base64": "...",
      "processing_time_ms": 1234
    }
    
    // 2. Frame skipped
    {
      "type": "frame_processed",
      "status": "skipped",
      "reason": "no_significant_change"
    }
    
    // 3. Réponse question
    {
      "type": "question_answered",
      "question": "...",
      "answer": "...",
      "audio_base64": "..."
    }
    
    // 4. Erreur
    {
      "type": "error",
      "message": "..."
    }
    
    // 5. Pong
    {
      "type": "pong"
    }
```
    """
    
    # Connexion client
    await manager.connect(websocket)
    
    # Handler
    handler = StreamHandler(manager, orchestrator)
    
    try:
        # Message bienvenue
        await manager.send_personal_message({
            "type": "connected",
            "message": "Connecté au stream Vision Assistant",
            "client_id": manager.get_client_info(websocket)["client_id"]
        }, websocket)
        
        # Boucle réception messages
        while True:
            # Réception message JSON
            data = await websocket.receive_json()
            
            # Dispatch selon type
            message_type = data.get("type")
            
            if message_type == "frame":
                await handler.handle_frame(websocket, data)
            
            elif message_type == "question":
                await handler.handle_question(websocket, data)
            
            elif message_type == "ping":
                await handler.handle_ping(websocket)
            
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Type de message inconnu : {message_type}"
                }, websocket)
    
    except WebSocketDisconnect:
        logger.info("Client déconnecté (WebSocketDisconnect)")
    
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket : {e}", exc_info=True)
    
    finally:
        # Nettoyage
        manager.disconnect(websocket)
        handler.cleanup_client(websocket)


@router.get("/ws/stats")
async def websocket_stats(
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    ## Statistiques WebSocket
    
    Nombre de clients connectés.
    """
    return {
        "connected_clients": manager.get_connected_count()
    }
"""
Handlers pour WebSocket stream
"""
import base64
import tempfile
import asyncio
import uuid
from pathlib import Path
from typing import Optional
from app.config import settings  # ✅ AJOUTÉ
from app.websocket.manager import ConnectionManager
from app.core.orchestrator import VisionOrchestrator
from app.utils.logger import setup_logger
from app.utils.validators import FileValidator
from app.utils.exceptions import ProcessingError, InvalidInputError

logger = setup_logger(__name__)


class StreamHandler:
    """
    Gère le traitement des frames en streaming
    """
    
    def __init__(
        self,
        manager: ConnectionManager,
        orchestrator: VisionOrchestrator
    ):
        """
        Initialise le handler
        
        Args:
            manager: Gestionnaire connexions
            orchestrator: Orchestrateur principal
        """
        self.manager = manager
        self.orchestrator = orchestrator
        self.logger = setup_logger(__name__)
        
        # Locks par client (évite concurrence)
        self.client_locks = {}
    
    async def handle_frame(
        self,
        websocket,
        data: dict
    ):
        """
        Traite une frame reçue via WebSocket
        
        Args:
            websocket: WebSocket client
            data: Données frame {image_base64, force?, timestamp?}
        """
        client_id = self.manager.get_client_info(websocket).get("client_id", "unknown")
        
        # Lock par client
        if websocket not in self.client_locks:
            self.client_locks[websocket] = asyncio.Lock()
        
        async with self.client_locks[websocket]:
            image_path = None
            
            try:
                # Validation données
                if "image_base64" not in data:
                    await self.manager.send_personal_message({
                        "type": "error",
                        "message": "Champ 'image_base64' manquant"
                    }, websocket)
                    return
                
                # Décodage image
                image_data = base64.b64decode(data["image_base64"])
                image_path = Path(settings.temp_path / f"{uuid.uuid4()}.jpg")  # ✅ CORRIGÉ
                image_path.write_bytes(image_data)
                
                # Validation
                FileValidator.validate_image(image_path)
                
                # Traitement
                force = data.get("force", False)
                result = await self.orchestrator.process_frame(image_path, force=force)
                
                # Réponse client
                response = {
                    "type": "frame_processed",
                    "status": result["status"],
                    "frame_id": result["frame_id"],
                    "difference_score": result["difference_score"],
                    "threshold": result["threshold"],
                    "description": result.get("description"),
                    "processing_time_ms": result["processing_time_ms"]
                }
                
                # Si traité par Gemini → audio
                if result["status"] == "processed" and result.get("audio_response"):
                    audio_base64 = base64.b64encode(result["audio_response"]).decode()
                    response["audio_base64"] = audio_base64
                
                await self.manager.send_personal_message(response, websocket)
                
                # Broadcast aux autres clients (optionnel)
                if result["status"] == "processed":
                    await self.manager.broadcast({
                        "type": "scene_update",
                        "description": result.get("description"),
                        "frame_id": result["frame_id"]
                    }, exclude=websocket)
                
            except InvalidInputError as e:
                self.logger.error(f"❌ Validation frame : {e}")
                await self.manager.send_personal_message({
                    "type": "error",
                    "message": str(e)
                }, websocket)
            
            except ProcessingError as e:
                self.logger.error(f"❌ Traitement frame : {e}")
                await self.manager.send_personal_message({
                    "type": "error",
                    "message": f"Erreur traitement : {e}"
                }, websocket)
            
            except Exception as e:
                self.logger.error(f"❌ Erreur inattendue : {e}", exc_info=True)
                await self.manager.send_personal_message({
                    "type": "error",
                    "message": f"Erreur serveur interne: {str(e)}"
                }, websocket)
            
            finally:
                # Note : image_path reste dans cache, nettoyé par TTL
                pass
    
    async def handle_question(
        self,
        websocket,
        data: dict
    ):
        """
        Traite une question reçue via WebSocket
        
        Args:
            websocket: WebSocket client
            data: Données question {question_text}
        """
        try:
            # Validation
            question_text = data.get("question_text")
            if not question_text:
                await self.manager.send_personal_message({
                    "type": "error",
                    "message": "Champ 'question_text' manquant"
                }, websocket)
                return
            
            # Traitement
            result = await self.orchestrator.ask_question(question_text=question_text)
            
            # Réponse
            audio_base64 = base64.b64encode(result["audio_response"]).decode()
            
            await self.manager.send_personal_message({
                "type": "question_answered",
                "question": result["question"],
                "answer": result["answer"],
                "audio_base64": audio_base64,
                "frame_id": result["frame_id"],
                "processing_time_ms": result["processing_time_ms"]
            }, websocket)
            
        except ProcessingError as e:
            self.logger.error(f"❌ Erreur question : {e}")
            await self.manager.send_personal_message({
                "type": "error",
                "message": str(e)
            }, websocket)
        
        except Exception as e:
            self.logger.error(f"❌ Erreur inattendue : {e}", exc_info=True)
            await self.manager.send_personal_message({
                "type": "error",
                "message": f"Erreur serveur interne: {str(e)}"
            }, websocket)
    
    async def handle_ping(self, websocket):
        """Répond à un ping (keep-alive)"""
        await self.manager.send_personal_message({
            "type": "pong"
        }, websocket)
    
    def cleanup_client(self, websocket):
        """Nettoyage ressources client déconnecté"""
        if websocket in self.client_locks:
            del self.client_locks[websocket]
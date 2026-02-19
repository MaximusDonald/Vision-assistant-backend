"""
Orchestrateur principal - Gemini Vision en temps réel
"""
import time
import asyncio
import uuid
from pathlib import Path
from typing import Optional, Tuple
from app.gemini.client import GeminiClient
from app.cache.frame_cache import FrameCache
from app.voice.speech_to_text import SpeechToText
from app.voice.text_to_speech import TextToSpeech
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class VisionOrchestrator:
    """
    Chef d'orchestre du pipeline temps réel
    
    Flux :
    1. Frame capturée → Comparaison avec cache
    2. Si changement significatif → Gemini Vision
    3. Description → Synthèse vocale
    4. Stockage cache
    """
    
    def __init__(
        self,
        gemini: GeminiClient,
        cache: FrameCache,
        stt: SpeechToText,
        tts: TextToSpeech
    ):
        """
        Initialise l'orchestrateur
        
        Args:
            gemini: Client Gemini
            cache: Cache frames
            stt: Speech-to-Text
            tts: Text-to-Speech
        """
        self.gemini = gemini
        self.cache = cache
        self.stt = stt
        self.tts = tts
        self.logger = setup_logger(__name__)
    
    async def process_frame(
        self,
        image_path: Path,
        force: bool = False
    ) -> dict:
        """
        Traite une frame capturée
        
        Args:
            image_path: Chemin vers l'image
            force: Force le traitement Gemini même si pas de changement
            
        Returns:
            Dict avec résultats
        """
        start_time = time.time()
        
        try:
            self.logger.info("=" * 60)
            self.logger.info(f"📸 TRAITEMENT FRAME : {image_path.name}")
            self.logger.info("=" * 60)
            
            # ÉTAPE 1 : Vérification besoin traitement Gemini
            should_process, diff_score = await self.cache.should_process_new_frame(image_path)
            
            if not should_process and not force:
                # Pas de changement → Récupération dernière description
                latest = await self.cache.get_latest_frame()
                
                # Ajout frame au cache sans traitement Gemini
                frame = await self.cache.add_frame(image_path)
                
                processing_time = int((time.time() - start_time) * 1000)
                
                self.logger.info(f"⏭️ SKIP Gemini (diff: {diff_score}) - {processing_time}ms")
                self.logger.info("=" * 60)
                
                return {
                    "status": "skipped",
                    "reason": "no_significant_change",
                    "frame_id": frame.frame_id,
                    "difference_score": diff_score,
                    "threshold": settings.FRAME_DIFF_THRESHOLD,
                    "description": latest.description if latest else None,
                    "description_age_seconds": latest.age_seconds() if latest else None,
                    "audio_response": None,
                    "processing_time_ms": processing_time
                }
            
            # ÉTAPE 2 : Traitement Gemini (changement détecté)
            self.logger.info(f"🤖 Gemini Vision (diff: {diff_score})...")
            description = await asyncio.get_event_loop().run_in_executor(
                None,
                self.gemini.describe_image,
                image_path
            )
            
            # ÉTAPE 3 : Ajout au cache avec description
            frame = await self.cache.add_frame(image_path, description)
            
            # ÉTAPE 4 : Synthèse vocale
            self.logger.info("🔊 Synthèse vocale...")
            audio_bytes = await self.tts.synthesize(
                description,
                language=settings.TTS_LANGUAGE,
                gender=settings.TTS_VOICE_GENDER
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            self.logger.info("=" * 60)
            self.logger.info(f"✅ TRAITEMENT TERMINÉ - {processing_time}ms")
            self.logger.info("=" * 60)
            
            return {
                "status": "processed",
                "frame_id": frame.frame_id,
                "difference_score": diff_score,
                "threshold": settings.FRAME_DIFF_THRESHOLD,
                "description": description,
                "audio_response": audio_bytes,
                "audio_size_bytes": len(audio_bytes),
                "processing_time_ms": processing_time,
                "timestamp": frame.timestamp
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement frame : {e}", exc_info=True)
            raise ProcessingError(f"Traitement frame échoué : {e}")
    
    async def ask_question(
        self,
        question_text: Optional[str] = None,
        question_audio_path: Optional[Path] = None
    ) -> dict:
        """
        Répond à une question sur la scène actuelle
        
        Args:
            question_text: Question en texte (prioritaire)
            question_audio_path: Question en audio (si pas de texte)
            
        Returns:
            Dict avec réponse
        """
        start_time = time.time()
        
        try:
            self.logger.info("=" * 60)
            self.logger.info("❓ QUESTION UTILISATEUR")
            self.logger.info("=" * 60)
            
            # ÉTAPE 1 : Récupération question
            if question_text:
                question = question_text
                self.logger.info(f"📝 Question (texte) : \"{question}\"")
            elif question_audio_path:
                self.logger.info("🎤 Transcription question audio...")
                question = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.stt.transcribe,
                    question_audio_path
                )
                self.logger.info(f"📝 Question transcrite : \"{question}\"")
            else:
                raise ProcessingError("Aucune question fournie (texte ou audio)")
            
            if not question or len(question.strip()) < 2:
                raise ProcessingError("Question vide ou invalide")
            
            # ÉTAPE 2 : Récupération dernière frame
            latest_frame = await self.cache.get_latest_frame()
            
            if not latest_frame:
                raise ProcessingError("Aucune frame en cache. Capturez une image d'abord.")
            
            self.logger.info(f"📸 Frame de référence : {latest_frame.frame_id} (âge: {latest_frame.age_seconds():.1f}s)")
            
            # ÉTAPE 3 : Question Gemini avec contexte
            self.logger.info("🤖 Gemini Chat...")
            answer = await asyncio.get_event_loop().run_in_executor(
                None,
                self.gemini.answer_question,
                latest_frame.image_path,
                question,
                latest_frame.description
            )
            
            # ÉTAPE 4 : Synthèse vocale réponse
            self.logger.info("🔊 Synthèse vocale...")
            audio_bytes = await self.tts.synthesize(
                answer,
                language=settings.TTS_LANGUAGE,
                gender=settings.TTS_VOICE_GENDER
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            self.logger.info("=" * 60)
            self.logger.info(f"✅ QUESTION TRAITÉE - {processing_time}ms")
            self.logger.info("=" * 60)
            
            return {
                "status": "answered",
                "question": question,
                "answer": answer,
                "audio_response": audio_bytes,
                "audio_size_bytes": len(audio_bytes),
                "frame_id": latest_frame.frame_id,
                "frame_age_seconds": latest_frame.age_seconds(),
                "context_description": latest_frame.description,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur question : {e}", exc_info=True)
            raise ProcessingError(f"Traitement question échoué : {e}")
    
    async def get_current_scene_description(self) -> Optional[str]:
        """
        Récupère la description de la scène actuelle
        
        Returns:
            Description ou None
        """
        latest = await self.cache.get_latest_frame()
        return latest.description if latest else None
    
    async def get_cache_stats(self) -> dict:
        """
        Statistiques du cache
        
        Returns:
            Dict avec stats
        """
        return await self.cache.get_stats()
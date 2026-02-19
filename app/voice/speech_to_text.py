"""
Transcription audio avec Faster-Whisper
"""
from pathlib import Path
from faster_whisper import WhisperModel
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class SpeechToText:
    """
    Wrapper Faster-Whisper
    Transcrit audio en texte (français prioritaire)
    """
    
    def __init__(self, model: WhisperModel):
        """
        Initialise le transcripteur
        
        Args:
            model: Instance Whisper pré-chargée
        """
        self.model = model
        self.logger = setup_logger(__name__)
    
    def transcribe(
        self,
        audio_path: Path,
        language: str = "fr"
    ) -> str:
        """
        Transcrit un fichier audio en texte
        
        Args:
            audio_path: Chemin vers le fichier audio
            language: Code langue (fr, en, etc.)
            
        Returns:
            Texte transcrit
        """
        try:
            self.logger.info(f"🎤 Transcription: {audio_path.name}")
            
            # Transcription avec VAD (Voice Activity Detection)
            segments, info = self.model.transcribe(
                str(audio_path),
                language=language,
                beam_size=5,          # Qualité transcription
                vad_filter=True,      # Filtrage silence
                vad_parameters={
                    "threshold": 0.5,
                    "min_speech_duration_ms": 250
                }
            )
            
            # Concaténation segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            result = " ".join(text_parts).strip()
            
            if not result:
                self.logger.warning("⚠️ Aucun texte détecté dans l'audio")
                return ""
            
            self.logger.info(f"✅ Transcription: \"{result[:50]}...\"")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erreur transcription: {e}", exc_info=True)
            raise ProcessingError(f"Transcription audio échouée: {e}")
    
    def detect_language(self, audio_path: Path) -> str:
        """
        Détecte automatiquement la langue de l'audio
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Code langue détecté (fr, en, etc.)
        """
        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                beam_size=5
            )
            
            detected_language = info.language
            self.logger.info(f"🌍 Langue détectée: {detected_language}")
            return detected_language
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection langue: {e}")
            return "fr"  # Fallback français
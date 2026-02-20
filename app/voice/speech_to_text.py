"""
Transcription audio avec OpenAI Whisper
"""
import whisper
from pathlib import Path
from typing import Optional
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class SpeechToText:
    """
    Wrapper OpenAI Whisper
    Transcrit audio en texte (français prioritaire)
    """
    
    def __init__(self, model):
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
            
            # Transcription
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                fp16=False  # CPU mode
            )
            
            text = result["text"].strip()
            
            if not text:
                self.logger.warning("⚠️ Aucun texte détecté dans l'audio")
                return ""
            
            self.logger.info(f"✅ Transcription: \"{text[:50]}...\"")
            return text
            
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
            # Load audio and pad/trim it to fit 30 seconds
            audio = whisper.load_audio(str(audio_path))
            audio = whisper.pad_or_trim(audio)

            # Make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

            # Detect the spoken language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            self.logger.info(f"🌍 Langue détectée: {detected_language}")
            return detected_language
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection langue: {e}")
            return "fr"  # Fallback français
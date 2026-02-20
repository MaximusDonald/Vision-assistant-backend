"""
Transcription audio avec Groq Whisper API
"""
from pathlib import Path
from groq import Groq
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class SpeechToText:
    """
    Wrapper Groq Whisper API
    Ultra rapide, pas de modèle local
    """
    
    def __init__(self, client: Groq):
        """
        Initialise le transcripteur
        
        Args:
            client: Client Groq pré-initialisé
        """
        self.client = client
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
            self.logger.info(f"🎤 Transcription Groq: {audio_path.name}")
            
            # Lecture fichier
            with open(audio_path, "rb") as audio_file:
                # Transcription via Groq
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    language=language,
                    response_format="json"
                )
            
            text = transcription.text.strip()
            
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
            Code langue détecté
        """
        try:
            with open(audio_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    response_format="json"
                )
            
            detected_language = transcription.language or "fr"
            self.logger.info(f"🌍 Langue détectée: {detected_language}")
            return detected_language
            
        except Exception as e:
            self.logger.error(f"❌ Erreur détection langue: {e}")
            return "fr"  # Fallback
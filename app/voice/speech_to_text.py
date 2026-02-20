"""
Transcription audio avec Groq Whisper API
"""
from pathlib import Path
from groq import Groq
import requests
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class SpeechToText:
    """
    Wrapper Groq Whisper API
    Ultra rapide, pas de modele local
    """

    def __init__(self, client: Groq):
        """
        Initialise le transcripteur

        Args:
            client: Client Groq pre-initialise
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
            self.logger.info(f"Transcription Groq: {audio_path.name}")

            if hasattr(self.client, "audio"):
                with open(audio_path, "rb") as audio_file:
                    transcription = self.client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        language=language,
                        response_format="json"
                    )
                text = transcription.text.strip()
            else:
                # Compatibility fallback for older Groq SDK versions without `client.audio`
                text = self._transcribe_via_http(audio_path, language).strip()

            if not text:
                self.logger.warning("Aucun texte detecte dans l'audio")
                return ""

            self.logger.info(f"Transcription: \"{text[:50]}...\"")
            return text

        except Exception as e:
            self.logger.error(f"Erreur transcription: {e}", exc_info=True)
            raise ProcessingError(f"Transcription audio echouee: {e}")

    def detect_language(self, audio_path: Path) -> str:
        """
        Detecte automatiquement la langue de l'audio

        Args:
            audio_path: Chemin vers le fichier audio

        Returns:
            Code langue detecte
        """
        try:
            if hasattr(self.client, "audio"):
                with open(audio_path, "rb") as audio_file:
                    transcription = self.client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        response_format="json"
                    )
                detected_language = transcription.language or "fr"
            else:
                # No detect-language with older path; use safe fallback
                detected_language = "fr"

            self.logger.info(f"Langue detectee: {detected_language}")
            return detected_language

        except Exception as e:
            self.logger.error(f"Erreur detection langue: {e}")
            return "fr"  # Fallback

    def _transcribe_via_http(self, audio_path: Path, language: str) -> str:
        """
        Fallback using Groq OpenAI-compatible transcription endpoint.
        """
        api_key = getattr(self.client, "api_key", None)
        if not api_key:
            raise ProcessingError("Cle API Groq introuvable sur le client.")

        with open(audio_path, "rb") as audio_file:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                data={
                    "model": "whisper-large-v3",
                    "language": language,
                    "response_format": "json",
                },
                files={"file": (audio_path.name, audio_file, "application/octet-stream")},
                timeout=60,
            )

        if response.status_code >= 400:
            raise ProcessingError(f"Groq transcription HTTP error {response.status_code}: {response.text}")

        payload = response.json()
        return payload.get("text", "")

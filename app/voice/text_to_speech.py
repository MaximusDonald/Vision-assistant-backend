"""
Synthèse vocale avec Edge-TTS
"""
import edge_tts
import asyncio
import tempfile
from pathlib import Path
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class TextToSpeech:
    """
    Wrapper Edge-TTS
    Génère audio à partir de texte
    """
    
    # Voix françaises disponibles (Microsoft Edge)
    VOICES = {
        "fr": {
            "female": "fr-FR-DeniseNeural",      # Voix féminine claire
            "male": "fr-FR-HenriNeural",         # Voix masculine
            "female_alt": "fr-FR-EloiseNeural"   # Alternative féminine
        },
        "en": {
            "female": "en-US-AriaNeural",
            "male": "en-US-GuyNeural"
        }
    }
    
    # Paramètres optimaux pour accessibilité
    DEFAULT_RATE = "+10%"    # Légèrement plus rapide
    DEFAULT_VOLUME = "+0%"   # Volume normal
    DEFAULT_PITCH = "+0Hz"   # Pitch normal
    
    def __init__(self):
        """Initialise le synthétiseur"""
        self.logger = setup_logger(__name__)
    
    async def synthesize(
        self,
        text: str,
        language: str = "fr",
        gender: str = "male",
        rate: str = None,
        output_format: str = "audio-24khz-48kbitrate-mono-mp3"
    ) -> bytes:
        """
        Synthétise du texte en audio
        
        Args:
            text: Texte à synthétiser
            language: Code langue (fr, en)
            gender: Genre voix (female, male)
            rate: Vitesse de parole (ex: "+10%", "-5%")
            output_format: Format audio de sortie
            
        Returns:
            Bytes audio (MP3)
        """
        try:
            self.logger.info(f"🔊 Synthèse TTS: \"{text[:50]}...\"")
            
            # Sélection voix
            voice = self.VOICES.get(language, self.VOICES["fr"]).get(gender, "fr-FR-HenryNeural")
            
            # Paramètres
            rate = rate or self.DEFAULT_RATE
            
            # Génération audio
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=rate,
                volume=self.DEFAULT_VOLUME,
                pitch=self.DEFAULT_PITCH
            )
            
            # Sauvegarde temporaire
            temp_file = Path(tempfile.mktemp(suffix=".mp3"))
            
            try:
                await communicate.save(str(temp_file))
                
                # Lecture bytes
                audio_bytes = temp_file.read_bytes()
                
                self.logger.info(f"✅ Audio généré: {len(audio_bytes)} bytes")
                return audio_bytes
                
            finally:
                # Nettoyage
                if temp_file.exists():
                    temp_file.unlink()
            
        except Exception as e:
            self.logger.error(f"❌ Erreur TTS: {e}", exc_info=True)
            raise ProcessingError(f"Synthèse vocale échouée: {e}")
    
    def synthesize_sync(
        self,
        text: str,
        language: str = "fr",
        gender: str = "female"
    ) -> bytes:
        """
        Version synchrone de synthesize (pour tests)
        
        Args:
            text: Texte à synthétiser
            language: Code langue
            gender: Genre voix
            
        Returns:
            Bytes audio
        """
        return asyncio.run(self.synthesize(text, language, gender))
    
    @staticmethod
    def get_available_voices(language: str = None) -> list:
        """
        Liste les voix disponibles
        
        Args:
            language: Filtrer par langue (optionnel)
            
        Returns:
            Liste des voix disponibles
        """
        if language:
            return list(TextToSpeech.VOICES.get(language, {}).values())
        
        all_voices = []
        for lang_voices in TextToSpeech.VOICES.values():
            all_voices.extend(lang_voices.values())
        return all_voices
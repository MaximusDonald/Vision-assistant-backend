"""
Utilitaires de traitement audio
"""
import wave
from pathlib import Path
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class AudioProcessor:
    """Normalisation et validation fichiers audio"""
    
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.ogg']
    MAX_DURATION_SECONDS = 60  # Limite durée audio
    
    @staticmethod
    def validate_audio(audio_path: Path) -> bool:
        """
        Valide un fichier audio
        
        Args:
            audio_path: Chemin vers le fichier
            
        Returns:
            True si valide
            
        Raises:
            ProcessingError si invalide
        """
        try:
            # Vérification extension
            if audio_path.suffix.lower() not in AudioProcessor.SUPPORTED_FORMATS:
                raise ProcessingError(
                    f"Format audio non supporté: {audio_path.suffix}. "
                    f"Formats acceptés: {AudioProcessor.SUPPORTED_FORMATS}"
                )
            
            # Vérification existence
            if not audio_path.exists():
                raise ProcessingError(f"Fichier audio introuvable: {audio_path}")
            
            # Vérification taille
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            if size_mb > 10:  # Limite 10MB
                raise ProcessingError(f"Fichier audio trop volumineux: {size_mb:.1f}MB")
            
            logger.info(f"✅ Audio validé: {audio_path.name} ({size_mb:.2f}MB)")
            return True
            
        except ProcessingError:
            raise
        except Exception as e:
            logger.error(f"❌ Erreur validation audio: {e}")
            raise ProcessingError(f"Validation audio échouée: {e}")
    
    @staticmethod
    def get_audio_duration(audio_path: Path) -> float:
        """
        Récupère la durée d'un fichier audio WAV
        
        Args:
            audio_path: Chemin vers le fichier WAV
            
        Returns:
            Durée en secondes
        """
        try:
            with wave.open(str(audio_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception as e:
            logger.warning(f"⚠️ Impossible de lire durée audio: {e}")
            return 0.0
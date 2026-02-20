"""
Validation des entrées utilisateur
"""
try:
    import magic  # type: ignore
except Exception:  # libmagic may be missing on some platforms
    magic = None
from pathlib import Path
from PIL import Image
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.exceptions import InvalidInputError

logger = setup_logger(__name__)


class FileValidator:
    """Validation robuste des fichiers uploadés"""

    ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/png", "image/jpg"]
    ALLOWED_AUDIO_MIMES = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav"]
    ALLOWED_IMAGE_EXTS = [".jpg", ".jpeg", ".png"]
    ALLOWED_AUDIO_EXTS = [".wav", ".mp3"]

    @staticmethod
    def validate_image(file_path: Path) -> bool:
        """
        Valide un fichier image

        Args:
            file_path: Chemin vers l'image

        Returns:
            True si valide

        Raises:
            InvalidInputError si invalide
        """
        try:
            # Vérification existence
            if not file_path.exists():
                raise InvalidInputError(f"Fichier introuvable: {file_path}")

            # Vérification magic number (sécurité)
            if magic:
                mime = magic.from_file(str(file_path), mime=True)
                if mime not in FileValidator.ALLOWED_IMAGE_MIMES:
                    raise InvalidInputError(
                        f"Format image non supporté: {mime}. "
                        f"Formats acceptés: JPEG, PNG"
                    )
            else:
                # Fallback: extension check if libmagic is unavailable
                if file_path.suffix.lower() not in FileValidator.ALLOWED_IMAGE_EXTS:
                    raise InvalidInputError(
                        f"Extension image non supportée: {file_path.suffix}. "
                        f"Formats acceptés: JPEG, PNG"
                    )

            # Vérification taille
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > settings.MAX_IMAGE_SIZE_MB:
                raise InvalidInputError(
                    f"Image trop volumineuse: {size_mb:.1f}MB. "
                    f"Maximum: {settings.MAX_IMAGE_SIZE_MB}MB"
                )

            # Vérification intégrité avec PIL
            try:
                img = Image.open(file_path)
                img.verify()

                # Vérification dimensions minimales
                img = Image.open(file_path)  # Réouverture après verify
                if img.width < 50 or img.height < 50:
                    raise InvalidInputError("Image trop petite (min 50x50px)")

            except Exception as e:
                raise InvalidInputError(f"Image corrompue: {e}")

            logger.info(f"✅ Image validée: {file_path.name}")
            return True

        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(f"❌ Erreur validation image: {e}")
            raise InvalidInputError(f"Validation image échouée: {e}")

    @staticmethod
    def validate_audio(file_path: Path) -> bool:
        """
        Valide un fichier audio

        Args:
            file_path: Chemin vers l'audio

        Returns:
            True si valide

        Raises:
            InvalidInputError si invalide
        """
        try:
            # Vérification existence
            if not file_path.exists():
                raise InvalidInputError(f"Fichier introuvable: {file_path}")

            # Vérification magic number
            if magic:
                mime = magic.from_file(str(file_path), mime=True)
                if mime not in FileValidator.ALLOWED_AUDIO_MIMES:
                    raise InvalidInputError(
                        f"Format audio non supporté: {mime}. "
                        f"Formats acceptés: WAV, MP3"
                    )
            else:
                # Fallback: extension check if libmagic is unavailable
                if file_path.suffix.lower() not in FileValidator.ALLOWED_AUDIO_EXTS:
                    raise InvalidInputError(
                        f"Extension audio non supportée: {file_path.suffix}. "
                        f"Formats acceptés: WAV, MP3"
                    )

            # Vérification taille
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > settings.MAX_AUDIO_SIZE_MB:
                raise InvalidInputError(
                    f"Audio trop volumineux: {size_mb:.1f}MB. "
                    f"Maximum: {settings.MAX_AUDIO_SIZE_MB}MB"
                )

            logger.info(f"✅ Audio validé: {file_path.name}")
            return True

        except InvalidInputError:
            raise
        except Exception as e:
            logger.error(f"❌ Erreur validation audio: {e}")
            raise InvalidInputError(f"Validation audio échouée: {e}")

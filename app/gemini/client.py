"""
Client Gemini Vision avec gestion cache
"""
import time
import google.generativeai as genai
from pathlib import Path
from PIL import Image
from typing import Optional
from app.config import settings
from app.gemini.prompts import GeminiPrompts
from app.utils.logger import setup_logger
from app.utils.exceptions import ProcessingError

logger = setup_logger(__name__)


class GeminiClient:
    """
    Client Gemini optimisé pour vision temps réel
    """
    
    def __init__(self):
        """Initialise le client Gemini"""
        self.logger = setup_logger(__name__)
        
        # Configuration API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Modèle
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "max_output_tokens": settings.GEMINI_MAX_TOKENS,
                "temperature": settings.GEMINI_TEMPERATURE,
            }
        )
        
        self.logger.info(f"✅ Gemini client initialisé : {settings.GEMINI_MODEL}")
    
    def describe_image(self, image_path: Path) -> str:
        """
        Génère une description accessible d'une image
        
        Args:
            image_path: Chemin vers l'image
            
        Returns:
            Description textuelle
        """
        try:
            self.logger.info(f"🤖 Gemini Vision : {image_path.name}")
            
            # Chargement image
            img = Image.open(image_path)
            
            # Prompt
            prompt = GeminiPrompts.build_vision_prompt()
            
            # Génération
            response = self.model.generate_content([prompt, img])
            
            # Extraction texte
            description = response.text.strip()
            
            self.logger.info(f"✅ Description : \"{description}\"")
            return description
            
        except Exception as e:
            self.logger.error(f"❌ Erreur Gemini Vision : {e}", exc_info=True)
            raise ProcessingError(f"Gemini Vision échoué : {e}")
    
    def answer_question(
        self,
        image_path: Path,
        question: str,
        previous_description: Optional[str] = None
    ) -> str:
        """
        Répond à une question sur une image
        
        Args:
            image_path: Chemin vers l'image
            question: Question utilisateur
            previous_description: Contexte (description précédente)
            
        Returns:
            Réponse textuelle
        """
        try:
            self.logger.info(f"❓ Question : \"{question}\"")
            
            # Chargement image
            img = Image.open(image_path)
            
            # Prompt contextualisé
            prompt = GeminiPrompts.build_question_prompt(question, previous_description)
            
            # Génération
            response = self.model.generate_content([prompt, img])
            
            # Extraction
            answer = response.text.strip()
            
            self.logger.info(f"✅ Réponse : \"{answer}\"")
            return answer
            
        except Exception as e:
            self.logger.error(f"❌ Erreur Gemini Chat : {e}", exc_info=True)
            raise ProcessingError(f"Gemini Chat échoué : {e}")
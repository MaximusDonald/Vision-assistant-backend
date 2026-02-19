"""
Schémas Pydantic pour validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class ProcessFrameResponse(BaseModel):
    """Réponse traitement frame"""
    status: str
    frame_id: str
    difference_score: int
    threshold: int
    description: Optional[str]
    audio_size_bytes: Optional[int] = None  # ✅ Optionnel maintenant
    processing_time_ms: int
    reason: Optional[str] = None
    description_age_seconds: Optional[float] = None
    timestamp: Optional[float] = None  # ✅ Ajouté


class AskQuestionRequest(BaseModel):
    """Requête question"""
    question: Optional[str] = Field(None, description="Question en texte")
    
    @validator('question')
    def validate_question(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError("Question trop courte (min 2 caractères)")
        return v


class AskQuestionResponse(BaseModel):
    """Réponse question"""
    status: str
    question: str
    answer: str
    audio_size_bytes: int
    frame_id: str
    frame_age_seconds: float
    context_description: Optional[str]
    processing_time_ms: int


class CacheStatsResponse(BaseModel):
    """Statistiques cache"""
    total_frames: int
    max_size: int
    ttl_seconds: int
    frames_with_description: int
    oldest_frame_age_seconds: float
    newest_frame_age_seconds: float
    total_size_mb: float


class HealthResponse(BaseModel):
    """Health check"""
    status: str
    version: str
    gemini_model: str
    cache: CacheStatsResponse
"""
Dependency Injection pour FastAPI
"""
from app.gemini.client import GeminiClient
from app.cache.frame_cache import get_frame_cache, FrameCache
from app.voice.speech_to_text import SpeechToText
from app.voice.text_to_speech import TextToSpeech


# Instances globales (singletons)
_gemini_client = None
_stt_client = None
_tts_client = None


def get_gemini_client() -> GeminiClient:
    """
    Dependency : Client Gemini
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def get_stt_client() -> SpeechToText:
    """
    Dependency : Speech-to-Text (Whisper)
    """
    global _stt_client
    if _stt_client is None:
        from app.models.whisper_loader import get_whisper_model
        _stt_client = SpeechToText(get_whisper_model())
    return _stt_client


def get_tts_client() -> TextToSpeech:
    """
    Dependency : Text-to-Speech
    """
    global _tts_client
    if _tts_client is None:
        _tts_client = TextToSpeech()
    return _tts_client


def get_cache() -> FrameCache:
    """
    Dependency : Cache frames
    """
    return get_frame_cache()

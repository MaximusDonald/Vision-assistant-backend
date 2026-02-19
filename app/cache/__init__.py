"""
Système de cache intelligent pour images et descriptions
"""
from app.cache.frame_cache import FrameCache
from app.cache.models import CachedFrame

__all__ = ["FrameCache", "CachedFrame"]
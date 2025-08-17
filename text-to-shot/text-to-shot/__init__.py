"""
Text to Shots Package
Converts text stories into scenes and shots for film production.
"""

from .core import TextToShotsProcessor
from .models import StoryAnalysisResult

__version__ = "1.0.0"
__all__ = ["TextToShotsProcessor", "StoryAnalysisResult"]
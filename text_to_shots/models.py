"""Data models for the text_to_shots package."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StoryAnalysisResult:
    """Result of story analysis containing scenes and shots."""

    original_story: str
    detected_language: str
    translated_story: Optional[str]
    scenes: str
    shots: str
    references_used: List[str]


"""
Comic Panel Image Sheet Models and Helpers

This module defines the Pydantic models and utility functions for representing,
generating, and exporting comic panel image sheet data, including support for
multiple variants per panel for A/B evaluation and metadata for out-of-frame speakers.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PanelImageSheet(BaseModel):
    panel: int
    variant_id: Optional[str] = None  # e.g., "A", "B", "draft-1"
    filename: str
    scene_description: str
    characters_in_frame: List[str] = Field(default_factory=list)
    characters_not_in_frame: Optional[Dict[str, str]] = (
        None  # name -> context (Zoom, SMS, etc.)
    )
    speech_bubbles: Dict[str, str] = Field(default_factory=dict)
    narration: str
    tone: Optional[str] = None  # e.g., "tense", "reflective", "urgent", etc.

    @property
    def all_speakers(self) -> List[str]:
        return list(self.speech_bubbles.keys())


def infer_characters_not_in_frame(
    speech_bubbles: Dict[str, str],
    characters_in_frame: List[str],
    context_lookup: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, str]]:
    """
    Returns a dict of {name: context} for speakers not in frame.
    context_lookup optionally maps character name to context (Zoom, SMS, etc.).
    """
    not_in_frame = {}
    for name in speech_bubbles.keys():
        if name not in characters_in_frame:
            context = (
                context_lookup.get(name, "off-panel") if context_lookup else "off-panel"
            )
            not_in_frame[name] = context
    return not_in_frame if not_in_frame else None


# Optionally: define a collection structure for chapter or batch export
from typing import Union


class ChapterImageSheet(BaseModel):
    panels: Union[
        Dict[int, List[PanelImageSheet]],  # Grouped by panel number
        List[PanelImageSheet],  # Flat list (if you prefer)
    ]

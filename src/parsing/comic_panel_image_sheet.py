from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChecklistResult(BaseModel):
    teaching_narrative_satisfied: bool
    common_example_aligned: bool
    roles_used_effectively: bool
    missing_elements: Optional[str] = ""
    reviewer_notes: Optional[str] = ""
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}


class SpeechBubble(BaseModel):
    character_name: str
    role: str
    speech: str
    interface: str  # "in_person", "zoom", "slack", etc.

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}


class PanelImageInfo(BaseModel):
    image_filename: str  # e.g., "images/ch1_p1_something.png"
    alt_text: str  # e.g., "Pager blares while Manu’s face glows green..."
    caption: Optional[str] = ""
    width: Optional[int] = 640
    llm_image_prompt: Optional[str] = None
    llm_model: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}


class SceneEnhancement(BaseModel):
    version_id: str
    scene_text: str
    llm_metadata: Dict[str, Any] = Field(default_factory=dict)
    checklist: Optional[ChecklistResult] = None
    panel_image: Optional[PanelImageInfo] = None
    image_prompt_json: Optional[Dict[str, Any]] = None
    user_rating: Optional[str] = ""

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}


class ComicPanelImageSheet(BaseModel):
    panel_id: str
    chapter_id: Optional[str] = None
    panel_index: Optional[int] = None
    scene_description_original: str
    teaching_narrative_original: str
    common_example_original: str
    scene_enhancements: List[SceneEnhancement] = Field(default_factory=list)
    speech_bubbles: List[SpeechBubble] = Field(default_factory=list)
    checklist_results: List[ChecklistResult] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)
    image_prompt_json: Optional[Dict[str, Any]] = None
    current_scene_enhancement: Optional[str] = None
    panel_image: Optional[PanelImageInfo] = (
        None  # Optional, for panel-level legacy/compat
    )

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}

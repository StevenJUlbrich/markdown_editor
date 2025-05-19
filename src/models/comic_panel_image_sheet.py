# comic_panel_image_sheet.py

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChecklistResult(BaseModel):
    teaching_narrative_satisfied: bool
    common_example_aligned: bool
    roles_used_effectively: bool
    missing_elements: Optional[str] = ""
    reviewer_notes: Optional[str] = ""
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class SpeechBubble(BaseModel):
    character_name: str
    role: str
    speech: str  # Leave blank if silent
    interface: str  # "in_person", "zoom", "slack", etc.

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}


class SceneEnhancement(BaseModel):
    version_id: str  # e.g. "v1", "ab-test-a", "llm-20240518-gpt4o"
    scene_text: str
    llm_metadata: Dict[str, Any] = Field(
        default_factory=dict
    )  # e.g., prompt, model, temperature, etc.
    checklist: Optional[ChecklistResult] = None
    image_prompt_json: Optional[Dict[str, Any]] = None  # For DALL-E, Stable Diff, etc.
    user_rating: Optional[str] = ""  # For human QA/A/B ranking

    model_config = {"arbitrary_types_allowed": True, "orm_mode": True}


class ComicPanelImageSheet(BaseModel):
    # Basic panel identifiers
    panel_id: str
    chapter_id: Optional[str] = None
    panel_index: Optional[int] = None

    # Original extracted content for traceability
    scene_description_original: str
    teaching_narrative_original: str
    common_example_original: str

    # All LLM-generated or manually-enhanced scene versions
    scene_enhancements: List[SceneEnhancement] = Field(default_factory=list)

    # Speech bubbles for the current/selected enhancement
    speech_bubbles: List[SpeechBubble] = Field(default_factory=list)

    # Checklist results for LLM/human evaluation (latest or per-version)
    checklist_results: List[ChecklistResult] = Field(default_factory=list)

    # LLM or user metadata for audit/tracing
    processing_metadata: Dict[str, Any] = Field(
        default_factory=dict
    )  # e.g., {"processed_by": "main.py", "llm_model": "gpt-4o"}

    # Downstream output for image prompt pipelines
    image_prompt_json: Optional[Dict[str, Any]] = None

    # Optionally store current selected enhancement for output
    current_scene_enhancement: Optional[str] = None  # version_id

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


# Example usage: Creating a new ComicPanelImageSheet from extracted markdown panel data
# (You can add helper methods to assist with mapping, retrieval, or exporting as needed.)

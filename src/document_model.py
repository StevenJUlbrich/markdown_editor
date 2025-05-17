# document_model.py
from typing import Any, Dict, List, Optional, Union

from mistletoe import Document
from mistletoe.block_token import BlockToken, Heading
from mistletoe.markdown_renderer import MarkdownRenderer
from pydantic import BaseModel, Field

from logging_config import setup_logging

setup_logging()


def _strip_outer_markdown_fences(markdown_text: str) -> str:
    """
    Strips common outer markdown code fences (```markdown ... ``` or ``` ... ```).
    """
    processed_text = markdown_text.strip()
    lines = processed_text.splitlines()

    if len(lines) >= 2:  # Needs at least two lines for fences (e.g., ```\n```)
        starts_with_fence = lines[0].startswith("```")
        ends_with_fence = lines[-1] == "```"

        if starts_with_fence and ends_with_fence:
            # Remove "markdown" language specifier if present on the first line
            if lines[0].startswith("```markdown"):
                # Check if it's just ```markdown or ```markdown followed by content on the same line
                # This simple version assumes ```markdown is on its own line or only has whitespace after.
                # A more robust regex might be needed for complex cases.
                pass  # Handled by slicing [1:-1]

            # Join the content between the fences
            content_between_fences = "\n".join(lines[1:-1])
            return content_between_fences.strip()
    return processed_text  # Return original (stripped of outer whitespace) if not clearly fenced


# --- Helper Function ---
def get_heading_text(heading_node: Heading) -> str:
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):
                text += child.content
    return text.strip()


def render_blocks_to_markdown(
    blocks: List[BlockToken], renderer: MarkdownRenderer
) -> str:
    if not blocks:
        return ""
    valid_blocks = [b for b in blocks if b is not None and isinstance(b, BlockToken)]
    if not valid_blocks:
        return ""
    temp_doc = Document("")
    try:
        temp_doc.children = valid_blocks
    except Exception as e:
        print(f"Error assigning children in render_blocks_to_markdown: {e}")
        print(f"Problematic valid_blocks (first 5): {valid_blocks[:5]}")
        return "Error: Could not render blocks."
    return renderer.render(temp_doc).strip()


_MODULE_LEVEL_RENDERER_INSTANCE: Optional[MarkdownRenderer] = None
try:
    _MODULE_LEVEL_RENDERER_INSTANCE = MarkdownRenderer()
    print(
        "INFO: Module-level MarkdownRenderer instantiated successfully during import of document_model."
    )
except Exception as e:
    print(
        f"CRITICAL ERROR during import: Could not instantiate module-level MarkdownRenderer: {e}"
    )
    print("Further Mistletoe operations will likely fail.")


class SceneAnalysisPydantic(BaseModel):
    scene_types: List[str]
    inferred_by_ai: bool = True
    raw_summary: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    tone: Optional[str] = None  # calm, tense, reflective, chaotic, etc.
    teaching_level: Optional[str] = None  # basic, advanced, metaphorical, meta
    notes: Optional[str] = None


# --- Pydantic Models ---
class H4Pydantic(BaseModel):
    heading_text: str
    mistletoe_h4_block: Optional[Any] = None
    content_markdown: str = ""
    h4_number_in_h3: int


class H3Pydantic(BaseModel):
    heading_text: str
    mistletoe_h3_block: Optional[Any] = None
    initial_content_markdown: str = ""
    h4_sections: List[H4Pydantic] = Field(default_factory=list)
    original_full_markdown: str = ""
    api_suggested_enhancement_needed: Optional[bool] = None
    api_suggested_enhancement_type: Optional[str] = None
    api_suggested_enhancement_reason: Optional[str] = None
    api_improved_markdown: Optional[str] = None
    h3_number_in_panel: int


class PanelPydantic(BaseModel):
    panel_title_text: str
    mistletoe_h2_block: Optional[Any] = None
    h3_sections: List[H3Pydantic] = Field(default_factory=list)
    panel_number_in_doc: Optional[int] = None
    scene_analysis: Optional[SceneAnalysisPydantic] = None


class GenericContentPydantic(BaseModel):
    content_markdown: str
    mistletoe_blocks: List[Any] = Field(default_factory=list)
    title_text: Optional[str] = None


class ChapterPydantic(BaseModel):
    chapter_title_text: str
    mistletoe_h1_block: Optional[Any] = None
    document_elements: List[Union[GenericContentPydantic, PanelPydantic]] = Field(
        default_factory=list
    )

    def get_scene_balance_feedback(self) -> str:
        counts = self.get_scene_distribution()
        total = sum(counts.values())

        feedback = []
        if counts.get("Teaching Scene", 0) > total * 0.7:
            feedback.append(
                "⚠️ Heavy on Teaching Scenes — consider breaking up with chaos or decisions."
            )
        if counts.get("Chaos Scene", 0) < 1:
            feedback.append(
                "⚠️ No Chaos Scene? Add tension, incidents, or operational disruption."
            )
        if "Reflection Scene" not in counts:
            feedback.append(
                "⚠️ Missing Reflection Scene. Consider a quieter, summarizing panel."
            )
        if "Meta Scene" not in counts:
            feedback.append(
                "⚠️ No Meta Scene. Could add conceptual grounding or diagrams."
            )

        return "\n".join(feedback) or "✅ Scene distribution looks balanced."

    def get_scene_distribution(self) -> Dict[str, int]:
        counts = {}
        for el in self.document_elements:
            if isinstance(el, PanelPydantic) and el.scene_analysis:
                for tag in el.scene_analysis.scene_types:
                    counts[tag] = counts.get(tag, 0) + 1
        return counts


# --- Main Document Class ---

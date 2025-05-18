# comic_panel_mapping.py

import re
from typing import Any, Dict, List, Optional

from models.comic_panel_image_sheet import (
    ChecklistResult,
    ComicPanelImageSheet,
    SceneEnhancement,
    SpeechBubble,
)


def extract_panel_sections(panel_md: str) -> Dict[str, str]:
    """
    Parses a single panel markdown text and returns a dict of key sections.
    Assumes headings are consistently used: 'Scene Description', 'Teaching Narrative', etc.
    """
    sections = {}
    current_section = None
    buffer = []

    for line in panel_md.splitlines():
        h3_match = re.match(r"^###\s+(.+)$", line.strip())
        if h3_match:
            # Save previous section
            if current_section and buffer:
                sections[current_section] = "\n".join(buffer).strip()
            current_section = h3_match.group(1).strip().lower()
            buffer = []
        elif current_section:
            buffer.append(line)
    if current_section and buffer:
        sections[current_section] = "\n".join(buffer).strip()
    return sections


def get_panel_id(panel_md: str) -> str:
    """
    Extracts a panel ID from a markdown header line (e.g., '## Panel 1: ...').
    """
    match = re.search(r"^##\s*Panel\s*([0-9]+)", panel_md, re.MULTILINE)
    return f"panel_{match.group(1)}" if match else "panel_unknown"


def map_to_comic_panel_image_sheet(
    panel_md: str, chapter_id: Optional[str] = None, panel_index: Optional[int] = None
) -> ComicPanelImageSheet:
    """
    Given a markdown block for a single panel, creates a ComicPanelImageSheet instance.
    """
    sections = extract_panel_sections(panel_md)
    panel_id = get_panel_id(panel_md)
    scene_desc = sections.get("scene description", "")
    teaching = sections.get("teaching narrative", "")
    common_example = sections.get("common example of the problem", "")

    panel_sheet = ComicPanelImageSheet(
        panel_id=panel_id,
        chapter_id=chapter_id,
        panel_index=panel_index,
        scene_description_original=scene_desc,
        teaching_narrative_original=teaching,
        common_example_original=common_example,
        # All other fields start empty, to be filled by LLM or later steps
    )
    return panel_sheet


def extract_all_panels_from_markdown(md_text: str) -> List[str]:
    """
    Splits a markdown file into panel-level strings based on '## Panel' headers.
    """
    panel_blocks = re.split(r"^##\s*Panel", md_text, flags=re.MULTILINE)
    result = []
    for idx, block in enumerate(panel_blocks):
        if idx == 0 and not block.strip().startswith("1"):
            continue  # skip preamble before first panel
        result.append("## Panel" + block)
    return [panel for panel in result if "scene description" in panel.lower()]


def create_panel_sheets_from_markdown(
    md_text: str, chapter_id: Optional[str] = None
) -> List[ComicPanelImageSheet]:
    """
    Converts a markdown file into a list of ComicPanelImageSheet objects.
    """
    panel_blocks = extract_all_panels_from_markdown(md_text)
    sheets = []
    for idx, panel_md in enumerate(panel_blocks):
        sheet = map_to_comic_panel_image_sheet(
            panel_md, chapter_id, panel_index=idx + 1
        )
        sheets.append(sheet)
    return sheets


# Example usage:
# with open("my_chapter.md", "r", encoding="utf-8") as f:
#     md_text = f.read()
# panel_sheets = create_panel_sheets_from_markdown(md_text, chapter_id="chapter_01")

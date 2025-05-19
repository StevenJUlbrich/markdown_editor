# chapter_scene_json_exporter.py

import json
import os
from typing import Dict, List

from models.comic_panel_image_sheet import ComicPanelImageSheet


def export_chapter_to_json(
    enriched_sheets: List[ComicPanelImageSheet], output_json_path: str
):
    """
    Writes all enriched ComicPanelImageSheet objects for a chapter to a JSON file.
    Pydantic v2: uses .model_dump() for export.
    """
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in enriched_sheets], f, indent=2)
    print(f"Chapter scene data saved to: {output_json_path}")


def export_all_chapters_to_json(
    sheets_by_chapter: Dict[str, List[ComicPanelImageSheet]], output_dir: str
):
    """
    Exports all enriched ComicPanelImageSheet lists by chapter.
    Each key in sheets_by_chapter is a chapter_id or filename stem.
    Output: one JSON per chapter in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    for chapter_id, sheets in sheets_by_chapter.items():
        out_path = os.path.join(output_dir, f"{chapter_id}_enriched.json")
        export_chapter_to_json(sheets, out_path)

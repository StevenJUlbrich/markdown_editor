# panel_markdown_exporter.py

import os
from typing import List, Optional

from models.comic_panel_image_sheet import ComicPanelImageSheet


def build_panel_markdown_block(
    panel_sheet: ComicPanelImageSheet, enhancement_index: int = 0
) -> str:
    """
    Build upgraded markdown for a single panel, using enriched data and image info.
    enhancement_index: which SceneEnhancement to use (default: first).
    """
    # Defensive: Handle missing enhancements gracefully
    se = None
    if panel_sheet.scene_enhancements and 0 <= enhancement_index < len(
        panel_sheet.scene_enhancements
    ):
        se = panel_sheet.scene_enhancements[enhancement_index]

    panel_image = se.panel_image if se and se.panel_image else None

    lines = []

    # H2: Panel Header (title can be improved as needed)
    title = f"Panel {panel_sheet.panel_index or '?'}"
    lines.append(f"## {title}")

    # H3: Scene Description (use LLM summary if available, fallback to original)
    lines.append("### Scene Description")
    if se and se.llm_metadata.get("neutral_scene_summary"):
        summary = se.llm_metadata["neutral_scene_summary"]
        lines.append(summary.strip())
    elif se and se.scene_text:
        lines.append(se.scene_text.strip())
    else:
        lines.append(panel_sheet.scene_description_original.strip())

    # H4: Panel Image (if present)
    if panel_image:
        lines.append("#### Panel Image")
        width_str = f"{{width={panel_image.width}}}" if panel_image.width else ""
        lines.append(
            f"![{panel_image.alt_text}]({panel_image.image_filename}){width_str}"
        )

    # H3: Teaching Narrative
    lines.append("### Teaching Narrative")
    lines.append(panel_sheet.teaching_narrative_original.strip())

    # H3: Common Example of the Problem
    lines.append("### Common Example of the Problem")
    lines.append(panel_sheet.common_example_original.strip())

    # Future: Add additional sections or enrichment as needed

    return "\n\n".join(lines)


def export_markdown_for_chapter(
    sheets: List[ComicPanelImageSheet],
    output_md_path: str,
    chapter_title: Optional[str] = None,
) -> None:
    """
    Export a complete markdown file for a chapter, including all panels.
    Each panel is separated with a horizontal rule.
    """
    lines = []
    if chapter_title:
        lines.append(f"# {chapter_title}\n")

    for sheet in sheets:
        panel_md = build_panel_markdown_block(sheet)
        lines.append(panel_md)
        lines.append("\n---\n")  # Horizontal rule between panels

    full_md = "\n".join(lines)
    with open(output_md_path, "w", encoding="utf-8") as out:
        out.write(full_md)
    print(f"Markdown exported: {output_md_path}")


def export_markdown_for_directory(
    sheets_by_filename: dict, output_dir: str, chapter_titles: Optional[dict] = None
) -> None:
    """
    Batch export markdown for multiple chapters.
    sheets_by_filename: Dict[str, List[ComicPanelImageSheet]]
    chapter_titles: Optional Dict[str, str] for custom H1 per chapter
    """
    os.makedirs(output_dir, exist_ok=True)
    for fname, sheets in sheets_by_filename.items():
        chapter_title = (
            chapter_titles[fname]
            if chapter_titles and fname in chapter_titles
            else None
        )
        base = os.path.splitext(fname)[0]
        out_md = os.path.join(output_dir, f"{base}_final.md")
        export_markdown_for_chapter(sheets, out_md, chapter_title=chapter_title)


# Example CLI use:
if __name__ == "__main__":
    import json

    # Example: Load enriched panels from JSON, export to markdown
    enriched_json = "chapter_01_enriched.json"
    output_md = "chapter_01_final.md"

    with open(enriched_json, "r", encoding="utf-8") as f:
        enriched_sheets = [ComicPanelImageSheet.model_validate(p) for p in json.load(f)]

    export_markdown_for_chapter(
        sheets=enriched_sheets,
        output_md_path=output_md,
        chapter_title="Chapter 1: On-Call Chaos",
    )

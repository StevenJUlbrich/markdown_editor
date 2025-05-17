import json
from pathlib import Path
from logging_config import get_logger

logger = get_logger(__name__)


def export_chapter_scene_report(panel_json_path: Path, output_md_path: Path):
    with open(panel_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    panels = data.get("panels", [])
    if not panels:
        logger.warning("No panels found in the input JSON.")
        return

    lines = ["# 📘 Scene Analysis Report\n"]

    for panel in panels:
        panel_id = panel.get("panel")
        panel_title = panel.get("filename", "").replace("_", " ").replace(".png", "")
        analysis = panel.get("scene_analysis", {})

        lines.append(f"## Panel {panel_id}: {panel_title}")
        lines.append(f"**Scene Types**: {', '.join(analysis.get('scene_types', []))}")
        lines.append(f"**Tone**: {analysis.get('tone', 'N/A')}")
        lines.append(f"**Teaching Level**: {analysis.get('teaching_level', 'N/A')}")
        lines.append(f"**Location**: {analysis.get('location', 'N/A')}")
        lines.append(f"**Time of Day**: {analysis.get('time_of_day', 'N/A')}")
        notes = analysis.get("notes", "").strip()
        if notes:
            lines.append(f"**Notes**:\n> {notes}")
        lines.append("\n---\n")

    output_md_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Scene report saved to %s", output_md_path)


# Example usage
if __name__ == "__main__":
    panel_json = Path(
        "D:\Development_Personal\SRE-Training\SRE CORE PRACTICES\day 03\character\chapter_03_character_sheet.json"
    )  # Update this if needed
    output_md = Path("chapter_scene_report.md")
    export_chapter_scene_report(panel_json, output_md)

import json
from pathlib import Path
from typing import List

from document_model import PanelPydantic
from markdown_document import MarkdownDocument
from openai_service import generate_scene_analysis_from_ai


def analyze_markdown_file(md_path: Path, character_json_path: Path) -> dict:
    doc = MarkdownDocument(filepath=str(md_path))
    if not doc.chapter_model:
        print(f"⚠️ Failed to parse: {md_path.name}")
        return {}

    report = {
        "filename": md_path.name,
        "panels": [],
        "scene_type_counts": {},
    }

    for panel in doc.chapter_model.document_elements:
        if not isinstance(panel, PanelPydantic):
            continue

        sections = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        scene_md = sections.get("Scene Description", "")
        teaching_md = sections.get("Teaching Narrative", "")

        scene_analysis = generate_scene_analysis_from_ai(scene_md, teaching_md)
        panel.scene_analysis = scene_analysis

        for tag in scene_analysis.scene_types:
            report["scene_type_counts"][tag] = (
                report["scene_type_counts"].get(tag, 0) + 1
            )

        report["panels"].append(
            {
                "panel_id": panel.panel_number_in_doc,
                "panel_title": panel.panel_title_text,
                "scene_analysis": scene_analysis.model_dump(),
            }
        )

    return report


def summarize_feedback(scene_type_counts: dict, total_panels: int) -> List[str]:
    feedback = []
    if scene_type_counts.get("Teaching Scene", 0) > total_panels * 0.7:
        feedback.append(
            "⚠️ High ratio of Teaching Scenes. Add variation (Chaos, Reflection, etc)."
        )
    if "Chaos Scene" not in scene_type_counts:
        feedback.append("⚠️ No Chaos Scenes. Consider adding narrative tension.")
    if "Reflection Scene" not in scene_type_counts:
        feedback.append(
            "⚠️ No Reflection Scenes. Add space for takeaways or retrospectives."
        )
    if "Meta Scene" not in scene_type_counts:
        feedback.append(
            "ℹ️ No Meta Scenes. You could include one to reinforce concepts."
        )
    return feedback or ["✅ Scene distribution looks healthy."]


def write_markdown_report(report_data: dict, output_path: Path):
    lines = [f"# Scene Analysis Report: `{report_data['filename']}`\n"]

    total = len(report_data["panels"])
    lines.append(f"## 📊 Scene Type Distribution (Total Panels: {total})")
    for k, v in report_data["scene_type_counts"].items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")

    feedback = summarize_feedback(report_data["scene_type_counts"], total)
    lines.append("## 🧠 Structural Feedback")
    lines.extend([f"- {f}" for f in feedback])
    lines.append("\n---\n")

    for panel in report_data["panels"]:
        sa = panel["scene_analysis"]
        lines.append(f"### Panel {panel['panel_id']}: {panel['panel_title']}")
        lines.append(f"- **Scene Types**: {', '.join(sa.get('scene_types', []))}")
        lines.append(f"- **Tone**: {sa.get('tone', 'N/A')}")
        lines.append(f"- **Teaching Level**: {sa.get('teaching_level', 'N/A')}")
        lines.append(f"- **Location**: {sa.get('location', 'N/A')}")
        lines.append(f"- **Time of Day**: {sa.get('time_of_day', 'N/A')}")
        notes = sa.get("notes", "").strip()
        if notes:
            lines.append(f"- **Notes**: {notes}")
        lines.append("\n---\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Report saved to: {output_path}")


def main():
    print("\n📘 Scene Report Generator\n")

    md_input = input("Enter Markdown file or folder path: ").strip()
    character_json_path = input("Enter character JSON path: ").strip()
    output_path = input(
        "Enter output report filename (e.g., scene_report.md): "
    ).strip()

    md_path = Path(md_input)
    char_path = Path(character_json_path)
    out_path = Path(output_path)

    if not char_path.exists():
        print("❌ Character JSON file not found.")
        return

    md_files = [md_path] if md_path.is_file() else list(md_path.glob("*.md"))
    if not md_files:
        print("❌ No markdown files found.")
        return

    for file in md_files:
        print(f"\n🔍 Analyzing {file.name}...")
        report_data = analyze_markdown_file(file, char_path)
        if report_data:
            if len(md_files) > 1:
                file_output_path = out_path.with_name(f"{file.stem}_scene_report.md")
            else:
                file_output_path = out_path
            write_markdown_report(report_data, file_output_path)


if __name__ == "__main__":
    main()

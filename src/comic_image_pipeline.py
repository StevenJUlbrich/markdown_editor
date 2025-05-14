import json
from pathlib import Path

from document_model import MarkdownDocument
from generate_character_profiles import generate_character_profiles_for_roles
from logging_config import get_logger
from openai_service import rewrite_scene_and_teaching_as_summary
from suggest_character_roles import suggest_character_roles_from_context

logger = get_logger(__name__)


def process_chapter_for_visual_panels(
    chapter_md_path: Path,
    character_json_path: Path,
    output_md_path: Path,
    output_json_path: Path,
    images_folder: str = "images",
    characters_per_role: int = 2,
):
    doc = MarkdownDocument(filepath=str(chapter_md_path))
    if not doc.chapter_model:
        logger.error("❌ Failed to parse: %s", chapter_md_path.name)
        return

    # Load character profile JSON
    with open(character_json_path, "r", encoding="utf-8") as f:
        character_data = json.load(f)

    existing_roles = {
        c["role"] for c in character_data.get("characters", {}).values() if "role" in c
    }

    all_panel_json = []
    new_roles_needed = set()

    for panel in doc.chapter_model.document_elements:
        if not hasattr(panel, "panel_number_in_doc"):
            continue

        panel_id = panel.panel_number_in_doc
        panel_title = panel.panel_title_text

        # Step 1: Extract sections
        sections = doc.extract_named_sections_from_panel(panel_id)
        scene_md = sections.get("Scene Description", "")
        teaching_md = sections.get("Teaching Narrative", "")
        if not scene_md.strip() and not teaching_md.strip():
            logger.warning(
                "Skipping Panel ID %s (%s): no scene or teaching content",
                panel_id,
                panel_title,
            )
            continue

        # Step 2: Suggest roles
        suggested_roles = suggest_character_roles_from_context(
            panel_title=panel_title,
            scene_description_md=scene_md,
            teaching_narrative_md=teaching_md,
        )

        # Step 3: Detect and collect missing roles
        for role in suggested_roles:
            if role not in existing_roles:
                new_roles_needed.add(role)

        # Step 4: Rewrite scene + teaching as summary
        scene_summary = rewrite_scene_and_teaching_as_summary(scene_md, teaching_md)

        # Step 5: Generate JSON entry for this panel
        filename = f"{chapter_md_path.stem}_panel_{panel_id}.png"
        panel_json = {
            "panel_id": panel_id,
            "panel_title": panel_title,
            "filename": f"{images_folder}/{filename}",
            "summary": scene_summary,
            "suggested_roles": suggested_roles,
            "characters_in_frame": [],  # to be filled later
            "speech_bubbles": [],  # optional
            "narration": "",  # optional
        }
        all_panel_json.append(panel_json)

        # Step 6: Insert image into markdown
        image_markdown = f"![{panel_title}]({images_folder}/{filename})"
        new_scene_md = f"{scene_summary}\n\n{image_markdown}"
        doc.update_named_section_in_panel(panel_id, "Scene Description", new_scene_md)

    # Step 7: Generate new characters if needed
    if new_roles_needed:
        generate_character_profiles_for_roles(
            list(new_roles_needed),
            input_json_path=character_json_path,
            output_json_path=character_json_path,
            characters_per_role=characters_per_role,
        )

    # Step 8: Save image metadata JSON
    with open(output_json_path, "w", encoding="utf-8") as jf:
        json.dump(all_panel_json, jf, indent=2, ensure_ascii=False)

    # Step 9: Save updated markdown
    doc.save_document(str(output_md_path))

    logger.info("✅ Chapter processed and saved: %s", output_md_path)

import json
from pathlib import Path
from typing import Dict

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

        # Step 4: Rewrite scene + teaching as summary (min 350 chars)
        scene_summary = rewrite_scene_and_teaching_as_summary(scene_md, teaching_md)
        if len(scene_summary) < 350:
            scene_summary = scene_summary + " " + "(Expanded for length.)"
        if len(scene_summary) > 750:
            scene_summary = scene_summary[:745] + "..."

        # Step 5: Assign characters
        named_characters = []
        used_names = set()
        for role in suggested_roles:
            candidates = [
                name
                for name, profile in character_data["characters"].items()
                if profile.get("role") == role and name not in used_names
            ]
            if candidates:
                chosen = candidates[0]
                named_characters.append(chosen)
                used_names.add(chosen)

        # Step 6: Build filename
        panel_index = panel_id
        chapter_num = chapter_md_path.stem[-2:]
        safe_title = (
            panel_title.lower()
            .replace(" ", "-")
            .replace(":", "")
            .replace("'", "")
            .replace(",", "")
        )
        filename = f"ch{chapter_num}_p{panel_index}_{safe_title}.png"

        # Step 7: Build image reference markdown
        image_markdown = f"![{panel_title}]({images_folder}/{filename})"
        new_scene_md = f"{scene_summary}\n\n{image_markdown}"
        doc.update_named_section_in_panel(panel_id, "Scene Description", new_scene_md)

        # Step 8: Build full panel JSON entry
        speech_bubble_dict = {name: "" for name in named_characters}

        panel_json = {
            "panel": panel_index,
            "filename": filename,
            "scene_description": scene_summary,
            "characters_in_frame": named_characters,
            "speech_bubbles": speech_bubble_dict,
            "narration": scene_summary,
        }

        all_panel_json.append(panel_json)

    # Step 9: Generate missing characters if needed
    if new_roles_needed:
        generate_character_profiles_for_roles(
            list(new_roles_needed),
            input_json_path=character_json_path,
            output_json_path=character_json_path,
            characters_per_role=characters_per_role,
        )
        # Refresh character data to include new ones
        with open(character_json_path, "r", encoding="utf-8") as f:
            character_data = json.load(f)

    # Step 10: Save chapter image JSON
    with open(output_json_path, "w", encoding="utf-8") as jf:
        json.dump({"panels": all_panel_json}, jf, indent=2, ensure_ascii=False)

    # Step 11: Save updated markdown
    doc.save_document(str(output_md_path))
    logger.info("✅ Chapter processed and saved: %s", output_md_path)


def generate_image_prompt_from_panel(panel_json: Dict, character_data: Dict) -> str:
    """
    Constructs a detailed image generation prompt for a comic panel,
    including scene summary and visual descriptions of each character.

    Args:
        panel_json: One panel entry from chapter_images.json
        character_data: Full character JSON dictionary

    Returns:
        A complete prompt string suitable for image generation
    """
    summary = panel_json.get("summary", "").strip()
    if not summary:
        return "Scene summary missing."

    # Ensure minimum length
    if len(summary) < 350:
        summary = f"This scene should be more detailed: {summary}"
    elif len(summary) > 750:
        summary = summary[:745] + "..."

    characters = panel_json.get("characters_in_frame", [])
    character_descriptions = []

    for name in characters:
        profile = character_data.get("characters", {}).get(name, {})
        if not profile:
            continue
        role = profile.get("role", "Unknown role")
        visual_tags = profile.get("visual_tags", [])
        tag_desc = ", ".join(visual_tags)
        character_descriptions.append(f"- {name}: {role}. Visual tags: {tag_desc}")

    character_block = (
        "\n".join(character_descriptions)
        if character_descriptions
        else "No character descriptions available."
    )

    # Final formatted image prompt
    image_prompt = f"""
Scene:
{summary}

Characters:
{character_block}

Style:
Comic panel illustration, digital art, clean lines.
Facial expressions should reflect emotion. The setting should be a realistic tech workspace.
Make sure the scene reads clearly as a single moment in time.
    """.strip()

    return image_prompt


def export_prompts_from_json(
    panel_json_path: Path, character_json_path: Path, output_txt_path: Path
):
    with open(panel_json_path, "r", encoding="utf-8") as f:
        panels = json.load(f)
    with open(character_json_path, "r", encoding="utf-8") as f:
        character_data = json.load(f)

    prompts = []
    for panel in panels:
        prompt = generate_image_prompt_from_panel(panel, character_data)
        prompts.append(f"--- Prompt for Panel {panel.get('panel_id')} ---\n{prompt}\n")

    with open(output_txt_path, "w", encoding="utf-8") as outf:
        outf.write("\n\n".join(prompts))

    print(f"✅ Exported {len(prompts)} prompts to {output_txt_path}")

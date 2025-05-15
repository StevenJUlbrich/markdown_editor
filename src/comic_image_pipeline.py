import json
from pathlib import Path
from typing import Dict, Optional

from document_model import MarkdownDocument
from generate_character_profiles import generate_character_profiles_for_roles
from logging_config import get_logger
from openai_service import (
    generate_narration_title_for_panel,
    generate_speech_bubbles_for_panel,
    rewrite_scene_and_teaching_as_summary,
    suggest_character_roles_from_context,
)

logger = get_logger(__name__)


def process_panel_to_json(
    doc: MarkdownDocument,
    panel,
    character_data: Dict,
    character_json_path: Path,
    characters_per_role: int,
    chapter_prefix: str,
    images_folder: str,
) -> Optional[Dict]:
    import json
    from pathlib import Path

    from openai_service import infer_scene_tags_for_panel

    panel_id = panel.panel_number_in_doc
    panel_title = panel.panel_title_text

    sections = doc.extract_named_sections_from_panel(panel_id)
    scene_md = sections.get("Scene Description", "")
    teaching_md = sections.get("Teaching Narrative", "")

    if not scene_md.strip() and not teaching_md.strip():
        logger.warning("Panel %s has no Scene or Teaching Narrative.", panel_title)
        return None

    # 🔹 NEW: Get detailed AI-driven scene analysis
    from openai_service import generate_scene_analysis_from_ai

    scene_analysis = generate_scene_analysis_from_ai(scene_md, teaching_md)
    panel.scene_analysis = scene_analysis

    # 🔹 STEP 1: Tag scene type(s)
    scene_tags = infer_scene_tags_for_panel(scene_md, teaching_md)

    # 🔹 STEP 2: Get required roles from tag map
    tag_to_roles = {
        "Teaching Scene": ["Senior SRE", "Junior Developer", "Product Owner"],
        "Chaos Scene": ["Support Engineer", "Angry Customer", "SRE Engineer"],
        "Reflection Scene": ["Senior SRE", "Product Owner"],
        "Meta Scene": ["Senior SRE"],
    }
    required_roles = set()
    for tag in scene_tags:
        required_roles.update(tag_to_roles.get(tag, []))
    required_roles = list(required_roles)

    # 🔹 STEP 3: Ensure characters for needed roles exist
    existing_roles = {
        c["role"] for c in character_data.get("characters", {}).values() if "role" in c
    }
    new_roles = [r for r in required_roles if r not in existing_roles]
    if new_roles:
        generate_character_profiles_for_roles(
            new_roles,
            input_json_path=character_json_path,
            output_json_path=character_json_path,
            characters_per_role=characters_per_role,
        )
        with open(character_json_path, "r", encoding="utf-8") as f:
            character_data = json.load(f)

    # 🔹 STEP 4: Assign characters for required roles
    role_to_character = {}
    used_names = set()
    for role in required_roles:
        candidates = [
            name
            for name, profile in character_data["characters"].items()
            if profile.get("role") == role and name not in used_names
        ]
        if candidates:
            selected = candidates[0]
            role_to_character[role] = selected
            used_names.add(selected)

    characters_in_frame = list(role_to_character.values())

    # 🔹 STEP 5: Rewrite scene summary
    scene_summary = rewrite_scene_and_teaching_as_summary(scene_md, teaching_md).strip()
    if len(scene_summary) < 350:
        scene_summary += " (Expanded.)"
    elif len(scene_summary) > 750:
        scene_summary = scene_summary[:745] + "..."

    # 🔹 STEP 6: Generate speech bubbles and narration
    speech_bubbles = generate_speech_bubbles_for_panel(
        scene_summary, characters_in_frame, character_data
    )
    narration = generate_narration_title_for_panel(scene_md, teaching_md)

    # 🔹 STEP 7: Generate image markdown
    safe_title = (
        panel_title.lower()
        .replace(" ", "-")
        .replace(":", "")
        .replace("'", "")
        .replace(",", "")
    )
    filename = f"{chapter_prefix}_p{panel_id}_{safe_title}.png"
    image_markdown = f"![{panel_title}]({images_folder}/{filename})"
    updated_scene = f"{scene_summary}\n\n{image_markdown}"
    doc.update_named_section_in_panel(panel_id, "Scene Description", updated_scene)

    # 🔹 STEP 8: Return structured JSON with roles
    return {
        "panel": panel_id,
        "filename": filename,
        "scene_tags": scene_tags,
        "scene_description": scene_summary,
        "characters_in_frame": characters_in_frame,
        "character_roles": role_to_character,
        "speech_bubbles": speech_bubbles,
        "narration": narration,
        "scene_analysis": scene_analysis.model_dump(),
    }


def process_chapter_for_visual_panels(
    chapter_md_path: Path,
    character_json_path: Path,
    output_md_path: Path,
    output_json_path: Path,
    images_folder: str = "images",
    characters_per_role: int = 2,
):

    # Check if the input path is a file
    if not chapter_md_path.is_file():
        logger.error("❌ Input path is not a file: %s", chapter_md_path)
        return

    doc = MarkdownDocument(filepath=str(chapter_md_path))

    if not doc.chapter_model:
        logger.error("❌ Failed to parse: %s", chapter_md_path.name)
        return

    # Load character profile JSON
    with open(character_json_path, "r", encoding="utf-8") as f:
        character_data = json.load(f)

    all_panel_json = []
    chapter_prefix = chapter_md_path.stem.lower()  # e.g. "chapter_03"

    for panel in doc.chapter_model.document_elements:
        if not hasattr(panel, "panel_number_in_doc"):
            continue

        panel_json = process_panel_to_json(
            doc=doc,
            panel=panel,
            character_data=character_data,
            character_json_path=character_json_path,
            characters_per_role=characters_per_role,
            chapter_prefix=chapter_prefix,
            images_folder=images_folder,
        )

        if panel_json:
            all_panel_json.append(panel_json)

    # Save final chapter image JSON
    with open(output_json_path, "w", encoding="utf-8") as jf:
        json.dump({"panels": all_panel_json}, jf, indent=2, ensure_ascii=False)

    # Save final markdown file
    doc.save_document(str(output_md_path))
    logger.info("✅ Chapter markdown + panel JSON saved.")


def generate_image_prompt_from_panel(panel_json: Dict, character_data: Dict) -> str:
    """
    Constructs a detailed image generation prompt for a comic panel,
    using structured character-role mapping and scene tags.

    Args:
        panel_json: A single panel entry from chapter_image.json
        character_data: Full character JSON dictionary

    Returns:
        A formatted prompt string suitable for image generation
    """
    # Step 1: Extract scene summary
    summary = panel_json.get("scene_description", "").strip()
    if not summary:
        return "Scene summary missing."

    # Step 2: Determine characters and roles
    characters = panel_json.get("characters_in_frame", [])
    role_map = panel_json.get("character_roles", {})

    character_descriptions = []

    for name in characters:
        profile = character_data.get("characters", {}).get(name, {})
        if not profile:
            continue

        role = profile.get("role", "Unknown role")
        visual_tags = profile.get("visual_tags", [])
        tag_desc = ", ".join(visual_tags)
        motion = profile.get("motion_rules", "neutral movement")
        tone = profile.get("voice_tone", "neutral")

        character_descriptions.append(
            f"- **{name}** ({role}): {tag_desc}\n  - Motion: {motion}\n  - Voice tone: {tone}"
        )

    if not character_descriptions:
        character_descriptions.append("No character descriptions available.")

    scene_tags = panel_json.get("scene_tags", [])
    scene_type_str = ", ".join(scene_tags) if scene_tags else "Unspecified scene type"

    # Step 3: Build final prompt
    prompt = f"""
**Scene Type**: {scene_type_str}

**Scene Summary**:
{summary}

**Characters**:
{chr(10).join(character_descriptions)}

**Instructions**:
- Create a comic panel illustration in clean digital style.
- Use expressive body language and facial expressions to show the emotional tone.
- Layout should reflect a single snapshot in time, clearly showing the tension or insight.
- If the scene is a Teaching or Reflection scene, the Senior SRE (e.g., Hector or Juana) should appear calm, analytical, or observational.
- If the scene is a Chaos scene, show action, tension, or confusion.
- Background elements like terminals, dashboards, or conference tables should match the setting.

**Visual Style**:
Modern comic panel, clean lines, expressive characters, detailed backgrounds.
"""
    return prompt.strip()


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

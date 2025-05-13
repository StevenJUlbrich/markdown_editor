import json
from pathlib import Path
from typing import Dict, List

from document_model import MarkdownDocument, PanelPydantic
from logging_config import get_logger
from suggest_character_roles import suggest_character_roles_from_context

logger = get_logger(__name__)


def extract_roles_per_panel(doc: MarkdownDocument) -> Dict[str, List[str]]:
    """Returns a map of panel title → suggested roles."""
    results = {}
    if not doc.chapter_model:
        return results

    for element in doc.chapter_model.document_elements:
        if isinstance(element, PanelPydantic):
            section_map = doc.extract_named_sections_from_panel(
                element.panel_number_in_doc
            )
            scene = section_map.get("Scene Description", "")
            teaching = section_map.get("Teaching Narrative", "")
            if scene.strip() or teaching.strip():
                roles = suggest_character_roles_from_context(
                    panel_title=element.panel_title_text,
                    scene_description_md=scene,
                    teaching_narrative_md=teaching,
                )
                results[element.panel_title_text] = roles
    return results


def get_valid_roles_from_character_json(json_path: Path) -> List[str]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return list(
            {
                char["role"]
                for char in data.get("characters", {}).values()
                if "role" in char
            }
        )


def validate_roles(
    character_json: Path, markdown_dir: Path
) -> List[Dict[str, List[str]]]:
    valid_roles = set(get_valid_roles_from_character_json(character_json))
    logger.info("Loaded %d defined roles from character config.", len(valid_roles))

    validation_report = []
    for md_file in markdown_dir.glob("*.md"):
        doc = MarkdownDocument(filepath=str(md_file))
        logger.info("Checking file: %s", md_file.name)
        panel_roles = extract_roles_per_panel(doc)
        for panel_title, roles in panel_roles.items():
            missing = [r for r in roles if r not in valid_roles]
            if missing:
                logger.warning(
                    "❌ Panel '%s' in '%s' has undefined roles: %s",
                    panel_title,
                    md_file.name,
                    missing,
                )
                validation_report.append(
                    {
                        "file": md_file.name,
                        "panel": panel_title,
                        "missing_roles": missing,
                    }
                )
            else:
                logger.info(
                    "✅ Panel '%s' roles in '%s' are all mapped.",
                    panel_title,
                    md_file.name,
                )
    return validation_report

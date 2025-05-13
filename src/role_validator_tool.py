import json
from pathlib import Path
from typing import Dict, List

from document_model import MarkdownDocument, PanelPydantic
from suggest_character_roles import suggest_character_roles_from_context


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


def validate_roles(character_json: Path, markdown_dir: Path):
    valid_roles = set(get_valid_roles_from_character_json(character_json))
    print(f"Loaded {len(valid_roles)} defined roles from character config.")

    for md_file in markdown_dir.glob("*.md"):
        doc = MarkdownDocument(filepath=str(md_file))
        print(f"\n📘 Checking {md_file.name}...")
        panel_roles = extract_roles_per_panel(doc)
        for panel_title, roles in panel_roles.items():
            missing = [r for r in roles if r not in valid_roles]
            if missing:
                print(f"  ❌ Panel '{panel_title}' has undefined roles: {missing}")
            else:
                print(f"  ✅ Panel '{panel_title}' roles are all mapped.")


# Example usage (modify paths as needed):
# validate_roles(Path("merged_character_sheet.json"), Path("./chapters/topic1"))

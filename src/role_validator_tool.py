"""
Improved role validator tool that properly handles nested list types
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Union

from document_model import MarkdownDocument, PanelPydantic
from logging_config import get_logger
from openai_service import suggest_character_roles_from_context

logger = get_logger(__name__)


def flatten_roles(roles: Union[List[Any], Any]) -> List[str]:
    """
    Recursively flattens a potentially nested list structure of roles into a single list of strings.

    Args:
        roles: A list (potentially nested) or single item that contains roles

    Returns:
        A flat list of string roles with no nesting
    """
    flattened = []

    # Handle the case when roles is not a list
    if not isinstance(roles, list):
        if isinstance(roles, str):
            return [roles]
        logger.warning(
            f"Non-list, non-string role found: {roles} (type: {type(roles).__name__})"
        )
        return []

    # Process the list recursively
    for item in roles:
        if isinstance(item, str):
            flattened.append(item)
        elif isinstance(item, list):
            # Recursively flatten nested lists
            flattened.extend(flatten_roles(item))
        else:
            logger.warning(
                f"Unexpected role type in list: {item} (type: {type(item).__name__})"
            )

    return flattened


def extract_roles_per_panel(doc: MarkdownDocument) -> Dict[str, List[str]]:
    """
    Returns a map of panel title → suggested roles, ensuring all roles are properly flattened.

    Args:
        doc: The document model to extract roles from

    Returns:
        Dictionary mapping panel titles to lists of role strings
    """
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
                # Get roles from OpenAI service
                parsed_roles = suggest_character_roles_from_context(
                    panel_title=element.panel_title_text,
                    scene_description_md=scene,
                    teaching_narrative_md=teaching,
                )

                # Ensure roles are flattened to a simple list of strings
                flattened_roles = flatten_roles(parsed_roles)

                if flattened_roles:
                    results[element.panel_title_text] = flattened_roles
                    logger.info(
                        "Panel '%s': Found %d role(s): %s",
                        element.panel_title_text,
                        len(flattened_roles),
                        flattened_roles,
                    )
                else:
                    logger.warning(
                        "No valid roles found for panel '%s' after flattening.",
                        element.panel_title_text,
                    )

    return results


def get_valid_roles_from_character_json(json_path: Path) -> List[str]:
    """
    Extract all unique role strings from the character JSON file.

    Args:
        json_path: Path to the character JSON file

    Returns:
        List of unique role strings
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        roles = []

        # Extract roles from characters
        for char in data.get("characters", {}).values():
            if "role" in char:
                role_value = char["role"]

                # Handle potential nested list structures in roles
                if isinstance(role_value, str):
                    roles.append(role_value)
                elif isinstance(role_value, list):
                    roles.extend(flatten_roles(role_value))
                else:
                    logger.warning(
                        f"Unexpected role type in character JSON: {role_value} "
                        f"(type: {type(role_value).__name__})"
                    )

        # Return unique role strings
        return list(set(roles))


def validate_roles(
    character_json: Path, markdown_dir: Path
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Validates that all character roles found in markdown files exist in the character JSON.

    Args:
        character_json: Path to the character JSON file
        markdown_dir: Path to the directory containing markdown files

    Returns:
        List of dictionaries with information about missing roles
    """
    # Get all valid roles from the character JSON
    valid_roles = set(get_valid_roles_from_character_json(character_json))
    logger.info("Loaded %d defined roles from character config.", len(valid_roles))

    validation_report = []
    for md_file in markdown_dir.glob("*.md"):
        doc = MarkdownDocument(filepath=str(md_file))
        logger.info("Checking file: %s", md_file.name)

        # Get roles for each panel
        panel_roles = extract_roles_per_panel(doc)

        for panel_title, roles in panel_roles.items():
            # Check if roles are missing - ensure we're working with flattened strings
            flattened_roles = flatten_roles(roles)
            missing = [r for r in flattened_roles if r not in valid_roles]

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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: python role_validator_tool.py <character_json> <markdown_directory>"
        )
        sys.exit(1)

    character_json = Path(sys.argv[1])
    markdown_directory = Path(sys.argv[2])

    if not character_json.exists():
        print(f"Character JSON not found: {character_json}")
        sys.exit(1)
    if not markdown_directory.exists() or not markdown_directory.is_dir():
        print(f"Markdown directory not found or invalid: {markdown_directory}")
        sys.exit(1)

    report = validate_roles(character_json, markdown_directory)
    print("\n=== MISSING ROLE SUMMARY ===")
    for entry in report:
        print(
            f"- {entry['file']} | Panel: {entry['panel']} | Missing: {entry['missing_roles']}"
        )
    print(f"\n✅ Completed: {len(report)} panel(s) with missing roles found.")

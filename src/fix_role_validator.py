#!/usr/bin/env python
"""
Fix for role validator tool to prevent "unhashable type: 'list'" error
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Union
from logging_config import get_logger

logger = get_logger(__name__)


def clean_roles_list(roles: List[Union[str, List[str]]]) -> List[str]:
    """Flatten and clean a potentially nested list of roles"""
    cleaned = []
    for item in roles:
        if isinstance(item, str):
            cleaned.append(item)
        elif isinstance(item, list):
            cleaned.extend([r for r in item if isinstance(r, str)])
    return cleaned


def fix_role_validation(
    character_json_path: str, markdown_dir_path: str, per_role: int = 2
):
    """Fixed version of the role validation function"""
    from services.generate_character_profiles import generate_character_profiles_for_roles
    from role_validator_tool import validate_roles

    char_path = Path(character_json_path)
    md_path = Path(markdown_dir_path)

    if not char_path.exists():
        logger.error("Character JSON file not found: %s", char_path)
        return
    if not md_path.exists() or not md_path.is_dir():
        logger.error("Markdown directory invalid: %s", md_path)
        return

    logger.info("Running role validation on %s against %s...", md_path, char_path)
    report = validate_roles(char_path, md_path)

    # Collect unique roles from report with extra validation
    all_missing_roles = []
    for entry in report:
        missing_roles = entry.get("missing_roles", [])
        # Ensure we're only dealing with strings
        if isinstance(missing_roles, list):
            # Clean and flatten any nested lists
            valid_roles = clean_roles_list(missing_roles)
            all_missing_roles.extend(valid_roles)
        else:
            logger.warning(
                "Expected list for missing_roles, got %s",
                type(missing_roles).__name__,
            )

    # Create a set of unique string roles
    missing_roles_set = set(all_missing_roles)

    if not missing_roles_set:
        logger.info("All roles are already covered. No characters needed.")
        return

    logger.info("📝 Missing Roles Detected: %s", ", ".join(sorted(missing_roles_set)))

    confirm = (
        input("Proceed to generate characters for these roles? (yes/no): ")
        .strip()
        .lower()
    )
    if confirm != "yes":
        logger.info("Operation cancelled.")
        return

    logger.info("Generating %d characters for each missing role...", per_role)
    generate_character_profiles_for_roles(
        list(missing_roles_set),  # Convert set back to list of strings
        input_json_path=char_path,
        output_json_path=char_path,
        characters_per_role=per_role,
    )
    logger.info("Character generation complete!")


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        # Interactive mode
        logger.info("--- Scan Markdown and Auto-Patch Character JSON ---")
        char_json_path = input("Enter path to character JSON: ").strip()
        md_dir_path = input("Enter markdown directory path: ").strip()
        per_role_input = input("How many characters per role? (default: 2): ").strip()
        per_role = int(per_role_input) if per_role_input.strip().isdigit() else 2
        fix_role_validation(char_json_path, md_dir_path, per_role)
    else:
        # Command-line mode
        char_json_path = sys.argv[1]
        md_dir_path = sys.argv[2]
        per_role = (
            int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 2
        )
        fix_role_validation(char_json_path, md_dir_path, per_role)

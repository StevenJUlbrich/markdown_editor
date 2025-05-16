#!/usr/bin/env python
"""
Diagnostic script to debug the 'unhashable type: list' error in option 17
"""
import json
import sys
import traceback
from pathlib import Path


def diagnose_json_file(json_path):
    """Examine the JSON file structure to identify potential issues"""
    print(f"\n===== EXAMINING JSON FILE: {json_path} =====")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"✅ Successfully loaded JSON file")
        print(
            f"📊 File contains {len(data.keys())} top-level keys: {', '.join(data.keys())}"
        )

        characters = data.get("characters", {})
        print(f"👤 Found {len(characters)} character entries")

        # Check character roles
        roles = []
        role_types = {}
        for name, char_data in characters.items():
            role = char_data.get("role")
            role_type = type(role).__name__
            roles.append(role)
            role_types[role_type] = role_types.get(role_type, 0) + 1

        print(f"📋 Role types found: {role_types}")
        if "list" in role_types:
            print(
                f"⚠️ WARNING: Found {role_types['list']} roles that are lists (potential error source)"
            )
            # Print examples of list roles
            for name, char_data in characters.items():
                role = char_data.get("role")
                if isinstance(role, list):
                    print(f"  - Character '{name}' has list role: {role}")

        return data
    except Exception as e:
        print(f"❌ ERROR examining JSON: {e}")
        traceback.print_exc()
        return None


def debug_role_validation(json_path, md_path):
    """Debug the role validation process step by step"""
    print(f"\n===== DEBUGGING ROLE VALIDATION =====")

    try:
        # First try to import necessary modules
        sys.path.append("src")  # Ensure src directory is in path

        # Try imports
        try:
            from role_validator_tool import (
                extract_roles_per_panel,
                get_valid_roles_from_character_json,
                validate_roles,
            )

            print("✅ Successfully imported role_validator_tool")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print(
                "⚠️ Make sure you're running this script from the project root directory"
            )
            return

        # Get valid roles from character JSON
        try:
            valid_roles = get_valid_roles_from_character_json(Path(json_path))
            print(f"✅ Found {len(valid_roles)} valid roles in character JSON")

            if any(isinstance(r, list) for r in valid_roles):
                print("⚠️ WARNING: Some roles from JSON are lists!")
                list_roles = [r for r in valid_roles if isinstance(r, list)]
                print(
                    f"  List roles: {list_roles[:3]}{'...' if len(list_roles) > 3 else ''}"
                )
        except Exception as e:
            print(f"❌ ERROR getting valid roles: {e}")
            traceback.print_exc()
            return

        # Run validation with detailed tracing
        print("\n---Running validation with detailed tracing---")
        try:
            # Modified version of validate_roles with extra debugging
            from MarkdownDocument import MarkdownDocument

            validation_report = []
            for md_file in Path(md_path).glob("*.md"):
                print(f"\nProcessing file: {md_file.name}")
                doc = MarkdownDocument(filepath=str(md_file))
                panel_roles = extract_roles_per_panel(doc)

                for panel_title, roles in panel_roles.items():
                    print(f"  Panel: '{panel_title}'")
                    print(
                        f"    Suggested roles: {roles} (type: {type(roles).__name__})"
                    )

                    if not isinstance(roles, list):
                        print(
                            f"    ⚠️ WARNING: Panel roles not a list: {type(roles).__name__}"
                        )
                        continue

                    missing = []
                    for role in roles:
                        print(
                            f"    Checking role: '{role}' (type: {type(role).__name__})"
                        )
                        if isinstance(role, list):
                            print(f"      ⚠️ WARNING: Role is a list: {role}")
                            # Check each subrole
                            for subrole in role:
                                if subrole not in valid_roles:
                                    missing.append(subrole)
                        elif role not in valid_roles:
                            missing.append(role)

                    if missing:
                        print(f"    ❌ Missing roles: {missing}")
                        validation_report.append(
                            {
                                "file": md_file.name,
                                "panel": panel_title,
                                "missing_roles": missing,
                            }
                        )
                    else:
                        print(f"    ✅ All roles are valid")

            return validation_report
        except Exception as e:
            print(f"❌ ERROR during validation: {e}")
            traceback.print_exc()
            return None
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return None


def diagnose_error_17(json_path, md_path):
    """Main diagnostic function for option 17 error"""
    print("\n========== ERROR DIAGNOSIS FOR OPTION 17 ==========")
    print(f"JSON Path: {json_path}")
    print(f"Markdown Path: {md_path}")

    # Examine JSON file
    data = diagnose_json_file(json_path)
    if not data:
        return

    # Debug role validation
    validation_report = debug_role_validation(json_path, md_path)

    # Analyze the validation report to find potential issues
    if validation_report is not None:
        print("\n===== VALIDATION REPORT ANALYSIS =====")
        print(f"Found {len(validation_report)} entries with missing roles")

        # Look for list values in missing_roles
        for entry in validation_report:
            missing_roles = entry.get("missing_roles", [])
            for role in missing_roles:
                if isinstance(role, list):
                    print(
                        f"⚠️ FOUND ERROR SOURCE: 'missing_roles' contains a list: {role}"
                    )
                    print(f"  In file: {entry['file']}, panel: {entry['panel']}")
                    print(
                        "  This will cause 'unhashable type: list' when creating a set"
                    )

    print("\n===== SUGGESTED FIXES =====")
    print(
        "1. Fix the validate_roles() function in role_validator_tool.py to flatten nested lists"
    )
    print(
        "2. Fix the suggest_character_roles_from_context() function to always return flat lists"
    )
    print("3. Fix option 17 in main.py to handle nested lists in the report")
    print("\nRun the fix_role_validator.py script as a workaround in the meantime")


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        # Interactive mode
        print("===== DIAGNOSING OPTION 17 ERROR =====")
        json_path = input("Enter path to character JSON: ").strip()
        md_path = input("Enter markdown directory path: ").strip()
        diagnose_error_17(json_path, md_path)
    else:
        # Command-line mode
        json_path = sys.argv[1]
        md_path = sys.argv[2]
        diagnose_error_17(json_path, md_path)

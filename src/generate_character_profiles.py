import json
import time
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

from logging_config import get_logger

client = OpenAI()
logger = get_logger(__name__)

# Example character profile for reference
EXAMPLE_CHARACTER = {
    "visual_tags": [
        "non-binary",
        "35 years old",
        "medium height",
        "glasses",
        "buzzed hair",
        "hazel eyes",
        "casual hoodie",
        "slacks",
        "cyberpunk pin",
    ],
    "required_constraints": [
        "Always brings up ethics",
        "Frequently references compliance metrics",
    ],
    "motion_rules": "Fidgets with objects during meetings; leans forward when engaged.",
    "voice_tone": "Low and calm, but firm; uses analogies when teaching.",
    "prop_loadout": [
        "encrypted USB",
        "annotated doc binder",
        "emergency caffeine pack",
    ],
    "appearance": "An analytical mind with a renegade visual edge.",
    "role": "Risk Analyst",
    "catchphrase": "You can't monitor what you don't model.",
}


def generate_prompt(
    missing_roles: List[str], existing_names: List[str], per_role: int = 2
) -> str:
    return f"""
You are a professional character writer for a graphic novel about banking system reliability.

Generate {per_role} unique characters for each of the following roles:
{", ".join(missing_roles)}

Avoid any names from this list:
{", ".join(existing_names)}

Each character must match this JSON format:
{json.dumps({"Example Character": EXAMPLE_CHARACTER}, indent=2)}

Return only the final JSON object like:
{{ "New Name 1": {{...}}, "New Name 2": {{...}}, ... }}

Do not include commentary or explanation.
"""


def parse_response_with_retry(
    content: str, retries: int = 3, delay: float = 1.0
) -> Dict[str, Any]:
    for attempt in range(retries):
        try:
            if content.startswith("```json"):
                content = content[7:].strip()
            elif content.startswith("```"):
                content = content[3:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                print("Retrying...\n")
    raise ValueError("❌ Failed to parse OpenAI response after retries.")


def clean_and_flatten_roles(roles: List[Any]) -> List[str]:
    """
    Recursively flattens any nested lists and ensures only string roles are returned.

    Args:
        roles: A list that may contain strings, lists, or other types

    Returns:
        A flattened list containing only string values
    """
    cleaned = []

    def flatten(item):
        if isinstance(item, str):
            cleaned.append(item)
        elif isinstance(item, list):
            for subitem in item:
                flatten(subitem)
        else:
            print(
                f"⚠️ Skipping invalid role entry: {item} (type: {type(item).__name__})"
            )

    for r in roles:
        flatten(r)

    return cleaned


def generate_character_profiles_for_roles(
    missing_roles: List[Any],
    input_json_path: Path,
    output_json_path: Path,
    characters_per_role: int = 2,
):
    cleaned_roles = clean_and_flatten_roles(missing_roles)

    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_chars = data.get("characters", {})
    existing_names = list(existing_chars.keys())

    prompt = generate_prompt(cleaned_roles, existing_names, characters_per_role)

    print(f"📡 Requesting new characters from OpenAI for roles: {cleaned_roles}")
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    raw = response.choices[0].message.content.strip()
    try:
        parsed = parse_response_with_retry(raw)
        new_entries = parsed.get("characters", parsed)

        added = 0
        per_role_counts = {r: 0 for r in cleaned_roles}
        for name, profile in new_entries.items():
            role = profile.get("role")
            if name not in existing_names and role in per_role_counts:
                existing_chars[name] = profile
                added += 1
                per_role_counts[role] += 1

        print(f"\n✅ Added {added} new characters to the file.\n")
        for role, count in per_role_counts.items():
            if count == characters_per_role:
                print(f"✔️ {count} characters created for role: {role}")
            else:
                print(
                    f"❗ Only {count} created for role: {role} (expected {characters_per_role})"
                )

        data["characters"] = existing_chars
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved updated character file to: {output_json_path}")

    except Exception as e:
        print("❌ Character generation failed.")
        print("Error:", e)
        print("\nRaw OpenAI output:\n", raw)

import json
from pathlib import Path
from typing import Dict, List

from openai import OpenAI

client = OpenAI()

EXAMPLE_CHARACTER = {
    "visual_tags": [
        "female",
        "42 years old",
        "tall",
        "piercing eyes",
        "short curly hair",
        "dark brown eyes",
        "business formal attire",
        "pinstripe blazer",
        "silver badge lanyard",
    ],
    "required_constraints": [
        "Always takes charge during incidents",
        "Never accepts vague status updates",
    ],
    "motion_rules": "Moves decisively, frequently points while speaking, maintains confident posture.",
    "voice_tone": "Assertive, mid-range, speaks with clarity and urgency under stress.",
    "prop_loadout": [
        "incident response tablet",
        "audit log binder",
        "emergency contact headset",
    ],
    "appearance": "A composed leader with a reputation for clarity and action in crises.",
    "role": "Executive Stakeholder",
    "catchphrase": "If it's not in the log, it didn't happen.",
}


def generate_prompt(
    missing_roles: List[str], existing_names: List[str], characters_per_role: int = 2
) -> str:
    return f"""
You are an expert character designer for an educational graphic novel about SRE (site reliability engineering) in banking.

We are missing characters for the following roles:
{', '.join(missing_roles)}

For each role, generate {characters_per_role} unique characters in this JSON structure. Do not duplicate names from this list:
{', '.join(existing_names)}

Return only a JSON object under "characters" where keys are character names.

Use this format for each character:
{json.dumps({"Example Name": EXAMPLE_CHARACTER}, indent=2)}

Return a valid JSON object. Do not include explanatory text.
"""


def generate_character_profiles_for_roles(
    missing_roles: List[str],
    input_json_path: Path,
    output_json_path: Path,
    characters_per_role: int = 2,
):
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_characters = data.get("characters", {})
    existing_names = list(existing_characters.keys())

    prompt = generate_prompt(missing_roles, existing_names, characters_per_role)

    print("Calling OpenAI to generate new character profiles...")
    response = client.chat.completions.create(
        model="gpt-4o-2024-11-20",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:].strip()
    elif content.startswith("```"):
        content = content[3:].strip()
    if content.endswith("```"):
        content = content[:-3].strip()

    try:
        parsed = json.loads(content)
        new_chars = parsed.get("characters", {})
        deduped = {
            name: profile
            for name, profile in new_chars.items()
            if name not in existing_names
        }

        print(f"✅ Adding {len(deduped)} new characters to file.")
        existing_characters.update(deduped)

        data["characters"] = existing_characters
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Updated file written to: {output_json_path}")
    except Exception as e:
        print("❌ Failed to parse OpenAI JSON:", e)
        print("Raw output:")
        print(content)

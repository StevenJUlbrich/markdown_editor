import json
import time
from pathlib import Path
from typing import Any, Dict, List

from openai import APIError, OpenAI, OpenAIError, RateLimitError

from logging_config import get_logger
from utils import clean_and_flatten_roles, generate_prompt, parse_response_with_retry

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
            logger.debug(f"JSON parse error (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                logger.info("Retrying...")
    raise ValueError("Failed to parse OpenAI response after retries.")


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

    logger.info(f"Requesting new characters from OpenAI for roles: {cleaned_roles}")

    retries = 3
    delay = 2.0  # seconds

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
            )

            raw = response.choices[0].message.content.strip()
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

            logger.info(f"Added {added} new characters to the file.")
            for role, count in per_role_counts.items():
                if count == characters_per_role:
                    logger.info(f"{count} characters created for role: {role}")
                else:
                    logger.warning(
                        f"Only {count} created for role: {role} (expected {characters_per_role})"
                    )

            data["characters"] = existing_chars
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved updated character file to: {output_json_path}")
            break

        except (RateLimitError, APIError) as e:
            logger.warning(
                f"Attempt {attempt + 1} failed with error: {e}. Retrying in {delay} seconds..."
            )
            time.sleep(delay)
        except OpenAIError as e:
            logger.error(
                f"An OpenAI-specific error occurred while processing roles: {cleaned_roles}. Input file: {input_json_path}"
            )
            logger.debug(f"OpenAIError: {e}")
            break
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while processing roles: {cleaned_roles}. Input file: {input_json_path}"
            )
            logger.debug(f"Exception: {e}")
            break
    else:
        logger.error("Failed to complete the API call after multiple retries.")

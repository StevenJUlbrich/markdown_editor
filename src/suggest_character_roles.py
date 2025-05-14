"""
Fixed version of suggest_character_roles.py to ensure consistent return type
"""

import json
import re
from typing import Any, Dict, List

from openai_service import client


def clean_json_list_from_fenced_response(raw: str) -> List[str]:
    """Clean JSON list from code-fenced response"""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, str)]
        else:
            print("Warning: OpenAI response was not a list:", parsed)
            return []
    except Exception as e:
        print("Warning: Failed to parse JSON response:", e)
        print("Raw response was:", raw)
        return []


def suggest_character_roles_from_context(
    panel_title: str,
    scene_description_md: str,
    teaching_narrative_md: str,
    model: str = "gpt-4o-2024-11-20",
    temperature: float = 0.5,
) -> List[str]:
    """
    Sends a prompt to OpenAI to infer character roles appropriate for visualizing this scene.
    Returns a flat list of role strings (e.g., ["SRE Engineer", "Developer", "Junior Dev"])
    """
    prompt = f"""
You are a technical storyboard designer for a graphic novel that teaches site reliability engineering (SRE).
You must decide which character types should be visually present in the following scene.

The scene includes a description and a teaching narrative. Think about what character roles would best convey confusion, expertise, conflict, or insight.

Scene Title: {panel_title}

---
SCENE DESCRIPTION:
{scene_description_md}

---
TEACHING NARRATIVE:
{teaching_narrative_md}

---

Based on this material, list up to 4 character roles that should appear in the comic panel.
Use roles like "SRE Engineer", "Junior Developer", "Developer", "Product Owner", "Finance Analyst", etc.

Return only a JSON array like this:
["SRE Engineer", "Junior Developer"]
    """

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )

    raw = response.choices[0].message.content.strip()

    # Ensure we always return a list of strings
    try:
        if raw.startswith("```"):
            raw = re.sub(
                r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE
            )

        parsed = json.loads(raw)
        flattened = []

        # Handle potentially nested structure
        def extract_strings(item: Any) -> None:
            if isinstance(item, str):
                flattened.append(item)
            elif isinstance(item, list):
                for subitem in item:
                    extract_strings(subitem)

        if isinstance(parsed, list):
            for item in parsed:
                extract_strings(item)
        else:
            print("Warning: OpenAI response was not a list:", parsed)

        return flattened
    except Exception as e:
        print("Failed to parse character role list from OpenAI:", e)
        print("Raw response was:", raw)
        return []

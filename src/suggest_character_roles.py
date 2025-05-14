import json
import re
from typing import Dict, List

from openai_service import client


def suggest_character_roles_from_context(
    panel_title: str,
    scene_description_md: str,
    teaching_narrative_md: str,
    model: str = "gpt-4o-2024-11-20",
    temperature: float = 0.5,
) -> List[str]:
    """
    Sends a prompt to OpenAI to infer character roles appropriate for visualizing this scene.
    Returns a list of role strings (e.g., ["SRE Engineer", "Developer", "Junior Dev"])
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
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        else:
            print("OpenAI response was not a list:", parsed)
            return []
    except Exception as e:
        print("Failed to parse character role list from OpenAI:", e)
        print("Raw response was:\n", raw)
        return []

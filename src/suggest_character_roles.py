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

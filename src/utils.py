import json
import re
from logging_config import get_logger

logger = get_logger(__name__)


def flatten_list(data):
    """Recursively flattens any nested list of strings into a single list of strings."""
    flat = []
    if isinstance(data, str):
        return [data]
    if isinstance(data, list):
        for item in data:
            flat.extend(flatten_list(item))
    return flat


def strip_markdown_fences(markdown_text):
    """Removes ``` or ```markdown fences from OpenAI responses."""
    cleaned = markdown_text.strip()
    # Remove code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:markdown|json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE
        )
    return cleaned.strip()


def clean_json_list_from_response(raw):
    """Parses a JSON list from a code-fenced OpenAI response, returning a flat list of strings."""
    try:
        cleaned = strip_markdown_fences(raw)
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, str)]
        else:
            # Try to flatten if list-of-lists
            return flatten_list(parsed)
    except Exception as e:
        logger.warning("Failed to parse JSON response: %s", e)
        logger.debug("Raw response was: %s", raw)
        return []


def clean_and_flatten_roles(roles):
    """Convenience alias for flatten_list, for code clarity."""
    return flatten_list(roles)

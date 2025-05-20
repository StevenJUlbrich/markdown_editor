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


import os


def safe_export_markdown(
    markdown_str: str,
    input_path: str,
    output_dir: str = None,
    suffix: str = "_enhanced",
    extension: str = ".md",
    force: bool = False,
) -> str:
    """
    Exports markdown to a file derived from input_path with overwrite protection.

    Args:
        markdown_str: Markdown content to write.
        input_path: Path to the original markdown file.
        output_dir: If provided, write output here instead of input file's dir.
        suffix: Suffix to append before extension (default: "_enhanced").
        extension: Output file extension (default: ".md").
        force: If True, will overwrite output file if it exists.

    Returns:
        Path to the written output file.
    """
    basename = os.path.basename(input_path)
    stem, _ = os.path.splitext(basename)
    output_stem = f"{stem}{suffix}"
    output_filename = f"{output_stem}{extension}"

    if output_dir is None:
        output_dir = os.path.dirname(input_path)

    output_path = os.path.join(output_dir, output_filename)

    # Prevent accidental overwrite unless force=True
    if os.path.exists(output_path) and not force:
        # Find a unique filename by incrementing
        i = 2
        while True:
            candidate = os.path.join(output_dir, f"{output_stem}_v{i}{extension}")
            if not os.path.exists(candidate):
                output_path = candidate
                break
            i += 1

    # Make sure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_str)

    return output_path

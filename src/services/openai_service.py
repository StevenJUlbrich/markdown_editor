# openai_service.py
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from logging_config import get_logger
from models.document_model import SceneAnalysisPydantic

from .utils import (
    clean_and_flatten_roles,
    clean_json_list_from_response,
    strip_markdown_fences,
)

logger = get_logger(__name__)

# --- OpenAI Model/Temperature Central Config ---
from config import (
    OPENAI_MODEL_DEFAULT,
    OPENAI_MODEL_ENHANCEMENT,
    OPENAI_MODEL_SPEECH,
    OPENAI_MODEL_SUGGESTION,
    OPENAI_TEMP_DEFAULT,
    OPENAI_TEMP_ENHANCEMENT,
    OPENAI_TEMP_SPEECH,
    OPENAI_TEMP_SUGGESTION,
)

# --- OpenAI Client Setup ---
MOCK_CLIENT = False

if MOCK_CLIENT:
    # (Mock code omitted for brevity)
    pass
else:
    try:
        from openai import OpenAI

        client = OpenAI()
    except ImportError:
        client = None
        logger.error("OpenAI library not installed.")
    except Exception as e:
        client = None
        logger.exception("Could not initialize OpenAI client: %s", e)


# --- BATCHED ROLE SUGGESTION FUNCTION ---
def suggest_character_roles_for_panels(
    panels: List[Dict],
    model: str = OPENAI_MODEL_SUGGESTION,
    temperature: float = OPENAI_TEMP_SUGGESTION,
    max_attempts: int = 3,
) -> Dict[str, List[str]]:
    """
    Sends one batch prompt for all panels, returns {panel_title: [role, ...], ...}
    """
    prompt_panels = []
    for p in panels:
        prompt_panels.append(
            f"---\nPanel Title: {p['title']}\nScene Description:\n{p['scene']}\nTeaching Narrative:\n{p['teaching']}\n"
        )
    prompt = f"""
You are a technical storyboard designer for a graphic novel that teaches SRE.
For each panel below, suggest up to 4 individual character roles that should be visually present.
Roles should reflect the scene's context and teaching narrative and can include roles like "SRE Engineer", "Junior Developer", "Product Owner", etc.
The roles names should be clear and concise, suitable for visual representation in a comic panel.
Return a JSON dictionary: {{ "Panel Title 1": [roles...], ... }}
{''.join(prompt_panels)}
Respond ONLY with the JSON object.
    """
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            raw = response.choices[0].message.content.strip()
            raw = strip_markdown_fences(raw)

            result = json.loads(raw)
            return {
                k: [v2 for v2 in v if isinstance(v2, str)]
                for k, v in result.items()
                if isinstance(v, list)
            }
        except Exception as e:
            if attempt == max_attempts - 1:
                logger.error("Failed to parse batch character roles: %s", e)
                logger.debug("Raw: %s", raw)
                return {}
            time.sleep(2**attempt)


def handle_openai_response(response_content: str, section_title: str) -> str:
    cleaned = response_content.strip()
    if "![" in cleaned:
        logger.warning(
            "Image markdown detected in OpenAI response for section: '%s'",
            section_title,
        )
    return cleaned


def get_enhancement_suggestions_for_panel_h3s(
    panel_title: str,
    panel_context_markdown: str,
    h3_sections_content: Dict[str, str],
    model: str = OPENAI_MODEL_SUGGESTION,
    temperature: float = OPENAI_TEMP_SUGGESTION,
) -> Dict[str, Dict[str, Any]]:
    if not h3_sections_content:
        return {}
    h3_sections_text_for_prompt = []
    for h3_title, h3_md in h3_sections_content.items():
        content_without_heading = h3_md
        temp_content = h3_md.strip()
        if h3_title != "Initial Content" and temp_content.startswith(f"### {h3_title}"):
            lines = temp_content.splitlines()
            if len(lines) > 1:
                content_without_heading = "\n".join(lines[1:]).strip()
            else:
                content_without_heading = ""
        elif h3_title == "Initial Content":
            content_without_heading = temp_content
        h3_sections_text_for_prompt.append(
            f"## {h3_title}\n{content_without_heading if content_without_heading.strip() else 'This section appears to have no primary content following its heading.'}"
        )
    separator = "\n\n---\n\n"
    joined_sections = separator.join(h3_sections_text_for_prompt)
    prompt = f"""You are a senior SRE and technical learning designer.
You are reviewing H3 sub-sections within a larger document panel titled: "{panel_title}"

Here is some overall context for this panel (which may include its H2 title and potentially key introductory H3 sections like Scene Description or Teaching Narrative):
---
{panel_context_markdown}
---

Evaluate the following H3 sub-sections from this panel. For each one, determine if it could be enhanced for clarity, engagement, or practical application.

H3 Sub-sections to Evaluate:
---
{joined_sections}
---

For each H3 sub-section evaluated (use its exact title as the key, e.g., "Scene Description", "Common Example of the Problem"), provide your assessment in the following JSON format:
{{
  "Exact H3 Title 1": {{ "enhance": "Yes/No", "recommendation": "Type of enhancement (e.g., Add Mermaid Diagram, Text Diagram, More Examples, Checklist, Code Snippet, Table, Analogy) or null if No", "reason": "Brief justification for your recommendation or why no enhancement is needed." }},
  "Exact H3 Title 2": {{ "enhance": "Yes/No", "recommendation": "...", "reason": "..." }}
}}

Ensure your entire response is a single, valid JSON object. Do not add any explanatory text before or after the JSON.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        raw_response_content = response.choices[0].message.content
        if not raw_response_content:
            logger.error("Received empty response for suggestions.")
            return {}
        cleaned_response = raw_response_content.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
        suggestions = json.loads(cleaned_response.strip())
        parsed_suggestions = {}
        for title_key, details in suggestions.items():
            if isinstance(details, dict):
                parsed_suggestions[title_key] = {
                    "enhance": str(details.get("enhance", "No")).lower() == "yes",
                    "recommendation": details.get("recommendation"),
                    "reason": details.get("reason"),
                }
            else:
                logger.warning(
                    "Unexpected format for suggestion details for '%s': %s",
                    title_key,
                    details,
                )
        return parsed_suggestions
    except json.JSONDecodeError as e:
        logger.error("Error decoding JSON response for suggestions: %s", e)
        logger.debug("Raw response was:\n>>>\n%s\n<<<", raw_response_content)
        return {}
    except Exception as e:
        logger.exception("Unexpected error getting suggestions: %s", e)
        return {}


def get_improved_markdown_for_section(
    original_h3_markdown_content: str,
    enhancement_type: Optional[str],
    enhancement_reason: Optional[str],
    panel_title_context: str,
    overall_panel_context_md: str,
    model: str = OPENAI_MODEL_ENHANCEMENT,
    temperature: float = OPENAI_TEMP_ENHANCEMENT,
) -> Optional[str]:
    if not original_h3_markdown_content or not original_h3_markdown_content.strip():
        logger.info("[OpenAI Service] Skipping enhancement for empty content.")
        return original_h3_markdown_content
    h3_title_in_md = "This Section"
    lines = original_h3_markdown_content.strip().splitlines()
    if lines and lines[0].strip().startswith("### "):
        h3_title_in_md = lines[0].strip()
        h3_title_for_prompt = h3_title_in_md[4:].strip()
    else:
        h3_title_for_prompt = "the provided section"
    prompt = f"""You are a senior SRE and technical learning designer.
You are tasked with improving a specific H3 sub-section from a larger document panel titled \"{panel_title_context}\".
The overall context for the panel is:
---
{overall_panel_context_md}
---

The H3 sub-section to improve is titled: \"{h3_title_for_prompt}\"

It was previously identified that this section should be enhanced.
Suggested Enhancement Type: {enhancement_type or "General improvement"}
Reason for Enhancement: {enhancement_reason or "Make it more engaging and clear."}

Here is the original H3 sub-section content (which includes its H3 heading):
---
{original_h3_markdown_content}
---

Please provide an improved version of this H3 sub-section.
- Incorporate the suggested enhancement.
- Preserve the original tone and technical accuracy.
- Ensure the output is well-formatted Markdown.
- Return only the improved Markdown content for this section.
- Do **not** include image references, links to diagrams, or Markdown image tags (e.g., `![label](url)`).
- If a visual aid is required, use **Mermaid diagrams**, **ASCII flowcharts**, or **text-based representations**.
- Do not include explanations or any content outside of the Markdown.
"""
    logger.info(
        "Requesting enhancement for H3 section: '%s' in panel '%s'",
        h3_title_for_prompt,
        panel_title_context,
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        improved_markdown = response.choices[0].message.content
        if improved_markdown:
            cleaned_improved_markdown = handle_openai_response(
                strip_markdown_fences(improved_markdown), h3_title_for_prompt
            )
            expected_heading = f"### {h3_title_for_prompt}"
            if not cleaned_improved_markdown.startswith("### "):
                if original_h3_markdown_content.strip().startswith("### "):
                    original_heading_line = (
                        original_h3_markdown_content.strip().splitlines()[0]
                    )
                    if not cleaned_improved_markdown.strip().startswith(
                        original_heading_line.strip()
                    ):
                        logger.info(
                            "Prepending original H3 heading '%s' to API response.",
                            original_heading_line.strip(),
                        )
                        cleaned_improved_markdown = (
                            original_heading_line + "\n\n" + cleaned_improved_markdown
                        )
            return cleaned_improved_markdown
        else:
            logger.error("Received empty response for content enhancement.")
            return None
    except Exception as e:
        logger.exception("Unexpected error during content enhancement: %s", str(e))
        return None


def rewrite_scene_and_teaching_as_summary(
    scene_markdown: str,
    teaching_markdown: str,
    model: str = OPENAI_MODEL_DEFAULT,
    temperature: float = OPENAI_TEMP_DEFAULT,
) -> str:
    prompt = f"""
You are writing a short, vivid scene summary for a comic panel based on technical teaching material.

Below is the raw material: a Scene Description and a Teaching Narrative.

Your task is to summarize them into one paragraph that captures:
- The key moment or emotion of the scene,
- Any conflict or learning opportunity,
- Any visual cues (e.g. dashboards, people reacting, stress, insight),
- And tone appropriate for a learning comic (engaging, clear, not overly dramatic).

Avoid technical jargon unless necessary. Make it easy to visualize. Do not mention "scene description" or "teaching narrative."

Scene Description:
---
{scene_markdown.strip()}
---

Teaching Narrative:
---
{teaching_markdown.strip()}
---

Write a single-paragraph summary suitable for visualizing in a comic panel. Do not include quotes or markdown.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        logger.error("OpenAI error in scene summary generation: %s", str(e))
        return "A visual summary of this scene could not be generated."


def generate_narration_title_for_panel(
    scene_md: str,
    teaching_md: str,
    model: str = OPENAI_MODEL_SPEECH,
    temperature: float = OPENAI_TEMP_SPEECH,
) -> str:
    prompt = f"""
You are writing short narration tags for comic panels in a technical learning comic.

Below is the scene and teaching content for one panel.

Your task is to write a **very short narration line** (3 to 5 words) that captures the core idea or tension of the scene.

Scene Description:
---
{scene_md}

---

Teaching Narrative:
---
{teaching_md}

---

Return only a short title. No quotes, no markdown, no formatting.
Example outputs: 
- "Hidden Errors Emerge"
- "Green But Failing"
- "Metrics Mislead Everyone"
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("OpenAI narration generation failed: %s", str(e))
        return "Narration missing"


def generate_speech_bubbles_for_panel(
    scene_summary: str,
    character_names: List[str],
    character_data: Dict,
    model: str = OPENAI_MODEL_SPEECH,
    temperature: float = OPENAI_TEMP_SPEECH,
) -> Dict[str, str]:
    character_lines = []
    for name in character_names:
        profile = character_data.get("characters", {}).get(name, {})
        if not profile:
            continue
        role = profile.get("role", "Unknown role")
        tone = profile.get("voice_tone", "")
        tags = ", ".join(profile.get("visual_tags", []))
        character_lines.append(f"- {name} ({role}): {tone}. Tags: {tags}")
    character_block = "\n".join(character_lines)
    prompt = f"""
You are writing realistic speech bubble text for a comic panel.

Scene:
{scene_summary}

Characters:
{character_block}

Instructions:
- Write up to 1 speech bubble per character.
- If a character is silently reacting or watching, leave them out.
- Each bubble should be short (max 15 words), fit in a comic panel, and reflect their personality and role.
- Do not include any formatting or markdown.

Return only a JSON object like:
{{
  "Hector": "Logs say otherwise.",
  "Wanjiru": "Metrics are green though!"
}}
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:].strip()
        elif content.startswith("```"):
            content = content[3:].strip()
        if content.endswith("```"):
            content = content[:-3].strip()
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return {k: v for k, v in parsed.items() if isinstance(v, str)}
        else:
            return {}
    except Exception as e:
        logger.error("Failed to generate speech bubbles: %s", str(e))
        return {}


def suggest_character_roles_from_context(
    panel_title: str,
    scene_description_md: str,
    teaching_narrative_md: str,
    model: str = OPENAI_MODEL_SUGGESTION,
    temperature: float = OPENAI_TEMP_SUGGESTION,
) -> List[str]:
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
    try:
        if raw.startswith("```"):
            raw = re.sub(
                r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE
            )
        parsed = json.loads(raw)
        flattened = []

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
            logger.warning("OpenAI response was not a list: %s", parsed)
        return flattened
    except Exception as e:
        logger.error("Failed to parse character role list from OpenAI: %s", e)
        logger.debug("Raw response was: %s", raw)
        return []


def infer_scene_tags_for_panel(scene_md: str, teaching_md: str) -> List[str]:
    tags = []
    text = f"{scene_md}\n{teaching_md}".lower()
    if "confusion" in text or "customer calls" in text:
        tags.append("Chaos Scene")
    if "checklist" in text or "lesson" in text or "recommend" in text:
        tags.append("Teaching Scene")
    if "after" in text or "reflection" in text or "retrospective" in text:
        tags.append("Reflection Scene")
    if "triangle" in text or "pillars" in text:
        tags.append("Meta Scene")
    if not tags:
        tags.append("Teaching Scene")
    return tags


def generate_scene_analysis_from_ai(
    scene_markdown: str,
    teaching_markdown: str,
    model: str = OPENAI_MODEL_DEFAULT,
    temperature: float = OPENAI_TEMP_DEFAULT,
) -> SceneAnalysisPydantic:
    """
    Uses OpenAI to analyze a panel and generate a structured SceneAnalysisPydantic object.

    Args:
        scene_markdown: The scene description from the markdown panel
        teaching_markdown: The teaching narrative from the markdown panel
        model: The OpenAI model to use

    Returns:
        SceneAnalysisPydantic instance with AI-inferred tags and metadata
    """

    prompt = f"""
You are analyzing a scene and its teaching narrative from a visual technical comic.

Read the following and classify the scene based on tone, intent, and structure.

Scene Description:
---
{scene_markdown.strip()}
---

Teaching Narrative:
---
{teaching_markdown.strip()}
---

Return your analysis as a JSON object with the following fields:
{{
    "scene_types": ["list of tags like Teaching Scene, Chaos Scene, Reflection Scene, Meta Scene, Decision Scene"],
    "tone": "describe the emotional feel, e.g., calm, tense, fast-paced",
    "location": "where does it take place, if mentioned",
    "time_of_day": "e.g., 2 AM, morning, late night, or None",
    "teaching_level": "basic, intermediate, advanced, metaphorical, meta",
    "notes": "anything else that might be useful to know about this scene"
}}

Respond with ONLY a single valid JSON object. Do not wrap in markdown fences. No commentary.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        data = json.loads(content)
        return SceneAnalysisPydantic(
            scene_types=data.get("scene_types", []),
            tone=data.get("tone"),
            location=data.get("location"),
            time_of_day=data.get("time_of_day"),
            teaching_level=data.get("teaching_level"),
            notes=data.get("notes"),
            raw_summary=f"{scene_markdown.strip()}\n\n{teaching_markdown.strip()}",
            inferred_by_ai=True,
        )
    except Exception as e:
        logger.error("Error during scene analysis generation: %s", e)
        logger.debug("Raw response: %s", content if "content" in locals() else "None")
        return SceneAnalysisPydantic(
            scene_types=["Teaching Scene"],
            inferred_by_ai=True,
            notes="Fallback to default scene type due to AI error.",
        )

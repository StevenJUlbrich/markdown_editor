# openai_service.py
import json
import logging
import os  # For environment variables
import re
import time
from typing import Any, Dict, List, Optional

from logging_config import get_logger

logger = get_logger(__name__)


def handle_openai_response(response_content: str, section_title: str) -> str:
    """
    Process OpenAI response content and log any unexpected image markdown.
    """
    cleaned = response_content.strip()

    if "![" in cleaned:
        logger.warning(
            "Image markdown detected in OpenAI response for section: '%s'",
            section_title,
        )

    # Additional response sanitation can go here
    return cleaned


# --- Mock OpenAI Client ---
class MockOpenAIClient:
    """
    A mock client to simulate OpenAI API calls without actual costs or calls.
    """

    def __init__(self, api_key: Optional[str] = "MOCK_API_KEY"):
        self.api_key = api_key

    class Chat:
        class Completions:
            @staticmethod
            def create(
                model: str, messages: List[Dict[str, str]], temperature: float, **kwargs
            ) -> Any:
                time.sleep(0.05)

                user_content = messages[-1]["content"]
                print(
                    f"\n--- MockOpenAIClient.create called (Model: {model}, Temp: {temperature}) ---"
                )

                suggestion_keywords = [
                    "You are a senior SRE and technical learning designer.",
                    "Evaluate the following H3 sub-sections from this panel.",
                    "H3 Sub-sections to Evaluate:\n---",
                    "provide your assessment in the following JSON format:",
                ]
                is_suggestion_prompt = all(
                    kw in user_content for kw in suggestion_keywords
                )

                enhancement_keywords = [
                    "You are a senior SRE and technical learning designer.",
                    "improve a specific H3 sub-section from a larger document panel",
                    "Here is the original H3 sub-section content:\n---",
                    "Return *only* the complete, improved Markdown for this H3 sub-section",
                ]
                is_enhancement_prompt = all(
                    kw in user_content for kw in enhancement_keywords
                )

                if is_suggestion_prompt:
                    print(
                        "MockOpenAIClient: Matched 'get_enhancement_suggestions' prompt. Simulating JSON response."
                    )
                    mock_suggestions: Dict[str, Dict[str, Any]] = {}
                    h3_eval_block_match = re.search(
                        r"H3 Sub-sections to Evaluate:\s*---\s*(.*?)\s*---",
                        user_content,
                        re.DOTALL | re.MULTILINE,
                    )
                    h3_titles_in_prompt = []
                    if h3_eval_block_match:
                        h3_eval_text = h3_eval_block_match.group(1)
                        found_titles = re.findall(
                            r"^\s*##\s*(.+?)\s*$", h3_eval_text, re.MULTILINE
                        )
                        h3_titles_in_prompt = [
                            title.strip()
                            for title in found_titles
                            if title.strip() != "H3 Sub-sections to Evaluate:"
                        ]
                        print(
                            f"MockOpenAIClient: Parsed H3 titles for suggestions: {h3_titles_in_prompt}"
                        )
                    else:
                        print(
                            "MockOpenAIClient: Could not find 'H3 Sub-sections to Evaluate' block in prompt."
                        )

                    if not h3_titles_in_prompt:
                        print(
                            "MockOpenAIClient: No H3 titles parsed from prompt for suggestions, returning empty JSON."
                        )
                        response_content = json.dumps({}, indent=2)
                    else:
                        for i, title in enumerate(h3_titles_in_prompt):
                            title_key = str(title).strip()
                            if (
                                title_key == "Initial Content"
                                and len(h3_titles_in_prompt) > 1
                            ):
                                enhance_decision = "No"
                                recommendation = None
                                reason = f"Mock: '{title_key}' is introductory; focus on named H3s."
                            elif i % 2 == 0:  # Alternate suggestions
                                enhance_decision = "Yes"
                                recommendation = (
                                    "Mock Suggestion: Add Real-World Analogy"
                                )
                                reason = f"Mock: An analogy would make '{title_key}' more relatable."
                            else:
                                enhance_decision = "No"
                                recommendation = None
                                reason = (
                                    f"Mock: The section '{title_key}' appears adequate."
                                )
                            mock_suggestions[title_key] = {
                                "enhance": enhance_decision,  # Storing as string like API
                                "recommendation": recommendation,
                                "reason": reason,
                            }
                        response_content = json.dumps(mock_suggestions, indent=2)

                elif is_enhancement_prompt:
                    print(
                        "MockOpenAIClient: Matched 'enhance_section' prompt. Simulating Markdown response."
                    )
                    original_h3_title_match = re.search(
                        r'The H3 sub-section to improve is: "([^"]+)"', user_content
                    )
                    original_h3_title = (
                        original_h3_title_match.group(1).strip()
                        if original_h3_title_match
                        else "Unknown Section Title"
                    )
                    enhancement_type_match = re.search(
                        r"Suggested Enhancement Type: ([^\n]+)", user_content
                    )
                    enhancement_type = (
                        enhancement_type_match.group(1).strip()
                        if enhancement_type_match
                        else "a general improvement"
                    )
                    response_content = (
                        f"### {original_h3_title} (Mock Enhanced - Type: {enhancement_type})\n\n"
                        f"This is the **MOCK enhanced Markdown content** for '{original_h3_title}'.\n"
                        f"The mock suggestion was to improve it with: '{enhancement_type}'.\n\n"
                        f"- Mock bullet point one reflecting the change.\n"
                        f"- Mock bullet point two with further details."
                    )
                else:
                    print(
                        "MockOpenAIClient: Prompt not matched. Simulating a generic non-JSON response."
                    )
                    response_content = "This is a generic mock response from OpenAI because the prompt was not recognized as a specific suggestion or enhancement request by the mock client."

                class MockMessage:
                    def __init__(self, content_str):
                        self.content = content_str

                class MockChoice:
                    def __init__(self, content_str):
                        self.message = MockMessage(content_str)

                class MockResponse:
                    def __init__(self, content_str):
                        self.choices = [MockChoice(content_str)]

                return MockResponse(response_content)

        def __init__(self):
            self.completions = self.Completions()

    def __init__(
        self, api_key: Optional[str] = "MOCK_API_KEY", **kwargs
    ):  # Added **kwargs
        self.api_key = api_key
        self.chat = self.Chat()
        print(
            f"INFO: MockOpenAIClient initialized. API Key: {'SET' if api_key else 'NOT SET'}"
        )


# --- Service Functions ---
MOCK_CLIENT = False  # <--- CHANGE THIS TO False TO USE REAL API

# Attempt to load API key from environment variable if not mocking
# This is just for the real client; mock client doesn't use it.
# The real OpenAI() client automatically looks for OPENAI_API_KEY.
# api_key_from_env = os.getenv("OPENAI_API_KEY")

if MOCK_CLIENT:
    client = MockOpenAIClient(api_key="FAKE_KEY_FOR_MOCK_IF_NEEDED_BY_MOCK")
    print("INFO: Using MOCK OpenAI client.")
else:
    try:
        from openai import OpenAI  # Standard import for openai library v1.x+

        # The OpenAI client will automatically use the OPENAI_API_KEY environment variable.
        # You can also pass it explicitly: client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # if you prefer, but it's not strictly necessary if the env var is set.
        client = OpenAI()
        print(
            "INFO: Using REAL OpenAI client. Ensure OPENAI_API_KEY environment variable is set."
        )
        # Perform a simple test call if desired, e.g., listing models (be mindful of costs)
        # models = client.models.list()
        # print("INFO: Successfully connected to OpenAI and listed models.")
    except ImportError:
        print("ERROR: OpenAI library not found. Please install it: pip install openai")
        print("INFO: Falling back to MOCK_CLIENT.")
        client = MockOpenAIClient(api_key="FALLBACK_MOCK_KEY_IMPORT_ERROR")
        MOCK_CLIENT = True
    except (
        Exception
    ) as e:  # Catch other potential errors during OpenAI client initialization
        print(f"ERROR: Failed to initialize REAL OpenAI client: {e}")
        print("INFO: Falling back to MOCK_CLIENT.")
        client = MockOpenAIClient(api_key="FALLBACK_MOCK_KEY_INIT_ERROR")
        MOCK_CLIENT = True


MODEL_FOR_SUGGESTIONS = "gpt-4o-2024-11-20"  # Or "gpt-3.5-turbo", etc.
MODEL_FOR_ENHANCEMENT = "gpt-4o-2024-11-20"  # Or "gpt-3.5-turbo", etc.


def get_enhancement_suggestions_for_panel_h3s(
    panel_title: str, panel_context_markdown: str, h3_sections_content: Dict[str, str]
) -> Dict[str, Dict[str, Any]]:
    if not h3_sections_content:
        return {}

    h3_sections_text_for_prompt = []
    for h3_title, h3_md in h3_sections_content.items():
        content_without_heading = h3_md
        temp_content = h3_md.strip()

        # Prepare content for the prompt: use "## H3_Title" for the prompt structure
        # and strip the original "### H3_Title" from the content itself if present.
        if h3_title != "Initial Content" and temp_content.startswith(f"### {h3_title}"):
            lines = temp_content.splitlines()
            if len(lines) > 1:
                content_without_heading = "\n".join(lines[1:]).strip()
            else:
                content_without_heading = ""  # Only heading was present
        elif (
            h3_title == "Initial Content"
        ):  # Initial content doesn't have its own H3 heading in h3_md
            content_without_heading = temp_content
        # Else, if it's a named H3 but doesn't start with its own heading (e.g. original_full_markdown was just content blocks)
        # then content_without_heading remains as temp_content.

        h3_sections_text_for_prompt.append(
            f"## {h3_title}\n{content_without_heading if content_without_heading.strip() else 'This section appears to have no primary content following its heading.'}"
        )

    prompt = f"""You are a senior SRE and technical learning designer.
You are reviewing H3 sub-sections within a larger document panel titled: "{panel_title}"

Here is some overall context for this panel (which may include its H2 title and potentially key introductory H3 sections like Scene Description or Teaching Narrative):
---
{panel_context_markdown}
---

Evaluate the following H3 sub-sections from this panel. For each one, determine if it could be enhanced for clarity, engagement, or practical application.

H3 Sub-sections to Evaluate:
---
{ "\n\n---\n\n".join(h3_sections_text_for_prompt) }
---

For each H3 sub-section evaluated (use its exact title as the key, e.g., "Scene Description", "Common Example of the Problem"), provide your assessment in the following JSON format:
{{
  "Exact H3 Title 1": {{ "enhance": "Yes/No", "recommendation": "Type of enhancement (e.g., Add Mermaid Diagram, Text Diagram, More Examples, Checklist, Code Snippet, Table, Analogy) or null if No", "reason": "Brief justification for your recommendation or why no enhancement is needed." }},
  "Exact H3 Title 2": {{ "enhance": "Yes/No", "recommendation": "...", "reason": "..." }}
}}

Ensure your entire response is a single, valid JSON object. Do not add any explanatory text before or after the JSON.
"""
    # print(f"\nDEBUG [OpenAI Service] Suggestions Prompt for Panel '{panel_title}':\n{prompt[:1000]}...\n") # For debugging

    print(
        f"\n[OpenAI Service] Getting suggestions for Panel: '{panel_title}' (Processing {len(h3_sections_content)} H3s)"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_FOR_SUGGESTIONS,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            # response_format={ "type": "json_object" }, # For newer models that support JSON mode
        )
        raw_response_content = response.choices[0].message.content
        if not raw_response_content:
            print("[OpenAI Service] ERROR: Received empty response for suggestions.")
            return {}

        # Clean potential markdown code block fences around JSON
        cleaned_response = raw_response_content.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
        elif cleaned_response.startswith(
            "```"
        ):  # Handle case where 'json' isn't specified
            cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

        suggestions = json.loads(cleaned_response.strip())

        parsed_suggestions = {}
        for title_key, details in suggestions.items():
            if isinstance(details, dict):
                parsed_suggestions[title_key] = {
                    "enhance": str(details.get("enhance", "No")).lower()
                    == "yes",  # Ensure boolean
                    "recommendation": details.get("recommendation"),
                    "reason": details.get("reason"),
                }
            else:
                print(
                    f"[OpenAI Service] WARNING: Unexpected format for suggestion details for '{title_key}': {details}"
                )
        return parsed_suggestions
    except json.JSONDecodeError as e:
        print(
            f"[OpenAI Service] ERROR: Error decoding JSON response for suggestions: {e}"
        )
        print(f"Raw response was:\n>>>\n{raw_response_content}\n<<<")
        return {}
    except Exception as e:
        print(
            f"[OpenAI Service] ERROR: Unexpected error getting suggestions: {type(e).__name__} - {e}"
        )
        # if not MOCK_CLIENT and hasattr(e, 'response') and hasattr(e.response, 'text'):
        # print(f"OpenAI API Error Details: {e.response.text}")
        return {}


def get_improved_markdown_for_section(
    original_h3_markdown_content: str,
    enhancement_type: Optional[str],
    enhancement_reason: Optional[str],
    panel_title_context: str,
    overall_panel_context_md: str,
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
            model=MODEL_FOR_ENHANCEMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
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


def strip_markdown_fences(markdown_content: str) -> str:
    """
    Strips markdown code fences from content returned by OpenAI.
    """
    if not markdown_content:
        return markdown_content

    cleaned = markdown_content.strip()
    lines = cleaned.splitlines()

    # Check if the content is wrapped in code fences
    if (
        len(lines) >= 2
        and lines[0].strip().startswith("```markdown")
        and lines[-1].strip() == "```"
    ):
        # Remove the first and last lines (the fences)
        cleaned = "\n".join(lines[1:-1]).strip()

        # Recursively clean in case there are nested fences
        if cleaned.startswith("```"):
            return strip_markdown_fences(cleaned)

    return cleaned


def rewrite_scene_and_teaching_as_summary(
    scene_markdown: str,
    teaching_markdown: str,
    model: str = "gpt-4o-2024-11-20",
    temperature: float = 0.4,
) -> str:
    """
    Calls OpenAI to rewrite a scene description and teaching narrative
    into a concise, visually friendly summary for a comic panel.
    """
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
    model: str = "gpt-4o-2024-11-20",
    temperature: float = 0.3,
) -> str:
    """
    Generates a short 3–5 word narration summary for a panel, based on its source content.
    """
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
    model: str = "gpt-4o-2024-11-20",
    temperature: float = 0.7,
) -> Dict[str, str]:
    """
    Generate a speech bubble line (or none) per character in the scene.

    Args:
        scene_summary: Visual and emotional summary of the panel
        character_names: Characters visible in the panel
        character_data: Full character profile dictionary

    Returns:
        Dict mapping character name to speech bubble text
    """
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
        tags.append("Teaching Scene")  # default
    return tags

# openai_service.py
import json
import re
import time
from typing import Any, Dict, List, Optional


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
                # Uncomment for deep prompt debugging:
                # print(f"\n--- MockOpenAIClient.create RECEIVED PROMPT (Model '{model}') ---")
                # print(f"First 600 chars:\n{user_content[:600]}")
                # print("---------------------------------------------------------------")
                print(f"\n--- MockOpenAIClient.create called (Model: {model}) ---")

                # More specific and ordered keywords for "get_section_improvement_suggestions"
                suggestion_keywords = [
                    "You are a senior SRE and technical learning designer.",
                    "Evaluate the following H3 sub-sections from this panel.",
                    "H3 Sub-sections to Evaluate:\n---",
                    "provide your assessment in the following JSON format:",
                ]
                is_suggestion_prompt = all(
                    kw in user_content for kw in suggestion_keywords
                )

                # More specific and ordered keywords for "enhance_section"
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
                                reason = f"The '{title_key}' section is usually introductory; specific enhancements are better targeted at named H3s unless it's substantial."
                            elif i % 3 == 0:  # Vary the suggestions a bit more
                                enhance_decision = "Yes"
                                recommendation = "Add Detailed Checklist"
                                reason = f"A checklist would provide actionable steps for '{title_key}'."
                            elif i % 3 == 1:
                                enhance_decision = "Yes"
                                recommendation = "Incorporate a Table"
                                reason = f"A table could summarize key information in '{title_key}' effectively."
                            else:
                                enhance_decision = "No"
                                recommendation = None
                                reason = f"The section '{title_key}' is clear and does not require immediate changes."

                            mock_suggestions[title_key] = {
                                "enhance": enhance_decision,
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
                        f"### {original_h3_title} (Enhanced by MockAPI - Type: {enhancement_type})\n\n"
                        f"This is the **mock enhanced Markdown content** for the section originally titled '{original_h3_title}'.\n"
                        f"The suggestion was to improve it with: '{enhancement_type}'.\n\n"
                        f"Key changes include:\n"
                        f"- More detailed explanations and examples have been woven in.\n"
                        f"- A new summary bullet point list might be added for quick takeaways.\n\n"
                        f"This mock ensures the content is different and reflects a tangible enhancement based on the suggestion."
                    )
                else:
                    print(
                        "MockOpenAIClient: Prompt not matched. Simulating a generic non-JSON response."
                    )
                    response_content = "This is a generic mock response from OpenAI because the prompt was not recognized as a specific suggestion or enhancement request."

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

    def __init__(self, api_key: Optional[str] = "MOCK_API_KEY", **kwargs):
        self.api_key = api_key
        self.chat = self.Chat()
        print(
            f"MockOpenAIClient initialized (v1.x style). API Key: {'SET' if api_key else 'NOT SET'}"
        )


# --- Service Functions ---
MOCK_CLIENT = True

if MOCK_CLIENT:
    client = MockOpenAIClient(api_key="FAKE_KEY_FOR_MOCK")
else:
    try:
        from openai import OpenAI

        client = OpenAI()
    except ImportError:
        print("OpenAI library not found. Please install it: pip install openai")
        print("Falling back to MOCK_CLIENT.")
        client = MockOpenAIClient(api_key="FALLBACK_MOCK_KEY")
        MOCK_CLIENT = True


MODEL_FOR_SUGGESTIONS = "gpt-4o"
MODEL_FOR_ENHANCEMENT = "gpt-4o"


def get_enhancement_suggestions_for_panel_h3s(
    panel_title: str, panel_context_markdown: str, h3_sections_content: Dict[str, str]
) -> Dict[str, Dict[str, Any]]:
    if not h3_sections_content:
        return {}

    h3_sections_text_for_prompt = []
    for h3_title, h3_md in h3_sections_content.items():
        content_without_heading = (
            h3_md  # Default to full markdown if heading not found/stripped
        )
        temp_content = h3_md.strip()

        # Check if h3_md starts with "### H3_Title" and strip it for the prompt section
        # The prompt expects "## H3_Title" for the mock client's parsing.
        expected_heading = f"### {h3_title}"
        if temp_content.startswith(expected_heading):
            lines = temp_content.splitlines()
            if len(lines) > 1:  # Content exists beyond the heading
                content_without_heading = "\n".join(lines[1:]).strip()
            else:  # Only the heading line was present
                content_without_heading = ""
        elif temp_content.startswith(
            "### "
        ):  # Starts with H3 but title mismatch or other H3
            # This means original_full_markdown might not be perfectly aligned with h3_title
            # Or h3_title is "Initial Content" and h3_md is actual content from another H3
            # For "Initial Content", h3_md should NOT start with "### Initial Content"
            if h3_title == "Initial Content":
                content_without_heading = temp_content  # Use as is
            else:  # It's a named H3, but title in content doesn't match. Strip generic H3.
                lines = temp_content.splitlines()
                if len(lines) > 1:
                    content_without_heading = "\n".join(lines[1:]).strip()
                else:
                    content_without_heading = ""

        h3_sections_text_for_prompt.append(
            f"## {h3_title}\n{content_without_heading if content_without_heading else 'This section appears to have no primary content following its heading.'}"
        )

    prompt = f"""You are a senior SRE and technical learning designer.
You are reviewing H3 sub-sections within a larger document panel titled: "{panel_title}"

Here is some overall context for this panel:
---
{panel_context_markdown}
---

Evaluate the following H3 sub-sections from this panel. For each one, determine if it could be enhanced for clarity, engagement, or practical application.

H3 Sub-sections to Evaluate:
---
{ "\n\n---\n\n".join(h3_sections_text_for_prompt) }
---

For each H3 sub-section evaluated (use its exact title as the key), provide your assessment in the following JSON format:
{{
  "Exact H3 Title 1": {{ "enhance": "Yes/No", "recommendation": "Type of enhancement (e.g., Add Diagram, More Examples, Checklist, Code Snippet, Table, Analogy) or null if No", "reason": "Brief justification for your recommendation or why no enhancement is needed." }},
  "Exact H3 Title 2": {{ "enhance": "Yes/No", "recommendation": "...", "reason": "..." }}
}}

Ensure your entire response is a single, valid JSON object.
"""
    print(
        f"\n[OpenAI Service] Getting suggestions for Panel: {panel_title} (H3s: {list(h3_sections_content.keys())})"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_FOR_SUGGESTIONS,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw_response_content = response.choices[0].message.content
        if not raw_response_content:
            print("[OpenAI Service] Error: Received empty response for suggestions.")
            return {}

        cleaned_response = raw_response_content.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        suggestions = json.loads(cleaned_response.strip())

        parsed_suggestions = {}
        for title, details in suggestions.items():
            if isinstance(details, dict):
                parsed_suggestions[title] = {
                    "enhance": str(details.get("enhance", "No")).lower() == "yes",
                    "recommendation": details.get("recommendation"),
                    "reason": details.get("reason"),
                }
            else:
                print(
                    f"[OpenAI Service] Warning: Unexpected format for suggestion details for '{title}': {details}"
                )
        return parsed_suggestions
    except json.JSONDecodeError as e:
        print(f"[OpenAI Service] Error decoding JSON response for suggestions: {e}")
        print(f"Raw response was:\n>{raw_response_content}<")
        return {}
    except Exception as e:
        print(f"[OpenAI Service] Unexpected error getting suggestions: {e}")
        return {}


def get_improved_markdown_for_section(
    original_h3_markdown_content: str,
    enhancement_type: Optional[str],
    enhancement_reason: Optional[str],
    panel_title_context: str,
    overall_panel_context_md: str,
) -> Optional[str]:
    if (
        not original_h3_markdown_content
    ):  # If original content is empty, nothing to improve
        print(
            f"[OpenAI Service] Skipping enhancement for empty original content (H3: {original_h3_markdown_content[:30]}...)."
        )
        return None  # Or return original_h3_markdown_content if API should generate from scratch

    h3_title_in_md = "This Section"
    lines = original_h3_markdown_content.strip().splitlines()
    if lines and lines[0].strip().startswith("### "):
        h3_title_in_md = lines[0].strip()

    prompt = f"""You are a senior SRE and technical learning designer.
You are tasked with improving a specific H3 sub-section from a larger document panel titled "{panel_title_context}".
The overall context for the panel (e.g., Scene Description, Teaching Narrative) is:
---
{overall_panel_context_md}
---

The H3 sub-section to improve is: "{h3_title_in_md.replace("### ","").strip()}"

It was previously identified that this section should be enhanced.
Suggested Enhancement Type: {enhancement_type or "General improvement"}
Reason for Enhancement: {enhancement_reason or "Make it more engaging and clear."}

Here is the original H3 sub-section content:
---
{original_h3_markdown_content}
---

Please provide an improved version of this H3 sub-section.
- Incorporate the suggested enhancement.
- Preserve the original tone and technical accuracy.
- Ensure the output is well-formatted Markdown.
- Return *only* the complete, improved Markdown for this H3 sub-section, including its H3 heading. Do not add any explanatory text before or after the Markdown.
"""
    print(f"\n[OpenAI Service] Requesting enhancement for H3 section: {h3_title_in_md}")
    try:
        response = client.chat.completions.create(
            model=MODEL_FOR_ENHANCEMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        improved_markdown = response.choices[0].message.content
        if improved_markdown:
            return improved_markdown.strip()
        else:
            print(
                "[OpenAI Service] Error: Received empty response for content enhancement."
            )
            return None
    except Exception as e:
        print(f"[OpenAI Service] Unexpected error during content enhancement: {e}")
        return None

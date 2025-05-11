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
                time.sleep(0.05)  # Even faster for testing

                user_content = messages[-1]["content"]
                # For debugging prompts:
                # print(f"\n--- MockOpenAIClient.create received prompt for Model '{model}': ---\n{user_content}\n------------------------------------")
                print(f"\n--- MockOpenAIClient.create called (Model: {model}) ---")

                # Specific keywords for "get_section_improvement_suggestions"
                is_suggestion_prompt = (
                    "You are a senior SRE and technical learning designer."
                    in user_content
                    and "Evaluate the following H3 sub-sections" in user_content
                    and "provide your assessment in the following JSON format"
                    in user_content
                    and "H3 Sub-sections to Evaluate:" in user_content
                )
                # Specific keywords for "enhance_section"
                is_enhancement_prompt = (
                    "You are a senior SRE and technical learning designer."
                    in user_content
                    and "improve a specific H3 sub-section" in user_content
                    and "Return *only* the complete, improved Markdown" in user_content
                    and "Here is the original H3 sub-section content:" in user_content
                )

                if is_suggestion_prompt:
                    print(
                        "MockOpenAIClient: Matched 'get_enhancement_suggestions' prompt. Simulating JSON response."
                    )

                    mock_suggestions: Dict[str, Dict[str, Any]] = {}
                    # Regex to find "## Title" which is how H3s are formatted in the prompt for evaluation
                    h3_titles_in_prompt = re.findall(
                        r"^\s*##\s*(.+?)\s*$", user_content, re.MULTILINE
                    )
                    # Filter out the "H3 Sub-sections to Evaluate:" line itself if caught
                    h3_titles_in_prompt = [
                        title
                        for title in h3_titles_in_prompt
                        if title != "H3 Sub-sections to Evaluate:"
                    ]

                    print(
                        f"MockOpenAIClient: Parsed H3 titles for suggestions: {h3_titles_in_prompt}"
                    )

                    if not h3_titles_in_prompt:
                        print(
                            "MockOpenAIClient: Could not parse H3 titles from prompt for suggestions, returning empty JSON."
                        )
                        # Return empty JSON to avoid breaking downstream parsing
                        response_content = json.dumps({}, indent=2)
                    else:
                        for i, title in enumerate(h3_titles_in_prompt):
                            title_key = str(title).strip()  # Ensure it's a clean string
                            if i % 2 == 0:
                                mock_suggestions[title_key] = {
                                    "enhance": "Yes",
                                    "recommendation": "Add Real-World Analogy",
                                    "reason": f"An analogy would make '{title_key}' more relatable.",
                                }
                            else:
                                mock_suggestions[title_key] = {
                                    "enhance": "No",
                                    "recommendation": None,
                                    "reason": f"The section '{title_key}' is sufficiently detailed.",
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
                        f"### {original_h3_title} (Enhanced by MockAPI - {enhancement_type})\n\n"
                        f"This is the **mock enhanced version** of the section titled '{original_h3_title}'.\n"
                        f"It has been improved by incorporating the suggestion to '{enhancement_type}'.\n\n"
                        f"- A new key insight has been added.\n"
                        f"- Existing explanations were made more concise.\n\n"
                        f"This mock ensures the content is different and reflects an enhancement."
                    )
                else:
                    print(
                        "MockOpenAIClient: Prompt not matched. Simulating a generic non-JSON response (this will cause JSONDecodeError downstream if JSON is expected)."
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
        content_without_heading = h3_md
        # The h3_md (original_full_markdown) should already include "### H3 Title"
        # The mock client expects "## H3 Title" in the list for parsing.
        # For the real API, sending "### H3 Title\nContent..." is fine.
        # Let's adjust the prompt formatting for the mock client's parsing.

        # Strip the actual H3 heading from h3_md if present, then prepend "## H3_Title"
        # for the mock client's title extraction logic.
        temp_content = h3_md.strip()
        if temp_content.startswith(f"### {h3_title}"):
            lines = temp_content.splitlines()
            if len(lines) > 1:
                content_without_heading = "\n".join(lines[1:]).strip()
            else:  # Only the heading line was present
                content_without_heading = ""
        elif temp_content.startswith(
            "### "
        ):  # Mismatch or different H3 title in content
            lines = temp_content.splitlines()
            if len(lines) > 1:
                content_without_heading = "\n".join(lines[1:]).strip()
            else:
                content_without_heading = ""

        h3_sections_text_for_prompt.append(
            f"## {h3_title}\n{content_without_heading if content_without_heading else 'No specific content provided for this section.'}"
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
            # response_format={ "type": "json_object" } # Uncomment for newer models
        )
        raw_response_content = response.choices[0].message.content
        if not raw_response_content:
            print("[OpenAI Service] Error: Received empty response for suggestions.")
            return {}

        # Clean potential markdown code block fences
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
    if not original_h3_markdown_content:
        return None

    h3_title_in_md = "This Section"
    lines = original_h3_markdown_content.strip().splitlines()
    if lines and lines[0].strip().startswith("### "):
        h3_title_in_md = lines[0].strip()  # This will be "### Actual Title"

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

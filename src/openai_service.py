# openai_service.py
import json
import os  # For environment variables
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


MODEL_FOR_SUGGESTIONS = "gpt-4o"  # Or "gpt-3.5-turbo", etc.
MODEL_FOR_ENHANCEMENT = "gpt-4o"  # Or "gpt-3.5-turbo", etc.


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
  "Exact H3 Title 1": {{ "enhance": "Yes/No", "recommendation": "Type of enhancement (e.g., Add Diagram, More Examples, Checklist, Code Snippet, Table, Analogy) or null if No", "reason": "Brief justification for your recommendation or why no enhancement is needed." }},
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
        print(
            f"[OpenAI Service] INFO: Skipping enhancement for empty or whitespace-only original content."
        )
        return original_h3_markdown_content  # Return original (empty/whitespace)

    # Extract H3 title from the original_h3_markdown_content if it starts with "###"
    h3_title_in_md = "This Section"  # Default if no H3 heading found in the content
    lines = original_h3_markdown_content.strip().splitlines()
    if lines and lines[0].strip().startswith("### "):
        h3_title_in_md = lines[0].strip()  # This will be like "### Scene Description"
        # For the prompt, we might want just "Scene Description"
        h3_title_for_prompt = h3_title_in_md[4:].strip()  # Remove "### "
    else:  # If it doesn't start with H3, use a placeholder or infer
        h3_title_for_prompt = "the provided section"

    prompt = f"""You are a senior SRE and technical learning designer.
You are tasked with improving a specific H3 sub-section from a larger document panel titled "{panel_title_context}".
The overall context for the panel is:
---
{overall_panel_context_md}
---

The H3 sub-section to improve is titled: "{h3_title_for_prompt}"

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
- Return *only* the complete, improved Markdown for this H3 sub-section, *including its H3 heading* (e.g., "### {h3_title_for_prompt}\n...new content..."). 
- Do not add any explanatory text, apologies, or conversational filler before or after the Markdown.
"""
    # print(f"\nDEBUG [OpenAI Service] Enhancement Prompt for H3 '{h3_title_for_prompt}':\n{prompt[:1000]}...\n")

    print(
        f"\n[OpenAI Service] Requesting enhancement for H3 section: '{h3_title_for_prompt}' in panel '{panel_title_context}'"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_FOR_ENHANCEMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Higher temperature for more creative rewriting
        )
        improved_markdown = response.choices[0].message.content
        if improved_markdown:
            # Ensure the response starts with the H3 heading if the API sometimes forgets
            cleaned_improved_markdown = improved_markdown.strip()
            expected_heading = f"### {h3_title_for_prompt}"
            if not cleaned_improved_markdown.startswith(
                "### "
            ):  # If API omits H3 heading
                # Try to find if original_h3_markdown_content started with one to reconstruct
                if original_h3_markdown_content.strip().startswith("### "):
                    original_heading_line = (
                        original_h3_markdown_content.strip().splitlines()[0]
                    )
                    if not cleaned_improved_markdown.strip().startswith(
                        original_heading_line.strip()
                    ):
                        print(
                            f"[OpenAI Service] INFO: Prepending original H3 heading '{original_heading_line.strip()}' to API response."
                        )
                        cleaned_improved_markdown = (
                            original_heading_line + "\n\n" + cleaned_improved_markdown
                        )
                # else if no original heading, and API didn't provide one, this might be an issue.
                # For now, we assume the API is instructed to return it.

            return cleaned_improved_markdown
        else:
            print(
                "[OpenAI Service] ERROR: Received empty response for content enhancement."
            )
            return None
    except Exception as e:
        print(
            f"[OpenAI Service] ERROR: Unexpected error during content enhancement: {type(e).__name__} - {e}"
        )
        return None

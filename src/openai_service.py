# openai_service.py
import json
import re  # Import re for more robust title extraction
import time
from typing import Any, Dict, List, Optional

# --- Mock OpenAI Client ---
# In a real application, you would import and use the actual openai library:
# from openai import OpenAI
# client = OpenAI(api_key="YOUR_OPENAI_API_KEY_OR_ENV_VAR")


class MockOpenAIClient:
    """
    A mock client to simulate OpenAI API calls without actual costs or calls.
    """

    def __init__(self, api_key: Optional[str] = "MOCK_API_KEY"):
        self.api_key = api_key
        # print(f"MockOpenAIClient initialized. (API Key: {'SET' if api_key else 'NOT SET'})") # Less verbose

    class Chat:
        class Completions:
            @staticmethod
            def create(
                model: str, messages: List[Dict[str, str]], temperature: float, **kwargs
            ) -> Any:
                time.sleep(0.2)  # Reduced sleep time for faster testing

                user_content = messages[-1]["content"]
                print(f"\n--- MockOpenAIClient.create called (Model: {model}) ---")

                # Condition for "get_section_improvement_suggestions"
                # Making keywords more specific to the generated prompt
                is_suggestion_prompt = (
                    "Evaluate the following H3 sub-sections" in user_content
                    and "provide your assessment in the following JSON format"
                    in user_content
                )
                # Condition for "enhance_section"
                is_enhancement_prompt = (
                    "improve a specific H3 sub-section" in user_content
                    and "Return *only* the complete, improved Markdown" in user_content
                )

                if is_suggestion_prompt:
                    print(
                        "MockOpenAIClient: Simulating 'get_enhancement_suggestions' response."
                    )

                    mock_suggestions: Dict[str, Dict[str, Any]] = {}
                    # Extract H3 titles using regex from the "H3 Sub-sections to Evaluate" part
                    # The prompt format is "## H3 Title\nContent..."
                    # Regex to find lines starting with "## " followed by text
                    # and not part of the overall panel context section.

                    # Find the block of H3s first
                    h3_block_match = re.search(
                        r"H3 Sub-sections to Evaluate:\s*---(.*?)---",
                        user_content,
                        re.DOTALL | re.MULTILINE,
                    )
                    h3_titles_in_prompt = []
                    if h3_block_match:
                        h3_block_text = h3_block_match.group(1)
                        h3_titles_in_prompt = [
                            line.replace("## ", "").strip()
                            for line in h3_block_text.splitlines()
                            if line.strip().startswith("## ")
                        ]

                    if not h3_titles_in_prompt:
                        print(
                            "MockOpenAIClient: Could not parse H3 titles from prompt for suggestions, using fallback titles."
                        )
                        # Fallback if parsing fails, to ensure some JSON is returned
                        h3_titles_in_prompt = [
                            "Common Example of the Problem",
                            "SRE Best Practice: Evidence-Based Investigation",
                            "Banking Impact",
                            "Implementation Guidance",
                            "Scene Description",
                            "Teaching Narrative",
                        ]

                    for i, title in enumerate(h3_titles_in_prompt):
                        if i % 2 == 0:  # Alternate for variety
                            mock_suggestions[title] = {
                                "enhance": "Yes",
                                "recommendation": "Add Diagram",
                                "reason": f"A diagram would visually clarify the key points for '{title}'.",
                            }
                        else:
                            mock_suggestions[title] = {
                                "enhance": "No",
                                "recommendation": None,
                                "reason": f"The section '{title}' is clear and concise as is.",
                            }

                    response_content = json.dumps(mock_suggestions, indent=2)

                elif is_enhancement_prompt:
                    print("MockOpenAIClient: Simulating 'enhance_section' response.")

                    # Extract original H3 title from the prompt for more realistic mock
                    original_h3_title_match = re.search(
                        r'The H3 sub-section to improve is: "([^"]+)"', user_content
                    )
                    original_h3_title = (
                        original_h3_title_match.group(1)
                        if original_h3_title_match
                        else "Unknown Section"
                    )

                    enhancement_type_match = re.search(
                        r"Suggested Enhancement Type: ([^\n]+)", user_content
                    )
                    enhancement_type = (
                        enhancement_type_match.group(1)
                        if enhancement_type_match
                        else "General improvement"
                    )

                    original_section_content_match = re.search(
                        r"Here is the original H3 sub-section content:\s*---(.*?)---",
                        user_content,
                        re.DOTALL | re.MULTILINE,
                    )
                    original_section_content_snippet = (
                        original_section_content_match.group(1).strip()[:100]
                        if original_section_content_match
                        else "Original content snippet not found."
                    )

                    response_content = (
                        f"### {original_h3_title} (Enhanced Mock)\n\n"
                        f"This is the **mock enhanced version** of the section, "
                        f"incorporating the suggestion to '{enhancement_type}'.\n\n"
                        f"The original content started like this: '{original_section_content_snippet}...'\n\n"
                        f"Further improvements could include more real-world examples or a checklist."
                    )
                else:
                    print(
                        "MockOpenAIClient: Simulating a generic non-JSON response (prompt not specifically matched)."
                    )
                    response_content = "This is a generic mock response from OpenAI because the prompt was not recognized as suggestion or enhancement."

                class MockMessage:
                    def __init__(self, content_str):
                        self.content = content_str

                class MockChoice:
                    def __init__(self, content_str):
                        self.message = MockMessage(content_str)

                class MockResponse:
                    def __init__(self, content_str):
                        self.choices = [MockChoice(content_str)]

                # print(f"Mock response generated: {response_content[:150]}...") # For debugging
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
        # Strip the H3 heading itself if present in h3_md, as we add "## H3 Title"
        content_without_heading = h3_md
        if h3_md.strip().startswith(f"### {h3_title}"):
            lines = h3_md.splitlines()
            content_without_heading = "\n".join(lines[1:]).strip()

        h3_sections_text_for_prompt.append(f"## {h3_title}\n{content_without_heading}")

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

        if raw_response_content.strip().startswith("```json"):
            raw_response_content = raw_response_content.strip()[7:]
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]

        suggestions = json.loads(raw_response_content.strip())

        parsed_suggestions = {}
        for title, details in suggestions.items():
            if isinstance(details, dict):  # Ensure details is a dictionary
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
        print(f"Raw response was:\n{raw_response_content}")
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

    h3_title_in_md = (
        original_h3_markdown_content.splitlines()[0].strip()
        if original_h3_markdown_content.strip().startswith("### ")
        else "This Section"
    )

    prompt = f"""You are a senior SRE and technical learning designer.
You are tasked with improving a specific H3 sub-section from a larger document panel titled "{panel_title_context}".
The overall context for the panel (e.g., Scene Description, Teaching Narrative) is:
---
{overall_panel_context_md}
---

The H3 sub-section to improve is: "{h3_title_in_md.replace("### ","")}"

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

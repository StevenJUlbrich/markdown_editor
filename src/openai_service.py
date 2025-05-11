# openai_service.py
import json
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
        print(
            f"MockOpenAIClient initialized. (API Key: {'SET' if api_key else 'NOT SET'})"
        )

    class Chat:
        class Completions:
            @staticmethod
            def create(
                model: str, messages: List[Dict[str, str]], temperature: float, **kwargs
            ) -> Any:
                # Simulate a delay
                time.sleep(0.5)

                user_content = messages[-1][
                    "content"
                ]  # Get the last message, which is the user's prompt
                print(f"\n--- MockOpenAIClient.create called ---")
                print(f"Model: {model}, Temperature: {temperature}")
                # print(f"Prompt (first 200 chars): {user_content[:200]}...")

                # Determine response based on prompt content (very basic simulation)
                if (
                    "Evaluate the following sections" in user_content
                    and "Respond in this JSON format" in user_content
                ):
                    # This is likely the "get_section_improvement_suggestions" call
                    print("Simulating 'get_section_improvement_suggestions' response.")
                    # Extract H3 section titles from the prompt to build a mock response
                    # This is a simplified way to get the keys for the JSON response
                    h3_titles_in_prompt = []
                    for line in user_content.splitlines():
                        if (
                            line.startswith("## ") and ":" not in line
                        ):  # A simple heuristic for H3 titles in the prompt format
                            h3_titles_in_prompt.append(line.replace("## ", "").strip())

                    mock_suggestions = {}
                    if not h3_titles_in_prompt:  # If parsing fails, use generic keys
                        h3_titles_in_prompt = [
                            "Common Example of the Problem",
                            "SRE Best Practice: Evidence-Based Investigation",
                            "Banking Impact",
                        ]

                    for title in h3_titles_in_prompt:
                        # Alternate "Yes" and "No" for variety
                        if len(mock_suggestions) % 2 == 0:
                            mock_suggestions[title] = {
                                "enhance": "Yes",
                                "recommendation": "Add Example",
                                "reason": f"A concrete example would clarify the concept for {title}.",
                            }
                        else:
                            mock_suggestions[title] = {
                                "enhance": "No",
                                "recommendation": None,
                                "reason": None,
                            }

                    response_content = json.dumps(mock_suggestions, indent=2)

                elif (
                    "Improve it accordingly" in user_content
                    and "Return only the new version" in user_content
                ):
                    # This is likely the "enhance_section" call
                    print("Simulating 'enhance_section' response.")
                    original_section_match = user_content.split(
                        "Here is the original section:\n"
                    )
                    original_section_text = (
                        original_section_match[1]
                        if len(original_section_match) > 1
                        else "Original section content not found in prompt."
                    )

                    response_content = (
                        f"### Mock Enhanced Section Title (was: {user_content.splitlines()[2].replace('- Type: ','')})\n"
                        f"This is the **mock enhanced version** of the section.\n\n"
                        f"Original content started with:\n{original_section_text[:100]}...\n\n"
                        f"The recommendation was to improve it with: {user_content.splitlines()[1].replace('- Type: ','')}.\n"
                        f"Reason: {user_content.splitlines()[2].replace('- Reason: ','')}"
                    )
                else:
                    print("Simulating a generic response.")
                    response_content = "This is a generic mock response from OpenAI."

                # Simulate the structure of an OpenAI API response object
                class MockMessage:
                    def __init__(self, content_str):
                        self.content = content_str

                class MockChoice:
                    def __init__(self, content_str):
                        self.message = MockMessage(content_str)

                class MockResponse:
                    def __init__(self, content_str):
                        self.choices = [MockChoice(content_str)]

                print(
                    f"Mock response content (first 100 chars): {response_content[:100]}..."
                )
                return MockResponse(response_content)

        def __init__(self):  # To allow MockOpenAIClient.Chat.Completions.create()
            self.completions = self.Completions()

    def __init__(
        self, api_key: Optional[str] = "MOCK_API_KEY", **kwargs
    ):  # For OpenAI v1.x client init
        self.api_key = api_key
        self.chat = self.Chat()  # Instantiate the inner Chat class
        print(
            f"MockOpenAIClient initialized for v1.x style. (API Key: {'SET' if api_key else 'NOT SET'})"
        )


# --- Service Functions ---
# For testing, use the mock client. In production, use the real one.
# MOCK_CLIENT = True # Set to False to attempt using the real OpenAI client (requires API key)
MOCK_CLIENT = True

if MOCK_CLIENT:
    client = MockOpenAIClient(api_key="FAKE_KEY_FOR_MOCK")
else:
    try:
        from openai import OpenAI  # type: ignore

        # IMPORTANT: Replace with your actual API key loading mechanism (e.g., environment variable)
        # Ensure the OPENAI_API_KEY environment variable is set if not using MOCK_CLIENT
        client = OpenAI()
    except ImportError:
        print("OpenAI library not found. Please install it: pip install openai")
        print("Falling back to MOCK_CLIENT.")
        client = MockOpenAIClient(api_key="FALLBACK_MOCK_KEY")
        MOCK_CLIENT = True


MODEL_FOR_SUGGESTIONS = "gpt-4o"  # Or your preferred model
MODEL_FOR_ENHANCEMENT = "gpt-4o"  # Or your preferred model


def get_enhancement_suggestions_for_panel_h3s(
    panel_title: str,
    panel_context_markdown: str,  # e.g., H2 title + Scene Description + Teaching Narrative
    h3_sections_content: Dict[str, str],  # Dict of {h3_title: h3_full_markdown_content}
) -> Dict[str, Dict[str, Any]]:
    """
    Sends content of multiple H3 sections from a panel to OpenAI to get enhancement suggestions.
    Args:
        panel_title: The title of the H2 Panel.
        panel_context_markdown: Markdown content providing overall context for the panel.
        h3_sections_content: A dictionary where keys are H3 titles and values are their
                             full Markdown content.
    Returns:
        A dictionary where keys are H3 titles and values are dictionaries
        with "enhance" (bool), "recommendation" (str), and "reason" (str).
    """
    if not h3_sections_content:
        return {}

    h3_sections_text_for_prompt = []
    for h3_title, h3_md in h3_sections_content.items():
        # Use a simpler heading for the prompt to avoid confusion with panel H2
        h3_sections_text_for_prompt.append(
            f"## {h3_title}\n{h3_md.splitlines()[1:] if h3_md.startswith('###') else h3_md}"
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
  // ... and so on for all provided H3 sub-sections.
}}

Ensure your entire response is a single, valid JSON object.
"""
    print(f"\n[OpenAI Service] Getting suggestions for Panel: {panel_title}")
    try:
        response = client.chat.completions.create(
            model=MODEL_FOR_SUGGESTIONS,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more deterministic suggestions
            # response_format={ "type": "json_object" } # For newer models that support JSON mode
        )
        raw_response_content = response.choices[0].message.content
        if not raw_response_content:
            print("[OpenAI Service] Error: Received empty response for suggestions.")
            return {}

        # Attempt to clean the response if it's wrapped in markdown code block
        if raw_response_content.strip().startswith("```json"):
            raw_response_content = raw_response_content.strip()[7:]
            if raw_response_content.endswith("```"):
                raw_response_content = raw_response_content[:-3]

        suggestions = json.loads(raw_response_content.strip())

        # Validate and convert "enhance" to boolean
        parsed_suggestions = {}
        for title, details in suggestions.items():
            parsed_suggestions[title] = {
                "enhance": str(details.get("enhance", "No")).lower() == "yes",
                "recommendation": details.get("recommendation"),
                "reason": details.get("reason"),
            }
        return parsed_suggestions
    except json.JSONDecodeError as e:
        print(f"[OpenAI Service] Error decoding JSON response for suggestions: {e}")
        print(f"Raw response was:\n{raw_response_content}")
        return {}  # Return empty or raise error
    except Exception as e:
        print(f"[OpenAI Service] Unexpected error getting suggestions: {e}")
        return {}


def get_improved_markdown_for_section(
    original_h3_markdown_content: str,  # Full original markdown of the H3 section
    enhancement_type: Optional[str],
    enhancement_reason: Optional[str],
    panel_title_context: str,  # Title of the parent H2 Panel
    overall_panel_context_md: str,  # Scene desc + teaching narrative
) -> Optional[str]:
    """
    Sends an H3 section's original Markdown and an enhancement suggestion to OpenAI
    and requests an improved version of the Markdown.
    Args:
        original_h3_markdown_content: The full Markdown string of the H3 section.
        enhancement_type: The type of enhancement suggested (e.g., "Add Diagram").
        enhancement_reason: The reason for the enhancement.
        panel_title_context: The title of the H2 panel this H3 belongs to.
        overall_panel_context_md: Broader context from the panel.
    Returns:
        The improved Markdown string for the H3 section, or None if an error occurs.
    """
    if not original_h3_markdown_content:
        return None

    # Extract H3 title from the original markdown for the prompt
    h3_title_in_md = (
        original_h3_markdown_content.splitlines()[0]
        if original_h3_markdown_content.startswith("### ")
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

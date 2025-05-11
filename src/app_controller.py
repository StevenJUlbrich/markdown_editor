# app_controller.py
from typing import Any, Dict, List, Optional

# Assuming document_model.py (with Pydantic models) is in the same directory or PYTHONPATH
from document_model import H3Pydantic, H4Pydantic, MarkdownDocument, PanelPydantic


class AppController:
    """
    Controller for the Markdown processing application.
    Manages interaction between the view (CLI/GUI) and the model (MarkdownDocument).
    """

    def __init__(self):
        self.doc_model: Optional[MarkdownDocument] = None

    def load_document(self, filepath: str) -> bool:
        """Loads a Markdown document using the model."""
        self.doc_model = MarkdownDocument()  # Create a new model instance for each load
        if self.doc_model.load_and_process(filepath):
            print("Controller: Document loaded and processed successfully.")
            return True
        else:
            print("Controller: Failed to load or process document.")
            self.doc_model = None  # Clear model if loading failed
            return False

    def get_document_structure_view_with_h4(self) -> str:
        """Gets a string representation of the document's panel/subsection structure, including H4s."""
        if (
            not self.doc_model
            or not self.doc_model.chapter_model
            or not self.doc_model.chapter_model.document_elements
        ):
            return "No document loaded or structure is empty."

        output_lines = [f"Chapter: {self.doc_model.chapter_model.chapter_title_text}"]

        for i, element in enumerate(self.doc_model.chapter_model.document_elements):
            if (
                element.type == "generic"
            ):  # Assuming GenericContentPydantic has a 'type' field or check isinstance
                output_lines.append(
                    f"  Generic Content Block {i+1} (preview: {element.content_markdown[:50].replace('\n', ' ')}...)"
                )
            elif isinstance(element, PanelPydantic):
                output_lines.append(f"  Panel: {element.panel_title_text}")
                for h3_section in element.h3_sections:
                    output_lines.append(f"    H3: {h3_section.heading_text}")
                    if h3_section.initial_content_markdown.strip():
                        output_lines.append(
                            f"      H4 (Implicit Initial Content): {h3_section.initial_content_markdown[:40].replace('\n', ' ')}..."
                        )
                    for h4_section in h3_section.h4_sections:
                        output_lines.append(
                            f"      H4: {h4_section.heading_text} (content: {h4_section.content_markdown[:30].replace('\n', ' ')}...)"
                        )
            else:  # Should not happen with current Pydantic models
                output_lines.append(
                    f"  Unknown Element Type at top level: {type(element)}"
                )

        return "\n".join(output_lines)

    def get_specific_section_content_md(
        self,
        panel_title_fragment: str,
        h3_title_fragment: Optional[str] = None,
        h4_title_fragment: Optional[str] = None,
    ) -> str:
        """
        Retrieves the full Markdown content of a specific H2 Panel, H3 Sub-section, or H4 Sub-sub-section.
        """
        if not self.doc_model:
            return "Error: No document loaded."

        panel = self.doc_model.get_panel_pydantic(panel_title_fragment)
        if not panel:
            return f"Error: Panel containing '{panel_title_fragment}' not found."

        # The model's get_section_markdown_for_api handles the logic for different levels
        content = self.doc_model.get_section_markdown_for_api(
            panel_title_fragment, h3_title_fragment, h4_title_fragment
        )
        return (
            content
            if content is not None
            else "Error: Content not found or issue in retrieval."
        )

    def prepare_sections_for_api_v2(
        self,
        sections_to_process: List[tuple[str, Optional[str], Optional[str]]],
        common_prompt: str = "Analyze the following content:",
    ) -> List[Dict[str, Any]]:
        """
        Retrieves content for multiple specified sections (H2, H3, or H4),
        simulating preparation for API calls.
        sections_to_process: List of tuples (panel_frag, h3_frag_or_None, h4_frag_or_None)
        """
        if not self.doc_model:
            print("Error: No document loaded for API preparation.")
            return []

        print(
            f"\n--- Preparing Multiple Sections for API (Prompt: '{common_prompt}') ---"
        )
        prepared_data = []
        for panel_frag, h3_frag, h4_frag in sections_to_process:
            content_md = self.get_specific_section_content_md(
                panel_frag, h3_frag, h4_frag
            )

            if content_md and not content_md.startswith("Error:"):
                print(
                    f"  Successfully retrieved content for: Panel '{panel_frag}'"
                    + (f", H3 '{h3_frag}'" if h3_frag else "")
                    + (f", H4 '{h4_frag}'" if h4_frag else "")
                    + "."
                )
                prepared_data.append(
                    {
                        "panel_title_fragment": panel_frag,
                        "h3_title_fragment": h3_frag,
                        "h4_title_fragment": h4_frag,
                        "prompt": common_prompt,  # This could be customized per section
                        "content_to_send": content_md,
                        # "api_response": None # Placeholder for actual API response
                    }
                )
            else:
                error_message = (
                    content_md if content_md else "Unknown error retrieving content."
                )
                print(
                    f"  Failed to retrieve content for: Panel '{panel_frag}'"
                    + (f", H3 '{h3_frag}'" if h3_frag else "")
                    + (f", H4 '{h4_frag}'" if h4_frag else "")
                    + f". Reason: {error_message}"
                )

        print(f"--- Prepared {len(prepared_data)} section(s) for API calls. ---")
        return prepared_data

    def modify_section_content(
        self,
        panel_title_fragment: str,
        h3_title_fragment: str,  # H3 must be specified for modification
        new_markdown_content: str,
        h4_title_fragment: Optional[str] = None,
    ) -> bool:
        """
        Modifies the content of a specific H3's "Initial Content" or an H4 sub-subsection.
        Direct modification of an entire H2 Panel's content is not directly supported by this method.
        """
        if not self.doc_model:
            print("Error: No document loaded to modify content.")
            return False
        if (
            not h3_title_fragment
        ):  # Ensure H3 is specified for current modification logic
            print("Error: H3 sub-section must be specified for content modification.")
            return False

        # This maps to the model's `update_subsection_content` which targets
        # H3's initial content (if h4_title is None) or a specific H4's content.
        success = self.doc_model.update_subsection_content(
            panel_title_fragment,
            h3_title_fragment,
            new_markdown_content,
            h4_subsubsection_title_fragment=h4_title_fragment,
        )
        if success:
            target_desc = (
                f"H4 '{h4_title_fragment}'"
                if h4_title_fragment
                else f"H3 '{h3_title_fragment}' (Initial Content)"
            )
            print(
                f"Controller: Content modification for {target_desc} in Panel '{panel_title_fragment}' was successful in the model."
            )
        else:
            print(
                f"Controller: Content modification failed for Panel '{panel_title_fragment}', H3 '{h3_title_fragment}'"
                + (f", H4 '{h4_title_fragment}'." if h4_title_fragment else ".")
            )
        return success

    def add_to_section_content(
        self,
        panel_title_fragment: str,
        h3_title_fragment: str,  # H3 must be specified
        new_markdown_content: str,
        position: str = "end",
        h4_title_fragment: Optional[str] = None,
    ) -> bool:
        """
        Adds new Markdown content to an H3's "Initial Content" or an H4 sub-subsection.
        """
        if not self.doc_model:
            print("Error: No document loaded to add content.")
            return False
        if not h3_title_fragment:
            print("Error: H3 sub-section must be specified for adding content.")
            return False

        success = self.doc_model.add_content_to_subsection(
            panel_title_fragment,
            h3_title_fragment,
            new_markdown_content,
            position=position,
            h4_subsubsection_title_fragment=h4_title_fragment,
        )
        if success:
            target_desc = (
                f"H4 '{h4_title_fragment}'"
                if h4_title_fragment
                else f"H3 '{h3_title_fragment}' (Initial Content)"
            )
            print(
                f"Controller: Adding content to {target_desc} in Panel '{panel_title_fragment}' was successful in the model."
            )
        else:
            print(
                f"Controller: Adding content failed for Panel '{panel_title_fragment}', H3 '{h3_title_fragment}'"
                + (f", H4 '{h4_title_fragment}'." if h4_title_fragment else ".")
            )
        return success

    def process_api_enhancements_for_h3(
        self,
        panel_title: str,
        h3_title: str,
        improved_markdown: str,
        recommendation: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Updates an H3Pydantic object with content received from an API (e.g., OpenAI).
        This uses the `api_improved_markdown` field.
        """
        if not self.doc_model:
            print("Error: No document loaded.")
            return False

        success = self.doc_model.update_h3_section_via_api(
            panel_title, h3_title, improved_markdown, recommendation, reason
        )
        if success:
            print(
                f"Controller: API enhancement for H3 '{h3_title}' in Panel '{panel_title}' recorded in model."
            )
        else:
            print(f"Controller: Failed to record API enhancement for H3 '{h3_title}'.")
        return success

    def save_document(self, output_filepath: str) -> bool:
        """
        Saves the current state of the document model to a new file.
        """
        if not self.doc_model:
            print("Error: No document loaded to save.")
            return False

        if self.doc_model.save_document(output_filepath):
            print(f"Controller: Document saved successfully to {output_filepath}.")
            return True
        else:
            print(f"Controller: Failed to save document to {output_filepath}.")
            return False

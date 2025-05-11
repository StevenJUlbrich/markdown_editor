# app_controller.py
from typing import Any, Dict, List, Optional

# Assuming document_model.py (with Pydantic models) is in the same directory or PYTHONPATH
from document_model import (
    GenericContentPydantic,
    H3Pydantic,
    H4Pydantic,
    MarkdownDocument,
    PanelPydantic,
)


class AppController:
    """
    Controller for the Markdown processing application.
    Manages interaction between the view (CLI/GUI) and the model (MarkdownDocument).
    """

    def __init__(self):
        self.doc_model: Optional[MarkdownDocument] = None
        # To store context for multi-step operations, e.g., selecting a panel then a subsection
        self.current_selected_panel: Optional[PanelPydantic] = None
        self.last_listed_targetable_sections: List[Dict[str, Any]] = []

    def load_document(self, filepath: str) -> bool:
        """Loads a Markdown document using the model."""
        self.doc_model = MarkdownDocument()
        self.current_selected_panel = None  # Reset selected panel on new load
        self.last_listed_targetable_sections = []
        if self.doc_model.load_and_process(filepath):
            print("Controller: Document loaded and processed successfully.")
            return True
        else:
            print("Controller: Failed to load or process document.")
            self.doc_model = None
            return False

    # --- Listing Methods for CLI ---
    def list_all_h2_sections_for_cli(self) -> Optional[List[Dict[str, Any]]]:
        """1. List All H2 Sections (generic or panel)"""
        if not self.doc_model:
            print("Error: No document loaded.")
            return None
        return self.doc_model.list_all_h2_sections()

    def list_panels_for_cli(self) -> Optional[List[PanelPydantic]]:
        """2. List all Panels"""
        if not self.doc_model:
            print("Error: No document loaded.")
            return None
        return self.doc_model.list_panels()

    def select_panel_by_number_for_cli(self, panel_number: int) -> bool:
        """3. Select Panel by number (stores it in controller)"""
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        panel = self.doc_model.get_panel_by_number(panel_number)
        if panel:
            self.current_selected_panel = panel
            print(
                f"Controller: Selected Panel {panel.panel_number_in_doc}: {panel.panel_title_text}"
            )
            return True
        else:
            print(f"Controller: Panel number {panel_number} not found.")
            self.current_selected_panel = None
            return False

    def list_h3_sections_in_selected_panel_for_cli(
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        """4. Select Panel by number and list the H3 sections under that Panel"""
        if not self.current_selected_panel:
            print("Error: No panel currently selected. Please select a panel first.")
            return None
        return self.doc_model.list_h3_sections_in_panel(self.current_selected_panel)

    def list_and_get_h3_content_for_cli(self, h3_number_in_panel: int) -> Optional[str]:
        """5. Select the Panel by number (It will list the H3 Sections with number)
        then select H3 to pretty print the H3 sections (with H4 if it exists)
        """
        if not self.current_selected_panel:
            print("Error: No panel selected.")
            return None

        h3_options = self.doc_model.list_h3_sections_in_panel(
            self.current_selected_panel
        )
        if not h3_options or not (0 < h3_number_in_panel <= len(h3_options)):
            print(f"Error: Invalid H3 section number {h3_number_in_panel}.")
            return None

        selected_h3_data = h3_options[h3_number_in_panel - 1]  # h3_object is H3Pydantic
        h3_pydantic_object = selected_h3_data.get("h3_object")

        if h3_pydantic_object and isinstance(h3_pydantic_object, H3Pydantic):
            # Get the full markdown for this H3 section, including its H4s
            return self.doc_model.get_h3_subsection_full_markdown(h3_pydantic_object)
        else:
            print(
                f"Error: Could not retrieve H3 object for selection {h3_number_in_panel}."
            )
            return None

    def list_targetable_sections_in_selected_panel_for_cli(
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        """6. Select Panel to Prep for API send (List the sections with number)."""
        if not self.current_selected_panel:
            print("Error: No panel currently selected.")
            return None
        self.last_listed_targetable_sections = (
            self.doc_model.list_targetable_sections_in_panel(
                self.current_selected_panel
            )
        )
        return self.last_listed_targetable_sections

    # --- Content Retrieval and API Preparation ---
    def get_content_for_targetable_section(self, display_number: int) -> Optional[str]:
        """Helper to get content based on display_number from last_listed_targetable_sections"""
        if not self.last_listed_targetable_sections or not (
            0 < display_number <= len(self.last_listed_targetable_sections)
        ):
            print(
                "Error: Invalid selection number or no sections previously listed for targeting."
            )
            return None

        target_info = self.last_listed_targetable_sections[display_number - 1]

        # Use the more generic getter from the model
        return self.doc_model.get_section_markdown_for_api(
            panel_title=target_info["panel_title"],  # panel_title is always present
            h3_title=target_info.get("h3_title"),
            h4_title=target_info.get("h4_title"),
            is_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )

    def prepare_multiple_selected_sections_for_api(
        self, display_numbers: List[int], common_prompt: str = "Analyze:"
    ) -> List[Dict[str, Any]]:
        """Prepares content for API for sections selected by their display_numbers."""
        if not self.doc_model:
            print("Error: No document loaded.")
            return []
        if not self.last_listed_targetable_sections:
            print("Error: No targetable sections have been listed recently.")
            return []

        prepared_data = []
        for num in display_numbers:
            if not (0 < num <= len(self.last_listed_targetable_sections)):
                print(f"Warning: Invalid selection number {num} skipped.")
                continue

            target_info = self.last_listed_targetable_sections[num - 1]
            content_md = self.get_content_for_targetable_section(num)

            if content_md and not content_md.startswith("Error:"):
                prepared_data.append(
                    {
                        "panel_title": target_info["panel_title"],
                        "h3_title": target_info.get("h3_title"),
                        "h4_title": target_info.get("h4_title"),
                        "is_h3_initial_content": target_info.get(
                            "is_initial_content_for_h3", False
                        ),
                        "type": target_info["type"],
                        "title": target_info["title"],
                        "prompt": common_prompt,
                        "content_to_send": content_md,
                    }
                )
            else:
                print(
                    f"Warning: Could not retrieve content for selection {num} ('{target_info['title']}'). Skipping."
                )

        print(f"--- Prepared {len(prepared_data)} section(s) for API calls. ---")
        return prepared_data

    # --- Modification and API Update Methods ---
    def update_target_section_content(
        self, display_number: int, new_markdown_content: str
    ) -> bool:
        """7. Select Panel Number to edit subsection. Which section do you want to Edit or Replace"""
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        if not self.last_listed_targetable_sections or not (
            0 < display_number <= len(self.last_listed_targetable_sections)
        ):
            print(
                "Error: Invalid selection number or no sections previously listed for targeting."
            )
            return False

        target_info = self.last_listed_targetable_sections[display_number - 1]

        return self.doc_model.update_target_content(
            panel_title=target_info["panel_title"],
            new_markdown_content=new_markdown_content,
            h3_title=target_info.get("h3_title"),
            h4_title=target_info.get("h4_title"),
            is_h3_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )

    def add_to_target_section_content(
        self, display_number: int, new_markdown_content: str, position: str = "end"
    ) -> bool:
        """Adds content to a targetable section (H3 Initial or H4 content)."""
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        if not self.last_listed_targetable_sections or not (
            0 < display_number <= len(self.last_listed_targetable_sections)
        ):
            print(
                "Error: Invalid selection number or no sections previously listed for targeting."
            )
            return False

        target_info = self.last_listed_targetable_sections[display_number - 1]

        # The model's add_content_to_target is designed for H3-Initial or H4.
        # Adding to H2 or full H3 would require new model methods or more complex logic here.
        if target_info["type"] not in ["H3 Initial Content", "H4 Sub-sub-section"]:
            print(
                f"Error: Adding content is currently supported for 'H3 Initial Content' or 'H4 Sub-sub-section', not '{target_info['type']}'."
            )
            return False

        return self.doc_model.add_content_to_target(
            panel_title=target_info["panel_title"],
            new_markdown_content=new_markdown_content,
            position=position,
            h3_title=target_info.get(
                "h3_title"
            ),  # Must be present for H3-Initial or H4
            h4_title=target_info.get("h4_title"),  # Present if target is H4
            is_h3_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )

    def process_api_enhancements_for_h3(
        self,
        panel_title: str,
        h3_title: str,
        improved_markdown: str,
        recommendation: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Updates an H3Pydantic object with content received from an API."""
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

    # --- Save ---
    def save_document(self, output_filepath: str) -> bool:
        """Saves the current state of the document model to a new file."""
        if not self.doc_model:
            print("Error: No document loaded to save.")
            return False

        if self.doc_model.save_document(output_filepath):
            print(f"Controller: Document saved successfully to {output_filepath}.")
            return True
        else:
            print(f"Controller: Failed to save document to {output_filepath}.")
            return False

    # --- Deprecated/Old methods for reference or to be removed ---
    # def get_document_structure_view(self) -> str: ...
    # def get_specific_subsection_content_md(self, panel_title_fragment: str, h3_title_fragment: Optional[str] = None, h4_title_fragment: Optional[str] = None) -> str: ...
    # def prepare_sections_for_api_v2(self, sections_to_process: List[tuple[str, Optional[str], Optional[str]]], common_prompt: str = "Analyze:") -> List[Dict[str, Any]]: ...
    # def modify_section_content(self, panel_title_fragment: str, h3_title_fragment: str, new_markdown_content: str, h4_title_fragment: Optional[str] = None) -> bool: ...
    # def add_to_section_content(self, panel_title_fragment: str, h3_title_fragment: str, new_markdown_content: str, position: str = "end", h4_title_fragment: Optional[str] = None) -> bool: ...

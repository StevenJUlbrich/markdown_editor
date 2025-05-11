# app_controller.py
from typing import Any, Dict, List, Optional

# Assuming document_model.py (with Pydantic models and numeric IDs) is in the same directory or PYTHONPATH
from document_model import H3Pydantic, MarkdownDocument, PanelPydantic


class AppController:
    """
    Controller for the Markdown processing application.
    Manages interaction between the view (CLI/GUI) and the model (MarkdownDocument),
    using numeric IDs for section targeting.
    """

    def __init__(self):
        self.doc_model: Optional[MarkdownDocument] = None
        self.current_selected_panel_id: Optional[int] = None
        self.last_listed_targetable_sections: List[Dict[str, Any]] = []

    def load_document(self, filepath: str) -> bool:
        """Loads a Markdown document using the model."""
        self.doc_model = MarkdownDocument()
        self.current_selected_panel_id = None  # Reset selected panel ID
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
        return (
            self.doc_model.list_panels()
        )  # Model returns sorted list of PanelPydantic objects

    def select_panel_by_number_for_cli(self, panel_doc_number: int) -> bool:
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        panel = self.doc_model.get_panel_by_number(panel_doc_number)
        if panel:
            self.current_selected_panel_id = panel.panel_number_in_doc  # Store the ID
            print(
                f"Controller: Selected Panel ID {panel.panel_number_in_doc}: {panel.panel_title_text}"
            )
            return True
        else:
            print(
                f"Controller: Panel with document number {panel_doc_number} not found."
            )
            self.current_selected_panel_id = None
            return False

    def get_current_selected_panel_title(self) -> Optional[str]:
        """Helper to get the title of the currently selected panel for display."""
        if not self.doc_model or self.current_selected_panel_id is None:
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        return panel.panel_title_text if panel else None

    def list_h3_sections_in_selected_panel_for_cli(
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        if not self.doc_model or self.current_selected_panel_id is None:
            print(
                "Error: No panel currently selected. Please select a panel first (Option 4)."
            )
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        if not panel:
            print(
                f"Error: Could not retrieve selected panel (ID: {self.current_selected_panel_id})."
            )
            return None
        # Model's list_h3_sections_in_panel returns {"number": h3.h3_number_in_panel, "title": ..., "h3_object":...}
        return self.doc_model.list_h3_sections_in_panel(panel)

    def list_and_get_h3_content_for_cli(
        self, h3_list_selection_number: int
    ) -> Optional[str]:
        """Gets full content for an H3 based on its selection number from the CLI list."""
        if not self.doc_model or self.current_selected_panel_id is None:
            print("Error: No panel selected.")
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        if not panel:
            return "Error: Selected panel not found."

        h3_options = self.doc_model.list_h3_sections_in_panel(panel)
        if not h3_options or not (0 < h3_list_selection_number <= len(h3_options)):
            print(f"Error: Invalid H3 selection number {h3_list_selection_number}.")
            return None

        # h3_options items have "number" which is h3_number_in_panel and "h3_object"
        selected_h3_data = h3_options[h3_list_selection_number - 1]
        h3_pydantic_object = selected_h3_data.get("h3_object")

        if h3_pydantic_object and isinstance(h3_pydantic_object, H3Pydantic):
            return self.doc_model.get_h3_subsection_full_markdown(h3_pydantic_object)
        else:
            print(
                f"Error: Could not retrieve H3 object for selection {h3_list_selection_number}."
            )
            return None

    def list_targetable_sections_in_selected_panel_for_cli(
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        if not self.doc_model or self.current_selected_panel_id is None:
            print("Error: No panel currently selected.")
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        if not panel:
            print(
                f"Error: Could not retrieve selected panel (ID: {self.current_selected_panel_id})."
            )
            return None

        self.last_listed_targetable_sections = (
            self.doc_model.list_targetable_sections_in_panel(panel)
        )
        return self.last_listed_targetable_sections

    # --- Content Retrieval and API Preparation ---
    def _get_target_info_from_display_number(
        self, display_number: int
    ) -> Optional[Dict[str, Any]]:
        """Helper to retrieve target section details from a display number."""
        if not self.last_listed_targetable_sections or not (
            0 < display_number <= len(self.last_listed_targetable_sections)
        ):
            print(
                "Error: Invalid selection number or no sections previously listed for targeting."
            )
            return None
        return self.last_listed_targetable_sections[display_number - 1]

    def prepare_multiple_selected_sections_for_api(
        self, display_numbers: List[int], common_prompt: str = "Analyze:"
    ) -> List[Dict[str, Any]]:
        if not self.doc_model:
            print("Error: No document loaded.")
            return []
        if self.current_selected_panel_id is None:
            print("Error: No panel selected.")
            return []
        if not self.last_listed_targetable_sections:
            print("Error: Targetable sections not listed for current panel.")
            return []

        prepared_data = []
        for num in display_numbers:
            target_info = self._get_target_info_from_display_number(num)
            if not target_info:
                continue

            content_md = self.doc_model.get_section_markdown_for_api(
                panel_id=target_info["panel_id"],
                h3_id_in_panel=target_info.get("h3_id"),
                h4_id_in_h3=target_info.get("h4_id"),
                is_initial_content_target=target_info.get(
                    "is_initial_content_for_h3", False
                ),
            )

            if content_md and not content_md.startswith("Error:"):
                prepared_data.append(
                    {
                        "panel_id": target_info["panel_id"],
                        "h3_id": target_info.get("h3_id"),
                        "h4_id": target_info.get("h4_id"),
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
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        target_info = self._get_target_info_from_display_number(display_number)
        if not target_info:
            return False

        return self.doc_model.update_target_content(
            panel_id=target_info["panel_id"],
            new_markdown_content=new_markdown_content,
            h3_id_in_panel=target_info.get("h3_id"),
            h4_id_in_h3=target_info.get("h4_id"),
            is_h3_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )

    def add_to_target_section_content(
        self, display_number: int, new_markdown_content: str, position: str = "end"
    ) -> bool:
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        target_info = self._get_target_info_from_display_number(display_number)
        if not target_info:
            return False

        if target_info["type"] not in ["H3 Initial Content", "H4 Sub-sub-section"]:
            print(
                f"Error: Adding content is currently supported for 'H3 Initial Content' or 'H4 Sub-sub-section', not '{target_info['type']}'."
            )
            return False

        return self.doc_model.add_content_to_target(
            panel_id=target_info["panel_id"],
            new_markdown_content=new_markdown_content,
            position=position,
            h3_id_in_panel=target_info.get("h3_id"),
            h4_id_in_h3=target_info.get("h4_id"),
            is_h3_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )

    def process_api_enhancements_for_h3(
        self,
        panel_id: int,
        h3_id_in_panel: int,
        improved_markdown: str,
        recommendation: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        if not self.doc_model:
            print("Error: No document loaded.")
            return False

        success = self.doc_model.update_h3_section_with_improved_markdown(  # Changed from via_api to with_improved_markdown
            panel_id, h3_id_in_panel, improved_markdown
        )
        if success and (
            recommendation or reason
        ):  # Also update suggestions if provided
            self.doc_model.update_h3_section_with_api_suggestions(
                panel_id,
                h3_id_in_panel,
                should_enhance=True,  # Implied if we have improved_markdown
                enhancement_type=recommendation,
                enhancement_reason=reason,
            )

        if success:
            h3_obj = self.doc_model.get_h3_by_number(
                self.doc_model.get_panel_by_number(panel_id), h3_id_in_panel
            )
            h3_title = h3_obj.heading_text if h3_obj else f"ID {h3_id_in_panel}"
            panel_title = self.doc_model.get_panel_by_number(panel_id).panel_title_text
            print(
                f"Controller: API enhancement for H3 '{h3_title}' in Panel '{panel_title}' recorded."
            )
        else:
            print(
                f"Controller: Failed to record API enhancement for H3 ID {h3_id_in_panel}."
            )
        return success

    # --- Save ---
    def save_document(self, output_filepath: str) -> bool:
        if not self.doc_model:
            print("Error: No document loaded to save.")
            return False
        return self.doc_model.save_document(output_filepath)

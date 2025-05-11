# app_controller.py
from typing import Any, Dict, List, Optional

from diff_utils import generate_text_diff
from document_model import H3Pydantic  # Assuming numeric IDs
from document_model import MarkdownDocument, PanelPydantic

# Pydantic v2 provides model_dump_json, v1 uses .json()
# We'll try to use model_dump_json and fallback or adjust if needed based on Pydantic version.
# For simplicity in this example, we'll assume Pydantic v2+ .model_dump_json() is available.


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

    # ... (all previous methods from the diff tool implementation remain here) ...
    def load_document(self, filepath: str) -> bool:
        self.doc_model = MarkdownDocument()
        self.current_selected_panel_id = None
        self.last_listed_targetable_sections = []
        if self.doc_model.load_and_process(filepath):
            print("Controller: Document loaded and processed successfully.")
            return True
        else:
            print("Controller: Failed to load or process document.")
            self.doc_model = None
            return False

    def list_all_h2_sections_for_cli(self) -> Optional[List[Dict[str, Any]]]:
        if not self.doc_model:
            print("Error: No document loaded.")
            return None
        return self.doc_model.list_all_h2_sections()

    def list_panels_for_cli(self) -> Optional[List[PanelPydantic]]:
        if not self.doc_model:
            print("Error: No document loaded.")
            return None
        return self.doc_model.list_panels()

    def select_panel_by_number_for_cli(self, panel_doc_number: int) -> bool:
        if not self.doc_model:
            print("Error: No document loaded.")
            return False
        panel = self.doc_model.get_panel_by_number(panel_doc_number)
        if panel:
            self.current_selected_panel_id = panel.panel_number_in_doc
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
        return self.doc_model.list_h3_sections_in_panel(panel)

    def list_and_get_h3_content_for_cli(
        self, h3_list_selection_number: int
    ) -> Optional[str]:
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

    def _get_target_info_from_display_number(
        self, display_number: int
    ) -> Optional[Dict[str, Any]]:
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

    def get_h3_section_diff_text(
        self, panel_id: int, h3_id_in_panel: int
    ) -> Optional[str]:
        """
        Retrieves the original and API-improved markdown for an H3 section
        and returns a text-based diff.
        """
        if not self.doc_model:
            print("Error: No document loaded.")
            return None

        panel = self.doc_model.get_panel_by_number(panel_id)
        if not panel:
            return f"Error: Panel ID {panel_id} not found."

        h3_section = self.doc_model.get_h3_by_number(panel, h3_id_in_panel)
        if not h3_section:
            return f"Error: H3 ID {h3_id_in_panel} not found in Panel ID {panel_id}."

        if h3_section.api_improved_markdown is None:
            return f"H3 section '{h3_section.heading_text}' (ID: {h3_id_in_panel}) has no API-improved content to compare."

        if h3_section.original_full_markdown is None:
            return f"H3 section '{h3_section.heading_text}' (ID: {h3_id_in_panel}) is missing original_full_markdown."

        return generate_text_diff(
            h3_section.original_full_markdown, h3_section.api_improved_markdown
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

        success = self.doc_model.update_h3_section_with_improved_markdown(
            panel_id, h3_id_in_panel, improved_markdown
        )
        if success and (recommendation or reason):
            self.doc_model.update_h3_section_with_api_suggestions(
                panel_id,
                h3_id_in_panel,
                should_enhance=True,
                enhancement_type=recommendation,
                enhancement_reason=reason,
            )

        if success:
            h3_obj = self.doc_model.get_h3_by_number(
                self.doc_model.get_panel_by_number(panel_id), h3_id_in_panel
            )
            h3_title = h3_obj.heading_text if h3_obj else f"ID {h3_id_in_panel}"
            panel_obj = self.doc_model.get_panel_by_number(panel_id)
            panel_title = panel_obj.panel_title_text if panel_obj else f"ID {panel_id}"
            print(
                f"Controller: API enhancement for H3 '{h3_title}' in Panel '{panel_title}' recorded."
            )
        else:
            print(
                f"Controller: Failed to record API enhancement for H3 ID {h3_id_in_panel}."
            )
        return success

    def get_chapter_model_as_json(self) -> Optional[str]:
        """
        Exports the current self.doc_model.chapter_model to a JSON string,
        excluding Mistletoe block objects for readability.
        """
        if not self.doc_model or not self.doc_model.chapter_model:
            print("Error: No document loaded or chapter model not built.")
            return None

        try:
            # Define fields to exclude. This can get complex for nested models.
            # We want to exclude any field that stores raw Mistletoe token objects.
            exclude_mistletoe_fields = {
                "mistletoe_h1_block": True,
                "mistletoe_blocks": True,  # from GenericContentPydantic
                "mistletoe_h2_block": True,  # from PanelPydantic
                "mistletoe_h3_block": True,  # from H3Pydantic
                "mistletoe_h4_block": True,  # from H4Pydantic
            }

            # For Pydantic v2 (model_dump_json)
            # The exclude structure for nested models:
            # 'parent_list': {'__all__': {'field_in_list_item_to_exclude': True}}
            # or 'parent_list': {int_index: {'field_to_exclude': True}}

            # We need to construct the exclude dict carefully for nested models
            # Pydantic v2's model_dump(exclude=...) is more flexible before dumping to json

            # Simplified exclusion for this example, focusing on top-level and known nested fields
            # A more robust way might involve a custom encoder or iterating the model dict

            # Using model_dump to create a dict first, then remove unwanted keys before json.dumps
            # This gives more control for complex nested exclusions if Pydantic's direct exclude is tricky.

            # For Pydantic v2 .model_dump_json(exclude=...)
            # This is a common pattern but might need adjustment based on exact model structure and Pydantic version specifics
            # for excluding fields from items within lists of models.
            # A simpler way for Pydantic v2 is to get the dict first, then filter.
            chapter_dict = self.doc_model.chapter_model.model_dump(exclude_none=True)

            # Recursively remove mistletoe blocks for cleaner JSON
            def clean_dict(d):
                if isinstance(d, dict):
                    return {
                        k: clean_dict(v)
                        for k, v in d.items()
                        if not k.startswith("mistletoe_")  # General rule
                    }
                elif isinstance(d, list):
                    return [clean_dict(i) for i in d]
                return d

            cleaned_chapter_dict = clean_dict(chapter_dict)

            import json

            return json.dumps(cleaned_chapter_dict, indent=2)

        except AttributeError as e:
            # Fallback for Pydantic v1 style or other issues
            print(
                f"Note: Using basic Pydantic .json() export due to AttributeError ({e}). Mistletoe objects might be included or cause errors."
            )
            try:
                # Pydantic v1 .json() does not have such granular exclude for nested __all__
                # This will likely include Mistletoe objects or fail if they are not serializable.
                # A custom encoder with .json(encoder=custom_encoder) would be needed for Pydantic v1.
                return self.doc_model.chapter_model.json(indent=2)
            except Exception as json_err:
                print(f"Error during JSON export: {json_err}")
                return f'{{"error": "Could not serialize chapter model to JSON: {json_err}"}}'
        except Exception as e:
            print(f"Error during JSON export: {e}")
            return f'{{"error": "Could not serialize chapter model to JSON: {e}"}}'

    def save_document(self, output_filepath: str) -> bool:
        if not self.doc_model:
            print("Error: No document loaded to save.")
            return False
        return self.doc_model.save_document(output_filepath)

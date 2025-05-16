# app_controller.py
from typing import Any, Dict, List, Optional

import openai_service  # For OpenAI interactions
from diff_utils import generate_text_diff
from document_model import H3Pydantic, PanelPydantic
from logging_config import setup_logging

# Assuming document_model.py, openai_service.py, diff_utils.py are in the same directory or PYTHONPATH
from MarkdownDocument import MarkdownDocument

setup_logging()


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
        self.doc_model = MarkdownDocument()
        self.current_selected_panel_id = None
        self.last_listed_targetable_sections = []
        if self.doc_model.load_and_process(filepath):
            # Message is now in model's load_and_process
            return True
        else:
            # Message is now in model's load_and_process
            self.doc_model = None
            return False

    # --- Listing Methods for CLI ---
    def list_all_h2_sections_for_cli(self) -> Optional[List[Dict[str, Any]]]:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return None
        return self.doc_model.list_all_h2_sections()

    def list_panels_for_cli(self) -> Optional[List[PanelPydantic]]:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return None
        return self.doc_model.list_panels()

    def select_panel_by_number_for_cli(self, panel_doc_number: int) -> bool:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return False
        panel = self.doc_model.get_panel_by_number(panel_doc_number)
        if panel and panel.panel_number_in_doc is not None:
            self.current_selected_panel_id = panel.panel_number_in_doc
            print(
                f"INFO: Controller: Selected Panel ID {panel.panel_number_in_doc} ('{panel.panel_title_text}')"
            )
            return True
        else:
            print(
                f"ERROR: Controller: Panel with document number {panel_doc_number} not found or missing ID."
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
            print("ERROR: No panel currently selected. Please select a panel first.")
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        if not panel:
            print(
                f"ERROR: Could not retrieve selected panel (ID: {self.current_selected_panel_id})."
            )
            return None
        return self.doc_model.list_h3_sections_in_panel(panel)

    def list_and_get_h3_content_for_cli(
        self, h3_list_selection_number: int
    ) -> Optional[str]:
        if not self.doc_model or self.current_selected_panel_id is None:
            print("ERROR: No panel selected.")
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        if not panel:
            print(
                f"ERROR: Selected panel (ID: {self.current_selected_panel_id}) not found."
            )
            return "Error: Selected panel not found."  # Return error string

        h3_options = self.doc_model.list_h3_sections_in_panel(panel)
        if not h3_options or not (0 < h3_list_selection_number <= len(h3_options)):
            print(
                f"ERROR: Invalid H3 selection number {h3_list_selection_number} from list."
            )
            return None

        actual_h3_id_in_panel = h3_options[h3_list_selection_number - 1].get("number")
        if actual_h3_id_in_panel is None:
            print(
                f"ERROR: H3 list item {h3_list_selection_number} is missing its ID ('number' field)."
            )
            return None

        h3_pydantic_object = self.doc_model.get_h3_by_number(
            panel, actual_h3_id_in_panel
        )

        if h3_pydantic_object:
            return self.doc_model.get_h3_subsection_full_markdown(h3_pydantic_object)
        else:
            print(
                f"ERROR: Could not retrieve H3 object for ID {actual_h3_id_in_panel} from list selection {h3_list_selection_number}."
            )
            return None

    def list_targetable_sections_in_selected_panel_for_cli(
        self,
    ) -> Optional[List[Dict[str, Any]]]:
        if not self.doc_model or self.current_selected_panel_id is None:
            print("ERROR: No panel currently selected.")
            return None
        panel = self.doc_model.get_panel_by_number(self.current_selected_panel_id)
        if not panel:
            print(
                f"ERROR: Could not retrieve selected panel (ID: {self.current_selected_panel_id})."
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
                "ERROR: Invalid selection number or no sections previously listed for targeting."
            )
            return None
        return self.last_listed_targetable_sections[display_number - 1]

    def prepare_multiple_selected_sections_for_api(
        self, display_numbers: List[int], common_prompt: str = "Analyze:"
    ) -> List[Dict[str, Any]]:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return []
        if self.current_selected_panel_id is None:
            print("ERROR: No panel selected.")
            return []
        # list_targetable_sections_in_selected_panel_for_cli should be called first by CLI to populate this
        if not self.last_listed_targetable_sections:
            print(
                "ERROR: Targetable sections not listed for current panel. Please list them first."
            )
            return []

        prepared_data = []
        for num in display_numbers:
            target_info = self._get_target_info_from_display_number(num)
            if not target_info:
                continue  # Error already printed by helper

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
                    f"WARNING: Could not retrieve content for selection {num} ('{target_info['title']}'). Skipping. Reason: {content_md}"
                )

        print(f"INFO: --- Prepared {len(prepared_data)} section(s) for API calls. ---")
        return prepared_data

    def update_target_section_content(
        self, display_number: int, new_markdown_content: str
    ) -> bool:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return False
        target_info = self._get_target_info_from_display_number(display_number)
        if not target_info:
            return False

        success = self.doc_model.update_target_content(
            panel_id=target_info["panel_id"],
            new_markdown_content=new_markdown_content,
            h3_id_in_panel=target_info.get("h3_id"),
            h4_id_in_h3=target_info.get("h4_id"),
            is_h3_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )
        if success:
            print(
                f"INFO: Content for '{target_info['title']}' (Type: {target_info['type']}) updated in model."
            )
        else:
            print(f"ERROR: Failed to update content for '{target_info['title']}'.")
        return success

    def add_to_target_section_content(
        self, display_number: int, new_markdown_content: str, position: str = "end"
    ) -> bool:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return False
        target_info = self._get_target_info_from_display_number(display_number)
        if not target_info:
            return False

        if target_info["type"] not in ["H3 Initial Content", "H4 Sub-sub-section"]:
            print(
                f"ERROR: Adding content is currently supported for 'H3 Initial Content' or 'H4 Sub-sub-section', not '{target_info['type']}'."
            )
            return False

        success = self.doc_model.add_content_to_target(
            panel_id=target_info["panel_id"],
            new_markdown_content=new_markdown_content,
            position=position,
            h3_id_in_panel=target_info.get("h3_id"),
            h4_id_in_h3=target_info.get("h4_id"),
            is_h3_initial_content_target=target_info.get(
                "is_initial_content_for_h3", False
            ),
        )
        if success:
            print(
                f"INFO: Content added to '{target_info['title']}' (Type: {target_info['type']}, Position: {position}) in model."
            )
        else:
            print(f"ERROR: Failed to add content for '{target_info['title']}'.")
        return success

    def get_h3_section_diff_text(
        self, panel_id: int, h3_id_in_panel: int
    ) -> Optional[str]:
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return None

        panel = self.doc_model.get_panel_by_number(panel_id)
        if not panel:
            return f"ERROR: Panel ID {panel_id} not found."

        h3_section = self.doc_model.get_h3_by_number(panel, h3_id_in_panel)
        if not h3_section:
            return f"ERROR: H3 ID {h3_id_in_panel} not found in Panel ID {panel_id}."

        if h3_section.api_improved_markdown is None:
            return f"INFO: H3 section '{h3_section.heading_text}' (ID: {h3_id_in_panel}) has no API-improved content to compare."

        if h3_section.original_full_markdown is None:
            return f"ERROR: H3 section '{h3_section.heading_text}' (ID: {h3_id_in_panel}) is missing original_full_markdown."

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
            print("ERROR: No document loaded.")
            return False

        # First, update the H3 section with the improved markdown content
        success_update_md = self.doc_model.update_h3_section_with_improved_markdown(
            panel_id, h3_id_in_panel, improved_markdown
        )
        if not success_update_md:
            print(
                f"ERROR: Controller: Failed to store improved markdown for H3 ID {h3_id_in_panel}."
            )
            return False  # Stop if markdown update failed

        # Then, if recommendation or reason are provided, update the suggestion fields
        if recommendation or reason:
            success_update_suggestions = (
                self.doc_model.update_h3_section_with_api_suggestions(
                    panel_id,
                    h3_id_in_panel,
                    should_enhance=True,  # Implied, as we have improved_markdown
                    enhancement_type=recommendation,
                    enhancement_reason=reason,
                )
            )
            if not success_update_suggestions:
                print(
                    f"WARNING: Controller: Stored improved markdown for H3 ID {h3_id_in_panel}, but failed to store suggestion details."
                )
                # Continue, as the main content was updated.

        # Retrieve panel and H3 objects for logging purposes
        panel_obj = self.doc_model.get_panel_by_number(panel_id)
        h3_obj = (
            self.doc_model.get_h3_by_number(panel_obj, h3_id_in_panel)
            if panel_obj
            else None
        )

        h3_title = h3_obj.heading_text if h3_obj else f"ID {h3_id_in_panel}"
        panel_title = panel_obj.panel_title_text if panel_obj else f"ID {panel_id}"
        print(
            f"INFO: Controller: API enhancement for H3 '{h3_title}' in Panel '{panel_title}' recorded in model."
        )
        return True

    # --- New Method for Targeted Enhancement Pipeline ---
    def enhance_structured_panel_sections(self, panel_id: int) -> bool:
        """
        Orchestrates the enhancement of predefined named H3 sections within a specific panel.
        """
        if not self.doc_model:
            print("ERROR: No document loaded.")
            return False

        panel_obj = self.doc_model.get_panel_by_number(panel_id)
        if not panel_obj:
            print(f"ERROR: Panel ID {panel_id} not found for targeted enhancement.")
            return False

        print(
            f"\nINFO: Starting targeted enhancement for Panel ID {panel_id} ('{panel_obj.panel_title_text}')."
        )

        section_map = self.doc_model.extract_named_sections_from_panel(panel_id)

        if not section_map or not any(section_map.values()):
            print(
                f"INFO: No predefined named sections with content found in Panel ID {panel_id}. Nothing to enhance."
            )
            return True

        panel_context_for_suggestions = f"## {panel_obj.panel_title_text}\n"
        # Use .get() for safety, and check if the content is non-empty before adding
        scene_desc_content = section_map.get("Scene Description", "")
        if scene_desc_content.strip():
            panel_context_for_suggestions += scene_desc_content + "\n\n"

        teaching_narr_content = section_map.get("Teaching Narrative", "")
        if teaching_narr_content.strip():
            panel_context_for_suggestions += teaching_narr_content + "\n\n"

        sections_to_suggest_for: Dict[str, str] = {
            title: md_content
            for title, md_content in section_map.items()
            if md_content and md_content.strip()
        }

        if not sections_to_suggest_for:
            print(
                f"INFO: All predefined named sections in Panel ID {panel_id} are effectively empty. Nothing to send for suggestions."
            )
            return True

        print(
            f"INFO: Getting enhancement suggestions for {len(sections_to_suggest_for)} named sections in Panel ID {panel_id}..."
        )

        suggestions_from_api = openai_service.get_enhancement_suggestions_for_panel_h3s(
            panel_title=panel_obj.panel_title_text,
            panel_context_markdown=panel_context_for_suggestions.strip(),
            h3_sections_content=sections_to_suggest_for,
        )

        if not suggestions_from_api:
            print(f"WARNING: No suggestions received from API for Panel ID {panel_id}.")
            return True

        enhancements_made_count = 0
        for section_h3_title, suggestion_details in suggestions_from_api.items():
            if section_h3_title not in sections_to_suggest_for:
                print(
                    f"WARNING: Suggestion received for unknown or filtered section '{section_h3_title}'. Skipping."
                )
                continue

            original_section_content = sections_to_suggest_for[section_h3_title]
            target_h3_obj_for_update: Optional[H3Pydantic] = None
            for h3_iter in panel_obj.h3_sections:
                if h3_iter.heading_text.strip() == section_h3_title:
                    target_h3_obj_for_update = h3_iter
                    break

            if not target_h3_obj_for_update:
                print(
                    f"WARNING: Could not find matching H3Pydantic object for '{section_h3_title}' to store suggestions/updates."
                )
                continue

            # Store suggestion details in the H3Pydantic object
            self.doc_model.update_h3_section_with_api_suggestions(
                panel_id=panel_id,
                h3_id_in_panel=target_h3_obj_for_update.h3_number_in_panel,
                should_enhance=suggestion_details.get("enhance"),  # This is a boolean
                enhancement_type=suggestion_details.get("recommendation"),
                enhancement_reason=suggestion_details.get("reason"),
            )

            if suggestion_details.get("enhance"):
                recommendation = suggestion_details.get("recommendation")
                reason = suggestion_details.get("reason")

                print(
                    f"\nINFO: Enhancing named section '{section_h3_title}' in Panel ID {panel_id} (Suggestion: {recommendation or 'N/A'})"
                )

                improved_content_md = openai_service.get_improved_markdown_for_section(
                    original_h3_markdown_content=original_section_content,
                    enhancement_type=recommendation,
                    enhancement_reason=reason,
                    panel_title_context=panel_obj.panel_title_text,
                    overall_panel_context_md=panel_context_for_suggestions.strip(),
                )

                if improved_content_md is not None:
                    # Use the model's method that updates api_improved_markdown by H3 title
                    if self.doc_model.update_named_section_in_panel(
                        panel_id, section_h3_title, improved_content_md
                    ):
                        print(
                            f"INFO: Successfully stored enhanced content for '{section_h3_title}' in Panel ID {panel_id}."
                        )
                        enhancements_made_count += 1
                    else:
                        print(
                            f"ERROR: Failed to store enhanced content for '{section_h3_title}' in Panel ID {panel_id}."
                        )
                else:
                    print(
                        f"INFO: No improvement generated by API for '{section_h3_title}'. Original content preserved for this section."
                    )
            else:
                print(
                    f"INFO: Skipping enhancement for named section '{section_h3_title}' – no enhancement suggested by API."
                )

        if enhancements_made_count > 0:
            print(
                f"INFO: Targeted enhancement process completed for Panel ID {panel_id}. {enhancements_made_count} section(s) were updated with API improvements."
            )
        else:
            print(
                f"INFO: Targeted enhancement process completed for Panel ID {panel_id}. No sections were enhanced based on API suggestions."
            )
        return True

    def get_chapter_model_as_json(self) -> Optional[str]:
        if not self.doc_model or not self.doc_model.chapter_model:
            print("ERROR: No document loaded or chapter model not built.")
            return None
        try:
            # Pydantic v2+ .model_dump() is preferred
            chapter_dict = self.doc_model.chapter_model.model_dump(exclude_none=True)

            def clean_dict_for_json(d_item: Any) -> Any:
                if isinstance(d_item, dict):
                    return {
                        k: clean_dict_for_json(v)
                        for k, v in d_item.items()
                        if not k.startswith("mistletoe_")  # Exclude Mistletoe objects
                    }
                elif isinstance(d_item, list):
                    return [clean_dict_for_json(i) for i in d_item]
                return d_item  # Primitives, Pydantic models (if not excluded by key)

            cleaned_chapter_dict = clean_dict_for_json(chapter_dict)

            import json  # Standard library

            return json.dumps(cleaned_chapter_dict, indent=2, ensure_ascii=False)

        except AttributeError:
            print(
                f"WARNING: Using basic Pydantic .json() export (likely Pydantic v1). Mistletoe objects might be included or cause errors."
            )
            try:
                return self.doc_model.chapter_model.json(indent=2)  # Pydantic v1
            except Exception as json_err:
                print(f"ERROR: Error during Pydantic v1 JSON export: {json_err}")
                return f'{{"error": "Could not serialize chapter model to JSON (v1 attempt): {json_err}"}}'
        except Exception as e:
            print(f"ERROR: Unexpected error during JSON export: {e}")
            return f'{{"error": "Could not serialize chapter model to JSON: {e}"}}'

    def save_document(self, output_filepath: str) -> bool:
        if not self.doc_model:
            print("ERROR: No document loaded to save.")
            return False
        return self.doc_model.save_document(output_filepath)

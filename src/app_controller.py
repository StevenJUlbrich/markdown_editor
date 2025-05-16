# app_controller.py (refactored)

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from character_role_suggester import CharacterRoleSuggester
from markdown_document import MarkdownDocument

logger = logging.getLogger(__name__)


class AppController:
    """
    Controller for orchestrating high-level document workflows.
    Interacts with the view/CLI and delegates all business logic to MarkdownDocument.
    """

    def __init__(self):
        self.doc: Optional[MarkdownDocument] = None
        self.current_selected_panel_id: Optional[int] = None
        self.last_listed_targetable_sections: List[Dict[str, Any]] = []

    def load_document(self, filepath: str) -> bool:
        self.doc = MarkdownDocument()
        self.current_selected_panel_id = None
        self.last_listed_targetable_sections = []
        result = self.doc.load_and_process(filepath)
        logger.info(f"Document load result for '{filepath}': {result}")
        return result

    def save_document(self, filepath: str) -> bool:
        if not self.doc:
            logger.error("No document loaded for saving.")
            return False
        return self.doc.save_document(filepath)

    def list_panels(self) -> List[Dict[str, Any]]:
        if not self.doc:
            logger.warning("No document loaded for listing panels.")
            return []
        return [
            {
                "panel_number_in_doc": p.panel_number_in_doc,
                "panel_title_text": p.panel_title_text,
            }
            for p in self.doc.list_panels()
        ]

    def select_panel(self, panel_number: int) -> bool:
        if not self.doc:
            logger.warning("No document loaded for selecting panel.")
            return False
        panel = self.doc.get_panel_by_number(panel_number)
        if panel:
            self.current_selected_panel_id = panel.panel_number_in_doc
            logger.info(f"Panel {panel.panel_number_in_doc} selected.")
            return True
        logger.warning(f"Panel {panel_number} not found.")
        self.current_selected_panel_id = None
        return False

    def extract_named_sections(self) -> Dict[str, str]:
        if not self.doc or self.current_selected_panel_id is None:
            logger.warning("No panel selected for extracting sections.")
            return {}
        return self.doc.extract_named_sections_from_panel(
            self.current_selected_panel_id
        )

    def update_named_section(self, section_h3_title: str, new_content: str) -> bool:
        if not self.doc or self.current_selected_panel_id is None:
            logger.warning("No panel selected for updating section.")
            return False
        return self.doc.update_named_section_in_panel(
            self.current_selected_panel_id, section_h3_title, new_content
        )

    def suggest_character_roles_in_folder(self, folder_path: str):
        return CharacterRoleSuggester.suggest_roles_for_folder(folder_path)

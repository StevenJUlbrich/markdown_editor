# app_controller.py

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from batch_processing.comic_panel_batch_processor import process_panel
from models.comic_panel_image_sheet import ComicPanelImageSheet
from parsing.comic_panel_mapping import map_to_comic_panel_image_sheet
from parsing.markdown_document import MarkdownDocument
from services.character_role_suggester import CharacterRoleSuggester

logger = logging.getLogger(__name__)


class AppController:
    """
    Controller for orchestrating high-level document workflows.
    Interacts with the view/CLI and delegates all business logic to MarkdownDocument,
    and now supports LLM-based enrichment and ComicPanelImageSheet export.
    """

    def __init__(self):
        self.doc: Optional[MarkdownDocument] = None
        self.current_selected_panel_id: Optional[int] = None
        self.last_listed_targetable_sections: List[Dict[str, Any]] = []
        self.current_enriched_panel: Optional[ComicPanelImageSheet] = None
        self.llm_prompts: Optional[dict] = None
        self.character_base: Optional[dict] = None

    def load_llm_prompts(self, prompts_path: str):
        with open(prompts_path, "r", encoding="utf-8") as f:
            self.llm_prompts = yaml.safe_load(f)

    def load_character_base(self, character_json_path: str):
        with open(character_json_path, "r", encoding="utf-8") as f:
            self.character_base = json.load(f)["characters"]

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

    # ---------- NEW METHODS FOR ENRICHMENT & EXPORT ----------

    def get_comic_panel_image_sheet(
        self, panel_number: int
    ) -> Optional[ComicPanelImageSheet]:
        """Map the selected panel to a ComicPanelImageSheet object (original content)."""
        if not self.doc:
            logger.warning("No document loaded for image sheet extraction.")
            return None
        panel_md = self.doc.get_panel_markdown_by_number(panel_number)
        if not panel_md:
            logger.warning(f"Panel {panel_number} markdown not found.")
            return None
        return map_to_comic_panel_image_sheet(
            panel_md,
            chapter_id=getattr(self.doc, "chapter_id", None),
            panel_index=panel_number,
        )

    def enrich_panel_with_llm(
        self, panel_number: int
    ) -> Optional[ComicPanelImageSheet]:
        """Run LLM processing on the selected panel and return enriched ComicPanelImageSheet."""
        sheet = self.get_comic_panel_image_sheet(panel_number)
        if not sheet:
            logger.warning("ComicPanelImageSheet not available for enrichment.")
            return None
        enriched = process_panel(sheet)  # Calls your LLM orchestrator
        self.current_enriched_panel = enriched
        return enriched

    def enrich_all_panels(self) -> List[ComicPanelImageSheet]:
        """Process all panels in the loaded document via LLM."""
        if not self.doc:
            logger.warning("No document loaded for batch enrichment.")
            return []
        enriched_list = []
        for p in self.list_panels():
            num = p["panel_number_in_doc"]
            enriched = self.enrich_panel_with_llm(num)
            if enriched:
                enriched_list.append(enriched)
        return enriched_list

    def save_enriched_panels(
        self, output_path: str, enriched_panels: List[ComicPanelImageSheet]
    ):
        """Save enriched panel JSON (list) to disk. (Pydantic v2: uses model_dump())"""
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in enriched_panels], f, indent=2)
        logger.info(f"Enriched panel data saved to {output_path}")

    def get_enriched_panel_json(self, panel_number: int) -> Optional[dict]:
        """Return the enriched JSON for the selected panel (for GUI preview or API)."""
        enriched = self.enrich_panel_with_llm(panel_number)
        return enriched.model_dump() if enriched else None

    def list_all_sections(self) -> List[Dict[str, Any]]:
        """
        Lists all sections in the document, including both generic content and panels.

        Returns:
            List of dictionaries with section information.
        """
        if not self.doc or not self.doc.chapter_model:
            logger.warning("No document loaded for listing sections.")
            return []

        sections = []
        idx = 0

        for element in self.doc.chapter_model.document_elements:
            if hasattr(element, "panel_title_text"):  # PanelPydantic
                sections.append(
                    {
                        "index": idx,
                        "type": "Panel",
                        "title": element.panel_title_text,
                        "version": getattr(element, "version", 1),
                        "line": getattr(element, "heading_line_number", None),
                        "source": getattr(element, "source_filename", None),
                    }
                )
            elif (
                hasattr(element, "title_text") and element.title_text
            ):  # GenericContentPydantic with title
                sections.append(
                    {
                        "index": idx,
                        "type": "Section",
                        "title": element.title_text,
                        "version": getattr(element, "version", 1),
                        "line": getattr(element, "heading_line_number", None),
                        "source": getattr(element, "source_filename", None),
                    }
                )
            else:  # GenericContentPydantic without title or other element
                title = "Untitled Section"
                # Try to extract a title from the first few words
                if hasattr(element, "content_markdown") and element.content_markdown:
                    first_line = element.content_markdown.strip().split("\n")[0]
                    if len(first_line) > 30:
                        title = f"{first_line[:30]}..."
                    else:
                        title = first_line

                sections.append(
                    {
                        "index": idx,
                        "type": "Content",
                        "title": title,
                        "version": getattr(element, "version", 1),
                        "line": getattr(element, "heading_line_number", None),
                        "source": getattr(element, "source_filename", None),
                    }
                )
            idx += 1

        return sections

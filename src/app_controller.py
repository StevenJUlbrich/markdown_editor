import json
import logging
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

    # ... (all other methods unchanged) ...

    def enrich_panel_with_llm(
        self, panel_number: int
    ) -> Optional[ComicPanelImageSheet]:
        sheet = self.get_comic_panel_image_sheet(panel_number)
        if not sheet or not self.llm_prompts or not self.character_base:
            logger.warning("Missing ComicPanelImageSheet or LLM config for enrichment.")
            return None
        enriched = process_panel(sheet, self.llm_prompts, self.character_base)
        self.current_enriched_panel = enriched
        return enriched

    def enrich_all_panels(self) -> List[ComicPanelImageSheet]:
        if not self.doc or not self.llm_prompts or not self.character_base:
            logger.warning("Document or LLM config not loaded for batch enrichment.")
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
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in enriched_panels], f, indent=2)
        logger.info(f"Enriched panel data saved to {output_path}")

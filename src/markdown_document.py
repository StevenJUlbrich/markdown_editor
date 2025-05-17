# markdown_document.py

import logging
from typing import Optional

from mistletoe import Document

from document_model import (
    _MODULE_LEVEL_RENDERER_INSTANCE,
    ChapterPydantic,
    PanelPydantic,
    render_blocks_to_markdown,
)
from document_model_builder import DocumentModelBuilder
from document_validator import DocumentValidator
from markdown_file_manager import MarkdownFileManager
from markdown_parser import MarkdownParser
from panel_section_manager import PanelSectionManager

logger = logging.getLogger(__name__)


class MarkdownDocument:
    """
    Facade class: Orchestrates file I/O, parsing, model-building, and section updates.
    Keeps state: current filename, loaded text, parsed AST, and model tree.
    """

    def __init__(self):
        self.filepath: Optional[str] = None
        self.raw_content: Optional[str] = None
        self.mistletoe_doc: Optional[Document] = None
        self.chapter_model: Optional[ChapterPydantic] = None

    def load_and_process(self, filepath: str) -> bool:
        self.filepath = filepath
        try:
            self.raw_content = MarkdownFileManager.read_file(filepath)
            self.mistletoe_doc = MarkdownParser.parse(self.raw_content)
            self.chapter_model = DocumentModelBuilder().build(self.mistletoe_doc)
            valid = DocumentValidator.validate(self.chapter_model)
            if not valid:
                logger.warning(f"Model validation failed for file {filepath}.")
            return True
        except Exception as e:
            logger.error(f"Failed to load/process '{filepath}': {e}")
            self.raw_content = None
            self.mistletoe_doc = None
            self.chapter_model = None
            return False

    def save_document(self, output_filepath: str) -> bool:
        try:
            rendered_content = self.reconstruct_and_render_document()
            MarkdownFileManager.write_file(output_filepath, rendered_content)
            logger.info(f"Document successfully saved to '{output_filepath}'.")
            return True
        except Exception as e:
            logger.error(f"Error saving document to '{output_filepath}': {e}")
            return False

    def reconstruct_and_render_document(self) -> str:
        if not self.chapter_model:
            return self.raw_content or ""
        all_blocks = []
        if self.chapter_model.mistletoe_h1_block:
            all_blocks.append(self.chapter_model.mistletoe_h1_block)
        for element in self.chapter_model.document_elements:
            if hasattr(element, "mistletoe_blocks") and element.mistletoe_blocks:
                all_blocks.extend(element.mistletoe_blocks)
            elif isinstance(element, PanelPydantic):
                if element.mistletoe_h2_block:
                    all_blocks.append(element.mistletoe_h2_block)
                for h3_section in element.h3_sections:
                    content_string_for_h3 = None
                    if (
                        hasattr(h3_section, "api_improved_markdown")
                        and h3_section.api_improved_markdown is not None
                    ):
                        content_string_for_h3 = h3_section.api_improved_markdown
                    elif h3_section.original_full_markdown:
                        content_string_for_h3 = h3_section.original_full_markdown
                    if content_string_for_h3:
                        h3_doc = Document(content_string_for_h3)
                        all_blocks.extend(b for b in h3_doc.children if b is not None)
        return render_blocks_to_markdown(all_blocks, _MODULE_LEVEL_RENDERER_INSTANCE)

    # Section-level helpers (delegating to PanelSectionManager)
    def extract_named_sections_from_panel(self, panel_id: int) -> dict:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            logger.error(f"Panel ID {panel_id} not found for extract_named_sections.")
            return {}
        return PanelSectionManager.extract_named_sections(panel)

    def update_named_section_in_panel(
        self, panel_id: int, section_h3_title: str, new_markdown_content: str
    ) -> bool:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            logger.error(f"Panel ID {panel_id} not found for update_named_section.")
            return False
        return PanelSectionManager.update_named_section(
            panel, section_h3_title, new_markdown_content
        )

    # Navigation helpers
    def list_panels(self):
        if not self.chapter_model:
            return []
        return [
            el
            for el in self.chapter_model.document_elements
            if isinstance(el, PanelPydantic)
        ]

    def get_panel_by_number(self, panel_doc_number: int) -> Optional[PanelPydantic]:
        if not self.chapter_model:
            return None
        for element in self.chapter_model.document_elements:
            if (
                isinstance(element, PanelPydantic)
                and element.panel_number_in_doc == panel_doc_number
            ):
                return element
        return None

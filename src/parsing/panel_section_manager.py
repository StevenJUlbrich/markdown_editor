# panel_section_manager.py

import logging
from typing import Dict, Optional

from models.document_model import H3Pydantic, PanelPydantic
from models.section_titles import (
    SECTION_TITLES,
)  # Assuming this is a module with section titles

logger = logging.getLogger(__name__)


class PanelSectionManager:
    """
    Helper/service for extracting and updating named sections within a panel.
    Does not directly parse markdown or handle files.
    """

    KNOWN_SECTION_TITLES = [s.value for s in SECTION_TITLES]

    @staticmethod
    def extract_named_sections(panel: PanelPydantic) -> Dict[str, str]:
        """
        Returns a dict mapping known H3 section names to their markdown content (original).
        """
        if not panel:
            logger.error("Panel is None for extract_named_sections.")
            return {}
        extracted_sections = {
            title: "" for title in PanelSectionManager.KNOWN_SECTION_TITLES
        }
        for h3_section in panel.h3_sections:
            h3_title = h3_section.heading_text.strip()
            if h3_title in extracted_sections:
                extracted_sections[h3_title] = h3_section.original_full_markdown
        return extracted_sections

    @staticmethod
    def update_named_section(
        panel: PanelPydantic, section_h3_title: str, new_markdown_content: str
    ) -> bool:
        """
        Update the content of a named H3 section in the panel. Returns True if successful.
        """
        if not panel:
            logger.error(
                f"Panel is None for update_named_section '{section_h3_title}'."
            )
            return False
        target_h3_section: Optional[H3Pydantic] = None
        for h3 in panel.h3_sections:
            if h3.heading_text.strip() == section_h3_title.strip():
                target_h3_section = h3
                break
        if not target_h3_section:
            logger.error(
                f"H3 section with title '{section_h3_title}' not found in Panel."
            )
            return False
        cleaned = PanelSectionManager._sanitize_markdown(
            section_h3_title, new_markdown_content
        )
        # Ensure heading is present
        if not cleaned.strip().startswith(f"### {section_h3_title}"):
            cleaned = f"### {section_h3_title}\n\n{cleaned}"
        target_h3_section.api_improved_markdown = cleaned
        target_h3_section.api_suggested_enhancement_needed = True
        logger.info(f"API improved markdown set for H3 '{section_h3_title}'.")
        return True

    @staticmethod
    def _sanitize_markdown(heading_text: str, markdown: str) -> str:
        cleaned = markdown.strip()
        if cleaned.startswith("```markdown") or cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) > 2 and lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1]).strip()
        # Remove H3 heading duplicates and code blocks if any
        from mistletoe import Document
        from mistletoe.block_token import BlockCode, BlockToken, Heading

        from models.document_model import (
            get_heading_text,
            render_blocks_to_markdown,
        )

        original_doc = Document(cleaned)
        lower_heading = heading_text.strip().lower()
        filtered_blocks = []
        for block in original_doc.children:
            if isinstance(block, Heading) and block.level == 3:
                block_heading = get_heading_text(block).strip().lower()
                if block_heading == lower_heading:
                    continue
            if isinstance(block, BlockCode):
                continue
            filtered_blocks.append(block)
        new_doc = Document("")
        new_doc.children = filtered_blocks
        rendered = render_blocks_to_markdown(filtered_blocks, new_doc.renderer)
        return rendered.strip()

# document_validator.py

import logging
from typing import Any, Set

from document_model import ChapterPydantic, H3Pydantic, H4Pydantic, PanelPydantic

logger = logging.getLogger(__name__)


class DocumentValidator:
    """
    Validation utilities for Chapter/Panel/H3/H4 model structure.
    Checks uniqueness, presence, and structural soundness.
    """

    @staticmethod
    def validate(chapter_model: ChapterPydantic) -> bool:
        if not chapter_model:
            logger.error(
                "VALIDATION_ERROR: Chapter model not built. Cannot validate IDs. Ensure the document was processed correctly."
            )
            return False
        is_valid = True
        panel_doc_numbers_seen: Set[int] = set()
        for element_idx, element in enumerate(chapter_model.document_elements):
            if isinstance(element, PanelPydantic):
                if element.panel_number_in_doc is None:
                    logger.warning(
                        f"VALIDATE_ID_WARNING: Panel '{element.panel_title_text}' (element #{element_idx}) is missing 'panel_number_in_doc'."
                    )
                    is_valid = False
                    continue
                if element.panel_number_in_doc in panel_doc_numbers_seen:
                    logger.warning(
                        f"VALIDATE_ID_WARNING: Duplicate 'panel_number_in_doc' {element.panel_number_in_doc} for Panel '{element.panel_title_text}'."
                    )
                    is_valid = False
                panel_doc_numbers_seen.add(element.panel_number_in_doc)
                h3_numbers_in_panel_seen: Set[int] = set()
                for h3_idx, h3_section in enumerate(element.h3_sections):
                    if h3_section.h3_number_in_panel is None:
                        logger.warning(
                            f"VALIDATE_ID_WARNING: H3 '{h3_section.heading_text}' (H3 #{h3_idx+1}) in Panel ID {element.panel_number_in_doc} is missing 'h3_number_in_panel'."
                        )
                        is_valid = False
                        continue
                    if h3_section.h3_number_in_panel in h3_numbers_in_panel_seen:
                        logger.warning(
                            f"VALIDATE_ID_WARNING: Duplicate 'h3_number_in_panel' {h3_section.h3_number_in_panel} in Panel ID {element.panel_number_in_doc}."
                        )
                        is_valid = False
                    h3_numbers_in_panel_seen.add(h3_section.h3_number_in_panel)
                    h4_numbers_in_h3_seen: Set[int] = set()
                    for h4_idx, h4_section in enumerate(h3_section.h4_sections):
                        if h4_section.h4_number_in_h3 is None:
                            logger.warning(
                                f"VALIDATE_ID_WARNING: H4 '{h4_section.heading_text}' (H4 #{h4_idx+1}) under H3 ID {h3_section.h3_number_in_panel} (Panel ID {element.panel_number_in_doc}) is missing 'h4_number_in_h3'."
                            )
                            is_valid = False
                            continue
                        if h4_section.h4_number_in_h3 in h4_numbers_in_h3_seen:
                            logger.warning(
                                f"VALIDATE_ID_WARNING: Duplicate 'h4_number_in_h3' {h4_section.h4_number_in_h3} under H3 ID {h3_section.h3_number_in_panel} (Panel ID {element.panel_number_in_doc})."
                            )
                            is_valid = False
                        h4_numbers_in_h3_seen.add(h4_section.h4_number_in_h3)
        if is_valid:
            logger.info("Internal ID validation passed.")
        else:
            logger.warning("Internal ID validation failed.")
        return is_valid

# batch_processor.py
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai_service
from batch_processing.base_batch_processor import BaseBatchProcessor
from models.document_model import H3Pydantic, PanelPydantic
from logging_config import get_logger
from markdown_document import MarkdownDocument

logger = get_logger(__name__)


class BatchProcessor(BaseBatchProcessor):
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run=dry_run)

    def validate_document_structure(self, doc_model: MarkdownDocument) -> bool:
        """
        Enhanced validation with detailed checks for BatchProcessor.
        """
        if not super().validate_document_structure(doc_model):
            return False

        base_filename = Path(doc_model.filepath).name
        has_panels = False
        all_checks_passed = True

        for element_idx, element in enumerate(
            doc_model.chapter_model.document_elements
        ):
            if isinstance(element, PanelPydantic):
                has_panels = True
                panel: PanelPydantic = element
                panel_id_str = (
                    f"Panel ID {panel.panel_number_in_doc} ('{panel.panel_title_text}')"
                )

                # Detailed validation logic moved from original method
                # (Rest of the validation logic from original method)
                # ...

        if not has_panels:
            logger.warning(
                "VALIDATION_WARNING: [%s] No Panel sections found in the document.",
                base_filename,
            )

        if all_checks_passed:
            logger.info(
                "[%s] Document structure validation passed (with any warnings noted above).",
                base_filename,
            )
        else:
            logger.info(
                "[%s] Document structure validation completed with warnings.",
                base_filename,
            )

        return True  # Return True even with warnings, as in original

    def process_single_file(self, filepath: Path, output_dir: Path) -> bool:
        """
        Process a single file - batch processor implementation.
        """
        if not super().process_single_file(filepath, output_dir):
            return False

        doc = MarkdownDocument(filepath=str(filepath))
        any_h3_marked_for_enhancement = False

        for element in doc.chapter_model.document_elements:
            if isinstance(element, PanelPydantic):
                panel: PanelPydantic = element
                if panel.panel_number_in_doc is None:
                    logger.error(
                        "CRITICAL_ERROR: Panel '%s' is missing its document number. Skipping panel processing.",
                        panel.panel_title_text,
                    )
                    continue

                logger.info(
                    "  Processing Panel: ID %s ('%s')",
                    panel.panel_number_in_doc,
                    panel.panel_title_text,
                )

                # Original panel processing logic
                # ...

        if any_h3_marked_for_enhancement:
            output_filename = output_dir / f"{filepath.stem}_enhanced{filepath.suffix}"
            output_dir.mkdir(parents=True, exist_ok=True)
            if self.dry_run:
                logger.info(
                    "  DRY RUN: Would save enhanced document to: %s", output_filename
                )
                return True
            else:
                return doc.save_document(str(output_filename))
        else:
            logger.info(
                "  No enhancements suggested or applied for %s. Original preserved (not re-saved).",
                filepath.name,
            )
            return True

    def process_directory(self, source_dir_path: str, output_dir_path: str) -> None:
        """
        Process all markdown files in a directory - sequential processing.
        """
        super().process_directory(source_dir_path, output_dir_path)

        source_dir = Path(source_dir_path)
        output_dir = Path(output_dir_path)
        markdown_files = list(source_dir.glob("*.md"))

        processed_count = 0
        failed_count = 0

        for md_file_path in markdown_files:
            result = self.process_single_file(md_file_path, output_dir)
            if result:
                processed_count += 1
            else:
                failed_count += 1

        logger.info(
            "\n--- Batch Processing Complete (%s) ---",
            "DRY RUN" if self.dry_run else "LIVE RUN",
        )
        logger.info("Successfully processed/simulated: %s file(s).", processed_count)
        if failed_count > 0:
            logger.info("Failed to process due to errors: %s file(s).", failed_count)

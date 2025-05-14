# base_batch_processor.py
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from document_model import H3Pydantic, MarkdownDocument, PanelPydantic
from logging_config import get_logger

logger = get_logger(__name__)


class BaseBatchProcessor:
    """Base class containing shared functionality for batch processing Markdown files."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize the base batch processor.

        Args:
            dry_run: If True, simulate operations without making actual changes
        """
        self.dry_run = dry_run
        logger.info(
            "BatchProcessor initialized in %s mode.",
            "DRY RUN" if self.dry_run else "LIVE",
        )

    def validate_document_structure(self, doc_model: MarkdownDocument) -> bool:
        """
        Validates if the parsed document model meets structural criteria.
        Returns True if validation passes, False otherwise.
        """
        if not doc_model.filepath:
            logger.error("VALIDATION_ERROR: Document model has no filepath.")
            return False

        base_filename = Path(doc_model.filepath).name

        if not doc_model.chapter_model:
            logger.error(
                "VALIDATION_ERROR: [%s] Chapter model not built.", base_filename
            )
            return False

        if not doc_model.chapter_model.document_elements:
            logger.error(
                "VALIDATION_ERROR: [%s] No document elements found.", base_filename
            )
            return False

        # Basic validation passed
        return True

    def process_panel(self, doc: MarkdownDocument, panel: PanelPydantic) -> int:
        """
        Process a single panel for enhancement.

        Args:
            doc: The document model containing the panel
            panel: The panel to process

        Returns:
            Number of enhancements applied
        """
        section_map = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        if not section_map:
            logger.info("No named sections found in panel %s", panel.panel_title_text)
            return 0

        # Build panel context from available sections
        context_parts = [f"## {panel.panel_title_text}"]
        for section in ["Scene Description", "Teaching Narrative"]:
            if section_map.get(section):
                context_parts.append(section_map[section])
        panel_context = "\n\n".join(context_parts)

        from openai_service import get_enhancement_suggestions_for_panel_h3s

        # Get suggestions for panel H3 sections
        suggestions = get_enhancement_suggestions_for_panel_h3s(
            panel_title=panel.panel_title_text,
            panel_context_markdown=panel_context,
            h3_sections_content=section_map,
        )

        return suggestions

    def process_single_file(self, filepath: Path, output_dir: Path) -> bool:
        """
        Base implementation for processing a single file.
        Subclasses should override as needed.

        Args:
            filepath: Path to the markdown file to process
            output_dir: Directory to save the processed file

        Returns:
            True if processing was successful, False otherwise
        """
        logger.info("Processing file: %s", filepath.name)
        doc = MarkdownDocument(filepath=str(filepath))

        if not doc.chapter_model:
            logger.error("Failed to load document model: %s", filepath.name)
            return False

        if not self.validate_document_structure(doc):
            logger.warning(
                "Skipping %s: Document structure validation failed.", filepath.name
            )
            return False

        return True

    def process_directory(
        self, source_dir_path: Union[str, Path], output_dir_path: Union[str, Path]
    ) -> None:
        """
        Process all markdown files in a directory.

        Args:
            source_dir_path: Directory containing markdown files to process
            output_dir_path: Directory to save processed files
        """
        source_dir = Path(source_dir_path)
        output_dir = Path(output_dir_path)

        if not source_dir.is_dir():
            logger.error(
                "Source directory '%s' not found or is not a directory.", source_dir
            )
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Processing Markdown files from: %s", source_dir)
        logger.info(
            "Output will be saved to%s: %s",
            " (or simulated for)" if self.dry_run else "",
            output_dir,
        )

        markdown_files = list(source_dir.glob("*.md"))
        if not markdown_files:
            logger.info("No Markdown files found in '%s'.", source_dir)
            return

        # Subclasses must implement the actual processing logic

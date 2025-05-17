# enhanced_batch_processor.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Union

from batch_processing.base_batch_processor import BaseBatchProcessor
from document_model import H3Pydantic, PanelPydantic
from logging_config import get_logger
from markdown_document import MarkdownDocument
from openai_service import (
    get_enhancement_suggestions_for_panel_h3s,
    get_improved_markdown_for_section,
    suggest_character_roles_from_context,
)
from section_titles import (
    SECTION_TITLES,
)  # Assuming this is a module with section titles

logger = get_logger(__name__)


class EnhancedBatchProcessor(BaseBatchProcessor):
    def __init__(self, dry_run: bool = False, max_workers: int = 3):
        super().__init__(dry_run=dry_run)
        self.max_workers = max_workers
        logger.info(
            "EnhancedBatchProcessor initialized with %d worker threads",
            self.max_workers,
        )

    def process_panel_roles(
        self, doc: MarkdownDocument, panel: PanelPydantic
    ) -> List[str]:
        """
        Process character roles for a panel.
        """
        section_map = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        if not section_map:
            return []

        scene_md = section_map.get(SECTION_TITLES.SCENE_DESCRIPTION.value, "")
        teaching_md = section_map.get(SECTION_TITLES.TEACHING_NARRATIVE.value, "")

        roles = suggest_character_roles_from_context(
            panel_title=panel.panel_title_text,
            scene_description_md=scene_md,
            teaching_narrative_md=teaching_md,
        )
        logger.info(
            "Suggested character roles for panel '%s': %s",
            panel.panel_title_text,
            roles,
        )
        return roles

    def process_panel(self, doc: MarkdownDocument, panel: PanelPydantic) -> int:
        """
        Enhanced panel processing with more streamlined logic.
        """
        # Get panel context and suggestions using shared base method
        section_map = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        if not section_map:
            return 0

        context_parts = [f"## {panel.panel_title_text}"]
        for section in [
            SECTION_TITLES.SCENE_DESCRIPTION.value,
            SECTION_TITLES.TEACHING_NARRATIVE.value,
        ]:
            if section_map.get(section):
                context_parts.append(section_map[section])
        context = "\n\n".join(context_parts)

        suggestions = get_enhancement_suggestions_for_panel_h3s(
            panel_title=panel.panel_title_text,
            panel_context_markdown=context,
            h3_sections_content=section_map,
        )

        enhancements = 0
        for h3_title, details in suggestions.items():
            if not details.get("enhance"):
                continue
            original = section_map[h3_title]
            enhanced = get_improved_markdown_for_section(
                original_h3_markdown_content=original,
                enhancement_type=details.get("recommendation"),
                enhancement_reason=details.get("reason"),
                panel_title_context=panel.panel_title_text,
                overall_panel_context_md=context,
            )
            if enhanced and doc.update_named_section_in_panel(
                panel.panel_number_in_doc, h3_title, enhanced
            ):
                enhancements += 1
        return enhancements

    def process_single_file(self, filepath: Path, output_dir: Path) -> bool:
        """
        Process a single file - enhanced implementation.
        """
        if not super().process_single_file(filepath, output_dir):
            return False

        doc = MarkdownDocument(filepath=str(filepath))
        updated_panels = 0
        for el in doc.chapter_model.document_elements:
            if isinstance(el, PanelPydantic):
                updated = self.process_panel(doc, el)
                updated_panels += updated

        if updated_panels:
            out_path = output_dir / f"{filepath.stem}_enhanced{filepath.suffix}"
            if self.dry_run:
                logger.info("[DRY RUN] Would save to: %s", out_path)
                return True
            else:
                return doc.save_document(str(out_path))
        else:
            logger.info("No enhancements applied to: %s", filepath.name)
            return True

    def process_roles_directory(self, input_folder: Union[str, Path]) -> None:
        """
        Process only the roles in a directory of markdown files.
        """
        input_folder = Path(input_folder)
        input_folder.mkdir(exist_ok=True)
        all_files = list(input_folder.glob("*.md"))

        for file_path in all_files:
            logger.info("[Roles Only] Processing: %s", file_path.name)
            doc = MarkdownDocument(filepath=str(file_path))
            if not doc.chapter_model:
                logger.warning(
                    "[Roles Only] Skipping: Failed to load document model: %s",
                    file_path.name,
                )
                continue

            for panel in doc.chapter_model.document_elements:
                if isinstance(panel, PanelPydantic):
                    self.process_panel_roles(doc, panel)

    def process_directory(
        self, input_folder: Union[str, Path], output_folder: Union[str, Path]
    ) -> None:
        """
        Process all markdown files in a directory with multi-threading.
        """
        super().process_directory(input_folder, output_folder)

        input_folder = Path(input_folder)
        output_folder = Path(output_folder)
        all_files = list(input_folder.glob("*.md"))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_single_file, f, output_folder): f
                for f in all_files
            }
            for future in as_completed(futures):
                f = futures[future]
                try:
                    success = future.result()
                    if success:
                        logger.info("✅ Processed: %s", f.name)
                    else:
                        logger.warning("⚠️ Failed to process: %s", f.name)
                except Exception as e:
                    logger.exception(
                        "Unhandled error while processing file: %s", f.name
                    )

        logger.info("Batch processing complete. Processed %d files.", len(all_files))

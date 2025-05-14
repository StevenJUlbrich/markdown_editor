from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from document_model import H3Pydantic, MarkdownDocument, PanelPydantic
from logging_config import get_logger
from openai_service import (
    get_enhancement_suggestions_for_panel_h3s,
    get_improved_markdown_for_section,
    suggest_character_roles_from_context,
)

logger = get_logger(__name__)


class EnhancedBatchProcessor:
    def __init__(self, dry_run: bool = False, max_workers: int = 3):
        self.dry_run = dry_run
        self.max_workers = max_workers

    def process_panel_roles(
        self, doc: MarkdownDocument, panel: PanelPydantic
    ) -> List[str]:
        section_map = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        if not section_map:
            return []

        scene_md = section_map.get("Scene Description", "")
        teaching_md = section_map.get("Teaching Narrative", "")

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

    def process_roles_directory(self, input_folder: Path) -> None:
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

    def process_panel(self, doc: MarkdownDocument, panel: PanelPydantic) -> int:
        section_map = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        if not section_map:
            return 0

        context_parts = [f"## {panel.panel_title_text}"]
        for section in ["Scene Description", "Teaching Narrative"]:
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

    def process_file(self, filepath: Path, output_dir: Path) -> bool:
        logger.info("Processing file: %s", filepath.name)
        doc = MarkdownDocument(filepath=str(filepath))
        if not doc.chapter_model:
            logger.error("Failed to load document model: %s", filepath.name)
            return False

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

    def process_directory(self, input_folder: Path, output_folder: Path) -> None:
        input_folder.mkdir(exist_ok=True)
        output_folder.mkdir(exist_ok=True)
        all_files = list(input_folder.glob("*.md"))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_file, f, output_folder): f
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

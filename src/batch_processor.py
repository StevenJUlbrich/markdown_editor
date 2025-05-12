# batch_processor.py
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai_service
from document_model import H3Pydantic, MarkdownDocument, PanelPydantic


class BatchProcessor:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        if self.dry_run:
            print("INFO: BatchProcessor initialized in DRY RUN mode.")
        else:
            print("INFO: BatchProcessor initialized.")

    def validate_document_structure(self, doc_model: MarkdownDocument) -> bool:
        """
        Validates if the parsed document model meets basic and deeper structural criteria.
        Returns True if validation passes, False otherwise.
        """
        if not doc_model.filepath:  # Should always have a filepath if loaded
            print("VALIDATION_ERROR: Document model has no filepath.")
            return False

        base_filename = Path(doc_model.filepath).name  # For context in messages

        if not doc_model.chapter_model:
            print(f"VALIDATION_ERROR: [{base_filename}] Chapter model not built.")
            return False
        if (
            not doc_model.chapter_model.chapter_title_text
            or doc_model.chapter_model.chapter_title_text == "Untitled Chapter"
        ):
            print(
                f"VALIDATION_WARNING: [{base_filename}] Chapter title is missing or default ('{doc_model.chapter_model.chapter_title_text}')."
            )
            # Not returning False, as it might still be processable

        if not doc_model.chapter_model.document_elements:
            print(
                f"VALIDATION_ERROR: [{base_filename}] No document elements (generic content or panels) found."
            )
            return False

        has_panels = False
        all_checks_passed = True  # Track overall validation status

        for element_idx, element in enumerate(
            doc_model.chapter_model.document_elements
        ):
            if isinstance(element, PanelPydantic):
                has_panels = True
                panel: PanelPydantic = element
                panel_id_str = (
                    f"Panel ID {panel.panel_number_in_doc} ('{panel.panel_title_text}')"
                )

                # 1. Ensure each Panel has at least one H3 section
                if not panel.h3_sections:
                    print(
                        f"VALIDATION_WARNING: [{base_filename}] {panel_id_str} has no H3 sections."
                    )
                    all_checks_passed = (
                        False  # Consider this a warning that might affect processing
                    )

                for h3_idx, h3_section in enumerate(panel.h3_sections):
                    h3_id_str = f"H3 ID {h3_section.h3_number_in_panel} ('{h3_section.heading_text}') in {panel_id_str}"

                    # 2. Ensure non-"Initial Content" H3s have substance
                    if (
                        h3_section.heading_text != "Initial Content"
                        and not h3_section.initial_content_markdown.strip()
                        and not h3_section.h4_sections
                    ):
                        print(
                            f"VALIDATION_WARNING: [{base_filename}] {h3_id_str} (not 'Initial Content') appears to have no content or H4 sub-sections."
                        )
                        # all_checks_passed = False # Decide if this is critical

                    # 3. Ensure H4 sections have substance
                    for h4_idx, h4_section in enumerate(h3_section.h4_sections):
                        h4_id_str = f"H4 ID {h4_section.h4_number_in_h3} ('{h4_section.heading_text}') in {h3_id_str}"
                        if not h4_section.content_markdown.strip():
                            print(
                                f"VALIDATION_WARNING: [{base_filename}] {h4_id_str} appears to have no content."
                            )
                            # all_checks_passed = False # Decide if this is critical

        if not has_panels:
            print(
                f"VALIDATION_WARNING: [{base_filename}] No Panel sections found in the document."
            )
            # Depending on requirements, this might be an error:
            # all_checks_passed = False

        if all_checks_passed:
            print(
                f"INFO: [{base_filename}] Document structure validation passed (with any warnings noted above)."
            )
        else:
            print(
                f"INFO: [{base_filename}] Document structure validation completed with warnings."
            )
            # Return True even with warnings, to allow processing.
            # If any warning should be a hard fail, set all_checks_passed = False and return it.

        # For now, we return True if basic model structure is there, even with content warnings.
        # If specific warnings should halt processing, `all_checks_passed` should be returned.
        # The doc_model already runs _validate_internal_ids which is more critical.
        return True  # Let's keep it as True for now, and rely on warnings.

    def process_single_file(self, filepath: Path, output_dir: Path) -> bool:
        print(f"\n--- Processing file: {filepath.name} ---")
        doc: MarkdownDocument = MarkdownDocument(filepath=str(filepath))
        if (
            not doc.raw_content or not doc.chapter_model
        ):  # Check if model building failed earlier
            print(
                f"Skipping {filepath.name}: Failed to load or parse initial model (doc.chapter_model is None)."
            )
            return False

        if not self.validate_document_structure(doc):
            # If validate_document_structure returns False for critical errors (currently it returns True even with warnings)
            print(
                f"Skipping {filepath.name}: Failed critical document structure validation."
            )
            return False

        any_h3_marked_for_enhancement = False

        for element in doc.chapter_model.document_elements:
            if isinstance(element, PanelPydantic):
                panel: PanelPydantic = element
                if panel.panel_number_in_doc is None:
                    print(
                        f"CRITICAL_ERROR: Panel '{panel.panel_title_text}' is missing its document number. Skipping panel processing."
                    )
                    continue

                print(
                    f"  Processing Panel: ID {panel.panel_number_in_doc} ('{panel.panel_title_text}')"
                )

                panel_context_markdown = f"## {panel.panel_title_text}\n"
                # Simplified context - can be expanded
                if panel.h3_sections and len(panel.h3_sections) > 0:
                    first_h3_example = panel.h3_sections[0]
                    if (
                        "scene description" in first_h3_example.heading_text.lower()
                        and first_h3_example.original_full_markdown
                    ):
                        panel_context_markdown += (
                            first_h3_example.original_full_markdown + "\n\n"
                        )
                    if len(panel.h3_sections) > 1:
                        second_h3_example = panel.h3_sections[1]
                        if (
                            "teaching narrative"
                            in second_h3_example.heading_text.lower()
                            and second_h3_example.original_full_markdown
                        ):
                            panel_context_markdown += (
                                second_h3_example.original_full_markdown + "\n\n"
                            )

                h3s_to_evaluate_content: Dict[str, str] = {}
                valid_h3s_for_api: List[H3Pydantic] = []

                for h3_section in panel.h3_sections:
                    if h3_section.h3_number_in_panel is None:
                        print(
                            f"CRITICAL_ERROR: H3 section '{h3_section.heading_text}' in Panel ID {panel.panel_number_in_doc} is missing its number. Skipping H3."
                        )
                        continue

                    # Skip truly empty "Initial Content" or other H3s if their original_full_markdown is empty/whitespace
                    # original_full_markdown includes the heading. Content check should be on content part.
                    is_empty_initial_content = (
                        h3_section.heading_text == "Initial Content"
                        and (
                            not h3_section.initial_content_markdown
                            or not h3_section.initial_content_markdown.strip()
                        )
                        and not h3_section.h4_sections
                    )

                    # Check if a named H3 is effectively empty (no initial content and no H4s)
                    is_empty_named_h3 = (
                        h3_section.heading_text != "Initial Content"
                        and not h3_section.initial_content_markdown.strip()
                        and not h3_section.h4_sections
                    )

                    if is_empty_initial_content or is_empty_named_h3:
                        print(
                            f"    Skipping empty H3 section '{h3_section.heading_text}' (ID: {h3_section.h3_number_in_panel}) in Panel ID {panel.panel_number_in_doc} for API evaluation."
                        )
                        continue

                    h3s_to_evaluate_content[h3_section.heading_text] = (
                        h3_section.original_full_markdown  # Send the full H3 section
                    )
                    valid_h3s_for_api.append(h3_section)

                if not h3s_to_evaluate_content:
                    print(
                        f"    No non-empty H3 sections found in Panel ID {panel.panel_number_in_doc} to evaluate."
                    )
                    continue  # To the next panel

                suggestions: Dict[str, Dict[str, Any]] = {}
                if self.dry_run:
                    print(
                        f"    DRY RUN: Would call OpenAI for suggestions for {len(h3s_to_evaluate_content)} H3 section(s)..."
                    )
                    for i, h3_s_obj in enumerate(valid_h3s_for_api):
                        suggestions[h3_s_obj.heading_text] = {
                            "enhance": (i % 2 == 0),  # Alternate for testing
                            "recommendation": (
                                "Add DryRun Example" if (i % 2 == 0) else None
                            ),
                            "reason": (
                                "Dry run testing"
                                if (i % 2 == 0)
                                else "Dry run, no change"
                            ),
                        }
                else:
                    print(
                        f"    Getting OpenAI suggestions for {len(h3s_to_evaluate_content)} H3 section(s)..."
                    )
                    suggestions = (
                        openai_service.get_enhancement_suggestions_for_panel_h3s(
                            panel_title=panel.panel_title_text,
                            panel_context_markdown=panel_context_markdown.strip(),
                            h3_sections_content=h3s_to_evaluate_content,
                        )
                    )

                if not suggestions:
                    print(
                        f"    No suggestions received (or simulated) for H3s in Panel ID {panel.panel_number_in_doc}."
                    )

                for h3_section in valid_h3s_for_api:
                    suggestion_for_h3 = suggestions.get(h3_section.heading_text)
                    if suggestion_for_h3:
                        doc.update_h3_section_with_api_suggestions(
                            panel_id=panel.panel_number_in_doc,
                            h3_id_in_panel=h3_section.h3_number_in_panel,
                            should_enhance=suggestion_for_h3.get("enhance"),
                            enhancement_type=suggestion_for_h3.get("recommendation"),
                            enhancement_reason=suggestion_for_h3.get("reason"),
                        )
                        if h3_section.api_suggested_enhancement_needed:
                            any_h3_marked_for_enhancement = True
                            print(
                                f"      H3 '{h3_section.heading_text}' (ID: {h3_section.h3_number_in_panel}) marked for enhancement: {h3_section.api_suggested_enhancement_type}"
                            )

                for h3_section in valid_h3s_for_api:
                    if h3_section.api_suggested_enhancement_needed:
                        improved_md: Optional[str] = None
                        if self.dry_run:
                            print(
                                f"    DRY RUN: Would call OpenAI to enhance H3 ID {h3_section.h3_number_in_panel} ('{h3_section.heading_text}') (Suggestion: {h3_section.api_suggested_enhancement_type})"
                            )
                            improved_md = f"### {h3_section.heading_text}\n\nThis is a **DRY RUN enhanced version** for H3 ID {h3_section.h3_number_in_panel} ('{h3_section.heading_text}') based on '{h3_section.api_suggested_enhancement_type}'.\nOriginal content snippet: {h3_section.original_full_markdown[:100]}..."
                        else:
                            print(
                                f"    Getting improved content for H3 ID {h3_section.h3_number_in_panel} ('{h3_section.heading_text}') (Suggestion: {h3_section.api_suggested_enhancement_type})"
                            )
                            # Ensure original_full_markdown is passed for enhancement
                            improved_md = openai_service.get_improved_markdown_for_section(
                                original_h3_markdown_content=h3_section.original_full_markdown,
                                enhancement_type=h3_section.api_suggested_enhancement_type,
                                enhancement_reason=h3_section.api_suggested_enhancement_reason,
                                panel_title_context=panel.panel_title_text,
                                overall_panel_context_md=panel_context_markdown.strip(),
                            )

                        if improved_md is not None:
                            doc.update_h3_section_with_improved_markdown(
                                panel_id=panel.panel_number_in_doc,
                                h3_id_in_panel=h3_section.h3_number_in_panel,
                                improved_markdown=improved_md,
                            )
                        else:
                            print(
                                f"      INFO: No improved content received (or simulated) for H3 ID {h3_section.h3_number_in_panel} ('{h3_section.heading_text}'). Original will be used."
                            )
                            # This is not necessarily a failure of the process, API might decide not to change.
                            # Or, if it was an empty section, get_improved_markdown_for_section returns None.

        if (
            any_h3_marked_for_enhancement
        ):  # Only save if an actual (or dry-run simulated) enhancement was made
            output_filename = output_dir / f"{filepath.stem}_enhanced{filepath.suffix}"
            output_dir.mkdir(parents=True, exist_ok=True)
            if self.dry_run:
                print(f"  DRY RUN: Would save enhanced document to: {output_filename}")
                # dry_run_content = doc.reconstruct_and_render_document() # To see what would be saved
                # print(f"  DRY RUN: Reconstructed content preview (first 200 chars):\n{dry_run_content[:200]}...")
                return True
            else:
                if doc.save_document(str(output_filename)):
                    # print(f"  Enhanced document saved to: {output_filename}") # Message is in doc.save_document()
                    return True
                else:
                    # print(f"  Failed to save enhanced document: {output_filename}") # Message is in doc.save_document()
                    return False
        else:
            print(
                f"  No enhancements suggested or applied for {filepath.name}. Original preserved (not re-saved)."
            )
            return True

    def process_directory(self, source_dir_path: str, output_dir_path: str) -> None:
        source_dir = Path(source_dir_path)
        output_dir = Path(output_dir_path)

        if not source_dir.is_dir():
            print(
                f"ERROR: Source directory '{source_dir}' not found or is not a directory."
            )
            return

        if self.dry_run:
            print(f"\n--- DRY RUN MODE ENABLED ---")
            print(
                f"--- Actions will be simulated, no files will be written, no API calls made (unless mock service prints) ---"
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"INFO: Processing Markdown files from: {source_dir}")
        print(f"INFO: Output will be saved to (or simulated for): {output_dir}")

        markdown_files = list(source_dir.glob("*.md"))

        if not markdown_files:
            print(f"INFO: No Markdown files found in '{source_dir}'.")
            return

        processed_count = 0
        failed_count = 0
        skipped_count = 0

        for md_file_path in markdown_files:
            result = self.process_single_file(md_file_path, output_dir)
            if (
                result
            ):  # process_single_file returns True if processed (even if no changes) or skipped due to no enhancements
                processed_count += 1
            else:  # Only returns False on critical load/parse errors or save errors
                failed_count += 1

        print(
            f"\n--- Batch Processing Complete ({'DRY RUN' if self.dry_run else 'LIVE RUN'}) ---"
        )
        print(f"Successfully processed/simulated: {processed_count} file(s).")
        if failed_count > 0:
            print(f"Failed to process due to errors: {failed_count} file(s).")


if __name__ == "__main__":
    print("Starting Batch Processor Test...")
    DRY_RUN_ENABLED = True  # Toggle this for live runs

    current_script_dir = Path(
        __file__
    ).parent.resolve()  # Use resolve for absolute path
    test_source_dir = current_script_dir / "test_markdown_source_batch_validation"
    test_output_dir = current_script_dir / "test_markdown_output_batch_validation"

    print(f"Test source directory: {test_source_dir}")
    print(f"Test output directory: {test_output_dir}")

    test_source_dir.mkdir(exist_ok=True)
    test_output_dir.mkdir(exist_ok=True)

    # File that should pass basic validation but might have content warnings
    valid_structure_md = """# Chapter 1: Valid Structure
## Panel 1: First Panel
### Scene Description
Content here.
### Teaching Narrative
More content.
#### Sub-detail 1
Sub-content.
"""
    # File with a panel missing H3s (should trigger a warning)
    panel_no_h3_md = """# Chapter 2: Panel No H3
## Panel 1: Empty Panel
"""
    # File with a named H3 that is empty (should trigger a warning)
    empty_named_h3_md = """# Chapter 3: Empty Named H3
## Panel 1: Contains Empty H3
### Scene Description
Valid content.
### Empty H3 Section
### Another Valid H3
Content.
"""
    # File with an empty H4 (should trigger a warning)
    empty_h4_md = """# Chapter 4: Empty H4
## Panel 1: Contains Empty H4
### Scene Description
Content.
### H3 with Empty H4
#### Empty H4 Heading
#### Non-Empty H4
Content for non-empty H4.
"""
    files_to_create = {
        "valid_structure.md": valid_structure_md,
        "panel_no_h3.md": panel_no_h3_md,
        "empty_named_h3.md": empty_named_h3_md,
        "empty_h4.md": empty_h4_md,
    }

    for filename, content in files_to_create.items():
        file_path = test_source_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created dummy file: {file_path}")

    processor = BatchProcessor(dry_run=DRY_RUN_ENABLED)
    processor.process_directory(str(test_source_dir), str(test_output_dir))
    print("\nBatch Processor Test Finished.")

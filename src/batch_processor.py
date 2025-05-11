# batch_processor.py
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Assuming document_model.py and openai_service.py are in the same directory or PYTHONPATH
import openai_service  # Our service for OpenAI calls
from document_model import MarkdownDocument, PanelPydantic  # Pydantic-based model


class BatchProcessor:
    def __init__(self, dry_run: bool = False):
        # The openai_service module initializes its own client (mock or real)
        self.dry_run = dry_run
        if self.dry_run:
            print("BatchProcessor initialized in DRY RUN mode.")
        else:
            print("BatchProcessor initialized.")

    def validate_document_structure(self, doc_model: MarkdownDocument) -> bool:
        """
        Validates if the parsed document model meets basic expected criteria.
        """
        if not doc_model.chapter_model:
            print(
                f"Validation Error: Chapter model not built for {doc_model.filepath}."
            )
            return False
        if (
            not doc_model.chapter_model.chapter_title_text
            or doc_model.chapter_model.chapter_title_text == "Untitled Chapter"
        ):
            print(
                f"Validation Error: Chapter title missing or default in {doc_model.filepath}."
            )
            return False
        if not doc_model.chapter_model.document_elements:
            print(
                f"Validation Error: No document elements (generic content or panels) found in {doc_model.filepath}."
            )
            return False

        has_panels = any(
            isinstance(el, PanelPydantic)
            for el in doc_model.chapter_model.document_elements
        )

        if not has_panels:
            print(
                f"Validation Warning: No Panel sections found in {doc_model.filepath}."
            )
            # Decide if this is a critical error or just a warning
            # return False

        print(f"Validation basic check passed for {doc_model.filepath}.")
        return True

    def process_single_file(self, filepath: Path, output_dir: Path) -> bool:
        """
        Processes a single Markdown file.
        In dry_run mode, it will simulate actions but not make API calls or save files.
        """
        print(f"\n--- Processing file: {filepath.name} ---")
        doc: MarkdownDocument = MarkdownDocument(filepath=str(filepath))
        if not doc.raw_content or not doc.chapter_model:
            print(f"Skipping {filepath.name}: Failed to load or parse initial model.")
            return False

        if not self.validate_document_structure(doc):
            print(f"Skipping {filepath.name}: Failed validation.")
            return False

        any_h3_marked_for_enhancement = False

        for element in doc.chapter_model.document_elements:
            if isinstance(element, PanelPydantic):
                panel: PanelPydantic = element
                print(f"  Processing Panel: {panel.panel_title_text}")

                # Simplified panel context for now, can be expanded
                panel_context_markdown = f"## {panel.panel_title_text}\n"
                # Example: Add Scene Description and Teaching Narrative if they exist as first H3s
                if panel.h3_sections:
                    if "scene description" in panel.h3_sections[0].heading_text.lower():
                        panel_context_markdown += (
                            panel.h3_sections[0].original_full_markdown + "\n\n"
                        )
                    if (
                        len(panel.h3_sections) > 1
                        and "teaching narrative"
                        in panel.h3_sections[1].heading_text.lower()
                    ):
                        panel_context_markdown += (
                            panel.h3_sections[1].original_full_markdown + "\n\n"
                        )

                h3s_to_evaluate_content: Dict[str, str] = {}
                valid_h3s_for_api = []

                for h3_section in panel.h3_sections:
                    # Filter out empty "Initial Content" sections if desired before API call
                    if h3_section.heading_text == "Initial Content" and (
                        not h3_section.initial_content_markdown
                        or not h3_section.initial_content_markdown.strip()
                    ):
                        print(
                            f"    Skipping empty 'Initial Content' in Panel '{panel.panel_title_text}' for API evaluation."
                        )
                        continue
                    h3s_to_evaluate_content[h3_section.heading_text] = (
                        h3_section.original_full_markdown
                    )
                    valid_h3s_for_api.append(h3_section)

                if not h3s_to_evaluate_content:
                    print(
                        f"    No non-empty H3 sections found in Panel '{panel.panel_title_text}' to evaluate."
                    )
                    continue

                suggestions: Dict[str, Dict[str, Any]] = {}
                if self.dry_run:
                    print(
                        f"    DRY RUN: Would call OpenAI for suggestions for {len(h3s_to_evaluate_content)} H3 section(s)..."
                    )
                    # Simulate some suggestions for dry run testing flow
                    for i, h3_title_key in enumerate(h3s_to_evaluate_content.keys()):
                        if i % 2 == 0:  # Make some sections need enhancement in dry run
                            suggestions[h3_title_key] = {
                                "enhance": True,
                                "recommendation": "Add DryRun Example",
                                "reason": "Dry run testing",
                            }
                        else:
                            suggestions[h3_title_key] = {
                                "enhance": False,
                                "recommendation": None,
                                "reason": "Dry run, no change",
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
                        f"    No suggestions received (or simulated) for H3s in Panel '{panel.panel_title_text}'."
                    )
                    # continue # Continue to next panel if no suggestions

                for (
                    h3_section
                ) in valid_h3s_for_api:  # Iterate only over H3s sent for evaluation
                    suggestion_for_h3 = suggestions.get(h3_section.heading_text)
                    if suggestion_for_h3:
                        doc.update_h3_section_with_api_suggestions(
                            panel_title=panel.panel_title_text,
                            h3_title=h3_section.heading_text,
                            should_enhance=suggestion_for_h3.get("enhance"),
                            enhancement_type=suggestion_for_h3.get("recommendation"),
                            enhancement_reason=suggestion_for_h3.get("reason"),
                        )
                        if suggestion_for_h3.get("enhance"):
                            any_h3_marked_for_enhancement = True
                            print(
                                f"      H3 '{h3_section.heading_text}' marked for enhancement: {suggestion_for_h3.get('recommendation')}"
                            )

                for h3_section in valid_h3s_for_api:
                    if h3_section.api_suggested_enhancement_needed:
                        improved_md: Optional[str] = None
                        if self.dry_run:
                            print(
                                f"    DRY RUN: Would call OpenAI to enhance H3: {h3_section.heading_text} (Suggestion: {h3_section.api_suggested_enhancement_type})"
                            )
                            improved_md = f"### {h3_section.heading_text}\n\nThis is a **DRY RUN enhanced version** for '{h3_section.heading_text}' based on '{h3_section.api_suggested_enhancement_type}'.\nOriginal content snippet: {h3_section.original_full_markdown[:100]}..."
                        else:
                            print(
                                f"    Getting improved content for H3: {h3_section.heading_text} (Suggestion: {h3_section.api_suggested_enhancement_type})"
                            )
                            improved_md = openai_service.get_improved_markdown_for_section(
                                original_h3_markdown_content=h3_section.original_full_markdown,
                                enhancement_type=h3_section.api_suggested_enhancement_type,
                                enhancement_reason=h3_section.api_suggested_enhancement_reason,
                                panel_title_context=panel.panel_title_text,
                                overall_panel_context_md=panel_context_markdown.strip(),
                            )

                        if (
                            improved_md is not None
                        ):  # Check for None, not just truthiness, as empty string might be valid
                            doc.update_h3_section_with_improved_markdown(
                                panel_title=panel.panel_title_text,
                                h3_title=h3_section.heading_text,
                                improved_markdown=improved_md,
                            )
                        else:
                            print(
                                f"      Failed to get (or simulate) improved content for H3: {h3_section.heading_text}"
                            )

        if any_h3_marked_for_enhancement:
            output_filename = output_dir / f"{filepath.stem}_enhanced{filepath.suffix}"
            output_dir.mkdir(parents=True, exist_ok=True)
            if self.dry_run:
                print(f"  DRY RUN: Would save enhanced document to: {output_filename}")
                # Optionally print a snippet of what would be saved in dry run:
                # dry_run_content = doc.reconstruct_and_render_document()
                # print(f"  DRY RUN: Content snippet (first 200 chars):\n{dry_run_content[:200]}...")
                return True  # Simulate success for dry run
            else:
                if doc.save_document(str(output_filename)):
                    print(f"  Enhanced document saved to: {output_filename}")
                    return True
                else:
                    print(f"  Failed to save enhanced document: {output_filename}")
                    return False
        else:
            print(
                f"  No enhancements suggested or applied for {filepath.name}. Original preserved (not re-saved)."
            )
            return True  # Still considered a successful process in terms of workflow

    def process_directory(self, source_dir_path: str, output_dir_path: str) -> None:
        source_dir = Path(source_dir_path)
        output_dir = Path(output_dir_path)

        if not source_dir.is_dir():
            print(
                f"Error: Source directory '{source_dir}' not found or is not a directory."
            )
            return

        if self.dry_run:
            print(f"--- DRY RUN MODE ENABLED ---")
            print(
                f"--- Actions will be simulated, no files will be written, no API calls made ---"
            )

        output_dir.mkdir(
            parents=True, exist_ok=True
        )  # Still create output_dir in dry_run to check writability
        print(f"Processing Markdown files from: {source_dir}")
        print(f"Output will be saved to (or simulated for): {output_dir}")

        markdown_files = list(
            source_dir.glob("*.md")
        )  # Consider specific patterns like "chapter_*.md"

        if not markdown_files:
            print(f"No Markdown files found in '{source_dir}'.")
            return

        processed_count = 0
        failed_count = 0
        for md_file_path in markdown_files:
            if self.process_single_file(md_file_path, output_dir):
                processed_count += 1
            else:
                failed_count += 1

        print(
            f"\n--- Batch Processing Complete ({'DRY RUN' if self.dry_run else 'LIVE RUN'}) ---"
        )
        print(f"Successfully processed (or simulated): {processed_count} file(s).")
        print(f"Failed to process: {failed_count} file(s).")


# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Starting Batch Processor Test...")

    # --- !!! SET DRY_RUN MODE HERE for testing !!! ---
    DRY_RUN_ENABLED = True
    # Set to False to perform actual operations (API calls, file saves)
    # --- !!! ------------------------------------ !!! ---

    # Create dummy directories and a file for testing
    current_script_dir = Path(__file__).parent
    test_source_dir = (
        current_script_dir / "test_markdown_source_batch"
    )  # Changed name to avoid conflict
    test_output_dir = current_script_dir / "test_markdown_output_batch"
    test_source_dir.mkdir(exist_ok=True)
    test_output_dir.mkdir(exist_ok=True)

    dummy_md_content_batch = """# Chapter 1: Test Chapter Batch

## Chapter Overview
This is a test overview for batch processing.

---

## Panel 1: Test Panel One Batch
### Scene Description
A test scene for batch.
### Teaching Narrative
Test teaching narrative for panel one batch.
### Common Example of the Problem
A test common problem for batch.
### SRE Best Practice: Evidence-Based Investigation
Test SRE best practice for batch.

---

## Panel 2: Test Panel Two Batch
### Scene Description
Another test scene for batch.
### Teaching Narrative
Test teaching narrative for panel two batch.
### SRE Best Practice: Evidence-Based Investigation
Test SRE best practice for batch.
    """
    dummy_file_path_batch = test_source_dir / "test_chapter_01_batch.md"
    with open(dummy_file_path_batch, "w", encoding="utf-8") as f:
        f.write(dummy_md_content_batch)

    print(f"Created dummy file: {dummy_file_path_batch}")

    processor = BatchProcessor(dry_run=DRY_RUN_ENABLED)  # Pass the dry_run flag
    processor.process_directory(str(test_source_dir), str(test_output_dir))

    print("\nBatch Processor Test Finished.")

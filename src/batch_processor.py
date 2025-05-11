# batch_processor.py
import os
from pathlib import Path
from typing import Any, Dict, List, Optional  # Added Optional for type hint

import openai_service  # Our new service for OpenAI calls

# Ensure PanelPydantic is imported directly for type hinting and isinstance checks
from document_model import MarkdownDocument, PanelPydantic  # Pydantic-based model


class BatchProcessor:
    def __init__(self, openai_api_key: Optional[str] = None):
        # The openai_service module initializes its own client (mock or real)
        # We might pass the key if the service was designed to take it at runtime.
        # For now, openai_service handles its own client setup.
        print("BatchProcessor initialized.")

    def validate_document_structure(self, doc_model: MarkdownDocument) -> bool:
        """
        Validates if the parsed document model meets basic expected criteria.
        Placeholder: Implement more specific validation rules as needed.
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

        # Check for at least one panel using the directly imported PanelPydantic
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
        Processes a single Markdown file:
        1. Loads and parses into Pydantic model.
        2. Validates structure.
        3. Iterates panels and H3s, gets OpenAI suggestions.
        4. If suggestions indicate enhancement, gets improved content from OpenAI.
        5. Updates the Pydantic model.
        6. Saves the (potentially) modified document if enhancements were suggested.
        """
        print(f"\n--- Processing file: {filepath.name} ---")
        # Ensure doc_model is correctly typed for Pylance if MarkdownDocument is complex
        doc: MarkdownDocument = MarkdownDocument(filepath=str(filepath))
        if not doc.raw_content or not doc.chapter_model:
            print(f"Skipping {filepath.name}: Failed to load or parse initial model.")
            return False

        if not self.validate_document_structure(doc):
            print(f"Skipping {filepath.name}: Failed validation.")
            return False

        any_h3_marked_for_enhancement = False

        for element in doc.chapter_model.document_elements:
            # Corrected isinstance check and type hint
            if isinstance(element, PanelPydantic):
                panel: PanelPydantic = element  # Correct type hint
                print(f"  Processing Panel: {panel.panel_title_text}")

                panel_context_parts = [f"## {panel.panel_title_text}"]
                h3s_to_evaluate_content: Dict[str, str] = {}

                scene_desc_content = ""
                teaching_narr_content = ""

                for h3_idx, h3_section in enumerate(panel.h3_sections):
                    if h3_idx == 0 and "Scene Description" in h3_section.heading_text:
                        scene_desc_content = h3_section.original_full_markdown
                    elif (
                        h3_idx == 1 and "Teaching Narrative" in h3_section.heading_text
                    ):
                        teaching_narr_content = h3_section.original_full_markdown

                    h3s_to_evaluate_content[h3_section.heading_text] = (
                        h3_section.original_full_markdown
                    )

                if scene_desc_content:
                    panel_context_parts.append(scene_desc_content)
                if teaching_narr_content:
                    panel_context_parts.append(teaching_narr_content)
                current_panel_context_md = "\n\n---\n\n".join(panel_context_parts)

                if not h3s_to_evaluate_content:
                    print(
                        f"    No H3 sections found in Panel '{panel.panel_title_text}' to evaluate."
                    )
                    continue

                print(
                    f"    Getting OpenAI suggestions for {len(h3s_to_evaluate_content)} H3 section(s)..."
                )
                suggestions = openai_service.get_enhancement_suggestions_for_panel_h3s(
                    panel_title=panel.panel_title_text,
                    panel_context_markdown=current_panel_context_md,
                    h3_sections_content=h3s_to_evaluate_content,
                )

                if not suggestions:
                    print(
                        f"    No suggestions received from OpenAI for H3s in Panel '{panel.panel_title_text}'."
                    )
                    continue

                for h3_section in panel.h3_sections:
                    suggestion_for_h3 = suggestions.get(h3_section.heading_text)
                    if suggestion_for_h3:
                        # Assuming update_h3_section_with_api_suggestions is a method of MarkdownDocument (doc)
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

                # This condition should check if *any* H3 in the *current panel* or *entire document* was marked.
                # The current any_h3_marked_for_enhancement is document-wide.
                # For processing per panel, you might reset this flag or check h3_section.api_suggested_enhancement_needed directly.
                # For simplicity, let's assume if any H3 in the document is marked, we proceed for those that are.

                # Iterate again to get improved content for those marked
                for h3_section in panel.h3_sections:
                    if (
                        h3_section.api_suggested_enhancement_needed
                    ):  # Check the flag on the Pydantic object
                        print(
                            f"    Getting improved content for H3: {h3_section.heading_text} (Suggestion: {h3_section.api_suggested_enhancement_type})"
                        )
                        improved_md = openai_service.get_improved_markdown_for_section(
                            original_h3_markdown_content=h3_section.original_full_markdown,
                            enhancement_type=h3_section.api_suggested_enhancement_type,
                            enhancement_reason=h3_section.api_suggested_enhancement_reason,
                            panel_title_context=panel.panel_title_text,
                            overall_panel_context_md=current_panel_context_md,
                        )
                        if improved_md:
                            # Assuming update_h3_section_with_improved_markdown is a method of MarkdownDocument (doc)
                            doc.update_h3_section_with_improved_markdown(
                                panel_title=panel.panel_title_text,
                                h3_title=h3_section.heading_text,
                                improved_markdown=improved_md,
                            )
                        else:
                            print(
                                f"      Failed to get improved content for H3: {h3_section.heading_text}"
                            )

        if any_h3_marked_for_enhancement:
            output_filename = output_dir / f"{filepath.stem}_enhanced{filepath.suffix}"
            output_dir.mkdir(parents=True, exist_ok=True)
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
            return True

    def process_directory(self, source_dir_path: str, output_dir_path: str) -> None:
        source_dir = Path(source_dir_path)
        output_dir = Path(output_dir_path)

        if not source_dir.is_dir():
            print(
                f"Error: Source directory '{source_dir}' not found or is not a directory."
            )
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Processing Markdown files from: {source_dir}")
        print(f"Output will be saved to: {output_dir}")

        markdown_files = list(source_dir.glob("*.md"))

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

        print(f"\n--- Batch Processing Complete ---")
        print(
            f"Successfully processed (or skipped without changes): {processed_count} file(s)."
        )
        print(f"Failed to process: {failed_count} file(s).")


# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Starting Batch Processor Test...")

    test_source_dir = Path("test_markdown_source")
    test_output_dir = Path("test_markdown_output")
    test_source_dir.mkdir(exist_ok=True)
    test_output_dir.mkdir(exist_ok=True)

    dummy_md_content = """# Chapter 1: Test Chapter

## Chapter Overview
This is a test overview.

---

## Panel 1: Test Panel One
### Scene Description
A test scene.
### Teaching Narrative
Test teaching narrative for panel one.
### Common Example of the Problem
A test common problem.

---

## Panel 2: Test Panel Two
### Scene Description
Another test scene.
### Teaching Narrative
Test teaching narrative for panel two.
### SRE Best Practice: Evidence-Based Investigation
Test SRE best practice.
    """
    dummy_file_path = test_source_dir / "test_chapter_01.md"
    with open(dummy_file_path, "w", encoding="utf-8") as f:
        f.write(dummy_md_content)

    print(f"Created dummy file: {dummy_file_path}")

    processor = BatchProcessor(
        openai_api_key="YOUR_ACTUAL_OR_MOCK_KEY_IF_NEEDED_BY_SERVICE"
    )
    processor.process_directory(str(test_source_dir), str(test_output_dir))

    print("\nBatch Processor Test Finished.")

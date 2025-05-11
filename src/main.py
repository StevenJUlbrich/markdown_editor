# main.py
from app_controller import (
    AppController,
)  # Assuming app_controller.py is in the same directory


def main_cli():
    """
    Main command-line interface function for the Markdown Processor.
    """
    controller = AppController()
    document_is_loaded = False
    # Updated default document path based on user's latest file
    default_doc_path = "day_03_chapter_01_draft.md"

    while True:
        print("\n======= Markdown Processor CLI (Pydantic Model) =======")
        if (
            document_is_loaded
            and controller.doc_model
            and controller.doc_model.filepath
        ):
            print(f"Current Document: {controller.doc_model.filepath}")
        else:
            print("No document loaded.")
        print("-------------------------------------------------------")
        print("1. Load Document")
        print("2. View Document Structure (H2/H3/H4)")
        print("3. Get Specific Section Content (H2/H3/H4)")
        print("4. Prepare Multiple Sections for API (H2/H3/H4)")
        print("5. Modify Section Content (H3 Initial/H4)")
        print("6. Add Content to Section (H3 Initial/H4)")
        print(
            "7. Process API Enhancement for H3 Section"
        )  # New option for the API workflow
        print("8. Save Document")  # Changed number from 7 to 8
        print("0. Exit")
        print("-------------------------------------------------------")

        choice = input("Enter your choice: ")

        if choice == "1":
            filepath_to_load = (
                input(
                    f"Enter document filepath (or press Enter for '{default_doc_path}'): "
                )
                or default_doc_path
            )
            if controller.load_document(filepath_to_load):
                document_is_loaded = True
            else:
                document_is_loaded = False

        elif choice == "2":
            if document_is_loaded:
                print("\n--- Document Structure ---")
                print(controller.get_document_structure_view_with_h4())
                print("------------------------")
            else:
                print("Please load a document first (Option 1).")

        elif choice == "3":
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title fragment: ")
                h3_frag = (
                    input(
                        "Enter H3 Sub-section title fragment (optional, press Enter to target H2 Panel): "
                    )
                    or None
                )
                h4_frag = None
                if h3_frag:
                    h4_frag = (
                        input(
                            "Enter H4 Sub-sub-section title fragment (optional, press Enter to target H3's content): "
                        )
                        or None
                    )

                content = controller.get_specific_section_content_md(
                    panel_frag, h3_frag, h4_frag
                )
                print("\n--- Section Content ---")
                print(content)
                print("-----------------------")
            else:
                print("Please load a document first.")

        elif choice == "4":
            if document_is_loaded:
                sections_to_process_input = input(
                    "Enter sections to process, one per line (format: PanelTitle;H3Title;H4Title or PanelTitle;H3Title or PanelTitle).\n"
                    "Leave H3/H4 blank if not applicable. Press Enter on an empty line to finish:\n"
                )
                sections_to_process = []
                while True:
                    line = input("> ")
                    if not line:
                        break
                    parts = [p.strip() or None for p in line.split(";")]
                    if len(parts) == 1:
                        sections_to_process.append((parts[0], None, None))
                    elif len(parts) == 2:
                        sections_to_process.append((parts[0], parts[1], None))
                    elif len(parts) == 3:
                        sections_to_process.append((parts[0], parts[1], parts[2]))
                    else:
                        print("Invalid format. Use Panel;H3;H4 or Panel;H3 or Panel.")

                if sections_to_process:
                    print(f"\nPreparing sections: {sections_to_process}")
                    api_ready_data = controller.prepare_sections_for_api_v2(
                        sections_to_process
                    )
                    if api_ready_data:
                        print(
                            f"\n{len(api_ready_data)} sections prepared. Example data for first prepared section (if any):"
                        )
                        if api_ready_data:
                            first_item = api_ready_data[0]
                            target_level = "H2 Panel"
                            target_title = first_item.get("panel_title_fragment")
                            if first_item.get("h3_title_fragment"):
                                target_level = "H3 Sub-section"
                                target_title = first_item.get("h3_title_fragment")
                                if first_item.get("h4_title_fragment"):
                                    target_level = "H4 Sub-sub-section"
                                    target_title = first_item.get("h4_title_fragment")

                            print(
                                f"  Panel Context: {first_item.get('panel_title_fragment')}"
                            )
                            print(f"  Target Level: {target_level}")
                            print(f"  Target Title: {target_title}")
                            print(
                                f"  Content (first 50 chars): {first_item.get('content_to_send', '')[:50]}..."
                            )
                    else:
                        print("No sections were successfully prepared.")
                else:
                    print("No sections specified for API preparation.")
            else:
                print("Please load a document first.")

        elif choice == "5":
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title fragment to modify in: ")
                h3_frag = input("Enter H3 Sub-section title fragment to modify in: ")
                h4_frag = (
                    input(
                        "Enter H4 Sub-sub-section title fragment to modify (optional, press Enter to target H3's initial content): "
                    )
                    or None
                )

                if not h3_frag:
                    print("H3 sub-section must be specified for modification.")
                    continue

                print(
                    f"\nAttempting to get current content for Panel '{panel_frag}', H3 '{h3_frag}'"
                    + (f", H4 '{h4_frag}'" if h4_frag else "'s Initial Content")
                    + "..."
                )
                current_content = controller.get_specific_section_content_md(
                    panel_frag, h3_frag, h4_frag
                )
                print(f"Current content:\n{current_content}\n")

                new_md = input(
                    f"Enter NEW Markdown content (use \\n for newlines):\n"
                ).replace("\\n", "\n")
                controller.modify_section_content(panel_frag, h3_frag, new_md, h4_frag)
            else:
                print("Please load a document first.")

        elif choice == "6":
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title fragment to add to: ")
                h3_frag = input("Enter H3 Sub-section title fragment to add to: ")
                h4_frag = (
                    input(
                        "Enter H4 Sub-sub-section title fragment to add to (optional, press Enter to target H3's initial content): "
                    )
                    or None
                )

                if not h3_frag:
                    print("H3 sub-section must be specified for adding content.")
                    continue

                new_md = input(
                    f"Enter Markdown content to ADD (use \\n for newlines):\n"
                ).replace("\\n", "\n")
                position = (
                    input("Add at 'start' or 'end'? (default: end): ").strip().lower()
                    or "end"
                )
                controller.add_to_section_content(
                    panel_frag, h3_frag, new_md, position, h4_frag
                )
            else:
                print("Please load a document first.")

        elif choice == "7":  # Process API Enhancement for H3
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title for H3 enhancement: ")
                h3_frag = input("Enter H3 Sub-section title to enhance: ")

                # In a real scenario, the improved_markdown, recommendation, and reason
                # would come from an actual OpenAI API call. Here we simulate it.
                print(
                    f"\nSimulating API call for H3 '{h3_frag}' in Panel '{panel_frag}'."
                )
                print(
                    "Imagine OpenAI suggested an enhancement and provided new Markdown."
                )

                current_h3_content = controller.get_specific_section_content_md(
                    panel_frag, h3_frag, None
                )
                print(f"\nCurrent H3 ('{h3_frag}') Content:\n{current_h3_content}\n")

                sim_recommendation = input(
                    "Enter simulated API recommendation (e.g., 'Add Diagram'): "
                )
                sim_reason = input("Enter simulated API reason for recommendation: ")
                sim_improved_md = input(
                    f"Enter SIMULATED improved Markdown for H3 '{h3_frag}' (use \\n for newlines):\n"
                ).replace("\\n", "\n")

                controller.process_api_enhancements_for_h3(
                    panel_frag,
                    h3_frag,
                    sim_improved_md,
                    recommendation=sim_recommendation,
                    reason=sim_reason,
                )
                print(
                    "Note: The document model now holds this 'api_improved_markdown'. Save (Option 8) to see changes."
                )
            else:
                print("Please load a document first.")

        elif choice == "8":  # Save Document (was 7)
            if document_is_loaded:
                output_file = input(
                    "Enter output filepath (e.g., day_03_chapter_01_updated.md): "
                )
                if output_file:
                    controller.save_document(output_file)
                else:
                    print("Save cancelled: No output filepath provided.")
            else:
                print("Please load a document first.")

        elif choice == "0":
            print("Exiting Markdown Processor.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    print("Starting Markdown Processor CLI...")
    main_cli()

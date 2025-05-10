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
    default_doc_path = "chapter_01_draft.md"  # Default document to load

    while True:
        print("\n======= Markdown Processor CLI (H4 Support) =======")
        if (
            document_is_loaded
            and controller.doc_model
            and controller.doc_model.filepath
        ):
            print(f"Current Document: {controller.doc_model.filepath}")
        else:
            print("No document loaded.")
        print("-------------------------------------------------")
        print("1. Load Document (defaults to chapter_01_draft.md)")
        print("2. View Document Structure (with H4s)")
        print("3. Get Specific Section Content (H2/H3/H4)")
        print("4. Prepare Multiple Sections for API (targets H2/H3/H4)")
        print("5. Modify Section Content (H2/H3/H4)")
        print("6. Add Content to Section (H2/H3/H4)")
        print("7. Save Document")
        print("0. Exit")
        print("-------------------------------------------------")

        choice = input("Enter your choice: ")

        if choice == "1":
            filepath_to_load = (
                input(
                    f"Enter document filepath (or press Enter for '{default_doc_path}'): "
                )
                or default_doc_path
            )
            if controller.load_document(
                filepath_to_load
            ):  # This should call the model's load_and_process
                document_is_loaded = True
            else:
                document_is_loaded = False

        elif choice == "2":
            if document_is_loaded:
                print("\n--- Document Structure ---")
                # This controller method will need to be updated to format H4s
                print(controller.get_document_structure_view_with_h4())
                print("------------------------")
            else:
                print("Please load a document first (Option 1).")

        elif choice == "3":  # Get Specific Section Content
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title fragment: ")
                h3_frag = (
                    input(
                        "Enter H3 Sub-section title fragment (optional, press Enter to target H2 Panel): "
                    )
                    or None
                )
                h4_frag = None
                if h3_frag:  # Only ask for H4 if H3 is specified
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

        elif choice == "4":  # Prepare Multiple Sections for API
            if document_is_loaded:
                # Example sections to process.
                # Each tuple: (panel_frag, h3_frag or None, h4_frag or None)
                # If h3_frag is None, it targets the whole H2 Panel.
                # If h4_frag is None (but h3_frag is not), it targets the H3's initial content or the whole H3.
                sections_to_process = [
                    ("Panel 1", None, None),  # Targeting entire H2 "Panel 1"
                    ("Panel 1", "Scene Description", "Characters"),  # Targeting an H4
                    (
                        "Panel 1",
                        "Teaching Narrative",
                        None,
                    ),  # Targeting an H3's content
                    ("Panel 2", "Common Example", None),
                ]
                print(f"Preparing sections: {sections_to_process}")
                # Note: controller.prepare_sections_for_api_v2 will need to handle this new targeting logic
                api_ready_data = controller.prepare_sections_for_api_v2(
                    sections_to_process
                )
                if api_ready_data:
                    print(
                        f"\n{len(api_ready_data)} sections prepared. Example data for first prepared section (if any):"
                    )
                    if api_ready_data:  # Check again if list is not empty
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
                print("Please load a document first.")

        elif choice == "5":  # Modify Section Content
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title fragment to modify in: ")
                h3_frag = (
                    input(
                        "Enter H3 Sub-section title fragment to modify in (optional for H2 direct modification - NOT YET SUPPORTED): "
                    )
                    or None
                )  # H2 direct mod not supported yet
                h4_frag = None
                if h3_frag:
                    h4_frag = (
                        input(
                            "Enter H4 Sub-sub-section title fragment to modify (optional, press Enter to target H3's initial content): "
                        )
                        or None
                    )

                if not h3_frag:
                    print(
                        "Modification of entire H2 Panel content directly is not yet supported. Please specify an H3 section."
                    )
                    # Or implement logic to replace all content of an H2 panel
                    continue

                print(
                    f"\nAttempting to get current content for Panel '{panel_frag}', H3 '{h3_frag}'"
                    + (
                        f", H4 '{h4_frag}'"
                        if h4_frag
                        else ("'s Initial Content" if h3_frag else "")
                    )
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

        elif choice == "6":  # Add Content to Section
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title fragment to add to: ")
                h3_frag = (
                    input(
                        "Enter H3 Sub-section title fragment to add to (optional for H2 direct - NOT YET SUPPORTED): "
                    )
                    or None
                )  # H2 direct add not supported yet
                h4_frag = None
                if h3_frag:
                    h4_frag = (
                        input(
                            "Enter H4 Sub-sub-section title fragment to add to (optional, press Enter to target H3's initial content): "
                        )
                        or None
                    )

                if not h3_frag:
                    print(
                        "Adding content directly to H2 Panel (outside H3s) is not yet supported. Please specify an H3 section."
                    )
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

        elif choice == "7":  # Save Document
            if document_is_loaded:
                output_file = input(
                    "Enter output filepath (e.g., chapter_01_updated.md): "
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

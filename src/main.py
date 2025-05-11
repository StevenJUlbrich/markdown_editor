# main.py
from typing import Any, Dict, List, Optional

from app_controller import (
    AppController,
)  # Assuming app_controller.py is in the same directory


def display_numbered_list(
    items: List[Dict[str, Any]], title_key: str = "title", number_key: str = "number"
) -> None:
    """Helper to display a numbered list of items from a list of dictionaries."""
    if not items:
        print("No items to display.")
        return
    for item in items:
        # Ensure number_key and title_key exist, provide defaults if not
        num = item.get(
            number_key, item.get("display_number", "?")
        )  # Fallback for display_number
        title = item.get(title_key, "N/A")
        item_type = item.get("type", "")  # For targetable sections
        type_display = f" ({item_type})" if item_type else ""
        print(f"  {num}. {title}{type_display}")


def get_int_choice(prompt_text: str, max_val: Optional[int] = None) -> Optional[int]:
    """Helper to get an integer choice from the user."""
    while True:
        try:
            choice_str = input(prompt_text).strip()
            if not choice_str:  # Allow empty input to mean "cancel" or "none"
                return None
            choice_int = int(choice_str)
            if max_val is not None and not (0 < choice_int <= max_val):
                print(f"Please enter a number between 1 and {max_val}.")
                continue
            return choice_int
        except ValueError:
            print("Invalid input. Please enter a number.")


def main_cli():
    """
    Main command-line interface function for the Markdown Processor.
    """
    controller = AppController()
    document_is_loaded = False
    # Updated default document path based on user's latest file
    default_doc_path = "day_03_chapter_01_draft.md"

    while True:
        print("\n======= Markdown Processor CLI (Revised Flow) =======")
        if (
            document_is_loaded
            and controller.doc_model
            and controller.doc_model.filepath
        ):
            print(f"Current Document: {controller.doc_model.filepath}")
            if controller.current_selected_panel:
                print(
                    f"Currently Selected Panel: [{controller.current_selected_panel.panel_number_in_doc}] {controller.current_selected_panel.panel_title_text}"
                )
            else:
                print("No panel currently selected.")
        else:
            print("No document loaded.")
        print("----------------------------------------------------")
        print("--- Document Operations ---")
        print("1. Load Document")
        print("2. List All Document Sections (H1, Generic H2s, Panels)")
        print("3. List All Panels (by number & title)")
        print("4. Select Panel by Number (sets current panel context)")
        print("--- Operations on SELECTED Panel ---")
        print("5. View Content of Selected Panel (List H3s, then select H3 to print)")
        print("6. Prepare Sections in Current Panel for API")
        print("7. Modify/Add Content in Current Panel")
        print("--- Other ---")
        print("8. Process API Enhancement for Specific H3 (Manual Title Input)")
        print("9. Save Document")
        print("0. Exit")
        print("----------------------------------------------------")

        choice = input("Enter your choice: ")

        if choice == "1":  # Load Document
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

        elif choice == "2":  # List All Document Sections
            if document_is_loaded:
                print("\n--- All Document H2-Level Sections ---")
                sections = controller.list_all_h2_sections_for_cli()
                if sections:
                    display_numbered_list(
                        sections, title_key="title", number_key="number"
                    )
            else:
                print("Please load a document first.")

        elif choice == "3":  # List All Panels
            if document_is_loaded:
                print("\n--- All Panels ---")
                panels = controller.list_panels_for_cli()
                if panels:
                    # Need to format for display_numbered_list or print directly
                    for i, p_obj in enumerate(panels):
                        print(
                            f"  {p_obj.panel_number_in_doc}. {p_obj.panel_title_text}"
                        )
                else:
                    print("No panels found in the document.")
            else:
                print("Please load a document first.")

        elif choice == "4":  # Select Panel by Number
            if document_is_loaded:
                panel_num_str = input("Enter Panel number to select: ")
                try:
                    panel_num = int(panel_num_str)
                    if not controller.select_panel_by_number_for_cli(panel_num):
                        print(
                            f"Panel number {panel_num} could not be selected or found."
                        )
                except ValueError:
                    print("Invalid panel number.")
            else:
                print("Please load a document first.")

        elif choice == "5":  # View Content of Selected Panel
            if document_is_loaded and controller.current_selected_panel:
                print(
                    f"\n--- H3 Sections in Panel: {controller.current_selected_panel.panel_title_text} ---"
                )
                h3_options = controller.list_h3_sections_in_selected_panel_for_cli()
                if h3_options:
                    display_numbered_list(
                        h3_options, title_key="title", number_key="number"
                    )
                    h3_choice = get_int_choice(
                        "Enter H3 number to pretty print (or Enter to skip): ",
                        len(h3_options),
                    )
                    if h3_choice is not None:
                        content = controller.list_and_get_h3_content_for_cli(h3_choice)
                        print("\n--- Full H3 Section Content (inc. H4s) ---")
                        print(content if content else "No content found or error.")
                        print("------------------------------------------")
                else:
                    print("No H3 sections in the selected panel.")
            elif not document_is_loaded:
                print("Please load a document first.")
            else:
                print("Please select a Panel first (Option 4).")

        elif choice == "6":  # Prepare Sections in Current Panel for API
            if document_is_loaded and controller.current_selected_panel:
                print(
                    f"\n--- Targetable Sections in Panel: {controller.current_selected_panel.panel_title_text} ---"
                )
                targetable_sections = (
                    controller.list_targetable_sections_in_selected_panel_for_cli()
                )
                if targetable_sections:
                    display_numbered_list(
                        targetable_sections,
                        title_key="title",
                        number_key="display_number",
                    )
                    numbers_str = input(
                        "Enter comma-separated numbers of sections to prep for API: "
                    )
                    try:
                        selected_display_numbers = [
                            int(n.strip()) for n in numbers_str.split(",") if n.strip()
                        ]
                        if selected_display_numbers:
                            api_ready_data = (
                                controller.prepare_multiple_selected_sections_for_api(
                                    selected_display_numbers
                                )
                            )
                            # Display summary or details of api_ready_data
                            if api_ready_data:
                                print(
                                    f"\n{len(api_ready_data)} sections prepared. Example data for first prepared section (if any):"
                                )
                                if api_ready_data:
                                    first_item = api_ready_data[0]
                                    print(
                                        f"  Target: [{first_item.get('type')}] {first_item.get('title')}"
                                    )
                                    print(
                                        f"  Content (first 50 chars): {first_item.get('content_to_send', '')[:50]}..."
                                    )
                        else:
                            print("No section numbers entered.")
                    except ValueError:
                        print("Invalid input. Please enter comma-separated numbers.")
                else:
                    print("No targetable sections found in the selected panel.")
            elif not document_is_loaded:
                print("Please load a document first.")
            else:
                print("Please select a Panel first (Option 4).")

        elif choice == "7":  # Modify/Add Content in Current Panel
            if document_is_loaded and controller.current_selected_panel:
                print(
                    f"\n--- Targetable Sections for Modification in Panel: {controller.current_selected_panel.panel_title_text} ---"
                )
                targetable_sections = (
                    controller.list_targetable_sections_in_selected_panel_for_cli()
                )  # This populates controller.last_listed_targetable_sections
                if targetable_sections:
                    display_numbered_list(
                        targetable_sections,
                        title_key="title",
                        number_key="display_number",
                    )
                    section_choice = get_int_choice(
                        "Enter number of section to modify/add to: ",
                        len(targetable_sections),
                    )
                    if section_choice is not None:
                        action_choice = (
                            input(
                                "Action: 'replace' current content, or 'add start', 'add end'? (default: replace): "
                            )
                            .strip()
                            .lower()
                            or "replace"
                        )
                        new_md = input(
                            f"Enter Markdown content (use \\n for newlines):\n"
                        ).replace("\\n", "\n")

                        if action_choice == "replace":
                            controller.update_target_section_content(
                                section_choice, new_md
                            )
                        elif action_choice in ["add start", "add end"]:
                            pos = "start" if action_choice == "add start" else "end"
                            controller.add_to_target_section_content(
                                section_choice, new_md, pos
                            )
                        else:
                            print("Invalid action choice.")
                else:
                    print("No targetable sections found to modify.")
            elif not document_is_loaded:
                print("Please load a document first.")
            else:
                print("Please select a Panel first (Option 4).")

        elif choice == "8":  # Process API Enhancement for Specific H3
            if document_is_loaded:
                panel_frag = input("Enter Panel (H2) title for H3 enhancement: ")
                h3_frag = input("Enter H3 Sub-section title to enhance: ")

                print(
                    f"\nSimulating API call for H3 '{h3_frag}' in Panel '{panel_frag}'."
                )

                # Get current content to show user (optional, but helpful)
                # This requires a controller method that can get H3 content by title directly
                # For simplicity, we'll skip showing current content here and assume user knows.
                # Or, the controller method for API enhancement could fetch it.

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
                    "Note: The document model now holds this 'api_improved_markdown'. Save (Option 9) to see changes."
                )
            else:
                print("Please load a document first.")

        elif choice == "9":  # Save Document
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

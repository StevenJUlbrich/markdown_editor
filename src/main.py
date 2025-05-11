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
        print("  No items to display.")
        return
    for item in items:
        num = item.get(number_key, item.get("display_number", "?"))
        title = item.get(title_key, "N/A")
        item_type = item.get("type", "")
        type_display = f" ({item_type})" if item_type else ""
        id_info = []
        if item.get("panel_id") is not None:
            id_info.append(f"P:{item['panel_id']}")
        if item.get("h3_id") is not None:
            id_info.append(f"H3:{item['h3_id']}")
        if item.get("h4_id") is not None:
            id_info.append(f"H4:{item['h4_id']}")
        id_display = f" [{', '.join(id_info)}]" if id_info else ""

        # For list_all_h2_sections, the 'id' field can be the panel_number_in_doc or a generic title
        raw_id = item.get("id")
        if (
            raw_id is not None and not id_info and not item_type
        ):  # Likely from list_all_h2_sections
            id_display = f" [RawID: {raw_id}]"

        print(f"  {num}. {title}{type_display}{id_display}")


def get_int_choice(
    prompt_text: str, max_val: Optional[int] = None, min_val: int = 1
) -> Optional[int]:
    """Helper to get an integer choice from the user."""
    while True:
        try:
            choice_str = input(prompt_text).strip()
            if not choice_str:
                return None
            choice_int = int(choice_str)
            if max_val is not None and not (min_val <= choice_int <= max_val):
                print(f"  Please enter a number between {min_val} and {max_val}.")
                continue
            if choice_int < min_val:
                print(f"  Please enter a number greater than or equal to {min_val}.")
                continue
            return choice_int
        except ValueError:
            print("  Invalid input. Please enter a number.")


def main_cli():
    """
    Main command-line interface function for the Markdown Processor.
    Utilizes numeric IDs for section targeting.
    """
    controller = AppController()
    document_is_loaded = False
    default_doc_path = "day_03_chapter_01_draft.md"

    while True:
        print("\n======= Markdown Processor CLI (Numeric IDs) =======")
        if (
            document_is_loaded
            and controller.doc_model
            and controller.doc_model.filepath
        ):
            print(f"Current Document: {controller.doc_model.filepath}")
            selected_panel_title = controller.get_current_selected_panel_title()
            if selected_panel_title:
                print(
                    f"Currently Selected Panel: [ID:{controller.current_selected_panel_id}] {selected_panel_title}"
                )
            else:
                print("No panel currently selected.")
        else:
            print("No document loaded.")
        print("----------------------------------------------------")
        print("--- Document Operations ---")
        print("1. Load Document")
        print("2. List All Document Sections (Generic & Panel H2s)")
        print("3. List All Panels (by their document number)")
        print("4. Select Panel by its Document Number")
        print("--- Operations on SELECTED Panel ---")
        print("5. View H3 Sections in Selected Panel (then view H3 content)")
        print("6. Prepare Targetable Sections in Selected Panel for API")
        print("7. Modify/Add Content in Selected Panel (Target by Display #)")
        print("--- Other ---")
        print("8. Process API Enhancement for Specific H3 (Select Panel & H3 by #)")
        print("9. Save Document")
        print("0. Exit")
        print("----------------------------------------------------")

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
                print("\n--- All Document H2-Level Sections ---")
                sections = controller.list_all_h2_sections_for_cli()
                display_numbered_list(sections, title_key="title", number_key="number")
            else:
                print("  Please load a document first.")

        elif choice == "3":
            if document_is_loaded:
                print("\n--- All Panels ---")
                panels = (
                    controller.list_panels_for_cli()
                )  # Returns list of PanelPydantic objects
                if panels:
                    for panel_obj in panels:
                        print(
                            f"  Panel Doc #: {panel_obj.panel_number_in_doc}. {panel_obj.panel_title_text}"
                        )
                else:
                    print("  No panels found in the document.")
            else:
                print("  Please load a document first.")

        elif choice == "4":
            if document_is_loaded:
                panel_doc_num = get_int_choice(
                    "Enter Panel Document Number to select: "
                )
                if panel_doc_num is not None:
                    if not controller.select_panel_by_number_for_cli(panel_doc_num):
                        print(
                            f"  Panel with Document Number {panel_doc_num} could not be selected or found."
                        )
                else:
                    print("  Panel selection cancelled.")
            else:
                print("  Please load a document first.")

        elif choice == "5":
            if document_is_loaded and controller.current_selected_panel_id is not None:
                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- H3 Sections in Panel ID {controller.current_selected_panel_id} ('{panel_title}') ---"
                )
                h3_options = (
                    controller.list_h3_sections_in_selected_panel_for_cli()
                )  # Gets list of {"number": h3_id, "title":...}
                if h3_options:
                    display_numbered_list(
                        h3_options, title_key="title", number_key="number"
                    )  # "number" is h3_number_in_panel
                    h3_selection_num = get_int_choice(
                        "Enter H3 number (from list above) to view its content (or Enter to skip): ",
                        len(h3_options),
                    )
                    if h3_selection_num is not None:
                        # The 'number' in h3_options IS the h3_number_in_panel
                        selected_h3_data = next(
                            (
                                h3
                                for h3 in h3_options
                                if h3.get("number") == h3_selection_num
                            ),
                            None,
                        )
                        if selected_h3_data:
                            content = controller.list_and_get_h3_content_for_cli(
                                selected_h3_data["number"]
                            )  # Pass h3_number_in_panel
                            print("\n--- Full H3 Section Content (inc. H4s) ---")
                            print(
                                content if content else "  No content found or error."
                            )
                            print("------------------------------------------")
                        else:
                            print(f"  Invalid H3 selection.")
                else:
                    print("  No H3 sections in the selected panel.")
            elif not document_is_loaded:
                print("  Please load a document first.")
            else:
                print("  Please select a Panel first (Option 4).")

        elif choice == "6":
            if document_is_loaded and controller.current_selected_panel_id is not None:
                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- Targetable Sections in Panel ID {controller.current_selected_panel_id} ('{panel_title}') ---"
                )
                targetable_sections = (
                    controller.list_targetable_sections_in_selected_panel_for_cli()
                )
                if targetable_sections:  # This list now has panel_id, h3_id, h4_id
                    display_numbered_list(
                        targetable_sections,
                        title_key="title",
                        number_key="display_number",
                    )
                    numbers_str = input(
                        "Enter comma-separated display numbers of sections to prep for API: "
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
                            if api_ready_data:
                                print(
                                    f"\n  {len(api_ready_data)} sections prepared. Example for first:"
                                )
                                if api_ready_data:
                                    first_item = api_ready_data[0]
                                    print(
                                        f"    Target Type: {first_item.get('type')}, Title: {first_item.get('title')}"
                                    )
                                    print(
                                        f"    Content (first 50 chars): {first_item.get('content_to_send', '')[:50]}..."
                                    )
                        else:
                            print("  No section numbers entered.")
                    except ValueError:
                        print("  Invalid input. Please enter comma-separated numbers.")
                else:
                    print("  No targetable sections found in the selected panel.")
            elif not document_is_loaded:
                print("  Please load a document first.")
            else:
                print("  Please select a Panel first (Option 4).")

        elif choice == "7":
            if document_is_loaded and controller.current_selected_panel_id is not None:
                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- Targetable Sections for Modification in Panel ID {controller.current_selected_panel_id} ('{panel_title}') ---"
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
                    section_display_num = get_int_choice(
                        "Enter display number of section to modify/add to: ",
                        len(targetable_sections),
                    )
                    if section_display_num is not None:
                        action_choice = (
                            input(
                                "  Action: 'replace' current content, or 'add start', 'add end'? (default: replace): "
                            )
                            .strip()
                            .lower()
                            or "replace"
                        )
                        new_md = input(
                            f"  Enter Markdown content (use \\n for newlines):\n"
                        ).replace("\\n", "\n")

                        if action_choice == "replace":
                            controller.update_target_section_content(
                                section_display_num, new_md
                            )
                        elif action_choice in ["add start", "add end"]:
                            pos = "start" if action_choice == "add start" else "end"
                            controller.add_to_target_section_content(
                                section_display_num, new_md, pos
                            )
                        else:
                            print("  Invalid action choice.")
                else:
                    print("  No targetable sections found to modify.")
            elif not document_is_loaded:
                print("  Please load a document first.")
            else:
                print("  Please select a Panel first (Option 4).")

        elif choice == "8":
            if document_is_loaded:
                print("\n--- Process API Enhancement for H3 Section ---")
                panel_doc_num = get_int_choice(
                    "Enter Panel Document Number containing the H3: "
                )
                if panel_doc_num is None:
                    print("Cancelled.")
                    continue

                # Temporarily select panel to list its H3s
                original_selected_panel_id = controller.current_selected_panel_id
                if not controller.select_panel_by_number_for_cli(panel_doc_num):
                    controller.current_selected_panel_id = (
                        original_selected_panel_id  # Restore
                    )
                    continue

                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- H3 Sections in Panel ID {panel_doc_num} ('{panel_title}') ---"
                )
                h3_options = controller.list_h3_sections_in_selected_panel_for_cli()
                if not h3_options:
                    print(f"  No H3 sections in Panel ID {panel_doc_num}.")
                    controller.current_selected_panel_id = (
                        original_selected_panel_id  # Restore
                    )
                    continue

                display_numbered_list(
                    h3_options, title_key="title", number_key="number"
                )
                h3_selection_num = get_int_choice(
                    "Enter H3 number (from list above) to enhance: ", len(h3_options)
                )

                controller.current_selected_panel_id = (
                    original_selected_panel_id  # Restore original selection
                )

                if h3_selection_num is not None:
                    selected_h3_data = next(
                        (
                            h3
                            for h3 in h3_options
                            if h3.get("number") == h3_selection_num
                        ),
                        None,
                    )
                    if selected_h3_data:
                        h3_id_in_panel = selected_h3_data[
                            "number"
                        ]  # This is h3_number_in_panel
                        h3_title_for_prompt = selected_h3_data["title"]

                        print(
                            f"\nSimulating API call for Panel ID {panel_doc_num}, H3 ID {h3_id_in_panel} ('{h3_title_for_prompt}')."
                        )
                        current_h3_content = (
                            controller.doc_model.get_section_markdown_for_api(
                                panel_id=panel_doc_num, h3_id_in_panel=h3_id_in_panel
                            )
                        )  # Get current content
                        print(f"\nCurrent H3 Content:\n{current_h3_content}\n")

                        sim_recommendation = input(
                            "  Enter simulated API recommendation (e.g., 'Add Diagram'): "
                        )
                        sim_reason = input("  Enter simulated API reason: ")
                        sim_improved_md = input(
                            f"  Enter SIMULATED improved Markdown for H3 '{h3_title_for_prompt}' (use \\n for newlines):\n"
                        ).replace("\\n", "\n")

                        controller.process_api_enhancements_for_h3(
                            panel_doc_num,
                            h3_id_in_panel,
                            sim_improved_md,
                            recommendation=sim_recommendation,
                            reason=sim_reason,
                        )
                        print(
                            "  Note: The document model now holds this 'api_improved_markdown'. Save (Option 9) to see changes."
                        )
                    else:
                        print(f"  Invalid H3 selection.")
                else:
                    print("  H3 enhancement cancelled.")
            else:
                print("  Please load a document first.")

        elif choice == "9":
            if document_is_loaded:
                output_file = input(
                    "Enter output filepath (e.g., day_03_chapter_01_updated.md): "
                )
                if output_file:
                    controller.save_document(output_file)
                else:
                    print("  Save cancelled: No output filepath provided.")
            else:
                print("  Please load a document first.")

        elif choice == "0":
            print("Exiting Markdown Processor.")
            break

        else:
            print("  Invalid choice. Please try again.")


if __name__ == "__main__":
    print("Starting Markdown Processor CLI...")
    main_cli()

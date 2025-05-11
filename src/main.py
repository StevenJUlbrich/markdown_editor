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
    for item_idx, item in enumerate(
        items
    ):  # Use enumerate for consistent 1-based display if 'number' key is missing
        # Prioritize 'display_number', then 'number', then 1-based index
        num_to_display = item.get("display_number", item.get(number_key, item_idx + 1))

        title = item.get(title_key, "N/A")
        item_type = item.get("type", "")
        type_display = f" ({item_type})" if item_type else ""

        id_info = []
        if item.get("panel_id") is not None:
            id_info.append(f"P_ID:{item['panel_id']}")
        if item.get("h3_id") is not None:
            id_info.append(
                f"H3_ID:{item['h3_id']}"
            )  # Changed from H3 to H3_ID for clarity
        if item.get("h4_id") is not None:
            id_info.append(
                f"H4_ID:{item['h4_id']}"
            )  # Changed from H4 to H4_ID for clarity
        id_display = f" [{', '.join(id_info)}]" if id_info else ""

        # Handle 'id' from list_all_h2_sections which might be panel_number_in_doc or generic title
        raw_id = item.get("id")
        if raw_id is not None and not id_info and not item_type:
            id_display = f" [DocID: {raw_id}]"  # Clarified RawID to DocID for panels

        print(f"  {num_to_display}. {title}{type_display}{id_display}")


def get_int_choice(
    prompt_text: str, max_val: Optional[int] = None, min_val: int = 1
) -> Optional[int]:
    """Helper to get an integer choice from the user."""
    while True:
        try:
            choice_str = input(prompt_text).strip()
            if not choice_str:
                return None  # Allow empty input to cancel
            choice_int = int(choice_str)
            if max_val is not None and not (min_val <= choice_int <= max_val):
                print(
                    f"  Invalid input. Please enter a number between {min_val} and {max_val}."
                )
                continue
            # This check is redundant if max_val is handled, but good for clarity if max_val is None
            if choice_int < min_val:
                print(
                    f"  Invalid input. Please enter a number greater than or equal to {min_val}."
                )
                continue
            return choice_int
        except ValueError:
            print(
                "  Invalid input. Please enter a whole number."
            )  # More specific error


def main_cli():
    """
    Main command-line interface function for the Markdown Processor.
    Utilizes numeric IDs for section targeting and provides improved user feedback.
    """
    controller = AppController()
    document_is_loaded = False
    default_doc_path = "day_03_chapter_01_draft.md"

    main_menu_options_count = 11  # Options 0 through 11

    while True:
        print("\n======= Markdown Processor CLI (Improved Feedback v2) =======")
        if (
            document_is_loaded
            and controller.doc_model
            and controller.doc_model.filepath
        ):
            print(f"Current Document: {controller.doc_model.filepath}")
            selected_panel_title = controller.get_current_selected_panel_title()
            if (
                selected_panel_title
                and controller.current_selected_panel_id is not None
            ):  # Check ID too
                print(
                    f"Currently Selected Panel: [ID:{controller.current_selected_panel_id}] {selected_panel_title}"
                )
            else:
                print("No panel currently selected.")
        else:
            print("No document loaded.")
        print("-----------------------------------------------------------------")
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
        print("9. View Diff for API-Improved H3 Section")
        print("10. Export Document Structure to JSON")
        print("11. Save Document")
        print("0. Exit")
        print("-----------------------------------------------------------------")

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
                # Controller prints success/failure, so main.py doesn't need to repeat as much
            else:
                document_is_loaded = False

        elif choice == "2":
            if document_is_loaded:
                print("\n--- All Document Top-Level Sections (Generic & Panels) ---")
                sections = controller.list_all_h2_sections_for_cli()
                # display_numbered_list will print "No items to display." if sections is empty or None
                display_numbered_list(sections, title_key="title", number_key="number")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "3":
            if document_is_loaded:
                print("\n--- All Panels (Selectable by Document Number) ---")
                panels = controller.list_panels_for_cli()
                if panels:
                    for panel_obj in panels:
                        print(
                            f"  Panel Doc #: {panel_obj.panel_number_in_doc}. {panel_obj.panel_title_text}"
                        )
                else:
                    print("  No panels found in the document.")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "4":
            if document_is_loaded:
                panels = controller.list_panels_for_cli()
                if not panels:
                    print("  No panels available in the document to select.")
                    continue

                print("\n--- Available Panels for Selection ---")
                for panel_obj in panels:
                    print(
                        f"  Panel Doc #: {panel_obj.panel_number_in_doc}. {panel_obj.panel_title_text}"
                    )

                panel_doc_num = get_int_choice(
                    "Enter Panel Document Number to select (or Enter to cancel): "
                )
                if panel_doc_num is not None:
                    if not controller.select_panel_by_number_for_cli(panel_doc_num):
                        print(
                            f"  Error: Panel with Document Number {panel_doc_num} could not be selected or was not found."
                        )
                    # Success message is printed by controller's select_panel_by_number_for_cli
                else:
                    print("  Panel selection cancelled.")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "5":
            if document_is_loaded and controller.current_selected_panel_id is not None:
                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- H3 Sections in Selected Panel [ID:{controller.current_selected_panel_id}] ('{panel_title}') ---"
                )
                h3_options = controller.list_h3_sections_in_selected_panel_for_cli()
                if h3_options:  # display_numbered_list handles empty case
                    # "number" key in h3_options is h3_number_in_panel
                    display_numbered_list(
                        h3_options, title_key="title", number_key="number"
                    )

                    # Use h3_list_selection_number for clarity that it's an index to the list, not the ID itself
                    h3_list_selection_number = get_int_choice(
                        "Enter H3 list number (from above) to view its content (or Enter to skip): ",
                        max_val=len(h3_options),
                    )
                    if h3_list_selection_number is not None:
                        # The controller's list_and_get_h3_content_for_cli expects the list selection number
                        content = controller.list_and_get_h3_content_for_cli(
                            h3_list_selection_number
                        )
                        print("\n--- Full H3 Section Content (inc. H4s if any) ---")
                        print(
                            content
                            if content
                            else "  No content found or error retrieving content for this H3."
                        )
                        print("-------------------------------------------------")
                # display_numbered_list already handles "No items to display" if h3_options is empty
            elif not document_is_loaded:
                print("  Please load a document first (Option 1).")
            else:
                print("  Please select a Panel first (Option 4).")

        elif choice == "6":
            if document_is_loaded and controller.current_selected_panel_id is not None:
                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- Targetable Sections in Selected Panel [ID:{controller.current_selected_panel_id}] ('{panel_title}') ---"
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
                        "Enter comma-separated display numbers of sections to prep for API (e.g., 1,3,4): "
                    )
                    try:
                        selected_display_numbers = [
                            int(n.strip()) for n in numbers_str.split(",") if n.strip()
                        ]
                        if selected_display_numbers:
                            max_display_num = len(targetable_sections)
                            valid_selections = [
                                num
                                for num in selected_display_numbers
                                if 0 < num <= max_display_num
                            ]
                            invalid_selections = [
                                num
                                for num in selected_display_numbers
                                if not (0 < num <= max_display_num)
                            ]
                            if invalid_selections:
                                print(
                                    f"  Warning: Invalid display numbers skipped: {invalid_selections}. Please choose from 1 to {max_display_num}."
                                )

                            if valid_selections:
                                api_ready_data = controller.prepare_multiple_selected_sections_for_api(
                                    valid_selections
                                )
                                if api_ready_data:
                                    print(
                                        f"\n  {len(api_ready_data)} sections prepared. Example for first:"
                                    )
                                    first_item = api_ready_data[0]
                                    print(
                                        f"    Target Type: {first_item.get('type')}, Title: {first_item.get('title')}"
                                    )
                                    print(
                                        f"    Content (first 50 chars): {first_item.get('content_to_send', '')[:50]}..."
                                    )
                                else:  # This case implies valid_selections were made, but prepare_multiple failed for all.
                                    print(
                                        "  No sections were successfully prepared (e.g., content retrieval failed for all valid selections)."
                                    )
                            elif (
                                not invalid_selections
                            ):  # No valid selections and no invalid ones means empty input after parsing
                                print(
                                    "  No section numbers entered or all were invalid."
                                )
                        else:  # Empty list from numbers_str.split(',')
                            print("  No section numbers entered.")
                    except ValueError:
                        print(
                            "  Invalid input. Please enter comma-separated numbers (e.g., 1,3,4)."
                        )
                # display_numbered_list handles empty targetable_sections
            elif not document_is_loaded:
                print("  Please load a document first (Option 1).")
            else:
                print("  Please select a Panel first (Option 4).")

        elif choice == "7":
            if document_is_loaded and controller.current_selected_panel_id is not None:
                panel_title = controller.get_current_selected_panel_title()
                print(
                    f"\n--- Targetable Sections for Modification in Selected Panel [ID:{controller.current_selected_panel_id}] ('{panel_title}') ---"
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
                        "Enter display number of section to modify/add to (or Enter to cancel): ",
                        len(targetable_sections),
                    )
                    if section_display_num is not None:
                        target_info = controller._get_target_info_from_display_number(
                            section_display_num
                        )
                        if (
                            target_info
                        ):  # Should always be true if section_display_num is valid
                            print(
                                f"\n--- Current content of '{target_info.get('title')}' (Type: {target_info.get('type')}) ---"
                            )
                            # Fetch content using the controller method that uses numeric IDs from target_info
                            current_content = (
                                controller.doc_model.get_section_markdown_for_api(
                                    panel_id=target_info["panel_id"],
                                    h3_id_in_panel=target_info.get("h3_id"),
                                    h4_id_in_h3=target_info.get("h4_id"),
                                    is_initial_content_target=target_info.get(
                                        "is_initial_content_for_h3", False
                                    ),
                                )
                            )
                            print(
                                current_content
                                if current_content
                                and not current_content.startswith("Error:")
                                else "  (No current content or error retrieving)"
                            )
                            print("--------------------------------------------------")

                        action_choice = (
                            input(
                                "  Action: 'replace' current content, or 'add start', 'add end'? (default: replace): "
                            )
                            .strip()
                            .lower()
                            or "replace"
                        )
                        if action_choice not in ["replace", "add start", "add end"]:
                            print(
                                "  Invalid action. Valid actions are: 'replace', 'add start', 'add end'."
                            )
                            continue

                        new_md = input(
                            f"  Enter Markdown content for '{action_choice}' (use \\n for newlines):\n"
                        ).replace("\\n", "\n")

                        success = False
                        if action_choice == "replace":
                            success = controller.update_target_section_content(
                                section_display_num, new_md
                            )
                            if success:
                                print("  Content replaced successfully.")
                            else:
                                print("  Failed to replace content.")
                        elif action_choice in ["add start", "add end"]:
                            pos = "start" if action_choice == "add start" else "end"
                            success = controller.add_to_target_section_content(
                                section_display_num, new_md, pos
                            )
                            if success:
                                print(f"  Content added to {pos} successfully.")
                            else:
                                print(f"  Failed to add content to {pos}.")
                    else:  # User pressed Enter at get_int_choice
                        print("  Modification/addition cancelled.")
                # display_numbered_list handles empty targetable_sections
            elif not document_is_loaded:
                print("  Please load a document first (Option 1).")
            else:
                print("  Please select a Panel first (Option 4).")

        elif choice == "8":
            if document_is_loaded:
                print("\n--- Process API Enhancement for Specific H3 Section ---")
                panels = controller.list_panels_for_cli()
                if not panels:
                    print("  No panels in document to select from.")
                    continue

                print("Available Panels:")
                for p_obj in panels:
                    print(
                        f"  Panel Doc #: {p_obj.panel_number_in_doc}. {p_obj.panel_title_text}"
                    )
                panel_doc_num = get_int_choice(
                    "Enter Panel Document Number for the H3 (or Enter to cancel): "
                )
                if panel_doc_num is None:
                    print("  API enhancement cancelled.")
                    continue

                # Temporarily select panel to list its H3s
                original_selected_panel_id = controller.current_selected_panel_id
                if not controller.select_panel_by_number_for_cli(panel_doc_num):
                    controller.current_selected_panel_id = original_selected_panel_id
                    continue

                panel_title_for_display = controller.get_current_selected_panel_title()
                print(
                    f"\n--- H3 Sections in Selected Panel [ID:{panel_doc_num}] ('{panel_title_for_display}') ---"
                )
                h3_options = controller.list_h3_sections_in_selected_panel_for_cli()
                if not h3_options:
                    print(f"  No H3 sections in Panel ID {panel_doc_num}.")
                    controller.current_selected_panel_id = original_selected_panel_id
                    continue

                display_numbered_list(
                    h3_options, title_key="title", number_key="number"
                )
                h3_list_selection_number = get_int_choice(
                    "Enter H3 list number (from above) to enhance (or Enter to cancel): ",
                    len(h3_options),
                )

                controller.current_selected_panel_id = (
                    original_selected_panel_id  # Restore original selection
                )

                if h3_list_selection_number is not None:
                    selected_h3_data = next(
                        (
                            h3
                            for idx, h3 in enumerate(h3_options)
                            if idx + 1 == h3_list_selection_number
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
                        )
                        print(
                            f"\nCurrent H3 Content:\n{current_h3_content if current_h3_content else '  (No content or error retrieving)'}\n"
                        )

                        sim_recommendation = input(
                            "  Enter simulated API recommendation (e.g., 'Add Diagram'): "
                        )
                        sim_reason = input("  Enter simulated API reason: ")
                        sim_improved_md = input(
                            f"  Enter SIMULATED improved Markdown for H3 '{h3_title_for_prompt}' (use \\n for newlines):\n"
                        ).replace("\\n", "\n")

                        if controller.process_api_enhancements_for_h3(
                            panel_doc_num,
                            h3_id_in_panel,
                            sim_improved_md,
                            recommendation=sim_recommendation,
                            reason=sim_reason,
                        ):
                            print(
                                "  API enhancement processed successfully (simulated)."
                            )
                        else:
                            print("  API enhancement processing failed (simulated).")
                        print(
                            "  Note: The document model now holds this 'api_improved_markdown'. Save (Option 11) to see changes."
                        )
                    else:
                        print(f"  Invalid H3 selection from list.")
                else:
                    print("  H3 enhancement cancelled.")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "9":
            if document_is_loaded:
                print("\n--- View Diff for API-Improved H3 Section ---")
                panels = controller.list_panels_for_cli()
                if not panels:
                    print("  No panels in document to select from.")
                    continue
                print("Available Panels:")
                for p_obj in panels:
                    print(
                        f"  Panel Doc #: {p_obj.panel_number_in_doc}. {p_obj.panel_title_text}"
                    )

                panel_doc_num = get_int_choice(
                    "Enter Panel Document Number for the H3 (or Enter to cancel): "
                )
                if panel_doc_num is None:
                    print("  Diff view cancelled.")
                    continue

                original_selected_panel_id = controller.current_selected_panel_id
                if not controller.select_panel_by_number_for_cli(panel_doc_num):
                    controller.current_selected_panel_id = original_selected_panel_id
                    continue

                panel_title_for_display = controller.get_current_selected_panel_title()
                print(
                    f"\n--- H3 Sections in Selected Panel [ID:{panel_doc_num}] ('{panel_title_for_display}') ---"
                )
                h3_options = controller.list_h3_sections_in_selected_panel_for_cli()
                if not h3_options:
                    print(f"  No H3 sections in Panel ID {panel_doc_num}.")
                    controller.current_selected_panel_id = original_selected_panel_id
                    continue

                display_numbered_list(
                    h3_options, title_key="title", number_key="number"
                )
                h3_list_selection_number = get_int_choice(
                    "Enter H3 list number (from above) to view diff for (or Enter to cancel): ",
                    len(h3_options),
                )

                controller.current_selected_panel_id = original_selected_panel_id

                if h3_list_selection_number is not None:
                    selected_h3_data = next(
                        (
                            h3
                            for idx, h3 in enumerate(h3_options)
                            if idx + 1 == h3_list_selection_number
                        ),
                        None,
                    )
                    if selected_h3_data:
                        h3_id_in_panel = selected_h3_data[
                            "number"
                        ]  # Actual h3_number_in_panel
                        diff_text = controller.get_h3_section_diff_text(
                            panel_doc_num, h3_id_in_panel
                        )
                        if diff_text:
                            print(
                                f"\n--- Diff for H3: {selected_h3_data['title']} (Panel ID {panel_doc_num}, H3 ID {h3_id_in_panel}) ---"
                            )
                            print(
                                diff_text
                            )  # Diff util should handle "identical" message
                            print("--------------------------------------------------")
                        # else: controller method prints detailed messages for errors or no diff
                    else:
                        print("  Invalid H3 selection from list.")
                else:
                    print("  Diff view cancelled.")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "10":
            if document_is_loaded:
                print("\n--- Exporting Document Structure to JSON ---")
                json_output = controller.get_chapter_model_as_json()
                if json_output:
                    print(json_output)
                    save_to_file = input(
                        "  Save to file? (e.g., structure.json, press Enter to skip): "
                    ).strip()
                    if save_to_file:
                        try:
                            with open(save_to_file, "w", encoding="utf-8") as f:
                                f.write(json_output)
                            print(f"  Successfully saved to {save_to_file}")
                        except Exception as e:
                            print(f"  Error saving JSON to file: {e}")
                else:
                    # Controller method already prints error if JSON couldn't be generated
                    pass
                print("------------------------------------------")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "11":
            if document_is_loaded:
                output_file = input(
                    "Enter output filepath (e.g., day_03_chapter_01_updated.md): "
                )
                if output_file:
                    if controller.save_document(output_file):
                        # Success message printed by controller
                        pass
                    else:
                        # Failure message printed by controller
                        pass
                else:
                    print("  Save cancelled: No output filepath provided.")
            else:
                print("  Please load a document first (Option 1).")

        elif choice == "0":
            print("Exiting Markdown Processor.")
            break

        else:
            print(
                f"  Invalid choice '{choice}'. Please enter a number between 0 and {main_menu_options_count}."
            )


if __name__ == "__main__":
    print("Starting Markdown Processor CLI...")
    main_cli()

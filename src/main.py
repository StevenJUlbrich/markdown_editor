# main.py
from typing import Any, Dict, List, Optional

from app_controller import (
    AppController,
)  # Assuming app_controller.py is in the same directory


def display_numbered_list(
    items: List[Dict[str, Any]], title_key: str = "title", number_key: str = "number"
) -> None:
    """
    Helper to display a numbered list of items from a list of dictionaries.
    It intelligently determines the numbering key to use.
    """
    if not items:
        print("  No items to display.")
        return

    effective_number_key = None
    if items:
        if items[0].get("display_number") is not None:
            effective_number_key = "display_number"
        elif items[0].get(number_key) is not None:
            effective_number_key = number_key

    for item_idx, item in enumerate(items):
        if effective_number_key:
            num_to_display = item.get(effective_number_key)
            if num_to_display is None:
                num_to_display = item_idx + 1
        else:
            num_to_display = item_idx + 1

        title = item.get(title_key, "N/A")
        item_type = item.get("type", "")
        type_display = f" ({item_type})" if item_type else ""

        id_info = []
        if item.get("panel_id") is not None:
            id_info.append(f"P_ID:{item['panel_id']}")
        if item.get("h3_id") is not None:
            id_info.append(f"H3_ID:{item['h3_id']}")
        if item.get("h4_id") is not None:
            id_info.append(f"H4_ID:{item['h4_id']}")
        id_display = f" [{', '.join(id_info)}]" if id_info else ""

        raw_id = item.get("id")
        if (
            raw_id is not None
            and not id_info
            and not item_type
            and not item.get("is_panel")
        ):
            id_display = f" [GenericSectionID: {raw_id}]"
        elif raw_id is not None and item.get("is_panel") and not id_info:
            id_display = f" [PanelDocID: {raw_id}]"

        print(f"  {num_to_display}. {title}{type_display}{id_display}")


def get_int_choice(
    prompt_text: str,
    max_val: Optional[int] = None,
    min_val: int = 1,
    allow_cancel: bool = True,
) -> Optional[int]:
    """
    Helper to get an integer choice from the user, with improved validation and cancel option.
    """
    while True:
        try:
            choice_str = input(prompt_text).strip()
            if not choice_str and allow_cancel:
                print("  Action cancelled.")
                return None
            if not choice_str and not allow_cancel:
                print("  Input cannot be empty. Please enter a number.")
                continue

            choice_int = int(choice_str)

            range_error_msg = ""
            if max_val is not None and not (min_val <= choice_int <= max_val):
                range_error_msg = f"  Invalid input. Please enter a number between {min_val} and {max_val}."
            elif choice_int < min_val:
                range_error_msg = f"  Invalid input. Please enter a number greater than or equal to {min_val}."

            if range_error_msg:
                print(range_error_msg)
                continue
            return choice_int
        except ValueError:
            print("  Invalid input. Please enter a whole number (e.g., 1, 2, 3).")


def main_cli():
    """
    Main command-line interface function for the Markdown Processor.
    """
    controller = AppController()
    document_is_loaded = False
    default_doc_path = "day_03_chapter_01_draft.md"

    main_menu_options = {
        "1": "Load Document",
        "2": "List All Document Sections (Generic & Panel H2s)",
        "3": "List All Panels (by their document number)",
        "4": "Select Panel by its Document Number",
        "5": "View H3 Sections in Selected Panel (then view H3 content)",
        "6": "Prepare Targetable Sections in Selected Panel for API",
        "7": "Modify/Add Content in Selected Panel (Target by Display #)",
        "8": "Process API Enhancement for Specific H3 (Select Panel & H3 by #)",
        "9": "View Diff for API-Improved H3 Section",
        "10": "Export Document Structure to JSON",
        "11": "Enhance Named Sections in Selected Panel (Targeted API Call)",  # New Option
        "12": "Save Document",  # Renumbered from 11
        "0": "Exit",
    }
    # Determine the highest valid numeric choice for the main menu
    numeric_choices = [int(k) for k in main_menu_options.keys() if k.isdigit()]
    min_main_menu_choice = min(numeric_choices) if numeric_choices else 0
    max_main_menu_choice = max(numeric_choices) if numeric_choices else 0

    while True:
        print(f"\n======= Markdown Processor CLI (Targeted Enhance) =======")
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
            ):
                print(
                    f"Currently Selected Panel: [ID:{controller.current_selected_panel_id}] {selected_panel_title}"
                )
            else:
                print("No panel currently selected.")
        else:
            print("No document loaded.")
        print("-----------------------------------------------------------------")
        for key, value in main_menu_options.items():
            print(f"{key}. {value}")
        print("-----------------------------------------------------------------")

        choice = input("Enter your choice: ")

        if choice == "1":
            filepath_to_load = input(
                f"Enter document filepath (or press Enter for '{default_doc_path}', 'cancel' to abort): "
            ).strip()
            if filepath_to_load.lower() == "cancel":
                print("  Loading cancelled.")
                continue
            filepath_to_load = filepath_to_load or default_doc_path

            if controller.load_document(filepath_to_load):
                document_is_loaded = True
            else:
                document_is_loaded = False

        elif choice == "2":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            print("\n--- All Document Top-Level Sections (Generic & Panels) ---")
            sections = controller.list_all_h2_sections_for_cli()
            display_numbered_list(sections, title_key="title", number_key="number")

        elif choice == "3":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            print("\n--- All Panels (Selectable by Document Number) ---")
            panels = controller.list_panels_for_cli()
            if panels:
                for panel_obj in panels:
                    print(
                        f"  Panel Doc #: {panel_obj.panel_number_in_doc}. {panel_obj.panel_title_text}"
                    )
            else:
                print("  No panels found in the document.")

        elif choice == "4":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            panels = controller.list_panels_for_cli()
            if not panels:
                print("  No panels available in the document to select from.")
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
                    pass

        elif choice == "5":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            if controller.current_selected_panel_id is None:
                print("  Please select a Panel first (Option 4).")
                continue

            panel_title = controller.get_current_selected_panel_title()
            print(
                f"\n--- H3 Sections in Selected Panel [ID:{controller.current_selected_panel_id}] ('{panel_title}') ---"
            )
            h3_options = controller.list_h3_sections_in_selected_panel_for_cli()

            if h3_options:
                display_numbered_list(
                    h3_options, title_key="title", number_key="number"
                )
                h3_list_selection_number = get_int_choice(
                    "Enter H3 list number (from above) to view its content (or Enter to skip): ",
                    max_val=len(h3_options),
                )
                if h3_list_selection_number is not None:
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

        elif choice == "6":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            if controller.current_selected_panel_id is None:
                print("  Please select a Panel first (Option 4).")
                continue

            panel_title = controller.get_current_selected_panel_title()
            print(
                f"\n--- Targetable Sections in Selected Panel [ID:{controller.current_selected_panel_id}] ('{panel_title}') ---"
            )
            targetable_sections = (
                controller.list_targetable_sections_in_selected_panel_for_cli()
            )
            if targetable_sections:
                display_numbered_list(
                    targetable_sections, title_key="title", number_key="display_number"
                )
                numbers_str = input(
                    "Enter comma-separated display numbers for API (e.g., 1,3 or Enter to cancel): "
                )
                if not numbers_str:
                    print("  API preparation cancelled.")
                    continue

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
                                f"  Warning: Invalid display numbers skipped: {invalid_selections}. Valid range: 1 to {max_display_num}."
                            )

                        if valid_selections:
                            api_ready_data = (
                                controller.prepare_multiple_selected_sections_for_api(
                                    valid_selections
                                )
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
                            else:
                                print(
                                    "  No sections were successfully prepared (e.g., content retrieval failed)."
                                )
                        elif not invalid_selections:
                            print("  No valid section numbers entered.")
                    else:
                        print("  No section numbers entered.")
                except ValueError:
                    print(
                        "  Invalid input. Please enter comma-separated numbers (e.g., 1,3,4)."
                    )

        elif choice == "7":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            if controller.current_selected_panel_id is None:
                print("  Please select a Panel first (Option 4).")
                continue

            panel_title = controller.get_current_selected_panel_title()
            print(
                f"\n--- Targetable Sections for Modification in Panel [ID:{controller.current_selected_panel_id}] ('{panel_title}') ---"
            )
            targetable_sections = (
                controller.list_targetable_sections_in_selected_panel_for_cli()
            )
            if targetable_sections:
                display_numbered_list(
                    targetable_sections, title_key="title", number_key="display_number"
                )
                section_display_num = get_int_choice(
                    "Enter display number of section to modify/add to (or Enter to cancel): ",
                    len(targetable_sections),
                )
                if section_display_num is not None:
                    target_info = controller._get_target_info_from_display_number(
                        section_display_num
                    )
                    if target_info and controller.doc_model:
                        print(
                            f"\n--- Current content of '{target_info.get('title')}' (Type: {target_info.get('type')}) ---"
                        )
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

                    while True:
                        action_choice_prompt = "  Action: 'replace' current content, 'add start', 'add end', or 'cancel' to abort this operation? (default: replace): "
                        action_choice = (
                            input(action_choice_prompt).strip().lower() or "replace"
                        )
                        if action_choice == "cancel":
                            print("  Modification/addition cancelled.")
                            break
                        if action_choice not in ["replace", "add start", "add end"]:
                            print(
                                "  Invalid action. Valid actions are: 'replace', 'add start', 'add end', or 'cancel'."
                            )
                            continue

                        new_md_prompt = f"  Enter Markdown content for '{action_choice}' (use \\n for newlines, or type 'CANCELINPUT' to abort this input):\n"
                        new_md = input(new_md_prompt).replace("\\n", "\n")
                        if new_md.upper() == "CANCELINPUT":
                            print("  Content input cancelled.")
                            break

                        success = False
                        if action_choice == "replace":
                            success = controller.update_target_section_content(
                                section_display_num, new_md
                            )
                        elif action_choice in ["add start", "add end"]:
                            pos = "start" if action_choice == "add start" else "end"
                            success = controller.add_to_target_section_content(
                                section_display_num, new_md, pos
                            )

                        if success:
                            print(f"  Content action '{action_choice}' successful.")
                        else:
                            print(f"  Content action '{action_choice}' failed.")
                        break

        elif choice == "8":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue

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

            display_numbered_list(h3_options, title_key="title", number_key="number")
            h3_list_selection_number = get_int_choice(
                "Enter H3 list number (from above) to enhance (or Enter to cancel): ",
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
                    h3_id_in_panel = selected_h3_data["number"]
                    h3_title_for_prompt = selected_h3_data["title"]

                    print(
                        f"\nSimulating API call for Panel ID {panel_doc_num}, H3 ID {h3_id_in_panel} ('{h3_title_for_prompt}')."
                    )
                    if controller.doc_model:
                        current_h3_content = (
                            controller.doc_model.get_section_markdown_for_api(
                                panel_id=panel_doc_num, h3_id_in_panel=h3_id_in_panel
                            )
                        )
                        print(
                            f"\nCurrent H3 Content:\n{current_h3_content if current_h3_content else '  (No content or error retrieving)'}\n"
                        )
                    else:
                        print(" Error: Document model not available.")

                    sim_recommendation = input(
                        "  Enter simulated API recommendation (e.g., 'Add Diagram', or 'cancel'): "
                    ).strip()
                    if sim_recommendation.lower() == "cancel":
                        print("  API enhancement cancelled.")
                        continue

                    sim_reason = input(
                        "  Enter simulated API reason (or 'cancel'): "
                    ).strip()
                    if sim_reason.lower() == "cancel":
                        print("  API enhancement cancelled.")
                        continue

                    sim_improved_md_prompt = f"  Enter SIMULATED improved Markdown for H3 '{h3_title_for_prompt}' (use \\n for newlines, or 'CANCELINPUT'):\n"
                    sim_improved_md = input(sim_improved_md_prompt).replace("\\n", "\n")

                    if sim_improved_md.upper() == "CANCELINPUT":
                        print("  API Enhancement input cancelled.")
                    elif controller.process_api_enhancements_for_h3(
                        panel_doc_num,
                        h3_id_in_panel,
                        sim_improved_md,
                        recommendation=sim_recommendation,
                        reason=sim_reason,
                    ):
                        print("  API enhancement processed successfully (simulated).")
                        print(
                            "  Note: The document model now holds this 'api_improved_markdown'. Save (Option 12) to see changes."
                        )
                    else:
                        print("  API enhancement processing failed (simulated).")
                else:
                    print(f"  Invalid H3 selection from list.")

        elif choice == "9":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue

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

            display_numbered_list(h3_options, title_key="title", number_key="number")
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
                    h3_id_in_panel = selected_h3_data["number"]
                    diff_text = controller.get_h3_section_diff_text(
                        panel_doc_num, h3_id_in_panel
                    )
                    if diff_text:
                        print(
                            f"\n--- Diff for H3: {selected_h3_data['title']} (Panel ID {panel_doc_num}, H3 ID {h3_id_in_panel}) ---"
                        )
                        print(diff_text)
                        print("--------------------------------------------------")
                else:
                    print("  Invalid H3 selection from list.")

        elif choice == "10":
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            print("\n--- Exporting Document Structure to JSON ---")
            json_output = controller.get_chapter_model_as_json()
            if json_output and not json_output.startswith('{"error"'):
                print(json_output)
                save_to_file = input(
                    "  Save to file? (e.g., structure.json, or Enter to skip): "
                ).strip()
                if save_to_file:
                    try:
                        with open(save_to_file, "w", encoding="utf-8") as f:
                            f.write(json_output)
                        print(f"  Successfully saved JSON to {save_to_file}")
                    except Exception as e:
                        print(f"  Error saving JSON to file: {e}")
            elif json_output:
                print(f"  {json_output}")
            else:
                print("  Could not generate JSON output (Controller returned None).")
            print("------------------------------------------")

        elif choice == "11":  # New Option: Targeted Panel Enhancement
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            if controller.current_selected_panel_id is None:
                print(
                    "  No panel currently selected. Please select a panel first (Option 4) to target for enhancement."
                )
                continue

            print(
                f"\n--- Targeted API Enhancement for Selected Panel [ID:{controller.current_selected_panel_id}] ---"
            )
            print(
                "This will extract predefined named sections (Scene Description, Teaching Narrative, etc.)"
            )
            print(
                "from the currently selected panel, send them for API suggestions, and then enhance them if suggested."
            )

            panel_to_enhance_id = (
                controller.current_selected_panel_id
            )  # Use the already selected panel ID
            panel_to_enhance_title = controller.get_current_selected_panel_title()

            confirm = (
                input(
                    f"Proceed with enhancing Panel ID {panel_to_enhance_id} ('{panel_to_enhance_title}')? (yes/no): "
                )
                .strip()
                .lower()
            )
            if confirm == "yes":
                if controller.enhance_structured_panel_sections(panel_to_enhance_id):
                    # Controller method now prints detailed INFO/ERROR messages
                    print(
                        f"  Targeted enhancement process for Panel ID {panel_to_enhance_id} completed."
                    )
                    print(
                        "  Remember to save the document (Option 12) to persist changes."
                    )
                else:  # Should ideally not happen if panel_id is valid and doc_model exists
                    print(
                        f"  Targeted enhancement process for Panel ID {panel_to_enhance_id} encountered an error or was aborted by controller."
                    )
            else:
                print("  Targeted enhancement cancelled.")

        elif choice == "12":  # Save Document (was 11)
            if not document_is_loaded:
                print("  Please load a document first (Option 1).")
                continue
            output_file = input(
                "Enter output filepath (e.g., day_03_chapter_01_updated.md or Enter to cancel): "
            )
            if output_file:
                if controller.save_document(output_file):
                    pass
                else:
                    pass
            else:
                print("  Save cancelled: No output filepath provided.")

        elif choice == "0":
            print("Exiting Markdown Processor.")
            break

        else:
            print(
                f"  Invalid choice '{choice}'. Please enter a number from the menu ({min_main_menu_choice}-{max_main_menu_choice})."
            )


if __name__ == "__main__":
    print("Starting Markdown Processor CLI...")
    main_cli()

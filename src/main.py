# main.py
from app_controller import AppController


def main_cli():
    controller = AppController()
    doc_loaded = False

    while True:
        print("\nMarkdown Processor CLI")
        print("----------------------")
        print("1. Load Document (chapter_01_draft.md)")
        print("2. View Document Structure")
        print("3. Get Specific Subsection Content (for API simulation)")
        print("4. Process Multiple Sections (API simulation - Example #2)")
        print("5. Modify Subsection Content (Example #3)")
        print("6. Add Content to Subsection (Example #4)")
        print("7. Save Document (Example #5)")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            if controller.load_document("chapter_01_draft.md"):
                doc_loaded = True
            else:
                doc_loaded = False
        elif choice == "2":
            if doc_loaded:
                print(controller.get_document_structure_view())
            else:
                print("Please load a document first (Option 1).")
        elif choice == "3":
            if doc_loaded:
                panel_frag = input("Enter panel title fragment (e.g., 'Panel 1'): ")
                sub_frag = input(
                    "Enter subsection title fragment (e.g., 'Teaching Narrative'): "
                )
                content = controller.get_content_for_api(panel_frag, sub_frag)
                if content:
                    print("\n--- Subsection Content ---")
                    print(content)
                    print("------------------------")
                else:
                    print("Could not retrieve content.")
            else:
                print("Please load a document first.")
        elif choice == "4":  # Example #2
            if doc_loaded:
                sections = [
                    ("Panel 1", "Teaching Narrative"),
                    ("Panel 2", "Banking Impact"),
                ]
                prompt = "Summarize this section and provide key takeaways."
                controller.process_multiple_sections_for_api(sections, prompt)
            else:
                print("Please load a document first.")
        elif choice == "5":  # Example #3
            if doc_loaded:
                panel_frag = input("Enter panel title fragment to modify: ")
                sub_frag = input("Enter subsection title fragment to modify: ")
                new_md = input(
                    f"Enter new Markdown content for '{sub_frag}' (can be multi-line if you handle input carefully, or just a short string for test):\n"
                )
                controller.modify_content_example(panel_frag, sub_frag, new_md)
            else:
                print("Please load a document first.")
        elif choice == "6":  # Example #4
            if doc_loaded:
                panel_frag = input("Enter panel title fragment to add to: ")
                sub_frag = input("Enter subsection title fragment to add to: ")
                new_md = input(f"Enter new Markdown content to add to '{sub_frag}':\n")
                position = (
                    input("Add at 'start' or 'end' of subsection? (default: end): ")
                    or "end"
                )
                controller.add_content_example(panel_frag, sub_frag, new_md, position)
            else:
                print("Please load a document first.")

        elif choice == "7":  # Example #5
            if doc_loaded:
                output_file = input(
                    "Enter output filepath (e.g., chapter_01_updated.md): "
                )
                controller.save_document(output_file)
            else:
                print("Please load a document first.")
        elif choice == "0":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # Ensure mistletoe is installed in your environment
    # (e.g., conda install -c conda-forge mistletoe)
    main_cli()

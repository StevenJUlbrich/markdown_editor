# main.py (refactored CLI)

from app_controller import AppController
from logging_config import get_logger

logger = get_logger(__name__)


def print_panel_list(panel_list):
    print("\nPanels in Document:")
    for p in panel_list:
        print(f"  {p['panel_number_in_doc']}: {p['panel_title_text']}")


def main():
    controller = AppController()
    document_loaded = False

    while True:
        print("\n=== Markdown Training CLI ===")
        print("1. Load Markdown Document")
        print("2. List Panels")
        print("3. Select Panel by Number")
        print("4. Show Named Sections in Selected Panel")
        print("5. Update Named Section in Panel")
        print("6. Save Document")
        print("7. Suggest Character Roles Only (Panels in Folder)")
        print("8. Export Enriched Scene JSON")
        print("0. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            path = input("Enter markdown file path: ").strip()
            document_loaded = controller.load_document(path)
            print(f"Loaded: {document_loaded}")
        elif choice == "2":
            if not document_loaded:
                print("Load a document first.")
                continue
            panel_list = controller.list_panels()
            print_panel_list(panel_list)
        elif choice == "3":
            if not document_loaded:
                print("Load a document first.")
                continue
            num = input("Panel number: ").strip()
            try:
                num = int(num)
                selected = controller.select_panel(num)
                print(f"Panel selected: {selected}")
            except Exception:
                print("Invalid input.")
        elif choice == "4":
            if not document_loaded or controller.current_selected_panel_id is None:
                print("Select a panel first.")
                continue
            sections = controller.extract_named_sections()
            print("Named Sections:")
            for k, v in sections.items():
                print(f"-- {k} --\n{v[:120]}{'...' if len(v) > 120 else ''}\n")
        elif choice == "5":
            if not document_loaded or controller.current_selected_panel_id is None:
                print("Select a panel first.")
                continue
            title = input("Section H3 Title: ").strip()
            new_md = input("New Markdown Content (use \\n for newlines): ").replace(
                "\\n", "\n"
            )
            success = controller.update_named_section(title, new_md)
            print(f"Update success: {success}")
        elif choice == "6":
            if not document_loaded:
                print("Load a document first.")
                continue
            out_path = input("Enter output file path: ").strip()
            success = controller.save_document(out_path)
            print(f"Save success: {success}")

        elif choice == "7":
            folder = input("Enter folder path containing markdown files: ").strip()
            try:
                results = controller.suggest_character_roles_in_folder(folder)
                for filename, panels in results.items():
                    print(f"\nFile: {filename}")
                    for panel_title, roles in panels.items():
                        print(f"  Panel: {panel_title}")
                        print(f"    Suggested Roles: {roles}")
            except Exception as e:
                logger.error("Error: %s", e)
        elif choice == "8":
            if not document_loaded:
                print("Load and enrich a document first.")
                continue
            # Optionally, check if panels are already enriched, or enrich now:
            enriched = controller.enrich_all_panels()  # Or load if already done
            out_path = input(
                "Enter output JSON file path (e.g. chapter_01_enriched.json): "
            ).strip()
            from services.chapter_scene_json_exporter import export_chapter_to_json

            export_chapter_to_json(enriched, out_path)
        elif choice == "0":
            print("Exiting.")
            break
        else:
            print("Unknown choice.")


if __name__ == "__main__":
    main()

import json
from pathlib import Path
from typing import List

from comic_image_pipeline import process_panel_to_json
from document_model import MarkdownDocument
from generate_character_profiles import generate_character_profiles_for_roles

CHARACTER_JSON_PATH = Path(
    "D:\Development_Personal\SRE-Training\SRE CORE PRACTICES\day 03\character\chapter_03_character_sheet.json"
)  # Preloaded character file
CHAPTER_MD_PATH = Path(
    "D:/Development_Personal\SRE-Training\SRE CORE PRACTICES\day 03\chapters\enhanced_chapters\day_03_chapter_01_draft_enhanced.md"
)  # Replace with your test markdown
IMAGES_FOLDER = "images"
CHARACTERS_PER_ROLE = 2
CHAPTER_PREFIX = CHAPTER_MD_PATH.stem.lower()


def main():
    print(f"📄 Loading chapter: {CHAPTER_MD_PATH}")
    doc = MarkdownDocument(filepath=str(CHAPTER_MD_PATH))

    if not doc.chapter_model:
        print("❌ Failed to parse markdown into document model.")
        return

    with open(CHARACTER_JSON_PATH, "r", encoding="utf-8") as f:
        character_data = json.load(f)

    print(f"📚 Found {len(doc.chapter_model.document_elements)} document elements.\n")

    all_panels = [
        el
        for el in doc.chapter_model.document_elements
        if hasattr(el, "panel_number_in_doc")
    ]

    for panel in all_panels:
        panel_json = process_panel_to_json(
            doc=doc,
            panel=panel,
            character_data=character_data,
            character_json_path=CHARACTER_JSON_PATH,
            characters_per_role=CHARACTERS_PER_ROLE,
            chapter_prefix=CHAPTER_PREFIX,
            images_folder=IMAGES_FOLDER,
        )

        if not panel_json:
            print(
                f"⚠️  Skipping panel {panel.panel_number_in_doc}: no usable content.\n"
            )
            continue

        print(f"--- Panel {panel_json['panel']}: {panel.panel_title_text} ---")
        print("Scene Types:", panel_json["scene_analysis"]["scene_types"])
        print("Tone:", panel_json["scene_analysis"].get("tone"))
        print("Teaching Level:", panel_json["scene_analysis"].get("teaching_level"))
        print("Location:", panel_json["scene_analysis"].get("location"))
        print("Time of Day:", panel_json["scene_analysis"].get("time_of_day"))
        print("Notes:", panel_json["scene_analysis"].get("notes"))
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()

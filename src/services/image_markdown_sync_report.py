import os
from typing import List, Set

from models.comic_panel_image_sheet import ComicPanelImageSheet


def collect_all_referenced_images(sheets: List[ComicPanelImageSheet]) -> Set[str]:
    images = set()
    for sheet in sheets:
        for se in sheet.scene_enhancements:
            if se.panel_image and se.panel_image.image_filename:
                # Normalize path for comparison (relative to images/)
                images.add(os.path.normpath(se.panel_image.image_filename))
    return images


def report_image_markdown_sync(
    sheets: List[ComicPanelImageSheet],
    images_dir: str = "images",
    print_missing_only: bool = False,
):
    # Set of all image files actually present
    all_image_files = set(
        os.path.normpath(os.path.join(images_dir, f))
        for f in os.listdir(images_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
    )

    # Set of all referenced images in JSON
    all_referenced_images = collect_all_referenced_images(sheets)

    # 1. Panels with missing or absent images
    missing_image_refs = []
    for sheet in sheets:
        for panel_idx, se in enumerate(sheet.scene_enhancements):
            if not se.panel_image or not se.panel_image.image_filename:
                missing_image_refs.append((sheet.panel_id, panel_idx, "no image info"))
            else:
                image_path = os.path.normpath(se.panel_image.image_filename)
                full_path = os.path.normpath(
                    os.path.join(images_dir, os.path.basename(image_path))
                )
                if not os.path.exists(full_path):
                    missing_image_refs.append((sheet.panel_id, panel_idx, image_path))

    # 2. Orphan image files (exist on disk, not referenced)
    orphan_files = []
    for img in all_image_files:
        if os.path.normpath(img) not in all_referenced_images:
            orphan_files.append(img)

    # Reporting
    print("\n--- Image/Markdown Sync QA Report ---")
    print(f"Total panels checked: {sum(len(s.scene_enhancements) for s in sheets)}")
    print(f"Total image files in '{images_dir}/': {len(all_image_files)}")
    print(f"Total unique images referenced in JSON: {len(all_referenced_images)}\n")

    if missing_image_refs:
        print("Panels with missing or absent images:")
        for panel_id, panel_idx, msg in missing_image_refs:
            print(f"  Panel {panel_id}, Enhancement {panel_idx}: {msg}")
    else:
        print("✅ All panels/enhancements have image references and files present.")

    if orphan_files:
        print("\nImages in folder NOT referenced by any panel:")
        for img in orphan_files:
            print(f"  {img}")
    else:
        print("\n✅ All images in folder are referenced in at least one panel.")

    print("\n--- End of Report ---\n")

    # Optionally: return details for further processing (or export as JSON)
    return {"missing_image_refs": missing_image_refs, "orphan_files": orphan_files}


# Example CLI usage
if __name__ == "__main__":
    import json

    # Adjust path as needed
    enriched_json = "chapter_01_enriched.json"
    images_dir = "images"

    with open(enriched_json, "r", encoding="utf-8") as f:
        sheets = [ComicPanelImageSheet.model_validate(p) for p in json.load(f)]

    report_image_markdown_sync(sheets, images_dir=images_dir)

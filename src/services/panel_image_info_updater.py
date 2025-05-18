import os
from typing import List, Optional

from models.comic_panel_image_sheet import (
    ComicPanelImageSheet,
    PanelImageInfo,
    SceneEnhancement,
)


def update_panel_images_for_sheets(
    sheets: List[ComicPanelImageSheet],
    image_dir: str = "images",
    default_width: int = 640,
    default_model: str = "dalle-3",
):
    """
    For each ComicPanelImageSheet in the list, attach PanelImageInfo to each SceneEnhancement.
    Matches based on a naming convention, or pre-populated info.
    """
    # Build a set of all images in the folder for fast lookup
    all_images = set(os.listdir(image_dir))

    for sheet in sheets:
        for idx, enhancement in enumerate(sheet.scene_enhancements):
            # Example convention: images/ch{chapter}_p{panel}_{version_id}.png
            chapter = sheet.chapter_id or "ch0"
            panel = sheet.panel_index or idx + 1
            version = enhancement.version_id or "main"
            # (You can adjust the naming logic as needed!)
            candidate_names = [
                f"ch{chapter}_p{panel}_{version}.png",
                f"ch{chapter}_p{panel}.png",
                f"panel_{panel}_{version}.png",
            ]
            image_file = next(
                (img for img in all_images if img in candidate_names), None
            )
            if not image_file:
                print(
                    f"Warning: No image found for {chapter}, panel {panel}, version {version}"
                )
                continue

            image_path = os.path.join(image_dir, image_file)

            # Compose alt text: Prefer explicit, else use part of scene_text
            alt_text = enhancement.llm_metadata.get("image_alt_text") or (
                enhancement.scene_text[:80] + "..."
            )  # fallback to start of scene
            # Use image prompt if available, else fallback
            image_prompt = (
                enhancement.llm_metadata.get("llm_image_prompt")
                or enhancement.llm_metadata.get("image_prompt")
                or enhancement.scene_text
            )

            # Create the PanelImageInfo and update the enhancement
            panel_image = PanelImageInfo(
                image_filename=image_path,
                alt_text=alt_text,
                width=default_width,
                llm_image_prompt=image_prompt,
                llm_model=default_model,
            )
            enhancement.panel_image = panel_image

    return sheets


# Example usage:
# enriched_sheets = load_your_enriched_sheets()  # List[ComicPanelImageSheet]
# update_panel_images_for_sheets(enriched_sheets, image_dir="images")
# ...then save/export enriched_sheets as usual

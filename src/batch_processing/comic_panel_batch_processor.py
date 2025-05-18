# src/batch_processing/comic_panel_batch_processor.py

import json
import os

import yaml

from models.comic_panel_image_sheet import (
    ChecklistResult,
    ComicPanelImageSheet,
    SceneEnhancement,
    SpeechBubble,
)
from parsing.comic_panel_mapping import create_panel_sheets_from_markdown

# Load prompts and character DB (do this once, reuse in loop)
with open("llm_prompts.yaml", "r", encoding="utf-8") as f:
    llm_prompts = yaml.safe_load(f)

with open("character_base_list.json", "r", encoding="utf-8") as f:
    character_db = json.load(f)["characters"]


def ask_openai(prompt):
    # Placeholder for actual OpenAI API call
    print(f"LLM PROMPT:\n{prompt}\n---")
    # Replace this with the real API logic
    return {"scene_theme": "Chaos", "rationale": "Example"}  # Mock


def process_panel(comic_panel: ComicPanelImageSheet):
    # 1. Scene Theme Analysis
    scene_theme_prompt = llm_prompts["scene_theme_analysis"].format(
        scene_text=comic_panel.scene_description_original
    )
    scene_theme_result = ask_openai(scene_theme_prompt)
    scene_theme = scene_theme_result["scene_theme"]

    # 2. Role Extraction
    roles_prompt = llm_prompts["role_extraction"].format(scene_theme=scene_theme)
    roles_result = ask_openai(roles_prompt)
    required_roles = [r["role"] for r in roles_result]

    # 3. Scene Rewrite
    scene_rewrite_prompt = llm_prompts["scene_rewrite"].format(
        required_roles=", ".join(required_roles),
        original_scene=comic_panel.scene_description_original,
    )
    scene_text = ask_openai(scene_rewrite_prompt)

    # 4. Checklist Evaluation
    scene_checklist_prompt = llm_prompts["scene_checklist_evaluation"].format(
        scene_text=scene_text,
        common_example=comic_panel.common_example_original,
        required_roles=", ".join(required_roles),
    )
    checklist_result = ask_openai(scene_checklist_prompt)
    while not (
        checklist_result["teaching_narrative_satisfied"]
        and checklist_result["common_example_aligned"]
        and checklist_result["roles_used_effectively"]
    ):
        scene_rewrite_fix_prompt = llm_prompts["scene_rewrite_fix"].format(
            missing_elements=checklist_result["missing_elements"], scene_text=scene_text
        )
        scene_text = ask_openai(scene_rewrite_fix_prompt)
        scene_checklist_prompt = llm_prompts["scene_checklist_evaluation"].format(
            scene_text=scene_text,
            common_example=comic_panel.common_example_original,
            required_roles=", ".join(required_roles),
        )
        checklist_result = ask_openai(scene_checklist_prompt)

    # 5. Character Enhancement
    character_details = []
    for role in required_roles:
        found = None
        for name, data in character_db.items():
            if data["role"].lower() == role.lower():
                character = {"name": name, **data}
                found = character
                break
        if not found:
            char_enhance_prompt = llm_prompts["character_enhancement"].format(
                required_roles=role
            )
            character = ask_openai(char_enhance_prompt)
        character_details.append(found or character)

    # 6. Speech Bubble Generation
    speech_bubble_prompt = llm_prompts["speech_bubble_generation"].format(
        scene_text=scene_text, characters=json.dumps(character_details)
    )
    speech_bubbles = ask_openai(speech_bubble_prompt)

    # 7. Save LLM and QA Results to ComicPanelImageSheet
    scene_enhancement = SceneEnhancement(
        version_id="llm-v1",
        scene_text=scene_text,
        llm_metadata={"scene_theme": scene_theme},
        checklist=ChecklistResult(**checklist_result),
    )
    comic_panel.scene_enhancements.append(scene_enhancement)
    comic_panel.speech_bubbles = [SpeechBubble(**b) for b in speech_bubbles]
    comic_panel.checklist_results.append(ChecklistResult(**checklist_result))
    return comic_panel


def process_markdown_file(md_path, chapter_id=None):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    panel_sheets = create_panel_sheets_from_markdown(md_text, chapter_id)
    enriched_panels = []
    for panel in panel_sheets:
        enriched_panel = process_panel(panel)
        enriched_panels.append(enriched_panel)
    return enriched_panels


def process_markdown_directory(md_dir):
    enriched_files = {}
    for fname in os.listdir(md_dir):
        if fname.endswith(".md"):
            md_path = os.path.join(md_dir, fname)
            chapter_id = os.path.splitext(fname)[0]
            enriched_panels = process_markdown_file(md_path, chapter_id=chapter_id)
            enriched_files[fname] = [p.dict() for p in enriched_panels]
    return enriched_files


if __name__ == "__main__":
    # Example usage for one file
    enriched_panels = process_markdown_file("chapter_01.md", chapter_id="chapter_01")
    with open("chapter_01_enriched.json", "w", encoding="utf-8") as out:
        json.dump([p.dict() for p in enriched_panels], out, indent=2)

    # Example usage for batch directory
    # enriched_files = process_markdown_directory("./chapters/")
    # for fname, panels in enriched_files.items():
    #     with open(f"{fname}_enriched.json", "w", encoding="utf-8") as out:
    #         json.dump(panels, out, indent=2)

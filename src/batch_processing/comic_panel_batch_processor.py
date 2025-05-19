# src/batch_processing/comic_panel_batch_processor.py

import argparse
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


def load_llm_prompts(llm_prompts_path):
    with open(llm_prompts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_character_db(character_json_path):
    with open(character_json_path, "r", encoding="utf-8") as f:
        return json.load(f)["characters"]


def ask_openai(prompt):
    # Placeholder for actual OpenAI API call
    print(f"LLM PROMPT:\n{prompt}\n---")
    return {"scene_theme": "Chaos", "rationale": "Example"}  # Mock


def process_panel(comic_panel: ComicPanelImageSheet, llm_prompts, character_db):
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


def process_markdown_file(md_path, llm_prompts, character_db, chapter_id=None):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    panel_sheets = create_panel_sheets_from_markdown(md_text, chapter_id)
    enriched_panels = []
    for panel in panel_sheets:
        enriched_panel = process_panel(panel, llm_prompts, character_db)
        enriched_panels.append(enriched_panel)
    return enriched_panels


def process_markdown_directory(md_dir, llm_prompts, character_db):
    enriched_files = {}
    for fname in os.listdir(md_dir):
        if fname.endswith(".md"):
            md_path = os.path.join(md_dir, fname)
            chapter_id = os.path.splitext(fname)[0]
            enriched_panels = process_markdown_file(
                md_path, llm_prompts, character_db, chapter_id=chapter_id
            )
            enriched_files[fname] = [p.model_dump() for p in enriched_panels]
    return enriched_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch process SRE comic panels with LLM."
    )
    parser.add_argument("--file", type=str, help="Markdown file to process")
    parser.add_argument(
        "--dir", type=str, help="Directory of markdown files to process"
    )
    parser.add_argument(
        "--prompts",
        type=str,
        default="llm_prompts.yaml",
        help="Path to LLM prompts YAML",
    )
    parser.add_argument(
        "--characters",
        type=str,
        default="character_base_list.json",
        help="Path to character base list JSON",
    )
    parser.add_argument(
        "--out", type=str, help="Output JSON file (for single file mode)"
    )
    args = parser.parse_args()

    llm_prompts = load_llm_prompts(args.prompts)
    character_db = load_character_db(args.characters)

    if args.file:
        enriched_panels = process_markdown_file(args.file, llm_prompts, character_db)
        out_path = args.out or (os.path.splitext(args.file)[0] + "_enriched.json")
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump([p.model_dump() for p in enriched_panels], out, indent=2)
        print(f"Enriched panels saved to {out_path}")

    elif args.dir:
        enriched_files = process_markdown_directory(args.dir, llm_prompts, character_db)
        for fname, panels in enriched_files.items():
            out_path = os.path.join(
                args.dir, f"{os.path.splitext(fname)[0]}_enriched.json"
            )
            with open(out_path, "w", encoding="utf-8") as out:
                json.dump(panels, out, indent=2)
            print(f"Enriched file saved to {out_path}")

    else:
        parser.print_help()

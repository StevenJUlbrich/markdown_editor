import argparse
import json
import logging
import os
import sys

import yaml
from tqdm import tqdm

from models.comic_panel_image_sheet import (
    ChecklistResult,
    ComicPanelImageSheet,
    SceneEnhancement,
    SpeechBubble,
)
from parsing.comic_panel_mapping import create_panel_sheets_from_markdown

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Load prompts and character DB
with open("llm_prompts.yaml", "r", encoding="utf-8") as f:
    llm_prompts = yaml.safe_load(f)

with open("character_base_list.json", "r", encoding="utf-8") as f:
    character_db = json.load(f)["characters"]


def ask_openai(prompt):
    # Placeholder for actual OpenAI API call
    logger.debug(f"LLM PROMPT:\n{prompt[:500]}...")  # Truncate long prompts for logs
    # Replace with your actual API call and parsing logic
    # For demo, return a mock
    return {
        "scene_theme": "Chaos",
        "rationale": "Example",
        "teaching_narrative_satisfied": True,
        "common_example_aligned": True,
        "roles_used_effectively": True,
        "missing_elements": "",
    }


def process_panel(comic_panel: ComicPanelImageSheet):
    try:
        # 1. Scene Theme Analysis
        scene_theme_prompt = llm_prompts["scene_theme_analysis"].format(
            scene_text=comic_panel.scene_description_original
        )
        scene_theme_result = ask_openai(scene_theme_prompt)
        scene_theme = scene_theme_result.get("scene_theme", "Chaos")

        # 2. Role Extraction
        roles_prompt = llm_prompts["role_extraction"].format(scene_theme=scene_theme)
        roles_result = ask_openai(roles_prompt)
        # If role_extraction returns a list of dicts or just a list of roles
        required_roles = (
            [r.get("role", r) for r in roles_result]
            if isinstance(roles_result, list)
            else ["SRE Lead", "junior SRE"]
        )

        # 3. Scene Rewrite
        scene_rewrite_prompt = llm_prompts["scene_rewrite"].format(
            required_roles=", ".join(required_roles),
            original_scene=comic_panel.scene_description_original,
        )
        scene_text = ask_openai(scene_rewrite_prompt)
        if isinstance(scene_text, dict) and "scene_text" in scene_text:
            scene_text = scene_text["scene_text"]

        # 4. Checklist Evaluation
        scene_checklist_prompt = llm_prompts["scene_checklist_evaluation"].format(
            scene_text=scene_text,
            common_example=comic_panel.common_example_original,
            required_roles=", ".join(required_roles),
        )
        checklist_result = ask_openai(scene_checklist_prompt)
        while not (
            checklist_result.get("teaching_narrative_satisfied", True)
            and checklist_result.get("common_example_aligned", True)
            and checklist_result.get("roles_used_effectively", True)
        ):
            scene_rewrite_fix_prompt = llm_prompts["scene_rewrite_fix"].format(
                missing_elements=checklist_result.get("missing_elements", ""),
                scene_text=scene_text,
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
        if not isinstance(speech_bubbles, list):
            speech_bubbles = []

        # 7. Save LLM and QA Results to ComicPanelImageSheet
        scene_enhancement = SceneEnhancement(
            version_id="llm-v1",
            scene_text=scene_text,
            llm_metadata={"scene_theme": scene_theme},
            checklist=ChecklistResult(**checklist_result),
        )
        comic_panel.scene_enhancements.append(scene_enhancement)
        comic_panel.speech_bubbles = [
            SpeechBubble(**b) for b in speech_bubbles if isinstance(b, dict)
        ]
        comic_panel.checklist_results.append(ChecklistResult(**checklist_result))
        return comic_panel
    except Exception as e:
        logger.error(f"Error processing panel: {e}")
        return comic_panel


def process_markdown_file(md_path, chapter_id=None):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    panel_sheets = create_panel_sheets_from_markdown(md_text, chapter_id)
    enriched_panels = []
    logger.info(f"Processing file: {md_path} ({len(panel_sheets)} panels)")
    for panel in tqdm(
        panel_sheets, desc=f"Panels in {os.path.basename(md_path)}", ncols=80
    ):
        enriched_panel = process_panel(panel)
        enriched_panels.append(enriched_panel)
    return enriched_panels


def process_markdown_directory(md_dir):
    enriched_files = {}
    md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]
    logger.info(f"Processing directory: {md_dir} ({len(md_files)} markdown files)")
    for fname in tqdm(md_files, desc="Markdown Files", ncols=80):
        md_path = os.path.join(md_dir, fname)
        chapter_id = os.path.splitext(fname)[0]
        enriched_panels = process_markdown_file(md_path, chapter_id=chapter_id)
        enriched_files[fname] = [p.dict() for p in enriched_panels]
        # Save per-file
        output_path = os.path.join(md_dir, f"{chapter_id}_enriched.json")
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump([p.dict() for p in enriched_panels], out, indent=2)
        logger.info(f"Saved enriched output: {output_path}")
    return enriched_files


def main():
    parser = argparse.ArgumentParser(
        description="Batch process SRE comic panels with LLM."
    )
    parser.add_argument("--file", type=str, help="Markdown file to process")
    parser.add_argument(
        "--dir", type=str, help="Directory of markdown files to process"
    )
    parser.add_argument(
        "--out", type=str, help="Output JSON file (for single file mode)"
    )
    args = parser.parse_args()

    if args.file:
        logger.info(f"Processing markdown file: {args.file}")
        enriched_panels = process_markdown_file(args.file)
        out_path = args.out or (os.path.splitext(args.file)[0] + "_enriched.json")
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump([p.dict() for p in enriched_panels], out, indent=2)
        logger.info(f"Saved output: {out_path}")

    elif args.dir:
        process_markdown_directory(args.dir)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

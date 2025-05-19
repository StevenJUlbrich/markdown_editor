import os
import random
import re
from typing import Any, Dict, List, Optional

import yaml

from models.comic_panel_image_sheet import (
    ChecklistResult,
    ComicPanelImageSheet,
    SceneEnhancement,
    SpeechBubble,
)
from services.openai_service import OpenAIService


class SceneEnhancer:
    def __init__(
        self,
        chapter_panels,
        character_repo,
        env_template_path="scene_environment_templates.yaml",
        prompt_yaml_path=None,
    ):
        self.chapter_panels = chapter_panels
        self.character_repo = character_repo["characters"]
        self.llm = OpenAIService(prompt_yaml_path)
        with open(env_template_path, "r", encoding="utf-8") as f:
            self.env_templates = yaml.safe_load(f)

    def evaluate_scene_types(self) -> Dict[str, int]:
        """Count scene types in the chapter to help balance variety."""
        scene_type_counts = {}
        for panel in self.chapter_panels:
            scene_type = panel.get("scene_type", "Unknown")
            scene_type_counts[scene_type] = scene_type_counts.get(scene_type, 0) + 1
        return scene_type_counts

    def adjust_scene_tones(self):
        """Force first/last panels to preferred scene types/tone if needed."""
        if self.chapter_panels:
            self.chapter_panels[0]["scene_type"] = "Chaos"
            self.chapter_panels[0]["tone"] = "Urgent, tense, action-driven"
            self.chapter_panels[-1]["scene_type"] = "Reflection"
            self.chapter_panels[-1]["tone"] = "Calm, retrospective, learning"

    def map_scene_type_to_roles(self, scene_type: str) -> List[str]:
        """Map each scene type to canonical required roles."""
        mapping = {
            "Chaos": ["Junior SRE", "Senior SRE"],
            "Teaching": ["Senior SRE", "SRE Engineer", "Junior SRE"],
            "Reflection": ["Senior SRE", "Analyst", "QA Engineer"],
            "Meta": ["Senior SRE", "Stakeholder"],
            "Decision": ["Senior SRE", "Product Manager", "Banking Executive"],
        }
        return mapping.get(scene_type, ["Senior SRE"])

    def resolve_role_from_title(self, title: str) -> Optional[str]:
        """Find the shortest/most canonical role for a title."""
        title = title.lower()
        for char_data in self.character_repo.values():
            if title in char_data["role"].lower() or char_data["role"].lower() in title:
                return char_data["role"]
        # Fallback for partial or fuzzy matches:
        for char_data in self.character_repo.values():
            if re.search(title, char_data["role"], re.IGNORECASE):
                return char_data["role"]
        return None

    def build_character_pool(self, role: str, max_chars=2) -> List[Dict[str, Any]]:
        """Find up to N characters for a given role, using the repo."""
        pool = []
        for name, char_data in self.character_repo.items():
            if char_data["role"].lower() == role.lower():
                pool.append({"name": name, **char_data})
            if len(pool) >= max_chars:
                break
        # If none found, create a placeholder character:
        if not pool:
            pool.append(
                {
                    "name": f"Generated {role}",
                    "role": role,
                    "visual_tags": [],
                    "appearance": "To be designed",
                    "voice_tone": "TBD",
                    "prop_loadout": [],
                    "motion_rules": "TBD",
                }
            )
        return pool

    def enrich_environment(self, panel, tone, characters):
        scene_type = panel.get("scene_type", "Teaching")
        env = self.env_templates.get(scene_type, {})
        description = env.get("description", "A generic operations setting.")
        # Optionally interpolate context vars (like time_of_day)
        if "{{time_of_day}}" in description:
            tod = panel.get("time_of_day", "late night")
            description = description.replace("{{time_of_day}}", tod)
        panel["environment"] = description
        panel["psychological_cues"] = env.get("psychological_cues", [])
        panel["teaching_hint"] = env.get("teaching_hint", "")
        panel["tone"] = tone
        panel["characters"] = characters
        return panel

    def assign_speech_bubbles(self, panel: Dict, characters: List[Dict]):
        """Define which characters speak and order (basic example: only a subset)."""
        speakers = []
        for idx, char in enumerate(characters):
            # Not everyone speaks, and not all speech is equal length.
            if idx == 0 or random.random() < 0.5:
                speech = f"{char['name']} addresses key issue."
                speakers.append({"character": char["name"], "speech": speech})
        panel["speech_bubbles"] = speakers

    def set_character_emotion_and_pose(self, panel: Dict):
        """Suggest emotion and pose based on scene context and character definitions."""
        emotion_templates = {
            "Chaos": ["anxious", "surprised", "urgent"],
            "Teaching": ["focused", "curious", "thoughtful"],
            "Reflection": ["calm", "relieved", "introspective"],
            "Meta": ["reflective", "analytical"],
            "Decision": ["decisive", "concerned", "engaged"],
        }
        for char in panel.get("characters", []):
            scene_type = panel.get("scene_type", "")
            char["emotion"] = random.choice(
                emotion_templates.get(scene_type, ["neutral"])
            )
            char["pose"] = (
                "standing" if char["emotion"] in ["urgent", "decisive"] else "seated"
            )

    def enhance_all_panels(self):
        self.adjust_scene_tones()
        for panel in self.chapter_panels:
            # Step 1: Evaluate and enforce scene type/tone (balance already adjusted)
            roles_needed = []
            # Step 2: Map scene type to required roles
            scene_type = panel.get("scene_type", "Teaching")
            roles_needed = self.map_scene_type_to_roles(scene_type)
            # Step 3: Build character pool for each role
            character_pool = []
            for role in roles_needed:
                canonical_role = self.resolve_role_from_title(role) or role
                characters = self.build_character_pool(canonical_role, max_chars=2)
                character_pool.extend(characters)
            # Step 4: Enrich environment, assign presence
            self.enrich_environment(panel, panel.get("tone", "neutral"), character_pool)
            # Step 5: Assign speech bubbles (order)
            self.assign_speech_bubbles(panel, character_pool)
            # Step 6: Set emotion and pose
            self.set_character_emotion_and_pose(panel)
        return self.chapter_panels

    def enrich_panel(self, panel_sheet: ComicPanelImageSheet):
        # 1. Scene Theme
        scene_theme_result = self.llm.prompt_and_call(
            "scene_theme_analysis",
            is_json=True,
            scene_text=panel_sheet.scene_description_original,
        )
        scene_theme = scene_theme_result.get("scene_theme", "Chaos")

        # 2. Roles
        roles_result = self.llm.prompt_and_call(
            "role_extraction", is_json=True, scene_theme=scene_theme
        )
        required_roles = [r["role"] for r in roles_result]

        # 3. Rewrite Scene
        scene_text = self.llm.prompt_and_call(
            "scene_rewrite",
            is_json=False,
            required_roles=", ".join(required_roles),
            original_scene=panel_sheet.scene_description_original,
        )

        # 4. Checklist + Fix/Iterate
        for _ in range(2):  # Max two attempts for simplicity
            checklist_result = self.llm.prompt_and_call(
                "scene_checklist_evaluation",
                is_json=True,
                scene_text=scene_text,
                common_example=panel_sheet.common_example_original,
                required_roles=", ".join(required_roles),
            )
            if all(
                [
                    checklist_result["teaching_narrative_satisfied"],
                    checklist_result["common_example_aligned"],
                    checklist_result["roles_used_effectively"],
                ]
            ):
                break
            # Fix and re-prompt
            scene_text = self.llm.prompt_and_call(
                "scene_rewrite_fix",
                is_json=False,
                missing_elements=checklist_result["missing_elements"],
                scene_text=scene_text,
            )

        # 5. Speech Bubbles
        # (This could use more data for characters in your pipeline)
        speech_bubbles = self.llm.prompt_and_call(
            "speech_bubble_generation",
            is_json=True,
            scene_text=scene_text,
            characters=str(required_roles),
        )
        speech_bubble_objs = [SpeechBubble(**b) for b in speech_bubbles]

        # 6. Alt Text & Scene Summary
        alt_text = self.llm.prompt_and_call(
            "panel_image_alt_text", is_json=False, scene_text=scene_text
        )
        neutral_summary = self.llm.prompt_and_call(
            "neutral_scene_summary", is_json=False, scene_text=scene_text
        )

        # 7. Assemble and update panel
        enhancement = SceneEnhancement(
            version_id="llm-v1",
            scene_text=scene_text,
            llm_metadata={
                "scene_theme": scene_theme,
                "neutral_scene_summary": neutral_summary,
            },
            checklist=ChecklistResult(**checklist_result),
        )
        panel_sheet.scene_enhancements = [enhancement]
        panel_sheet.speech_bubbles = speech_bubble_objs
        panel_sheet.current_scene_enhancement = "llm-v1"
        return panel_sheet


# Usage example (assuming you've parsed the markdown to a list of panel dicts and loaded the character JSON):
# from scene_enhancer import SceneEnhancer
# panels = [...]  # Your parsed chapter panels, each as a dict
# with open("character_base_list.json", "r") as f:
#     character_repo = json.load(f)
# enhancer = SceneEnhancer(panels, character_repo)
# enhanced_panels = enhancer.enhance_all_panels()

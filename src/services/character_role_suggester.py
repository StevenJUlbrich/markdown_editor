# character_role_suggester.py (updated)

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models.comic_panel_image_sheet import (
    ComicPanelImageSheet,
    SceneEnhancement,
    SpeechBubble,
)
from models.document_model import ChapterPydantic, PanelPydantic
from models.section_titles import SECTION_TITLES
from parsing.markdown_document import MarkdownDocument

from .openai_service import suggest_character_roles_for_panels


class CharacterRoleSuggester:
    @staticmethod
    def _suggest_roles_for_doc(doc: MarkdownDocument) -> Dict[str, List[str]]:
        """
        Extracts panel information from the Pydantic model and suggests roles.
        Uses the loaded document model rather than parsing markdown directly.
        """
        if not doc.chapter_model:
            return {}

        panel_inputs = []
        panel_titles = []

        # Extract panels from the Pydantic model
        for element in doc.chapter_model.document_elements:
            if not isinstance(element, PanelPydantic):
                continue

            # Extract panel information from the model
            panel = element
            sections = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
            scene = sections.get(SECTION_TITLES.SCENE_DESCRIPTION.value, "")
            teaching = sections.get(SECTION_TITLES.TEACHING_NARRATIVE.value, "")

            if not scene and not teaching:
                continue

            panel_inputs.append(
                {
                    "title": panel.panel_title_text,
                    "scene": scene,
                    "teaching": teaching,
                }
            )
            panel_titles.append(panel.panel_title_text)

        if not panel_inputs:
            return {}

        # Batch OpenAI call for all panels in the file
        role_dict = suggest_character_roles_for_panels(panel_inputs)
        return {title: role_dict.get(title, []) for title in panel_titles}

    @staticmethod
    def _suggest_roles_for_path(md_path: Path) -> Dict[str, Dict[str, List[str]]]:
        """Process a single markdown file using the Pydantic model."""
        if not md_path.exists() or not md_path.is_file():
            raise ValueError(f"File {md_path} not found or is not a file.")

        # Load document into Pydantic model
        doc = MarkdownDocument()
        if not doc.load_and_process(str(md_path)):
            raise ValueError(f"Failed to load document from {md_path}.")

        # Use the model to extract panel information
        roles = CharacterRoleSuggester._suggest_roles_for_doc(doc)
        return {md_path.name: roles}

    @staticmethod
    def suggest_roles_for_folder(folder_path: str) -> Dict[str, Dict[str, List[str]]]:
        """Process all markdown files in a folder using Pydantic models."""
        folder = Path(folder_path)
        result = {}

        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Folder {folder_path} not found or is not a directory.")

        for file in folder.glob("*.md"):
            try:
                file_roles = CharacterRoleSuggester._suggest_roles_for_path(file)
                result.update(file_roles)
            except Exception as e:
                # Log error but continue processing other files
                continue

        return result

    @staticmethod
    def suggest_character_roles_in_file(
        file_path: str,
    ) -> Dict[str, Dict[str, List[str]]]:
        """Process a single markdown file using Pydantic models."""
        return CharacterRoleSuggester._suggest_roles_for_path(Path(file_path))

    @staticmethod
    def enhance_panel_with_roles(
        doc: MarkdownDocument, panel_number: int
    ) -> Optional[ComicPanelImageSheet]:
        """Create a ComicPanelImageSheet with suggested roles and speech bubbles."""
        # Import required modules
        from datetime import datetime
        from pathlib import Path

        from services.openai_service import (
            generate_speech_for_characters,
            suggest_character_roles_for_panels,
        )

        panel = None
        for element in doc.chapter_model.document_elements:
            if (
                isinstance(element, PanelPydantic)
                and element.panel_number_in_doc == panel_number
            ):
                panel = element
                break

        if not panel:
            return None

        # Extract section content
        sections = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
        scene = sections.get(SECTION_TITLES.SCENE_DESCRIPTION.value, "")
        teaching = sections.get(SECTION_TITLES.TEACHING_NARRATIVE.value, "")
        common_example = sections.get(SECTION_TITLES.COMMON_EXAMPLE.value, "")

        if not scene and not teaching:
            return None

        # Get role suggestions
        panel_input = {
            "title": panel.panel_title_text,
            "scene": scene,
            "teaching": teaching,
        }
        roles_dict = suggest_character_roles_for_panels([panel_input])
        roles = roles_dict.get(panel.panel_title_text, [])

        # Create ComicPanelImageSheet
        panel_sheet = ComicPanelImageSheet(
            panel_id=f"panel_{panel.panel_number_in_doc}",
            chapter_id=Path(doc.filepath).stem if doc.filepath else None,
            panel_index=panel.panel_number_in_doc,
            scene_description_original=scene,
            teaching_narrative_original=teaching,
            common_example_original=common_example,
            processing_metadata={
                "processed_by": "CharacterRoleSuggester",
                "timestamp": datetime.utcnow().isoformat(),
                "suggested_roles": roles,
            },
        )

        # Generate character profiles from roles
        character_profiles = []
        for role in roles:
            character_profiles.append(
                {
                    "name": f"{role}",  # Use role as placeholder name
                    "role": role,
                    "tone": "professional",  # Default tone
                }
            )

        # Generate speech bubbles
        if character_profiles:
            speech_result = generate_speech_for_characters(scene, character_profiles)

            # Create SpeechBubble objects
            for char_name, speech_data in speech_result.items():
                bubble = SpeechBubble(
                    character_name=char_name,
                    role=next(
                        (
                            p["role"]
                            for p in character_profiles
                            if p["name"] == char_name
                        ),
                        "Unknown",
                    ),
                    speech=speech_data.get("text", ""),
                    interface=speech_data.get("interface", "in_person"),
                )
                panel_sheet.speech_bubbles.append(bubble)

        # Create a basic scene enhancement
        from services.openai_service import rewrite_scene_and_teaching_as_summary

        enhanced_scene = rewrite_scene_and_teaching_as_summary(scene, teaching)

        enhancement = SceneEnhancement(
            version_id="roles-v1",
            scene_text=enhanced_scene,
            llm_metadata={
                "scene_theme": "auto",
                "generated_roles": roles,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        panel_sheet.scene_enhancements.append(enhancement)
        panel_sheet.current_scene_enhancement = "roles-v1"

        return panel_sheet

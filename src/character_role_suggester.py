# character_role_suggester.py (batch-optimized)

from pathlib import Path
from typing import Dict, List

from markdown_document import MarkdownDocument
from openai_service import suggest_character_roles_for_panels
from models.section_titles import SECTION_TITLES


class CharacterRoleSuggester:
    @staticmethod
    def _suggest_roles_for_path(md_path: Path) -> Dict[str, Dict[str, List[str]]]:
        if not md_path.exists() or not md_path.is_file():
            raise ValueError(f"File {md_path} not found or is not a file.")
        doc = MarkdownDocument()
        if not doc.load_and_process(str(md_path)):
            raise ValueError(f"Failed to load document from {md_path}.")
        panel_inputs = []
        panel_titles = []
        for panel in doc.list_panels():
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
            return {md_path.name: {}}
        # Batch OpenAI call for all panels in the file
        role_dict = suggest_character_roles_for_panels(panel_inputs)
        return {
            md_path.name: {title: role_dict.get(title, []) for title in panel_titles}
        }

    @staticmethod
    def suggest_roles_for_folder(folder_path: str) -> Dict[str, Dict[str, List[str]]]:
        folder = Path(folder_path)
        result = {}
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Folder {folder_path} not found or is not a directory.")
        for file in folder.glob("*.md"):
            try:
                file_roles = CharacterRoleSuggester._suggest_roles_for_path(file)
                result.update(file_roles)
            except Exception as e:
                # Optionally log or handle per-file errors here
                continue
        return result

    @staticmethod
    def suggest_character_roles_in_file(
        file_path: str,
    ) -> Dict[str, Dict[str, List[str]]]:
        return CharacterRoleSuggester._suggest_roles_for_path(Path(file_path))

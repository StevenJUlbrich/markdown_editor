# character_role_suggester.py

from pathlib import Path
from typing import Dict, List

from MarkdownDocument import MarkdownDocument
from openai_service import suggest_character_roles_from_context


class CharacterRoleSuggester:
    @staticmethod
    def _suggest_roles_for_path(md_path: Path) -> Dict[str, Dict[str, List[str]]]:
        if not md_path.exists() or not md_path.is_file():
            raise ValueError(f"File {md_path} not found or is not a file.")
        doc = MarkdownDocument()
        if not doc.load_and_process(str(md_path)):
            raise ValueError(f"Failed to load document from {md_path}.")
        file_result = {}
        for panel in doc.list_panels():
            sections = doc.extract_named_sections_from_panel(panel.panel_number_in_doc)
            scene = sections.get("Scene Description", "")
            teaching = sections.get("Teaching Narrative", "")
            if not scene and not teaching:
                continue
            roles = suggest_character_roles_from_context(
                panel_title=panel.panel_title_text,
                scene_description_md=scene,
                teaching_narrative_md=teaching,
            )
            file_result[panel.panel_title_text] = roles
        return {md_path.name: file_result}

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

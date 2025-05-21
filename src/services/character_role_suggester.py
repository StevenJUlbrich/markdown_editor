# character_role_suggester.py (updated)

from pathlib import Path
from typing import Dict, List

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

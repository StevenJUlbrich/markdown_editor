# document_model.py
from typing import Any, Dict, List, Optional, Set, Union

from mistletoe import Document
from mistletoe.block_token import BlockCode, BlockToken, Heading, Paragraph
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText  # Ensure RawText is imported
from pydantic import BaseModel, Field

from logging_config import setup_logging

setup_logging()


def _strip_outer_markdown_fences(markdown_text: str) -> str:
    """
    Strips common outer markdown code fences (```markdown ... ``` or ``` ... ```).
    """
    processed_text = markdown_text.strip()
    lines = processed_text.splitlines()

    if len(lines) >= 2:  # Needs at least two lines for fences (e.g., ```\n```)
        starts_with_fence = lines[0].startswith("```")
        ends_with_fence = lines[-1] == "```"

        if starts_with_fence and ends_with_fence:
            # Remove "markdown" language specifier if present on the first line
            if lines[0].startswith("```markdown"):
                # Check if it's just ```markdown or ```markdown followed by content on the same line
                # This simple version assumes ```markdown is on its own line or only has whitespace after.
                # A more robust regex might be needed for complex cases.
                pass  # Handled by slicing [1:-1]

            # Join the content between the fences
            content_between_fences = "\n".join(lines[1:-1])
            return content_between_fences.strip()
    return processed_text  # Return original (stripped of outer whitespace) if not clearly fenced


# --- Helper Function ---
def get_heading_text(heading_node: Heading) -> str:
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):
                text += child.content
    return text.strip()


def render_blocks_to_markdown(
    blocks: List[BlockToken], renderer: MarkdownRenderer
) -> str:
    if not blocks:
        return ""
    valid_blocks = [b for b in blocks if b is not None and isinstance(b, BlockToken)]
    if not valid_blocks:
        return ""
    temp_doc = Document("")
    try:
        temp_doc.children = valid_blocks
    except Exception as e:
        print(f"Error assigning children in render_blocks_to_markdown: {e}")
        print(f"Problematic valid_blocks (first 5): {valid_blocks[:5]}")
        return "Error: Could not render blocks."
    return renderer.render(temp_doc).strip()


_MODULE_LEVEL_RENDERER_INSTANCE: Optional[MarkdownRenderer] = None
try:
    _MODULE_LEVEL_RENDERER_INSTANCE = MarkdownRenderer()
    print(
        "INFO: Module-level MarkdownRenderer instantiated successfully during import of document_model."
    )
except Exception as e:
    print(
        f"CRITICAL ERROR during import: Could not instantiate module-level MarkdownRenderer: {e}"
    )
    print("Further Mistletoe operations will likely fail.")


class SceneAnalysisPydantic(BaseModel):
    scene_types: List[str]
    inferred_by_ai: bool = True
    raw_summary: Optional[str] = None
    location: Optional[str] = None
    time_of_day: Optional[str] = None
    tone: Optional[str] = None  # calm, tense, reflective, chaotic, etc.
    teaching_level: Optional[str] = None  # basic, advanced, metaphorical, meta
    notes: Optional[str] = None


# --- Pydantic Models ---
class H4Pydantic(BaseModel):
    heading_text: str
    mistletoe_h4_block: Optional[Any] = None
    content_markdown: str = ""
    h4_number_in_h3: int


class H3Pydantic(BaseModel):
    heading_text: str
    mistletoe_h3_block: Optional[Any] = None
    initial_content_markdown: str = ""
    h4_sections: List[H4Pydantic] = Field(default_factory=list)
    original_full_markdown: str = ""
    api_suggested_enhancement_needed: Optional[bool] = None
    api_suggested_enhancement_type: Optional[str] = None
    api_suggested_enhancement_reason: Optional[str] = None
    api_improved_markdown: Optional[str] = None
    h3_number_in_panel: int


class PanelPydantic(BaseModel):
    panel_title_text: str
    mistletoe_h2_block: Optional[Any] = None
    h3_sections: List[H3Pydantic] = Field(default_factory=list)
    panel_number_in_doc: Optional[int] = None
    scene_analysis: Optional[SceneAnalysisPydantic] = None


class GenericContentPydantic(BaseModel):
    content_markdown: str
    mistletoe_blocks: List[Any] = Field(default_factory=list)
    title_text: Optional[str] = None


class ChapterPydantic(BaseModel):
    chapter_title_text: str
    mistletoe_h1_block: Optional[Any] = None
    document_elements: List[Union[GenericContentPydantic, PanelPydantic]] = Field(
        default_factory=list
    )

    def get_scene_distribution(self) -> Dict[str, int]:
        counts = {}
        for el in self.document_elements:
            if isinstance(el, PanelPydantic) and el.scene_analysis:
                for tag in el.scene_analysis.scene_types:
                    counts[tag] = counts.get(tag, 0) + 1
        return counts


# --- Main Document Class ---
class MarkdownDocument:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath: Optional[str] = filepath
        self.raw_content: Optional[str] = None
        self.mistletoe_doc: Optional[Document] = None
        self.chapter_model: Optional[ChapterPydantic] = None

        if _MODULE_LEVEL_RENDERER_INSTANCE is None:
            raise RuntimeError(
                "Mistletoe MarkdownRenderer could not be initialized at the module level. Cannot proceed."
            )
        self.renderer: MarkdownRenderer = _MODULE_LEVEL_RENDERER_INSTANCE

        if filepath:
            self.load_and_process(filepath)

    def _is_paragraph_effectively_empty(self, p_block: BlockToken) -> bool:
        """Checks if a Paragraph block is empty or contains only whitespace."""
        if isinstance(p_block, Paragraph):
            if not p_block.children:  # Truly empty <p></p>
                return True
            # Check if all children are RawText and their content is whitespace
            for child in p_block.children:
                if isinstance(child, RawText):
                    if child.content.strip() != "":
                        return False  # Found non-whitespace RawText
                else:
                    return False  # Found a non-RawText span token (e.g., Emphasis)
            return True  # All children were RawText and all were whitespace
        return False

    def load_and_process(self, filepath: str) -> bool:
        self.filepath = filepath
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.raw_content = f.read()
            print(f"INFO: Successfully loaded '{self.filepath}'.")
        except FileNotFoundError:
            print(f"ERROR: File not found at '{self.filepath}'")
            self.raw_content = None
            return False
        except Exception as e:
            print(f"ERROR: Error reading file '{self.filepath}': {e}")
            self.raw_content = None
            return False

        if self.raw_content:
            self._parse_to_mistletoe_ast()
            self._build_pydantic_model()
            if not self.mistletoe_doc or not self.mistletoe_doc.children:
                print("WARNING: Document was loaded but Mistletoe AST is empty.")
            elif not self.chapter_model or not self.chapter_model.document_elements:
                print(
                    "WARNING: Document parsed, but Pydantic chapter model is empty or has no elements."
                )
        return True

    def _parse_to_mistletoe_ast(self):
        if self.raw_content:
            self.mistletoe_doc = Document(self.raw_content)
            print("INFO: Document parsed to Mistletoe AST.")

    def _build_pydantic_model(self):
        if not self.mistletoe_doc or not self.mistletoe_doc.children:
            print("ERROR: Mistletoe AST is empty, cannot build Pydantic model.")
            return

        doc_elements: List[Union[GenericContentPydantic, PanelPydantic]] = []
        current_generic_blocks: List[BlockToken] = []
        chapter_h1_block_node: Optional[Heading] = None
        chapter_title = "Untitled Chapter"
        panel_counter = 0

        if (
            self.mistletoe_doc.children
            and isinstance(self.mistletoe_doc.children[0], Heading)
            and self.mistletoe_doc.children[0].level == 1
        ):
            chapter_h1_block_node = self.mistletoe_doc.children[0]
            chapter_title = get_heading_text(chapter_h1_block_node)
            start_index = 1
        else:
            start_index = 0

        all_top_level_blocks_to_process = self.mistletoe_doc.children[start_index:]

        current_block_index = 0
        while current_block_index < len(all_top_level_blocks_to_process):
            block = all_top_level_blocks_to_process[current_block_index]
            is_h2_panel_heading = False
            panel_title_text = ""
            panel_h2_block_node = None

            if isinstance(block, Heading) and block.level == 2:
                heading_text = get_heading_text(block)
                if heading_text.startswith("Panel "):
                    is_h2_panel_heading = True
                    panel_title_text = heading_text
                    panel_h2_block_node = block

            if is_h2_panel_heading and panel_h2_block_node:
                if current_generic_blocks:
                    generic_title = None
                    if current_generic_blocks and isinstance(
                        current_generic_blocks[0], Heading
                    ):
                        generic_title = get_heading_text(current_generic_blocks[0])
                    generic_md = render_blocks_to_markdown(
                        current_generic_blocks, self.renderer
                    )
                    doc_elements.append(
                        GenericContentPydantic(
                            content_markdown=generic_md,
                            mistletoe_blocks=list(current_generic_blocks),
                            title_text=generic_title,
                        )
                    )
                    current_generic_blocks = []

                panel_counter += 1
                panel_content_blocks_for_h3s: List[BlockToken] = []
                current_block_index += 1

                while current_block_index < len(all_top_level_blocks_to_process):
                    next_block_in_panel = all_top_level_blocks_to_process[
                        current_block_index
                    ]
                    is_next_block_another_panel_h2 = False
                    if (
                        isinstance(next_block_in_panel, Heading)
                        and next_block_in_panel.level == 2
                    ):
                        if get_heading_text(next_block_in_panel).startswith("Panel "):
                            is_next_block_another_panel_h2 = True
                    if is_next_block_another_panel_h2:
                        break
                    panel_content_blocks_for_h3s.append(next_block_in_panel)
                    current_block_index += 1

                panel_h3_sections = self._parse_h3_sections_from_panel_blocks(
                    panel_content_blocks_for_h3s
                )
                doc_elements.append(
                    PanelPydantic(
                        panel_title_text=panel_title_text,
                        mistletoe_h2_block=panel_h2_block_node,
                        h3_sections=panel_h3_sections,
                        panel_number_in_doc=panel_counter,
                    )
                )
            else:
                current_generic_blocks.append(block)
                current_block_index += 1

        if current_generic_blocks:
            generic_title = None
            if current_generic_blocks and isinstance(
                current_generic_blocks[0], Heading
            ):
                generic_title = get_heading_text(current_generic_blocks[0])
            generic_md = render_blocks_to_markdown(
                current_generic_blocks, self.renderer
            )
            doc_elements.append(
                GenericContentPydantic(
                    content_markdown=generic_md,
                    mistletoe_blocks=list(current_generic_blocks),
                    title_text=generic_title,
                )
            )

        self.chapter_model = ChapterPydantic(
            chapter_title_text=chapter_title,
            mistletoe_h1_block=chapter_h1_block_node,
            document_elements=doc_elements,
        )
        if self.chapter_model:
            print(
                f"INFO: Pydantic model built for '{self.chapter_model.chapter_title_text}' with {len(self.chapter_model.document_elements)} elements."
            )
            if not self._validate_internal_ids():
                print(
                    "WARNING: Internal ID validation failed after building Pydantic model. Structure may be inconsistent."
                )
        else:
            print("ERROR: Pydantic chapter model could not be built.")

    def _parse_h3_sections_from_panel_blocks(
        self, panel_content_blocks: List[BlockToken]
    ) -> List[H3Pydantic]:
        h3_pydantic_list: List[H3Pydantic] = []
        current_h3_content_blocks_for_h4s: List[BlockToken] = []
        active_h3_title = "Initial Content"
        active_h3_block_node: Optional[Heading] = None
        h3_counter_in_panel = 0

        if not panel_content_blocks:
            h3_counter_in_panel += 1
            h3_pydantic_list.append(
                H3Pydantic(
                    heading_text=active_h3_title,
                    mistletoe_h3_block=None,
                    initial_content_markdown="",
                    h4_sections=[],
                    original_full_markdown="",
                    h3_number_in_panel=h3_counter_in_panel,
                )
            )
            return h3_pydantic_list

        block_idx = 0
        while block_idx < len(panel_content_blocks):
            block = panel_content_blocks[block_idx]
            is_h3_heading = False

            if isinstance(block, Heading) and block.level == 3:
                is_h3_heading = True

            if is_h3_heading:
                if active_h3_block_node or (
                    active_h3_title == "Initial Content"
                    and current_h3_content_blocks_for_h4s
                ):
                    h3_counter_in_panel += 1

                    expected_h3_text_for_unwrap = (
                        active_h3_title if active_h3_block_node else None
                    )

                    cleaned_h3_content_blocks = [
                        block
                        for block in current_h3_content_blocks_for_h4s
                        if not self._is_paragraph_effectively_empty(block)
                    ]
                    initial_md_for_prev_h3, h4s_for_prev_h3 = (
                        self._parse_h4_sections_from_h3_blocks(
                            cleaned_h3_content_blocks
                        )
                    )

                    temp_h3_blocks_for_render = []
                    if active_h3_block_node:
                        temp_h3_blocks_for_render.append(active_h3_block_node)
                    if initial_md_for_prev_h3:
                        temp_doc_initial = Document(initial_md_for_prev_h3)
                        temp_h3_blocks_for_render.extend(
                            b
                            for b in temp_doc_initial.children
                            if isinstance(b, BlockToken)
                        )
                    for h4_sec in h4s_for_prev_h3:
                        if h4_sec.mistletoe_h4_block:
                            temp_h3_blocks_for_render.append(h4_sec.mistletoe_h4_block)
                        if h4_sec.content_markdown:
                            temp_doc_h4_content = Document(h4_sec.content_markdown)
                            temp_h3_blocks_for_render.extend(
                                b
                                for b in temp_doc_h4_content.children
                                if isinstance(b, BlockToken)
                            )

                    full_h3_md = render_blocks_to_markdown(
                        temp_h3_blocks_for_render, self.renderer
                    )
                    h3_pydantic_list.append(
                        H3Pydantic(
                            heading_text=active_h3_title,
                            mistletoe_h3_block=active_h3_block_node,
                            initial_content_markdown=initial_md_for_prev_h3,
                            h4_sections=h4s_for_prev_h3,
                            original_full_markdown=full_h3_md,
                            h3_number_in_panel=h3_counter_in_panel,
                        )
                    )

                active_h3_block_node = block
                active_h3_title = get_heading_text(active_h3_block_node)
                current_h3_content_blocks_for_h4s = []
                block_idx += 1
            else:
                current_h3_content_blocks_for_h4s.append(block)
                block_idx += 1

        if active_h3_block_node or current_h3_content_blocks_for_h4s:
            h3_counter_in_panel += 1
            expected_h3_text_for_unwrap_last = (
                active_h3_title if active_h3_block_node else None
            )
            cleaned_h3_content_blocks_last = [
                block
                for block in current_h3_content_blocks_for_h4s
                if not self._is_paragraph_effectively_empty(block)
            ]
            initial_md_for_last_h3, h4s_for_last_h3 = (
                self._parse_h4_sections_from_h3_blocks(cleaned_h3_content_blocks_last)
            )

            temp_h3_blocks_for_render_last = []
            if active_h3_block_node:
                temp_h3_blocks_for_render_last.append(active_h3_block_node)
            if initial_md_for_last_h3:
                temp_doc_initial_last = Document(initial_md_for_last_h3)
                temp_h3_blocks_for_render_last.extend(
                    b
                    for b in temp_doc_initial_last.children
                    if isinstance(b, BlockToken)
                )
            for h4_sec in h4s_for_last_h3:
                if h4_sec.mistletoe_h4_block:
                    temp_h3_blocks_for_render_last.append(h4_sec.mistletoe_h4_block)
                if h4_sec.content_markdown:
                    temp_doc_h4_content_last = Document(h4_sec.content_markdown)
                    temp_h3_blocks_for_render_last.extend(
                        b
                        for b in temp_doc_h4_content_last.children
                        if isinstance(b, BlockToken)
                    )

            full_h3_md = render_blocks_to_markdown(
                temp_h3_blocks_for_render_last, self.renderer
            )
            h3_pydantic_list.append(
                H3Pydantic(
                    heading_text=active_h3_title,
                    mistletoe_h3_block=active_h3_block_node,
                    initial_content_markdown=initial_md_for_last_h3,
                    h4_sections=h4s_for_last_h3,
                    original_full_markdown=full_h3_md,
                    h3_number_in_panel=h3_counter_in_panel,
                )
            )
        elif not h3_pydantic_list and panel_content_blocks:
            h3_counter_in_panel += 1
            cleaned_initial_blocks = [
                block
                for block in panel_content_blocks
                if not self._is_paragraph_effectively_empty(block)
            ]
            initial_md, h4s = self._parse_h4_sections_from_h3_blocks(
                cleaned_initial_blocks
            )
            temp_blocks_render = []
            if initial_md:
                temp_blocks_render.extend(Document(initial_md).children)
            for h4_sec in h4s:
                if h4_sec.mistletoe_h4_block:
                    temp_blocks_render.append(h4_sec.mistletoe_h4_block)
                if h4_sec.content_markdown:
                    temp_blocks_render.extend(
                        Document(h4_sec.content_markdown).children
                    )

            h3_pydantic_list.append(
                H3Pydantic(
                    heading_text="Initial Content",
                    mistletoe_h3_block=None,
                    initial_content_markdown=initial_md,
                    h4_sections=h4s,
                    original_full_markdown=render_blocks_to_markdown(
                        temp_blocks_render, self.renderer
                    ),
                    h3_number_in_panel=h3_counter_in_panel,
                )
            )
        return h3_pydantic_list

    def _parse_h4_sections_from_h3_blocks(
        self, h3_content_blocks: List[BlockToken]
    ) -> tuple[str, List[H4Pydantic]]:
        def process_active_h4_block():
            nonlocal h4_counter_in_h3, active_h4_block_node, current_h4_content_blocks
            if active_h4_block_node:
                h4_counter_in_h3 += 1
                expected_h4_text = get_heading_text(active_h4_block_node)
                cleaned_h4_content_blocks = [
                    block
                    for block in current_h4_content_blocks
                    if not self._is_paragraph_effectively_empty(block)
                ]
                h4_content_md = render_blocks_to_markdown(
                    cleaned_h4_content_blocks, self.renderer
                )
                h4_pydantic_list.append(
                    H4Pydantic(
                        heading_text=expected_h4_text,
                        mistletoe_h4_block=active_h4_block_node,
                        content_markdown=h4_content_md,
                        h4_number_in_h3=h4_counter_in_h3,
                    )
                )
                current_h4_content_blocks = []

        h4_pydantic_list: List[H4Pydantic] = []
        current_h4_content_blocks: List[BlockToken] = []
        initial_content_for_h3_blocks: List[BlockToken] = []
        active_h4_block_node: Optional[Heading] = None
        is_before_first_h4 = True
        h4_counter_in_h3 = 0

        if not h3_content_blocks:
            return "", []

        for block in h3_content_blocks:
            if isinstance(block, Heading) and block.level == 4:
                is_before_first_h4 = False
                process_active_h4_block()
                active_h4_block_node = block
            else:
                if is_before_first_h4:
                    initial_content_for_h3_blocks.append(block)
                else:
                    current_h4_content_blocks.append(block)

        process_active_h4_block()

        initial_content_markdown_for_h3 = render_blocks_to_markdown(
            initial_content_for_h3_blocks, self.renderer
        )
        return initial_content_markdown_for_h3, h4_pydantic_list

    def _validate_internal_ids(self) -> bool:
        # ... (same as document_model_targeted_enh_v1) ...
        if not self.chapter_model:
            print("VALIDATE_ID_ERROR: Chapter model not built. Cannot validate IDs.")
            return False

        is_valid = True
        panel_doc_numbers_seen: Set[int] = set()

        for element_idx, element in enumerate(self.chapter_model.document_elements):
            if isinstance(element, PanelPydantic):
                if element.panel_number_in_doc is None:
                    print(
                        f"VALIDATE_ID_WARNING: Panel '{element.panel_title_text}' (element #{element_idx}) is missing 'panel_number_in_doc'."
                    )
                    is_valid = False
                    continue
                if element.panel_number_in_doc in panel_doc_numbers_seen:
                    print(
                        f"VALIDATE_ID_WARNING: Duplicate 'panel_number_in_doc' {element.panel_number_in_doc} for Panel '{element.panel_title_text}'."
                    )
                    is_valid = False
                panel_doc_numbers_seen.add(element.panel_number_in_doc)

                h3_numbers_in_panel_seen: Set[int] = set()
                for h3_idx, h3_section in enumerate(element.h3_sections):
                    if h3_section.h3_number_in_panel is None:
                        print(
                            f"VALIDATE_ID_WARNING: H3 '{h3_section.heading_text}' (H3 #{h3_idx+1}) in Panel ID {element.panel_number_in_doc} is missing 'h3_number_in_panel'."
                        )
                        is_valid = False
                        continue
                    if h3_section.h3_number_in_panel in h3_numbers_in_panel_seen:
                        print(
                            f"VALIDATE_ID_WARNING: Duplicate 'h3_number_in_panel' {h3_section.h3_number_in_panel} in Panel ID {element.panel_number_in_doc}."
                        )
                        is_valid = False
                    h3_numbers_in_panel_seen.add(h3_section.h3_number_in_panel)

                    h4_numbers_in_h3_seen: Set[int] = set()
                    for h4_idx, h4_section in enumerate(h3_section.h4_sections):
                        if h4_section.h4_number_in_h3 is None:
                            print(
                                f"VALIDATE_ID_WARNING: H4 '{h4_section.heading_text}' (H4 #{h4_idx+1}) under H3 ID {h3_section.h3_number_in_panel} (Panel ID {element.panel_number_in_doc}) is missing 'h4_number_in_h3'."
                            )
                            is_valid = False
                            continue
                        if h4_section.h4_number_in_h3 in h4_numbers_in_h3_seen:
                            print(
                                f"VALIDATE_ID_WARNING: Duplicate 'h4_number_in_h3' {h4_section.h4_number_in_h3} under H3 ID {h3_section.h3_number_in_panel} (Panel ID {element.panel_number_in_doc})."
                            )
                            is_valid = False
                        h4_numbers_in_h3_seen.add(h4_section.h4_number_in_h3)
        if is_valid:
            print("INFO: Internal ID validation passed.")
        return is_valid

    def list_all_h2_sections(self) -> List[Dict[str, Any]]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not self.chapter_model:
            return []
        sections = []
        overall_section_counter = 0
        for element in self.chapter_model.document_elements:
            overall_section_counter += 1
            title = f"Generic Section {overall_section_counter}"
            is_panel = False
            element_id = None
            if isinstance(element, GenericContentPydantic):
                title = (
                    element.title_text
                    if element.title_text
                    else f"Generic Content Block {overall_section_counter}"
                )
                element_id = f"generic-{overall_section_counter}"
            elif isinstance(element, PanelPydantic):
                title = element.panel_title_text
                is_panel = True
                element_id = element.panel_number_in_doc
            sections.append(
                {
                    "number": overall_section_counter,
                    "title": title,
                    "is_panel": is_panel,
                    "id": element_id,
                }
            )
        return sections

    def list_panels(self) -> List[PanelPydantic]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not self.chapter_model:
            return []
        return sorted(
            [
                el
                for el in self.chapter_model.document_elements
                if isinstance(el, PanelPydantic)
            ],
            key=lambda p: p.panel_number_in_doc or 0,
        )

    def get_panel_by_number(self, panel_doc_number: int) -> Optional[PanelPydantic]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not self.chapter_model:
            return None
        for element in self.chapter_model.document_elements:
            if (
                isinstance(element, PanelPydantic)
                and element.panel_number_in_doc == panel_doc_number
            ):
                return element
        return None

    def get_h3_by_number(
        self, panel: PanelPydantic, h3_panel_number: int
    ) -> Optional[H3Pydantic]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not panel:
            return None
        for h3_section in panel.h3_sections:
            if h3_section.h3_number_in_panel == h3_panel_number:
                return h3_section
        return None

    def get_h4_by_number(
        self, h3_section: H3Pydantic, h4_h3_number: int
    ) -> Optional[H4Pydantic]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not h3_section:
            return None
        for h4_section in h3_section.h4_sections:
            if h4_section.h4_number_in_h3 == h4_h3_number:
                return h4_section
        return None

    def list_h3_sections_in_panel(self, panel: PanelPydantic) -> List[Dict[str, Any]]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not panel:
            return []
        return [
            {"number": h3.h3_number_in_panel, "title": h3.heading_text, "h3_object": h3}
            for h3 in panel.h3_sections
        ]

    def list_targetable_sections_in_panel(
        self, panel: PanelPydantic
    ) -> List[Dict[str, Any]]:
        # ... (same as document_model_targeted_enh_v1) ...
        if not panel:
            return []
        targets = []
        current_display_number = 1
        targets.append(
            {
                "display_number": current_display_number,
                "type": "H2 Panel",
                "title": panel.panel_title_text,
                "panel_id": panel.panel_number_in_doc,
                "h3_id": None,
                "h4_id": None,
                "is_initial_content_for_h3": False,
            }
        )
        current_display_number += 1
        for h3_sec in panel.h3_sections:
            targets.append(
                {
                    "display_number": current_display_number,
                    "type": "H3 Sub-section",
                    "title": h3_sec.heading_text,
                    "panel_id": panel.panel_number_in_doc,
                    "h3_id": h3_sec.h3_number_in_panel,
                    "h4_id": None,
                    "is_initial_content_for_h3": False,
                }
            )
            current_display_number += 1
            if (
                h3_sec.initial_content_markdown
                and h3_sec.initial_content_markdown.strip()
            ):
                targets.append(
                    {
                        "display_number": current_display_number,
                        "type": "H3 Initial Content",
                        "title": f"{h3_sec.heading_text} (Initial Content)",
                        "panel_id": panel.panel_number_in_doc,
                        "h3_id": h3_sec.h3_number_in_panel,
                        "h4_id": None,
                        "is_initial_content_for_h3": True,
                    }
                )
                current_display_number += 1
            for h4_sec in h3_sec.h4_sections:
                targets.append(
                    {
                        "display_number": current_display_number,
                        "type": "H4 Sub-sub-section",
                        "title": h4_sec.heading_text,
                        "panel_id": panel.panel_number_in_doc,
                        "h3_id": h3_sec.h3_number_in_panel,
                        "h4_id": h4_sec.h4_number_in_h3,
                        "is_initial_content_for_h3": False,
                    }
                )
                current_display_number += 1
        return targets

    # --- Getters for Content ---
    # ... (get_section_markdown_for_api, get_panel_full_markdown, get_h3_subsection_full_markdown,
    #      get_h4_subsubsection_full_markdown remain the same as document_model_targeted_enh_v1)
    def get_section_markdown_for_api(
        self,
        panel_id: int,
        h3_id_in_panel: Optional[int] = None,
        h4_id_in_h3: Optional[int] = None,
        is_initial_content_target: bool = False,
    ) -> Optional[str]:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            return f"Error: Panel ID '{panel_id}' not found."
        if h3_id_in_panel is None:
            return self.get_panel_full_markdown(panel)
        h3_section = self.get_h3_by_number(panel, h3_id_in_panel)
        if not h3_section:
            return (
                f"Error: H3 ID '{h3_id_in_panel}' not found in Panel ID '{panel_id}'."
            )
        if is_initial_content_target:
            return h3_section.initial_content_markdown
        if h4_id_in_h3 is None:
            return h3_section.original_full_markdown
        h4_section_model = self.get_h4_by_number(h3_section, h4_id_in_h3)
        if not h4_section_model:
            return (
                f"Error: H4 ID '{h4_id_in_h3}' not found in H3 ID '{h3_id_in_panel}'."
            )
        h4_blocks = []
        if h4_section_model.mistletoe_h4_block:
            h4_blocks.append(h4_section_model.mistletoe_h4_block)
        if h4_section_model.content_markdown:
            h4_blocks.extend(
                b
                for b in Document(h4_section_model.content_markdown).children
                if isinstance(b, BlockToken)
            )
        return render_blocks_to_markdown(h4_blocks, self.renderer)

    def get_panel_full_markdown(self, panel_data: PanelPydantic) -> str:
        if not panel_data or not isinstance(panel_data, PanelPydantic):
            return "Error: Invalid panel data provided."
        panel_blocks_to_render = []
        if panel_data.mistletoe_h2_block:
            panel_blocks_to_render.append(panel_data.mistletoe_h2_block)
        for h3_item in panel_data.h3_sections:
            if h3_item.original_full_markdown:
                temp_h3_doc = Document(h3_item.original_full_markdown)
                valid_children = [
                    b
                    for b in temp_h3_doc.children
                    if b is not None and isinstance(b, BlockToken)
                ]
                panel_blocks_to_render.extend(valid_children)
        if not panel_blocks_to_render and panel_data.mistletoe_h2_block is None:
            return f"Panel '{panel_data.panel_title_text}' appears empty."
        elif not panel_blocks_to_render and panel_data.mistletoe_h2_block:
            return render_blocks_to_markdown(
                [panel_data.mistletoe_h2_block], self.renderer
            )
        return render_blocks_to_markdown(panel_blocks_to_render, self.renderer)

    def get_h3_subsection_full_markdown(self, h3_subsection_data: H3Pydantic) -> str:
        if not h3_subsection_data or not isinstance(h3_subsection_data, H3Pydantic):
            return "Error: Invalid H3 subsection data provided."
        return h3_subsection_data.original_full_markdown

    def get_h4_subsubsection_full_markdown(
        self, h4_subsubsection_data: H4Pydantic
    ) -> str:
        if not h4_subsubsection_data or not isinstance(
            h4_subsubsection_data, H4Pydantic
        ):
            return "Error: Invalid H4 sub-subsection data provided."
        h4_blocks_to_render = []
        if h4_subsubsection_data.mistletoe_h4_block:
            h4_blocks_to_render.append(h4_subsubsection_data.mistletoe_h4_block)
        if h4_subsubsection_data.content_markdown:
            temp_h4_content_doc = Document(h4_subsubsection_data.content_markdown)
            valid_children = [
                b
                for b in temp_h4_content_doc.children
                if b is not None and isinstance(b, BlockToken)
            ]
            h4_blocks_to_render.extend(valid_children)
        if not h4_blocks_to_render:
            return (
                render_blocks_to_markdown(
                    [h4_subsubsection_data.mistletoe_h4_block], self.renderer
                )
                if h4_subsubsection_data.mistletoe_h4_block
                else ""
            )
        return render_blocks_to_markdown(h4_blocks_to_render, self.renderer)

    # --- New Methods for Targeted Enhancement ---
    def extract_named_sections_from_panel(self, panel_id: int) -> Dict[str, str]:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            print(
                f"ERROR: Panel ID {panel_id} not found for extracting named sections."
            )
            return {}
        known_section_titles = [
            "Scene Description",
            "Teaching Narrative",
            "Common Example of the Problem",
            "SRE Best Practice: Evidence-Based Investigation",
            "Banking Impact",
            "Implementation Guidance",
        ]
        extracted_sections: Dict[str, str] = {
            title: "" for title in known_section_titles
        }
        for h3_section in panel.h3_sections:
            normalized_h3_title = h3_section.heading_text.strip()
            if normalized_h3_title in extracted_sections:
                extracted_sections[normalized_h3_title] = (
                    h3_section.original_full_markdown
                )
        return extracted_sections

    def update_named_section_in_panel(
        self, panel_id: int, section_h3_title: str, new_markdown_content: str
    ) -> bool:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            print(
                f"ERROR: Panel ID {panel_id} not found for updating named section '{section_h3_title}'."
            )
            return False
        target_h3_section: Optional[H3Pydantic] = None
        for h3 in panel.h3_sections:
            if h3.heading_text.strip() == section_h3_title.strip():
                target_h3_section = h3
                break
        if not target_h3_section:
            print(
                f"ERROR: H3 section with title '{section_h3_title}' not found in Panel ID {panel_id}."
            )
            return False
        cleaned = self._sanitize_markdown(section_h3_title, new_markdown_content)

        # Check if the heading was preserved and add it if missing
        if not cleaned.strip().startswith(f"### {section_h3_title}"):
            cleaned = f"### {section_h3_title}\n\n{cleaned}"

        target_h3_section.api_improved_markdown = cleaned
        target_h3_section.api_suggested_enhancement_needed = True
        print(
            f"INFO: API improved markdown set for H3 '{section_h3_title}' in Panel ID {panel_id}."
        )
        return True

    def update_h3_section_with_api_suggestions(
        self,
        panel_id: int,
        h3_id_in_panel: int,
        should_enhance: Optional[bool],
        enhancement_type: Optional[str],
        enhancement_reason: Optional[str],
    ) -> bool:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            print(f"ERROR: Panel ID '{panel_id}' not found.")
            return False
        h3 = self.get_h3_by_number(panel, h3_id_in_panel)
        if not h3:
            print(
                f"ERROR: H3 ID '{h3_id_in_panel}' not found in Panel ID '{panel_id}'."
            )
            return False
        h3.api_suggested_enhancement_needed = should_enhance
        h3.api_suggested_enhancement_type = enhancement_type
        h3.api_suggested_enhancement_reason = enhancement_reason
        print(
            f"INFO: API suggestions for H3 ID '{h3.h3_number_in_panel}' ('{h3.heading_text}') recorded."
        )
        return True

    def update_h3_section_with_improved_markdown(
        self, panel_id: int, h3_id_in_panel: int, improved_markdown: str
    ) -> bool:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            print(f"ERROR: Panel ID '{panel_id}' not found.")
            return False
        h3 = self.get_h3_by_number(panel, h3_id_in_panel)
        if not h3:
            print(f"ERROR: H3 ID '{h3_id_in_panel}' not found.")
            return False

        cleaned = self._sanitize_markdown(h3.heading_text, improved_markdown)
        h3.api_improved_markdown = cleaned
        print(f"INFO: Cleaned and stored improved markdown for H3 '{h3.heading_text}'")
        return True

    def update_target_content(
        self,
        panel_id: int,
        new_markdown_content: str,
        h3_id_in_panel: Optional[int] = None,
        h4_id_in_h3: Optional[int] = None,
        is_h3_initial_content_target: bool = False,
    ) -> bool:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            print(f"ERROR: Panel ID '{panel_id}' not found.")
            return False

        if h3_id_in_panel is None:  # Updating H2 Panel (entire panel content)
            # This part already re-parses H3s. Consider if new_markdown_content here also needs fence stripping.
            # For now, focusing on the H3 update case as per the problem.
            print(f"WARNING: Replacing entire content of Panel ID '{panel_id}'.")
            # Potentially apply _strip_outer_markdown_fences to new_markdown_content here too if panels can be wrapped
            temp_doc_for_new_panel_content = Document(new_markdown_content)
            new_h3_sections = self._parse_h3_sections_from_panel_blocks(
                list(temp_doc_for_new_panel_content.children)  # Ensure it's a list
            )
            panel.h3_sections = new_h3_sections
            print(f"INFO: Entire content of Panel ID '{panel_id}' replaced.")
            return True

        h3_section = self.get_h3_by_number(panel, h3_id_in_panel)
        if not h3_section:
            print(
                f"ERROR: H3 ID '{h3_id_in_panel}' not found in Panel ID '{panel_id}'."
            )
            return False

        if is_h3_initial_content_target:
            # Initial content is usually smaller; direct assignment is often fine,
            # but stripping could be applied here too if users paste fenced blocks.
            h3_section.initial_content_markdown = _strip_outer_markdown_fences(
                new_markdown_content
            )
            h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
                h3_section
            )
            print(f"INFO: Initial content of H3 ID '{h3_id_in_panel}' updated.")
            return True

        if h4_id_in_h3 is None:  # This means updating an entire H3 section's content
            # Apply fence stripping to the incoming Markdown for the H3 section
            processed_h3_content = _strip_outer_markdown_fences(new_markdown_content)

            temp_doc_new_h3 = Document(processed_h3_content)
            if not (
                temp_doc_new_h3.children
                and isinstance(temp_doc_new_h3.children[0], Heading)
                and temp_doc_new_h3.children[0].level == 3
            ):
                print(
                    f"ERROR: New content for H3 ID '{h3_id_in_panel}' must start with an H3 heading (after potential fence stripping)."
                )
                return False

            h3_section.original_full_markdown = (
                processed_h3_content  # Store the processed (stripped) content
            )
            h3_section.mistletoe_h3_block = temp_doc_new_h3.children[0]
            h3_section.heading_text = get_heading_text(h3_section.mistletoe_h3_block)

            h3_content_blocks_for_h4_parsing = list(
                temp_doc_new_h3.children[1:]
            )  # Ensure it's a list
            (
                h3_section.initial_content_markdown,
                h3_section.h4_sections,
            ) = self._parse_h4_sections_from_h3_blocks(h3_content_blocks_for_h4_parsing)
            print(
                f"INFO: Entire H3 section ID '{h3_id_in_panel}' updated and re-parsed with potentially stripped fences."
            )
            return True

        # H4 content update
        h4_section = self.get_h4_by_number(h3_section, h4_id_in_h3)
        if not h4_section:
            print(
                f"ERROR: H4 ID '{h4_id_in_h3}' not found in H3 ID '{h3_id_in_panel}'."
            )
            return False
        # H4 content is typically just paragraphs, lists, etc., not a full fenced block.
        # But stripping could be added here if necessary.
        h4_section.content_markdown = _strip_outer_markdown_fences(new_markdown_content)
        h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
            h3_section
        )
        print(
            f"INFO: Content of H4 ID '{h4_id_in_h3}' in H3 ID '{h3_id_in_panel}' updated."
        )
        return True

    def add_content_to_target(
        self,
        panel_id: int,
        new_markdown_content: str,
        position: str = "end",
        h3_id_in_panel: Optional[int] = None,
        h4_id_in_h3: Optional[int] = None,
        is_h3_initial_content_target: bool = False,
    ) -> bool:
        panel = self.get_panel_by_number(panel_id)
        if not panel:
            print(f"ERROR: Panel ID '{panel_id}' not found.")
            return False
        if h3_id_in_panel is None:
            print(
                "ERROR: Cannot directly add content to H2 Panel this way. Target H3 or H4."
            )
            return False
        h3_section = self.get_h3_by_number(panel, h3_id_in_panel)
        if not h3_section:
            print(f"ERROR: H3 ID '{h3_id_in_panel}' not found.")
            return False
        target_name = ""
        modified = False
        if is_h3_initial_content_target:
            if position == "start":
                h3_section.initial_content_markdown = (
                    new_markdown_content + "\n" + h3_section.initial_content_markdown
                )
            else:
                h3_section.initial_content_markdown = (
                    h3_section.initial_content_markdown + "\n" + new_markdown_content
                ).strip()
            target_name = f"H3 ID '{h3_id_in_panel}' (Initial Content)"
            modified = True
        elif h4_id_in_h3 is not None:
            h4_section = self.get_h4_by_number(h3_section, h4_id_in_h3)
            if not h4_section:
                print(f"ERROR: H4 ID '{h4_id_in_h3}' not found.")
                return False
            if position == "start":
                h4_section.content_markdown = (
                    new_markdown_content + "\n" + h4_section.content_markdown
                )
            else:
                h4_section.content_markdown = (
                    h4_section.content_markdown + "\n" + new_markdown_content
                ).strip()
            target_name = f"H4 ID '{h4_id_in_h3}'"
            modified = True
        else:
            print(
                "ERROR: Target for adding content (H3 Initial or H4) not clearly specified."
            )
            return False
        if modified:
            h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
                h3_section
            )
            print(
                f"INFO: Successfully added content to {target_name} (position: {position})."
            )
        return modified

    def _regenerate_h3_full_markdown(self, h3_section: H3Pydantic) -> str:
        blocks_for_render = []
        if h3_section.mistletoe_h3_block:
            blocks_for_render.append(h3_section.mistletoe_h3_block)

        if h3_section.initial_content_markdown:
            content_lines = h3_section.initial_content_markdown.strip().splitlines()
            heading_line = f"### {h3_section.heading_text.strip().lower()}"
            if content_lines and content_lines[0].strip().lower() == heading_line:
                content_lines = content_lines[1:]
            content = "\n".join(content_lines).strip()
            initial_content_doc = Document(content)
            blocks_for_render.extend(
                b for b in initial_content_doc.children if isinstance(b, BlockToken)
            )

        for h4_s in h3_section.h4_sections:
            if h4_s.mistletoe_h4_block:
                blocks_for_render.append(h4_s.mistletoe_h4_block)
            if h4_s.content_markdown:
                h4_content_doc = Document(h4_s.content_markdown)
                blocks_for_render.extend(
                    b for b in h4_content_doc.children if isinstance(b, BlockToken)
                )

        return render_blocks_to_markdown(blocks_for_render, self.renderer)

    # document_model.py
    def _sanitize_markdown(self, heading_text: str, markdown: str) -> str:
        # Imports like `from mistletoe import Document` are typically at the module level.
        # If `BlockCode` and `Heading` are only used here, their import can stay,
        # but `MarkdownRenderer` import is not needed if using `self.renderer`.

        cleaned = markdown.strip()
        if cleaned.startswith("```markdown") or cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) > 2 and lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:-1]).strip()

        # It's good practice to ensure Document is imported if not already at module top
        # from mistletoe import Document (if not already globally available)
        # from mistletoe.block_token import BlockCode, Heading (if not already globally)

        original_doc = Document(cleaned)
        lower_heading = heading_text.strip().lower()

        filtered_blocks = []
        for block in original_doc.children:
            if isinstance(block, Heading) and block.level == 3:
                block_heading = get_heading_text(block).strip().lower()
                if block_heading == lower_heading:
                    continue
            if isinstance(block, BlockCode):  # Make sure BlockCode is imported
                continue
            filtered_blocks.append(block)

        new_doc = Document("")
        new_doc.children = filtered_blocks

        # Use the class's shared renderer instance instead of creating a new one.
        # No try/finally/close needed for the shared renderer here,
        # as its lifecycle isn't tied to this specific call.
        rendered = self.renderer.render(new_doc)

        return rendered.strip()

    def reconstruct_and_render_document(self) -> str:
        if not self.chapter_model:
            return self.raw_content or ""

        all_final_blocks: List[BlockToken] = (
            []
        )  # Ensure BlockToken is imported or defined

        if self.chapter_model.mistletoe_h1_block:
            all_final_blocks.append(self.chapter_model.mistletoe_h1_block)

        for element in self.chapter_model.document_elements:
            if isinstance(element, GenericContentPydantic):
                if element.mistletoe_blocks:
                    all_final_blocks.extend(
                        b
                        for b in element.mistletoe_blocks
                        if b is not None and isinstance(b, BlockToken)
                    )
                elif element.content_markdown:
                    generic_doc = Document(element.content_markdown)  # Original logic
                    all_final_blocks.extend(
                        b
                        for b in generic_doc.children
                        if b is not None and isinstance(b, BlockToken)
                    )
            elif isinstance(element, PanelPydantic):
                if element.mistletoe_h2_block:
                    all_final_blocks.append(element.mistletoe_h2_block)

                for h3_section in element.h3_sections:
                    content_string_for_h3 = None
                    if h3_section.api_improved_markdown is not None:
                        content_string_for_h3 = h3_section.api_improved_markdown
                    elif (
                        h3_section.original_full_markdown
                    ):  # Ensure this field exists and is the one to use
                        content_string_for_h3 = h3_section.original_full_markdown

                    if content_string_for_h3:
                        h3_doc = Document(content_string_for_h3)
                        all_final_blocks.extend(
                            b
                            for b in h3_doc.children
                            if b is not None and isinstance(b, BlockToken)
                        )
                    else:
                        pass

        return render_blocks_to_markdown(all_final_blocks, self.renderer)

    def save_document(self, output_filepath: str) -> bool:
        rendered_content = self.reconstruct_and_render_document()
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            print(f"INFO: Document successfully saved to '{output_filepath}'.")
            return True
        except Exception as e:
            print(f"ERROR: Error saving document to '{output_filepath}': {e}")
            return False

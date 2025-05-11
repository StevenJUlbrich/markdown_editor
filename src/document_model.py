# document_model.py
from typing import Any, Dict, List, Optional, Union

from mistletoe import Document
from mistletoe.block_token import BlockToken, Heading, Paragraph
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText
from pydantic import BaseModel, Field


# --- Helper Function ---
def get_heading_text(heading_node: Heading) -> str:
    """Extracts the plain text from a Mistletoe Heading node."""
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):
                text += child.content
    return text.strip()


def render_blocks_to_markdown(
    blocks: List[BlockToken], renderer: Optional[MarkdownRenderer] = None
) -> str:
    """Renders a list of Mistletoe block tokens to a Markdown string, filtering out None values."""
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

    active_renderer = renderer if renderer else MarkdownRenderer()
    return active_renderer.render(temp_doc).strip()


# --- Pydantic Models ---
class H4Pydantic(BaseModel):
    heading_text: str
    mistletoe_h4_block: Optional[Any] = None
    content_markdown: str = ""


class H3Pydantic(BaseModel):
    heading_text: str
    mistletoe_h3_block: Optional[Any] = None
    initial_content_markdown: str = ""
    h4_sections: List[H4Pydantic] = Field(default_factory=list)
    original_full_markdown: str = ""
    api_improved_markdown: Optional[str] = None
    api_recommendation: Optional[str] = None
    api_reason: Optional[str] = None


class PanelPydantic(BaseModel):
    panel_title_text: str
    mistletoe_h2_block: Optional[Any] = None
    h3_sections: List[H3Pydantic] = Field(default_factory=list)
    # Add a unique identifier for selection by number
    panel_number_in_doc: Optional[int] = None


class GenericContentPydantic(BaseModel):
    content_markdown: str
    mistletoe_blocks: List[Any] = Field(default_factory=list)
    # Optional: Add a representative title if the first block is a heading
    title_text: Optional[str] = None


class ChapterPydantic(BaseModel):
    chapter_title_text: str
    mistletoe_h1_block: Optional[Any] = None
    document_elements: List[Union[GenericContentPydantic, PanelPydantic]] = Field(
        default_factory=list
    )


# --- Main Document Class ---
class MarkdownDocument:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath: Optional[str] = filepath
        self.raw_content: Optional[str] = None
        self.mistletoe_doc: Optional[Document] = None
        self.chapter_model: Optional[ChapterPydantic] = None
        self.renderer: MarkdownRenderer = MarkdownRenderer()

        if filepath:
            self.load_and_process(filepath)

    def load_and_process(self, filepath: str) -> bool:
        self.filepath = filepath
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.raw_content = f.read()
            print(f"Successfully loaded '{self.filepath}'.")
        except FileNotFoundError:
            print(f"Error: File not found at '{self.filepath}'")
            self.raw_content = None
            return False
        except Exception as e:
            print(f"Error reading file: {e}")
            self.raw_content = None
            return False

        if self.raw_content:
            self._parse_to_mistletoe_ast()
            self._build_pydantic_model()
            if not self.mistletoe_doc or not self.mistletoe_doc.children:
                print("Warning: Document was loaded but Mistletoe AST is empty.")
            elif not self.chapter_model or not self.chapter_model.document_elements:
                print(
                    "Warning: Document parsed, but Pydantic chapter model is empty or has no elements."
                )
        return True

    def _parse_to_mistletoe_ast(self):
        if self.raw_content:
            self.mistletoe_doc = Document(self.raw_content)
            print("Document parsed to Mistletoe AST.")

    def _build_pydantic_model(self):
        if not self.mistletoe_doc or not self.mistletoe_doc.children:
            print("Mistletoe AST is empty, cannot build Pydantic model.")
            return

        doc_elements: List[Union[GenericContentPydantic, PanelPydantic]] = []
        current_generic_blocks: List[BlockToken] = []

        chapter_h1_block_node: Optional[Heading] = None
        chapter_title = "Untitled Chapter"
        panel_counter = 0  # To number panels as they are found

        first_block = self.mistletoe_doc.children[0]
        if isinstance(first_block, Heading) and first_block.level == 1:
            chapter_h1_block_node = first_block
            chapter_title = get_heading_text(chapter_h1_block_node)
        # else: # If no H1, the first block will be handled by the loop as generic or panel
        # current_generic_blocks.append(first_block) # This was causing first block to be duplicated if it wasn't H1

        start_index = 1 if chapter_h1_block_node else 0  # Start after H1 if found
        all_top_level_blocks = self.mistletoe_doc.children

        # If no H1, ensure the very first block is considered for generic/panel processing
        if not chapter_h1_block_node and all_top_level_blocks:
            all_top_level_blocks_to_process = all_top_level_blocks
        else:
            all_top_level_blocks_to_process = all_top_level_blocks[start_index:]

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
                f"Pydantic model built for '{self.chapter_model.chapter_title_text}' with {len(self.chapter_model.document_elements)} elements."
            )

    def _parse_h3_sections_from_panel_blocks(
        self, panel_content_blocks: List[BlockToken]
    ) -> List[H3Pydantic]:
        h3_pydantic_list: List[H3Pydantic] = []
        current_h3_content_blocks_for_h4s: List[BlockToken] = []
        active_h3_title = "Initial Content"
        active_h3_block_node: Optional[Heading] = None

        if not panel_content_blocks:
            full_h3_md = ""
            h3_pydantic_list.append(
                H3Pydantic(
                    heading_text=active_h3_title,
                    mistletoe_h3_block=None,
                    initial_content_markdown="",
                    h4_sections=[],
                    original_full_markdown=full_h3_md,
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
                    initial_md_for_prev_h3, h4s_for_prev_h3 = (
                        self._parse_h4_sections_from_h3_blocks(
                            current_h3_content_blocks_for_h4s
                        )
                    )
                    all_blocks_for_this_h3_section = []
                    if active_h3_block_node:
                        all_blocks_for_this_h3_section.append(active_h3_block_node)
                    # Add blocks that formed initial_md_for_prev_h3 and H4s' blocks
                    # This requires current_h3_content_blocks_for_h4s to be correctly passed and used
                    # The blocks for initial_md are the ones *before* first H4 in current_h3_content_blocks_for_h4s
                    # The blocks for H4s are inside h4s_for_prev_h3.content_markdown (or their Mistletoe blocks if stored)
                    temp_doc_initial = Document(initial_md_for_prev_h3)
                    all_blocks_for_this_h3_section.extend(
                        b
                        for b in temp_doc_initial.children
                        if b is not None and isinstance(b, BlockToken)
                    )
                    for h4_sec in h4s_for_prev_h3:
                        if h4_sec.mistletoe_h4_block:
                            all_blocks_for_this_h3_section.append(
                                h4_sec.mistletoe_h4_block
                            )
                        temp_doc_h4_content = Document(h4_sec.content_markdown)
                        all_blocks_for_this_h3_section.extend(
                            b
                            for b in temp_doc_h4_content.children
                            if b is not None and isinstance(b, BlockToken)
                        )

                    full_h3_md = render_blocks_to_markdown(
                        all_blocks_for_this_h3_section, self.renderer
                    )
                    h3_pydantic_list.append(
                        H3Pydantic(
                            heading_text=active_h3_title,
                            mistletoe_h3_block=active_h3_block_node,
                            initial_content_markdown=initial_md_for_prev_h3,
                            h4_sections=h4s_for_prev_h3,
                            original_full_markdown=full_h3_md,
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
            initial_md_for_last_h3, h4s_for_last_h3 = (
                self._parse_h4_sections_from_h3_blocks(
                    current_h3_content_blocks_for_h4s
                )
            )
            all_blocks_for_this_h3_section = []
            if active_h3_block_node:
                all_blocks_for_this_h3_section.append(active_h3_block_node)
            temp_doc_initial_last = Document(initial_md_for_last_h3)
            all_blocks_for_this_h3_section.extend(
                b
                for b in temp_doc_initial_last.children
                if b is not None and isinstance(b, BlockToken)
            )
            for h4_sec in h4s_for_last_h3:
                if h4_sec.mistletoe_h4_block:
                    all_blocks_for_this_h3_section.append(h4_sec.mistletoe_h4_block)
                temp_doc_h4_content_last = Document(h4_sec.content_markdown)
                all_blocks_for_this_h3_section.extend(
                    b
                    for b in temp_doc_h4_content_last.children
                    if b is not None and isinstance(b, BlockToken)
                )

            full_h3_md = render_blocks_to_markdown(
                all_blocks_for_this_h3_section, self.renderer
            )
            h3_pydantic_list.append(
                H3Pydantic(
                    heading_text=active_h3_title,
                    mistletoe_h3_block=active_h3_block_node,
                    initial_content_markdown=initial_md_for_last_h3,
                    h4_sections=h4s_for_last_h3,
                    original_full_markdown=full_h3_md,
                )
            )
        return h3_pydantic_list

    def _parse_h4_sections_from_h3_blocks(
        self, h3_content_blocks: List[BlockToken]
    ) -> tuple[str, List[H4Pydantic]]:
        h4_pydantic_list: List[H4Pydantic] = []
        current_h4_content_blocks: List[BlockToken] = []
        initial_content_for_h3_blocks: List[BlockToken] = []
        active_h4_block_node: Optional[Heading] = None
        is_before_first_h4 = True

        if not h3_content_blocks:
            return "", []

        block_idx = 0
        while block_idx < len(h3_content_blocks):
            block = h3_content_blocks[block_idx]
            is_h4_heading = False

            if isinstance(block, Heading) and block.level == 4:
                is_h4_heading = True

            if is_h4_heading:
                is_before_first_h4 = False
                if active_h4_block_node:
                    h4_content_md = render_blocks_to_markdown(
                        current_h4_content_blocks, self.renderer
                    )
                    h4_pydantic_list.append(
                        H4Pydantic(
                            heading_text=get_heading_text(active_h4_block_node),
                            mistletoe_h4_block=active_h4_block_node,
                            content_markdown=h4_content_md,
                        )
                    )
                active_h4_block_node = block
                current_h4_content_blocks = []
                block_idx += 1
            else:
                if is_before_first_h4:
                    initial_content_for_h3_blocks.append(block)
                else:
                    current_h4_content_blocks.append(block)
                block_idx += 1

        if active_h4_block_node:
            h4_content_md = render_blocks_to_markdown(
                current_h4_content_blocks, self.renderer
            )
            h4_pydantic_list.append(
                H4Pydantic(
                    heading_text=get_heading_text(active_h4_block_node),
                    mistletoe_h4_block=active_h4_block_node,
                    content_markdown=h4_content_md,
                )
            )

        initial_content_markdown_for_h3 = render_blocks_to_markdown(
            initial_content_for_h3_blocks, self.renderer
        )
        return initial_content_markdown_for_h3, h4_pydantic_list

    # --- Listing Methods ---
    def list_all_h2_sections(self) -> List[Dict[str, Any]]:
        """Returns a list of all H2-level sections (generic or panel) with titles."""
        if not self.chapter_model:
            return []
        sections = []
        for i, element in enumerate(self.chapter_model.document_elements):
            title = f"Generic Section {i+1}"
            is_panel = False
            panel_obj_id = (
                None  # For panels, we can use their object id or panel_number_in_doc
            )

            if isinstance(element, GenericContentPydantic):
                title = (
                    element.title_text
                    if element.title_text
                    else f"Generic Content Block starting with: {element.content_markdown[:30].strip()}..."
                )
            elif isinstance(element, PanelPydantic):
                title = element.panel_title_text
                is_panel = True
                panel_obj_id = (
                    element.panel_number_in_doc
                )  # Or element.panel_title_text for unique ID
            sections.append(
                {
                    "number": i + 1,
                    "title": title,
                    "is_panel": is_panel,
                    "id": panel_obj_id if is_panel else title,
                }
            )
        return sections

    def list_panels(self) -> List[PanelPydantic]:
        """Returns a list of PanelPydantic objects."""
        if not self.chapter_model:
            return []
        return [
            el
            for el in self.chapter_model.document_elements
            if isinstance(el, PanelPydantic)
        ]

    def get_panel_by_number(self, panel_number: int) -> Optional[PanelPydantic]:
        """Gets a panel by its 1-indexed number in the document."""
        if not self.chapter_model:
            return None
        for element in self.chapter_model.document_elements:
            if (
                isinstance(element, PanelPydantic)
                and element.panel_number_in_doc == panel_number
            ):
                return element
        return None

    def list_h3_sections_in_panel(self, panel: PanelPydantic) -> List[Dict[str, Any]]:
        """Returns a list of H3 sections within a given panel, with numbering."""
        if not panel:
            return []
        h3_list = []
        for i, h3_sec in enumerate(panel.h3_sections):
            h3_list.append(
                {
                    "number": i + 1,
                    "title": h3_sec.heading_text,
                    "h3_object": h3_sec,  # Store the actual H3Pydantic object
                }
            )
        return h3_list

    def list_targetable_sections_in_panel(
        self, panel: PanelPydantic
    ) -> List[Dict[str, Any]]:
        """
        Lists all targetable sections within a panel for API prep or editing:
        Panel itself (H2), H3 sections, H3 Initial Content, H4 sections.
        Returns a list of dicts: {"display_number": int, "type": str, "title": str,
                                 "panel_title": str, "h3_title": Optional[str], "h4_title": Optional[str]}
        """
        if not panel:
            return []

        targets = []
        current_display_number = 1

        # 1. The Panel (H2) itself
        targets.append(
            {
                "display_number": current_display_number,
                "type": "H2 Panel",
                "title": panel.panel_title_text,
                "panel_title": panel.panel_title_text,  # For identification
                "h3_title": None,
                "h4_title": None,
            }
        )
        current_display_number += 1

        # 2. H3 sections and their H4s
        for h3_sec in panel.h3_sections:
            # The H3 section as a whole
            targets.append(
                {
                    "display_number": current_display_number,
                    "type": "H3 Sub-section",
                    "title": h3_sec.heading_text,
                    "panel_title": panel.panel_title_text,
                    "h3_title": h3_sec.heading_text,
                    "h4_title": None,
                }
            )
            current_display_number += 1

            # H3's Initial Content (if it exists and is not just whitespace)
            if (
                h3_sec.initial_content_markdown
                and h3_sec.initial_content_markdown.strip()
            ):
                targets.append(
                    {
                        "display_number": current_display_number,
                        "type": "H3 Initial Content",
                        "title": f"{h3_sec.heading_text} (Initial Content)",
                        "panel_title": panel.panel_title_text,
                        "h3_title": h3_sec.heading_text,  # Context
                        "h4_title": None,  # Special marker for H3 initial content
                        "is_initial_content_for_h3": True,
                    }
                )
                current_display_number += 1

            # H4 sections within this H3
            for h4_sec in h3_sec.h4_sections:
                targets.append(
                    {
                        "display_number": current_display_number,
                        "type": "H4 Sub-sub-section",
                        "title": h4_sec.heading_text,
                        "panel_title": panel.panel_title_text,
                        "h3_title": h3_sec.heading_text,  # Parent H3
                        "h4_title": h4_sec.heading_text,
                    }
                )
                current_display_number += 1
        return targets

    # --- Getters for Content (to be used by Controller) ---
    def get_panel_pydantic(
        self, panel_title_fragment: str
    ) -> Optional[PanelPydantic]:  # Renamed from get_panel_by_title for clarity
        if not self.chapter_model:
            return None
        for element in self.chapter_model.document_elements:
            if (
                isinstance(element, PanelPydantic)
                and panel_title_fragment in element.panel_title_text
            ):
                return element
        return None

    def get_h3_pydantic(
        self, panel: PanelPydantic, h3_title_fragment: str
    ) -> Optional[H3Pydantic]:  # Renamed
        if not panel:
            return None
        for h3_section in panel.h3_sections:
            if h3_title_fragment in h3_section.heading_text:
                return h3_section
        return None

    def get_h4_pydantic(
        self, h3_section: H3Pydantic, h4_title_fragment: str
    ) -> Optional[H4Pydantic]:  # Renamed
        if not h3_section:
            return None
        for h4_section_model in h3_section.h4_sections:
            if h4_title_fragment in h4_section_model.heading_text:
                return h4_section_model
        return None

    def get_panel_full_markdown(self, panel_data: PanelPydantic) -> str:
        if not panel_data or not isinstance(panel_data, PanelPydantic):
            return "Error: Invalid panel data provided."

        panel_blocks_to_render = []
        if panel_data.mistletoe_h2_block:
            panel_blocks_to_render.append(panel_data.mistletoe_h2_block)

        for h3_item in panel_data.h3_sections:
            # Reconstruct H3 from its original_full_markdown
            if h3_item.original_full_markdown:
                temp_h3_doc = Document(h3_item.original_full_markdown)
                valid_children = [
                    b
                    for b in temp_h3_doc.children
                    if b is not None and isinstance(b, BlockToken)
                ]
                panel_blocks_to_render.extend(valid_children)
            # Fallback (should ideally not be needed if original_full_markdown is always populated)
            # elif h3_item.mistletoe_h3_block:
            #     panel_blocks_to_render.append(h3_item.mistletoe_h3_block)
            #     if h3_item.initial_content_markdown:
            #         panel_blocks_to_render.extend(Document(h3_item.initial_content_markdown).children)
            #     for h4_item_fallback in h3_item.h4_sections:
            #         if h4_item_fallback.mistletoe_h4_block: panel_blocks_to_render.append(h4_item_fallback.mistletoe_h4_block)
            #         if h4_item_fallback.content_markdown: panel_blocks_to_render.extend(Document(h4_item_fallback.content_markdown).children)

        if not panel_blocks_to_render:
            return f"Panel '{panel_data.panel_title_text}' appears empty."
        return render_blocks_to_markdown(panel_blocks_to_render, self.renderer)

    def get_h3_subsection_full_markdown(self, h3_subsection_data: H3Pydantic) -> str:
        if not h3_subsection_data or not isinstance(h3_subsection_data, H3Pydantic):
            return "Error: Invalid H3 subsection data provided."
        # original_full_markdown should contain the H3 heading and all its content
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
        if h4_subsubsection_data.content_markdown:  # This is content *under* H4
            temp_h4_content_doc = Document(h4_subsubsection_data.content_markdown)
            valid_children = [
                b
                for b in temp_h4_content_doc.children
                if b is not None and isinstance(b, BlockToken)
            ]
            h4_blocks_to_render.extend(valid_children)

        if not h4_blocks_to_render:
            return f"H4 section '{h4_subsubsection_data.heading_text}' appears empty."
        return render_blocks_to_markdown(h4_blocks_to_render, self.renderer)

    def get_section_markdown_for_api(
        self,
        panel_title: str,
        h3_title: Optional[str] = None,
        h4_title: Optional[str] = None,
        is_initial_content_target: bool = False,
    ) -> Optional[str]:
        """
        Retrieves markdown for H2, H3, H3's initial content, or H4 level.
        is_initial_content_target: Flag to specifically get H3's initial content.
        """
        panel = self.get_panel_pydantic(panel_title)
        if not panel:
            return f"Error: Panel '{panel_title}' not found."

        if not h3_title:
            return self.get_panel_full_markdown(panel)

        h3_section = self.get_h3_pydantic(panel, h3_title)
        if not h3_section:
            return f"Error: H3 section '{h3_title}' not found in '{panel.panel_title_text}'."

        if is_initial_content_target:  # Explicitly targeting H3's initial content
            return h3_section.initial_content_markdown

        if not h4_title:
            return self.get_h3_subsection_full_markdown(h3_section)

        h4_section_model = self.get_h4_pydantic(h3_section, h4_title)
        if not h4_section_model:
            return f"Error: H4 section '{h4_title}' not found in '{h3_section.heading_text}'."
        return self.get_h4_subsubsection_full_markdown(h4_section_model)

    # --- Modification Methods ---
    def update_h3_section_via_api(
        self,
        panel_title: str,
        h3_title: str,
        improved_markdown: str,
        recommendation: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        panel = self.get_panel_pydantic(panel_title)
        if not panel:
            print(f"Cannot update: Panel '{panel_title}' not found.")
            return False
        h3 = self.get_h3_pydantic(panel, h3_title)
        if not h3:
            print(f"Cannot update: H3 '{h3_title}' not found in Panel '{panel_title}'.")
            return False

        h3.api_improved_markdown = improved_markdown
        if recommendation:
            h3.api_recommendation = recommendation
        if reason:
            h3.api_reason = reason
        print(
            f"H3 section '{h3_title}' in Panel '{panel_title}' marked for update with API content."
        )
        return True

    def update_target_content(
        self,
        panel_title: str,
        new_markdown_content: str,
        h3_title: Optional[str] = None,
        h4_title: Optional[str] = None,
        is_h3_initial_content_target: bool = False,
    ) -> bool:
        """
        Updates content for H2 Panel (not recommended for full replacement), H3, H3-Initial, or H4.
        For H2, this would replace ALL content under the H2, which is a broad operation.
        """
        panel = self.get_panel_pydantic(panel_title)
        if not panel:
            print(f"Panel '{panel_title}' not found.")
            return False

        if not h3_title:  # Target is the entire H2 Panel
            print(
                f"Warning: Replacing entire content of Panel '{panel_title}'. This is a broad operation."
            )
            new_h3_sections = self._parse_h3_sections_from_panel_blocks(
                Document(new_markdown_content).children
            )
            panel.h3_sections = new_h3_sections
            # Note: panel.mistletoe_h2_block remains unchanged.
            print(
                f"Entire content of Panel '{panel_title}' replaced (H3s and H4s re-parsed)."
            )
            return True

        h3_section = self.get_h3_pydantic(panel, h3_title)
        if not h3_section:
            print(f"H3 '{h3_title}' not found.")
            return False

        if is_h3_initial_content_target:
            h3_section.initial_content_markdown = new_markdown_content
            h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
                h3_section
            )
            print(f"Initial content of H3 '{h3_title}' updated.")
            return True

        if not h4_title:  # Target is the entire H3 section
            h3_section.original_full_markdown = new_markdown_content
            # Re-parse this new full H3 markdown to update its components (initial_content, h4_sections)
            # This requires the new_markdown_content to include the H3 heading itself.
            temp_doc_new_h3 = Document(new_markdown_content)
            if (
                temp_doc_new_h3.children
                and isinstance(temp_doc_new_h3.children[0], Heading)
                and temp_doc_new_h3.children[0].level == 3
            ):
                h3_section.mistletoe_h3_block = temp_doc_new_h3.children[0]
                h3_section.heading_text = get_heading_text(
                    h3_section.mistletoe_h3_block
                )
                h3_content_blocks = temp_doc_new_h3.children[1:]
                h3_section.initial_content_markdown, h3_section.h4_sections = (
                    self._parse_h4_sections_from_h3_blocks(h3_content_blocks)
                )
                print(f"Entire H3 section '{h3_title}' updated and re-parsed.")
                return True
            else:
                print(
                    f"Error: New content for H3 '{h3_title}' must start with an H3 heading."
                )
                return False

        # Target is an H4 section
        h4_found_and_updated = False
        for h4_idx, h4_s_val in enumerate(h3_section.h4_sections):
            if h4_s_val.heading_text == h4_title:
                # new_markdown_content is the content *under* the H4 heading
                h3_section.h4_sections[h4_idx].content_markdown = new_markdown_content
                h4_found_and_updated = True
                break
        if not h4_found_and_updated:
            print(f"H4 '{h4_title}' not found for update.")
            return False

        h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
            h3_section
        )
        print(f"Content of H4 '{h4_title}' in H3 '{h3_title}' updated.")
        return True

    def add_content_to_target(
        self,
        panel_title: str,
        new_markdown_content: str,
        position: str = "end",
        h3_title: Optional[str] = None,
        h4_title: Optional[str] = None,
        is_h3_initial_content_target: bool = False,
    ) -> bool:
        """Adds content. Targets H3-Initial or H4."""
        panel = self.get_panel_pydantic(panel_title)
        if not panel:
            print(f"Panel '{panel_title}' not found.")
            return False

        if not h3_title:
            print("Error: H3 section must be specified to add content within a panel.")
            return False

        h3_section = self.get_h3_pydantic(panel, h3_title)
        if not h3_section:
            print(f"H3 '{h3_title}' not found.")
            return False

        if is_h3_initial_content_target:
            if position == "start":
                h3_section.initial_content_markdown = (
                    new_markdown_content + "\n" + h3_section.initial_content_markdown
                )
            else:
                h3_section.initial_content_markdown += "\n" + new_markdown_content
            target_name = f"H3 '{h3_title}' (Initial Content)"
        elif h4_title:
            h4_found = False
            for h4_idx, h4_s_val in enumerate(h3_section.h4_sections):
                if h4_s_val.heading_text == h4_title:
                    if position == "start":
                        h3_section.h4_sections[h4_idx].content_markdown = (
                            new_markdown_content + "\n" + h4_s_val.content_markdown
                        )
                    else:
                        h3_section.h4_sections[h4_idx].content_markdown += (
                            "\n" + new_markdown_content
                        )
                    h4_found = True
                    break
            if not h4_found:
                print(f"H4 '{h4_title}' not found for adding content.")
                return False
            target_name = f"H4 '{h4_title}'"
        else:
            print(
                "Error: Target for adding content (H3 Initial or H4) not clearly specified."
            )
            return False

        h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
            h3_section
        )
        print(
            f"Successfully added content to {target_name} (position: {position}) in panel '{panel.panel_title_text}'."
        )
        return True

    def _regenerate_h3_full_markdown(self, h3_section: H3Pydantic) -> str:
        """Helper to reconstruct the full markdown string for an H3 section from its components."""
        blocks_for_render = []
        if h3_section.mistletoe_h3_block:
            blocks_for_render.append(h3_section.mistletoe_h3_block)

        if h3_section.initial_content_markdown:
            # Parse the string back to blocks to ensure correct rendering relative to H4s
            # Filter out None or non-BlockToken items that might come from an empty string parse
            initial_content_doc = Document(h3_section.initial_content_markdown)
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

    def reconstruct_and_render_document(self) -> str:
        if not self.chapter_model:
            return self.raw_content or ""

        all_final_blocks: List[BlockToken] = []
        if self.chapter_model.mistletoe_h1_block:
            all_final_blocks.append(self.chapter_model.mistletoe_h1_block)

        for element in self.chapter_model.document_elements:
            if isinstance(element, GenericContentPydantic):
                if element.mistletoe_blocks:  # Prefer original blocks
                    all_final_blocks.extend(
                        b
                        for b in element.mistletoe_blocks
                        if b is not None and isinstance(b, BlockToken)
                    )
                elif element.content_markdown:
                    generic_doc = Document(element.content_markdown)
                    all_final_blocks.extend(
                        b
                        for b in generic_doc.children
                        if b is not None and isinstance(b, BlockToken)
                    )

            elif isinstance(element, PanelPydantic):
                if element.mistletoe_h2_block:
                    all_final_blocks.append(element.mistletoe_h2_block)

                for h3_section in element.h3_sections:
                    if h3_section.api_improved_markdown is not None:
                        improved_doc = Document(h3_section.api_improved_markdown)
                        all_final_blocks.extend(
                            b
                            for b in improved_doc.children
                            if b is not None and isinstance(b, BlockToken)
                        )
                    elif h3_section.original_full_markdown:
                        original_h3_doc = Document(h3_section.original_full_markdown)
                        all_final_blocks.extend(
                            b
                            for b in original_h3_doc.children
                            if b is not None and isinstance(b, BlockToken)
                        )

        return render_blocks_to_markdown(all_final_blocks, self.renderer)

    def save_document(self, output_filepath: str) -> bool:
        rendered_content = self.reconstruct_and_render_document()
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            print(f"Document successfully saved to '{output_filepath}'.")
            return True
        except Exception as e:
            print(f"Error saving document to '{output_filepath}': {e}")
            return False

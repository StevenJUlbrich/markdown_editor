# document_model.py
from typing import Any, List, Optional, Union

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

    # Filter out any None values from the blocks list before assigning
    valid_blocks = [b for b in blocks if b is not None and isinstance(b, BlockToken)]
    if not valid_blocks:  # If filtering results in an empty list
        # print("Warning: render_blocks_to_markdown received no valid blocks after filtering.")
        return ""

    temp_doc = Document("")
    try:
        temp_doc.children = valid_blocks  # Assign only valid blocks
    except Exception as e:
        print(f"Error assigning children in render_blocks_to_markdown: {e}")
        print(f"Problematic valid_blocks (first 5): {valid_blocks[:5]}")
        return "Error: Could not render blocks."

    active_renderer = renderer if renderer else MarkdownRenderer()
    return active_renderer.render(temp_doc).strip()


# --- Pydantic Models ---
class H4Pydantic(BaseModel):
    """Represents an H4 sub-sub-section."""

    heading_text: str
    mistletoe_h4_block: Optional[Any] = (
        None  # Stores the Mistletoe Heading object for H4
    )
    content_markdown: str = ""


class H3Pydantic(BaseModel):
    """Represents an H3 sub-section within a Panel."""

    heading_text: str
    mistletoe_h3_block: Optional[Any] = (
        None  # Stores the Mistletoe Heading object for H3
    )
    initial_content_markdown: str = ""
    h4_sections: List[H4Pydantic] = Field(default_factory=list)
    original_full_markdown: str = ""
    api_improved_markdown: Optional[str] = None
    api_recommendation: Optional[str] = None
    api_reason: Optional[str] = None


class PanelPydantic(BaseModel):
    """Represents an H2 Panel section."""

    panel_title_text: str
    mistletoe_h2_block: Optional[Any] = (
        None  # Stores the Mistletoe Heading object for H2
    )
    h3_sections: List[H3Pydantic] = Field(default_factory=list)


class GenericContentPydantic(BaseModel):
    """Represents a block of generic content (not part of a Panel)."""

    content_markdown: str
    # Storing original blocks can avoid re-parsing during reconstruction
    mistletoe_blocks: List[Any] = Field(default_factory=list)


class ChapterPydantic(BaseModel):
    """Represents the entire chapter document."""

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

        first_block = self.mistletoe_doc.children[0]
        if isinstance(first_block, Heading) and first_block.level == 1:
            chapter_h1_block_node = first_block
            chapter_title = get_heading_text(chapter_h1_block_node)
        else:
            current_generic_blocks.append(first_block)

        start_index = 1 if chapter_h1_block_node else 0
        all_top_level_blocks = self.mistletoe_doc.children
        current_block_index = start_index

        while current_block_index < len(all_top_level_blocks):
            block = all_top_level_blocks[current_block_index]
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
                    generic_md = render_blocks_to_markdown(
                        current_generic_blocks, self.renderer
                    )
                    doc_elements.append(
                        GenericContentPydantic(
                            content_markdown=generic_md,
                            mistletoe_blocks=list(current_generic_blocks),
                        )
                    )
                    current_generic_blocks = []

                panel_content_blocks_for_h3s: List[BlockToken] = []
                current_block_index += 1

                while current_block_index < len(all_top_level_blocks):
                    next_block_in_panel = all_top_level_blocks[current_block_index]
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
                    )
                )
            else:
                current_generic_blocks.append(block)
                current_block_index += 1

        if current_generic_blocks:
            generic_md = render_blocks_to_markdown(
                current_generic_blocks, self.renderer
            )
            doc_elements.append(
                GenericContentPydantic(
                    content_markdown=generic_md,
                    mistletoe_blocks=list(current_generic_blocks),
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
                    all_blocks_for_this_h3_section.extend(
                        current_h3_content_blocks_for_h4s
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
            all_blocks_for_this_h3_section.extend(current_h3_content_blocks_for_h4s)
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
                            heading_text=get_heading_text(
                                active_h4_block_node
                            ),  # Get text from the node
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

    def get_panel_pydantic(self, panel_title_fragment: str) -> Optional[PanelPydantic]:
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
    ) -> Optional[H3Pydantic]:
        if not panel:
            return None
        for h3_section in panel.h3_sections:
            if h3_title_fragment in h3_section.heading_text:
                return h3_section
        return None

    def get_h4_pydantic(
        self, h3_section: H3Pydantic, h4_title_fragment: str
    ) -> Optional[H4Pydantic]:
        if not h3_section:
            return None
        for h4_section_model in h3_section.h4_sections:
            if h4_title_fragment in h4_section_model.heading_text:
                return h4_section_model
        return None

    def get_section_markdown_for_api(
        self,
        panel_title: str,
        h3_title: Optional[str] = None,
        h4_title: Optional[str] = None,
    ) -> Optional[str]:
        panel = self.get_panel_pydantic(panel_title)
        if not panel:
            return f"Error: Panel '{panel_title}' not found."

        if not h3_title:
            # Assemble full panel markdown
            blocks_for_panel = []
            if panel.mistletoe_h2_block:  # Check if H2 block is not None
                blocks_for_panel.append(panel.mistletoe_h2_block)
            else:  # Should ideally not happen if panel object exists
                print(
                    f"Warning: Panel '{panel.panel_title_text}' Pydantic object exists but H2 Mistletoe block is missing."
                )

            for h3_sec in panel.h3_sections:
                # original_full_markdown for H3 includes its heading and all content (H4s etc.)
                if h3_sec.original_full_markdown:
                    # Parse this string back to Mistletoe blocks to append
                    temp_h3_doc = Document(h3_sec.original_full_markdown)
                    valid_children = [
                        b
                        for b in temp_h3_doc.children
                        if b is not None and isinstance(b, BlockToken)
                    ]
                    blocks_for_panel.extend(valid_children)

            if (
                not blocks_for_panel and panel.mistletoe_h2_block is None
            ):  # Only return error if truly nothing, not even H2
                return (
                    f"Error: Panel '{panel.panel_title_text}' has no content to render."
                )
            return render_blocks_to_markdown(blocks_for_panel, self.renderer)

        h3_section = self.get_h3_pydantic(panel, h3_title)
        if not h3_section:
            return f"Error: H3 section '{h3_title}' not found in '{panel.panel_title_text}'."

        if not h4_title:
            return h3_section.original_full_markdown

        h4_section_model = self.get_h4_pydantic(h3_section, h4_title)
        if not h4_section_model:
            return f"Error: H4 section '{h4_title}' not found in '{h3_section.heading_text}'."

        h4_full_md_blocks = []
        if h4_section_model.mistletoe_h4_block:  # Check if H4 block is not None
            h4_full_md_blocks.append(h4_section_model.mistletoe_h4_block)
        if h4_section_model.content_markdown:
            temp_h4_content_doc = Document(h4_section_model.content_markdown)
            valid_children = [
                b
                for b in temp_h4_content_doc.children
                if b is not None and isinstance(b, BlockToken)
            ]
            h4_full_md_blocks.extend(valid_children)

        if not h4_full_md_blocks and h4_section_model.mistletoe_h4_block is None:
            return f"Error: H4 section '{h4_section_model.heading_text}' has no content to render."
        return render_blocks_to_markdown(h4_full_md_blocks, self.renderer)

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

    def update_subsection_content(
        self,
        panel_title_fragment: str,
        h3_subsection_title_fragment: str,
        new_markdown_content: str,
        h4_subsubsection_title_fragment: Optional[str] = None,
    ):
        panel = self.get_panel_pydantic(panel_title_fragment)
        if not panel:
            print(f"Panel '{panel_title_fragment}' not found.")
            return False

        h3_section = self.get_h3_pydantic(panel, h3_subsection_title_fragment)
        if not h3_section:
            print(f"H3 Subsection '{h3_subsection_title_fragment}' not found.")
            return False

        target_section_data_dict = None
        target_section_name = ""

        if h4_subsubsection_title_fragment:
            for h4_s_dict_idx, h4_s_dict_val in enumerate(h3_section.h4_sections):
                if h4_s_dict_val.heading_text == h4_subsubsection_title_fragment:
                    target_section_data_dict = h3_section.h4_sections[
                        h4_s_dict_idx
                    ]  # This is H4Pydantic object
                    target_section_name = f"H4 '{h4_subsubsection_title_fragment}'"
                    break
            if not target_section_data_dict:
                print(
                    f"H4 Sub-subsection '{h4_subsubsection_title_fragment}' not found for update."
                )
                return False

            # Update H4Pydantic.content_markdown
            # The new_markdown_content is the content *under* the H4 heading
            target_section_data_dict.content_markdown = new_markdown_content
            # Also need to update the parent H3's original_full_markdown
            h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
                h3_section
            )

        else:
            # Target H3's "Initial Content"
            h3_section.initial_content_markdown = new_markdown_content
            # Also need to update the H3's original_full_markdown
            h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
                h3_section
            )
            target_section_name = (
                f"H3 '{h3_subsection_title_fragment}' (Initial Content)"
            )

        print(
            f"Successfully updated {target_section_name} in panel '{panel.panel_title_text}'."
        )
        return True

    def add_content_to_subsection(
        self,
        panel_title_fragment: str,
        h3_subsection_title_fragment: str,
        new_markdown_content: str,
        position: str = "end",
        h4_subsubsection_title_fragment: Optional[str] = None,
    ):
        panel = self.get_panel_pydantic(panel_title_fragment)
        if not panel:
            print(f"Panel '{panel_title_fragment}' not found.")
            return False

        h3_section = self.get_h3_pydantic(panel, h3_subsection_title_fragment)
        if not h3_section:
            print(f"H3 Subsection '{h3_subsection_title_fragment}' not found.")
            return False

        target_section_data_dict = (
            None  # H4Pydantic object or H3Pydantic for initial_content
        )
        target_section_name = ""
        is_h4_target = False

        if h4_subsubsection_title_fragment:
            for h4_s_dict_idx, h4_s_dict_val in enumerate(h3_section.h4_sections):
                if h4_s_dict_val.heading_text == h4_subsubsection_title_fragment:
                    target_section_data_dict = h3_section.h4_sections[h4_s_dict_idx]
                    target_section_name = f"H4 '{h4_subsubsection_title_fragment}'"
                    is_h4_target = True
                    break
            if not target_section_data_dict:
                print(
                    f"H4 Sub-subsection '{h4_subsubsection_title_fragment}' not found for adding content."
                )
                return False
        else:
            target_section_data_dict = (
                h3_section  # Target H3's initial_content_markdown
            )
            target_section_name = (
                f"H3 '{h3_subsection_title_fragment}' (Initial Content)"
            )

        if is_h4_target and isinstance(target_section_data_dict, H4Pydantic):
            if position == "start":
                target_section_data_dict.content_markdown = (
                    new_markdown_content
                    + "\n"
                    + target_section_data_dict.content_markdown
                )
            else:  # "end"
                target_section_data_dict.content_markdown = (
                    target_section_data_dict.content_markdown
                    + "\n"
                    + new_markdown_content
                )
        elif not is_h4_target and isinstance(target_section_data_dict, H3Pydantic):
            if position == "start":
                target_section_data_dict.initial_content_markdown = (
                    new_markdown_content
                    + "\n"
                    + target_section_data_dict.initial_content_markdown
                )
            else:  # "end"
                target_section_data_dict.initial_content_markdown = (
                    target_section_data_dict.initial_content_markdown
                    + "\n"
                    + new_markdown_content
                )
        else:
            print("Error: Could not determine target for adding content.")
            return False

        # Update the parent H3's original_full_markdown
        h3_section.original_full_markdown = self._regenerate_h3_full_markdown(
            h3_section
        )
        print(
            f"Successfully added content to {target_section_name} (position: {position}) in panel '{panel.panel_title_text}'."
        )
        return True

    def _regenerate_h3_full_markdown(self, h3_section: H3Pydantic) -> str:
        """Helper to reconstruct the full markdown string for an H3 section from its components."""
        blocks_for_render = []
        if h3_section.mistletoe_h3_block:
            blocks_for_render.append(h3_section.mistletoe_h3_block)
        if h3_section.initial_content_markdown:
            # Parse the string back to blocks to ensure correct rendering relative to H4s
            blocks_for_render.extend(
                Document(h3_section.initial_content_markdown).children
            )
        for h4_s in h3_section.h4_sections:
            if h4_s.mistletoe_h4_block:
                blocks_for_render.append(h4_s.mistletoe_h4_block)
            if h4_s.content_markdown:
                blocks_for_render.extend(Document(h4_s.content_markdown).children)
        return render_blocks_to_markdown(blocks_for_render, self.renderer)

    def reconstruct_and_render_document(self) -> str:
        if not self.chapter_model:
            return self.raw_content or ""

        all_final_blocks: List[BlockToken] = []
        if self.chapter_model.mistletoe_h1_block:  # Add H1 if it exists
            all_final_blocks.append(self.chapter_model.mistletoe_h1_block)

        for element in self.chapter_model.document_elements:
            if isinstance(element, GenericContentPydantic):
                # Use stored Mistletoe blocks for generic content if available
                if element.mistletoe_blocks:
                    all_final_blocks.extend(
                        b
                        for b in element.mistletoe_blocks
                        if b is not None and isinstance(b, BlockToken)
                    )
                elif element.content_markdown:  # Fallback to re-parsing
                    generic_doc = Document(element.content_markdown)
                    all_final_blocks.extend(
                        b
                        for b in generic_doc.children
                        if b is not None and isinstance(b, BlockToken)
                    )

            elif isinstance(element, PanelPydantic):
                if element.mistletoe_h2_block:  # Add Panel H2
                    all_final_blocks.append(element.mistletoe_h2_block)

                for h3_section in element.h3_sections:
                    if h3_section.api_improved_markdown is not None:
                        # API provided improved content for the whole H3 section
                        improved_doc = Document(h3_section.api_improved_markdown)
                        all_final_blocks.extend(
                            b
                            for b in improved_doc.children
                            if b is not None and isinstance(b, BlockToken)
                        )
                    else:
                        # Use original H3 content. original_full_markdown includes H3 heading.
                        if h3_section.original_full_markdown:
                            original_h3_doc = Document(
                                h3_section.original_full_markdown
                            )
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

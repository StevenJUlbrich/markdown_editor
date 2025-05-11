# document_model.py
from typing import Any, List, Optional, Union

from mistletoe import Document
from mistletoe.block_token import (  # Base class for Mistletoe blocks
    BlockToken,
    Heading,
    Paragraph,
)
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText
from pydantic import (  # Ensure pydantic is installed: pip install pydantic / conda install pydantic
    BaseModel,
    Field,
)


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
    """Renders a list of Mistletoe block tokens to a Markdown string."""
    if not blocks:
        return ""
    # Create a temporary Document to render these blocks
    temp_doc = Document("")
    temp_doc.children = blocks  # Assign the already parsed blocks

    # Use provided renderer or create a new one
    active_renderer = renderer if renderer else MarkdownRenderer()
    return active_renderer.render(temp_doc).strip()


# --- Pydantic Models ---
class H4Pydantic(BaseModel):
    """Represents an H4 sub-sub-section."""

    heading_text: str
    mistletoe_h4_block: Any  # Stores the Mistletoe Heading object for H4
    # Content directly under this H4, rendered as a Markdown string
    content_markdown: str = ""
    # Original Mistletoe blocks for content under this H4 (excluding H4 heading itself)
    # content_mistletoe_blocks: List[Any] = Field(default_factory=list) # Optional: if needed for very granular ops


class H3Pydantic(BaseModel):
    """Represents an H3 sub-section within a Panel."""

    heading_text: str
    mistletoe_h3_block: Any  # Stores the Mistletoe Heading object for H3

    # Markdown content directly under H3, before any H4s
    initial_content_markdown: str = ""
    h4_sections: List[H4Pydantic] = Field(default_factory=list)

    # The complete original Markdown for this entire H3 section (H3 heading + initial_content + all H4s)
    original_full_markdown: str = ""

    # For OpenAI enhancements
    api_improved_markdown: Optional[str] = None
    api_recommendation: Optional[str] = None
    api_reason: Optional[str] = None


class PanelPydantic(BaseModel):
    """Represents an H2 Panel section."""

    panel_title_text: str  # e.g., "Panel 1: Why Traditional Metrics Fail"
    mistletoe_h2_block: Any  # Stores the Mistletoe Heading object for H2
    h3_sections: List[H3Pydantic] = Field(default_factory=list)


class GenericContentPydantic(BaseModel):
    """Represents a block of generic content (not part of a Panel)."""

    # All generic blocks rendered together as a single Markdown string
    content_markdown: str
    # Original Mistletoe blocks for this generic section
    # mistletoe_blocks: List[Any] = Field(default_factory=list) # Optional


class ChapterPydantic(BaseModel):
    """Represents the entire chapter document."""

    chapter_title_text: str  # e.g., "Chapter 1: Fundamentals of SRE Metrics"
    mistletoe_h1_block: Optional[Any] = (
        None  # Stores the Mistletoe Heading object for H1
    )
    document_elements: List[Union[GenericContentPydantic, PanelPydantic]] = Field(
        default_factory=list
    )


# --- Main Document Class ---
class MarkdownDocument:
    def __init__(self, filepath: Optional[str] = None):
        self.filepath: Optional[str] = filepath
        self.raw_content: Optional[str] = None
        self.mistletoe_doc: Optional[Document] = None  # Root Mistletoe AST
        self.chapter_model: Optional[ChapterPydantic] = None  # Parsed Pydantic model
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

        # Find Chapter H1 first
        first_block = self.mistletoe_doc.children[0]
        if isinstance(first_block, Heading) and first_block.level == 1:
            chapter_h1_block_node = first_block
            chapter_title = get_heading_text(chapter_h1_block_node)
            # Consider if H1 should be part of generic_blocks or handled separately
            # For now, let's assume H1 is the chapter title and other content follows.
            # If H1 is the *only* content, it will be handled by trailing generic blocks.
        else:  # No H1, add first block to generic content
            current_generic_blocks.append(first_block)

        # Process blocks starting from the second block if H1 was found, else from first
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
                    panel_title_text = heading_text  # Full title like "Panel 1: Why..."
                    panel_h2_block_node = block

            if is_h2_panel_heading and panel_h2_block_node:
                if current_generic_blocks:
                    generic_md = render_blocks_to_markdown(
                        current_generic_blocks, self.renderer
                    )
                    doc_elements.append(
                        GenericContentPydantic(content_markdown=generic_md)
                    )
                    current_generic_blocks = []

                panel_content_blocks_for_h3s: List[BlockToken] = []
                current_block_index += 1  # Move past the H2 heading

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
            else:  # Generic content
                current_generic_blocks.append(block)
                current_block_index += 1

        if current_generic_blocks:  # Add any trailing generic blocks
            generic_md = render_blocks_to_markdown(
                current_generic_blocks, self.renderer
            )
            doc_elements.append(GenericContentPydantic(content_markdown=generic_md))

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
        current_h3_associated_blocks: List[BlockToken] = (
            []
        )  # Blocks for the current H3 (its heading + content)
        active_h3_title = "Initial Content"
        active_h3_block_node: Optional[Heading] = None

        # These collect blocks *between* H3 headings, or before the first H3
        current_h3_content_blocks_for_h4s: List[BlockToken] = []

        if not panel_content_blocks:  # Handle panel with no H3s (only H2)
            # Create an "Initial Content" H3 section for the panel
            full_h3_md = ""  # Empty initial content
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
                # Finalize previous H3 section (if any)
                if (
                    active_h3_block_node
                    or active_h3_title == "Initial Content"
                    and current_h3_content_blocks_for_h4s
                ):
                    initial_md_for_prev_h3, h4s_for_prev_h3 = (
                        self._parse_h4_sections_from_h3_blocks(
                            current_h3_content_blocks_for_h4s
                        )
                    )

                    # Construct original_full_markdown for the previous H3 section
                    temp_h3_blocks_for_render = []
                    if active_h3_block_node:
                        temp_h3_blocks_for_render.append(active_h3_block_node)
                    # Need to render initial_md_for_prev_h3 (if it's already md) or its source blocks
                    # For now, assume initial_md_for_prev_h3 is markdown.
                    # And h4s_for_prev_h3 contains H4Pydantic objects.
                    # This part needs careful block assembly for original_full_markdown

                    # To get original_full_markdown: assemble Mistletoe blocks and render
                    all_blocks_for_this_h3_section = []
                    if active_h3_block_node:
                        all_blocks_for_this_h3_section.append(active_h3_block_node)
                    all_blocks_for_this_h3_section.extend(
                        current_h3_content_blocks_for_h4s
                    )  # These are the blocks passed to parse_h4
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

                # Start new H3 section
                active_h3_block_node = block  # This is an H3 Heading object
                active_h3_title = get_heading_text(active_h3_block_node)
                current_h3_content_blocks_for_h4s = []  # Reset for content under new H3
                block_idx += 1
            else:
                current_h3_content_blocks_for_h4s.append(block)
                block_idx += 1

        # Add the last H3 section
        if (
            active_h3_block_node or current_h3_content_blocks_for_h4s
        ):  # If there was any content at all for the last H3 section
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

        active_h4_title = "Initial Content H4"  # Should not be used if H4 found
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
                is_before_first_h4 = False  # We've encountered the first H4
                # Finalize previous H4 section (if any)
                if active_h4_block_node:  # If there was a previous H4
                    h4_content_md = render_blocks_to_markdown(
                        current_h4_content_blocks, self.renderer
                    )
                    h4_pydantic_list.append(
                        H4Pydantic(
                            heading_text=active_h4_title,
                            mistletoe_h4_block=active_h4_block_node,
                            content_markdown=h4_content_md,
                        )
                    )

                # Start new H4 section
                active_h4_block_node = block  # This is an H4 Heading object
                active_h4_title = get_heading_text(active_h4_block_node)
                current_h4_content_blocks = []  # Reset for content under new H4
                block_idx += 1
            else:
                if is_before_first_h4:
                    initial_content_for_h3_blocks.append(block)
                else:  # Content for the current H4
                    current_h4_content_blocks.append(block)
                block_idx += 1

        # Add the last H4 section's content or if no H4s, all content is initial
        if active_h4_block_node:  # If at least one H4 was processed
            h4_content_md = render_blocks_to_markdown(
                current_h4_content_blocks, self.renderer
            )
            h4_pydantic_list.append(
                H4Pydantic(
                    heading_text=active_h4_title,
                    mistletoe_h4_block=active_h4_block_node,
                    content_markdown=h4_content_md,
                )
            )

        initial_content_markdown_for_h3 = render_blocks_to_markdown(
            initial_content_for_h3_blocks, self.renderer
        )
        return initial_content_markdown_for_h3, h4_pydantic_list

    # --- Getters for Content (to be used by Controller) ---
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
        """Gets the full Markdown for H2, H3, or H4 section for API processing."""
        panel = self.get_panel_pydantic(panel_title)
        if not panel:
            return f"Error: Panel '{panel_title}' not found."

        if not h3_title:  # Target is the H2 Panel itself
            # Assemble full panel markdown
            blocks_for_panel = [panel.mistletoe_h2_block]
            for h3_sec in panel.h3_sections:
                blocks_for_panel.append(h3_sec.mistletoe_h3_block)
                # For full H2 panel content, we need to reconstruct from H3's original_full_markdown or its parts
                # This requires H3.original_full_markdown to NOT include the H3 heading itself if we add it above
                # Let's assume H3.original_full_markdown is the complete H3 section content *including* its heading.
                blocks_for_panel.extend(
                    Document(h3_sec.original_full_markdown).children
                    if h3_sec.original_full_markdown
                    else []
                )
            return render_blocks_to_markdown(blocks_for_panel, self.renderer)

        h3_section = self.get_h3_pydantic(panel, h3_title)
        if not h3_section:
            return f"Error: H3 section '{h3_title}' not found in '{panel.panel_title_text}'."

        if not h4_title:  # Target is the H3 section
            return (
                h3_section.original_full_markdown
            )  # This should be the full H3 section MD

        h4_section_model = self.get_h4_pydantic(h3_section, h4_title)
        if not h4_section_model:
            return f"Error: H4 section '{h4_title}' not found in '{h3_section.heading_text}'."

        # Return H4 heading + its content
        h4_full_md_blocks = [h4_section_model.mistletoe_h4_block]
        if h4_section_model.content_markdown:  # content_markdown is already a string
            h4_full_md_blocks.extend(
                Document(h4_section_model.content_markdown).children
            )
        return render_blocks_to_markdown(h4_full_md_blocks, self.renderer)

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

    # update_h4_section_via_api would be similar if needed

    # --- Reconstruction and Saving ---
    def reconstruct_and_render_document(self) -> str:
        if not self.chapter_model:
            return self.raw_content or ""

        all_final_blocks: List[BlockToken] = []
        if self.chapter_model.mistletoe_h1_block:
            all_final_blocks.append(self.chapter_model.mistletoe_h1_block)

        for element in self.chapter_model.document_elements:
            if isinstance(element, GenericContentPydantic):
                # Re-parse the stored markdown to get blocks, or store original blocks
                # For simplicity, re-parsing. Storing original blocks in GenericContentPydantic is better.
                if element.content_markdown:
                    all_final_blocks.extend(Document(element.content_markdown).children)

            elif isinstance(element, PanelPydantic):
                if element.mistletoe_h2_block:
                    all_final_blocks.append(element.mistletoe_h2_block)

                for h3_section in element.h3_sections:
                    if h3_section.api_improved_markdown is not None:
                        # API provided improved content for the whole H3 section
                        # This improved_markdown should be a complete section including H3 heading
                        all_final_blocks.extend(
                            Document(h3_section.api_improved_markdown).children
                        )
                    else:
                        # Use original H3 content (which includes H3 heading, initial content, and H4s)
                        if h3_section.original_full_markdown:
                            all_final_blocks.extend(
                                Document(h3_section.original_full_markdown).children
                            )
                        # Fallback if original_full_markdown wasn't properly populated (should not happen)
                        # else:
                        #     if h3_section.mistletoe_h3_block: all_final_blocks.append(h3_section.mistletoe_h3_block)
                        #     if h3_section.initial_content_markdown: all_final_blocks.extend(Document(h3_section.initial_content_markdown).children)
                        #     for h4_s in h3_section.h4_sections:
                        #         if h4_s.mistletoe_h4_block: all_final_blocks.append(h4_s.mistletoe_h4_block)
                        #         if h4_s.content_markdown: all_final_blocks.extend(Document(h4_s.content_markdown).children)

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

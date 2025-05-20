import logging
import os
from typing import Any, List, Optional, Union

from mistletoe import Document
from mistletoe.block_token import BlockToken, Heading
from models.document_model import (
    _MODULE_LEVEL_RENDERER_INSTANCE,
    ChapterPydantic,
    GenericContentPydantic,
    H3Pydantic,
    H4Pydantic,
    PanelPydantic,
    get_heading_text,
    render_blocks_to_markdown,
)

logger = logging.getLogger(__name__)

PANEL_HEADING_PREFIX = "Panel "
INITIAL_CONTENT_TITLE = "Initial Content"


class DocumentModelBuilder:
    """
    Builds a Pydantic model tree from a mistletoe AST.
    Sets source_filename and heading_line_number on every node.
    Enforces only one H1 in the file.
    """

    def build(
        self, mistletoe_doc: Document, source_filename: str = "unknown.md"
    ) -> ChapterPydantic:
        doc_elements: List[Union[PanelPydantic, Any]] = []
        current_generic_blocks: List[BlockToken] = []
        chapter_h1_block_node: Optional[Heading] = None
        chapter_title = "Untitled Chapter"
        chapter_h1_line = None
        h1_count = 0

        # Detect H1 as chapter title
        start_index = 0
        if (
            mistletoe_doc.children
            and isinstance(mistletoe_doc.children[0], Heading)
            and mistletoe_doc.children[0].level == 1
        ):
            chapter_h1_block_node = mistletoe_doc.children[0]
            chapter_title = get_heading_text(chapter_h1_block_node)
            chapter_h1_line = getattr(chapter_h1_block_node, "position", None)
            h1_count += 1
            start_index = 1

        # Scan for extra H1s
        for i, block in enumerate(mistletoe_doc.children[start_index:]):
            if isinstance(block, Heading) and block.level == 1:
                h1_count += 1
                if h1_count > 1:
                    raise ValueError(
                        f"Multiple H1 headings found in {source_filename} at line {getattr(block, 'position', None)}. Only one H1 (chapter) allowed."
                    )

        all_top_level_blocks = mistletoe_doc.children[start_index:]
        current_block_index = 0
        panel_counter = 0

        while current_block_index < len(all_top_level_blocks):
            block = all_top_level_blocks[current_block_index]
            is_h2_panel_heading = False
            panel_title_text = ""
            panel_h2_block_node = None
            panel_h2_line = None

            if isinstance(block, Heading) and block.level == 2:
                heading_text = get_heading_text(block)
                if heading_text.startswith(PANEL_HEADING_PREFIX):
                    is_h2_panel_heading = True
                    panel_title_text = heading_text
                    panel_h2_block_node = block
                    panel_h2_line = getattr(block, "position", None)

            if is_h2_panel_heading and panel_h2_block_node:
                # Save any accumulated generic blocks as a GenericContentPydantic
                if current_generic_blocks:
                    generic_title = None
                    generic_line = None
                    if isinstance(current_generic_blocks[0], Heading):
                        generic_title = get_heading_text(current_generic_blocks[0])
                        generic_line = getattr(
                            current_generic_blocks[0], "position", None
                        )
                    generic_md = render_blocks_to_markdown(
                        current_generic_blocks, _MODULE_LEVEL_RENDERER_INSTANCE
                    )
                    doc_elements.append(
                        GenericContentPydantic(
                            content_markdown=generic_md,
                            mistletoe_blocks=list(current_generic_blocks),
                            title_text=generic_title,
                            source_filename=source_filename,
                            heading_line_number=generic_line,
                        )
                    )
                    current_generic_blocks = []
                panel_counter += 1
                panel_content_blocks: List[BlockToken] = []
                current_block_index += 1
                while current_block_index < len(all_top_level_blocks):
                    next_block = all_top_level_blocks[current_block_index]
                    if (
                        isinstance(next_block, Heading)
                        and next_block.level == 2
                        and get_heading_text(next_block).startswith(
                            PANEL_HEADING_PREFIX
                        )
                    ):
                        break
                    panel_content_blocks.append(next_block)
                    current_block_index += 1
                h3_sections = self._parse_h3_sections_from_panel_blocks(
                    panel_content_blocks,
                    _MODULE_LEVEL_RENDERER_INSTANCE,
                    source_filename,
                )
                doc_elements.append(
                    PanelPydantic(
                        panel_title_text=panel_title_text,
                        mistletoe_h2_block=panel_h2_block_node,
                        h3_sections=h3_sections,
                        panel_number_in_doc=panel_counter,
                        source_filename=source_filename,
                        heading_line_number=panel_h2_line,
                    )
                )
            else:
                current_generic_blocks.append(block)
                current_block_index += 1
        # Any trailing generic content
        if current_generic_blocks:
            generic_title = None
            generic_line = None
            if isinstance(current_generic_blocks[0], Heading):
                generic_title = get_heading_text(current_generic_blocks[0])
                generic_line = getattr(current_generic_blocks[0], "position", None)
            generic_md = render_blocks_to_markdown(
                current_generic_blocks, _MODULE_LEVEL_RENDERER_INSTANCE
            )
            doc_elements.append(
                GenericContentPydantic(
                    content_markdown=generic_md,
                    mistletoe_blocks=list(current_generic_blocks),
                    title_text=generic_title,
                    source_filename=source_filename,
                    heading_line_number=generic_line,
                )
            )
        return ChapterPydantic(
            chapter_title_text=chapter_title,
            mistletoe_h1_block=chapter_h1_block_node,
            document_elements=doc_elements,
            source_filename=source_filename,
            heading_line_number=chapter_h1_line,
        )

    def _parse_h3_sections_from_panel_blocks(
        self, panel_blocks: List[BlockToken], renderer, source_filename: str
    ) -> List[H3Pydantic]:
        h3_list: List[H3Pydantic] = []
        current_h3_blocks: List[BlockToken] = []
        active_h3_title = INITIAL_CONTENT_TITLE
        active_h3_block: Optional[Heading] = None
        h3_counter = 0
        h3_line = None

        if not panel_blocks:
            h3_counter += 1
            h3_list.append(
                H3Pydantic(
                    heading_text=active_h3_title,
                    mistletoe_h3_block=None,
                    initial_content_markdown="",
                    h4_sections=[],
                    original_full_markdown="",
                    h3_number_in_panel=h3_counter,
                    source_filename=source_filename,
                    heading_line_number=None,
                )
            )
            return h3_list
        block_idx = 0
        while block_idx < len(panel_blocks):
            block = panel_blocks[block_idx]
            is_h3_heading = isinstance(block, Heading) and block.level == 3
            if is_h3_heading:
                if active_h3_block or (
                    active_h3_title == INITIAL_CONTENT_TITLE and current_h3_blocks
                ):
                    h3_counter += 1
                    initial_md, h4s = self._parse_h4_sections_from_h3_blocks(
                        current_h3_blocks, renderer, source_filename
                    )
                    temp_blocks = []
                    if active_h3_block:
                        temp_blocks.append(active_h3_block)
                        h3_line = getattr(active_h3_block, "position", None)
                    if initial_md:
                        temp_doc_initial = Document(initial_md)
                        temp_blocks.extend(
                            b
                            for b in temp_doc_initial.children
                            if isinstance(b, BlockToken)
                        )
                    for h4 in h4s:
                        if hasattr(h4, "mistletoe_h4_block") and h4.mistletoe_h4_block:
                            temp_blocks.append(h4.mistletoe_h4_block)
                        if h4.content_markdown:
                            temp_doc_h4 = Document(h4.content_markdown)
                            temp_blocks.extend(
                                b
                                for b in temp_doc_h4.children
                                if isinstance(b, BlockToken)
                            )
                    full_md = render_blocks_to_markdown(temp_blocks, renderer)
                    h3_list.append(
                        H3Pydantic(
                            heading_text=active_h3_title,
                            mistletoe_h3_block=active_h3_block,
                            initial_content_markdown=initial_md,
                            h4_sections=h4s,
                            original_full_markdown=full_md,
                            h3_number_in_panel=h3_counter,
                            source_filename=source_filename,
                            heading_line_number=h3_line,
                        )
                    )
                active_h3_block = block
                active_h3_title = get_heading_text(active_h3_block)
                h3_line = getattr(active_h3_block, "position", None)
                current_h3_blocks = []
                block_idx += 1
            else:
                current_h3_blocks.append(block)
                block_idx += 1
        # Final trailing H3
        if active_h3_block or current_h3_blocks:
            h3_counter += 1
            initial_md, h4s = self._parse_h4_sections_from_h3_blocks(
                current_h3_blocks, renderer, source_filename
            )
            temp_blocks = []
            if active_h3_block:
                temp_blocks.append(active_h3_block)
                h3_line = getattr(active_h3_block, "position", None)
            if initial_md:
                temp_doc_initial = Document(initial_md)
                temp_blocks.extend(
                    b for b in temp_doc_initial.children if isinstance(b, BlockToken)
                )
            for h4 in h4s:
                if hasattr(h4, "mistletoe_h4_block") and h4.mistletoe_h4_block:
                    temp_blocks.append(h4.mistletoe_h4_block)
                if h4.content_markdown:
                    temp_doc_h4 = Document(h4.content_markdown)
                    temp_blocks.extend(
                        b for b in temp_doc_h4.children if isinstance(b, BlockToken)
                    )
            full_md = render_blocks_to_markdown(temp_blocks, renderer)
            h3_list.append(
                H3Pydantic(
                    heading_text=active_h3_title,
                    mistletoe_h3_block=active_h3_block,
                    initial_content_markdown=initial_md,
                    h4_sections=h4s,
                    original_full_markdown=full_md,
                    h3_number_in_panel=h3_counter,
                    source_filename=source_filename,
                    heading_line_number=h3_line,
                )
            )
        return h3_list

    def _parse_h4_sections_from_h3_blocks(
        self, h3_blocks: List[BlockToken], renderer, source_filename: str
    ) -> tuple[str, List[H4Pydantic]]:
        from mistletoe.block_token import Heading

        h4_list: List[H4Pydantic] = []
        current_h4_blocks: List[BlockToken] = []
        initial_content_blocks: List[BlockToken] = []
        active_h4_block: Optional[Heading] = None
        h4_counter = 0
        is_before_first_h4 = True
        h4_line = None
        for block in h3_blocks:
            if isinstance(block, Heading) and block.level == 4:
                is_before_first_h4 = False
                if active_h4_block:
                    h4_counter += 1
                    content_md = render_blocks_to_markdown(current_h4_blocks, renderer)
                    h4_line = getattr(active_h4_block, "position", None)
                    h4_list.append(
                        H4Pydantic(
                            heading_text=get_heading_text(active_h4_block),
                            mistletoe_h4_block=active_h4_block,
                            content_markdown=content_md,
                            h4_number_in_h3=h4_counter,
                            source_filename=source_filename,
                            heading_line_number=h4_line,
                        )
                    )
                    current_h4_blocks = []
                active_h4_block = block
                h4_line = getattr(active_h4_block, "position", None)
            else:
                if is_before_first_h4:
                    initial_content_blocks.append(block)
                else:
                    current_h4_blocks.append(block)
        # Final trailing H4
        if active_h4_block:
            h4_counter += 1
            content_md = render_blocks_to_markdown(current_h4_blocks, renderer)
            h4_line = getattr(active_h4_block, "position", None)
            h4_list.append(
                H4Pydantic(
                    heading_text=get_heading_text(active_h4_block),
                    mistletoe_h4_block=active_h4_block,
                    content_markdown=content_md,
                    h4_number_in_h3=h4_counter,
                    source_filename=source_filename,
                    heading_line_number=h4_line,
                )
            )
        initial_content_md = render_blocks_to_markdown(initial_content_blocks, renderer)
        return initial_content_md, h4_list

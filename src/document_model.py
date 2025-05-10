# document_model.py
from mistletoe import Document
from mistletoe.block_token import (  # Import other block tokens if needed
    Heading,
    Paragraph,
)
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText, Strong  # Import other span tokens if needed


def get_heading_text(heading_node):
    """
    Extracts the plain text from a Mistletoe Heading node.
    """
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):  # Typically RawText
                text += child.content
    return text.strip()


def get_paragraph_strong_text(paragraph_node):
    """
    If a paragraph starts with strongly emphasized text (like '**Scene Description:**'),
    returns that emphasized text. Otherwise, returns None.
    """
    if (
        not paragraph_node
        or not hasattr(paragraph_node, "children")
        or not paragraph_node.children
    ):
        return None

    first_span = paragraph_node.children[0]
    if isinstance(first_span, Strong):
        strong_text = ""
        if hasattr(first_span, "children"):
            for child in first_span.children:
                if hasattr(child, "content"):  # Typically RawText within Strong
                    strong_text += child.content
        return strong_text.strip()
    return None


class MarkdownDocument:
    """
    Represents and manages a Markdown document, its structure, and modifications.
    """

    def __init__(self, filepath=None):
        self.filepath = filepath
        self.raw_content = None
        self.mistletoe_doc = None  # The root Mistletoe Document object after parsing
        # self.structured_data will now be a list of dictionaries.
        # Each dictionary will have a 'type' ('panel' or 'generic')
        # and 'blocks' (for generic) or panel-specific structure.
        self.structured_data = []
        self.renderer = MarkdownRenderer()

        if filepath:
            self.load_and_process(filepath)

    def load_and_process(self, filepath):
        """Loads, parses, and structures the Markdown document."""
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
            self._parse_to_ast()
            self._build_structured_data()  # This will now populate the new structured_data format
            if (
                not self.mistletoe_doc.children
            ):  # Check if the original doc had any content
                print(
                    "Warning: Document was loaded but appears to be empty after parsing."
                )
            elif not self.structured_data:
                print(
                    "Warning: Document was loaded and parsed, but no structured data (panels or generic content) was identified."
                )

        return True

    def _parse_to_ast(self):
        """Parses the raw Markdown content into a Mistletoe Document object."""
        if self.raw_content:
            self.mistletoe_doc = Document(self.raw_content)
            print("Document parsed to Mistletoe AST.")

    def _build_structured_data(self):
        """
        Builds a structured representation of the document, including both
        Panel sections and generic content blocks in between or around them.
        """
        if not self.mistletoe_doc or not self.mistletoe_doc.children:
            self.structured_data = []
            print("AST is empty, cannot build structure.")
            return

        self.structured_data = []
        current_generic_blocks = []

        for block in self.mistletoe_doc.children:
            is_h2_panel_heading = False
            panel_title_text = ""
            panel_h2_block_node = None

            if isinstance(block, Heading) and block.level == 2:
                heading_text = get_heading_text(block)
                if heading_text.startswith("Panel "):
                    is_h2_panel_heading = True
                    panel_title_text = heading_text
                    panel_h2_block_node = block

            if is_h2_panel_heading:
                # If there were preceding generic blocks, save them
                if current_generic_blocks:
                    self.structured_data.append(
                        {
                            "type": "generic",
                            "blocks": list(current_generic_blocks),  # Store a copy
                        }
                    )
                    current_generic_blocks = []  # Reset for next generic section

                # Start processing this new panel
                panel_data = {
                    "type": "panel",
                    "panel_title_text": panel_title_text,
                    "panel_h2_block": panel_h2_block_node,
                    "sub_content": [],  # To be filled by _process_single_panel_content
                }
                # We need to collect blocks for *this* panel until the next H2 Panel or end of doc.
                # This requires a lookahead or a different iteration strategy for panel content.
                # For simplicity in this step, we'll assume _process_single_panel_content
                # will be called with the *content blocks* of a panel.
                # The current loop structure is better for identifying sections sequentially.
                # Let's refine: we collect panel blocks here.

                current_panel_content_blocks = (
                    []
                )  # Blocks *after* the H2 heading for this panel
                # This panel_data will be populated with its sub_content later if we decide to
                # pass only its content blocks to a helper.
                # For now, let's just mark its start.
                # The actual panel content (H3s etc.) will be associated when we reconstruct or query.
                # This is a bit tricky. Let's rethink the panel content gathering.

                # Alternative: _build_structured_data identifies sections (generic or panel H2).
                # Panel content parsing happens when a panel section is processed.

                # Let's try this: when a panel H2 is found, we create the panel entry.
                # Subsequent blocks are added to current_generic_blocks until the next panel H2.
                # This means a panel's content isn't immediately part of its structure here.
                # This is not quite right for what we need for modification.

                # Corrected approach for _build_structured_data:
                # It will identify sequences of generic blocks and "Panel" H2s.
                # The detailed parsing of a panel's internal H3s will be done on demand or
                # as a secondary step to populate the "sub_content" for panel-type entries.

                # Simpler: let's assume for now that a "panel" entry in structured_data
                # will contain ALL its blocks, starting from its H2.
                # The _process_panel_internals will then take these blocks.

                # Let's go back to the idea of collecting blocks for a panel once its H2 is found.
                # This means we need to change how `panel_block_groups` was done.

                # New strategy for _build_structured_data:
                # Iterate through all blocks. If it's not a Panel H2, add to current_generic_blocks.
                # If it IS a Panel H2:
                #   1. Store current_generic_blocks if any.
                #   2. Start a new "panel" structure. This panel structure will need to consume
                #      its H2 and all subsequent blocks until the next Panel H2 or end of doc.
                # This implies a nested loop or a state machine.

                # Let's refine the loop:
                # We are iterating block by block.
                # If block is a Panel H2:
                #   If current_generic_blocks is not empty, add it as a generic section.
                #   Start a new panel section, add this H2 block to it.
                #   Mark that we are "in_panel_mode".
                # Else (not a Panel H2):
                #   If "in_panel_mode", add this block to the current panel's blocks.
                #   Else (not in_panel_mode), add to current_generic_blocks.

                # This is still not quite right for preserving the panel's internal structure easily later.
                # The previous approach of `panel_block_groups` was better for isolating panel content.
                # Let's combine:

                # Phase 1: Identify all top-level blocks.
                # Phase 2: Iterate and assign to generic or panel structures.

                all_blocks = list(
                    self.mistletoe_doc.children
                )  # Get all top-level blocks
                idx = 0
                while idx < len(all_blocks):
                    block = all_blocks[idx]
                    is_h2_panel_heading = False
                    panel_title_text = ""
                    panel_h2_block_node = None

                    if isinstance(block, Heading) and block.level == 2:
                        heading_text = get_heading_text(block)
                        if heading_text.startswith("Panel "):
                            is_h2_panel_heading = True
                            panel_title_text = heading_text
                            panel_h2_block_node = block

                    if is_h2_panel_heading:
                        # Current block is an H2 Panel heading.
                        # Collect all blocks belonging to this panel.
                        current_panel_all_blocks = [panel_h2_block_node]
                        panel_content_blocks = (
                            []
                        )  # Blocks after H2 for sub-content processing
                        idx += 1
                        while idx < len(all_blocks):
                            next_block = all_blocks[idx]
                            # Check if next_block is another H2 Panel heading
                            is_next_h2_panel = False
                            if (
                                isinstance(next_block, Heading)
                                and next_block.level == 2
                            ):
                                if get_heading_text(next_block).startswith("Panel "):
                                    is_next_h2_panel = True

                            if is_next_h2_panel:
                                break  # End of current panel
                            else:
                                current_panel_all_blocks.append(next_block)
                                panel_content_blocks.append(next_block)
                                idx += 1

                        # Now process this panel's content for H3s etc.
                        panel_sub_content = self._process_panel_content_for_subsections(
                            panel_content_blocks
                        )
                        self.structured_data.append(
                            {
                                "type": "panel",
                                "panel_title_text": panel_title_text,
                                "panel_h2_block": panel_h2_block_node,
                                "sub_content": panel_sub_content,
                                "_all_panel_blocks": current_panel_all_blocks,  # For easier reconstruction if sub_content isn't used directly
                            }
                        )
                        # idx is already advanced to the start of the next panel or end of doc
                    else:
                        # This block is generic content
                        current_generic_blocks.append(block)
                        idx += 1
                        # If next items are also generic, they'll be caught in next iteration
                        # We need to group consecutive generic blocks
                        if idx == len(all_blocks) or (
                            isinstance(all_blocks[idx], Heading)
                            and all_blocks[idx].level == 2
                            and get_heading_text(all_blocks[idx]).startswith("Panel ")
                        ):
                            # End of generic block sequence
                            if current_generic_blocks:
                                self.structured_data.append(
                                    {
                                        "type": "generic",
                                        "blocks": list(current_generic_blocks),
                                    }
                                )
                                current_generic_blocks = []

                # If there were trailing generic blocks after the last panel
                if current_generic_blocks:
                    self.structured_data.append(
                        {"type": "generic", "blocks": list(current_generic_blocks)}
                    )

        if self.structured_data:
            print(
                f"Document structure built with {len(self.structured_data)} top-level section(s) (panels/generic)."
            )

    def _process_panel_content_for_subsections(self, panel_content_blocks):
        """
        Processes a list of blocks (content of a single panel, after its H2 heading)
        and identifies H3 sub-sections.
        """
        sub_content_list = []
        current_subsection_blocks = []
        active_subsection_title = "Initial Content"
        active_subsection_h3_block = None
        initial_content_processed = False  # To track if we've handled special initial content like "Scene Description"

        # Try to identify "Scene Description" or similar initial content from the first block
        if panel_content_blocks:
            first_block_in_panel = panel_content_blocks[0]
            if isinstance(first_block_in_panel, Paragraph) and not (
                isinstance(first_block_in_panel, Heading)
                and first_block_in_panel.level == 3
            ):
                strong_text = get_paragraph_strong_text(first_block_in_panel)
                if (
                    strong_text and "scene description" in strong_text.lower()
                ):  # Heuristic
                    active_subsection_title = strong_text.rstrip(":")
                    initial_content_processed = True
                    # This first block itself will be added to current_subsection_blocks in the loop.

        for block in panel_content_blocks:
            is_h3_heading = False
            h3_title_text = ""
            h3_block_node = None

            if isinstance(block, Heading) and block.level == 3:
                is_h3_heading = True
                h3_title_text = get_heading_text(block)
                h3_block_node = block

            if is_h3_heading:
                # Finalize previous H3 sub-section or initial content
                # Ensure we add if there are blocks OR if it was titled initial content (even if empty)
                if (
                    current_subsection_blocks
                    or active_subsection_title == "Initial Content"
                    or initial_content_processed
                ):
                    sub_content_list.append(
                        {
                            "sub_heading_text": active_subsection_title,
                            "sub_heading_h3_block": active_subsection_h3_block,
                            "blocks": list(current_subsection_blocks),  # Store a copy
                        }
                    )

                active_subsection_title = h3_title_text
                active_subsection_h3_block = h3_block_node
                current_subsection_blocks = (
                    []
                )  # Reset for content blocks *after* this H3
                initial_content_processed = (
                    False  # Reset this flag for subsequent sections
                )
            else:
                current_subsection_blocks.append(block)

        # Add the last collected sub-section
        if (
            current_subsection_blocks or active_subsection_title
        ):  # Ensure even empty titled sections are added
            sub_content_list.append(
                {
                    "sub_heading_text": active_subsection_title,
                    "sub_heading_h3_block": active_subsection_h3_block,
                    "blocks": list(current_subsection_blocks),
                }
            )
        return sub_content_list

    def get_panel_by_title(self, panel_title_fragment):
        """Retrieves a panel from structured_data by a fragment of its title."""
        for section in self.structured_data:
            if (
                section["type"] == "panel"
                and panel_title_fragment in section["panel_title_text"]
            ):
                return section
        return None

    def get_subsection_by_title(self, panel_data, subsection_title_fragment):
        """Retrieves a subsection from a panel's sub_content by a fragment of its title."""
        if (
            not panel_data
            or panel_data["type"] != "panel"
            or "sub_content" not in panel_data
        ):
            return None
        for sub in panel_data["sub_content"]:
            if subsection_title_fragment in sub["sub_heading_text"]:
                return sub
        return None

    def get_subsection_markdown(self, subsection_data):
        """Renders the blocks of a subsection back to a Markdown string."""
        if (
            not subsection_data
            or "blocks" not in subsection_data
            or not subsection_data["blocks"]
        ):
            return ""
        temp_doc = Document("")
        temp_doc.children = subsection_data["blocks"]
        return self.renderer.render(temp_doc).strip()

    def update_subsection_content(
        self, panel_title_fragment, subsection_title_fragment, new_markdown_content
    ):
        """
        Replaces the content blocks of a specific subsection with new Markdown content.
        """
        panel = self.get_panel_by_title(panel_title_fragment)
        if not panel:
            print(
                f"Error: Panel containing '{panel_title_fragment}' not found for update."
            )
            return False

        subsection_found = False
        for sub_idx, sub in enumerate(panel["sub_content"]):
            if subsection_title_fragment in sub["sub_heading_text"]:
                new_blocks_doc = Document(new_markdown_content)
                panel["sub_content"][sub_idx]["blocks"] = new_blocks_doc.children
                subsection_found = True
                print(
                    f"Successfully updated subsection '{subsection_title_fragment}' in panel '{panel['panel_title_text']}'."
                )
                break

        if not subsection_found:
            print(
                f"Error: Subsection '{subsection_title_fragment}' in Panel '{panel['panel_title_text']}' not found for update."
            )
            return False
        return True

    def add_content_to_subsection(
        self,
        panel_title_fragment,
        subsection_title_fragment,
        new_markdown_content,
        position="end",
    ):
        """Adds new Markdown content (parsed into blocks) to a subsection, either at the start or end."""
        panel = self.get_panel_by_title(panel_title_fragment)
        if not panel:
            print(
                f"Error: Panel '{panel_title_fragment}' not found for adding content."
            )
            return False

        subsection_found = False
        for sub_idx, sub in enumerate(panel["sub_content"]):
            if subsection_title_fragment in sub["sub_heading_text"]:
                new_blocks_doc = Document(new_markdown_content)
                if position == "start":
                    panel["sub_content"][sub_idx]["blocks"] = (
                        new_blocks_doc.children + sub["blocks"]
                    )
                else:  # "end"
                    panel["sub_content"][sub_idx]["blocks"].extend(
                        new_blocks_doc.children
                    )
                subsection_found = True
                print(
                    f"Successfully added content to subsection '{subsection_title_fragment}' (position: {position}) in panel '{panel['panel_title_text']}'."
                )
                break

        if not subsection_found:
            print(
                f"Error: Subsection '{subsection_title_fragment}' in Panel '{panel['panel_title_text']}' not found for adding content."
            )
            return False
        return True

    def reconstruct_and_render_document(self):
        """
        Reconstructs the entire Mistletoe document from the structured_data
        (including generic and panel sections) and renders it back to a Markdown string.
        """
        if not self.structured_data:
            print("No structured data to reconstruct document from.")
            # If raw_content exists, it means load was successful but structure building might have issues or doc was empty.
            # Return raw_content if you want to preserve original if structure fails, or empty if it should reflect structure.
            return self.raw_content if self.raw_content else ""

        all_new_blocks = []
        for section_data in self.structured_data:
            if section_data["type"] == "generic":
                all_new_blocks.extend(section_data["blocks"])
            elif section_data["type"] == "panel":
                # Add the H2 panel heading for this panel
                if section_data["panel_h2_block"]:
                    all_new_blocks.append(section_data["panel_h2_block"])

                # Add content from sub_content
                for sub_content_item in section_data["sub_content"]:
                    # Add the H3 sub-heading if it exists for this sub_content item
                    if sub_content_item["sub_heading_h3_block"]:
                        all_new_blocks.append(sub_content_item["sub_heading_h3_block"])
                    # Add all content blocks of the subsection
                    all_new_blocks.extend(sub_content_item["blocks"])
            else:
                print(
                    f"Warning: Unknown section type '{section_data['type']}' encountered during reconstruction."
                )

        reconstructed_doc = Document("")
        reconstructed_doc.children = all_new_blocks

        # It's good practice to update the model's main AST if it's going to be used further
        # self.mistletoe_doc = reconstructed_doc
        # However, for rendering, this temp doc is sufficient.
        return self.renderer.render(reconstructed_doc)

    def save_document(self, output_filepath):
        """Renders the current state of the document and saves it to a file."""
        rendered_content = self.reconstruct_and_render_document()

        # Check if rendered_content is empty and if there was original raw_content
        # This handles cases where the document might become empty after processing
        if (
            not rendered_content
            and self.raw_content
            and not self.mistletoe_doc.children
        ):
            print(
                "Warning: Document became empty after processing, but had original content. Saving empty file."
            )
        elif not rendered_content and not self.raw_content:
            print(
                "Warning: Document is empty and was originally empty. Nothing to save effectively."
            )
            # Optionally, prevent saving an empty file if it was always empty
            # return False

        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            print(f"Document successfully saved to '{output_filepath}'.")
            return True
        except Exception as e:
            print(f"Error saving document to '{output_filepath}': {e}")
            return False

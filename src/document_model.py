# document_model.py
from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText, Strong


def get_heading_text(heading_node):
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):
                text += child.content
    return text.strip()


def get_paragraph_strong_text(paragraph_node):
    if (
        not paragraph_node
        or not hasattr(paragraph_node, "children")
        or not paragraph_node.children
    ):
        return None
    first_span = paragraph_node.children[0]
    if (
        isinstance(first_span, Strong)
        and first_span.children
        and isinstance(first_span.children[0], RawText)
    ):
        return first_span.children[0].content.strip()
    return None


class MarkdownDocument:
    def __init__(self, filepath=None):
        self.filepath = filepath
        self.raw_content = None
        self.mistletoe_doc = None  # Parsed Mistletoe Document object
        self.structured_data = []  # List of panel structures
        self.renderer = MarkdownRenderer()

        if filepath:
            self.load_and_process(filepath)

    def load_and_process(self, filepath):
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
            self._build_structured_data()
        return True

    def _parse_to_ast(self):
        if self.raw_content:
            self.mistletoe_doc = Document(self.raw_content)
            print("Document parsed to AST.")

    def _build_structured_data(self):
        if not self.mistletoe_doc or not self.mistletoe_doc.children:
            self.structured_data = []
            return

        self.structured_data = []
        panel_block_groups = []
        temp_current_panel_blocks = []

        # 1. Group blocks by H2 "Panel" headings
        for block in self.mistletoe_doc.children:
            is_h2_panel_heading = False
            if isinstance(block, Heading) and block.level == 2:
                heading_text = get_heading_text(block)
                if heading_text.startswith("Panel "):
                    is_h2_panel_heading = True

            if is_h2_panel_heading:
                if temp_current_panel_blocks:
                    panel_block_groups.append(temp_current_panel_blocks)
                temp_current_panel_blocks = [block]
            elif temp_current_panel_blocks:
                temp_current_panel_blocks.append(block)
        if temp_current_panel_blocks:
            panel_block_groups.append(temp_current_panel_blocks)

        # 2. Process each panel group for H3 sub-sections
        for panel_blocks_group in panel_block_groups:
            if not panel_blocks_group:
                continue

            panel_h2_node = panel_blocks_group[
                0
            ]  # This is the H2 Heading mistletoe object
            panel_title_text = get_heading_text(panel_h2_node)

            panel_data = {
                "panel_title_text": panel_title_text,
                "panel_h2_block": panel_h2_node,  # Store the original Mistletoe block
                "sub_content": [],
            }

            content_blocks_for_this_panel = panel_blocks_group[1:]
            current_subsection_blocks = []
            active_subsection_title = "Initial Content"  # Default
            active_subsection_h3_block = None

            # Handle "Scene Description" like elements (first paragraph, bolded)
            # We need to be careful not to consume a legitimate H3 if it's the first content block.
            if content_blocks_for_this_panel:
                first_block = content_blocks_for_this_panel[0]
                if isinstance(first_block, Paragraph) and not (
                    isinstance(first_block, Heading) and first_block.level == 3
                ):
                    scene_desc_text = get_paragraph_strong_text(first_block)
                    if (
                        scene_desc_text
                        and "scene description" in scene_desc_text.lower()
                    ):
                        active_subsection_title = scene_desc_text.rstrip(":")
                        # current_subsection_blocks.append(first_block) # Will be added in the loop
                        # content_blocks_for_this_panel = content_blocks_for_this_panel[1:]

            for block_idx, block in enumerate(content_blocks_for_this_panel):
                is_h3_heading = False
                h3_title_text = ""
                h3_block_node = None

                if isinstance(block, Heading) and block.level == 3:
                    is_h3_heading = True
                    h3_title_text = get_heading_text(block)
                    h3_block_node = block

                # Special case: If this is the first block for "Scene Description"
                if (
                    block_idx == 0
                    and active_subsection_title != "Initial Content"
                    and current_subsection_blocks == []
                ):
                    current_subsection_blocks.append(block)
                    continue

                if is_h3_heading:
                    if (
                        current_subsection_blocks
                        or active_subsection_title == "Initial Content"
                    ):  # Store previous subsection
                        panel_data["sub_content"].append(
                            {
                                "sub_heading_text": active_subsection_title,
                                "sub_heading_h3_block": active_subsection_h3_block,  # Store H3 block if exists
                                "blocks": current_subsection_blocks,
                            }
                        )

                    active_subsection_title = h3_title_text
                    active_subsection_h3_block = h3_block_node
                    current_subsection_blocks = (
                        []
                    )  # Start new list for H3 content blocks (H3 itself will be added by reconstruction if needed or handled separately)
                else:
                    current_subsection_blocks.append(block)

            # Add the last sub-section
            if current_subsection_blocks or active_subsection_title:
                panel_data["sub_content"].append(
                    {
                        "sub_heading_text": active_subsection_title,
                        "sub_heading_h3_block": active_subsection_h3_block,
                        "blocks": current_subsection_blocks,
                    }
                )
            self.structured_data.append(panel_data)
        print(f"Document structure built with {len(self.structured_data)} panels.")

    def get_panel_by_title(self, panel_title_fragment):
        for panel in self.structured_data:
            if panel_title_fragment in panel["panel_title_text"]:
                return panel
        return None

    def get_subsection_by_title(self, panel_data, subsection_title_fragment):
        if not panel_data:
            return None
        for sub in panel_data["sub_content"]:
            if subsection_title_fragment in sub["sub_heading_text"]:
                return sub
        return None

    def get_subsection_markdown(self, subsection_data):
        if not subsection_data or not subsection_data["blocks"]:
            return ""
        temp_doc = Document("")
        temp_doc.children = subsection_data["blocks"]
        return self.renderer.render(temp_doc).strip()

    def update_subsection_content(
        self, panel_title_fragment, subsection_title_fragment, new_markdown_content
    ):
        """
        Updates the content of a specific subsection with new Markdown.
        The new_markdown_content is parsed into Mistletoe blocks.
        This currently only updates the structured_data. Rebuilding the main
        mistletoe_doc from structured_data is needed for full document rendering.
        """
        panel = self.get_panel_by_title(panel_title_fragment)
        if not panel:
            print(f"Error: Panel containing '{panel_title_fragment}' not found.")
            return False

        subsection = self.get_subsection_by_title(panel, subsection_title_fragment)
        if not subsection:
            print(
                f"Error: Subsection containing '{subsection_title_fragment}' in Panel '{panel['panel_title_text']}' not found."
            )
            return False

        # Parse the new markdown content into Mistletoe blocks
        new_blocks_doc = Document(new_markdown_content)
        subsection["blocks"] = new_blocks_doc.children  # Replace with new blocks
        print(
            f"Updated subsection '{subsection_title_fragment}' in panel '{panel['panel_title_text']}'."
        )
        # Note: This modifies structured_data. To see this in a full re-render,
        # self.mistletoe_doc needs to be reconstructed from self.structured_data.
        return True

    def add_content_to_subsection(
        self,
        panel_title_fragment,
        subsection_title_fragment,
        new_markdown_content,
        position="end",
    ):
        """Adds new markdown content to a subsection (start or end)."""
        panel = self.get_panel_by_title(panel_title_fragment)
        if not panel:
            return False
        subsection = self.get_subsection_by_title(panel, subsection_title_fragment)
        if not subsection:
            return False

        new_blocks_doc = Document(new_markdown_content)
        if position == "start":
            subsection["blocks"] = new_blocks_doc.children + subsection["blocks"]
        else:  # end
            subsection["blocks"].extend(new_blocks_doc.children)
        print(
            f"Added content to subsection '{subsection_title_fragment}' in panel '{panel['panel_title_text']}'."
        )
        return True

    def reconstruct_and_render_document(self):
        """
        Reconstructs the Mistletoe document from structured_data and renders it.
        This is key for reflecting modifications made to structured_data in the full output.
        """
        if not self.structured_data:
            return ""

        all_new_blocks = []
        for panel_data in self.structured_data:
            all_new_blocks.append(
                panel_data["panel_h2_block"]
            )  # Add the H2 panel heading
            for sub_content_item in panel_data["sub_content"]:
                if sub_content_item[
                    "sub_heading_h3_block"
                ]:  # If there was an H3 heading for this sub-content
                    all_new_blocks.append(sub_content_item["sub_heading_h3_block"])
                all_new_blocks.extend(
                    sub_content_item["blocks"]
                )  # Add content blocks of the subsection

        reconstructed_doc = Document("")
        reconstructed_doc.children = all_new_blocks
        self.mistletoe_doc = reconstructed_doc  # Update the main AST
        return self.renderer.render(self.mistletoe_doc)

    def save_document(self, output_filepath):
        rendered_content = self.reconstruct_and_render_document()
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            print(f"Document successfully saved to '{output_filepath}'.")
            return True
        except Exception as e:
            print(f"Error saving document: {e}")
            return False

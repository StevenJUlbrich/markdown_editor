# document_model.py
from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText


def get_heading_text(heading_node):
    """
    Extracts the plain text from a Mistletoe Heading node.
    """
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):
                text += child.content
    return text.strip()


class MarkdownDocument:
    """
    Represents and manages a Markdown document, its structure, and modifications.
    Handles H2 Panels, H3 sub-sections, and H4 sub-sub-sections.
    """

    def __init__(self, filepath=None):
        self.filepath = filepath
        self.raw_content = None
        self.mistletoe_doc = None
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
            self._build_structured_data()
            if not self.mistletoe_doc.children:
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
        Builds a structured representation of the document, including generic content,
        H2 Panel sections, H3 sub-sections, and H4 sub-sub-sections.
        """
        if not self.mistletoe_doc or not self.mistletoe_doc.children:
            self.structured_data = []
            print("AST is empty, cannot build structure.")
            return

        self.structured_data = []
        current_generic_blocks = []
        all_top_level_blocks = list(self.mistletoe_doc.children)
        current_block_index = 0

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

            if is_h2_panel_heading:
                if current_generic_blocks:
                    self.structured_data.append(
                        {"type": "generic", "blocks": list(current_generic_blocks)}
                    )
                    current_generic_blocks = []

                panel_content_blocks_for_h3s = []
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

                panel_sub_content = self._process_panel_content_for_h3_subsections(
                    panel_content_blocks_for_h3s
                )
                self.structured_data.append(
                    {
                        "type": "panel",
                        "panel_title_text": panel_title_text,
                        "panel_h2_block": panel_h2_block_node,
                        "sub_content": panel_sub_content,
                    }
                )
            else:
                current_generic_blocks.append(block)
                current_block_index += 1

        if current_generic_blocks:
            self.structured_data.append(
                {"type": "generic", "blocks": list(current_generic_blocks)}
            )

        if self.structured_data:
            print(
                f"Document structure built with {len(self.structured_data)} top-level section(s)."
            )

    def _process_panel_content_for_h3_subsections(self, panel_content_blocks):
        h3_sub_content_list = []
        current_h3_blocks_for_h4s = []
        active_h3_title = "Initial Content"
        active_h3_block_node = None

        if not panel_content_blocks:
            h3_sub_content_list.append(
                {
                    "sub_heading_text": active_h3_title,
                    "sub_heading_h3_block": None,
                    "sub_sub_content": [
                        {
                            "sub_sub_heading_text": "Initial Content",
                            "sub_sub_heading_h4_block": None,
                            "blocks": [],
                        }
                    ],
                }
            )
            return h3_sub_content_list

        for block in panel_content_blocks:
            is_h3_heading = False
            h3_title_text = ""
            h3_block_node = None

            if isinstance(block, Heading) and block.level == 3:
                is_h3_heading = True
                h3_title_text = get_heading_text(block)
                h3_block_node = block

            if is_h3_heading:
                if current_h3_blocks_for_h4s or active_h3_title == "Initial Content":
                    h4_level_content = self._process_h3_content_for_h4_subsubsections(
                        current_h3_blocks_for_h4s
                    )
                    h3_sub_content_list.append(
                        {
                            "sub_heading_text": active_h3_title,
                            "sub_heading_h3_block": active_h3_block_node,
                            "sub_sub_content": h4_level_content,
                        }
                    )
                active_h3_title = h3_title_text
                active_h3_block_node = h3_block_node
                current_h3_blocks_for_h4s = []
            else:
                current_h3_blocks_for_h4s.append(block)

        h4_level_content = self._process_h3_content_for_h4_subsubsections(
            current_h3_blocks_for_h4s
        )
        h3_sub_content_list.append(
            {
                "sub_heading_text": active_h3_title,
                "sub_heading_h3_block": active_h3_block_node,
                "sub_sub_content": h4_level_content,
            }
        )
        return h3_sub_content_list

    def _process_h3_content_for_h4_subsubsections(self, h3_content_blocks):
        h4_sub_sub_content_list = []
        current_h4_blocks = []
        active_h4_title = "Initial Content"
        active_h4_block_node = None

        if not h3_content_blocks:
            h4_sub_sub_content_list.append(
                {
                    "sub_sub_heading_text": active_h4_title,
                    "sub_sub_heading_h4_block": None,
                    "blocks": [],
                }
            )
            return h4_sub_sub_content_list

        for block in h3_content_blocks:
            is_h4_heading = False
            h4_title_text = ""
            h4_block_node = None

            if isinstance(block, Heading) and block.level == 4:
                is_h4_heading = True
                h4_title_text = get_heading_text(block)
                h4_block_node = block

            if is_h4_heading:
                if current_h4_blocks or active_h4_title == "Initial Content":
                    h4_sub_sub_content_list.append(
                        {
                            "sub_sub_heading_text": active_h4_title,
                            "sub_sub_heading_h4_block": active_h4_block_node,
                            "blocks": list(current_h4_blocks),
                        }
                    )
                active_h4_title = h4_title_text
                active_h4_block_node = h4_block_node
                current_h4_blocks = []
            else:
                current_h4_blocks.append(block)

        h4_sub_sub_content_list.append(
            {
                "sub_sub_heading_text": active_h4_title,
                "sub_sub_heading_h4_block": active_h4_block_node,
                "blocks": list(current_h4_blocks),
            }
        )
        return h4_sub_sub_content_list

    def get_panel_by_title(self, panel_title_fragment):
        for section in self.structured_data:
            if section.get("type") == "panel" and panel_title_fragment in section.get(
                "panel_title_text", ""
            ):
                return section
        return None

    def get_subsection_by_title(self, panel_data, h3_subsection_title_fragment):
        if (
            not panel_data
            or panel_data.get("type") != "panel"
            or "sub_content" not in panel_data
        ):
            return None
        for sub in panel_data["sub_content"]:
            if h3_subsection_title_fragment in sub.get("sub_heading_text", ""):
                return sub
        return None

    def get_h4_subsubsection_by_title(
        self, h3_subsection_data, h4_subsubsection_title_fragment
    ):
        if not h3_subsection_data or "sub_sub_content" not in h3_subsection_data:
            return None
        for h4_sub in h3_subsection_data["sub_sub_content"]:
            if h4_subsubsection_title_fragment in h4_sub.get(
                "sub_sub_heading_text", ""
            ):
                return h4_sub
        return None

    def get_panel_full_markdown(self, panel_data):
        """Renders the entire content of an H2 Panel, including its H2 heading and all nested content."""
        if not panel_data or panel_data.get("type") != "panel":
            return "Error: Invalid panel data provided."

        panel_blocks_to_render = []
        if panel_data.get("panel_h2_block"):
            panel_blocks_to_render.append(panel_data["panel_h2_block"])

        for h3_item in panel_data.get("sub_content", []):
            if h3_item.get("sub_heading_h3_block"):
                panel_blocks_to_render.append(h3_item["sub_heading_h3_block"])
            for h4_item in h3_item.get("sub_sub_content", []):
                if h4_item.get("sub_sub_heading_h4_block"):
                    panel_blocks_to_render.append(h4_item["sub_sub_heading_h4_block"])
                panel_blocks_to_render.extend(h4_item.get("blocks", []))

        if not panel_blocks_to_render:
            return ""  # Or a message indicating the panel is empty

        temp_doc = Document("")
        temp_doc.children = panel_blocks_to_render
        return self.renderer.render(temp_doc).strip()

    def get_h3_subsection_full_markdown(self, h3_subsection_data):
        """Renders an H3 subsection, including its H3 heading and all its H4s and content."""
        if not h3_subsection_data:
            return "Error: Invalid H3 subsection data provided."

        h3_blocks_to_render = []
        if h3_subsection_data.get("sub_heading_h3_block"):
            h3_blocks_to_render.append(h3_subsection_data["sub_heading_h3_block"])

        for h4_item in h3_subsection_data.get("sub_sub_content", []):
            if h4_item.get("sub_sub_heading_h4_block"):
                h3_blocks_to_render.append(h4_item["sub_sub_heading_h4_block"])
            h3_blocks_to_render.extend(h4_item.get("blocks", []))

        if not h3_blocks_to_render:
            # This case could mean an H3 section with no H4s and no "Initial Content" blocks,
            # or an "Initial Content" pseudo-H3 section that is empty.
            return (
                ""
                if not h3_subsection_data.get("sub_heading_h3_block")
                else self.renderer.render(
                    h3_subsection_data["sub_heading_h3_block"]
                ).strip()
            )

        temp_doc = Document("")
        temp_doc.children = h3_blocks_to_render
        return self.renderer.render(temp_doc).strip()

    def get_h4_subsubsection_full_markdown(self, h4_subsubsection_data):
        """Renders an H4 sub-subsection, including its H4 heading and content blocks."""
        if not h4_subsubsection_data:
            return "Error: Invalid H4 sub-subsection data provided."

        h4_blocks_to_render = []
        if h4_subsubsection_data.get("sub_sub_heading_h4_block"):
            h4_blocks_to_render.append(
                h4_subsubsection_data["sub_sub_heading_h4_block"]
            )
        h4_blocks_to_render.extend(h4_subsubsection_data.get("blocks", []))

        if not h4_blocks_to_render:
            return (
                ""
                if not h4_subsubsection_data.get("sub_sub_heading_h4_block")
                else self.renderer.render(
                    h4_subsubsection_data["sub_sub_heading_h4_block"]
                ).strip()
            )

        temp_doc = Document("")
        temp_doc.children = h4_blocks_to_render
        return self.renderer.render(temp_doc).strip()

    def get_specific_section_markdown_content(
        self, panel_data, h3_title_fragment=None, h4_title_fragment=None
    ):
        """
        Retrieves markdown for H2, H3, or H4 level based on provided fragments.
        If only panel_data is provided, returns full H2 panel content.
        If h3_title_fragment is provided, returns full H3 content.
        If h4_title_fragment is also provided, returns full H4 content.
        """
        if not panel_data or panel_data.get("type") != "panel":
            return "Error: Invalid panel data."

        if not h3_title_fragment:  # Target is the H2 Panel itself
            return self.get_panel_full_markdown(panel_data)

        h3_section = self.get_subsection_by_title(panel_data, h3_title_fragment)
        if not h3_section:
            return f"Error: H3 Sub-section '{h3_title_fragment}' not found in panel '{panel_data.get('panel_title_text')}'. "

        if not h4_title_fragment:  # Target is the H3 Sub-section
            return self.get_h3_subsection_full_markdown(h3_section)

        # Target is an H4 Sub-sub-section
        h4_section = self.get_h4_subsubsection_by_title(h3_section, h4_title_fragment)
        if not h4_section:
            return f"Error: H4 Sub-sub-section '{h4_title_fragment}' not found in H3 '{h3_title_fragment}'. "
        return self.get_h4_subsubsection_full_markdown(h4_section)

    def update_subsection_content(
        self,
        panel_title_fragment,
        h3_subsection_title_fragment,
        new_markdown_content,
        h4_subsubsection_title_fragment=None,
    ):
        panel = self.get_panel_by_title(panel_title_fragment)
        if not panel:
            print(f"Panel '{panel_title_fragment}' not found.")
            return False

        h3_section = self.get_subsection_by_title(panel, h3_subsection_title_fragment)
        if not h3_section:
            print(f"H3 Subsection '{h3_subsection_title_fragment}' not found.")
            return False

        target_section_data_dict = (
            None  # This will be the dictionary whose "blocks" key we modify
        )
        target_section_name = ""

        if h4_subsubsection_title_fragment:
            # Find the specific H4 dict within h3_section["sub_sub_content"]
            for h4_s_dict in h3_section["sub_sub_content"]:
                if (
                    h4_s_dict.get("sub_sub_heading_text")
                    == h4_subsubsection_title_fragment
                ):
                    target_section_data_dict = h4_s_dict
                    target_section_name = f"H4 '{h4_subsubsection_title_fragment}'"
                    break
            if not target_section_data_dict:
                print(
                    f"H4 Sub-subsection '{h4_subsubsection_title_fragment}' not found for update."
                )
                return False
        else:
            # Target H3's "Initial Content" (blocks directly under H3, not under an H4)
            for h4_s_dict in h3_section.get("sub_sub_content", []):
                if (
                    h4_s_dict.get("sub_sub_heading_text") == "Initial Content"
                    and h4_s_dict.get("sub_sub_heading_h4_block") is None
                ):
                    target_section_data_dict = h4_s_dict
                    target_section_name = (
                        f"H3 '{h3_subsection_title_fragment}' (Initial Content)"
                    )
                    break
            if not target_section_data_dict:
                print(
                    f"Warning: Could not find 'Initial Content' for H3 '{h3_subsection_title_fragment}' to update."
                )
                return False

        if target_section_data_dict is not None:
            new_blocks_doc = Document(new_markdown_content)
            target_section_data_dict["blocks"] = new_blocks_doc.children
            print(
                f"Successfully updated {target_section_name} in panel '{panel['panel_title_text']}'."
            )
            return True

        print(
            f"Error: Could not find appropriate block list to update for H3 '{h3_subsection_title_fragment}'."
        )
        return False

    def add_content_to_subsection(
        self,
        panel_title_fragment,
        h3_subsection_title_fragment,
        new_markdown_content,
        position="end",
        h4_subsubsection_title_fragment=None,
    ):
        panel = self.get_panel_by_title(panel_title_fragment)
        if not panel:
            print(f"Panel '{panel_title_fragment}' not found.")
            return False

        h3_section = self.get_subsection_by_title(panel, h3_subsection_title_fragment)
        if not h3_section:
            print(f"H3 Subsection '{h3_subsection_title_fragment}' not found.")
            return False

        target_section_data_dict = (
            None  # This will be the dictionary whose "blocks" key we modify
        )
        target_section_name = ""

        if h4_subsubsection_title_fragment:
            for h4_s_dict in h3_section["sub_sub_content"]:
                if (
                    h4_s_dict.get("sub_sub_heading_text")
                    == h4_subsubsection_title_fragment
                ):
                    target_section_data_dict = h4_s_dict
                    target_section_name = f"H4 '{h4_subsubsection_title_fragment}'"
                    break
            if not target_section_data_dict:
                print(
                    f"H4 Sub-subsection '{h4_subsubsection_title_fragment}' not found for adding content."
                )
                return False
        else:
            for h4_s_dict in h3_section.get("sub_sub_content", []):
                if (
                    h4_s_dict.get("sub_sub_heading_text") == "Initial Content"
                    and h4_s_dict.get("sub_sub_heading_h4_block") is None
                ):
                    target_section_data_dict = h4_s_dict
                    target_section_name = (
                        f"H3 '{h3_subsection_title_fragment}' (Initial Content)"
                    )
                    break
            if not target_section_data_dict:
                print(
                    f"Warning: Could not find 'Initial Content' for H3 '{h3_subsection_title_fragment}' to add to."
                )
                return False

        if target_section_data_dict is not None:
            new_blocks_doc = Document(new_markdown_content)
            # Ensure "blocks" key exists, initialize if not (though it should by parsing logic)
            if "blocks" not in target_section_data_dict:
                target_section_data_dict["blocks"] = []

            if position == "start":
                target_section_data_dict["blocks"] = (
                    new_blocks_doc.children + target_section_data_dict["blocks"]
                )
            else:  # "end"
                target_section_data_dict["blocks"].extend(new_blocks_doc.children)
            print(
                f"Successfully added content to {target_section_name} (position: {position}) in panel '{panel['panel_title_text']}'."
            )
            return True

        print(
            f"Error: Could not find appropriate block list to add content for H3 '{h3_subsection_title_fragment}'."
        )
        return False

    def reconstruct_and_render_document(self):
        if not self.structured_data:
            return self.raw_content if self.raw_content else ""

        all_new_blocks = []
        for section_data in self.structured_data:
            if section_data.get("type") == "generic":
                all_new_blocks.extend(section_data.get("blocks", []))
            elif section_data.get("type") == "panel":
                if section_data.get("panel_h2_block"):
                    all_new_blocks.append(section_data["panel_h2_block"])

                for h3_sub_item in section_data.get("sub_content", []):
                    if h3_sub_item.get("sub_heading_h3_block"):
                        all_new_blocks.append(h3_sub_item["sub_heading_h3_block"])

                    for h4_sub_sub_item in h3_sub_item.get("sub_sub_content", []):
                        if h4_sub_sub_item.get("sub_sub_heading_h4_block"):
                            all_new_blocks.append(
                                h4_sub_sub_item["sub_sub_heading_h4_block"]
                            )
                        all_new_blocks.extend(h4_sub_sub_item.get("blocks", []))
            else:
                print(
                    f"Warning: Unknown section type '{section_data.get('type')}' encountered."
                )

        reconstructed_doc = Document("")
        reconstructed_doc.children = all_new_blocks
        return self.renderer.render(reconstructed_doc)

    def save_document(self, output_filepath):
        rendered_content = self.reconstruct_and_render_document()
        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_content)
            print(f"Document successfully saved to '{output_filepath}'.")
            return True
        except Exception as e:
            print(f"Error saving document to '{output_filepath}': {e}")
            return False

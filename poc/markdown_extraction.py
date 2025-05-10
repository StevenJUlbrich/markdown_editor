from mistletoe import Document
from mistletoe.block_token import Heading, Paragraph
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import RawText, Strong


def get_heading_text(heading_node):
    """Extracts the plain text from a Mistletoe Heading node."""
    text = ""
    if hasattr(heading_node, "children"):
        for child in heading_node.children:
            if hasattr(child, "content"):
                text += child.content
    return text.strip()


def get_paragraph_strong_text(paragraph_node):
    """
    If a paragraph starts with strongly emphasized text, returns that text.
    Used for 'Scene Description' like elements.
    """
    if not paragraph_node.children:
        return None
    first_span = paragraph_node.children[0]
    if (
        isinstance(first_span, Strong)
        and first_span.children
        and isinstance(first_span.children[0], RawText)
    ):
        return first_span.children[0].content.strip()
    return None


def analyze_document_structure(file_path):
    """
    Loads a Markdown file, parses it, and creates a structured
    representation of "Panel" sections and their sub-sections.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fin:
            markdown_content = fin.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

    doc = Document(markdown_content)

    structured_data = []
    current_panel_raw_blocks = []  # Blocks for the current H2 panel

    # First, split the document by H2 "Panel" headings
    # This logic is similar to extract_panel_sections but we'll store blocks directly

    panel_block_groups = []
    temp_current_panel_blocks = []

    for i, block in enumerate(doc.children):
        is_h2_panel_heading = False
        h2_title_text = ""

        if isinstance(block, Heading) and block.level == 2:
            heading_text = get_heading_text(block)
            if heading_text.startswith("Panel "):
                is_h2_panel_heading = True
                h2_title_text = heading_text

        if is_h2_panel_heading:
            if temp_current_panel_blocks:  # Finalize previous panel
                panel_block_groups.append(temp_current_panel_blocks)
            temp_current_panel_blocks = [block]  # Start new panel with its H2 heading
        elif temp_current_panel_blocks:  # If we are in a panel, collect its blocks
            temp_current_panel_blocks.append(block)

    if temp_current_panel_blocks:  # Add the last panel
        panel_block_groups.append(temp_current_panel_blocks)

    # Now, process each panel group to find H3 sub-sections
    for panel_blocks_group in panel_block_groups:
        if not panel_blocks_group:
            continue

        panel_h2_node = panel_blocks_group[0]
        panel_title = get_heading_text(panel_h2_node)

        panel_data = {
            "panel_title": panel_title,
            "panel_h2_markdown": f"## {panel_title}",
            "sub_content": [],  # Will store intro content and H3 sub-sections
        }

        # Blocks within this panel, excluding the H2 heading itself
        content_blocks_for_this_panel = panel_blocks_group[1:]

        current_subsection_blocks = []
        current_h3_title = None  # For blocks before the first H3
        active_h3_markdown_title = (
            "Initial Content"  # Default for content before first H3
        )

        # Special handling for "Scene Description" which is often a bolded paragraph
        # This assumes "Scene Description" if present, is the first content block.
        if content_blocks_for_this_panel:
            first_content_block = content_blocks_for_this_panel[0]
            if isinstance(first_content_block, Paragraph):
                scene_desc_text = get_paragraph_strong_text(first_content_block)
                if (
                    scene_desc_text and "scene description" in scene_desc_text.lower()
                ):  # Basic check
                    active_h3_markdown_title = scene_desc_text.rstrip(
                        ":"
                    )  # Use the bolded text as title
                    current_subsection_blocks.append(first_content_block)
                    content_blocks_for_this_panel = content_blocks_for_this_panel[
                        1:
                    ]  # Consume it

        for block in content_blocks_for_this_panel:
            is_h3_heading = False
            h3_title_text = ""

            if isinstance(block, Heading) and block.level == 3:
                is_h3_heading = True
                h3_title_text = get_heading_text(block)

            if is_h3_heading:
                # Finalize previous H3 sub-section or initial content
                if (
                    current_subsection_blocks
                    or active_h3_markdown_title == "Initial Content"
                    and not current_subsection_blocks
                ):
                    panel_data["sub_content"].append(
                        {
                            "sub_heading_text": active_h3_markdown_title,
                            "blocks": current_subsection_blocks,
                        }
                    )

                active_h3_markdown_title = h3_title_text
                current_subsection_blocks = [
                    block
                ]  # Start new H3 section with its H3 heading
            else:
                current_subsection_blocks.append(block)

        # Add the last H3 sub-section or remaining initial content
        if current_subsection_blocks or active_h3_markdown_title:
            panel_data["sub_content"].append(
                {
                    "sub_heading_text": active_h3_markdown_title,
                    "blocks": current_subsection_blocks,
                }
            )

        structured_data.append(panel_data)

    return structured_data


def print_structured_data(data):
    if not data:
        print("No data to display.")
        return

    renderer = MarkdownRenderer()
    for i, panel in enumerate(data):
        print(f"\n=================================================")
        print(f"PANEL {i+1}: {panel['panel_title']}")
        print(f"=================================================\n")

        for sub_section in panel["sub_content"]:
            print(f"  --- Sub-Section: {sub_section['sub_heading_text']} ---")
            if sub_section["blocks"]:
                # Render the blocks for this sub-section back to Markdown for display
                # Create a temporary Document to render these blocks
                temp_doc = Document("")
                temp_doc.children = sub_section["blocks"]
                sub_section_markdown = renderer.render(temp_doc)
                print(sub_section_markdown.strip())
            else:
                print("    (No content blocks for this sub-section)")
            print(f"  --- End Sub-Section: {sub_section['sub_heading_text']} ---\n")


# --- Main Execution ---
if __name__ == "__main__":
    markdown_file = "chapter_01_draft.md"

    # Ensure mistletoe is installed in your environment
    # (e.g., conda install -c conda-forge mistletoe)

    parsed_structure = analyze_document_structure(markdown_file)

    if parsed_structure:
        print_structured_data(parsed_structure)

        # Example of how to access specific parts:
        # if len(parsed_structure) > 0 and len(parsed_structure[0]['sub_content']) > 1:
        #     print("\n\n--- Example Access ---")
        #     first_panel = parsed_structure[0]
        #     second_sub_section = first_panel['sub_content'][1] # e.g., Teaching Narrative
        #     print(f"Title of second sub-section in first panel: {second_sub_section['sub_heading_text']}")
        #     # You can then take second_sub_section['blocks'] and send to OpenAI, modify, etc.

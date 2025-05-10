from mistletoe import Document
from mistletoe.block_token import Heading
from mistletoe.markdown_renderer import (
    MarkdownRenderer,
)  # Ensure this import is correct


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


def extract_panel_sections(file_path):
    """
    Loads a Markdown file, parses it with Mistletoe, extracts sections
    starting with "## Panel X:", and prints their Markdown content.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as fin:
            markdown_content = fin.read()
        print(f"Successfully loaded '{file_path}'.\n")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("--- Parsing with Mistletoe ---")
    doc = Document(markdown_content)
    print("Successfully parsed the document.\n")

    panel_sections = []
    current_panel_blocks = []
    current_panel_title = None

    for i, block in enumerate(doc.children):
        is_panel_heading = False
        panel_heading_text = ""

        if isinstance(block, Heading) and block.level == 2:
            heading_text = get_heading_text(block)
            if heading_text.startswith("Panel "):
                is_panel_heading = True
                # Reconstruct the full heading markdown for the title.
                # For simplicity in just getting the title, the raw text is often enough.
                # If you need the exact Markdown like "## Panel X: Title", you'd use the renderer on just the heading.
                current_panel_title_text = f"## {heading_text}"

        if is_panel_heading:
            if current_panel_title and current_panel_blocks:
                panel_sections.append(
                    {
                        "title": current_panel_title,  # Use the title captured when the previous panel started
                        "blocks": current_panel_blocks,
                    }
                )

            current_panel_title = (
                current_panel_title_text  # Set title for the new panel
            )
            current_panel_blocks = [block]  # Start with the heading itself
        elif current_panel_title:  # Important: check if we are actually inside a panel
            current_panel_blocks.append(block)

    if current_panel_title and current_panel_blocks:
        panel_sections.append(
            {"title": current_panel_title, "blocks": current_panel_blocks}
        )

    if not panel_sections:
        print("No 'Panel X:' sections found in the document.")
        return

    print(f"\n--- Extracted Panel Sections ({len(panel_sections)} found) ---")

    # Initialize the renderer once
    # The 'with' statement is good practice if the renderer had __enter__/__exit__
    # For MarkdownRenderer, direct instantiation is also fine.
    renderer = MarkdownRenderer()  # Or with MarkdownRenderer() as renderer:

    for i, section in enumerate(panel_sections):
        print(f"\n--- Panel Extracted #{i+1} ---")
        print(f"Title: {section['title']}")

        # Create a temporary Document object to render the list of blocks
        # The Document constructor expects an iterable (e.g., a string or list of lines to parse).
        # To use existing tokens, we create a dummy Document and then assign its children.
        temp_doc = Document(
            ""
        )  # Pass an empty string for parsing, not strictly necessary if children are immediately replaced
        temp_doc.children = section[
            "blocks"
        ]  # Manually assign the already parsed blocks

        # Now render the temporary document which contains only the panel's blocks
        panel_markdown_content = renderer.render(temp_doc)

        print("Content:")
        # The renderer might add an extra newline at the end, strip() can clean it up.
        print(panel_markdown_content.strip())
        print("--- End of Panel ---")
        if i < len(panel_sections) - 1:
            print("\n=====================================\n")


# --- Main Execution ---
if __name__ == "__main__":
    markdown_file = "chapter_01_draft.md"
    extract_panel_sections(markdown_file)

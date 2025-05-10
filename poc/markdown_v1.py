from mistletoe import Document
from mistletoe.ast_renderer import ASTRenderer  # For a detailed AST view
from mistletoe.block_token import (
    BlockCode,
    Heading,
    List,
    Paragraph,
    Quote,
    Table,
    ThematicBreak,
)
from mistletoe.span_token import (
    AutoLink,
    Emphasis,
    Image,
    LineBreak,
    Link,
    RawText,
    Strong,
)


def review_markdown_parsing(file_path):
    """
    Loads a Markdown file, parses it with Mistletoe, and prints a review
    of the parsed structure, highlighting Panel sections.
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

    print("--- Document Structure Review (Top-Level Blocks) ---")
    for i, block in enumerate(doc.children):
        block_type = type(block).__name__
        print(f"\nBlock {i+1}: Type = {block_type}")

        if isinstance(block, Heading):
            # To get the text of a heading, we need to combine its children (span tokens)
            heading_text = ""
            for span_child in block.children:
                if hasattr(span_child, "content"):  # e.g., RawText
                    heading_text += span_child.content
                # Could add more checks for other span tokens like Emphasis, etc.
                # if you expect them within your panel titles
            print(f"  Level: {block.level}")
            print(f"  Text: '{heading_text.strip()}'")
            if heading_text.strip().startswith("Panel "):
                print(f"  >>> This is a 'Panel' heading!")
        elif isinstance(block, Paragraph):
            # Similar to heading, get text from children span tokens
            para_text = ""
            for span_child in block.children:
                if hasattr(span_child, "content"):
                    para_text += span_child.content
            print(
                f"  Content Snippet: '{para_text.strip()[:100]}...'"
            )  # Print a snippet
        elif isinstance(block, List):
            print(f"  Start Number (if ordered): {block.start}")
            print(f"  List Items: {len(block.children)}")
            # You could iterate through block.children (which are ListItems) for more detail
        elif isinstance(block, BlockCode):
            print(f"  Language: '{block.language}'")
            print(f"  Content Snippet: '{block.children[0].content.strip()[:100]}...'")
        elif isinstance(block, ThematicBreak):
            print("  (Horizontal Rule ---)")
        elif isinstance(block, Quote):
            print("  (Blockquote)")
            # block.children would contain the paragraphs/blocks inside the quote
        else:
            print("  (Other block type, content not fully displayed here for brevity)")

    print("\n--- Detailed AST (First few top-level nodes) ---")
    # The ASTRenderer gives a very detailed, nested view.
    # This can be overwhelming for the whole document, so let's limit it.
    # You can render the whole 'doc' if you want a complete AST dump.
    renderer = ASTRenderer()
    for i, block in enumerate(doc.children):
        if i < 5:  # Print AST for the first 5 blocks
            print(f"\nAST for Block {i+1}:")
            print(renderer.render(block))
        else:
            break
    if len(doc.children) > 5:
        print("\n(AST review limited to the first 5 top-level blocks for brevity)")

    print("\n--- Review Complete ---")


# --- Main Execution ---
if __name__ == "__main__":
    # Make sure 'chapter_01_draft.md' is in the same directory as the script,
    # or provide the full path to the file.
    markdown_file = "chapter_01_draft.md"
    review_markdown_parsing(markdown_file)

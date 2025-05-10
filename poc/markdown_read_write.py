from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer


def test_read_parse_write_cycle(input_filepath, output_filepath):
    """
    Reads a Markdown file, parses it with Mistletoe, renders it back
    to Markdown, and saves it to a new file.
    """
    try:
        with open(input_filepath, "r", encoding="utf-8") as fin:
            original_markdown_content = fin.read()
        print(f"Successfully loaded '{input_filepath}'.")
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    print("--- Parsing with Mistletoe ---")
    # Parse the original content into a Mistletoe Document object
    doc = Document(original_markdown_content)
    print("Successfully parsed the document.")

    print("--- Rendering back to Markdown ---")
    # Initialize the MarkdownRenderer
    # The 'with' statement isn't strictly necessary for MarkdownRenderer
    # as it doesn't manage external resources like file handles in its __enter__/__exit__
    # but it's harmless. Direct instantiation is fine too.
    renderer = MarkdownRenderer()

    # Render the entire Document object back to a Markdown string
    reread_markdown_content = renderer.render(doc)
    print("Successfully rendered the document back to a Markdown string.")

    try:
        with open(output_filepath, "w", encoding="utf-8") as fout:
            fout.write(reread_markdown_content)
        print(f"Successfully saved the re-rendered Markdown to '{output_filepath}'.")
    except Exception as e:
        print(f"Error writing output file: {e}")
        return

    print("\n--- Cycle Complete ---")
    print(
        f"Please compare the original file ('{input_filepath}') with the re-rendered file ('{output_filepath}')."
    )
    print("You can use a diff tool to see any differences.")
    print(
        "Minor differences in whitespace or list markers can sometimes occur due to normalization by the renderer."
    )


# --- Main Execution ---
if __name__ == "__main__":
    original_file = "chapter_01_draft.md"  # Your input file
    output_file = "chapter_01_reread.md"  # Name for the re-rendered output file

    # Ensure mistletoe is installed in your environment
    # (e.g., conda install -c conda-forge mistletoe)
    test_read_parse_write_cycle(original_file, output_file)

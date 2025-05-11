# test_renderer.py
from mistletoe.markdown_renderer import MarkdownRenderer

try:
    print("Attempting to create MarkdownRenderer...")
    renderer = MarkdownRenderer()
    print("MarkdownRenderer created successfully!")
except Exception as e:
    print(f"Error creating MarkdownRenderer: {e}")
    import traceback

    traceback.print_exc()

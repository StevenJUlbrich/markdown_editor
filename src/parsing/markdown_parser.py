from mistletoe import Document


class MarkdownParser:
    """
    Minimalist Markdown parser that wraps mistletoe.Document.
    This class only parses raw markdown text to a mistletoe AST.
    All model building, metadata, and enforcement is handled by the builder layer.
    """

    @staticmethod
    def parse(markdown_text: str) -> Document:
        """
        Parse raw markdown text to a mistletoe AST Document.

        :param markdown_text: The raw markdown file contents.
        :return: A mistletoe Document AST.
        """
        return Document(markdown_text)

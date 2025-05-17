from mistletoe import Document


class MarkdownParser:
    @staticmethod
    def parse(markdown_text: str) -> Document:
        return Document(markdown_text)

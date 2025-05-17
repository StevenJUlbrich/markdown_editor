from .block_token import Heading, BlockCode, Paragraph
from .markdown_renderer import MarkdownRenderer


class Document:
    """Very small subset of mistletoe's Document for tests."""

    def __init__(self, text: str = ""):
        self.renderer = MarkdownRenderer()
        self.children = []
        if text:
            self.children = self._parse(text)

    def _parse(self, text: str):
        tokens = []
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("```"):
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                tokens.append(BlockCode("\n".join(code_lines)))
                # skip closing fence
            elif line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line[level:].strip()
                tokens.append(Heading(level, title))
            elif line.strip():
                tokens.append(Paragraph(line.strip()))
            i += 1
        return tokens

from .block_token import BlockCode, Heading, Paragraph
from .markdown_renderer import MarkdownRenderer

class Document:
    def __init__(self, text: str = ''):
        self.renderer = MarkdownRenderer()
        self.children = []
        lines = text.splitlines()
        in_code = False
        code_lines = []
        for line in lines:
            if line.startswith('```'):
                if in_code:
                    self.children.append(BlockCode('\n'.join(code_lines)))
                    code_lines = []
                    in_code = False
                else:
                    in_code = True
                continue
            if in_code:
                code_lines.append(line)
                continue
            if line.startswith('### '):
                self.children.append(Heading(3, line[4:].strip()))
            elif line.startswith('## '):
                self.children.append(Heading(2, line[3:].strip()))
            elif line.strip():
                self.children.append(Paragraph(line.strip()))
            else:
                self.children.append(Paragraph(''))
        if in_code:
            self.children.append(BlockCode('\n'.join(code_lines)))

from .block_token import Heading, BlockCode, Paragraph

class MarkdownRenderer:
    def render(self, document) -> str:
        lines = []
        for block in getattr(document, 'children', []):
            if isinstance(block, Heading):
                text = ''.join(child.content for child in block.children)
                lines.append('#' * block.level + ' ' + text)
            elif isinstance(block, BlockCode):
                lines.append('```')
                lines.extend(block.children[0].content.splitlines())
                lines.append('```')
            elif isinstance(block, Paragraph):
                lines.append(block.children[0].content)
            else:
                lines.append(str(block))
        return '\n'.join(lines)

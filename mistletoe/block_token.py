class Text:
    def __init__(self, content: str):
        self.content = content

class BlockToken:
    pass

class Heading(BlockToken):
    def __init__(self, level: int, text: str):
        self.level = level
        self.children = [Text(text)]

class BlockCode(BlockToken):
    def __init__(self, text: str):
        self.children = [Text(text)]

class Paragraph(BlockToken):
    def __init__(self, text: str):
        self.children = [Text(text)]

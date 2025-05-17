class MarkdownFileManager:
    @staticmethod
    def read_file(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_file(filepath: str, content: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

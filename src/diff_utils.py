# diff_utils.py
import difflib

# ANSI escape codes for colors
COLOR_GREEN = "\033[92m"  # Green for additions
COLOR_RED = "\033[91m"  # Red for deletions
COLOR_END = "\033[0m"  # Reset color


def generate_text_diff(text1: str, text2: str, colored: bool = True) -> str:
    """
    Generates a text-based diff between two strings, with optional ANSI coloring.
    """
    diff = difflib.unified_diff(
        text1.splitlines(keepends=True),
        text2.splitlines(keepends=True),
        fromfile="Original",
        tofile="Improved",
        lineterm="",  # Important to avoid extra newlines from difflib
    )

    diff_output = []
    for line in diff:
        if colored:
            if line.startswith("+") and not line.startswith("+++"):
                diff_output.append(COLOR_GREEN + line + COLOR_END)
            elif line.startswith("-") and not line.startswith("---"):
                diff_output.append(COLOR_RED + line + COLOR_END)
            else:
                diff_output.append(line)
        else:
            diff_output.append(line)

    if not diff_output:  # If texts are identical
        return "Texts are identical."

    return "".join(diff_output)


if __name__ == "__main__":
    # Example Usage
    original_text = """### Original Section
This is the first line.
This line is old.
This line remains the same.
Another common line."""

    improved_text = """### Original Section
This is the first line, slightly modified.
This line is new.
This line remains the same.
Another common line, but improved."""

    print("--- Colored Diff ---")
    colored_diff = generate_text_diff(original_text, improved_text)
    print(colored_diff)

    print("\n--- Plain Diff ---")
    plain_diff = generate_text_diff(original_text, improved_text, colored=False)
    print(plain_diff)

    print("\n--- Identical Diff ---")
    identical_diff = generate_text_diff("hello world", "hello world")
    print(identical_diff)

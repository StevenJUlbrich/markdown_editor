#!/usr/bin/env python3

import os
import re
from logging_config import get_logger

logger = get_logger(__name__)

# Strict header matches
STRICT_HEADERS = {"## Learning Objectives", "## Key Takeaways"}

# Flexible pattern for headers starting with "## Panel 1"
PANEL_PATTERN = re.compile(r"^## Panel 1\b")


def should_insert_dash(line):
    stripped = line.strip()
    return stripped in STRICT_HEADERS or PANEL_PATTERN.match(stripped)


def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        if should_insert_dash(line):
            updated_lines.append("---\n")
        updated_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

    logger.info("✔ %s", file_path)


def process_folder(folder_path):
    for fname in os.listdir(folder_path):
        if fname.endswith(".md"):
            process_file(os.path.join(folder_path, fname))


def main():
    path = input("Enter path to a markdown file or folder: ").strip()

    if os.path.isfile(path) and path.endswith(".md"):
        process_file(path)
    elif os.path.isdir(path):
        process_folder(path)
    else:
        logger.error(
            "❌ Invalid input. Please provide a markdown file or a folder of .md files."
        )


if __name__ == "__main__":
    main()

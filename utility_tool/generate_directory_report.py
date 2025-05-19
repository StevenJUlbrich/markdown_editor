import argparse
import fnmatch  # Added for pattern matching
import os
from pathlib import Path

# Define patterns for Python cache files and folders to ignore
PYTHON_CACHE_IGNORE_PATTERNS = [
    "__pycache__",  # Standard cache directory
    "*.pyc",  # Compiled Python files
    "*.pyo",  # Optimized compiled Python files
    "*.pyd",  # C extensions (often alongside .py files)
    ".pytest_cache",  # Pytest cache
    ".mypy_cache",  # MyPy cache
]


def should_ignore_item(item_name, ignore_patterns):
    """
    Checks if an item name matches any of the ignore patterns.

    Args:
        item_name (str): The name of the file or directory.
        ignore_patterns (list): A list of patterns to ignore.

    Returns:
        bool: True if the item should be ignored, False otherwise.
    """
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(item_name, pattern):
            return True
    return False


def generate_directory_report(
    source_dir, output_file, ignore_patterns=PYTHON_CACHE_IGNORE_PATTERNS
):
    """
    Generate a structured directory report similar to the tree command,
    ignoring specified patterns.

    Args:
        source_dir (str): Source directory path.
        output_file (str): Output file path for the report.
        ignore_patterns (list, optional): Patterns to ignore.
                                          Defaults to PYTHON_CACHE_IGNORE_PATTERNS.
    """
    # Convert to absolute path
    source_dir = os.path.abspath(source_dir)

    # Get base directory name
    base_name = os.path.basename(source_dir)

    # Initialize the report with the base directory
    report = [f"{base_name}/"]

    # Process directory tree
    def process_directory(directory, prefix="", is_last=False):
        # Get all items in the directory
        try:
            all_items = sorted(os.listdir(directory))
        except PermissionError:
            report.append(
                f"{prefix}└── [Error: Permission Denied to read {os.path.basename(directory)}/]"
            )
            return

        # Filter items based on ignore_patterns
        items_to_process = [
            item for item in all_items if not should_ignore_item(item, ignore_patterns)
        ]

        dirs = [
            item
            for item in items_to_process
            if os.path.isdir(os.path.join(directory, item))
        ]
        files = [
            item
            for item in items_to_process
            if os.path.isfile(os.path.join(directory, item))
        ]

        # Process directories first
        for i, dir_name in enumerate(dirs):
            # Check if this is the last item to be listed in the current directory
            # (considering both remaining dirs and all files)
            is_last_entry_in_current_level = (i == len(dirs) - 1) and (len(files) == 0)

            dir_prefix = "└── " if is_last_entry_in_current_level else "├── "
            report.append(f"{prefix}{dir_prefix}{dir_name}/")

            # Process subdirectory
            next_prefix = prefix + (
                "    " if is_last_entry_in_current_level else "│   "
            )
            process_directory(os.path.join(directory, dir_name), next_prefix)

        # Then process files
        for i, file_name in enumerate(files):
            is_last_file = i == len(files) - 1

            file_prefix = "└── " if is_last_file else "├── "
            report.append(f"{prefix}{file_prefix}{file_name}")

    # Start processing from the source directory
    process_directory(source_dir)

    # Write report to file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
    except IOError as e:
        print(f"Error writing report to file '{output_file}': {e}")
        # Optionally, re-raise or handle more gracefully
        raise

    return report


def main():
    """Main function to run the script from command line"""
    # Get source directory and output file from user input
    source_dir = input("Enter the source directory path: ")
    output_file = input("Enter the path where the report should be saved: ")

    # Validate source directory
    if not os.path.isdir(source_dir):
        print(f"Error: '{source_dir}' is not a valid directory")
        return

    # Ensure output directory exists
    output_dir_path = os.path.dirname(output_file)
    if output_dir_path and not os.path.exists(output_dir_path):
        try:
            os.makedirs(output_dir_path)
            print(f"Created output directory: {output_dir_path}")
        except OSError as e:
            print(f"Error creating output directory '{output_dir_path}': {e}")
            return

    # Generate and save the report
    try:
        print(f"\nIgnoring cache patterns: {', '.join(PYTHON_CACHE_IGNORE_PATTERNS)}")
        report = generate_directory_report(
            source_dir, output_file
        )  # Uses default ignore patterns
        print(f"Directory report successfully generated and saved to {output_file}")

        # Print report to console as well
        print("\n--- Report Start ---")
        print("\n".join(report))
        print("--- Report End ---")
    except Exception as e:
        print(f"Error generating directory report: {e}")


if __name__ == "__main__":
    main()

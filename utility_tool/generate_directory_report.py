import argparse
import os
from pathlib import Path


def generate_directory_report(source_dir, output_file):
    """
    Generate a structured directory report similar to the tree command

    Args:
        source_dir (str): Source directory path
        output_file (str): Output file path for the report
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
        items = sorted(os.listdir(directory))
        dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
        files = [
            item for item in items if os.path.isfile(os.path.join(directory, item))
        ]

        # Process directories first
        for i, dir_name in enumerate(dirs):
            is_last_dir = i == len(dirs) - 1 and len(files) == 0

            # Add directory to report
            dir_prefix = "└── " if is_last_dir else "├── "
            report.append(f"{prefix}{dir_prefix}{dir_name}/")

            # Process subdirectory
            next_prefix = prefix + ("    " if is_last_dir else "│   ")
            process_directory(os.path.join(directory, dir_name), next_prefix)

        # Then process files
        for i, file_name in enumerate(files):
            is_last_file = i == len(files) - 1

            # Add file to report
            file_prefix = "└── " if is_last_file else "├── "
            report.append(f"{prefix}{file_prefix}{file_name}")

    # Start processing from the source directory
    process_directory(source_dir)

    # Write report to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

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
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            print(f"Error creating output directory: {e}")
            return

    # Generate and save the report
    try:
        report = generate_directory_report(source_dir, output_file)
        print(f"Directory report successfully generated and saved to {output_file}")

        # Print report to console as well
        print("\n" + "\n".join(report))
    except Exception as e:
        print(f"Error generating directory report: {e}")


if __name__ == "__main__":
    main()

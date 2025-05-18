import fnmatch  # For pattern matching
import os
import zipfile


def get_user_inputs():
    """
    Prompts the user for the root folder of the application,
    the target location for the zip file, and the desired zip file name.

    Returns:
        tuple: (root_dir, target_dir, zip_name)
    """
    while True:
        root_dir = input(
            "Enter the absolute path to the root folder of your Python application: "
        )
        if os.path.isdir(root_dir):
            break
        else:
            print(
                f"Error: The path '{root_dir}' is not a valid directory. Please try again."
            )

    while True:
        target_dir = input(
            "Enter the absolute path to the folder where you want to save the zip file: "
        )
        if os.path.isdir(target_dir):
            break
        else:
            print(
                f"Error: The path '{target_dir}' is not a valid directory. Please try again."
            )

    zip_name = input(
        "Enter the desired name for the zip file (e.g., my_application.zip): "
    )
    if not zip_name.endswith(".zip"):
        zip_name += ".zip"

    return root_dir, target_dir, zip_name


def should_ignore(path, ignore_patterns):
    """
    Checks if the given path (or any part of it) matches any of the ignore patterns.

    Args:
        path (str): The path to check (can be a file or directory).
        ignore_patterns (list): A list of patterns to ignore (e.g., "__pycache__", "*.pyc").

    Returns:
        bool: True if the path should be ignored, False otherwise.
    """
    # Normalize path separators for consistent matching
    normalized_path = path.replace("\\", "/")
    path_parts = normalized_path.split("/")

    for pattern in ignore_patterns:
        # Check if any part of the path matches the pattern (for directory names)
        if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
            return True
        # Check if the full path basename matches the pattern (for file names/extensions)
        if fnmatch.fnmatch(os.path.basename(normalized_path), pattern):
            return True
    return False


def zip_application(root_dir, target_zip_path, ignore_patterns):
    """
    Zips the contents of the root_dir into target_zip_path, excluding
    items matching ignore_patterns.

    Args:
        root_dir (str): The root directory of the application to zip.
        target_zip_path (str): The full path for the output zip file.
        ignore_patterns (list): A list of patterns to ignore.
    """
    try:
        with zipfile.ZipFile(target_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Store the original directory to restore it later
            original_cwd = os.getcwd()
            # Change current working directory to the parent of root_dir
            # This helps in creating a cleaner structure within the zip file
            parent_dir = os.path.dirname(root_dir)
            app_folder_name = os.path.basename(root_dir)

            if parent_dir:  # If root_dir is not the root of the filesystem
                os.chdir(parent_dir)
                # The path to walk is now just the app_folder_name
                walk_path = app_folder_name
            else:  # If root_dir is something like "C:\"
                walk_path = root_dir

            print(f"\nStarting to zip '{root_dir}' into '{target_zip_path}'...")
            print(f"Ignoring patterns: {', '.join(ignore_patterns)}\n")

            items_added = 0
            items_ignored = 0

            for foldername, subfolders, filenames in os.walk(walk_path, topdown=True):
                # --- Filter subfolders ---
                # We modify subfolders in-place to prevent os.walk from traversing them
                # Create a copy for iteration as we are modifying the original list
                original_subfolders = list(subfolders)
                subfolders[:] = []  # Clear the original list

                for subfolder in original_subfolders:
                    subfolder_path_for_check = os.path.join(foldername, subfolder)
                    if not should_ignore(subfolder_path_for_check, ignore_patterns):
                        subfolders.append(subfolder)  # Add back if not ignored
                        # print(f"  Processing directory: {subfolder_path_for_check}")
                    else:
                        print(f"  Ignoring directory: {subfolder_path_for_check}")
                        items_ignored += 1

                # --- Process and add files ---
                for filename in filenames:
                    file_path_absolute = os.path.join(
                        original_cwd,
                        parent_dir if parent_dir else "",
                        foldername,
                        filename,
                    )
                    file_path_relative_to_walk_root = os.path.join(foldername, filename)

                    if not should_ignore(
                        file_path_relative_to_walk_root, ignore_patterns
                    ):
                        # The arcname is the path as it will appear inside the zip file.
                        # We want it to be relative to the `walk_path` (the application's root folder).
                        zipf.write(
                            file_path_relative_to_walk_root,
                            arcname=file_path_relative_to_walk_root,
                        )
                        print(f"  Adding file: {file_path_relative_to_walk_root}")
                        items_added += 1
                    else:
                        print(f"  Ignoring file: {file_path_relative_to_walk_root}")
                        items_ignored += 1

            # Restore the original working directory
            os.chdir(original_cwd)

        print(f"\nSuccessfully created zip file: {target_zip_path}")
        print(f"Items added: {items_added}")
        print(f"Items ignored: {items_ignored}")

    except FileNotFoundError:
        print(f"Error: The directory '{root_dir}' was not found.")
    except PermissionError:
        print(f"Error: Permission denied. Could not write to '{target_zip_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure CWD is restored even if an error occurs
        if "original_cwd" in locals() and os.getcwd() != original_cwd:
            os.chdir(original_cwd)


if __name__ == "__main__":
    # Define patterns to ignore
    # These patterns will match directory names or file names/extensions
    DEFAULT_IGNORE_PATTERNS = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".DS_Store",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "build/",  # Trailing slash to indicate directory
        "dist/",
        "*.egg-info/",
        "venv/",
        ".venv/",
        "env/",
        ".env",  # Specific file
        "*.log",
        "local_settings.py",  # Example of a specific config file often ignored
        ".git/",
        ".vscode/",
        "node_modules/",  # If you have JS components
    ]

    print("Python Application Zipper")
    print("--------------------------")

    root_directory, target_save_directory, zip_file_name = get_user_inputs()
    full_target_zip_path = os.path.join(target_save_directory, zip_file_name)

    # You can customize ignore_patterns here if needed, or ask the user
    # For example:
    # custom_ignore_str = input(f"Default ignore patterns: {DEFAULT_IGNORE_PATTERNS}. Add more comma-separated patterns or press Enter: ")
    # if custom_ignore_str:
    #     DEFAULT_IGNORE_PATTERNS.extend([p.strip() for p in custom_ignore_str.split(',')])

    zip_application(root_directory, full_target_zip_path, DEFAULT_IGNORE_PATTERNS)

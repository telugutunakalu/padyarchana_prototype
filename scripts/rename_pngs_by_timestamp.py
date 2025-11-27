#!/usr/bin/env python3
"""
Rename PNG files in a folder based on creation timestamp.
Files are renamed to 1.png, 2.png, ..., n.png where 1.png is the oldest file.
"""

import os
import sys
import argparse
from pathlib import Path


def get_creation_time(file_path: Path) -> float:
    """Get file creation time, falling back to modification time if not available."""
    stat = file_path.stat()
    # Try to get birth time (creation time), fall back to mtime
    try:
        return stat.st_birthtime
    except AttributeError:
        # Linux doesn't have st_birthtime, use st_mtime
        return stat.st_mtime


def rename_pngs_by_timestamp(folder: str, dry_run: bool = False) -> None:
    """Rename all PNG files in folder to sequential numbers based on timestamp."""
    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"Error: Folder '{folder}' does not exist.")
        sys.exit(1)

    if not folder_path.is_dir():
        print(f"Error: '{folder}' is not a directory.")
        sys.exit(1)

    # Get all PNG files
    png_files = list(folder_path.glob("*.png"))

    if not png_files:
        print(f"No PNG files found in '{folder}'.")
        return

    # Sort by creation/modification time (oldest first)
    png_files.sort(key=get_creation_time)

    print(f"Found {len(png_files)} PNG files.")

    # First pass: rename to temporary names to avoid conflicts
    temp_names = []
    for i, file_path in enumerate(png_files, start=1):
        temp_name = folder_path / f"__temp_rename_{i}__.png"
        temp_names.append((temp_name, folder_path / f"{i}.png", file_path.name))
        if not dry_run:
            file_path.rename(temp_name)

    # Second pass: rename to final names
    for temp_name, final_name, original_name in temp_names:
        if dry_run:
            print(f"  {original_name} -> {final_name.name}")
        else:
            temp_name.rename(final_name)
            print(f"  Renamed: {original_name} -> {final_name.name}")

    print(f"\nSuccessfully renamed {len(png_files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Rename PNG files to sequential numbers based on creation timestamp."
    )
    parser.add_argument(
        "folder",
        help="Path to the folder containing PNG files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming"
    )

    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN - No files will be renamed:\n")

    rename_pngs_by_timestamp(args.folder, args.dry_run)


if __name__ == "__main__":
    main()

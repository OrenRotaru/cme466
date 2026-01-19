#!/usr/bin/env python3
"""
Cross-platform script to find and delete .venv directories.
Works on Windows, macOS, and Linux.
"""

import os
import shutil
import sys
from pathlib import Path


def find_venvs(root_dir: Path) -> list[Path]:
    """Find all .venv directories under root_dir."""
    venvs = []
    for dirpath, dirnames, _ in os.walk(root_dir):
        if ".venv" in dirnames:
            venvs.append(Path(dirpath) / ".venv")
            dirnames.remove(".venv")  # Don't descend into .venv
    return venvs


def get_dir_size(path: Path) -> int:
    """Get total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except (PermissionError, OSError):
        pass
    return total


def format_size(size_bytes: float) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    root = Path.cwd()
    print(f"Scanning for .venv directories in: {root}\n")

    venvs = find_venvs(root)

    if not venvs:
        print("No .venv directories found.")
        return

    # Calculate sizes and display
    total_size = 0
    print("Found .venv directories:")
    print("-" * 60)
    for venv in venvs:
        size = get_dir_size(venv)
        total_size += size
        relative = venv.relative_to(root)
        print(f"  {relative}  ({format_size(size)})")

    print("-" * 60)
    print(f"Total: {len(venvs)} directories, {format_size(total_size)}\n")

    # Confirm deletion
    if "--yes" in sys.argv or "-y" in sys.argv:
        confirm = "y"
    else:
        confirm = input("Delete all these directories? [y/N]: ").strip().lower()

    if confirm != "y":
        print("Aborted.")
        return

    # Delete directories
    deleted = 0
    for venv in venvs:
        try:
            print(f"Deleting {venv.relative_to(root)}...", end=" ")
            shutil.rmtree(venv)
            print("done")
            deleted += 1
        except Exception as e:
            print(f"failed: {e}")

    print(f"\nDeleted {deleted}/{len(venvs)} directories.")


if __name__ == "__main__":
    main()

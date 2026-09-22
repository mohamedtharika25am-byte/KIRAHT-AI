"""
KIRAHT AI - File System & Developer Engine
Provides file inspections (size, lines, modified time), direct opening in editors,
directory exploration, and safe code reading/editing for KIRAHT AI.
"""

import os
import datetime
import shutil
import subprocess

WORKSPACE_DIR = r"d:\KIRAHT AI"


def resolve_path(target_path: str) -> str:
    """
    Resolves relative path against workspace directory, or returns absolute path if provided.
    """
    clean_path = target_path.strip().strip('"').strip("'")
    if os.path.isabs(clean_path):
        return clean_path
    return os.path.abspath(os.path.join(WORKSPACE_DIR, clean_path))


def format_size(size_bytes: int) -> str:
    """
    Formats byte size into readable string (Bytes, KB, MB).
    """
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_file_info(filepath: str, call_me: str = "Sir") -> str:
    """
    Returns file size, total lines count, and last modified date.
    """
    full_path = resolve_path(filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, the file '{os.path.basename(filepath)}' was not found in the workspace."

    if os.path.isdir(full_path):
        return get_folder_info(full_path, call_me)

    try:
        stat = os.stat(full_path)
        size_str = format_size(stat.st_size)
        mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        line_count = 0
        is_text = True
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                line_count = sum(1 for _ in f)
        except Exception:
            is_text = False

        base_name = os.path.basename(full_path)
        lines_info = f" with {line_count:,} lines" if is_text else ""
        return (
            f"{call_me}, '{base_name}' is {size_str}{lines_info}.\n"
            f"  - Location: {full_path}\n"
            f"  - Last Modified: {mod_time}"
        )
    except Exception as err:
        return f"{call_me}, failed to inspect '{filepath}': {err}"


def get_folder_info(folder_path: str, call_me: str = "Sir") -> str:
    """
    Returns total size and file count of a directory.
    """
    total_size = 0
    total_files = 0
    for root, _, files in os.walk(folder_path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
                total_files += 1
            except Exception:
                continue

    size_str = format_size(total_size)
    base_name = os.path.basename(folder_path.rstrip("/\\")) or folder_path
    return f"{call_me}, folder '{base_name}' contains {total_files} files ({size_str})."


def open_file_in_editor(filepath: str, call_me: str = "Sir") -> str:
    """
    Opens target file directly in VS Code if available, or system default editor.
    """
    full_path = resolve_path(filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, file '{filepath}' does not exist."

    base_name = os.path.basename(full_path)

    # Try opening in VS Code first
    try:
        res = subprocess.run(["code", full_path], shell=True, capture_output=True, timeout=3)
        if res.returncode == 0:
            return f"{call_me}, opened '{base_name}' in Visual Studio Code."
    except Exception:
        pass

    # Fallback to default Windows program
    try:
        os.startfile(full_path)
        return f"{call_me}, opened '{base_name}' in default editor."
    except Exception as err:
        return f"{call_me}, could not open '{base_name}': {err}"


def list_workspace_files(folder_path: str = WORKSPACE_DIR, call_me: str = "Sir") -> str:
    """
    Lists files in the workspace with sizes and extensions.
    """
    target = resolve_path(folder_path)
    if not os.path.exists(target) or not os.path.isdir(target):
        return f"{call_me}, directory '{folder_path}' not found."

    try:
        entries = os.listdir(target)
        files = []
        folders = []

        for entry in entries:
            # Skip git and cache internals for clean view
            if entry in (".git", "__pycache__", ".vscode"):
                continue

            full = os.path.join(target, entry)
            if os.path.isdir(full):
                folders.append(f"[DIR]  {entry}/")
            else:
                size_str = format_size(os.path.getsize(full))
                files.append(f"[FILE] {entry.ljust(24)} ({size_str})")

        items = []
        if folders:
            items.extend(sorted(folders))
        if files:
            items.extend(sorted(files))

        if not items:
            return f"{call_me}, the directory is empty."

        summary = "\n  ".join(items)
        return f"{call_me}, here are the files in {os.path.basename(target) or target}:\n  {summary}"
    except Exception as err:
        return f"{call_me}, error listing files: {err}"


def read_file_content(filepath: str, max_lines: int = 50, call_me: str = "Sir") -> str:
    """
    Safely reads file content up to max_lines.
    """
    full_path = resolve_path(filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, file '{filepath}' was not found."

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines).rstrip()

        base_name = os.path.basename(full_path)
        preview = f"--- [{base_name}] ---\n{content}\n--- End of preview ---"
        return f"{call_me}, here is the content of '{base_name}':\n\n{preview}"
    except Exception as err:
        return f"{call_me}, failed to read '{filepath}': {err}"


def safe_create_or_modify_file(filepath: str, new_content: str, call_me: str = "Sir") -> str:
    """
    Creates or modifies a file with automatic backup creation if it already exists.
    """
    full_path = resolve_path(filepath)
    base_name = os.path.basename(full_path)

    try:
        if os.path.exists(full_path):
            backup_path = f"{full_path}.bak"
            shutil.copy2(full_path, backup_path)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"{call_me}, successfully saved '{base_name}'. (Backup created at {base_name}.bak)"
    except Exception as err:
        return f"{call_me}, failed to save '{base_name}': {err}"

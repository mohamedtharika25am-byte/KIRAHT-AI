"""
KIRAHT AI - File System & Developer Engine
Provides file inspections (size, lines, modified time), direct opening in editors,
directory exploration, and safe code reading/editing for KIRAHT AI.
"""

import os
import re
import datetime
import shutil
import subprocess

WORKSPACE_DIR = r"d:\KIRAHT AI"


def get_user_known_folders() -> dict:
    """
    Returns verified paths to Workspace, Downloads, Desktop, Documents, Pictures, Videos, Movies, and Music.
    """
    home = os.path.expanduser("~")
    folders = {
        "workspace": WORKSPACE_DIR,
        "kiraht": WORKSPACE_DIR,
        "kiraht ai": WORKSPACE_DIR,
        "kiraht-ai": WORKSPACE_DIR,
        "project": WORKSPACE_DIR,
        "downloads": os.path.join(home, "Downloads"),
        "documents": os.path.join(home, "Documents"),
        "desktop": os.path.join(home, "Desktop"),
        "pictures": os.path.join(home, "Pictures"),
        "screenshots": os.path.join(home, "Pictures", "Screenshots"),
        "videos": os.path.join(home, "Videos"),
        "movies": os.path.join(home, "Videos", "Movies"),
        "music": os.path.join(home, "Music"),
    }
    # Check OneDrive variants
    for candidate in [
        os.path.join(home, "OneDrive - KGISL Institute of Technology", "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
    ]:
        if os.path.exists(candidate):
            folders["desktop"] = candidate
            break

    for candidate in [
        os.path.join(home, "OneDrive - KGISL Institute of Technology", "Documents"),
        os.path.join(home, "OneDrive", "Documents"),
    ]:
        if os.path.exists(candidate):
            folders["documents"] = candidate
            break

    # Discover Movies on root drives or home
    for candidate in [
        "D:\\\U0001f3acMovies",
        "D:\\Movies",
        os.path.join(home, "Videos", "\U0001f3acMovies"),
        os.path.join(home, "Videos", "Movies"),
        os.path.join(home, "Movies"),
    ]:
        if os.path.exists(candidate):
            folders["movies"] = candidate
            folders["\U0001f3acmovies"] = candidate
            folders["movie"] = candidate
            break

    # Discover VS Code Extensions folder (~/.vscode/extensions)
    vscode_ext = os.path.join(home, ".vscode", "extensions")
    if os.path.exists(vscode_ext):
        folders["extensions"] = vscode_ext
        folders["extension"] = vscode_ext
        folders["xtensions"] = vscode_ext
        folders["xtension"] = vscode_ext
        folders["vscode extensions"] = vscode_ext
        folders["vs code extensions"] = vscode_ext

    # Discover GitHub folder in Documents or home
    for gh_cand in [
        os.path.join(home, "Documents", "GitHub"),
        os.path.join(home, "GitHub"),
    ]:
        if os.path.exists(gh_cand):
            folders["github"] = gh_cand
            folders["git hub"] = gh_cand
            break

    return folders


LAST_ACCESSED_PATH = WORKSPACE_DIR


def set_last_path(path: str) -> None:
    """
    Tracks the most recently inspected file or folder path for follow-up resolution.
    """
    global LAST_ACCESSED_PATH
    if path and os.path.exists(path):
        LAST_ACCESSED_PATH = os.path.abspath(path)


def get_last_path() -> str:
    """
    Returns the most recently inspected file or folder path.
    """
    global LAST_ACCESSED_PATH
    return LAST_ACCESSED_PATH


def resolve_path(target_path: str) -> str:
    """
    Resolves relative path against workspace, known user folders, or root drives.
    Supports emojis, common typos (foler/folder), pronoun follow-ups ('that folder'), and multi-word names.
    """
    clean_path = target_path.strip().strip('"').strip("'")
    if not clean_path:
        return WORKSPACE_DIR

    lower_p = clean_path.lower().strip()

    # Coreference / pronoun resolution for follow-ups ("that folder", "that", "it", "this")
    if lower_p in ("that", "this", "it", "same", "the folder", "the file", "that folder", "that directory", "that file"):
        last = get_last_path()
        if last and os.path.exists(last):
            return last

    if os.path.isabs(clean_path):
        if os.path.exists(clean_path):
            set_last_path(clean_path)
        return clean_path

    known = get_user_known_folders()

    # Strip trailing "folder" or "foler" or "floder" or "dir" or "directory" or "file"
    lower_clean = re.sub(r"\s+(?:folder|foler|floder|fldr|dir|directory|file)$", "", lower_p).strip()
    if lower_clean in ("that", "this", "it", "same"):
        last = get_last_path()
        if last and os.path.exists(last):
            return last

    if lower_clean in known and os.path.exists(known[lower_clean]):
        cand = known[lower_clean]
        set_last_path(cand)
        return cand
    if lower_p in known and os.path.exists(known[lower_p]):
        cand = known[lower_p]
        set_last_path(cand)
        return cand

    # Normalized alphanumeric matching (handles emojis like 🎬movies -> movies)
    norm_target = re.sub(r"[^a-zA-Z0-9_\-]", "", lower_clean).strip().lower()
    if norm_target:
        for k, v in known.items():
            norm_k = re.sub(r"[^a-zA-Z0-9_\-]", "", k).strip().lower()
            if norm_k == norm_target and os.path.exists(v):
                return v

    # Prefix checks (e.g. "downloads/resume.pdf" or "desktop/file.txt")
    for key in ("downloads", "desktop", "documents", "workspace", "videos", "pictures", "movies", "music"):
        if key in known:
            if lower_p.startswith(f"{key}/") or lower_p.startswith(f"{key}\\"):
                rel = clean_path[len(key) + 1:]
                return os.path.join(known[key], rel)

    # 1. Try workspace first
    ws_candidate = os.path.abspath(os.path.join(WORKSPACE_DIR, clean_path))
    if os.path.exists(ws_candidate):
        return ws_candidate

    ws_clean_cand = os.path.abspath(os.path.join(WORKSPACE_DIR, lower_clean))
    if os.path.exists(ws_clean_cand):
        return ws_clean_cand

    # 2. Search root directories, user home, and known folders
    home = os.path.expanduser("~")
    search_roots = [
        WORKSPACE_DIR,
        "D:\\",
        home,
        known.get("downloads", ""),
        known.get("desktop", ""),
        known.get("documents", ""),
        known.get("videos", ""),
        known.get("pictures", ""),
    ]
    for root in search_roots:
        if not root or not os.path.exists(root):
            continue
        cand = os.path.join(root, clean_path)
        if os.path.exists(cand):
            return cand
        cand_clean = os.path.join(root, lower_clean)
        if os.path.exists(cand_clean):
            return cand_clean

        # Entry-level matching inside root (case-insensitive and emoji-tolerant)
        try:
            for entry in os.listdir(root):
                if entry.lower() in (lower_clean, lower_p):
                    return os.path.join(root, entry)
                norm_e = re.sub(r"[^a-zA-Z0-9_\-]", "", entry).strip().lower()
                if norm_target and norm_e == norm_target:
                    return os.path.join(root, entry)
        except Exception:
            pass

    return ws_candidate


def format_size(size_bytes: int) -> str:
    """
    Formats byte size into readable string (Bytes, KB, MB, GB).
    """
    if size_bytes < 1024:
        return f"{size_bytes} Bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_file_info(filepath: str, call_me: str = "Sir") -> str:
    """
    Returns file or folder size, total lines/files count, and last modified date.
    """
    full_path = resolve_path(filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, could not find '{os.path.basename(filepath)}' in your workspace, user folders, or drives."

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
    Returns total size, file count, and location of a directory.
    """
    full_path = resolve_path(folder_path)
    if not os.path.exists(full_path):
        return f"{call_me}, folder '{folder_path}' was not found on your system."

    set_last_path(full_path)
    total_size = 0
    total_files = 0
    for root, _, files in os.walk(full_path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_size += os.path.getsize(fp)
                total_files += 1
            except Exception:
                continue

    size_str = format_size(total_size)
    base_name = os.path.basename(full_path.rstrip("/\\")) or full_path
    return f"{call_me}, folder '{base_name}' contains {total_files} files ({size_str}) at '{full_path}'."


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


def open_system_item(filepath: str, call_me: str = "Sir") -> str:
    """
    Opens any file or folder using its native application (VS Code for code/text, Explorer for folders, default player for media).
    """
    full_path = resolve_path(filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, could not find '{os.path.basename(filepath)}' on your system."

    if os.path.isdir(full_path):
        try:
            os.startfile(full_path)
            return f"{call_me}, opened folder: {full_path}."
        except Exception as err:
            return f"{call_me}, could not open folder '{full_path}': {err}"

    base_name = os.path.basename(full_path)
    code_exts = (".py", ".json", ".txt", ".md", ".env", ".csv", ".log", ".html", ".js", ".css", ".bat", ".sh", ".c", ".cpp", ".java", ".xml", ".yaml", ".yml")
    if any(base_name.lower().endswith(ext) for ext in code_exts):
        return open_file_in_editor(full_path, call_me=call_me)

    try:
        os.startfile(full_path)
        return f"{call_me}, opened '{base_name}'."
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
    Ensures parent directories are created automatically so saving into any folder works.
    """
    full_path = resolve_path(filepath)
    base_name = os.path.basename(full_path)

    try:
        parent_dir = os.path.dirname(full_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        if os.path.isdir(full_path):
            return f"{call_me}, '{base_name}' is a directory, not a file. File write skipped."

        if os.path.exists(full_path):
            backup_path = f"{full_path}.bak"
            try:
                shutil.copy2(full_path, backup_path)
            except Exception:
                pass

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        set_last_path(full_path)
        return f"{call_me}, successfully saved '{base_name}' to {full_path}."
    except Exception as err:
        return f"{call_me}, failed to save '{base_name}': {err}"


def create_folder(folder_name_or_path: str, parent_folder: str = None, call_me: str = "Sir") -> str:
    """
    Creates a new directory on disk.
    Supports relative names, parent resolution, pronoun follow-ups ('in that', 'in this'),
    and automatically cleans up any accidentally created dummy zero/small files with the same name.
    """
    clean_target = folder_name_or_path.strip().strip("'\"")
    clean_target = re.sub(r"^(?:named|called)\s+", "", clean_target, flags=re.IGNORECASE).strip()
    clean_target = re.sub(r"\s+folder$", "", clean_target, flags=re.IGNORECASE).strip()

    # Determine base directory
    if os.path.isabs(clean_target):
        target_dir = clean_target
    elif parent_folder:
        p_clean = parent_folder.strip().strip("'\"")
        p_clean = re.sub(r"^(?:in|into|inside)\s+", "", p_clean, flags=re.IGNORECASE).strip()
        parent_dir = resolve_path(p_clean)
        target_dir = os.path.abspath(os.path.join(parent_dir, clean_target))
    else:
        # Check if the last accessed path is an existing directory other than root workspace
        last = get_last_path()
        if last and os.path.isdir(last) and last != WORKSPACE_DIR:
            target_dir = os.path.abspath(os.path.join(last, clean_target))
        else:
            target_dir = os.path.abspath(os.path.join(WORKSPACE_DIR, clean_target))

    folder_name = os.path.basename(target_dir)

    try:
        # If a file already exists at this path (e.g. dummy script created previously)
        if os.path.isfile(target_dir):
            try:
                os.remove(target_dir)
            except Exception as r_err:
                return f"{call_me}, a file named '{folder_name}' already exists at {target_dir} and could not be replaced: {r_err}"

        os.makedirs(target_dir, exist_ok=True)
        set_last_path(target_dir)
        return f"{call_me}, folder '{folder_name}' has been created successfully at '{target_dir}'."
    except Exception as err:
        return f"{call_me}, failed to create folder '{folder_name}': {err}"


def search_files_across_folders(query: str, target_location: str = "all", max_results: int = 8, call_me: str = "Sir") -> str:
    """
    Searches for files matching query across Workspace, Downloads, Desktop, and Documents.
    """
    known = get_user_known_folders()
    query_clean = query.strip().lower()
    if not query_clean:
        return f"{call_me}, please specify a filename or keyword to search for."

    search_dirs = []
    loc_lower = target_location.lower().strip()
    if loc_lower in known:
        search_dirs.append((loc_lower.title(), known[loc_lower]))
    else:
        search_dirs = [
            ("Workspace", known["workspace"]),
            ("Downloads", known["downloads"]),
            ("Desktop", known["desktop"]),
            ("Documents", known["documents"]),
        ]

    matches = []
    for label, dir_path in search_dirs:
        if not os.path.exists(dir_path):
            continue
        try:
            # Shallow search + 1 level deep to avoid slow deep recursion
            for root, dirs, files in os.walk(dir_path):
                # Don't recurse deep into node_modules, .git, etc.
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv")]
                rel_depth = root[len(dir_path):].count(os.sep)
                if rel_depth > 1:
                    continue

                for f in files:
                    if f.startswith("."):
                        continue
                    if query_clean in f.lower():
                        fp = os.path.join(root, f)
                        try:
                            sz = format_size(os.path.getsize(fp))
                        except Exception:
                            sz = "unknown size"
                        matches.append((label, f, sz, fp))
                        if len(matches) >= max_results:
                            break
                if len(matches) >= max_results:
                    break
        except Exception:
            continue

    if not matches:
        return f"{call_me}, no files matching '{query}' were found in your {target_location} folders."

    lines = [f"{call_me}, found {len(matches)} matching file(s):"]
    for label, fname, sz, fullpath in matches:
        lines.append(f"  • [{label}] {fname} ({sz})\n    Path: {fullpath}")
    return "\n".join(lines)


def safe_delete_file(filepath: str, call_me: str = "Sir") -> str:
    """
    Safely deletes a file after saving a timestamped backup in .kiraht_trash/.
    """
    full_path = resolve_path(filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, file '{filepath}' does not exist."
    if os.path.isdir(full_path):
        return f"{call_me}, '{filepath}' is a directory. Folder deletion is restricted for safety."

    base_name = os.path.basename(full_path)
    try:
        bak_dir = os.path.join(WORKSPACE_DIR, ".kiraht_trash")
        os.makedirs(bak_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_path = os.path.join(bak_dir, f"{base_name}_{timestamp}.bak")
        shutil.copy2(full_path, bak_path)

        shutil.remove = os.remove
        os.remove(full_path)
        return f"{call_me}, successfully deleted '{base_name}'. (Safety backup saved in .kiraht_trash/)"
    except Exception as err:
        return f"{call_me}, failed to delete '{base_name}': {err}"


def safe_delete_folder(folder_path: str, call_me: str = "Sir") -> str:
    """
    Safely deletes a directory after creating a backup copy in .kiraht_trash/.
    Guards against deleting root directories.
    """
    full_path = resolve_path(folder_path)
    if not os.path.exists(full_path):
        return f"{call_me}, folder '{folder_path}' does not exist."
    if not os.path.isdir(full_path):
        return safe_delete_file(folder_path, call_me=call_me)

    norm_ws = os.path.normpath(WORKSPACE_DIR)
    norm_target = os.path.normpath(full_path)
    if norm_target == norm_ws or len(norm_target) <= 3:
        return f"{call_me}, cannot delete the root workspace folder for safety."

    base_name = os.path.basename(full_path) or "folder"
    try:
        bak_dir = os.path.join(WORKSPACE_DIR, ".kiraht_trash")
        os.makedirs(bak_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_path = os.path.join(bak_dir, f"{base_name}_{timestamp}")
        shutil.copytree(full_path, bak_path, dirs_exist_ok=True)

        shutil.rmtree(full_path)
        return f"{call_me}, successfully deleted folder '{base_name}'. (Safety backup saved in .kiraht_trash/)"
    except Exception as err:
        return f"{call_me}, failed to delete folder '{base_name}': {err}"


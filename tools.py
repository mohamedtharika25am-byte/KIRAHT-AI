"""
KIRAHT AI - Tools Engine (Laptop Operations, Desktop Apps & File Management)
Provides local, secure, and instant Windows automation for KIRAHT AI.

Capabilities:
- Dynamic Installed Desktop App Launcher (WhatsApp, ChatGPT, Android Studio, VS Code, Cursor, etc.)
- App Killer / Task Closer (taskkill)
- File Management Engine (File size, open in VS Code, list directory files, read code)
- System Hardware Metrics (Battery, CPU, RAM)
- Audio & Volume Controls (Mute, Volume Up, Volume Down)
- Web & YouTube Direct Search (Opens in default browser)
- Directory Explorer (Downloads, Documents, Desktop, Project Folders)
- Security Controls (Lock Workstation)
"""

import ctypes
import json
import os
import re
import subprocess
import urllib.parse
import webbrowser
import psutil

# Import file operations engine
from file_tools import (
    get_file_info,
    open_file_in_editor,
    list_workspace_files,
    read_file_content,
    safe_create_or_modify_file,
    resolve_path,
)

# Import system tools engine (Clipboard, Terminal, Screenshot, OS controls)
from system_tools import (
    get_clipboard_text,
    set_clipboard_text,
    clear_clipboard,
    run_terminal_command,
    take_screenshot,
    empty_recycle_bin,
    get_wifi_status,
    show_desktop_notification,
)

# Virtual-Key codes for Windows user32 keybd_event
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

WORKSPACE_DIR = r"d:\KIRAHT AI"
APPS_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps_cache.json")

# Nickname aliases for quick matching
APP_ALIASES = {
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "code": "visual studio code",
    "wp": "whatsapp",
    "wa": "whatsapp",
    "gpt": "chatgpt",
    "studio": "android studio",
    "calc": "calculator",
    "browser": "google chrome",
    "chrome": "google chrome",
    "antigravity": "antigravity ide",
    "arduino": "arduino ide",
}

# Fallback Application Launch Commands
APP_COMMANDS = {
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "spotify": "spotify",
    "antigravity": "antigravity",
    "explorer": "explorer",
    "file explorer": "explorer",
    "cmd": "cmd /c start cmd",
    "command prompt": "cmd /c start cmd",
    "powershell": "cmd /c start powershell",
    "terminal": "cmd /c start powershell",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "settings": "start ms-settings:",
}

# Common Process Names for Closing Apps
PROCESS_NAMES = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe"],
    "calc": ["CalculatorApp.exe", "calc.exe"],
    "spotify": ["Spotify.exe"],
    "vscode": ["Code.exe"],
    "vs code": ["Code.exe"],
    "whatsapp": ["WhatsApp.exe"],
    "chatgpt": ["ChatGPT.exe"],
}

# Known Web Destinations (Removed WhatsApp/ChatGPT so they launch locally!)
WEB_SITES = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "linkedin": "https://www.linkedin.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
}


# ============================================================
# 1. INSTALLED DESKTOP APPLICATION SCANNER & LAUNCHER
# ============================================================
def scan_installed_apps() -> dict:
    """
    Scans Windows Start Menu shortcuts (.lnk) and Windows UWP AppIDs (Get-StartApps).
    Caches results into apps_cache.json for instantaneous local lookup.
    """
    apps = {}

    # 1. Start Menu Shortcuts (.lnk)
    folders = [
        os.path.join(os.environ.get("ProgramData", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    ]
    for folder in folders:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4].strip()
                        lower_name = name.lower()
                        if "uninstall" not in lower_name and "help" not in lower_name:
                            apps[lower_name] = {
                                "name": name,
                                "type": "lnk",
                                "target": os.path.join(root, f),
                            }

    # 2. Windows Modern / UWP AppIDs via PowerShell Get-StartApps
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-StartApps | ConvertTo-Json -Compress"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            if isinstance(data, list):
                for item in data:
                    name = item.get("Name", "").strip()
                    appid = item.get("AppID", "").strip()
                    if name and appid:
                        lower = name.lower()
                        apps[lower] = {
                            "name": name,
                            "type": "uwp" if ("!" in appid or "." in appid or "{" in appid) else "lnk",
                            "target": appid,
                        }
    except Exception:
        pass

    try:
        with open(APPS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(apps, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return apps


def load_apps_cache() -> dict:
    """
    Loads apps cache from disk or triggers a scan if not yet cached.
    """
    if os.path.exists(APPS_CACHE_FILE):
        try:
            with open(APPS_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return scan_installed_apps()


def find_installed_app(app_query: str) -> dict | None:
    """
    Resolves user query to an installed Windows desktop application.
    Supports aliases, exact matches, prefix matches, and fuzzy substring matches.
    """
    cache = load_apps_cache()
    clean = app_query.lower().strip()
    clean = APP_ALIASES.get(clean, clean)

    # 1. Exact match
    if clean in cache:
        return cache[clean]

    # 2. Starts with match
    for k, info in cache.items():
        if k.startswith(clean) or clean.startswith(k):
            return info

    # 3. Substring match
    for k, info in cache.items():
        if clean in k:
            return info

    return None


def launch_desktop_app(app_name: str, call_me: str = "Sir") -> tuple[bool, str]:
    """
    Launches a native installed application directly on Windows.
    Prefers local desktop apps over browser tabs.
    """
    clean_name = app_name.lower().strip()
    app_info = find_installed_app(clean_name)

    if app_info:
        display_name = app_info.get("name", clean_name.title())
        target = app_info.get("target", "")
        app_type = app_info.get("type", "lnk")

        try:
            if app_type == "uwp" or (not os.path.exists(target) and "\\" not in target):
                # Shell AppID / Store App
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{target}"])
                return True, f"{call_me}, launching {display_name} desktop app."
            elif os.path.exists(target):
                # Start Menu .lnk or executable path
                os.startfile(target)
                return True, f"{call_me}, launching {display_name}."
            else:
                subprocess.Popen(f"start {target}", shell=True)
                return True, f"{call_me}, launched {display_name}."
        except Exception as err:
            return False, f"{call_me}, failed to launch {display_name}: {err}"

    # Fallback to standard APP_COMMANDS
    cmd = APP_COMMANDS.get(clean_name)
    if cmd:
        try:
            subprocess.Popen(cmd, shell=True)
            return True, f"{call_me}, {clean_name.title()} launched."
        except Exception as err:
            return False, f"{call_me}, failed to open {clean_name}: {err}"

    return False, f"{call_me}, no installed desktop app found for '{app_name}'."


# ============================================================
# 2. SYSTEM HARDWARE METRICS & AUDIO CONTROLS
# ============================================================
def get_system_stats(call_me: str = "Sir") -> str:
    """
    Returns battery percentage, charging state, CPU load, and RAM usage.
    """
    try:
        battery = psutil.sensors_battery()
        battery_text = "Battery info unavailable"
        if battery is not None:
            status = "charging" if battery.power_plugged else "discharging"
            battery_text = f"battery is at {battery.percent}% ({status})"

        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent

        return f"{call_me}, {battery_text}. Current CPU load is {cpu}% and RAM usage is {ram}%."
    except Exception as err:
        return f"{call_me}, unable to fetch system metrics: {err}"


def close_app(app_name: str, call_me: str = "Sir") -> str:
    """
    Terminates a running application by process name using Windows taskkill.
    """
    clean_name = app_name.lower().strip()
    target_procs = PROCESS_NAMES.get(clean_name, [f"{clean_name}.exe"])
    closed_any = False

    for proc in target_procs:
        try:
            res = subprocess.run(
                ["taskkill", "/f", "/im", proc],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                closed_any = True
        except Exception:
            continue

    if closed_any:
        return f"{call_me}, {clean_name.title()} has been closed."
    return f"{call_me}, no active process found for {clean_name.title()}."


def open_web(site_name: str, search_query: str = "", call_me: str = "Sir") -> str:
    """
    Opens web services or performs direct searches on YouTube/Google.
    """
    clean_site = site_name.lower().strip()

    if clean_site == "youtube" and search_query:
        encoded = urllib.parse.quote(search_query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        return f"{call_me}, opened YouTube search for '{search_query}'."

    if clean_site == "google" and search_query:
        encoded = urllib.parse.quote(search_query)
        webbrowser.open(f"https://www.google.com/search?q={encoded}")
        return f"{call_me}, opened Google search for '{search_query}'."

    url = WEB_SITES.get(clean_site)
    if not url:
        url = f"https://{clean_site}.com" if "." not in clean_site else f"https://{clean_site}"

    webbrowser.open(url)
    return f"{call_me}, opening {clean_site.title()} in your browser."


def open_folder(folder_name: str, call_me: str = "Sir") -> str:
    """
    Opens a specific user or workspace folder in Windows File Explorer.
    """
    clean = folder_name.lower().strip()
    home = os.path.expanduser("~")

    folder_map = {
        "downloads": os.path.join(home, "Downloads"),
        "documents": os.path.join(home, "Documents"),
        "pictures": os.path.join(home, "Pictures"),
        "desktop": os.path.join(home, "Desktop"),
        "project": WORKSPACE_DIR,
        "workspace": WORKSPACE_DIR,
        "kiraht": WORKSPACE_DIR,
    }

    target = folder_map.get(clean, folder_name)
    if os.path.exists(target):
        os.startfile(target)
        return f"{call_me}, opened folder: {target}."
    return f"{call_me}, folder '{folder_name}' was not found."


def adjust_volume(action: str, call_me: str = "Sir", steps: int = 5) -> str:
    """
    Controls master volume using Windows user32 keybd_event.
    """
    act = action.lower().strip()
    try:
        if act in ("mute", "unmute", "toggle mute"):
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            return f"{call_me}, volume mute toggled."

        if "up" in act or "increase" in act:
            for _ in range(steps):
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
            return f"{call_me}, volume increased."

        if "down" in act or "decrease" in act:
            for _ in range(steps):
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                ctypes.windll.user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
            return f"{call_me}, volume decreased."

        return f"{call_me}, unrecognized volume command."
    except Exception as err:
        return f"{call_me}, audio adjustment failed: {err}"


def lock_workstation(call_me: str = "Sir") -> str:
    """
    Locks the Windows user session.
    """
    try:
        ctypes.windll.user32.LockWorkStation()
        return f"{call_me}, workstation is now locked."
    except Exception as err:
        return f"{call_me}, unable to lock PC: {err}"


# ============================================================
# 3. UNIFIED COMMAND ROUTER (APPS, FILES & HARDWARE)
# ============================================================
def is_file_target(target: str) -> bool:
    """
    Determines if target string refers to a file (has extension or exists on disk).
    """
    clean = target.strip().strip("'\"")
    known_exts = (".py", ".json", ".txt", ".md", ".env", ".csv", ".log", ".html", ".js", ".css", ".bat", ".sh")
    if any(clean.lower().endswith(ext) for ext in known_exts):
        return True
    return os.path.exists(resolve_path(clean))


def execute_system_command(user_text: str, call_me: str = "Sir") -> tuple[bool, str]:
    """
    Matches user intent against desktop apps, file operations, and hardware automation tools.
    Returns (handled, response_string).
    """
    cleaned = user_text.strip().lower()

    # 1. Rescan Installed Applications Cache
    if cleaned in ("/scan_apps", "scan apps", "rescan apps", "refresh apps"):
        apps = scan_installed_apps()
        return True, f"{call_me}, scanned and indexed {len(apps)} installed desktop applications into apps_cache.json."

    # 2. Battery / Power / System Performance
    if re.search(r"\b(battery|battery status|battery level|battery percentage|charging status)\b", cleaned):
        return True, get_system_stats(call_me)
    if re.search(r"\b(system status|pc status|system metrics|cpu status|ram status|cpu usage|ram usage)\b", cleaned):
        return True, get_system_stats(call_me)

    # 3. Lock Workstation
    if re.search(r"\b(lock pc|lock screen|lock workstation|lock computer)\b", cleaned):
        return True, lock_workstation(call_me)

    # 4. Audio & Volume
    if re.search(r"\b(mute volume|unmute volume|mute pc|unmute pc|mute|unmute)\b", cleaned):
        return True, adjust_volume("mute", call_me)
    if re.search(r"\b(volume up|increase volume|volume increase|louder)\b", cleaned):
        return True, adjust_volume("up", call_me)
    if re.search(r"\b(volume down|decrease volume|volume decrease|lower volume)\b", cleaned):
        return True, adjust_volume("down", call_me)

    # 5. Clipboard Operations
    if re.search(r"^(?:please\s+)?(?:read|check|view|show|what is in my|what's in my)\s+clipboard\b", cleaned) or cleaned in ("clipboard", "/clipboard"):
        return True, get_clipboard_text(call_me)
    if re.search(r"\b(clear clipboard|empty clipboard)\b", cleaned):
        return True, clear_clipboard(call_me)
    copy_match = re.search(r"^(?:please\s+)?copy\s+(?:to\s+clipboard\s+)?(.+)$", user_text.strip(), re.IGNORECASE)
    if copy_match and not cleaned.startswith("copy file"):
        text_to_copy = copy_match.group(1).strip()
        return True, set_clipboard_text(text_to_copy, call_me)

    # 6. Screen Capture / Screenshot
    if re.search(r"\b(take screenshot|screenshot|capture screen|screen capture)\b", cleaned):
        return True, take_screenshot(call_me)

    # 7. Wi-Fi & Network Status
    if re.search(r"\b(wifi|wi-fi|wifi status|wi-fi status|check wifi|network status|internet connection status)\b", cleaned):
        return True, get_wifi_status(call_me)

    # 8. Empty Recycle Bin
    if re.search(r"\b(empty recycle bin|clean recycle bin|clear recycle bin|empty trash)\b", cleaned):
        return True, empty_recycle_bin(call_me)

    # 9. Direct Terminal / Developer Execution (Safe runner)
    run_cmd_match = re.search(r"^(?:run|exec|execute|terminal|cmd)\s+(.+)$", user_text.strip(), re.IGNORECASE)
    if run_cmd_match:
        cmd = run_cmd_match.group(1).strip()
        return True, run_terminal_command(cmd, call_me)
    if re.search(r"^git\s+(status|diff|branch|log|pull|commit|push)\b", cleaned):
        return True, run_terminal_command(user_text.strip(), call_me)
    if re.search(r"^pip\s+(list|show|check)\b", cleaned):
        return True, run_terminal_command(user_text.strip(), call_me)

    # 10. Desktop Notifications & Reminders
    notify_match = re.search(r"^(?:notify|send notification|remind me to)\s+(.+)$", user_text.strip(), re.IGNORECASE)
    if notify_match:
        reminder_msg = notify_match.group(1).strip()
        return True, show_desktop_notification("KIRAHT AI", reminder_msg, call_me)

    # 5. File Size / File Info Operations
    size_match = (
        re.search(r"\b(?:size of|file size of|info of|details of)\s+([a-zA-Z0-9_\-\./\\]+)\b", cleaned)
        or re.search(r"^([a-zA-Z0-9_\-\./\\]+)\s+(?:size|file size)\b", cleaned)
        or re.search(r"^([a-zA-Z0-9_\-\./\\]+)\s+size\s+enna\b", cleaned)
    )
    if size_match:
        target_file = size_match.group(1).strip()
        return True, get_file_info(target_file, call_me)

    # 6. List Workspace / Project Files
    if re.search(r"\b(list files|show files|files in project|project files|directory files|dir files|all files)\b", cleaned):
        return True, list_workspace_files(WORKSPACE_DIR, call_me)

    # 7. Read File Content
    read_match = re.search(r"^(?:please\s+)?(?:read|view|show content of|display code of|show code of)\s+([a-zA-Z0-9_\-\./\\]+)\b", cleaned)
    if read_match:
        target_file = read_match.group(1).strip()
        return True, read_file_content(target_file, max_lines=60, call_me=call_me)

    # 8. YouTube Search with Query
    yt_match = (
        re.search(r"^(?:open\s+)?youtube\s+(?:and\s+)?search\s+(.+)$", cleaned)
        or re.search(r"^search\s+(.+)\s+(?:on|in)\s+youtube$", cleaned)
    )
    if yt_match:
        query = yt_match.group(1).strip()
        return True, open_web("youtube", search_query=query, call_me=call_me)

    # 9. Google Search with Query
    google_match = (
        re.search(r"^(?:open\s+)?google\s+(?:and\s+)?search\s+(.+)$", cleaned)
        or re.search(r"^search\s+(.+)\s+(?:on|in)\s+google$", cleaned)
    )
    if google_match:
        query = google_match.group(1).strip()
        return True, open_web("google", search_query=query, call_me=call_me)

    # 10. Open Web Destinations (Only purely web services like YouTube, GitHub, Gmail)
    web_match = re.search(r"^(?:please\s+)?(?:open|go to|launch)\s+(youtube|github|gmail|linkedin|twitter)\b", cleaned)
    if web_match:
        site = web_match.group(1).strip()
        return True, open_web(site, call_me=call_me)

    # 11. Open Folders
    folder_match = re.search(
        r"^(?:please\s+)?open\s+(downloads|documents|pictures|desktop|project|workspace|kiraht)(?:\s+folder)?\b",
        cleaned,
    )
    if folder_match:
        target_folder = folder_match.group(1).strip()
        return True, open_folder(target_folder, call_me=call_me)

    # 12. Close Application
    close_match = re.search(r"^(?:please\s+)?(?:close|kill|quit|terminate)\s+([a-zA-Z0-9\s]+)\b", cleaned)
    if close_match:
        app_to_close = close_match.group(1).strip()
        return True, close_app(app_to_close, call_me=call_me)

    # 13. Open File in Editor (e.g. "open main.py", "open file memory.json")
    open_file_match = re.search(r"^(?:please\s+)?open\s+(?:file\s+)?([a-zA-Z0-9_\-\./\\]+)\b", cleaned)
    if open_file_match:
        target_item = open_file_match.group(1).strip()
        if is_file_target(target_item):
            return True, open_file_in_editor(target_item, call_me)

    # 14. Open Desktop Application (Native Laptop App First!)
    open_app_match = re.search(r"^(?:please\s+)?(?:open|launch|start|run)\s+([a-zA-Z0-9\s]+)\b", cleaned)
    if open_app_match:
        app_to_open = open_app_match.group(1).strip()
        # Ensure it's not a folder or file intent
        if app_to_open not in ("folder", "file") and not is_file_target(app_to_open):
            launched, msg = launch_desktop_app(app_to_open, call_me=call_me)
            if launched:
                return True, msg

    return False, ""

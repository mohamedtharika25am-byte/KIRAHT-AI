"""
KIRAHT AI - Tools Engine (Laptop Operations, Desktop Apps, Precision Audio & System Automation)
Provides local, secure, and instant Windows automation for KIRAHT AI.

Capabilities:
- Dynamic Installed Desktop App Launcher with Typo Tolerance & Browser Fallback (WhatsApp, ChatGPT, Android Studio, etc.)
- App Killer / Task Closer (taskkill)
- File Management Engine (File size, open in VS Code, list directory files, read code)
- Precision Windows Master Volume Control (Set exact %, ±10% defaults, custom delta, mute)
- Native Bulletproof Screen Capture (ctypes GDI + PIL)
- System Hardware Metrics (Battery, CPU, RAM) with Low-Battery Guardian
- Current Date & Time Engine
- Network Ping & Latency Diagnostics
- Quick Notes Notepad System
- Audio & Volume Controls
- Web & YouTube Direct Search (Opens in default browser)
- Directory Explorer (Downloads, Documents, Desktop, Project Folders)
- Security Controls (Lock Workstation)
"""

import ctypes
import datetime
import difflib
import json
import os
import re
import subprocess
import urllib.parse
import webbrowser
import psutil
import time

# Import file operations engine
from file_tools import (
    get_file_info,
    open_file_in_editor,
    list_workspace_files,
    read_file_content,
    safe_create_or_modify_file,
    resolve_path,
    search_files_across_folders,
)

# Import system tools engine (Clipboard, Terminal, Screenshot, Volume, Notes, OS controls)
from system_tools import (
    get_clipboard_text,
    set_clipboard_text,
    clear_clipboard,
    run_terminal_command,
    take_screenshot,
    empty_recycle_bin,
    get_wifi_status,
    check_ping,
    show_desktop_notification,
    get_current_volume,
    set_volume_level,
    adjust_volume_delta,
    toggle_mute,
    toggle_mic_mute,
    adjust_volume,
    sleep_laptop,
    shutdown_laptop,
    restart_laptop,
    cancel_shutdown,
    hibernate_laptop,
    turn_off_display,
    get_running_processes,
    get_screen_brightness,
    set_screen_brightness,
    adjust_screen_brightness,
    add_note,
    get_notes,
    clear_notes,
    add_contact,
    add_contact_alias,
    add_group,
    list_contacts,
    import_google_contacts_csv,
    resolve_contact,
    resolve_group,
    send_whatsapp_message,
)

# Virtual-Key codes for Windows user32 keybd_event fallback
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

WORKSPACE_DIR = r"d:\KIRAHT AI"
APPS_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps_cache.json")

# Nickname & common typo aliases for instant matching
APP_ALIASES = {
    # 1. VS Code / Code Editors
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "vsc": "visual studio code",
    "code": "visual studio code",
    "vscod": "visual studio code",
    "vs": "visual studio code",
    "visual code": "visual studio code",
    "visual studio": "visual studio code",
    "visual std": "visual studio code",
    "vstudio": "visual studio code",
    "vs code editor": "visual studio code",
    "code editor": "visual studio code",

    # 2. WhatsApp
    "whatsapp": "whatsapp",
    "whatsap": "whatsapp",
    "whatapp": "whatsapp",
    "whatsappp": "whatsapp",
    "whatssap": "whatsapp",
    "watapp": "whatsapp",
    "whtsapp": "whatsapp",
    "whtsap": "whatsapp",
    "whtsp": "whatsapp",
    "watsapp": "whatsapp",
    "watsp": "whatsapp",
    "wp": "whatsapp",
    "wa": "whatsapp",
    "whats app": "whatsapp",
    "whapp" : "whatsapp",
    "whasap" : "whatsapp",

    # 3. ChatGPT & AI Tools
    "chatgpt": "chatgpt",
    "chatgbt": "chatgpt",
    "chat gpt": "chatgpt",
    "chat-gpt": "chatgpt",
    "chagpt": "chatgpt",
    "cha gpt": "chatgpt",
    "chatg": "chatgpt",
    "gpt": "chatgpt",
    "gpt4": "chatgpt",
    "openai": "chatgpt",
    "open ai": "chatgpt",
    "chat gbt": "chatgpt",
    "chat gpt 4": "chatgpt",
    "copilot": "microsoft 365 copilot",
    "ms copilot": "microsoft 365 copilot",
    "365 copilot": "microsoft 365 copilot",
    "ai copilot": "microsoft 365 copilot",
    "ollama": "ollama",
    "olama": "ollama",

    # 4. IDEs & Developer Environments
    "studio": "android studio",
    "android studio": "android studio",
    "androidstudio": "android studio",
    "as": "android studio",
    "adt": "android studio",
    "android ide": "android studio",
    "arduino": "arduino ide",
    "arduino ide": "arduino ide",
    "arduinoid": "arduino ide",
    "arduin": "arduino ide",
    "cursor": "cursor",
    "cursor ai": "cursor",
    "cursor ide": "cursor",
    "antigravity": "antigravity ide",
    "antigravity ide": "antigravity ide",
    "agy": "antigravity ide",
    "agy ide": "antigravity ide",

    # 5. Web Browsers
    "chrome": "google chrome",
    "google chrome": "google chrome",
    "chrom": "google chrome",
    "googlechrome": "google chrome",
    "browser": "google chrome",
    "web browser": "google chrome",
    "gchrome": "google chrome",
    "chome": "google chrome",
    "crome": "google chrome",
    "brave": "brave",
    "brave browser": "brave",
    "brav": "brave",
    "bravebrowser": "brave",
    "firefox": "firefox",
    "ff": "firefox",
    "mozilla": "firefox",
    "mozilla firefox": "firefox",
    "fire fox": "firefox",
    "firefox private": "firefox private browsing",
    "edge": "microsoft edge",
    "ms edge": "microsoft edge",
    "msedge": "microsoft edge",
    "microsoft edge": "microsoft edge",
    "msedg": "microsoft edge",

    # 6. Notepad & Text Editors
    "notepad": "notepad",
    "notepd": "notepad",
    "note pad": "notepad",
    "notpd": "notepad",
    "txt": "notepad",
    "text editor": "notepad",
    "sticky notes": "sticky notes (new)",
    "sticky note": "sticky notes (new)",
    "stickynotes": "sticky notes (new)",
    "sticky": "sticky notes (new)",
    "notes app": "sticky notes (new)",

    # 7. Calculator & Math
    "calc": "calculator",
    "calculator": "calculator",
    "calculater": "calculator",
    "cal": "calculator",
    "calcy": "calculator",
    "calci": "calculator",
    "calculate": "calculator",
    "clac": "calculator",

    # 8. Media Players & Audio
    "spotify": "spotify",
    "spotfy": "spotify",
    "spoty": "spotify",
    "spoti": "spotify",
    "vlc": "vlc media player",
    "vlc player": "vlc media player",
    "vlc media player": "vlc media player",
    "videolan": "vlc media player",
    "media player": "media player",
    "music player": "media player",
    "video player": "media player",
    "windows media player": "media player",
    "sound recorder": "sound recorder",
    "voice recorder": "sound recorder",
    "audio recorder": "sound recorder",
    "recorder": "sound recorder",

    # 9. Terminal, Shells & Git
    "terminal": "terminal",
    "windows terminal": "terminal",
    "wt": "terminal",
    "cmd": "command prompt",
    "command prompt": "command prompt",
    "prompt": "command prompt",
    "powershell": "windows powershell",
    "ps": "windows powershell",
    "pwsh": "windows powershell",
    "powershell ise": "windows powershell ise",
    "ise": "windows powershell ise",
    "git bash": "git bash",
    "bash": "git bash",
    "git": "git bash",
    "git gui": "git gui",
    "git cmd": "git cmd",
    "github": "github desktop",
    "github desktop": "github desktop",
    "gh desktop": "github desktop",

    # 10. Microsoft Office & Productivity
    "word": "word",
    "ms word": "word",
    "microsoft word": "word",
    "msword": "word",
    "doc": "word",
    "docx": "word",
    "excel": "excel",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "msexcel": "excel",
    "xls": "excel",
    "xlsx": "excel",
    "spreadsheet": "excel",
    "powerpoint": "powerpoint",
    "ppt": "powerpoint",
    "pptx": "powerpoint",
    "ms powerpoint": "powerpoint",
    "presentation": "powerpoint",
    "onenote": "onenote",
    "ms onenote": "onenote",
    "one note": "onenote",
    "outlook": "outlook (classic)",
    "ms outlook": "outlook (classic)",
    "mail": "outlook (classic)",
    "email": "outlook (classic)",
    "access": "access",
    "ms access": "access",
    "publisher": "publisher",
    "ms publisher": "publisher",

    # 11. Communication & Meetings
    "teams": "microsoft teams classic (work or school)",
    "ms teams": "microsoft teams classic (work or school)",
    "microsoft teams": "microsoft teams classic (work or school)",
    "zoom": "zoom workplace",
    "zoom workplace": "zoom workplace",
    "zm": "zoom workplace",
    "telegram": "telegram web",
    "telegram web": "telegram web",
    "tg": "telegram web",

    # 12. Windows System & Hardware Tools
    "settings": "settings",
    "windows settings": "settings",
    "setting": "settings",
    "config": "settings",
    "control panel": "control panel",
    "cpanel": "control panel",
    "task manager": "task manager",
    "taskmgr": "task manager",
    "task man": "task manager",
    "taskmanager": "task manager",
    "file explorer": "file explorer",
    "explorer": "file explorer",
    "files": "file explorer",
    "my computer": "file explorer",
    "this pc": "file explorer",
    "device manager": "device manager",
    "devmgmt": "device manager",
    "disk cleanup": "disk cleanup",
    "cleanmgr": "disk cleanup",
    "defrag": "defragment and optimize drives",
    "services": "services",
    "services.msc": "services",
    "event viewer": "event viewer",
    "resource monitor": "resource monitor",
    "resmon": "resource monitor",
    "perfmon": "performance monitor",
    "performance monitor": "performance monitor",
    "system info": "system information",
    "sysinfo": "system information",
    "msinfo32": "system information",
    "registry editor": "registry editor",
    "regedit": "registry editor",

    # 13. Graphics, Screen Capture & Utility
    "paint": "paint",
    "mspaint": "paint",
    "ms paint": "paint",
    "photos": "photos",
    "photo viewer": "photos",
    "picture viewer": "photos",
    "camera": "camera",
    "webcam": "camera",
    "cam": "camera",
    "snipping tool": "snipping tool",
    "snip": "snipping tool",
    "screenshot tool": "snipping tool",
    "snipper": "snipping tool",
    "snip tool": "snipping tool",
    "clipchamp": "microsoft clipchamp",
    "video editor": "microsoft clipchamp",
    "clock": "clock",
    "alarm": "clock",
    "timer": "clock",
    "stopwatch": "clock",
    "phone link": "phone link",
    "phonelink": "phone link",
    "quick assist": "quick assist",
    "user guide": "user guide",

    # 14. Compression & Archives
    "7zip": "7-zip file manager",
    "7-zip": "7-zip file manager",
    "7z": "7-zip file manager",
    "zip": "7-zip file manager",
    "winzip": "7-zip file manager",

    # 15. Databases & Programming Environments
    "mysql": "mysql 9.7 command line client",
    "mysql client": "mysql 9.7 command line client",
    "sql": "mysql 9.7 command line client",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "npm": "node.js command prompt",
    "python": "idle (python 3.13 64-bit)",
    "python idle": "idle (python 3.13 64-bit)",
    "idle": "idle (python 3.13 64-bit)",
    "py": "idle (python 3.13 64-bit)",
    "wsl": "wsl",
    "ubuntu": "ubuntu",
    "linux": "ubuntu",

    # 16. Lenovo & Audio Utilities
    "lenovo vantage": "lenovo vantage",
    "vantage": "lenovo vantage",
    "lenovo": "lenovo vantage",
    "lenovo now": "lenovo now",
    "dolby": "dolby access",
    "dolby access": "dolby access",
    "dolby audio": "dolby access",
    "store": "microsoft store",
    "ms store": "microsoft store",
    "windows store": "microsoft store",
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
    "visual studio code": "code",
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
    "visual studio code": ["Code.exe"],
    "code": ["Code.exe"],
    "vsc": ["Code.exe"],
    "whatsapp": ["WhatsApp.exe", "WhatsApp.Root.exe"],
    "chatgpt": ["ChatGPT.exe"],
    "antigravity": ["antigravity.exe", "Antigravity Ide.exe"],
    "edge": ["msedge.exe"],
    "ms edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
}

# Known Web Destinations
WEB_SITES = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "linkedin": "https://www.linkedin.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "chatgpt": "https://chatgpt.com",
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


LAST_ACCESSED_APP = "whatsapp"


def set_last_app(app_name: str):
    """
    Tracks the most recently referenced application for context and pronoun resolution ('it', 'that').
    """
    global LAST_ACCESSED_APP
    clean = app_name.lower().strip() if app_name else ""
    if clean and clean not in ("it", "that", "this", "app", "the app", "again", "it again"):
        LAST_ACCESSED_APP = clean


def get_last_app() -> str:
    """
    Returns the most recently referenced application name.
    """
    global LAST_ACCESSED_APP
    return LAST_ACCESSED_APP


def find_installed_app(app_query: str) -> dict | None:
    """
    Resolves user query to an installed Windows desktop application.
    Supports aliases, exact matches, prefix matches, and fuzzy typo tolerance.
    Pronouns and generic words ('it', 'that', 'this', 'app') are strictly rejected.
    """
    clean = app_query.lower().strip() if app_query else ""
    if not clean or clean in ("it", "that", "this", "app", "the app", "again", "it again"):
        return None

    cache = load_apps_cache()
    clean = APP_ALIASES.get(clean, clean)

    # 1. Exact match
    if clean in cache:
        return cache[clean]

    # 2. Starts with match (minimum 3 characters to avoid accidental 1-2 letter prefix collisions)
    if len(clean) >= 3:
        for k, info in cache.items():
            if k.startswith(clean):
                return info

    # 3. Whole-word substring match (e.g. "word" matches "microsoft word", but NOT "it" in "iscsi initiator")
    if len(clean) >= 3:
        pattern = re.compile(rf"\b{re.escape(clean)}\b", re.IGNORECASE)
        for k, info in cache.items():
            if pattern.search(k):
                return info

    # 4. Fuzzy typo matching (minimum 4 characters, strict cutoff)
    if len(clean) >= 4:
        close_matches = difflib.get_close_matches(clean, cache.keys(), n=1, cutoff=0.7)
        if close_matches:
            return cache[close_matches[0]]

    return None


def launch_desktop_app(app_name: str, call_me: str = "Sir") -> tuple[bool, str]:
    """
    Launches a native installed application directly on Windows.
    Includes automatic browser fallback for services like ChatGPT.
    Supports pronoun resolution ('open it', 'launch that') to the last referenced application.
    """
    clean_name = app_name.lower().strip() if app_name else ""

    # Contextual pronoun resolution ('it', 'that', 'again')
    if clean_name in ("it", "that", "this", "again", "the app", "it again"):
        last = get_last_app()
        if last:
            clean_name = last
        else:
            return False, f"{call_me}, which application would you like me to open?"

    if not clean_name:
        return False, f"{call_me}, which application would you like me to open?"

    # Dedicated direct handler for Task Manager application
    if clean_name in ("task manager", "taskmgr", "task man", "taskmanager"):
        set_last_app("task manager")
        try:
            subprocess.Popen("taskmgr.exe", shell=True)
            return True, f"{call_me}, launching Task Manager desktop app."
        except Exception as e:
            return False, f"{call_me}, failed to launch Task Manager: {e}"

    # Dedicated high-speed native launch for Visual Studio Code
    if clean_name in ("visual studio code", "vscode", "vs code", "code", "vsc"):
        vscode_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Microsoft VS Code\Code.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft VS Code\Code.exe"),
        ]
        for vpath in vscode_paths:
            if os.path.exists(vpath):
                set_last_app("visual studio code")
                try:
                    os.startfile(vpath)
                    return True, f"{call_me}, launching Visual Studio Code."
                except Exception:
                    pass
        code_cmd = shutil.which("code")
        if code_cmd:
            set_last_app("visual studio code")
            try:
                subprocess.Popen(["code"], shell=True)
                return True, f"{call_me}, launching Visual Studio Code."
            except Exception:
                pass

    clean_name = APP_ALIASES.get(clean_name, clean_name)
    app_info = find_installed_app(clean_name)

    if app_info:
        set_last_app(clean_name)
        display_name = app_info.get("name", clean_name.title())
        target = app_info.get("target", "")
        app_type = app_info.get("type", "lnk")

        try:
            if app_type == "uwp" or (not os.path.exists(target) and "\\" not in target):
                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{target}"])
                return True, f"{call_me}, launching {display_name} desktop app."
            elif os.path.exists(target):
                os.startfile(target)
                return True, f"{call_me}, launching {display_name}."
            else:
                subprocess.Popen(f"start {target}", shell=True)
                return True, f"{call_me}, launched {display_name}."
        except Exception:
            # Fallback if desktop app launch throws
            if clean_name in ("chatgpt", "chatgbt", "chat gpt", "gpt"):
                webbrowser.open("https://chatgpt.com")
                return True, f"{call_me}, opened ChatGPT in your browser (Desktop fallback)."

    # Fallback to standard APP_COMMANDS
    cmd = APP_COMMANDS.get(clean_name)
    if cmd:
        try:
            subprocess.Popen(cmd, shell=True)
            return True, f"{call_me}, {clean_name.title()} launched."
        except Exception:
            pass

    # Fallback to web if known destination
    if clean_name in ("chatgpt", "chatgbt", "chat gpt", "gpt"):
        webbrowser.open("https://chatgpt.com")
        return True, f"{call_me}, opened ChatGPT in your browser."

    if clean_name in WEB_SITES:
        return True, open_web(clean_name, call_me=call_me)

    return False, f"{call_me}, no installed desktop app found for '{app_name}'."


# ============================================================
# 2. SYSTEM HARDWARE METRICS, AUDIO & TIME
# ============================================================
def get_current_time_and_date(call_me: str = "Sir") -> str:
    """
    Returns current local time (including seconds), day of the week, and formatted date.
    """
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M:%S %p")
    date_str = now.strftime("%A, %d %B %Y")
    return f"{call_me}, the current time is {time_str} on {date_str}."


def get_system_stats(call_me: str = "Sir") -> str:
    """
    Returns battery percentage, charging state, CPU load, and RAM usage.
    Includes low battery guardian warning if below 20% and discharging.
    """
    try:
        battery = psutil.sensors_battery()
        battery_text = "Battery info unavailable"
        warning = ""
        if battery is not None:
            status = "charging" if battery.power_plugged else "discharging"
            battery_text = f"battery is at {battery.percent}% ({status})"
            if battery.percent <= 20 and not battery.power_plugged:
                warning = f"\n  [!] Warning: Battery is low ({battery.percent}%). Please connect your charger, {call_me}!"

        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent

        return f"{call_me}, {battery_text}. Current CPU load is {cpu}% and RAM usage is {ram}%.{warning}"
    except Exception as err:
        return f"{call_me}, unable to fetch system metrics: {err}"


def close_app(app_name: str, call_me: str = "Sir") -> str:
    """
    Terminates a running application by process name using alias resolution,
    fuzzy matching, and dynamic process inspection via psutil.
    Supports pronoun resolution ('close it', 'kill that').
    """
    clean_name = app_name.lower().strip() if app_name else ""
    if clean_name in ("it", "that", "this", "the app"):
        last = get_last_app()
        if last:
            clean_name = last
        else:
            return f"{call_me}, which application would you like me to close?"

    if not clean_name:
        return f"{call_me}, which application would you like me to close?"

    set_last_app(clean_name)

    # 1. Resolve known aliases (e.g. chatgbt -> chatgpt, vs code -> vscode)
    clean_name = APP_ALIASES.get(clean_name, clean_name)

    # 2. Fuzzy match against PROCESS_NAMES or APP_ALIASES
    if clean_name not in PROCESS_NAMES:
        candidate_keys = list(PROCESS_NAMES.keys()) + list(APP_ALIASES.keys())
        close_keys = difflib.get_close_matches(clean_name, candidate_keys, n=1, cutoff=0.55)
        if close_keys:
            resolved = close_keys[0]
            clean_name = APP_ALIASES.get(resolved, resolved)

    target_procs = PROCESS_NAMES.get(clean_name, [f"{clean_name}.exe"])
    closed_any = False

    # 3. Direct taskkill attempt on target process names
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

    # 4. Dynamic inspection via psutil for matching processes
    if not closed_any:
        try:
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    p_name = (p.info.get("name") or "").lower()
                    if clean_name in p_name or any(tp.lower() in p_name for tp in target_procs):
                        p.terminate()
                        closed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

    if closed_any:
        return f"{call_me}, {clean_name.title()} has been closed."

    # 5. Helpful guidance if it is a known web application running in a browser tab
    if clean_name in ("chatgpt", "chatgbt", "youtube", "github", "gmail", "linkedin", "twitter") or clean_name in WEB_SITES:
        return (
            f"{call_me}, no standalone desktop process found for '{clean_name.title()}'.\n"
            f"If it is currently open inside your web browser, please close that browser tab."
        )

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
        "screenshots": os.path.join(home, "Pictures", "Screenshots"),
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
    Legacy keystroke volume control (mute toggle or basic steps).
    """
    act = action.lower().strip()
    try:
        if act in ("mute", "unmute", "toggle mute"):
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
            return f"{call_me}, volume mute toggled."
        return f"{call_me}, unrecognized volume action."
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
# 3. UNIFIED COMMAND ROUTER (APPS, FILES, HARDWARE & UTILITIES)
# ============================================================
def is_file_target(target: str) -> bool:
    """
    Determines if target string refers to a file (has extension or is an actual file on disk).
    Does NOT match directories or known application aliases.
    """
    clean = target.strip().strip("'\"")
    clean_lower = clean.lower()
    if clean_lower in APP_ALIASES or clean_lower in APP_COMMANDS:
        return False
    known_exts = (".py", ".json", ".txt", ".md", ".env", ".csv", ".log", ".html", ".js", ".css", ".bat", ".sh", ".c", ".cpp", ".java", ".xml", ".yaml", ".yml")
    if any(clean_lower.endswith(ext) for ext in known_exts):
        return True
    resolved = resolve_path(clean)
    return os.path.isfile(resolved)


def execute_system_command(user_text: str, call_me: str = "Sir") -> tuple[bool, str]:
    """
    Matches user intent against desktop apps, file operations, audio, screen capture,
    and hardware automation tools. Returns (handled, response_string).
    """
    cleaned = user_text.strip().lower()
    cleaned = re.sub(r"[?!.,;]+$", "", cleaned).strip()

    # 1. Rescan Installed Applications Cache
    if cleaned in ("/scan_apps", "scan apps", "rescan apps", "refresh apps"):
        apps = scan_installed_apps()
        return True, f"{call_me}, scanned and indexed {len(apps)} installed desktop applications into apps_cache.json."

    # 2. Time and Date Engine (Strict matching to avoid hijacking instructional / conversational queries)
    time_or_date_match = (
        re.search(r"^(?:what(?:'s|\s+is)?\s+(?:the\s+)?(?:current\s+)?time(?:\s+now)?(?:\s+please)?|what\s+time\s+is\s+it|tell\s+me\s+(?:the\s+)?(?:current\s+)?time|current\s+time(?:\s+now)?|time\s+now|time)$", cleaned)
        or re.search(r"^(?:what(?:'s|\s+is)?\s+(?:the\s+)?(?:current\s+|today(?:'s)?\s+)?date(?:\s+today)?(?:\s+please)?|what\s+date\s+is\s+it|what\s+day\s+is\s+(?:it|today)|today(?:'s)?\s+date|current\s+date|date\s+today|date)$", cleaned)
        or re.search(r"^(?:tell\s+me\s+)?(?:the\s+)?(?:time\s+and\s+date|date\s+and\s+time)$", cleaned)
    )
    if time_or_date_match:
        return True, get_current_time_and_date(call_me)

    # 3. Battery / Power / System Performance
    if re.search(r"\b(battery|battery status|battery level|battery percentage|charging status)\b", cleaned):
        return True, get_system_stats(call_me)
    if re.search(r"\b(system status|pc status|system metrics|cpu status|ram status|cpu usage|ram usage)\b", cleaned):
        return True, get_system_stats(call_me)

    # 4. Windows Power Operations & Security Controls
    if re.search(r"\b(cancel\s+shutdown|abort\s+shutdown|stop\s+shutdown|don't\s+shutdown|dont\s+shutdown)\b", cleaned):
        return True, cancel_shutdown(call_me)

    if re.search(r"\b(sleep(?:\s+the)?\s*(?:laptop|pc|computer|system)?|put\s+(?:the\s+)?laptop\s+to\s+sleep|standby)\b", cleaned):
        return True, sleep_laptop(call_me)

    if re.search(r"\b(shut\s*down(?:\s+the)?\s*(?:laptop|pc|computer|system)?|turn\s*off\s+(?:the\s+)?(?:laptop|pc|computer|system)|power\s*off)\b", cleaned) and not re.search(r"\b(cancel|abort|stop)\b", cleaned):
        return True, shutdown_laptop(10, call_me)

    if re.search(r"\b(restart(?:\s+the)?\s*(?:laptop|pc|computer|system)?|reboot(?:\s+the)?\s*(?:laptop|pc|computer|system)?)\b", cleaned):
        return True, restart_laptop(10, call_me)

    if re.search(r"\b(hibernate(?:\s+the)?\s*(?:laptop|pc|computer|system)?)\b", cleaned):
        return True, hibernate_laptop(call_me)

    if re.search(r"\b(turn\s*off\s+(?:the\s+)?(?:screen|display|monitor)|screen\s*off|display\s*off)\b", cleaned):
        return True, turn_off_display(call_me)

    if re.search(r"\b(lock\s*(?:pc|screen|workstation|laptop|computer)?)\b", cleaned):
        return True, lock_workstation(call_me)

    # 5. Precision Windows Audio & Volume Controls
    vol_set_match = (
        re.search(r"\b(?:vol|volume)\s*(?:set)?\s*(?:to|=)?\s*(\d{1,3})\s*%?\b", cleaned)
        or re.search(r"\b(?:set|change|put)\s+(?:the\s+)?(?:vol|volume)\s*(?:level|to|=)?\s*(\d{1,3})\s*%?\b", cleaned)
        or re.search(r"\bst\s+vol\s+(\d{1,3})\b", cleaned)
    )
    if vol_set_match:
        target_val = int(vol_set_match.group(1))
        return True, set_volume_level(target_val, call_me)

    vol_inc_by = (
        re.search(r"\b(?:increase|raise|boost|up)\s+(?:the\s+)?(?:vol|volume)\s*(?:by)?\s*(\d{1,3})\b", cleaned)
        or re.search(r"\b(?:vol|volume)\s+up\s*(?:by)?\s*(\d{1,3})\b", cleaned)
    )
    if vol_inc_by:
        delta = int(vol_inc_by.group(1))
        return True, adjust_volume_delta(delta, call_me)

    vol_dec_by = (
        re.search(r"\b(?:decrease|lower|reduce|down)\s+(?:the\s+)?(?:vol|volume)\s*(?:by)?\s*(\d{1,3})\b", cleaned)
        or re.search(r"\b(?:vol|volume)\s+down\s*(?:by)?\s*(\d{1,3})\b", cleaned)
    )
    if vol_dec_by:
        delta = int(vol_dec_by.group(1))
        return True, adjust_volume_delta(-delta, call_me)

    if re.search(r"\b(volume up|vol up|increase volume|louder|vol \+|inc vol)\b", cleaned):
        return True, adjust_volume_delta(15, call_me)
    if re.search(r"\b(volume down|vol down|decrease volume|lower volume|quieter|softer|vol \-|dec vol)\b", cleaned):
        return True, adjust_volume_delta(-15, call_me)
    # 5.1 Microphone Control (Mute, Unmute, Mic Off, Mic On)
    if re.search(r"\b(?:unmute\s+(?:mic|microphone)|(?:mic|microphone)\s+(?:unmute|on|enable|start))\b", cleaned):
        return True, toggle_mic_mute("unmute", call_me)
    if re.search(r"\b(?:mute\s+(?:mic|microphone)|(?:mic|microphone)\s+(?:mute|off|disable|stop)|mic\s*off)\b", cleaned):
        return True, toggle_mic_mute("mute", call_me)
    if re.search(r"\b(?:toggle\s+(?:mic|microphone)|(?:mic|microphone)\s+toggle)\b", cleaned):
        return True, toggle_mic_mute("toggle", call_me)

    if re.search(r"\b(?:unmute(?:\s+volume|\s+vol|\s+pc|\s+audio)?|(?:volume|vol|audio)\s+unmute)\b", cleaned) and not re.search(r"\b(mic|microphone)\b", cleaned):
        return True, toggle_mute("unmute", call_me)
    if re.search(r"\b(?:mute(?:\s+volume|\s+vol|\s+pc|\s+audio)?|(?:volume|vol|audio)\s+mute|vol\s*mute|mute\s*vol)\b", cleaned) and not re.search(r"\b(mic|microphone)\b", cleaned):
        return True, toggle_mute("mute", call_me)

    # 6. Clipboard Operations
    if re.search(r"^(?:please\s+)?(?:read|check|view|show|what is in my|what's in my)\s+clipboard\b", cleaned) or cleaned in ("clipboard", "/clipboard"):
        return True, get_clipboard_text(call_me)
    if re.search(r"\b(clear clipboard|empty clipboard)\b", cleaned):
        return True, clear_clipboard(call_me)
    copy_match = re.search(r"^(?:please\s+)?copy\s+(?:to\s+clipboard\s+)?(.+)$", user_text.strip(), re.IGNORECASE)
    if copy_match and not cleaned.startswith("copy file"):
        text_to_copy = copy_match.group(1).strip()
        return True, set_clipboard_text(text_to_copy, call_me)

    # 7. Native Bulletproof Screenshot Engine
    if re.search(r"\b(take\s+(?:a\s+)?screen\s*shot|screen\s*shot|capture\s+screen|screen\s+capture)\b", cleaned):
        return True, take_screenshot(call_me)

    # 8. Wi-Fi, Ping & Network Latency Diagnostics
    if re.search(r"\b(ping|check ping|latency|network latency|ping test)\b", cleaned):
        return True, check_ping(call_me=call_me)
    if re.search(r"\b(wifi|wi-fi|wifi status|wi-fi status|check wifi|network status|internet connection status)\b", cleaned):
        return True, get_wifi_status(call_me)

    # 9. Quick Notes System
    note_add_match = re.search(r"^(?:add\s+)?note\s*:\s*(.+)$", user_text.strip(), re.IGNORECASE)
    if note_add_match:
        return True, add_note(note_add_match.group(1).strip(), call_me)
    if re.search(r"\b(show notes|read notes|my notes|view notes|notes list)\b", cleaned):
        return True, get_notes(call_me)
    if re.search(r"\b(clear notes|empty notes|delete notes)\b", cleaned):
        return True, clear_notes(call_me)

    # 10. Empty Recycle Bin
    if re.search(r"\b(empty recycle bin|clean recycle bin|clear recycle bin|empty trash)\b", cleaned):
        return True, empty_recycle_bin(call_me)

    # 10.1 Task Manager App vs Running Processes / System Load Listing
    if re.search(r"\b(?:open|launch|start)\s+(?:the\s+)?(?:task\s*manager|taskmgr)\b", cleaned):
        return True, launch_desktop_app("task manager", call_me=call_me)[1]

    if re.search(r"\b(running apps|active apps|what apps are running|list processes|running processes|show processes|show task manager|top apps|system processes|active processes|system load)\b", cleaned):
        return True, get_running_processes(10, call_me)

    # 10.2 Screen Brightness Controls
    bright_set = re.search(r"\b(?:set\s+)?brightness\s+(?:to\s+)?(\d{1,3})(?:%|\b)", cleaned)
    if bright_set:
        return True, set_screen_brightness(int(bright_set.group(1)), call_me)
    if re.search(r"\b(increase|boost|raise|more)\s+brightness\b", cleaned) or cleaned in ("brighter", "screen brighter"):
        return True, adjust_screen_brightness(15, call_me)
    if re.search(r"\b(decrease|lower|reduce|dim)\s+brightness\b", cleaned) or cleaned in ("dim screen", "less brightness"):
        return True, adjust_screen_brightness(-15, call_me)
    if re.search(r"\b(brightness|screen brightness|display brightness|check brightness|current brightness)\b", cleaned):
        return True, get_screen_brightness(call_me)

    # 10.3 Search Files Across Folders (Downloads, Desktop, Documents, Workspace)
    search_file_match = re.search(r"^(?:find|search\s+for|look\s+for)\s+(?:file\s+)?([a-zA-Z0-9_\-\.\s]+?)(?:\s+in\s+(downloads|desktop|documents|workspace))?$", cleaned)
    if search_file_match:
        f_query = search_file_match.group(1).strip()
        f_loc = search_file_match.group(2) or "all"
        return True, search_files_across_folders(f_query, f_loc, max_results=8, call_me=call_me)

    # 11. Direct Terminal / Developer Execution (Safe runner)
    run_cmd_match = re.search(r"^(?:run|exec|execute|terminal|cmd)\s+(.+)$", user_text.strip(), re.IGNORECASE)
    if run_cmd_match:
        cmd = run_cmd_match.group(1).strip()
        return True, run_terminal_command(cmd, call_me)
    if re.search(r"^git\s+(status|diff|branch|log|pull|commit|push)\b", cleaned):
        return True, run_terminal_command(user_text.strip(), call_me)
    if re.search(r"^pip\s+(list|show|check)\b", cleaned):
        return True, run_terminal_command(user_text.strip(), call_me)

    # 12. Desktop Notifications & Reminders
    notify_match = re.search(r"^(?:notify|send notification|remind me to)\s+(.+)$", user_text.strip(), re.IGNORECASE)
    if notify_match:
        reminder_msg = notify_match.group(1).strip()
        return True, show_desktop_notification("KIRAHT AI", reminder_msg, call_me)

    # 13. File Size / File Info Operations
    size_match = (
        re.search(r"\b(?:size of|file size of|info of|details of)\s+([a-zA-Z0-9_\-\./\\]+)\b", cleaned)
        or re.search(r"^([a-zA-Z0-9_\-\./\\]+)\s+(?:size|file size)\b", cleaned)
        or re.search(r"^([a-zA-Z0-9_\-\./\\]+)\s+size\s+enna\b", cleaned)
    )
    if size_match:
        target_file = size_match.group(1).strip()
        return True, get_file_info(target_file, call_me)

    # 14. List Workspace / Project Files
    if re.search(r"\b(list files|show files|files in project|project files|directory files|dir files|all files)\b", cleaned):
        return True, list_workspace_files(WORKSPACE_DIR, call_me)

    # 15. Read File Content
    read_match = re.search(r"^(?:please\s+)?(?:read|view|show content of|display code of|show code of)\s+([a-zA-Z0-9_\-\./\\]+)\b", cleaned)
    if read_match:
        target_file = read_match.group(1).strip()
        return True, read_file_content(target_file, max_lines=60, call_me=call_me)

    # 16. YouTube Search with Query
    yt_match = (
        re.search(r"^(?:open\s+)?youtube\s+(?:and\s+)?search\s+(.+)$", cleaned)
        or re.search(r"^search\s+(.+)\s+(?:on|in)\s+youtube$", cleaned)
    )
    if yt_match:
        query = yt_match.group(1).strip()
        return True, open_web("youtube", search_query=query, call_me=call_me)

    # 17. Google Search with Query
    google_match = (
        re.search(r"^(?:open\s+)?google\s+(?:and\s+)?search\s+(.+)$", cleaned)
        or re.search(r"^search\s+(.+)\s+(?:on|in)\s+google$", cleaned)
    )
    if google_match:
        query = google_match.group(1).strip()
        return True, open_web("google", search_query=query, call_me=call_me)

    # 18. Open Web Destinations
    web_match = re.search(r"^(?:please\s+)?(?:open|go to|launch)\s+(youtube|github|gmail|linkedin|twitter)\b", cleaned)
    if web_match:
        site = web_match.group(1).strip()
        return True, open_web(site, call_me=call_me)

    # 19. Open Folders
    folder_match = re.search(
        r"^(?:please\s+)?open\s+(downloads|documents|pictures|screenshots|desktop|project|workspace|kiraht)(?:\s+folder)?\b",
        cleaned,
    )
    if folder_match:
        target_folder = folder_match.group(1).strip()
        return True, open_folder(target_folder, call_me=call_me)

    # 20. Contacts & WhatsApp Messaging Engine
    contact_add_match = re.search(
        r"^(?:please\s+)?(?:add\s+contact|save\s+contact|add)\s+([a-zA-Z0-9_\s]+?)\s+([+0-9\s\-]+)$",
        user_text.strip(),
        re.IGNORECASE,
    )
    if contact_add_match:
        c_name = contact_add_match.group(1).strip()
        c_phone = contact_add_match.group(2).strip()
        if c_name.lower() not in ("alias", "nickname", "note", "group", "grp"):
            return True, add_contact(c_name, c_phone, call_me)

    grp_add_match = re.search(
        r"^(?:please\s+)?(?:add\s+group|save\s+group|add\s+grp)\s+([a-zA-Z0-9_\s]+)$",
        user_text.strip(),
        re.IGNORECASE,
    )
    if grp_add_match:
        g_name = grp_add_match.group(1).strip()
        return True, add_group(g_name, call_me)

    alias_match = (
        re.search(
            r"^(?:please\s+)?(?:add\s+)?(?:alias|nickname)\s+([a-zA-Z0-9_\s]+?)\s+(?:for|to|=|is)\s+([a-zA-Z0-9_\s]+)$",
            user_text.strip(),
            re.IGNORECASE,
        )
        or re.search(
            r"^(?:please\s+)?set\s+nickname\s+([a-zA-Z0-9_\s]+?)\s+as\s+([a-zA-Z0-9_\s]+)$",
            user_text.strip(),
            re.IGNORECASE,
        )
    )
    if alias_match:
        nick = alias_match.group(1).strip()
        target = alias_match.group(2).strip()
        return True, add_contact_alias(nick, target, call_me)

    if re.search(r"\b(import contacts|import google contacts|/import_contacts|sync contacts)\b", cleaned):
        return True, import_google_contacts_csv("googlecontacts.csv", call_me)

    if re.search(r"\b(list contacts|show contacts|view contacts|contacts list|my contacts)\b", cleaned):
        return True, list_contacts(call_me)

    WA_TRIGS = r"(?:whats?\s*app|whatasapp|whataspp|whatsap|whatapp|whatsappp|whatssap|watsapp|watapp|watsp|whapp|whasap|whtsp|whtsapp|wa|wp)"
    GRP_TRIGS = r"(?:group|grp|grop|grup|groupp)"

    # Check "send <target> (from|on|via|through) whatsapp <msg>" (e.g. "send juhail from whatsapp hi")
    wa_from_match = re.search(rf"^(?:please\s+)?send\s+([a-zA-Z0-9_\-\.\s]+?)\s+(?:from|on|via|through)\s+{WA_TRIGS}\s*(.*)$", user_text.strip(), re.IGNORECASE)
    if wa_from_match:
        target = wa_from_match.group(1).strip()
        msg_text = wa_from_match.group(2).strip()
        if msg_text:
            return True, send_whatsapp_message(target, msg_text, call_me, is_group=False, auto_send=True)
        else:
            phone, display_name, related = resolve_contact(target)
            disp = display_name if display_name else target.title()
            return True, f"__NEED_MESSAGE__:{target}:{disp}:individual:send"

    wa_pattern = rf"^(?:please\s+)?(?:send\s+(?:a\s+)?(?:{WA_TRIGS}\s+)?(?:message|msg)\s+(?:to\s+)?|send\s+{WA_TRIGS}(?:\s+to)?|{WA_TRIGS})\s+(.*)$"
    wa_match = re.search(wa_pattern, user_text.strip(), re.IGNORECASE)
    if wa_match:
        # Check if user explicitly used 'send' (auto-send) or just 'whatsapp' (review mode)
        is_auto_send = bool(re.search(rf"^\s*(?:please\s+)?send\s+(?:a\s+)?(?:{WA_TRIGS}|message|msg)\b", user_text.strip(), re.IGNORECASE))
        send_flag = "send" if is_auto_send else "review"

        rest = wa_match.group(1).strip()
        is_group = False

        # Check if starts with group keyword (e.g. "grp roombies" or "group clg project")
        grp_match = re.search(rf"^{GRP_TRIGS}\s+(.*)$", rest, re.IGNORECASE)
        if grp_match:
            is_group = True
            rest = grp_match.group(1).strip()

        target = ""
        msg_text = ""

        # Case A: explicit delimiter (: or saying or msg or text: or that)
        delim_match = re.search(r"^(.*?)\s*(?::|saying|msg|message|text:|that)\s*(.*)$", rest, re.IGNORECASE)
        if delim_match:
            target = delim_match.group(1).strip()
            msg_text = delim_match.group(2).strip()
        elif is_group:
            # Case B: For group, check words
            words = rest.split()
            if len(words) == 1:
                target = rest
                msg_text = ""
            else:
                target = rest
                msg_text = ""
        else:
            # Case C: Check if entire rest is a known contact or alias
            phone, dname, rel = resolve_contact(rest)
            if phone:
                target = rest
                msg_text = ""
            else:
                # Case D: Check if first N words match a known contact (greedy 3 words down to 1)
                words = rest.split()
                matched_prefix = False
                for n in range(min(3, len(words) - 1), 0, -1):
                    cand = " ".join(words[:n])
                    c_phone, c_dname, c_rel = resolve_contact(cand)
                    if c_phone:
                        target = cand
                        msg_text = " ".join(words[n:])
                        matched_prefix = True
                        break
                if not matched_prefix:
                    if len(words) == 1:
                        target = words[0]
                        msg_text = ""
                    else:
                        target = words[0]
                        msg_text = " ".join(words[1:])

        # Check if it's a group:
        if is_group:
            g_info, related_groups = resolve_group(target)
            target_display = g_info['display'] if g_info else target.strip()
            if not msg_text:
                return True, f"__NEED_MESSAGE__:{target_display}:{target_display}:group:{send_flag}"
            else:
                return True, send_whatsapp_message(target_display, msg_text, call_me, is_group=True, auto_send=is_auto_send)

        # Individual contact:
        if not msg_text:
            phone, display_name, related = resolve_contact(target)
            disp = display_name if display_name else target.title()
            return True, f"__NEED_MESSAGE__:{target}:{disp}:individual:{send_flag}"

        # If message text is provided, dispatch immediately!
        return True, send_whatsapp_message(target, msg_text, call_me, is_group=False, auto_send=is_auto_send)

    # 20.1 Compound Command: "close <app> and (then )?reopen it"
    reopen_compound = re.search(r"^(?:please\s+)?close\s+([a-zA-Z0-9\s\-]+?)\s+and\s+(?:then\s+)?(?:reopen|open)\s*(?:it)?$", cleaned)
    if reopen_compound:
        app_target = reopen_compound.group(1).strip()
        close_app(app_target, call_me=call_me)
        time.sleep(1.0)
        launched, msg = launch_desktop_app(app_target, call_me=call_me)
        return True, f"{call_me}, closed {app_target.title()} and reopened it."

    restart_match = re.search(r"^(?:please\s+)?(?:restart|reopen)\s+([a-zA-Z0-9\s\-]+)$", cleaned)
    if restart_match:
        app_target = restart_match.group(1).strip()
        if app_target in ("it", "that", "this", "the app"):
            app_target = get_last_app()
        if not app_target:
            return True, f"{call_me}, which application would you like me to restart?"
        close_app(app_target, call_me=call_me)
        time.sleep(1.0)
        launched, msg = launch_desktop_app(app_target, call_me=call_me)
        return True, f"{call_me}, closed {app_target.title()} and reopened it."

    # 21. Close Application
    close_match = re.search(r"^(?:please\s+)?(?:close|kill|quit|terminate)\s+([a-zA-Z0-9\s]+)\b", cleaned)
    if close_match:
        app_to_close = close_match.group(1).strip()
        return True, close_app(app_to_close, call_me=call_me)

    # 22. Open File in Editor (e.g. "open main.py", "open file memory.json")
    open_file_match = re.search(r"^(?:please\s+)?open\s+(?:file\s+)?([a-zA-Z0-9_\-\./\\]+)\b", cleaned)
    if open_file_match:
        target_item = open_file_match.group(1).strip()
        if is_file_target(target_item):
            return True, open_file_in_editor(target_item, call_me)

    # 23. Open Desktop Application (Native Laptop App First, with Browser Fallback)
    if cleaned in ("open", "launch", "start", "run") or re.match(r"^(?:please\s+)?(?:open|launch|start|run)\s*$", cleaned):
        return True, f"{call_me}, which application would you like me to open?"

    open_app_match = re.search(r"^(?:please\s+)?(?:open|launch|start|run)\s+([a-zA-Z0-9\s\-]+)\b", cleaned)
    if open_app_match:
        app_to_open = open_app_match.group(1).strip()
        if not app_to_open:
            return True, f"{call_me}, which application would you like me to open?"
        if app_to_open in ("it", "that", "this", "again", "the app", "it again"):
            app_to_open = get_last_app()
            if not app_to_open:
                return True, f"{call_me}, which application would you like me to open?"
        if app_to_open not in ("folder", "file") and not is_file_target(app_to_open):
            launched, msg = launch_desktop_app(app_to_open, call_me=call_me)
            if launched:
                return True, msg

    return False, ""

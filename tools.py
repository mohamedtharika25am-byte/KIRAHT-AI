"""
KIRAHT AI - Tools Engine (Laptop Operations & OS Automation)
Provides local, secure, and instant Windows automation for KIRAHT AI.

Capabilities:
- App Launcher & Killer (Chrome, Notepad, Calculator, VS Code, Spotify, Antigravity, etc.)
- System Hardware Metrics (Battery, CPU, RAM)
- Audio & Volume Controls (Mute, Volume Up, Volume Down)
- Web & YouTube Direct Search (Opens in default browser)
- Directory Explorer (Downloads, Documents, Desktop, Project Folders)
- Security Controls (Lock Workstation)
"""

import ctypes
import os
import re
import subprocess
import urllib.parse
import webbrowser
import psutil

# Virtual-Key codes for Windows user32 keybd_event
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

# Common Application Launch Mapping
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
}

# Known Web Destinations
WEB_SITES = {
    "youtube": "https://www.youtube.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "google": "https://www.google.com",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chat.openai.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
}


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


def open_app(app_name: str, call_me: str = "Sir") -> str:
    """
    Launches a local application on Windows.
    """
    clean_name = app_name.lower().strip()
    cmd = APP_COMMANDS.get(clean_name, f"start {clean_name}")

    try:
        subprocess.Popen(cmd, shell=True)
        display_name = clean_name.title()
        return f"{call_me}, {display_name} has been launched."
    except Exception as err:
        return f"{call_me}, failed to open {app_name}: {err}"


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
        "project": r"d:\KIRAHT AI",
        "workspace": r"d:\KIRAHT AI",
        "kiraht": r"d:\KIRAHT AI",
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


def execute_system_command(user_text: str, call_me: str = "Sir") -> tuple[bool, str]:
    """
    Matches user intent against laptop operation tools.
    Returns (handled, response_string).
    """
    cleaned = user_text.strip().lower()

    # 1. Battery / Power / System Performance
    if re.search(r"\b(battery|battery status|battery level|battery percentage|charging status)\b", cleaned):
        return True, get_system_stats(call_me)
    if re.search(r"\b(system status|pc status|system metrics|cpu status|ram status|cpu usage|ram usage)\b", cleaned):
        return True, get_system_stats(call_me)

    # 2. Lock Workstation
    if re.search(r"\b(lock pc|lock screen|lock workstation|lock computer)\b", cleaned):
        return True, lock_workstation(call_me)

    # 3. Audio & Volume
    if re.search(r"\b(mute volume|unmute volume|mute pc|unmute pc|mute|unmute)\b", cleaned):
        return True, adjust_volume("mute", call_me)
    if re.search(r"\b(volume up|increase volume|volume increase|louder)\b", cleaned):
        return True, adjust_volume("up", call_me)
    if re.search(r"\b(volume down|decrease volume|volume decrease|lower volume)\b", cleaned):
        return True, adjust_volume("down", call_me)

    # 4. YouTube Search with Query
    yt_match = re.search(r"^(?:open\s+)?youtube\s+(?:and\s+)?search\s+(.+)$", cleaned) or \
               re.search(r"^search\s+(.+)\s+(?:on|in)\s+youtube$", cleaned)
    if yt_match:
        query = yt_match.group(1).strip()
        return True, open_web("youtube", search_query=query, call_me=call_me)

    # 5. Google Search with Query
    google_match = re.search(r"^(?:open\s+)?google\s+(?:and\s+)?search\s+(.+)$", cleaned) or \
                   re.search(r"^search\s+(.+)\s+(?:on|in)\s+google$", cleaned)
    if google_match:
        query = google_match.group(1).strip()
        return True, open_web("google", search_query=query, call_me=call_me)

    # 6. Open Web Destinations
    web_match = re.search(r"^(?:please\s+)?(?:open|go to|launch)\s+(youtube|github|gmail|whatsapp|linkedin|chatgpt|twitter)\b", cleaned)
    if web_match:
        site = web_match.group(1).strip()
        return True, open_web(site, call_me=call_me)

    # 7. Open Folders
    folder_match = re.search(r"^(?:please\s+)?open\s+(downloads|documents|pictures|desktop|project|workspace|kiraht)(?:\s+folder)?\b", cleaned)
    if folder_match:
        target_folder = folder_match.group(1).strip()
        return True, open_folder(target_folder, call_me=call_me)

    # 8. Close Application
    close_match = re.search(r"^(?:please\s+)?(?:close|kill|quit|terminate)\s+([a-zA-Z0-9\s]+)\b", cleaned)
    if close_match:
        app_to_close = close_match.group(1).strip()
        if app_to_close in PROCESS_NAMES or app_to_close in APP_COMMANDS:
            return True, close_app(app_to_close, call_me=call_me)

    # 9. Open Application
    open_match = re.search(r"^(?:please\s+)?(?:open|launch|start|run)\s+([a-zA-Z0-9\s]+)\b", cleaned)
    if open_match:
        app_to_open = open_match.group(1).strip()
        if app_to_open in APP_COMMANDS:
            return True, open_app(app_to_open, call_me=call_me)

    return False, ""

"""
KIRAHT AI - Smart Desktop Web HUD Launcher
1. Checks if the server is already active on port 8000.
2. If not running, launches 'python main.py --web' quietly in the background.
3. Automatically opens the default web browser to http://127.0.0.1:8000.
"""

import os
import sys
import time
import urllib.request
import webbrowser
import subprocess

PORT = 8000
URL = f"http://127.0.0.1:{PORT}"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def is_server_ready(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KIRAHT-Launcher/1.0"})
        with urllib.request.urlopen(req, timeout=1.2) as resp:
            return resp.status in (200, 301, 302, 404)
    except Exception:
        return False


def launch():
    # If already running, simply focus / open browser
    if is_server_ready(URL):
        webbrowser.open(URL)
        return

    # Start main.py --web in background without opening CMD window
    python_exe = sys.executable
    if python_exe.lower().endswith("pythonw.exe"):
        # Use python.exe for child process to ensure full standard library runtime
        normal_python = python_exe[:-5] + ".exe"
        if os.path.exists(normal_python):
            python_exe = normal_python

    log_file_path = os.path.join(PROJECT_DIR, "web_server.log")
    log_file = open(log_file_path, "a", encoding="utf-8")

    creation_flags = 0
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        creation_flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    subprocess.Popen(
        [python_exe, "main.py", "--web"],
        cwd=PROJECT_DIR,
        creationflags=creation_flags,
        stdout=log_file,
        stderr=log_file,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )

    # Wait until server is listening and ready (up to 15 seconds)
    for _ in range(30):
        time.sleep(0.5)
        if is_server_ready(URL):
            break

    webbrowser.open(URL)


if __name__ == "__main__":
    launch()

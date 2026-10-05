"""
KIRAHT AI - Global System Hotkeys Daemon (Category 2)
Listens for system-wide hotkeys across Windows (regardless of which app is active):
  - Alt + Shift + K : Bring KIRAHT Web HUD to front / Open Web HUD
  - Alt + Shift + S : Global Instant Screen Capture
  - Alt + Shift + D : Global System Diagnostic Trigger
"""

import ctypes
from ctypes import wintypes
import os
import sys
import threading
import time
import webbrowser

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001

HOTKEY_HUD = 1       # Alt + Shift + K
HOTKEY_SCREEN = 2    # Alt + Shift + S
HOTKEY_DIAG = 3      # Alt + Shift + D

VK_K = 0x4B
VK_S = 0x53
VK_D = 0x44

_hotkey_thread = None
_stop_event = threading.Event()
_user32 = ctypes.windll.user32 if sys.platform == "win32" else None


def _bring_hud_to_front():
    """Focuses the browser window running KIRAHT AI HUD or opens it."""
    try:
        import win32gui
        import win32con
        found = []

        def enum_win(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "KIRAHT AI" in title or "Tactical Web HUD" in title:
                    found.append(hwnd)

        win32gui.EnumWindows(enum_win, None)
        if found:
            hwnd = found[0]
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
    except Exception:
        pass
    webbrowser.open("http://127.0.0.1:8000")
    return True


def _trigger_global_screenshot():
    """Takes instant screenshot from any window."""
    try:
        from system_tools import capture_screenshot
        res = capture_screenshot()
        print(f"[*] Global hotkey screenshot: {res}")
    except Exception as e:
        print(f"[!] Global screenshot error: {e}")


def _trigger_global_diag():
    """Triggers global system telemetry diagnostic."""
    try:
        from core import get_system_telemetry
        telem = get_system_telemetry()
        print(f"[*] Global diagnostic: CPU {telem.get('cpu', {}).get('percent')}%")
    except Exception as e:
        print(f"[!] Global diag error: {e}")


def _hotkey_worker():
    if not _user32:
        return
    # Register hotkeys on thread message queue
    _user32.RegisterHotKey(None, HOTKEY_HUD, MOD_ALT | MOD_SHIFT, VK_K)
    _user32.RegisterHotKey(None, HOTKEY_SCREEN, MOD_ALT | MOD_SHIFT, VK_S)
    _user32.RegisterHotKey(None, HOTKEY_DIAG, MOD_ALT | MOD_SHIFT, VK_D)

    print("[*] Global System Hotkeys active (Alt+Shift+K: Focus HUD, Alt+Shift+S: Screenshot, Alt+Shift+D: Diagnostic)")

    msg = wintypes.MSG()
    try:
        while not _stop_event.is_set():
            if _user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                if msg.message == WM_HOTKEY:
                    hk_id = msg.wParam
                    if hk_id == HOTKEY_HUD:
                        threading.Thread(target=_bring_hud_to_front, daemon=True).start()
                    elif hk_id == HOTKEY_SCREEN:
                        threading.Thread(target=_trigger_global_screenshot, daemon=True).start()
                    elif hk_id == HOTKEY_DIAG:
                        threading.Thread(target=_trigger_global_diag, daemon=True).start()
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.04)
    finally:
        try:
            _user32.UnregisterHotKey(None, HOTKEY_HUD)
            _user32.UnregisterHotKey(None, HOTKEY_SCREEN)
            _user32.UnregisterHotKey(None, HOTKEY_DIAG)
        except Exception:
            pass


def start_global_hotkeys():
    """Starts the global system hotkeys daemon thread."""
    global _hotkey_thread
    if sys.platform != "win32" or not _user32:
        return
    if _hotkey_thread and _hotkey_thread.is_alive():
        return
    _stop_event.clear()
    _hotkey_thread = threading.Thread(target=_hotkey_worker, name="KIRAHT-GlobalHotkeys", daemon=True)
    _hotkey_thread.start()


def stop_global_hotkeys():
    """Stops the global system hotkeys daemon."""
    _stop_event.set()

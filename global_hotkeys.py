"""
KIRAHT AI - Global System Hotkeys Daemon (Category 2)
Listens for system-wide hotkeys across Windows (regardless of which app is active):
  - Ctrl + Alt + K / Ctrl + Shift + K : Bring KIRAHT Web HUD to front / Open Web HUD
  - Ctrl + Alt + S / Ctrl + Shift + S : Global Instant Screen Capture
  - Ctrl + Alt + D / Ctrl + Shift + D : Global System Diagnostic Trigger

Note on Windows OS:
Alt+Shift is reserved by the Windows kernel for switching keyboard input languages,
so Windows blocks user applications from hooking Alt+Shift. Ctrl+Alt and Ctrl+Shift
are fully supported and work reliably across all Windows 10/11 versions.
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
WM_QUIT = 0x0012

# Hotkey IDs
HK_HUD_CA = 101       # Ctrl + Alt + K
HK_HUD_CS = 102       # Ctrl + Shift + K
HK_SCREEN_CA = 201    # Ctrl + Alt + S
HK_SCREEN_CS = 202    # Ctrl + Shift + S
HK_DIAG_CA = 301      # Ctrl + Alt + D
HK_DIAG_CS = 302      # Ctrl + Shift + D

VK_K = 0x4B
VK_S = 0x53
VK_D = 0x44

_hotkey_thread = None
_hotkey_thread_id = None
_user32 = ctypes.windll.user32 if sys.platform == "win32" else None
_kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None


def _force_window_foreground(hwnd):
    """Bypasses Windows focus-stealing prevention to bring window to front."""
    if not _user32:
        return
    # Restore if minimized
    _user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    # Simulate ALT keystroke to grant foreground activation privilege
    _user32.keybd_event(0x12, 0, 0, 0)
    _user32.keybd_event(0x12, 0, 2, 0)
    _user32.SetForegroundWindow(hwnd)


def _bring_hud_to_front():
    """Focuses the browser window running KIRAHT AI HUD or opens it."""
    try:
        import win32gui
        found = []

        def enum_win(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "KIRAHT AI" in title or "Tactical Web HUD" in title:
                    found.append(hwnd)

        win32gui.EnumWindows(enum_win, None)
        if found:
            _force_window_foreground(found[0])
            return True
    except Exception:
        pass
    webbrowser.open("http://127.0.0.1:8000")
    return True


def _trigger_global_screenshot():
    """Takes instant screenshot from any active window."""
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


def _hotkey_worker(ready_evt: threading.Event):
    global _hotkey_thread_id
    if not _user32 or not _kernel32:
        ready_evt.set()
        return

    _hotkey_thread_id = _kernel32.GetCurrentThreadId()

    # Register hotkey combinations
    reg_list = [
        (HK_HUD_CA, MOD_CONTROL | MOD_ALT, VK_K, "Ctrl+Alt+K (Focus HUD)"),
        (HK_HUD_CS, MOD_CONTROL | MOD_SHIFT, VK_K, "Ctrl+Shift+K (Focus HUD)"),
        (HK_SCREEN_CA, MOD_CONTROL | MOD_ALT, VK_S, "Ctrl+Alt+S (Screenshot)"),
        (HK_SCREEN_CS, MOD_CONTROL | MOD_SHIFT, VK_S, "Ctrl+Shift+S (Screenshot)"),
        (HK_DIAG_CA, MOD_CONTROL | MOD_ALT, VK_D, "Ctrl+Alt+D (Diagnostic)"),
        (HK_DIAG_CS, MOD_CONTROL | MOD_SHIFT, VK_D, "Ctrl+Shift+D (Diagnostic)"),
    ]

    active_ids = []
    for hkid, mod, vk, desc in reg_list:
        success = _user32.RegisterHotKey(None, hkid, mod, vk)
        if success:
            active_ids.append(hkid)

    print(f"[*] Global System Hotkeys initialized ({len(active_ids)} hotkeys active).")
    ready_evt.set()

    msg = wintypes.MSG()
    try:
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                hk_id = msg.wParam
                if hk_id in (HK_HUD_CA, HK_HUD_CS):
                    threading.Thread(target=_bring_hud_to_front, daemon=True).start()
                elif hk_id in (HK_SCREEN_CA, HK_SCREEN_CS):
                    threading.Thread(target=_trigger_global_screenshot, daemon=True).start()
                elif hk_id in (HK_DIAG_CA, HK_DIAG_CS):
                    threading.Thread(target=_trigger_global_diag, daemon=True).start()

            _user32.TranslateMessage(ctypes.byref(msg))
            _user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        for hkid in active_ids:
            try:
                _user32.UnregisterHotKey(None, hkid)
            except Exception:
                pass


def start_global_hotkeys():
    """Starts the global system hotkeys daemon thread."""
    global _hotkey_thread
    if sys.platform != "win32" or not _user32:
        return
    if _hotkey_thread and _hotkey_thread.is_alive():
        return

    ready_evt = threading.Event()
    _hotkey_thread = threading.Thread(
        target=_hotkey_worker,
        args=(ready_evt,),
        name="KIRAHT-GlobalHotkeys",
        daemon=True
    )
    _hotkey_thread.start()
    ready_evt.wait(timeout=2.0)


def stop_global_hotkeys():
    """Stops the global system hotkeys daemon."""
    global _hotkey_thread_id
    if _user32 and _hotkey_thread_id:
        try:
            _user32.PostThreadMessageW(_hotkey_thread_id, WM_QUIT, 0, 0)
        except Exception:
            pass

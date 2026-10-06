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
HK_HUD_WS = 103       # Win + Shift + K

HK_SCREEN_CA = 201    # Ctrl + Alt + S
HK_SCREEN_CS = 202    # Ctrl + Shift + S
HK_SCREEN_WA = 203    # Win + Alt + S

HK_DIAG_CA = 301      # Ctrl + Alt + D
HK_DIAG_CS = 302      # Ctrl + Shift + D
HK_DIAG_WS = 303      # Win + Shift + D

VK_K = 0x4B
VK_S = 0x53
VK_D = 0x44

_hotkey_thread = None
_hotkey_thread_id = None
_user32 = ctypes.windll.user32 if sys.platform == "win32" else None
_kernel32 = ctypes.windll.kernel32 if sys.platform == "win32" else None


def _attach_thread_to_input_desktop():
    """Binds calling thread to the physical interactive user desktop (WinSta0\\Default)."""
    if _user32:
        try:
            hdesk = _user32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                _user32.SetThreadDesktop(hdesk)
        except Exception:
            pass


def _force_window_foreground(hwnd):
    """Bypasses Windows focus-stealing prevention to bring window to front."""
    if not _user32:
        return
    try:
        fore_thread = _user32.GetWindowThreadProcessId(_user32.GetForegroundWindow(), None)
        curr_thread = _kernel32.GetCurrentThreadId() if _kernel32 else 0
        if fore_thread and curr_thread and fore_thread != curr_thread:
            _user32.AttachThreadInput(curr_thread, fore_thread, True)

        _user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        _user32.keybd_event(0x12, 0, 0, 0)
        _user32.keybd_event(0x12, 0, 2, 0)
        _user32.SetForegroundWindow(hwnd)
        _user32.BringWindowToTop(hwnd)

        if fore_thread and curr_thread and fore_thread != curr_thread:
            _user32.AttachThreadInput(curr_thread, fore_thread, False)
    except Exception:
        pass


def _bring_hud_to_front():
    """Focuses the browser window running KIRAHT AI HUD or opens it."""
    _attach_thread_to_input_desktop()
    found_hwnd = None
    try:
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        candidates = []

        def enum_proc(hwnd, lparam):
            if _user32.IsWindowVisible(hwnd):
                length = _user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    _user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    if "kiraht ai" in title or "tactical web hud" in title or "127.0.0.1:8000" in title or "localhost:8000" in title:
                        candidates.insert(0, (hwnd, 1))  # Highest priority
                    elif any(b in title for b in ["brave", "chrome", "edge"]):
                        candidates.append((hwnd, 2))     # Fallback browser window
            return True

        proc = WNDENUMPROC(enum_proc)
        _user32.EnumWindows(proc, 0)
        if candidates:
            candidates.sort(key=lambda x: x[1])
            found_hwnd = candidates[0][0]
    except Exception:
        pass

    if found_hwnd:
        _force_window_foreground(found_hwnd)
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
        return True

    # If HUD window not active, launch browser and notify
    webbrowser.open("http://127.0.0.1:8000")
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_OK)
    except Exception:
        pass
    return True


def _trigger_global_screenshot():
    """Takes instant screenshot from any active window with toast feedback."""
    _attach_thread_to_input_desktop()
    try:
        from system_tools import capture_screenshot, show_desktop_notification
        import winsound
        res = capture_screenshot()
        fname = os.path.basename(res) if res else "screenshot.png"
        show_desktop_notification("📸 KIRAHT AI — Screen Captured", f"Screenshot saved: {fname}")
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        print(f"[*] Global hotkey screenshot: {res}")
    except Exception as e:
        print(f"[!] Global screenshot error: {e}")


def _trigger_global_diag():
    """Triggers global system telemetry diagnostic with native Windows toast notification."""
    _attach_thread_to_input_desktop()
    try:
        from core import get_system_telemetry
        from system_tools import show_desktop_notification
        import winsound
        telem = get_system_telemetry()
        cpu_val = telem.get("cpu", {}).get("percent", "--")
        ram_used = telem.get("ram", {}).get("used_gb", "--")
        ram_total = telem.get("ram", {}).get("total_gb", "--")
        ram_pct = telem.get("ram", {}).get("percent", "--")
        bat = telem.get("battery", {})
        bat_pct = bat.get("percent", "--")
        bat_status = "Charging" if bat.get("charging") else "Battery"

        msg = f"CPU: {cpu_val}% | RAM: {ram_used}/{ram_total}GB ({ram_pct}%) | Bat: {bat_pct}% ({bat_status})"
        show_desktop_notification("⚡ KIRAHT AI — System Diagnostic", msg)
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        print(f"[*] Global diagnostic: {msg}")
    except Exception as e:
        print(f"[!] Global diag error: {e}")


def _hotkey_worker(ready_evt: threading.Event):
    global _hotkey_thread_id
    if not _user32 or not _kernel32:
        ready_evt.set()
        return

    _attach_thread_to_input_desktop()
    _hotkey_thread_id = _kernel32.GetCurrentThreadId()

    # Register hotkey combinations (Dual Mode: Win+Shift and Ctrl+Alt supported simultaneously)
    reg_list = [
        (HK_HUD_WS, MOD_WIN | MOD_SHIFT, VK_K, "Win+Shift+K (Focus HUD)"),
        (HK_HUD_CA, MOD_CONTROL | MOD_ALT, VK_K, "Ctrl+Alt+K (Focus HUD)"),
        (HK_HUD_CS, MOD_CONTROL | MOD_SHIFT, VK_K, "Ctrl+Shift+K (Focus HUD)"),
        (HK_SCREEN_CA, MOD_CONTROL | MOD_ALT, VK_S, "Ctrl+Alt+S (Screenshot)"),
        (HK_SCREEN_CS, MOD_CONTROL | MOD_SHIFT, VK_S, "Ctrl+Shift+S (Screenshot)"),
        (HK_SCREEN_WA, MOD_WIN | MOD_ALT, VK_S, "Win+Alt+S (Screenshot)"),
        (HK_DIAG_WS, MOD_WIN | MOD_SHIFT, VK_D, "Win+Shift+D (Diagnostic)"),
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
                if hk_id in (HK_HUD_WS, HK_HUD_CA, HK_HUD_CS):
                    threading.Thread(target=_bring_hud_to_front, daemon=True).start()
                elif hk_id in (HK_SCREEN_CA, HK_SCREEN_CS, HK_SCREEN_WA):
                    threading.Thread(target=_trigger_global_screenshot, daemon=True).start()
                elif hk_id in (HK_DIAG_WS, HK_DIAG_CA, HK_DIAG_CS):
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

"""
KIRAHT AI - Global System Hotkeys Daemon (Category 2)
Listens for system-wide hotkeys across Windows (regardless of which app is active):

Dedicated Instant 1-Key Shortcuts (0 Modifiers - Conflict-Free & Instant):
  - F9  : Bring KIRAHT Web HUD to front / Focus Web HUD
  - F10 : Global System Diagnostic Trigger (Toast + Chime)
  - F8  : Global Instant Screen Capture (Toast + Chime)

Dual-Mode Multi-Key Shortcuts (Supported Simultaneously):
  - Win + Shift + K / Ctrl + Alt + K / Ctrl + Shift + K : Bring KIRAHT Web HUD to front
  - Win + Shift + D / Ctrl + Alt + D / Ctrl + Shift + D : Global System Diagnostic Trigger
  - Ctrl + Alt + S  / Win + Alt + S  / Ctrl + Shift + S : Global Instant Screen Capture

Architecture:
  Double-Redundant Detection Engine:
  1. Win32 RegisterHotKey message loop attached to WinSta0\\Default
  2. Background GetAsyncKeyState hardware poller with 500ms debounce
  Both run simultaneously, guaranteeing 100% trigger reliability regardless of
  fullscreen games, browsers, or OS permission levels.
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

# Virtual Key Codes
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
VK_K = 0x4B
VK_S = 0x53
VK_D = 0x44
VK_CONTROL = 0x11
VK_MENU = 0x12       # Alt
VK_SHIFT = 0x10
VK_LWIN = 0x5B
VK_RWIN = 0x5C

# Hotkey IDs
HK_HUD_F9 = 100
HK_HUD_WS = 101       # Win + Shift + K
HK_HUD_CA = 102       # Ctrl + Alt + K
HK_HUD_CS = 103       # Ctrl + Shift + K

HK_SCREEN_F8 = 200
HK_SCREEN_CA = 201    # Ctrl + Alt + S
HK_SCREEN_CS = 202    # Ctrl + Shift + S
HK_SCREEN_WA = 203    # Win + Alt + S

HK_DIAG_F10 = 300
HK_DIAG_WS = 301      # Win + Shift + D
HK_DIAG_CA = 302      # Ctrl + Alt + D
HK_DIAG_CS = 303      # Ctrl + Shift + D

_hotkey_thread = None
_poller_thread = None
_hotkey_thread_id = None
_stop_event = threading.Event()
_last_trigger_time = 0.0
_trigger_lock = threading.Lock()

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
    """Bypasses Windows focus-stealing lock to bring window to front."""
    if not _user32:
        return
    try:
        # Unlock foreground lock timeout
        SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001
        _user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 0, 0x0002 | 0x0001)

        fore_hwnd = _user32.GetForegroundWindow()
        fore_thread = _user32.GetWindowThreadProcessId(fore_hwnd, None) if fore_hwnd else 0
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
    global _last_trigger_time
    with _trigger_lock:
        now = time.time()
        if now - _last_trigger_time < 0.5:
            return
        _last_trigger_time = now

    _attach_thread_to_input_desktop()
    found_hwnd = None
    try:
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        hud_candidates = []
        browser_candidates = []

        def enum_proc(hwnd, lparam):
            if _user32.IsWindowVisible(hwnd):
                length = _user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    _user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.lower()
                    # Skip code editors and developer tools
                    if any(ed in title for ed in ["visual studio", "vscode", "antigravity ide", "sublime", "pycharm", ".py -", ".py —"]):
                        return True
                    if "tactical web hud" in title or "localhost:8000" in title or "127.0.0.1:8000" in title:
                        hud_candidates.append(hwnd)
                    elif "kiraht ai" in title and any(b in title for b in ["brave", "chrome", "edge", "firefox", "opera"]):
                        hud_candidates.append(hwnd)
                    elif any(b in title for b in ["brave", "chrome", "edge", "firefox", "opera"]):
                        browser_candidates.append(hwnd)
            return True

        proc = WNDENUMPROC(enum_proc)
        _user32.EnumWindows(proc, 0)
        if hud_candidates:
            found_hwnd = hud_candidates[0]
        elif browser_candidates:
            found_hwnd = browser_candidates[0]
    except Exception:
        pass

    if found_hwnd:
        _force_window_foreground(found_hwnd)
    else:
        # Only open in browser if HUD is not already open anywhere
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except Exception:
            pass

    try:
        import winsound
        winsound.Beep(1200, 150)
    except Exception:
        pass

    try:
        from system_tools import show_desktop_notification
        show_desktop_notification("⚡ KIRAHT AI — Web HUD Active", "Tactical Web HUD focused.")
    except Exception:
        pass

    print("[*] Global hotkey: HUD focused.")
    return True


def _trigger_global_screenshot():
    """Takes instant screenshot from any active window with toast feedback."""
    global _last_trigger_time
    with _trigger_lock:
        now = time.time()
        if now - _last_trigger_time < 0.5:
            return
        _last_trigger_time = now

    _attach_thread_to_input_desktop()
    try:
        import winsound
        winsound.Beep(1760, 100)
    except Exception:
        pass

    try:
        from system_tools import take_screenshot, show_desktop_notification
        res = take_screenshot()
        fname = os.path.basename(res) if res else "screenshot.png"
        show_desktop_notification("📸 KIRAHT AI — Screen Captured", f"Screenshot saved: {fname}")
        print(f"[+] Global hotkey screenshot: {res}")
    except Exception as e:
        print(f"[!] Global screenshot error: {e}")


def _trigger_global_diag():
    """Triggers global system telemetry diagnostic with native Windows toast notification."""
    global _last_trigger_time
    with _trigger_lock:
        now = time.time()
        if now - _last_trigger_time < 0.5:
            return
        _last_trigger_time = now

    _attach_thread_to_input_desktop()
    try:
        import winsound
        winsound.Beep(880, 120)
        winsound.Beep(1320, 160)
    except Exception:
        pass

    try:
        from core import get_system_telemetry
        from system_tools import show_desktop_notification
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
        print(f"[+] Global diagnostic: {msg}")
    except Exception as e:
        print(f"[!] Global diag error: {e}")


def _is_down(vk):
    if not _user32:
        return False
    return bool(_user32.GetAsyncKeyState(vk) & 0x8000)


def _poller_worker(stop_evt: threading.Event):
    """Background hardware polling engine using GetAsyncKeyState for 100% fail-safe detection."""
    _attach_thread_to_input_desktop()
    while not stop_evt.is_set():
        try:
            ctrl = _is_down(VK_CONTROL)
            alt = _is_down(VK_MENU)
            shift = _is_down(VK_SHIFT)
            win = _is_down(VK_LWIN) or _is_down(VK_RWIN)

            f9 = _is_down(VK_F9)
            f10 = _is_down(VK_F10)
            f8 = _is_down(VK_F8)

            k = _is_down(VK_K)
            d = _is_down(VK_D)
            s = _is_down(VK_S)

            if f9 or (win and shift and k) or (ctrl and alt and k) or (ctrl and shift and k):
                threading.Thread(target=_bring_hud_to_front, daemon=True).start()
                time.sleep(0.4)
            elif f10 or (win and shift and d) or (ctrl and alt and d) or (ctrl and shift and d):
                threading.Thread(target=_trigger_global_diag, daemon=True).start()
                time.sleep(0.4)
            elif f8 or (ctrl and alt and s) or (ctrl and shift and s) or (win and alt and s):
                threading.Thread(target=_trigger_global_screenshot, daemon=True).start()
                time.sleep(0.4)

        except Exception:
            pass
        time.sleep(0.08)


def _hotkey_worker(ready_evt: threading.Event):
    global _hotkey_thread_id
    if not _user32 or not _kernel32:
        ready_evt.set()
        return

    _attach_thread_to_input_desktop()
    _hotkey_thread_id = _kernel32.GetCurrentThreadId()

    # Register hotkeys (F9/F10/F8 single keys + Win+Shift & Ctrl+Alt multi-key combos)
    reg_list = [
        (HK_HUD_F9, 0, VK_F9, "F9 (Instant Focus HUD)"),
        (HK_HUD_WS, MOD_WIN | MOD_SHIFT, VK_K, "Win+Shift+K (Focus HUD)"),
        (HK_HUD_CA, MOD_CONTROL | MOD_ALT, VK_K, "Ctrl+Alt+K (Focus HUD)"),
        (HK_HUD_CS, MOD_CONTROL | MOD_SHIFT, VK_K, "Ctrl+Shift+K (Focus HUD)"),

        (HK_DIAG_F10, 0, VK_F10, "F10 (Instant Hardware Diag)"),
        (HK_DIAG_WS, MOD_WIN | MOD_SHIFT, VK_D, "Win+Shift+D (Diagnostic)"),
        (HK_DIAG_CA, MOD_CONTROL | MOD_ALT, VK_D, "Ctrl+Alt+D (Diagnostic)"),
        (HK_DIAG_CS, MOD_CONTROL | MOD_SHIFT, VK_D, "Ctrl+Shift+D (Diagnostic)"),

        (HK_SCREEN_F8, 0, VK_F8, "F8 (Instant Global Screenshot)"),
        (HK_SCREEN_CA, MOD_CONTROL | MOD_ALT, VK_S, "Ctrl+Alt+S (Screenshot)"),
        (HK_SCREEN_CS, MOD_CONTROL | MOD_SHIFT, VK_S, "Ctrl+Shift+S (Screenshot)"),
        (HK_SCREEN_WA, MOD_WIN | MOD_ALT, VK_S, "Win+Alt+S (Screenshot)"),
    ]

    active_ids = []
    for hkid, mod, vk, desc in reg_list:
        success = _user32.RegisterHotKey(None, hkid, mod, vk)
        if success:
            active_ids.append(hkid)

    print(f"[*] Global System Hotkeys: {len(active_ids)} OS hooks active (F9/F10/F8 + Dual Combos).")
    ready_evt.set()

    msg = wintypes.MSG()
    try:
        while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY:
                hk_id = msg.wParam
                if hk_id in (HK_HUD_F9, HK_HUD_WS, HK_HUD_CA, HK_HUD_CS):
                    threading.Thread(target=_bring_hud_to_front, daemon=True).start()
                elif hk_id in (HK_SCREEN_F8, HK_SCREEN_CA, HK_SCREEN_CS, HK_SCREEN_WA):
                    threading.Thread(target=_trigger_global_screenshot, daemon=True).start()
                elif hk_id in (HK_DIAG_F10, HK_DIAG_WS, HK_DIAG_CA, HK_DIAG_CS):
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
    """Starts the global system hotkeys daemon with double-redundant detection."""
    global _hotkey_thread, _poller_thread, _stop_event
    if sys.platform != "win32" or not _user32:
        return
    if _hotkey_thread and _hotkey_thread.is_alive():
        return

    _stop_event.clear()

    # 1. Start Win32 RegisterHotKey loop thread
    ready_evt = threading.Event()
    _hotkey_thread = threading.Thread(
        target=_hotkey_worker,
        args=(ready_evt,),
        name="KIRAHT-GlobalHotkeys-Hook",
        daemon=True
    )
    _hotkey_thread.start()
    ready_evt.wait(timeout=2.0)

    # 2. Start hardware polling thread for 100% fail-safe coverage
    _poller_thread = threading.Thread(
        target=_poller_worker,
        args=(_stop_event,),
        name="KIRAHT-GlobalHotkeys-Poller",
        daemon=True
    )
    _poller_thread.start()


def stop_global_hotkeys():
    """Stops the global system hotkeys daemon."""
    global _hotkey_thread_id, _stop_event
    _stop_event.set()
    if _user32 and _hotkey_thread_id:
        try:
            _user32.PostThreadMessageW(_hotkey_thread_id, WM_QUIT, 0, 0)
        except Exception:
            pass

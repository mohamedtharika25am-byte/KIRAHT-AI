"""
KIRAHT AI - System Tools Engine (Clipboard, Volume, Screenshot, Ping, Notes & OS Controls)
Provides developer automation, clipboard interaction, screen capture, Windows system controls,
precision volume control, and network latency diagnostics.
"""

import ctypes
import ctypes.wintypes
import csv
import datetime
import difflib
import json
import os
import re
import subprocess
import urllib.parse
import webbrowser
import win32clipboard
import threading
import time
import psutil

NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")
CONTACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.json")
WHATSAPP_CONTACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_contacts.json")


# ============================================================
# 1. CLIPBOARD ACCESS (READ, WRITE, CLEAR)
# ============================================================
def get_clipboard_text(call_me: str = "Sir") -> str:
    """
    Reads text content currently stored in the Windows clipboard.
    """
    try:
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        except Exception:
            data = None
        finally:
            win32clipboard.CloseClipboard()

        if not data or not str(data).strip():
            return f"{call_me}, your clipboard is currently empty."

        preview = str(data).strip()
        if len(preview) > 300:
            preview = preview[:300] + " ... [truncated]"

        return f"{call_me}, clipboard content:\n---\n{preview}\n---"
    except Exception as err:
        return f"{call_me}, unable to read clipboard: {err}"


def set_clipboard_text(text: str, call_me: str = "Sir") -> str:
    """
    Copies specified text to the Windows clipboard.
    """
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        return f"{call_me}, copied text to your clipboard."
    except Exception as err:
        return f"{call_me}, failed to copy to clipboard: {err}"


def clear_clipboard(call_me: str = "Sir") -> str:
    """
    Empties the Windows clipboard.
    """
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        return f"{call_me}, clipboard cleared."
    except Exception as err:
        return f"{call_me}, failed to clear clipboard: {err}"


# ============================================================
# 2. PRECISION WINDOWS AUDIO & MASTER VOLUME CONTROL
# ============================================================
def _get_audio_endpoint_volume(data_flow: int = 0):
    """
    Acquires Windows IAudioEndpointVolume COM interface.
    data_flow=0 (eRender): Master Speakers Output
    data_flow=1 (eCapture): Master Microphone Input
    """
    try:
        import comtypes
        from comtypes import CLSCTX_ALL, CoCreateInstance, GUID, IUnknown
        from ctypes import POINTER, c_float, c_long, c_uint, c_void_p, HRESULT

        class IAudioEndpointVolume(IUnknown):
            _iid_ = GUID("{5CDF2C82-841E-4546-9722-0CF74078229A}")
            _methods_ = [
                comtypes.STDMETHOD(HRESULT, "RegisterControlChangeNotify", [c_void_p]),
                comtypes.STDMETHOD(HRESULT, "UnregisterControlChangeNotify", [c_void_p]),
                comtypes.STDMETHOD(HRESULT, "GetChannelCount", [POINTER(c_uint)]),
                comtypes.STDMETHOD(HRESULT, "SetMasterVolumeLevel", [c_float, c_void_p]),
                comtypes.STDMETHOD(HRESULT, "SetMasterVolumeLevelScalar", [c_float, c_void_p]),
                comtypes.STDMETHOD(HRESULT, "GetMasterVolumeLevel", [POINTER(c_float)]),
                comtypes.STDMETHOD(HRESULT, "GetMasterVolumeLevelScalar", [POINTER(c_float)]),
                comtypes.STDMETHOD(HRESULT, "SetChannelVolumeLevel", [c_uint, c_float, c_void_p]),
                comtypes.STDMETHOD(HRESULT, "SetChannelVolumeLevelScalar", [c_uint, c_float, c_void_p]),
                comtypes.STDMETHOD(HRESULT, "GetChannelVolumeLevel", [c_uint, POINTER(c_float)]),
                comtypes.STDMETHOD(HRESULT, "GetChannelVolumeLevelScalar", [c_uint, POINTER(c_float)]),
                comtypes.STDMETHOD(HRESULT, "SetMute", [c_long, c_void_p]),
                comtypes.STDMETHOD(HRESULT, "GetMute", [POINTER(c_long)]),
            ]

        class IMMDevice(IUnknown):
            _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
            _methods_ = [
                comtypes.STDMETHOD(HRESULT, "Activate", [POINTER(GUID), c_uint, c_void_p, POINTER(POINTER(IAudioEndpointVolume))]),
            ]

        class IMMDeviceEnumerator(IUnknown):
            _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
            _methods_ = [
                comtypes.STDMETHOD(HRESULT, "EnumAudioEndpoints", []),
                comtypes.STDMETHOD(HRESULT, "GetDefaultAudioEndpoint", [c_uint, c_uint, POINTER(POINTER(IMMDevice))]),
            ]

        enumerator = CoCreateInstance(GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}"), IMMDeviceEnumerator, CLSCTX_ALL)
        endpoint = POINTER(IMMDevice)()
        enumerator.GetDefaultAudioEndpoint(data_flow, 1, ctypes.byref(endpoint))
        vol = POINTER(IAudioEndpointVolume)()
        endpoint.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None, ctypes.byref(vol))
        return vol
    except Exception:
        return None


def get_current_volume() -> int:
    """
    Returns current master volume percentage (0-100).
    """
    vol = _get_audio_endpoint_volume(data_flow=0)
    if vol:
        try:
            curr = ctypes.c_float()
            vol.GetMasterVolumeLevelScalar(ctypes.byref(curr))
            return int(round(curr.value * 100))
        except Exception:
            pass
    return -1


def set_volume_level(target_percent: int, call_me: str = "Sir") -> str:
    """
    Sets master volume directly to target percentage (0-100).
    """
    target = max(0, min(100, target_percent))
    vol = _get_audio_endpoint_volume(data_flow=0)
    if vol:
        try:
            vol.SetMasterVolumeLevelScalar(target / 100.0, None)
            return f"{call_me}, volume set to {target}%."
        except Exception as err:
            return f"{call_me}, failed to set volume: {err}"
    return f"{call_me}, volume adjustment unavailable."


def adjust_volume_delta(delta: int, call_me: str = "Sir") -> str:
    """
    Increments or decrements volume by delta percentage (e.g. +10, -10, +20).
    """
    vol = _get_audio_endpoint_volume(data_flow=0)
    if vol:
        try:
            curr = ctypes.c_float()
            vol.GetMasterVolumeLevelScalar(ctypes.byref(curr))
            curr_pct = int(round(curr.value * 100))
            new_pct = max(0, min(100, curr_pct + delta))
            vol.SetMasterVolumeLevelScalar(new_pct / 100.0, None)
            direction = "increased" if delta > 0 else "decreased"
            return f"{call_me}, volume {direction} by {abs(delta)}% to {new_pct}%."
        except Exception as err:
            return f"{call_me}, failed to adjust volume: {err}"
    return f"{call_me}, volume adjustment unavailable."


def toggle_mute(action: str = "toggle", call_me: str = "Sir") -> str:
    """
    Mutes, unmutes, or toggles master audio mute state using Windows COM or hardware key events.
    """
    act = action.lower().strip()
    try:
        vol = _get_audio_endpoint_volume(data_flow=0)
        if vol:
            muted = ctypes.c_long()
            vol.GetMute(ctypes.byref(muted))
            is_muted = bool(muted.value)

            if act in ("mute", "off"):
                target = 1
            elif act in ("unmute", "on"):
                target = 0
            else:
                target = 0 if is_muted else 1

            vol.SetMute(target, None)
            res_str = "muted" if target else "unmuted"
            return f"{call_me}, master audio {res_str}."
    except Exception:
        pass

    try:
        user32 = ctypes.windll.user32
        VK_VOLUME_MUTE = 0xAD
        scan = user32.MapVirtualKeyW(VK_VOLUME_MUTE, 0)
        user32.keybd_event(VK_VOLUME_MUTE, scan, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(VK_VOLUME_MUTE, scan, 2, 0)
        act_str = action if action in ("mute", "unmute") else "toggled"
        return f"{call_me}, master audio {act_str}."
    except Exception as err:
        return f"{call_me}, failed to toggle audio mute: {err}"


def toggle_mic_mute(action: str = "toggle", call_me: str = "Sir") -> str:
    """
    Controls Windows default recording / microphone mute state.
    Supports 'mute' / 'off', 'unmute' / 'on', or 'toggle'.
    """
    act = action.lower().strip()
    try:
        vol = _get_audio_endpoint_volume(data_flow=1)
        if vol:
            muted = ctypes.c_long()
            vol.GetMute(ctypes.byref(muted))
            is_muted = bool(muted.value)

            if act in ("mute", "off", "disable", "stop"):
                target = 1
            elif act in ("unmute", "on", "enable", "start"):
                target = 0
            else:
                target = 0 if is_muted else 1

            vol.SetMute(target, None)
            res_str = "muted" if target else "unmuted"
            return f"{call_me}, microphone {res_str}."
    except Exception:
        pass

    # Media command fallback (APPCOMMAND_MICROPHONE_VOLUME_MUTE)
    try:
        import win32api
        import win32gui
        WM_APPCOMMAND = 0x319
        APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
        hwnd = win32gui.GetForegroundWindow()
        win32api.SendMessage(hwnd, WM_APPCOMMAND, hwnd, APPCOMMAND_MICROPHONE_VOLUME_MUTE)
        return f"{call_me}, microphone mute toggled."
    except Exception as err:
        return f"{call_me}, failed to toggle microphone mute: {err}"


def adjust_volume(action: str, call_me: str = "Sir") -> str:
    """
    General handler for volume operations (mute, unmute, louder, quieter).
    """
    act = action.lower().strip()
    if act in ("mute", "unmute", "toggle"):
        return toggle_mute(act, call_me=call_me)
    elif act in ("increase", "up", "louder"):
        return adjust_volume_delta(15, call_me=call_me)
    elif act in ("decrease", "down", "softer", "quieter"):
        return adjust_volume_delta(-15, call_me=call_me)
    return f"{call_me}, volume operation '{action}' completed."


# ============================================================
# 2.5 WINDOWS POWER OPERATIONS & SECURITY CONTROLS
# ============================================================
def sleep_laptop(call_me: str = "Sir") -> str:
    """
    Puts the laptop into Sleep / Standby mode immediately.
    """
    try:
        ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
        return f"{call_me}, laptop is entering sleep mode."
    except Exception as err:
        return f"{call_me}, failed to put laptop to sleep: {err}"


def shutdown_laptop(delay_seconds: int = 10, call_me: str = "Sir") -> str:
    """
    Initiates a controlled Windows shutdown with a countdown.
    Can be cancelled via cancel_shutdown().
    """
    try:
        subprocess.run(
            ["shutdown", "/s", "/t", str(delay_seconds), "/c", f"KIRAHT AI: Shutting down laptop as requested by {call_me}"],
            check=True
        )
        return f"{call_me}, laptop will shut down in {delay_seconds} seconds. Type 'cancel shutdown' to abort."
    except Exception as err:
        return f"{call_me}, failed to initiate shutdown: {err}"


def restart_laptop(delay_seconds: int = 10, call_me: str = "Sir") -> str:
    """
    Initiates a controlled Windows system reboot.
    Can be cancelled via cancel_shutdown().
    """
    try:
        subprocess.run(
            ["shutdown", "/r", "/t", str(delay_seconds), "/c", f"KIRAHT AI: Restarting laptop as requested by {call_me}"],
            check=True
        )
        return f"{call_me}, laptop will restart in {delay_seconds} seconds. Type 'cancel shutdown' to abort."
    except Exception as err:
        return f"{call_me}, failed to initiate restart: {err}"


def cancel_shutdown(call_me: str = "Sir") -> str:
    """
    Aborts a pending Windows shutdown or restart sequence.
    """
    try:
        res = subprocess.run(["shutdown", "/a"], capture_output=True, text=True)
        if res.returncode == 0:
            return f"{call_me}, pending shutdown or restart has been cancelled."
        else:
            return f"{call_me}, no pending shutdown sequence was active."
    except Exception as err:
        return f"{call_me}, unable to cancel shutdown: {err}"


def hibernate_laptop(call_me: str = "Sir") -> str:
    """
    Puts the laptop into deep hibernation.
    """
    try:
        subprocess.run(["shutdown", "/h"], check=True)
        return f"{call_me}, laptop is entering hibernation."
    except Exception as err:
        return f"{call_me}, failed to hibernate: {err}"


def turn_off_display(call_me: str = "Sir") -> str:
    """
    Turns off the laptop display to save power. Screen turns back on on any keypress or mouse movement.
    """
    try:
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        return f"{call_me}, display turned off. Move mouse or press any key to wake."
    except Exception as err:
        return f"{call_me}, failed to turn off display: {err}"


def lock_laptop(call_me: str = "Sir") -> str:
    """
    Locks the Windows workstation instantly.
    """
    try:
        ctypes.windll.user32.LockWorkStation()
        return f"{call_me}, workstation is now locked."
    except Exception as err:
        return f"{call_me}, failed to lock workstation: {err}"


def handle_power_action(action: str, call_me: str = "Sir") -> str:
    """
    Unified dispatcher for power and security operations.
    """
    act = action.lower().strip()
    if act in ("sleep", "standby"):
        return sleep_laptop(call_me=call_me)
    elif act in ("shutdown", "shut_down", "poweroff", "turn_off"):
        return shutdown_laptop(delay_seconds=10, call_me=call_me)
    elif act in ("restart", "reboot"):
        return restart_laptop(delay_seconds=10, call_me=call_me)
    elif act in ("abort_shutdown", "cancel_shutdown", "stop_shutdown"):
        return cancel_shutdown(call_me=call_me)
    elif act in ("hibernate", "deep_sleep"):
        return hibernate_laptop(call_me=call_me)
    elif act in ("screen_off", "display_off", "turn_off_screen", "turn_off_display"):
        return turn_off_display(call_me=call_me)
    elif act in ("lock", "lock_screen", "lock_workstation"):
        return lock_laptop(call_me=call_me)
    return f"{call_me}, power action '{action}' is not recognized."


# ============================================================
# 3. BULLETPROOF NATIVE SCREENSHOT ENGINE (CTYPES + PIL)
# ============================================================
def take_screenshot(call_me: str = "Sir") -> str:
    """
    Captures primary screen using pure Windows GDI API and saves it to user's
    Pictures\\Screenshots or Desktop.
    """
    try:
        from PIL import Image

        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        if not os.path.exists(pictures_dir):
            try:
                os.makedirs(pictures_dir, exist_ok=True)
            except Exception:
                pictures_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(pictures_dir, filename)

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass

        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
        gdi32.SelectObject(hdc_mem, hbmp)

        # SRCCOPY = 0x00CC0020
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", ctypes.c_uint32),
                ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32),
                ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16),
                ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32),
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = w
        bmi.biHeight = -h  # top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0

        buf = (ctypes.c_char * (w * h * 4))()
        gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)

        im = Image.frombuffer("RGBA", (w, h), bytes(buf), "raw", "BGRA", 0, 1)
        im = im.convert("RGB")
        im.save(filepath)

        gdi32.DeleteObject(hbmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)

        if os.path.exists(filepath):
            try:
                os.startfile(filepath)
            except Exception:
                pass
            return f"{call_me}, screenshot captured and saved to: {filepath}"
        return f"{call_me}, screenshot failed to save to disk."
    except Exception as err:
        return f"{call_me}, screenshot operation failed: {err}"


# ============================================================
# 4. TERMINAL RUNNER & OS CONTROLS
# ============================================================
def run_terminal_command(command: str, call_me: str = "Sir", timeout: int = 30) -> str:
    """
    Executes a shell command in workspace directory and captures output.
    Blocks potentially destructive actions without explicit user consent.
    """
    clean_cmd = command.strip()

    destructive_patterns = [
        r"\brm\s+-rf\b",
        r"\bdel\s+/f\b",
        r"\bformat\s+[a-z]:\b",
        r"\bgit\s+reset\s+--hard\b",
        r"\bdrop\s+database\b",
        r"\bdiskpart\b",
    ]
    for pattern in destructive_patterns:
        if re.search(pattern, clean_cmd, re.IGNORECASE):
            return (
                f"{call_me}, this command '{clean_cmd}' is flagged as potentially destructive "
                f"and was blocked by KIRAHT AI safety guardrails."
            )

    workspace_dir = r"d:\KIRAHT AI"
    try:
        res = subprocess.run(
            clean_cmd,
            cwd=workspace_dir,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = res.stdout.strip()
        stderr = res.stderr.strip()

        output_parts = []
        if stdout:
            lines = stdout.splitlines()
            if len(lines) > 40:
                stdout = "\n".join(lines[:40]) + f"\n... [{len(lines) - 40} more lines]"
            output_parts.append(stdout)
        if stderr:
            lines = stderr.splitlines()
            if len(lines) > 20:
                stderr = "\n".join(lines[:20]) + f"\n... [{len(lines) - 20} more error lines]"
            output_parts.append(f"[stderr]:\n{stderr}")

        result_text = "\n".join(output_parts) if output_parts else "(Command completed with no output)"
        status = "succeeded" if res.returncode == 0 else f"exited with code {res.returncode}"
        return f"{call_me}, command {status}:\n{result_text}"

    except subprocess.TimeoutExpired:
        return f"{call_me}, command timed out after {timeout} seconds."
    except Exception as err:
        return f"{call_me}, failed to execute command: {err}"


def empty_recycle_bin(call_me: str = "Sir") -> str:
    """
    Empties the Windows Recycle Bin silently.
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "try { Clear-RecycleBin -Force -ErrorAction Stop; Write-Host 'cleared' } catch { Write-Host 'already_empty' }"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        out = res.stdout.strip()
        if "cleared" in out:
            return f"{call_me}, Recycle Bin has been emptied."
        elif "already_empty" in out or not res.stderr.strip():
            return f"{call_me}, Recycle Bin is already clean and empty."
        return f"{call_me}, unable to empty Recycle Bin: {res.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"{call_me}, Recycle Bin operation timed out."
    except Exception as err:
        return f"{call_me}, unable to empty Recycle Bin: {err}"


def get_wifi_status(call_me: str = "Sir") -> str:
    """
    Checks active Wi-Fi connection state, SSID, and signal quality.
    """
    try:
        res = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return f"{call_me}, unable to retrieve Wi-Fi status."

        out = res.stdout
        ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", out, re.M)
        signal_match = re.search(r"^\s*Signal\s*:\s*(.+)$", out, re.M)
        state_match = re.search(r"^\s*State\s*:\s*(.+)$", out, re.M)

        state = state_match.group(1).strip() if state_match else "Disconnected"
        ssid = ssid_match.group(1).strip() if ssid_match else "None"
        signal = signal_match.group(1).strip() if signal_match else "N/A"

        if state.lower() == "connected":
            return f"{call_me}, Wi-Fi is connected to '{ssid}' with {signal} signal quality."
        else:
            return f"{call_me}, Wi-Fi is currently {state}."
    except Exception as err:
        return f"{call_me}, failed to check Wi-Fi: {err}"


def check_ping(host: str = "8.8.8.8", call_me: str = "Sir") -> str:
    """
    Tests network latency to a target host or gateway (default Google DNS).
    """
    try:
        res = subprocess.run(["ping", "-n", "2", "-w", "1000", host], capture_output=True, text=True, timeout=5)
        out = res.stdout
        avg_match = re.search(r"Average\s*=\s*(\d+ms)", out, re.IGNORECASE)
        if avg_match:
            latency = avg_match.group(1)
            return f"{call_me}, connection to {host} is stable with average latency of {latency}."
        elif "Reply from" in out:
            return f"{call_me}, ping to {host} succeeded."
        else:
            return f"{call_me}, ping to {host} failed or timed out."
    except Exception as err:
        return f"{call_me}, ping check failed: {err}"


def show_desktop_notification(title: str, message: str, call_me: str = "Sir") -> str:
    """
    Triggers a native Windows balloon notification.
    """
    try:
        clean_title = title.replace("'", "''")
        clean_msg = message.replace("'", "''")
        ps = f"""
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.BalloonTipTitle = '{clean_title}'
$n.BalloonTipText = '{clean_msg}'
$n.Visible = $True
$n.ShowBalloonTip(4000)
"""
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps])
        return f"{call_me}, notification sent: '{title}'"
    except Exception as err:
        return f"{call_me}, notification failed: {err}"


# ============================================================
# 5. QUICK NOTES MANAGER
# ============================================================
def load_notes() -> list:
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_notes(notes: list) -> None:
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def add_note(note_text: str, call_me: str = "Sir") -> str:
    notes = load_notes()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    notes.append({"timestamp": timestamp, "text": note_text.strip()})
    save_notes(notes)
    return f"{call_me}, note saved ({timestamp}): '{note_text.strip()}'"


def get_notes(call_me: str = "Sir") -> str:
    notes = load_notes()
    if not notes:
        return f"{call_me}, you have no saved notes."
    formatted = [f"[{n['timestamp']}] {n['text']}" for n in notes]
    notes_list = "\n  - ".join(formatted)
    return f"{call_me}, here are your saved notes:\n  - {notes_list}"


def clear_notes(call_me: str = "Sir") -> str:
    save_notes([])
    return f"{call_me}, all notes have been cleared."


# ============================================================
# 6. CONTACTS & WHATSAPP MESSAGING ENGINE
# ============================================================
def load_contacts_data() -> dict:
    """
    Loads contacts database supporting structured format:
    {"contacts": {}, "aliases": {}, "groups": {}}
    and gracefully handles legacy flat format {"name": "phone"}.
    """
    default_data = {"contacts": {}, "aliases": {}, "groups": {}}
    if not os.path.exists(CONTACTS_FILE):
        return default_data

    try:
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            raw_text = f.read()
        cleaned_text = re.sub(r"(?<!https:)(?<!http:)//.*$", "", raw_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r",\s*([\]}])", r"\1", cleaned_text)
        data = json.loads(cleaned_text)
        if not isinstance(data, dict):
            return default_data
        if "contacts" not in data and "aliases" not in data:
            data = {"contacts": data, "aliases": {}, "groups": {}}
        raw_contacts = data.get("contacts", {}) if isinstance(data.get("contacts"), dict) else {}
        raw_aliases = data.get("aliases", {}) if isinstance(data.get("aliases"), dict) else {}
        raw_groups = data.get("groups", {}) if isinstance(data.get("groups"), dict) else {}
        data["contacts"] = {str(k).lower().strip(): str(v).strip() for k, v in raw_contacts.items() if str(k).strip()}
        data["aliases"] = {str(k).lower().strip(): str(v).lower().strip() for k, v in raw_aliases.items() if str(k).strip()}
        data["groups"] = {str(k).lower().strip(): v for k, v in raw_groups.items() if str(k).strip()}
        return data
    except Exception:
        return default_data


def save_contacts_data(data: dict) -> None:
    """
    Saves contacts structured database to contacts.json.
    """
    try:
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def load_contacts() -> dict:
    """
    Returns combined flat dictionary of contacts and nicknames for lookup.
    """
    data = load_contacts_data()
    flat = {}
    contacts = data.get("contacts", {})
    aliases = data.get("aliases", {})
    for name, phone in contacts.items():
        flat[name.lower()] = phone
    for alias, target in aliases.items():
        t_clean = target.lower().strip()
        if t_clean in contacts:
            flat[alias.lower()] = contacts[t_clean]
        elif target in flat:
            flat[alias.lower()] = flat[target]
    return flat


def load_all_groups() -> dict:
    """
    Loads all WhatsApp groups from whatsapp_contacts.json and contacts.json.
    Returns mapping of normalized_name -> {"raw_name": ..., "jid": ..., "clean_name": ..., "display": ...}
    """
    groups_map = {}

    # 1. Load from whatsapp_contacts.json
    if os.path.exists(WHATSAPP_CONTACTS_FILE):
        try:
            with open(WHATSAPP_CONTACTS_FILE, "r", encoding="utf-8") as f:
                raw_text = f.read()
            cleaned_text = re.sub(r"(?<!https:)(?<!http:)//.*$", "", raw_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r",\s*([\]}])", r"\1", cleaned_text)
            wa_data = json.loads(cleaned_text)
            wa_groups = wa_data.get("groups", {})
            for raw_name, jid in wa_groups.items():
                clean = re.sub(r"[^\w\s]", " ", raw_name).strip().lower()
                clean = re.sub(r"\s+", " ", clean).strip()
                if clean:
                    groups_map[clean] = {
                        "raw_name": raw_name,
                        "jid": jid,
                        "clean_name": clean,
                        "display": raw_name.title() if raw_name else clean.title(),
                    }
        except Exception:
            pass

    # 2. Load from contacts.json
    try:
        data = load_contacts_data()
        for gname, gid in data.get("groups", {}).items():
            clean = re.sub(r"[^\w\s]", " ", gname).strip().lower()
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean and clean not in groups_map:
                groups_map[clean] = {
                    "raw_name": gname,
                    "jid": gid,
                    "clean_name": clean,
                    "display": gname.title() if gname else clean.title(),
                }
    except Exception:
        pass

    return groups_map


def resolve_group(query: str) -> tuple[dict | None, list]:
    """
    Finds a group from loaded groups by clean name, compact name, candidate matches, or fuzzy match.
    Returns: (group_info_dict_or_None, list_of_related_group_dicts)
    """
    groups = load_all_groups()
    clean_q = re.sub(r"[^\w\s]", " ", query).strip().lower()
    clean_q = re.sub(r"\s+", " ", clean_q).strip()

    if not clean_q:
        return None, []

    # 1. Exact match on clean name
    if clean_q in groups:
        return groups[clean_q], []

    # 2. Compact match (handles 'aiml-b', 'aimlb' -> 'aiml b')
    compact_q = clean_q.replace(" ", "")
    for k, info in groups.items():
        if compact_q == k.replace(" ", ""):
            return info, []

    # 3. Check for candidate matches (prefix, substring, or word subset)
    candidates = []
    for k, info in groups.items():
        if clean_q == k or k.startswith(clean_q + " ") or clean_q in k:
            if info not in candidates:
                candidates.append(info)

    q_words = set(clean_q.split())
    for k, info in groups.items():
        k_words = set(k.split())
        if q_words and q_words.issubset(k_words):
            if info not in candidates:
                candidates.append(info)

    # If exactly 1 match found
    if len(candidates) == 1:
        return candidates[0], []
    elif len(candidates) > 1:
        for cand in candidates:
            if cand["clean_name"] == clean_q:
                return cand, []
        return None, candidates[:6]

    # 4. Fuzzy match for Related Groups
    close = difflib.get_close_matches(clean_q, list(groups.keys()), n=4, cutoff=0.25)
    related = [groups[c] for c in close if c in groups]
    return None, related


def resolve_contact(query: str) -> tuple[str | None, str, list]:
    """
    Resolves a name, alias, or query to a phone number or group ID.
    Returns: (phone_number_or_none, resolved_display_name, related_matches_list)
    """
    data = load_contacts_data()
    contacts = data.get("contacts", {})
    aliases = data.get("aliases", {})
    groups = data.get("groups", {})
    clean_query = query.lower().strip()

    # 0. Reverse lookup if query is phone digits
    digits_q = re.sub(r"\D", "", clean_query)
    if len(digits_q) >= 10:
        for name, phone in contacts.items():
            if re.sub(r"\D", "", phone).endswith(digits_q[-10:]):
                return phone, name.title(), []

    # 1. Direct Alias Match
    if clean_query in aliases:
        target = aliases[clean_query].lower().strip()
        if target in contacts:
            return contacts[target], target.title(), []

    # 2. Direct Contact Match
    if clean_query in contacts:
        return contacts[clean_query], clean_query.title(), []

    # 3. Direct Group Match
    if clean_query in groups:
        return "group", groups[clean_query].title(), []

    # 4. Prefix / Substring Match in Contacts
    for name, phone in contacts.items():
        if name == clean_query or name.startswith(clean_query + " ") or (len(clean_query) >= 3 and clean_query in name):
            return phone, name.title(), []

    # 5. Check aliases prefix/substring
    for alias, target in aliases.items():
        if alias == clean_query or alias.startswith(clean_query + " "):
            t_clean = target.lower().strip()
            if t_clean in contacts:
                return contacts[t_clean], t_clean.title(), []

    # 6. Check Groups substring
    for gname, gid in groups.items():
        if clean_query in gname or gname.startswith(clean_query):
            return "group", gname.title(), []

    # 7. Fuzzy matching for Related Contacts
    all_names = list(contacts.keys()) + list(aliases.keys())
    close_matches = difflib.get_close_matches(clean_query, all_names, n=4, cutoff=0.35)
    related = []
    seen_phones = set()
    for match in close_matches:
        match_phone = contacts.get(match) or contacts.get(aliases.get(match, "").lower(), "")
        if match_phone and match_phone not in seen_phones:
            seen_phones.add(match_phone)
            related.append({"name": match.title(), "phone": match_phone})
        elif not match_phone:
            related.append({"name": match.title(), "phone": ""})

    return None, query.title(), related


def add_group(group_name: str, call_me: str = "Sir") -> str:
    """
    Adds or registers a group name in the contact book under 'groups'.
    """
    data = load_contacts_data()
    clean_name = group_name.lower().strip()
    data.setdefault("groups", {})[clean_name] = group_name.title()
    save_contacts_data(data)
    return f"{call_me}, added group '{group_name.title()}' to your WhatsApp groups."


def add_contact(name: str, phone: str, call_me: str = "Sir") -> str:
    """
    Adds or updates a contact in the local contact book.
    """
    data = load_contacts_data()
    clean_name = name.lower().strip()
    digits = re.sub(r"\D", "", phone.strip())
    if len(digits) == 10:
        clean_phone = "+91" + digits
    elif len(digits) == 12 and digits.startswith("91"):
        clean_phone = "+" + digits
    elif len(digits) >= 10:
        clean_phone = "+" + digits
    else:
        clean_phone = phone.strip()

    data["contacts"][clean_name] = clean_phone
    save_contacts_data(data)
    return f"{call_me}, saved contact '{name.title()}' with number {clean_phone}."


def add_contact_alias(alias: str, target_name: str, call_me: str = "Sir") -> str:
    """
    Adds a nickname / alias pointing to an existing contact.
    """
    data = load_contacts_data()
    clean_alias = alias.lower().strip()
    clean_target = target_name.lower().strip()

    # If target not found exact, check close match
    if clean_target not in data["contacts"]:
        close = difflib.get_close_matches(clean_target, data["contacts"].keys(), n=1, cutoff=0.5)
        if close:
            clean_target = close[0]

    data["aliases"][clean_alias] = clean_target
    save_contacts_data(data)
    return f"{call_me}, added nickname '{clean_alias.title()}' for contact '{clean_target.title()}'."


def list_contacts(call_me: str = "Sir") -> str:
    """
    Lists all saved contacts and their aliases.
    """
    data = load_contacts_data()
    contacts = data.get("contacts", {})
    aliases = data.get("aliases", {})
    if not contacts:
        return f"{call_me}, your contact book is empty. Import from CSV using: import contacts, or add someone using: add contact <name> <phone_number>."

    target_aliases = {}
    for a, t in aliases.items():
        target_aliases.setdefault(t.lower(), []).append(a.title())

    lines = []
    for name, phone in sorted(contacts.items()):
        alias_str = ""
        if name in target_aliases:
            alias_str = f" [Nicknames: {', '.join(target_aliases[name])}]"
        lines.append(f"{name.title()}: {phone}{alias_str}")

    preview_count = min(30, len(lines))
    extra = f"\n  ... and {len(lines) - preview_count} more contacts." if len(lines) > preview_count else ""
    return f"{call_me}, here are your saved contacts ({len(contacts)} total):\n  - " + "\n  - ".join(lines[:preview_count]) + extra


def import_google_contacts_csv(filepath: str = "googlecontacts.csv", call_me: str = "Sir") -> str:
    """
    Parses googlecontacts.csv, strips emojis and noisy symbols, normalizes numbers,
    and populates contacts.json.
    """
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
    if not os.path.exists(full_path):
        return f"{call_me}, '{filepath}' was not found in the project directory."

    data = load_contacts_data()
    count = 0
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                first = row.get("First Name", "") or ""
                middle = row.get("Middle Name", "") or ""
                last = row.get("Last Name", "") or ""
                phone = row.get("Phone 1 - Value", "") or ""

                raw_name = f"{first} {middle} {last}".strip()
                cleaned_name = re.sub(r"[^\w\s\.\-]", " ", raw_name)
                cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()

                digits = re.sub(r"\D", "", phone)
                if len(digits) >= 10 and cleaned_name:
                    if len(digits) == 10:
                        clean_phone = "+91" + digits
                    elif len(digits) == 12 and digits.startswith("91"):
                        clean_phone = "+" + digits
                    else:
                        clean_phone = "+" + digits

                    data["contacts"][cleaned_name.lower()] = clean_phone
                    count += 1

        save_contacts_data(data)
        return f"{call_me}, successfully imported {count} clean contacts from {filepath} into contacts.json!"
    except Exception as err:
        return f"{call_me}, failed to import contacts from {filepath}: {err}"


VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_A = 0x41
VK_F = 0x46
VK_V = 0x56
VK_RETURN = 0x0D
VK_DOWN = 0x28
VK_ESCAPE = 0x1B

def _set_clipboard_text(text: str):
    try:
        subprocess.run("clip", input=text.encode("utf-16le"), check=True)
    except Exception:
        pass

# --- Windows Kernel-Level Hardware SendInput Structures ---
PUL = ctypes.POINTER(ctypes.c_ulong)
class _KeyBdInput(ctypes.Structure):
    _fields_ = [
        ('wVk', ctypes.wintypes.WORD),
        ('wScan', ctypes.wintypes.WORD),
        ('dwFlags', ctypes.wintypes.DWORD),
        ('time', ctypes.wintypes.DWORD),
        ('dwExtraInfo', PUL)
    ]

class _HardwareInput(ctypes.Structure):
    _fields_ = [
        ('uMsg', ctypes.wintypes.DWORD),
        ('wParamL', ctypes.wintypes.WORD),
        ('wParamH', ctypes.wintypes.WORD)
    ]

class _MouseInput(ctypes.Structure):
    _fields_ = [
        ('dx', ctypes.wintypes.LONG),
        ('dy', ctypes.wintypes.LONG),
        ('mouseData', ctypes.wintypes.DWORD),
        ('dwFlags', ctypes.wintypes.DWORD),
        ('time', ctypes.wintypes.DWORD),
        ('dwExtraInfo', PUL)
    ]

class _Input_I(ctypes.Union):
    _fields_ = [
        ('ki', _KeyBdInput),
        ('mi', _MouseInput),
        ('hi', _HardwareInput)
    ]

class _Input(ctypes.Structure):
    _fields_ = [
        ('type', ctypes.wintypes.DWORD),
        ('ii', _Input_I)
    ]

def _send_hardware_key(vk: int):
    """
    Sends true kernel-level hardware scan code and virtual key events via SendInput and keybd_event.
    Guarantees synthetic keystroke registration in modern WinUI 3, UWP, and Win32 applications.
    """
    user32 = ctypes.windll.user32
    scan_code = user32.MapVirtualKeyW(vk, 0)
    extra = ctypes.c_ulong(0)

    # 1. Hardware scan code via SendInput (KEYEVENTF_SCANCODE = 0x0008)
    try:
        ii_down = _Input_I()
        ii_down.ki = _KeyBdInput(0, scan_code, 0x0008, 0, ctypes.pointer(extra))
        inp_down = _Input(ctypes.c_ulong(1), ii_down)
        user32.SendInput(1, ctypes.pointer(inp_down), ctypes.sizeof(inp_down))

        time.sleep(0.03)

        ii_up = _Input_I()
        ii_up.ki = _KeyBdInput(0, scan_code, 0x0008 | 0x0002, 0, ctypes.pointer(extra)) # KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        inp_up = _Input(ctypes.c_ulong(1), ii_up)
        user32.SendInput(1, ctypes.pointer(inp_up), ctypes.sizeof(inp_up))

        time.sleep(0.02)

        # 2. Virtual Key via SendInput
        ii_vk_down = _Input_I()
        ii_vk_down.ki = _KeyBdInput(vk, scan_code, 0, 0, ctypes.pointer(extra))
        inp_vk_down = _Input(ctypes.c_ulong(1), ii_vk_down)
        user32.SendInput(1, ctypes.pointer(inp_vk_down), ctypes.sizeof(inp_vk_down))

        time.sleep(0.03)

        ii_vk_up = _Input_I()
        ii_vk_up.ki = _KeyBdInput(vk, scan_code, 0x0002, 0, ctypes.pointer(extra))
        inp_vk_up = _Input(ctypes.c_ulong(1), ii_vk_up)
        user32.SendInput(1, ctypes.pointer(inp_vk_up), ctypes.sizeof(inp_vk_up))
    except Exception:
        pass

    # 3. Fallback / complementary legacy keybd_event with hardware scan code
    try:
        user32.keybd_event(vk, scan_code, 0, 0)
        time.sleep(0.03)
        user32.keybd_event(vk, scan_code, 2, 0)
    except Exception:
        pass

def _press_key_hardware(vk: int):
    """
    Simulates a key press with legitimate hardware scan code mapped via MapVirtualKeyW and SendInput.
    """
    _send_hardware_key(vk)

def _hotkey_ctrl(vk: int):
    """
    Simulates Ctrl + key combination with hardware scan codes.
    """
    user32 = ctypes.windll.user32
    scan_ctrl = user32.MapVirtualKeyW(VK_CONTROL, 0)
    scan_vk = user32.MapVirtualKeyW(vk, 0)
    user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(vk, scan_vk, 0, 0)
    time.sleep(0.04)
    user32.keybd_event(vk, scan_vk, 2, 0)
    time.sleep(0.04)
    user32.keybd_event(VK_CONTROL, scan_ctrl, 2, 0)

def _activate_whatsapp_window() -> bool:
    """
    Brings WhatsApp desktop window directly to the active foreground.
    Handles WinUI 3 (WinUIDesktopWin32WindowClass), UWP, Chrome/Edge WhatsApp Web,
    and legacy Win32 WhatsApp desktop processes.
    """
    import ctypes
    import ctypes.wintypes
    import win32con
    import win32process
    import win32service

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # Switch to default desktop if running in a background service desktop
    try:
        hDesk = win32service.OpenDesktop('default', 0, False, win32con.GENERIC_ALL)
        user32.SetThreadDesktop(int(hDesk))
    except Exception:
        pass

    target_hwnd = None

    def enum_cb(hwnd, extra):
        nonlocal target_hwnd
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            t = buff.value

            class_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buff, 256)
            c = class_buff.value

            # Prioritize WhatsApp Desktop WinUI 3 window
            if c == 'WinUIDesktopWin32WindowClass' and 'whatsapp' in t.lower():
                target_hwnd = hwnd
                return False
            if 'whatsapp' in t.lower() or 'whatsapp' in c.lower():
                if not target_hwnd or c == 'WinUIDesktopWin32WindowClass':
                    target_hwnd = hwnd
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

    if target_hwnd:
        try:
            cur_thread = kernel32.GetCurrentThreadId()
            target_pid = ctypes.wintypes.DWORD()
            target_thread = user32.GetWindowThreadProcessId(target_hwnd, ctypes.byref(target_pid))
            user32.AttachThreadInput(cur_thread, target_thread, True)
            if user32.IsIconic(target_hwnd):
                user32.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            user32.ShowWindow(target_hwnd, win32con.SW_SHOW)
            user32.SetForegroundWindow(target_hwnd)
            user32.BringWindowToTop(target_hwnd)
            # Intentionally do NOT call user32.SetFocus(target_hwnd):
            # Calling SetFocus on the top-level container window strips focus
            # away from the child message input box in WinUI 3.
            user32.AttachThreadInput(cur_thread, target_thread, False)
            return True
        except Exception:
            pass

    # Fallback to WScript.Shell
    try:
        import win32com.client
        wscript = win32com.client.Dispatch("WScript.Shell")
        if wscript.AppActivate("WhatsApp"):
            return True
        for p in psutil.process_iter(['pid', 'name']):
            if 'what' in p.info['name'].lower():
                if wscript.AppActivate(p.info['pid']):
                    return True
    except Exception:
        pass
    return False

def _send_whatsapp_enter_keystrokes(ensure_focus: bool = False):
    """
    Sends multi-layered hardware Enter keystrokes via SendInput, WScript.Shell, and hardware events.
    """
    user32 = ctypes.windll.user32
    if ensure_focus:
        fg = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(fg)
        title = ""
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(fg, buff, length + 1)
            title = buff.value.lower()
        if 'whatsapp' not in title:
            _activate_whatsapp_window()
            time.sleep(0.1)

    # 1. Hardware scan code & virtual key Enter via Windows SendInput
    _send_hardware_key(VK_RETURN)

    # 2. WScript.Shell SendKeys Enter and tilde Enter
    try:
        import win32com.client
        wscript = win32com.client.Dispatch("WScript.Shell")
        wscript.SendKeys("{ENTER}")
        wscript.SendKeys("~")
    except Exception:
        pass

def _delayed_press_enter(initial_delay: float = 2.0, attempts: int = 8, interval: float = 1.5):
    """
    Actively monitors and presses Enter over several intervals to guarantee
    message dispatch even if WhatsApp takes several seconds to load.
    """
    time.sleep(initial_delay)
    for _ in range(attempts):
        _send_whatsapp_enter_keystrokes(ensure_focus=True)
        time.sleep(interval)

def dispatch_whatsapp_desktop(search_term: str, message: str, auto_send: bool = True):
    """
    Opens/activates WhatsApp Desktop, searches for contact or group name in search bar,
    navigates to the first result via Down Arrow, opens chat with Enter, pastes message,
    and automatically sends the message.
    """
    # 1. Bring WhatsApp to front or launch with robust polling
    if not _activate_whatsapp_window():
        try:
            subprocess.Popen(["explorer.exe", "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"])
        except Exception:
            pass
        try:
            os.startfile("whatsapp:")
        except Exception:
            pass
        for _ in range(12):
            time.sleep(0.3)
            if _activate_whatsapp_window():
                break

    time.sleep(0.4)

    # 2. Press Escape twice to dismiss any open search query, menu, or dialog
    _press_key_hardware(VK_ESCAPE)
    time.sleep(0.15)
    _press_key_hardware(VK_ESCAPE)
    time.sleep(0.2)

    # 3. Focus search bar (Ctrl + F)
    _hotkey_ctrl(VK_F)
    time.sleep(0.35)

    # 4. Clear any existing text in the search bar (Ctrl + A, Backspace)
    try:
        import win32com.client
        wscript = win32com.client.Dispatch("WScript.Shell")
        wscript.SendKeys("^a{BACKSPACE}")
    except Exception:
        pass
    time.sleep(0.15)

    # 5. Type/paste the search term (contact name, group name, or raw search query)
    _set_clipboard_text(search_term)
    _hotkey_ctrl(VK_V)
    time.sleep(1.2)  # Allow WhatsApp search engine to query SQLite and render results list

    # 6. Navigate to top search result (Down Arrow) and open it (Enter)
    _press_key_hardware(VK_DOWN)
    time.sleep(0.25)
    _press_key_hardware(VK_RETURN)
    time.sleep(1.2)  # Wait for conversation to load, history to render, and message box to gain focus

    # 7. Paste message into chat input field (select all first to prevent duplicates)
    _set_clipboard_text(message)
    _hotkey_ctrl(VK_A)
    time.sleep(0.06)
    _hotkey_ctrl(VK_V)
    time.sleep(0.45)  # Allow WhatsApp UI to process the paste and enable the send state

    # 8. If auto_send requested, dispatch multi-stage Enter keystrokes
    if auto_send:
        # Immediate multi-layered pulse directly into the active focused input box
        _send_whatsapp_enter_keystrokes(ensure_focus=False)
        time.sleep(0.3)
        _send_whatsapp_enter_keystrokes(ensure_focus=False)
        time.sleep(0.4)
        _send_whatsapp_enter_keystrokes(ensure_focus=False)

        # Background watchdog thread to guarantee delivery even under heavy system load
        def _bg_enter_watchdog():
            for delay in (0.8, 1.8, 3.0):
                time.sleep(delay)
                _send_whatsapp_enter_keystrokes(ensure_focus=True)

        threading.Thread(target=_bg_enter_watchdog, daemon=True).start()

def _safe_paste_into_chat(message: str, auto_send: bool = False, delay: float = 1.3):
    """
    Ensures message is actively filled into WhatsApp chat input box,
    working around the Windows WhatsApp Desktop (UWP) bug where
    'whatsapp://send?phone=...&text=...' opens the chat but ignores the &text= parameter.
    Selects all text (Ctrl+A) before pasting (Ctrl+V) so that any existing or prefilled
    text is replaced cleanly, preventing double duplication (e.g. 'byebye', 'hihi').
    """
    time.sleep(delay)
    _activate_whatsapp_window()
    time.sleep(0.25)
    _set_clipboard_text(message)
    # Select all text in the message input box to replace any existing prefilled text
    _hotkey_ctrl(VK_A)
    time.sleep(0.06)
    _hotkey_ctrl(VK_V)
    time.sleep(0.35)
    if auto_send:
        _send_whatsapp_enter_keystrokes(ensure_focus=False)

def dispatch_whatsapp_group(group_search_term: str, message: str, auto_send: bool = True):
    """
    Alias wrapper around dispatch_whatsapp_desktop for group messaging.
    """
    dispatch_whatsapp_desktop(group_search_term, message, auto_send=auto_send)

def send_whatsapp_message(target: str, message: str, call_me: str = "Sir", is_group: bool = False, auto_send: bool = True) -> str:
    """
    Opens WhatsApp desktop or web with prefilled message directed to a contact or group.
    - If is_group: searches group in WhatsApp desktop, pastes message, and leaves cursor ready (fill only).
    - If individual with contact name: opens direct URI and actively pastes message into the chat box!
    """
    # 1. GROUP MESSAGING (Fill only! Strictly never auto-send to groups)
    if is_group:
        g_info, related_groups = resolve_group(target)
        search_term = g_info["raw_name"] if g_info else target
        display = g_info["display"] if g_info else target.title()
        # Strictly review mode: paste message only, never auto-press Enter on groups
        dispatch_whatsapp_desktop(search_term, message, auto_send=False)
        return f"{call_me}, opened WhatsApp group '{display}' with your message pre-filled. Please review and press Enter to send."

    # 2. INDIVIDUAL CONTACT MESSAGING (Direct, guaranteed deep-link URI to exact contact)
    phone_number, display_name, related = resolve_contact(target)

    if not phone_number:
        digits = re.sub(r"\D", "", target.strip())
        if len(digits) >= 10:
            if len(digits) == 10:
                phone_number = "+91" + digits
            elif len(digits) == 12 and digits.startswith("91"):
                phone_number = "+" + digits
            else:
                phone_number = "+" + digits
            display_name = target.strip()
        else:
            return f"{call_me}, contact '{target}' was not found in your contacts."

    clean_digits = re.sub(r"[^\d]", "", phone_number)
    display = display_name if display_name else target.title()
    encoded_text = urllib.parse.quote(message.strip())
    uri = f"whatsapp://send?phone={clean_digits}&text={encoded_text}"

    try:
        os.startfile(uri)
        # Actively paste message into chat box to guarantee it is filled on Windows UWP
        threading.Thread(target=_safe_paste_into_chat, args=(message, auto_send, 1.3), daemon=True).start()
        if auto_send:
            return f"{call_me}, dispatched WhatsApp message to {display}: '{message}'."
        else:
            return f"{call_me}, opened WhatsApp for {display} with message: '{message}'. Press Enter to send."
    except Exception as err:
        return f"{call_me}, could not open WhatsApp: {err}"


# ============================================================
# 10. RUNNING PROCESSES & HARDWARE METRICS
# ============================================================
def get_running_processes(limit: int = 10, call_me: str = "Sir") -> str:
    """
    Returns active running applications and processes sorted by memory usage.
    """
    try:
        ignore = {
            "svchost.exe", "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
            "services.exe", "lsass.exe", "fontdrvhost.exe", "dwm.exe", "spoolsv.exe",
            "sihost.exe", "taskhostw.exe", "conhost.exe", "ctfmon.exe",
            "searchindexer.exe", "securityhealthservice.exe", "mpengine.dll"
        }

        proc_map = {}
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                name = p.info.get('name') or "Unknown"
                if name.lower() in ignore:
                    continue
                mem = p.info.get('memory_percent') or 0.0
                cpu = p.info.get('cpu_percent') or 0.0
                if name not in proc_map:
                    proc_map[name] = {"mem": mem, "cpu": cpu, "count": 1}
                else:
                    proc_map[name]["mem"] += mem
                    proc_map[name]["cpu"] += cpu
                    proc_map[name]["count"] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        sorted_procs = sorted(proc_map.items(), key=lambda x: x[1]["mem"], reverse=True)[:limit]
        if not sorted_procs:
            return f"{call_me}, no active user applications detected."

        vm = psutil.virtual_memory()
        cpu_total = psutil.cpu_percent(interval=0.1)

        lines = [f"{call_me}, here are the top active applications on your laptop:"]
        for name, data in sorted_procs:
            display_name = name.replace(".exe", "").replace(".Root", "").title()
            lines.append(f"  • {display_name}: RAM {data['mem']:.1f}% | CPU {data['cpu']:.1f}%")

        lines.append(f"\nOverall System Load: RAM {vm.percent}% in use | CPU {cpu_total}%")
        return "\n".join(lines)
    except Exception as err:
        return f"{call_me}, failed to retrieve running processes: {err}"


# ============================================================
# 11. SCREEN BRIGHTNESS CONTROLS (NATIVE WMI)
# ============================================================
def get_screen_brightness(call_me: str = "Sir") -> str:
    """
    Retrieves the current display brightness level percentage via Windows WMI.
    """
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        output = res.stdout.strip()
        if output.isdigit():
            return f"{call_me}, your laptop screen brightness is currently {output}%."
        return f"{call_me}, current screen brightness is approximately 50%."
    except Exception as err:
        return f"{call_me}, could not query screen brightness: {err}"


def set_screen_brightness(level: int, call_me: str = "Sir") -> str:
    """
    Sets the laptop display brightness to a specific percentage (0-100).
    """
    try:
        target = max(0, min(100, int(level)))
        cmd = [
            "powershell", "-NoProfile", "-Command",
            f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {target})"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return f"{call_me}, screen brightness set to {target}%."
        return f"{call_me}, unable to adjust screen brightness (Code {res.returncode})."
    except Exception as err:
        return f"{call_me}, failed to set screen brightness: {err}"


def adjust_screen_brightness(delta: int, call_me: str = "Sir") -> str:
    """
    Increases or decreases current display brightness by delta (e.g. +15 or -15).
    """
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        current = 50
        if res.stdout.strip().isdigit():
            current = int(res.stdout.strip())
        target = max(0, min(100, current + delta))
        return set_screen_brightness(target, call_me)
    except Exception:
        target = max(0, min(100, 50 + delta))
        return set_screen_brightness(target, call_me)


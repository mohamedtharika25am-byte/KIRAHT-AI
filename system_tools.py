"""
KIRAHT AI - System Tools Engine (Clipboard, Volume, Screenshot, Ping, Notes & OS Controls)
Provides developer automation, clipboard interaction, screen capture, Windows system controls,
precision volume control, and network latency diagnostics.
"""

import ctypes
import datetime
import json
import os
import re
import subprocess
import urllib.parse
import webbrowser
import win32clipboard

NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")
CONTACTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts.json")


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
def _get_audio_endpoint_volume():
    """
    Acquires Windows IAudioEndpointVolume COM interface for master volume manipulation.
    """
    try:
        import comtypes
        from comtypes import CLSCTX_ALL, CoCreateInstance, GUID, IUnknown
        from ctypes import POINTER, c_float, c_long, HRESULT

        class IAudioEndpointVolume(IUnknown):
            _iid_ = GUID("{5CDF2C82-841E-4546-9722-0CF74078229A}")
            _methods_ = [
                comtypes.STDMETHOD(HRESULT, "RegisterControlChangeNotify", []),
                comtypes.STDMETHOD(HRESULT, "UnregisterControlChangeNotify", []),
                comtypes.STDMETHOD(HRESULT, "GetChannelCount", [POINTER(ctypes.c_uint)]),
                comtypes.STDMETHOD(HRESULT, "SetMasterVolumeLevel", [c_float, ctypes.c_void_p]),
                comtypes.STDMETHOD(HRESULT, "SetMasterVolumeLevelScalar", [c_float, ctypes.c_void_p]),
                comtypes.STDMETHOD(HRESULT, "GetMasterVolumeLevel", [POINTER(c_float)]),
                comtypes.STDMETHOD(HRESULT, "GetMasterVolumeLevelScalar", [POINTER(c_float)]),
                comtypes.STDMETHOD(HRESULT, "SetMute", [c_long, ctypes.c_void_p]),
                comtypes.STDMETHOD(HRESULT, "GetMute", [POINTER(c_long)]),
            ]

        class IMMDevice(IUnknown):
            _iid_ = GUID("{D666063F-1587-4E43-81F1-B948E807363F}")
            _methods_ = [
                comtypes.STDMETHOD(HRESULT, "Activate", [POINTER(GUID), ctypes.c_uint, ctypes.c_void_p, POINTER(POINTER(IAudioEndpointVolume))]),
            ]

        class IMMDeviceEnumerator(IUnknown):
            _iid_ = GUID("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
            _methods_ = [
                comtypes.STDMETHOD(HRESULT, "EnumAudioEndpoints", []),
                comtypes.STDMETHOD(HRESULT, "GetDefaultAudioEndpoint", [ctypes.c_uint, ctypes.c_uint, POINTER(POINTER(IMMDevice))]),
            ]

        enumerator = CoCreateInstance(GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}"), IMMDeviceEnumerator, CLSCTX_ALL)
        endpoint = POINTER(IMMDevice)()
        enumerator.GetDefaultAudioEndpoint(0, 1, ctypes.byref(endpoint))
        vol = POINTER(IAudioEndpointVolume)()
        endpoint.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None, ctypes.byref(vol))
        return vol
    except Exception:
        return None


def get_current_volume() -> int:
    """
    Returns current master volume percentage (0-100).
    """
    vol = _get_audio_endpoint_volume()
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
    vol = _get_audio_endpoint_volume()
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
    vol = _get_audio_endpoint_volume()
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
def load_contacts() -> dict:
    """
    Loads saved contacts mapping names to phone numbers from contacts.json.
    """
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_contacts(contacts: dict) -> None:
    """
    Saves contacts mapping to contacts.json.
    """
    try:
        with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(contacts, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def add_contact(name: str, phone: str, call_me: str = "Sir") -> str:
    """
    Adds or updates a contact in the local contact book.
    """
    contacts = load_contacts()
    clean_name = name.lower().strip()
    clean_phone = re.sub(r"[^\d+]", "", phone.strip())
    # If 10 digits without country code, default to India (+91)
    if len(clean_phone) == 10 and not clean_phone.startswith("+"):
        clean_phone = "+91" + clean_phone

    contacts[clean_name] = clean_phone
    save_contacts(contacts)
    return f"{call_me}, saved contact '{name.title()}' with number {clean_phone}."


def list_contacts(call_me: str = "Sir") -> str:
    """
    Lists all saved contacts.
    """
    contacts = load_contacts()
    if not contacts:
        return f"{call_me}, your contact book is empty. You can add someone using: add contact <name> <phone_number>."
    formatted = [f"{name.title()}: {phone}" for name, phone in contacts.items()]
    return f"{call_me}, here are your saved contacts:\n  - " + "\n  - ".join(formatted)


def send_whatsapp_message(target: str, message: str, call_me: str = "Sir") -> str:
    """
    Opens WhatsApp desktop or web with prefilled message directed to a contact or phone number.
    Uses official Windows whatsapp:// protocol with automatic web fallback.
    """
    contacts = load_contacts()
    clean_target = target.lower().strip()

    phone_number = ""
    display_name = target.title()

    if clean_target in contacts:
        phone_number = contacts[clean_target]
        display_name = clean_target.title()
    else:
        # Check if target is directly a phone number
        digits = re.sub(r"[^\d+]", "", target.strip())
        if len(digits) >= 10:
            if len(digits) == 10 and not digits.startswith("+"):
                phone_number = "+91" + digits
            else:
                phone_number = digits
            display_name = phone_number
        else:
            return (
                f"{call_me}, '{target}' was not found in your contacts, and does not appear to be a valid phone number.\n"
                f"You can save them first: add contact {target} <number>"
            )

    # Normalize phone: numbers only for URI protocol
    url_phone = re.sub(r"[^\d]", "", phone_number)
    encoded_text = urllib.parse.quote(message.strip())

    # Native Windows WhatsApp URI protocol
    uri = f"whatsapp://send?phone={url_phone}&text={encoded_text}"
    web_fallback = f"https://web.whatsapp.com/send?phone={url_phone}&text={encoded_text}"

    try:
        os.startfile(uri)
        return f"{call_me}, opened WhatsApp for {display_name} with your message pre-filled. Press Enter to send."
    except Exception:
        try:
            webbrowser.open(web_fallback)
            return f"{call_me}, opened WhatsApp Web for {display_name} with your message pre-filled."
        except Exception as err:
            return f"{call_me}, unable to open WhatsApp: {err}"


"""
KIRAHT AI - System Tools Engine (Clipboard, Volume, Screenshot, Ping, Notes & OS Controls)
Provides developer automation, clipboard interaction, screen capture, Windows system controls,
precision volume control, and network latency diagnostics.
"""

import ctypes
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
            data = json.load(f)
            if not isinstance(data, dict):
                return default_data
            # If flat dict (no 'contacts' key), migrate to structured format
            if "contacts" not in data and "aliases" not in data:
                return {"contacts": data, "aliases": {}, "groups": {}}
            if "contacts" not in data:
                data["contacts"] = {}
            if "aliases" not in data:
                data["aliases"] = {}
            if "groups" not in data:
                data["groups"] = {}
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
        return groups[clean_query], groups[clean_query], []

    # 4. Prefix / Substring Match in Contacts
    for name, phone in contacts.items():
        if name.startswith(clean_query) or clean_query in name:
            return phone, name.title(), []

    # 5. Check aliases prefix/substring
    for alias, target in aliases.items():
        if alias.startswith(clean_query) or clean_query in alias:
            t_clean = target.lower().strip()
            if t_clean in contacts:
                return contacts[t_clean], t_clean.title(), []

    # 6. Check Groups substring
    for gname, gid in groups.items():
        if clean_query in gname or gname.startswith(clean_query):
            return gid, gname.title(), []

    # 7. Fuzzy matching for Related Contacts
    all_names = list(contacts.keys()) + list(aliases.keys())
    close_matches = difflib.get_close_matches(clean_query, all_names, n=3, cutoff=0.45)
    related = []
    for match in close_matches:
        match_phone = contacts.get(match) or contacts.get(aliases.get(match, "").lower(), "")
        if match_phone:
            related.append(f"{match.title()} ({match_phone})")
        else:
            related.append(match.title())

    return None, query.title(), related


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


def send_whatsapp_message(target: str, message: str, call_me: str = "Sir") -> str:
    """
    Opens WhatsApp desktop or web with prefilled message directed to a contact or phone number.
    Uses official Windows whatsapp:// protocol with automatic web fallback.
    """
    phone_number, display_name, related = resolve_contact(target)

    if not phone_number:
        # Check if target is directly a raw phone number
        digits = re.sub(r"\D", "", target.strip())
        if len(digits) >= 10:
            if len(digits) == 10:
                phone_number = "+91" + digits
            elif len(digits) == 12 and digits.startswith("91"):
                phone_number = "+" + digits
            else:
                phone_number = "+" + digits
            display_name = phone_number
        else:
            related_msg = f"\nRelated contacts found: {', '.join(related)}" if related else ""
            return (
                f"{call_me}, '{target}' was not found in your contacts.{related_msg}\n"
                f"You can save them first: add contact {target} <number>"
            )

    # Check if target is a group (ends with @g.us)
    if str(phone_number).endswith("@g.us"):
        encoded_text = urllib.parse.quote(message.strip())
        uri = f"whatsapp://send?text={encoded_text}"
        try:
            os.startfile(uri)
            return f"{call_me}, opened WhatsApp with message pre-filled for group '{display_name}'. Select group and press Send."
        except Exception:
            return f"{call_me}, opened WhatsApp for group '{display_name}'."

    # Normalize phone: numbers only for URI protocol
    url_phone = re.sub(r"[^\d]", "", phone_number)
    encoded_text = urllib.parse.quote(message.strip())

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


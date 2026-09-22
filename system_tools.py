"""
KIRAHT AI - System Tools Engine (Clipboard, Terminal Runner, Screenshot & OS Controls)
Provides developer automation, clipboard interaction, screen capture, and Windows system controls.
"""

import ctypes
import datetime
import os
import re
import subprocess
import win32clipboard


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


def run_terminal_command(command: str, call_me: str = "Sir", timeout: int = 30) -> str:
    """
    Executes a shell command in workspace directory and captures output.
    Blocks potentially destructive actions without explicit user consent.
    """
    clean_cmd = command.strip()

    # Safety guardrail against destructive commands
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
            # Truncate very long outputs
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


def take_screenshot(call_me: str = "Sir") -> str:
    """
    Captures primary screen and saves it to user's Pictures\\Screenshots or Desktop.
    """
    try:
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        if not os.path.exists(pictures_dir):
            pictures_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(pictures_dir, filename)

        # PowerShell screen capture script
        ps_code = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('{filepath}')
$g.Dispose()
$bmp.Dispose()
"""
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_code],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if os.path.exists(filepath):
            # Try to open the screenshot
            try:
                os.startfile(filepath)
            except Exception:
                pass
            return f"{call_me}, screenshot captured and saved to: {filepath}"
        else:
            err_msg = res.stderr.strip() or "Unknown error"
            return f"{call_me}, unable to capture screen: {err_msg}"
    except Exception as err:
        return f"{call_me}, screenshot operation failed: {err}"


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


def show_desktop_notification(title: str, message: str, call_me: str = "Sir") -> str:
    """
    Triggers a native Windows balloon / toast notification.
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

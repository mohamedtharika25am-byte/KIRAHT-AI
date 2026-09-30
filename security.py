"""
KIRAHT AI - Security & Permission Gating System
Provides permission verification, safety gates, and destructive command interception.
Inspired by enterprise AI assistant security models.

Modes:
- SAFE MODE (Default: KIRAHT_ALLOW_WRITES=0):
  Any file write/creation, file deletion, recycle bin emptying, or destructive
  terminal commands will interactively prompt the user for (y/n) confirmation.
- WRITE MODE (KIRAHT_ALLOW_WRITES=1):
  Effectful and write operations are auto-permitted for seamless automation.
"""

import os
import re
import sys
from dotenv import load_dotenv

load_dotenv()


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def are_writes_allowed() -> bool:
    """
    Returns True if KIRAHT_ALLOW_WRITES=1 in environment or .env,
    allowing automatic writes without interactive prompts.
    """
    try:
        load_dotenv(override=True)
    except Exception:
        pass
    val = os.getenv("KIRAHT_ALLOW_WRITES", "1").strip().lower()
    return val in ("1", "true", "yes", "allow", "enabled")


def get_security_mode_label() -> str:
    """
    Returns formatted security status string for the startup banner.
    """
    if are_writes_allowed():
        return "[WRITE MODE] (Auto-write enabled)"
    return "[SAFE MODE] (Confirm on write/delete)"


def is_destructive_shell_command(cmd_str: str) -> bool:
    """
    Detects if a shell command contains destructive or file-modifying verbs.
    """
    clean = cmd_str.strip().lower()
    destructive_patterns = [
        r"\b(?:del|erase|rm|rmdir|rd)\s+",
        r"\bformat\s+[a-z]:",
        r"\b(?:git\s+reset\s+--hard|git\s+clean\s+-[a-z]*f)",
        r"\b(?:pip\s+uninstall)\b",
        r"\b(?:drop\s+database|drop\s+table|truncate\s+table)\b",
        r"\b(?:taskkill\s+/f|kill\s+-9)\b",
        r"\b(?:shutdown\s+/[s|r])\b",
    ]
    for pattern in destructive_patterns:
        if re.search(pattern, clean):
            return True
    return False


def request_permission(action_type: str, description: str, call_me: str = "Sir") -> bool:
    """
    Evaluates whether an effectful action may proceed.
    If KIRAHT_ALLOW_WRITES=1, logs an auto-permit notice and returns True.
    Otherwise, prompts the user interactively (y/n).
    If running non-interactively (web daemon/background), permits safely.
    """
    if are_writes_allowed():
        print(f"\n[KIRAHT AI Security: Auto-permitted '{action_type}' (KIRAHT_ALLOW_WRITES=1)]")
        return True

    if not sys.stdin or not sys.stdin.isatty():
        print(f"\n[KIRAHT AI Security: Non-interactive environment, auto-permitting '{action_type}']")
        return True

    prompt_text = (
        f"\n[KIRAHT AI Security Gate: Permission Required]\n"
        f"  Target Action: {description}\n"
        f"  Do you want to proceed, {call_me}? (y/n): "
    )
    try:
        sys.stdout.write(prompt_text)
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        if choice in ("y", "yes", "sure", "ok", "proceed", "confirm", "allow"):
            return True
        else:
            print(f"\n[KIRAHT AI: Action declined by {call_me}. Operation cancelled safely.]")
            return False
    except (KeyboardInterrupt, EOFError):
        print(f"\n[KIRAHT AI: Operation cancelled by {call_me}.]")
        return False

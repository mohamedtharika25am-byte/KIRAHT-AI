import os
import json
import time
import datetime
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMINDERS_FILE = os.path.join(BASE_DIR, "reminders.json")

DEFAULT_REMINDERS_DATA = {
    "prayer_times": {
        "fajr": {"name": "Fajr (சுபஹ்)", "time": "05:35", "enabled": True, "last_triggered": ""},
        "dhuhr": {"name": "Dhuhr (ளுஹர்)", "time": "13:00", "enabled": True, "last_triggered": ""},
        "asr": {"name": "Asr (அஸர்)", "time": "15:15", "enabled": True, "last_triggered": ""},
        "maghrib": {"name": "Maghrib (மஃரிப்)", "time": "18:30", "enabled": True, "last_triggered": ""},
        "isha": {"name": "Isha (இஷா)", "time": "20:15", "enabled": True, "last_triggered": ""},
    },
    "custom_reminders": [
        {
            "id": "rem_hydrate",
            "title": "Drink Water & Hydrate (தண்ணீர் அருந்தவும்)",
            "time": "11:00",
            "enabled": True,
            "days": ["daily"],
            "last_triggered": "",
        }
    ],
    "settings": {
        "voice_announce": True,
        "desktop_notification": True,
        "snooze_minutes": 10,
    },
    "history": []
}


def load_reminders() -> Dict[str, Any]:
    """Loads reminders data from reminders.json with automatic defaults."""
    if not os.path.exists(REMINDERS_FILE):
        save_reminders(DEFAULT_REMINDERS_DATA)
        return json.loads(json.dumps(DEFAULT_REMINDERS_DATA))
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure mandatory keys exist
            if "prayer_times" not in data:
                data["prayer_times"] = DEFAULT_REMINDERS_DATA["prayer_times"]
            if "custom_reminders" not in data:
                data["custom_reminders"] = DEFAULT_REMINDERS_DATA["custom_reminders"]
            if "settings" not in data:
                data["settings"] = DEFAULT_REMINDERS_DATA["settings"]
            return data
    except Exception as e:
        print(f"[!] Error loading reminders.json: {e}")
        return json.loads(json.dumps(DEFAULT_REMINDERS_DATA))


def save_reminders(data: Dict[str, Any]) -> bool:
    """Persists reminders data to reminders.json atomically."""
    try:
        temp_file = REMINDERS_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if os.path.exists(REMINDERS_FILE):
            os.remove(REMINDERS_FILE)
        os.rename(temp_file, REMINDERS_FILE)
        return True
    except Exception as e:
        print(f"[!] Error saving reminders.json: {e}")
        return False


def update_prayer_time(prayer_key: str, new_time: str, enabled: Optional[bool] = None) -> Tuple[bool, str]:
    """
    Updates the scheduled time for one of the 5 prayers.
    new_time should be 'HH:MM' (24-hour) or 'HH:MM AM/PM'.
    """
    key = prayer_key.lower().strip()
    data = load_reminders()
    prayers = data.get("prayer_times", {})

    if key not in prayers:
        return False, f"Unknown prayer name: '{prayer_key}'. Supported: fajr, dhuhr, asr, maghrib, isha."

    # Parse and normalize time string to HH:MM (24-hr format)
    norm_time = normalize_time_str(new_time)
    if not norm_time:
        return False, f"Invalid time format: '{new_time}'. Use HH:MM format like '05:15' or '05:15 AM'."

    prayers[key]["time"] = norm_time
    if enabled is not None:
        prayers[key]["enabled"] = enabled

    save_reminders(data)
    name = prayers[key].get("name", key.capitalize())
    return True, f"Prayer time for {name} updated to {format_12hr(norm_time)}."


def add_custom_reminder(title: str, time_str: str, days: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any], str]:
    """Adds a new custom event reminder."""
    norm_time = normalize_time_str(time_str)
    if not norm_time:
        return False, {}, f"Invalid time format: '{time_str}'."

    data = load_reminders()
    rem_id = f"rem_{int(time.time())}"
    new_rem = {
        "id": rem_id,
        "title": title.strip(),
        "time": norm_time,
        "enabled": True,
        "days": days or ["daily"],
        "last_triggered": "",
    }
    data.setdefault("custom_reminders", []).append(new_rem)
    save_reminders(data)
    return True, new_rem, f"Reminder set: '{title}' at {format_12hr(norm_time)}."


def delete_custom_reminder(reminder_id: str) -> Tuple[bool, str]:
    """Deletes a custom reminder by ID."""
    data = load_reminders()
    customs = data.get("custom_reminders", [])
    before_count = len(customs)
    data["custom_reminders"] = [r for r in customs if r.get("id") != reminder_id]
    if len(data["custom_reminders"]) < before_count:
        save_reminders(data)
        return True, "Reminder successfully removed."
    return False, "Reminder not found."


def record_reminder_response(reminder_id: str, action: str) -> Tuple[bool, str]:
    """
    Handles Accept or Deny (Snooze) action for a triggered reminder.
    action: 'accept' (Dismiss / Completed) or 'deny' (Snooze / Postpone)
    """
    data = load_reminders()
    action = action.lower().strip()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    # Check prayer times
    for key, p in data.get("prayer_times", {}).items():
        if key == reminder_id or f"prayer_{key}" == reminder_id:
            if action == "accept":
                p["status"] = "accepted"
                save_reminders(data)
                return True, f"✅ Prayer '{p['name']}' acknowledged as completed."
            elif action in ("deny", "snooze"):
                # Snooze by 10 minutes
                snooze_min = data.get("settings", {}).get("snooze_minutes", 10)
                p["snooze_until"] = (datetime.datetime.now() + datetime.timedelta(minutes=snooze_min)).strftime("%H:%M")
                save_reminders(data)
                return True, f"⏰ Prayer reminder snoozed for {snooze_min} minutes."

    # Check custom reminders
    for rem in data.get("custom_reminders", []):
        if rem.get("id") == reminder_id:
            if action == "accept":
                rem["status"] = "accepted"
                save_reminders(data)
                return True, f"✅ Reminder '{rem['title']}' completed."
            elif action in ("deny", "snooze"):
                snooze_min = data.get("settings", {}).get("snooze_minutes", 10)
                rem["snooze_until"] = (datetime.datetime.now() + datetime.timedelta(minutes=snooze_min)).strftime("%H:%M")
                save_reminders(data)
                return True, f"⏰ Reminder snoozed for {snooze_min} minutes."

    return False, f"Reminder '{reminder_id}' not found."


def check_due_reminders() -> List[Dict[str, Any]]:
    """
    Checks all prayer times and custom reminders against current local time.
    Returns list of due reminder dictionaries.
    """
    now = datetime.datetime.now()
    cur_time = now.strftime("%H:%M")
    today_date = now.strftime("%Y-%m-%d")

    data = load_reminders()
    due_list: List[Dict[str, Any]] = []

    # 1. Check Prayer Times
    for key, p in data.get("prayer_times", {}).items():
        if not p.get("enabled", True):
            continue

        p_time = p.get("time", "")
        last_trig = p.get("last_triggered", "")
        snooze_until = p.get("snooze_until", "")

        is_due = False
        if snooze_until == cur_time:
            is_due = True
            p["snooze_until"] = ""  # Reset snooze
        elif p_time == cur_time and last_trig != today_date:
            is_due = True
            p["last_triggered"] = today_date

        if is_due:
            due_list.append({
                "id": f"prayer_{key}",
                "category": "prayer",
                "key": key,
                "title": p.get("name", key.capitalize()),
                "time": format_12hr(p_time),
                "message": f"Sir, it is time for {p.get('name', key.capitalize())} Prayer. (தொழுகை நேரம் வந்துவிட்டது)",
                "icon": "🕌",
            })

    # 2. Check Custom Reminders
    for rem in data.get("custom_reminders", []):
        if not rem.get("enabled", True):
            continue

        rem_time = rem.get("time", "")
        last_trig = rem.get("last_triggered", "")
        snooze_until = rem.get("snooze_until", "")

        is_due = False
        if snooze_until == cur_time:
            is_due = True
            rem["snooze_until"] = ""
        elif rem_time == cur_time and last_trig != today_date:
            is_due = True
            rem["last_triggered"] = today_date

        if is_due:
            due_list.append({
                "id": rem.get("id"),
                "category": "custom",
                "title": rem.get("title", "Scheduled Reminder"),
                "time": format_12hr(rem_time),
                "message": f"Sir, reminder: {rem.get('title', 'Scheduled event')}",
                "icon": "⏰",
            })

    if due_list:
        save_reminders(data)

    return due_list


def normalize_time_str(time_str: str) -> Optional[str]:
    """Converts diverse user time inputs ('5:00 am', '17:30', '5pm') to strict 'HH:MM' 24-hr format."""
    s = time_str.strip().lower()
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return dt.strftime("%H:%M")
        except ValueError:
            pass
    return None


def format_12hr(time_24: str) -> str:
    """Formats 'HH:MM' into friendly 'hh:mm AM/PM'."""
    try:
        dt = datetime.datetime.strptime(time_24, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return time_24


def handle_reminder_intent(query: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Checks if user text matches prayer times or reminder intents.
    Returns: (is_handled, category, tool_name, result_string)
    """
    import re
    cleaned = query.strip()
    lower = cleaned.lower()

    # 1. Check Accept / Deny responses to active reminder
    if lower in ("accept", "accept reminder", "done", "completed", "mudinjithu", "thozhuthuten", "thozhuthaachu"):
        ok, msg = record_reminder_response("latest", "accept")
        return True, "reminder", "record_reminder_response", f"{call_me}, {msg}"

    if lower in ("deny", "deny reminder", "snooze", "snooze reminder", "later", "aprom", "aprom pandren"):
        ok, msg = record_reminder_response("latest", "deny")
        return True, "reminder", "record_reminder_response", f"{call_me}, {msg}"

    # 2. Query all Prayer Times
    if re.search(r"\b(?:prayer\s*times?|namaz\s*times?|salah\s*times?|thozhugai\s*neram|5\s*prayers?)\b", lower):
        data = load_reminders()
        prayers = data.get("prayer_times", {})
        lines = [f"{call_me}, here are the scheduled 5 Daily Prayer Times (தொழுகை நேரங்கள்):"]
        for k in ("fajr", "dhuhr", "asr", "maghrib", "isha"):
            if k in prayers:
                p = prayers[k]
                status_icon = "🟢" if p.get("enabled", True) else "⚪ [OFF]"
                lines.append(f"• **{p.get('name', k.capitalize())}**: `{format_12hr(p['time'])}` {status_icon}")
        lines.append("\n*You can edit any time in the Calendar/Reminders popup or by saying 'set fajr time to 05:15'.*")
        return True, "prayer_times", "get_prayer_times", "\n".join(lines)

    # 3. Edit / Set specific Prayer Time
    set_prayer_m = re.search(
        r"(?:set|change|update)\s+(?:the\s+)?(fajr|dhuhr|asr|maghrib|isha)\s+(?:prayer\s+)?(?:time\s+)?(?:to\s+)?(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)",
        cleaned,
        re.IGNORECASE,
    )
    if set_prayer_m:
        p_name = set_prayer_m.group(1).lower()
        new_t = set_prayer_m.group(2).strip()
        ok, msg = update_prayer_time(p_name, new_t)
        return True, "prayer_times", "update_prayer_time", f"{call_me}, {msg}"

    # 4. Add Custom Reminder: "remind me to [task] at [time]"
    rem_match = re.search(
        r"^(?:please\s+)?(?:remind\s+me\s+to|set\s+(?:a\s+)?reminder\s+to|add\s+(?:a\s+)?reminder\s+(?:for|to)?)\s+(.+?)\s+(?:at|on)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)$",
        cleaned,
        re.IGNORECASE,
    )
    if rem_match:
        task = rem_match.group(1).strip()
        time_str = rem_match.group(2).strip()
        ok, new_rem, msg = add_custom_reminder(task, time_str)
        return True, "custom_reminder", "add_custom_reminder", f"{call_me}, {msg}"

    # 5. List Custom Reminders
    if re.search(r"\b(?:list\s+reminders?|show\s+reminders?|my\s+reminders?|reminders?\s+list)\b", lower):
        data = load_reminders()
        customs = data.get("custom_reminders", [])
        if not customs:
            return True, "custom_reminder", "list_reminders", f"{call_me}, you have no active custom reminders scheduled."
        lines = [f"{call_me}, here are your active custom reminders:"]
        for r in customs:
            status_icon = "🟢" if r.get("enabled", True) else "⚪ [OFF]"
            lines.append(f"• **{r.get('title', 'Event')}**: `{format_12hr(r.get('time', ''))}` {status_icon}")
        return True, "custom_reminder", "list_reminders", "\n".join(lines)

    return False, "", "", ""


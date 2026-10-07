"""
KIRAHT AI - Unified Core Engine
Shared brain for both Terminal Mode (main.py) and Web HUD (web_server.py).
Handles memory, persistent chat history, deterministic intent routing,
system telemetry, dual AI engine inference (Gemini + Ollama), and real-time streaming.
"""

import ast
import asyncio
import datetime
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Any

import httpx
import ollama
import psutil
from dotenv import load_dotenv
from security import are_writes_allowed

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")
KNOWLEDGE_CACHE_FILE = os.path.join(BASE_DIR, "knowledge_cache.json")
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
WORKSPACE_DIR = r"d:\KIRAHT AI"

# Attempt imports for DuckDuckGo search
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

# Default memory template
DEFAULT_MEMORY = {
    "user_name": "Mohamed Tharik A",
    "preferred_name": "Tharik",
    "call_me": "Sir",
    "assistant_name": "KIRAHT AI",
    "persona": "Polite, razor-sharp, direct, and highly intelligent personal assistant",
    "response_style": "Strictly concise. Answer only what is asked in 1-3 sentences. Never include unnecessary preambles, disclaimers, or filler text unless detailed explanation is specifically requested.",
    "language_preference": "English / Tanglish",
    "custom_notes": [
        "Address the user with respect as Sir.",
        "Be sharp and straight to the point.",
        "Do not provide verbose essays or unsolicited advice.",
    ],
}

# Session start timestamp for uptime tracking
SESSION_START_DT = datetime.datetime.now()

# Performance caches to prevent blocking the async event loop during frequent telemetry pushes
_CACHED_WIFI: Tuple[str, float] = ("Wi-Fi", 0.0)
_CACHED_LOCAL_IP: Tuple[str, float] = ("127.0.0.1", 0.0)
_CACHED_ONLINE: Tuple[bool, float] = (True, 0.0)
_CACHED_NET_IO: Tuple[Any, float] = (None, 0.0)
_CACHED_NET_SPEED: Tuple[str, str, float] = ("0.0 KB/s", "0.0 KB/s", 0.0)
_CACHED_PING: Tuple[int, float] = (24, 0.0)
_CACHED_GEMINI_CLIENT: Any = None
_CACHED_GEMINI_KEY: str = ""
_CACHED_OLLAMA_CLIENT: Any = None
_CACHED_OLLAMA_HOST: str = ""

_IS_REFRESHING_WIFI = False
_IS_REFRESHING_PING = False


def _bg_refresh_wifi():
    global _CACHED_WIFI, _IS_REFRESHING_WIFI
    try:
        from system_tools import get_wifi_status
        raw_wifi = get_wifi_status(call_me="Sir")
        match = re.search(r"SSID\s*:\s*([^\n,]+)", raw_wifi)
        if match:
            _CACHED_WIFI = (match.group(1).strip(), time.time())
    except Exception:
        pass
    finally:
        _IS_REFRESHING_WIFI = False


def _bg_refresh_ping():
    global _CACHED_PING, _IS_REFRESHING_PING
    try:
        t0 = time.time()
        s = socket.create_connection(("1.1.1.1", 53), timeout=0.25)
        s.close()
        p = max(1, int((time.time() - t0) * 1000))
        _CACHED_PING = (p, time.time())
    except Exception:
        try:
            t0 = time.time()
            s = socket.create_connection(("8.8.8.8", 53), timeout=0.25)
            s.close()
            p = max(1, int((time.time() - t0) * 1000))
            _CACHED_PING = (p, time.time())
        except Exception:
            _CACHED_PING = (24, time.time())
    finally:
        _IS_REFRESHING_PING = False



# =====================================================================
# 1. PERSISTENT USER MEMORY (memory.json) - NEVER MIX WITH CHAT HISTORY
# =====================================================================
def load_memory() -> dict:
    """Loads persistent user profile and preferences from memory.json."""
    if not os.path.exists(MEMORY_FILE):
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, val in DEFAULT_MEMORY.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception:
        return DEFAULT_MEMORY.copy()


def save_memory(memory_data: dict) -> None:
    """Saves the user profile and preferences to memory.json."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[!] Warning: Failed to save memory: {err}")


def build_system_prompt(memory: dict) -> str:
    """Builds the core system prompt using persistent user memory with full context injection."""
    user_name = memory.get("user_name", "Mohamed Tharik A")
    preferred = memory.get("preferred_name", "Tharik")
    call_me = memory.get("call_me", "Sir")
    persona = memory.get("persona", DEFAULT_MEMORY["persona"])
    response_style = memory.get("response_style", DEFAULT_MEMORY["response_style"])
    profile = memory.get("user_profile", {})
    edu = profile.get("education", {})
    edu_str = f"{edu.get('degree', 'B.E. CSE')} ({edu.get('specialization', 'AI/ML')}) - {edu.get('year', '2nd Year')} at {edu.get('college', 'KGiSL Institute of Technology, Coimbatore')}"
    projects = profile.get("projects", [])
    proj_str = ", ".join(f"{p.get('name')}: {p.get('description')}" for p in projects)
    notes = memory.get("custom_notes", [])
    notes_str = "\n".join(f"- {n}" for n in notes)
    current_dt = datetime.datetime.now().strftime("%A, %d %B %Y %I:%M:%S %p")

    return (
        f"You are KIRAHT AI, an elite personal AI assistant. Your persona is {persona}.\n"
        f"Current System Time: {current_dt}\n"
        f"Workspace Location: d:\\KIRAHT AI (All project files and newly created files reside here by default)\n"
        f"Creator & Boss: You were developed and created by {user_name} ({preferred}). He is your sole Boss, Master, and Creator.\n"
        f"Master Identity: You are speaking with {user_name}. Always address him with high respect as '{call_me}'.\n\n"
        f"Master's Background & Identity (from persistent memory):\n"
        f"- Full Name: {user_name} ({preferred})\n"
        f"- College & Education: {edu_str}\n"
        f"- Location: {profile.get('location', 'Coimbatore, Tamil Nadu, India')}\n"
        f"- Key Projects: {proj_str}\n"
        f"- Technical Interests: {', '.join(profile.get('technical_interests', []))}\n\n"
        f"Identity Directives:\n"
        f"- When asked 'Who am I?', 'Tell me about myself', 'En profile enna', or asked to refer to memory.json/memory, you ALREADY HAVE his full profile above! Summarize his name, college, degree, projects, and goals proudly, respectfully, and accurately.\n"
        f"- When asked 'Who created you?' or 'Who is your boss?', reply: '{user_name} ({call_me}) is my creator and boss.'\n\n"
        f"LANGUAGE & TANGLISH RULES:\n"
        f"1. If the user writes in English, reply in crisp, clear English.\n"
        f"2. TANGLISH DEFINITION: Tanglish is Tamil spoken or written phonetically using English letters. You understand Tanglish perfectly. When the user asks in Tanglish, reply in polite, natural Tanglish or clear English.\n"
        f"3. STRICT PROHIBITION: NEVER use Hindi or Hinglish words under any circumstances.\n\n"
        f"CODE GENERATION & FILE SAVING RULES:\n"
        f"0. FULL PERMISSION TO WRITE AND GENERATE CODE IN CHAT:\n"
        f"   - You have FULL AND UNRESTRICTED PERMISSION from {call_me} to generate, write, improve, upgrade, and display complete code directly in this chat!\n"
        f"   - STRICT PROHIBITION: NEVER refuse code requests, and NEVER say 'I will not modify existing files without explicit permission' or 'I will not generate code without permission'.\n"
        f"   - When {call_me} asks to update, upgrade, improve, or provide code (e.g. 'update this file\\'s code', 'give updated code on chat', 'upgrade snake_game.py', 'generic code in java'):\n"
        f"     IMMEDIATELY write and display the full, working code in standard markdown code blocks (```python, ```java, etc.) right in your chat response!\n"
        f"1. CODE GENERATION / EXPLANATIONS (NEVER AUTO-SAVE TO DISK WITHOUT DIRECT COMMAND):\n"
        f"   - When the user asks for code, scripts, circuits, or technical help (e.g. 'write python code for...', 'how to use esp32...', 'give me script...', 'oled is not mandatory'):\n"
        f"     Present the code using regular markdown code blocks (e.g. ```python, ```ino, ```cpp).\n"
        f"     STRICT DIRECTIVE: DO NOT output ```FILE_SAVE:...```! NEVER automatically write or save code to disk on your own without an explicit user command to save/create a file!\n"
        f"     Instead, at the end of your response, ask politely if they want you to save it:\n"
        f"     'Shall I save this code for you, Sir? I recommend saving it in `kiraht\\'s project/<filename>`.'\n"
        f"     (If speaking Tanglish: 'Sir, intha code-ah save pannata? `kiraht\\'s project/<filename>`-la save panna recommend panren. Vera folder venaalum sollunga!')\n"
        f"2. EXPLICIT FILE SAVING (ONLY ON DIRECT USER COMMAND):\n"
        f"   - ONLY output a ```FILE_SAVE:<filepath>``` block when the user EXPLICITLY ordered you to save, create, or write a file (e.g. 'save this as...', 'create file...', 'save pannu', 'yes save it').\n"
        f"   - DEFAULT RECOMMENDATION & DESTINATION: Default to saving scripts and projects inside 'Kiraht\\'s project' folder:\n"
        f"     ```FILE_SAVE:d:\\KIRAHT AI\\Kiraht's project\\<filename>\n"
        f"     <file content here>\n"
        f"     ```\n"
        f"     DO NOT save user scripts directly into the root workspace folder ({WORKSPACE_DIR})!\n"
        f"   - CUSTOM DESTINATION: If the user explicitly mentions another directory (e.g. 'downloads', 'desktop', 'documents', or a custom folder path), target that specified folder instead.\n"
        f"     Example: ```FILE_SAVE:C:\\Users\\KiTE\\Downloads\\<filename>```\n"
        f"   - The backend server automatically intercepts this block, creates all parent folders, writes the file to disk, and confirms the save.\n"
        f"   - Never claim you have saved a file without including the ```FILE_SAVE:<filepath> block.\n\n"
        f"FOLDER CREATION DIRECTIVE:\n"
        f"- Whenever the user instructs you to create, add, or make a folder/directory (e.g. 'create folder atomic_game', 'add folder in that named xyz', 'atomic_game nu folder create pannu'):\n"
        f"  YOU MUST output a structured folder block in this exact format:\n"
        f"  ```FOLDER_CREATE:<folder_path>\n"
        f"  ```\n"
        f"  Example:\n"
        f"  ```FOLDER_CREATE:d:\\KIRAHT AI\\kiraht's project\\atomic_game\n"
        f"  ```\n"
        f"  The backend server automatically intercepts this block and creates the directory on disk.\n"
        f"  STRICT RULE: NEVER output a ```FILE_SAVE:...``` block when the user asked for a FOLDER! A folder is a directory, NOT a file with Python code or placeholder text inside it.\n\n"
        f"FILE & FOLDER DELETION DIRECTIVE:\n"
        f"- You have FULL PERMISSION to delete files and folders whenever requested by the user.\n"
        f"- NEVER refuse deletion by claiming lack of OS permissions or telling the user to run commands manually.\n"
        f"- Whenever the user instructs you to delete or remove a file or directory (e.g. 'delete downloads folder', 'remove esp32_audio_recorder.ino', 'delete folder xyz', 'downloads ah delete pannu'):\n"
        f"  YOU MUST output a structured deletion block in this exact format:\n"
        f"  ```DELETE_TARGET:<path>\n"
        f"  ```\n"
        f"  Example:\n"
        f"  ```DELETE_TARGET:d:\\KIRAHT AI\\downloads\n"
        f"  ```\n"
        f"  The backend server automatically intercepts this block, performs the deletion with a safe backup in .kiraht_trash/, and confirms to the user.\n\n"
        f"WHATSAPP MESSAGING & DESKTOP DIRECTIVE:\n"
        f"- You have NATIVE desktop automation to send WhatsApp messages to any contact or phone number on this laptop.\n"
        f"- NEVER say 'I am unable to interface with WhatsApp', 'I cannot send messages automatically', 'I do not have access to your account', or provide wa.me links to click manually. You HAVE direct desktop tool execution!\n"
        f"- Whenever the user instructs you to message someone on WhatsApp (e.g. 'sent whatsapp to dharma : https://...', 'whatsapp dharma hello', 'send whatsapp to naveen'):\n"
        f"  YOU MUST output a structured WhatsApp block in this exact format:\n"
        f"  ```WHATSAPP:<target>:::<message>\n"
        f"  ```\n"
        f"  Example:\n"
        f"  ```WHATSAPP:dharma:::https://pin.it/DLsW6wVCQ\n"
        f"  ```\n"
        f"  The backend server automatically looks up contacts, launches WhatsApp Desktop, and delivers the message.\n\n"
        f"Tone and Rules:\n"
        f"1. {response_style}\n"
        f"2. Be razor-sharp, direct, and factual. Never add conversational filler.\n"
        f"3. Prioritize brevity.\n"
        f"4. If live search results are provided, synthesize facts concisely.\n\n"
        f"Persistent Directives:\n"
        f"{notes_str}"
    )


# =====================================================================
# 2. LOCAL PERSISTENT CHAT HISTORY (chat_history.json)
# =====================================================================
def load_chat_history() -> List[Dict[str, Any]]:
    """Loads past conversation messages from chat_history.json."""
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


def save_chat_history(messages: List[Dict[str, Any]]) -> None:
    """Saves conversation messages to chat_history.json (limits to last 100 messages)."""
    try:
        # Keep last 100 messages for fast startup while retaining ample context
        trimmed = messages[-100:]
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[!] Warning: Failed to save chat history: {err}")


def add_chat_history_message(role: str, content: str, meta: Optional[dict] = None) -> Dict[str, Any]:
    """Appends a new message to chat_history.json and returns the record."""
    history = load_chat_history()
    timestamp = datetime.datetime.now().strftime("%I:%M %p")
    msg = {
        "role": role,
        "content": content,
        "timestamp": timestamp,
        "meta": meta or {}
    }
    history.append(msg)
    save_chat_history(history)
    return msg


def clear_chat_history() -> None:
    """Safely archives persistent conversation history to protect user messages from ever being lost."""
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            history = load_chat_history()
            if history:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_dir = os.path.join(os.path.dirname(CHAT_HISTORY_FILE), "history_archives")
                os.makedirs(archive_dir, exist_ok=True)
                archive_path = os.path.join(archive_dir, f"chat_history_archive_{timestamp}.json")
                with open(archive_path, "w", encoding="utf-8") as f:
                    json.dump(history, f, indent=2)
                print(f"[*] Chat history safely archived to: {archive_path}")
    except Exception as err:
        print(f"[!] Warning: Failed to archive chat history: {err}")


# =====================================================================
# 3. KNOWLEDGE CACHE
# =====================================================================
def load_knowledge_cache() -> dict:
    """Loads persistent knowledge cache from knowledge_cache.json."""
    if not os.path.exists(KNOWLEDGE_CACHE_FILE):
        return {}
    try:
        with open(KNOWLEDGE_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_knowledge_cache(cache: dict) -> None:
    """Saves the knowledge cache to knowledge_cache.json."""
    try:
        with open(KNOWLEDGE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"[!] Warning: Failed to save knowledge cache: {err}")


def find_cached_knowledge(user_text: str, cache: dict) -> Tuple[bool, str]:
    """Checks if query matches any learned topic in knowledge_cache.json."""
    if not cache:
        return False, ""
    clean_query = re.sub(r"[^\w\s]", " ", user_text.lower()).strip()
    query_words = set(clean_query.split())
    for key, data in cache.items():
        clean_key = re.sub(r"[^\w\s]", " ", key.lower()).strip()
        topic = re.sub(r"[^\w\s]", " ", data.get("topic", "").lower()).strip()
        if (clean_key and clean_key in clean_query) or (topic and topic in clean_query):
            return True, data.get("summary", "")
        key_words = set(clean_key.split())
        if key_words and key_words.issubset(query_words):
            return True, data.get("summary", "")
    return False, ""


# =====================================================================
# 4. REAL-TIME SYSTEM TELEMETRY (REAL BACKEND METRICS)
# =====================================================================
def get_system_telemetry() -> Dict[str, Any]:
    """
    Collects real-time hardware telemetry:
    CPU, RAM, Disks (C & D), Battery, Network, OS, and Uptime.
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{cpu_freq.current / 1000:.2f} GHz" if cpu_freq else "N/A"

    # RAM
    vmem = psutil.virtual_memory()
    ram_percent = vmem.percent
    ram_used_gb = round((vmem.total - vmem.available) / (1024 ** 3), 1)
    ram_total_gb = round(vmem.total / (1024 ** 3), 1)

    # Disks (C: and D: if available)
    disks = []
    for drive in ["C:\\", "D:\\"]:
        if os.path.exists(drive):
            try:
                usage = psutil.disk_usage(drive)
                disks.append({
                    "drive": drive[:2],
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                    "used_gb": round(usage.used / (1024 ** 3), 1),
                    "free_gb": round(usage.free / (1024 ** 3), 1),
                    "percent": usage.percent,
                })
            except Exception:
                pass

    # Battery
    battery = psutil.sensors_battery()
    bat_percent = round(battery.percent) if battery else 100
    bat_charging = battery.power_plugged if battery else True
    bat_status = "Plugged In (Charging)" if (battery and battery.power_plugged) else ("Discharging" if battery else "Desktop (AC)")

    # Network & Wi-Fi (non-blocking background refresh)
    global _CACHED_WIFI, _CACHED_LOCAL_IP, _CACHED_NET_IO, _CACHED_NET_SPEED, _CACHED_PING, _IS_REFRESHING_WIFI, _IS_REFRESHING_PING
    now_ts = time.time()
    online = is_online(timeout=0.15)
    net_status = "Connected (Online)" if online else "Offline"

    if now_ts - _CACHED_WIFI[1] > 30.0 and not _IS_REFRESHING_WIFI:
        _IS_REFRESHING_WIFI = True
        import threading
        threading.Thread(target=_bg_refresh_wifi, daemon=True).start()
    wifi_name = _CACHED_WIFI[0]

    # Hostname & IP (cached)
    hostname = socket.gethostname()
    if now_ts - _CACHED_LOCAL_IP[1] > 60.0:
        try:
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"
        _CACHED_LOCAL_IP = (local_ip, now_ts)
    else:
        local_ip = _CACHED_LOCAL_IP[0]

    # Network Speed (Download / Upload)
    dl_speed_str, ul_speed_str = _CACHED_NET_SPEED[0], _CACHED_NET_SPEED[1]
    try:
        cur_io = psutil.net_io_counters()
        last_io, last_time = _CACHED_NET_IO
        if last_io is not None and (now_ts - last_time) >= 1.0:
            dt = max(0.5, now_ts - last_time)
            rx_rate = max(0.0, (cur_io.bytes_recv - last_io.bytes_recv) / dt)
            tx_rate = max(0.0, (cur_io.bytes_sent - last_io.bytes_sent) / dt)

            def _fmt_rate(b):
                if b >= 1024 * 1024:
                    return f"{b / (1024 * 1024):.1f} MB/s"
                elif b >= 1024:
                    return f"{b / 1024:.1f} KB/s"
                return f"{int(b)} B/s"

            dl_speed_str = _fmt_rate(rx_rate)
            ul_speed_str = _fmt_rate(tx_rate)
            _CACHED_NET_SPEED = (dl_speed_str, ul_speed_str, now_ts)
            _CACHED_NET_IO = (cur_io, now_ts)
        elif last_io is None:
            _CACHED_NET_IO = (cur_io, now_ts)
    except Exception:
        pass

    # Ping latency (non-blocking background refresh)
    if (now_ts - _CACHED_PING[1]) > 10.0 and online and not _IS_REFRESHING_PING:
        _IS_REFRESHING_PING = True
        import threading
        threading.Thread(target=_bg_refresh_ping, daemon=True).start()
    ping_ms = _CACHED_PING[0]

    # OS Info
    import platform
    os_name = f"Windows {platform.release()} ({platform.machine()})"

    # Uptimes
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    sys_uptime_delta = datetime.datetime.now() - boot_time
    sys_hours, sys_rem = divmod(int(sys_uptime_delta.total_seconds()), 3600)
    sys_minutes, _ = divmod(sys_rem, 60)
    sys_uptime_str = f"{sys_hours}h {sys_minutes}m"

    session_delta = datetime.datetime.now() - SESSION_START_DT
    s_hours, s_rem = divmod(int(session_delta.total_seconds()), 3600)
    s_minutes, s_seconds = divmod(s_rem, 60)
    session_uptime_str = f"{s_hours}h {s_minutes}m {s_seconds}s" if s_hours > 0 else f"{s_minutes}m {s_seconds}s"

    # Active AI status
    gemini_client, gemini_model = get_gemini_client()
    _, ollama_model, _ = get_client_and_model()
    load_dotenv()
    engine_env = os.getenv("KIRAHT_ENGINE", "auto").strip().lower()
    if engine_env == "gemini" and gemini_client and online:
        ai_engine = f"Gemini Cloud ({gemini_model})"
        ai_provider = "Google Gemini"
    elif engine_env == "ollama":
        ai_engine = f"Local Ollama ({ollama_model})"
        ai_provider = "Local Ollama"
    else:
        ai_engine = f"Gemini Cloud ({gemini_model})" if (gemini_client and online) else f"Local Ollama ({ollama_model})"
        ai_provider = "Hybrid (Cloud/Local)"

    core_model_name = os.getenv("AI_MODEL", "qwen2.5:3b").strip() or "qwen2.5:3b"

    return {
        "timestamp": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "cpu": {
            "percent": cpu_percent,
            "cores": cpu_count,
            "frequency": freq_str,
        },
        "ram": {
            "percent": ram_percent,
            "used_gb": ram_used_gb,
            "total_gb": ram_total_gb,
        },
        "disks": disks,
        "battery": {
            "percent": bat_percent,
            "charging": bat_charging,
            "status": bat_status,
        },
        "network": {
            "online": online,
            "status": net_status,
            "ssid": wifi_name,
            "ip": local_ip,
            "hostname": hostname,
            "download": dl_speed_str,
            "upload": ul_speed_str,
            "ping": f"{ping_ms} ms",
            "connection": wifi_name if online else "Offline",
        },
        "core": {
            "ai": "ONLINE" if online else "OFFLINE",
            "memory": "ACTIVE",
            "tools": "READY",
            "search": "READY",
            "model": core_model_name,
        },
        "os": {
            "name": os_name,
            "version": platform.version(),
        },
        "uptime": {
            "system": sys_uptime_str,
            "session": session_uptime_str,
        },
        "ai": {
            "engine": ai_engine,
            "provider": ai_provider,
            "model": gemini_model if ("Gemini" in ai_engine) else ollama_model,
            "online": online,
        },
        "security": "WRITE MODE" if are_writes_allowed() else "SAFE MODE",
    }


# =====================================================================
# 5. CONNECTIVITY & WEB SEARCH
# =====================================================================
def is_online(timeout: float = 0.3) -> bool:
    """Checks if internet connection is reachable (cached for 6s for high performance)."""
    global _CACHED_ONLINE
    now_ts = time.time()
    if now_ts - _CACHED_ONLINE[1] < 6.0:
        return _CACHED_ONLINE[0]

    for host in ("1.1.1.1", "8.8.8.8"):
        try:
            s = socket.create_connection((host, 53), timeout=timeout)
            s.close()
            _CACHED_ONLINE = (True, now_ts)
            return True
        except (socket.timeout, OSError):
            continue

    _CACHED_ONLINE = (False, now_ts)
    return False


def search_web(query: str, max_results: int = 3) -> str:
    """Searches live web using DuckDuckGo and returns concise snippets."""
    if DDGS is None:
        return ""
    try:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return ""
        snippets = []
        for idx, item in enumerate(results, 1):
            title = item.get("title", "").strip()
            body = item.get("body", "").strip()
            snippets.append(f"[{idx}] {title}: {body}")
        return "\n".join(snippets)
    except Exception:
        return ""


# =====================================================================
# 6. MODEL CLIENTS (GEMINI & OLLAMA)
# =====================================================================
def get_client_and_model():
    """Initializes and caches Ollama configuration."""
    global _CACHED_OLLAMA_CLIENT, _CACHED_OLLAMA_HOST
    load_dotenv()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434"
    model = os.getenv("AI_MODEL", "qwen2.5:3b").strip() or "qwen2.5:3b"

    if _CACHED_OLLAMA_CLIENT is not None and _CACHED_OLLAMA_HOST == host:
        return _CACHED_OLLAMA_CLIENT, model, host

    client = ollama.Client(host=host)
    _CACHED_OLLAMA_CLIENT = client
    _CACHED_OLLAMA_HOST = host
    return client, model, host


def get_gemini_client():
    """Initializes and caches Google GenAI client if GEMINI_API_KEY is configured in .env."""
    global _CACHED_GEMINI_CLIENT, _CACHED_GEMINI_KEY
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    raw_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    if raw_model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash-lite"):
        model = "gemini-3.1-flash-lite"
    else:
        model = raw_model

    if not key:
        return None, model

    if _CACHED_GEMINI_CLIENT is not None and _CACHED_GEMINI_KEY == key:
        return _CACHED_GEMINI_CLIENT, model

    try:
        import logging
        logging.getLogger("google_genai").setLevel(logging.ERROR)
        from google import genai
        client = genai.Client(api_key=key)
        _CACHED_GEMINI_CLIENT = client
        _CACHED_GEMINI_KEY = key
        return client, model
    except Exception:
        return None, model


# =====================================================================
# 7. DETERMINISTIC INTENT ROUTER & TOOL DISPATCHER
# =====================================================================
# Pre-checks user query to avoid slow LLM calls for deterministic tasks

def handle_direct_file_create(cleaned: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Handles explicit file creation commands:
    e.g. 'create file add_numbers.py with content ...'
         'save file <path> with content ...'
         'write file <path> with ...'
    """
    create_match = re.search(
        r"^(?:please\s+)?(?:create|make|write|save)\s+(?:a\s+)?(?:new\s+)?file\s+([^\s:]+)\s+(?:with(?:\s+content)?|content|as)\s*[:\n]?\s*(.+)$",
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )
    if create_match:
        target_name = create_match.group(1).strip().strip("'\"")
        new_content = create_match.group(2).strip()
        from file_tools import safe_create_or_modify_file, resolve_path, KIRAHT_PROJECTS_DIR
        if not os.path.dirname(target_name) and not os.path.isabs(target_name):
            target_name = os.path.join(KIRAHT_PROJECTS_DIR, target_name)
        full_p = resolve_path(target_name)
        res = safe_create_or_modify_file(full_p, new_content, call_me=call_me)
        return True, "file_system", "safe_create_or_modify_file", f"{res}\nLocation: {full_p}"

    create_simple = re.search(
        r"^(?:please\s+)?(?:create|make|write)\s+(?:a\s+)?(?:new\s+)?file\s+([a-zA-Z0-9_\-\./\\]+)(?:\s+(?:in|inside|to)\s+(?:the\s+)?([a-zA-Z0-9_\-\./\\:'\s]+))?$",
        cleaned,
        re.IGNORECASE,
    )
    if create_simple:
        fname = create_simple.group(1).strip().strip("'\"")
        folder = create_simple.group(2).strip().strip("'\"") if create_simple.group(2) else ""
        from file_tools import safe_create_or_modify_file, resolve_path, KIRAHT_PROJECTS_DIR
        target_dir = resolve_path(folder) if folder else KIRAHT_PROJECTS_DIR
        full_p = os.path.join(target_dir, fname) if not os.path.isabs(fname) else fname
        starter = f"// {fname} - Created by KIRAHT AI\n" if fname.endswith((".ino", ".cpp", ".c", ".js")) else f"# {fname} - Created by KIRAHT AI\n"
        res = safe_create_or_modify_file(full_p, starter, call_me=call_me)
        return True, "file_system", "safe_create_or_modify_file", f"{res}\nLocation: {resolve_path(full_p)}"

    return False, "", "", ""


def handle_direct_delete(cleaned: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Directly and safely executes file and folder deletion requests.
    Supports English, Tanglish, and direct paths without requiring LLM inference.
    """
    lower = cleaned.lower()
    del_patterns = [
        r"^(?:please\s+)?(?:delete|remove|del|erase|destroy)\s+(?:the\s+)?(?:folder|directory|dir|file)?\s*([a-zA-Z0-9_\-\./\\:\'\s]+?)(?:\s+(?:folder|directory|dir|file|this folder and file))?$",
        r"^(?:please\s+)?(?:rmdir|rd|del|rm)\s+(?:/s\s+/q\s+|-[a-z]*\s+)?([a-zA-Z0-9_\-\./\\:\'\s]+)$",
        r"^([a-zA-Z0-9_\-\./\\:\'\s]+?)\s+(?:folder|file)?\s*(?:ah\s+)?(?:delete|remove)\s+(?:pannu|panniru|seithuvidu)\b",
    ]

    target_path = ""
    for pat in del_patterns:
        m = re.match(pat, lower)
        if m:
            target_path = m.group(1).strip().strip("'\"")
            target_path = re.sub(r"\s+(?:this\s+folder\s+and\s+file|this\s+folder|this\s+file)$", "", target_path).strip()
            break

    if not target_path:
        if ("delete" in lower or "remove" in lower) and any(w in lower for w in ("folder", "downloads", "directory", "file", ".ino", ".py")):
            m = re.search(r"\b(?:in|at|the)?\s*([a-zA-Z]:[\\/][a-zA-Z0-9_\-\./\\:\s]+)", cleaned)
            if m:
                target_path = m.group(1).strip().strip("'\"")

    if target_path:
        from file_tools import resolve_path, safe_delete_folder, safe_delete_file, WORKSPACE_DIR
        full_p = resolve_path(target_path)
        if not os.path.exists(full_p):
            cand = os.path.join(WORKSPACE_DIR, target_path)
            if os.path.exists(cand):
                full_p = cand

        if os.path.exists(full_p):
            if os.path.isdir(full_p):
                res = safe_delete_folder(full_p, call_me=call_me)
                return True, "file_system", "safe_delete_folder", res
            else:
                res = safe_delete_file(full_p, call_me=call_me)
                return True, "file_system", "safe_delete_file", res

    return False, "", "", ""


def try_handle_conversational_file_save(user_text: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Detects follow-up requests to save code or files from previous turns.
    e.g. 'yeah do bro', 'save it', 'do it', 'save as add_numbers.py',
         'save it in desktop', 'save in Kiraht\'s project', 'athula save pannu', etc.
    Extracts code from the last assistant message and executes the save to disk.
    """
    cleaned = user_text.strip()
    lower = cleaned.lower()

    # 0. STRICT NEGATIVE INTENT GUARD:
    # If the user explicitly says "no save", "don't save", "save panna venaam", "without saving", etc.,
    # IMMEDIATELY abort so no files are auto-saved against the user's wish.
    neg_save_pattern = r"\b(?:no\s+save|don'?t\s+save|do\s+not\s+save|never\s+save|not\s+save|without\s+saving|save\s+panna\s+venaam|save\s+venaam|venaam)\b"
    if re.search(neg_save_pattern, lower):
        return False, "", "", ""

    affirmative_patterns = [
        r"^(?:yeah|yes|yep|sure|ok|okay|do it|save it|save this|save the file|save code|save script|save|save pannu|pannu|do bro|yeah do bro|yeah do|yes do|go ahead|proceed|confirm)(?:\s+(?:bro|sir|please|it|this))?(?:\s+(?:in|to|into|inside|as)\s+(.+))?$",
        r"^(?:please\s+)?save(?:\s+this|\s+the|\s+it)?\s+(?:code|script|file)?(?:\s+(?:as|in|to|into|inside)\s+(.+))?$",
        r"^(?:please\s+)?add(?:\s+this)?\s+(?:code|file|script)\s+(?:in|to|into|inside)\s+(.+)$",
        r"^(?:athula|vera\s+folder\s+la|folder\s+la)\s+(?:code\s+)?(?:save\s+pannu|add\s+pannu|podu)\b",
    ]

    matched = False
    specified_dest = ""
    for pat in affirmative_patterns:
        m = re.match(pat, lower)
        if m:
            matched = True
            if m.groups() and m.group(1):
                specified_dest = m.group(1).strip()
            break

    # Tanglish destination syntax: "<folder> la save pannu" / "<folder> folder la save pannu"
    if not matched:
        tanglish_la = re.search(r"^([a-zA-Z0-9_\-\.:\\/ ']+?)(?:\s+folder)?\s+la\s+(?:code\s+)?(?:save\s+pannu|add\s+pannu|podu|save)\b", lower)
        if tanglish_la:
            matched = True
            cand = tanglish_la.group(1).strip()
            if cand not in ("athula", "vera", "antha", ""):
                specified_dest = cand

    if not matched:
        if re.search(r"\b(save\s+it|save\s+this|save\s+file|save\s+code|save\s+pannu|add\s+pannu)\b", lower):
            matched = True
            dest_m = re.search(r"\b(?:in|to|into|inside|as)\s+(.+)$", cleaned, re.IGNORECASE)
            if dest_m:
                specified_dest = dest_m.group(1).strip()

    if not matched:
        return False, "", "", ""

    history = load_chat_history()
    if not history:
        return False, "", "", ""

    target_assistant_msg = ""
    for msg in reversed(history[-6:]):
        if msg.get("role") == "assistant" and msg.get("content"):
            c = msg["content"]
            if "```" in c or "def " in c or "print(" in c or "input(" in c or "import " in c or "save this as a file" in c.lower() or "saved the script" in c.lower() or "python\n" in c.lower():
                target_assistant_msg = c
                break

    if not target_assistant_msg:
        return False, "", "", ""

    code_content = ""
    blocks = re.findall(r"```(?:[a-zA-Z0-9_\-\+]+)?\s*\n(.*?)```", target_assistant_msg, re.DOTALL)
    if blocks:
        code_content = blocks[-1].strip()
    else:
        code_m = re.search(r"(?:python|code:)\s*\n(.*)", target_assistant_msg, re.DOTALL | re.IGNORECASE)
        if code_m:
            raw = code_m.group(1).strip()
            code_content = re.split(r"\n\s*(?:would you like|shall i|do you want|let me know)", raw, flags=re.IGNORECASE)[0].strip()
        else:
            lines = target_assistant_msg.splitlines()
            code_lines = []
            collecting = False
            for line in lines:
                s = line.strip()
                if any(s.startswith(k) for k in ("def ", "class ", "import ", "from ", "print(", "return ", "if ", "for ", "while ")) or ("=" in s and not s.startswith("-")):
                    collecting = True
                    code_lines.append(line)
                elif collecting and (not s or s.startswith(" ") or s.startswith("\t") or s.startswith(")") or s.startswith("}")):
                    code_lines.append(line)
                elif collecting and any(q in s.lower() for q in ("would you like", "shall i", "saved as", "let me know")):
                    break
            if code_lines:
                code_content = "\n".join(code_lines).strip()

    if not code_content:
        return False, "", "", ""

    from file_tools import resolve_path, safe_create_or_modify_file, WORKSPACE_DIR, KIRAHT_PROJECTS_DIR

    filename = ""
    target_folder = KIRAHT_PROJECTS_DIR  # Default recommendation and destination!

    if specified_dest:
        dest_clean = specified_dest.strip().strip("'\"")
        dest_clean = re.sub(r"\s+(?:folder|foler|directory|dir)\s*$", "", dest_clean, flags=re.IGNORECASE).strip()
        dest_clean = re.sub(r"^(?:in|to|into|inside|as)\s+", "", dest_clean, flags=re.IGNORECASE).strip()

        # Check pattern: "<filename> in <folder>" or "<filename> to <folder>"
        split_m = re.match(r"^([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)\s+(?:in|to|into|inside)\s+(.+)$", dest_clean, re.IGNORECASE)
        if split_m:
            filename = split_m.group(1).strip()
            target_folder = resolve_path(split_m.group(2).strip())
        else:
            fn_match = re.search(r"\b([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)$", dest_clean)
            if fn_match:
                filename = fn_match.group(1)
                parent_part = dest_clean[:fn_match.start()].strip()
                parent_part = re.sub(r"^(?:in|to|into|inside|as)\s+", "", parent_part, flags=re.IGNORECASE).strip()
                if parent_part:
                    target_folder = resolve_path(parent_part)
            else:
                target_folder = resolve_path(dest_clean)

    if not filename:
        fn_in_ast = re.search(r"\b([a-zA-Z0-9_\-]+\.(?:py|ino|cpp|c|h|hpp|js|ts|html|css|json|txt|md|java|sh|bat))\b", target_assistant_msg, re.IGNORECASE)
        if fn_in_ast:
            filename = fn_in_ast.group(1)

    if not filename:
        combo = (cleaned + " " + target_assistant_msg).lower()
        if "add" in combo and "number" in combo:
            filename = "add_numbers.py"
        elif "fibonacci" in combo:
            filename = "fibonacci.py"
        elif "calculator" in combo:
            filename = "calculator.py"
        else:
            filename = "script.py"

    final_filepath = os.path.join(target_folder, filename) if not os.path.isabs(filename) else filename
    final_filepath = resolve_path(final_filepath)

    res = safe_create_or_modify_file(final_filepath, code_content, call_me=call_me)
    return True, "file_system", "safe_create_or_modify_file", f"{call_me}, I have saved the script as '{filename}' in {final_filepath}. It is ready for execution."


def handle_direct_whatsapp(cleaned: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Directly parses and executes WhatsApp messaging intents (English & Tanglish).
    Matches patterns like:
      - 'send a hi message to naveen in whatsapp'
      - 'send a hi message to group roombies in whatsapp'
      - 'send hi to naveen in whatsapp'
      - 'send hi to jailani in whatsapp'
      - 'sent whatsapp to dharma : https://pin.it/DLsW6wVCQ'
      - 'sent whatsapp dharma https://pin.it/DLsW6wVCQ'
      - 'send whatsapp to naveen : ...'
      - 'send whatsapp group roombies hi'
      - 'whatsapp roombies hello'
      - 'whatsapp naveen hi'
      - 'naveen ku whatsapp la hi nu anupu'
      - 'jailani ku whatsapp la hi nu anupu'
      - 'type hi to naveen in whatsapp'
    """
    WA_TRIGS = r"(?:whats?\s*app|whatasapp|whataspp|whatsap|whatapp|whatsappp|whatssap|watsapp|watapp|watsp|whapp|whasap|whtsp|whtsapp|wa|wp)"
    GRP_TRIGS = r"(?:group|grp|groupe|groups)"
    lower = cleaned.lower()

    # Fast reject if no WA trig, no "ku", and no send/type/msg triggers
    has_send = bool(re.search(r"\b(?:send|anupu|sent|share|forward|drop|fill|type|draft)\b", lower))
    has_wa = bool(re.search(rf"\b(?:{WA_TRIGS}|message|msg)\b", lower))
    has_ku = bool(re.search(r"\bku\b", lower))
    if not (has_wa or has_ku or has_send):
        return False, "", "", ""

    # Determine auto_send vs fill
    is_send = bool(re.search(r"\b(?:send|anupu|sent|share|forward|drop|post|shoot|blast|anupunga)\b", lower))
    is_fill = bool(re.search(r"\b(?:fill|type|draft|write|paste|just\s+type|just\s+write|review)\b", lower))
    auto_send = is_send and not is_fill

    from system_tools import resolve_contact, resolve_group, send_whatsapp_message

    target = ""
    msg = ""
    is_group = False

    # Check explicit group mentions
    if re.search(rf"\b{GRP_TRIGS}\b", lower):
        is_group = True

    # 1. Tanglish: "<target> ku (whatsapp la)? <msg> (nu)? anupu"
    t_m = re.search(
        rf"^([a-zA-Z0-9_\-\.\s]+?)\s+ku\s+(?:(?:msg|message|whatsapp|in\s+whatsapp|on\s+whatsapp)\s+)?(?:la\s+)?(.*?)(?:\s+(?:nu|solli|saying))?\s*(?:anupu|podu|send\s*pannu|anupunga|share\s*pannu)$",
        cleaned,
        re.IGNORECASE
    )
    if t_m:
        target = t_m.group(1).strip()
        msg = (t_m.group(2) or "").strip()

    # 2. "send a <msg> (message|msg) to (group)? <target> in/on/via/through whatsapp"
    # e.g. "send a hi message to naveen in whatsapp"
    if not target:
        m2 = re.search(
            rf"^(?:please\s+)?(?:send|sent|share|forward|drop|fill|type|draft)\s+(?:a\s+)?(.*?)\s+(?:message|msg)\s+to\s+(?:{GRP_TRIGS}\s+)?([a-zA-Z0-9_\-\.\s]+?)\s+(?:in|on|via|through|from)\s+{WA_TRIGS}$",
            cleaned,
            re.IGNORECASE
        )
        if m2:
            msg = m2.group(1).strip()
            target = m2.group(2).strip()

    # 3. "send/fill/type <msg> to (group)? <target> (in/on/via/through whatsapp)"
    # e.g. "send hi to naveen in whatsapp", "send hello to jailani on whatsapp"
    if not target:
        m3 = re.search(
            rf"^(?:please\s+)?(?:send|sent|share|forward|drop|fill|type|draft)\s+(.*?)\s+to\s+(?:{GRP_TRIGS}\s+)?([a-zA-Z0-9_\-\.\s]+?)\s+(?:in|on|via|through|from)\s+{WA_TRIGS}$",
            cleaned,
            re.IGNORECASE
        )
        if m3:
            msg = m3.group(1).strip()
            target = m3.group(2).strip()

    # 4. "send/draft (a)? (message|msg)? to (group)? <target> in/on/via/through whatsapp (saying|:|that)? <msg>"
    # e.g. "send to naveen in whatsapp hi", "draft message to naveen in whatsapp hi"
    if not target:
        m4 = re.search(
            rf"^(?:please\s+)?(?:send|sent|share|forward|drop|fill|type|draft)\s+(?:a\s+)?(?:message\s+|msg\s+)?to\s+(?:{GRP_TRIGS}\s+)?([a-zA-Z0-9_\-\.\s]+?)\s+(?:in|on|via|through|from)\s+{WA_TRIGS}(?:\s*(?::|saying|that)\s*|\s+)(.*)$",
            cleaned,
            re.IGNORECASE
        )
        if m4:
            target = m4.group(1).strip()
            msg = m4.group(2).strip()

    # 5. "send/sent <target> (from|on|via|through) whatsapp <msg>"
    # e.g. "send naveen from whatsapp hi", "send jailani on whatsapp hello"
    if not target:
        m5 = re.search(
            rf"^(?:please\s+)?(?:send|sent|share|forward|drop|fill|type|draft)\s+(?:{GRP_TRIGS}\s+)?([a-zA-Z0-9_\-\.\s]+?)\s+(?:from|on|via|through)\s+{WA_TRIGS}\s*(.*)$",
            cleaned,
            re.IGNORECASE
        )
        if m5:
            cand = m5.group(1).strip()
            rem = m5.group(2).strip()
            p, _, _ = resolve_contact(cand)
            g, _ = resolve_group(cand)
            if p or g or not target:
                target = cand
                msg = rem

    # 6. Prefix pattern: (send|whatsapp) (to)? (group)? <rest>
    if not target:
        m6 = re.search(
            rf"^(?:please\s+)?(?:(?:send|sent|share|forward|drop|fill|type|draft)\s+(?:a\s+)?(?:{WA_TRIGS}\s+)?(?:message|msg)?\s*(?:to\s+)?|(?:send|sent|share|forward|drop|fill|type|draft)\s+{WA_TRIGS}(?:\s+to)?|{WA_TRIGS}(?:\s+to)?|(?:send|sent|share|forward|drop|fill|type|draft)\s+(?:to\s+)?)\s*(.*)$",
            cleaned,
            re.IGNORECASE
        )
        if m6:
            rest = m6.group(1).strip()
            rest = re.sub(r"^to\s+", "", rest, flags=re.IGNORECASE).strip()

            grp_m = re.search(rf"^{GRP_TRIGS}\s+(.*)$", rest, re.IGNORECASE)
            if grp_m:
                is_group = True
                rest = grp_m.group(1).strip()

            delim = re.search(r"^(.*?)\s*(?::(?!\/\/)|saying|text:)\s*(.*)$", rest, re.IGNORECASE)
            if delim:
                target = delim.group(1).strip()
                msg = delim.group(2).strip()
            else:
                url_m = re.search(r"^(.*?)\s+(https?://\S+.*)$", rest, re.IGNORECASE)
                if url_m:
                    target = url_m.group(1).strip()
                    msg = url_m.group(2).strip()
                else:
                    words = rest.split()
                    if is_group:
                        g_exact, _ = resolve_group(rest)
                        if g_exact:
                            target = rest
                            msg = ""
                        else:
                            matched = False
                            for n in range(len(words) - 1, 0, -1):
                                cand = " ".join(words[:n])
                                c_info, _ = resolve_group(cand)
                                if c_info:
                                    target = cand
                                    msg = " ".join(words[n:])
                                    matched = True
                                    break
                            if not matched:
                                target = words[0] if words else rest
                                msg = " ".join(words[1:]) if len(words) > 1 else ""
                    else:
                        matched = False
                        for n in range(min(4, len(words) - 1), 0, -1):
                            cand = " ".join(words[:n])
                            p, _, _ = resolve_contact(cand)
                            if p:
                                target = cand
                                msg = " ".join(words[n:])
                                matched = True
                                break
                            g, _ = resolve_group(cand)
                            if g:
                                target = cand
                                msg = " ".join(words[n:])
                                is_group = True
                                matched = True
                                break
                        if not matched:
                            if len(words) == 1:
                                target = words[0]
                                msg = ""
                            else:
                                target = words[0]
                                msg = " ".join(words[1:])

    # Clean target
    target = target.strip().strip("'\"")
    grp_sub = re.sub(rf"^{GRP_TRIGS}\s+", "", target, flags=re.IGNORECASE)
    if grp_sub != target:
        is_group = True
        target = grp_sub.strip()

    target = re.sub(r"^to\s+", "", target, flags=re.IGNORECASE).strip()

    # Clean message quotes/colons
    msg = msg.strip()
    if msg.startswith(":") or msg.startswith("-"):
        msg = msg[1:].strip()
    msg = msg.strip("'\"")

    if not target:
        return False, "", "", ""

    # Ignore if user was just saying 'open whatsapp' or 'close whatsapp'
    if target.lower() in ("app", "desktop", "web", "application") and not msg:
        return False, "", "", ""

    # Check if target is a group
    g_chk, _ = resolve_group(target)
    if g_chk:
        is_group = True

    phone, disp, _ = resolve_contact(target)
    display_label = disp if disp else target.title()

    if not msg:
        return True, "whatsapp", "send_whatsapp", f"{call_me}, please specify the message to send to {display_label} (e.g. 'whatsapp {target} <message>')."

    res = send_whatsapp_message(target, msg, call_me=call_me, is_group=is_group, auto_send=auto_send)
    return True, "whatsapp", "send_whatsapp", res


def check_deterministic_intent(user_text: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Checks if user text can be answered with a 100% deterministic local tool.
    Returns: (is_handled, category, tool_name, result_string)
    """
    cleaned = user_text.strip()
    lower = cleaned.lower()

    # 0.0 Direct WhatsApp Messaging Intent (English & Tanglish)
    is_wa, wa_cat, wa_tool, wa_res = handle_direct_whatsapp(cleaned, call_me)
    if is_wa:
        return True, wa_cat, wa_tool, wa_res

    # 0.1 Folder Creation Intent (English & Tanglish)
    from tools import parse_and_create_folder
    is_folder, folder_res = parse_and_create_folder(cleaned, call_me)
    if is_folder:
        return True, "folder_create", "create_folder", folder_res

    # 0.1 File Creation & Conversational Save Intent
    is_create, f_cat, f_tool, f_res = handle_direct_file_create(cleaned, call_me)
    if is_create:
        return True, f_cat, f_tool, f_res

    is_save, s_cat, s_tool, s_res = try_handle_conversational_file_save(cleaned, call_me)
    if is_save:
        return True, s_cat, s_tool, s_res

    # 0.2 Direct File & Folder Deletion Intent
    is_del, d_cat, d_tool, d_res = handle_direct_delete(cleaned, call_me)
    if is_del:
        return True, d_cat, d_tool, d_res

    # 0.3 Follow-up Execution Intent: "execute this", "execute", "do it", "run this"
    if lower in ("execute this", "execute", "run this", "run", "do it", "pannu", "execute command", "itha execute pannu"):
        history = load_chat_history()
        last_ast = None
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("content"):
                last_ast = msg["content"]
                break
        if last_ast:
            # Check for shell deletion commands
            del_m = re.search(r"(?:rmdir\s+/s\s+/q|rd\s+/s\s+/q|del\s+/f\s+/q|del|rm)\s+([^\n`]+)", last_ast, re.IGNORECASE)
            if del_m:
                t_path = del_m.group(1).strip().strip("'\"")
                from file_tools import resolve_path, safe_delete_folder, safe_delete_file
                full_p = resolve_path(t_path)
                if os.path.exists(full_p):
                    if os.path.isdir(full_p):
                        return True, "file_system", "safe_delete_folder", safe_delete_folder(full_p, call_me=call_me)
                    else:
                        return True, "file_system", "safe_delete_file", safe_delete_file(full_p, call_me=call_me)
            # Check for code blocks to save
            save_cand = re.search(r"(?:save|create|file|code)\s+.*?([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+)", last_ast, re.IGNORECASE)
            if save_cand:
                cand_file = save_cand.group(1).strip().strip("'\"")
                code_blocks = re.findall(r"```(?:[a-zA-Z0-9_\-\+]+)?\s*\n(.*?)```", last_ast, re.DOTALL)
                if code_blocks:
                    from file_tools import resolve_path, safe_create_or_modify_file, KIRAHT_PROJECTS_DIR
                    if not os.path.dirname(cand_file) and not os.path.isabs(cand_file):
                        cand_file = os.path.join(KIRAHT_PROJECTS_DIR, cand_file)
                    full_p = resolve_path(cand_file)
                    safe_create_or_modify_file(full_p, code_blocks[0].strip(), call_me=call_me)
                    return True, "file_system", "safe_create_or_modify_file", f"{call_me}, executed save for '{os.path.basename(full_p)}'."

    # 1. Built-in Slash & System Commands
    if lower in ("/clear", "clear chat", "clear conversation"):
        clear_chat_history()
        return True, "system", "clear_chat", f"{call_me}, conversation history cleared."

    if lower in ("/memory", "view memory", "show memory"):
        mem = load_memory()
        prof = mem.get("user_profile", {})
        edu = prof.get("education", {})
        info = (
            f"User Profile Memory:\n"
            f"- Name: {mem.get('user_name')} ({prof.get('preferred_name', 'Tharik')})\n"
            f"- Title: {mem.get('call_me', 'Sir')}\n"
            f"- Education: {edu.get('degree')} ({edu.get('specialization')}) - {edu.get('year')} at {edu.get('college')}\n"
            f"- Location: {prof.get('location')}\n"
            f"- Persona: {mem.get('persona')}\n"
            f"- Response Style: {mem.get('response_style')}"
        )
        return True, "memory", "get_memory", info

    if lower.startswith("/callme "):
        new_title = cleaned[8:].strip()
        if new_title:
            mem = load_memory()
            mem["call_me"] = new_title
            save_memory(mem)
            return True, "memory", "update_callme", f"Understood. I will address you as '{new_title}' from now on."

    if lower.startswith("/name "):
        new_name = cleaned[6:].strip()
        if new_name:
            mem = load_memory()
            mem["user_name"] = new_name
            save_memory(mem)
            return True, "memory", "update_name", f"Profile updated. Registered user name: {new_name}, {call_me}."

    # 2. Math & Calculator Intent
    from tools import evaluate_math
    is_math, math_res = evaluate_math(cleaned, call_me)
    if is_math:
        return True, "calculator", "evaluate_math", math_res

    # 3. Unit Conversion Intent
    from tools import convert_units
    is_conv, conv_res = convert_units(cleaned, call_me)
    if is_conv:
        return True, "unit_converter", "convert_units", conv_res

    # 4. Weather Intent
    from tools import get_weather
    is_weather, weather_res = get_weather(cleaned, call_me)
    if is_weather:
        return True, "weather", "get_weather", weather_res

    # 5. Media & Audio Playback Control
    from tools import control_media
    is_media, media_res = control_media(cleaned, call_me)
    if is_media:
        return True, "media_control", "control_media", media_res

    # 6. QR Code Generation
    from tools import generate_qr_code
    is_qr, qr_res = generate_qr_code(cleaned, call_me)
    if is_qr:
        return True, "qr_generator", "generate_qr_code", qr_res

    # 7. Document & PDF Inspection
    from tools import inspect_document
    is_doc, doc_res = inspect_document(cleaned, call_me)
    if is_doc:
        return True, "document_tool", "inspect_document", doc_res

    # 8. Translation
    from tools import translate_text
    is_trans, trans_res = translate_text(cleaned, call_me)
    if is_trans:
        return True, "translation", "translate_text", trans_res

    # 9. Existing System & Laptop Operations (Tools Engine)
    from tools import execute_system_command
    handled, sys_res = execute_system_command(cleaned, call_me)
    if handled:
        # Check for special WhatsApp conversational tags
        if sys_res.startswith("__NEED_"):
            return True, "whatsapp", "send_whatsapp", f"{call_me}, please specify the recipient or message in WhatsApp format: 'whatsapp <name> <message>'."
        return True, "system_command", "execute_system_command", sys_res

    return False, "", "", ""


# =====================================================================
# 8. UNIFIED REAL-TIME STREAMING PIPELINE (WEBSOCKET & TERMINAL)
# =====================================================================
async def process_user_message_stream(
    user_input: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main real-time streaming processor.
    Yields event packets:
      {"type": "status", "state": "PROCESSING" | "SEARCHING" | "USING TOOL" | "RESPONDING" | "READY", "detail": "..."}
      {"type": "activity", "actor": "User" | "KIRAHT" | "System", "action": "...", "detail": "..."}
      {"type": "chunk", "text": "..."}
      {"type": "done", "full_text": "...", "meta": {...}}
    """
    cleaned = user_input.strip()
    if not cleaned:
        yield {"type": "status", "state": "READY", "detail": "Ready"}
        return

    memory = load_memory()
    call_me = memory.get("call_me", "Sir")

    # 1. Processing state & log User activity
    yield {"type": "status", "state": "PROCESSING", "detail": "Analyzing user request..."}
    yield {"type": "activity", "actor": "User", "action": "Prompt", "detail": cleaned}

    # 2. Check Deterministic Intent Router first
    is_handled, category, tool_name, result = check_deterministic_intent(cleaned, call_me)
    if is_handled:
        display_tool = tool_name
        is_screenshot = ("screenshot" in cleaned.lower() or "screen shot" in cleaned.lower() or "screenshot" in result.lower())
        if is_screenshot:
            display_tool = "screenshot"
            source_lbl = "SCREENSHOT TOOL"
        elif category == "system_command":
            lower_res = result.lower()
            lower_cmd = cleaned.lower()
            if "whatsapp" in lower_res or "whatsapp" in lower_cmd:
                display_tool = "whatsapp"
                source_lbl = "APP: WHATSAPP"
            elif "chrome" in lower_res or "chrome" in lower_cmd:
                display_tool = "chrome"
                source_lbl = "APP: CHROME"
            elif "vs code" in lower_res or "code" in lower_cmd or "vscode" in lower_res:
                display_tool = "vscode"
                source_lbl = "APP: VS CODE"
            elif "task manager" in lower_res or "taskmgr" in lower_cmd:
                display_tool = "task_manager"
                source_lbl = "APP: TASK MANAGER"
            elif "closed" in lower_res and "reopened" in lower_res:
                display_tool = "reopen_app"
                source_lbl = "TOOL: REOPEN"
            elif "closed" in lower_res:
                display_tool = "close_app"
                source_lbl = "TOOL: CLOSE"
            elif "launching" in lower_res or "launched" in lower_res:
                display_tool = "launch_app"
                source_lbl = "TOOL: LAUNCH"
            elif "volume" in lower_cmd:
                display_tool = "volume"
                source_lbl = "TOOL: VOLUME"
            elif "brightness" in lower_cmd:
                display_tool = "brightness"
                source_lbl = "TOOL: BRIGHTNESS"
            elif "battery" in lower_cmd:
                display_tool = "battery"
                source_lbl = "TOOL: BATTERY"
            elif "wifi" in lower_cmd or "wi-fi" in lower_cmd or "network" in lower_cmd:
                display_tool = "network"
                source_lbl = "TOOL: NETWORK"
            elif "clipboard" in lower_cmd:
                display_tool = "clipboard"
                source_lbl = "TOOL: CLIPBOARD"
            elif "note" in lower_cmd:
                display_tool = "notes"
                source_lbl = "TOOL: NOTES"
            else:
                display_tool = "system_tool"
                source_lbl = "SYSTEM TOOL"
        elif category == "folder_create":
            display_tool = "create_folder"
            source_lbl = "TOOL: CREATE FOLDER"
        elif category:
            source_lbl = f"TOOL: {category.replace('_', ' ').upper()}"
        else:
            source_lbl = f"TOOL: {tool_name.replace('_', ' ').upper()}"

        tool_meta = {
            "engine": "tool",
            "tool": display_tool,
            "category": category,
            "source_label": source_lbl,
        }

        if is_screenshot:
            m = re.search(r"([A-Za-z0-9_\-]+\.png)", result)
            if m:
                tool_meta["screenshot_url"] = f"/screenshots/{m.group(1)}"

        yield {"type": "status", "state": "USING TOOL", "detail": f"Using {source_lbl}"}
        yield {"type": "activity", "actor": "Tool", "action": f"Executed ({source_lbl})", "detail": result[:120]}
        await asyncio.sleep(0.05)
        yield {"type": "activity", "actor": "System", "action": "Executed", "detail": result[:120]}

        yield {"type": "status", "state": "RESPONDING", "detail": "Sending response"}
        # Stream result in pleasant token chunks
        words = result.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == len(words) - 1 else word + " "
            yield {"type": "chunk", "text": chunk}
            await asyncio.sleep(0.01)

        # Save to chat history
        add_chat_history_message("user", cleaned)
        add_chat_history_message("assistant", result, meta=tool_meta)

        yield {"type": "activity", "actor": "Tool", "action": "Tool Delivered", "detail": f"Source: {source_lbl}"}
        yield {"type": "done", "full_text": result, "meta": tool_meta}
        yield {"type": "status", "state": "READY", "detail": "Ready"}
        return

    # 3. Check for Live Web Search requirement
    from main import should_trigger_search, check_file_context
    needs_search, search_query = should_trigger_search(cleaned)
    prompt_with_context = cleaned

    if needs_search:
        if is_online():
            yield {"type": "status", "state": "SEARCHING", "detail": f"Searching web for '{search_query}'"}
            yield {"type": "activity", "actor": "KIRAHT", "action": "Searching web", "detail": f"DuckDuckGo: {search_query}"}
            # Run DuckDuckGo in thread pool to prevent blocking event loop
            snippets = await asyncio.to_thread(search_web, search_query, 3)
            if snippets:
                yield {"type": "activity", "actor": "System", "action": "Web snippets", "detail": f"Retrieved search context"}
                prompt_with_context = (
                    f"[Real-Time Live Web Search Results for '{search_query}']:\n"
                    f"{snippets}\n\n"
                    f"[User Question]:\n{cleaned}"
                )
        else:
            yield {"type": "activity", "actor": "System", "action": "Offline mode", "detail": "Web search unavailable"}

    # Check for workspace file context
    file_context = check_file_context(cleaned)
    if file_context and prompt_with_context == cleaned:
        prompt_with_context = f"{file_context}[User Question]:\n{cleaned}"

    # 4. Prepare Conversation Messages for AI Engine
    system_prompt = build_system_prompt(memory)
    messages = [{"role": "system", "content": system_prompt}]

    # Load recent conversation history if not explicitly provided
    if conversation_history is None:
        history = load_chat_history()
        # Take last 8 turns (16 messages) for multi-turn conversational context
        for msg in history[-16:]:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    else:
        for msg in conversation_history[-16:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": prompt_with_context})

    # 5. Dual-Engine Generation (Gemini Cloud preferred if online, else Ollama)
    gemini_client, gemini_model = get_gemini_client()
    ollama_client, ollama_model, ollama_host = get_client_and_model()

    load_dotenv()
    engine_preference = os.getenv("KIRAHT_ENGINE", "auto").strip().lower()
    use_gemini = (engine_preference in ("gemini", "auto")) and gemini_client and is_online()

    full_reply_chunks: List[str] = []

    if use_gemini:
        yield {"type": "status", "state": "RESPONDING", "detail": f"Generating with Gemini ({gemini_model})"}
        yield {"type": "activity", "actor": "KIRAHT", "action": "Model Inference", "detail": f"Google Gemini Cloud: {gemini_model}"}

        target_model = gemini_model
        if target_model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
            target_model = "gemini-3.1-flash-lite"

        try:
            # Build clean prompt string for Gemini
            contents = []
            for m in messages[1:]:
                role = "User" if m["role"] == "user" else "Assistant"
                contents.append(f"{role}: {m['content']}")
            full_prompt = f"{system_prompt}\n\n" + "\n\n".join(contents)

            stream_resp = await asyncio.to_thread(
                gemini_client.models.generate_content_stream,
                model=target_model,
                contents=full_prompt,
            )

            for chunk in stream_resp:
                txt = chunk.text or ""
                if txt:
                    full_reply_chunks.append(txt)
                    yield {"type": "chunk", "text": txt}
                    await asyncio.sleep(0.005)

        except Exception as gem_err:
            yield {"type": "activity", "actor": "System", "action": "Gemini Fallback", "detail": f"{gem_err}"}
            use_gemini = False

    if not use_gemini:
        # Local Ollama Streaming
        yield {"type": "status", "state": "RESPONDING", "detail": f"Generating with Ollama ({ollama_model})"}
        yield {"type": "activity", "actor": "KIRAHT", "action": "Local Inference", "detail": f"Ollama {ollama_model} @ {ollama_host}"}

        try:
            stream_resp = await asyncio.to_thread(
                ollama_client.chat,
                model=ollama_model,
                messages=messages,
                stream=True,
                options={
                    "temperature": 0.35,
                    "num_thread": 8,
                    "num_ctx": 2048,
                },
            )

            in_tool_tag = False
            for chunk in stream_resp:
                content = chunk.message.content or ""
                if not content:
                    continue

                # Filter out raw internal tool call tags
                if "<tool_call>" in content or in_tool_tag:
                    in_tool_tag = True
                    if "</tool_call>" in content:
                        in_tool_tag = False
                    continue

                full_reply_chunks.append(content)
                yield {"type": "chunk", "text": content}
                await asyncio.sleep(0.005)

        except Exception as o_err:
            err_msg = f"{call_me}, error connecting to local Ollama ({o_err}). Ensure 'ollama serve' is running."
            yield {"type": "chunk", "text": err_msg}
            full_reply_chunks.append(err_msg)

    final_text = "".join(full_reply_chunks).strip()
    if not final_text:
        final_text = f"{call_me}, systems standing by."

    # Post-generation WhatsApp Interception (Interception of WHATSAPP blocks)
    wa_matches = list(re.finditer(r"```WHATSAPP:([^:\n]+):::\s*(.*?)\s*```", final_text, re.DOTALL))
    for m in wa_matches:
        wa_target = m.group(1).strip()
        wa_msg = m.group(2).strip()
        from system_tools import send_whatsapp_message, resolve_group
        g_chk, _ = resolve_group(wa_target)
        is_grp = bool(g_chk)
        is_send = bool(re.search(r"\b(?:send|anupu|sent|share|forward|drop)\b", cleaned.lower()))
        is_fill = bool(re.search(r"\b(?:fill|type|draft|write|paste|review)\b", cleaned.lower()))
        auto_send_flag = is_send and not is_fill
        wa_res = send_whatsapp_message(wa_target, wa_msg, call_me=call_me, is_group=is_grp, auto_send=auto_send_flag)
        action_verb = "Dispatched" if auto_send_flag else "Filled"
        replacement = f"> **[WhatsApp {action_verb}]** {wa_res}"
        final_text = final_text.replace(m.group(0), replacement)
        yield {"type": "activity", "actor": "Tool", "action": f"WhatsApp {action_verb}", "detail": f"{action_verb} to {wa_target}: {wa_msg[:50]}"}

    # Post-generation Folder Interception (Interception of FOLDER_CREATE blocks)
    from file_tools import safe_create_or_modify_file, create_folder, safe_delete_folder, safe_delete_file, resolve_path
    folder_create_matches = list(re.finditer(r"```FOLDER_CREATE:([^\n]+)```", final_text))
    for m in folder_create_matches:
        f_path = m.group(1).strip().strip("'\"")
        create_folder(f_path, call_me=call_me)
        full_p = resolve_path(f_path)
        base_name = os.path.basename(full_p)
        replacement = f"> **[Folder Created]** `{base_name}` created at `{full_p}`"
        final_text = final_text.replace(m.group(0), replacement)
        yield {"type": "activity", "actor": "System", "action": "Folder Created", "detail": f"Created folder {base_name}"}

    # Post-generation Deletion Interception (Interception of DELETE_TARGET blocks)
    delete_matches = list(re.finditer(r"```DELETE_TARGET:([^\n]+)```", final_text))
    for m in delete_matches:
        d_path = m.group(1).strip().strip("'\"")
        full_p = resolve_path(d_path)
        if os.path.isdir(full_p):
            del_res = safe_delete_folder(full_p, call_me=call_me)
        else:
            del_res = safe_delete_file(full_p, call_me=call_me)
        replacement = f"> **[Action Executed]** {del_res}"
        final_text = final_text.replace(m.group(0), replacement)
        yield {"type": "activity", "actor": "System", "action": "Deleted", "detail": f"Removed {os.path.basename(full_p)}"}

    # Post-generation Ollama Bash Command Interception (e.g. rmdir /s /q ... or del ...)
    bash_del_matches = list(re.finditer(r"```(?:bash|cmd|sh|powershell)?\s*\n\s*(?:rmdir\s+/s\s+/q|rd\s+/s\s+/q|del\s+/f\s+/q|del)\s+([^\n`]+?)\s*\n```", final_text, re.IGNORECASE))
    for m in bash_del_matches:
        raw_t = m.group(1).strip().strip("'\"")
        full_p = resolve_path(raw_t)
        if os.path.exists(full_p):
            if os.path.isdir(full_p):
                del_res = safe_delete_folder(full_p, call_me=call_me)
            else:
                del_res = safe_delete_file(full_p, call_me=call_me)
            replacement = f"> **[Action Executed]** {del_res}"
            final_text = final_text.replace(m.group(0), replacement)
            yield {"type": "activity", "actor": "System", "action": "Deleted", "detail": f"Auto-executed deletion for {os.path.basename(full_p)}"}

    # Determine if user explicitly requested file creation/saving
    neg_save_pattern = r"\b(?:no\s+save|don'?t\s+save|do\s+not\s+save|never\s+save|not\s+save|without\s+saving|save\s+panna\s+venaam|save\s+venaam|venaam)\b"
    has_negative_save = bool(re.search(neg_save_pattern, cleaned, re.IGNORECASE))

    save_intent_keywords = [
        r"\b(?:save\s+it|save\s+this|save\s+the\s+file|save\s+as|save\s+to|save\s+in|save\s+into)\b",
        r"\b(?:create\s+(?:a\s+)?(?:new\s+)?file|write\s+(?:to\s+)?(?:a\s+)?file|make\s+(?:a\s+)?file)\b",
        r"\b(?:save\s+pannu|file\s+create\s+pannu|athula\s+save|podu\s+file|add\s+pannu)\b",
        r"\b(?:la\s+save\s+pannu|folder\s+la\s+save)\b",
        r"^(?:yes|yeah|sure|ok|okay|do it|proceed|confirm)\b",
    ]
    has_save_intent = (not has_negative_save) and any(re.search(pat, cleaned, re.IGNORECASE) for pat in save_intent_keywords)

    # Post-generation File Interception (Interception of FILE_SAVE blocks)
    file_save_matches = list(re.finditer(r"```FILE_SAVE:([^\n]+)\n(.*?)```", final_text, re.DOTALL))
    for m in file_save_matches:
        save_path = m.group(1).strip().strip("'\"")
        file_content = m.group(2)
        base_name = os.path.basename(save_path)
        ext = os.path.splitext(save_path)[1].lstrip(".") or "python"

        # Safety Check: If user asked for a folder, redirect to folder creation
        if re.search(r"\b(?:folder|dir|directory)\b", cleaned, re.IGNORECASE) and not os.path.splitext(save_path)[1]:
            full_p = resolve_path(save_path)
            create_folder(full_p, call_me=call_me)
            bname = os.path.basename(full_p)
            replacement = f"> **[Folder Created]** `{bname}` created at `{full_p}`"
            final_text = final_text.replace(m.group(0), replacement)
            yield {"type": "activity", "actor": "System", "action": "Folder Created", "detail": f"Created folder {bname}"}
            continue

        if not has_save_intent:
            # DO NOT AUTO-SAVE! User asked for code/help, not to write to disk.
            # Convert FILE_SAVE block to a standard syntax-highlighted code block:
            rec_offer = (
                f"\n\n*Shall I save this code for you, {call_me}? I recommend saving it in `kiraht's project/{base_name}`. "
                f"(Or let me know if you prefer another folder like Downloads or Desktop!)*"
            )
            if not any(q in final_text.lower() for q in ("shall i save", "save pannata", "would you like me to save", "recommend saving")):
                replacement = f"```{ext}\n{file_content}\n```{rec_offer}"
            else:
                replacement = f"```{ext}\n{file_content}\n```"
            final_text = final_text.replace(m.group(0), replacement)
            yield {"type": "activity", "actor": "System", "action": "Code Generated", "detail": f"Generated code for {base_name} (Awaiting confirmation)"}
            continue

        # User explicitly requested to save:
        from file_tools import KIRAHT_PROJECTS_DIR, WORKSPACE_DIR
        full_p = resolve_path(save_path)
        norm_dir = os.path.normpath(os.path.dirname(full_p))
        if norm_dir == os.path.normpath(WORKSPACE_DIR) and not re.search(r"\b(?:workspace|root)\b", cleaned, re.IGNORECASE):
            full_p = os.path.join(KIRAHT_PROJECTS_DIR, base_name)
            full_p = resolve_path(full_p)

        safe_create_or_modify_file(full_p, file_content, call_me=call_me)
        replacement = f"```{ext}\n{file_content}\n```\n\n> **[File Saved]** `{base_name}` saved to `{full_p}`"
        final_text = final_text.replace(m.group(0), replacement)
        yield {"type": "activity", "actor": "System", "action": "File Saved", "detail": f"Saved {base_name} to {full_p}"}

    # If code was generated via regular markdown blocks without FILE_SAVE, and user didn't request save:
    # Ensure we ask the user if they'd like to save it in Kiraht's project
    if not has_save_intent and not file_save_matches:
        code_blocks = re.findall(r"```(?:[a-zA-Z0-9_\-\+]+)?\s*\n(.*?)```", final_text, re.DOTALL)
        if any(len(b.strip().splitlines()) >= 3 for b in code_blocks):
            if not any(q in final_text.lower() for q in ("shall i save", "save pannata", "would you like me to save", "recommend saving", "save this as a file")):
                fn_m = re.search(r"\b([a-zA-Z0-9_\-]+\.(?:py|ino|cpp|c|h|hpp|js|ts|html|css|json|txt))\b", final_text, re.IGNORECASE)
                suggested_fn = fn_m.group(1) if fn_m else "script.py"
                is_tanglish_prompt = any(w in cleaned.lower() for w in ("laam", "keta", "pannu", "venum", "sollu", "iruku", "enna", "epdi"))
                if is_tanglish_prompt:
                    final_text += f"\n\n*Sir, intha code-ah save pannata? `kiraht's project/{suggested_fn}`-la save panna recommend panren. Vera folder venaalum sollunga!*"
                else:
                    final_text += f"\n\n*Shall I save this code for you, {call_me}? I recommend saving it to `kiraht's project/{suggested_fn}`. (Or let me know if you prefer another folder like Downloads or Desktop!)*"

    # Save completed exchange into persistent local chat_history.json
    source_label = f"GEMINI CLOUD ({target_model})" if use_gemini else f"OLLAMA LOCAL ({ollama_model})"
    engine_name = "gemini" if use_gemini else "ollama"
    meta_info = {
        "engine": engine_name,
        "model": target_model if use_gemini else ollama_model,
        "source_label": source_label,
    }

    add_chat_history_message("user", cleaned)
    add_chat_history_message("assistant", final_text, meta=meta_info)

    yield {"type": "activity", "actor": "KIRAHT", "action": "Response Delivered", "detail": f"Engine Source: {source_label}"}
    yield {"type": "done", "full_text": final_text, "meta": meta_info}
    yield {"type": "status", "state": "READY", "detail": "Ready"}

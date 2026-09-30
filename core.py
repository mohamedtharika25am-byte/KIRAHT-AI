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
    """Clears persistent conversation history in chat_history.json."""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as err:
        print(f"[!] Warning: Failed to clear chat history: {err}")


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

    # Network & Wi-Fi (cached for 12 seconds to prevent blocking event loop)
    global _CACHED_WIFI, _CACHED_LOCAL_IP, _CACHED_NET_IO, _CACHED_NET_SPEED, _CACHED_PING
    now_ts = time.time()
    online = is_online(timeout=0.3)
    net_status = "Connected (Online)" if online else "Offline"

    if now_ts - _CACHED_WIFI[1] > 12.0:
        wifi_name = "Wi-Fi"
        try:
            from system_tools import get_wifi_status
            raw_wifi = get_wifi_status(call_me="Sir")
            match = re.search(r"SSID\s*:\s*([^\n,]+)", raw_wifi)
            if match:
                wifi_name = match.group(1).strip()
        except Exception:
            pass
        _CACHED_WIFI = (wifi_name, now_ts)
    else:
        wifi_name = _CACHED_WIFI[0]

    # Hostname & IP (cached)
    hostname = socket.gethostname()
    if now_ts - _CACHED_LOCAL_IP[1] > 30.0:
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

    # Ping latency
    ping_ms = _CACHED_PING[0]
    if (now_ts - _CACHED_PING[1]) > 5.0 and online:
        try:
            t0 = time.time()
            s = socket.create_connection(("1.1.1.1", 53), timeout=0.3)
            s.close()
            ping_ms = max(1, int((time.time() - t0) * 1000))
            _CACHED_PING = (ping_ms, now_ts)
        except Exception:
            try:
                t0 = time.time()
                s = socket.create_connection(("8.8.8.8", 53), timeout=0.3)
                s.close()
                ping_ms = max(1, int((time.time() - t0) * 1000))
                _CACHED_PING = (ping_ms, now_ts)
            except Exception:
                ping_ms = 24

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

def check_deterministic_intent(user_text: str, call_me: str = "Sir") -> Tuple[bool, str, str, str]:
    """
    Checks if user text can be answered with a 100% deterministic local tool.
    Returns: (is_handled, category, tool_name, result_string)
    """
    cleaned = user_text.strip()
    lower = cleaned.lower()

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
        yield {"type": "status", "state": "USING TOOL", "detail": f"Using {tool_name}"}
        yield {"type": "activity", "actor": "KIRAHT", "action": f"Tool: {tool_name}", "detail": f"Category: {category}"}
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
        add_chat_history_message("assistant", result, meta={"tool": tool_name, "category": category})

        yield {"type": "done", "full_text": result, "meta": {"tool": tool_name, "category": category}}
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

    # Save completed exchange into persistent local chat_history.json
    add_chat_history_message("user", cleaned)
    add_chat_history_message("assistant", final_text, meta={"engine": "gemini" if use_gemini else "ollama"})

    yield {"type": "done", "full_text": final_text, "meta": {"engine": "gemini" if use_gemini else "ollama"}}
    yield {"type": "status", "state": "READY", "detail": "Ready"}

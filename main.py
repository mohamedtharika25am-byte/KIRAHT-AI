"""
KIRAHT AI - Version 0.2
A local, intelligent personal AI assistant.

Key Features:
- Live Token Streaming (immediate word-by-word terminal response).
- Elite Persona: Razor-sharp, polite, concise, and strictly to the point.
- Persistent Memory (memory.json): Remembers user name, title ("Sir"), and preferences across sessions.
- Hybrid Internet Awareness:
    * Online: Live DuckDuckGo search for real-time news, dates, and updates.
    * Offline: Gracefully falls back to local Ollama model knowledge.
- In-memory multi-turn conversation history with session commands (/memory, /callme, /search, /clear).
- 100% local model inference (qwen2.5:3b or custom) via native Ollama client.
"""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from dotenv import load_dotenv
import httpx
import ollama
from tools import execute_system_command

# Attempt imports for DuckDuckGo search (supports both ddgs and duckduckgo_search)
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

# Configure UTF-8 output encoding on Windows terminals to support emojis and unicode
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
KNOWLEDGE_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_cache.json")

DEFAULT_MEMORY = {
    "user_name": "Tharik",
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


# ==========================================
# 1. PERSISTENT MEMORY MANAGEMENT
# ==========================================
def load_memory() -> dict:
    """
    Loads persistent user profile and preferences from memory.json.
    Creates default memory.json if not present.
    """
    if not os.path.exists(MEMORY_FILE):
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all default keys exist
            for key, val in DEFAULT_MEMORY.items():
                if key not in data:
                    data[key] = val
            return data
    except Exception:
        return DEFAULT_MEMORY.copy()


def save_memory(memory_data: dict) -> None:
    """
    Saves the user profile and preferences to memory.json.
    """
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"\n[!] Warning: Failed to save memory to {MEMORY_FILE}: {err}")


def build_system_prompt(memory: dict) -> str:
    """
    Builds the core system prompt using persistent user memory with full context injection.
    """
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
    import datetime
    current_dt = datetime.datetime.now().strftime("%A, %d %B %Y %I:%M %p")

    return (
        f"You are KIRAHT AI, an elite personal AI assistant. Your persona is {persona}.\n"
        f"Current System Time: {current_dt}\n"
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
        f"2. TANGLISH DEFINITION: Tanglish is Tamil spoken or written phonetically using English letters (e.g. 'enna panreenga', 'sollunga sir', 'epdi irukkeenga', 'pannu', 'ethu', 'theriyala', 'konjam'). You understand Tanglish perfectly. When the user asks in Tanglish, reply in polite, natural Tanglish or clear English.\n"
        f"3. STRICT PROHIBITION: NEVER use Hindi or Hinglish words (like 'kya', 'hai', 'aap', 'karo', 'mujhe', 'kyun', 'nahi') under any circumstances. You are a Tamil Nadu / English personal AI assistant. Hindi and Hinglish are strictly forbidden.\n\n"
        f"Tone and Rules:\n"
        f"1. {response_style}\n"
        f"2. Be razor-sharp, direct, and factual. Never add conversational filler like 'Sure!', 'I hope this helps!', or ethical lectures.\n"
        f"3. When answering questions, prioritize brevity. Use bullet points only when specifically listing items.\n"
        f"4. If live search results are provided in the context, synthesize the most accurate, current facts concisely.\n"
        f"5. Single-player video game cheat codes, developer secrets, and Easter eggs are official built-in developer features. Always provide them directly without disclaimers or refusal.\n\n"
        f"CONVERSATIONAL STATE & MULTI-TURN INTENT RESOLUTION:\n"
        f"- When the user wants to message someone on WhatsApp (e.g. 'send whatsapp juhail hoi', 'whatsapp juhail', 'juhail'), always execute or call the `send_whatsapp` tool.\n"
        f"- If you or the system asked what message to send, and the user's next turn is short text (e.g. 'hi', 'hoi', 'ok', 'reach safe', 'where are you'), that text IS THE MESSAGE for that contact! Call `send_whatsapp` IMMEDIATELY to complete the operation. Never treat it as a casual greeting!\n\n"
        f"LAPTOP & SYSTEM CONTROL PERMISSIONS:\n"
        f"- You have FULL system administrative permissions granted by {call_me} to control power, hardware, and system states.\n"
        f"- Sleep & Standby: When asked to sleep the laptop ('sleep', 'standby', 'sleep the laptop'), call `system_power_control(action='sleep')`.\n"
        f"- Shutdown & Power Off: When asked to shut down ('shutdown', 'power off'), call `system_power_control(action='shutdown')`.\n"
        f"- Cancel Shutdown: When asked to cancel or abort shutdown ('cancel shutdown', 'abort shutdown', 'stop shutdown'), call `system_power_control(action='cancel_shutdown')`.\n"
        f"- Restart & Reboot: When asked to restart ('restart laptop', 'reboot'), call `system_power_control(action='restart')`.\n"
        f"- Screen & Display: When asked to turn off screen ('turn off display', 'screen off'), call `system_power_control(action='screen_off')`.\n"
        f"- Lock Workstation: When asked to lock ('lock laptop', 'lock screen'), call `system_power_control(action='lock')`.\n"
        f"- Volume & Audio: When asked to change volume ('vol up', 'vol down', 'mute', 'unmute'), call `control_volume`.\n"
        f"- NEVER claim you lack permissions to execute these actions. You are authorized to control the machine as requested.\n\n"
        f"PROGRAMMING, KNOWLEDGE & CONCEPTUAL QUERIES:\n"
        f"- You are an elite AI engineer, programmer, and knowledgeable companion.\n"
        f"- When {call_me} asks for an example, explanation, coding snippet, or algorithm (e.g. 'deque example', 'binary search', 'how to sort in python'):\n"
        f"  IMMEDIATELY provide clean, working code examples and clear explanations without hesitation.\n"
        f"- NEVER mention function tools, function signatures, or tool sets when {call_me} asks a programming, educational, or conceptual question.\n\n"
        f"Persistent Directives:\n"
        f"{notes_str}"
    )


# ==========================================
# 2. CONNECTIVITY & WEB SEARCH
# ==========================================
def is_online(timeout: float = 1.5) -> bool:
    """
    Quickly checks if internet connection is reachable via DNS lookup.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname("duckduckgo.com")
        return True
    except (socket.gaierror, OSError):
        return False


def search_web(query: str, max_results: int = 3) -> str:
    """
    Searches the live web using DuckDuckGo and returns concise summary snippets.
    """
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


# ==========================================
# 2. KNOWLEDGE CACHE & IDENTITY GUARD
# ==========================================
def load_knowledge_cache() -> dict:
    """
    Loads persistent knowledge cache from knowledge_cache.json.
    """
    if not os.path.exists(KNOWLEDGE_CACHE_FILE):
        return {}
    try:
        with open(KNOWLEDGE_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_knowledge_cache(cache: dict) -> None:
    """
    Saves the knowledge cache to knowledge_cache.json.
    """
    try:
        with open(KNOWLEDGE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print(f"\n[!] Warning: Failed to save knowledge cache: {err}")


def find_cached_knowledge(user_text: str, cache: dict) -> tuple[bool, str]:
    """
    Checks if the user query matches any learned topic in knowledge_cache.json.
    Returns (found, summary).
    """
    if not cache:
        return False, ""

    clean_query = re.sub(r"[^\w\s]", " ", user_text.lower()).strip()
    query_words = set(clean_query.split())

    for key, data in cache.items():
        clean_key = re.sub(r"[^\w\s]", " ", key.lower()).strip()
        topic = re.sub(r"[^\w\s]", " ", data.get("topic", "").lower()).strip()

        # Direct phrase match in query
        if clean_key and clean_key in clean_query:
            return True, data.get("summary", "")
        if topic and topic in clean_query:
            return True, data.get("summary", "")

        # Key words subset check (e.g. key='tn cm', query='who is the tn cm now')
        key_words = set(clean_key.split())
        if key_words and key_words.issubset(query_words):
            return True, data.get("summary", "")

    return False, ""


def add_to_knowledge_cache(query: str, answer: str) -> None:
    """
    Caches a newly searched fact into knowledge_cache.json for future instant lookup.
    """
    if not answer or len(answer.strip()) < 10:
        return

    # Normalize query into a concise topic key
    clean = re.sub(r"^(who is|what is|tell me about|how is|which is|search for|latest|current)\s+", "", query.lower().strip())
    clean = re.sub(r"[^\w\s]", " ", clean).strip()
    key = clean if clean else query.lower()[:30]

    cache = load_knowledge_cache()
    from datetime import date
    cache[key] = {
        "topic": query.strip(),
        "summary": answer.strip(),
        "updated_at": str(date.today()),
    }
    save_knowledge_cache(cache)


def is_identity_query(user_text: str) -> bool:
    """
    Returns True if the query asks about the user, assistant creator, or boss identity.
    Prevents accidental web searches for personal identity queries.
    """
    lower = user_text.lower().strip()

    # Boss / Creator words (substring matching catches typos and compound words)
    boss_indicators = ("boss", "creator", "created", "developer", "master", "owner", "maker", "made you", "programmed you")
    if any(b in lower for b in boss_indicators):
        return True

    # User identity phrases
    user_phrases = ("who am i", "my name", "about me", "my college", "my project", "my degree", "what is my name", "do you know me")
    if any(phrase in lower for phrase in user_phrases):
        return True

    # Assistant identity phrases
    asst_phrases = ("who are you", "what are you", "what is your name", "your name", "tell me about yourself")
    if any(phrase in lower for phrase in asst_phrases):
        return True

    return False


def should_trigger_search(user_text: str) -> tuple[bool, str]:
    """
    Determines if the user's input asks for current/real-time information
    or explicitly requests a search.
    Returns (needs_search, search_query).
    """
    cleaned = user_text.strip()

    # Never trigger web search for identity or personal queries
    if is_identity_query(cleaned):
        return False, ""

    # Explicit command triggers: /search, search:, google:, find online:, etc.
    for prefix in ("/search ", "search:", "search for ", "google:", "google ", "find online ", "look up ", "source for "):
        if cleaned.lower().startswith(prefix):
            return True, cleaned[len(prefix):].strip()

    # Tanglish search triggers
    tanglish_search = re.search(r"^(?:net\s+la|internet\s+la|google\s+la)\s+(?:thedu|paaru|search\s+pannu)\s+(.*)$", cleaned, re.IGNORECASE)
    if tanglish_search:
        return True, tanglish_search.group(1).strip()

    tanglish_search_end = re.search(r"^(.*?)\s+(?:pathu\s+sollu|thedi\s+sollu|search\s+panni\s+sollu|net\s+la\s+thedu)$", cleaned, re.IGNORECASE)
    if tanglish_search_end:
        return True, tanglish_search_end.group(1).strip()

    # Time-sensitive and real-time query keywords
    triggers = [
        r"\btoday\b",
        r"\blatest\b",
        r"\bcurrent\b",
        r"\bnews\b",
        r"\bweather\b",
        r"\bscore\b",
        r"\bprice\b",
        r"\bwho won\b",
        r"\brecent\b",
        r"\bupdate\b",
        r"\byesterday\b",
        r"\btomorrow\b",
        r"\bnow\b",
        r"\b2025\b",
        r"\b2026\b",
        r"\bcm\b",
        r"\bpm\b",
        r"\bchief minister\b",
        r"\bprime minister\b",
        r"\bpresident\b",
        r"\bceo\b",
        r"^who is\b",
        r"\bcheat\b",
        r"\bcheats\b",
        r"\bgta\b",
    ]

    lower = cleaned.lower()
    for pattern in triggers:
        if re.search(pattern, lower):
            return True, cleaned

    return False, ""


def should_enable_tools(user_text: str) -> bool:
    """
    Determines if the user's input is an actionable laptop/system control command
    that requires native function tool calling.

    Returns False for questions, explanations, coding requests, internet lookups,
    and conversational prompts so the model uses its full knowledge and streams
    direct answers instead of hallucinating tool signature mismatches.
    """
    lower = user_text.lower().strip()

    # 1. Obvious question, educational, algorithmic, conceptual queries -> NEVER pass tools
    coding_and_question_patterns = [
        r"\bexample\b",
        r"\bhow\s+to\b",
        r"\bhow\s+do\b",
        r"\bwhat\s+is\b",
        r"\bwhat\s+are\b",
        r"\bwhy\s+is\b",
        r"\bwhy\s+does\b",
        r"\bexplain\b",
        r"\bmeaning\b",
        r"\bdifference\b",
        r"\btutorial\b",
        r"\bteach\b",
        r"\bwrite\s+(?:a\s+)?(?:code|script|program|function|class|essay|story|poem)\b",
        r"\bpython\b",
        r"\bjava\b",
        r"\bc\+\+\b",
        r"\bjavascript\b",
        r"\balgorithm\b",
        r"\bdata\s+structure\b",
        r"\bdeque\b",
        r"\bstack\b",
        r"\bqueue\b",
        r"\bleetcode\b",
        r"\bsolve\b",
        r"\bdebug\b",
        r"\berror\b",
        r"\bissue\b",
        r"\bconcept\b",
        r"\bsummarize\b",
        r"\bnotes\s+on\b",
        r"\bwho\s+is\b",
        r"\bwhere\s+is\b",
        r"\bwhich\s+is\b",
        r"\bwhen\s+did\b",
        r"\bcan\s+you\s+explain\b",
        r"\btell\s+me\s+about\b",
        r"\bguide\b",
        r"\bdefinition\b",
        r"\bsyntax\b",
        r"\bimplementation\b",
        r"\binterview\b",
        r"\bquestions?\b",
    ]
    for p in coding_and_question_patterns:
        if re.search(p, lower):
            return False

    # 2. Tanglish question and conversation patterns -> NEVER pass tools
    tanglish_questions = [
        r"\benna\b",
        r"\bepdi\b",
        r"\bethuku\b",
        r"\byaru\b",
        r"\btheriyuma\b",
        r"\bsolli\s*kudu\b",
        r"\bpurila\b",
        r"\bpaaru\b",
        r"\bsollu\b",
        r"\bennalam\b",
        r"\bpanreenga\b",
        r"\bseiya\b",
    ]
    for p in tanglish_questions:
        if re.search(p, lower):
            return False

    # 3. Actionable system command patterns
    action_triggers = [
        r"\b(?:open|launch|start|run)\s+[a-zA-Z0-9_\-\.\s]+",
        r"\b(?:close|kill|quit|terminate)\s+[a-zA-Z0-9_\-\.\s]+",
        r"\b(?:vol|volume|sound|mute|unmute)\b",
        r"\b(?:sleep|standby|shutdown|shut\s*down|reboot|restart|power\s*off|screen\s*off|lock\s*screen|lock\s*pc|lock\s*laptop)\b",
        r"\b(?:brightness|dim|dimmer)\b",
        r"\b(?:running\s+processes|top\s+processes|task\s*manager|cpu\s+usage|ram\s+usage)\b",
        r"\b(?:battery|wifi|wi-fi|ssid|ping\s+latency)\b",
        r"\b(?:search\s+file|find\s+file|read\s+file)\b",
        r"\b(?:whatsapp|whatsap|watsapp|send\s+message)\b",
    ]
    for p in action_triggers:
        if re.search(p, lower):
            return True

    return False


def check_file_context(user_text: str) -> str:
    """
    If the user asks to explain, review, or debug a workspace file,
    reads the initial lines of that file and returns context for the LLM.
    """
    lower = user_text.lower()
    keywords = ("explain", "review", "analyze", "what does", "check", "debug", "fix", "summarize", "look at")
    if not any(k in lower for k in keywords):
        return ""

    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        entries = os.listdir(workspace_dir)
        for entry in entries:
            if entry.startswith(".") or entry in ("__pycache__", "apps_cache.json"):
                continue
            if entry.lower() in lower:
                filepath = os.path.join(workspace_dir, entry)
                if os.path.isfile(filepath):
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        lines = [f.readline() for _ in range(80)]
                        snippet = "".join(lines).rstrip()
                    return f"[Workspace Code Context for '{entry}' ({len(lines)} lines)]:\n{snippet}\n\n"
    except Exception:
        pass
    return ""


# ==========================================
# 3. OLLAMA CLIENT & INITIALIZATION
# ==========================================
def find_ollama_executable() -> str | None:
    """
    Locates the ollama CLI executable on the system.
    """
    exe = shutil.which("ollama")
    if exe:
        return exe
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
        os.path.expandvars(r"%ProgramFiles%\Ollama\ollama.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Ollama\ollama.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def is_ollama_endpoint_alive(url: str, timeout: float = 1.0) -> bool:
    """
    Quickly probes whether an Ollama host URL is responsive.
    """
    try:
        req = urllib.request.Request(url.rstrip("/") + "/", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_client_and_model():
    """
    Loads configuration from environment / .env file and initializes the Ollama client.
    """
    load_dotenv()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434"
    model = os.getenv("AI_MODEL", "qwen2.5:3b").strip() or "qwen2.5:3b"
    client = ollama.Client(host=host)
    return client, model, host


def verify_and_ensure_ollama(model: str, initial_host: str) -> tuple[ollama.Client, str]:
    """
    Verifies that the local Ollama daemon is reachable and the requested model exists.
    If Ollama is not running, attempts to start 'ollama serve' in the background.
    Supports localhost/127.0.0.1 dual-fallback for Windows IPv4/IPv6 compatibility.
    """
    candidates = [initial_host]
    if "localhost" in initial_host:
        candidates.append(initial_host.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in initial_host:
        candidates.append(initial_host.replace("127.0.0.1", "localhost"))

    # 1. Check if Ollama is already active on any candidate host
    working_host = None
    for h in candidates:
        if is_ollama_endpoint_alive(h, timeout=0.8):
            working_host = h
            break

    # 2. If not running, attempt auto-starting
    if not working_host:
        ollama_bin = find_ollama_executable()
        if ollama_bin:
            print(f"\n[i] Ollama server is not running on {initial_host}.")
            print(f"[*] Starting local Ollama service in the background ('{ollama_bin} serve')...")

            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            try:
                subprocess.Popen(
                    [ollama_bin, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=flags,
                    close_fds=True if sys.platform != "win32" else False,
                )
            except Exception as e:
                print(f"[!] Could not launch Ollama daemon automatically: {e}")

            # Wait up to 12 seconds for Ollama to become responsive
            start_t = time.time()
            while time.time() - start_t < 12:
                time.sleep(0.8)
                for h in candidates:
                    if is_ollama_endpoint_alive(h, timeout=0.8):
                        working_host = h
                        break
                if working_host:
                    print(f"[✓] Ollama server is up and responsive at {working_host}!\n")
                    break
                print(".", end="", flush=True)
            print()

    # 3. If still unreachable, show helpful instructions and exit
    if not working_host:
        print(f"\n[!] Connection Error: Unable to connect to Ollama at {initial_host}.")
        print("    Ensure Ollama is installed and running:")
        print("      1. Open a terminal and run: ollama serve")
        print("      2. Or launch the Ollama desktop app from the Start menu.")
        print("      3. If not installed, download from: https://ollama.com\n")
        sys.exit(1)

    # 4. Initialize client with verified working host
    client = ollama.Client(host=working_host)

    # 5. Model presence check
    try:
        response = client.list()
        available_models = []
        for item in response.models:
            name = getattr(item, "model", None) or getattr(item, "name", None)
            if name:
                available_models.append(name)

        model_found = any(
            m == model or m.startswith(f"{model}:") or model.startswith(f"{m}:")
            for m in available_models
        )

        if not model_found:
            print(f"\n[!] Model Error: Model '{model}' was not found in your local Ollama library.")
            print("    Available installed models:")
            if available_models:
                for m in available_models:
                    print(f"      - {m}")
            else:
                print("      (No models found in local library)")
            print(f"\n    To install it, run:")
            print(f"      ollama pull {model}")
            print(f"    Or change AI_MODEL in your .env file to an available model.\n")
            sys.exit(1)

    except Exception as err:
        print(f"\n[!] Unexpected Error while checking Ollama models: {err}\n")
        sys.exit(1)

    return client, working_host


def verify_ollama_status(client: ollama.Client, model: str, host: str) -> None:
    """
    Backwards-compatible wrapper that delegates to verify_and_ensure_ollama.
    """
    verify_and_ensure_ollama(model, host)


# ==========================================
# 4. MULTILINE INPUT BUFFER & AGENT TOOLS
# ==========================================
def get_user_input_multiline(prompt_text: str = "\nYou: ") -> str:
    """
    Reads terminal input. If the user pastes multiple lines, captures
    all lines from the console buffer and combines them into a single line.
    """
    sys.stdout.write(prompt_text)
    sys.stdout.flush()

    first_line = sys.stdin.readline()
    if not first_line:
        return ""

    lines = [first_line.rstrip("\r\n")]

    if sys.platform == "win32":
        try:
            import msvcrt
            time.sleep(0.04)  # brief 40ms pause to catch paste chunks
            while msvcrt.kbhit():
                extra = sys.stdin.readline()
                if not extra:
                    break
                lines.append(extra.rstrip("\r\n"))
                time.sleep(0.01)
        except Exception:
            pass

    return " ".join(part.strip() for part in lines if part.strip())


AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_running_processes",
            "description": "Inspects active running applications, top memory-consuming processes, and overall system RAM/CPU load on the user's laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of top processes to return (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_brightness",
            "description": "Retrieves the current laptop display screen brightness level percentage.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_screen_brightness",
            "description": "Sets the laptop screen brightness to a specific percentage (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Brightness percentage from 0 to 100"}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_screen_brightness",
            "description": "Increases or decreases laptop screen brightness by a delta amount (e.g. +15 for brighter, -15 for dimmer).",
            "parameters": {
                "type": "object",
                "properties": {
                    "delta": {"type": "integer", "description": "Positive integer to brighten, negative to dim"}
                },
                "required": ["delta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_volume",
            "description": "Controls Windows master audio volume: set exact level %, adjust up/down delta, or mute/unmute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["set", "increase", "decrease", "mute", "unmute"]},
                    "value": {"type": "integer", "description": "Volume percentage level (0-100) or delta amount (10, 15, etc.)"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_power_control",
            "description": "Performs Windows system power operations: put laptop to sleep / standby, shutdown PC, restart PC, cancel/abort pending shutdown, hibernate, lock workstation, or turn off display.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["sleep", "shutdown", "restart", "abort_shutdown", "hibernate", "screen_off", "lock"],
                        "description": "The exact power or security operation to execute"
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_or_read_file",
            "description": "Searches for files across Workspace, Downloads, Desktop, and Documents, or reads file content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "read", "info"], "description": "search by name, read content, or get file size/info"},
                    "target": {"type": "string", "description": "Filename or keyword to search/read"},
                    "location": {"type": "string", "enum": ["all", "workspace", "downloads", "desktop", "documents"], "description": "Which folder to look in"}
                },
                "required": ["action", "target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launches an installed Windows desktop application (e.g. Task Manager, Chrome, WhatsApp, Android Studio, VS Code, Spotify, Notepad, Calculator). Only call this when user explicitly names an application to open.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to open"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Closes or terminates a running Windows application by process name or window title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to close (e.g. chrome, notepad, spotify)"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_metrics",
            "description": "Retrieves battery percentage, charging status, Wi-Fi network SSID, and ping latency.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_identity",
            "description": "Retrieves the user's complete profile, education, projects, and personal memory from memory.json.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_whatsapp",
            "description": "Sends or opens a WhatsApp message to a contact, group, or phone number on the user's laptop. Always call this tool when user wants to send a WhatsApp message or provides the message content in a follow-up turn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Contact name, group name, or phone number (e.g. 'juhail', 'rahul', 'mom', 'roombies')"},
                    "message": {"type": "string", "description": "The exact message text to send to the recipient"},
                    "is_group": {"type": "boolean", "description": "True if sending to a WhatsApp group, False for individual"}
                },
                "required": ["recipient", "message"]
            }
        }
    }
]


def execute_agent_tool(tool_name: str, args: dict, call_me: str = "Sir") -> str:
    """
    Executes native tool call dispatched by Ollama model and returns output string.
    """
    try:
        if tool_name == "get_running_processes":
            from system_tools import get_running_processes
            limit = args.get("limit", 10)
            return get_running_processes(limit=limit, call_me=call_me)

        elif tool_name == "get_screen_brightness":
            from system_tools import get_screen_brightness
            return get_screen_brightness(call_me=call_me)

        elif tool_name == "set_screen_brightness":
            from system_tools import set_screen_brightness
            level = args.get("level", 50)
            return set_screen_brightness(level=level, call_me=call_me)

        elif tool_name == "adjust_screen_brightness":
            from system_tools import adjust_screen_brightness
            delta = args.get("delta", 15)
            return adjust_screen_brightness(delta=delta, call_me=call_me)

        elif tool_name == "control_volume":
            from system_tools import set_volume_level, adjust_volume_delta, adjust_volume, toggle_mute
            action = args.get("action", "set")
            val = args.get("value", 50)
            if action == "set":
                return set_volume_level(val, call_me=call_me)
            elif action in ("increase", "up"):
                return adjust_volume_delta(val if val and val > 0 else 15, call_me=call_me)
            elif action in ("decrease", "down"):
                return adjust_volume_delta(-abs(val) if val else -15, call_me=call_me)
            elif action in ("mute", "unmute", "toggle"):
                return toggle_mute(action, call_me=call_me)
            return adjust_volume(action, call_me=call_me)

        elif tool_name == "system_power_control":
            from system_tools import handle_power_action
            action = args.get("action", "sleep")
            return handle_power_action(action, call_me=call_me)

        elif tool_name == "search_or_read_file":
            from file_tools import search_files_across_folders, read_file_content, get_file_info
            action = args.get("action", "search")
            target = args.get("target", "")
            loc = args.get("location", "all")
            if action == "search":
                return search_files_across_folders(target, target_location=loc, call_me=call_me)
            elif action == "read":
                return read_file_content(target, call_me=call_me)
            elif action == "info":
                return get_file_info(target, call_me=call_me)
            return f"{call_me}, file inspected."

        elif tool_name == "open_application":
            app = args.get("app_name", "").strip()
            if not app or app.lower() in ("app", "application", "none", "null"):
                return f"{call_me}, which application would you like me to open?"
            if app.lower() in ("it", "that", "this", "again", "the app", "it again"):
                from tools import get_last_app
                last = get_last_app()
                if last:
                    app = last
                else:
                    return f"{call_me}, which application would you like me to open?"
            handled, res = execute_system_command(f"open {app}", call_me=call_me)
            return res if handled else f"{call_me}, attempted to launch {app}."

        elif tool_name == "close_application":
            app = args.get("app_name", "").strip()
            if not app or app.lower() in ("app", "application", "none", "null"):
                return f"{call_me}, which application would you like me to close?"
            if app.lower() in ("it", "that", "this", "the app"):
                from tools import get_last_app
                last = get_last_app()
                if last:
                    app = last
                else:
                    return f"{call_me}, which application would you like me to close?"
            handled, res = execute_system_command(f"close {app}", call_me=call_me)
            return res if handled else f"{call_me}, attempted to close {app}."

        elif tool_name == "get_system_metrics":
            from tools import get_system_stats
            from system_tools import get_wifi_status
            b_res = get_system_stats(call_me=call_me)
            w_res = get_wifi_status(call_me=call_me)
            return f"{b_res}\n{w_res}"

        elif tool_name == "get_user_identity":
            mem = load_memory()
            profile = mem.get("user_profile", {})
            edu = profile.get("education", {})
            name = mem.get("user_name", "Mohamed Tharik A")
            pref = mem.get("preferred_name", "Tharik")
            return (
                f"User Profile from persistent memory:\n"
                f"- Name: {name} ({pref})\n"
                f"- Title: {mem.get('call_me', 'Sir')}\n"
                f"- College: {edu.get('college')}\n"
                f"- Degree: {edu.get('degree')} - {edu.get('specialization')} ({edu.get('year')})\n"
                f"- Location: {profile.get('location')}\n"
                f"- Key Projects: KIRAHT AI (Personal Assistant), Kaiko (Android SOS), SIH Hackathons, Robotics\n"
                f"- Interests: {', '.join(profile.get('interests', []))}"
            )

        elif tool_name == "send_whatsapp":
            from system_tools import send_whatsapp_message
            recipient = args.get("recipient", "")
            msg = args.get("message", "")
            is_grp = args.get("is_group", False)
            if not recipient:
                return f"{call_me}, please specify who to send the WhatsApp message to."
            if not msg:
                return f"{call_me}, please provide the message content you would like to send."
            return send_whatsapp_message(recipient, msg, call_me=call_me, is_group=is_grp, auto_send=True)

        return f"{call_me}, executed tool '{tool_name}'."
    except Exception as err:
        return f"{call_me}, error executing tool '{tool_name}': {err}"


# ==========================================
# 5. STREAMING CHAT LOOP
# ==========================================
def run_chat_loop(client: ollama.Client, model: str, host: str = "http://localhost:11434") -> None:
    """
    Runs the interactive terminal chat loop with token streaming,
    persistent memory, and live web search integration.
    """
    memory = load_memory()
    call_me = memory.get("call_me", "Sir")
    system_prompt = build_system_prompt(memory)

    # Check internet connectivity
    online = is_online()
    status_icon = "🌐 ONLINE (Live Web Search)" if online else "📴 OFFLINE (Local Memory Only)"

    print("=" * 60)
    print(f"  KIRAHT AI")
    print(f"  Model: {model}  |  Status: {status_icon}")
    print(f"  Laptop Tools: Active (Apps, Files, Clipboard, Terminal, Screenshot, Wi-Fi, Hardware)")
    print(f"  Commands: /memory, /callme <title>, /name <name>, /scan_apps, /search <query>, /clear, exit")
    print("=" * 60)
    print(f"\nkiraht AI: Online and ready, {call_me}. How may I assist you?")

    messages = [{"role": "system", "content": system_prompt}]
    last_system_command = ""
    last_chat_prompt = ""
    pending_whatsapp = None

    while True:
        try:
            user_input = get_user_input_multiline("\nYou: ").strip()

            if not user_input:
                continue

            # Multi-turn WhatsApp interactive resolution (missing message, phone number, or group)
            if pending_whatsapp:
                if user_input.lower() in ("cancel", "abort", "no", "stop"):
                    pending_whatsapp = None
                    print(f"\nkiraht AI: Operation cancelled, {call_me}.")
                    continue

                p_type = pending_whatsapp.get("type")
                auto_send = pending_whatsapp.get("auto_send", False)

                if p_type == "need_message":
                    rec = pending_whatsapp["target"]
                    is_group = pending_whatsapp.get("is_group", False)
                    pending_whatsapp = None
                    from system_tools import send_whatsapp_message
                    res = send_whatsapp_message(rec, user_input, call_me, is_group=is_group, auto_send=auto_send)
                    print(f"\nkiraht AI: {res}")
                    continue

                elif p_type == "need_group":
                    user_choice = user_input.strip()
                    related = pending_whatsapp.get("related", [])
                    msg = pending_whatsapp.get("message", "")
                    target_grp = None

                    if user_choice.isdigit() and 1 <= int(user_choice) <= len(related):
                        target_grp = related[int(user_choice) - 1]["name"]
                    else:
                        for item in related:
                            if user_choice.lower() in item["name"].lower():
                                target_grp = item["name"]
                                break
                        if not target_grp:
                            target_grp = user_choice

                    pending_whatsapp = None
                    from system_tools import send_whatsapp_message
                    res = send_whatsapp_message(target_grp, msg, call_me, is_group=True, auto_send=auto_send)
                    print(f"\nkiraht AI: {res}")
                    continue

                elif p_type == "need_phone":
                    user_choice = user_input.strip()
                    related = pending_whatsapp.get("related", [])
                    msg = pending_whatsapp.get("message", "")
                    rec = pending_whatsapp["target"]

                    # 1. Check if user selected an option number (1, 2, 3...)
                    if user_choice.isdigit() and 1 <= int(user_choice) <= len(related):
                        chosen = related[int(user_choice) - 1]
                        pending_whatsapp = None
                        from system_tools import send_whatsapp_message
                        res = send_whatsapp_message(chosen["phone"], msg, call_me, auto_send=auto_send)
                        print(f"\nkiraht AI: Selected {chosen['name']} ({chosen['phone']}). {res}")
                        continue

                    # 2. Check if user typed a name matching one of the related options
                    matched_opt = None
                    for item in related:
                        if user_choice.lower() in item["name"].lower() and item.get("phone"):
                            matched_opt = item
                            break
                    if matched_opt:
                        pending_whatsapp = None
                        from system_tools import send_whatsapp_message
                        res = send_whatsapp_message(matched_opt["phone"], msg, call_me, auto_send=auto_send)
                        print(f"\nkiraht AI: Selected {matched_opt['name']} ({matched_opt['phone']}). {res}")
                        continue

                    # 3. Check if user entered a 10-digit phone number
                    digits = re.sub(r"\D", "", user_input)
                    if len(digits) >= 10:
                        from system_tools import add_contact, send_whatsapp_message
                        add_contact(rec, digits, call_me)
                        pending_whatsapp = None
                        if msg:
                            res = send_whatsapp_message(rec, msg, call_me, auto_send=auto_send)
                            print(f"\nkiraht AI: Saved contact '{rec.title()}' (+91{digits[-10:]}) and {res}")
                        else:
                            print(f"\nkiraht AI: Saved contact '{rec.title()}' with number +91{digits[-10:]}, {call_me}.")
                        continue
                    else:
                        rel_count = len(related)
                        opt_hint = f"option number (1-{rel_count}) or a " if rel_count > 0 else ""
                        print(f"\nkiraht AI: Please enter a valid {opt_hint}10-digit phone number (or type 'cancel'):")
                        continue

            # Check for repeat / again / now command
            if user_input.lower() in ("again", "now", "repeat", "once more", "one more time", "/again"):
                if last_system_command:
                    print(f"\n[KIRAHT AI: 🔄 Repeating last command: '{last_system_command}']")
                    user_input = last_system_command
                elif last_chat_prompt:
                    print(f"\n[KIRAHT AI: 🔄 Re-explaining with fresh clarity: '{last_chat_prompt}']")
                    user_input = f"Provide a fresh, simpler explanation or alternative practical perspective on: {last_chat_prompt}"
                else:
                    print(f"\nkiraht AI: No previous command or question to repeat, {call_me}.")
                    continue

            # Check for exit
            if user_input.lower() in ("exit", "quit", "bye","goodbye","exit now","quit now","bye now","tata","see you",):
                print(f"\nkiraht AI: Systems entering standby. Goodbye, {call_me}!")
                break

            # Command: /memory
            if user_input.lower() == "/memory":
                profile = memory.get("user_profile", {})
                edu = profile.get("education", {})
                print(f"\n[Persistent Memory Profile]")
                print(f"  Name: {memory.get('user_name')} ({profile.get('preferred_name', 'Tharik')})")
                print(f"  Title: {memory.get('call_me')}")
                if edu:
                    print(f"  Education: {edu.get('degree')} - {edu.get('specialization')} ({edu.get('year')})")
                    print(f"  College: {edu.get('college')}")
                projects = profile.get("projects", [])
                if projects:
                    proj_names = ", ".join(p.get("name") for p in projects)
                    print(f"  Projects: {proj_names}")
                print(f"  Style: {memory.get('response_style')}")
                continue

            # Command: /callme <title>
            if user_input.lower().startswith("/callme "):
                new_title = user_input[8:].strip()
                if new_title:
                    memory["call_me"] = new_title
                    save_memory(memory)
                    call_me = new_title
                    # Refresh system prompt
                    system_prompt = build_system_prompt(memory)
                    messages[0] = {"role": "system", "content": system_prompt}
                    print(f"\nkiraht AI: Understood. I will address you as '{call_me}' from now on.")
                continue

            # Command: /name <name>
            if user_input.lower().startswith("/name "):
                new_name = user_input[6:].strip()
                if new_name:
                    memory["user_name"] = new_name
                    save_memory(memory)
                    system_prompt = build_system_prompt(memory)
                    messages[0] = {"role": "system", "content": system_prompt}
                    print(f"\nkiraht AI: Profile updated. Registered name: {new_name}, {call_me}.")
                continue

            # Command: /clear
            if user_input.lower() == "/clear":
                messages = [{"role": "system", "content": system_prompt}]
                print(f"\nkiraht AI: Conversation context cleared, {call_me}.")
                continue

            # Command: /scan_apps
            if user_input.lower() in ("/scan_apps", "/scanapps", "scan apps"):
                from tools import scan_installed_apps
                print(f"\n[KIRAHT AI: Scanning installed applications on your laptop...]")
                apps = scan_installed_apps()
                print(f"\nkiraht AI: Scanned and indexed {len(apps)} installed desktop apps into apps_cache.json, {call_me}.")
                continue

            # Intent: Create file with content (with safety confirmation guardrail)
            create_file_match = re.search(
                r"^create\s+file\s+([a-zA-Z0-9_\-\./\\]+)\s+with\s+(.+)$",
                user_input,
                re.DOTALL | re.IGNORECASE,
            )
            if create_file_match:
                target_name = create_file_match.group(1).strip()
                new_code = create_file_match.group(2).strip()
                confirm = input(f"\nkiraht AI: Sir, are you sure you want to write to '{target_name}'? (y/n): ").strip().lower()
                if confirm in ("y", "yes"):
                    from file_tools import safe_create_or_modify_file
                    res = safe_create_or_modify_file(target_name, new_code, call_me=call_me)
                    print(f"\nkiraht AI: {res}")
                    messages.append({"role": "user", "content": user_input})
                    messages.append({"role": "assistant", "content": res})
                else:
                    print(f"\nkiraht AI: Operation cancelled, {call_me}. '{target_name}' was not modified.")
                continue

            # Check for laptop / OS operation commands (Desktop Apps, Files, Hardware)
            handled, action_result = execute_system_command(user_input, call_me)
            if handled:
                if action_result.startswith("__NEED_MESSAGE__:"):
                    parts = action_result.split(":")
                    rec = parts[1]
                    display = parts[2] if len(parts) > 2 else rec.title()
                    grp_flag = parts[3] if len(parts) > 3 else "individual"
                    send_flag = parts[4] if len(parts) > 4 else "review"
                    is_group = (grp_flag == "group")
                    auto_send = (send_flag == "send")
                    pending_whatsapp = {"type": "need_message", "target": rec, "display": display, "is_group": is_group, "auto_send": auto_send}
                    if is_group:
                        print(f"\nkiraht AI: Sir, what message would you like to send to group '{display}'?")
                    else:
                        print(f"\nkiraht AI: Sir, what message would you like to send to {display}?")
                    continue

                if action_result.startswith("__NEED_GROUP__:"):
                    parts = action_result.split(":", 4)
                    target = parts[1]
                    msg = parts[2] if len(parts) > 2 else ""
                    related_raw = parts[3] if len(parts) > 3 else "[]"
                    send_flag = parts[4] if len(parts) > 4 else "review"
                    auto_send = (send_flag == "send")
                    try:
                        related_list = json.loads(related_raw)
                    except Exception:
                        related_list = []

                    pending_whatsapp = {
                        "type": "need_group",
                        "target": target,
                        "message": msg,
                        "related": related_list,
                        "auto_send": auto_send,
                    }
                    if related_list:
                        opts = "\n".join([f"    [{i+1}] {item['name']}" for i, item in enumerate(related_list)])
                        print(
                            f"\nkiraht AI: Sir, group '{target}' was not found in your WhatsApp groups.\n"
                            f"  Related group options:\n{opts}\n\n"
                            f"  Reply with:\n"
                            f"    * Option number (1-{len(related_list)}) or group name to select\n"
                            f"    * Or 'cancel' to abort"
                        )
                    else:
                        print(f"\nkiraht AI: Sir, group '{target}' was not found in your WhatsApp groups (or type 'cancel').")
                    continue

                if action_result.startswith("__NEED_PHONE__:"):
                    parts = action_result.split(":", 4)
                    rec = parts[1]
                    msg = parts[2] if len(parts) > 2 else ""
                    related_raw = parts[3] if len(parts) > 3 else "[]"
                    send_flag = parts[4] if len(parts) > 4 else "review"
                    auto_send = (send_flag == "send")
                    try:
                        related_list = json.loads(related_raw)
                    except Exception:
                        related_list = []

                    pending_whatsapp = {
                        "type": "need_phone",
                        "target": rec,
                        "message": msg,
                        "related": related_list,
                        "auto_send": auto_send,
                    }
                    valid_opts = [item for item in related_list if item.get("phone")]
                    if valid_opts:
                        opts = "\n".join([f"    [{i+1}] {item['name']} ({item['phone']})" for i, item in enumerate(valid_opts)])
                        print(
                            f"\nkiraht AI: Sir, '{rec.title()}' is not in your contacts.\n"
                            f"  Related contact options:\n{opts}\n\n"
                            f"  Reply with:\n"
                            f"    * Option number (1-{len(valid_opts)}) to send to that contact\n"
                            f"    * Or a 10-digit phone number to save '{rec.title()}'\n"
                            f"    * Or 'cancel' to abort"
                        )
                    else:
                        print(f"\nkiraht AI: Sir, '{rec.title()}' is not in your contacts.\n  Please provide their 10-digit phone number to save and proceed (or type 'cancel'):")
                    continue

                print(f"\nkiraht AI: {action_result}")
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": action_result})
                last_system_command = user_input
                last_chat_prompt = ""
                continue

            # Check if live web search is needed
            needs_search, search_query = should_trigger_search(user_input)
            prompt_content = user_input

            if needs_search:
                if is_online():
                    print(f"\n[KIRAHT AI: 🌐 Searching live web for '{search_query}'...]")
                    web_snippets = search_web(search_query, max_results=3)
                    if web_snippets:
                        prompt_content = (
                            f"[Real-Time Live Web Search Results for '{search_query}']:\n"
                            f"{web_snippets}\n\n"
                            f"[User Question]:\n{user_input}"
                        )
                else:
                    print(f"\n[KIRAHT AI: 📴 Offline mode — relying on internal knowledge]")

            # Check if workspace file code context should be injected
            file_context = check_file_context(user_input)
            if file_context and prompt_content == user_input:
                prompt_content = f"{file_context}[User Question]:\n{user_input}"

            # Add to messages history
            # In history, store the user's prompt (with search context for this turn)
            messages.append({"role": "user", "content": prompt_content})
            last_chat_prompt = user_input
            last_system_command = ""

            # Stream generation or agent tool-calling
            try:
                use_tools = should_enable_tools(user_input)
                if use_tools:
                    # 1. Ask Ollama with tools enabled for device commands
                    res = client.chat(
                        model=model,
                        messages=messages,
                        tools=AVAILABLE_TOOLS,
                        options={
                            "temperature": 0.35,
                            "num_thread": 8,
                            "num_ctx": 2048,
                        },
                    )
                    tool_calls = getattr(res.message, "tool_calls", None)
                    if tool_calls:
                        messages.append(res.message)
                        for tc in tool_calls:
                            fn_name = tc.function.name
                            fn_args = tc.function.arguments or {}
                            print(f"\n[KIRAHT AI: ⚙️ Executing {fn_name}()]")
                            tool_res = execute_agent_tool(fn_name, fn_args, call_me)
                            messages.append({
                                "role": "tool",
                                "content": tool_res,
                            })
                        response_stream = client.chat(
                            model=model,
                            messages=messages,
                            stream=True,
                            options={
                                "temperature": 0.35,
                                "num_thread": 8,
                                "num_ctx": 2048,
                            },
                        )
                    else:
                        response_stream = [res]
                else:
                    # 2. Pure streaming chat mode for questions, coding, explanations, and knowledge
                    response_stream = client.chat(
                        model=model,
                        messages=messages,
                        stream=True,
                        options={
                            "temperature": 0.35,
                            "num_thread": 8,
                            "num_ctx": 2048,
                        },
                    )

                print(f"\nkiraht AI: ", end="", flush=True)

                reply_chunks = []
                is_thinking = False

                for chunk in response_stream:
                    thinking = getattr(chunk.message, "thinking", None)
                    content = chunk.message.content or ""

                    if thinking and not content:
                        if not is_thinking:
                            print("[Thinking...] ", end="", flush=True)
                            is_thinking = True
                        continue

                    if content:
                        if is_thinking:
                            # Clear the [Thinking...] text and reset line
                            print("\r\033[Kkiraht AI: ", end="", flush=True)
                            is_thinking = False
                        print(content, end="", flush=True)
                        reply_chunks.append(content)

                print()  # newline after streaming completes
                full_reply = "".join(reply_chunks).strip()

                # If web context was attached, rewrite last user message in history to clean user_input
                if prompt_content != user_input:
                    messages[-1] = {"role": "user", "content": user_input}

                # Save assistant response to session history
                messages.append({"role": "assistant", "content": full_reply})

            except KeyboardInterrupt:
                if messages and messages[-1].get("role") == "user":
                    messages.pop()
                print(f"\n\n[kiraht AI: Response cancelled by {call_me}]")
                continue

            except ollama.ResponseError as err:
                messages.pop()
                print(f"\nkiraht AI: [Ollama Error {err.status_code}] {err.error}")

            except (httpx.ConnectError, ConnectionRefusedError, ConnectionError, ollama.RequestError):
                messages.pop()
                print(f"\nkiraht AI: [Connection Error] Lost connection to local Ollama daemon at {host}.")

            except Exception as err:
                messages.pop()
                print(f"\nkiraht AI: [Error] {err}")

        except (KeyboardInterrupt, EOFError):
            print(f"\nkiraht AI: Systems standing by. Goodbye, {call_me}!")
            break


def main() -> None:
    """
    Main entry point for KIRAHT AI.
    """
    load_dotenv()
    initial_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434"
    model = os.getenv("AI_MODEL", "qwen2.5:3b").strip() or "qwen2.5:3b"
    client, host = verify_and_ensure_ollama(model, initial_host)
    run_chat_loop(client, model, host=host)


if __name__ == "__main__":
    main()

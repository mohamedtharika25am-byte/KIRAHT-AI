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

import datetime
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
        f"- If you or the system asked what message to send, and the user's next turn is short text (e.g. 'hi', 'hoi', 'ok', 'reach safe', 'where are you'), that text IS THE MESSAGE for that contact! Call `send_whatsapp` IMMEDIATELY to complete the operation. Never treat it as a casual greeting!\n"
        f"- Contextual Pronoun & Follow-Up Resolution ('open that', 'open it', 'close that', 'check that', 'run that'):\n"
        f"  Always inspect the previous conversation turns to identify what 'that' or 'it' refers to.\n"
        f"  * If previous turn was showing Task Manager or active processes, 'open that' means `open_application(app_name='task manager')`!\n"
        f"  * If previous turn was talking about a desktop app, call `open_application(app_name=...)`!\n"
        f"  * If previous turn was a folder, call `open_folder(folder_name=...)`!\n"
        f"  * If previous turn was a file, call `open_file(filepath=...)`!\n"
        f"  Always execute the tool call immediately based on previous context.\n\n"
        f"LAPTOP & SYSTEM CONTROL PERMISSIONS:\n"
        f"- You have FULL system administrative permissions granted by {call_me} to control power, hardware, and system states.\n"
        f"- Sleep & Standby: When asked to sleep the laptop ('sleep', 'standby', 'sleep the laptop'), call `system_power_control(action='sleep')`.\n"
        f"- Shutdown & Power Off: When asked to shut down ('shutdown', 'power off'), call `system_power_control(action='shutdown')`.\n"
        f"- Cancel Shutdown: When asked to cancel or abort shutdown ('cancel shutdown', 'abort shutdown', 'stop shutdown'), call `system_power_control(action='cancel_shutdown')`.\n"
        f"- Restart & Reboot: When asked to restart ('restart laptop', 'reboot'), call `system_power_control(action='restart')`.\n"
        f"- Screen & Display: When asked to turn off screen ('turn off display', 'screen off'), call `system_power_control(action='screen_off')`.\n"
        f"- Lock Workstation: When asked to lock ('lock laptop', 'lock screen'), call `system_power_control(action='lock')`.\n"
        f"- Volume & Audio: When asked to change volume ('vol up', 'vol down', 'mute', 'unmute'), call `control_volume`.\n"
        f"- Microphone: When asked to mute, unmute, or turn on/off microphone ('mic mute', 'mic off', 'mic on', 'unmute mic'), call `control_microphone`.\n"
        f"- Native Desktop Tools Integration: You are directly connected to Windows 11 on {call_me}'s laptop with native tools for desktop applications (WhatsApp, Chrome, VS Code), opening any folder or file across drives, inspecting files & folder sizes, managing system clipboard, and hardware metrics. NEVER say 'I cannot directly interact with external applications', 'I don't have direct access to open folders', or 'I don't have access to check folder sizes'.\n"
        f"OPERATIONAL HONESTY & ACTION DIRECTIVES:\n"
        f"- NEVER claim you have created a folder, modified a directory, or executed a system task unless you actually called a tool that completed it.\n"
        f"- Never confuse college degrees (such as AIML), educational groups, or projects with folder creation.\n"
        f"- Always be 100% honest and accurate about system actions.\n\n"
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
    or inspection (files, folders, sizes, apps, WhatsApp, hardware) that requires native function tool calling.

    Returns False for pure programming/algorithmic questions, conceptual tutorials,
    and purely conversational prompts so the model uses internal knowledge directly.
    """
    lower = user_text.lower().strip()

    # 1. Check if user is asking a pure theoretical coding or algorithmic problem
    pure_coding_patterns = [
        r"\b(?:write|code|script)\s+(?:a\s+)?(?:python|java|c\+\+|javascript|typescript|sql|bash|html)\b",
        r"\b(?:algorithm|data\s+structure|leetcode|deque|binary\s+tree|recursion|quicksort|mergesort)\b",
        r"\b(?:tutorial|teach|syntax\s+of|interview\s+question)\b",
        r"\bwrite\s+(?:a\s+)?(?:code|program|function|class|essay|story|poem)\b",
    ]
    if any(re.search(p, lower) for p in pure_coding_patterns):
        return False

    # 2. User confirmation & follow-up affirmations (e.g. "yeah thats right buddy", "check it out", "yes do it")
    affirmation_patterns = [
        r"\b(?:yeah|yes|yep|sure|ok|okay|thats\s+right|that's\s+right|correct|do\s+it|go\s+ahead|proceed)\b",
        r"\b(?:then\s+check|check\s+it\s+out|check\s+that|tell\s+me\s+then|i\s+mentioned)\b",
    ]
    for p in affirmation_patterns:
        if re.search(p, lower):
            return True

    # 3. Actionable system command & device inspection triggers (Folders, Files, Sizes, Apps, WhatsApp, Hardware)
    system_action_triggers = [
        # Folders, Files, and Disk Size inspection
        r"\b(?:folder|foler|floder|directory|dir|drive)\b",
        r"\b(?:file|files|storage|size|mb|gb|bytes|capacity)\b",
        r"\b(?:workspace|downloads|desktop|documents|movies|pictures|videos)\b",
        # Installed Apps and Window control
        r"\b(?:open|launch|start|run|close|kill|terminate|exit)\s+[a-zA-Z0-9_\-\.]+",
        r"\b(?:open|launch|start|run|close)\s+(?:app|application|software|tool|program)\b",
        # WhatsApp & Messaging
        r"\b(?:whatsapp|whatsap|watsapp|wa|wp|message|msg)\b",
        # Screen Brightness & Audio Volume
        r"\b(?:brightness|screen|display|volume|vol|sound|mute|unmute|mic|microphone)\b",
        # Laptop Metrics & System Controls
        r"\b(?:battery|power|charging|wifi|ping|ram|cpu|processes|process|taskmgr|task\s*manager)\b",
        r"\b(?:sleep|shutdown|restart|reboot|hibernate|lock)\b",
        # Pronoun & contextual follow-ups ("open that", "open that folder", "check that", "close it", etc.)
        r"\b(?:(?:open|launch|start|run|close|kill|check)\s+(?:that|it|this)|that\s+(?:folder|file|app|directory)|the\s+(?:folder|file|app|directory))\b",
    ]
    for p in system_action_triggers:
        if re.search(p, lower):
            return True

    # 3. Conversational / educational question filters
    coding_and_question_patterns = [
        r"\bexample\b",
        r"\bhow\s+to\b",
        r"\bhow\s+do\b",
        r"\bhow\s+does\b",
        r"\bhow\s+can\b",
        r"\bwhat\s+is\b",
        r"\bwhat\s+are\b",
        r"\bwhat\s+can\b",
        r"\bwhat\s+did\b",
        r"\bwhat\s+do\b",
        r"\bwhat\s+does\b",
        r"\bwhat\s+will\b",
        r"\bwhy\s+is\b",
        r"\bwhy\s+does\b",
        r"\bexplain\b",
        r"\bexplanation\b",
        r"\bmeaning\b",
        r"\bdifference\b",
        r"\btutorial\b",
        r"\bteach\b",
        r"\bwho\s+is\b",
        r"\bwhere\s+is\b",
        r"\bwhich\s+is\b",
        r"\bwhen\s+did\b",
        r"\bcan\s+you\s+explain\b",
        r"\btell\s+me\s+about\b",
        r"\bguide\b",
        r"\bdefinition\b",
        r"\bconcept\b",
        r"\bsummarize\b",
    ]
    for p in coding_and_question_patterns:
        if re.search(p, lower):
            return False

    # 4. Tanglish general question patterns
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


def get_gemini_client():
    """
    Initializes Google GenAI client if GEMINI_API_KEY is present in .env.
    Auto-migrates deprecated model names to current active 2026 models.
    """
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    raw_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip() or "gemini-3.1-flash-lite"
    if raw_model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash-lite"):
        model = "gemini-3.1-flash-lite"
    else:
        model = raw_model

    if not key:
        return None, model
    try:
        import logging
        logging.getLogger("google_genai").setLevel(logging.ERROR)
        from google import genai
        client = genai.Client(api_key=key)
        return client, model
    except Exception:
        return None, model


def inspect_screen_with_gemini(gemini_client, gemini_model: str, user_prompt: str, call_me: str = "Sir") -> tuple[bool, str]:
    """
    Captures primary screen and streams Gemini Vision analysis.
    """
    if not gemini_client:
        return False, f"{call_me}, screen vision requires a Google Gemini API key. Please add GEMINI_API_KEY in your .env file."

    from system_tools import take_silent_screenshot
    from PIL import Image

    print(f"\n[KIRAHT AI: 📸 Capturing live screen for Gemini Vision analysis...]")
    shot_path = take_silent_screenshot()
    if not shot_path or not os.path.exists(shot_path):
        return False, f"{call_me}, failed to capture screen for vision inspection."

    target_model = gemini_model
    if target_model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
        target_model = "gemini-3.1-flash-lite"

    try:
        img = Image.open(shot_path)
        prompt = (
            f"You are KIRAHT AI, a razor-sharp, elite personal AI assistant. Address the user as '{call_me}'.\n"
            f"User request: '{user_prompt}'\n"
            f"Task: Inspect the attached screen capture of the user's laptop. Provide a direct, crystal-clear, step-by-step diagnosis or explanation. If there is code, terminal errors, or UI issues visible, pinpoint the exact root cause and solution."
        )
        try:
            response_stream = gemini_client.models.generate_content_stream(
                model=target_model,
                contents=[img, prompt]
            )
        except Exception as e:
            if "404" in str(e) or "503" in str(e):
                target_model = "gemini-3.1-flash-lite"
                response_stream = gemini_client.models.generate_content_stream(
                    model=target_model,
                    contents=[img, prompt]
                )
            else:
                raise e

        print(f"\nkiraht AI: ", end="", flush=True)
        chunks = []
        for chunk in response_stream:
            text = chunk.text or ""
            print(text, end="", flush=True)
            chunks.append(text)
        print()
        return True, "".join(chunks).strip()
    except Exception as err:
        return False, f"{call_me}, screen vision error: {err}"


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
            "name": "control_microphone",
            "description": "Controls Windows microphone audio recording input: mute, unmute, or toggle microphone state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["mute", "unmute", "toggle"],
                        "description": "Action to perform on microphone"
                    }
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
            "description": "Launches an installed Windows desktop application (e.g. Task Manager, Chrome, WhatsApp, Android Studio, VS Code, Spotify, Notepad, Calculator, Antigravity). Call this when user explicitly asks to open an app or says 'open that' referring to an app or task manager previously discussed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the application to open (e.g. 'Task Manager', 'Chrome', 'VS Code')"}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file",
            "description": "Opens a specific file in its native application or code editor. Call this when the user asks to open a file or says 'open that' referring to a file discussed previously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "File name or full file path to open"}
                },
                "required": ["filepath"]
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
                    "recipient": {"type": "string", "description": "The exact contact name, group name, or phone number explicitly specified by the user in this conversation. Never assume or invent a name."},
                    "message": {"type": "string", "description": "The exact message text to send to the recipient"},
                    "is_group": {"type": "boolean", "description": "True if sending to a WhatsApp group, False for individual"}
                },
                "required": ["recipient", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_folder_info",
            "description": "Inspects any directory or folder on the user's laptop (e.g. 'KIRAHT AI', 'Downloads', 'Desktop', 'Documents', 'Movies', 'D:\\' drive) and returns its exact disk size (KB/MB/GB), total file count, and verified path. Call this whenever the user asks for folder size, directory size, or folder inspection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_name": {"type": "string", "description": "Name or path of the folder to inspect (e.g. 'KIRAHT AI', 'Downloads', 'Desktop', 'D:\\', or 'that folder')"}
                },
                "required": ["folder_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_folder",
            "description": "Opens any directory or folder in Windows File Explorer (e.g. 'Downloads', 'Documents', 'Desktop', 'KIRAHT AI', 'Movies', 'D:\\' drive, or 'that folder').",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_name": {"type": "string", "description": "Name or path of the folder to open (e.g. 'Downloads', 'KIRAHT AI', 'that folder')"}
                },
                "required": ["folder_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory_contents",
            "description": "Lists all files and subdirectories inside a given folder on the user's laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_name": {"type": "string", "description": "Folder to list files from (e.g. 'KIRAHT AI', 'Downloads', or workspace root)"}
                }
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

        elif tool_name == "control_microphone":
            from system_tools import toggle_mic_mute
            action = args.get("action", "toggle")
            return toggle_mic_mute(action, call_me=call_me)

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
            app = str(args.get("app_name", "")).strip()
            app = re.sub(r"^(?:open|launch|start|run)\s+", "", app, flags=re.IGNORECASE).strip()
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
            if handled:
                return res
            from tools import launch_desktop_app
            launched, msg = launch_desktop_app(app, call_me=call_me)
            return msg if launched else f"{call_me}, attempted to launch {app}."

        elif tool_name == "open_file":
            from file_tools import open_system_item
            f_path = str(args.get("filepath", "")).strip()
            if not f_path:
                return f"{call_me}, please specify the file path to open."
            return open_system_item(f_path, call_me=call_me)

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
            recipient = str(args.get("recipient", "")).strip()
            msg = str(args.get("message", "")).strip()
            is_grp = args.get("is_group", False)
            if not recipient:
                return f"{call_me}, please specify who to send the WhatsApp message to."
            if not msg or msg.lower() in ("how can i assist you today?", "how can i help you?", "hello", "hi"):
                return f"{call_me}, please specify what message you would like to send to {recipient}."
            return send_whatsapp_message(recipient, msg, call_me=call_me, is_group=is_grp, auto_send=True)

        elif tool_name == "get_folder_info":
            from file_tools import get_file_info, get_last_path
            folder = str(args.get("folder_name", "")).strip()
            if not folder or folder.lower() in ("that", "it", "this", "that folder", "the folder", "same"):
                folder = get_last_path() or "d:\\KIRAHT AI"
            return get_file_info(folder, call_me=call_me)

        elif tool_name == "open_folder":
            from tools import open_folder
            from file_tools import get_last_path
            folder = str(args.get("folder_name", "")).strip()
            if not folder or folder.lower() in ("that", "it", "this", "that folder", "the folder", "same"):
                folder = get_last_path() or "d:\\KIRAHT AI"
            return open_folder(folder, call_me=call_me)

        elif tool_name == "list_directory_contents":
            from file_tools import list_workspace_files, resolve_path, WORKSPACE_DIR
            folder = str(args.get("folder_name", "")).strip()
            if not folder or folder.lower() in ("workspace", "project", "kiraht", "kiraht ai"):
                target = WORKSPACE_DIR
            else:
                target = resolve_path(folder)
            return list_workspace_files(target, call_me=call_me)

        return f"{call_me}, executed tool '{tool_name}'."
    except Exception as err:
        return f"{call_me}, error executing tool '{tool_name}': {err}"


def get_last_update_info() -> str:
    """
    Returns formatted timestamp of the latest Git commit or current build.
    """
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=format:%d %b %Y, %I:%M %p"],
            capture_output=True,
            text=True,
            timeout=2,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "25 Sep 2026, 11:34 PM"


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
    last_update = get_last_update_info()

    from security import get_security_mode_label
    security_label = get_security_mode_label()

    session_start_dt = datetime.datetime.now()
    session_start_time = session_start_dt.strftime("%d %b %Y • %I:%M:%S %p (%A)")

    gemini_client, gemini_model = get_gemini_client()
    engine_mode = "auto"
    active_engine = "gemini" if gemini_client and online else "ollama"
    engine_display = f"🚀 GEMINI ({gemini_model})" if active_engine == "gemini" else f"🛡️ LOCAL OLLAMA ({model})"

    print("=" * 68)
    print("  :::    ::: ::: :::::::::      :::     :::    ::: ::::::::::: ")
    print("  :+:   :+:  :+: :+:    :+:   :+: :+:   :+:    :+:     :+:     ")
    print("  +:+  +:+   +:+ +:+    +:+  +:+   +:+  +:+    +:+     +:+     ")
    print("  +#++:++    +#+ +#++:++#:  +#++:++#++: +#++:++#++     +#+     ")
    print("  +#+  +#+   +#+ +#+    +#+ +#+     +#+ +#+    +#+     +#+     ")
    print("  #+#   #+#  #+# #+#    #+# #+#     #+# #+#    #+#     #+#     ")
    print("  ###    ### ### ###    ### ###     ### ###    ###     ###     ")
    print("=" * 68)
    print(f"  ⚡ System          : KIRAHT AI - v0.2.1")
    print(f"  🕒 Session Started : {session_start_time}")
    print(f"  📦 Last Code Update: {last_update}")
    print(f"  🤖 Active Engine   : {engine_display}  |  {status_icon}")
    print(f"  🛡️ Security Mode   : {security_label}")
    print(f"  🛠️ Laptop Tools    : Active (Apps, Files, Folders, WhatsApp, Screenshot, Wi-Fi)")
    print(f"  💡 Quick Commands  : /engine, /memory, /uptime, /think, /thoughts, /callme, exit")
    print(f"  🧠 Shortcuts       : Ctrl+C (Cancel Response)")
    print("=" * 68)
    print(f"\nkiraht AI: Online and ready, {call_me}. How may I assist you?")

    messages = [{"role": "system", "content": system_prompt}]
    last_system_command = ""
    last_chat_prompt = ""
    pending_whatsapp = None
    show_thoughts = False
    last_thought_process = ""

    while True:
        is_processing = False
        try:
            user_input = get_user_input_multiline("\nYou: ").strip()

            if not user_input:
                continue

            is_processing = True

            # Vision Screen Inspection Intent
            is_vision_request = any(trig in user_input.lower() for trig in (
                "inspect screen", "see screen", "look at screen", "read screen",
                "screen paaru", "screen-la enna iruku", "screen la error enna",
                "what is on my screen", "what's on my screen", "debug my screen",
                "explain my screen", "check my screen", "screen-ah paaru", "screen analyze pannu"
            ))
            if is_vision_request:
                if gemini_client:
                    ok, res = inspect_screen_with_gemini(gemini_client, gemini_model, user_input, call_me)
                    if ok:
                        messages.append({"role": "user", "content": user_input})
                        messages.append({"role": "assistant", "content": res})
                    else:
                        print(f"\nkiraht AI: {res}")
                    continue
                else:
                    from system_tools import take_screenshot
                    shot_res = take_screenshot(call_me)
                    print(f"\nkiraht AI: {shot_res}\n  💡 To analyze this screenshot with Vision AI, add your GEMINI_API_KEY in .env!")
                    continue

            # Multi-turn WhatsApp interactive resolution (missing message, phone number, or group)
            if pending_whatsapp:
                user_clean = user_input.strip().lower()
                cancel_words = (
                    "cancel", "abort", "no", "stop", "exit", "quit", "close",
                    "nevermind", "vendam", "cancel pannu", "cancel panni", "/cancel"
                )
                if user_clean in cancel_words or any(user_clean.startswith(cw) for cw in ("cancel", "abort", "stop")):
                    pending_whatsapp = None
                    print(f"\nkiraht AI: Operation cancelled, {call_me}.")
                    continue

                # Check if user typed a completely different system command or prompt
                lower_in = user_input.lower().strip()
                is_override = (
                    lower_in.startswith(("whatsapp", "send whatsapp", "open ", "close ", "vol ", "volume ", "time", "date", "battery", "wifi", "note:", "ping", "/"))
                )
                if is_override:
                    pending_whatsapp = None
                    # Fall through to execute the command directly
                else:
                    p_type = pending_whatsapp.get("type")
                    auto_send = pending_whatsapp.get("auto_send", False)

                    if p_type == "need_recipient":
                        pending_whatsapp = None
                        prefix = "send whatsapp" if auto_send else "whatsapp"
                        user_input = f"{prefix} {user_input.strip()}"
                        # Fall through to execute the command directly below

                    elif p_type == "need_message":
                        rec = pending_whatsapp["target"]
                        is_group = pending_whatsapp.get("is_group", False)
                        pending_whatsapp = None
                        from system_tools import send_whatsapp_message
                        res = send_whatsapp_message(rec, user_input, call_me, is_group=is_group, auto_send=auto_send)
                        print(f"\nkiraht AI: {res}")
                        prefix = "send whatsapp" if auto_send else "whatsapp"
                        grp_word = "group " if is_group else ""
                        last_system_command = f"{prefix} {grp_word}{rec} {user_input}"
                        last_chat_prompt = ""
                        continue

                    elif p_type == "need_group":
                        user_choice = user_input.strip()
                        related = pending_whatsapp.get("related", [])
                        msg = pending_whatsapp.get("message", "")
                        target_grp = None

                        if user_choice.isdigit() and 1 <= int(user_choice) <= len(related):
                            chosen_item = related[int(user_choice) - 1]
                            if chosen_item.get("is_direct_search"):
                                target_grp = chosen_item.get("query", pending_whatsapp.get("target"))
                            else:
                                target_grp = chosen_item["name"]
                        elif user_choice.lower() in ("search", "desktop", "direct", "find", "search whatsapp"):
                            target_grp = pending_whatsapp.get("target")
                        else:
                            for item in related:
                                if user_choice.lower() in item["name"].lower():
                                    if item.get("is_direct_search"):
                                        target_grp = item.get("query", pending_whatsapp.get("target"))
                                    else:
                                        target_grp = item["name"]
                                    break
                            if not target_grp:
                                target_grp = user_choice

                        pending_whatsapp = None

                        # If no message was provided yet, transition to need_message
                        if not msg:
                            pending_whatsapp = {
                                "type": "need_message",
                                "target": target_grp,
                                "display": target_grp,
                                "is_group": True,
                                "auto_send": auto_send
                            }
                            print(f"\nkiraht AI: Selected group '{target_grp}'. What message would you like to send to this group? (or type 'cancel')")
                            continue

                        from system_tools import send_whatsapp_message
                        res = send_whatsapp_message(target_grp, msg, call_me, is_group=True, auto_send=auto_send)
                        print(f"\nkiraht AI: {res}")
                        prefix = "send whatsapp" if auto_send else "whatsapp"
                        last_system_command = f"{prefix} group {target_grp} {msg}"
                        last_chat_prompt = ""
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
                            if chosen.get("is_direct_search"):
                                if not msg:
                                    pending_whatsapp = {
                                        "type": "need_message",
                                        "target": rec,
                                        "display": rec.title(),
                                        "is_group": False,
                                        "auto_send": auto_send,
                                    }
                                    print(f"\nkiraht AI: Searching WhatsApp for '{rec}'. What message would you like to send? (or type 'cancel')")
                                    continue
                                res = send_whatsapp_message(chosen.get("query", rec), msg, call_me, auto_send=auto_send)
                                print(f"\nkiraht AI: Searching WhatsApp Desktop for '{rec}'. {res}")
                            else:
                                if not msg:
                                    pending_whatsapp = {
                                        "type": "need_message",
                                        "target": chosen["phone"],
                                        "display": chosen["name"],
                                        "is_group": False,
                                        "auto_send": auto_send,
                                    }
                                    print(f"\nkiraht AI: Selected {chosen['name']}. What message would you like to send? (or type 'cancel')")
                                    continue
                                res = send_whatsapp_message(chosen["phone"], msg, call_me, auto_send=auto_send)
                                print(f"\nkiraht AI: Selected {chosen['name']} ({chosen['phone']}). {res}")
                                prefix = "send whatsapp" if auto_send else "whatsapp"
                                last_system_command = f"{prefix} {chosen['name']} {msg}"
                                last_chat_prompt = ""
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
                            if not msg:
                                pending_whatsapp = {
                                    "type": "need_message",
                                    "target": matched_opt["phone"],
                                    "display": matched_opt["name"],
                                    "is_group": False,
                                    "auto_send": auto_send,
                                }
                                print(f"\nkiraht AI: Selected {matched_opt['name']}. What message would you like to send? (or type 'cancel')")
                                continue
                            res = send_whatsapp_message(matched_opt["phone"], msg, call_me, auto_send=auto_send)
                            print(f"\nkiraht AI: Selected {matched_opt['name']} ({matched_opt['phone']}). {res}")
                            prefix = "send whatsapp" if auto_send else "whatsapp"
                            last_system_command = f"{prefix} {matched_opt['name']} {msg}"
                            last_chat_prompt = ""
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
                                prefix = "send whatsapp" if auto_send else "whatsapp"
                                last_system_command = f"{prefix} {rec} {msg}"
                                last_chat_prompt = ""
                            else:
                                print(f"\nkiraht AI: Saved contact '{rec.title()}' with number +91{digits[-10:]}, {call_me}.")
                            continue
                        # 4. Check if user re-entered a contact name
                        from system_tools import resolve_contact, send_whatsapp_message
                        new_phone, new_dname, new_related = resolve_contact(user_choice)
                        if new_phone:
                            pending_whatsapp = None
                            if not msg:
                                pending_whatsapp = {
                                    "type": "need_message",
                                    "target": new_phone,
                                    "display": new_dname,
                                    "is_group": False,
                                    "auto_send": auto_send,
                                }
                                print(f"\nkiraht AI: Selected {new_dname}. What message would you like to send? (or type 'cancel')")
                                continue
                            res = send_whatsapp_message(new_phone, msg, call_me, auto_send=auto_send)
                            print(f"\nkiraht AI: Selected {new_dname} ({new_phone}). {res}")
                            prefix = "send whatsapp" if auto_send else "whatsapp"
                            last_system_command = f"{prefix} {new_dname} {msg}"
                            last_chat_prompt = ""
                            continue
                        elif new_related:
                            pending_whatsapp["target"] = user_choice
                            pending_whatsapp["related"] = new_related
                            new_valid = [it for it in new_related if it.get("phone")]
                            if new_valid:
                                opts = "\n".join([f"    [{i+1}] {item['name']} ({item['phone']})" for i, item in enumerate(new_valid)])
                                print(
                                    f"\nkiraht AI: Sir, '{user_choice.title()}' is not in your contacts.\n"
                                    f"  Related contact options:\n{opts}\n\n"
                                    f"  Reply with:\n"
                                    f"    * Option number (1-{len(new_valid)}) to send to that contact\n"
                                    f"    * Or re-enter the correct contact name to search again\n"
                                    f"    * Or enter a 10-digit phone number to save '{user_choice.title()}'\n"
                                    f"    * Or 'cancel' to abort"
                                )
                            else:
                                print(
                                    f"\nkiraht AI: Sir, '{user_choice.title()}' is not in your contacts.\n"
                                    f"  Reply with:\n"
                                    f"    * Re-enter the correct contact name to search again\n"
                                    f"    * Or enter a 10-digit phone number to save '{user_choice.title()}'\n"
                                    f"    * Or 'cancel' to abort"
                                )
                            continue
                        else:
                            rel_count = len(related)
                            opt_hint = f"option number (1-{rel_count}), " if rel_count > 0 else ""
                            print(f"\nkiraht AI: '{user_choice.title()}' was not found. Please enter a valid {opt_hint}re-enter the contact name, or enter a 10-digit phone number (or type 'cancel'):")
                            continue

            # Check for repeat / again / now command
            repeat_triggers = (
                "again", "now", "repeat", "once more", "one more time", "/again",
                "send again", "send it again", "resend", "repeat send", "send once more", "again send"
            )
            if user_input.lower().strip() in repeat_triggers:
                if last_system_command:
                    print(f"\n[KIRAHT AI: 🔄 Repeating last command: '{last_system_command}']")
                    user_input = last_system_command
                elif last_chat_prompt:
                    clean_last = last_chat_prompt.strip().lower()
                    words = clean_last.split()
                    if len(words) <= 2 or clean_last in ("through whatsapp", "via whatsapp", "on whatsapp", "yeah", "yes", "ok", "cancel", "1", "2", "3", "4", "hi", "hello"):
                        print(f"\nkiraht AI: No previous command or question to repeat, {call_me}.")
                        continue
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

            # Command: /uptime
            if user_input.lower().strip() in ("/uptime", "uptime", "session time"):
                elapsed = datetime.datetime.now() - session_start_dt
                hours, rem = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(rem, 60)
                parts = []
                if hours > 0:
                    parts.append(f"{hours}h")
                if minutes > 0 or hours > 0:
                    parts.append(f"{minutes}m")
                parts.append(f"{seconds}s")
                elapsed_str = " ".join(parts)
                print(f"\nkiraht AI: Current session started at {session_start_time}.\n  Active uptime: ⏳ {elapsed_str}, {call_me}.")
                continue

            # Command: /think [on|off] or Ctrl+T toggle
            if user_input.lower().strip() in ("/think", "think", "/think on", "/think off", "/think toggle", "\x14") or user_input.lower().strip().startswith(("/think ", "think ")):
                cmd_parts = user_input.lower().strip().split()
                if len(cmd_parts) > 1 and cmd_parts[1] in ("on", "true", "1"):
                    show_thoughts = True
                elif len(cmd_parts) > 1 and cmd_parts[1] in ("off", "false", "0"):
                    show_thoughts = False
                else:
                    show_thoughts = not show_thoughts
                status = "ON (Reasoning stream visible)" if show_thoughts else "OFF (Compact mode - press Ctrl+T to view)"
                note = ""
                if "r1" not in model.lower() and "qwq" not in model.lower() and "think" not in model.lower():
                    note = f"\n  💡 Note: Active model '{model}' is a direct-response model. Step-by-step thinking streams are emitted by reasoning models (e.g. 'deepseek-r1')."
                print(f"\nkiraht AI: 🧠 Thought Process Visibility: {status}, {call_me}.{note}")
                continue

            # Command: /thoughts or /why
            if user_input.lower().strip() in ("/thoughts", "/thought", "/why", "/brain", "why", "thoughts", "show thoughts", "show thinking"):
                if last_thought_process.strip():
                    print(f"\n┌─ 💭 [KIRAHT AI Thought Process] " + "─" * 40)
                    for line in last_thought_process.strip().splitlines():
                        print(f"│  {line}")
                    print("└" + "─" * 70)
                else:
                    print(f"\nkiraht AI: No active thought reasoning available from the last turn, {call_me}.")
                continue

            # Command: /engine [gemini|ollama|local|auto]
            if user_input.lower().strip().startswith(("/engine", "engine")):
                cmd_parts = user_input.lower().strip().split()
                if len(cmd_parts) > 1:
                    target_eng = cmd_parts[1]
                    if target_eng in ("gemini", "cloud"):
                        if gemini_client:
                            active_engine = "gemini"
                            engine_mode = "gemini"
                            print(f"\nkiraht AI: Switched active engine to 🚀 Google Gemini ({gemini_model}), {call_me}.")
                        else:
                            print(f"\nkiraht AI: Google Gemini API key not found in .env. Please configure GEMINI_API_KEY first, {call_me}.")
                    elif target_eng in ("ollama", "local", "offline"):
                        active_engine = "ollama"
                        engine_mode = "ollama"
                        print(f"\nkiraht AI: Switched active engine to 🛡️ Local Ollama ({model}), {call_me}.")
                    elif target_eng in ("auto", "hybrid", "default"):
                        engine_mode = "auto"
                        active_engine = "gemini" if gemini_client and is_online() else "ollama"
                        print(f"\nkiraht AI: Engine set to Auto/Hybrid (Active: {active_engine.title()}), {call_me}.")
                else:
                    curr_name = f"🚀 Google Gemini ({gemini_model})" if active_engine == "gemini" else f"🛡️ Local Ollama ({model})"
                    gem_status = f"Ready ({gemini_model})" if gemini_client else "Not configured (add GEMINI_API_KEY in .env)"
                    print(
                        f"\n[KIRAHT AI Dual-Engine Status]\n"
                        f"  Active Engine : {curr_name}\n"
                        f"  Engine Mode   : {engine_mode.title()}\n"
                        f"  Local Ollama  : {model} (Ready)\n"
                        f"  Gemini Cloud  : {gem_status}\n"
                        f"  Switch command: /engine gemini | /engine local | /engine auto"
                    )
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

            # Intent: Conversational Follow-up File Saving ("yeah do bro", "save it", etc.)
            from core import try_handle_conversational_file_save
            is_save, s_cat, s_tool, s_res = try_handle_conversational_file_save(user_input, call_me)
            if is_save:
                print(f"\nkiraht AI: {s_res}")
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": s_res})
                continue

            # Intent: Create file with content (gated by Security Permission Gate)
            create_file_match = re.search(
                r"^(?:please\s+)?create\s+(?:a\s+)?(?:new\s+)?file\s+([a-zA-Z0-9_\-\./\\]+)\s+with(?:\s+content)?\s+(.+)$",
                user_input,
                re.DOTALL | re.IGNORECASE,
            )
            if create_file_match:
                target_name = create_file_match.group(1).strip()
                new_code = create_file_match.group(2).strip()
                from security import request_permission
                if request_permission("file_write", f"Create or overwrite file '{target_name}'", call_me=call_me):
                    from file_tools import safe_create_or_modify_file, resolve_path
                    res = safe_create_or_modify_file(target_name, new_code, call_me=call_me)
                    full_p = resolve_path(target_name)
                    print(f"\nkiraht AI: {res} (Location: {full_p})")
                    messages.append({"role": "user", "content": user_input})
                    messages.append({"role": "assistant", "content": f"{res} (Location: {full_p})"})
                else:
                    print(f"\nkiraht AI: Operation cancelled, {call_me}. '{target_name}' was not modified.")
                continue

            # Check for laptop / OS operation commands (Desktop Apps, Files, Hardware)
            handled, action_result = execute_system_command(user_input, call_me)
            if handled:
                if action_result.startswith("__NEED_RECIPIENT__"):
                    parts = action_result.split(":")
                    send_flag = parts[1] if len(parts) > 1 else "review"
                    auto_send = (send_flag == "send")
                    pending_whatsapp = {"type": "need_recipient", "auto_send": auto_send}
                    print(f"\nkiraht AI: Sir, who would you like to send a WhatsApp message to? (or type 'cancel')")
                    continue

                if action_result.startswith("__NEED_MESSAGE__"):
                    parts = action_result.split(";;;") if ";;;" in action_result else action_result.split(":")
                    rec = parts[1]
                    display = parts[2] if len(parts) > 2 else rec.title()
                    grp_flag = parts[3] if len(parts) > 3 else "individual"
                    send_flag = parts[4] if len(parts) > 4 else "review"
                    is_group = (grp_flag == "group")
                    # Strict Safety Lock: Groups are ALWAYS review mode (fill only, never auto-send)
                    auto_send = (send_flag == "send" and not is_group)
                    pending_whatsapp = {"type": "need_message", "target": rec, "display": display, "is_group": is_group, "auto_send": auto_send}
                    if is_group:
                        print(f"\nkiraht AI: Sir, what message would you like to send to group '{display}'? (or type 'cancel')")
                    else:
                        print(f"\nkiraht AI: Sir, what message would you like to send to {display}? (or type 'cancel')")
                    continue

                if action_result.startswith("__NEED_GROUP__"):
                    parts = action_result.split(";;;") if ";;;" in action_result else action_result.split(":", 4)
                    target = parts[1]
                    msg = parts[2] if len(parts) > 2 else ""
                    related_raw = parts[3] if len(parts) > 3 else "[]"
                    send_flag = parts[4] if len(parts) > 4 else "review"
                    # Strict Safety Lock: Groups are ALWAYS review mode (fill only, never auto-send)
                    auto_send = False
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

                if action_result.startswith("__NEED_PHONE__"):
                    parts = action_result.split(";;;") if ";;;" in action_result else action_result.split(":", 4)
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
                            f"    * Or re-enter the correct contact name to search again\n"
                            f"    * Or a 10-digit phone number to save '{rec.title()}'\n"
                            f"    * Or 'cancel' to abort"
                        )
                    else:
                        print(
                            f"\nkiraht AI: Sir, '{rec.title()}' is not in your contacts.\n"
                            f"  Reply with:\n"
                            f"    * Re-enter the correct contact name to search again\n"
                            f"    * Or provide a 10-digit phone number to save '{rec.title()}'\n"
                            f"    * Or 'cancel' to abort"
                        )
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
                    # If active engine is Gemini and online, stream with Google Gemini Cloud Engine
                    if active_engine == "gemini" and gemini_client and is_online():
                        try:
                            print(f"\nkiraht AI: ", end="", flush=True)
                            target_gem_model = gemini_model
                            if target_gem_model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
                                target_gem_model = "gemini-3.1-flash-lite"
                            try:
                                g_stream = gemini_client.models.generate_content_stream(
                                    model=target_gem_model,
                                    contents=prompt_content
                                )
                            except Exception as g_init_err:
                                if ("404" in str(g_init_err) or "503" in str(g_init_err)) and target_gem_model != "gemini-3.1-flash-lite":
                                    target_gem_model = "gemini-3.1-flash-lite"
                                    gemini_model = "gemini-3.1-flash-lite"
                                    g_stream = gemini_client.models.generate_content_stream(
                                        model=target_gem_model,
                                        contents=prompt_content
                                    )
                                else:
                                    raise g_init_err

                            reply_chunks = []
                            for g_chunk in g_stream:
                                txt = g_chunk.text or ""
                                print(txt, end="", flush=True)
                                reply_chunks.append(txt)
                            print()
                            full_reply = "".join(reply_chunks).strip()
                            if prompt_content != user_input:
                                messages[-1] = {"role": "user", "content": user_input}
                            messages.append({"role": "assistant", "content": full_reply})
                            continue
                        except Exception as gem_err:
                            print(f"\n[KIRAHT AI: ⚠️ Gemini API error ({gem_err}) — falling back to local Ollama]")

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
                thought_chunks = []
                is_thinking = False
                in_tool_tag = False

                for chunk in response_stream:
                    thinking = getattr(chunk.message, "thinking", None)
                    content = chunk.message.content or ""

                    if thinking and not content:
                        thought_chunks.append(thinking)
                        if show_thoughts:
                            if not is_thinking:
                                print(f"\n\033[90m┌─ 💭 [Thinking Process] " + "─" * 45 + "\033[0m\n", end="", flush=True)
                                is_thinking = True
                            print(f"\033[90m{thinking}\033[0m", end="", flush=True)
                        else:
                            if not is_thinking:
                                print("[Thinking...] ", end="", flush=True)
                                is_thinking = True
                        continue

                    if content:
                        if is_thinking:
                            if show_thoughts:
                                print(f"\n\033[90m└" + "─" * 68 + "\033[0m\n\nkiraht AI: ", end="", flush=True)
                            else:
                                print("\r\033[Kkiraht AI: ", end="", flush=True)
                            is_thinking = False

                        # Intercept raw <tool_call> tags from leaking to terminal
                        if "<tool_call>" in content or in_tool_tag:
                            in_tool_tag = True
                            reply_chunks.append(content)
                            if "</tool_call>" in content:
                                in_tool_tag = False
                            continue

                        print(content, end="", flush=True)
                        reply_chunks.append(content)

                if is_thinking and show_thoughts:
                    print(f"\n\033[90m└" + "─" * 68 + "\033[0m", flush=True)

                print()  # newline after streaming completes
                full_reply = "".join(reply_chunks).strip()
                last_thought_process = "".join(thought_chunks).strip()

                # Intercept model raw <tool_call> text outputs and execute immediately
                tc_match = re.search(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", full_reply, re.DOTALL)
                if tc_match:
                    try:
                        tc_data = json.loads(tc_match.group(1))
                        fn_name = tc_data.get("name")
                        fn_args = tc_data.get("arguments", {})
                        if fn_name:
                            print(f"\r\033[K[KIRAHT AI: ⚙️ Executing {fn_name}()]")
                            tool_res = execute_agent_tool(fn_name, fn_args, call_me)
                            print(f"\nkiraht AI: {tool_res}")
                            messages.append({"role": "assistant", "content": f"Executed {fn_name}."})
                            messages.append({"role": "tool", "content": tool_res})
                            full_reply = tool_res
                    except Exception:
                        pass

                # Intercept FILE_SAVE directives from LLM output
                from file_tools import safe_create_or_modify_file, resolve_path, KIRAHT_PROJECTS_DIR, WORKSPACE_DIR
                save_intent_keywords = [
                    r"\b(?:save\s+it|save\s+this|save\s+the\s+file|save\s+as|save\s+to|save\s+in|save\s+into)\b",
                    r"\b(?:create\s+(?:a\s+)?(?:new\s+)?file|write\s+(?:to\s+)?(?:a\s+)?file|make\s+(?:a\s+)?file)\b",
                    r"\b(?:save\s+pannu|file\s+create\s+pannu|athula\s+save|podu\s+file|add\s+pannu)\b",
                    r"\b(?:la\s+save\s+pannu|folder\s+la\s+save)\b",
                    r"^(?:yes|yeah|sure|ok|okay|do it|proceed|confirm)\b",
                ]
                has_save_intent = any(re.search(pat, user_input, re.IGNORECASE) for pat in save_intent_keywords)
                file_save_matches = list(re.finditer(r"```FILE_SAVE:([^\n]+)\n(.*?)```", full_reply, re.DOTALL))
                for m in file_save_matches:
                    save_path = m.group(1).strip().strip("'\"")
                    file_content = m.group(2)
                    base_name = os.path.basename(save_path)
                    ext = os.path.splitext(save_path)[1].lstrip(".") or "python"
                    if not has_save_intent:
                        rec_offer = f"\n\n*Shall I save this code for you, {call_me}? I recommend saving it to `kiraht's project/{base_name}`.*"
                        full_reply = full_reply.replace(m.group(0), f"```{ext}\n{file_content}\n```{rec_offer}")
                        continue
                    full_p = resolve_path(save_path)
                    norm_dir = os.path.normpath(os.path.dirname(full_p))
                    if norm_dir == os.path.normpath(WORKSPACE_DIR) and not re.search(r"\b(?:workspace|root)\b", user_input, re.IGNORECASE):
                        full_p = os.path.join(KIRAHT_PROJECTS_DIR, base_name)
                        full_p = resolve_path(full_p)
                    safe_res = safe_create_or_modify_file(full_p, file_content, call_me=call_me)
                    full_reply = full_reply.replace(m.group(0), f"```{ext}\n{file_content}\n```\n\n> **[File Saved]** `{base_name}` saved to `{full_p}`")
                    print(f"\n[KIRAHT AI: 💾 {safe_res}]")

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

        except KeyboardInterrupt:
            if is_processing:
                if messages and messages[-1].get("role") == "user":
                    messages.pop()
                print(f"\n\n[kiraht AI: Operation cancelled by {call_me}]")
                continue
            elif pending_whatsapp:
                pending_whatsapp = None
                print(f"\n\n[kiraht AI: Operation cancelled by {call_me}]")
                continue
            else:
                print(f"\nkiraht AI: Systems standing by. Goodbye, {call_me}!")
                break

        except EOFError:
            print(f"\nkiraht AI: Systems standing by. Goodbye, {call_me}!")
            break


def main() -> None:
    """
    Main entry point for KIRAHT AI.
    Supports:
      python main.py         -> Interactive Terminal Interface (default)
      python main.py --web   -> Futuristic Web HUD (http://127.0.0.1:8000)
    """
    if "--web" in sys.argv or "-w" in sys.argv:
        from web_server import run_server
        run_server()
        return

    load_dotenv()
    try:
        from global_hotkeys import start_global_hotkeys
        start_global_hotkeys()
    except Exception:
        pass
    initial_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434"
    model = os.getenv("AI_MODEL", "qwen2.5:3b").strip() or "qwen2.5:3b"
    client, host = verify_and_ensure_ollama(model, initial_host)
    run_chat_loop(client, model, host=host)


if __name__ == "__main__":
    main()


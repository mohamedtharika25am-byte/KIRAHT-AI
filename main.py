"""
KIRAHT AI - Version 0.2 (J.A.R.V.I.S. Edition)
A local, intelligent AI assistant inspired by Iron Man's J.A.R.V.I.S.

Key Features:
- Live Token Streaming (immediate word-by-word terminal response).
- J.A.R.V.I.S. Persona: Razor-sharp, polite, concise, and strictly to the point.
- Persistent Memory (memory.json): Remembers user name, title ("Sir"), and preferences across sessions.
- Hybrid Internet Awareness:
    * Online: Live DuckDuckGo search for real-time news, dates, and updates.
    * Offline: Gracefully falls back to local Ollama model knowledge.
- In-memory multi-turn conversation history with session commands (/memory, /callme, /search, /clear).
- 100% local model inference (qwen3:8b or custom) via native Ollama client.
"""

import json
import os
import re
import socket
import sys
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

DEFAULT_MEMORY = {
    "user_name": "Tharika",
    "call_me": "Sir",
    "assistant_name": "KIRAHT AI",
    "persona": "J.A.R.V.I.S. - polite, razor-sharp, direct, and intelligent",
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
    Builds the core J.A.R.V.I.S. system prompt using persistent user memory.
    """
    user_name = memory.get("user_name", "Mohamed Tharik A")
    preferred = memory.get("preferred_name", "Tharik")
    call_me = memory.get("call_me", "Sir")
    persona = memory.get("persona", DEFAULT_MEMORY["persona"])
    response_style = memory.get("response_style", DEFAULT_MEMORY["response_style"])
    notes = memory.get("custom_notes", [])
    notes_str = "\n".join(f"- {n}" for n in notes)

    return (
        f"You are KIRAHT AI, an elite personal AI assistant inspired by {persona}.\n"
        f"Creator & Boss: You were developed and created by {user_name} ({preferred}). He is your sole Boss, Master, and Creator.\n"
        f"Master Identity: You are speaking with {user_name}. Always address him with high respect as '{call_me}'.\n"
        f"Tone and Rules:\n"
        f"1. {response_style}\n"
        f"2. Be razor-sharp, direct, and factual. Never add conversational filler like 'Sure!', 'I hope this helps!', or ethical lectures.\n"
        f"3. When answering questions, prioritize brevity. Use bullet points only when specifically listing items.\n"
        f"4. If live search results are provided in the context, synthesize the most accurate, current facts concisely.\n"
        f"5. When asked 'Who is your boss?', 'Who created you?', or 'Who made you?', answer clearly: '{user_name} ({call_me}) is my creator and boss.'\n"
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


def should_trigger_search(user_text: str) -> tuple[bool, str]:
    """
    Determines if the user's input asks for current/real-time information
    or explicitly requests a search.
    Returns (needs_search, search_query).
    """
    cleaned = user_text.strip()

    # Explicit command trigger: /search <query> or search: <query>
    if cleaned.lower().startswith("/search "):
        return True, cleaned[8:].strip()
    if cleaned.lower().startswith("search:"):
        return True, cleaned[7:].strip()

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
    ]

    lower = cleaned.lower()

    # Never trigger web search for assistant identity or user identity queries
    personal_keywords = [
        "your boss", "your creator", "your developer", "your master", "your owner", "your maker",
        "who are you", "who am i", "my name", "about me", "my college", "my project",
        "who made you", "who built you", "who programmed you"
    ]
    if any(pk in lower for pk in personal_keywords):
        return False, ""

    for pattern in triggers:
        if re.search(pattern, lower):
            return True, cleaned

    return False, ""


# ==========================================
# 3. OLLAMA CLIENT & INITIALIZATION
# ==========================================
def get_client_and_model():
    """
    Loads configuration from environment / .env file and initializes the Ollama client.
    """
    load_dotenv()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip() or "http://localhost:11434"
    model = os.getenv("AI_MODEL", "qwen3:8b").strip() or "qwen3:8b"
    client = ollama.Client(host=host)
    return client, model, host


def verify_ollama_status(client: ollama.Client, model: str, host: str) -> None:
    """
    Verifies that the local Ollama daemon is running and that the requested model exists.
    """
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
            print("    Available models:")
            if available_models:
                for m in available_models:
                    print(f"      - {m}")
            else:
                print("      (No models found)")
            print(f"\n    Run 'ollama pull {model}' to download the model.")
            sys.exit(1)

    except (httpx.ConnectError, ConnectionRefusedError, ConnectionError, ollama.RequestError):
        print(f"\n[!] Connection Error: Unable to connect to Ollama at {host}.")
        print("    Ensure Ollama is running ('ollama serve').\n")
        sys.exit(1)
    except Exception as err:
        print(f"\n[!] Unexpected Error while checking Ollama status: {err}\n")
        sys.exit(1)


# ==========================================
# 4. STREAMING CHAT LOOP (J.A.R.V.I.S.)
# ==========================================
def run_chat_loop(client: ollama.Client, model: str) -> None:
    """
    Runs the J.A.R.V.I.S. interactive terminal chat loop with token streaming,
    persistent memory, and live web search integration.
    """
    memory = load_memory()
    call_me = memory.get("call_me", "Sir")
    system_prompt = build_system_prompt(memory)

    # Check internet connectivity
    online = is_online()
    status_icon = "🌐 ONLINE (Live Web Search)" if online else "📴 OFFLINE (Local Memory Only)"

    print("=" * 60)
    print(f"  KIRAHT AI — J.A.R.V.I.S. Edition")
    print(f"  Model: {model}  |  Status: {status_icon}")
    print(f"  Laptop Tools: Active (Apps, Battery, Volume, Web, Folders)")
    print(f"  Commands: /memory, /callme <title>, /name <name>, /search <query>, /clear, exit")
    print("=" * 60)
    print(f"\nkiraht AI: Online and ready, {call_me}. How may I assist you?")

    messages = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            # Check for exit
            if user_input.lower() in ("exit", "quit", "bye"):
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

            # Check for laptop / OS operation commands
            handled, action_result = execute_system_command(user_input, call_me)
            if handled:
                print(f"\nkiraht AI: {action_result}")
                messages.append({"role": "user", "content": user_input})
                messages.append({"role": "assistant", "content": action_result})
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

            # Add to messages history
            # In history, store the user's prompt (with search context for this turn)
            messages.append({"role": "user", "content": prompt_content})

            # Stream generation with low temperature for concise, direct responses
            try:
                response_stream = client.chat(
                    model=model,
                    messages=messages,
                    stream=True,
                    options={"temperature": 0.35},
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

            except ollama.ResponseError as err:
                messages.pop()
                print(f"\nkiraht AI: [Ollama Error {err.status_code}] {err.error}")

            except (httpx.ConnectError, ConnectionRefusedError, ConnectionError, ollama.RequestError):
                messages.pop()
                print(f"\nkiraht AI: [Connection Error] Lost connection to local Ollama daemon at http://localhost:11434.")

            except Exception as err:
                messages.pop()
                print(f"\nkiraht AI: [Error] {err}")

        except (KeyboardInterrupt, EOFError):
            print(f"\nkiraht AI: Systems standing by. Goodbye, {call_me}!")
            break


def main() -> None:
    """
    Main entry point for KIRAHT AI (J.A.R.V.I.S. Edition).
    """
    client, model, host = get_client_and_model()
    verify_ollama_status(client, model, host)
    run_chat_loop(client, model)


if __name__ == "__main__":
    main()

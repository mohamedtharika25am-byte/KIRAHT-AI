# KIRAHT AI (Phase 1)

A local, intelligent personal AI assistant powered by **Ollama**, featuring live token streaming, concise personality tuning, persistent memory, and real-time DuckDuckGo web search.

---

## Key Features in Phase 1

1. **⚡ Live Token Streaming**: Words appear immediately on screen as they generate (sub-2s initial response), eliminating long delays.
2. **🎯 Elite Persona**: Polite, razor-sharp, and strictly to the point (1–3 sentences). No conversational filler or rambling essays.
3. **🧠 Persistent Memory (`memory.json`)**:
   - Remembers who you are across terminal sessions and PC restarts.
   - Defaults to addressing you as **"Sir"**.
   - Built-in commands to update your profile on the fly.
4. **🌐 Hybrid Online/Offline Awareness**:
   - **Online**: Uses free DuckDuckGo search to fetch live facts, news, and current updates.
   - **Offline**: Gracefully falls back to your local Ollama model knowledge.
5. **🛡️ 100% Local Inference & Privacy**:
   - Core inference runs locally via Ollama (`http://localhost:11434`).
   - Zero paid cloud API keys or accounts required.

---

## Architecture Flow

```
                     User Prompt
                          │
          [Auto-Detect Internet & Search Trigger]
                     /                 \
          (Online & Search Needed)    (Offline or Standard Question)
                 ▼                                 │
     DuckDuckGo Live Search                        │
       (Current Web Snippets)                      │
                 │                                 │
                 └──────────────┬──────────────────┘
                                │
             [System Prompt + Persistent Memory]
                    (memory.json: "Sir", Concise)
                                │
                                ▼
                   Local Ollama (qwen3:8b)
                  (Live Token-by-Token Stream)
                                │
                                ▼
                       Terminal Output
```

---

## Built-in Commands

| Command | Description |
| :--- | :--- |
| `/memory` | View your saved profile and personality directives in `memory.json`. |
| `/knowledge` | View self-learned facts saved in `knowledge_cache.json`. |
| `/scan_apps` | Scan and index installed Windows applications into `apps_cache.json`. |
| `/clipboard` | View current contents of the Windows clipboard. |
| `/callme <title>` | Change what KIRAHT calls you (e.g. `/callme Boss` or `/callme Sir`). |
| `/name <name>` | Update your registered user name in `memory.json`. |
| `/search <query>` | Explicitly force a real-time web search for any query. |
| `/clear` | Clear the current conversation history while keeping system instructions intact. |
| `exit` / `quit` / `bye` | Gracefully shut down the assistant. |

---

## 💻 Laptop Operations & PC Automation Engine

KIRAHT AI executes local Windows operations instantly (sub-100ms) right from the chat loop:

| Action Category | Example Commands | Description |
| :--- | :--- | :--- |
| **WhatsApp Messaging** | `send whatsapp to rahul saying I will be late`, `whatsapp mom: reach home safely`, `whatsapp +919876543210 msg: check this` | Directly focuses WhatsApp desktop with contact chat and prefilled message via Windows URI scheme. |
| **Contacts Book** | `add contact rahul 9876543210`, `list contacts` | Manages local contact book saved securely in `contacts.json`. |
| **Desktop App Launcher** | `open whatsapp`, `open chatgpt`, `open android studio`, `open vs code`, `open cursor` | Automatically launches **native Windows desktop applications** (170+ apps indexed). |
| **Intelligent App Closer** | `close chatgbt`, `close spotify`, `close notepad` | Terminates processes with fuzzy matching, alias resolution, and browser tab guidance. |
| **File Size & Info** | `size of main.py`, `file_tools.py size enna`, `info of memory.json` | Shows file size (Bytes, KB, MB), total lines, location, and modified date. |
| **Open File in Editor** | `open main.py`, `open file memory.json` | Opens files directly in Visual Studio Code (`code <file>`) or default editor. |
| **Directory & Code Explorer** | `list files`, `read requirements.txt`, `explain file_tools.py` | Lists workspace files and streams code into terminal or LLM context for review. |
| **Precision Audio** | `vol 50`, `set volume 70`, `vol up`, `vol down`, `increase volume by 15` | Sets exact volume (0-100%) or adjusts by default ±10% or custom delta via Windows Core Audio. |
| **Repeat / Dispatcher** | `again`, `now`, `repeat`, `once more` | Re-executes last system command (battery, time, wifi) or re-explains previous chat topic. |
| **Time & Date** | `time`, `what is the time`, `today date`, `current date` | Reports live system clock, day of the week, and formatted date. |
| **Screen Capture** | `take screenshot`, `screen shot`, `capture screen` | Fast native Windows screen capture saved to `Pictures\Screenshots` (0.05s). |
| **Quick Notes** | `note: meeting at 4pm`, `show notes`, `clear notes` | Local quick notepad for developer tasks and ideas saved in `notes.json`. |
| **Network & Ping** | `wifi status`, `ping`, `check ping`, `network latency` | Reports Wi-Fi SSID/signal quality and tests latency. |
| **System Maintenance** | `empty recycle bin`, `lock pc`, `battery status` | Empties Recycle Bin, locks workstation, or reports battery with low-battery alerts. |
| **Clipboard Access** | `clipboard`, `copy <text>`, `clear clipboard` | Reads, copies, or clears text on the Windows clipboard. |
| **Terminal & Dev Runner** | `run git status`, `run python file_tools.py`, `pip list` | Runs terminal commands and captures output with safety guardrails. |
| **Web & Media** | `open youtube and search AR Rahman`, `open github`, `open gmail` | Launches URLs or searches directly in default browser. |

---

## Project Structure

```text
KIRAHT AI/
├── main.py              # Main core logic, streaming, search, and chat loop
├── tools.py             # Unified automation engine & intent router
├── file_tools.py        # File inspections, size, VS Code launcher, and code reading
├── system_tools.py      # Clipboard, terminal runner, screenshot, Wi-Fi, and OS controls
├── apps_cache.json      # Auto-indexed cache of installed Windows desktop applications
├── memory.json          # Persistent user profile and memory
├── knowledge_cache.json # Self-learned persistent fact cache
├── .env                 # Local configuration (model name, Ollama host)
├── .env.example         # Example template for .env
├── .gitignore           # Git ignore rules
├── requirements.txt     # Dependencies (ollama, python-dotenv, ddgs, psutil, pywin32)
└── README.md            # Comprehensive documentation
```

---

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Ollama is Running**:
   ```bash
   ollama serve
   ```
   Verify that your model is pulled (default: `qwen2.5:3b`):
   ```bash
   ollama pull qwen2.5:3b
   ```

3. **Start KIRAHT AI**:
   ```bash
   python main.py
   ```

---

## Customizing Your Assistant

You can edit [memory.json](file:///d:/KIRAHT%20AI/memory.json) directly or use terminal commands:
```json
{
  "user_name": "Tharika",
  "call_me": "Sir",
  "assistant_name": "KIRAHT AI",
  "persona": "Polite, razor-sharp, direct, and highly intelligent personal assistant",
  "response_style": "Strictly concise. Answer only what is asked in 1-3 sentences.",
  "language_preference": "English / Tanglish"
}
```
To switch models in the future, simply change `AI_MODEL` in [.env](file:///d:/KIRAHT%20AI/.env) (e.g., `AI_MODEL=llama3.2:3b`).

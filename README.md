# KIRAHT AI — Local Web HUD & Personal AI Assistant

A futuristic, local personal AI assistant powered by **Local Ollama** (`qwen2.5:3b`) and **Google Gemini Cloud Engine** (`gemini-3.1-flash-lite`), featuring a tactical **JARVIS-style Web HUD**, live token-by-token streaming, real-time hardware telemetry, persistent memory, and Windows automation.

---

## 🚀 Key Features

1. **🌐 Tactical Web HUD (FastAPI + WebSocket)**:
   - Futuristic dark cyberpunk dashboard accessible locally at `http://127.0.0.1:8000`.
   - Real-time bidirectional streaming over WebSocket (`/ws`).
   - Visual telemetry gauges for CPU, RAM, Disks, Battery, Wi-Fi, OS, and Uptime.
   - Quick action control bar and live activity event feed.
2. **⚡ Dual-Engine AI Architecture**:
   - **Local Ollama**: 100% offline inference with native function tool calling (`qwen2.5:3b`).
   - **Google Gemini Cloud**: High-speed cloud reasoning (`gemini-3.1-flash-lite`) and live Gemini Vision screen inspection.
   - Dynamic auto-failover: Smoothly switches between cloud and local Ollama if offline.
3. **🧠 Memory vs. Chat History Separation**:
   - **User Profile Memory (`memory.json`)**: Persistent identity directives, boss profile ("Mohamed Tharik A", "Sir"), college background, and custom rules.
   - **Local Conversation History (`chat_history.json`)**: Dedicated session conversation persistence, loaded automatically in Web HUD and cleared with `/clear`.
4. **⚙️ Deterministic Tool Engine**:
   - High-speed zero-token evaluation for math, unit conversions, weather, media controls, QR generation, documents, and system tasks without unnecessary LLM calls.
5. **💻 Native Windows Automation**:
   - Desktop application launcher (170+ apps indexed with typo tolerance).
   - Precision audio controls, screen capture, WhatsApp messaging, and hardware controls.
6. **🖥️ Dual Mode Support**:
   - Run in interactive **Terminal Mode** (`python main.py`) or full **Web HUD Mode** (`python main.py --web` or `python web_server.py`).

---

## 🏛️ System Architecture

```text
                           ┌────────────────────────────┐
                           │      KIRAHT AI BRAIN       │
                           │         (core.py)          │
                           └─────────────┬──────────────┘
                                         │
                 ┌───────────────────────┴──────────────────────┐
                 ▼                                              ▼
   ┌───────────────────────────┐                  ┌───────────────────────────┐
   │       Terminal Mode       │                  │       Web HUD Server      │
   │         (main.py)         │                  │      (web_server.py)      │
   └─────────────┬─────────────┘                  └─────────────┬─────────────┘
                 │                                              │
                 ▼                                              ▼
          Console Buffer                                    WebSocket
           (STDOUT / CLI)                                   (ws://127.0.0.1:8000/ws)
                                                                │
                                                                ▼
                                                        Browser Tactical HUD
                                                       (http://127.0.0.1:8000)
```

---

## 💻 Web HUD Dashboard Layout

The Web HUD is structured into 4 interactive zones:

- **HEADER**:
  - Logo, Online/Offline indicator, Active AI engine status, live local clock, and session uptime ticker.
- **LEFT PANEL — SYSTEM TELEMETRY**:
  - Live animated bar gauges for CPU usage %, RAM utilization %, Battery/charging state, Drive storage (C: / D:), Wi-Fi SSID, and host OS.
- **CENTER — CHAT & STREAMING**:
  - Conversation cards (User vs. KIRAHT AI), live token-by-token streaming, state badges (`READY`, `PROCESSING`, `SEARCHING`, `USING TOOL`, `RESPONDING`), suggestion chips, chat input, and send button.
- **RIGHT PANEL — AI & CORE STATUS**:
  - Active AI engine details, User memory summary (`memory.json`), DuckDuckGo web intelligence status, and registered tool directory.
- **BOTTOM — QUICK ACTIONS & ACTIVITY LOG**:
  - One-click buttons: System Status, Open Chrome, Open VS Code, Screenshot, File Manager, YouTube, Clear Chat.
  - Real-time activity log showing live actor dispatches (`User ➔ KIRAHT ➔ System`).

---

## 🛠️ Integrated Tool Suite

KIRAHT AI features 11 deterministic and automated tools:

| # | Tool | Example Trigger | Description |
| :-: | :--- | :--- | :--- |
| **1** | **Weather** | `weather in Coimbatore`, `what is the weather` | Live weather, feels-like temperature, humidity, and wind via wttr.in. |
| **2** | **Calculator** | `calculate 25 * 40 + 150`, `15% of 250`, `sqrt(144)` | Deterministic safe AST math evaluator (arithmetic, percentages, trig, powers). |
| **3** | **Unit Converter** | `convert 100 km to miles`, `50 kg in lbs`, `100 f to c` | Instant conversion across length, weight, data, temperature, and speed. |
| **4** | **File Engine** | `size of main.py`, `list files`, `read file_tools.py` | Inspect file/folder sizes, list directories, and view code safely. |
| **5** | **Screenshot** | `take screenshot`, quick action button | Native Windows screen capture saved to `Pictures\Screenshots` with HUD preview. |
| **6** | **System Telemetry** | `system status`, `battery status`, `cpu status` | Real-time psutil hardware telemetry (CPU, RAM, Disks, Battery, Network). |
| **7** | **Translation** | `translate hello to tamil`, `translate good morning in french` | Deterministic language translation via MyMemory API. |
| **8** | **QR Generator** | `generate qr code https://github.com` | Creates high-resolution QR code PNG saved to `static/generated/` and previews in chat. |
| **9** | **Media Controls** | `play music`, `pause`, `next song`, `previous track` | Natively controls Windows media playback via virtual key events. |
| **10** | **Web Search** | `search latest AI news`, `who won today match` | Real-time DuckDuckGo web search snippet synthesis. |
| **11** | **PDF / Docs** | `read pdf document.pdf`, `inspect file notes.txt` | Reads PDF page counts and text extracts via `pypdf`. |

---

## 📋 Built-in Commands

| Command | Description |
| :--- | :--- |
| `/memory` | Inspect saved user profile directives in `memory.json`. |
| `/callme <title>` | Update preferred address title (e.g. `/callme Boss` or `/callme Sir`). |
| `/name <name>` | Update registered user name in `memory.json`. |
| `/clear` | Clear conversation history in `chat_history.json` and reset HUD viewport. |
| `/uptime` | View live system and session uptime. |
| `/engine [gemini\|ollama\|auto]` | Switch active inference engine between Cloud Gemini and Local Ollama. |
| `/scan_apps` | Scan and index installed desktop applications into `apps_cache.json`. |

---

## 📦 Project Structure

```text
d:\KIRAHT AI/
├── core.py               # Shared KIRAHT brain (memory, chat history, telemetry, streaming)
├── web_server.py         # FastAPI & WebSocket server for Web HUD (http://127.0.0.1:8000)
├── main.py               # Core entry point (supports terminal and --web modes)
├── tools.py              # Unified tool suite (weather, calculator, converter, media, QR, etc.)
├── file_tools.py         # File inspection, folder sizes, and code reader
├── system_tools.py       # Native screen capture, volume, clipboard, and Wi-Fi
├── security.py           # Permission gating and safety checks
├── static/
│   ├── index.html        # Futuristic JARVIS-style Web HUD layout
│   ├── css/
│   │   └── hud.css       # Cyberpunk glassmorphism, neon styling, and telemetry gauges
│   ├── js/
│   │   └── hud.js        # WebSocket client, token streaming, and DOM controller
│   └── generated/        # Generated QR codes and media
├── memory.json           # User profile and personality directives (Boss profile)
├── chat_history.json     # Persistent conversation history
├── knowledge_cache.json  # Cached web query facts
├── requirements.txt      # Python dependencies
└── README.md             # Documentation
```

---

## ⚙️ Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment (`.env`)**:
   Create or verify your `.env` file:
   ```env
   # Local Ollama Configuration
   OLLAMA_HOST=http://localhost:11434
   AI_MODEL=qwen2.5:3b
   KIRAHT_ALLOW_WRITES=0

   # Google Gemini Cloud Engine (Optional for Vision and Cloud inference)
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.1-flash-lite
   ```

3. **Ensure Ollama is Running**:
   ```bash
   ollama serve
   ollama pull qwen2.5:3b
   ```

---

## 🚀 Running KIRAHT AI

### Option A: Futuristic Web HUD (Recommended)
Launch the Web HUD server:
```bash
python main.py --web
```
or:
```bash
python web_server.py
```
Open your browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Option B: Interactive Terminal Interface
Launch directly in your console:
```bash
python main.py
```

---

## 🛡️ Security & Privacy

- **Localhost Isolation**: Web HUD server binds exclusively to `127.0.0.1:8000` to prevent external network exposure.
- **Credential Protection**: API keys and environment variables remain in backend Python space; zero secrets are exposed to client JavaScript.
- **Safe Mode**: File writes, deletions, and shell commands require permission gating via `security.py`.

---

## 🔧 Troubleshooting

- **Web HUD won't connect / Disconnected status**:
  Ensure `python web_server.py` is running on port 8000 and firewall isn't blocking loopback traffic.
- **Ollama Connection Refused**:
  Run `ollama serve` in a separate terminal or verify Ollama desktop application is active.
- **Microphone / Audio issues**:
  Ensure Windows Audio service is active. Master volume and media keys use native `user32.dll` and Windows Core Audio COM endpoints.

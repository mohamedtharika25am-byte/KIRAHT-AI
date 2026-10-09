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

---

## 🔮 Future Implementation & GitHub JARVIS Architectural Roadmap

### 1. Comparative Analysis: Open-Source JARVIS Projects vs. KIRAHT AI

| Tier | Representative Repositories | Core Architecture | Strengths | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Beginner / Script-based** (80% of GitHub repos) | `Jarvis-Desktop-Voice-Assistant`, `Iron-Man-Jarvis` | `while True` loop, Google SpeechRecognition, `if/elif` regex, `pyttsx3`, `pywhatkit` | Fast for 5 hardcoded commands, easy to run | Fragile: No LLM reasoning, robotic 1990s voice, freezes on unexpected phrasing, mouse hijacking during automation. |
| **Tier 2: Modern Local LLM Assistants** | `BranchingBad/ollama-STT-TTS`, `officialuditpandey/JARVIS-`, `Jm7997/JARVIS` | `openWakeWord` + `faster-whisper` + Ollama (`Llama 3` / `Qwen`) + `edge-tts` / `Piper` + PyQt6 HUD | 100% offline, privacy-first, natural conversational reasoning | Often lacks deep Windows OS automation; limited contact resolution; heavy RAM consumption if unquantized. |
| **Tier 3: Enterprise & Agentic Automators** | `OpenInterpreter`, `microsoft/JARVIS` (HuggingGPT), AutoGen Desktop | LLM Agent with Tool Calling (ReAct), Dynamic PowerShell/Python execution, Windows UIA | Can accomplish arbitrary computer tasks, self-corrects on errors | High token usage, latency, potential safety risks without strict permission gating. |
| **KIRAHT AI (Current Architecture)** | **KIRAHT AI** | **Hybrid Brain** (`qwen2.5:3b` + `gemini-3.1-flash-lite`) + Deterministic Pre-Router + **3D Web HUD** + Native Windows API Automation | Sub-millisecond pre-routing, zero token waste on deterministic tools, persistent memory vs chat history separation, enterprise permission gate. | Real-time wake-word and token-to-voice streaming in active development. |

---

### 2. Architectural Pipeline Upgrades (Implemented)

#### A. Window Management & "Bring-to-Front" App Switcher
- **Duplicate Window Prevention**: When user says *"open chrome"*, *"open vs code"*, or *"open notepad"*, KIRAHT AI now inspects active visible windows via Win32 `EnumWindows` and brings the existing instance to the foreground instead of spawning redundant windows.
- **Windows 11 Foreground Restriction Bypass**: Uses the Win32 `AttachThreadInput` trick with `SW_RESTORE` and `SetForegroundWindow` to ensure background workers can bring windows to the top without flashing orange on the taskbar.
- **Window State Directives**:
  - `minimize window` / `minimize <app>`
  - `maximize window` / `maximize <app>`
  - `restore window` / `unminimize <app>`
  - `switch to <app>` / `focus <app>`
  - `close window` / `close active window` (graceful `WM_CLOSE` without killing process trees)

#### B. Windows Registry "App Paths" Indexing
- Scans both `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths` and `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths` plus `%LOCALAPPDATA%\Microsoft\WindowsApps`.
- Directly indexes developer tools, editors, and utilities (`code.exe`, `chrome.exe`, `brave.exe`, `notepad++.exe`, `vlc.exe`, `7zFM.exe`, `wt.exe`) that do not always create Start Menu shortcuts.

#### C. Zero-Drop WhatsApp Automation Pipeline
- Replaced fixed delays with dynamic active window polling (`wait_for_window_active`) up to 3.5s timeout.
- Instant process-name checking via `psutil.Process(pid)` replacing whole-system iteration loops.
- Active clipboard and selection verification (`Ctrl+A` -> `Ctrl+V` -> multi-pulse Enter) preventing duplicate characters or missed deliveries under high system load.

#### D. Tactical Web HUD Voice Engine
- **Voice Input (Speech-to-Text)**: Tactical microphone button (`🎙️`) in the chat input bar utilizing Web Speech Recognition (`webkitSpeechRecognition`) with real-time transcript streaming.
- **Voice Output (Text-to-Speech)**: High-speed vocal speech synthesis (`🔊 VOICE MODE`) reading assistant responses aloud with natural cadence and Markdown stripping.
- **Reactive Equalizer Frequency Spectrum**: Real-time wave harmonic animations in the 32-bar audio spectrum while KIRAHT is speaking.

---

### 3. Future Roadmap Phases

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       KIRAHT AI UPCOMING ROADMAP                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 1: Real-Time Sentence-Level Neural Voice (Edge-TTS / Piper)           │
│   • As tokens stream from Ollama/Gemini, buffer until punctuation (. ! ?)   │
│   • Stream audio chunks over WebSocket to Web HUD audio buffer               │
│   • Time-to-first-voice drops to <300ms with ultra-realistic human cadence  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 2: Ultra-Low-Power Wake-Word Engine (openWakeWord)                    │
│   • 100% offline local ONNX model listening for "Hey Kiraht" or "Jarvis"     │
│   • Consumes <1% CPU with Silero Voice Activity Detection (VAD)             │
│   • Hands-free activation from across the room without cloud dependencies    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 3: Proactive Hardware Watchdog & System Alerts                        │
│   • Background daemon monitoring battery (<20%), RAM (>90%), and CPU (>95%) │
│   • Pushes tactical HUD alerts and audio chimes before system degradation    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 4: Headless Background Browser Worker (Playwright)                    │
│   • Silent WhatsApp dispatch and background web research                    │
│   • Executes tasks without stealing screen focus when user is gaming/coding  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Phase 5: Autonomous Multi-Step Agentic Planning                             │
│   • ReAct / plan-and-solve execution loops for multi-stage PC directives    │
│   • Self-correction and retry loops on unexpected file or process errors    │
└─────────────────────────────────────────────────────────────────────────────┘
```

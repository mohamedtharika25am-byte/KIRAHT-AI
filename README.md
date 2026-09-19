# KIRAHT AI (V0.1 - Local Ollama Edition)

A clean, minimalist, and beginner-friendly terminal-based AI assistant built in Python powered locally by Ollama and Qwen3:8b.

---

## 1. Project Title
**KIRAHT AI — Version 0.1 (Local Edition)**

---

## 2. What Kiraht AI is
**KIRAHT AI** is an interactive command-line AI chatbot developed in Python. It provides a direct, responsive terminal interface that connects users to locally hosted language models through Ollama (specifically `qwen3:8b`). Designed with clean code and complete privacy in mind, KIRAHT AI runs 100% locally with zero cloud API keys, zero external data sharing, and zero subscription costs.

---

## 3. What V0.1 Currently Does
In this local release (V0.1), KIRAHT AI provides essential terminal chat functionality:
- **Terminal Chat Loop**: Continuous conversational loop right inside your shell.
- **In-Memory Multi-Turn Context**: Remembers previous questions and answers during the active session so you can ask follow-ups naturally.
- **100% Local Inference**: Runs via Ollama at `http://localhost:11434` without sending data to any cloud service.
- **No Cloud API Keys**: No OpenAI API key or cloud credentials required.
- **Friendly Error Handling**: Gracefully detects if Ollama is not running or if the required model is missing, giving clear troubleshooting instructions.
- **Simple Exit Control**: Type `exit`, `quit`, or `bye` (or press `Ctrl+C`) anytime to cleanly exit.

---

## 4. How the Architecture Works
KIRAHT AI follows a straightforward, local request-response flow:

```
User
↓
Python terminal application (KIRAHT AI)
↓
Ollama Local Server (http://localhost:11434)
↓
AI Model (qwen3:8b)
↓
Response
↓
Terminal
```

1. **User**: Enters a prompt in the terminal.
2. **Python terminal application (`main.py`)**:
   - Reads the input and appends it to an in-memory list of conversation messages.
   - Packages the message history into an Ollama chat request using the native `ollama` Python SDK.
3. **Ollama Local Server (`http://localhost:11434`)**: Receives the request locally via HTTP REST endpoint.
4. **AI model (`qwen3:8b`)**: Executes inference locally on your hardware, processing the dialogue history.
5. **Response**: Ollama returns the generated response back to the local application.
6. **Terminal**: The application prints the assistant's reply and stores it in conversation memory for subsequent turns.

---

## 5. Project Folder Structure

```text
KIRAHT AI/
├── main.py              # Main application logic and terminal chat loop
├── .env                 # Optional local configuration (ignored by Git)
├── .env.example         # Example template for setting up .env
├── .gitignore           # Git ignore file protecting .env and temporary files
├── requirements.txt     # Python project dependencies (ollama, python-dotenv)
└── README.md            # Comprehensive project documentation
```

---

## 6. Prerequisites
Before running KIRAHT AI, ensure you have:
- **Python 3.8+** installed on your system (Python 3.10+ recommended).
- **Ollama** installed from [ollama.com](https://ollama.com).
- The **`qwen3:8b`** model pulled locally in Ollama:
  ```bash
  ollama pull qwen3:8b
  ```
- No API keys or internet connection required during inference!

---

## 7. Installation Steps

1. **Clone or navigate to the project directory**:
   ```bash
   cd "d:\KIRAHT AI"
   ```

2. *(Optional but recommended)* **Create and activate a virtual environment**:
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

---

## 8. How to Configure the `.env` File (Optional)

KIRAHT AI runs out of the box with defaults (`http://localhost:11434` and `qwen3:8b`). If you want to customize the host or model:

1. Copy `.env.example` to `.env`:
   - On Windows (PowerShell):
     ```powershell
     Copy-Item .env.example .env
     ```
   - On Linux/macOS:
     ```bash
     cp .env.example .env
     ```

2. Customize if needed:
   ```env
   OLLAMA_HOST=http://localhost:11434
   AI_MODEL=qwen3:8b
   ```

---

## 9. How to Install Dependencies

Install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

This installs:
- **`ollama`** (>=0.4.0): Official Ollama Python SDK.
- **`python-dotenv`** (>=1.0.0): Library for loading configuration from `.env`.

---

## 10. How to Run the Application

1. Ensure Ollama is running:
   ```bash
   ollama serve
   ```
   *(On Windows, Ollama usually runs automatically in the system tray).*

2. Make sure the `qwen3:8b` model is downloaded:
   ```bash
   ollama pull qwen3:8b
   ```

3. Execute `main.py` using Python:
   ```bash
   python main.py
   ```

If Ollama is not running or the model is missing, KIRAHT AI will display helpful instructions on how to start Ollama or pull the model.

---

## 11. Example Terminal Usage

Here is a sample interaction with KIRAHT AI:

```text
Type 'exit' to quit.

You: What is Python?

kiraht AI: Python is a versatile, high-level programming language known for its readability and clean syntax. It is widely used for web development, machine learning, data analysis, and automation.

You: What did I just ask?

kiraht AI: You asked what Python is.

You: exit

Goodbye!
```

---

## 12. Current Limitations
Because this is strictly **V0.1 Local Edition**, the following constraints apply:
- **In-Memory Only**: Conversation history resets when the application is closed.
- **Single-Threaded Terminal Interface**: Terminal interaction only; no graphical interface or web UI yet.
- **Hardware-Dependent**: Inference speed depends on your local CPU / GPU capabilities.
- **Context Window Limit**: Extremely long conversations will eventually grow in token size until the model's context window is reached.

---

## 13. Planned Future Versions

Future iterations are planned to expand KIRAHT AI incrementally:

- **V0.2**:
  - Persistent chat history (save/load past conversations to local JSON/SQLite).
  - Streaming token responses for real-time typewriter output in the terminal.
  - Interactive model switcher command.
- **V0.3**:
  - Local tool usage (calculator, local system time, basic file reading).
  - Rich terminal styling with color highlights and markdown rendering.
- **V0.4+**:
  - Voice input/output (local STT/TTS).
  - Local Retrieval-Augmented Generation (RAG) for querying personal documents.
  - Web UI / Desktop interface.

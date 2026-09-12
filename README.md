# KIRAHT AI (V0.1)

A clean, minimalist, and beginner-friendly terminal-based AI assistant built in Python using the official OpenAI SDK.

---

## 1. Project Title
**KIRAHT AI — Version 0.1**

---

## 2. What Kiraht AI is
**KIRAHT AI** is an interactive command-line AI chatbot developed in Python. It provides a direct, responsive terminal interface that connects users to state-of-the-art language models through the official OpenAI API. Designed with clean code and security best practices in mind, KIRAHT AI never hardcodes secrets, loads configuration safely via environment variables, and provides a dependable foundation for conversational AI experiments.

---

## 3. What V0.1 Currently Does
In this initial release (V0.1), KIRAHT AI provides essential terminal chat functionality:
- **Terminal Chat Loop**: Continuous conversational loop right inside your shell.
- **In-Memory Multi-Turn Context**: Remembers previous questions and answers during the active session so you can ask follow-ups naturally.
- **Secure Key Management**: Loads the OpenAI API key securely from a `.env` file using `python-dotenv`.
- **Friendly Error Handling**: Gracefully handles missing API keys, invalid credentials, rate limits, and network errors without crashing or dumping messy tracebacks.
- **Simple Exit Control**: Type `exit`, `quit`, or `bye` (or press `Ctrl+C`) anytime to cleanly exit.

---

## 4. How the Architecture Works
KIRAHT AI follows a straightforward, synchronous request-response flow:

```
User
↓
Python terminal application
↓
OpenAI API
↓
AI model
↓
Response
↓
Terminal
```

1. **User**: Enters a prompt in the terminal.
2. **Python terminal application (`main.py`)**:
   - Reads the input and appends it to an in-memory list of conversation messages.
   - Packages the message history into an OpenAI Chat Completion request.
3. **OpenAI API**: Validates the API key and forwards the conversation payload securely over HTTPS.
4. **AI model (`gpt-4o-mini`)**: Processes the dialogue history and generates a context-aware response.
5. **Response**: The API sends the text completion back to the local application.
6. **Terminal**: The application prints the assistant's reply and stores it in conversation memory for subsequent turns.

---

## 5. Project Folder Structure

```text
KIRAHT AI/
├── main.py              # Main application logic and terminal chat loop
├── .env                 # Local environment file containing your OpenAI API key (ignored by Git)
├── .env.example         # Example template for setting up .env safely
├── .gitignore           # Git ignore file protecting .env and temporary files
├── requirements.txt     # Python project dependencies
└── README.md            # Comprehensive project documentation
```

---

## 6. Prerequisites
Before running KIRAHT AI, ensure you have:
- **Python 3.8+** installed on your system (Python 3.10+ recommended).
- A valid **OpenAI API key** from the [OpenAI Developer Platform](https://platform.openai.com/api-keys).
- An active internet connection.

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

## 8. How to Create and Configure the `.env` File

KIRAHT AI requires an OpenAI API key stored in a `.env` file.

1. Locate or create the `.env` file in the project root directory (you can copy `.env.example`):
   - On Windows (PowerShell):
     ```powershell
     Copy-Item .env.example .env
     ```
   - On Linux/macOS:
     ```bash
     cp .env.example .env
     ```

2. Open `.env` in any text editor (e.g., Notepad, VS Code) and set your key:
   ```env
   OPENAI_API_KEY=sk-proj-yourActualOpenAiApiKeyGoesHere
   ```

> [!WARNING]
> Never commit your `.env` file or share your API key publicly. The `.gitignore` file included in this repository already prevents `.env` from being tracked.

---

## 9. How to Install Dependencies

Install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

This installs:
- **`openai`** (>=1.0.0): Official OpenAI Python SDK.
- **`python-dotenv`** (>=1.0.0): Library for loading configuration from `.env`.

---

## 10. How to Run the Application

Execute `main.py` using Python:

```bash
python main.py
```

If the API key is not configured or still set to the placeholder, KIRAHT AI will alert you with clear instructions without crashing. Once configured, you will see the chat prompt.

---

## 11. Example Terminal Usage

Here is a sample interaction with KIRAHT AI:

```text
Type 'exit' to quit.

You: What is Python?

kiraht AI: Python is a high-level programming language known for its clear syntax and versatility. It is widely used in web development, data science, automation, and artificial intelligence.

You: What did I just ask?

kiraht AI: You asked about Python.

You: exit

Goodbye!
```

---

## 12. Current Limitations
Because this is strictly **V0.1**, the following constraints apply:
- **In-Memory Only**: Conversation history resets when the application is closed.
- **Single-Threaded Terminal Interface**: Does not have a graphical interface, web UI, or mobile app.
- **No External Web Access**: Cannot browse the live web or access files outside the chat session.
- **Text-Only**: Does not support voice input/output or image generation/analysis.
- **Context Window Limit**: Extremely long conversations will eventually grow in token size until the model's single-request limit is reached.

---

## 13. Planned Future Versions

Future iterations are planned to expand KIRAHT AI incrementally:

- **V0.2**:
  - Persistent chat history (save/load past conversations to local JSON/SQLite).
  - Configurable model selection and system persona through `.env` or CLI arguments.
  - Streaming token responses for real-time typewriter output in the terminal.
- **V0.3**:
  - Local tool usage (e.g. calculator, local system time, basic file reading).
  - Rich terminal styling with color highlights and markdown rendering.
- **V0.4+**:
  - Voice input/output (STT/TTS).
  - Retrieval-Augmented Generation (RAG) for querying custom documents.
  - Web UI / Desktop interface.

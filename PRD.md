# PRD: KIRAHT AI — Tactical Autonomous Personal Assistant & Web HUD

> **Status**: `FINALIZED`  
> **Target Loop**: Ralph Wiggum Autonomous Coding Loop (`ralph.sh` / Ralph CLI)  
> **Repository**: `d:\KIRAHT AI`  
> **Last Updated**: 2026-10-19

---

## 1. Overview & Vision

**KIRAHT AI** is a futuristic, offline-first personal tactical AI assistant. It integrates **Local Ollama (`qwen2.5:3b`)** and **Google Gemini Cloud (`gemini-3.1-flash-lite`)** with a high-fidelity cyberpunk **Web HUD (`http://127.0.0.1:8000`)**, live bi-directional WebSocket telemetry, deterministic tools, Islamic prayer schedules, desktop automation, and persistent memory.

This Product Requirements Document (PRD) defines the quality standards, architectural constraints, completed foundation stories, and autonomous backlog items for the **Ralph Loop** task runner.

---

## 2. Quality Gates

Before any user story can be considered complete, the following quality gates must pass cleanly:

1. **Python Compilation Gate**:
   ```bash
   python -m py_compile core.py web_server.py main.py tools.py reminder_tools.py
   ```
2. **Frontend Syntax Gate**:
   ```bash
   node -c static/js/hud.js
   ```
3. **Test Suite Gate** (once tests exist):
   ```bash
   python -m unittest discover tests -v
   ```
4. **Git Hygiene**:
   - One commit per story: `feat(scope): ...` or `fix(scope): ...`
   - Clean working tree with zero untracked temp files.
   - Synchronized with `origin/main` per project rules.

---

## 3. Architecture & Constraints

- **Backend**: Python 3.10+, FastAPI, Uvicorn, WebSockets, `psutil`, `pyttsx3`, `requests`.
- **Frontend**: Vanilla HTML5, Vanilla CSS3 (glassmorphism, CSS variables, keyframe animations), Vanilla JS (no heavy frameworks, zero npm build step).
- **Inference**: Dual-engine auto-failover (Gemini Flash Cloud ⇄ Local Ollama).
- **Data Persistence**:
  - Identity & direct personality memory: `memory.json`
  - Conversation logs: `chat_history.json`
  - Reminders & prayer configuration: `reminders.json`
  - Desktop application index: `apps_cache.json`
  - Notes & scratchpad: `notes.json`

---

## 4. User Stories

### [COMPLETED] Foundation & Tactical Polish

#### US-001: Sequenced 3D Arc Reactor Startup Boot
**As a** HUD user  
**I want** the 3D Arc Reactor to spin up completely before the welcome card appears  
**So that** the startup animation feels cinematic and unobstructed  
- [x] `#reactor-core` executes complete 1080° spin-up over 1.85s.
- [x] `#tactical-welcome-hero` has `.delayed-boot` with `visibility: hidden` during reactor spin.
- [x] Hero smoothly glides and elevates into view at 1.85s with `.boot-complete` stabilization (no re-trigger/glitch).
- [x] Asset cache buster bumped to `v=5.2`.

#### US-002: Auto-Dismissing Welcome Hero on Directives
**As a** HUD user  
**I want** the welcome card to automatically fade out once I send a chat message or load history  
**So that** viewport space is maximized for live chat exchanges  
- [x] `dismissWelcomeHero()` animates card out and unmounts DOM node.
- [x] Viewport restores hero dynamically if user clears chat history via `/clear`.
- [x] `flex-shrink: 0` protects card layout from squeeze distortion.

#### US-003: 5 Daily Islamic Prayer Times & Custom Events Suite
**As a** user  
**I want** an integrated 5 prayer times schedule and event reminder tool  
**So that** I receive proactive desktop and chat notifications for daily prayers  
- [x] Dedicated calendar and prayer schedule tabs in the HUD clock popup.
- [x] Editable schedules and toggle switches stored in `reminders.json`.
- [x] Periodic background monitor (~7.5s) dispatches interactive action cards in chat.
- [x] `[ ✅ ACCEPT ]` and `[ ⏰ SNOOZE 10M ]` buttons handle state changes in real time.

#### US-004: Branded Center Logo for Generated QR Codes
**As a** user  
**I want** generated QR codes to embed the glowing Kiraht AI circular logo  
**So that** generated codes look tactical and branded  
- [x] Uses `ERROR_CORRECT_H` (30% error tolerance) in `qrcode` library.
- [x] Centers circular Kiraht logo with high-contrast cyan border.
- [x] Returns inline preview card in chat and saves to `static/generated/`.

#### US-005: Smart Scroll Pinning on Chat Transmission
**As a** user  
**I want** the chat to snap to bottom when I send a message, but never drag me down when reading previous messages during streaming  
**So that** reading earlier responses is never interrupted  
- [x] Resets scroll lock to bottom immediately upon user message transmit.
- [x] Detects upward scroll and preserves user position during active AI token streaming.

---

### [ACTIVE BACKLOG] Autonomous Ralph Loop Iterations

#### US-006: Comprehensive Unit Test Suite for Tools & Telemetry
**As a** developer running autonomous Ralph loops  
**I want** a standardized automated test suite in `tests/`  
**So that** regression bugs are caught instantly before committing  

##### Acceptance Criteria
- [ ] Directory `tests/` created with `__init__.py`.
- [ ] `tests/test_tools.py` created testing calculator, unit converter, and weather parsing logic.
- [ ] `tests/test_reminders.py` created testing prayer time validation and reminder persistence.
- [ ] All tests execute and pass via `python -m unittest discover tests -v`.
- [ ] Quality gates updated to enforce test pass before git commit.

---

#### US-007: Persistent Notes & Scratchpad Tool Integration
**As a** user  
**I want** to ask Kiraht AI to take notes, list notes, search notes, and delete notes  
**So that** my quick thoughts and tasks persist locally across sessions in `notes.json`  

##### Acceptance Criteria
- [ ] Implement `take_note(title, content)`, `list_notes()`, `search_notes(keyword)`, and `delete_note(note_id)` in `tools.py`.
- [ ] Notes are persisted in `notes.json` with unique ID, ISO timestamp, title, and content.
- [ ] Add `/notes` command and intent routing in `core.py`.
- [ ] Expose REST API endpoint `GET /api/notes` and `POST /api/notes` in `web_server.py`.
- [ ] Add a quick "Notes" shortcut chip in the Web HUD.

---

#### US-008: Audio-Reactive Arc Reactor Visualizer in HUD Voice Mode
**As a** HUD user  
**I want** the central Arc Reactor to pulse and react to my microphone audio level in Voice Mode  
**So that** the reactor feels alive and responsive to my speech  

##### Acceptance Criteria
- [ ] Initialize `AudioContext` and `AnalyserNode` in `static/js/hud.js` when user activates Voice Mode.
- [ ] Calculate real-time RMS audio volume from microphone input stream.
- [ ] Modulate `.reactor-epicenter` and `.voice-wave-ring` scale/brightness in real time (e.g. `transform: scale(1 + volume * 0.35)`).
- [ ] Smoothly disconnect audio stream and reset visualizer styles when microphone is muted or Voice Mode exits.

---

#### US-009: Dynamic Ollama Model Auto-Detection & Switching
**As a** user  
**I want** the Web HUD to detect all installed Ollama models and let me switch between them  
**So that** I can change local models (e.g., `qwen2.5:3b`, `llama3.2:3b`, `mistral`) without editing config files  

##### Acceptance Criteria
- [ ] Add endpoint `GET /api/models` in `web_server.py` fetching model tags from `http://localhost:11434/api/tags`.
- [ ] Fall back gracefully with cached/current models if Ollama is unreachable.
- [ ] In the Web HUD right panel (`AI & CORE STATUS`), display a dropdown showing available models.
- [ ] Selecting a model dispatches `/engine ollama <model_name>` and updates active model badges in real time.

---

#### US-010: System Resource Threshold Alerts & Diagnostic Watcher
**As a** user  
**I want** Kiraht AI to proactively warn me when RAM or CPU usage stays critically high (>90%)  
**So that** I can identify rogue processes before my workstation slows down  

##### Acceptance Criteria
- [ ] Add sliding window monitor in `core.py` background telemetry thread checking CPU/RAM.
- [ ] If CPU or RAM exceeds 90% across 3 consecutive checks (15 seconds), dispatch high-priority warning card over WebSocket.
- [ ] Warning card includes top 3 resource-consuming processes by CPU/memory.
- [ ] Include one-click "Dismiss" and "Inspect Process" action buttons.
- [ ] Add cooldown period (10 minutes) to prevent notification spam.

---

## 5. Non-Goals (Out of Scope for Current Loop)

- Full cloud sync / multi-user SaaS accounts (KIRAHT AI is single-tenant local assistant).
- Replacing native Windows system apps (automation targets existing applications).
- Heavy external frontend frameworks (React, Vue, Tailwind) — must preserve Vanilla HTML/CSS/JS.

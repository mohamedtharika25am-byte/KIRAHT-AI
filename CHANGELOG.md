# 📜 KIRAHT AI — Official Changelog & Release Notes
All notable changes, version upgrades, bug fixes, UI overhauls, and architectural enhancements for **KIRAHT AI** are documented here chronologically.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), adhering to Semantic Versioning (`vMAJOR.MINOR.PATCH`).

---

## ⚡ [v2.3.0] — 2026-10-14 11:30 AM IST (Live GitHub Release)

### 📌 Summary (சுருக்கம்):
Major overhaul addressing the Transmit/STOP button freeze, introducing ChatGPT-style smart auto-scroll with floating down-arrow (`↓`), Stark Industries Dual-Tone Arc Reactor (Cyan Outer + Intense Glowing Orange Core), High-Error-Correction Branded QR code generator with central Kiraht AI logo, 50-message cumulative history pagination, dedicated monospace date/time top pill to eliminate header shifting, and native Antigravity IDE launcher support.

---

### 🚀 New Features (புதிய வசதிகள்):
1. **ChatGPT-Style Floating Down-Arrow Button (`↓`) & Smart Auto-Scroll:**
   - Detects when the operator scrolls up (`> 70px`) to read earlier messages or code.
   - Automatically pauses forced auto-scroll during long answer streaming so the view is never yanked down.
   - Displays a sleek floating glassmorphic down-arrow button (`↓`) with cyan pulse. Clicking it smoothly animates scroll directly to the latest response.
2. **Branded QR Code Engine with Central Kiraht Logo (`tools.py`):**
   - Upgraded to `ERROR_CORRECT_H` (High: 30% redundancy).
   - Generates tactical QR codes with the official circular Kiraht AI logo embedded in the exact center with a white/cyan shield badge.
   - 100% smartphone camera scannable across all lighting conditions.
3. **Cumulative 50-Message History Pagination (`core.py`, `web_server.py`, `hud.js`):**
   - Replaced full history dumps with incremental batches: clicking "LOAD HISTORY" slices and renders the latest 50 messages (`first 50`), and clicking again prepends the preceding 50 messages (`second 50`, `third 50`, etc.).
   - Increased persistent storage buffer in `core.py` from 100 to 500 messages.
   - Added backward-compatible `/chat_history.json` and paginated `/api/history?limit=50&offset=0`.
4. **Antigravity IDE Quick Action Tile & Deep Launch (`tools.py`, `web_server.py`, `index.html`):**
   - Added tactical tile for **ANTIGRAVITY** positioned directly above **VS CODE**.
   - Added high-speed native launcher detecting `Antigravity IDE.exe` in `%LOCALAPPDATA%\Programs\Antigravity IDE\`.

---

### 🐞 Bug Fixes & Defect Resolutions (பிரச்சனை தீர்வுகள்):
1. **Transmit / STOP Button Stuck Defect Resolved:**
   - **Background Tab Throttling Fix:** Implemented `document.hidden` queue bypass and `visibilitychange` handler in `hud.js`. Drains word streaming queue immediately when the tab is in the background, bypassing the 1000ms browser throttling.
   - **Guaranteed `finally:` Block:** Added bulletproof `finally:` in `web_server.py` ensuring `stream_end` and `status: READY` packets are dispatched on every command, preventing orphan `isGenerating = true` states.
   - **Quick Action Completion Dispatch:** Dispatched explicit `stream_end` packets on all quick actions (System Status, Screenshot, Apps) so button automatically reverts.
   - **20-Second Safety Watchdog:** Integrated client-side watchdog timer in `hud.js` that automatically auto-recovers the button to `EXECUTE` if server latency or packet loss exceeds 20 seconds.
   - **Markdown Parsing Crash Guard:** Wrapped `formatMarkdown` in `try...catch` inside the streaming timer so unescaped tokens never crash the interval.
2. **Top Bar Header Time Movement / Jitter Resolved:**
   - **Dedicated Monospace Pill Container (`.clock-date-pill`):** Encapsulated Date (`14 OCT 2026`) and Clock (`11:05:00 AM`) in a glassmorphic pill with `font-variant-numeric: tabular-nums` and monospace typography. Top bar never shifts or jitters by even 1 pixel.
3. **CSS Parsing Error in `hud.css` Resolved:**
   - Removed orphaned rules and unmatched closing brace at line 2458 in `static/css/hud.css`. Total CSS brace balance verified to 0.

---

### 🎨 UI & Aesthetics Overhaul (தோற்றம் & வடிவமைப்பு):
1. **Stark Industries Dual-Tone Arc Reactor (Cyan Outer + Intense Orange Core):**
   - Configured `.epicenter-plasma-core` with radial amber-orange plasma (`rgba(255, 120, 0, 0.8)`), `#ff7700` border, and warm 35px glow.
   - Updated `.gyro-ring-inner` with dual amber/orange borders (`#ffaa00` and `#ff5500`).
   - Outer concentric SVG holographic rings maintain signature tactical cyan glow for an authentic Iron Man Mark XLIV aesthetic.
2. **Circular Rotating HUD Ring Kiraht Logo:**
   - Upgraded `.logo-image-wrap`, `.brand-logo-img`, and `.assistant-card .message-avatar` from square box (8px radius) to full circular glass badges (`50% border-radius`).
   - Added an outer rotating dashed HUD reticle ring (`::before`) spinning continuously around the brand logo.
3. **Button Nomenclature Upgrade:**
   - Renamed `TRANSMIT` to **`EXECUTE`** (`Execute Directive [Enter]`).
4. **Quick Action Tiles Rearrangement:**
   - Reordered action tiles: `OPEN CHROME` ➔ `BRAVE BROWSER` ➔ `ANTIGRAVITY` ➔ `VS CODE` ➔ `WHATSAPP` ➔ `TASK MANAGER` ➔ `SCREENSHOT` ➔ `SYSTEM STATUS` (moved directly below Screenshot).
5. **Telemetry Section Spacing & Model Placement:**
   - Reduced padding and stat row gaps across Telemetry for a tighter, high-density tactical layout.
   - Auto-fitting grid (`minmax(75px, 1fr)`) prevents circular dials from getting clipped when resizing panels.
   - Moved Ollama Model badge (`#core-model-name`) to the very top of the `KIRAHT CORE` section.

---

## ⚡ [v2.2.0] — 2026-10-10
- **3D Chamfered Tactical HUD Panels:** Introduced 3-column resizable layout with left telemetry, center chat hero, and right action tiles.
- **Circular Hardware Gauges:** Implemented real-time SVG circular gauges for CPU, RAM, Battery, and Disk.
- **Global Hotkeys Daemon (Category 2):** Integrated `global_hotkeys.py` listening for `F9`, `F10`, `F8`, `Win+Shift+K`, `Ctrl+Alt+S`.

## ⚡ [v2.1.0] — 2026-10-05
- **Dual-Engine Speech Recognition (STT):** Integrated 100% local offline `faster-whisper` (CTranslate2) with Web Speech API cloud fallback.
- **Voice Interruption & Barge-In:** Allowed natural voice cut-off during active AI speech output.
- **Real-Time Token Streaming:** Added word-by-word streaming pipeline over WebSocket connection.

## ⚡ [v2.0.0] — 2026-09-28
- **Futuristic Web HUD Dashboard:** Migrated from CLI-only interface to full browser-based dashboard running on `http://127.0.0.1:8000`.
- **Interactive 3D Arc Reactor:** Introduced holographic concentric SVG rotating rings with gyroscopic 3D perspective stage.

## ⚡ [v1.0.0] — Initial Release
- **Core AI Assistant:** Terminal-based personal assistant with Ollama LLM integration, system automation, and web searching.

---
*Maintained by Mohamed Tharika & Antigravity IDE Pair Programming Engine.*

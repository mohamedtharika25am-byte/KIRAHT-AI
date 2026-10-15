# 📜 KIRAHT AI — Official Changelog & Release Notes
All notable changes, version upgrades, bug fixes, UI overhauls, and architectural enhancements for **KIRAHT AI** are documented here chronologically.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), adhering to Semantic Versioning (`vMAJOR.MINOR.PATCH`).

---

## ⚡ [v2.5.2] — 2026-10-15 12:40 PM IST (Complete Transcript Removal)

### 📌 Summary (சுருக்கம்):
Completely removed the Voice Transcript component, sidebar, and right panel tab per user request. The right panel is now dedicated exclusively to Tactical Quick Action Tiles with a clean, unified header (`⚡ ACTIONS`) mirroring the Telemetry panel.

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Complete Removal of Transcript UI:**
   - Removed `📜 TRANSCRIPT` tab button (`#tab-btn-transcript`) and `.tabbed-panel-header` wrappers.
   - Removed the `#voice-transcript-wrapper` sidebar and DOM lists from `index.html`.
   - Styled the right panel header with standard unified `.panel-header.compact-header` containing `⚡ ACTIONS` title and collapse button.
2. **Controller Safeguards & Mode Normalization:**
   - Updated `setHudMode()` and `switchRightTab()` in `hud.js` to always keep Tactical Action Tiles active in both Voice and Chat modes.
   - Removed transcript event triggers and history sync overhead.

---

## ⚡ [v2.5.1] — 2026-10-15 12:05 PM IST (Popup Clipping Fix, ⏱️ Time & ⌛ Uptime Redesign)

### 📌 Summary (சுருக்கம்):
Tactical patch fixing calendar popup clipping behind panels by lifting `#hud-calendar-popup` to the root viewport layer with `position: fixed; z-index: 999999`, removing `.hud-header`'s `clip-path` constraint, adding dedicated `⏱️` (Stopwatch) icon to Time and `⌛` (Hourglass) icon to Uptime, and styling the top capsule with modular glassmorphic micro-chips.

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Calendar Popup Stacking & Clipping Fix:**
   - Lifted `#hud-calendar-popup` outside `<header>` in DOM to eliminate ancestor clipping.
   - Removed `clip-path` on `.hud-header.tactical-frame` and enabled `overflow: visible; z-index: 1000`.
   - Pop-up positioned with `position: fixed; z-index: 999999` and calculated dynamically via `positionCalendarPopup()` based on viewport bounds and window resizing.
2. **Dedicated ⏱️ Time & ⌛ Uptime Telemetry Icons:**
   - Added Stopwatch emoji `⏱️` to the live chronometer segment (`.pill-time-segment`).
   - Added Hourglass emoji `⌛` with subtle pulse animation to the active session uptime segment (`.pill-uptime-segment`).
3. **Cyberpunk Tri-Module Capsule Redesign (Figma / Pinterest Style):**
   - Transformed the top right container into a sleek multi-segment capsule with neon cyber diamond dividers (`◆`).
   - Added subtle dropdown indicator chevron (`▾`) to the date button with smooth 180° rotation when open.

---

## ⚡ [v2.5.0] — 2026-10-15 11:45 AM IST (Figma Calendar, Uptime Fix & ChatGPT Scroll Release)

### 📌 Summary (சுருக்கம்):
Tactical UI and ergonomics release addressing user requests: permanently resolved the Uptime flickering bug by synchronizing frontend timers with backend session timestamps, redesigned the top Time & Date widget with Figma / Pinterest-inspired glassmorphism, implemented a compact interactive dropdown calendar directly below the date pill with month navigation and today highlight, and centered the floating down-arrow (`↓`) button at the bottom of the chat like ChatGPT/Claude with a strict 10-message scroll threshold and zero badge numbers.

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Permanent Uptime Synchronization Fix:**
   - Added `start_timestamp` and `session_seconds` to telemetry payload in `core.py`.
   - Frontend `hud.js` now smoothly synchronizes its 1-second live ticker with the backend session timestamp.
   - Removed conflicting `updateTelemetry` text overwrites, completely eliminating the rapid jumping/flickering between frontend and backend uptimes.
2. **Pinterest & Figma-Inspired Time & Date Glassmorphic Pill:**
   - Redesigned `#clock-date-pill` with cyberpunk gradient glassmorphism (`linear-gradient(135deg, rgba(8, 24, 48, 0.94), rgba(3, 12, 28, 0.98))`), 1px cyan border, and subtle cyan ambient glow.
   - Date area transformed into an interactive button (`#btn-toggle-calendar`) with smooth hover feedback.
   - High-contrast neon tabular clock (`#hud-clock`) and dedicated amber uptime chip (`#hud-uptime`).
3. **Interactive Dropdown Calendar Popup:**
   - Clicking the Date button opens a compact, holographic calendar directly below the date pill (`#hud-calendar-popup`).
   - Displays current month and year in bold cyberpunk header with `◀` (Prev) and `▶` (Next) month navigation.
   - Weekdays grid (`MO TU WE TH FR SA SU`) and interactive days grid.
   - Today's date highlighted with Stark Arc Reactor cyan glow and bold accent.
   - `TODAY` jump shortcut in the footer and automatic dismissal when clicking outside or pressing `Escape`.
4. **Centered ChatGPT / Claude Style Down-Arrow (↓):**
   - Centered horizontally at the bottom of the chat viewport (`left: 50%; transform: translateX(-50%); bottom: 16px;`) right above the input bar.
   - Removed all badge numbers/counts (`+10`) for a clean, minimal circular button.
   - Triggers strictly when the user has scrolled past at least 10 chat messages (`cardsBelow >= 10 || scrollGap >= 1200`).
   - Profile images, avatars, and headers kept 100% untouched.

---

## ⚡ [v2.4.0] — 2026-10-14 12:35 PM IST (Live Tactical Patch & Visual Overhaul)

### 📌 Summary (சுருக்கம்):
Critical stability patch fixing the STOP button lock caused by a JS variable scope bug, eliminating classroom noise auto-transmission via a new Voice Manual/Auto toggle with Tamil (`TA-IN`) support, adding dual history pagination controls (`+50 HISTORY` and `➖ 50` collapse), removing the legacy audio spectrum footer for a clean full-width activity console, relocating the floating down-arrow (`↓`) button above the input bar with wheel scroll-pause, elevating Arc Reactor core opacity to 0.82 with Stark Industries golden-orange plasma flicker, eliminating panel header clipping (`TELEMETRY`), and ensuring reliable branded QR code generation with center logo.

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Live Date, Monospace Clock & Uptime Top Pill:**
   - Integrated live Date (`14 OCT 2026`), Tabular Monospace Clock (`12:30:00 PM`), and System Uptime (`UP: 28h 16m`) in a unified, non-jittering glassmorphic pill.
2. **Dual History Controls (`+50 HISTORY` & `➖ 50 LESS`):**
   - Click `+50 HISTORY` to load the preceding 50 archived messages.
   - Click `➖ 50` to collapse/hide 50 loaded past messages from the viewport, with live message count badge.
3. **Voice Classroom Noise Safeguard & Tamil/English Switcher:**
   - **Manual Dictation Mode (Default):** Speech recognition loads transcribed text directly into the chat textarea for review before sending, preventing inadvertent auto-transmission of classroom noise.
   - **Language Toggle Chip:** Easily toggle between English (`EN 🇮🇳`) and Tamil (`TA 🇮🇳` - `ta-IN`) directly from the input bar.
   - **Background Noise Gate:** Auto-transmit mode requires `> 5` characters and 1200ms debounce to filter out random background chatter.
4. **Full-Width Tactical Activity Console:**
   - Removed legacy audio spectrum frequency bars from the footer; expanded the Activity Telemetry Stream to 100% full-width tactical terminal format.
5. **Floating Down-Arrow (`↓`) Above Input Bar:**
   - Moved button to `bottom: 78px; right: 28px; z-index: 100;` floating prominently above the input bar.
   - Added mouse wheel up (`wheel deltaY < 0`) listener to instantly pause auto-scroll when reading earlier messages.
6. **Chat Viewport Steady Typing (No Jumping Down):**
   - Added height delta compensation on `#chat-input` auto-expand so messages remain perfectly stationary when typing multi-line text.
7. **Responsive Headers & Action Tiles (No Truncation):**
   - Fixed header text clipping (`TELEMETF ◀` ➔ `TELEMETRY ◀`) using `clamp()` typography and `min-width: 0`.
   - Action tiles shrink gracefully with responsive ellipsis on title and description when resizing panels.
8. **Stark Industries Hyper-Vibrant Arc Reactor Glow:**
   - Increased reactor core opacity from 0.38 to `0.82`, eliminating murky darkness.
   - Upgraded epicenter plasma core to high-energy golden-orange plasma (`#ffe600` to `#ff7700`) with dynamic flicker animation.
9. **Branded QR Code Center Logo Engine:**
   - Robust `base_dir` image path resolution ensuring `kiraht_ai_logo.png` is always embedded in the center with high-contrast circular shield.
10. **STOP Button Freeze Permanent Resolution:**
    - Fixed `ReferenceError: textToRender is not defined` inside `finishStream()` by hoisting variable declaration and wrapping in `try ... finally { setGeneratingState(false); }`.

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

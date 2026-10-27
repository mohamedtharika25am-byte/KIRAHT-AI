# 📜 KIRAHT AI — Official Changelog & Release Notes
All notable changes, version upgrades, bug fixes, UI overhauls, and architectural enhancements for **KIRAHT AI** are documented here chronologically.

Format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), adhering to Semantic Versioning (`vMAJOR.MINOR.PATCH`).

## ⚡ [v2.8.3] — 2026-10-27 10:58 AM IST (Down Arrow Position Fix, User MP3 Audio, Auto/Manual Voice Send & Chat Alignment)

### 📌 Summary (சுருக்கம்):
Refined HUD based on user screenshot and feedback:
1. **Scroll-To-Bottom Down Arrow (`↓`) Position Fix:**
   - Changed `#btn-scroll-bottom` position from `bottom: 16px` to `bottom: 114px` so it floats cleanly above the docked chat input bar in the messages area and never obscures the bottom toolbar chips (`MANUAL`, `EN IN`, `🔊`).
2. **User Transmit Audio (`fahhh_KcgAXfs.mp3`):**
   - Replaced audio source with user's custom file `/static/audio/fahhh_KcgAXfs.mp3`, loaded with zero latency on message dispatch.
3. **Fixed Auto / Manual Voice Transmit:**
   - Offline Whisper transcription callback now strictly checks `isVoiceAutoSendEnabled`. In `MANUAL` mode, spoken text is placed into the textarea for review without auto-sending.
   - Saved `isVoiceAutoSendEnabled` to `localStorage` (`kiraht_voice_auto_send`) and restored chip state on page load.
4. **Chat Textarea & Send Arrow Pixel-Perfect Alignment:**
   - Textarea and `➔` send button calibrated to identical `44px` height with matching `10px` border-radius.
   - Compact placeholder `"Directive or question..."` ensures single-line presentation without height jumping.
   - Bottom alignment (`align-items: flex-end`) ensures button remains anchored cleanly even during multi-line expansion.

---

## ⚡ [v2.8.2] — 2026-10-27 10:35 AM IST (Send Arrow Button, True Fullscreen War Room, Voice Auto-Engage & "FAAAH" Uplink SFX)

### 📌 Summary (சுருக்கம்):
Addressed all user feedback for clean UX and immersive interaction:
1. **Send Button (➔ Only, Zero Overlap):**
   - Removed legacy `▲ EXECUTE` text overwrite from `hud.js` and `hud.css`.
   - Replaced with a crisp, dedicated neon arrow button `➔` (`flex: 0 0 44px; width: 44px; height: 42px;`), neatly positioned side-by-side with zero collision.
   - Replaced stop text with a minimal `■` stop icon when generating.
2. **Textarea Inner Alignment & Padding:**
   - Corrected textarea inner padding (`10px 14px`), box-sizing, line-height (`1.45`), and font styling.
   - Refined placeholder to concise `"Type a directive or ask KIRAHT..."` to prevent clumsy multi-line wrapping in narrow viewports.
3. **True Fullscreen Mode (100% Immersive 3D Arc Reactor):**
   - Going to fullscreen now completely hides top headers, tabs, time/date pills, footers, and sidebars (`body.war-room-active`).
   - The entire screen is exclusively the 3D Arc Reactor, scaled up smoothly to `scale(1.52)`.
   - Floating sleek translucent exit button `✕` in top-right corner allows instant exit with Esc or F11.
4. **Auto-Engage Voice Mode on Fullscreen:**
   - Entering Fullscreen immediately turns on Voice Mode (`startMicListening()`), making KIRAHT listen to spoken commands like JARVIS without needing to click mic.
5. **Authentic Sci-Fi "FAAAH" Transmit Sound:**
   - Synthesized and installed high-fidelity audio `static/audio/transmit_faah.wav` (resonant bandpass swept noise whoosh + plasma body).
   - Wired Enter key and Send button to trigger `playTransmitFaahSound()` on message dispatch, with Web Audio synthesizer fallback and SFX mute (`🔊` / `🔇`) support.

---

## ⚡ [v2.8.1] — 2026-10-26 06:55 PM IST (HUD De-clutter, Minimal Clean Arc Reactor Stage & SFX Sound Control)

### 📌 Summary (சுருக்கம்):
Refined HUD design based on user feedback to eliminate clutter and restore true Jarvis minimalism:
1. **Renamed `TELEMETRY` ➔ `STATS`:** Eliminates text truncation (`TELE...`) in the left panel header and top nav toggles.
2. **Compact Send Arrow (`➔`):** Replaced bulky `▲ EXECUTE` button with minimal neon arrow, giving textarea 75% more room.
3. **Removed Tactical Shortcuts Bar:** Deleted the overlapping horizontal bar that blocked the center Arc Reactor; 3D core is now 100% visible and floating unobstructed.
4. **Cleaned Reticle Corner Tags:** Removed `[SYS.MK-VII]`, `[FLUX: 100%]`, `[AZIMUTH: 045]` tags colliding with boundaries.
5. **Removed Center Stage Header:** Deleted `SYS.MK-VII • TACTICAL AI CORE` bar, transforming Center Stage into pure, infinite deep-space holographic canvas.
6. **SFX Audio Control (`🔊` / `🔇`):** Added simple emoji sound mute toggle in the chat input toolbar to silence synthesizer tones ("faah" sound).
7. **Enhanced Fullscreen Mode:** Wired both top bar `⛶ FULLSCREEN` button and stage fab with `F11` / `Escape` support.

---

## ⚡ [v2.8.0] — 2026-10-26 04:35 PM IST (Jarvis AI Spark 3-Zone Layout & 3D Arc Reactor Center Stage)

### 📌 Summary (சுருக்கம்):
Major HUD architectural overhaul inspired by [@jarvis_ai_spark](https://www.instagram.com/jarvis_ai_spark) and Stark Industries aesthetics:
1. **Center Stage:** Unobstructed 3D Arc Reactor (100% visible, centered, solar amber + electric cyan palette, interactive click-to-voice, tech reticle brackets).
2. **Left Panel:** Hardware telemetry dials (CPU, RAM, Battery, Storage, Network, Prayer schedule) in deep obsidian dark theme.
3. **Right Panel:** Transformed into dedicated Chat Directives terminal with docked bottom input and top tab switcher for `[ 💬 CHAT DIRECTIVES ]` and `[ ⚡ TOOLS / LOGS ]`.
4. **Maximized Viewport:** Removed the bottom footer telemetry bar, moving the event stream into the right panel tabs, allowing the center stage to span the full 100% height.
5. **War Room Fullscreen Mode:** Toggle button (`#btn-war-room-fullscreen` / F11) collapses sidebars and expands the 3D Arc Reactor to full screen with responsive audio waves.

---

## ⚡ [v2.7.2] — 2026-10-22 03:08 PM IST (Welcome Hero Startup Glitch & Animation Loop Fix)

### 📌 Summary (சுருக்கம்):
Resolved the startup animation glitch where the Tactical Welcome Hero card (`#tactical-welcome-hero`) would flash, jump, or replay its entry animation right after completing its initial sequenced boot. Decoupled initial boot from dynamic re-renders, added GPU compositor layer optimization, added `.boot-complete` stabilization, and added critical head styles to prevent FOUC.

---

### 🚀 Bug Fixes & Enhancements (பிழை திருத்தங்கள் & மேம்பாடுகள்):
1. **Eliminated Startup Double-Animation Glitch:**
   - Previously, `.tactical-welcome-hero` had a default `animation: welcome-boot-in 0.75s`. When the `.delayed-boot` class was removed at 2.75s, the browser treated `.tactical-welcome-hero` as a fresh rule and restarted `welcome-boot-in` from 0% opacity, causing the card to glitch/re-animate right after settling.
   - Removed the default animation from `.tactical-welcome-hero` base style; isolated instant re-renders to `.tactical-welcome-hero.instant-boot`.
   - Added `.tactical-welcome-hero.boot-complete` with `animation: none !important; opacity: 1 !important; transform: none !important;` to lock the card seamlessly once booted.
2. **GPU Rendering & Compositing Optimization:**
   - Removed conflicting `filter: blur(...)` inside keyframes on an element that already uses `backdrop-filter: blur(16px)` (which was causing GPU layer repaint stutters).
   - Added `will-change: opacity, transform` and `animation-fill-mode: both` to prevent frame hitching.
3. **Critical Pre-render Styling & Cache-Busting:**
   - Added inline `<style>` in `<head>` of [index.html](file:///d:/KIRAHT%20AI/static/index.html) to eliminate any possible flash of unstyled content before stylesheets parse.
   - Bumped stylesheet and HUD script asset versions to `v=5.2`.

---

## ⚡ [v2.7.1] — 2026-10-19 08:45 PM IST (Sequenced Startup Boot: 3D Arc Reactor Showcase First, Followed by Welcome Hero Card)

### 📌 Summary (சுருக்கம்):
Sequenced the startup HUD boot animations so the 3D Holographic Arc Reactor (`#reactor-core`) takes full, unobstructed center stage upon opening. The Arc Reactor executes its complete 1080° spin-up, cyan flux flares, and gyro stabilization over ~1.85s. Only after the Arc Reactor completes this startup sequence does the Tactical Welcome Hero card (`#tactical-welcome-hero`) smoothly glide and fade into view.

---

### 🚀 Enhancements (மேம்பாடுகள்):
1. **Unobstructed 3D Arc Reactor Startup Showcase:**
   - On page load, the 3D Arc Reactor starts at `scale(0.06) rotate(-1080deg)`, surges up to `scale(1.15)` at high cyan luminescence (opacity 1.0, drop-shadow 55px), stabilizes at azimuth 0°, and gently eases into standard ambient HUD brightness at 1.85s.
2. **Sequenced Tactical Welcome Hero Entry:**
   - Added `.delayed-boot` class on `#tactical-welcome-hero` on initial load (`opacity: 0; visibility: hidden; pointer-events: none`).
   - At `1.85s`, triggers `@keyframes welcome-delayed-boot-in` over 0.85s, sliding up smoothly from translateY(26px) with dynamic cyan boundary lighting and restoring `pointer-events: auto`.
   - JavaScript safely cleans up the `.delayed-boot` class after sequence completion (2.75s) and cleanly overrides on instant dismissals.
3. **Cache-Busting Update:**
   - Bumped stylesheet and HUD script asset versions to `v=5.1` to ensure instant client synchronization.

---

## ⚡ [v2.7.0] — 2026-10-17 12:30 AM IST (5 Prayer Times & Reminders System, Logo QR Code, Smart Scroll Pin & Guaranteed Response Fix)

### 📌 Summary (சுருக்கம்):
Added a comprehensive 5 Islamic Prayer Times (Fajr, Dhuhr, Asr, Maghrib, Isha) and custom events reminder suite with editable schedules and interactive chat action cards (Accept / Snooze 10m). Resolved silent response drops with full error & diagnostic cards, embedded the Kiraht AI logo in generated QR codes with high error correction, and implemented smart scroll pinning (immediate bottom snap on user send, zero downward dragging when user scrolls up during AI streaming).

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Guaranteed Assistant Responses & Diagnostics Visibility:**
   - Fixed issue where errors or stream terminations without cards silently disappeared.
   - Core pipeline and WebSocket handlers now guarantee an informative fallback notice or diagnostic error card in chat rather than leaving the user's message hanging with no reply.
2. **Branded QR Code Center Logo:**
   - Upgraded `generate_qr_code()` to use `ERROR_CORRECT_H` (30% error correction) and embedded the circular Kiraht AI branded logo with cyan glowing perimeter badge at the exact center.
3. **Smart Scroll Pin Logic:**
   - When user is scrolled far up and sends a message (Enter or Execute), the chat immediately resets scroll lock and scrolls down to the bottom.
   - When AI is streaming a response and the user scrolls up to read earlier messages, the viewport respects the user's scroll position and never drags them down.
4. **5 Daily Prayer Times & Custom Reminders Manager:**
   - Tactical dual tabs inside the clock/calendar popup (`[ 📅 CALENDAR ]` & `[ 🕌 PRAYER & REMINDERS ]`).
   - Integrated schedule for 5 daily prayers (Fajr, Dhuhr, Asr, Maghrib, Isha) with editable times and toggle switches.
   - Custom reminders and events manager allowing additions, deletions, and persistence in `reminders.json`.
   - Real-time periodic checks (~7.5s) dispatching tactical reminder cards directly into chat with interactive `[ ✅ ACCEPT ]` and `[ ⏰ SNOOZE 10M ]` buttons, desktop notifications, and voice announcements.

---

## ⚡ [v2.6.1] — 2026-10-16 01:25 AM IST (Auto-Dismiss Welcome Hero on Chat, Adaptive Stream Draining & Diagnostics Fix)

### 📌 Summary (சுருக்கம்):
Implemented ChatGPT-style auto-dismissal of the Tactical Welcome Hero upon sending the first message or loading history, added flex-shrink protection, enhanced token streaming with adaptive queue draining and a 1.2s safety timer to prevent frozen streaming states, and routed System Diagnostics quick chip to the internal `/api/quick-action` API.

---

### 🚀 Enhancements & Bug Fixes (மேம்பாடுகள் & பிழைத்திருத்தங்கள்):
1. **Auto-Dismiss Welcome Hero (Option 1):**
   - Added smooth fade-out and DOM unmounting (`dismissWelcomeHero()`) as soon as the user transmits a message, loads history (+50), or triggers a directive.
   - Preserves full Welcome Hero at startup and restores it dynamically whenever the user clears the chat (`handleChatCleared()`).
   - Added `flex-shrink: 0;` to prevent flexbox from vertically squeezing or distorting the welcome card while visible.
2. **Streaming Freeze Safeguard & Adaptive Draining:**
   - Improved `startWordStreamWorker()` with adaptive draining that automatically scales up token drain speed during backlogs and stream completion.
   - Added a hard 1.2s timeout fallback in `handleStreamEnd()` ensuring the typing cursor and red STOP button always reset cleanly.
3. **System Diagnostics Quick Action Routing:**
   - Directly wired `⚡ System Diagnostics` chip to call `/api/quick-action` (`system_status`), preventing terminal command parsing errors (`'full' is not recognized`).

---

## ⚡ [v2.6.0] — 2026-10-15 11:30 PM IST (Sidebar Section Inversion, History User Avatar & Tactical Welcome Hero)

### 📌 Summary (சுருக்கம்):
Shifted KIRAHT CORE section above NETWORK in the Telemetry sidebar, fixed user profile avatar rendering for loaded history messages (+50 history), ensured `-50` collapse button is hidden on startup and only appears when history is actually loaded, and introduced a futuristic Tactical Holographic Welcome Hero with dynamic time-of-day greeting, system readiness grid, interactive prompt chips, and voice greeting briefing.

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Telemetry Sidebar Layout Inversion (KIRAHT CORE Above NETWORK):**
   - Moved `KIRAHT CORE` telemetry divider and metrics (`Model`, `AI`, `Memory`, `Tools`, `Search`) to section 2 above `NETWORK`.
   - Moved `NETWORK` divider and metrics (`Download`, `Upload`, `Ping`, `Connection`) to section 3 below `KIRAHT CORE`.
2. **User Profile Picture for Loaded History Messages:**
   - Standardized avatar creation through `createUserAvatarElement()` and `createAssistantAvatarElement()`.
   - Fixed `loadNextHistoryBatch()` which previously hardcoded `👤` fallback instead of loading `/static/img/user_avatar.jpg`. Loaded history messages now consistently show the user's actual profile picture.
3. **`-50` Collapse Button Lifecycle Safeguard:**
   - Fixed startup display bug where `-50` button appeared immediately on load because `cachedChatHistory.length > 0`.
   - Button visibility now strictly tracks active rendered history batches (`historyOffset > 0`), ensuring `-50` is completely hidden at startup and only shows when the user expands history (+50).
4. **Interactive Tactical Welcome Hero & Dynamic Boot Greeting:**
   - Replaced static plain-text initial greeting with a futuristic Holographic Welcome Hero card featuring glassmorphism, corner reticles, glowing scanline pulse, and KIRAHT seal.
   - Dynamic time-of-day greeting: *Good Morning, Sir.*, *Good Afternoon, Sir.*, *Good Evening, Sir.*, and *Late-Night Tactical Session, Sir.*
   - Integrated System Readiness grid displaying live core, active neural engine, defense state, and voice protocol status.
   - Interactive Quick Directives: `⚡ System Diagnostics`, `🌐 Web Intelligence`, `💻 Code Assistant`, `🎙️ Start Voice Mode`, `📜 Load Chat History`, and `🔊 Voice Greeting` audio briefing.
   - Restored and re-hydrated dynamically during screen clear (`handleChatCleared()`).

---

## ⚡ [v2.5.3] — 2026-10-15 12:50 PM IST (Complete Actions Panel Removal & Full-Width Chat Viewport)

### 📌 Summary (சுருக்கம்):
Completely removed the Quick Actions panel (`#actions-panel`), right drag-resizer (`#resizer-right`), top navbar Actions toggle (`#toggle-actions-btn`), and `Alt+Q` keyboard shortcut. The primary central chat interface now expands cleanly to the full right edge of the screen, providing maximum space and readability.

---

### 🚀 New Features & Enhancements (புதிய வசதிகள் & மேம்பாடுகள்):
1. **Full Actions Panel & Resizer Removal:**
   - Removed `#actions-panel` and all launcher tiles (Chrome, Brave, VS Code, WhatsApp, etc.) from `index.html`.
   - Removed right drag-resizer splitter (`#resizer-right`).
   - Removed `● ACTIONS` quick toggle button from top navbar.
   - Removed `Alt+Q` entry from Tactical Keyboard Shortcuts modal cheat-sheet.
2. **Spacious Full-Width Chat Viewport:**
   - The central chat hero (`.center-panel`) now expands naturally to take 100% of available space right of the telemetry sidebar (`flex: 1 1 0%`).
   - Eliminated all right-side resizer/panel drag event listeners and storage overhead in `hud.js`.

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

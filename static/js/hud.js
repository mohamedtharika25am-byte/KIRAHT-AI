/**
 * KIRAHT AI — Futuristic Web HUD Frontend Engine
 * Connects to FastAPI backend via WebSocket (ws://127.0.0.1:8000/ws).
 * Features:
 *  - 3D Rotating Arc Reactor Core with active computing pulse & gyro spin
 *  - Word-by-word streaming typing queue with glowing tactical cursor
 *  - Real-time SVG circular telemetry dials (CPU, RAM, Battery, Disk)
 *  - Large tactile quick action tiles (Chrome, VS Code, Screenshot, Workspace, YouTube)
 *  - Interactive high-contrast QR Code & Screenshot card renderers
 */

(function () {
  'use strict';

  // State Variables
  let ws = null;
  let isConnected = false;
  let reconnectTimeout = null;

  // Streaming State & Word Queue
  let currentStreamingCard = null;
  let currentStreamingContentEl = null;
  let accumulatedStreamText = '';
  let wordStreamQueue = [];
  let wordStreamInterval = null;
  let isStreamingActive = false;
  let pendingStreamEnd = null;
  let thinkingCard = null;
  let isGenerating = false;
  let lastOptimisticUserMessage = null;

  // DOM Elements - Core & Navigation
  const chatViewport = document.getElementById('chat-viewport');
  const chatInput = document.getElementById('chat-input');
  const btnSend = document.getElementById('btn-send');
  const btnClearChat = document.getElementById('btn-clear-chat');
  const statusState = document.getElementById('status-state');
  const statusDetail = document.getElementById('status-detail');
  const networkDot = document.getElementById('network-dot');
  const networkStatusText = document.getElementById('network-status-text');
  const activityLogStream = document.getElementById('activity-log-stream');
  const hudClock = document.getElementById('hud-clock');
  const hudUptime = document.getElementById('hud-uptime');
  const headerEngineText = document.getElementById('header-engine-text');
  const reactorCore = document.getElementById('reactor-core');
  const reactorEpicenter = document.getElementById('reactor-epicenter');
  const epicenterPlasmaCore = document.getElementById('epicenter-plasma-core');
  const coreStatusText = document.getElementById('core-status-text');
  const btnShortcutsModal = document.getElementById('btn-shortcuts-modal');
  const shortcutsModal = document.getElementById('shortcuts-modal');
  const btnCloseShortcuts = document.getElementById('btn-close-shortcuts');

  // DOM Elements - Telemetry Gauges
  const cpuPercent = document.getElementById('cpu-percent');
  const cpuCircle = document.getElementById('cpu-circle');
  const cpuSubtext = document.getElementById('cpu-subtext');

  const ramPercent = document.getElementById('ram-percent');
  const ramCircle = document.getElementById('ram-circle');
  const ramSubtext = document.getElementById('ram-subtext');

  const batteryPercent = document.getElementById('battery-percent');
  const batCircle = document.getElementById('bat-circle');
  const batterySubtext = document.getElementById('battery-subtext');

  const diskPercent = document.getElementById('disk-percent');
  const diskCircle = document.getElementById('disk-circle');
  const diskSubtext = document.getElementById('disk-subtext');

  const netDownload = document.getElementById('net-download');
  const netUpload = document.getElementById('net-upload');
  const netPing = document.getElementById('net-ping');
  const netConnection = document.getElementById('net-connection');

  const coreAiStatus = document.getElementById('core-ai-status');
  const coreMemStatus = document.getElementById('core-mem-status');
  const coreToolsStatus = document.getElementById('core-tools-status');
  const coreSearchStatus = document.getElementById('core-search-status');
  const coreModelName = document.getElementById('core-model-name');

  const netSsid = document.getElementById('net-ssid');
  const osName = document.getElementById('os-name');
  const securityModeText = document.getElementById('security-mode-text');

  let lastTelemetryTime = Date.now();
  let telemetryTickCount = 0;
  let highCpuAlertFired = false;

  const CIRCLE_CIRCUMFERENCE = 251.2; // 2 * PI * 40

  // =========================================================================
  // 1. WEBSOCKET CONNECTION MANAGER
  // =========================================================================
  function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    updateStatus('CONNECTING', 'Synchronizing with KIRAHT Core...');
    logActivity('System', 'Connecting', `WebSocket to ${wsUrl}`);

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = function () {
        isConnected = true;
        if (networkDot) networkDot.className = 'status-dot green-pulse';
        if (networkStatusText) {
          networkStatusText.textContent = 'CONNECTING...';
          networkStatusText.style.color = 'var(--text-muted)';
        }
        updateStatus('READY', 'Connected to KIRAHT AI Brain');
        logActivity('System', 'Connected', 'Tactical HUD operational @ 127.0.0.1:8000');
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
      };

      ws.onmessage = function (event) {
        try {
          const packet = jsonParseSafe(event.data);
          if (!packet) return;
          handleServerPacket(packet);
        } catch (err) {
          console.error('[HUD] Packet parse error:', err);
        }
      };

      ws.onclose = function () {
        isConnected = false;
        if (networkDot) {
          networkDot.className = 'status-dot';
          networkDot.style.background = '#ff3366';
          networkDot.style.boxShadow = '0 0 10px #ff3366';
        }
        if (networkStatusText) {
          networkStatusText.textContent = 'DISCONNECTED';
          networkStatusText.style.color = '#ff3366';
        }
        updateStatus('OFFLINE', 'Connection lost — retrying in 3s...');
        logActivity('System', 'Disconnected', 'Lost link to 127.0.0.1:8000');
        if (typeof setGeneratingState === 'function') setGeneratingState(false);
        scheduleReconnect();
      };

      ws.onerror = function (err) {
        console.warn('[HUD] WebSocket error:', err);
      };
    } catch (e) {
      scheduleReconnect();
    }
  }

  function scheduleReconnect() {
    if (!reconnectTimeout) {
      reconnectTimeout = setTimeout(function () {
        reconnectTimeout = null;
        initWebSocket();
      }, 3000);
    }
  }

  function sendWebSocket(payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  }

  // =========================================================================
  // 2. SERVER PACKET DISPATCHER
  // =========================================================================
  function handleServerPacket(packet) {
    switch (packet.type) {
      case 'status':
        updateStatus(packet.state, packet.detail);
        break;

      case 'telemetry':
        updateTelemetry(packet.data);
        break;

      case 'chat_history':
        cachedChatHistory = packet.messages || [];
        updateHistoryButtonBadge(cachedChatHistory.length);
        if (typeof syncTranscriptWithHistory === 'function') {
          syncTranscriptWithHistory();
        }
        break;

      case 'chat_message':
        if (packet.role === 'user' && lastOptimisticUserMessage && packet.content === lastOptimisticUserMessage) {
          lastOptimisticUserMessage = null;
          return;
        }
        renderSingleMessage(packet.role, packet.content, packet.timestamp, packet.meta);
        if (packet.role === 'user') {
          showThinkingIndicator();
          setGeneratingState(true);
        }
        break;

      case 'activity':
        logActivity(packet.actor, packet.action, packet.detail);
        break;

      case 'stream_chunk':
        handleStreamChunk(packet.chunk);
        break;

      case 'stream_end':
        handleStreamEnd(packet.full_text, packet.meta);
        break;

      case 'chat_cleared':
        handleChatCleared();
        break;

      case 'error':
        if (thinkingCard) {
          if (thinkingCard.parentNode) {
            thinkingCard.parentNode.removeChild(thinkingCard);
          }
          thinkingCard = null;
          currentStreamingCard = null;
          currentStreamingContentEl = null;
        }
        setGeneratingState(false);
        logActivity('System', 'Error', packet.error);
        break;
    }
  }

  // =========================================================================
  // 3. CIRCULAR TELEMETRY GAUGES
  // =========================================================================
  function setCircleProgress(circleEl, percent) {
    if (!circleEl) return;
    const clamped = Math.max(0, Math.min(100, percent));
    const offset = CIRCLE_CIRCUMFERENCE - (clamped / 100) * CIRCLE_CIRCUMFERENCE;
    circleEl.style.strokeDashoffset = offset;
  }

  function updateTelemetry(data) {
    if (!data) return;
    lastTelemetryTime = Date.now();
    telemetryTickCount++;

    // CPU
    if (data.cpu) {
      if (cpuPercent) cpuPercent.textContent = `${data.cpu.percent}%`;
      setCircleProgress(cpuCircle, data.cpu.percent);
      if (cpuSubtext) cpuSubtext.textContent = `${data.cpu.cores} Cores`;
    }

    // RAM
    if (data.ram) {
      if (ramPercent) ramPercent.textContent = `${data.ram.percent}%`;
      setCircleProgress(ramCircle, data.ram.percent);
      if (ramSubtext) ramSubtext.textContent = `${data.ram.used_gb}G/${data.ram.total_gb}G`;
    }

    // Battery
    if (data.battery) {
      if (batteryPercent) batteryPercent.textContent = `${data.battery.percent}%`;
      setCircleProgress(batCircle, data.battery.percent);
      if (batterySubtext) {
        batterySubtext.textContent = data.battery.charging ? 'Charging' : (data.battery.percent > 95 ? 'Full' : 'Battery');
      }
    }

    // Disk C:
    if (data.disks && data.disks.length > 0) {
      const cDisk = data.disks[0];
      if (diskPercent) diskPercent.textContent = `${cDisk.percent}%`;
      setCircleProgress(diskCircle, cDisk.percent);
      if (diskSubtext) diskSubtext.textContent = `${cDisk.free_gb} GB Free`;
    }

    // Network & Host
    if (data.network) {
      const isNetOnline = Boolean(data.network.online);
      if (networkStatusText) {
        networkStatusText.textContent = isNetOnline ? 'ONLINE' : 'OFFLINE';
        networkStatusText.style.color = isNetOnline ? 'var(--accent-cyan)' : '#ffaa00';
      }
      if (networkDot) {
        if (isNetOnline) {
          networkDot.className = 'status-dot green-pulse';
          networkDot.style.background = '#00f3ff';
          networkDot.style.boxShadow = '0 0 10px #00f3ff';
        } else {
          networkDot.className = 'status-dot';
          networkDot.style.background = '#ffaa00';
          networkDot.style.boxShadow = '0 0 10px #ffaa00';
        }
      }
      if (netSsid) netSsid.textContent = data.network.ssid || (isNetOnline ? 'Wi-Fi' : 'Offline');
      if (netDownload) netDownload.textContent = data.network.download || '0.0 KB/s';
      if (netUpload) netUpload.textContent = data.network.upload || '0.0 KB/s';
      if (netPing) netPing.textContent = data.network.ping || (isNetOnline ? '24 ms' : 'Offline');
      if (netConnection) netConnection.textContent = data.network.connection || (isNetOnline ? 'Wi-Fi' : 'No Internet');
    }
    if (data.os && osName) {
      osName.textContent = data.os.name ? data.os.name.split(' (')[0] : 'Windows 11';
    }

    // KIRAHT CORE Section
    if (data.core) {
      if (coreAiStatus) {
        const isAiOnline = data.core.ai === 'ONLINE';
        coreAiStatus.innerHTML = `<span class="telem-dot-mini ${isAiOnline ? 'green-pulse' : ''}" style="${isAiOnline ? '' : 'background:#ff3366;'}"></span> ${data.core.ai}`;
        coreAiStatus.className = `stat-value ${isAiOnline ? 'text-green' : 'text-red'}`;
      }
      if (coreMemStatus) {
        coreMemStatus.innerHTML = `<span class="telem-dot-mini green-pulse"></span> ${data.core.memory || 'ACTIVE'}`;
      }
      if (coreToolsStatus) {
        coreToolsStatus.innerHTML = `<span class="telem-dot-mini green-pulse"></span> ${data.core.tools || 'READY'}`;
      }
      if (coreSearchStatus) {
        coreSearchStatus.innerHTML = `<span class="telem-dot-mini green-pulse"></span> ${data.core.search || 'READY'}`;
      }
      if (coreModelName) {
        coreModelName.textContent = data.core.model || 'qwen2.5:3b';
      }
    } else if (data.ai && coreModelName) {
      coreModelName.textContent = data.ai.model || 'qwen2.5:3b';
    }

    // AI Engine Header
    if (data.ai && headerEngineText) {
      const enginePart = data.ai.engine ? data.ai.engine.split(' ')[0].toUpperCase() : 'GEMINI';
      headerEngineText.textContent = `AI: ${enginePart}`;
    }

    // Security Mode Pill
    if (securityModeText) {
      const sMode = data.security || 'WRITE MODE';
      securityModeText.textContent = sMode;
      securityModeText.style.color = sMode.includes('WRITE') ? 'var(--accent-green)' : 'var(--accent-cyan)';
    }

    // Uptime
    if (data.uptime && hudUptime) {
      hudUptime.textContent = `UPTIME: ${data.uptime.session || '0m 0s'}`;
    }

    // Stream active telemetry heartbeat periodically without spamming raw dashes
    if (telemetryTickCount % 20 === 0 && data.cpu && typeof data.cpu.percent === 'number' && data.ram) {
      const cpuVal = `${data.cpu.percent}%`;
      const ramVal = `${data.ram.percent}%`;
      const pingVal = data.network ? (data.network.ping || '24ms') : '24ms';
      const dlVal = data.network ? (data.network.download || '0.0 KB/s') : '0.0 KB/s';
      const ulVal = data.network ? (data.network.upload || '0.0 KB/s') : '0.0 KB/s';
      logActivity('Telemetry', 'Heartbeat', `CPU ${cpuVal} • RAM ${ramVal} • Ping ${pingVal} • [↓${dlVal} ↑${ulVal}]`);
    }

    // High compute spike detection
    if (data.cpu && data.cpu.percent > 70 && !highCpuAlertFired) {
      logActivity('System', 'Compute Spike', `CPU load elevated to ${data.cpu.percent}%`);
      highCpuAlertFired = true;
      setTimeout(function () { highCpuAlertFired = false; }, 10000);
    }
  }

  // Active Telemetry Stream Watchdog & Polling Fallback
  setInterval(async function () {
    if (Date.now() - lastTelemetryTime > 2500) {
      try {
        const resp = await fetch('/api/telemetry');
        if (resp.ok) {
          const telemData = await resp.json();
          updateTelemetry(telemData);
        }
      } catch (e) {
        // network or server busy
      }
    }
  }, 2000);

  // =========================================================================
  // 4. CHAT HISTORY & MESSAGING (ON-DEMAND ARCHIVE & FRESH BOOT)
  // =========================================================================
  let cachedChatHistory = [];
  let isHistoryRendered = false;

  function updateHistoryButtonBadge(count) {
    const navCountEl = document.getElementById('nav-history-count');
    const tileDescEl = document.getElementById('tile-history-desc');
    if (navCountEl) {
      if (count > 0) {
        navCountEl.textContent = count;
        navCountEl.style.display = 'inline-block';
      } else {
        navCountEl.style.display = 'none';
      }
    }
    if (tileDescEl) {
      tileDescEl.textContent = count > 0 ? `${count} past logs saved` : 'View past conversations';
    }
  }

  function displayLoadedHistory() {
    if (isHistoryRendered) {
      logActivity('History', 'Notice', 'Previous history is already displayed');
      scrollToBottom();
      return;
    }

    if (!cachedChatHistory || cachedChatHistory.length === 0) {
      // If cache is empty, fetch fresh from backend
      fetch('/chat_history.json?v=' + Date.now())
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (Array.isArray(data) && data.length > 0) {
            cachedChatHistory = data;
            updateHistoryButtonBadge(cachedChatHistory.length);
            renderLoadedHistory();
          } else {
            logActivity('History', 'Empty', 'No archived conversations found');
            alert('No previous conversation history found, Sir.');
          }
        })
        .catch(function () {
          logActivity('History', 'Empty', 'Archive file unavailable');
          alert('No previous history recorded yet, Sir.');
        });
      return;
    }

    renderLoadedHistory();
  }

  function renderLoadedHistory() {
    if (isHistoryRendered || !chatViewport) return;

    if (!cachedChatHistory || cachedChatHistory.length === 0) {
      logActivity('History', 'Empty', 'No previous archived chats found');
      return;
    }

    // Preserve any current active session cards if user has already exchanged messages
    const existingCards = Array.from(chatViewport.children);
    chatViewport.innerHTML = '';

    // Archive header
    const archiveHeader = document.createElement('div');
    archiveHeader.className = 'history-divider';
    archiveHeader.innerHTML = `<span>📜 PREVIOUS ARCHIVED LOGS (${cachedChatHistory.length} MESSAGES) 📜</span>`;
    chatViewport.appendChild(archiveHeader);

    // Append cached history cards
    cachedChatHistory.forEach(function (msg) {
      appendMessageCard(msg.role, msg.content, msg.timestamp || 'Archived', msg.meta);
    });

    // If user already had messages or welcome message in active session, preserve them below active session divider
    if (existingCards.length > 0) {
      const activeDivider = document.createElement('div');
      activeDivider.className = 'history-divider';
      activeDivider.innerHTML = `<span>⚡ CURRENT ACTIVE SESSION ⚡</span>`;
      chatViewport.appendChild(activeDivider);

      existingCards.forEach(function (card) {
        chatViewport.appendChild(card);
      });
    }

    isHistoryRendered = true;

    // Update buttons
    const navText = document.getElementById('nav-history-text');
    const btnNav = document.getElementById('btn-load-history');
    const tileTitle = document.getElementById('tile-history-title');
    const tileDesc = document.getElementById('tile-history-desc');
    if (navText) navText.textContent = 'HISTORY LOADED';
    if (btnNav) btnNav.classList.add('active');
    if (tileTitle) tileTitle.textContent = 'HISTORY LOADED';
    if (tileDesc) tileDesc.textContent = `${cachedChatHistory.length} logs displayed`;

    logActivity('System', 'History Loaded', `${cachedChatHistory.length} archived messages rendered`);
    scrollToBottom();
  }

  function renderSingleMessage(role, content, timestamp, meta) {
    if (role === 'assistant' && thinkingCard) {
      if (thinkingCard.parentNode) {
        thinkingCard.parentNode.removeChild(thinkingCard);
      }
      thinkingCard = null;
      currentStreamingCard = null;
      currentStreamingContentEl = null;
    }
    appendMessageCard(role, content, timestamp, meta);
    scrollToBottom();
  }

  function createEngineSourceBadge(meta) {
    const badge = document.createElement('span');
    badge.className = 'engine-source-badge';

    let icon = '⚡';
    let text = 'GEMINI CLOUD';
    let variant = 'gemini';

    if (!meta) {
      badge.classList.add('badge-gemini');
      badge.innerHTML = `<span class="badge-icon">⚡</span> <span class="badge-text">GEMINI CLOUD</span>`;
      return badge;
    }

    const sourceLabel = meta.source_label || '';
    const engine = (meta.engine || '').toLowerCase();
    const tool = (meta.tool || '').toLowerCase();

    if (tool === 'screenshot' || sourceLabel.includes('SCREENSHOT')) {
      variant = 'screenshot';
      icon = '📸';
      text = 'SCREENSHOT TOOL';
    } else if (sourceLabel.startsWith('APP:')) {
      variant = 'app';
      icon = '📱';
      text = sourceLabel;
    } else if (engine === 'tool' || tool || sourceLabel.startsWith('TOOL:')) {
      variant = 'tool';
      icon = '🛠️';
      text = sourceLabel || `TOOL: ${(tool || 'SYSTEM').toUpperCase()}`;
    } else if (engine === 'ollama' || sourceLabel.includes('OLLAMA')) {
      variant = 'ollama';
      icon = '🦙';
      text = meta.model ? `OLLAMA (${meta.model})` : (sourceLabel || 'OLLAMA LOCAL');
    } else if (engine === 'gemini' || sourceLabel.includes('GEMINI')) {
      variant = 'gemini';
      icon = '⚡';
      text = meta.model ? `GEMINI (${meta.model})` : (sourceLabel || 'GEMINI CLOUD');
    } else if (sourceLabel) {
      variant = 'gemini';
      icon = '⚡';
      text = sourceLabel;
    }

    badge.classList.add(`badge-${variant}`);
    badge.innerHTML = `<span class="badge-icon">${icon}</span> <span class="badge-text">${text}</span>`;
    return badge;
  }

  function appendMessageCard(role, content, timestamp, meta) {
    const isUser = role === 'user';
    const card = document.createElement('div');
    card.className = `message-card ${isUser ? 'user-card' : 'assistant-card'}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    if (isUser) {
      const userImg = document.createElement('img');
      userImg.src = '/static/img/user_avatar.jpg';
      userImg.className = 'message-avatar-img user-avatar-img';
      userImg.alt = 'User';
      userImg.onerror = function () {
        this.style.display = 'none';
        avatar.innerHTML = '<span class="avatar-fallback-user">👤</span>';
      };
      avatar.appendChild(userImg);
    } else {
      const avatarImg = document.createElement('img');
      avatarImg.src = '/static/img/kiraht_ai_logo.png?v=4.0';
      avatarImg.className = 'message-avatar-img assistant-avatar-img';
      avatarImg.alt = 'K';
      avatar.appendChild(avatarImg);
    }

    const body = document.createElement('div');
    body.className = 'message-body';

    const header = document.createElement('div');
    header.className = 'message-header';

    const headerLeft = document.createElement('div');
    headerLeft.className = 'message-header-left';

    const sender = document.createElement('span');
    sender.className = 'sender-name';
    sender.textContent = isUser ? 'You' : 'KIRAHT AI';
    headerLeft.appendChild(sender);

    if (!isUser) {
      const badge = createEngineSourceBadge(meta);
      headerLeft.appendChild(badge);
    }

    const time = document.createElement('span');
    time.className = 'message-timestamp';
    time.textContent = timestamp || getCurrentTime();

    header.appendChild(headerLeft);
    header.appendChild(time);

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.innerHTML = formatMarkdown(content);

    // Check for screenshot meta preview
    if (meta && meta.screenshot_url) {
      const img = document.createElement('img');
      img.src = meta.screenshot_url;
      img.className = 'chat-preview-img';
      img.alt = 'Screenshot Preview';
      img.onclick = function () { window.open(meta.screenshot_url, '_blank'); };
      contentEl.appendChild(img);
    }

    body.appendChild(header);
    body.appendChild(contentEl);

    card.appendChild(avatar);
    card.appendChild(body);

    chatViewport.appendChild(card);

    // Synchronize to Voice Transcript Sidebar
    if (typeof appendTranscriptEntry === 'function' && content) {
      appendTranscriptEntry(role, content, timestamp, meta);
    }
    if (!isUser && typeof updateVoiceResponseCard === 'function' && content) {
      updateVoiceResponseCard(content);
    }

    if (!isUser && ((typeof isVoiceModeEnabled !== 'undefined' && isVoiceModeEnabled) || isVoiceTriggered) && content) {
      speakAloud(content);
      isVoiceTriggered = false;
    }
    return contentEl;
  }

  // =========================================================================
  // 5. WORD-BY-WORD STREAMING & GEMINI-STYLE THINKING INDICATOR
  // =========================================================================
  function showThinkingIndicator() {
    if (thinkingCard || currentStreamingCard) return;

    const card = document.createElement('div');
    card.className = 'message-card assistant-card thinking-card';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = '/static/img/kiraht_ai_logo.png?v=4.0';
    avatarImg.className = 'message-avatar-img assistant-avatar-img';
    avatarImg.alt = 'K';
    avatar.appendChild(avatarImg);

    const body = document.createElement('div');
    body.className = 'message-body';

    const header = document.createElement('div');
    header.className = 'message-header';

    const headerLeft = document.createElement('div');
    headerLeft.className = 'message-header-left';

    const sender = document.createElement('span');
    sender.className = 'sender-name';
    sender.textContent = 'KIRAHT AI';
    headerLeft.appendChild(sender);

    const thinkingBadge = document.createElement('span');
    thinkingBadge.className = 'engine-source-badge badge-thinking';
    thinkingBadge.innerHTML = `<span class="badge-icon">⏳</span> <span class="badge-text">ROUTING...</span>`;
    headerLeft.appendChild(thinkingBadge);

    const time = document.createElement('span');
    time.className = 'message-timestamp';
    time.textContent = getCurrentTime();

    header.appendChild(headerLeft);
    header.appendChild(time);

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content thinking-content';
    contentEl.innerHTML = `
      <div class="thinking-bubble">
        <span class="thinking-dot dot-cyan"></span>
        <span class="thinking-dot dot-purple"></span>
        <span class="thinking-dot dot-blue"></span>
        <span class="thinking-text">Thinking...</span>
      </div>
    `;

    body.appendChild(header);
    body.appendChild(contentEl);

    card.appendChild(avatar);
    card.appendChild(body);

    chatViewport.appendChild(card);
    scrollToBottom();

    thinkingCard = card;
    currentStreamingCard = card;
    currentStreamingContentEl = contentEl;
    logActivity('KIRAHT', 'Processing', 'Analyzing prompt & context...');
  }

  function startWordStreamWorker() {
    if (wordStreamInterval) return;

    wordStreamInterval = setInterval(function () {
      if (wordStreamQueue.length > 0) {
        // Pop next token or word
        const token = wordStreamQueue.shift();
        accumulatedStreamText += token;
        if (currentStreamingContentEl) {
          currentStreamingContentEl.innerHTML = formatMarkdown(accumulatedStreamText) + '<span class="typing-cursor"></span>';
          scrollToBottom();
        }
      } else if (!isStreamingActive && pendingStreamEnd) {
        // Queue is finished draining and stream has finished
        clearInterval(wordStreamInterval);
        wordStreamInterval = null;
        finishStream(pendingStreamEnd.fullText, pendingStreamEnd.meta);
        pendingStreamEnd = null;
      }
    }, 20); // 20ms cadence gives a fluid, natural word-by-word typing experience
  }

  function handleStreamChunk(chunk) {
    if (!chunk) return;

    // Seamlessly transition from Gemini-style thinking dots to real streamed tokens
    if (thinkingCard) {
      if (currentStreamingContentEl) {
        currentStreamingContentEl.innerHTML = '';
        currentStreamingContentEl.classList.remove('thinking-content');
      }
      thinkingCard.classList.remove('thinking-card');
      thinkingCard = null;
      accumulatedStreamText = '';
      wordStreamQueue = [];
      isStreamingActive = true;
    }

    if (!currentStreamingCard) {
      accumulatedStreamText = '';
      wordStreamQueue = [];
      isStreamingActive = true;

      const card = document.createElement('div');
      card.className = 'message-card assistant-card';

      const avatar = document.createElement('div');
      avatar.className = 'message-avatar';
      const avatarImg = document.createElement('img');
      avatarImg.src = '/static/img/kiraht_ai_logo.png?v=4.0';
      avatarImg.className = 'message-avatar-img assistant-avatar-img';
      avatarImg.alt = 'K';
      avatar.appendChild(avatarImg);

      const body = document.createElement('div');
      body.className = 'message-body';

      const header = document.createElement('div');
      header.className = 'message-header';

      const headerLeft = document.createElement('div');
      headerLeft.className = 'message-header-left';

      const sender = document.createElement('span');
      sender.className = 'sender-name';
      sender.textContent = 'KIRAHT AI';
      headerLeft.appendChild(sender);

      const streamBadge = document.createElement('span');
      streamBadge.className = 'engine-source-badge badge-thinking';
      streamBadge.innerHTML = `<span class="badge-icon">⚡</span> <span class="badge-text">STREAMING...</span>`;
      headerLeft.appendChild(streamBadge);

      const time = document.createElement('span');
      time.className = 'message-timestamp';
      time.textContent = getCurrentTime();

      header.appendChild(headerLeft);
      header.appendChild(time);

      const contentEl = document.createElement('div');
      contentEl.className = 'message-content';

      body.appendChild(header);
      body.appendChild(contentEl);

      card.appendChild(avatar);
      card.appendChild(body);

      chatViewport.appendChild(card);

      currentStreamingCard = card;
      currentStreamingContentEl = contentEl;
    }

    // Tokenize chunk into words while preserving spacing and linebreaks
    const tokens = chunk.match(/\S+|\s+/g) || [chunk];
    for (let i = 0; i < tokens.length; i++) {
      wordStreamQueue.push(tokens[i]);
    }

    isStreamingActive = true;
    startWordStreamWorker();
  }

  function handleStreamEnd(fullText, meta) {
    isStreamingActive = false;

    // If queue is already empty, finish immediately
    if (wordStreamQueue.length === 0) {
      if (wordStreamInterval) {
        clearInterval(wordStreamInterval);
        wordStreamInterval = null;
      }
      finishStream(fullText, meta);
    } else {
      // Allow remaining words to drain smoothly, then finish
      pendingStreamEnd = { fullText, meta };
      startWordStreamWorker();
    }
  }

  function finishStream(fullText, meta) {
    if (currentStreamingCard) {
      const headerLeft = currentStreamingCard.querySelector('.message-header-left');
      if (headerLeft) {
        const oldBadge = headerLeft.querySelector('.engine-source-badge');
        if (oldBadge) {
          headerLeft.removeChild(oldBadge);
        }
        const badge = createEngineSourceBadge(meta);
        headerLeft.appendChild(badge);
      }
    }

    if (currentStreamingContentEl) {
      const textToRender = fullText || accumulatedStreamText;
      currentStreamingContentEl.innerHTML = formatMarkdown(textToRender);

      if (meta && meta.screenshot_url) {
        const img = document.createElement('img');
        img.src = meta.screenshot_url;
        img.className = 'chat-preview-img';
        img.alt = 'Screenshot';
        img.onclick = function () { window.open(meta.screenshot_url, '_blank'); };
        currentStreamingContentEl.appendChild(img);
      }
    }

    const engineTag = (meta && meta.engine) ? meta.engine.toUpperCase() : 'AI';
    const sourceLabel = (meta && meta.source_label) ? meta.source_label : `Delivered via ${engineTag}`;
    logActivity('KIRAHT', 'Response Done', sourceLabel);

    // Synchronize to Voice Transcript Sidebar
    if (typeof appendTranscriptEntry === 'function' && textToRender) {
      appendTranscriptEntry('assistant', textToRender, getCurrentTime(), meta);
    }
    if (typeof updateVoiceResponseCard === 'function' && textToRender) {
      updateVoiceResponseCard(textToRender);
    }

    if (((typeof isVoiceModeEnabled !== 'undefined' && isVoiceModeEnabled) || isVoiceTriggered) && textToRender) {
      speakAloud(textToRender);
      isVoiceTriggered = false;
    }

    currentStreamingCard = null;
    currentStreamingContentEl = null;
    accumulatedStreamText = '';
    wordStreamQueue = [];
    thinkingCard = null;
    setGeneratingState(false);
    scrollToBottom();
  }

  function handleChatCleared() {
    thinkingCard = null;
    currentStreamingCard = null;
    currentStreamingContentEl = null;
    wordStreamQueue = [];
    accumulatedStreamText = '';
    isHistoryRendered = false;
    setGeneratingState(false);

    const navText = document.getElementById('nav-history-text');
    const btnNav = document.getElementById('btn-load-history');
    const tileTitle = document.getElementById('tile-history-title');
    const tileDesc = document.getElementById('tile-history-desc');

    if (navText) navText.textContent = 'LOAD HISTORY';
    if (btnNav) btnNav.classList.remove('active');
    if (tileTitle) tileTitle.textContent = 'LOAD HISTORY';
    if (tileDesc) tileDesc.textContent = `${cachedChatHistory.length} past logs saved`;

    chatViewport.innerHTML = `
      <div class="message-card assistant-card">
        <div class="message-avatar">
          <img src="/static/img/kiraht_ai_logo.png?v=4.0" class="message-avatar-img assistant-avatar-img" alt="K">
        </div>
        <div class="message-body">
          <div class="message-header">
            <span class="sender-name">KIRAHT AI</span>
            <span class="message-timestamp">Just now</span>
          </div>
          <div class="message-content">
            Fresh screen session active, Sir. 3D Arc Reactor synchronized. Past logs remain safely archived in chat_history.json.
          </div>
        </div>
      </div>
    `;
    if (typeof voiceTranscriptList !== 'undefined' && voiceTranscriptList) {
      voiceTranscriptList.innerHTML = '';
    }
    if (typeof transcriptCountTag !== 'undefined' && transcriptCountTag) {
      transcriptCountTag.textContent = '0 EXCHANGES';
    }
    scrollToBottom();
  }

  // =========================================================================
  // 6. ACTIVITY / TOOL LOG STREAM
  // =========================================================================
  function logActivity(actor, action, detail) {
    if (!activityLogStream) return;

    const entry = document.createElement('div');
    entry.className = 'activity-entry';

    const time = document.createElement('span');
    time.className = 'log-time';
    time.textContent = `[${getCurrentTime(true)}]`;

    const actorEl = document.createElement('span');
    const actLower = (actor || 'System').toLowerCase();
    actorEl.className = `log-actor actor-${actLower}`;
    actorEl.textContent = actor || 'System';

    const arrow = document.createElement('span');
    arrow.className = 'log-arrow';
    arrow.textContent = '➔';

    const actEl = document.createElement('span');
    actEl.className = 'log-action';
    actEl.textContent = action || '';

    const detailEl = document.createElement('span');
    detailEl.className = 'log-detail';
    detailEl.textContent = detail ? `(${detail})` : '';

    entry.appendChild(time);
    entry.appendChild(actorEl);
    entry.appendChild(arrow);
    entry.appendChild(actEl);
    entry.appendChild(detailEl);

    activityLogStream.appendChild(entry);
    activityLogStream.scrollTop = activityLogStream.scrollHeight;

    // Flash left Telemetry panel Tools status on tool or app execution
    if (coreToolsStatus && (actor === 'Tool' || (action && (action.includes('Tool') || action.includes('APP:') || action.includes('Execute'))))) {
      const toolLabel = detail ? detail.replace(/^Source:\s*/i, '').replace(/[()]/g, '') : action;
      coreToolsStatus.innerHTML = `<span class="telem-dot-mini green-pulse"></span> ${toolLabel.substring(0, 16)}`;
      coreToolsStatus.className = 'stat-value text-green';
      if (window._toolStatusResetTimer) clearTimeout(window._toolStatusResetTimer);
      window._toolStatusResetTimer = setTimeout(function () {
        if (coreToolsStatus) {
          coreToolsStatus.innerHTML = `<span class="telem-dot-mini green-pulse"></span> READY`;
        }
      }, 8000);
    }

    // Keep log trimmed to 40 entries
    while (activityLogStream.children.length > 40) {
      activityLogStream.removeChild(activityLogStream.firstChild);
    }

    activityLogStream.scrollTop = activityLogStream.scrollHeight;
  }

  // =========================================================================
  // 7. INPUT, SEND & GENERATION CANCELLATION (STOP) HANDLING
  // =========================================================================
  function setGeneratingState(generating) {
    isGenerating = Boolean(generating);
    if (!btnSend) return;
    if (isGenerating) {
      btnSend.classList.add('btn-cancel');
      btnSend.setAttribute('title', 'Stop Generating (Esc)');
      btnSend.innerHTML = '<span class="btn-cancel-icon" style="font-size:12px;">■</span> <span class="btn-send-text">STOP</span>';
      if (typeof setReactorState === 'function') setReactorState('thinking');
    } else {
      btnSend.classList.remove('btn-cancel');
      btnSend.setAttribute('title', 'Send Directive (Enter)');
      btnSend.innerHTML = '<span class="btn-send-icon">▲</span> <span class="btn-send-text">TRANSMIT</span>';
      if (typeof setReactorState === 'function' && typeof isListening !== 'undefined' && !isListening) {
        setReactorState('idle');
      }
    }
  }

  function cancelGeneration() {
    if (!isGenerating && !thinkingCard && !currentStreamingCard && (!window.speechSynthesis || !window.speechSynthesis.speaking)) return;
    logActivity('User', 'Stop', 'Generation / speech halted by user');
    sendWebSocket({ type: 'cancel' });

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (typeof stopSpeakingModulation === 'function') {
      stopSpeakingModulation();
    }
    if (equalizerBars) {
      equalizerBars.classList.remove('speaking');
    }

    if (wordStreamInterval) {
      clearInterval(wordStreamInterval);
      wordStreamInterval = null;
    }
    wordStreamQueue = [];
    isStreamingActive = false;
    pendingStreamEnd = null;

    if (thinkingCard) {
      if (thinkingCard.parentNode) {
        thinkingCard.parentNode.removeChild(thinkingCard);
      }
      thinkingCard = null;
    }

    if (currentStreamingContentEl) {
      const cursor = currentStreamingContentEl.querySelector('.typing-cursor');
      if (cursor) cursor.remove();
      const stopNote = document.createElement('span');
      stopNote.className = 'badge-stopped';
      stopNote.textContent = '[Response stopped by user]';
      currentStreamingContentEl.appendChild(stopNote);
    }

    currentStreamingCard = null;
    currentStreamingContentEl = null;
    accumulatedStreamText = '';

    setGeneratingState(false);
    updateStatus('READY', 'Ready for command');
    if (typeof setReactorState === 'function') setReactorState('idle');
    if (typeof setVoicePipelineState === 'function') setVoicePipelineState('idle');
    scrollToBottom();
  }

  function sendMessage() {
    if (isGenerating) {
      cancelGeneration();
      return;
    }

    const text = chatInput.value.trim();
    if (!text) return;

    if (!isConnected) {
      logActivity('System', 'Warning', 'Not connected to backend. Reconnecting...');
      initWebSocket();
      return;
    }

    // Immediately render user message card with avatar optimistically (Point 9)
    const nowTime = getCurrentTime();
    appendMessageCard('user', text, nowTime);
    lastOptimisticUserMessage = text;

    chatInput.value = '';
    chatInput.style.height = '42px';
    chatInput.focus();
    scrollToBottom();

    // Show thinking indicator & switch button to STOP (Point 8)
    showThinkingIndicator();
    setGeneratingState(true);

    // Update live voice readout card and pipeline state
    if (voiceUserText) {
      voiceUserText.textContent = `"${text}"`;
    }
    if (userSpeechStatus) {
      userSpeechStatus.textContent = 'DISPATCHED';
      userSpeechStatus.className = 'speech-live-tag';
    }
    setVoicePipelineState('processing', 'TACTICAL SYNAPSE • DISPATCHING');

    logActivity('User', 'Transmit', text.length > 50 ? text.substring(0, 47) + '...' : text);
    sendWebSocket({ type: 'chat', message: text });
  }

  if (btnSend) btnSend.addEventListener('click', sendMessage);

  if (chatInput) {
    chatInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      } else if (e.key === 'Escape' && isGenerating) {
        e.preventDefault();
        cancelGeneration();
      }
    });

    // Auto-expand textarea
    chatInput.addEventListener('input', function () {
      this.style.height = '42px';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
  }

  window.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isGenerating) {
      e.preventDefault();
      cancelGeneration();
    }
  });

  // Clear chat button - Clears screen view while preserving chat_history.json
  if (btnClearChat) {
    btnClearChat.addEventListener('click', function () {
      if (confirm('Start fresh screen session, Sir? (Your chat_history.json will stay completely safe)')) {
        logActivity('User', 'Fresh Screen', 'Clearing active viewport');
        handleChatCleared();
      }
    });
  }

  // =========================================================================
  // 7.1 KIRAHT AI VOICE & TACTICAL INTERFACE ENGINE: AUDIO-REACTIVE ARC REACTOR & BARGE-IN
  // =========================================================================
  const btnMic = document.getElementById('btn-mic');
  const btnVoiceMode = document.getElementById('btn-voice-mode');
  const navVoiceText = document.getElementById('nav-voice-text');
  const equalizerBars = document.getElementById('equalizer-bars');

  // Central Voice Interface elements
  const centralVoiceInterface = document.getElementById('central-voice-interface');
  const voiceAudioStatus = document.getElementById('voice-audio-status');
  const pipelineIdle = document.getElementById('pipeline-idle');
  const pipelineListening = document.getElementById('pipeline-listening');
  const pipelineProcessing = document.getElementById('pipeline-processing');
  const pipelineSpeaking = document.getElementById('pipeline-speaking');
  const userSpeechCard = document.getElementById('user-speech-card');
  const kirahtSpeechCard = document.getElementById('kiraht-speech-card');
  const userSpeechStatus = document.getElementById('user-speech-status');
  const kirahtSpeechStatus = document.getElementById('kiraht-speech-status');
  const voiceUserText = document.getElementById('voice-user-text');
  const voiceKirahtText = document.getElementById('voice-kiraht-text');
  const btnCentralMic = document.getElementById('btn-central-mic');
  const centralMicText = document.getElementById('central-mic-text');
  const btnCentralInterrupt = document.getElementById('btn-central-interrupt');
  const btnReturnChat = document.getElementById('btn-return-chat');

  // Adaptive Right Panel Tabs & Voice Transcript elements
  const tabBtnTranscript = document.getElementById('tab-btn-transcript');
  const tabBtnActions = document.getElementById('tab-btn-actions');
  const voiceTranscriptWrapper = document.getElementById('voice-transcript-wrapper');
  const voiceTranscriptList = document.getElementById('voice-transcript-list');
  const transcriptCountTag = document.getElementById('transcript-count-tag');
  const actionTilesGrid = document.getElementById('action-tiles-grid');
  const chatInputBar = document.getElementById('chat-input-bar');

  let isVoiceModeEnabled = localStorage.getItem('kiraht_voice_mode') === 'true';
  let currentHudMode = localStorage.getItem('kiraht_hud_mode') || (isVoiceModeEnabled ? 'voice' : 'chat');
  let recognition = null;
  let isListening = false;
  let isVoiceTriggered = false;
  let cachedVoices = [];
  let synthKeepAlive = null;
  let speechDebounceTimer = null;
  let activeReactorState = 'idle';
  let currentVoiceStage = 'idle';

  // Helper: Append a message to the Voice Transcript Sidebar
  function appendTranscriptEntry(role, content, timestamp, meta) {
    if (!voiceTranscriptList) return;
    const isUser = role === 'user';
    const clean = isUser ? content : (cleanTextForSpeech(content) || content);
    if (!clean || !clean.trim()) return;

    const entry = document.createElement('div');
    entry.className = `transcript-entry ${isUser ? 'user-entry' : 'assistant-entry'}`;

    const metaDiv = document.createElement('div');
    metaDiv.className = 'transcript-entry-meta';

    const roleTag = document.createElement('span');
    roleTag.className = 'transcript-role-tag';
    roleTag.textContent = isUser ? 'OPERATOR' : 'KIRAHT AI';

    const timeSpan = document.createElement('span');
    timeSpan.className = 'transcript-time';
    timeSpan.textContent = timestamp || getCurrentTime();

    metaDiv.appendChild(roleTag);
    metaDiv.appendChild(timeSpan);
    entry.appendChild(metaDiv);

    const textDiv = document.createElement('div');
    textDiv.className = 'transcript-entry-text';
    textDiv.textContent = clean;
    entry.appendChild(textDiv);

    if (meta && meta.tool) {
      const toolBadge = document.createElement('div');
      toolBadge.className = 'transcript-tool-badge';
      toolBadge.textContent = `⚡ TOOL: ${meta.tool}`;
      entry.appendChild(toolBadge);
    }

    voiceTranscriptList.appendChild(entry);
    voiceTranscriptList.scrollTop = voiceTranscriptList.scrollHeight;

    if (transcriptCountTag) {
      const count = voiceTranscriptList.querySelectorAll('.transcript-entry').length;
      transcriptCountTag.textContent = `${count} EXCHANGES`;
    }
  }

  // Helper: Synchronize entire conversation history into Voice Transcript
  function syncTranscriptWithHistory() {
    if (!voiceTranscriptList) return;
    voiceTranscriptList.innerHTML = '';
    const cards = chatViewport ? chatViewport.querySelectorAll('.msg-card') : [];
    cards.forEach(card => {
      const isUser = card.classList.contains('user');
      const textEl = card.querySelector('.msg-text');
      const timeEl = card.querySelector('.msg-timestamp');
      if (textEl && textEl.textContent.trim()) {
        const text = textEl.textContent.trim();
        const time = timeEl ? timeEl.textContent.trim() : getCurrentTime();
        appendTranscriptEntry(isUser ? 'user' : 'assistant', text, time);
      }
    });
  }

  // Helper: Switch Right Panel Tab (Transcript vs Actions)
  function switchRightTab(tabName) {
    if (tabName === 'transcript') {
      if (tabBtnTranscript) tabBtnTranscript.classList.add('active');
      if (tabBtnActions) tabBtnActions.classList.remove('active');
      if (voiceTranscriptWrapper) voiceTranscriptWrapper.style.display = 'flex';
      if (actionTilesGrid) actionTilesGrid.style.display = 'none';
    } else {
      if (tabBtnActions) tabBtnActions.classList.add('active');
      if (tabBtnTranscript) tabBtnTranscript.classList.remove('active');
      if (actionTilesGrid) actionTilesGrid.style.display = 'grid';
      if (voiceTranscriptWrapper) voiceTranscriptWrapper.style.display = 'none';
    }
  }

  // Helper: Update Central Voice Readout Cards
  function updateVoiceResponseCard(text) {
    if (voiceKirahtText) {
      const clean = cleanTextForSpeech(text) || text;
      voiceKirahtText.textContent = `"${clean}"`;
    }
    if (kirahtSpeechStatus) {
      kirahtSpeechStatus.textContent = isVoiceModeEnabled ? 'SPEAKING' : 'DELIVERED';
      kirahtSpeechStatus.className = isVoiceModeEnabled ? 'speech-live-tag tag-speaking' : 'speech-live-tag';
    }
  }

  // Helper: Set Voice State Pipeline (IDLE -> LISTENING -> PROCESSING -> SPEAKING)
  function setVoicePipelineState(stage, detailText) {
    currentVoiceStage = stage;
    const stages = ['idle', 'listening', 'processing', 'speaking'];
    const elMap = {
      idle: pipelineIdle,
      listening: pipelineListening,
      processing: pipelineProcessing,
      speaking: pipelineSpeaking
    };

    stages.forEach(s => {
      const el = elMap[s];
      if (el) {
        if (s === stage) {
          el.classList.add('active');
        } else {
          el.classList.remove('active');
        }
      }
    });

    if (voiceAudioStatus) {
      if (detailText) {
        voiceAudioStatus.textContent = detailText;
      } else {
        const defaults = {
          idle: 'VOICE ENGINE READY • STANDBY',
          listening: 'MICROPHONE ACTIVE • LISTENING...',
          processing: 'TACTICAL SYNAPSE • EXECUTING...',
          speaking: 'AUDIO TRANSMISSION ACTIVE'
        };
        voiceAudioStatus.textContent = defaults[stage] || 'STANDBY';
      }
    }

    if (btnCentralMic) {
      if (stage === 'listening') {
        btnCentralMic.classList.add('active');
        if (centralMicText) centralMicText.textContent = 'MIC ACTIVE';
      } else {
        btnCentralMic.classList.remove('active');
        if (centralMicText) centralMicText.textContent = 'MIC STANDBY';
      }
    }

    // Synchronize Arc Reactor state
    if (stage === 'listening') {
      setReactorState('listening');
    } else if (stage === 'processing') {
      setReactorState('thinking');
    } else if (stage === 'speaking') {
      setReactorState('speaking');
    } else {
      if (!isGenerating && !isListening) {
        setReactorState('idle');
      }
    }
  }

  // 1. Web Audio API Context & Sci-Fi SFX Synthesizer (0 external audio files needed)
  let audioCtx = null;
  function getAudioContext() {
    if (!audioCtx) {
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      if (AudioCtxClass) {
        audioCtx = new AudioCtxClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playSciFiTone(type) {
    try {
      const ctx = getAudioContext();
      if (!ctx) return;
      const now = ctx.currentTime;

      if (type === 'activate') {
        // High-tech ascending chirp (440Hz -> 880Hz)
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.11);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.13);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.14);
      } else if (type === 'listen') {
        // Gentle harmonic listening ping (660Hz -> 880Hz)
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(660, now);
        osc.frequency.setValueAtTime(880, now + 0.05);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.2);
      } else if (type === 'transmit') {
        // Direct uplink transmission pulse (500Hz -> 1100Hz)
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(500, now);
        osc.frequency.exponentialRampToValueAtTime(1100, now + 0.08);
        gain.gain.setValueAtTime(0.07, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.09);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.1);
      } else if (type === 'interrupt') {
        // Tactical cutoff disengage sound (descending 260Hz -> 70Hz sawtooth burst)
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(260, now);
        osc.frequency.exponentialRampToValueAtTime(70, now + 0.09);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.11);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.12);
      } else if (type === 'complete') {
        // Positive completion blip (587Hz -> 880Hz)
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, now);
        osc.frequency.setValueAtTime(880, now + 0.06);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.18);
      }
    } catch (e) {
      // AudioContext policy handled gracefully
    }
  }

  // 2. Arc Reactor Core Tactical State Controller
  function setReactorState(state, statusOverride) {
    activeReactorState = state;
    if (!reactorCore) return;

    reactorCore.classList.remove('state-listening', 'state-speaking', 'state-thinking', 'state-interrupted');

    if (state === 'listening') {
      reactorCore.classList.add('state-listening');
      if (coreStatusText) {
        coreStatusText.textContent = statusOverride || '[VOICE: LISTENING]';
        coreStatusText.style.color = 'var(--accent-cyan)';
      }
    } else if (state === 'speaking') {
      reactorCore.classList.add('state-speaking');
      if (coreStatusText) {
        coreStatusText.textContent = statusOverride || '[KIRAHT: SPEAKING]';
        coreStatusText.style.color = '#00aaff';
      }
    } else if (state === 'thinking') {
      reactorCore.classList.add('state-thinking');
      if (coreStatusText) {
        coreStatusText.textContent = statusOverride || '[CORE: PROCESSING]';
        coreStatusText.style.color = 'var(--accent-amber)';
      }
    } else if (state === 'interrupted') {
      reactorCore.classList.add('state-interrupted');
      if (coreStatusText) {
        coreStatusText.textContent = statusOverride || '[ABORT: INTERRUPTED]';
        coreStatusText.style.color = '#ff1744';
      }
    } else {
      // Idle / Normal
      if (coreStatusText) {
        coreStatusText.textContent = 'SYS: ONLINE';
        coreStatusText.style.color = 'var(--accent-green)';
      }
      if (reactorEpicenter) {
        reactorEpicenter.style.transform = 'translate(-50%, -50%) scale(1)';
      }
      if (epicenterPlasmaCore) {
        epicenterPlasmaCore.style.boxShadow = '';
      }
    }
  }

  // 3. Audio-Reactive Real-Time Microphone Analysis Loop
  let micStream = null;
  let micAnalyser = null;
  let micSource = null;
  let micFreqData = null;
  let micRafId = null;
  let currentAmp = 0;

  function startMicAudioAnalysis() {
    if (micRafId) return;
    const ctx = getAudioContext();
    if (!ctx || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;

    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(function (stream) {
        micStream = stream;
        micSource = ctx.createMediaStreamSource(stream);
        micAnalyser = ctx.createAnalyser();
        micAnalyser.fftSize = 256;
        micAnalyser.smoothingTimeConstant = 0.7;
        micSource.connect(micAnalyser);
        micFreqData = new Uint8Array(micAnalyser.frequencyBinCount);

        function renderAudioReaction() {
          if (!isListening && activeReactorState !== 'listening') {
            stopMicAudioAnalysis();
            return;
          }

          if (isListening && micAnalyser && micFreqData) {
            micAnalyser.getByteFrequencyData(micFreqData);
            let sum = 0;
            for (let i = 0; i < micFreqData.length; i++) {
              sum += micFreqData[i] * micFreqData[i];
            }
            const rms = Math.sqrt(sum / micFreqData.length) / 128; // ~0 to 1
            const targetAmp = Math.min(1.0, rms * 1.6);
            currentAmp += (targetAmp - currentAmp) * 0.35; // smooth lerp

            // Scale Arc Reactor epicenter based on live voice amplitude!
            if (reactorEpicenter) {
              const scale = 1 + currentAmp * 0.42;
              reactorEpicenter.style.transform = `translate(-50%, -50%) scale(${scale.toFixed(3)})`;
            }
            if (epicenterPlasmaCore) {
              const glow = 20 + currentAmp * 75;
              const alpha = (0.5 + currentAmp * 0.5).toFixed(2);
              epicenterPlasmaCore.style.boxShadow = `0 0 ${glow.toFixed(0)}px rgba(0, 243, 255, ${alpha}), inset 0 0 ${(12 + currentAmp * 35).toFixed(0)}px rgba(0, 255, 170, ${alpha})`;
            }
            if (coreStatusText && isListening) {
              if (currentAmp > 0.08) {
                coreStatusText.textContent = '[VOICE: DETECTING]';
              } else {
                coreStatusText.textContent = '[VOICE: LISTENING]';
              }
            }
          }

          micRafId = requestAnimationFrame(renderAudioReaction);
        }

        micRafId = requestAnimationFrame(renderAudioReaction);
      })
      .catch(function (err) {
        console.warn('[HUD] Audio Analyser mic notice:', err);
      });
  }

  function stopMicAudioAnalysis() {
    if (micRafId) {
      cancelAnimationFrame(micRafId);
      micRafId = null;
    }
    if (micSource) {
      try { micSource.disconnect(); } catch (e) {}
      micSource = null;
    }
    if (micStream) {
      try {
        micStream.getTracks().forEach(t => t.stop());
      } catch (e) {}
      micStream = null;
    }
    currentAmp = 0;
    if (reactorEpicenter && activeReactorState !== 'speaking') {
      reactorEpicenter.style.transform = 'translate(-50%, -50%) scale(1)';
    }
    if (epicenterPlasmaCore && activeReactorState !== 'speaking') {
      epicenterPlasmaCore.style.boxShadow = '';
    }
  }

  // 4. Speech Synthesis Simulated Acoustic Wave Modulation
  let speakingModTimer = null;
  function startSpeakingModulation() {
    if (speakingModTimer) clearInterval(speakingModTimer);
    let step = 0;
    setReactorState('speaking');
    speakingModTimer = setInterval(function () {
      if (!window.speechSynthesis || !window.speechSynthesis.speaking) {
        stopSpeakingModulation();
        return;
      }
      step++;
      const mod = 0.5 + 0.5 * Math.sin(step * 0.45) * (0.8 + 0.2 * Math.cos(step * 0.2));
      if (reactorEpicenter) {
        reactorEpicenter.style.transform = `translate(-50%, -50%) scale(${(1 + mod * 0.22).toFixed(3)})`;
      }
      if (epicenterPlasmaCore) {
        const glow = 25 + mod * 55;
        epicenterPlasmaCore.style.boxShadow = `0 0 ${glow.toFixed(0)}px rgba(0, 170, 255, 0.95), inset 0 0 ${(15 + mod * 25).toFixed(0)}px rgba(0, 243, 255, 0.75)`;
      }
    }, 50);
  }

  function stopSpeakingModulation() {
    if (speakingModTimer) {
      clearInterval(speakingModTimer);
      speakingModTimer = null;
    }
    if (!isListening && !isGenerating) {
      setReactorState('idle');
    }
  }

  // 5. Stop Keywords & Interruption Engine
  const STOP_KEYWORDS = [
    'stop', 'stop it', 'stop talking', 'shut up', 'quiet', 'be quiet',
    'silence', 'pause', 'hold on', 'wait', 'enough', 'cancel',
    'halt', 'terminate', 'neruthu', 'niruthu', 'podhum', 'vaaya moodu', 'iruda'
  ];

  function isStopPhrase(raw) {
    if (!raw) return false;
    const lower = raw.toLowerCase().trim().replace(/[!.,?]/g, '');
    return STOP_KEYWORDS.some(function (k) {
      const regex = new RegExp('(?:^|\\s)' + k + '(?:\\s|$)', 'i');
      return regex.test(lower) || lower === k;
    });
  }

  function triggerVoiceInterruption(phrase) {
    // 1. Immediately cancel vocal speech
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    stopSpeakingModulation();

    // 2. Cancel active streaming / generation
    cancelGeneration();

    // 3. Reset equalizer
    if (equalizerBars) equalizerBars.classList.remove('speaking');

    // 4. Play tactical cutoff sound effect
    playSciFiTone('interrupt');

    // 5. Visual Crimson Shockwave on Arc Reactor
    setReactorState('interrupted');
    setTimeout(function () {
      if (isListening) {
        setReactorState('listening');
      } else {
        setReactorState('idle');
      }
    }, 1200);

    // 5. Update pipeline
    setVoicePipelineState('idle', 'INTERRUPTED BY OPERATOR');
    if (kirahtSpeechStatus) {
      kirahtSpeechStatus.textContent = 'INTERRUPTED';
      kirahtSpeechStatus.className = 'speech-live-tag';
    }

    // 6. Log
    logActivity('User', 'Voice Interrupted', `Halted by command: "${phrase || 'stop'}"`);

    // 7. Clear chat input
    if (chatInput) {
      chatInput.value = '';
      chatInput.placeholder = 'Interrupted. Listening for next command...';
    }
  }

  // 6. Mode Switcher (Chat Mode vs Voice Mode)
  function setHudMode(mode, autoListen = false) {
    currentHudMode = mode;
    localStorage.setItem('kiraht_hud_mode', mode);
    const hudMain = document.getElementById('hud-main');

    if (mode === 'voice') {
      isVoiceModeEnabled = true;
      localStorage.setItem('kiraht_voice_mode', 'true');
      if (hudMain) {
        hudMain.classList.remove('mode-chat');
        hudMain.classList.add('mode-voice');
      }
      if (centralVoiceInterface) {
        centralVoiceInterface.style.display = 'flex';
      }
      if (btnVoiceMode) {
        btnVoiceMode.classList.add('voice-active');
      }
      if (navVoiceText) {
        navVoiceText.textContent = 'VOICE: ACTIVE';
      }
      switchRightTab('transcript');
      setVoicePipelineState(isListening ? 'listening' : 'idle', 'VOICE ENGINE ARMED • LISTENING');
      logActivity('System', 'HUD Mode', 'Engaged KIRAHT VOICE COMMAND INTERFACE');

      if (autoListen || !isListening) {
        playSciFiTone('activate');
        startMicListening();
      }
    } else {
      // Chat mode
      isVoiceModeEnabled = false;
      localStorage.setItem('kiraht_voice_mode', 'false');
      if (hudMain) {
        hudMain.classList.remove('mode-voice');
        hudMain.classList.add('mode-chat');
      }
      if (centralVoiceInterface) {
        centralVoiceInterface.style.display = 'none';
      }
      if (btnVoiceMode) {
        btnVoiceMode.classList.remove('voice-active');
      }
      if (navVoiceText) {
        navVoiceText.textContent = 'VOICE: OFF';
      }
      switchRightTab('actions');
      setVoicePipelineState('idle', 'CHAT INTERFACE READY');
      logActivity('System', 'HUD Mode', 'Switched to CHAT INTERFACE');

      if (window.speechSynthesis) window.speechSynthesis.cancel();
      stopSpeakingModulation();
      stopMicListening();
      if (equalizerBars) equalizerBars.classList.remove('speaking');
    }
  }

  function toggleVoiceMode() {
    if (currentHudMode === 'voice') {
      setHudMode('chat', false);
    } else {
      setHudMode('voice', true);
    }
  }

  function updateVoiceModeUI() {
    if (navVoiceText) {
      navVoiceText.textContent = currentHudMode === 'voice' ? 'VOICE: ACTIVE' : 'VOICE: OFF';
    }
    if (btnVoiceMode) {
      if (currentHudMode === 'voice') {
        btnVoiceMode.classList.add('voice-active');
      } else {
        btnVoiceMode.classList.remove('voice-active');
      }
    }
  }

  if (btnVoiceMode) {
    btnVoiceMode.addEventListener('click', toggleVoiceMode);
  }

  // 7. Speech Synthesis Output & Voice Feedback Engine
  function showVoiceToast(msg, type = 'info') {
    let toast = document.getElementById('voice-hud-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'voice-hud-toast';
      toast.className = 'voice-hud-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.className = `voice-hud-toast show ${type}`;
    if (window._voiceToastTimer) clearTimeout(window._voiceToastTimer);
    window._voiceToastTimer = setTimeout(() => {
      toast.className = 'voice-hud-toast';
    }, 6000);
  }

  function loadCachedVoices() {
    if (window.speechSynthesis) {
      try {
        const v = window.speechSynthesis.getVoices();
        if (v && v.length) {
          cachedVoices = v;
        }
      } catch (e) {}
    }
  }

  if (window.speechSynthesis) {
    loadCachedVoices();
    window.speechSynthesis.onvoiceschanged = loadCachedVoices;
  }

  function startSynthKeepAlive() {
    if (synthKeepAlive) clearInterval(synthKeepAlive);
    synthKeepAlive = setInterval(() => {
      if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.pause();
        window.speechSynthesis.resume();
      } else {
        clearInterval(synthKeepAlive);
        synthKeepAlive = null;
      }
    }, 9000);
  }

  function cleanTextForSpeech(text) {
    if (!text) return '';
    return text
      .replace(/```[\s\S]*?```/g, 'Code block omitted.')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/!\[[^\]]*\]\([^)]+\)/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/[*_#~>]/g, '')
      .replace(/https?:\/\/\S+/g, 'link')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function speakViaBackend(text) {
    if (!text) return;
    const clean = cleanTextForSpeech(text);
    if (!clean) return;
    fetch('/api/voice/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: clean, rate: 175 })
    }).catch(e => console.warn('[HUD] Backend TTS fallback notice:', e));
  }

  function speakAloud(text) {
    const clean = cleanTextForSpeech(text);
    if (!clean) return;

    if (!window.speechSynthesis) {
      speakViaBackend(clean);
      return;
    }

    try {
      window.speechSynthesis.cancel();
    } catch (e) {}

    setTimeout(() => {
      try {
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        loadCachedVoices();
        const voices = cachedVoices.length ? cachedVoices : (window.speechSynthesis.getVoices() || []);
        const langVal = localStorage.getItem('kiraht_voice_lang') || 'en-IN';

        let chosenVoice = voices.find(v => v.lang.replace('_', '-').toLowerCase().startsWith(langVal.toLowerCase()));
        if (!chosenVoice) {
          chosenVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('David') || v.name.includes('Mark') || v.name.includes('Zira') || v.name.includes('Samantha')));
        }
        if (!chosenVoice) {
          chosenVoice = voices.find(v => v.lang.startsWith('en'));
        }
        if (chosenVoice) {
          utterance.voice = chosenVoice;
        }

        utterance.onstart = function () {
          if (equalizerBars) equalizerBars.classList.add('speaking');
          startSpeakingModulation();
          setVoicePipelineState('speaking', 'KIRAHT AUDIO TRANSMISSION ACTIVE');
          if (voiceKirahtText) {
            voiceKirahtText.textContent = `"${clean}"`;
          }
          if (kirahtSpeechStatus) {
            kirahtSpeechStatus.textContent = 'SPEAKING';
            kirahtSpeechStatus.className = 'speech-live-tag tag-speaking';
          }
          startSynthKeepAlive();
          ensureRecognitionForBargeIn();
        };

        utterance.onend = function () {
          if (synthKeepAlive) {
            clearInterval(synthKeepAlive);
            synthKeepAlive = null;
          }
          if (equalizerBars) equalizerBars.classList.remove('speaking');
          stopSpeakingModulation();
          playSciFiTone('complete');
          if (kirahtSpeechStatus) {
            kirahtSpeechStatus.textContent = 'READY';
            kirahtSpeechStatus.className = 'speech-live-tag';
          }

          // Hands-free conversational loop:
          if (isVoiceModeEnabled && !isGenerating) {
            setVoicePipelineState('listening', 'CONTINUOUS LISTENING ARMED');
            setTimeout(function () {
              if (!isListening) {
                startMicListening();
              }
            }, 450);
          } else {
            setVoicePipelineState('idle', 'SYSTEM IDLE & READY');
          }
        };

        utterance.onerror = function (event) {
          if (synthKeepAlive) {
            clearInterval(synthKeepAlive);
            synthKeepAlive = null;
          }
          if (equalizerBars) equalizerBars.classList.remove('speaking');
          stopSpeakingModulation();
          if (kirahtSpeechStatus) {
            kirahtSpeechStatus.textContent = 'READY';
            kirahtSpeechStatus.className = 'speech-live-tag';
          }
          setVoicePipelineState('idle');
          // Fallback to backend SAPI5 if browser synthesis failed
          speakViaBackend(clean);
        };

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error('[HUD] SpeechSynthesis error, delegating to backend:', err);
        speakViaBackend(clean);
      }
    }, 45);
  }

  // 8. Web Speech Recognition Engine (Continuous Barge-In & Auto Submit)
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return null;

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    const currentLang = localStorage.getItem('kiraht_voice_lang') || 'en-IN';
    rec.lang = currentLang;

    rec.onstart = function () {
      isListening = true;
      if (btnMic) btnMic.classList.add('listening');
      if (chatInput) chatInput.placeholder = 'KIRAHT Listening... Speak your command or say "Stop"';
      setVoicePipelineState('listening', 'MICROPHONE ACTIVE • LISTENING...');
      if (userSpeechStatus) {
        userSpeechStatus.textContent = 'LISTENING';
        userSpeechStatus.className = 'speech-live-tag tag-listening';
      }
      try {
        startMicAudioAnalysis();
      } catch (e) {}
      logActivity('User', 'Voice Input', 'Microphone active — audio analysis engaged');
    };

    rec.onresult = function (event) {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      const spoken = (final || interim).trim();
      if (!spoken) return;

      isVoiceTriggered = true; // User spoke, so assistant should speak back!

      if (voiceUserText) {
        voiceUserText.textContent = `"${spoken}"`;
      }
      if (userSpeechStatus) {
        if (final) {
          userSpeechStatus.textContent = 'VERIFIED';
          userSpeechStatus.className = 'speech-live-tag';
        } else {
          userSpeechStatus.textContent = 'STREAMING';
          userSpeechStatus.className = 'speech-live-tag tag-listening';
        }
      }

      const isAssistantSpeaking = window.speechSynthesis && window.speechSynthesis.speaking;
      const isBusy = isAssistantSpeaking || isGenerating;

      // 1. Check for STOP / INTERRUPT command
      if (isStopPhrase(spoken)) {
        triggerVoiceInterruption(spoken);
        return;
      }

      // 2. Barge-in detection while assistant is speaking or computing
      if (isBusy && spoken.length > 2) {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        stopSpeakingModulation();
        if (isGenerating) cancelGeneration();
        logActivity('User', 'Barge-In', `Interrupting with new prompt: "${spoken}"`);
        playSciFiTone('interrupt');
        setVoicePipelineState('listening', 'BARGE-IN DETECTED');
      }

      if (chatInput) {
        chatInput.value = spoken;
      }

      // 3. Hands-free auto transmit on final speech or natural pause
      if (final && final.trim()) {
        const finalText = final.trim();
        if (isStopPhrase(finalText)) return;

        setVoicePipelineState('processing', 'COMMAND VERIFIED • DISPATCHING');
        if (userSpeechStatus) {
          userSpeechStatus.textContent = 'DISPATCHED';
          userSpeechStatus.className = 'speech-live-tag tag-processing';
        }

        if (speechDebounceTimer) clearTimeout(speechDebounceTimer);
        speechDebounceTimer = setTimeout(function () {
          if (chatInput && chatInput.value.trim()) {
            const promptToSend = chatInput.value.trim();
            if (!isStopPhrase(promptToSend)) {
              logActivity('User', 'Voice Transmit', promptToSend);
              playSciFiTone('transmit');
              isVoiceTriggered = true;
              sendMessage();
            }
          }
        }, 650);
      }
    };

    rec.onerror = function (event) {
      const err = event.error;
      console.warn('[HUD] SpeechRecognition error:', err);
      logActivity('System', 'Mic Notice', `Speech error: ${err}`);

      if (err === 'not-allowed') {
        isListening = false;
        stopMicListening();
        showVoiceToast('⚠️ Microphone blocked! Click the lock/camera icon in your address bar to Allow microphone.', 'error');
        setVoicePipelineState('idle', 'MIC BLOCKED • ALLOW ACCESS');
      } else if (err === 'service-not-allowed') {
        isListening = false;
        stopMicListening();
        showVoiceToast('⚠️ Speech recognition service blocked. In Brave browser: enable Google Speech in Settings -> Privacy, or open in Chrome/Edge.', 'error');
        setVoicePipelineState('idle', 'SERVICE BLOCKED');
      } else if (err === 'audio-capture') {
        isListening = false;
        stopMicListening();
        showVoiceToast('⚠️ No microphone detected or microphone is in use by another application.', 'error');
        setVoicePipelineState('idle', 'NO MIC FOUND');
      } else if (err === 'network') {
        isListening = false;
        stopMicListening();
        showVoiceToast('⚠️ Speech recognition network timeout. Ensure internet is connected.', 'warning');
        setVoicePipelineState('idle', 'NETWORK TIMEOUT');
      } else if (err === 'no-speech') {
        // Normal silence timeout
      }
    };

    rec.onend = function () {
      if (isListening && isVoiceModeEnabled) {
        try {
          rec.start();
        } catch (e) {
          isListening = false;
          stopMicListening();
        }
      } else {
        stopMicListening();
      }
    };

    return rec;
  }

  function ensureRecognitionForBargeIn() {
    if (!recognition) recognition = initSpeechRecognition();
    if (recognition && !isListening) {
      try {
        isListening = true;
        recognition.start();
        if (btnMic) btnMic.classList.add('listening');
        try { startMicAudioAnalysis(); } catch (e) {}
      } catch (e) {
        // Already active
      }
    }
  }

  function startMicListening() {
    if (!recognition) recognition = initSpeechRecognition();
    if (!recognition) {
      logActivity('System', 'Mic Notice', 'Web Speech Recognition not supported in this browser.');
      showVoiceToast('⚠️ Speech Recognition is not supported by this browser. Please open in Google Chrome or Microsoft Edge.', 'error');
      return;
    }
    const selLang = localStorage.getItem('kiraht_voice_lang') || 'en-IN';
    recognition.lang = selLang;

    if (!isListening) {
      try {
        isListening = true;
        recognition.start();
        playSciFiTone('activate');
      } catch (e) {
        // Already running
      }
    }
  }

  function stopMicListening() {
    isListening = false;
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
    if (btnMic) btnMic.classList.remove('listening');
    try { stopMicAudioAnalysis(); } catch (e) {}
    if (!isGenerating && (!window.speechSynthesis || !window.speechSynthesis.speaking)) {
      setVoicePipelineState('idle');
    }
    if (chatInput) chatInput.placeholder = 'Type a message, system command, QR link, calculation, or question...';
    if (userSpeechStatus) {
      userSpeechStatus.textContent = 'IDLE';
      userSpeechStatus.className = 'speech-live-tag';
    }
    if (!isGenerating) setReactorState('idle');
  }

  function toggleMicListening() {
    if (isListening) {
      stopMicListening();
      logActivity('User', 'Voice Paused', 'Microphone deactivated');
    } else {
      startMicListening();
    }
  }

  if (btnMic) {
    btnMic.addEventListener('click', toggleMicListening);
  }

  if (btnCentralMic) {
    btnCentralMic.addEventListener('click', toggleMicListening);
  }

  if (btnCentralInterrupt) {
    btnCentralInterrupt.addEventListener('click', function () {
      triggerVoiceInterruption('Manual button halt');
    });
  }

  const btnVoiceTest = document.getElementById('btn-voice-test');
  if (btnVoiceTest) {
    btnVoiceTest.addEventListener('click', function () {
      showVoiceToast('🔊 Running Audio Test: Speaking diagnostic phrase...', 'info');
      speakAloud('KIRAHT AI voice engine is online and operational, Sir.');
      if (!isListening) {
        startMicListening();
        setTimeout(() => {
          if (!isVoiceModeEnabled) stopMicListening();
        }, 5000);
      }
    });
  }

  const voiceLangSelect = document.getElementById('voice-lang-select');
  if (voiceLangSelect) {
    const savedLang = localStorage.getItem('kiraht_voice_lang') || 'en-IN';
    voiceLangSelect.value = savedLang;
    voiceLangSelect.addEventListener('change', function () {
      const newLang = this.value;
      localStorage.setItem('kiraht_voice_lang', newLang);
      if (recognition) {
        recognition.lang = newLang;
      }
      showVoiceToast(`🌐 Voice Recognition language updated to ${newLang}`, 'success');
      logActivity('User', 'Voice Config', `Language set to ${newLang}`);
    });
  }

  if (btnReturnChat) {
    btnReturnChat.addEventListener('click', function () {
      setHudMode('chat', false);
    });
  }

  if (tabBtnTranscript) {
    tabBtnTranscript.addEventListener('click', function () {
      switchRightTab('transcript');
    });
  }

  if (tabBtnActions) {
    tabBtnActions.addEventListener('click', function () {
      switchRightTab('actions');
    });
  }

  // Large Tactical Quick Action Tiles
  document.querySelectorAll('.tactical-action-tile').forEach(function (tile) {
    tile.addEventListener('click', function () {
      const action = this.getAttribute('data-action');
      if (!action) return;

      if (action === 'clear_chat') {
        if (confirm('Start fresh screen session, Sir? (Your chat_history.json will stay completely safe)')) {
          logActivity('User', 'Fresh Screen', 'Clearing active viewport');
          handleChatCleared();
        }
        return;
      }

      if (action === 'load_history') {
        displayLoadedHistory();
        return;
      }

      logActivity('User', 'Action Trigger', action.replace(/_/g, ' ').toUpperCase());
      sendWebSocket({ type: 'quick_action', action: action });
    });
  });

  // Suggestion Chips
  document.querySelectorAll('.chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      const cmd = this.getAttribute('data-cmd');
      if (cmd && chatInput) {
        logActivity('User', 'Suggestion', cmd);
        chatInput.value = cmd;
        sendMessage();
      }
    });
  });

  // =========================================================================
  // 8. HELPERS & FORMATTING
  // =========================================================================
  function updateStatus(state, detail) {
    if (statusState) {
      statusState.textContent = state || 'READY';
      if (state === 'PROCESSING' || state === 'SEARCHING' || state === 'USING TOOL') {
        statusState.style.color = 'var(--accent-amber)';
      } else {
        statusState.style.color = 'var(--accent-cyan)';
      }
    }
    if (statusDetail) {
      statusDetail.textContent = detail ? `— ${detail}` : '';
    }

    // Synchronize Voice Pipeline State with backend
    if (state === 'PROCESSING' || state === 'SEARCHING' || state === 'USING TOOL') {
      setVoicePipelineState('processing', detail ? `${state}: ${detail}` : 'SYNAPSE COMPUTING...');
    } else if (state === 'READY') {
      if (!isListening && (!window.speechSynthesis || !window.speechSynthesis.speaking)) {
        setVoicePipelineState('idle', 'STANDBY • READY');
      }
    }

    // 3D Arc Reactor dynamic speed controller
    if (reactorCore) {
      if (state === 'PROCESSING' || state === 'SEARCHING' || state === 'USING TOOL' || state === 'RESPONDING') {
        reactorCore.classList.add('active-pulse');
      } else {
        reactorCore.classList.remove('active-pulse');
      }
    }
  }

  function scrollToBottom() {
    if (chatViewport) {
      chatViewport.scrollTop = chatViewport.scrollHeight;
    }
  }

  function getCurrentTime(withSeconds = false) {
    const now = new Date();
    return now.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: withSeconds ? '2-digit' : undefined,
    });
  }

  function jsonParseSafe(str) {
    try {
      return JSON.parse(str);
    } catch (e) {
      return null;
    }
  }

  function formatMarkdown(raw) {
    if (!raw) return '';
    let text = escapeHtml(raw);

    // 1. Tactical QR Code Preview Card: ![QR Code](url)
    text = text.replace(/!\[(?:QR Code|QR)\]\(([^)]+)\)/gi, function (match, url) {
      return `
        <div class="qr-preview-card">
          <div class="qr-title"><span>📱</span> TACTICAL QR CODE</div>
          <div class="qr-img-wrap">
            <img src="${url}" class="qr-img" alt="QR Code">
          </div>
          <div class="qr-action-row">
            <a href="${url}" target="_blank" class="qr-action-btn">⤢ Full View</a>
            <a href="${url}" download="kiraht_qr.png" class="qr-action-btn">⬇ Download</a>
          </div>
        </div>
      `;
    });

    // 2. Screenshot Previews: ![Screenshot](url)
    text = text.replace(/!\[Screenshot\]\(([^)]+)\)/gi, function (match, url) {
      return `<img src="${url}" class="chat-preview-img" alt="Screenshot" onclick="window.open('${url}', '_blank')">`;
    });

    // 3. Code blocks: ```language ... ```
    text = text.replace(/```([a-zA-Z0-9_\-\.]*)\n([\s\S]*?)```/g, function (match, lang, code) {
      return `<pre class="code-block"><div class="code-header">${lang || 'code'}</div><code>${code.trim()}</code></pre>`;
    });

    // 4. Inline code: `code`
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // 5. Bold: **text**
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 6. Italic: *text*
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 7. General Markdown Images: ![alt](url)
    text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" class="chat-preview-img" alt="$1" onclick="window.open(\'$2\', \'_blank\')">');

    // 8. Line breaks
    text = text.replace(/\n/g, '<br>');

    return text;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Live HUD Clock Ticker
  setInterval(function () {
    if (hudClock) {
      hudClock.textContent = getCurrentTime(true);
    }
  }, 1000);

  // =========================================================================
  // 6. RESIZE & COLLAPSE CONTROLLER FOR SIDEBARS & HALF-SCREEN
  // =========================================================================
  function initPanelResizersAndCollapsing() {
    const hudMain = document.getElementById('hud-main');
    const telemetryPanel = document.getElementById('telemetry-panel');
    const actionsPanel = document.getElementById('actions-panel');
    const resizerLeft = document.getElementById('resizer-left');
    const resizerRight = document.getElementById('resizer-right');
    const btnCollapseTelemetry = document.getElementById('btn-collapse-telemetry');
    const btnCollapseActions = document.getElementById('btn-collapse-actions');
    const toggleTelemetryBtn = document.getElementById('toggle-telemetry-btn');
    const toggleActionsBtn = document.getElementById('toggle-actions-btn');

    if (!hudMain) return;

    // Restore saved custom panel widths if any
    const savedTelemWidth = localStorage.getItem('kiraht_telemetry_width');
    if (savedTelemWidth) {
      hudMain.style.setProperty('--telemetry-width', savedTelemWidth + 'px');
    }
    const savedActionsWidth = localStorage.getItem('kiraht_actions_width');
    if (savedActionsWidth) {
      hudMain.style.setProperty('--actions-width', savedActionsWidth + 'px');
    }

    // Toggle Telemetry Panel
    function toggleTelemetry(forceState) {
      if (!telemetryPanel) return;
      const isCurrentlyCollapsed = telemetryPanel.classList.contains('collapsed');
      const targetCollapsed = forceState !== undefined ? !forceState : !isCurrentlyCollapsed;

      if (!targetCollapsed) {
        telemetryPanel.classList.remove('collapsed');
        if (btnCollapseTelemetry) {
          btnCollapseTelemetry.textContent = '◀';
          btnCollapseTelemetry.title = 'Collapse Telemetry (Alt+T)';
        }
        if (toggleTelemetryBtn) toggleTelemetryBtn.classList.add('active');
        if (resizerLeft) resizerLeft.style.display = '';
      } else {
        telemetryPanel.classList.add('collapsed');
        if (btnCollapseTelemetry) {
          btnCollapseTelemetry.textContent = '▶';
          btnCollapseTelemetry.title = 'Expand Telemetry (Alt+T)';
        }
        if (toggleTelemetryBtn) toggleTelemetryBtn.classList.remove('active');
        if (resizerLeft) resizerLeft.style.display = 'none';
      }
    }

    // Toggle Quick Actions Panel
    function toggleActions(forceState) {
      if (!actionsPanel) return;
      const isCurrentlyCollapsed = actionsPanel.classList.contains('collapsed');
      const targetCollapsed = forceState !== undefined ? !forceState : !isCurrentlyCollapsed;

      if (!targetCollapsed) {
        actionsPanel.classList.remove('collapsed');
        if (btnCollapseActions) {
          btnCollapseActions.textContent = '▶';
          btnCollapseActions.title = 'Collapse Quick Actions (Alt+Q)';
        }
        if (toggleActionsBtn) toggleActionsBtn.classList.add('active');
        if (resizerRight) resizerRight.classList.remove('hidden-resizer');
      } else {
        actionsPanel.classList.add('collapsed');
        if (btnCollapseActions) {
          btnCollapseActions.textContent = '◀';
          btnCollapseActions.title = 'Expand Quick Actions (Alt+Q)';
        }
        if (toggleActionsBtn) toggleActionsBtn.classList.remove('active');
        if (resizerRight) resizerRight.classList.add('hidden-resizer');
      }
    }

    if (btnCollapseTelemetry) {
      btnCollapseTelemetry.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleTelemetry();
      });
    }
    if (toggleTelemetryBtn) {
      toggleTelemetryBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleTelemetry();
      });
    }
    if (btnCollapseActions) {
      btnCollapseActions.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleActions();
      });
    }
    if (toggleActionsBtn) {
      toggleActionsBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleActions();
      });
    }

    // Shortcuts Modal Controls (F1 to toggle, Esc or click outside to hide)
    function showShortcutsModal() {
      if (shortcutsModal) shortcutsModal.style.display = 'flex';
    }

    function hideShortcutsModal() {
      if (shortcutsModal) shortcutsModal.style.display = 'none';
    }

    function toggleShortcutsModal() {
      if (!shortcutsModal) return;
      if (shortcutsModal.style.display === 'flex') {
        hideShortcutsModal();
      } else {
        showShortcutsModal();
      }
    }

    if (btnShortcutsModal) {
      btnShortcutsModal.addEventListener('click', toggleShortcutsModal);
    }
    if (btnCloseShortcuts) {
      btnCloseShortcuts.addEventListener('click', hideShortcutsModal);
    }
    if (shortcutsModal) {
      shortcutsModal.addEventListener('click', function (e) {
        if (e.target === shortcutsModal) {
          hideShortcutsModal();
        }
      });
    }

    // Comprehensive Keyboard Shortcuts: F1, Esc, Ctrl+K, Ctrl+Shift+S, Ctrl+L, Alt+1..5, Alt+M, Alt+T, Alt+Q
    window.addEventListener('keydown', function (e) {
      // 1. F1: Toggle Shortcuts Modal
      if (e.key === 'F1') {
        e.preventDefault();
        toggleShortcutsModal();
        return;
      }

      // 2. Esc: Close modal if open, cancel speech/generation, or blur chat input
      if (e.key === 'Escape') {
        if (shortcutsModal && shortcutsModal.style.display === 'flex') {
          e.preventDefault();
          hideShortcutsModal();
          return;
        }
        if (isGenerating || (window.speechSynthesis && window.speechSynthesis.speaking)) {
          e.preventDefault();
          triggerVoiceInterruption('Escape key');
          return;
        }
        if (chatInput && document.activeElement === chatInput) {
          chatInput.blur();
          return;
        }
      }

      // 3. Ctrl + K: Quick Focus Chat Input
      if (e.ctrlKey && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        if (chatInput) {
          chatInput.focus();
          chatInput.select();
        }
        return;
      }

      // 4. Ctrl + Shift + S: Instant Screenshot
      if (e.ctrlKey && e.shiftKey && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        logActivity('User', 'Shortcut 📸', 'Instant Screenshot Capture');
        sendWebSocket({ type: 'quick_action', action: 'screenshot' });
        return;
      }

      // 5. Ctrl + L: Fresh Screen View (Safe: Never deletes chat_history.json)
      if (e.ctrlKey && (e.key === 'l' || e.key === 'L')) {
        e.preventDefault();
        if (confirm('Start fresh screen session, Sir? (chat_history.json stays completely safe)')) {
          logActivity('User', 'Fresh Screen', 'Clearing active viewport');
          handleChatCleared();
        }
        return;
      }

      // 6. Alt + 1 .. Alt + 5: Quick Action Tiles
      if (e.altKey && !e.ctrlKey && !e.shiftKey) {
        const quickMap = {
          '1': 'system_status',
          '2': 'open_chrome',
          '3': 'open_vscode',
          '4': 'open_task_manager',
          '5': 'screenshot',
        };
        if (quickMap[e.key]) {
          e.preventDefault();
          const act = quickMap[e.key];
          logActivity('User', 'Shortcut Tile', act.replace(/_/g, ' ').toUpperCase());
          sendWebSocket({ type: 'quick_action', action: act });
          return;
        }
      }

      // 7. Alt + M: Cycle Bottom Log Console Height (MIN / MID / MAX)
      if (e.altKey && (e.key === 'm' || e.key === 'M')) {
        e.preventDefault();
        const minBtn = document.getElementById('btn-log-min');
        const midBtn = document.getElementById('btn-log-mid');
        const maxBtn = document.getElementById('btn-log-max');
        if (midBtn && midBtn.classList.contains('active')) {
          if (maxBtn) maxBtn.click();
        } else if (maxBtn && maxBtn.classList.contains('active')) {
          if (minBtn) minBtn.click();
        } else {
          if (midBtn) midBtn.click();
        }
        return;
      }

      // 8. Alt + H (Load History), Alt + T (Telemetry), Alt + Q (Actions), Alt + V (Voice Mic), Alt + S (Voice Mode)
      if (e.altKey && (e.key === 'h' || e.key === 'H')) {
        e.preventDefault();
        displayLoadedHistory();
      } else if (e.altKey && (e.key === 't' || e.key === 'T')) {
        e.preventDefault();
        toggleTelemetry();
      } else if (e.altKey && (e.key === 'q' || e.key === 'Q')) {
        e.preventDefault();
        toggleActions();
      } else if (e.altKey && (e.key === 'v' || e.key === 'V')) {
        e.preventDefault();
        toggleMicListening();
      } else if (e.altKey && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        toggleVoiceMode();
      }
    });

    // 1. Drag Resizer: Left (Telemetry)
    if (resizerLeft) {
      let isDraggingLeft = false;

      resizerLeft.addEventListener('mousedown', function (e) {
        isDraggingLeft = true;
        resizerLeft.classList.add('is-dragging');
        if (hudMain) hudMain.classList.add('is-resizing');
        if (telemetryPanel) telemetryPanel.style.transition = 'none';
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
      });

      resizerLeft.addEventListener('dblclick', function () {
        hudMain.style.setProperty('--telemetry-width', '215px');
        localStorage.removeItem('kiraht_telemetry_width');
      });

      window.addEventListener('mousemove', function (e) {
        if (!isDraggingLeft) return;
        const mainRect = hudMain.getBoundingClientRect();
        let newWidth = e.clientX - mainRect.left;
        newWidth = Math.max(160, Math.min(380, newWidth));
        hudMain.style.setProperty('--telemetry-width', newWidth + 'px');
      });

      window.addEventListener('mouseup', function () {
        if (isDraggingLeft) {
          isDraggingLeft = false;
          resizerLeft.classList.remove('is-dragging');
          if (hudMain) hudMain.classList.remove('is-resizing');
          if (telemetryPanel) telemetryPanel.style.transition = '';
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          const currentWidth = parseInt(getComputedStyle(hudMain).getPropertyValue('--telemetry-width'), 10);
          if (currentWidth) localStorage.setItem('kiraht_telemetry_width', currentWidth);
        }
      });
    }

    // 2. Drag Resizer: Right (Quick Actions)
    if (resizerRight) {
      let isDraggingRight = false;

      resizerRight.addEventListener('mousedown', function (e) {
        isDraggingRight = true;
        resizerRight.classList.add('is-dragging');
        if (hudMain) hudMain.classList.add('is-resizing');
        if (actionsPanel) actionsPanel.style.transition = 'none';
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
      });

      resizerRight.addEventListener('dblclick', function () {
        hudMain.style.setProperty('--actions-width', '220px');
        localStorage.removeItem('kiraht_actions_width');
      });

      window.addEventListener('mousemove', function (e) {
        if (!isDraggingRight) return;
        const mainRect = hudMain.getBoundingClientRect();
        let newWidth = mainRect.right - e.clientX;
        newWidth = Math.max(170, Math.min(380, newWidth));
        hudMain.style.setProperty('--actions-width', newWidth + 'px');
      });

      window.addEventListener('mouseup', function () {
        if (isDraggingRight) {
          isDraggingRight = false;
          resizerRight.classList.remove('is-dragging');
          if (hudMain) hudMain.classList.remove('is-resizing');
          if (actionsPanel) actionsPanel.style.transition = '';
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          const currentWidth = parseInt(getComputedStyle(hudMain).getPropertyValue('--actions-width'), 10);
          if (currentWidth) localStorage.setItem('kiraht_actions_width', currentWidth);
        }
      });
    }

    // 3. Drag Resizer: Bottom (Activity Telemetry Footer Console)
    const resizerBottom = document.getElementById('resizer-bottom');
    const hudContainer = document.querySelector('.hud-container');
    const btnLogClear = document.getElementById('btn-log-clear');
    const btnLogMin = document.getElementById('btn-log-min');
    const btnLogMid = document.getElementById('btn-log-mid');
    const btnLogMax = document.getElementById('btn-log-max');

    function updateFooterPresetButtons(height) {
      if (!btnLogMin || !btnLogMid || !btnLogMax) return;
      btnLogMin.classList.remove('active');
      btnLogMid.classList.remove('active');
      btnLogMax.classList.remove('active');
      if (height <= 85) {
        btnLogMin.classList.add('active');
      } else if (height <= 180) {
        btnLogMid.classList.add('active');
      } else {
        btnLogMax.classList.add('active');
      }
    }

    function setFooterHeight(heightPx, saveToStorage = true) {
      const clamped = Math.max(55, Math.min(420, heightPx));
      if (hudContainer) {
        hudContainer.style.setProperty('--footer-height', clamped + 'px');
      }
      if (saveToStorage) {
        localStorage.setItem('kiraht_footer_height', clamped);
      }
      updateFooterPresetButtons(clamped);
    }

    // Restore saved custom footer height if any
    const savedFooterHeight = localStorage.getItem('kiraht_footer_height');
    if (savedFooterHeight && hudContainer) {
      setFooterHeight(parseInt(savedFooterHeight, 10), false);
    } else {
      setFooterHeight(130, false);
    }

    if (btnLogClear) {
      btnLogClear.addEventListener('click', function () {
        if (activityLogStream) {
          activityLogStream.innerHTML = '';
          logActivity('System', 'Log Cleared', 'Console reset by user');
        }
      });
    }

    if (btnLogMin) {
      btnLogMin.addEventListener('click', function () {
        setFooterHeight(65);
      });
    }

    if (btnLogMid) {
      btnLogMid.addEventListener('click', function () {
        setFooterHeight(130);
      });
    }

    if (btnLogMax) {
      btnLogMax.addEventListener('click', function () {
        setFooterHeight(240);
      });
    }

    if (resizerBottom) {
      let isDraggingBottom = false;
      const hudFooter = document.querySelector('.hud-footer');

      resizerBottom.addEventListener('mousedown', function (e) {
        isDraggingBottom = true;
        resizerBottom.classList.add('is-dragging');
        if (hudFooter) hudFooter.classList.add('is-resizing');
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
      });

      resizerBottom.addEventListener('dblclick', function () {
        setFooterHeight(130);
        localStorage.removeItem('kiraht_footer_height');
      });

      window.addEventListener('mousemove', function (e) {
        if (!isDraggingBottom) return;
        const containerRect = hudContainer ? hudContainer.getBoundingClientRect() : document.body.getBoundingClientRect();
        const newHeight = containerRect.bottom - e.clientY;
        setFooterHeight(newHeight, false);
      });

      window.addEventListener('mouseup', function () {
        if (isDraggingBottom) {
          isDraggingBottom = false;
          resizerBottom.classList.remove('is-dragging');
          if (hudFooter) hudFooter.classList.remove('is-resizing');
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          const currentHeight = parseInt(getComputedStyle(hudContainer).getPropertyValue('--footer-height'), 10) || 130;
          localStorage.setItem('kiraht_footer_height', currentHeight);
          updateFooterPresetButtons(currentHeight);
        }
      });
    }
  }

  // Initialize Web HUD on load
  window.addEventListener('DOMContentLoaded', function () {
    if (hudClock) hudClock.textContent = getCurrentTime(true);
    fetch('/api/telemetry')
      .then(function (r) { return r.json(); })
      .then(function (data) { updateTelemetry(data); })
      .catch(function () {});

    initWebSocket();
    initPanelResizersAndCollapsing();

    // Restore Saved HUD Mode (Chat vs Voice Mode)
    if (currentHudMode === 'voice') {
      setHudMode('voice', false);
    } else {
      setHudMode('chat', false);
    }

    if (reactorCore) {
      reactorCore.classList.remove('boot-spin-in');
      void reactorCore.offsetWidth; // Force CSS reflow
      reactorCore.classList.add('boot-spin-in');
    }
  });
})();

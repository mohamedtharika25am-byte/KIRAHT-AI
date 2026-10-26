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
  let generationWatchdogTimer = null;
  let isUserScrolledUp = false;
  let historyOffset = 0;
  const HISTORY_BATCH_SIZE = 50;
  let isVoiceAutoSendEnabled = false;
  let activeVoiceLang = localStorage.getItem('kiraht_voice_lang') || 'en-IN';

  // DOM Elements - Core & Navigation
  const chatViewport = document.getElementById('chat-viewport');
  const chatInput = document.getElementById('chat-input');
  const btnSend = document.getElementById('btn-send');
  const btnClearChat = document.getElementById('btn-clear-chat');
  const btnScrollBottom = document.getElementById('btn-scroll-bottom');
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

      case 'reminder_alert':
        renderReminderChatCard(packet.reminder);
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
        appendMessageCard('assistant', `⚠️ **System Diagnostic Notice**:\n${packet.error || 'The model was unable to complete the request. Systems remain standing by.'}`, getCurrentTime(), { engine: 'error', source_label: 'DIAGNOSTIC NOTICE' });
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

    // Synchronize backend session start timestamp for smooth, non-flickering uptime
    if (data.uptime && data.uptime.start_timestamp) {
      serverSessionStartTs = data.uptime.start_timestamp * 1000;
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

  function createUserAvatarElement() {
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    const userImg = document.createElement('img');
    userImg.src = '/static/img/user_avatar.jpg?v=2.2';
    userImg.className = 'message-avatar-img user-avatar-img';
    userImg.alt = 'User';
    userImg.onerror = function () {
      this.style.display = 'none';
      if (!avatar.querySelector('.avatar-fallback-user')) {
        avatar.innerHTML = '<span class="avatar-fallback-user">👤</span>';
      }
    };
    avatar.appendChild(userImg);
    return avatar;
  }

  function createAssistantAvatarElement() {
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    const avatarImg = document.createElement('img');
    avatarImg.src = '/static/img/kiraht_ai_logo.png?v=4.0';
    avatarImg.className = 'message-avatar-img assistant-avatar-img';
    avatarImg.alt = 'KIRAHT';
    avatar.appendChild(avatarImg);
    return avatar;
  }

  function updateHistoryButtonBadge(count) {
    const navCountEl = document.getElementById('nav-history-count');
    const tileDescEl = document.getElementById('tile-history-desc');
    const collapseBtn = document.getElementById('btn-collapse-history');
    const totalCount = (cachedChatHistory && cachedChatHistory.length) ? cachedChatHistory.length : (count || 0);

    if (navCountEl) {
      if (totalCount > 0) {
        navCountEl.textContent = totalCount;
        navCountEl.style.display = 'inline-block';
      } else {
        navCountEl.style.display = 'none';
      }
    }
    // Only display collapse button when history batches have actually been loaded on screen
    if (collapseBtn) {
      collapseBtn.style.display = historyOffset > 0 ? 'inline-block' : 'none';
    }
    if (tileDescEl) {
      tileDescEl.textContent = totalCount > 0 ? `${totalCount} past logs saved` : 'View past conversations';
    }
  }

  function displayLoadedHistory() {
    if (!cachedChatHistory || cachedChatHistory.length === 0) {
      fetch('/api/history?limit=500&offset=0')
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (Array.isArray(data) && data.length > 0) {
            cachedChatHistory = data;
            loadNextHistoryBatch();
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

    loadNextHistoryBatch();
  }

  function collapseHistoryBatch() {
    if (!chatViewport) return;
    const batchGroups = chatViewport.querySelectorAll('.history-batch-group');
    if (batchGroups.length === 0) return;

    // Remove the oldest rendered batch group
    const oldestGroup = batchGroups[0];
    if (oldestGroup && oldestGroup.parentNode) {
      oldestGroup.parentNode.removeChild(oldestGroup);
    }

    historyOffset = Math.max(0, historyOffset - HISTORY_BATCH_SIZE);
    updateHistoryButtonBadge(historyOffset);

    const navText = document.getElementById('nav-history-text');
    const collapseBtn = document.getElementById('btn-collapse-history');
    if (historyOffset === 0) {
      if (navText) navText.textContent = '+50 HISTORY';
      if (collapseBtn) collapseBtn.style.display = 'none';
    } else {
      if (navText) navText.textContent = `+50 HISTORY`;
      if (collapseBtn) collapseBtn.style.display = 'inline-block';
    }
    logActivity('System', 'History Collapsed', `Collapsed 50 messages. Active history on screen: ${historyOffset}`);
  }

  function loadNextHistoryBatch() {
    if (!chatViewport || !cachedChatHistory || cachedChatHistory.length === 0) return;
    dismissWelcomeHero();

    const totalAvailable = cachedChatHistory.length;
    if (historyOffset >= totalAvailable) {
      logActivity('History', 'Complete', `All ${totalAvailable} archived messages already rendered`);
      const navText = document.getElementById('nav-history-text');
      const tileTitle = document.getElementById('tile-history-title');
      if (navText) navText.textContent = `ALL HISTORY (${totalAvailable})`;
      if (tileTitle) tileTitle.textContent = `ALL HISTORY (${totalAvailable})`;
      return;
    }

    // Slice next 50 messages backward (e.g. latest 50, then 50-100, etc.)
    const startIndex = Math.max(0, totalAvailable - historyOffset - HISTORY_BATCH_SIZE);
    const endIndex = totalAvailable - historyOffset;
    const batch = cachedChatHistory.slice(startIndex, endIndex);
    historyOffset += batch.length;

    // Create a container for this batch
    const batchContainer = document.createElement('div');
    batchContainer.className = 'history-batch-group';

    const batchDivider = document.createElement('div');
    batchDivider.className = 'history-divider';
    batchDivider.innerHTML = `<span>📜 ARCHIVED LOGS [${historyOffset}/${totalAvailable}] 📜</span>`;
    batchContainer.appendChild(batchDivider);

    batch.forEach(function (msg) {
      const isUser = msg.role === 'user';
      const card = document.createElement('div');
      card.className = `message-card ${isUser ? 'user-card' : 'assistant-card'}`;

      const avatar = isUser ? createUserAvatarElement() : createAssistantAvatarElement();

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
        const badge = createEngineSourceBadge(msg.meta);
        headerLeft.appendChild(badge);
      }

      const time = document.createElement('span');
      time.className = 'message-timestamp';
      time.textContent = msg.timestamp || 'Archived';
      header.appendChild(headerLeft);
      header.appendChild(time);

      const contentEl = document.createElement('div');
      contentEl.className = 'message-content';
      contentEl.innerHTML = formatMarkdown(msg.content);

      body.appendChild(header);
      body.appendChild(contentEl);
      card.appendChild(avatar);
      card.appendChild(body);
      batchContainer.appendChild(card);
    });

    // Prepend batch to top of chatViewport smoothly
    chatViewport.insertBefore(batchContainer, chatViewport.firstChild);

    // Update buttons
    const navText = document.getElementById('nav-history-text');
    const btnNav = document.getElementById('btn-load-history');
    const tileTitle = document.getElementById('tile-history-title');
    const tileDesc = document.getElementById('tile-history-desc');

    const collapseBtn = document.getElementById('btn-collapse-history');
    if (collapseBtn) collapseBtn.style.display = 'inline-block';

    if (historyOffset >= totalAvailable) {
      if (navText) navText.textContent = `ALL (${totalAvailable})`;
      if (tileTitle) tileTitle.textContent = `ALL (${totalAvailable})`;
      if (tileDesc) tileDesc.textContent = `All ${totalAvailable} logs loaded`;
    } else {
      if (navText) navText.textContent = `+50 HISTORY`;
      if (tileTitle) tileTitle.textContent = `+50 HISTORY`;
      if (tileDesc) tileDesc.textContent = `${historyOffset} of ${totalAvailable} loaded`;
    }

    logActivity('System', 'History Loaded', `Rendered batch of ${batch.length} messages (${historyOffset}/${totalAvailable})`);
  }

  function renderSingleMessage(role, content, timestamp, meta) {
    dismissWelcomeHero();
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

    const avatar = isUser ? createUserAvatarElement() : createAssistantAvatarElement();

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

  function renderReminderChatCard(reminder) {
    if (!chatViewport || !reminder) return;
    dismissWelcomeHero();

    const card = document.createElement('div');
    card.className = 'message-card assistant-card reminder-card';
    card.setAttribute('data-reminder-id', reminder.id);

    const avatar = createAssistantAvatarElement();

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

    const remBadge = document.createElement('span');
    remBadge.className = 'reminder-header-badge';
    remBadge.innerHTML = `<span>${reminder.icon || '🕌'}</span> ${reminder.category === 'prayer' ? 'PRAYER ALERT' : 'EVENT ALERT'}`;
    headerLeft.appendChild(remBadge);

    const time = document.createElement('span');
    time.className = 'message-timestamp';
    time.textContent = getCurrentTime();

    header.appendChild(headerLeft);
    header.appendChild(time);

    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.innerHTML = `
      <div style="font-weight: 800; font-size: 13px; color: var(--accent-cyan); margin-bottom: 4px;">
        ${escapeHtml(reminder.title)}
      </div>
      <div style="font-size: 12px; color: var(--text-primary); margin-bottom: 6px;">
        ${escapeHtml(reminder.message)}
      </div>
      <div style="font-family: var(--font-mono); font-size: 11px; color: var(--accent-green); margin-bottom: 8px;">
        ⏱️ Scheduled Time: <strong>${escapeHtml(reminder.time || '')}</strong>
      </div>
    `;

    // Interactive Action Row: Accept & Deny/Snooze
    const actionsRow = document.createElement('div');
    actionsRow.className = 'reminder-actions-row';

    const btnAccept = document.createElement('button');
    btnAccept.className = 'btn-reminder-action btn-reminder-accept';
    btnAccept.type = 'button';
    btnAccept.innerHTML = `<span>✅</span> ACCEPT`;

    const btnDeny = document.createElement('button');
    btnDeny.className = 'btn-reminder-action btn-reminder-deny';
    btnDeny.type = 'button';
    btnDeny.innerHTML = `<span>⏰</span> SNOOZE 10M`;

    btnAccept.onclick = function () {
      handleReminderActionClick(reminder.id, 'accept', card, btnAccept, btnDeny);
    };
    btnDeny.onclick = function () {
      handleReminderActionClick(reminder.id, 'deny', card, btnAccept, btnDeny);
    };

    actionsRow.appendChild(btnAccept);
    actionsRow.appendChild(btnDeny);
    contentEl.appendChild(actionsRow);

    body.appendChild(header);
    body.appendChild(contentEl);

    card.appendChild(avatar);
    card.appendChild(body);

    chatViewport.appendChild(card);
    if (!isUserScrolledUp) {
      scrollToBottom();
    }

    const spokenText = `Sir, reminder for ${reminder.title}. ${reminder.message}`;
    if (typeof speakAloud === 'function') {
      speakAloud(spokenText);
    }
  }

  function handleReminderActionClick(reminderId, action, cardEl, btnAccept, btnDeny) {
    if (btnAccept) btnAccept.disabled = true;
    if (btnDeny) btnDeny.disabled = true;

    if (action === 'accept') {
      if (btnAccept) {
        btnAccept.innerHTML = `<span>✅</span> ACCEPTED`;
        btnAccept.style.background = 'rgba(0, 255, 136, 0.4)';
      }
      if (btnDeny) btnDeny.style.display = 'none';
    } else {
      if (btnDeny) {
        btnDeny.innerHTML = `<span>⏰</span> SNOOZED (10M)`;
        btnDeny.style.background = 'rgba(255, 170, 0, 0.4)';
      }
      if (btnAccept) btnAccept.style.display = 'none';
    }

    sendWebSocket({
      type: 'reminder_action',
      id: reminderId,
      action: action
    });
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
      // Background Tab Throttling Protection: If tab is hidden in background, drain immediately
      if (document.hidden && wordStreamQueue.length > 0) {
        accumulatedStreamText += wordStreamQueue.join('');
        wordStreamQueue = [];
        if (currentStreamingContentEl) {
          try {
            currentStreamingContentEl.innerHTML = formatMarkdown(accumulatedStreamText) + '<span class="typing-cursor"></span>';
          } catch (e) {
            currentStreamingContentEl.textContent = accumulatedStreamText;
          }
          if (!isUserScrolledUp) {
            scrollToBottom();
          }
        }
        if (pendingStreamEnd) {
          clearInterval(wordStreamInterval);
          wordStreamInterval = null;
          finishStream(pendingStreamEnd.fullText, pendingStreamEnd.meta);
          pendingStreamEnd = null;
        }
        return;
      }

      if (wordStreamQueue.length > 0) {
        // Adaptive drain: drain faster if backlog accumulates or if stream has ended
        const drainBatch = pendingStreamEnd
          ? Math.min(wordStreamQueue.length, 6)
          : (wordStreamQueue.length > 25 ? 4 : (wordStreamQueue.length > 10 ? 2 : 1));

        for (let i = 0; i < drainBatch; i++) {
          if (wordStreamQueue.length > 0) {
            accumulatedStreamText += wordStreamQueue.shift();
          }
        }
        if (currentStreamingContentEl) {
          try {
            currentStreamingContentEl.innerHTML = formatMarkdown(accumulatedStreamText) + '<span class="typing-cursor"></span>';
          } catch (fmtErr) {
            currentStreamingContentEl.textContent = accumulatedStreamText;
          }
          if (!isUserScrolledUp) {
            scrollToBottom();
          }
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

  // Handle Tab Switch (Visibility Change) to instantly drain pending streaming queues
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && wordStreamQueue.length > 0) {
      accumulatedStreamText += wordStreamQueue.join('');
      wordStreamQueue = [];
      if (currentStreamingContentEl) {
        try {
          currentStreamingContentEl.innerHTML = formatMarkdown(accumulatedStreamText) + '<span class="typing-cursor"></span>';
        } catch (e) {
          currentStreamingContentEl.textContent = accumulatedStreamText;
        }
        if (!isUserScrolledUp) {
          scrollToBottom();
        }
      }
      if (pendingStreamEnd) {
        if (wordStreamInterval) {
          clearInterval(wordStreamInterval);
          wordStreamInterval = null;
        }
        finishStream(pendingStreamEnd.fullText, pendingStreamEnd.meta);
        pendingStreamEnd = null;
      }
    }
  });

  function handleStreamChunk(chunk) {
    if (!chunk) return;

    // Reset 20-second watchdog timer on every active chunk so active long responses are never cut short
    if (isGenerating && generationWatchdogTimer) {
      clearTimeout(generationWatchdogTimer);
      generationWatchdogTimer = setTimeout(function () {
        if (isGenerating) {
          console.warn('[HUD] Stream chunk 20s watchdog fired - auto recovering controls');
          setGeneratingState(false);
        }
      }, 20000);
    }

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
      dismissWelcomeHero();
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

      // Hard safety timer: guarantee stream finishes and STOP resets within 1.2s max
      setTimeout(function () {
        if (pendingStreamEnd) {
          if (wordStreamInterval) {
            clearInterval(wordStreamInterval);
            wordStreamInterval = null;
          }
          finishStream(pendingStreamEnd.fullText, pendingStreamEnd.meta);
          pendingStreamEnd = null;
        }
      }, 1200);
    }
  }

  function finishStream(fullText, meta) {
    let textToRender = fullText || accumulatedStreamText || '';
    if (!textToRender && !currentStreamingCard) {
      textToRender = 'Sir, the command was processed. Systems remain standing by.';
    }
    try {
      if (!currentStreamingCard && textToRender) {
        if (thinkingCard && thinkingCard.parentNode) {
          thinkingCard.parentNode.removeChild(thinkingCard);
        }
        thinkingCard = null;
        appendMessageCard('assistant', textToRender, getCurrentTime(), meta);
      } else {
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
    } catch (finishErr) {
      console.warn('[HUD] finishStream non-fatal warning:', finishErr);
    } finally {
      currentStreamingCard = null;
      currentStreamingContentEl = null;
      accumulatedStreamText = '';
      wordStreamQueue = [];
      thinkingCard = null;
      setGeneratingState(false);
      if (!isUserScrolledUp) {
        scrollToBottom();
      }
    }
  }

  function getWelcomeGreeting() {
    const hr = new Date().getHours();
    if (hr >= 4 && hr < 12) return 'Good Morning, Sir.';
    if (hr >= 12 && hr < 17) return 'Good Afternoon, Sir.';
    if (hr >= 17 && hr < 22) return 'Good Evening, Sir.';
    return 'Late-Night Tactical Session, Sir.';
  }

  function getWelcomeHeroHtml() {
    const greeting = getWelcomeGreeting();
    const now = new Date();
    const todayStr = `${now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()} • READY`;
    return `
      <div class="tactical-welcome-hero instant-boot" id="tactical-welcome-hero">
        <div class="welcome-header">
          <div class="welcome-badge">
            <span class="welcome-pulse-dot"></span>
            <span class="welcome-badge-text">SYS.MK-VII • TACTICAL AI ONLINE</span>
          </div>
          <div class="welcome-time-tag" id="welcome-live-date">${todayStr}</div>
        </div>

        <div class="welcome-main">
          <div class="welcome-avatar-wrap">
            <img src="/static/img/kiraht_ai_logo.png?v=4.0" class="welcome-avatar-img" alt="KIRAHT Core">
            <div class="welcome-avatar-glow"></div>
          </div>
          <div class="welcome-intro">
            <h2 class="welcome-title" id="welcome-greeting-title">${greeting}</h2>
            <p class="welcome-desc">
              Welcome to <strong class="text-cyan">KIRAHT Tactical AI Command</strong>. Workstation telemetry, neural models, and background automations are fully synchronized. Ready for directives.
            </p>
          </div>
        </div>

        <div class="welcome-readiness-grid">
          <div class="readiness-card">
            <span class="readiness-icon">⚡</span>
            <div class="readiness-info">
              <span class="readiness-label">Core Engine</span>
              <span class="readiness-val text-green">OPERATIONAL</span>
            </div>
          </div>
          <div class="readiness-card">
            <span class="readiness-icon">🧠</span>
            <div class="readiness-info">
              <span class="readiness-label">Neural Model</span>
              <span class="readiness-val text-cyan" id="welcome-active-model">qwen2.5:3b / Gemini</span>
            </div>
          </div>
          <div class="readiness-card">
            <span class="readiness-icon">🛡️</span>
            <div class="readiness-info">
              <span class="readiness-label">System State</span>
              <span class="readiness-val text-green">ARMED &amp; READY</span>
            </div>
          </div>
          <div class="readiness-card">
            <span class="readiness-icon">🎙️</span>
            <div class="readiness-info">
              <span class="readiness-label">Voice Protocol</span>
              <span class="readiness-val text-purple">STANDBY (Alt+V)</span>
            </div>
          </div>
        </div>

        <div class="welcome-actions-wrap">
          <span class="welcome-actions-label">QUICK DIRECTIVES:</span>
          <div class="welcome-chips-container">
            <button class="welcome-chip" type="button" data-prompt="Run full system hardware diagnostics and report status.">
              <span>⚡ System Diagnostics</span>
            </button>
            <button class="welcome-chip" type="button" data-prompt="Search the web for latest AI and technology news today.">
              <span>🌐 Web Intelligence</span>
            </button>
            <button class="welcome-chip" type="button" data-prompt="Help me review and debug the code in my current workspace.">
              <span>💻 Code Assistant</span>
            </button>
            <button class="welcome-chip chip-voice" type="button" id="welcome-chip-voice">
              <span>🎙️ Start Voice Mode</span>
            </button>
            <button class="welcome-chip chip-history" type="button" id="welcome-chip-history">
              <span>📜 Load Chat History</span>
            </button>
            <button class="welcome-chip chip-audio" type="button" id="welcome-chip-audio" title="Play Voice Greeting aloud">
              <span>🔊 Voice Greeting</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  function dismissWelcomeHero() {
    const hero = document.getElementById('tactical-welcome-hero');
    if (!hero || hero.classList.contains('fade-out')) return;
    hero.classList.remove('delayed-boot');
    hero.classList.remove('boot-complete');
    hero.classList.add('fade-out');
    setTimeout(() => {
      if (hero && hero.parentNode) {
        hero.parentNode.removeChild(hero);
      }
    }, 320);
  }

  function triggerSystemDiagnosticsAction() {
    dismissWelcomeHero();
    const nowTime = getCurrentTime();
    appendMessageCard('user', '⚡ Run full system diagnostics', nowTime);
    showThinkingIndicator();
    setGeneratingState(true);

    fetch('/api/quick-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'system_status' })
    })
      .then(r => r.json())
      .then(data => {
        if (thinkingCard && thinkingCard.parentNode) {
          thinkingCard.parentNode.removeChild(thinkingCard);
          thinkingCard = null;
        }
        setGeneratingState(false);
        if (data && data.result) {
          appendMessageCard('assistant', data.result, getCurrentTime(), data.meta);
          scrollToBottom();
        }
      })
      .catch(err => {
        if (thinkingCard && thinkingCard.parentNode) {
          thinkingCard.parentNode.removeChild(thinkingCard);
          thinkingCard = null;
        }
        setGeneratingState(false);
        appendMessageCard('assistant', 'Sir, unable to retrieve diagnostic telemetry at this time.', getCurrentTime());
        scrollToBottom();
      });
  }

  function initWelcomeHero() {
    const welcomeHero = document.getElementById('tactical-welcome-hero');
    if (!welcomeHero) return;

    // Clean up delayed-boot class once the sequenced startup animation completes
    if (welcomeHero.classList.contains('delayed-boot')) {
      setTimeout(() => {
        const hero = document.getElementById('tactical-welcome-hero');
        if (hero && hero.classList.contains('delayed-boot')) {
          hero.classList.remove('delayed-boot');
          hero.classList.add('boot-complete');
        }
      }, 2750);
    }

    const titleEl = document.getElementById('welcome-greeting-title');
    if (titleEl) {
      titleEl.textContent = getWelcomeGreeting();
    }

    const dateEl = document.getElementById('welcome-live-date');
    if (dateEl) {
      const now = new Date();
      dateEl.textContent = `${now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()} • READY`;
    }

    // Quick prompt chips
    const promptChips = welcomeHero.querySelectorAll('.welcome-chip[data-prompt]');
    promptChips.forEach(chip => {
      chip.onclick = function (e) {
        e.preventDefault();
        const promptText = chip.getAttribute('data-prompt');
        if (promptText && promptText.toLowerCase().includes('hardware diagnostics')) {
          triggerSystemDiagnosticsAction();
          return;
        }
        dismissWelcomeHero();
        const input = document.getElementById('chat-input');
        if (input) {
          input.value = promptText;
          const sendBtn = document.getElementById('btn-send');
          if (sendBtn) sendBtn.click();
        }
      };
    });

    // Voice mode chip
    const voiceChip = document.getElementById('welcome-chip-voice');
    if (voiceChip) {
      voiceChip.onclick = function (e) {
        e.preventDefault();
        dismissWelcomeHero();
        const btnVoiceMode = document.getElementById('btn-voice-mode');
        if (btnVoiceMode) btnVoiceMode.click();
      };
    }

    // History chip
    const historyChip = document.getElementById('welcome-chip-history');
    if (historyChip) {
      historyChip.onclick = function (e) {
        e.preventDefault();
        dismissWelcomeHero();
        displayLoadedHistory();
      };
    }

    // Audio greeting chip
    const audioChip = document.getElementById('welcome-chip-audio');
    if (audioChip) {
      audioChip.onclick = function (e) {
        e.preventDefault();
        const greeting = getWelcomeGreeting();
        speakAloud(`${greeting} Welcome to KIRAHT Tactical AI Command. All systems are operational and ready for your directives, Sir.`);
      };
    }
  }

  function handleChatCleared() {
    thinkingCard = null;
    currentStreamingCard = null;
    currentStreamingContentEl = null;
    wordStreamQueue = [];
    accumulatedStreamText = '';
    isHistoryRendered = false;
    historyOffset = 0;
    setGeneratingState(false);

    const navText = document.getElementById('nav-history-text');
    const btnNav = document.getElementById('btn-load-history');
    const tileTitle = document.getElementById('tile-history-title');
    const tileDesc = document.getElementById('tile-history-desc');
    const collapseBtn = document.getElementById('btn-collapse-history');

    if (navText) navText.textContent = '+50 HISTORY';
    if (btnNav) btnNav.classList.remove('active');
    if (tileTitle) tileTitle.textContent = '+50 HISTORY';
    if (tileDesc) tileDesc.textContent = `${cachedChatHistory.length} past logs saved`;
    if (collapseBtn) collapseBtn.style.display = 'none';

    if (chatViewport) {
      chatViewport.innerHTML = getWelcomeHeroHtml();
      initWelcomeHero();
    }
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

    if (generationWatchdogTimer) {
      clearTimeout(generationWatchdogTimer);
      generationWatchdogTimer = null;
    }

    if (isGenerating) {
      btnSend.classList.add('btn-cancel');
      btnSend.setAttribute('title', 'Stop Generating (Esc)');
      btnSend.innerHTML = '<span class="btn-cancel-icon" style="font-size:12px;">■</span> <span class="btn-send-text">STOP</span>';
      if (typeof setReactorState === 'function') setReactorState('thinking');

      // 60-second safety watchdog: Inform user instead of prematurely destroying response
      generationWatchdogTimer = setTimeout(function () {
        if (isGenerating) {
          console.warn('[HUD] Generation latency threshold reached (60s).');
          logActivity('System', 'Engine Latency', 'Neural inference taking longer than usual...');
          if (thinkingCard) {
            const thinkingText = thinkingCard.querySelector('.thinking-text');
            if (thinkingText) {
              thinkingText.textContent = 'Processing prompt... please wait a moment';
            }
          }
        }
      }, 60000);
    } else {
      btnSend.classList.remove('btn-cancel');
      btnSend.setAttribute('title', 'Execute Directive (Enter)');
      btnSend.innerHTML = '<span class="btn-send-icon">▲</span> <span class="btn-send-text">EXECUTE</span>';
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
    dismissWelcomeHero();

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

    // User explicitly entered a message: reset scroll lock and force scroll down to the new message
    isUserScrolledUp = false;
    if (btnScrollBottom) btnScrollBottom.style.display = 'none';
    scrollToBottom(true);

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

    // Auto-expand textarea without jumping messages
    let prevInputHeight = 42;
    chatInput.addEventListener('input', function () {
      this.style.height = '42px';
      const newHeight = Math.min(this.scrollHeight, 120);
      this.style.height = newHeight + 'px';
      const heightDelta = newHeight - prevInputHeight;
      prevInputHeight = newHeight;
      if (chatViewport && isUserScrolledUp && heightDelta !== 0) {
        chatViewport.scrollTop += heightDelta;
      }
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

  // Helper: Switch Right Panel Tab (Transcript removed - keep Actions active)
  function switchRightTab(tabName) {
    if (tabBtnActions) tabBtnActions.classList.add('active');
    if (tabBtnTranscript) tabBtnTranscript.classList.remove('active');
    if (actionTilesGrid) actionTilesGrid.style.display = 'grid';
    if (voiceTranscriptWrapper) voiceTranscriptWrapper.style.display = 'none';
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
      switchRightTab('actions');
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

  // 8. Dual-Engine Speech Recognition (Offline Whisper + Cloud Web Speech)
  let activeSpeechEngine = localStorage.getItem('kiraht_speech_engine') || 'offline';
  let offlineAudioStream = null;
  let offlineAudioContext = null;
  let offlineProcessor = null;
  let offlineAudioChunks = [];
  let isOfflineRecording = false;
  let lastAudioVolumeTime = 0;
  let hasDetectedSpeech = false;

  function encodeWAV(samples, sampleRate) {
    const targetSampleRate = 16000;
    let finalSamples = samples;

    // Resample to 16kHz for Whisper
    if (sampleRate !== targetSampleRate && samples.length > 0) {
      const ratio = sampleRate / targetSampleRate;
      const newLength = Math.round(samples.length / ratio);
      const resampled = new Float32Array(newLength);
      for (let i = 0; i < newLength; i++) {
        const index = Math.min(Math.round(i * ratio), samples.length - 1);
        resampled[i] = samples[index];
      }
      finalSamples = resampled;
    }

    const buffer = new ArrayBuffer(44 + finalSamples.length * 2);
    const view = new DataView(buffer);

    function writeString(view, offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    }

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + finalSamples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, 1, true); // Mono channel
    view.setUint32(24, targetSampleRate, true);
    view.setUint32(28, targetSampleRate * 2, true);
    view.setUint16(32, 2, true); // Block align
    view.setUint16(34, 16, true); // 16 bits per sample
    writeString(view, 36, 'data');
    view.setUint32(40, finalSamples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < finalSamples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, finalSamples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([buffer], { type: 'audio/wav' });
  }

  async function startOfflineMicRecording() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showVoiceToast('⚠️ Microphone access not supported by this browser.', 'error');
        return;
      }

      isOfflineRecording = true;
      isListening = true;
      offlineAudioChunks = [];
      hasDetectedSpeech = false;
      lastAudioVolumeTime = Date.now();

      offlineAudioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      offlineAudioContext = new AudioContextClass();
      if (offlineAudioContext.state === 'suspended') {
        await offlineAudioContext.resume();
      }

      const source = offlineAudioContext.createMediaStreamSource(offlineAudioStream);
      offlineProcessor = offlineAudioContext.createScriptProcessor(4096, 1, 1);

      offlineProcessor.onaudioprocess = function (e) {
        if (!isOfflineRecording) return;
        const inputData = e.inputBuffer.getChannelData(0);
        offlineAudioChunks.push(new Float32Array(inputData));

        // RMS audio volume detection
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);

        if (rms > 0.028) {
          hasDetectedSpeech = true;
          lastAudioVolumeTime = Date.now();
          if (coreStatusText) coreStatusText.textContent = '[VOICE: DETECTING]';
          if (reactorEpicenter) {
            const scale = 1 + Math.min(rms * 2.2, 0.45);
            reactorEpicenter.style.transform = `translate(-50%, -50%) scale(${scale.toFixed(3)})`;
          }
        } else {
          if (coreStatusText && isListening) coreStatusText.textContent = '[VOICE: LISTENING]';
          // Auto-transcribe after user pauses speaking for 1.3 seconds
          const durationSec = (offlineAudioChunks.length * 4096) / offlineAudioContext.sampleRate;
          if (hasDetectedSpeech && durationSec > 1.2 && Date.now() - lastAudioVolumeTime > 1300) {
            stopOfflineMicRecording(true);
          }
        }
      };

      source.connect(offlineProcessor);
      offlineProcessor.connect(offlineAudioContext.destination);

      if (btnMic) btnMic.classList.add('listening');
      if (btnCentralMic) {
        btnCentralMic.classList.add('active');
        if (centralMicText) centralMicText.textContent = 'MIC ACTIVE';
      }
      if (chatInput) chatInput.placeholder = 'KIRAHT Local Whisper Listening... Speak your command';
      setVoicePipelineState('listening', 'OFFLINE WHISPER ACTIVE • LISTENING...');
      if (userSpeechStatus) {
        userSpeechStatus.textContent = 'LISTENING';
        userSpeechStatus.className = 'speech-live-tag tag-listening';
      }
      playSciFiTone('activate');
      logActivity('User', 'Offline Mic', 'Local Whisper recording engaged');

    } catch (err) {
      console.error('[HUD] Offline mic access notice:', err);
      isOfflineRecording = false;
      isListening = false;
      if (btnMic) btnMic.classList.remove('listening');
      if (btnCentralMic) {
        btnCentralMic.classList.remove('active');
        if (centralMicText) centralMicText.textContent = 'MIC STANDBY';
      }
      setVoicePipelineState('idle');
      showVoiceToast('⚠️ Microphone blocked! Click the lock/camera icon in your address bar to Allow microphone.', 'error');
    }
  }

  async function stopOfflineMicRecording(autoTranscribe = true) {
    if (!isOfflineRecording && !isListening) return;
    isOfflineRecording = false;
    isListening = false;

    if (btnMic) btnMic.classList.remove('listening');
    if (btnCentralMic) {
      btnCentralMic.classList.remove('active');
      if (centralMicText) centralMicText.textContent = 'MIC STANDBY';
    }
    if (chatInput) chatInput.placeholder = 'Type a message, system command, QR link, calculation, or question...';

    if (offlineProcessor) {
      try { offlineProcessor.disconnect(); } catch (e) {}
      offlineProcessor = null;
    }
    if (offlineAudioStream) {
      try {
        offlineAudioStream.getTracks().forEach(t => t.stop());
      } catch (e) {}
      offlineAudioStream = null;
    }

    if (!autoTranscribe || offlineAudioChunks.length === 0) {
      setVoicePipelineState('idle');
      if (userSpeechStatus) {
        userSpeechStatus.textContent = 'IDLE';
        userSpeechStatus.className = 'speech-live-tag';
      }
      return;
    }

    // Merge chunks
    const totalLength = offlineAudioChunks.reduce((acc, c) => acc + c.length, 0);
    const sampleRate = offlineAudioContext ? offlineAudioContext.sampleRate : 16000;
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of offlineAudioChunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }
    offlineAudioChunks = [];

    // If recording was less than 0.35s, discard as noise
    if (totalLength < sampleRate * 0.35) {
      setVoicePipelineState('idle');
      if (userSpeechStatus) {
        userSpeechStatus.textContent = 'READY';
        userSpeechStatus.className = 'speech-live-tag';
      }
      return;
    }

    setVoicePipelineState('processing', 'WHISPER TRANSCRIBING AUDIO...');
    if (userSpeechStatus) {
      userSpeechStatus.textContent = 'TRANSCRIBING';
      userSpeechStatus.className = 'speech-live-tag tag-processing';
    }

    const wavBlob = encodeWAV(merged, sampleRate);
    const formData = new FormData();
    formData.append('audio', wavBlob, 'whisper_voice.wav');
    formData.append('lang', localStorage.getItem('kiraht_voice_lang') || 'en');

    try {
      const resp = await fetch('/api/voice/transcribe', {
        method: 'POST',
        body: formData,
      });
      const data = await resp.json();

      if (data.status === 'success' && data.text && data.text.trim()) {
        const spoken = data.text.trim();
        logActivity('User', 'Whisper Transcribed', spoken);

        if (voiceUserText) voiceUserText.textContent = `"${spoken}"`;
        if (chatInput) chatInput.value = spoken;
        if (userSpeechStatus) {
          userSpeechStatus.textContent = 'VERIFIED';
          userSpeechStatus.className = 'speech-live-tag';
        }

        if (isStopPhrase(spoken)) {
          triggerVoiceInterruption(spoken);
          return;
        }

        playSciFiTone('transmit');
        isVoiceTriggered = true;
        setVoicePipelineState('processing', 'COMMAND DISPATCHING');
        sendMessage();

      } else {
        setVoicePipelineState('idle', 'NO SPEECH DETECTED');
        if (userSpeechStatus) {
          userSpeechStatus.textContent = 'READY';
          userSpeechStatus.className = 'speech-live-tag';
        }
      }
    } catch (err) {
      console.error('[HUD] Transcribe error:', err);
      showVoiceToast('⚠️ Offline Whisper error: ' + err.message, 'error');
      setVoicePipelineState('idle');
      if (userSpeechStatus) {
        userSpeechStatus.textContent = 'READY';
        userSpeechStatus.className = 'speech-live-tag';
      }
    }
  }

  // Web Speech Recognition Engine (Cloud Fallback)
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

      isVoiceTriggered = true;

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

      if (isStopPhrase(spoken)) {
        triggerVoiceInterruption(spoken);
        return;
      }

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

      if (final && final.trim()) {
        const finalText = final.trim();
        if (isStopPhrase(finalText)) return;

        if (isVoiceAutoSendEnabled) {
          // Guard: require at least 5 characters to avoid random classroom chatter
          if (finalText.length < 5) {
            logActivity('Voice', 'Filtered', `Ignored short background chatter: "${finalText}"`);
            return;
          }

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
          }, 1200);
        } else {
          // Manual mode: Spoken words are safely loaded into textarea for user review (prevents classroom noise transmission)
          setVoicePipelineState('idle', 'SPEECH RECOGNIZED • PRESS EXECUTE');
          if (userSpeechStatus) {
            userSpeechStatus.textContent = 'READY TO EXECUTE';
            userSpeechStatus.className = 'speech-live-tag tag-listening';
          }
          logActivity('Voice', 'Dictation Loaded', `Spoken text placed into input bar: "${finalText}"`);
        }
      }
    };

    rec.onerror = function (event) {
      const err = event.error;
      console.warn('[HUD] SpeechRecognition error:', err);
      logActivity('System', 'Mic Notice', `Speech error: ${err}`);

      if (err === 'not-allowed') {
        isListening = false;
        stopWebSpeechListening();
        showVoiceToast('⚠️ Microphone blocked! Click the lock/camera icon in your address bar to Allow microphone.', 'error');
        setVoicePipelineState('idle', 'MIC BLOCKED • ALLOW ACCESS');
      } else if (err === 'service-not-allowed' || err === 'network') {
        // Brave browser blocks Google Speech API or offline -> Auto-switch to Local Offline Whisper!
        isListening = false;
        stopWebSpeechListening();
        showVoiceToast('⚠️ Brave/network blocked cloud speech. Switching automatically to 100% Local Offline Whisper...', 'warning');
        activeSpeechEngine = 'offline';
        localStorage.setItem('kiraht_speech_engine', 'offline');
        const engSelect = document.getElementById('voice-engine-select');
        if (engSelect) engSelect.value = 'offline';
        setTimeout(() => {
          startOfflineMicRecording();
        }, 400);
      } else if (err === 'audio-capture') {
        isListening = false;
        stopWebSpeechListening();
        showVoiceToast('⚠️ No microphone detected or microphone is in use by another application.', 'error');
        setVoicePipelineState('idle', 'NO MIC FOUND');
      } else if (err === 'no-speech') {
        // Normal silence timeout
      }
    };

    rec.onend = function () {
      if (isListening && isVoiceModeEnabled && activeSpeechEngine === 'web_speech') {
        try {
          rec.start();
        } catch (e) {
          isListening = false;
          stopWebSpeechListening();
        }
      } else {
        stopWebSpeechListening();
      }
    };

    return rec;
  }

  function ensureRecognitionForBargeIn() {
    if (activeSpeechEngine === 'web_speech') {
      if (!recognition) recognition = initSpeechRecognition();
      if (recognition && !isListening) {
        try {
          isListening = true;
          recognition.start();
          if (btnMic) btnMic.classList.add('listening');
          try { startMicAudioAnalysis(); } catch (e) {}
        } catch (e) {}
      }
    }
  }

  function startWebSpeechListening() {
    if (!recognition) recognition = initSpeechRecognition();
    if (!recognition) {
      logActivity('System', 'Mic Notice', 'Web Speech not supported. Switching to Local Offline Whisper.');
      activeSpeechEngine = 'offline';
      localStorage.setItem('kiraht_speech_engine', 'offline');
      startOfflineMicRecording();
      return;
    }
    const selLang = localStorage.getItem('kiraht_voice_lang') || 'en-IN';
    recognition.lang = selLang;

    if (!isListening) {
      try {
        isListening = true;
        recognition.start();
        playSciFiTone('activate');
      } catch (e) {}
    }
  }

  function stopWebSpeechListening() {
    isListening = false;
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
    if (btnMic) btnMic.classList.remove('listening');
    if (btnCentralMic) {
      btnCentralMic.classList.remove('active');
      if (centralMicText) centralMicText.textContent = 'MIC STANDBY';
    }
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

  function startMicListening() {
    if (activeSpeechEngine === 'offline') {
      startOfflineMicRecording();
    } else {
      startWebSpeechListening();
    }
  }

  function stopMicListening() {
    if (activeSpeechEngine === 'offline') {
      stopOfflineMicRecording(false);
    } else {
      stopWebSpeechListening();
    }
  }

  function toggleMicListening() {
    if (isListening || isOfflineRecording) {
      if (activeSpeechEngine === 'offline') {
        stopOfflineMicRecording(true);
      } else {
        stopWebSpeechListening();
      }
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

  const voiceEngineSelect = document.getElementById('voice-engine-select');
  if (voiceEngineSelect) {
    voiceEngineSelect.value = activeSpeechEngine;
    voiceEngineSelect.addEventListener('change', function () {
      activeSpeechEngine = this.value;
      localStorage.setItem('kiraht_speech_engine', activeSpeechEngine);
      const label = activeSpeechEngine === 'offline' ? '⚡ 100% Local Offline Whisper' : '🌐 Cloud Web Speech';
      showVoiceToast(`Speech Engine set to: ${label}`, 'success');
      logActivity('User', 'Speech Engine', activeSpeechEngine);
      if (isListening || isOfflineRecording) {
        stopMicListening();
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

  // ChatGPT / Claude Style Smart Auto-Scroll & Floating Down-Arrow Button Handler (Triggers only when >= 10 messages scrolled)
  function updateScrollBottomButton() {
    if (!chatViewport || !btnScrollBottom) return;

    const scrollGap = chatViewport.scrollHeight - chatViewport.scrollTop - chatViewport.clientHeight;

    // If near bottom (within 40px), user is reading latest -> resume auto-scroll & hide button
    if (scrollGap <= 40) {
      isUserScrolledUp = false;
      btnScrollBottom.style.display = 'none';
      return;
    }

    // User is scrolled up
    isUserScrolledUp = true;

    // Count how many message cards are below current visible viewport bottom
    const cards = chatViewport.querySelectorAll('.message-card');
    const viewportBottom = chatViewport.scrollTop + chatViewport.clientHeight;
    let cardsBelow = 0;

    for (let i = cards.length - 1; i >= 0; i--) {
      if (cards[i].offsetTop > viewportBottom - 20) {
        cardsBelow++;
      } else {
        break; // Message cards are sequential top-to-bottom
      }
    }

    // Only show if user has scrolled past at least 10 messages (or large scrollGap >= 1200px)
    if (cardsBelow >= 10 || scrollGap >= 1200) {
      btnScrollBottom.style.display = 'flex';
    } else {
      btnScrollBottom.style.display = 'none';
    }
  }

  let lastChatScrollTop = 0;
  if (chatViewport) {
    chatViewport.addEventListener('wheel', function (e) {
      if (e.deltaY < 0) {
        // User scrolled UP: pause auto-scroll immediately so AI response won't drag them down
        isUserScrolledUp = true;
      }
    }, { passive: true });

    chatViewport.addEventListener('touchmove', function () {
      if (chatViewport.scrollTop < lastChatScrollTop) {
        isUserScrolledUp = true;
      }
    }, { passive: true });

    chatViewport.addEventListener('scroll', function () {
      if (chatViewport.scrollTop < lastChatScrollTop - 4) {
        // Detected user actively scrolling up
        isUserScrolledUp = true;
      }
      lastChatScrollTop = chatViewport.scrollTop;
      updateScrollBottomButton();
    }, { passive: true });
  }

  if (btnScrollBottom) {
    btnScrollBottom.addEventListener('click', function () {
      isUserScrolledUp = false;
      if (chatViewport) {
        chatViewport.scrollTo({ top: chatViewport.scrollHeight, behavior: 'smooth' });
      }
      btnScrollBottom.style.display = 'none';
    });
  }

  function scrollToBottom(force = false) {
    if (!chatViewport) return;
    if (isUserScrolledUp && !force) {
      // User is reading previous messages or top of long answer - check threshold
      updateScrollBottomButton();
      return;
    }
    chatViewport.scrollTop = chatViewport.scrollHeight;
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

  // Live HUD Clock, Calendar Date & Uptime Ticker (Monospace Tabular Numerics - No Jitter)
  const hudDate = document.getElementById('hud-date');
  const hudUptimeEl = document.getElementById('hud-uptime');
  let serverSessionStartTs = Date.now();

  function updateLiveClockAndDate() {
    const now = new Date();
    if (hudClock) {
      hudClock.textContent = getCurrentTime(true);
    }
    if (hudDate) {
      const d = String(now.getDate()).padStart(2, '0');
      const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
      const m = months[now.getMonth()];
      const y = now.getFullYear();
      hudDate.textContent = `${d} ${m} ${y}`;
    }
    if (hudUptimeEl) {
      const elapsedSec = Math.max(0, Math.floor((Date.now() - serverSessionStartTs) / 1000));
      const hrs = Math.floor(elapsedSec / 3600);
      const mins = Math.floor((elapsedSec % 3600) / 60);
      const secs = elapsedSec % 60;
      hudUptimeEl.textContent = hrs > 0 
        ? `UP: ${String(hrs).padStart(2, '0')}h ${String(mins).padStart(2, '0')}m`
        : `UP: ${String(mins).padStart(2, '0')}m ${String(secs).padStart(2, '0')}s`;
    }
  }
  setInterval(updateLiveClockAndDate, 1000);
  updateLiveClockAndDate();

  // =========================================================================
  // INTERACTIVE TACTICAL DROPDOWN CALENDAR (FIGMA / PINTEREST HUD STYLE)
  // =========================================================================
  const btnToggleCalendar = document.getElementById('btn-toggle-calendar');
  const hudCalendarPopup = document.getElementById('hud-calendar-popup');
  const calMonthTitle = document.getElementById('cal-month-title');
  const calDaysGrid = document.getElementById('cal-days-grid');
  const calPrevMonth = document.getElementById('cal-prev-month');
  const calNextMonth = document.getElementById('cal-next-month');
  const calBtnToday = document.getElementById('cal-btn-today');
  const calTodayText = document.getElementById('cal-today-text');

  let calViewYear = new Date().getFullYear();
  let calViewMonth = new Date().getMonth();

  const CAL_MONTHS = [
    'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
    'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER'
  ];

  function renderCalendar(year, month) {
    if (!calDaysGrid || !calMonthTitle) return;

    calMonthTitle.textContent = `${CAL_MONTHS[month]} ${year}`;

    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
    const todayDate = today.getDate();

    if (calTodayText) {
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      calTodayText.textContent = `${days[today.getDay()]}, ${today.getDate()} ${months[today.getMonth()]} ${today.getFullYear()}`;
    }

    calDaysGrid.innerHTML = '';

    // First day index (Monday as 0)
    const firstDay = new Date(year, month, 1).getDay();
    const startOffset = (firstDay + 6) % 7;

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();

    // Previous month filler days
    for (let i = startOffset - 1; i >= 0; i--) {
      const cell = document.createElement('div');
      cell.className = 'cal-day-cell other-month';
      cell.textContent = daysInPrevMonth - i;
      calDaysGrid.appendChild(cell);
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      const cell = document.createElement('div');
      cell.className = 'cal-day-cell';
      if (isCurrentMonth && day === todayDate) {
        cell.classList.add('today');
        cell.title = 'Today';
      }
      cell.textContent = day;
      cell.addEventListener('click', function () {
        calDaysGrid.querySelectorAll('.cal-day-cell').forEach(c => c.classList.remove('selected'));
        cell.classList.add('selected');
      });
      calDaysGrid.appendChild(cell);
    }

    // Next month filler days (fill to 35 or 42 grid cells)
    const totalFilled = startOffset + daysInMonth;
    const targetGridCount = totalFilled > 35 ? 42 : 35;
    const nextDaysNeeded = targetGridCount - totalFilled;
    for (let d = 1; d <= nextDaysNeeded; d++) {
      const cell = document.createElement('div');
      cell.className = 'cal-day-cell other-month';
      cell.textContent = d;
      calDaysGrid.appendChild(cell);
    }
  }

  function positionCalendarPopup() {
    if (!hudCalendarPopup) return;
    const anchor = document.getElementById('clock-date-pill') || btnToggleCalendar;
    if (!anchor) return;
    const rect = anchor.getBoundingClientRect();
    const popupWidth = 325;

    hudCalendarPopup.style.position = 'fixed';
    hudCalendarPopup.style.top = `${Math.round(rect.bottom + 8)}px`;

    let rightPos = Math.round(window.innerWidth - rect.right);
    if (rightPos < 12) rightPos = 12;
    if (window.innerWidth - rightPos - popupWidth < 12) {
      rightPos = Math.max(12, window.innerWidth - popupWidth - 12);
    }
    hudCalendarPopup.style.right = `${rightPos}px`;
    hudCalendarPopup.style.left = 'auto';
    hudCalendarPopup.style.zIndex = '999999';
  }

  function toggleCalendar(forceState) {
    if (!hudCalendarPopup) return;
    const isVisible = hudCalendarPopup.style.display !== 'none';
    const targetState = forceState !== undefined ? forceState : !isVisible;

    if (targetState) {
      calViewYear = new Date().getFullYear();
      calViewMonth = new Date().getMonth();
      renderCalendar(calViewYear, calViewMonth);
      loadAndRenderReminders();
      hudCalendarPopup.style.display = 'block';
      positionCalendarPopup();
      if (btnToggleCalendar) btnToggleCalendar.classList.add('active');
    } else {
      hudCalendarPopup.style.display = 'none';
      if (btnToggleCalendar) btnToggleCalendar.classList.remove('active');
    }
  }

  if (btnToggleCalendar) {
    btnToggleCalendar.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleCalendar();
    });
  }

  if (calPrevMonth) {
    calPrevMonth.addEventListener('click', function (e) {
      e.stopPropagation();
      calViewMonth--;
      if (calViewMonth < 0) {
        calViewMonth = 11;
        calViewYear--;
      }
      renderCalendar(calViewYear, calViewMonth);
    });
  }

  if (calNextMonth) {
    calNextMonth.addEventListener('click', function (e) {
      e.stopPropagation();
      calViewMonth++;
      if (calViewMonth > 11) {
        calViewMonth = 0;
        calViewYear++;
      }
      renderCalendar(calViewYear, calViewMonth);
    });
  }

  if (calBtnToday) {
    calBtnToday.addEventListener('click', function (e) {
      e.stopPropagation();
      calViewYear = new Date().getFullYear();
      calViewMonth = new Date().getMonth();
      renderCalendar(calViewYear, calViewMonth);
    });
  }

  // =========================================================================
  // POPUP TABS & PRAYER SCHEDULE / CUSTOM REMINDERS MANAGER
  // =========================================================================
  const tabBtnCalendar = document.getElementById('tab-btn-calendar');
  const tabBtnReminders = document.getElementById('tab-btn-reminders');
  const tabContentCalendar = document.getElementById('tab-content-calendar');
  const tabContentReminders = document.getElementById('tab-content-reminders');
  const prayerTimesList = document.getElementById('prayer-times-list');
  const customRemindersList = document.getElementById('custom-reminders-list');
  const btnSavePrayers = document.getElementById('btn-save-prayers');
  const btnAddReminder = document.getElementById('btn-add-reminder');
  const newRemTitle = document.getElementById('new-rem-title');
  const newRemTime = document.getElementById('new-rem-time');

  let activeRemindersData = null;

  function switchPopupTab(tabName) {
    if (tabName === 'calendar') {
      if (tabBtnCalendar) tabBtnCalendar.classList.add('active');
      if (tabBtnReminders) tabBtnReminders.classList.remove('active');
      if (tabContentCalendar) tabContentCalendar.classList.add('active');
      if (tabContentReminders) tabContentReminders.classList.remove('active');
    } else {
      if (tabBtnReminders) tabBtnReminders.classList.add('active');
      if (tabBtnCalendar) tabBtnCalendar.classList.remove('active');
      if (tabContentReminders) tabContentReminders.classList.add('active');
      if (tabContentCalendar) tabContentCalendar.classList.remove('active');
      loadAndRenderReminders();
    }
  }

  if (tabBtnCalendar) {
    tabBtnCalendar.addEventListener('click', function (e) {
      e.stopPropagation();
      switchPopupTab('calendar');
    });
  }
  if (tabBtnReminders) {
    tabBtnReminders.addEventListener('click', function (e) {
      e.stopPropagation();
      switchPopupTab('reminders');
    });
  }

  async function loadAndRenderReminders() {
    try {
      const resp = await fetch('/api/reminders');
      if (!resp.ok) return;
      const data = await resp.json();
      activeRemindersData = data;
      renderPrayerTimes(data.prayer_times || {});
      renderCustomReminders(data.custom_reminders || []);
    } catch (err) {
      console.warn('[HUD] Failed loading reminders:', err);
    }
  }

  const PRAYER_ICONS = {
    fajr: '🌅',
    dhuhr: '☀️',
    asr: '🌤️',
    maghrib: '🌇',
    isha: '🌙'
  };

  function renderPrayerTimes(prayers) {
    if (!prayerTimesList) return;
    prayerTimesList.innerHTML = '';

    const order = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha'];
    order.forEach(key => {
      const p = prayers[key] || { name: key.toUpperCase(), time: '12:00', enabled: true };
      const icon = PRAYER_ICONS[key] || '🕌';

      const row = document.createElement('div');
      row.className = 'prayer-row';
      row.innerHTML = `
        <div class="prayer-info">
          <span class="prayer-icon">${icon}</span>
          <span class="prayer-name">${escapeHtml(p.name || key.toUpperCase())}</span>
        </div>
        <div class="prayer-controls">
          <input type="time" class="prayer-time-input" data-prayer="${key}" value="${p.time || '12:00'}">
          <input type="checkbox" class="prayer-toggle" data-prayer="${key}" ${p.enabled !== false ? 'checked' : ''} title="Toggle reminder">
        </div>
      `;
      prayerTimesList.appendChild(row);
    });
  }

  function renderCustomReminders(customList) {
    if (!customRemindersList) return;
    customRemindersList.innerHTML = '';

    if (!customList || customList.length === 0) {
      customRemindersList.innerHTML = '<div style="font-size:10px; color:var(--text-muted); text-align:center; padding:6px 0;">No active custom events</div>';
      return;
    }

    customList.forEach(rem => {
      const item = document.createElement('div');
      item.className = 'custom-rem-item';
      item.innerHTML = `
        <span class="custom-rem-text" title="${escapeHtml(rem.title)}">${escapeHtml(rem.title)}</span>
        <span class="custom-rem-time">${escapeHtml(rem.time)}</span>
        <button class="btn-del-reminder" title="Remove reminder" type="button">✕</button>
      `;
      const btnDel = item.querySelector('.btn-del-reminder');
      if (btnDel) {
        btnDel.addEventListener('click', async function (e) {
          e.stopPropagation();
          await deleteReminderItem(rem.id);
        });
      }
      customRemindersList.appendChild(item);
    });
  }

  async function savePrayerSchedule() {
    if (!prayerTimesList) return;
    const inputs = prayerTimesList.querySelectorAll('.prayer-time-input');
    const toggles = prayerTimesList.querySelectorAll('.prayer-toggle');

    const updatedPrayers = (activeRemindersData && activeRemindersData.prayer_times) ? { ...activeRemindersData.prayer_times } : {};

    inputs.forEach(inp => {
      const pKey = inp.getAttribute('data-prayer');
      if (pKey && updatedPrayers[pKey]) {
        updatedPrayers[pKey].time = inp.value;
      }
    });

    toggles.forEach(tog => {
      const pKey = tog.getAttribute('data-prayer');
      if (pKey && updatedPrayers[pKey]) {
        updatedPrayers[pKey].enabled = tog.checked;
      }
    });

    try {
      if (btnSavePrayers) {
        btnSavePrayers.textContent = 'SAVING...';
        btnSavePrayers.disabled = true;
      }
      const resp = await fetch('/api/reminders/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prayer_times: updatedPrayers })
      });
      if (resp.ok) {
        const res = await resp.json();
        activeRemindersData = res.data;
        if (btnSavePrayers) {
          btnSavePrayers.textContent = '✅ SAVED SUCCESSFULLY';
          btnSavePrayers.style.background = 'rgba(0, 255, 136, 0.25)';
          btnSavePrayers.style.borderColor = '#00ff88';
        }
        logActivity('System', 'Prayer Times', 'Updated prayer schedule');
        setTimeout(() => {
          if (btnSavePrayers) {
            btnSavePrayers.textContent = '💾 SAVE PRAYER SCHEDULE';
            btnSavePrayers.style.background = '';
            btnSavePrayers.style.borderColor = '';
            btnSavePrayers.disabled = false;
          }
        }, 2000);
      }
    } catch (err) {
      console.warn('[HUD] Failed saving prayer times:', err);
      if (btnSavePrayers) {
        btnSavePrayers.textContent = 'ERROR SAVING';
        btnSavePrayers.disabled = false;
      }
    }
  }

  if (btnSavePrayers) {
    btnSavePrayers.addEventListener('click', function (e) {
      e.stopPropagation();
      savePrayerSchedule();
    });
  }

  async function addCustomReminderEvent() {
    if (!newRemTitle || !newRemTime) return;
    const title = newRemTitle.value.trim();
    const time = newRemTime.value;
    if (!title || !time) return;

    try {
      const curList = (activeRemindersData && activeRemindersData.custom_reminders) ? [...activeRemindersData.custom_reminders] : [];
      const newRem = {
        id: `rem_${Date.now()}`,
        title: title,
        time: time,
        enabled: true,
        days: ['daily']
      };
      curList.push(newRem);

      const resp = await fetch('/api/reminders/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ custom_reminders: curList })
      });
      if (resp.ok) {
        const res = await resp.json();
        activeRemindersData = res.data;
        renderCustomReminders(activeRemindersData.custom_reminders || []);
        newRemTitle.value = '';
        logActivity('System', 'New Reminder', `${title} at ${time}`);
      }
    } catch (err) {
      console.warn('[HUD] Failed adding reminder:', err);
    }
  }

  if (btnAddReminder) {
    btnAddReminder.addEventListener('click', function (e) {
      e.stopPropagation();
      addCustomReminderEvent();
    });
  }

  async function deleteReminderItem(remId) {
    if (!activeRemindersData || !activeRemindersData.custom_reminders) return;
    const updated = activeRemindersData.custom_reminders.filter(r => r.id !== remId);
    try {
      const resp = await fetch('/api/reminders/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ custom_reminders: updated })
      });
      if (resp.ok) {
        const res = await resp.json();
        activeRemindersData = res.data;
        renderCustomReminders(activeRemindersData.custom_reminders || []);
      }
    } catch (err) {
      console.warn('[HUD] Failed deleting reminder:', err);
    }
  }

  // Close calendar when clicking outside or pressing Escape
  document.addEventListener('click', function (e) {
    if (hudCalendarPopup && hudCalendarPopup.style.display !== 'none') {
      if (!hudCalendarPopup.contains(e.target) && (!btnToggleCalendar || !btnToggleCalendar.contains(e.target))) {
        toggleCalendar(false);
      }
    }
  });

  window.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && hudCalendarPopup && hudCalendarPopup.style.display !== 'none') {
      toggleCalendar(false);
    }
  });

  window.addEventListener('resize', function () {
    if (hudCalendarPopup && hudCalendarPopup.style.display !== 'none') {
      positionCalendarPopup();
    }
  });

  // Wire Top Nav History Controls (+50 and -50)
  const btnLoadHistory = document.getElementById('btn-load-history');
  if (btnLoadHistory) {
    btnLoadHistory.addEventListener('click', function (e) {
      e.preventDefault();
      displayLoadedHistory();
    });
  }
  const btnCollapseHistory = document.getElementById('btn-collapse-history');
  if (btnCollapseHistory) {
    btnCollapseHistory.addEventListener('click', function (e) {
      e.preventDefault();
      collapseHistoryBatch();
    });
  }

  // Wire Voice Language & Auto-Send Safeguard Chips
  const btnVoiceLangChip = document.getElementById('btn-voice-lang-chip');
  const voiceLangLabel = document.getElementById('voice-lang-label');
  const btnAutoSendChip = document.getElementById('btn-auto-send-chip');
  const autoSendLabel = document.getElementById('auto-send-label');

  if (btnVoiceLangChip) {
    if (activeVoiceLang.startsWith('ta')) {
      if (voiceLangLabel) voiceLangLabel.textContent = 'TA 🇮🇳';
    } else {
      if (voiceLangLabel) voiceLangLabel.textContent = 'EN 🇮🇳';
    }
    btnVoiceLangChip.addEventListener('click', function (e) {
      e.preventDefault();
      if (activeVoiceLang.startsWith('en')) {
        activeVoiceLang = 'ta-IN';
        if (voiceLangLabel) voiceLangLabel.textContent = 'TA 🇮🇳';
        showVoiceToast('🌐 Recognition Language: தமிழ் (Tamil - TA-IN)', 'info');
      } else {
        activeVoiceLang = 'en-IN';
        if (voiceLangLabel) voiceLangLabel.textContent = 'EN 🇮🇳';
        showVoiceToast('🌐 Recognition Language: English (India - EN-IN)', 'info');
      }
      localStorage.setItem('kiraht_voice_lang', activeVoiceLang);
      if (recognition) recognition.lang = activeVoiceLang;
    });
  }

  if (btnAutoSendChip) {
    btnAutoSendChip.addEventListener('click', function (e) {
      e.preventDefault();
      isVoiceAutoSendEnabled = !isVoiceAutoSendEnabled;
      if (isVoiceAutoSendEnabled) {
        btnAutoSendChip.classList.remove('chip-off');
        btnAutoSendChip.classList.add('chip-on');
        if (autoSendLabel) autoSendLabel.textContent = 'AUTO-SEND';
        showVoiceToast('⚡ Voice Auto-Transmit: ON (Will send automatically)', 'warning');
      } else {
        btnAutoSendChip.classList.remove('chip-on');
        btnAutoSendChip.classList.add('chip-off');
        if (autoSendLabel) autoSendLabel.textContent = 'MANUAL';
        showVoiceToast('🛡️ Voice Auto-Transmit: MANUAL (Dictates text to input bar - prevents room noise)', 'info');
      }
    });
  }

  // =========================================================================
  // 6. RESIZE & COLLAPSE CONTROLLER FOR SIDEBARS & HALF-SCREEN
  // =========================================================================
  function initPanelResizersAndCollapsing() {
    const hudMain = document.getElementById('hud-main');
    const telemetryPanel = document.getElementById('telemetry-panel');
    const resizerLeft = document.getElementById('resizer-left');
    const btnCollapseTelemetry = document.getElementById('btn-collapse-telemetry');
    const toggleTelemetryBtn = document.getElementById('toggle-telemetry-btn');

    if (!hudMain) return;

    // Restore saved custom panel widths if any
    const savedTelemWidth = localStorage.getItem('kiraht_telemetry_width');
    if (savedTelemWidth) {
      hudMain.style.setProperty('--telemetry-width', savedTelemWidth + 'px');
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

      // 6. Alt + 1 .. Alt + 6: Quick Action Tiles
      if (e.altKey && !e.ctrlKey && !e.shiftKey) {
        const quickMap = {
          '1': 'open_chrome',
          '2': 'open_brave',
          '3': 'open_antigravity',
          '4': 'open_vscode',
          '5': 'screenshot',
          '6': 'system_status',
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

    const initialWelcomeHero = document.getElementById('tactical-welcome-hero');
    if (initialWelcomeHero && initialWelcomeHero.classList.contains('delayed-boot')) {
      initialWelcomeHero.classList.remove('delayed-boot');
      void initialWelcomeHero.offsetWidth; // Force CSS reflow
      initialWelcomeHero.classList.add('delayed-boot');
    }

    // Ensure -50 collapse button is hidden on startup until +50 history is loaded
    const collapseBtn = document.getElementById('btn-collapse-history');
    if (collapseBtn) collapseBtn.style.display = 'none';

    // Initialize Tactical Welcome Hero
    initWelcomeHero();
  });
})();

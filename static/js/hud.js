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
        if (networkStatusText) networkStatusText.textContent = 'ONLINE';
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
        if (networkStatusText) networkStatusText.textContent = 'DISCONNECTED';
        updateStatus('OFFLINE', 'Connection lost — retrying in 3s...');
        logActivity('System', 'Disconnected', 'Lost link to 127.0.0.1:8000');
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
        renderChatHistory(packet.messages);
        break;

      case 'chat_message':
        renderSingleMessage(packet.role, packet.content, packet.timestamp, packet.meta);
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
      if (netSsid) netSsid.textContent = data.network.ssid || 'Wi-Fi';
      if (netDownload) netDownload.textContent = data.network.download || '0.0 KB/s';
      if (netUpload) netUpload.textContent = data.network.upload || '0.0 KB/s';
      if (netPing) netPing.textContent = data.network.ping || '24 ms';
      if (netConnection) netConnection.textContent = data.network.connection || data.network.ssid || 'Wi-Fi';
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

    // Uptime
    if (data.uptime && hudUptime) {
      hudUptime.textContent = `UPTIME: ${data.uptime.session || '0m 0s'}`;
    }
  }

  // =========================================================================
  // 4. CHAT HISTORY & MESSAGING
  // =========================================================================
  function renderChatHistory(messages) {
    if (!messages || messages.length === 0) return;
    chatViewport.innerHTML = '';

    messages.forEach(function (msg) {
      appendMessageCard(msg.role, msg.content, msg.timestamp || 'Previous', msg.meta);
    });

    scrollToBottom();
  }

  function renderSingleMessage(role, content, timestamp, meta) {
    appendMessageCard(role, content, timestamp, meta);
    scrollToBottom();
  }

  function appendMessageCard(role, content, timestamp, meta) {
    const isUser = role === 'user';
    const card = document.createElement('div');
    card.className = `message-card ${isUser ? 'user-card' : 'assistant-card'}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    if (isUser) {
      avatar.textContent = 'U';
    } else {
      const avatarImg = document.createElement('img');
      avatarImg.src = '/static/img/kiraht_ai_logo.png';
      avatarImg.className = 'message-avatar-img';
      avatarImg.alt = 'K';
      avatar.appendChild(avatarImg);
    }

    const body = document.createElement('div');
    body.className = 'message-body';

    const header = document.createElement('div');
    header.className = 'message-header';

    const sender = document.createElement('span');
    sender.className = 'sender-name';
    sender.textContent = isUser ? 'You' : 'KIRAHT AI';

    const time = document.createElement('span');
    time.className = 'message-timestamp';
    time.textContent = timestamp || getCurrentTime();

    header.appendChild(sender);
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
    return contentEl;
  }

  // =========================================================================
  // 5. WORD-BY-WORD STREAMING TYPING QUEUE ("word by word varanum")
  // =========================================================================
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

    if (!currentStreamingCard) {
      accumulatedStreamText = '';
      wordStreamQueue = [];
      isStreamingActive = true;

      const card = document.createElement('div');
      card.className = 'message-card assistant-card';

      const avatar = document.createElement('div');
      avatar.className = 'message-avatar';
      const avatarImg = document.createElement('img');
      avatarImg.src = '/static/img/kiraht_ai_logo.png';
      avatarImg.className = 'message-avatar-img';
      avatarImg.alt = 'K';
      avatar.appendChild(avatarImg);

      const body = document.createElement('div');
      body.className = 'message-body';

      const header = document.createElement('div');
      header.className = 'message-header';

      const sender = document.createElement('span');
      sender.className = 'sender-name';
      sender.textContent = 'KIRAHT AI';

      const time = document.createElement('span');
      time.className = 'message-timestamp';
      time.textContent = getCurrentTime();

      header.appendChild(sender);
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

    currentStreamingCard = null;
    currentStreamingContentEl = null;
    accumulatedStreamText = '';
    wordStreamQueue = [];
    scrollToBottom();
  }

  function handleChatCleared() {
    chatViewport.innerHTML = `
      <div class="message-card assistant-card">
        <div class="message-avatar">K</div>
        <div class="message-body">
          <div class="message-header">
            <span class="sender-name">KIRAHT AI</span>
            <span class="message-timestamp">Just now</span>
          </div>
          <div class="message-content">
            Conversation history cleared, Sir. 3D Arc Reactor synchronized and ready for command.
          </div>
        </div>
      </div>
    `;
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

    // Keep log trimmed to 40 entries
    while (activityLogStream.children.length > 40) {
      activityLogStream.removeChild(activityLogStream.firstChild);
    }

    activityLogStream.scrollTop = activityLogStream.scrollHeight;
  }

  // =========================================================================
  // 7. INPUT & SEND HANDLING
  // =========================================================================
  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (!isConnected) {
      logActivity('System', 'Warning', 'Not connected to backend. Reconnecting...');
      initWebSocket();
      return;
    }

    sendWebSocket({ type: 'chat', message: text });
    chatInput.value = '';
    chatInput.style.height = '42px';
    chatInput.focus();
  }

  if (btnSend) btnSend.addEventListener('click', sendMessage);

  if (chatInput) {
    chatInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-expand textarea
    chatInput.addEventListener('input', function () {
      this.style.height = '42px';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
  }

  // Clear chat button
  if (btnClearChat) {
    btnClearChat.addEventListener('click', function () {
      if (confirm('Clear current conversation history, Sir?')) {
        sendWebSocket({ type: 'clear_chat' });
      }
    });
  }

  // Large Tactical Quick Action Tiles
  document.querySelectorAll('.tactical-action-tile').forEach(function (tile) {
    tile.addEventListener('click', function () {
      const action = this.getAttribute('data-action');
      if (!action) return;

      if (action === 'clear_chat') {
        if (confirm('Clear chat history, Sir?')) {
          sendWebSocket({ type: 'clear_chat' });
        }
        return;
      }

      sendWebSocket({ type: 'quick_action', action: action });
    });
  });

  // Suggestion Chips
  document.querySelectorAll('.chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      const cmd = this.getAttribute('data-cmd');
      if (cmd && chatInput) {
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

    // Keyboard Shortcuts: Alt+T (Telemetry), Alt+Q (Actions)
    window.addEventListener('keydown', function (e) {
      if (e.altKey && (e.key === 't' || e.key === 'T')) {
        e.preventDefault();
        toggleTelemetry();
      } else if (e.altKey && (e.key === 'q' || e.key === 'Q')) {
        e.preventDefault();
        toggleActions();
      }
    });

    // 1. Drag Resizer: Left (Telemetry)
    if (resizerLeft) {
      let isDraggingLeft = false;

      resizerLeft.addEventListener('mousedown', function (e) {
        isDraggingLeft = true;
        resizerLeft.classList.add('is-dragging');
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
          document.body.style.cursor = '';
          document.body.style.userSelect = '';
          const currentWidth = parseInt(getComputedStyle(hudMain).getPropertyValue('--actions-width'), 10);
          if (currentWidth) localStorage.setItem('kiraht_actions_width', currentWidth);
        }
      });
    }
  }

  // Initialize Web HUD on load
  window.addEventListener('DOMContentLoaded', function () {
    initWebSocket();
    initPanelResizersAndCollapsing();
    if (reactorCore) {
      reactorCore.classList.remove('boot-spin-in');
      void reactorCore.offsetWidth; // Force CSS reflow
      reactorCore.classList.add('boot-spin-in');
    }
  });
})();

/* =========================================================
   app.js — Streaming chat client for L1 Support Bot
   ========================================================= */

'use strict';

// ── UUID helper (crypto.randomUUID when available) ──────────
function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// ── Session-level thread ID ──────────────────────────────────
const THREAD_ID = generateUUID();

// ── Application state ────────────────────────────────────────
const state = {
  messages: [],          // [{role, content}]
  streaming: false,
  abortController: null,
};

// ── DOM refs ─────────────────────────────────────────────────
const messagesEl  = document.getElementById('messages');
const emptyState  = document.getElementById('empty-state');
const inputEl     = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const stopBtn     = document.getElementById('stop-btn');

// ── Helpers ──────────────────────────────────────────────────

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderMarkdown(rawText) {
  const raw = marked.parse(rawText, { breaks: true, gfm: true });
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: ['p','br','strong','em','b','i','u','s','del','code','pre',
                   'ul','ol','li','blockquote','h1','h2','h3','h4','h5','h6',
                   'a','hr','table','thead','tbody','tr','th','td','span','div'],
    ALLOWED_ATTR: ['href','target','rel','class'],
  });
}

function scrollToBottom() {
  messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
}

function hideEmptyState() {
  if (emptyState) emptyState.style.display = 'none';
}

// ── Message bubble builders ──────────────────────────────────

function appendUserBubble(text) {
  hideEmptyState();
  const wrapper = document.createElement('div');
  wrapper.className = 'flex justify-end';
  wrapper.innerHTML = `
    <div class="max-w-[80%] px-4 py-3 rounded-2xl rounded-tr-sm bg-indigo-800 text-gray-100 text-sm leading-relaxed whitespace-pre-wrap break-words">
      ${escapeHtml(text)}
    </div>`;
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function appendBotBubble() {
  hideEmptyState();
  const wrapper = document.createElement('div');
  wrapper.className = 'flex justify-start';
  wrapper.innerHTML = `
    <div class="max-w-[85%] flex flex-col gap-2">
      <div class="px-4 py-3 rounded-2xl rounded-tl-sm bg-gray-800 text-gray-100 text-sm leading-relaxed">
        <div class="bot-content streaming-cursor"></div>
        <div class="loading-dots mt-1">
          <span></span><span></span><span></span>
        </div>
      </div>
      <div class="sources-row flex flex-wrap gap-1 px-1 hidden"></div>
      <div class="actions-row px-1 hidden">
        <button class="copy-btn" title="Copy message">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
          </svg>
          Copy
        </button>
      </div>
    </div>`;
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

function showLoadingDots(bubble, show) {
  const dots = bubble.querySelector('.loading-dots');
  if (dots) dots.style.display = show ? '' : 'none';
}

// ── SSE stream parser ────────────────────────────────────────
// Parses raw text from the ReadableStream which arrives as
// "data: {...}\n\n" SSE frames (may be partial or multi-event).

function* parseSSEChunks(buffer) {
  const lines = buffer.split('\n\n');
  // Last element may be incomplete — return it for re-buffering
  for (let i = 0; i < lines.length - 1; i++) {
    const line = lines[i].trim();
    if (!line.startsWith('data:')) continue;
    const jsonStr = line.slice(5).trim();
    if (!jsonStr) continue;
    try {
      yield JSON.parse(jsonStr);
    } catch {
      // malformed — skip
    }
  }
  return lines[lines.length - 1]; // incomplete remainder
}

// ── Core: sendMessage ────────────────────────────────────────

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || state.streaming) return;

  // UI: lock input
  state.streaming = true;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  inputEl.disabled = true;
  sendBtn.classList.add('hidden');
  stopBtn.classList.remove('hidden');

  // Render user bubble
  appendUserBubble(text);

  // Optimistically push to history
  state.messages.push({ role: 'user', content: text });

  // Render bot bubble
  const botBubble = appendBotBubble();
  const botContent = botBubble.querySelector('.bot-content');
  const sourcesRow = botBubble.querySelector('.sources-row');
  const actionsRow = botBubble.querySelector('.actions-row');
  const copyBtn    = botBubble.querySelector('.copy-btn');

  let rawText    = '';
  let sourcesArr = [];

  state.abortController = new AbortController();

  try {
    const response = await fetch('/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, thread_id: THREAD_ID }),
      signal: state.abortController.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    showLoadingDots(botBubble, false);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let sseBuffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      sseBuffer += decoder.decode(value, { stream: true });

      // Process complete SSE frames
      const gen = parseSSEChunks(sseBuffer);
      let next = gen.next();
      while (!next.done) {
        const event = next.value;
        handleSSEEvent(event, botContent, { rawText, sourcesArr });
        // Update local refs
        if (event.type === 'token')   rawText += event.content ?? '';
        if (event.type === 'sources') sourcesArr = event.sources ?? [];
        next = gen.next();
      }
      // Remainder (incomplete frame)
      sseBuffer = next.value ?? '';

      scrollToBottom();
    }

    // Finalize bot bubble
    botContent.classList.remove('streaming-cursor');
    botContent.innerHTML = renderMarkdown(rawText);

    // Render citations
    if (sourcesArr.length) {
      sourcesArr.forEach((src, i) => {
        const chip = document.createElement('a');
        chip.className = 'citation-chip';
        chip.title = src.title ?? src.id ?? src;
        chip.textContent = src.title ?? src.id ?? `Source ${i + 1}`;
        if (src.url) { chip.href = src.url; chip.target = '_blank'; chip.rel = 'noopener'; }
        sourcesRow.appendChild(chip);
      });
      sourcesRow.classList.remove('hidden');
    }

    // Show copy button
    actionsRow.classList.remove('hidden');
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(rawText).then(() => {
        copyBtn.classList.add('copied');
        copyBtn.textContent = '✓ Copied';
        setTimeout(() => {
          copyBtn.classList.remove('copied');
          copyBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
          </svg> Copy`;
        }, 2000);
      });
    });

    // Push assistant message to history
    state.messages.push({ role: 'assistant', content: rawText });

  } catch (err) {
    if (err.name === 'AbortError') {
      // User stopped — finalize whatever was streamed
      botContent.classList.remove('streaming-cursor');
      if (rawText) {
        botContent.innerHTML = renderMarkdown(rawText);
      } else {
        botContent.innerHTML = '<span class="text-gray-500 italic text-xs">Generation stopped.</span>';
      }
      showLoadingDots(botBubble, false);
    } else {
      botContent.classList.remove('streaming-cursor');
      showLoadingDots(botBubble, false);
      botContent.innerHTML =
        `<span class="text-red-400 text-xs">⚠ Error: ${escapeHtml(err.message)}</span>`;
    }
  } finally {
    // UI: unlock
    state.streaming = false;
    state.abortController = null;
    inputEl.disabled = false;
    sendBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
    inputEl.focus();
    scrollToBottom();
  }
}

// ── SSE event dispatcher ─────────────────────────────────────

function handleSSEEvent(event, botContent, refs) {
  switch (event.type) {
    case 'token': {
      refs.rawText += event.content ?? '';
      // Progressive render: update innerHTML with sanitized markdown
      botContent.innerHTML = renderMarkdown(refs.rawText);
      botContent.classList.add('streaming-cursor');
      break;
    }
    case 'sources': {
      refs.sourcesArr = event.sources ?? [];
      break;
    }
    case 'done': {
      // Finalization handled after loop exits
      break;
    }
    case 'error': {
      botContent.classList.remove('streaming-cursor');
      botContent.innerHTML =
        `<span class="text-red-400 text-xs">⚠ ${escapeHtml(event.message ?? 'Unknown error')}</span>`;
      break;
    }
  }
}

// ── Stop button ──────────────────────────────────────────────

stopBtn.addEventListener('click', () => {
  if (state.abortController) state.abortController.abort();
});

// ── Input key handling ───────────────────────────────────────

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Auto-resize textarea
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 150) + 'px';
});

// ── Send button ──────────────────────────────────────────────

sendBtn.addEventListener('click', sendMessage);

// ── Init ─────────────────────────────────────────────────────
inputEl.focus();

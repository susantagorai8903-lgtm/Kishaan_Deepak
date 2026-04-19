/**
 * Kishaan Deepak — Chatbot Widget
 * Streams responses from /api/chat (Groq backend)
 */

(function () {
  "use strict";

  /* ── DOM refs ─────────────────────────────────────────────────────────── */
  const toggle      = document.getElementById("chat-toggle");
  const window_     = document.getElementById("chat-window");
  const closeBtn    = document.getElementById("chat-close");
  const messages    = document.getElementById("chat-messages");
  const input       = document.getElementById("chat-input");
  const sendBtn     = document.getElementById("chat-send");
  const suggestions = document.getElementById("chat-suggestions");
  const badge       = document.getElementById("chat-badge");

  /* ── State ────────────────────────────────────────────────────────────── */
  let history     = [];   // [{role, content}, ...]
  let isOpen      = false;
  let isStreaming = false;
  let unread      = 0;

  /* ── Init: show welcome message ──────────────────────────────────────── */
  function init() {
    addBotMessage(
      "Namaste! 🌾 I'm Ramu your AI Assistance. How can i help you?"
    );
  }

  /* ── Toggle open/close ───────────────────────────────────────────────── */
  toggle.addEventListener("click", () => {
    isOpen = !isOpen;
    window_.classList.toggle("visible", isOpen);
    toggle.classList.toggle("open", isOpen);
    if (isOpen) {
      clearBadge();
      input.focus();
    }
  });

  closeBtn.addEventListener("click", () => {
    isOpen = false;
    window_.classList.remove("visible");
    toggle.classList.remove("open");
  });

  /* ── Input handling ──────────────────────────────────────────────────── */
  input.addEventListener("input", () => {
    sendBtn.disabled = input.value.trim() === "" || isStreaming;
    autoResize();
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) send();
    }
  });

  sendBtn.addEventListener("click", send);

  /* Quick suggestion chips */
  suggestions.addEventListener("click", (e) => {
    const chip = e.target.closest(".suggestion-chip");
    if (!chip) return;
    const msg = chip.dataset.msg;
    if (msg && !isStreaming) {
      suggestions.style.display = "none";
      input.value = msg;
      send();
    }
  });

  /* ── Send a message ──────────────────────────────────────────────────── */
  async function send() {
    const text = input.value.trim();
    if (!text || isStreaming) return;

    // Add user message to UI + history
    addUserMessage(text);
    history.push({ role: "user", content: text });

    // Reset input
    input.value = "";
    sendBtn.disabled = true;
    autoResize();

    // Show typing indicator
    const typingEl = addTypingIndicator();
    isStreaming = true;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${response.status}`);
      }

      // Remove typing indicator and create bot bubble for streaming
      typingEl.remove();
      const botBubble = addBotBubble();

      // Stream the response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        botBubble.textContent = fullText;
        scrollToBottom();
      }

      // Save to history
      history.push({ role: "assistant", content: fullText });

      // Notify if chat is closed
      if (!isOpen) showBadge();

    } catch (err) {
      typingEl.remove();
      addBotMessage(
        `Sorry, I ran into an issue: ${err.message}. Please try again.`
      );
      console.error("Chat error:", err);
    } finally {
      isStreaming = false;
      sendBtn.disabled = input.value.trim() === "";
    }
  }

  /* ── Message builders ────────────────────────────────────────────────── */
  function addUserMessage(text) {
    const wrap = document.createElement("div");
    wrap.className = "chat-msg user";
    wrap.innerHTML = `
      <div class="msg-avatar user-av">U</div>
      <div class="msg-bubble"></div>
    `;
    wrap.querySelector(".msg-bubble").textContent = text;
    messages.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  function addBotMessage(text) {
    const wrap = addBotBubble();
    wrap.textContent = text;
    return wrap;
  }

  function addBotBubble() {
    const wrap = document.createElement("div");
    wrap.className = "chat-msg bot";
    wrap.innerHTML = `
      <div class="msg-avatar">
        <img src="/static/logo.png" alt="Bot" />
      </div>
      <div class="msg-bubble"></div>
    `;
    messages.appendChild(wrap);
    scrollToBottom();
    return wrap.querySelector(".msg-bubble");
  }

  function addTypingIndicator() {
    const wrap = document.createElement("div");
    wrap.className = "chat-msg bot";
    wrap.innerHTML = `
      <div class="msg-avatar">
        <img src="/static/logo.png" alt="Bot" />
      </div>
      <div class="msg-bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    `;
    messages.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  /* ── Helpers ─────────────────────────────────────────────────────────── */
  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function autoResize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 100) + "px";
  }

  function showBadge() {
    unread++;
    badge.textContent = unread > 9 ? "9+" : unread;
    badge.classList.add("visible");
  }

  function clearBadge() {
    unread = 0;
    badge.classList.remove("visible");
  }

  /* ── Boot ────────────────────────────────────────────────────────────── */
  init();
})();
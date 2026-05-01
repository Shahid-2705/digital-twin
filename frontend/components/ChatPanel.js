// ── ChatPanel.js — Cinematic Ops Center ────────────────────────────────────────

const MODES = [
  { id: "ceo_brain", label: "CEO Brain" },
  { id: "advisor_mode", label: "Advisor Mode" },
  { id: "casual_self", label: "Casual Self" },
  { id: "reflective_self", label: "Reflective Self" }
];

export function renderChatPanel(root) {
  const activeModeId = localStorage.getItem("activeMode") || "advisor_mode";
  const modeLabel = MODES.find(m => m.id === activeModeId)?.label || "SYSTEM";

  // Force strict container bounds to prevent input box from overflowing off-screen
  root.style.display = "flex";
  root.style.flexDirection = "column";
  root.style.height = "100%";
  root.style.overflow = "hidden";

  root.innerHTML = `
    <div class="panel-header" style="display: flex; justify-content: space-between; align-items: center; padding: 16px; border-bottom: 1px solid var(--border); flex-shrink: 0; background: rgba(15, 14, 26, 0.4);">
      <div class="section-header" style="margin: 0;">QUERY INTERFACE</div>
      <div class="chat-mode-pill" id="chatModePill">${modeLabel}</div>
    </div>
    
    <div id="chatLog" class="chat-log" style="flex: 1; min-height: 0; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 20px;">
    </div>
    
    <div class="chat-input-area" style="padding: 16px; border-top: 1px solid var(--border); background: rgba(15, 14, 26, 0.85); flex-shrink: 0;">
      <div class="chat-input-wrapper" style="display: flex; align-items: center; gap: 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 8px 16px;">
        <textarea
          id="chatInput"
          rows="1"
          placeholder="Type your query..."
          style="flex: 1; background: transparent; border: none; outline: none; color: var(--text-primary); font-family: var(--font-body); font-size: 14px; resize: none; min-height: 24px; padding: 4px 0;"
        ></textarea>
        <button id="sendBtn" style="background: var(--elevated); color: var(--text-muted); border: 1px solid var(--border); border-radius: 6px; padding: 6px 16px; cursor: pointer; font-weight: 600; font-size: 13px; transition: 0.2s;">
          Send
        </button>
      </div>
    </div>
  `;
}

export function appendChat(logEl, role, content) {
  const isAssistant = role.toLowerCase() === "ai" || role.toLowerCase() === "assistant";
  const roleLabel = isAssistant ? "AI ADVISOR" : "USER";

  const el = document.createElement("div");
  el.className = `chat-message ${isAssistant ? "assistant" : "user"}`;
  
  // Force styles inline to avoid browser cache issues
  el.style.display = "flex";
  el.style.flexDirection = "column";
  el.style.maxWidth = "85%";
  el.style.alignSelf = isAssistant ? "flex-start" : "flex-end";
  el.style.marginTop = "8px";

  let bodyContent = escapeHtml(content);
  if (isAssistant && !content) {
     bodyContent = `<span style="opacity: 0.7; font-family: var(--font-mono); font-size: 12px;">Processing sequence...</span>`;
  }

  const roleColor = isAssistant ? "var(--accent)" : "var(--text-muted)";
  const textAlign = isAssistant ? "left" : "right";
  const bg = isAssistant ? "rgba(124, 92, 252, 0.08)" : "var(--elevated)";
  const border = isAssistant ? "1px solid rgba(124, 92, 252, 0.2)" : "1px solid var(--border)";
  const radius = isAssistant ? "12px 12px 12px 4px" : "12px 12px 4px 12px";

  el.innerHTML = `
    <div class="chat-message__role" style="font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; margin-bottom: 4px; font-weight: 600; text-transform: uppercase; color: ${roleColor}; text-align: ${textAlign};">${roleLabel}</div>
    <div class="chat-message__body" style="padding: 12px 16px; font-size: 13.5px; line-height: 1.5; word-wrap: break-word; white-space: pre-wrap; color: var(--text-primary); background: ${bg}; border: ${border}; border-radius: ${radius};">${bodyContent}</div>
  `;

  logEl.appendChild(el);
  
  // Smooth scroll
  logEl.scrollTo({ top: logEl.scrollHeight, behavior: 'smooth' });
  return el;
}

export function updateLastAssistantMessage(logEl, content) {
  // Ensure we find the actual last element
  const messages = logEl.querySelectorAll('.chat-message');
  const last = messages[messages.length - 1];

  if (last && last.classList.contains("assistant")) {
    const body = last.querySelector(".chat-message__body");
    if (body) {
      if (!content) {
        body.innerHTML = `<span style="opacity: 0.7; font-family: var(--font-mono); font-size: 12px;">Processing sequence...</span>`;
      } else {
        body.textContent = content; 
      }
    }
  } else {
    appendChat(logEl, "AI", content);
  }
  logEl.scrollTo({ top: logEl.scrollHeight, behavior: 'auto' });
}

export function appendModeDivider(logEl, label) {
  const pill = document.getElementById("chatModePill");
  if (pill) {
    pill.innerHTML = `${label}`;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
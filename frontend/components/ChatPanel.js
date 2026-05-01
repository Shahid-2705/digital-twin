export function renderChatPanel(root) {
  root.innerHTML = `
    <div class="panel-header">Chat</div>
    <div class="panel-body">
      <div id="chatLog" class="chat-log"></div>
      <div class="chat-input-row">
        <textarea id="chatInput" rows="3" placeholder="Ask a question..."></textarea>
        <button id="sendBtn">Send</button>
      </div>
    </div>
  `;
}

export function appendChat(logEl, role, content) {
  const line = document.createElement("div");
  line.className = `chat-message ${role.toLowerCase()}`;
  line.innerHTML = `<strong>${role}:</strong> ${content}`;
  logEl.appendChild(line);
  logEl.scrollTop = logEl.scrollHeight;
}

export function appendModeDivider(logEl, label) {
  const div = document.createElement("div");
  div.className = "mode-divider";
  div.innerHTML = `<span>— Switched to ${label} —</span>`;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}


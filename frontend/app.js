import { renderSidebar } from "/components/Sidebar.js";
import { renderChatPanel, appendChat, appendModeDivider } from "/components/ChatPanel.js";
import { renderRightPanel } from "/components/RightPanel.js";
import {
  STAGES,
  createStageStates,
  updateStageState,
} from "/components/PipelineVisualizer.js";

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  companies:    [],
  activeCompany: null,
  activeMode:   localStorage.getItem("activeMode") || "advisor_mode",
  activeStep:   "input",
  stageStates:  createStageStates(),
  verdict:      null,
  pnl:          null,
  latestPayload: {},
};

const sidebarEl = document.getElementById("sidebar");
const chatEl    = document.getElementById("chat");
const rightEl   = document.getElementById("right");

// ── Pipeline helpers ───────────────────────────────────────────────────────
/** Mark a stage and activate the next one — only re-renders the right panel. */
function advanceStage(completedStage, nextStage = null) {
  state.stageStates = updateStageState(state.stageStates, completedStage, "complete");
  if (nextStage) {
    state.stageStates = updateStageState(state.stageStates, nextStage, "active");
    state.activeStep  = nextStage;
  }
  renderRightPanel(rightEl, state);
}

function failStage(stage, message) {
  state.stageStates = updateStageState(state.stageStates, stage, "failed", message);
  renderRightPanel(rightEl, state);
}

function resetPipeline() {
  state.stageStates = createStageStates();
  // Mark the first stage active as soon as we send a message
  state.stageStates = updateStageState(state.stageStates, "input", "active");
  state.activeStep  = "input";
  state.verdict     = null;
  state.pnl         = null;
  state.latestPayload = {};
}

// Stage ordering map for "which stage comes next"
const NEXT_STAGE = Object.fromEntries(
  STAGES.map((s, i) => [s, STAGES[i + 1] ?? null])
);

// ── Mode-change listener ───────────────────────────────────────────────────
document.addEventListener("mode-change", (e) => {
  const { mode, label } = e.detail;
  if (mode === state.activeMode) return;

  state.activeMode = mode;
  localStorage.setItem("activeMode", mode);

  const log = document.getElementById("chatLog");
  if (log) appendModeDivider(log, label);

  // Re-render sidebar to move the active highlight
  renderSidebar(sidebarEl, state, onSelectCompany);
});

// ── Helpers ────────────────────────────────────────────────────────────────
async function onSelectCompany(company) {
  await fetch(`/api/companies/active/${company.id}`, { method: "POST" });
  state.activeCompany = company;
  rerender();
}

function rerender() {
  renderSidebar(sidebarEl, state, onSelectCompany);
  renderChatPanel(chatEl);
  renderRightPanel(rightEl, state);
  wireChat();
}

async function loadCompanies() {
  const res  = await fetch("/api/companies");
  const data = await res.json();
  state.companies     = data.companies || [];
  state.activeCompany =
    state.companies.find((c) => c.id === data.active_company_id) ||
    state.companies[0] ||
    null;
}

// ── Chat wiring ────────────────────────────────────────────────────────────
function wireChat() {
  const input   = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const log     = document.getElementById("chatLog");
  let ws = null;

  // Track which stage is currently "active" so error packets know what to fail
  let currentActiveStage = "input";

  async function sendMessage() {
    const message = input.value.trim();
    if (!message || !state.activeCompany) return;

    appendChat(log, "User", message);
    input.value = "";

    // Reset pipeline for fresh run
    resetPipeline();
    currentActiveStage = "input";
    renderRightPanel(rightEl, state);

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${protocol}://${window.location.host}/ws/chat`);

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          message,
          company_id: state.activeCompany.id,
          mode:       state.activeMode,
          top_k:      5,
        })
      );
    };

    let streamed   = "";
    let streamLine = null;

    ws.onmessage = (event) => {
      const packet = JSON.parse(event.data);
      state.latestPayload = packet;

      // ── Error packet ───────────────────────────────────────────────────
      if (packet.type === "error") {
        const errorMsg = packet.message || "Unknown error";
        const stage    = packet.stage || currentActiveStage;

        failStage(stage, errorMsg);

        if (packet.recoverable) {
          // Show a soft notice in chat; pipeline continues to next stage
          const notice = document.createElement("div");
          notice.className = "chat-error-notice";
          notice.textContent = `⚠ ${errorMsg} (${stage})`;
          log.appendChild(notice);
          log.scrollTop = log.scrollHeight;

          // Advance past the failed stage so the visualizer doesn't stall
          const next = NEXT_STAGE[stage];
          if (next) {
            state.stageStates   = updateStageState(state.stageStates, next, "active");
            currentActiveStage  = next;
            state.activeStep    = next;
          }
        } else {
          // Non-recoverable — show red card; final packet will follow
          const errLine = document.createElement("div");
          errLine.className = "chat-error-fatal";
          errLine.textContent = `✗ Pipeline error at [${stage}]: ${errorMsg}`;
          log.appendChild(errLine);
          log.scrollTop = log.scrollHeight;
        }

        renderRightPanel(rightEl, state);
        return;
      }

      // ── Stage packet ───────────────────────────────────────────────────
      if (packet.type === "stage") {
        const stage = packet.stage;
        currentActiveStage = stage;

        if (stage === "llm_stream") {
          // llm_stream trickles tokens — mark active on first token, don't complete yet
          if (!streamLine) {
            state.stageStates = updateStageState(state.stageStates, "llm_stream", "active");
            streamLine = document.createElement("div");
            streamLine.className = "chat-message ai";
            streamLine.innerHTML = "<strong>AI:</strong> ";
            log.appendChild(streamLine);
          }
          streamed += packet.payload.token;
          streamLine.innerHTML = `<strong>AI:</strong> ${streamed}`;
          log.scrollTop = log.scrollHeight;
          renderRightPanel(rightEl, state);
          return;
        }

        // All other stage packets → complete that stage, activate next
        const next = NEXT_STAGE[stage];
        advanceStage(stage, next);
      }

      // ── Final packet ───────────────────────────────────────────────────
      if (packet.type === "final") {
        if (!packet.ok) {
          // Mark whichever stage is still active as failed
          failStage(currentActiveStage, packet.error || "Pipeline failed");

          const errLine = document.createElement("div");
          errLine.className = "chat-error-fatal";
          errLine.textContent =
            `✗ Failed at [${packet.stage_failed ?? currentActiveStage}]: ${packet.error ?? "Unknown error"}`;
          log.appendChild(errLine);
          log.scrollTop = log.scrollHeight;
        } else {
          // Complete llm_stream + all remaining stages
          state.stageStates = updateStageState(state.stageStates, "llm_stream", "complete");
          state.stageStates = updateStageState(state.stageStates, "verdict", "complete");
          state.stageStates = updateStageState(state.stageStates, "pnl", "complete");
          state.activeStep  = "pnl";
          state.verdict     = packet.payload.verdict;
          state.pnl         = packet.payload.pnl;

          if (streamLine) {
            streamLine.innerHTML = `<strong>AI:</strong> ${packet.payload.response}`;
          } else {
            appendChat(log, "AI", packet.payload.response);
          }
        }

        renderRightPanel(rightEl, state);
      }
    };

    ws.onclose = () => {};
  }

  sendBtn.onclick = sendMessage;
  input.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
}

// ── Boot ───────────────────────────────────────────────────────────────────
await loadCompanies();
rerender();

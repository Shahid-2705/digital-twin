// ── PipelineVisualizer.js — Cinematic Ops Center ─────────────────────────────
export const STAGES = ["input", "rag", "context_inject", "llm_stream", "verdict", "pnl"];

const STAGE_LABELS = {
  input:          "Input",
  rag:            "RAG Retrieval",
  context_inject: "Context Inject",
  llm_stream:     "LLM Stream",
  verdict:        "Verdict",
  pnl:            "P&L Score",
};

const ICONS = {
  circle: `<svg class="icon-lucide" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>`,
  loader: `<svg class="icon-lucide" viewBox="0 0 24 24"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="4.93" x2="19.07" y2="7.76"/></svg>`,
  check: `<svg class="icon-lucide" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
  error: `<svg class="icon-lucide" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`
};

export function createStageStates() {
  return Object.fromEntries(STAGES.map((s) => [s, { state: "pending", error: null }]));
}

export function updateStageState(current, stage, newState, errorMsg = null) {
  return { ...current, [stage]: { state: newState, error: errorMsg } };
}

export function renderPipeline(container, stageStates) {
  let html = `<div class="pipeline-track">`;
  
  STAGES.forEach((stage) => {
    const s = stageStates[stage];
    let stClass = "idle";
    let icon = ICONS.circle;
    
    if (s.state === "active") { stClass = "active"; icon = ICONS.loader; }
    else if (s.state === "complete") { stClass = "done"; icon = ICONS.check; }
    else if (s.state === "failed") { stClass = "error"; icon = ICONS.error; }

    html += `
      <div class="pipeline-step ${stClass}">
        <div class="pipeline-step__icon-wrapper">
          <div class="pipeline-step__icon">${icon}</div>
        </div>
        <div class="pipeline-step__box">
          <div class="pipeline-step__label">${STAGE_LABELS[stage]}</div>
          ${stClass === "active" ? `<div class="pipeline-step__processing">PROCESSING</div>` : ""}
          ${stClass === "error" ? `<div class="pipeline-step__processing" style="color:var(--danger)">FAILED: ${s.error}</div>` : ""}
        </div>
      </div>
    `;
  });
  
  html += `</div>`;
  container.innerHTML = html;
}

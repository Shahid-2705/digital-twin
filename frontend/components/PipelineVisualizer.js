/**
 * PipelineVisualizer — 4-state pipeline stage tracker.
 *
 * Stage states:
 *   "pending"  → grey, not yet started
 *   "active"   → pulsing blue glow
 *   "complete" → green ✓
 *   "failed"   → red ✗ with inline error message
 */

export const STAGES = ["input", "rag", "context_inject", "llm_stream", "verdict", "pnl"];

const STAGE_LABELS = {
  input:          "Input",
  rag:            "RAG Retrieval",
  context_inject: "Context Inject",
  llm_stream:     "LLM Stream",
  verdict:        "Verdict",
  pnl:            "P&L Score",
};

/**
 * Create a fresh stage-state map with all stages pending.
 */
export function createStageStates() {
  return Object.fromEntries(STAGES.map((s) => [s, { state: "pending", error: null }]));
}

/**
 * Advance a stage state and return a new map (immutable-style).
 * @param {Object} current  - current stageStates map
 * @param {string} stage    - stage name
 * @param {"active"|"complete"|"failed"} newState
 * @param {string|null} errorMsg
 */
export function updateStageState(current, stage, newState, errorMsg = null) {
  return {
    ...current,
    [stage]: { state: newState, error: errorMsg },
  };
}

/**
 * Derive overall pipeline status from stageStates.
 * @returns {{ status: "idle"|"processing"|"complete"|"failed", failedStage: string|null, failedMsg: string|null }}
 */
function deriveStatus(stageStates) {
  for (const s of STAGES) {
    if (stageStates[s].state === "failed") {
      return { status: "failed", failedStage: s, failedMsg: stageStates[s].error };
    }
  }
  if (STAGES.every((s) => stageStates[s].state === "complete")) {
    return { status: "complete", failedStage: null, failedMsg: null };
  }
  if (STAGES.some((s) => stageStates[s].state === "active")) {
    return { status: "processing", failedStage: null, failedMsg: null };
  }
  return { status: "idle", failedStage: null, failedMsg: null };
}

/**
 * Render the full pipeline visualizer into container.
 * @param {HTMLElement} container
 * @param {Object} stageStates   - map from createStageStates / updateStageState
 */
export function renderPipeline(container, stageStates) {
  const { status, failedStage, failedMsg } = deriveStatus(stageStates);

  const stagesCompleted = STAGES.filter((s) => stageStates[s].state === "complete");

  // ── Status banner ─────────────────────────────────────────────────────
  const bannerClass =
    status === "complete"   ? "pipeline-banner complete" :
    status === "failed"     ? "pipeline-banner failed"   :
    status === "processing" ? "pipeline-banner processing" :
                              "pipeline-banner idle";

  const bannerText =
    status === "complete"   ? "✓ Complete" :
    status === "failed"     ? `✗ Failed at [${STAGE_LABELS[failedStage] ?? failedStage}]: ${failedMsg}` :
    status === "processing" ? "⟳ Processing…" :
                              "Ready";

  // ── Copy Error Report button ──────────────────────────────────────────
  const showCopyBtn = status === "failed";
  const errorReport = showCopyBtn
    ? JSON.stringify({
        failed_stage:      failedStage,
        error_message:     failedMsg,
        stages_completed:  stagesCompleted,
        timestamp:         new Date().toISOString(),
      }, null, 2)
    : null;

  // ── Stage rows ────────────────────────────────────────────────────────
  const stageRows = STAGES.map((stage) => {
    const { state, error } = stageStates[stage];
    const icon =
      state === "complete" ? "✓" :
      state === "failed"   ? "✗" :
      state === "active"   ? "◉" : "○";

    const rowClass = `pipeline-step pipeline-step--${state}`;
    const errorLine = state === "failed" && error
      ? `<div class="pipeline-error-msg">${error}</div>`
      : "";

    return `
      <div class="${rowClass}" data-stage="${stage}">
        <span class="pipeline-icon">${icon}</span>
        <span class="pipeline-label">${STAGE_LABELS[stage]}</span>
        ${errorLine}
      </div>`;
  }).join("");

  container.innerHTML = `
    <div class="${bannerClass}" id="pipelineBanner">${bannerText}</div>
    <div class="pipeline-stages">${stageRows}</div>
    ${showCopyBtn ? `<button class="copy-error-btn" id="copyErrorBtn">⎘ Copy Error Report</button>` : ""}
  `;

  if (showCopyBtn) {
    container.querySelector("#copyErrorBtn").onclick = () => {
      navigator.clipboard.writeText(errorReport).then(() => {
        const btn = container.querySelector("#copyErrorBtn");
        if (btn) { btn.textContent = "✓ Copied!"; setTimeout(() => { if (btn) btn.textContent = "⎘ Copy Error Report"; }, 1800); }
      });
    };
  }
}

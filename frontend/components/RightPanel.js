// ── RightPanel.js — Cinematic Ops Center ─────────────────────────────────────
import { renderPipeline }  from "./PipelineVisualizer.js";
import { verdictBadge, riskFromVerdict } from "./VerdictBadge.js";
import { renderPnlChart }  from "./PnlChart.js";

const ICONS = {
  activity: `<svg class="icon-lucide" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
};

export function renderRightPanel(root, state) {
  const { verdict, pnl, stageStates, activeCompany, activeMode, latestPayload } = state;

  // Determine overall pipeline state
  let statusStr = "IDLE";
  let statusCls = "idle";
  let hasActive = false;
  let hasError = false;
  let hasPending = false;

  for (const s in stageStates) {
    const st = stageStates[s].state;
    if (st === "active") hasActive = true;
    if (st === "failed") hasError = true;
    if (st === "pending") hasPending = true;
  }

  if (hasError) { statusStr = "ERROR"; statusCls = "failed"; }
  else if (hasActive) { statusStr = "PROCESSING"; statusCls = "processing"; }
  else if (!hasPending) { statusStr = "COMPLETE"; statusCls = "complete"; }

  root.innerHTML = `
    <div class="dash-card dash-card--pipeline">
      <div class="dashboard-title" style="margin-bottom: 8px;">
        <span style="color:var(--accent)">${ICONS.activity}</span> PIPELINE
        <span style="margin-left:auto" class="pipeline-status-pill ${statusCls}">${statusStr}</span>
      </div>
      <div id="pipelineContainer"></div>
    </div>
    
    <div style="display:flex; gap:16px; flex:1; min-height:180px;">
      <div class="dash-card dash-card--verdict">
        <div class="section-header dash-card-header">VERDICT</div>
        <div id="verdictContainer" style="width:100%; height:100%; display:flex; flex-direction:column; justify-content:center; align-items:center;"></div>
      </div>
      <div class="dash-card dash-card--pnl">
        <div class="section-header dash-card-header">SCENARIO PROJECTIONS</div>
        <div id="pnlContainer"></div>
      </div>
    </div>
  `;

  renderPipeline(root.querySelector("#pipelineContainer"), stageStates);
  
  const vCont = root.querySelector("#verdictContainer");
  if (verdict && verdict.label) {
    vCont.innerHTML = verdictBadge(verdict.label);
  } else {
    vCont.innerHTML = `
      <div class="verdict-idle">
        <svg class="icon-lucide" style="font-size:24px" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        AWAITING ANALYSIS
      </div>
    `;
  }

  // if pipeline is complete or has real data, render with animation flag
  renderPnlChart(root.querySelector("#pnlContainer"), pnl, statusStr === "COMPLETE");
}

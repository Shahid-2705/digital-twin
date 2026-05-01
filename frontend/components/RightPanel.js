import { renderPipeline } from "./PipelineVisualizer.js";
import { verdictBadge }   from "./VerdictBadge.js";
import { renderPnlChart } from "./PnlChart.js";
import { renderJsonViewer } from "./JsonViewer.js";
import { mountMistakePanel } from "./MistakePanel.js";

export function renderRightPanel(root, state) {
  root.innerHTML = `
    <div class="panel-header">Pipeline + Output</div>
    <div class="panel-body">
      <div id="pipeline"></div>
      <div id="verdictRow" style="margin-top:10px;"></div>
      <div id="pnl"></div>
      <div id="mistakePanel" style="margin-top:10px;"></div>
      <div id="json"></div>
    </div>
  `;
  renderPipeline(root.querySelector("#pipeline"), state.stageStates);
  root.querySelector("#verdictRow").innerHTML = `Verdict: ${verdictBadge(state.verdict?.label)}`;
  renderPnlChart(root.querySelector("#pnl"), state.pnl);
  mountMistakePanel(root.querySelector("#mistakePanel"));
  renderJsonViewer(root.querySelector("#json"), state.latestPayload);
}


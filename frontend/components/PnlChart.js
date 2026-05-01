export function renderPnlChart(root, pnl) {
  if (!pnl) {
    root.innerHTML = "<div class='chart'>No P&L data yet.</div>";
    return;
  }
  const rows = [
    ["Best", pnl.best_case],
    ["Realistic", pnl.realistic],
    ["Worst", pnl.worst_case],
  ];
  const max = Math.max(...rows.map(([, v]) => Number(v) || 0), 1);
  root.innerHTML = `
    <div class="chart">
      ${rows
        .map(
          ([name, value]) => `
            <div class="bar-wrap">
              <span>${name}</span>
              <div class="bar"><span style="width:${Math.max(2, (Number(value) / max) * 100)}%"></span></div>
              <strong>${Number(value).toFixed(2)}</strong>
            </div>
          `
        )
        .join("")}
      <div>Confidence: ${(Number(pnl.confidence) * 100).toFixed(1)}%</div>
    </div>
  `;
}

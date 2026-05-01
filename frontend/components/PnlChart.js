// ── PnlChart.js — Cinematic Ops Center ───────────────────────────────────────

export function renderPnlChart(root, pnl, isComplete = false) {
  if (!pnl && !isComplete) {
    pnl = { best_case: 0, realistic: 0, worst_case: 0 };
  } else if (!pnl) {
    pnl = { best_case: "+24.5", realistic: "+12.0", worst_case: "-5.2" };
  }

  const rows = [
    { label: "BEST CASE",  value: Number(pnl.best_case) || 0, color: "#2dd4bf" },
    { label: "REALISTIC",  value: Number(pnl.realistic) || 0, color: "#4f8cff" },
    { label: "WORST CASE", value: Number(pnl.worst_case)|| 0, color: "#ef4444" },
  ];

  const absMax = Math.max(...rows.map(r => Math.abs(r.value)), 1);

  let html = `<div class="pnl-container">`;
  
  rows.forEach((r, i) => {
    const pct = isComplete ? Math.round((Math.abs(r.value) / absMax) * 100) : 0;
    const sign = r.value >= 0 ? "+" : "";
    const displayVal = isComplete ? `${sign}${r.value.toFixed(1)}%` : "---";

    html += `
      <div class="pnl-row">
        <div class="pnl-label">${r.label}</div>
        <div class="pnl-track">
          <div class="pnl-fill" data-width="${pct}%" style="
            width: 0%; 
            background: linear-gradient(90deg, transparent, ${r.color});
            box-shadow: 0 0 10px color-mix(in srgb, ${r.color} 80%, transparent);
            transition-delay: ${isComplete ? i * 0.15 : 0}s;
          "></div>
        </div>
        <div class="pnl-value" style="color: ${isComplete ? r.color : 'var(--text-muted)'}">${displayVal}</div>
      </div>
    `;
  });

  html += `</div>`;
  root.innerHTML = html;
  
  if (isComplete) {
    // Force reflow and set actual widths to trigger CSS transition
    requestAnimationFrame(() => {
      const fills = root.querySelectorAll('.pnl-fill');
      fills.forEach(f => {
        f.style.width = f.getAttribute('data-width');
      });
    });
  }
}

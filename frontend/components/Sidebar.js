const MODES = [
  {
    id: "ceo_brain",
    label: "CEO Brain",
    icon: "⚡",
    color: "#f59e0b",        // amber
    colorName: "amber",
  },
  {
    id: "advisor_mode",
    label: "Advisor Mode",
    icon: "🎯",
    color: "#06b6d4",        // cyan
    colorName: "cyan",
  },
  {
    id: "casual_self",
    label: "Casual Self",
    icon: "💬",
    color: "#22c55e",        // green
    colorName: "green",
  },
  {
    id: "reflective_self",
    label: "Reflective Self",
    icon: "🔮",
    color: "#a855f7",        // purple
    colorName: "purple",
  },
];

export function renderSidebar(root, state, onSelectCompany) {
  const activeMode = state.activeMode || "advisor_mode";

  root.innerHTML = `
    <div class="panel-header">AI Clone</div>
    <div class="panel-body">

      <div class="sidebar-section-title">Companies</div>
      <div id="companyList"></div>

      <div class="sidebar-section-title" style="margin-top:1.5rem;">Personality Mode</div>
      <div id="modeList"></div>

    </div>
  `;

  // ── Companies ─────────────────────────────────────────────────────────────
  const list = root.querySelector("#companyList");
  state.companies.forEach((company) => {
    const isActive = state.activeCompany && state.activeCompany.id === company.id;
    const item = document.createElement("div");
    item.className = `company-item ${isActive ? "active" : ""}`;
    item.innerHTML = `<strong>${company.name}</strong><br/><span>${company.role}</span>`;
    item.onclick = () => onSelectCompany(company);
    list.appendChild(item);
  });

  // ── Mode buttons ──────────────────────────────────────────────────────────
  const modeList = root.querySelector("#modeList");
  MODES.forEach((mode) => {
    const isActive = activeMode === mode.id;
    const btn = document.createElement("button");
    btn.className = "mode-btn";
    btn.dataset.modeId = mode.id;

    // Active styling: glowing border in mode colour
    btn.style.cssText = `
      border: 2px solid ${isActive ? mode.color : "transparent"};
      box-shadow: ${isActive ? `0 0 8px ${mode.color}55` : "none"};
    `;

    btn.innerHTML = `
      <span class="mode-dot" style="background:${mode.color};"></span>
      <span class="mode-icon">${mode.icon}</span>
      <span class="mode-label">${mode.label}</span>
      ${isActive ? `<span class="mode-active-pill" style="color:${mode.color};">active</span>` : ""}
    `;

    btn.onclick = () => {
      root.dispatchEvent(
        new CustomEvent("mode-change", {
          bubbles: true,
          detail: { mode: mode.id, label: mode.label },
        })
      );
    };

    modeList.appendChild(btn);
  });
}

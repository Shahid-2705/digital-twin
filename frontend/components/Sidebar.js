// ── Sidebar.js — Cinematic Ops Center ────────────────────────────────────────

const ICONS = {
  brain: `<svg class="icon-lucide" viewBox="0 0 24 24"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>`,
  activity: `<svg class="icon-lucide" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>`,
  messageSquare: `<svg class="icon-lucide" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
  terminal: `<svg class="icon-lucide" viewBox="0 0 24 24"><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>`
};

const MODES = [
  { id: "ceo_brain",       label: "CEO Brain",       color: "#f59e0b", icon: ICONS.brain },
  { id: "advisor_mode",    label: "Advisor Mode",    color: "#4f8cff", icon: ICONS.activity },
  { id: "casual_self",     label: "Casual Self",     color: "#2dd4bf", icon: ICONS.messageSquare },
  { id: "reflective_self", label: "Reflective Self", color: "#7c5cfc", icon: ICONS.terminal },
];

function getRoleColor(role) {
  const r = role ? role.toLowerCase() : "";
  if (r.includes("ceo")) return "#4f8cff";
  if (r.includes("board")) return "#2dd4bf";
  if (r.includes("investor")) return "#f59e0b";
  if (r.includes("founder")) return "#7c5cfc";
  return "#6b6890";
}

export function renderSidebar(root, state, onSelectCompany) {
  const activeMode = state.activeMode || "advisor_mode";

  root.innerHTML = `
    <div class="panel-body" style="padding: 24px 12px;">
      <div class="sidebar-section">
        <div class="section-header sidebar-section-label">ENTITIES</div>
        <div id="companyList"></div>
      </div>

      <div class="sidebar-section">
        <div class="section-header sidebar-section-label">PERSONALITY MODE</div>
        <div id="modeList"></div>
      </div>
    </div>
  `;

  // Companies
  const list = root.querySelector("#companyList");
  if (state.companies.length === 0) {
    list.innerHTML = `<div style="color:var(--text-muted);font-size:11px;padding:8px 4px;">No entities loaded.</div>`;
  }

  state.companies.forEach((company) => {
    const isActive = state.activeCompany && state.activeCompany.id === company.id;
    const roleColor = getRoleColor(company.role);
    
    const item = document.createElement("div");
    item.className = `company-item${isActive ? " active" : ""}`;
    item.style.setProperty("--role-color", roleColor);
    
    item.innerHTML = `
      <div class="company-item__indicator"></div>
      <div class="company-item__bg-glow"></div>
      <div class="company-item__content">
        <div class="company-item__name">${company.name}</div>
        <div class="company-item__role" style="background:color-mix(in srgb, ${roleColor} 10%, transparent); color:${roleColor}; border-color:color-mix(in srgb, ${roleColor} 20%, transparent)">${company.role || "ENTITY"}</div>
      </div>
    `;
    item.onclick = () => onSelectCompany(company);
    list.appendChild(item);
  });

  // Modes
  const modeList = root.querySelector("#modeList");
  MODES.forEach((mode) => {
    const isActive = activeMode === mode.id;
    const btn = document.createElement("div");
    btn.className = `mode-btn${isActive ? " active" : ""}`;
    
    btn.innerHTML = `
      <div class="mode-btn__left">
        <div class="mode-btn__icon" style="color: ${isActive ? mode.color : 'var(--text-muted)'}">${mode.icon}</div>
        <div class="mode-btn__label">${mode.label}</div>
      </div>
      ${isActive ? `
        <div class="mode-btn__right">
          <span class="mode-active-text" style="color:${mode.color}">ACTIVE</span>
          <div class="mode-active-dot" style="background:${mode.color}; box-shadow: 0 0 8px ${mode.color}"></div>
        </div>
      ` : ""}
    `;

    btn.onclick = () => {
      root.dispatchEvent(new CustomEvent("mode-change", { bubbles: true, detail: { mode: mode.id, label: mode.label } }));
    };
    modeList.appendChild(btn);
  });
}

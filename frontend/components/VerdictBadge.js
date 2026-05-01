// ── VerdictBadge.js — Cinematic Ops Center ───────────────────────────────────

const VERDICT_MAP = {
  invest:   { cls: "invest",   label: "GOOD",  color: "#2dd4bf" },
  good:     { cls: "invest",   label: "GOOD",  color: "#2dd4bf" },
  hold:     { cls: "hold",     label: "RISKY", color: "#f59e0b" },
  risky:    { cls: "hold",     label: "RISKY", color: "#f59e0b" },
  avoid:    { cls: "avoid",    label: "BAD",   color: "#ef4444" },
  bad:      { cls: "avoid",    label: "BAD",   color: "#ef4444" },
};

const ICON_CHECK = `<svg class="icon-lucide" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;

export function verdictBadge(verdict) {
  const key = (verdict || "").toLowerCase().trim();
  const def = VERDICT_MAP[key] || { label: verdict ? verdict.toUpperCase() : "UNKNOWN", color: "#6b6890" };
  
  // Set inline variables for animations
  const vStyle = `
    border-color: ${def.color};
    color: ${def.color};
    background-color: color-mix(in srgb, ${def.color} 15%, transparent);
    --v-color-20: color-mix(in srgb, ${def.color} 20%, transparent);
    --v-color-30: color-mix(in srgb, ${def.color} 30%, transparent);
    --v-color-40: color-mix(in srgb, ${def.color} 40%, transparent);
    --v-color-60: color-mix(in srgb, ${def.color} 60%, transparent);
  `;

  return `
    <div class="verdict-reveal">
      <div class="verdict-badge-box" style="${vStyle}">
        ${def.label}
      </div>
      <div class="verdict-verified">
        <span style="color:${def.color}; display:flex; align-items:center;">${ICON_CHECK}</span> VERIFIED OUTPUT
      </div>
    </div>
  `;
}

export function riskFromVerdict(verdict) {
  // Required by some existing app.js logic potentially
  return { cls: "moderate", label: "Moderate" };
}

export function verdictBadge(verdict) {
  const label = (verdict || "RISKY").toLowerCase();
  return `<span class="badge ${label}">${verdict || "RISKY"}</span>`;
}

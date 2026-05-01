/**
 * MistakePanel — collapsible section that shows pending BAD-verdict responses
 * fetched from GET /api/mistakes/pending.
 *
 * Mounts into any container element and manages its own state internally.
 * Auto-refreshes the pending count every 30 seconds.
 */

// ── Module-level singleton state ───────────────────────────────────────────
let _expanded     = false;
let _mistakes     = [];          // cached list from last fetch
let _pendingCount = 0;           // polled count
let _refreshTimer = null;        // setInterval handle
let _rootEl       = null;        // mounted container

// ── API helpers ────────────────────────────────────────────────────────────
async function fetchPending() {
  try {
    const res = await fetch("/api/mistakes/pending");
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

async function postReview(id, note) {
  await fetch(`/api/mistakes/${id}/review`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ note }),
  });
}

// ── Render helpers ─────────────────────────────────────────────────────────
function trunc(str, n) {
  return str && str.length > n ? str.slice(0, n) + "…" : (str ?? "");
}

function renderCard(mistake) {
  const card = document.createElement("div");
  card.className  = "mistake-card";
  card.dataset.id = mistake.id;

  // Query — expandable
  const queryFull    = mistake.user_query  ?? "";
  const queryShort   = trunc(queryFull, 100);
  const queryTrunc   = queryFull.length > 100;
  const responsePrev = trunc(mistake.llm_response ?? "", 150);

  card.innerHTML = `
    <div class="mistake-meta">
      <span class="mistake-badge company">${mistake.company_id ?? "—"}</span>
      <span class="mistake-badge role">${mistake.role ?? "—"}</span>
      <span class="mistake-badge domain">${mistake.domain ?? "general"}</span>
      <span class="mistake-time">${new Date(mistake.flagged_at).toLocaleString()}</span>
    </div>

    <div class="mistake-query" data-full="${encodeURIComponent(queryFull)}" data-expanded="false">
      <span class="mistake-label">Query</span>
      <span class="mistake-query-text">${queryShort}</span>
      ${queryTrunc ? `<button class="mistake-expand-btn">show more</button>` : ""}
    </div>

    <div class="mistake-response">
      <span class="mistake-label">Response</span>
      <span class="mistake-response-text">${responsePrev}</span>
    </div>

    <div class="mistake-reason">
      <span class="mistake-label">Reason</span>
      <span>${mistake.verdict_reason ?? "—"}</span>
    </div>

    <div class="mistake-actions">
      <button class="mistake-btn reviewed" data-action="reviewed">✓ Mark Reviewed</button>
      <button class="mistake-btn bad"      data-action="bad">✗ Confirm Bad</button>
    </div>
  `;

  // Expand/collapse query text
  const expandBtn = card.querySelector(".mistake-expand-btn");
  if (expandBtn) {
    expandBtn.onclick = () => {
      const queryEl  = card.querySelector(".mistake-query");
      const textEl   = card.querySelector(".mistake-query-text");
      const isExpanded = queryEl.dataset.expanded === "true";
      textEl.textContent         = isExpanded ? queryShort : decodeURIComponent(queryEl.dataset.full);
      queryEl.dataset.expanded   = (!isExpanded).toString();
      expandBtn.textContent      = isExpanded ? "show more" : "show less";
    };
  }

  // Review actions
  card.querySelector(".mistake-actions").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;

    const action = btn.dataset.action;
    const note   = action === "bad" ? "confirmed_bad" : "reviewed";

    btn.disabled    = true;
    btn.textContent = "…";

    await postReview(mistake.id, note);

    // Remove with animation
    card.classList.add(action === "bad" ? "mistake-card--flash-bad" : "mistake-card--fade");
    setTimeout(() => {
      card.remove();
      _mistakes     = _mistakes.filter((m) => m.id !== mistake.id);
      _pendingCount = Math.max(0, _pendingCount - 1);
      _updateHeader();

      // Show empty state if no cards remain
      const list = _rootEl?.querySelector(".mistake-list");
      if (list && list.children.length === 0) {
        list.innerHTML = `<div class="mistake-empty">✓ No flagged responses</div>`;
      }
    }, 350);
  });

  return card;
}

function _updateHeader() {
  const header = _rootEl?.querySelector(".mistake-header-count");
  if (header) header.textContent = `(${_pendingCount} pending review)`;
}

async function _loadAndRender() {
  _mistakes     = await fetchPending();
  _pendingCount = _mistakes.length;
  _updateHeader();

  const list = _rootEl?.querySelector(".mistake-list");
  if (!list) return;

  list.innerHTML = "";

  if (_mistakes.length === 0) {
    list.innerHTML = `<div class="mistake-empty">✓ No flagged responses</div>`;
    return;
  }

  _mistakes.forEach((m) => list.appendChild(renderCard(m)));
}

// ── Public API ─────────────────────────────────────────────────────────────
/**
 * Mount the MistakePanel into `container`.
 * Safe to call on every renderRightPanel — diffs by re-using existing mount.
 */
export function mountMistakePanel(container) {
  // Avoid re-creating DOM if already mounted into this element
  if (_rootEl === container && container.querySelector(".mistake-panel")) return;

  _rootEl = container;
  container.innerHTML = `
    <div class="mistake-panel">
      <button class="mistake-toggle" id="mistakeToggle">
        <span class="mistake-toggle-icon">▶</span>
        <span class="mistake-toggle-title">⚠ Flagged Responses</span>
        <span class="mistake-header-count">(… pending review)</span>
      </button>
      <div class="mistake-body" id="mistakeBody" style="display:none;">
        <div class="mistake-list"></div>
      </div>
    </div>
  `;

  // Poll count even while collapsed
  _pollCount();
  if (_refreshTimer) clearInterval(_refreshTimer);
  _refreshTimer = setInterval(_pollCount, 30_000);

  container.querySelector("#mistakeToggle").onclick = async () => {
    _expanded = !_expanded;
    const body = container.querySelector("#mistakeBody");
    const icon = container.querySelector(".mistake-toggle-icon");

    body.style.display = _expanded ? "block" : "none";
    icon.textContent   = _expanded ? "▼" : "▶";

    if (_expanded) await _loadAndRender();
  };
}

async function _pollCount() {
  try {
    const res = await fetch("/api/mistakes/pending");
    if (!res.ok) return;
    const data = await res.json();
    _pendingCount = Array.isArray(data) ? data.length : 0;
    _updateHeader();
  } catch { /* silent */ }
}

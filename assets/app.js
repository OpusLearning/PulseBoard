/* Pulseboard frontend — minimal, robust, no build step */

const ENDPOINT = "/data/pulse.json";
const EDITOR_ENDPOINT = "/data/editor.json";

function $(sel) { return document.querySelector(sel); }

function safeText(s) {
  if (s === null || s === undefined) return "";
  return String(s);
}

function parseDate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

function timeAgo(iso) {
  const d = parseDate(iso);
  if (!d) return "—";
  const diff = Date.now() - d.getTime();
  const sec = Math.max(0, Math.floor(diff / 1000));
  const min = Math.floor(sec / 60);
  const hr = Math.floor(min / 60);
  const day = Math.floor(hr / 24);

  if (sec < 60) return `${sec}s ago`;
  if (min < 60) return `${min}m ago`;
  if (hr < 48) return `${hr}h ago`;
  return `${day}d ago`;
}

function fmtUTC(iso) {
  const d = parseDate(iso);
  if (!d) return "—";
  return d.toISOString().replace("T", " ").replace(/\.\d+Z$/, "Z");
}

function validatePulse(data) {
  const errs = [];
  if (!data || typeof data !== "object") errs.push("pulse.json is not an object");
  if (!data || !Array.isArray(data.items)) errs.push("pulse.json missing items[]");
  return errs;
}

async function fetchPulse() {
  const res = await fetch(ENDPOINT, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load pulse.json (${res.status})`);
  const data = await res.json();
  const errs = validatePulse(data);
  if (errs.length) throw new Error(errs.join("; "));
  return data;
}

function validateEditor(data) {
  const errs = [];
  if (!data || typeof data !== "object") errs.push("editor.json is not an object");
  if (data && typeof data.editors_brief !== "string") errs.push("editor.json missing editors_brief");
  if (data && !Array.isArray(data.top_themes)) errs.push("editor.json missing top_themes[]");
  if (data && (!data.most_memeable || typeof data.most_memeable !== "object")) errs.push("editor.json missing most_memeable");
  return errs;
}

async function fetchEditor() {
  const res = await fetch(EDITOR_ENDPOINT, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load editor.json (${res.status})`);
  const data = await res.json();
  const errs = validateEditor(data);
  if (errs.length) throw new Error(errs.join("; "));
  return data;
}

function renderEditor(ed) {
  const briefTitle = document.querySelector("#brief-title");
  const briefText = document.querySelector("#brief-text");
  const memeable = document.querySelector("#memeable");
  const themes = document.querySelector("#themes");

  if (!briefTitle || !briefText || !memeable || !themes) return;

  // Title: keep it simple for now; later we can use a daily headline.
  briefTitle.textContent = safeText(ed.voice || "Pulseboard");
  briefText.textContent = safeText(ed.editors_brief || "");

  const mm = ed.most_memeable || {};
  const headline = safeText(mm.headline || "");
  const link = safeText(mm.link || "");
  memeable.innerHTML = link
    ? `Most memeable: <a href="${escapeAttr(link)}" target="_blank" rel="noreferrer">${escapeHTML(headline)}</a>`
    : `Most memeable: ${escapeHTML(headline)}`;

  const top = (ed.top_themes || []).slice(0, 4).map(t => safeText(t.theme)).filter(Boolean);
  themes.textContent = top.length ? `Top themes: ${top.join(" · ")}` : "Top themes: —";
}

}

function groupBySource(items) {
  const map = new Map();
  for (const it of items) {
    const src = safeText(it.source || "Unknown");
    if (!map.has(src)) map.set(src, []);
    map.get(src).push(it);
  }
  return map;
}

function sortNewestFirst(items) {
  return [...items].sort((a, b) => {
    const da = parseDate(a.published_utc)?.getTime() ?? 0;
    const db = parseDate(b.published_utc)?.getTime() ?? 0;
    return db - da;
  });
}

function card(it) {
  const title = safeText(it.title || "(untitled)");
  const link = safeText(it.link || "#");
  const src = safeText(it.source || "Unknown");
  const ago = timeAgo(it.published_utc);
  const utc = fmtUTC(it.published_utc);

  // deterministic accent choice per-source for subtle structure
  const accent = (hash(src) % 3);
  const accentClass = accent === 0 ? "a0" : accent === 1 ? "a1" : "a2";

  return `
    <a class="card ${accentClass}" href="${escapeAttr(link)}" target="_blank" rel="noreferrer">
      <div class="card-top">
        <span class="source">${escapeHTML(src)}</span>
        <span class="when" title="${escapeAttr(utc)}">${escapeHTML(ago)}</span>
      </div>
      <div class="title">${escapeHTML(title)}</div>
    </a>
  `;
}

function section(source, items) {
  const count = items.length;
  const body = items.map(card).join("");
  return `
    <section class="group" aria-label="${escapeAttr(source)}">
      <div class="group-head">
        <h2>${escapeHTML(source)}</h2>
        <div class="group-meta">${count} item${count === 1 ? "" : "s"}</div>
      </div>
      <div class="cards">${body}</div>
    </section>
  `;
}

function render(data) {
  const grid = $("#grid");
  const stamp = $("#stamp");
  const countEl = $("#count");
  const meta = $("#meta");

  const items = sortNewestFirst(data.items || []);
  const groups = groupBySource(items);

  stamp.textContent = `Updated: ${timeAgo(data.generated_utc)}`;
  stamp.title = `UTC: ${fmtUTC(data.generated_utc)}`;
  countEl.textContent = `${items.length} items`;

  const parts = [];
  for (const [src, arr] of groups.entries()) {
    parts.push(section(src, arr));
  }

  grid.innerHTML = parts.join("");
  meta.textContent = `Endpoint: ${ENDPOINT}`;
}

function renderError(err) {
  const grid = $("#grid");
  const stamp = $("#stamp");
  const countEl = $("#count");
  stamp.textContent = "Update failed";
  countEl.textContent = "—";
  grid.innerHTML = `
    <section class="group">
      <div class="group-head"><h2>Error</h2></div>
      <div class="cards">
        <div class="card a2" role="alert">
          <div class="card-top"><span class="source">Pulseboard</span><span class="when">—</span></div>
          <div class="title">${escapeHTML(String(err && err.message ? err.message : err))}</div>
        </div>
      </div>
    </section>
  `;
}

// Helpers
function hash(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0);
}

function escapeHTML(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttr(s) {
  return escapeHTML(s);
}

(async () => {
  try {
    const data = await fetchPulse();
    render(data);

    try {
      const ed = await fetchEditor();
      renderEditor(ed);
    } catch (e2) {
      // editor.json is optional; ignore failures for now
    }
  } catch (e) {
    renderError(e);
  }
})();

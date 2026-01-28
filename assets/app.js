/* Pulseboard Today frontend — static-first, resilient */

const TODAY_ENDPOINT = "/data/today.json";

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

function escapeHTML(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttr(s) { return escapeHTML(s); }

async function fetchToday() {
  const res = await fetch(TODAY_ENDPOINT, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load today.json (${res.status})`);
  return await res.json();
}

function getLens() {
  return localStorage.getItem("pb_lens") || "neutral";
}

function setLens(v) {
  localStorage.setItem("pb_lens", v);
}

function meterInit() {
  const state = { brief: false, audio: false, cards: false };

  function pct() {
    const done = Object.values(state).filter(Boolean).length;
    return Math.round((done / 3) * 100);
  }

  function render() {
    const p = pct();
    const fill = $("#meter-fill");
    const pctEl = $("#meter-pct");
    if (fill) fill.style.width = `${p}%`;
    if (pctEl) pctEl.textContent = `${p}%`;

    const steps = $("#meter-steps");
    if (steps) {
      for (const el of steps.querySelectorAll("span[data-step]")) {
        const k = el.getAttribute("data-step");
        el.classList.toggle("done", !!state[k]);
      }
    }

    const done = $("#done");
    if (done) done.hidden = p < 100;
  }

  function mark(k) { if (!state[k]) { state[k] = true; render(); } }

  render();
  return { mark };
}

function renderToday(today) {
  const stamp = $("#stamp");
  const count = $("#count");
  const title = $("#today-title");
  const kicker = $("#today-kicker");
  const angle = $("#today-angle");
  const updated = $("#updated");

  const lens = getLens();
  const v = (today.variants && today.variants[lens]) || (today.variants && today.variants.neutral) || null;

  const day = safeText(today.date || "");
  if (kicker) kicker.textContent = `Your Pulse (${day})`;
  if (title) title.textContent = "You’re up to speed.";
  if (angle) angle.textContent = v ? safeText(v.angle) : "";

  if (stamp) {
    stamp.textContent = `Updated: ${timeAgo(today.updated_utc)}`;
    stamp.title = safeText(today.updated_utc);
  }

  if (updated) updated.textContent = `Updated ${timeAgo(today.updated_utc)}`;

  // The 3
  const the3 = $("#the3");
  if (the3) {
    const items = today.the3 || [];
    if (count) count.textContent = "3 stories";
    the3.innerHTML = items.map((s, i) => {
      const link = safeText(s.link || "#");
      const conf = Number(s.confidence || 0);
      const confLabel = conf >= 0.75 ? "High" : conf >= 0.55 ? "Medium" : "Low";
      const insight = safeText(s.summary || "");
      const why = safeText(s.why_it_matters || "");
      const watch = safeText(s.watch_for || "");
      const say = safeText(s.what_to_say || "");
      const source = safeText(s.source || "");

      return `
        <article class="t3">
          <div class="t3-k">${i+1}</div>
          <div class="t3-b">
            <div class="t3-h">${escapeHTML(safeText(s.title))}</div>
            <div class="t3-insight">${escapeHTML(insight)}</div>

            <details class="t3-more">
              <summary>Details</summary>
              <div class="t3-r"><span>Why it matters</span> ${escapeHTML(why)}</div>
              <div class="t3-r"><span>Watch for</span> ${escapeHTML(watch)}</div>
              <div class="t3-r"><span>What to say</span> ${escapeHTML(say)}</div>
            </details>

            <div class="trust">
              <div class="trust-row"><span class="trust-k">Confidence</span> <span class="trust-v">${confLabel}</span></div>
              <div class="trust-row"><span class="trust-k">Why</span> <span class="trust-v">${escapeHTML(safeText(s.confidence_reason))}</span></div>
              <div class="trust-row"><span class="trust-k">Source</span> <span class="trust-v">${escapeHTML(source)}</span></div>
            </div>

            <div class="t3-f">
              <a href="${escapeAttr(link)}" target="_blank" rel="noreferrer">Open source</a>
            </div>
          </div>
        </article>
      `;
    }).join("");
  }
}

function renderAudio(today, meter) {
  const player = $("#audio-player");
  const meta = $("#audio-meta");
  if (!player || !meta) return;

  const latest = safeText(today.audio && today.audio.latest);
  const transcript = safeText(today.audio && today.audio.transcript);
  if (!latest) {
    meta.textContent = "Audio unavailable.";
    return;
  }
  player.src = latest.startsWith("/") ? latest : `/${latest}`;
  meta.innerHTML = `Transcript: <a href="/${escapeAttr(transcript)}" target="_blank" rel="noreferrer">open</a> · <a href="${escapeAttr(player.src)}">download</a>`;

  player.addEventListener("play", () => meter.mark("audio"), { once: true });
}

function renderCards(today, meter) {
  const grid = $("#cards");
  if (!grid) return;

  const cards = today.cards || [];
  const maxCards = Math.min(cards.length, 7);
  grid.innerHTML = cards.slice(0, maxCards).map((png, idx) => {
    const url = '/' + safeText(png).replace(/^\/+/, '');
    return `
      <figure class="cardimg cardimg-wide" style="scroll-snap-align:start">
        <a href="${escapeAttr(url)}" target="_blank" rel="noreferrer">
          <img src="${escapeAttr(url)}" alt="Pulseboard shareable" loading="lazy" decoding="async" />
        </a>
        <figcaption>
          <span class="muted">Card ${idx+1}</span>
          <a class="dl" href="${escapeAttr(url)}" download>download</a>
        </figcaption>
      </figure>
    `;
  }).join('');

  // mark cards when any card is clicked
  grid.addEventListener('click', () => meter.mark('cards'), { once: true });
}

function renderError(err) {
  const title = $("#today-title");
  const angle = $("#today-angle");
  if (title) title.textContent = "Pulse unavailable";
  if (angle) angle.textContent = safeText(err && err.message ? err.message : err);
  const meta = $("#meta");
  if (meta) meta.textContent = `Endpoint: ${TODAY_ENDPOINT}`;
}

(async () => {
  const meter = meterInit();

  const lensSel = $("#lens");
  if (lensSel) {
    lensSel.value = getLens();
    lensSel.addEventListener('change', () => {
      setLens(lensSel.value);
      // re-render from cached today
      if (window.__pb_today) renderToday(window.__pb_today);
    });
  }

  try {
    const today = await fetchToday();
    window.__pb_today = today;

    renderToday(today);
    renderAudio(today, meter);
    renderCards(today, meter);

    // brief counts as done once today rendered
    meter.mark('brief');

    const meta = $("#meta");
    if (meta) meta.textContent = `Endpoint: ${TODAY_ENDPOINT}`;

  } catch (e) {
    renderError(e);
  }
})();

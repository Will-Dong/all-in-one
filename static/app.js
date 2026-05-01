const state = {
  snapshot: null,
  opportunities: [],
  bots: [],
  trades: [],
  logs: [],
};

const fmtUsd = (value) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value || 0);

const fmtTime = (ms) => {
  if (!ms) return "never";
  return new Date(ms).toLocaleString();
};

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function loadAll({ scan = false } = {}) {
  setBusy(true);
  try {
    if (scan) {
      await api("/api/scan", { method: "POST", body: "{}" });
    }
    const [snapshot, opportunities, bots, trades, logs] = await Promise.all([
      api("/api/snapshot"),
      api("/api/opportunities"),
      api("/api/bots"),
      api("/api/trades"),
      api("/api/logs"),
    ]);
    state.snapshot = snapshot.snapshot;
    state.opportunities = opportunities.opportunities;
    state.bots = bots.bots;
    state.trades = trades.trades;
    state.logs = logs.logs;
    render();
  } catch (err) {
    alert(err.message);
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = isBusy;
  });
}

function render() {
  renderMetrics();
  renderOpportunities();
  renderBots();
  renderTrades();
  renderLogs();
}

function renderMetrics() {
  const byKind = state.opportunities.reduce((acc, op) => {
    acc[op.kind] = (acc[op.kind] || 0) + 1;
    return acc;
  }, {});
  const maxEdge = state.opportunities.reduce((best, op) => Math.max(best, op.edge_bps || 0), 0);
  const runningBots = state.bots.filter((bot) => bot.status === "running").length;
  const paperNotional = state.trades.reduce((sum, trade) => sum + trade.notional_usd, 0);

  const metrics = [
    ["Opportunities", state.opportunities.length, Object.entries(byKind).map(([k, v]) => `${k}: ${v}`).join(" · ")],
    ["Max Edge", `${maxEdge.toFixed(0)} bps`, "fee and slippage not fully modeled"],
    ["Running Bots", runningBots, "paper mode only"],
    ["Paper Notional", fmtUsd(paperNotional), `${state.trades.length} simulated fills`],
  ];

  document.getElementById("overview").innerHTML = metrics
    .map(
      ([label, value, helper]) => `
        <article class="metric">
          <span>${label}</span>
          <strong>${value}</strong>
          <p class="muted">${helper || ""}</p>
        </article>
      `
    )
    .join("");
}

function renderOpportunities() {
  document.getElementById("snapshotTime").textContent = state.snapshot
    ? `Last snapshot ${fmtTime(state.snapshot.captured_at_ms)}`
    : "";

  const rows = state.opportunities.map((op) => {
    const apr = op.expected_apr === null || op.expected_apr === undefined ? "n/a" : `${op.expected_apr.toFixed(2)}%`;
    return `
      <tr>
        <td><span class="kind">${op.kind}</span></td>
        <td><strong>${escapeHtml(op.title)}</strong></td>
        <td>${op.edge_bps.toFixed(1)} bps</td>
        <td>${apr}</td>
        <td>${fmtUsd(op.capacity_usd)}</td>
        <td><span class="risk ${op.risk}">${op.risk}</span></td>
        <td>${escapeHtml(op.action)}</td>
      </tr>
    `;
  });
  document.getElementById("opportunityRows").innerHTML =
    rows.join("") || `<tr><td colspan="7" class="muted">No opportunities above thresholds.</td></tr>`;
}

function renderBots() {
  document.getElementById("botGrid").innerHTML = state.bots
    .map(
      (bot) => `
        <article class="bot-card">
          <div class="bot-title">
            <div>
              <h3>${escapeHtml(bot.name)}</h3>
              <p class="muted">${bot.config.kinds.join(", ")} · min edge ${bot.config.min_edge_bps} bps</p>
            </div>
            <span class="status ${bot.status}">${bot.status}</span>
          </div>
          <div class="bot-meta">
            <div><small>Mode</small><strong>${bot.mode}</strong></div>
            <div><small>Scans</small><strong>${bot.scans}</strong></div>
            <div><small>Trades</small><strong>${bot.paper_trades}</strong></div>
          </div>
          <p class="muted">Heartbeat: ${fmtTime(bot.last_heartbeat_ms)}</p>
          <div class="bot-controls">
            <button onclick="botAction('${bot.bot_id}', 'start')">Start</button>
            <button class="secondary" onclick="botAction('${bot.bot_id}', 'pause')">Pause</button>
            <button class="secondary" onclick="botAction('${bot.bot_id}', 'stop')">Stop</button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderTrades() {
  const rows = state.trades.map(
    (trade) => `
      <tr>
        <td>${escapeHtml(trade.bot_id)}</td>
        <td><span class="kind">${escapeHtml(trade.kind)}</span></td>
        <td>${fmtUsd(trade.notional_usd)}</td>
        <td>${trade.edge_bps.toFixed(1)} bps</td>
        <td>${escapeHtml(trade.status)}</td>
        <td>${fmtTime(trade.created_at_ms)}</td>
      </tr>
    `
  );
  document.getElementById("tradeRows").innerHTML =
    rows.join("") || `<tr><td colspan="6" class="muted">No paper trades yet. Start a bot and scan.</td></tr>`;
}

function renderLogs() {
  document.getElementById("logList").innerHTML =
    state.logs
      .map(
        (log) => `
          <div class="log-item">
            <strong>${escapeHtml(log.bot_id)}</strong>
            <span>${escapeHtml(log.event_type)}</span>
            <span>${escapeHtml(log.message)}</span>
            <span class="muted">${fmtTime(log.created_at_ms)}</span>
          </div>
        `
      )
      .join("") || `<div class="log-item muted">No logs yet.</div>`;
}

async function botAction(botId, action) {
  setBusy(true);
  try {
    await api(`/api/bots/${botId}/${action}`, {
      method: "POST",
      body: JSON.stringify({ mode: "paper" }),
    });
    await loadAll();
  } catch (err) {
    alert(err.message);
  } finally {
    setBusy(false);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.getElementById("scanBtn").addEventListener("click", () => loadAll({ scan: true }));
document.getElementById("refreshBtn").addEventListener("click", () => loadAll());

loadAll();
setInterval(() => loadAll(), 30000);

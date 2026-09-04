const DATASET = window.DATASET;

const get = (id) => document.getElementById(id);
const setVisible = (id, visible) => { get(id).hidden = !visible; };
const escapeHtml = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");

function renderMetrics(metrics) {
  const box = get("metricsBox");
  if (!metrics) { box.innerHTML = '<div class="small">No metrics.</div>'; return; }
  const format = (value) => value == null ? "-" : value.toFixed(1);
  box.innerHTML = `<div class="metric-pills"><span class="pill">Total: ${metrics.total_requests}</span><span class="pill">Success: ${metrics.success_requests}</span><span class="pill">Failed: ${metrics.failed_requests}</span></div><div class="small">Latency (ms): last <span class="mono">${format(metrics.last_latency_ms)}</span>, avg <span class="mono">${format(metrics.avg_latency_ms)}</span>, p95 <span class="mono">${format(metrics.p95_latency_ms)}</span></div>`;
}

async function refreshMetrics() {
  const response = await fetch("api/metrics");
  renderMetrics(await response.json());
}

function initSamples() {
  const select = get("sampleSelect");
  select.innerHTML = '<option value="">- select -</option>';
  DATASET.forEach(([text, gold], index) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = `#${index + 1} (${gold}) ${text.slice(0, 70)}${text.length > 70 ? "..." : ""}`;
    select.appendChild(option);
  });
}

function showError(id, heading, message) {
  get(id).innerHTML = `<strong>${heading}</strong><br><div class="small">${escapeHtml(message)}</div>`;
  setVisible(id, true);
}

get("fillBtn").addEventListener("click", () => {
  const index = get("sampleSelect").value;
  if (index) {
    const sample = DATASET[Number(index)];
    get("textInput").value = sample[0];
  }
});

get("sampleSelect").addEventListener("change", () => {
  const index = get("sampleSelect").value;
});

get("scoreBtn").addEventListener("click", async () => {
  setVisible("singleError", false); setVisible("singleResult", false);
  const serviceUrl = get("serviceUrl").value.trim();
  const text = get("textInput").value;
  if (!serviceUrl) return showError("singleError", "Could not score the text.", "Please provide the base URL of the external service.");
  if (!text.trim()) return showError("singleError", "Could not score the text.", "Please enter some text to score.");
  const response = await fetch("api/score", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ service_url: serviceUrl, text }) });
  const data = await response.json(); await refreshMetrics();
  if (!response.ok) return showError("singleError", "Could not score the text.", data.detail || "Unknown error.");
  get("singleResult").innerHTML = `<span class="pill">Score: <span class="mono">${data.score}</span></span><span class="pill">Label: <span class="mono">${data.label}</span></span><span class="pill">Latency: <span class="mono">${data.latency_ms.toFixed(1)} ms</span></span>${data.warning ? `<div class="small">${escapeHtml(data.warning)}</div>` : ""}`;
  setVisible("singleResult", true);
});

get("batchBtn").addEventListener("click", async () => {
  setVisible("batchError", false); setVisible("batchSummary", false); setVisible("batchTableWrap", false); get("batchTableWrap").innerHTML = "";
  const serviceUrl = get("serviceUrl").value.trim();
  if (!serviceUrl) return showError("batchError", "Batch run failed.", "Please provide the base URL of the external service.");
  const response = await fetch("api/batch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ service_url: serviceUrl, dataset: DATASET }) });
  const data = await response.json(); await refreshMetrics();
  if (!response.ok) return showError("batchError", "Batch run failed.", data.detail || "Unknown error.");
  get("batchSummary").innerHTML = `<span class="pill">Items: <span class="mono">${data.n}</span></span><span class="pill">Accuracy: <span class="mono">${(100 * data.accuracy).toFixed(1)}%</span></span><span class="pill">Avg latency/item: <span class="mono">${data.avg_latency_ms.toFixed(1)} ms</span></span>`;
  const rows = data.rows.map((row, index) => `<tr><td class="mono">${index + 1}</td><td>${escapeHtml(row.text)}</td><td class="mono">${row.gold}</td><td class="mono">${row.score ?? "-"}</td><td class="mono">${row.pred ?? "-"}</td><td class="mono">${row.ok ? "yes" : "no"}</td><td class="mono">${row.latency_ms.toFixed(1)}</td></tr>`).join("");
  get("batchTableWrap").innerHTML = `<table><thead><tr><th>#</th><th>Text</th><th>Gold</th><th>Score</th><th>Pred</th><th>OK</th><th>Latency (ms)</th></tr></thead><tbody>${rows}</tbody></table>`;
  setVisible("batchSummary", true); setVisible("batchTableWrap", true);
});

initSamples();
refreshMetrics();

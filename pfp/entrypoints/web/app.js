"use strict";

const API = "/api/workbench";
const SVG_NS = "http://www.w3.org/2000/svg";
const MAX_VISIBLE_CANDIDATES = 300;
const MAX_VISIBLE_EVENTS = 100;

const $ = (id) => document.getElementById(id);

const state = {
  fixtures: [],
  fixture: null,
  runId: null,
  snapshot: null,
  submittedInput: null,
  apiOnline: false,
  events: new Map(),
  selectedCandidateId: null,
  eventSource: null,
  pollTimer: null,
  refreshTimer: null,
  refreshPending: false,
  starting: false,
};

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined && content !== null) node.textContent = String(content);
  return node;
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  return node;
}

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function count(value) {
  return Math.max(0, Math.floor(number(value)));
}

function formatCount(value) {
  return new Intl.NumberFormat().format(count(value));
}

function shortId(value, length = 18) {
  const text = String(value ?? "—");
  return text.length > length ? `${text.slice(0, length - 1)}…` : text;
}

function asText(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.map(asText).join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function setConnection(label, mode) {
  const target = $("api-state");
  target.className = `connection-state ${mode || ""}`;
  target.lastChild.textContent = label;
}

function showMessage(message) {
  const box = $("global-message");
  box.textContent = message;
  box.hidden = false;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => { box.hidden = true; }, 7000);
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...(options.headers || {}) },
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`Host returned a non-JSON response (${response.status}).`);
  }
  if (!response.ok) {
    const detail = data.detail || data.error || data.message || `HTTP ${response.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function setFixture(fixtureId) {
  state.fixture = state.fixtures.find((item) => String(item.id) === String(fixtureId)) || null;
  const fixture = state.fixture;
  $("fixture-description").textContent = fixture?.description || "Choose a finite graph to inspect.";
  const meta = $("fixture-meta");
  meta.replaceChildren();
  if (fixture) {
    const vertices = Array.isArray(fixture.vertices) ? fixture.vertices.length : count(fixture.vertices);
    const edges = Array.isArray(fixture.edges) ? fixture.edges.length : count(fixture.edges);
    for (const [label, value] of [["Vertices", vertices], ["Edges", edges], ["Scope", fixture.scope || "finite graph"]]) {
      const chip = element("span", "meta-chip");
      chip.append(element("strong", "", label), document.createTextNode(asText(value)));
      meta.append(chip);
    }
  }
  if (!state.snapshot) renderGraph(fixture);
  if (fixture) fillPacketFromControls();
  updateStartButton();
}

function fillPacketFromControls() {
  if (!state.fixture) return;
  $("input-yaml").value = [
    "schema: symbol_game.finite_gauge_input.v1",
    `fixture_id: ${state.fixture.id}`,
    `node_budget: ${$("node-budget").value}`,
    `pace_ms: ${$("pace-ms").value}`,
  ].join("\n");
  updateStartButton();
}

async function loadFixtures() {
  try {
    const result = await request(`${API}/fixtures`);
    if (!Array.isArray(result.fixtures)) throw new Error("The fixture response is missing its fixture list.");
    state.apiOnline = true;
    state.fixtures = result.fixtures;
    const selector = $("fixture-select");
    selector.replaceChildren();
    if (state.fixtures.length === 0) {
      selector.append(element("option", "", "No fixtures available"));
      $("run-hint").textContent = "The host has no graph fixtures.";
    } else {
      for (const fixture of state.fixtures) {
        const option = element("option", "", fixture.title || fixture.id);
        option.value = String(fixture.id);
        selector.append(option);
      }
      selector.disabled = false;
      setFixture(selector.value);
      $("run-hint").textContent = "Ready for a bounded search";
    }
    setConnection("Host connected", "online");
  } catch (error) {
    state.apiOnline = false;
    setConnection("Host unavailable", "offline");
    $("fixture-select").replaceChildren(element("option", "", "Host unavailable"));
    $("run-hint").textContent = "Start the local API to load fixtures";
    showMessage(`Could not load fixtures: ${error.message}`);
  }
  updateStartButton();
}

function updateStartButton() {
  const running = state.starting || (state.runId && (!state.snapshot || !isTerminal(state.snapshot.status)));
  $("start-button").disabled = !state.apiOnline || !$("input-yaml").value.trim() || !!running;
  $("start-button").firstElementChild.textContent = state.starting ? "Starting…" : running ? "Search running" : "Start search";
  $("fixture-select").disabled = !state.fixtures.length || !!running;
  $("node-budget").disabled = !!running;
  $("pace-ms").disabled = !!running;
  $("input-yaml").disabled = !!running;
}

function isRunning(status) {
  const value = String(status || "").toLowerCase();
  return ["running", "pending", "queued", "starting", "created", "scheduled", "in_progress", "in-progress"].includes(value);
}

function isTerminal(status) {
  const value = String(status || "").toLowerCase();
  return ["gauge_verified", "restricted_obstruction", "unknown", "failed"].includes(value);
}

function resetRun() {
  disconnectRun();
  state.snapshot = null;
  state.runId = null;
  state.submittedInput = null;
  state.events.clear();
  state.selectedCandidateId = null;
  $("candidate-inspector").hidden = true;
  $("submitted-input").hidden = true;
  $("global-message").hidden = true;
}

async function startRun() {
  if (state.starting || !state.apiOnline) return;
  const inputYaml = $("input-yaml").value;
  if (!inputYaml.trim()) {
    showMessage("Enter a YAML input packet to start the search.");
    $("input-yaml").focus();
    return;
  }

  resetRun();
  state.submittedInput = inputYaml;
  $("submitted-input-code").textContent = inputYaml;
  $("submitted-input").hidden = false;
  state.starting = true;
  updateStartButton();
  $("run-hint").textContent = "Creating the bounded run";
  try {
    const result = await request(`${API}/runs`, {
      method: "POST",
      body: JSON.stringify({ input_yaml: inputYaml }),
    });
    if (!result.run_id) throw new Error("The host did not return a run ID.");
    state.runId = String(result.run_id);
    if (result.snapshot) renderSnapshot(result.snapshot);
    $("run-hint").textContent = `Run ${shortId(state.runId, 24)} created`;
    if (!state.snapshot || !isTerminal(state.snapshot.status)) connectRun();
    scheduleRefresh();
  } catch (error) {
    $("run-hint").textContent = "The run could not start";
    showMessage(`Could not start search: ${error.message}`);
  } finally {
    state.starting = false;
    updateStartButton();
  }
}

function disconnectRun() {
  if (state.eventSource) { state.eventSource.close(); state.eventSource = null; }
  if (state.pollTimer) { clearInterval(state.pollTimer); state.pollTimer = null; }
  if (state.refreshTimer) { clearTimeout(state.refreshTimer); state.refreshTimer = null; }
}

function connectRun() {
  if (!state.runId) return;
  const runId = state.runId;
  if (typeof EventSource !== "undefined") {
    const source = new EventSource(`${API}/runs/${encodeURIComponent(runId)}/events`);
    state.eventSource = source;
    source.onopen = () => { if (state.runId === runId) setConnection("Live stream connected", "online"); };
    const receive = (message) => {
      if (state.runId !== runId) return;
      try {
        const event = JSON.parse(message.data);
        addEvent(event);
        renderEvents();
        scheduleRefresh();
      } catch {
        showMessage("The host sent an unreadable event; the snapshot will be refreshed.");
        scheduleRefresh();
      }
    };
    source.addEventListener("update", receive);
    source.onmessage = receive;
    source.onerror = () => {
      if (state.runId === runId && (!state.snapshot || !isTerminal(state.snapshot.status))) {
        setConnection("Stream reconnecting · snapshots active", "");
      }
    };
  }
  state.pollTimer = setInterval(() => {
    if (state.runId === runId && (!state.snapshot || !isTerminal(state.snapshot.status))) refreshSnapshot();
  }, 1500);
}

function scheduleRefresh() {
  if (state.refreshTimer) return;
  state.refreshTimer = setTimeout(() => { state.refreshTimer = null; refreshSnapshot(); }, 100);
}

async function refreshSnapshot() {
  if (!state.runId || state.refreshPending) return;
  const runId = state.runId;
  state.refreshPending = true;
  try {
    const snapshot = await request(`${API}/runs/${encodeURIComponent(runId)}`);
    if (state.runId !== runId) return;
    renderSnapshot(snapshot);
    if (isTerminal(snapshot.status)) {
      disconnectRun();
      setConnection("Host connected", "online");
      updateStartButton();
    }
  } catch (error) {
    if (state.runId === runId) {
      setConnection("Snapshot unavailable", "offline");
      showMessage(`Could not refresh run: ${error.message}`);
    }
  } finally {
    state.refreshPending = false;
  }
}

function addEvent(event) {
  if (!event || typeof event !== "object") return;
  const key = event.seq ?? `${event.type}:${event.at}:${event.candidate_id ?? ""}`;
  state.events.set(String(key), event);
}

function renderSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object") return;
  state.snapshot = snapshot;
  if (Array.isArray(snapshot.events)) for (const event of snapshot.events) addEvent(event);
  if (snapshot.run_id && !state.runId) state.runId = String(snapshot.run_id);
  renderStatus(snapshot.status);
  renderCounts(snapshot.counts || {});
  renderGraph(snapshot.graph || state.fixture);
  renderAntiMorphisms(snapshot.anti_morphisms || {});
  renderCandidates(Array.isArray(snapshot.candidates) ? snapshot.candidates : []);
  renderEvents();
  renderScope(snapshot.scope);
  renderReceipt(snapshot.receipt, snapshot.error, snapshot.status);
  updateStartButton();
}

function renderStatus(status) {
  const pill = $("run-status");
  const label = String(status || "Ready");
  const normalized = label.toLowerCase();
  const mode = isRunning(status) ? "running" : normalized === "failed" ? "error" : normalized === "restricted_obstruction" ? "obstruction" : normalized === "unknown" ? "unknown" : isTerminal(status) ? "complete" : "idle";
  pill.className = `status-pill status-${mode}`;
  pill.lastChild.textContent = label.replace(/[_-]/g, " ");
  $("run-id").textContent = state.runId ? `RUN ${state.runId}` : "No run selected";
}

function renderCounts(counts) {
  for (const key of ["generated", "scored", "pruned", "retained", "certified"]) {
    $(`count-${key}`).textContent = formatCount(counts[key]);
  }
  $("count-anti").textContent = formatCount(counts.anti_morphisms_total);
  const generated = count(counts.generated);
  const budget = count(state.snapshot?.config?.node_budget ?? $("node-budget").value) || 1;
  $("progress-label").textContent = `${formatCount(generated)} of ${formatCount(budget)} budgeted`;
  $("progress-fill").style.width = `${Math.min(100, (generated / budget) * 100)}%`;
  const track = $("progress-track");
  track.setAttribute("aria-valuemax", String(budget));
  track.setAttribute("aria-valuenow", String(Math.min(generated, budget)));
}

function normalizeVertices(vertices) {
  if (Array.isArray(vertices)) return vertices.map((item, index) => String(typeof item === "object" && item !== null ? item.id ?? item.name ?? index : item));
  if (typeof vertices === "number") return Array.from({ length: Math.max(0, Math.min(40, count(vertices))) }, (_, index) => String(index));
  if (vertices && typeof vertices === "object") return Object.keys(vertices);
  return [];
}

function normalizeEdges(edges) {
  if (!Array.isArray(edges)) return [];
  return edges.map((edge) => {
    if (Array.isArray(edge) && edge.length >= 2) return [String(edge[0]), String(edge[1]), count(edge[2])];
    if (edge && typeof edge === "object") return [String(edge.u ?? edge.source ?? edge.from ?? edge[0]), String(edge.v ?? edge.target ?? edge.to ?? edge[1]), count(edge.odd ?? edge.parity ?? edge[2])];
    return null;
  }).filter((edge) => edge && edge[0] !== "undefined" && edge[1] !== "undefined");
}

function renderGraph(graph) {
  const view = $("graph-view");
  view.replaceChildren();
  const vertices = normalizeVertices(graph?.vertices ?? graph?.nodes);
  const edges = normalizeEdges(graph?.edges ?? graph?.links);
  const edgeCount = edges.length || count(graph?.edges);
  $("graph-size").textContent = vertices.length ? `${vertices.length} V / ${edgeCount} E` : "—";
  if (!vertices.length) {
    view.append(element("div", "empty-small", "The selected fixture has no graph drawing available."));
    return;
  }
  view.setAttribute("aria-label", `${graph?.title || state.fixture?.title || "Graph"}: ${vertices.length} vertices and ${edgeCount} edges`);
  const svg = svgElement("svg", { viewBox: "0 0 360 190", "aria-hidden": "true" });
  const positions = new Map();
  vertices.forEach((vertex, index) => {
    const angle = (-Math.PI / 2) + (index * Math.PI * 2 / vertices.length);
    positions.set(vertex, { x: 180 + Math.cos(angle) * 125, y: 95 + Math.sin(angle) * 68 });
  });
  for (const [from, to, odd] of edges) {
    const a = positions.get(from), b = positions.get(to);
    if (a && b) {
      svg.append(svgElement("line", { class: `graph-edge graph-edge-${odd ? "odd" : "even"}`, x1: a.x, y1: a.y, x2: b.x, y2: b.y }));
      const edgeLabel = svgElement("text", { class: "graph-edge-label", x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });
      edgeLabel.textContent = String(odd);
      svg.append(edgeLabel);
    }
  }
  for (const vertex of vertices) {
    const p = positions.get(vertex);
    svg.append(svgElement("circle", { class: "graph-node", cx: p.x, cy: p.y, r: 16 }));
    const label = svgElement("text", { class: "graph-label", x: p.x, y: p.y + 1 });
    label.textContent = shortId(vertex, 7);
    svg.append(label);
  }
  view.append(svg);
}

function renderAntiMorphisms(antiMorphisms) {
  const entries = Object.entries(antiMorphisms).filter(([, value]) => count(value) > 0).sort((a, b) => count(b[1]) - count(a[1]) || a[0].localeCompare(b[0]));
  const list = $("anti-list");
  list.replaceChildren();
  const total = entries.reduce((sum, [, value]) => sum + count(value), 0);
  $("anti-total").textContent = `${formatCount(total)} finding${total === 1 ? "" : "s"}`;
  if (!entries.length) {
    list.append(element("div", "empty-small", "Typed failure modes appear as candidates are checked."));
    return;
  }
  const maximum = Math.max(...entries.map(([, value]) => count(value)));
  const descriptions = {
    ODD_EDGE_UNFLIPPED: "Odd edge required opposite vertex bits",
    EVEN_EDGE_FLIPPED: "Even edge required equal vertex bits",
    MULTIPLE_PARITY_MISMATCHES: "More than one edge equation failed",
  };
  for (const [code, value] of entries) {
    const row = element("div", "anti-row");
    const label = element("span", "anti-code", code);
    if (descriptions[code]) label.append(element("span", "anti-description", descriptions[code]));
    row.append(label, element("span", "anti-count", formatCount(value)));
    const bar = element("div", "anti-bar");
    const fill = element("span");
    fill.style.width = `${Math.max(7, (count(value) / maximum) * 100)}%`;
    bar.append(fill);
    row.append(bar);
    list.append(row);
  }
}

function mismatchLabel(value) {
  if (Array.isArray(value)) return formatCount(value.length);
  if (value && typeof value === "object") return formatCount(Object.keys(value).length);
  return asText(value);
}

function bitsLabel(bits) {
  if (Array.isArray(bits)) return bits.join("");
  return asText(bits);
}

function scoreLabel(score) {
  return typeof score === "number" && Number.isFinite(score) ? score.toFixed(3) : asText(score);
}

function renderCandidates(candidates) {
  const body = $("candidate-body");
  body.replaceChildren();
  $("candidate-total").textContent = `${formatCount(candidates.length)} candidate${candidates.length === 1 ? "" : "s"}`;
  const sorted = [...candidates].sort((a, b) => number(b.index) - number(a.index)).slice(0, MAX_VISIBLE_CANDIDATES);
  const footnote = $("candidate-limit");
  footnote.hidden = candidates.length <= MAX_VISIBLE_CANDIDATES;
  if (!footnote.hidden) footnote.textContent = `Showing the latest ${MAX_VISIBLE_CANDIDATES} of ${formatCount(candidates.length)} candidates.`;
  if (!sorted.length) {
    const row = element("tr");
    const cell = element("td");
    cell.colSpan = 5;
    cell.append(element("div", "table-empty", "The ledger will populate when a run begins."));
    row.append(cell);
    body.append(row);
  }
  for (const candidate of sorted) {
    const row = element("tr", String(candidate.id) === state.selectedCandidateId ? "selected" : "");
    row.append(element("td", "", candidate.index ?? "—"));
    const name = element("td");
    const button = element("button", "candidate-select", shortId(candidate.id, 26));
    button.type = "button";
    button.title = String(candidate.id);
    button.addEventListener("click", () => selectCandidate(candidate));
    name.append(button, element("span", "candidate-bits", `bits  ${bitsLabel(candidate.bits)}`));
    row.append(name);
    row.append(element("td", "score-value", scoreLabel(candidate.score)));
    row.append(element("td", "", mismatchLabel(candidate.mismatches)));
    const dispositionCell = element("td");
    const disposition = element("span", `disposition ${String(candidate.status || "").toLowerCase()}`, candidate.status || "pending");
    dispositionCell.append(disposition);
    row.append(dispositionCell);
    body.append(row);
  }
  if (state.selectedCandidateId) {
    const selected = candidates.find((candidate) => String(candidate.id) === state.selectedCandidateId);
    if (selected) renderCandidateInspector(selected);
    else $("candidate-inspector").hidden = true;
  }
}

function selectCandidate(candidate) {
  state.selectedCandidateId = String(candidate.id);
  renderCandidates(state.snapshot?.candidates || []);
  $("candidate-inspector").hidden = false;
}

function renderCandidateInspector(candidate) {
  const content = $("inspector-content");
  content.replaceChildren();
  const list = element("dl", "inspector-grid");
  const fields = [
    ["ID", candidate.id], ["Index", candidate.index], ["Status", candidate.status],
    ["Score", scoreLabel(candidate.score)], ["Bits", bitsLabel(candidate.bits)],
    ["Mismatches", candidate.mismatches], ["Host reason", candidate.reason],
  ];
  for (const [label, value] of fields) {
    const pair = element("div", label === "Host reason" || label === "Mismatches" ? "wide" : "");
    pair.append(element("dt", "", label), element("dd", "", asText(value)));
    list.append(pair);
  }
  content.append(list);
}

function eventSummary(event) {
  const data = event.data && typeof event.data === "object" ? event.data : {};
  const parts = [];
  if (event.candidate_id) parts.push(shortId(event.candidate_id, 24));
  if (data.candidate && typeof data.candidate === "object") {
    const candidate = data.candidate;
    if (candidate.bits) parts.push(`bits ${bitsLabel(candidate.bits)}`);
    if (candidate.score !== null && candidate.score !== undefined) parts.push(`score ${scoreLabel(candidate.score)}`);
    if (Array.isArray(candidate.mismatches) && candidate.mismatches.length) parts.push(`${candidate.mismatches.length} mismatched edge${candidate.mismatches.length === 1 ? "" : "s"}`);
    if (candidate.reason) parts.push(candidate.reason);
  }
  for (const key of ["code", "status", "reason", "message", "error"]) {
    if (data[key] !== undefined && data[key] !== null && data[key] !== "") parts.push(`${key}: ${asText(data[key])}`);
  }
  if (!parts.length && Object.keys(data).length) parts.push(JSON.stringify(data));
  if (event.at) {
    const date = new Date(event.at);
    if (!Number.isNaN(date.getTime())) parts.push(date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
  }
  return parts.join(" · ") || "Host transition recorded";
}

function renderEvents() {
  const all = [...state.events.values()].sort((a, b) => number(b.seq) - number(a.seq));
  $("event-total").textContent = `${formatCount(all.length)} event${all.length === 1 ? "" : "s"}`;
  const list = $("event-list");
  list.replaceChildren();
  if (!all.length) {
    list.append(element("li", "empty-small", "Run events will appear here as the host emits them."));
    return;
  }
  for (const event of all.slice(0, MAX_VISIBLE_EVENTS)) {
    const type = String(event.type || "Event");
    const category = /prun|refus|reject|anti/i.test(type) ? "event-pruned" : /certif|witness|verif/i.test(type) ? "event-certified" : "";
    const item = element("li", category);
    const top = element("div", "event-top");
    top.append(element("span", "event-type", type.replace(/[_-]/g, " ")), element("span", "event-seq", `#${event.seq ?? "—"}`));
    item.append(top, element("p", "event-detail", eventSummary(event)));
    list.append(item);
  }
}

function renderScope(scope) {
  const container = $("scope-content");
  container.replaceChildren();
  container.append(element("p", "", "Finite diagonal Z₂ graph control. This run does not query a live LLM or establish a general MUB(6) theorem."));
  if (scope) container.append(element("p", "", `Declared host scope: ${asText(scope)}`));
}

function renderReceipt(receipt, error, runStatus) {
  const container = $("receipt-content");
  container.replaceChildren();
  if (receipt === null || receipt === undefined) {
    const empty = element("div", "receipt-empty");
    const icon = element("span", "receipt-icon", "◇");
    icon.setAttribute("aria-hidden", "true");
    const text = element("div");
    text.append(element("strong", "", error ? "Run failed" : "Awaiting a host receipt"), element("p", "", error || "Results and remaining uncertainty will appear after the run."));
    empty.append(icon, text);
    container.append(empty);
    return;
  }
  const status = String(receipt.status || runStatus || "UNKNOWN");
  const labels = {
    GAUGE_VERIFIED: "Diagonal gauge witness verified",
    RESTRICTED_OBSTRUCTION: "Restricted graph obstruction verified",
    UNKNOWN: "Bounded search remains unknown",
  };
  container.append(element("div", "receipt-label", "Host receipt · finite control"));
  const summary = element("div", `receipt-summary ${status === "UNKNOWN" ? "uncertain" : ""}`);
  summary.append(element("strong", "", labels[status] || status.replace(/_/g, " ")));
  const witness = receipt.witness;
  if (witness?.type === "gauge") summary.append(element("p", "", `Witness bits: ${bitsLabel(witness.bits)}. The host replayed the finite edge equations.`));
  else if (witness?.type === "odd_cycle") summary.append(element("p", "", `Odd-cycle witness: ${asText(witness.steps)}. This is an obstruction within the declared graph grammar.`));
  else summary.append(element("p", "", "No gauge witness was established within this bounded run."));
  if (receipt.verified_by_replay === true) summary.append(element("p", "", "Independent finite receipt replay: verified."));
  if (receipt.receipt_sha256) summary.append(element("p", "", `Receipt SHA-256: ${receipt.receipt_sha256}`));
  container.append(summary);
  const details = element("details", "receipt-details");
  details.append(element("summary", "", "Inspect complete receipt"), element("pre", "receipt-json", typeof receipt === "string" ? receipt : JSON.stringify(receipt, null, 2)));
  container.append(details);
}

$("fixture-select").addEventListener("change", (event) => setFixture(event.target.value));
$("node-budget").addEventListener("change", fillPacketFromControls);
$("pace-ms").addEventListener("change", fillPacketFromControls);
$("input-yaml").addEventListener("input", updateStartButton);
$("start-button").addEventListener("click", startRun);
$("inspector-close").addEventListener("click", () => {
  state.selectedCandidateId = null;
  $("candidate-inspector").hidden = true;
  renderCandidates(state.snapshot?.candidates || []);
});
window.addEventListener("beforeunload", disconnectRun);
loadFixtures();

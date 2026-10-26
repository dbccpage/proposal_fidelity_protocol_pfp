// PFP Lab page. AuthorityEffect: None.
// The page only edits JSON and draws results; every number shown comes from the core.
"use strict";

const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";
let lastReceipt = null;

const TEMPLATES = {
  ASSERT: { move: "ASSERT", source: "a", target: "b", value: "1" },
  CUT: { move: "CUT", claims: [{ source: "a", target: "b", value: "0" }] },
  VERIFY: { move: "VERIFY", obligation: "ZERO_OBSTRUCTION" },
  RETRACT: { move: "RETRACT", target_step_id: "step_001", reason: "" },
};

function showBanner(text, good) {
  const banner = $("banner");
  banner.textContent = text;
  banner.classList.toggle("good", Boolean(good));
  banner.hidden = !text;
}

async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) {
    throw new Error(`${body.code || response.status}: ${body.message || "request failed"}`);
  }
  return body;
}

// Display only: a canonical rational string as a JavaScript number for plotting.
function toNumber(text) {
  const [p, q] = String(text).split("/");
  return Number(p) / (q === undefined ? 1 : Number(q));
}

function svg(tag, attributes, text) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

function drawGraph(scenario, final) {
  const root = $("graph");
  root.replaceChildren();
  root.appendChild(arrowMarker());
  const vertices = scenario.vertices || [];
  const place = {};
  vertices.forEach((name, index) => {
    const angle = (2 * Math.PI * index) / Math.max(vertices.length, 1) - Math.PI / 2;
    place[name] = { x: 160 + 95 * Math.cos(angle), y: 130 + 95 * Math.sin(angle) };
  });
  const claims = {};
  for (const claim of (final && final.claims) || []) claims[`${claim.source}>${claim.target}`] = claim.value;
  for (const edge of scenario.edges || []) drawEdge(root, place, edge, claims);
  for (const name of vertices) {
    const at = place[name];
    root.appendChild(svg("circle", { cx: at.x, cy: at.y, r: 15, class: "node" }));
    root.appendChild(svg("text", { x: at.x, y: at.y + 4, "text-anchor": "middle" }, name));
    const value = final && final.section ? final.section[name] : undefined;
    if (value !== undefined) {
      root.appendChild(svg("text", { x: at.x, y: at.y + 30, "text-anchor": "middle", class: "muted" }, `s=${value}`));
    }
  }
}

function arrowMarker() {
  const defs = svg("defs", {});
  const marker = svg("marker", { id: "arrow", viewBox: "0 0 10 10", refX: 10, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
  marker.appendChild(svg("path", { d: "M0,0 L10,5 L0,10 z", class: "ok" }));
  defs.appendChild(marker);
  return defs;
}

function drawEdge(root, place, edge, claims) {
  const from = place[edge.source];
  const to = place[edge.target];
  if (!from || !to) return;
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.hypot(dx, dy) || 1;
  const bend = 14;
  const mx = (from.x + to.x) / 2 - (dy / length) * bend;
  const my = (from.y + to.y) / 2 + (dx / length) * bend;
  const start = { x: from.x + (dx / length) * 16, y: from.y + (dy / length) * 16 };
  const end = { x: to.x - (dx / length) * 18, y: to.y - (dy / length) * 18 };
  root.appendChild(svg("path", { d: `M${start.x},${start.y} Q${mx},${my} ${end.x},${end.y}`, class: "edge", "marker-end": "url(#arrow)" }));
  const claim = claims[`${edge.source}>${edge.target}`];
  const label = `w${edge.weight === undefined ? 1 : edge.weight}${claim === undefined ? "" : ` c=${claim}`}`;
  root.appendChild(svg("text", { x: mx, y: my, "text-anchor": "middle" }, label));
}

function drawChart(verdicts) {
  const root = $("chart");
  root.replaceChildren();
  const left = 36, right = 308, top = 16, bottom = 228;
  root.appendChild(svg("line", { x1: left, y1: bottom, x2: right, y2: bottom, class: "axis" }));
  root.appendChild(svg("line", { x1: left, y1: top, x2: left, y2: bottom, class: "axis" }));
  if (!verdicts.length) return;
  const values = verdicts.map((v) => toNumber(v.defect_after));
  const peak = Math.max(...values, 1);
  const x = (i) => left + ((right - left) * (i + 0.5)) / verdicts.length;
  const y = (value) => bottom - ((bottom - top) * value) / peak;
  root.appendChild(svg("text", { x: 4, y: top + 4 }, String(Math.round(peak * 100) / 100)));
  root.appendChild(svg("text", { x: 4, y: bottom }, "0"));
  root.appendChild(svg("polyline", { points: values.map((v, i) => `${x(i)},${y(v)}`).join(" "), class: "trend" }));
  verdicts.forEach((verdict, i) => {
    const dot = svg("circle", { cx: x(i), cy: y(values[i]), r: 4, class: verdict.admitted ? "ok" : "refused" });
    dot.appendChild(svg("title", {}, `${verdict.step_id} ${verdict.status}: ${verdict.defect_before} -> ${verdict.defect_after}`));
    root.appendChild(dot);
    root.appendChild(svg("text", { x: x(i), y: bottom + 14, "text-anchor": "middle" }, String(i + 1)));
  });
}

function cell(text, className) {
  const td = document.createElement("td");
  if (className) td.className = className;
  td.textContent = text;
  return td;
}

function drawTrace(verdicts) {
  const body = $("trace");
  body.replaceChildren();
  for (const verdict of verdicts) {
    const row = document.createElement("tr");
    const status = cell("");
    const chip = document.createElement("span");
    chip.className = `chip ${verdict.admitted ? "ok" : "refused"}`;
    chip.textContent = verdict.status;
    status.appendChild(chip);
    row.append(cell(verdict.step_id, "num"), cell(verdict.move), status,
      cell(verdict.defect_before, "num"), cell(verdict.defect_after, "num"), cell(verdict.details));
    body.appendChild(row);
  }
}

function showReceipt(receipt) {
  lastReceipt = receipt;
  $("download").disabled = false;
  $("defect").textContent = receipt.final.defect;
  $("obstruction").textContent = receipt.final.obstruction;
  const admitted = receipt.verdicts.filter((v) => v.admitted).length;
  $("admitted").textContent = `${admitted}/${receipt.verdicts.length}`;
  drawGraph(receipt.scenario, receipt.final);
  drawChart(receipt.verdicts);
  drawTrace(receipt.verdicts);
  $("digest").textContent = `receipt sha256 ${receipt.digest}`;
}

async function loadPack(packId) {
  const scenario = await api(`/api/packs/${encodeURIComponent(packId)}`);
  $("scenario").value = JSON.stringify(scenario, null, 2);
  drawGraph(scenario, null);
}

async function run() {
  showBanner("");
  try {
    const receipt = await api("/api/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: $("scenario").value });
    showReceipt(receipt);
  } catch (error) {
    showBanner(error.message);
  }
}

function insertMove(kind) {
  try {
    const scenario = JSON.parse($("scenario").value);
    scenario.moves = [...(scenario.moves || []), TEMPLATES[kind]];
    $("scenario").value = JSON.stringify(scenario, null, 2);
  } catch (error) {
    showBanner(`The scenario is not valid JSON yet: ${error.message}`);
  }
}

function download() {
  if (!lastReceipt) return;
  const blob = new Blob([JSON.stringify(lastReceipt, null, 2) + "\n"], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `pfp-receipt-${lastReceipt.digest.slice(0, 12)}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function verifyUpload(event) {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  try {
    const text = await file.text();
    const report = await api("/api/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: text });
    if (report.valid) {
      showBanner(`Receipt verified: the digest matches and the replay agrees.\n${report.digest}`, true);
      showReceipt(JSON.parse(text));
    } else {
      showBanner(`Receipt NOT valid:\n- ${report.problems.join("\n- ")}`);
    }
  } catch (error) {
    showBanner(error.message);
  }
}

async function start() {
  try {
    const version = await api("/api/version");
    $("version").textContent = `v${version.version} · AuthorityEffect: ${version.authority_effect}`;
    const { packs } = await api("/api/packs");
    for (const pack of packs) {
      const option = document.createElement("option");
      option.value = pack.pack_id;
      option.textContent = `${pack.pack_id} (${pack.moves} moves)`;
      option.title = pack.title;
      $("pack").appendChild(option);
    }
    if (packs.length) await loadPack(packs[0].pack_id);
  } catch (error) {
    showBanner(error.message);
  }
}

$("pack").addEventListener("change", (event) => loadPack(event.target.value).catch((e) => showBanner(e.message)));
$("run").addEventListener("click", run);
$("download").addEventListener("click", download);
$("upload").addEventListener("change", verifyUpload);
for (const button of document.querySelectorAll("[data-move]")) {
  button.addEventListener("click", () => insertMove(button.dataset.move));
}
start();

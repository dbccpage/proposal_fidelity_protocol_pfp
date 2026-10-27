"""Five carriers by five reversible surfaces per pilot; no answers in public prompts."""
from __future__ import annotations

import copy
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re

import yaml

from .checking import answer_schema, mv
from .._paths import pilots_root

PILOTS = pilots_root(Path(__file__))
IDS = (0, 1, 2, 3, 4, 5, 188, 189, 190, 191)
FORMS = ("compact_json", "indented_json", "reordered_json", "emoji_tokens", "egyptian_tokens")
FAMILIES = {0: "linear_algebra", 1: "graph_facts", 2: "graph_repair", 3: "refusal", 4: "linear_algebra", 5: "graph_facts",
            188: "binary_spin_frustration", 189: "weighted_cycle_duality", 190: "degree4_primal_dual_certificate", 191: "chain_topology_scope_audit"}
SOURCES = {188: "demo_4/dossier_1_f2_spin_triangle", 189: "demo_4/dossier_2_exact_lp_certificate",
           190: "demo_9/dossier_1_hollow_5simplex_b4_1", 191: "demo_9/dossier_2_pontryagin_chern_4manifold"}
INSTRUCTIONS = {
    "linear": "Solve matrix*x=b over exact rationals. Supply the whole solution and dot(target,x).",
    "graph": "For the undirected simple graph, return its connected components (vertex lists), bridge edge indices (zero based), cycle rank E-V+C, and number of distinct triangles. Include isolated vertices.",
    "repair": "Remove a minimum number of edges to leave a spanning forest preserving every original connected component. Return removed zero-based edge indices and resulting cycle_rank. Any minimum witness is allowed.",
    "lookup": "Look up the exact length of the undirected query edge. VALUE requires its supplied length; MAP_UNDEFINED means no such edge; MISSING_LENGTH means the edge exists but its length is unspecified. A refusal carries null, never a guessed length.",
    "spin": "Over F2 find vertex bits minimizing Hamming weight of target XOR incidence*spins. Supply spins, residual bits in edge order, and minimum weight. Any optimum is allowed; a closed loop need not be a filled face.",
    "lp": "Minimize sum_i weights_i*abs(flux_i-(matrix*potential)_i). Supply any rational potential and dual satisfying transpose(matrix)*dual=0 and abs(dual_i)<=weights_i, with equal primal objective and dot(flux,dual). Report that exact objective. A nonzero gap is not a certificate.",
    "scope": "Compute the four exact rational matrix ranks and five Betti numbers dimensions minus adjacent ranks. Check all adjacent matrix products. Report CHAIN_LAW_FAILURE and betti=null if any product is nonzero, else MATCH or DECLARED_TOPOLOGY_MISMATCH against declared_betti. No cup product carrier is supplied: report UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER. Do not infer a manifold or multiplication table from boundary matrices.",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def source_input(pilot):
    archived = PILOTS / f"pilot_{pilot:07d}" / "misc" / "source" / "input.yaml"
    path = archived if archived.exists() else PILOTS / "demo_003" / SOURCES[pilot] / "input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def carrier(pilot, rung):
    k = rung
    if pilot in (0, 4):
        n = 2 if pilot == 0 else 3 + k // 3
        a = [[(3+k+i if i == j else (-1)**(i+j)*(i+j+1)) for j in range(n)] for i in range(n)]
        # Strict diagonal dominance keeps the generated systems nonsingular.
        for i in range(n):
            a[i][i] = sum(abs(a[i][j]) for j in range(n) if j != i) + k + 1
        x = [Q((-1)**i * (k+i+1), k+1) for i in range(n)]
        return dict(kind="linear", matrix=a, b=list(map(str, mv(a, x))), target=[(-1)**i*(i+2) for i in range(n)])
    if pilot in (1, 2, 5, 188):
        n = 3 + k
        edges = [[i, i+1] for i in range(n-1)] + [[n-1, 0]]
        if k >= 2:
            edges += [[0, 2]]
        if k >= 4:
            edges += [[1, n-2]]
        if pilot in (1, 5) and k % 2 == 0:
            n += 1  # isolated vertex: connectedness is not hard-coded
        if pilot == 188:
            return dict(kind="spin", n=n, edges=edges, target=[(i+k) % 2 for i in range(len(edges))])
        return dict(kind="repair" if pilot == 2 else "graph", n=n, edges=edges)
    if pilot == 3:
        edges = [[i, i+1, str(Q(2*i+k+1, k+1))] for i in range(k+3)]
        if k in (2, 4):
            edges[k][2] = None
        query = [k, k+1] if k != 3 else [0, k+2]
        return dict(kind="lookup", edges=edges, query=query)
    if pilot == 189:
        n = k + 2
        a = [[int(j == (i+1) % n)-int(j == i) for j in range(n)] for i in range(n)]
        return dict(kind="lp", matrix=a, flux=[str(Q((-1)**i*(i+k+1), k+2)) for i in range(n)],
                    weights=[str(1+(i+k) % 3) for i in range(n)])
    if pilot == 190:
        source = source_input(190)
        a = source["boundary_matrices"]["d3"]
        potential = [Q((-1)**i*(i % k), k+1) for i in range(len(a[0]))]
        cycle = list(map(Q, source["homology"]["fundamental_4_cycle"]))
        flux = [str(x + Q(k, 6*(k+1))*v) for x, v in zip(mv(a, potential), cycle)]
        return dict(kind="lp", matrix=a, flux=flux, weights=["1"]*len(a), degree=4)
    if pilot == 191:
        source = source_input(191)
        matrices = [source["boundary_matrices"][f"d{i}"] for i in range(4)]
        if k >= 3:
            matrices[3][0][0] = str(k-2)
        if k == 5:
            matrices[2][0][0] = "1"  # incompatible composition must be rejected
        declared = [1, 0, 2, 0, 1] if k % 2 else [1, 0, 1, 2, 1]
        return dict(kind="scope", matrices=matrices, declared_betti=declared)
    raise ValueError("UNKNOWN_PILOT")


TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?|true|false|null|[{}\[\]:,]')


def surface(task, form):
    original = canonical(task).decode("utf-8")
    if form == "compact_json":
        return original, {}
    if form == "indented_json":
        return json.dumps(task, indent=2), {}
    if form == "reordered_json":
        return json.dumps(dict(reversed(list(task.items())))), {}
    tokens = TOKEN.findall(original)
    if "".join(tokens) != original:
        raise ValueError("UNENCODABLE_CARRIER")
    unique = list(dict.fromkeys(tokens))
    glyphs = ([chr(0x1F400+i) for i in range(len(unique))] if form == "emoji_tokens"
              else [chr(0x13000+i) for i in range(len(unique))])
    legend = dict(zip(glyphs, unique))
    reverse = {v: g for g, v in legend.items()}
    encoded = " ".join(reverse[t] for t in tokens)
    if json.loads("".join(legend[t] for t in encoded.split())) != task:
        raise ValueError("REWRITE_ROUNDTRIP_FAILED")
    return encoded, legend


def wrapped(pilot, rung, form, template):
    task = carrier(pilot, rung)
    text, legend = surface(task, form)
    envelope = yaml.safe_load(template["response_schema"])
    envelope["properties"]["answer"] = answer_schema(task)
    prompt = copy.deepcopy(template)
    prompt["lineage"] = dict(prompt_id=f"pilot_{pilot:07d}_dossier_r{rung}_{form}", generation_id=1,
                             family_id=FAMILIES[pilot], parent_id=f"pilot_{pilot:07d}")
    prompt["guidance"] = dict(rules=[], antibodies=[], antipatterns=[], helpful_patterns=[])
    prompt["response_schema"] = yaml.safe_dump(envelope, sort_keys=False)
    prompt["user_prompt"] = (
        "Operational license: the declared finite graphs, matrix multiplication, rational arithmetic, F2 operations and optimization have their ordinary exact mathematical meanings. "
        "Glyph tokens are a reversible transport alphabet, not additional SYM SYS primitives. "
        "Use only this carrier. Return the full JSON response envelope, with a short summary and no markdown. "
        "Represent rationals as integer or p/q strings, never floating point numbers.\n"
        + INSTRUCTIONS[task["kind"]] + "\n"
        + ("Decode each space-delimited glyph using this exact JSON-token legend, then concatenate: " + json.dumps(legend, ensure_ascii=False) + "\n" if legend else "")
        + "Carrier:\n" + text + "\nResponse schema:\n" + json.dumps(envelope, separators=(",", ":")))
    return {"task": task, "representation": form, "rung": rung, "legend": legend,
            "carrier_sha256": sha(canonical(task)), "surface_sha256": sha(text.encode()), "prompt": prompt}

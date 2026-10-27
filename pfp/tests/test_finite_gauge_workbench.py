"""Meaningful end-to-end checks for the finite workbench and web contract."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path

import pytest

from pfp.domain.finite_gauge import RunConfig
from pfp.infrastructure.adapters.finite_gauge.input_yaml import (
    parse_input_yaml,
)
from pfp.infrastructure.composition.finite_gauge import (
    build_run,
    build_run_store,
)
from pfp.use_cases.finite_gauge_workbench import (
    FiniteGaugeRun,
)


def test_exact_witness_and_restricted_obstruction_are_distinct() -> None:
    yes = build_run(RunConfig("gauge_even_triangle", 8, 0)).execute().unwrap()
    no = build_run(RunConfig("gauge_odd_triangle", 8, 0)).execute().unwrap()
    partial = build_run(RunConfig("gauge_odd_triangle", 3, 0)).execute().unwrap()

    assert yes["status"] == "GAUGE_VERIFIED"
    assert yes["receipt"]["verified_by_replay"] is True
    assert yes["receipt"]["witness"]["type"] == "gauge"
    assert yes["counts"]["certified"] == 1
    assert no["status"] == "RESTRICTED_OBSTRUCTION"
    assert no["receipt"]["complete_oracle_used"] is True
    assert no["receipt"]["witness"]["type"] == "odd_cycle"
    assert no["counts"]["certified"] == 0
    assert partial["status"] == "UNKNOWN"
    assert partial["receipt"]["frontier"]["next_index"] == 3
    assert partial["receipt"]["witness"] is None

    for snapshot in (yes, no, partial):
        counts = snapshot["counts"]
        assert counts["generated"] == counts["scored"]
        assert counts["generated"] == counts["pruned"] + counts["retained"]
        assert counts["anti_morphisms_total"] == sum(snapshot["anti_morphisms"].values())
        assert [event["seq"] for event in snapshot["events"]] == list(
            range(1, len(snapshot["events"]) + 1)
        )
        assert [(c["index"], tuple(c["bits"]), c["valid"])
                for c in snapshot["receipt"]["checks"]] == [
            (c["index"], c["bits"], c["status"] == "retained")
            for c in snapshot["candidates"]
        ]


def test_canonical_checker_preserves_historical_bytes_and_shared_types() -> None:
    from pfp.infrastructure.adapters.finite_gauge import frontier_search, sign_graph
    historical = Path(__file__).resolve().parents[2] / (
        "atlas/coda_atlas/F004_papers/015_pfp/"
        "002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha"
    )
    pins = {
        "sign_graph.py": "9488ed63c65089af3086dafa3e01a9af948fb5d3c88505103e376f0590f0b3e1",
        "frontier_search.py": "d3529c2150f6b5d43be46a34c46bcde07ee2c082dc9f18ad522114977c417bc9",
    }
    for module in (sign_graph, frontier_search):
        current = Path(module.__file__)
        original = (historical / current.name).read_bytes()
        assert current.read_bytes() == original
        assert sha256(original).hexdigest() == pins[current.name]
    assert frontier_search.SignedRewrite is sign_graph.SignedRewrite
    assert frontier_search.GaugeWitness is sign_graph.GaugeWitness
    assert frontier_search.OddCycleWitness is sign_graph.OddCycleWitness
    assert frontier_search.CHECKER_VERSION == "finite-sign-graph-v1"
    with pytest.raises(FrozenInstanceError):
        sign_graph.GaugeWitness(("a",), (0,)).bits = (1,)


@pytest.mark.parametrize("fixture_id", ["gauge_even_triangle", "gauge_odd_triangle"])
def test_wrong_witness_is_rejected_even_with_resealed_receipt(fixture_id) -> None:
    from pfp.infrastructure.adapters.finite_gauge import (
        frontier_search,
        sign_graph,
    )
    from pfp.infrastructure.adapters.finite_gauge.paper002_checker import (
        _presentation_key,
    )

    sign, frontier = sign_graph, frontier_search
    spec = RunConfig(fixture_id, 8, 0).graph_spec()
    vertices = spec.vertices
    edges = tuple(sign.SignedRewrite(edge.source, edge.target, edge.odd) for edge in spec.edges)
    key = _presentation_key()
    receipt = frontier.search_sign_graph(vertices, edges, key, node_budget=8, workers=1)
    assert frontier.verify_search_receipt(vertices, edges, key, receipt)
    if isinstance(receipt.witness, sign.GaugeWitness):
        wrong = sign.GaugeWitness(vertices, (0, 0, 0))
        assert not sign.verify_gauge(vertices, edges, wrong)
    else:
        wrong = sign.OddCycleWitness(receipt.witness.steps[:-1])
        assert not sign.verify_odd_cycle(vertices, edges, wrong)
    forged = replace(receipt, witness=wrong)
    forged = replace(forged, receipt_sha256=frontier._canonical_sha256(frontier._receipt_body(forged)))
    assert not frontier.verify_search_receipt(vertices, edges, key, forged)


def test_source_only_workbench_closure_outside_checkout(tmp_path) -> None:
    """Copy only current source closure; this is not an installed-wheel check."""
    root = Path(__file__).resolve().parents[2]
    source_root = tmp_path / "source-only"
    paths = (
        "pfp/__init__.py",
        "pfp/infrastructure/__init__.py",
        "pfp/infrastructure/adapters/__init__.py",
        "pfp/infrastructure/adapters/finite_gauge/__init__.py",
        "pfp/infrastructure/adapters/finite_gauge/sign_graph.py",
        "pfp/infrastructure/adapters/finite_gauge/frontier_search.py",
        "pfp/infrastructure/adapters/finite_gauge/paper002_checker.py",
        "pfp/infrastructure/adapters/finite_gauge/run_store.py",
        "pfp/infrastructure/composition/__init__.py",
        "pfp/infrastructure/composition/finite_gauge.py",
        "pfp/domain/finite_gauge/__init__.py",
        "pfp/domain/finite_gauge/models.py",
        "pfp/domain/kernel/result.py",
        "pfp/domain/ports/finite_gauge.py",
        "pfp/use_cases/__init__.py",
        "pfp/use_cases/finite_gauge_workbench.py",
    )
    for relative in paths:
        target = source_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / relative).read_bytes())
    for package in ("domain", "domain/kernel", "domain/ports"):
        marker = source_root / "pfp" / package / "__init__.py"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("", encoding="utf-8")
    probe = """
import json, sys
from pathlib import Path
source_root = Path(sys.argv[1])
sys.path.insert(0, str(source_root))
from pfp.domain.finite_gauge import RunConfig
from pfp.infrastructure.adapters.finite_gauge import frontier_search, sign_graph
from pfp.infrastructure.composition.finite_gauge import build_run
outcomes = []
for fixture, budget, expected in (
    ('gauge_even_triangle', 8, 'GAUGE_VERIFIED'),
    ('gauge_odd_triangle', 8, 'RESTRICTED_OBSTRUCTION'),
    ('gauge_odd_triangle', 3, 'UNKNOWN'),
):
    result = build_run(RunConfig(fixture, budget, 0)).execute().unwrap()
    assert result['status'] == expected, result['error']
    assert result['receipt']['verified_by_replay']
    outcomes.append(result['status'])
for module in (sign_graph, frontier_search):
    assert Path(module.__file__).is_relative_to(source_root)
assert not any(name == 'research' or name.startswith(('research.', 'education'))
               for name in sys.modules)
print(json.dumps(outcomes))
"""
    result = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", probe, str(source_root)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == ["GAUGE_VERIFIED", "RESTRICTED_OBSTRUCTION", "UNKNOWN"]


def test_invalid_budget_rejected_before_run() -> None:
    with pytest.raises(ValueError, match="node_budget"):
        RunConfig("gauge_even_triangle", True, 0)
    with pytest.raises(ValueError, match="unknown"):
        RunConfig("does_not_exist", 8, 0)


def test_typed_yaml_and_custom_graph_without_run_script() -> None:
    source = """schema: symbol_game.finite_gauge_input.v1
objective: Check this signed graph only
node_budget: 4
pace_ms: 0
graph:
  vertices: [a, b]
  edges:
    - [a, b, 1]
"""
    config = parse_input_yaml(source)
    snapshot = build_run(config, input_text=source).execute().unwrap()
    assert snapshot["status"] == "GAUGE_VERIFIED"
    assert snapshot["input_text"] == source
    assert snapshot["input_packet"]["graph"]["edges"] == (("a", "b", 1),)
    assert snapshot["receipt"]["input_sha256"]
    with pytest.raises(ValueError, match="unique"):
        parse_input_yaml("schema: symbol_game.finite_gauge_input.v1\nnode_budget: 2\nnode_budget: 3")
    with pytest.raises(ValueError, match="aliases"):
        parse_input_yaml("schema: symbol_game.finite_gauge_input.v1\nobjective: &x hello\nfixture_id: *x")
    with pytest.raises(ValueError, match="anchors"):
        parse_input_yaml("schema: symbol_game.finite_gauge_input.v1\nobjective: &unused hello")
    with pytest.raises(ValueError, match="exact parity"):
        RunConfig.from_packet({"schema": "symbol_game.finite_gauge_input.v1",
                               "graph": {"vertices": ["a", "b"],
                                         "edges": [["a", "b", 0.5]]}})


def test_fastapi_run_and_replayable_sse() -> None:
    from fastapi.testclient import TestClient

    from pfp.entrypoints.web.workbench import create_app

    with TestClient(create_app(build_run_store())) as client:
        fixtures = client.get("/api/workbench/fixtures")
        assert fixtures.status_code == 200
        assert {fixture["id"] for fixture in fixtures.json()["fixtures"]} >= {
            "gauge_even_triangle", "gauge_odd_triangle"
        }
        assert client.get("/").status_code == 200
        assert client.get("/assets/app.css").status_code == 200
        assert client.get("/assets/workbench.py").status_code == 404
        packet = """schema: symbol_game.finite_gauge_input.v1
fixture_id: gauge_odd_triangle
node_budget: 3
pace_ms: 0
"""
        response = client.post("/api/workbench/runs", json={"input_yaml": packet})
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        snapshot = client.get(f"/api/workbench/runs/{run_id}").json()
        for _ in range(100):
            if snapshot["status"] in FiniteGaugeRun.TERMINAL:
                break
            snapshot = client.get(f"/api/workbench/runs/{run_id}").json()
        assert snapshot["status"] == "UNKNOWN"
        assert snapshot["input_text"] == packet
        assert snapshot["receipt"]["verified_by_replay"] is True
        stream = client.get(f"/api/workbench/runs/{run_id}/events")
        assert stream.status_code == 200
        events = [json.loads(line.removeprefix("data: "))
                  for line in stream.text.splitlines() if line.startswith("data: ")]
        assert len(events) == len(snapshot["events"])
        assert events[-1]["type"] == "run_finished"
        assert client.post("/api/workbench/runs", json={"input_yaml": packet.replace("node_budget: 3", "node_budget: 0")}).status_code == 422
        assert client.post("/api/workbench/runs", json={"fixture_id": "gauge_even_triangle", "phi": 0}).status_code == 422
        assert client.post("/api/workbench/runs", json={"fixture_id": []}).status_code == 422

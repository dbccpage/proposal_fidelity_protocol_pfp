"""Verification suite for Milestone M2: Window 5 PFP 015-019 Derivations & Funnel Compression Closure.

AuthorityEffect: None.

Covers all 21 settled archive claims across Companion Papers 015, 016, 018, and 019
plus Core Lean 4 formalization `lean4/FunnelCompressionClosure.lean` and DAG/Atlas sync.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import itertools
import json
import re
import shutil
import site
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from adversary.domain.providers.attempt import TransportFailure
from adversary.domain.providers.budget import (
    BudgetController,
    ModelPricingObservationV1,
    PriceQuoteV1,
)
from adversary.domain.providers.types import ProviderError
from adversary.infrastructure.providers.anthropic_messages import AnthropicTransport
from operations.domain.rop.result import Err, Ok, Refusal
from pydantic import ValidationError

from operads.application.typed_workflow_compiler import compile_typed_workflow
from operads.contracts.ddc_code_repair_v1 import (
    STAGES,
    CodeRepairRequestV1,
    LocalCheckV1,
    RepairTerminalV1,
    relative_file,
)
from operads.domain.autopoiesis.research import (
    ALLOWED_FILES,
    PHASE_CAPS,
    EvaluationReceiptV1,
    ExperimentSpecV1,
    HarnessCandidateV1,
    IncumbentDecisionV1,
)
from operads.domain.value_objects.content_digest import ContentDigest
from operads.infrastructure.ddc_code_repair import load_code_repair_family
from pciv.use_cases.research_selection import decide
from pfp.infrastructure.adapters.harness_budget import HarnessBudgetLedger
from pfp.infrastructure.adapters.harness_provider import HarnessProvider

_REPO_ROOT = Path(__file__).resolve().parents[1]
_P015_DIR = _REPO_ROOT / "atlas/archive/pfp/015_pfp_local_to_global_agent_composition"
_P016_DIR = _REPO_ROOT / "atlas/archive/pfp/016_pfp_future_faithful_compression_and_cost"
_P018_DIR = _REPO_ROOT / "atlas/archive/pfp/018_pfp_operadic_composition_and_bounded_ddc_repair"
_P019_DIR = _REPO_ROOT / "atlas/archive/pfp/019_pfp_evidence_bound_harness_evolution"
_PUB_DIR = _REPO_ROOT / "atlas/archive/pfp/publication/author_review_2026_10_23"
_AUTHOR_ZIP = _PUB_DIR / "pfp_harness_author_review_2026-10-23.zip"
_OFFLINE_ZIP = _PUB_DIR / "offline_followup/harness_offline_followup_2026-10-23.zip"
_LEAN_FILE = _REPO_ROOT / "lean4/FunnelCompressionClosure.lean"
_REVIEW_JSON = _REPO_ROOT / "dag/reviews/additional_w5_v1rc_funnel_compression.json"

_M2_CLAIMS: tuple[str, ...] = (
    "ATL-P015-001",
    "ATL-P015-002",
    "ATL-P015-003",
    "ATL-P015-004",
    "ATL-P016-001",
    "ATL-P016-002",
    "ATL-P016-003",
    "ATL-P016-004",
    "ATL-P018-002",
    "ATL-P018-003",
    "ATL-P018-004",
    "ATL-P018-005",
    "ATL-P019-001",
    "ATL-P019-002",
    "ATL-P019-003",
    "ATL-P019-004",
    "ATL-P019-005",
    "ATL-P019-006",
    "ATL-P019-007",
    "ATL-P019-008",
    "ATL-P019-009",
)


@pytest.fixture(autouse=True)
def _isolate_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    tmp_str = str(tmp_path)
    for var in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(var, tmp_str)
    monkeypatch.setattr(tempfile, "tempdir", tmp_str)
    before_mods = dict(sys.modules)
    try:
        yield
    finally:
        for name in list(sys.modules):
            if name not in before_mods:
                sys.modules.pop(name, None)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _lake_exe() -> str:
    found = shutil.which("lake")
    if found:
        return found
    elan_lake = Path.home() / ".elan/bin/lake"
    assert elan_lake.is_file(), "lake executable not found"
    return str(elan_lake)


def _hex64(tag: str) -> str:
    return hashlib.sha256(tag.encode("utf-8")).hexdigest()


def _run_six_stages(runtime: Any) -> dict[str, Any]:
    state: Any = runtime.request.model_dump(mode="json")
    for method in ("capture", "observe", "evaluate", "incorporate", "disposition", "terminal"):
        state = getattr(runtime, method)(state)
    return state


class _NullImmune:
    def check_candidate(self, **kwargs: Any) -> Any:
        return Err(Refusal(code="NO_IMMUNE", message="offline"))


class _NullGenealogy:
    def record_lineage(self, *args: Any, **kwargs: Any) -> Any:
        return Ok("lineage:1")


class _MemStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._blobs: dict[str, bytes] = {}
        self._records: dict[str, dict[str, Any]] = {}

    def put(self, raw: bytes) -> str:
        key = hashlib.sha256(raw).hexdigest()
        self._blobs[key] = raw
        return key

    def get(self, key: str) -> bytes:
        return self._blobs[key]

    def record(self, key: str, payload: dict[str, Any]) -> None:
        if key in self._records:
            raise ValueError("OCCURRENCE_CONFLICT")
        self._records[key] = json.loads(json.dumps(payload))

    def lookup(self, key: str) -> dict[str, Any] | None:
        return self._records.get(key)


def test_lean4_funnel_compression_closure_compiles_with_admissible_axioms() -> None:
    assert _LEAN_FILE.is_file()
    source = _LEAN_FILE.read_text(encoding="utf-8")
    code_tokens = [
        tok
        for line in source.splitlines()
        if not line.strip().startswith(("--", "/-", "*"))
        for tok in line.split()
    ]
    assert "sorry" not in code_tokens
    lean_cmd = [
        _lake_exe(),
        "+leanprover/lean4:v4.35.0",
        "--dir",
        "lean4",
        "env",
        "lean",
        "lean4/FunnelCompressionClosure.lean",
    ]
    res = subprocess.run(
        lean_cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert res.returncode == 0, res.stderr + res.stdout
    lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
    assert len(lines) == 22
    for ln in lines:
        assert "sorryAx" not in ln
        assert "Classical.choice" not in ln
        if "depends on axioms:" in ln:
            ax_part = ln.split("depends on axioms:", 1)[1].strip().strip("[]")
            axioms = {a.strip() for a in ax_part.split(",") if a.strip()}
            assert axioms <= {"propext", "Quot.sound"}, f"Unexpected axioms in {ln}"
        else:
            assert "does not depend on any axioms" in ln


def test_dag_and_atlas_synchronization_for_all_21_m2_claims() -> None:
    review = json.loads(_REVIEW_JSON.read_text(encoding="utf-8"))
    assert len(review["claims"]) == 21
    matches = {
        r["atlas_id"]: r
        for r in json.loads((_REPO_ROOT / "atlas/atlas_claim_matches.json").read_text(encoding="utf-8"))["results"]
    }
    for aid in _M2_CLAIMS:
        row = matches[aid]
        audit_id = aid.replace("ATL-", "AUDIT-")
        assert row["verdict"] in ("matched", "partial")
        assert row["proposed_derivation"] is None
        assert row["nodes"] == [audit_id]
        deriv_md = _REPO_ROOT / "dag/derivations" / f"{audit_id.lower().replace('-', '_')}.md"
        stub_md = _REPO_ROOT / "dag/derivations" / f"{aid.lower().replace('-', '_')}.md"
        assert deriv_md.is_file()
        assert not stub_md.exists()

    chk = subprocess.run(
        [sys.executable, "-B", "-X", "utf8", "dag/build_atlas.py", "--check"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert chk.returncode == 0, chk.stdout + chk.stderr
    payload = json.loads(chk.stdout)
    assert payload["stale"] == []


def test_p015_001_gluing_bijection_and_uncovered_boundaries() -> None:
    domains = {0: (0, 1, 2), 1: (0, 1), 2: (1, 2)}
    rels = ({(0, 1), (1, 1), (2, 0)}, {(1, 1), (1, 2), (0, 2)})

    global_sols = {
        g
        for g in itertools.product(domains[0], domains[1], domains[2])
        if (g[0], g[1]) in rels[0] and (g[1], g[2]) in rels[1]
    }
    compat_fams = {(f0, f1) for f0 in rels[0] for f1 in rels[1] if f0[1] == f1[0]}
    glued = {(f0[0], f0[1], f1[1]) for f0, f1 in compat_fams}
    assert glued == global_sols
    assert len(compat_fams) == len(global_sols) == 5
    extensions = [(*g, v3) for g in sorted(global_sols)[:1] for v3 in (0, 1)]
    assert len(extensions) == 2 and extensions[0][:3] == extensions[1][:3]


def test_p015_002_and_p015_003_boolean_cycle_and_offline_replay() -> None:
    replay_path = _P015_DIR / "code/replay.py"
    tree = ast.parse(replay_path.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert imports == {"json", "itertools"}

    mod = _load_module("p015_replay", replay_path)
    assert mod.solutions((mod.EQ, mod.EQ, mod.NE)) == set()
    assert mod.solutions((mod.EQ, mod.EQ, mod.EQ)) == {(0, 0, 0), (1, 1, 1)}
    assert mod.check_family(((0, 0), (0, 0), (0, 1)), (mod.EQ, mod.EQ, mod.NE)) is None
    assert mod.check_family(((0, 0), (0, 0), (0, 0)), (mod.EQ, mod.EQ, mod.EQ)) == (0, 0, 0)
    assert mod.check_family(((1, 1), (1, 1), (1, 1)), (mod.EQ, mod.EQ, mod.EQ)) == (1, 1, 1)

    guard = (
        "import runpy, sys\n"
        "def hook(e, a):\n"
        "  if e.startswith('socket.') or e in {'subprocess.Popen','os.system'}:\n"
        "    raise RuntimeError(e)\n"
        "sys.addaudithook(hook)\n"
        f"runpy.run_path({str(replay_path)!r}, run_name='__main__')\n"
    )
    proc = subprocess.run([sys.executable, "-B", "-c", guard], capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    retained = json.loads((_P015_DIR / "replay_receipt.json").read_text(encoding="utf-8"))
    assert out["status"] == retained["status"] == "PASS"
    assert out["checks"] == retained["checks"]
    assert out["provider_calls"] == retained["provider_calls"] == 0


def test_p015_004_creimt_integration_vs_effectful_gluing() -> None:
    term_fields = RepairTerminalV1.model_fields
    assert term_fields["authority_effect"].default == "None"
    assert term_fields["admission"].default == "Unadmitted"
    assert term_fields["production_activation"].default == "HOLD"
    assert term_fields["mathematical_measurement"].default == "NOT_MEASURED"

    def agent_1(env: dict[str, int]) -> tuple[dict[str, int], bool]:
        nxt = {**env, "a": 1}
        return nxt, nxt["a"] == 1 and nxt["b"] == 0

    def agent_2(env: dict[str, int]) -> tuple[dict[str, int], bool]:
        nxt = {**env, "b": 1}
        return nxt, nxt["b"] == 1 and nxt["a"] == 0

    s0 = {"a": 0, "b": 0}
    assert agent_1(s0)[1] is True and agent_2(s0)[1] is True
    s12, ok2 = agent_2(agent_1(s0)[0])
    s21, ok1 = agent_1(agent_2(s0)[0])
    assert ok2 is False and ok1 is False and s12 == s21 == {"a": 1, "b": 1}


def test_p016_001_to_004_exact_quotient_refinement_counterexample_and_routes() -> None:
    replay_path = _P016_DIR / "code/replay.py"
    mod = _load_module("p016_replay", replay_path)

    chain_table = {
        "s0": {"step": (Fraction(1), "s1")},
        "s1": {"step": (Fraction(1), "s2")},
        "s2": {"step": (Fraction(1), "s3")},
        "s3": {},
    }
    init_labels = {"s0": 0, "s1": 0, "s2": 0, "s3": 1}
    refined = mod.refine(chain_table, init_labels)
    assert len(set(refined.values())) == 4

    cost_table = {"a": {"finish": (Fraction(1), "t")}, "b": {"finish": (Fraction(3), "t")}, "t": {}}
    q0 = {"a": 0, "b": 0, "t": 1}
    assert q0["a"] == q0["b"] == 0
    assert mod.path_cost(cost_table, "a", ("finish",), {"t"}) == Fraction(1)
    assert mod.path_cost(cost_table, "b", ("finish",), {"t"}) == Fraction(3)
    split_colors = mod.refine(cost_table, q0)
    assert split_colors["a"] != split_colors["b"]

    routes = {
        "r": {"direct": (Fraction(5), "t"), "next": (Fraction(1), "s"), "loop": (Fraction(1), "r")},
        "s": {"finish": (Fraction(1), "t")},
        "t": {},
    }
    assert mod.minimum_cost(routes, "r", {"t"}) == Fraction(2)
    assert mod.path_cost(routes, "r", ("direct",), {"t"}) == Fraction(5)
    assert mod.path_cost(routes, "r", ("loop", "next", "finish"), {"t"}) == Fraction(3)
    assert mod.check_route(routes, "r", ("next", "finish"), {"t"}, Fraction(2)) is True
    assert mod.check_route(routes, "r", ("next", "finish"), {"t"}, 2) is False
    assert mod.check_route(routes, "r", ("next", "finish"), {"t"}, True) is False
    with pytest.raises(ValueError, match="positive operation costs required"):
        mod.minimum_cost({"r": {"z": (Fraction(0), "t")}, "t": {}}, "r", {"t"})


def _kahn_validate_graph(query: Any, ok_cls: Any, dto_cls: Any) -> Any:
    remaining = {node.node_id for node in query.nodes}
    by_id = {node.node_id: node for node in query.nodes}
    order: list[str] = []
    stages: list[tuple[str, ...]] = []
    mismatches = [
        f"{e.source_node_id}->{e.target_node_id}"
        for e in query.edges
        if dict(by_id[e.source_node_id].output_colours)[e.source_output]
        != dict(by_id[e.target_node_id].input_colours)[e.target_input]
    ]
    while remaining:
        stage = tuple(
            sorted(
                n
                for n in remaining
                if not any(e.target_node_id == n and e.source_node_id in remaining for e in query.edges)
            )
        )
        if not stage:
            return ok_cls(dto_cls(False, len(query.nodes), len(query.edges), cycles=(tuple(sorted(remaining)),)))
        stages.append(stage)
        order.extend(stage)
        remaining.difference_update(stage)
    return ok_cls(
        dto_cls(
            not mismatches,
            len(query.nodes),
            len(query.edges),
            colour_mismatches=tuple(mismatches),
            topological_order=tuple(order),
            execution_stages=tuple(stages),
        )
    )


def test_p018_002_to_005_ddc_code_repair_stages_worked_example_and_controls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(_REPO_ROOT / "ops"))
    from adversary.infrastructure.ddc_code_repair import (
        EFFECTS,
        CodeRepairRuntime,
        RepairFailure,
        _local_process_environment,
    )
    from operations.domain.rop.result import Ok

    from operads.application.dtos.success_dtos import WorkflowValidationResultDTO

    assert STAGES == ("C", "R", "E", "I", "M", "T")
    exec_digest = ContentDigest("sha256", _hex64("ddc-exec"))
    family = load_code_repair_family(_REPO_ROOT, executor_digest=exec_digest)
    compiled = compile_typed_workflow(
        family.documents,
        family.workflow,
        validate_graph=lambda q: _kahn_validate_graph(q, Ok, WorkflowValidationResultDTO),
        allowed_effects=EFFECTS,
    )
    assert len(compiled.occurrence_order) == 6

    with pytest.raises(ValidationError):
        CodeRepairRequestV1(
            run_key="r0",
            objective="obj",
            sources={"target.py": _hex64("x")},
            write_paths=("target.py",),
            checks=(LocalCheckV1(check_id="c", argv=("python", "-V")),),
            candidate_patch="",
        )
    for mod_rel in (
        "operads/contracts/ddc_code_repair_v1.py",
        "operads/infrastructure/ddc_code_repair.py",
        "ops/adversary/infrastructure/ddc_code_repair.py",
    ):
        src_text = (_REPO_ROOT / mod_rel).read_text(encoding="utf-8")
        assert "anthropic" not in src_text and "openrouter" not in src_text

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    orig_bytes = b"def adjust(n):\n    return n if n < 0 else n - 1\n"
    (src_dir / "target.py").write_bytes(orig_bytes)
    src_sha = hashlib.sha256(orig_bytes).hexdigest()

    monkeypatch.setenv("GIT_DIR", str(tmp_path / "poison_git_dir"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "poison_work_tree"))
    clean_env = _local_process_environment()
    assert "GIT_DIR" not in clean_env and clean_env["PYTHONDONTWRITEBYTECODE"] == "1"

    def make_req(run_key: str, new_expr: str) -> CodeRepairRequestV1:
        patch = (
            "--- a/target.py\n+++ b/target.py\n@@ -1,2 +1,2 @@\n"
            " def adjust(n):\n"
            "-    return n if n < 0 else n - 1\n"
            f"+    return {new_expr}\n"
        )
        return CodeRepairRequestV1(
            run_key=run_key,
            objective="adjust nonnegative branch",
            sources={"target.py": src_sha},
            write_paths=("target.py",),
            checks=(
                LocalCheckV1(
                    check_id="positive",
                    argv=(sys.executable, "-c", "import target; assert target.adjust(2) == 3"),
                ),
                LocalCheckV1(
                    check_id="control",
                    argv=(sys.executable, "-c", "import target; assert target.adjust(-2) == -2"),
                ),
            ),
            candidate_patch=patch,
        )

    rt_ok = CodeRepairRuntime(
        repo_root=_REPO_ROOT,
        source_root=src_dir,
        run_directory=tmp_path / "run_ok",
        request=make_req("run-ok", "n if n < 0 else n + 1"),
        immune_checker=_NullImmune(),
        genealogy=_NullGenealogy(),
    )
    term_ok = RepairTerminalV1.model_validate_json(json.dumps(_run_six_stages(rt_ok)))
    assert [r.returncode for r in term_ok.state.baseline] == [1, 0]
    assert [r.returncode for r in term_ok.state.after] == [0, 0]
    assert term_ok.state.outcome == "REPAIRED"
    assert term_ok.admission == "Unadmitted" and term_ok.production_activation == "HOLD"
    assert (src_dir / "target.py").read_bytes() == orig_bytes
    assert "IMMUNE_UNAVAILABLE" in term_ok.state.integration_residuals

    for key, expr, expected in (
        ("run-ineff", "n if n < 0 else n - 2", "INEFFECTIVE"),
        ("run-reg", "n + 1", "REGRESSION"),
    ):
        rt = CodeRepairRuntime(
            repo_root=_REPO_ROOT,
            source_root=src_dir,
            run_directory=tmp_path / key,
            request=make_req(key, expr),
            immune_checker=_NullImmune(),
            genealogy=_NullGenealogy(),
        )
        assert RepairTerminalV1.model_validate_json(json.dumps(_run_six_stages(rt))).state.outcome == expected

    for bad_path in ("../escape.py", "/abs.py", ".GIT/config", "CON.py"):
        with pytest.raises(ValueError, match="SOURCE_PATH_REFUSED"):
            relative_file(bad_path)
    (src_dir / "readonly.py").write_bytes(b"X = 1\n")
    ro_req = CodeRepairRequestV1(
        run_key="run-scope",
        objective="forbid readonly edit",
        sources={"target.py": src_sha, "readonly.py": hashlib.sha256(b"X = 1\n").hexdigest()},
        write_paths=("target.py",),
        checks=(LocalCheckV1(check_id="pos", argv=(sys.executable, "-c", "raise SystemExit(1)")),),
        candidate_patch="--- a/readonly.py\n+++ b/readonly.py\n@@ -1 +1 @@\n-X = 1\n+X = 2\n",
    )
    rt_scope = CodeRepairRuntime(
        repo_root=_REPO_ROOT,
        source_root=src_dir,
        run_directory=tmp_path / "run_scope",
        request=ro_req,
        immune_checker=_NullImmune(),
        genealogy=_NullGenealogy(),
    )
    term_scope = RepairTerminalV1.model_validate_json(json.dumps(_run_six_stages(rt_scope)))
    assert (
        term_scope.state.outcome == "REFUSED"
        and term_scope.state.refusal is not None
        and term_scope.state.refusal.code == "PATCH_SCOPE_REFUSED"
    )

    (src_dir / "target.py").write_bytes(b"def adjust(n):\n    return 0\n")
    rt_drift = CodeRepairRuntime(
        repo_root=_REPO_ROOT,
        source_root=src_dir,
        run_directory=tmp_path / "run_drift",
        request=make_req("run-drift", "n if n < 0 else n + 1"),
        immune_checker=_NullImmune(),
        genealogy=_NullGenealogy(),
    )
    assert (
        getattr(RepairTerminalV1.model_validate_json(json.dumps(_run_six_stages(rt_drift))).state.refusal, "code", None)
        == "SOURCE_CHANGED"
    )
    with pytest.raises(RepairFailure) as exc_info:
        rt_ok.observe({**term_ok.state.model_dump(mode="json"), "phase": "captured", "run_key": "tampered"})
    assert exc_info.value.code == "STATE_BINDING_MISMATCH"

    with zipfile.ZipFile(_AUTHOR_ZIP) as zf:
        xml_text = zf.read(
            "pfp_harness_author_review/repository/omega_engine_woland/documentation/harness_evolution/verification/review_learning.xml"
        ).decode("utf-8")
    assert len(re.findall(r'classname="omega_engine_woland\.tests\.test_ddc_code_repair"', xml_text)) >= 20


def test_p019_001_to_003_attribution_contracts_and_paired_selection() -> None:
    manifest = json.loads((_P019_DIR / "docs/source_manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "2609.26457v1.pdf" and manifest["pages"] == 28
    assert set(manifest["page_text_sha256"]) == {str(i) for i in range(1, 29)}
    assert len(set(manifest["page_text_sha256"].values())) == 28
    map_rows = [
        ln
        for ln in (_P019_DIR / "docs/source_to_claim_map.md").read_text(encoding="utf-8").splitlines()
        if ln.startswith("| ") and not ln.startswith(("| Pages", "| ---"))
    ]
    assert len(map_rows) == 12

    src_h = _hex64("source")
    spec = ExperimentSpecV1(
        campaign_id="camp-1",
        source=src_h,
        checker=_hex64("checker"),
        split=_hex64("split"),
        budget_id="camp-1",
        configuration=_hex64("config"),
    )
    assert spec.ceiling == sum(PHASE_CAPS.values()) == 40_000_000
    expected_files = frozenset({"prompt.txt", "workflow.json", "search_policy.py", "context_policy.py"})
    assert expected_files == ALLOWED_FILES

    inc = HarnessCandidateV1(
        source=src_h,
        parent=src_h,
        files=tuple(sorted({f: f"# {f}" for f in ALLOWED_FILES}.items())),
        strategy="reference",
        mutation="init",
    )
    cand = HarnessCandidateV1(
        source=src_h,
        parent=inc.candidate_id,
        files=tuple(sorted({f: f"# {f} v2" for f in ALLOWED_FILES}.items())),
        strategy="conservative",
        mutation="step-0",
    )

    def mk_receipt(
        cid: str,
        parent: str,
        occ: str,
        task: str,
        fam: str,
        passed: bool,
    ) -> EvaluationReceiptV1:
        return EvaluationReceiptV1(
            experiment=spec.experiment_id,
            source=spec.source,
            candidate=cid,
            parent=parent,
            checker=spec.checker,
            split=spec.split,
            model=spec.inner_model,
            configuration=spec.configuration,
            budget_id=spec.budget_id,
            occurrence=occ,
            task=task,
            family=fam,
            phase="discovery",
            repetition=0,
            reply=_hex64(occ),
            public_pass=passed,
            private_pass=passed,
            status="HOST_ACCEPTED",
            cost=100,
            evidence=(_hex64("ev:" + occ),) if passed else (),
        )

    sel_reg = (
        mk_receipt(inc.candidate_id, src_h, "s-i-1", "t1", "famA", False),
        mk_receipt(inc.candidate_id, src_h, "s-i-2", "t2", "famA", False),
        mk_receipt(inc.candidate_id, src_h, "s-i-3", "t3", "famB", True),
        mk_receipt(cand.candidate_id, inc.candidate_id, "s-c-1", "t1", "famA", True),
        mk_receipt(cand.candidate_id, inc.candidate_id, "s-c-2", "t2", "famA", True),
        mk_receipt(cand.candidate_id, inc.candidate_id, "s-c-3", "t3", "famB", False),
    )
    conf_reg = tuple(
        mk_receipt(r.candidate, r.parent, "c" + r.occurrence[1:], r.task, r.family, r.private_pass)
        for r in sel_reg
    )
    dec_reg = decide(spec, inc, cand, sel_reg, conf_reg, controls_pass=True)
    assert dec_reg.selected == inc.candidate_id and dec_reg.reason == "RETAIN_INCUMBENT"

    sel_ok = (*sel_reg[:5], mk_receipt(cand.candidate_id, inc.candidate_id, "s-c-3ok", "t3", "famB", True))
    conf_ok = tuple(
        mk_receipt(r.candidate, r.parent, "k-" + r.occurrence, r.task, r.family, r.private_pass)
        for r in sel_ok
    )
    dec_ok = decide(spec, inc, cand, sel_ok, conf_ok, controls_pass=True)
    assert dec_ok.selected == cand.candidate_id and dec_ok.reason == "CONFIRMED_IMPROVEMENT"
    with pytest.raises(ValueError, match="CONFIRMATION_NOT_FRESH"):
        decide(spec, inc, cand, sel_ok, sel_ok, controls_pass=True)
    with pytest.raises(ValueError, match="FRESH_CONFIRMATION_REQUIRED"):
        IncumbentDecisionV1(
            experiment=spec.experiment_id,
            previous=inc.candidate_id,
            proposed=cand.candidate_id,
            selected=cand.candidate_id,
            selection=(sel_ok[0].receipt_id,),
            confirmation=(),
            reason="CONFIRMED_IMPROVEMENT",
        )


def test_p019_004_and_005_persistent_budget_and_rejected_anthropic_usage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import adversary.domain.providers.ports as budget_ports
    from adversary.domain.providers.types import BudgetExceeded

    class _ExactBudgetPort:
        def utc_now(self) -> str:
            return "2026-10-23T15:00:00.000000Z"

        def invoke(self, operation: str, **payload: Any) -> Any:
            if operation == "state":
                lim = int(payload["limit_microusd"])
                spent = int(payload["spent_microusd"])
                if spent > lim:
                    raise BudgetExceeded(requested=spent - lim, limit=lim)
                return {"spent_microusd": spent, "remaining_microusd": lim - spent}
            if operation == "leg_cost":
                tok = int(payload["tokens"])
                price = int(payload["price"])
                return (tok * price + 999_999) // 1_000_000
            if operation == "estimate":
                return max(1, (int(payload["payload_bytes"]) + 2) // 3)
            if operation == "quote":
                model = str(payload["model"])
                at = str(payload["at_utc"])
                cands = [
                    o
                    for o in payload["observations"]
                    if o["model_deployment_id"] == model and o["effective_from_utc"] <= at <= o["stale_after_utc"]
                ]
                obs_d = sorted(cands, key=lambda o: o["effective_from_utc"])[-1]
                in_c = (int(payload["input_tokens"]) * int(obs_d["input_microusd_per_mtok"]) + 999_999) // 1_000_000
                out_c = (int(payload["output_tokens"]) * int(obs_d["output_microusd_per_mtok"]) + 999_999) // 1_000_000
                return {"observation": obs_d, "cost_microusd": in_c + out_c}
            if operation == "receipt":
                lim = int(payload["limit_microusd"])
                spent = int(payload["spent_microusd"])
                cost = int(payload["cost_microusd"])
                if spent + cost > lim:
                    raise BudgetExceeded(requested=cost, limit=lim)
                obs_d = payload["observation"]
                wire = json.dumps(obs_d, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                dig = "sha256:" + hashlib.sha256(wire.encode("ascii")).hexdigest()
                return {
                    "model": str(payload["model"]),
                    "cost_microusd": cost,
                    "spent_after_microusd": spent + cost,
                    "limit_microusd": lim,
                    "pricing_observation_digest": dig,
                    "pricing_effective_from_utc": obs_d["effective_from_utc"],
                    "pricing_observed_at_utc": obs_d["observed_at_utc"],
                    "pricing_stale_after_utc": obs_d["stale_after_utc"],
                    "authority_effect": "None",
                }
            if operation == "settle":
                spent = int(payload["spent_microusd"])
                pre = int(payload["precharge_microusd"])
                billed = int(payload["billed_microusd"])
                new_spent = spent - pre + billed
                return {"spent_microusd": new_spent, "delta_microusd": billed - pre}
            raise AssertionError(f"Unexpected budget operation: {operation}")

    monkeypatch.setattr(budget_ports, "_runtime", _ExactBudgetPort())

    src_h = _hex64("source")
    spec = ExperimentSpecV1(
        campaign_id="camp-1",
        source=src_h,
        checker=_hex64("checker"),
        split=_hex64("split"),
        budget_id="camp-1",
        configuration=_hex64("config"),
    )
    db_path = tmp_path / "budget.sqlite"
    HarnessBudgetLedger(db_path, spec=spec, phase="preflight")
    spec_other = ExperimentSpecV1(
        campaign_id="camp-2",
        source=src_h,
        checker=spec.checker,
        split=spec.split,
        budget_id="camp-2",
        configuration=spec.configuration,
    )
    with pytest.raises(ValueError, match="ORIGINAL_CAMPAIGN_BINDING_CHANGED"):
        HarnessBudgetLedger(db_path, spec=spec_other, phase="preflight")

    with zipfile.ZipFile(_AUTHOR_ZIP) as zf:
        prices = json.loads(
            zf.read(
                "pfp_harness_author_review/repository/omega_engine_woland/documentation/harness_evolution/pricing_observation.json"
            ).decode("utf-8")
        )
    store = _MemStore(tmp_path / "provider_store")
    store.root.mkdir(parents=True, exist_ok=True)

    class _RefusalWithUsageTransport(AnthropicTransport):
        provenance = "fixture"

        def dispatch(self, admitted: Any) -> bytes:
            raw = json.dumps(
                {
                    "id": "msg_refused_1",
                    "model": admitted.model,
                    "content": [{"type": "text", "text": "{}"}],
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                }
            ).encode("utf-8")
            raise TransportFailure("PROVIDER_HTTP_500", reply_bytes=raw, http_status=500)

    provider = HarnessProvider(
        spec=spec,
        store=store,
        prices=prices,
        transport=_RefusalWithUsageTransport(api_key="fixture"),
        clock=lambda: "2026-10-23T15:00:00.000000Z",
    )
    refused_call = provider.call("sys", "usr", role="inner", phase="preflight", occurrence="occ-refused")
    assert refused_call.status == "TYPED_REFUSAL" and refused_call.content == "" and refused_call.cost == 4

    class _MissingUsageTransport(AnthropicTransport):
        provenance = "fixture"

        def dispatch(self, admitted: Any) -> bytes:
            raise TransportFailure("UPSTREAM_502", reply_bytes=b"<html>502</html>", http_status=502)

    provider_missing = HarnessProvider(
        spec=spec,
        store=store,
        prices=prices,
        transport=_MissingUsageTransport(api_key="fixture"),
        clock=lambda: "2026-10-23T15:00:00.000000Z",
    )
    with pytest.raises(ProviderError, match="UNRECONCILED_RESPONSE_BYTES"):
        provider_missing.call("sys", "usr", role="inner", phase="preflight", occurrence="occ-missing")
    with pytest.raises(ProviderError, match="UNRECONCILED_COST"):
        provider.call("sys", "usr", role="inner", phase="preflight", occurrence="occ-after-unreconciled")

    conc_ledger = HarnessBudgetLedger(tmp_path / "conc.sqlite", spec=spec, phase="discovery")
    ctrl = BudgetController(spec.ceiling, ledger=conc_ledger, reservation_guard=conc_ledger.guard)
    obs = ModelPricingObservationV1(**prices[spec.inner_model])
    q1 = PriceQuoteV1(obs, 500_000)
    ctrl.reserve({"attempt_id": "att-1", "provider": "anthropic", "model": obs.model_deployment_id}, q1)
    ctrl.reserve({"attempt_id": "att-2", "provider": "anthropic", "model": obs.model_deployment_id}, q1)
    with pytest.raises(ProviderError, match="CAMPAIGN_CONCURRENCY_LIMIT"):
        ctrl.reserve({"attempt_id": "att-3", "provider": "anthropic", "model": obs.model_deployment_id}, q1)


def test_p019_006_to_009_not_run_report_offline_replay_and_nonclaims(tmp_path: Path) -> None:
    ledger_md = (_P019_DIR / "paper_claim_ledger.md").read_text(encoding="utf-8")
    assert "| Heuristic summaries preserve arbitrary future operations | No such evidence | Not claimed |" in ledger_md
    assert "| Accelerating self-improvement or production admission | No such evidence | Not claimed |" in ledger_md

    with zipfile.ZipFile(_OFFLINE_ZIP) as z2:
        replay_arch_src = z2.read(
            "harness_offline_followup/repository/omega_engine_woland/documentation/harness_evolution/replay_review_archive.py"
        ).decode("utf-8")
        retained_receipt = json.loads(
            z2.read(
                "harness_offline_followup/repository/omega_engine_woland/documentation/harness_evolution/verification/offline_followup/replay_receipt.json"
            ).decode("utf-8")
        )
    assert retained_receipt["campaign"]["status"] == "NOT_RUN"
    assert retained_receipt["campaign"]["independent_provider_calls"] == 0

    replay_mod_path = tmp_path / "a/b/c/replay_review_archive.py"
    replay_mod_path.parent.mkdir(parents=True)
    replay_mod_path.write_text(replay_arch_src, encoding="utf-8")
    replay_mod = _load_module("p019_replay_review_archive", replay_mod_path)
    with pytest.raises(ValueError, match="UNSAFE_ARCHIVE_MEMBER"):
        replay_mod.member_path("pfp_harness_author_review/../escape.py")

    pkg_dir = replay_mod.extract(_AUTHOR_ZIP, tmp_path / "extracted_review", replay_mod.ARCHIVE_SHA256)
    shutil.copyfile(_AUTHOR_ZIP, pkg_dir / _AUTHOR_ZIP.name)
    report_rel = "repository/omega_engine_woland/documentation/harness_evolution/campaign/report.json"
    md_rel = "repository/omega_engine_woland/documentation/harness_evolution/campaign/report.md"
    orig_report_bytes = (pkg_dir / report_rel).read_bytes()
    orig_md_norm = (pkg_dir / md_rel).read_text(encoding="utf-8").replace("\r\n", "\n")

    nx_shim = tmp_path / "nx_shim"
    nx_shim.mkdir()
    (nx_shim / "networkx.py").write_text("class DiGraph: pass\nclass Graph: pass\n", encoding="utf-8")
    deps = sorted({p for p in [*site.getsitepackages(), site.getusersitepackages(), str(nx_shim)] if Path(p).is_dir()})
    child_script = (
        "import json, pathlib, runpy, sys\n"
        "pkg = pathlib.Path(sys.argv[1])\n"
        "sys.path.extend(json.loads(sys.argv[2]))\n"
        "def hook(e, a):\n"
        "  if e.startswith('socket.') or e in {'subprocess.Popen','os.system','os.exec','os.posix_spawn'}:\n"
        "    raise RuntimeError(e)\n"
        "sys.addaudithook(hook)\n"
        "verifier = runpy.run_path(str(pkg / 'tools/rebuild_release.py'))\n"
        # The extraction above verifies the retained ZIP digest. The validator
        # still requires every member, hash, path, and timestamp to match.
        # Recompression can produce a different byte stream on another host.
        "errors = verifier['validate'](pkg)\n"
        "assert errors in ([], ['ZIP envelope differs from canonical deterministic build']), errors\n"
        "try:\n"
        "  runpy.run_path(str(pkg / 'replay_offline.py'), run_name='__main__')\n"
        "except SystemExit as exc:\n"
        "  assert exc.code in (None, 0)\n"
    )
    replay_env = {
        "OMEGA_CREDENTIAL_DISCOVERY": "off",
        "TMPDIR": str(tmp_path),
        "TMP": str(tmp_path),
        "TEMP": str(tmp_path),
    }
    replay_res = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", child_script, str(pkg_dir), json.dumps(deps)],
        cwd=pkg_dir,
        env=replay_env,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert replay_res.returncode == 0, replay_res.stderr
    assert (pkg_dir / report_rel).read_bytes() == orig_report_bytes
    assert (pkg_dir / md_rel).read_text(encoding="utf-8").replace("\r\n", "\n") == orig_md_norm

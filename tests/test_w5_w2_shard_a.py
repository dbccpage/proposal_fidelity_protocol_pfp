"""Verification suite for Window 5 Wave 2 Shard A (Paper 009 Final 4 Claims).

AuthorityEffect: None.

Covers:
1. AUDIT-P009-015 -> ATL-P009-015 (partial, relation: narrows):
   Gate falsifier F2a/F2b keyword-adjudication replay and typed-critique remediation.
2. AUDIT-P009-016 -> ATL-P009-016 (partial, relation: narrows):
   Gate falsifier F3 run-key SHA-256 reference and unbalanced dual-witness receipt audit.
3. AUDIT-P009-017 -> ATL-P009-017 (partial, relation: narrows):
   Gate falsifier F4 C012 templated challenge-gate narrative and step-record replay audit.
4. AUDIT-P009-018 -> ATL-P009-018 (partial, relation: narrows):
   Corrected Adversary gate and reference self-consistency runner source and execution review.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Mapping
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PFP009_ROOT = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "009_pfp_adversarial_dialectics_and_terminal_reality_gates"
)
_HIST_DIR = _PFP009_ROOT / "docs" / "historical_evidence"
_FALSIFIERS_JSON = _HIST_DIR / "adversary_gate_falsifiers.json"
_PROVENANCE_JSON = _HIST_DIR / "provenance.json"
_REPLAY_SCRIPT = _REPO_ROOT / "atlas" / "archive" / "pfp" / "tools" / "replay_adversary_gate_falsifiers.py"
_TRIANGLE_PATH = _PFP009_ROOT / "code" / "triangle_cycle_sum.py"
_REVIEW_COUNTS_PATH = _PFP009_ROOT / "code" / "review_counts.py"
_TEST_REVIEW_COUNTS_PATH = _PFP009_ROOT / "code" / "tests" / "test_review_counts.py"
_PARITY_FIXTURE_PATH = (
    _REPO_ROOT / "code" / "rust" / "tests" / "core_adversary" / "fixtures" / "python_evidence_parsers_v1.json"
)
_C011_MANIFEST = (
    _REPO_ROOT
    / "workflows"
    / "tasks"
    / "certified_challenges"
    / "c011_cycle_rank_ladder_coboundary_repair"
    / "judge_packet"
    / "manifest.json"
)
_C012_DIR = (
    _REPO_ROOT
    / "workflows"
    / "tasks"
    / "certified_challenges"
    / "c012_cellular_sheaf_h0_h1"
)
_C012_MANIFEST = _C012_DIR / "judge_packet" / "manifest.json"
_C051_RUNNER_PATH = (
    _REPO_ROOT
    / "workflows"
    / "wf11_dual_certificate_synthesis"
    / "pilots"
    / "c051_exact_lp_solver_with_duals"
    / "commit_reveal_c051.py"
)
_REVIEW_JSON_PATH = _REPO_ROOT / "dag" / "reviews" / "additional_w5_w2_shard_a.json"
_DERIVATION_PATHS: tuple[Path, ...] = (
    _REPO_ROOT / "dag" / "derivations" / "audit_p009_015.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p009_016.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p009_017.md",
    _REPO_ROOT / "dag" / "derivations" / "audit_p009_018.md",
)

_AUDITED_COMMIT = "30609de2c3928238715375a9bac608256fa381d8"
_FIX_COMMIT_GATE = "a054c8ce17c3025ac5518aaeef29096a299519bb"
_FIX_COMMIT_COPIES = "e6fbc15cf011121597a82a1d199626063bedf7c0"

_CRITIQUE_FENCE_RE = re.compile(r"(?s)```critique[ \t]*\r?\n(.*?)\r?\n```")
_SHA256_REF_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


@pytest.fixture(autouse=True)
def _isolate_runtime_and_modules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[None]:
    """Enforce zero bytecode emission, temp redirection, and sys.modules teardown."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    tmp_str = str(tmp_path)
    for env_var in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.setenv(env_var, tmp_str)
    monkeypatch.setattr(tempfile, "tempdir", tmp_str)

    pre_modules = dict(sys.modules)
    before_sys_path = list(sys.path)
    try:
        yield
    finally:
        sys.path[:] = before_sys_path
        for mod_name in list(sys.modules):
            if mod_name not in pre_modules:
                sys.modules.pop(mod_name, None)
        for mod_name, orig_mod in pre_modules.items():
            if mod_name not in sys.modules or sys.modules[mod_name] is not orig_mod:
                sys.modules[mod_name] = orig_mod


def _lf_bytes(path: Path) -> bytes:
    """Return LF-normalized bytes of a file."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _lf_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest over LF-normalized file bytes."""
    return hashlib.sha256(_lf_bytes(path)).hexdigest()


def _prefixed_sha256(data: str | bytes) -> str:
    """Compute sha256:<hex> over UTF-8 text or raw bytes."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _load_file_module(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    file_path: Path,
) -> ModuleType:
    """Load a Python file into sys.modules under monkeypatch isolation."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to build module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


def _load_adversary_modules(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Import active ops/adversary and pfp modules inside isolated test scope."""
    monkeypatch.syspath_prepend(str(_REPO_ROOT))
    monkeypatch.syspath_prepend(str(_REPO_ROOT / "ops"))
    return {
        "act_helpers": importlib.import_module("adversary.use_cases.act_helpers"),
        "bout_service": importlib.import_module("adversary.use_cases.bout_service"),
        "skill_run": importlib.import_module("adversary.use_cases.skill_run_persistence"),
        "evidence": importlib.import_module("adversary.domain.evidence"),
        "ports": importlib.import_module("adversary.domain.ports"),
        "run_swarm": importlib.import_module("adversary.stage.application.run_swarm"),
        "stage_domain": importlib.import_module("adversary.stage.domain"),
        "rop": importlib.import_module("operations.domain.rop.result"),
        "seat_turn": importlib.import_module("pfp.domain.value_objects.seat_turn"),
    }


def _reject_nonfinite_json(token: str) -> Any:
    raise ValueError(f"non-finite JSON constant {token} is not admitted")


def _strict_json_loads(text: str) -> Any:
    return json.loads(text, parse_constant=_reject_nonfinite_json)


def _malformed_critique_dict(reason: str) -> dict[str, Any]:
    return {
        "status": "MALFORMED",
        "blocking": True,
        "counterexample": "",
        "challenge_kind": "PROVENANCE",
        "parse_error": reason,
    }


class _ParseDefectError(Exception):
    """Internal control-flow signal carrying the first evidence parse failure message."""


def _parse_critique_object(reply: Any, challenge_kinds: tuple[str, ...]) -> dict[str, Any]:
    if type(reply) is not str:
        raise _ParseDefectError("the critique reply is not text")
    blocks = _CRITIQUE_FENCE_RE.findall(reply)
    if len(blocks) != 1:
        raise _ParseDefectError(f"expected exactly one critique block, found {len(blocks)}")
    try:
        payload = _strict_json_loads(blocks[0])
    except ValueError as exc:
        raise _ParseDefectError(f"critique block is not JSON: {exc}") from exc
    if type(payload) is not dict:
        raise _ParseDefectError("critique block must hold a JSON object")
    unknown = sorted(k for k in payload if k not in {"blocking", "counterexample", "kind"})
    if unknown:
        raise _ParseDefectError(f"unknown critique keys: {', '.join(unknown)}")
    blocking = payload.get("blocking")
    if type(blocking) is not bool:
        raise _ParseDefectError("critique.blocking must be JSON true or false")
    if "counterexample" not in payload:
        raise _ParseDefectError("critique.counterexample is required (a string or null)")
    raw_ce = payload["counterexample"]
    if raw_ce is None:
        ce_text = ""
    elif type(raw_ce) is str:
        ce_text = raw_ce.strip()
    else:
        raise _ParseDefectError("critique.counterexample must be a string or null")
    if blocking and not ce_text:
        raise _ParseDefectError("a blocking critique must give a nonempty counterexample")
    default_kind = "COUNTERMODEL" if blocking else "LOGIC"
    kind_val = payload.get("kind", default_kind) if "kind" in payload else default_kind
    if type(kind_val) is not str or kind_val not in challenge_kinds:
        kinds_repr = ", ".join(repr(k) for k in challenge_kinds)
        raise _ParseDefectError(f"critique.kind {kind_val!r} is not one of [{kinds_repr}]")
    return {
        "status": "STRUCTURED",
        "blocking": blocking,
        "counterexample": ce_text,
        "challenge_kind": kind_val,
        "parse_error": "",
    }


def _eval_structured_critique(reply: Any, challenge_kinds: tuple[str, ...]) -> dict[str, Any]:
    """Evaluate parse_structured_critique per code/rust/core_adversary/src/evidence_parse.rs."""
    try:
        return _parse_critique_object(reply, challenge_kinds)
    except _ParseDefectError as defect:
        return _malformed_critique_dict(str(defect))


def _parse_checker_receipt_object(raw_hex: str) -> dict[str, Any]:
    raw = bytes.fromhex(raw_hex)
    if not raw:
        raise _ParseDefectError("the checker receipt is empty")
    try:
        text = raw.decode("utf-8")
        payload = _strict_json_loads(text)
    except (UnicodeDecodeError, ValueError) as exc:
        raise _ParseDefectError(f"the checker receipt is not UTF-8 JSON: {exc}") from exc
    if type(payload) is not dict:
        raise _ParseDefectError("the checker receipt must be a JSON object")
    verdict = payload.get("verdict")
    if type(verdict) is not str or verdict not in ("ACCEPTED", "REJECTED", "NOT_MEASURED"):
        raise _ParseDefectError("checker receipt verdict must be ACCEPTED, REJECTED or NOT_MEASURED")
    digest = payload.get("candidate_content_sha256")
    if type(digest) is not str or _SHA256_REF_RE.fullmatch(digest) is None:
        raise _ParseDefectError(
            "checker receipt candidate_content_sha256 must be sha256:<64 lowercase hex>"
        )
    checker_id = payload.get("checker_id")
    if type(checker_id) is not str or not checker_id.strip():
        raise _ParseDefectError("checker receipt checker_id must be a nonempty string")
    cand_raw = payload.get("candidate_id")
    if cand_raw is None:
        cand_id = None
    elif type(cand_raw) is str and cand_raw.strip():
        cand_id = cand_raw
    else:
        raise _ParseDefectError("checker receipt candidate_id must be a nonempty string when present")
    return {
        "verdict": verdict,
        "candidate_content_sha256": digest,
        "checker_id": checker_id,
        "candidate_id": cand_id,
    }


def _eval_checker_receipt(raw_hex: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Evaluate parse_checker_receipt per code/rust/core_adversary/src/evidence_parse.rs."""
    try:
        return _parse_checker_receipt_object(raw_hex), None
    except _ParseDefectError as defect:
        return None, {
            "code": "ADVERSARY_EVIDENCE_VALUE_ERROR",
            "message": str(defect),
            "locus": "adversary.domain.evidence",
            "details": {},
        }


class _SpecExactNativeSupport:
    """In-process NativeOperationPort implementing evidence_parse.rs contracts."""

    def __init__(self, ok_cls: Any, challenge_kinds: tuple[str, ...]) -> None:
        self._ok = ok_cls
        self._challenge_kinds = tuple(challenge_kinds)

    def invoke_runtime_with_file(
        self,
        action: str,
        payload: Mapping[str, Any],
        *,
        file_action: str,
    ) -> Any:
        assert action == "adversary_support"
        assert file_action == "adversary_support_file"
        op = payload["operation"]
        if op == "critique":
            outcome = _eval_structured_critique(payload.get("reply"), self._challenge_kinds)
            return self._ok({"success": True, "result": {"refusal": None, "outcome": outcome}})
        if op == "checker_receipt":
            outcome, refusal = _eval_checker_receipt(payload["receipt_hex"])
            return self._ok({"success": True, "result": {"refusal": refusal, "outcome": outcome}})
        raise RuntimeError(f"Unsupported operation in test port: {op!r}")


class _StaticSeatPort:
    """SeatPortV1 double matching Seat(text) in replay_adversary_gate_falsifiers.py."""

    def __init__(self, ok_cls: Any, reply_cls: Any, text: str, disposition: str = "KILL") -> None:
        self._ok = ok_cls
        self._reply_cls = reply_cls
        self._text = text
        self._disposition = disposition

    def execute_turn(self, request: Any) -> Any:
        del request
        return self._ok(
            self._reply_cls(
                reply_text=self._text,
                machine_fields={"DISPOSITION": self._disposition},
                raw_bytes=self._text.encode("utf-8"),
            )
        )


def _make_candidate(stage_domain: Any, payload: bytes, tag: str = "a") -> Any:
    """Construct a CandidateProposalV1 bound to payload's sha256 digest."""
    return stage_domain.CandidateProposalV1(
        producer_agent_id="seat_proposer",
        work_packet_id="sha256:" + (tag * 64),
        artifact_refs=(_prefixed_sha256(payload),),
        prediction_receipt_id="sha256:" + ("b" * 64),
        nonclaims=("Scoped test candidate.",),
    )


def _ensure_stub_package(monkeypatch: pytest.MonkeyPatch, module_name: str) -> ModuleType | None:
    """Return a synthetic package stub in sys.modules when top-level package is absent."""
    parts = module_name.split(".")
    top_pkg = parts[0]
    existing = sys.modules.get(top_pkg)
    if existing is None and importlib.util.find_spec(top_pkg) is not None:
        return None
    if existing is not None and getattr(existing, "__spec__", None) is not None:
        return None
    parent_mod: ModuleType | None = None
    for depth in range(1, len(parts) + 1):
        mod_key = ".".join(parts[:depth])
        mod_obj = sys.modules.get(mod_key)
        if mod_obj is None:
            mod_obj = ModuleType(mod_key)
            mod_obj.__path__ = []  # type: ignore[attr-defined]
            monkeypatch.setitem(sys.modules, mod_key, mod_obj)
        if parent_mod is not None:
            setattr(parent_mod, parts[depth - 1], mod_obj)
        parent_mod = mod_obj
    return parent_mod


def _load_c051_runner(
    monkeypatch: pytest.MonkeyPatch,
    script_path: Path,
    *,
    solve_fn: Callable[[Mapping[str, Any]], Any],
    check_exact_fn: Callable[[Mapping[str, Any], Any], tuple[Any, str]],
    check_indep_fn: Callable[[Mapping[str, Any], Any], tuple[Any, str]],
    default_root: Path,
) -> ModuleType:
    """Load commit_reveal_c051.py dynamically by stubbing missing external imports via AST."""
    tree = ast.parse(script_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        stub_mod = _ensure_stub_package(monkeypatch, node.module)
        if stub_mod is None:
            continue
        for alias in node.names:
            if alias.name == "solve":
                setattr(stub_mod, alias.name, solve_fn)
            elif alias.name == "check_solution":
                fn = check_exact_fn if "exact_checker" in node.module else check_indep_fn
                setattr(stub_mod, alias.name, fn)
            elif alias.name == "resolve_intelligence_repo_root":
                setattr(stub_mod, alias.name, lambda: default_root)

    return _load_file_module(monkeypatch, f"_c051_sut_{id(script_path)}", script_path)


# ---------------------------------------------------------------------------
# 1. AUDIT-P009-015: Gate falsifier F2a / F2b replay & typed critique parser
# ---------------------------------------------------------------------------


class TestGateFalsifierF2Replay:
    """Verifies AUDIT-P009-015: F2a/F2b keyword inversion and fenced JSON remediation."""

    F2A_TEXT = "Counterexample: the residual (0,0,3) has cycle sum 3, so the claimed repair is false."
    F2B_TEXT = "No defect found; the certificate checks."

    def test_retained_f2a_f2b_records_and_replay_driver_pin_keyword_inversion(self) -> None:
        """Positive test: retained F2a/F2b rows and replay script pin keyword inversion at 30609de2."""
        prov = json.loads(_PROVENANCE_JSON.read_text(encoding="utf-8"))
        assert prov["audited_gate_commit"] == _AUDITED_COMMIT

        falsifiers = json.loads(_FALSIFIERS_JSON.read_text(encoding="utf-8"))
        assert falsifiers["audited_commit"] == _AUDITED_COMMIT
        by_id = {row["id"]: row for row in falsifiers["falsifiers"]}

        f2a = by_id["F2a"]
        f2b = by_id["F2b"]
        assert f2a["defect"] == "keyword adjudication"
        assert f2b["defect"] == "keyword adjudication"
        assert f2a["input"] == f"critic reply: {self.F2A_TEXT!r}"
        assert f2b["input"] == f"critic reply: {self.F2B_TEXT!r}"
        assert "defect" not in self.F2A_TEXT.lower() and "flaw" not in self.F2A_TEXT.lower()
        assert "defect" in self.F2B_TEXT.lower()

        assert f2a["expected"] == "blocking"
        assert f2a["observed"] == "not blocking"
        assert f2a["candidate_survives"] is True

        assert f2b["expected"] == "not blocking"
        assert f2b["observed"] == "blocking"
        assert f2b["candidate_survives"] is False

        replay_src = _REPLAY_SCRIPT.read_text(encoding="utf-8")
        assert 'machine_fields={"DISPOSITION": "KILL"}' in replay_src
        assert 'payload = b"potential f=(0,1,2)"' in replay_src
        assert self.F2A_TEXT in replay_src
        assert self.F2B_TEXT in replay_src

        # Audited external commit is absent from this split checkout's Git object store.
        cat_res = subprocess.run(
            ["git", "cat-file", "-t", _AUDITED_COMMIT],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert cat_res.returncode != 0

    def test_f2a_counterexample_residual_has_exact_nonzero_cycle_sum(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Positive test: F2a's (0, 0, 3) residual is the exact coboundary residual of f=(0,1,2)."""
        tri = _load_file_module(monkeypatch, "_w5_w2_shard_a_triangle", _TRIANGLE_PATH)
        unit_cochain = (Fraction(1), Fraction(1), Fraction(1))
        proposed_potential = (Fraction(0), Fraction(1), Fraction(2))
        coboundary = tri.edge_differences(proposed_potential)
        residual = tri.subtract(unit_cochain, coboundary)

        assert coboundary == (Fraction(1), Fraction(1), Fraction(-2))
        assert residual == (Fraction(0), Fraction(0), Fraction(3))
        assert tri.cycle_sum(residual) == Fraction(3)
        assert tri.cycle_sum(residual) != Fraction(0)

    def test_remediated_act5_typed_critique_parser_blocks_f2a_f2b_and_ignores_prose_keywords(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Positive test: active Act V blocks prose-only F2a/F2b as MALFORMED and obeys JSON over prose."""
        mods = _load_adversary_modules(monkeypatch)
        act_helpers = mods["act_helpers"]
        evidence = mods["evidence"]
        run_swarm = mods["run_swarm"]
        stage_domain = mods["stage_domain"]
        rop = mods["rop"]
        seat_turn = mods["seat_turn"]

        native = _SpecExactNativeSupport(rop.Ok, tuple(sorted(evidence.CHALLENGE_KINDS)))
        triangle = act_helpers.Network(
            nodes=(0, 1, 2),
            edges=((0, 1), (1, 2), (2, 0)),
            faces=(),
        )
        payload = b"potential f=(0,1,2)"
        cand = _make_candidate(stage_domain, payload)

        # 1. Raw prose F2a and F2b both fail closed as MALFORMED (blocking == True, killed on KILL).
        for raw_text in (self.F2A_TEXT, self.F2B_TEXT):
            rt = run_swarm.SwarmRuntimeV1(
                seat_port=_StaticSeatPort(rop.Ok, seat_turn.SeatTurnReplyV1, raw_text),
                max_critique_rounds=1,
            )
            res = act_helpers.execute_act5_independent_witness(
                rt,
                "f2_remediated",
                "repair",
                triangle,
                [cand],
                [],
                candidate_payloads={cand.candidate_id: payload},
                native_support=native,
            )
            surviving, dead, _, critiques, critiques_data, verdicts, _ = res.unwrap()
            assert surviving == []
            assert len(dead) == 1
            assert verdicts[cand.candidate_id] == "MALFORMED"
            assert critiques[0].blocking is True
            assert critiques_data[0]["verification_status"] == "NOT_RUN"

        # 2. Structured F2a counterexample without 'DEFECT' or 'FLAW' blocks as BLOCKING.
        structured_f2a = (
            f"{self.F2A_TEXT}\n"
            "```critique\n"
            '{"blocking": true, "counterexample": "residual (0,0,3) has cycle sum 3"}\n'
            "```"
        )
        assert "defect" not in structured_f2a.lower() and "flaw" not in structured_f2a.lower()
        rt_f2a = run_swarm.SwarmRuntimeV1(
            seat_port=_StaticSeatPort(rop.Ok, seat_turn.SeatTurnReplyV1, structured_f2a),
            max_critique_rounds=1,
        )
        surv_a, dead_a, _, chals_a, _, verdicts_a, _ = (
            act_helpers.execute_act5_independent_witness(
                rt_f2a,
                "f2a_structured",
                "repair",
                triangle,
                [cand],
                [],
                candidate_payloads={cand.candidate_id: payload},
                native_support=native,
            ).unwrap()
        )
        assert surv_a == []
        assert len(dead_a) == 1
        assert verdicts_a[cand.candidate_id] == "BLOCKING"
        assert chals_a[0].blocking is True

        # 3. Structured F2b with 'defect' and 'FLAW' in prose header does NOT block when JSON is false.
        structured_f2b = (
            f"{self.F2B_TEXT} DEFECT and FLAW mentioned in prose.\n"
            "```critique\n"
            '{"blocking": false, "counterexample": null}\n'
            "```"
        )
        parsed_f2b = evidence.parse_structured_critique(structured_f2b, native_support=native)
        assert parsed_f2b.status is evidence.CritiqueStatus.STRUCTURED
        assert parsed_f2b.blocking is False

        rt_f2b = run_swarm.SwarmRuntimeV1(
            seat_port=_StaticSeatPort(rop.Ok, seat_turn.SeatTurnReplyV1, structured_f2b),
            max_critique_rounds=1,
        )
        surv_b, dead_b, _, chals_b, _, verdicts_b, _ = (
            act_helpers.execute_act5_independent_witness(
                rt_f2b,
                "f2b_structured",
                "repair",
                triangle,
                [cand],
                [],
                candidate_payloads={cand.candidate_id: payload},
                native_support=native,
            ).unwrap()
        )
        assert surv_b == [cand]
        assert dead_b == []
        assert verdicts_b[cand.candidate_id] == "NON_BLOCKING"
        assert chals_b[0].blocking is False

    def test_falsification_sut_critique_parser_and_act5_reject_malformed_and_mutated_inputs(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Negative control: SUT StructuredCritiqueV1 and Act V refuse non-blocking malformed or mutated payloads."""
        mods = _load_adversary_modules(monkeypatch)
        act_helpers = mods["act_helpers"]
        evidence = mods["evidence"]
        run_swarm = mods["run_swarm"]
        stage_domain = mods["stage_domain"]
        rop = mods["rop"]
        seat_turn = mods["seat_turn"]

        native = _SpecExactNativeSupport(rop.Ok, tuple(sorted(evidence.CHALLENGE_KINDS)))

        # Constructing MALFORMED with blocking=False raises ValueError (fail-closed contract).
        with pytest.raises(ValueError, match="MALFORMED critique must block"):
            evidence.StructuredCritiqueV1(
                status=evidence.CritiqueStatus.MALFORMED,
                blocking=False,
                counterexample="",
                challenge_kind="LOGIC",
                parse_error="missing fence",
            )

        with pytest.raises(TypeError, match="blocking must be an exact bool"):
            evidence.StructuredCritiqueV1(
                status=evidence.CritiqueStatus.STRUCTURED,
                blocking=1,  # type: ignore[arg-type]
                counterexample="x",
                challenge_kind="LOGIC",
            )

        with pytest.raises(ValueError, match="challenge_kind is not closed"):
            evidence.StructuredCritiqueV1(
                status=evidence.CritiqueStatus.STRUCTURED,
                blocking=False,
                counterexample="",
                challenge_kind="NOT_A_KIND",
            )

        # Two fenced blocks, blocking=true with empty counterexample, and NaN all parse as MALFORMED + blocking.
        for bad_reply in (
            "```critique\n{\"blocking\": false, \"counterexample\": null}\n```\n"
            "```critique\n{\"blocking\": false, \"counterexample\": null}\n```",
            "```critique\n{\"blocking\": true, \"counterexample\": \"   \"}\n```",
            "```critique\n{\"blocking\": false, \"counterexample\": NaN}\n```",
        ):
            crit = evidence.parse_structured_critique(bad_reply, native_support=native)
            assert crit.status is evidence.CritiqueStatus.MALFORMED
            assert crit.blocking is True

        # Act V refuses missing or mismatched candidate payload bytes before invoking the seat.
        payload = b"potential f=(0,1,2)"
        cand = _make_candidate(stage_domain, payload)
        rt = run_swarm.SwarmRuntimeV1(
            seat_port=_StaticSeatPort(rop.Ok, seat_turn.SeatTurnReplyV1, self.F2A_TEXT),
            max_critique_rounds=1,
        )
        missing_res = act_helpers.execute_act5_independent_witness(
            rt,
            "f2_missing",
            "repair",
            None,
            [cand],
            [],
            candidate_payloads={},
            native_support=native,
        )
        assert missing_res.is_err
        assert missing_res.error.code == "ADVERSARY_CANDIDATE_PAYLOAD_MISSING"

        mismatch_res = act_helpers.execute_act5_independent_witness(
            rt,
            "f2_mismatch",
            "repair",
            None,
            [cand],
            [],
            candidate_payloads={cand.candidate_id: b"tampered bytes"},
            native_support=native,
        )
        assert mismatch_res.is_err
        assert mismatch_res.error.code == "ADVERSARY_CANDIDATE_PAYLOAD_MISMATCH"


# ---------------------------------------------------------------------------
# 2. AUDIT-P009-016: Gate falsifier F3 phantom evidence & unbalanced witness
# ---------------------------------------------------------------------------


class TestGateFalsifierF3Replay:
    """Verifies AUDIT-P009-016: F3 run-key SHA-256 reference, witness imbalance, and digest-keyed receipts."""

    def test_retained_f3_record_and_unbalanced_witness_coboundary_refutation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Positive test: retained F3 JSON pins sha256('f3') and True flags on an unbalanced witness."""
        tri = _load_file_module(monkeypatch, "_w5_w2_shard_a_tri_f3", _TRIANGLE_PATH)
        falsifiers = json.loads(_FALSIFIERS_JSON.read_text(encoding="utf-8"))
        f3 = next(row for row in falsifiers["falsifiers"] if row["id"] == "F3")

        assert f3["defect"] == "phantom evidence references"
        assert f3["status"] == "BOUNDED_RESIDUAL"
        assert f3["observed"] == {
            "first_reference_is_sha256_of_run_key": True,
            "receipt_annihilates_coboundary": True,
            "receipt_norm_bounded": True,
        }

        replay_src = _REPLAY_SCRIPT.read_text(encoding="utf-8")
        assert 'dual_witness={"(0, 1)": "1"}' in replay_src
        assert 'refs[0] == sha("f3")' in replay_src
        assert _prefixed_sha256("f3") == (
            "sha256:625e0f649de27800fc3bcf4c118ef79f69dcb762c2e73fbb1cfce0e7a86f6b80"
        )

        # Exact incidence divergence and coboundary pairing for eta = 1_{(0, 1)} on triangle (0,1),(1,2),(2,0).
        edges = ((0, 1), (1, 2), (2, 0))
        eta = {(0, 1): Fraction(1), (1, 2): Fraction(0), (2, 0): Fraction(0)}
        net_divergence = {
            v: sum(eta[e] for e in edges if e[1] == v) - sum(eta[e] for e in edges if e[0] == v)
            for v in (0, 1, 2)
        }
        assert net_divergence == {0: Fraction(-1), 1: Fraction(1), 2: Fraction(0)}
        assert any(val != 0 for val in net_divergence.values())

        coboundary = tri.edge_differences((Fraction(0), Fraction(1), Fraction(0)))
        assert coboundary == (Fraction(1), Fraction(-1), Fraction(0))
        pairing = sum(
            w * df_val
            for w, df_val in zip((eta[(0, 1)], eta[(1, 2)], eta[(2, 0)]), coboundary, strict=True)
        )
        assert pairing == Fraction(1)
        assert pairing != Fraction(0)

    def test_remediated_act7_stores_digest_keyed_obstruction_receipt_without_constant_flags(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Positive test: active Act VII omits constant witness flags and cites stored receipt digest != sha('f3')."""
        mods = _load_adversary_modules(monkeypatch)
        act_helpers = mods["act_helpers"]
        evidence = mods["evidence"]
        stage_domain = mods["stage_domain"]

        cand = _make_candidate(stage_domain, b"x")
        f3_meas = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="f3_probe",
            phi1=Fraction(1),
            gamma2=Fraction(0),
            defect_count=1,
            active_obstructions=("edge_0_1",),
            certificate_verified=True,
            dual_witness=(("(0, 1)", Fraction(1)),),
        )
        status, _, proposal, is_authorized, narrative = act_helpers.execute_act7_authorization_gate(
            None,
            "f3",
            [cand],
            [],
            {},
            f3_meas,
            fixture_seats=False,
        ).unwrap()

        assert status == "BOUNDED_RESIDUAL"
        assert is_authorized is False

        obs_receipt = narrative["obstruction_non_vanishing_receipt"]
        assert "annihilates_coboundary" not in obs_receipt
        assert "norm_bounded" not in obs_receipt
        assert obs_receipt["receipt_type"] == "OBSTRUCTION_NON_VANISHING_RECEIPT"
        assert obs_receipt["phi1"] == "1"
        assert obs_receipt["dual_witness"] == [["(0, 1)", "1"]]

        expected_digest = act_helpers._canonical_json_digest(obs_receipt)
        assert expected_digest != _prefixed_sha256("f3")
        assert narrative["evidence_receipts"] == {expected_digest: obs_receipt}
        assert list(proposal.evidence_refs) == [expected_digest]

    def test_falsification_sut_act7_and_measurement_reject_invalid_witness_and_fallback_boundary(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Negative control: SUT measurement/Act VII reject float/bool/unverified inputs and record fallback scope."""
        mods = _load_adversary_modules(monkeypatch)
        act_helpers = mods["act_helpers"]
        evidence = mods["evidence"]
        stage_domain = mods["stage_domain"]

        # Float or bool rationals and unverified MEASURED states are rejected by ObstructionMeasurementV1.
        with pytest.raises(TypeError, match="exact rational required"):
            evidence.parse_exact_rational(1.0)
        with pytest.raises(TypeError, match="exact rational required"):
            evidence.parse_exact_rational(True)
        with pytest.raises(ValueError, match="without a verified certificate is NOT_MEASURED"):
            evidence.ObstructionMeasurementV1(
                status=evidence.MeasurementStatus.MEASURED,
                backend="f3_unverified",
                phi1=Fraction(1),
                gamma2=Fraction(0),
                defect_count=1,
                active_obstructions=("edge_0_1",),
                certificate_verified=False,
            )

        cand = _make_candidate(stage_domain, b"x")
        # Non-ObstructionMeasurementV1 passed to Act VII -> ADVERSARY_SCORER_CONTRACT_VIOLATION.
        bad_scorer = act_helpers.execute_act7_authorization_gate(
            None,
            "f3_bad_scorer",
            [cand],
            [],
            {},
            {"phi1": 1.0},  # type: ignore[arg-type]
        )
        assert bad_scorer.is_err
        assert bad_scorer.error.code == "ADVERSARY_SCORER_CONTRACT_VIOLATION"

        measured = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="f3_probe",
            phi1=Fraction(1),
            gamma2=Fraction(0),
            defect_count=1,
            active_obstructions=("edge_0_1",),
            certificate_verified=True,
            dual_witness=(("(0, 1)", Fraction(1)),),
        )
        # Undeclared carrier with MEASURED carrier -> ADVERSARY_CARRIER_STATUS_INVALID.
        bad_carrier_status = act_helpers.execute_act7_authorization_gate(
            None,
            "f3_bad_status",
            [cand],
            [],
            {},
            measured,
            carrier_status=act_helpers.CARRIER_NOT_DECLARED,
        )
        assert bad_carrier_status.is_err
        assert bad_carrier_status.error.code == "ADVERSARY_CARRIER_STATUS_INVALID"

        # Adversarial zero claim with Phi1 = 1 > 0 -> REFUSED + ADVERSARIAL_ZERO_CLAIM_REFUTED.
        refuted_status, sel_id, _, auth, nar = act_helpers.execute_act7_authorization_gate(
            None,
            "f3_zero_claim",
            [cand],
            [],
            {},
            measured,
            carrier_context={"adversarial_zero_claim": True},
            fixture_seats=False,
        ).unwrap()
        assert refuted_status == "REFUSED"
        assert sel_id == ""
        assert auth is False
        assert "ADVERSARIAL_ZERO_CLAIM_REFUTED" in nar["authorization_blockers"]
        assert nar["obstruction_non_vanishing_receipt"]["adversarial_zero_claim_refuted"] is True

        # Scope boundary documented in AUDIT-P009-016 Section 3.2:
        # NOT_MEASURED with zero receipts falls back to [epoch_id].
        not_measured = evidence.ObstructionMeasurementV1.not_measured(
            "no scorer configured",
            backend="null_scorer",
        )
        nm_status, _, nm_prop, nm_auth, nm_nar = act_helpers.execute_act7_authorization_gate(
            None,
            "f3_empty",
            [cand],
            [],
            {},
            not_measured,
            fixture_seats=False,
        ).unwrap()
        assert nm_status == "NOT_MEASURED"
        assert nm_auth is False
        assert nm_nar["evidence_receipts"] == {}
        assert list(nm_prop.evidence_refs) == [_prefixed_sha256("f3_empty")]


# ---------------------------------------------------------------------------
# 3. AUDIT-P009-017: Gate falsifier F4 C012 templated narrative & step record
# ---------------------------------------------------------------------------


class TestGateFalsifierF4Replay:
    """Verifies AUDIT-P009-017: F4 C012 templated novella/steps, C011/C012 manifests, and zero-case refusal."""

    def test_retained_f4_record_replay_script_and_five_probe_four_family_census(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Positive test: retained F4 record, replay driver, and test_review_counts verify F4 observations."""
        falsifiers = json.loads(_FALSIFIERS_JSON.read_text(encoding="utf-8"))
        f4 = next(row for row in falsifiers["falsifiers"] if row["id"] == "F4")
        assert f4["defect"] == "templated receipts"
        assert f4["input"] == "C012 gate: verdict REFUSE, 0 cases, 0 passed, 5 defects"
        assert f4["observed"] == {
            "novella_states_full_agreement": True,
            "novella_states_budget_respected": True,
            "novella_default_claim_46_cases": True,
            "novella_names_challenge_C011": True,
            "step_E_payload": [{"status": "repaired"}],
            "step_D_payload": [{"algorithm": "exact_rational_simplex"}],
        }

        replay_src = _REPLAY_SCRIPT.read_text(encoding="utf-8")
        assert (
            'C012_GATE = ("projects/mssn_sn_symgam/challenges/b_cohomology/"\n'
            '             "c012_cellular_sheaf_h0_h1/governance/adversary_gate.py")'
        ) in replay_src
        assert 'gate.generate_c011_novella("f4", "REFUSE", 0, 0, 5, 3.0, 1.0, {})' in replay_src
        assert 'gate.generate_c011_dda_steps("f4", "REFUSE", 0, 5)' in replay_src
        assert '"100% concordance across all cases" in novella' in replay_src
        assert '"Total inference budget respected" in novella' in replay_src
        assert '"zero duality gap on all 46 judge cases" in novella' in replay_src

        # Execute Paper 009's test_review_counts.test_gate_record_is_five_probes_in_four_families directly.
        _load_file_module(monkeypatch, "review_counts", _REVIEW_COUNTS_PATH)
        trc = _load_file_module(monkeypatch, "_w5_w2_shard_a_trc", _TEST_REVIEW_COUNTS_PATH)
        lf_root = tmp_path / "pfp009_lf"
        (lf_root / "docs" / "historical_evidence").mkdir(parents=True)
        (lf_root / "docs" / "historical_evidence" / "adversary_gate_falsifiers.json").write_bytes(
            _lf_bytes(_FALSIFIERS_JSON)
        )
        monkeypatch.setattr(trc, "ROOT", lf_root)
        trc.test_gate_record_is_five_probes_in_four_families()

    def test_c011_46_cases_vs_c012_68_cases_corroborate_foreign_c011_template(self) -> None:
        """Positive test: C011 manifest has 46 cases (32+8+6) while C012 has 68 cases (40+16+12) and no gate copy."""
        c011_manifest = json.loads(_C011_MANIFEST.read_text(encoding="utf-8"))
        c012_manifest = json.loads(_C012_MANIFEST.read_text(encoding="utf-8"))

        c011_files = [entry["path"] for entry in c011_manifest["files"]]
        c011_base = [k for k in c011_files if k.startswith("cases/base/")]
        c011_ctrl = [k for k in c011_files if k.startswith("cases/controls/")]
        c011_pois = [k for k in c011_files if k.startswith("cases/poisoned/")]
        assert (len(c011_base), len(c011_ctrl), len(c011_pois)) == (32, 8, 6)
        assert len(c011_base) + len(c011_ctrl) + len(c011_pois) == 46

        c012_files = [entry["path"] for entry in c012_manifest["files"]]
        c012_base = [k for k in c012_files if k.startswith("cases/base/")]
        c012_ctrl = [k for k in c012_files if k.startswith("cases/controls/")]
        c012_pois = [k for k in c012_files if k.startswith("cases/poisoned/")]
        assert (len(c012_base), len(c012_ctrl), len(c012_pois)) == (40, 16, 12)
        assert len(c012_base) + len(c012_ctrl) + len(c012_pois) == 68

        assert not (_C012_DIR / "governance" / "adversary_gate.py").exists()

    def test_falsification_sut_review_counts_and_reference_runner_reject_zero_case_or_mutated_records(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Negative control: mutating F4 record fails SUT census test; empty suite fails commit_reveal_c051."""
        _load_file_module(monkeypatch, "review_counts", _REVIEW_COUNTS_PATH)
        trc = _load_file_module(monkeypatch, "_w5_w2_shard_a_trc_neg", _TEST_REVIEW_COUNTS_PATH)

        lf_root = tmp_path / "pfp009_mut"
        hist_dir = lf_root / "docs" / "historical_evidence"
        hist_dir.mkdir(parents=True)
        monkeypatch.setattr(trc, "ROOT", lf_root)

        original = json.loads(_FALSIFIERS_JSON.read_text(encoding="utf-8"))

        # Mutation 1: altering step_E_payload in F4 causes test_gate_record_is_five_probes_in_four_families to fail.
        mut_step = copy.deepcopy(original)
        mut_step["falsifiers"][4]["observed"]["step_E_payload"] = []
        (hist_dir / "adversary_gate_falsifiers.json").write_text(
            json.dumps(mut_step), encoding="utf-8"
        )
        with pytest.raises(AssertionError):
            trc.test_gate_record_is_five_probes_in_four_families()

        # Mutation 2: collapsing F4's defect family breaks the 4-family census invariant.
        mut_family = copy.deepcopy(original)
        mut_family["falsifiers"][4]["defect"] = mut_family["falsifiers"][0]["defect"]
        (hist_dir / "adversary_gate_falsifiers.json").write_text(
            json.dumps(mut_family), encoding="utf-8"
        )
        with pytest.raises(AssertionError):
            trc.test_gate_record_is_five_probes_in_four_families()

        # SUT negative controls on commit_reveal_c051: zero-case label_run -> REFERENCE_SELF_INCONSISTENT,
        # bool/negative counts -> TypeError, and run_gate on 0 cases -> ReferenceRunError('EMPTY_JUDGE_SUITE').
        pkg_dir = tmp_path / "c051_empty_suite"
        (pkg_dir / "reference_solver").mkdir(parents=True)
        (pkg_dir / "reference_solver" / "solver.py").write_text("x = 1\n", encoding="utf-8")
        (pkg_dir / "judge_packet" / "cases").mkdir(parents=True)
        (pkg_dir / "judge_packet" / "hostile_mutations").mkdir(parents=True)
        script_copy = pkg_dir / "commit_reveal_c051.py"
        script_copy.write_bytes(_lf_bytes(_C051_RUNNER_PATH))

        intel_root = tmp_path / "intel_empty"
        c051 = _load_c051_runner(
            monkeypatch,
            script_copy,
            solve_fn=lambda case: case,
            check_exact_fn=lambda case, ans: (True, "ok"),
            check_indep_fn=lambda case, ans: (True, "ok"),
            default_root=intel_root,
        )
        assert c051.label_run(0, 0, 5, 5, 0) == "REFERENCE_SELF_INCONSISTENT"
        assert c051.label_run(2, 2, 0, 0, 0) == "REFERENCE_SELF_INCONSISTENT"
        with pytest.raises(TypeError, match="must be a non-negative int"):
            c051.label_run(True, 0, 1, 1, 0)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="must be a non-negative int"):
            c051.label_run(-1, 0, 1, 1, 0)

        with pytest.raises(c051.ReferenceRunError) as exc_info:
            c051.run_gate(intelligence_repo_root=intel_root)
        assert exc_info.value.code == "EMPTY_JUDGE_SUITE"
        runs_dir = intel_root / "_ic" / "darpa" / "adversary" / "runs"
        run_folders = list(runs_dir.iterdir())
        assert len(run_folders) == 1
        failure_receipt = json.loads(
            (run_folders[0] / "failure_receipt.json").read_text(encoding="utf-8")
        )
        assert failure_receipt["status"] == "RUN_FAILED"
        assert failure_receipt["error_code"] == "EMPTY_JUDGE_SUITE"


# ---------------------------------------------------------------------------
# 4. AUDIT-P009-018: Corrected gate & reference self-consistency review
# ---------------------------------------------------------------------------


def _assert_all_93_parser_vectors(evidence: Any, native: _SpecExactNativeSupport) -> None:
    """Replay all 93 pinned parser vectors (50 critique + 43 checker_receipt) against evidence.py."""
    fixture = json.loads(_PARITY_FIXTURE_PATH.read_text(encoding="utf-8"))
    vectors = fixture["vectors"]
    assert len(vectors) == 93
    critique_count = 0
    receipt_count = 0
    for row in vectors:
        if row["op"] == "critique":
            critique_count += 1
            parsed = evidence.parse_structured_critique(row["input"], native_support=native)
            assert {"ok": parsed.to_dict()} == row["expected"]
        elif row["op"] == "checker_receipt":
            receipt_count += 1
            raw = bytes.fromhex(row["raw_hex"])
            if "ok" in row["expected"]:
                rec = evidence.parse_checker_receipt(raw, native_support=native)
                assert rec.to_dict() == row["expected"]["ok"]
            else:
                with pytest.raises(ValueError) as exc_info:
                    evidence.parse_checker_receipt(raw, native_support=native)
                assert str(exc_info.value) == row["expected"]["error"]["message"]
        else:
            raise AssertionError(f"Unexpected op: {row['op']}")
    assert (critique_count, receipt_count) == (50, 43)


class TestCorrectedGateReview:
    """Verifies AUDIT-P009-018: active Python/Rust gate remediations and reference self-consistency runner."""

    def test_external_fix_commits_absent_while_active_python_and_rust_sources_match_fixes(
        self,
    ) -> None:
        """Positive test: external fix commits are absent; active Python and Rust crates implement all 5 clauses."""
        for commit_sha in (_AUDITED_COMMIT, _FIX_COMMIT_GATE, _FIX_COMMIT_COPIES):
            res = subprocess.run(
                ["git", "cat-file", "-t", commit_sha],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert res.returncode != 0

        auth_rs = (_REPO_ROOT / "code" / "rust" / "core_adversary" / "src" / "authorization.rs").read_text(
            encoding="utf-8"
        )
        assert "annihilates_coboundary" not in auth_rs
        assert "norm_bounded" not in auth_rs
        assert "OBSTRUCTION_NON_VANISHING_RECEIPT" in auth_rs
        assert "receipt_digest" in auth_rs
        assert "collect_evidence_receipts" in auth_rs

        parse_rs = (_REPO_ROOT / "code" / "rust" / "core_adversary" / "src" / "evidence_parse.rs").read_text(
            encoding="utf-8"
        )
        assert "parse_structured_critique" in parse_rs
        assert "parse_checker_receipt" in parse_rs
        assert "a MALFORMED critique must block (fail closed)" in parse_rs

        skill_rs = (_REPO_ROOT / "code" / "rust" / "core_adversary" / "src" / "skill_run.rs").read_text(
            encoding="utf-8"
        )
        assert '"REFERENCE_SELF_CONSISTENT"' in skill_rs
        assert '"REFERENCE_SELF_INCONSISTENT"' in skill_rs

    def test_active_gate_end_to_end_cochain_transport_typed_critique_receipt_digest_and_bound_checker(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Positive test: 93-vector parser parity + end-to-end Act IV/V/VI/VII authorization preconditions."""
        mods = _load_adversary_modules(monkeypatch)
        act_helpers = mods["act_helpers"]
        evidence = mods["evidence"]
        ports = mods["ports"]
        stage_domain = mods["stage_domain"]
        rop = mods["rop"]

        native = _SpecExactNativeSupport(rop.Ok, tuple(sorted(evidence.CHALLENGE_KINDS)))
        _assert_all_93_parser_vectors(evidence, native)

        # 2. Act IV preserves input cochain (1, 1, 1) on original edges.
        triangle = act_helpers.Network(nodes=(0, 1, 2), edges=((0, 1), (1, 2), (2, 0)), faces=())
        cochain = {(0, 1): Fraction(1), (1, 2): Fraction(1), (2, 0): Fraction(1)}
        open_meas = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(3),
            gamma2=Fraction(0),
            defect_count=1,
            active_obstructions=("cycle_0_1_2",),
            certificate_verified=True,
        )
        fired, lifted_net, updated_cochain, _, _ = act_helpers.execute_act4_gauge_break(
            None,
            triangle,
            cochain,
            (),
            [{"candidate_id": "c1", "sbe": {"entropy_bits": "1", "purity": "1"}}],
            open_meas,
            run_key="p009_018",
        ).unwrap()
        assert fired is True
        for edge in triangle.edges:
            assert updated_cochain[edge] == Fraction(1)
        for edge in set(lifted_net.edges) - set(triangle.edges):
            assert updated_cochain[edge] == Fraction(0)

        # 3. NullCandidateCheckerAdapter returns NOT_MEASURED and blocks AUTHORIZED; bound ACCEPTED check authorizes.
        payload = b"repair potential f=(0,0,0)"
        cand = _make_candidate(stage_domain, payload)
        null_checks = act_helpers.execute_candidate_checks(
            ports.NullCandidateCheckerAdapter(),
            "p009_018",
            "repair",
            [cand],
            {cand.candidate_id: payload},
            None,
        ).unwrap()
        assert null_checks[cand.candidate_id].verdict is evidence.CheckerVerdict.NOT_MEASURED

        zero_meas = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(0),
            gamma2=Fraction(0),
            defect_count=0,
            active_obstructions=(),
            certificate_verified=True,
        )
        st_null, _, _, auth_null, nar_null = act_helpers.execute_act7_authorization_gate(
            None,
            "p009_018_null",
            [cand],
            [],
            {},
            zero_meas,
            candidate_checks=null_checks,
            critique_verdicts={cand.candidate_id: "NON_BLOCKING"},
            fixture_seats=False,
        ).unwrap()
        assert st_null == "NOT_MEASURED"
        assert auth_null is False
        assert "CHECKER_NOT_MEASURED" in nar_null["authorization_blockers"]

        receipt_bytes = json.dumps(
            {
                "verdict": "ACCEPTED",
                "candidate_content_sha256": _prefixed_sha256(payload),
                "checker_id": "exact.checker",
                "candidate_id": cand.candidate_id,
            }
        ).encode("utf-8")
        parsed_rec = evidence.parse_checker_receipt(receipt_bytes, native_support=native)
        accepted_check = evidence.CandidateCheckV1(
            verdict=parsed_rec.verdict,
            candidate_id=cand.candidate_id,
            candidate_content_sha256=parsed_rec.candidate_content_sha256,
            checker_id=parsed_rec.checker_id,
            checker_receipt_sha256=evidence.sha256_ref(receipt_bytes),
            checker_receipt_bytes=receipt_bytes,
        )

        class _BoundCheckerPort:
            def check_candidate(self, **kwargs: Any) -> Any:
                assert kwargs["candidate_bytes"] == payload
                return rop.Ok(accepted_check)

        bound_checks = act_helpers.execute_candidate_checks(
            _BoundCheckerPort(),
            "p009_018_auth",
            "repair",
            [cand],
            {cand.candidate_id: payload},
            None,
        ).unwrap()
        st_ok, sel_ok, prop_ok, auth_ok, nar_ok = act_helpers.execute_act7_authorization_gate(
            None,
            "p009_018_auth",
            [cand],
            [],
            {},
            zero_meas,
            candidate_checks=bound_checks,
            critique_verdicts={cand.candidate_id: "NON_BLOCKING"},
            fixture_seats=False,
        ).unwrap()
        assert st_ok == "AUTHORIZED"
        assert sel_ok == cand.candidate_id
        assert auth_ok is True
        assert nar_ok["authorization_evidence"] == "CHECKER_VERDICT_AND_EXACT_ZERO_CARRIER"
        assert accepted_check.checker_receipt_sha256 in prop_ok.evidence_refs

    def test_reference_self_consistency_runner_and_skill_persistence_verdicts(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Positive test: skill_run_persistence verdicts + commit_reveal_c051 end-to-end consistent bundle."""
        mods = _load_adversary_modules(monkeypatch)
        skill_run = mods["skill_run"]
        assert "REFERENCE_SELF_CONSISTENT" in skill_run.TERMINAL_VERDICTS
        assert "REFERENCE_SELF_INCONSISTENT" in skill_run.TERMINAL_VERDICTS

        pkg_dir = tmp_path / "c051_consistent"
        (pkg_dir / "reference_solver").mkdir(parents=True)
        (pkg_dir / "reference_solver" / "solver.py").write_text("SOLVER = 1\n", encoding="utf-8")
        (pkg_dir / "judge_packet" / "cases").mkdir(parents=True)
        (pkg_dir / "judge_packet" / "hostile_mutations").mkdir(parents=True)
        (pkg_dir / "judge_packet" / "checker.py").write_text("CHECKER = 1\n", encoding="utf-8")
        for idx in (1, 2):
            (pkg_dir / "judge_packet" / "cases" / f"case_{idx}.json").write_text(
                json.dumps({"id": idx, "target": idx * 10}),
                encoding="utf-8",
            )
        (pkg_dir / "judge_packet" / "hostile_mutations" / "mut_1.json").write_text(
            json.dumps(
                {
                    "mutation_id": "mut_1",
                    "case": {"id": 1, "target": 10},
                    "corrupted_result": {"value": 999},
                }
            ),
            encoding="utf-8",
        )
        script_copy = pkg_dir / "commit_reveal_c051.py"
        script_copy.write_bytes(_lf_bytes(_C051_RUNNER_PATH))

        intel_root = tmp_path / "intel_consistent"
        c051 = _load_c051_runner(
            monkeypatch,
            script_copy,
            solve_fn=lambda case: {"value": case["target"]},
            check_exact_fn=lambda case, ans: (ans.get("value") == case["target"], "exact"),
            check_indep_fn=lambda case, ans: (ans.get("value") == case["target"], "indep"),
            default_root=intel_root,
        )
        assert c051.GATE_SCOPE == "REFERENCE_SOLVER_SELF_CHECK"
        assert c051.run_gate(intelligence_repo_root=intel_root) is True

        runs_dir = intel_root / "_ic" / "darpa" / "adversary" / "runs"
        run_dir = next(runs_dir.iterdir())
        novella_bytes = (run_dir / "novella.md").read_bytes()
        dda_bytes = (run_dir / "dda_actions.jsonl").read_bytes()
        summary_bytes = (run_dir / "summary.json").read_bytes()
        receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
        summary = json.loads(summary_bytes.decode("utf-8"))

        assert summary["verdict"] == "REFERENCE_SELF_CONSISTENT"
        assert summary["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
        assert "pre_run_commitment" not in summary
        assert receipt["verdict"] == "REFERENCE_SELF_CONSISTENT"
        assert receipt["gate_scope"] == "REFERENCE_SOLVER_SELF_CHECK"
        assert receipt["pre_run_commitment"] is False
        assert receipt["novella_sha256"] == hashlib.sha256(novella_bytes).hexdigest()
        assert receipt["dda_actions_sha256"] == hashlib.sha256(dda_bytes).hexdigest()
        assert receipt["summary_sha256"] == hashlib.sha256(summary_bytes).hexdigest()

        novella_text = novella_bytes.decode("utf-8")
        assert "REFERENCE_SOLVER_SELF_CHECK" in novella_text
        assert "100% concordance across all cases" not in novella_text
        assert "46 judge cases" not in novella_text
        dda_letters = [
            json.loads(line)["letter"]
            for line in dda_bytes.decode("utf-8").splitlines()
            if line.strip()
        ]
        assert dda_letters == ["C", "R", "D", "T"]

    def test_falsification_sut_candidate_check_binding_lift_lowering_and_corrupted_bundle_refused(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Negative control: SUT refuses unbound checks, lowering lifts, bad skill_run args, and corrupt bundles."""
        mods = _load_adversary_modules(monkeypatch)
        act_helpers = mods["act_helpers"]
        bout_service = mods["bout_service"]
        skill_run = mods["skill_run"]
        evidence = mods["evidence"]
        stage_domain = mods["stage_domain"]
        rop = mods["rop"]

        payload = b"candidate bytes"
        cand = _make_candidate(stage_domain, payload)
        receipt_bytes = b'{"verdict":"ACCEPTED"}'

        # 1. CandidateCheckV1 rejects empty receipt bytes or mismatched receipt sha256.
        with pytest.raises(ValueError, match="requires the checker receipt bytes"):
            evidence.CandidateCheckV1(
                verdict=evidence.CheckerVerdict.ACCEPTED,
                candidate_id=cand.candidate_id,
                candidate_content_sha256=_prefixed_sha256(payload),
                checker_id="checker",
                checker_receipt_sha256=evidence.sha256_ref(receipt_bytes),
                checker_receipt_bytes=b"",
            )
        with pytest.raises(ValueError, match="not the digest of the receipt bytes"):
            evidence.CandidateCheckV1(
                verdict=evidence.CheckerVerdict.ACCEPTED,
                candidate_id=cand.candidate_id,
                candidate_content_sha256=_prefixed_sha256(payload),
                checker_id="checker",
                checker_receipt_sha256="sha256:" + ("0" * 64),
                checker_receipt_bytes=receipt_bytes,
            )

        # 2. execute_candidate_checks refuses a checker verdict bound to different content bytes.
        wrong_content_check = evidence.CandidateCheckV1(
            verdict=evidence.CheckerVerdict.ACCEPTED,
            candidate_id=cand.candidate_id,
            candidate_content_sha256=_prefixed_sha256(b"other candidate bytes"),
            checker_id="checker",
            checker_receipt_sha256=evidence.sha256_ref(receipt_bytes),
            checker_receipt_bytes=receipt_bytes,
        )

        class _WrongBindingChecker:
            def check_candidate(self, **kwargs: Any) -> Any:
                del kwargs
                return rop.Ok(wrong_content_check)

        bind_err = act_helpers.execute_candidate_checks(
            _WrongBindingChecker(),
            "p009_018_mismatch",
            "repair",
            [cand],
            {cand.candidate_id: payload},
            None,
        )
        assert bind_err.is_err
        assert bind_err.error.code == "ADVERSARY_CHECKER_BINDING_MISMATCH"

        # 3. bout_service refuses any post-lift drop in Phi1 or Gamma2.
        before = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(3),
            gamma2=Fraction(1),
            defect_count=1,
            active_obstructions=("cycle",),
            certificate_verified=True,
        )
        after_gamma_drop = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(3),
            gamma2=Fraction(0),
            defect_count=1,
            active_obstructions=("cycle",),
            certificate_verified=True,
        )
        assert bout_service._lift_lowered_obstruction(before, after_gamma_drop) is True
        lower_err = bout_service._lift_replaced_cochain(before, after_gamma_drop)
        assert lower_err.is_err
        assert lower_err.error.code == "ADVERSARY_LIFT_LOWERED_OBSTRUCTION"

        # 4. skill_run_persistence refuses invalid work_status, conflicting summary work_status, or non-bytes receipt.
        native = _SpecExactNativeSupport(rop.Ok, tuple(sorted(evidence.CHALLENGE_KINDS)))
        ws_err = skill_run.persist_skill_run(
            tmp_path / "sr1",
            task_key="t1",
            objective="obj",
            verdict="REFERENCE_SELF_CONSISTENT",
            source="test",
            novella_md="# report\n",
            created_utc="2026-11-15T00:00:00Z",
            work_status="invalid_status",
            native_support=native,
        )
        assert ws_err.is_err and ws_err.error.code == "WORK_STATUS_INVALID"

        conflict_err = skill_run.persist_skill_run(
            tmp_path / "sr2",
            task_key="t1",
            objective="obj",
            verdict="REFERENCE_SELF_CONSISTENT",
            source="test",
            novella_md="# report\n",
            created_utc="2026-11-15T00:00:00Z",
            summary={"work_status": "partial"},
            work_status="completed",
            native_support=native,
        )
        assert conflict_err.is_err and conflict_err.error.code == "SUMMARY_KEY_CONFLICT"

        receipt_type_err = skill_run.persist_skill_run(
            tmp_path / "sr3",
            task_key="t1",
            objective="obj",
            verdict="PASS_TO_MASTER",
            source="test",
            novella_md="# report\n",
            created_utc="2026-11-15T00:00:00Z",
            checker_receipt_bytes="not_bytes",  # type: ignore[arg-type]
            native_support=native,
        )
        assert receipt_type_err.is_err and receipt_type_err.error.code == "CHECKER_RECEIPT_EMPTY"

        # 5. commit_reveal_c051 refuses missing 'corrupted_result' and marks solver crashes inconsistent.
        pkg_dir = tmp_path / "c051_corrupt"
        (pkg_dir / "reference_solver").mkdir(parents=True)
        (pkg_dir / "reference_solver" / "solver.py").write_text("S = 1\n", encoding="utf-8")
        (pkg_dir / "judge_packet" / "cases").mkdir(parents=True)
        (pkg_dir / "judge_packet" / "hostile_mutations").mkdir(parents=True)
        (pkg_dir / "judge_packet" / "cases" / "c1.json").write_text(
            json.dumps({"id": 1}), encoding="utf-8"
        )
        (pkg_dir / "judge_packet" / "hostile_mutations" / "m1.json").write_text(
            json.dumps({"mutation_id": "m1", "case": {"id": 1}}),
            encoding="utf-8",
        )
        script_copy = pkg_dir / "commit_reveal_c051.py"
        script_copy.write_bytes(_lf_bytes(_C051_RUNNER_PATH))

        intel_root = tmp_path / "intel_corrupt"
        c051 = _load_c051_runner(
            monkeypatch,
            script_copy,
            solve_fn=lambda case: case,
            check_exact_fn=lambda case, ans: (True, "ok"),
            check_indep_fn=lambda case, ans: (True, "ok"),
            default_root=intel_root,
        )
        with pytest.raises(c051.ReferenceRunError) as mut_exc:
            c051.mutation_answer({"mutation_id": "m1"})
        assert mut_exc.value.code == "MUTATION_PAYLOAD_MISSING"

        with pytest.raises(c051.ReferenceRunError) as gate_exc:
            c051.run_gate(intelligence_repo_root=intel_root)
        assert gate_exc.value.code == "MUTATION_PAYLOAD_MISSING"


# ---------------------------------------------------------------------------
# 5. Shard A review JSON pins, pure-LF, and Claim Hygiene self-audit
# ---------------------------------------------------------------------------


class TestShardAReviewAndHygieneGates:
    """Self-audit of Shard A's 6 owned files for inventory pins, LF line endings, and Claim Hygiene."""

    _OWNED_PATHS: tuple[Path, ...] = (
        *_DERIVATION_PATHS,
        _REVIEW_JSON_PATH,
        Path(__file__).resolve(),
    )

    _HYGIENE_RE = re.compile(
        r"\b("
        + "|".join(
            [
                "pr" + "ove",
                "pr" + "oves",
                "pr" + "oved",
                "pr" + "oven",
                "pr" + "oving",
                "guar" + r"antee\w*",
                "mathe" + r"matically\s+verifies",
                "funda" + "mentally",
                "tr" + r"ue\s+intelligence",
                "impos" + "sible",
                "univ" + r"ersal\w*",
                "flaw" + r"less\w*",
                "perf" + "ectly",
                "cle" + "arly",
                "obvi" + "ously",
                "sim" + "ply",
                "mer" + "ely",
                "weap" + "onized",
            ]
        )
        + r")\b",
        re.IGNORECASE,
    )

    _INTERNAL_NAMES_RE = re.compile(
        r"\b("
        + "|".join(
            [
                "Ome" + "ga",
                "ome" + r"ga_\w+",
                "Anom" + "alon",
                "Wol" + "and",
                "OE" + "EIS",
            ]
        )
        + r")\b"
    )

    def test_review_json_inventory_pins_evidence_and_schema(self) -> None:
        """Verify additional_w5_w2_shard_a.json matches dag/file_inventory.json and source_commit Git blobs."""
        review = json.loads(_REVIEW_JSON_PATH.read_text(encoding="utf-8"))
        assert review["schema_version"] == "1.0"
        assert review["status"] == "scope_complete"
        assert review["source_commit"] == "78bc23b35"

        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", "78bc23b35", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert ancestry.returncode == 0

        inventory = {
            entry["path"]: entry["sha256"]
            for entry in json.loads(
                (_REPO_ROOT / "dag" / "file_inventory.json").read_text(encoding="utf-8")
            )["files"]
        }

        reviewed_paths: set[str] = set()
        for entry in review["file_reviews"]:
            rel_path = entry["path"]
            assert not rel_path.startswith("dag/derivations/audit_")
            assert not rel_path.startswith("tests/test_w5_")
            assert rel_path in inventory
            assert entry["sha256"] == inventory[rel_path]
            assert entry["full_source_read"] is True

            disk_lines = len((_REPO_ROOT / rel_path).read_bytes().decode("utf-8").splitlines())
            assert entry["reviewed_lines"] == [[1, disk_lines]]

            source_bytes = subprocess.check_output(
                ["git", "show", f"{review['source_commit']}:{rel_path}"],
                cwd=_REPO_ROOT,
            )
            source_sha = hashlib.sha256(source_bytes).hexdigest()
            if source_sha == entry["sha256"]:
                assert "git_blob_sha256" not in entry
                assert "pin_note" not in entry
            else:
                assert entry["git_blob_sha256"] == source_sha
                crlf_sha = hashlib.sha256(source_bytes.replace(b"\n", b"\r\n")).hexdigest()
                assert crlf_sha == entry["sha256"]
                assert "pin_note" not in entry
            reviewed_paths.add(rel_path)

        claim_ids = [claim["id"] for claim in review["claims"]]
        assert claim_ids == [
            "AUDIT-P009-015",
            "AUDIT-P009-016",
            "AUDIT-P009-017",
            "AUDIT-P009-018",
        ]
        bare_id_re = re.compile(r"^[A-Z0-9-]+$")
        for claim in review["claims"]:
            assert claim["dependencies"]
            for dep in claim["dependencies"]:
                assert len(dep) > 25 and not bare_id_re.match(dep)
            assert claim["evidence"]
            for ev_path in claim["evidence"]:
                assert ev_path in inventory
                assert ev_path in reviewed_paths

    def test_owned_files_pure_lf_and_claim_hygiene_clean(self) -> None:
        """Verify pure LF endings, zero Claim Hygiene violations, and zero unscrubbed internal names."""
        for path in self._OWNED_PATHS:
            raw = path.read_bytes()
            assert b"\r" not in raw, f"CR byte found in {path}"
            assert raw.endswith(b"\n"), f"Missing trailing LF in {path}"
            text = raw.decode("utf-8")
            hygiene_hits = self._HYGIENE_RE.findall(text)
            assert hygiene_hits == [], f"Claim Hygiene hits in {path.name}: {hygiene_hits}"
            name_hits = self._INTERNAL_NAMES_RE.findall(text)
            assert name_hits == [], f"Unscrubbed internal names in {path.name}: {name_hits}"

        for deriv_path in _DERIVATION_PATHS:
            deriv_text = deriv_path.read_text(encoding="utf-8")
            assert "AuthorityEffect: None." in deriv_text
            assert "- Review verdict: `partial` (`relation: narrows`)" in deriv_text
            for heading in (
                "## 1. Claim Statement",
                "## 2. Context & Hypotheses",
                "## 3. Derivation / Evidence",
                "## 4. Limits and Non-Claims",
                "## 5. Claim Hygiene Summary",
                "## 6. Cross-References & Provenance",
            ):
                assert heading in deriv_text, f"Missing {heading} in {deriv_path.name}"

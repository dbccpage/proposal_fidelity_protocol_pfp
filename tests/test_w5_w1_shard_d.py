"""Verification suite for Window 5 Wave 1 Shard D (Paper 009 Part 2).

AuthorityEffect: None.

Targets four audit derivations in Paper 009:
1. AUDIT-P009-007 (ATL-P009-007): Self-critique fails the unequal-hash
   independence predicate in Level15AuthorityCalculus.lean (zero-axiom kernel
   reflexivity rfl, verified via source read and clean out-of-tree lake build),
   without establishing statistical independence.
2. AUDIT-P009-009 (ATL-P009-009): TerminalizerPolicy.lean is excluded from
   Paper 009 and top-level Lake targets, and convergent tracked audit records
   attest that its header states its declarations were not typechecked / do not
   elaborate while the raw unbuilt blob remains outside this split repository.
3. AUDIT-P009-013 (ATL-P009-013): Retained replay receipt
   demo2_r7_adversarial_debate_receipt.json matches its pinned digest, binds to
   demo2_r7_adversarial_debate_1790210039.jsonl, refuses all 10 recorded
   proposals including all 4 OPEN_SIGN_OBSTRUCTION claims, and omits any
   checker revision pin.
4. AUDIT-P009-014 (ATL-P009-014): Gate falsifier F1 triangle cochain (1, 1, 1)
   has coboundary-invariant cycle sum 3; retained adversary_gate_falsifiers.json
   and replay_adversary_gate_falsifiers.py document 30609de2 authorization via
   lifted cochain zeroing, whereas current ops/adversary modules transport
   (1, 1, 1) intact, refuse lowering lifts, and block authorization.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
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
_PFP001_RESULTS = (
    _REPO_ROOT
    / "atlas"
    / "archive"
    / "pfp"
    / "001_pfp_discrete_cochain_retraction_and_toy_involutions"
    / "results"
)

_CENSUS_TOOL_PATH = _PFP009_ROOT / "tools" / "replay_lean_axiom_census.py"
_REVIEW_COUNTS_PATH = _PFP009_ROOT / "code" / "review_counts.py"
_TRIANGLE_CYCLE_SUM_PATH = _PFP009_ROOT / "code" / "triangle_cycle_sum.py"
_RECORDED_BOUT_TEST_PATH = _PFP009_ROOT / "code" / "tests" / "test_recorded_bout_counts.py"
_REPLAY_FALSIFIERS_PATH = _REPO_ROOT / "atlas" / "archive" / "pfp" / "tools" / "replay_adversary_gate_falsifiers.py"

_CENSUS_MOD_NAME = "_w5_w1_shard_d_lean_census"
_REVIEW_COUNTS_MOD_NAME = "review_counts"
_TRIANGLE_MOD_NAME = "triangle_cycle_sum"
_RECORDED_BOUT_MOD_NAME = "_w5_w1_shard_d_recorded_bout"

_CACHED_ARCHIVE_MODULES: dict[str, Any] = {}


def _load_archive_module(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    file_path: Path,
) -> Any:
    """Load an archived Python module via spec_from_file_location inside pytest scope."""
    if module_name in _CACHED_ARCHIVE_MODULES:
        mod = _CACHED_ARCHIVE_MODULES[module_name]
        monkeypatch.setitem(sys.modules, module_name, mod)
        return mod

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to create module spec for {file_path}")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    _CACHED_ARCHIVE_MODULES[module_name] = module
    return module


@pytest.fixture(autouse=True)
def _inject_isolated_archive_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bind Paper 009 archived modules per test with zero bytecode writes or import-time mutation."""
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    _load_archive_module(monkeypatch, _CENSUS_MOD_NAME, _CENSUS_TOOL_PATH)
    _load_archive_module(monkeypatch, _REVIEW_COUNTS_MOD_NAME, _REVIEW_COUNTS_PATH)
    _load_archive_module(monkeypatch, _TRIANGLE_MOD_NAME, _TRIANGLE_CYCLE_SUM_PATH)
    _load_archive_module(monkeypatch, _RECORDED_BOUT_MOD_NAME, _RECORDED_BOUT_TEST_PATH)


def _census_mod() -> Any:
    return sys.modules[_CENSUS_MOD_NAME]


def _review_counts_mod() -> Any:
    return sys.modules[_REVIEW_COUNTS_MOD_NAME]


def _triangle_mod() -> Any:
    return sys.modules[_TRIANGLE_MOD_NAME]


def _recorded_bout_mod() -> Any:
    return sys.modules[_RECORDED_BOUT_MOD_NAME]


def _load_adversary_gate_modules(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> dict[str, Any]:
    """Import in-repo ops/adversary modules inside test scope and pop all new sys.modules on teardown."""
    before = set(sys.modules)

    def _cleanup_imported_modules() -> None:
        for mod_key in set(sys.modules) - before:
            sys.modules.pop(mod_key, None)

    request.addfinalizer(_cleanup_imported_modules)
    monkeypatch.syspath_prepend(str(_REPO_ROOT / "ops"))
    return {
        "act_helpers": importlib.import_module("adversary.use_cases.act_helpers"),
        "bout_service": importlib.import_module("adversary.use_cases.bout_service"),
        "ports": importlib.import_module("adversary.domain.ports"),
        "evidence": importlib.import_module("adversary.domain.evidence"),
        "stage_domain": importlib.import_module("adversary.stage.domain"),
    }


def _lf_bytes(path: Path) -> bytes:
    """Return LF-normalized bytes of a file."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _lf_sha256(path: Path) -> str:
    """Compute SHA-256 over LF-normalized file bytes."""
    return hashlib.sha256(_lf_bytes(path)).hexdigest()


def _git_blob_sha1(lf_content: bytes) -> str:
    """Compute standard Git blob SHA-1 over LF-normalized content."""
    header = f"blob {len(lf_content)}\0".encode("ascii")
    return hashlib.sha1(header + lf_content).hexdigest()  # noqa: S324


def _lean_env() -> dict[str, str]:
    """Build subprocess environment with $HOME/.elan/bin prepended to PATH."""
    env = dict(os.environ)
    elan_bin = str(Path.home() / ".elan" / "bin")
    current_path = env.get("PATH", "")
    env["PATH"] = f"{elan_bin}:{current_path}" if current_path else elan_bin
    return env


@pytest.fixture(scope="module")
def _isolated_paper009_lean_build(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Compile Paper 009 Lean package once in an isolated tmp directory outside atlas/archive."""
    build_root = tmp_path_factory.mktemp("pfp009_shard_d_lean")
    shutil.copytree(_PFP009_ROOT / "lean4", build_root / "lean4")
    shutil.copytree(_PFP009_ROOT / "tools", build_root / "tools")
    res = subprocess.run(
        ["lake", "build"],
        cwd=build_root / "lean4",
        env=_lean_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Out-of-tree lake build failed:\n{res.stdout}\n{res.stderr}")
    return build_root


def _validate_retained_replay_receipt(
    receipt: dict[str, Any],
    trace_rows: list[dict[str, Any]],
    expected_trace_sha256: str,
) -> tuple[Fraction, Counter[str]]:
    """Verify trace digest binding, 10-trial bijection, and 100% refusal recount."""
    if receipt.get("source_trace_sha256") != expected_trace_sha256:
        raise ValueError("Receipt source_trace_sha256 does not match trace digest")
    trials = receipt.get("trials")
    if not isinstance(trials, list) or len(trials) != 10 or len(trace_rows) != 10:
        raise ValueError("Expected 10 trials and 10 trace rows")

    trace_by_cond = {(row["lattice_key"], row["u_val"]): row for row in trace_rows}
    trial_by_cond = {(t["lattice"], t["U_over_t"]): t for t in trials}
    if set(trace_by_cond) != set(trial_by_cond) or len(trial_by_cond) != 10:
        raise ValueError("Trial conditions do not form a 10-point bijection with trace")

    refused_count = 0
    statuses: Counter[str] = Counter()
    for cond, trial in trial_by_cond.items():
        admitted = trial["current_replay_admitted"]
        if type(admitted) is not bool:
            raise TypeError("current_replay_admitted must be an exact bool")
        status = trial["current_replay_status"]
        if admitted is True or not isinstance(status, str) or not status.startswith("Refused_"):
            raise ValueError(f"Condition {cond} was not refused in replay: {trial}")
        if trial["proposer_move"] != trace_by_cond[cond]["proposer_move"]["move_type"]:
            raise ValueError(f"Move mismatch on {cond}")
        if trial["proposer_move"] == "OPEN_SIGN_OBSTRUCTION" and status != "Refused_UnverifiedObstruction":
            raise ValueError(f"Obstruction claim {cond} missing Refused_UnverifiedObstruction")
        refused_count += 1
        statuses[status] += 1

    return Fraction(refused_count, len(trials)), statuses


def _detect_unbuilt_or_warned_lean_roots(
    lean_dir: Path,
    declared_roots: list[str],
) -> list[str]:
    """Return violations for missing root files, Mathlib imports, or non-elaborating headers."""
    issues: list[str] = []
    warning_re = re.compile(r"not\s+typechecked|does\s+not\s+elaborate", re.IGNORECASE)
    for root in declared_roots:
        lean_file = lean_dir / f"{root}.lean"
        if not lean_file.is_file():
            issues.append(f"missing:{root}")
            continue
        text = lean_file.read_text(encoding="utf-8")
        if re.search(r"^\s*import\s+Mathlib\b", text, re.MULTILINE):
            issues.append(f"mathlib:{root}")
        header = "\n".join(text.splitlines()[:25])
        if warning_re.search(header):
            issues.append(f"header_warning:{root}")
    return issues


# ---------------------------------------------------------------------------
# 1. AUDIT-P009-007: Self-critique fails the independence predicate
# ---------------------------------------------------------------------------


class TestSelfCritiqueFailsIndependencePredicate:
    """Verifies AUDIT-P009-007: unequal-hash independence predicate and fresh Lean build."""

    def test_level15_source_declares_unequal_hash_predicate_and_rfl_theorem(self) -> None:
        """Positive test: Level15AuthorityCalculus defines != on paramHash and negates (gen, gen)."""
        lean_path = _PFP009_ROOT / "lean4" / "Level15AuthorityCalculus.lean"
        source = lean_path.read_text(encoding="utf-8")

        assert "namespace MSSN.Level15" in source
        assert re.search(
            r"structure\s+AgentState\s+where\s+paramHash\s*:\s*Nat",
            source,
        )
        assert re.search(
            r"def\s+isIndependentVerifier\s*\(gen\s*:\s*AgentState\)\s*\(ver\s*:\s*AgentState\)\s*:\s*Prop\s*:=\s*"
            r"gen\.paramHash\s*≠\s*ver\.paramHash",
            source,
        )
        assert re.search(
            r"theorem\s+theorem2_self_critique_non_verification\s*\(gen\s*:\s*AgentState\)\s*:\s*"
            r"¬\s*isIndependentVerifier\s+gen\s+gen\s*:=\s*by\s+intro\s+h\s+exact\s+h\s+rfl",
            source,
        )
        assert "#print axioms theorem2_self_critique_non_verification" in source

    def test_census_and_out_of_tree_lake_build_confirm_zero_axioms(
        self,
        _isolated_paper009_lean_build: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Positive test: isolated lake build + Census.lean:36 + replay_census confirm zero axioms."""
        census_mod = _census_mod()
        assert census_mod.check_census(_PFP009_ROOT) is None

        census_lines = (_PFP009_ROOT / "lean4" / "Census.lean").read_text(encoding="utf-8").splitlines()
        assert (
            census_lines[35].strip()
            == "#print axioms MSSN.Level15.theorem2_self_critique_non_verification"
        )

        declarations = census_mod.parse_report(_PFP009_ROOT)
        assert len(declarations) == 32
        by_name = {d.name: d.axioms for d in declarations}
        target_name = "MSSN.Level15.theorem2_self_critique_non_verification"
        assert target_name in by_name
        assert by_name[target_name] == frozenset()

        res = subprocess.run(
            ["lake", "env", "lean", "Census.lean"],
            cwd=_isolated_paper009_lean_build / "lean4",
            env=_lean_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0, res.stderr
        assert f"'{target_name}' does not depend on any axioms" in res.stdout

        monkeypatch.setenv("PATH", _lean_env()["PATH"])
        assert census_mod.replay_census(_isolated_paper009_lean_build) is None
        assert not (_PFP009_ROOT / "lean4" / ".lake").exists()

    def test_falsification_equal_hash_mutant_rejected_by_lean_kernel(
        self,
        _isolated_paper009_lean_build: Path,
        tmp_path: Path,
    ) -> None:
        """Negative control: mutating != to = causes Lean kernel to reject the rfl self-critique proof."""
        good_probe = tmp_path / "GoodProbe.lean"
        good_probe.write_text(
            "import Level15AuthorityCalculus\n"
            "#check (MSSN.Level15.theorem2_self_critique_non_verification :\n"
            "  ∀ g : MSSN.Level15.AgentState, ¬ MSSN.Level15.isIndependentVerifier g g)\n",
            encoding="utf-8",
        )
        good_res = subprocess.run(
            ["lake", "env", "lean", str(good_probe)],
            cwd=_isolated_paper009_lean_build / "lean4",
            env=_lean_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert good_res.returncode == 0, good_res.stderr

        bad_probe = tmp_path / "BadMutantProbe.lean"
        bad_probe.write_text(
            "import Level15AuthorityCalculus\n"
            "def isIndependentVerifierBad (gen ver : MSSN.Level15.AgentState) : Prop :=\n"
            "  gen.paramHash = ver.paramHash\n"
            "theorem bad_self_critique (gen : MSSN.Level15.AgentState) :\n"
            "    ¬ isIndependentVerifierBad gen gen := by\n"
            "  intro h\n"
            "  exact h rfl\n",
            encoding="utf-8",
        )
        bad_res = subprocess.run(
            ["lake", "env", "lean", str(bad_probe)],
            cwd=_isolated_paper009_lean_build / "lean4",
            env=_lean_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert bad_res.returncode != 0

    def test_falsification_distinct_hashes_admit_identical_failure_maps(self) -> None:
        """Negative control: unequal paramHash satisfies predicate despite 100% correlated errors."""

        def is_independent_verifier(gen_hash: int, ver_hash: int) -> bool:
            return gen_hash != ver_hash

        assert is_independent_verifier(7, 7) is False
        assert is_independent_verifier(7, 8) is True

        inputs = (0, 1, 2, 3)
        # Both agents fail on odd inputs identically (agreement rate 4/4 == 1).
        gen_failures = tuple(x % 2 == 1 for x in inputs)
        ver_failures = tuple(x % 2 == 1 for x in inputs)
        co_failure_rate = Fraction(
            sum(1 for g, v in zip(gen_failures, ver_failures, strict=True) if g == v),
            len(inputs),
        )
        assert co_failure_rate == Fraction(1, 1)


# ---------------------------------------------------------------------------
# 2. AUDIT-P009-009: Header warning check on TerminalizerPolicy.lean
# ---------------------------------------------------------------------------


class TestTerminalizerPolicyHeaderCustody:
    """Verifies AUDIT-P009-009: exclusion of TerminalizerPolicy.lean and convergent attestations."""

    PAPER009_ROOTS = [
        "SLevel",
        "RuntimeLimits",
        "TriggerNotLicense",
        "Level15AuthorityCalculus",
    ]

    def test_terminalizer_policy_excluded_from_paper009_and_repo_lake_targets(self) -> None:
        """Positive test: TerminalizerPolicy.lean is absent from Paper 009, lean4/, and git tree."""
        census_mod = _census_mod()
        assert census_mod.import_roots(_PFP009_ROOT) == self.PAPER009_ROOTS
        assert not (_PFP009_ROOT / "lean4" / "TerminalizerPolicy.lean").exists()
        assert not (_REPO_ROOT / "lean4" / "TerminalizerPolicy.lean").exists()

        top_lakefile = (_REPO_ROOT / "lean4" / "lakefile.lean").read_text(encoding="utf-8")
        assert "TerminalizerPolicy" not in top_lakefile
        assert "Mathlib" not in top_lakefile

        tracked = subprocess.check_output(
            ["git", "ls-files", "*TerminalizerPolicy*"],
            cwd=_REPO_ROOT,
            text=True,
        ).strip()
        assert tracked == ""

    def test_convergent_ledgers_attest_non_typechecked_header_and_mathlib_exclusion(self) -> None:
        """Positive test: Paper 009, curriculum proof ledger, and lean4/README.md separate attestations."""
        paper_lines = (_PFP009_ROOT / "paper.md").read_text(encoding="utf-8").splitlines()
        claim_lines = (_PFP009_ROOT / "paper_claim_ledger.md").read_text(encoding="utf-8").splitlines()
        supplement = (_PFP009_ROOT / "docs" / "completion_supplement.md").read_text(encoding="utf-8")
        supplement_lines = supplement.splitlines()
        v01_review = json.loads(
            (_PFP009_ROOT / "docs" / "v01_review_2026_10_02.json").read_text(encoding="utf-8")
        )
        curriculum_lines = (
            _REPO_ROOT / "education" / "004_oepfp" / "levels" / "meta_03_symbol_game_proof_ledger.md"
        ).read_text(encoding="utf-8").splitlines()
        lean_readme_lines = (_REPO_ROOT / "lean4" / "README.md").read_text(encoding="utf-8").splitlines()

        assert "52cb5457f6c485ba548cfd292f6012a941ed22cf" in paper_lines[107]
        assert "imports a Mathlib module" in paper_lines[107]
        assert "not typechecked against the named package configuration" in paper_lines[107]
        assert "It is not copied into this package." in paper_lines[107]

        assert "G009-09" in claim_lines[19]
        assert "not typechecked" in claim_lines[19]
        assert "not copied into this package" in claim_lines[19]
        assert "No compiled theorem claimed" in claim_lines[19]

        assert supplement_lines[44].strip() == "## Formal-source boundaries"
        assert "TerminalizerPolicy.lean" in supplement
        assert "not typechecked against the named package configuration" in supplement
        assert "not\n  copied into this package" in supplement
        assert "Lean 4.34.0" in supplement_lines[57]

        assert set(v01_review["source_identity_inspection"].keys()) == {
            "lean4/Level15AuthorityCalculus.lean",
            "lean4/RuntimeLimits.lean",
            "lean4/SLevel.lean",
            "lean4/TriggerNotLicense.lean",
        }
        assert "lean4/TerminalizerPolicy.lean" not in v01_review["protected_artifacts_unchanged"]

        assert "# not found at source pin c419cc6beb (2026-10-20)" in curriculum_lines[13]
        assert "state in their own headers that they do not elaborate" in curriculum_lines[35]
        assert "TerminalizerPolicy" in curriculum_lines[35]
        assert (
            curriculum_lines[46].strip()
            == "| L043_08 Terminalizer | `lean4/TerminalizerPolicy.lean` | header: does not elaborate |"
        )
        assert (
            "`FiniteConsequences`, `LpWeakDuality` and `TerminalizerPolicy` have no grade, "
            "because their builds did not complete." in lean_readme_lines[29]
        )

    def test_bundled_paper009_lean_modules_carry_no_untypechecked_warnings(self) -> None:
        """Positive contrast: all 4 bundled Paper 009 Lean modules exist and pass root hygiene."""
        issues = _detect_unbuilt_or_warned_lean_roots(
            _PFP009_ROOT / "lean4",
            self.PAPER009_ROOTS,
        )
        assert issues == []

    def test_falsification_detector_flags_unbuilt_root_or_header_warning(
        self,
        tmp_path: Path,
    ) -> None:
        """Negative control: detector catches missing TerminalizerPolicy or non-typechecked header."""
        shutil.copytree(_PFP009_ROOT / "lean4", tmp_path / "lean4")
        missing_issues = _detect_unbuilt_or_warned_lean_roots(
            tmp_path / "lean4",
            [*self.PAPER009_ROOTS, "TerminalizerPolicy"],
        )
        assert missing_issues == ["missing:TerminalizerPolicy"]

        (tmp_path / "lean4" / "TerminalizerPolicy.lean").write_text(
            "/- WARNING: declarations in this file were not typechecked\n"
            "   against the named package configuration and do not elaborate. -/\n"
            "import Mathlib.Data.Real.Basic\n",
            encoding="utf-8",
        )
        warned_issues = _detect_unbuilt_or_warned_lean_roots(
            tmp_path / "lean4",
            [*self.PAPER009_ROOTS, "TerminalizerPolicy"],
        )
        assert warned_issues == [
            "mathlib:TerminalizerPolicy",
            "header_warning:TerminalizerPolicy",
        ]

    def test_falsification_census_rejects_terminalizer_root_and_lean_rejects_mathlib(
        self,
        _isolated_paper009_lean_build: Path,
        tmp_path: Path,
    ) -> None:
        """SUT negative controls: adding TerminalizerPolicy breaks check_census and Mathlib fails lake env lean."""
        census_mod = _census_mod()
        tmp_copy = tmp_path / "paper009_copy"
        shutil.copytree(_PFP009_ROOT / "lean4", tmp_copy / "lean4")
        assert census_mod.check_census(tmp_copy) is None

        lakefile = tmp_copy / "lean4" / "lakefile.lean"
        lakefile_text = lakefile.read_text(encoding="utf-8")
        mutated_lakefile = lakefile_text.replace(
            "`Level15AuthorityCalculus]",
            "`Level15AuthorityCalculus, `TerminalizerPolicy]",
        )
        assert mutated_lakefile != lakefile_text
        lakefile.write_text(mutated_lakefile, encoding="utf-8")
        with pytest.raises(ValueError, match="stale generated census"):
            census_mod.check_census(tmp_copy)

        mathlib_probe = tmp_path / "TerminalizerMathlibProbe.lean"
        mathlib_probe.write_text("import Mathlib.Data.Real.Basic\n", encoding="utf-8")
        mathlib_res = subprocess.run(
            ["lake", "env", "lean", str(mathlib_probe)],
            cwd=_isolated_paper009_lean_build / "lean4",
            env=_lean_env(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert mathlib_res.returncode != 0


# ---------------------------------------------------------------------------
# 3. AUDIT-P009-013: Retained replay recount
# ---------------------------------------------------------------------------


class TestRetainedReplayRecount:
    """Verifies AUDIT-P009-013: custody hashes and 10/10 refusal recount in replay receipt."""

    EXPECTED_TRACE_LF_SHA256 = "329e29228b3278dc9172bc318d82c38876107175a64c834c386e60d98bd509d7"
    EXPECTED_RECEIPT_LF_SHA256 = "41256258279dd25c8af2323c6c5cc115293104bc09cfe3958c793d80e5cb4856"
    EXPECTED_TRACE_BLOB_SHA1 = "8ecf963d857bf1c87fdf89e86da4f8c9b980b410"
    EXPECTED_RECEIPT_BLOB_SHA1 = "baddc37f788f10c589a7b85080ff424d094120a3"

    def test_receipt_and_trace_digests_match_provenance_and_paper001_copies(self) -> None:
        """Positive test: trace and receipt match provenance.json and Paper 001 byte-for-byte."""
        hist_dir = _PFP009_ROOT / "docs" / "historical_evidence"
        trace_path = hist_dir / "demo2_r7_adversarial_debate_1790210039.jsonl"
        receipt_path = hist_dir / "demo2_r7_adversarial_debate_receipt.json"
        prov = json.loads((hist_dir / "provenance.json").read_text(encoding="utf-8"))

        records_by_file = {r["file"]: r for r in prov["records"]}
        assert _lf_sha256(trace_path) == self.EXPECTED_TRACE_LF_SHA256
        assert _lf_sha256(receipt_path) == self.EXPECTED_RECEIPT_LF_SHA256
        assert _git_blob_sha1(_lf_bytes(trace_path)) == self.EXPECTED_TRACE_BLOB_SHA1
        assert _git_blob_sha1(_lf_bytes(receipt_path)) == self.EXPECTED_RECEIPT_BLOB_SHA1

        assert records_by_file[trace_path.name]["sha256"] == self.EXPECTED_TRACE_LF_SHA256
        assert records_by_file[trace_path.name]["git_blob_sha1"] == self.EXPECTED_TRACE_BLOB_SHA1
        assert records_by_file[receipt_path.name]["sha256"] == self.EXPECTED_RECEIPT_LF_SHA256
        assert records_by_file[receipt_path.name]["git_blob_sha1"] == self.EXPECTED_RECEIPT_BLOB_SHA1

        assert _lf_bytes(trace_path) == _lf_bytes(_PFP001_RESULTS / trace_path.name)
        assert _lf_bytes(receipt_path) == _lf_bytes(_PFP001_RESULTS / receipt_path.name)

    def test_all_ten_proposals_and_four_obstruction_claims_refused_in_replay(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Positive test: stored replay refuses all 10 proposals (4 + 5 + 1 status partition)."""
        hist_dir = _PFP009_ROOT / "docs" / "historical_evidence"
        trace_path = hist_dir / "demo2_r7_adversarial_debate_1790210039.jsonl"
        receipt_path = hist_dir / "demo2_r7_adversarial_debate_receipt.json"

        trace_rows = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        refusal_rate, status_counts = _validate_retained_replay_receipt(
            receipt,
            trace_rows,
            self.EXPECTED_TRACE_LF_SHA256,
        )
        assert refusal_rate == Fraction(10, 10) == Fraction(1, 1)
        assert dict(status_counts) == {
            "Refused_UnverifiedObstruction": 4,
            "Refused_UnverifiedInvolution_InvalidWitness": 5,
            "Refused_AM_FSP_2_NullXi": 1,
        }
        assert dict(status_counts) == receipt["current_replay_statuses"]

        # Point test_recorded_bout_counts at LF-normalized copies in tmp_path so its raw-byte
        # SHA-256 assertions execute identically without touching atlas/archive/.
        lf_trace = tmp_path / trace_path.name
        lf_receipt = tmp_path / receipt_path.name
        lf_trace.write_bytes(_lf_bytes(trace_path))
        lf_receipt.write_bytes(_lf_bytes(receipt_path))

        recorded_bout = _recorded_bout_mod()
        monkeypatch.setattr(recorded_bout, "TRACE", lf_trace)
        monkeypatch.setattr(recorded_bout, "RECEIPT", lf_receipt)
        recorded_bout.test_retained_replay_refuses_all_ten()

    def test_replay_verdicts_shift_confusion_summary_and_leave_checker_unpinned(self) -> None:
        """Positive test: replay verdicts yield 8 TP / 2 FN in Counts and pin no checker SHA."""
        rc = _review_counts_mod()
        hist_dir = _PFP009_ROOT / "docs" / "historical_evidence"
        trace_rows = [
            json.loads(line)
            for line in (hist_dir / "demo2_r7_adversarial_debate_1790210039.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        receipt = json.loads(
            (hist_dir / "demo2_r7_adversarial_debate_receipt.json").read_text(encoding="utf-8")
        )

        orig_counts = rc.recount(trace_rows)
        assert orig_counts == rc.Counts(
            true_positive=6,
            false_negative=0,
            false_positive=2,
            true_negative=2,
        )
        assert orig_counts.rates()["challenge_among_refused"] == Fraction(1, 1)

        replay_cells = Counter(
            (not t["current_replay_admitted"], t["adversary_verdict"]) for t in receipt["trials"]
        )
        replay_counts = rc.Counts(
            true_positive=replay_cells[(True, "CHALLENGE")],
            false_negative=replay_cells[(True, "CONCUR")],
            false_positive=replay_cells[(False, "CHALLENGE")],
            true_negative=replay_cells[(False, "CONCUR")],
        )
        assert replay_counts == rc.Counts(
            true_positive=8,
            false_negative=2,
            false_positive=0,
            true_negative=0,
        )
        assert replay_counts.rates()["challenge_among_refused"] == Fraction(4, 5)
        assert replay_counts.rates()["challenge_among_not_refused"] is None

        pin_keys = {
            k
            for k in receipt
            if any(tok in k.lower() for tok in ("commit", "version", "checker_sha", "binary"))
        }
        assert pin_keys == set()

    def test_falsification_sut_recount_rejects_unexpected_status_or_admitted_flip(
        self,
        tmp_path: Path,
    ) -> None:
        """SUT negative control: review_counts.recount rejects unexpected replay status or flipped admission."""
        rc = _review_counts_mod()
        hist_dir = _PFP009_ROOT / "docs" / "historical_evidence"
        trace_path = hist_dir / "demo2_r7_adversarial_debate_1790210039.jsonl"
        receipt_path = hist_dir / "demo2_r7_adversarial_debate_receipt.json"
        trace_rows = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        bad_status_trace_file = tmp_path / "bad_status_trace.jsonl"
        bad_status_rows = copy.deepcopy(trace_rows)
        bad_status_rows[0]["proposer_status"] = "Refused_UnverifiedObstruction"
        bad_status_trace_file.write_text(
            "\n".join(json.dumps(r) for r in bad_status_rows) + "\n",
            encoding="utf-8",
        )
        reloaded_bad_status = [
            json.loads(line)
            for line in bad_status_trace_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        with pytest.raises(ValueError, match="unknown status or label/status disagreement"):
            rc.recount(reloaded_bad_status)

        bad_admitted_receipt_file = tmp_path / "bad_admitted_receipt.json"
        bad_admitted = copy.deepcopy(receipt)
        refused_trial_idx = next(
            i
            for i, t in enumerate(bad_admitted["trials"])
            if t["proposer_move"] == "VERIFY_SIGN_FREE"
        )
        bad_admitted["trials"][refused_trial_idx]["current_replay_admitted"] = True
        bad_admitted_receipt_file.write_text(json.dumps(bad_admitted), encoding="utf-8")
        reloaded_bad_admitted = json.loads(bad_admitted_receipt_file.read_text(encoding="utf-8"))
        admitted_by_cond = {
            (t["lattice"], t["U_over_t"]): t["current_replay_admitted"]
            for t in reloaded_bad_admitted["trials"]
        }
        projected_rows = copy.deepcopy(trace_rows)
        for row in projected_rows:
            cond = (row["lattice_key"], row["u_val"])
            row["proposer_hallucination"] = not admitted_by_cond[cond]
        with pytest.raises(ValueError, match="unknown status or label/status disagreement"):
            rc.recount(projected_rows)

    def test_falsification_admitted_flip_or_trace_digest_mismatch_rejected(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Negative control: mutating trial admission, status, or trace SHA fails SUT replay and bijection checks."""
        recorded_bout = _recorded_bout_mod()
        hist_dir = _PFP009_ROOT / "docs" / "historical_evidence"
        trace_path = hist_dir / "demo2_r7_adversarial_debate_1790210039.jsonl"
        receipt_path = hist_dir / "demo2_r7_adversarial_debate_receipt.json"
        trace_rows = [
            json.loads(line)
            for line in trace_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        lf_trace = tmp_path / trace_path.name
        lf_trace.write_bytes(_lf_bytes(trace_path))
        monkeypatch.setattr(recorded_bout, "TRACE", lf_trace)

        bad_admitted = copy.deepcopy(receipt)
        bad_admitted["trials"][0]["current_replay_admitted"] = True
        bad_admitted_file = tmp_path / "bad_admitted_receipt.json"
        bad_admitted_bytes = json.dumps(bad_admitted).encode("utf-8")
        bad_admitted_file.write_bytes(bad_admitted_bytes)
        monkeypatch.setattr(recorded_bout, "RECEIPT", bad_admitted_file)
        monkeypatch.setattr(
            recorded_bout,
            "RECEIPT_SHA256",
            hashlib.sha256(bad_admitted_bytes).hexdigest(),
        )
        with pytest.raises(AssertionError):
            recorded_bout.test_retained_replay_refuses_all_ten()

        bad_obstruction = copy.deepcopy(receipt)
        obstruction_idx = next(
            i
            for i, t in enumerate(bad_obstruction["trials"])
            if t["proposer_move"] == "OPEN_SIGN_OBSTRUCTION"
        )
        bad_obstruction["trials"][obstruction_idx]["current_replay_status"] = (
            "Refused_AM_FSP_2_NullXi"
        )
        bad_obs_file = tmp_path / "bad_obstruction_receipt.json"
        bad_obs_bytes = json.dumps(bad_obstruction).encode("utf-8")
        bad_obs_file.write_bytes(bad_obs_bytes)
        monkeypatch.setattr(recorded_bout, "RECEIPT", bad_obs_file)
        monkeypatch.setattr(
            recorded_bout,
            "RECEIPT_SHA256",
            hashlib.sha256(bad_obs_bytes).hexdigest(),
        )
        with pytest.raises(AssertionError):
            recorded_bout.test_retained_replay_refuses_all_ten()

        with pytest.raises(ValueError, match="not refused in replay"):
            _validate_retained_replay_receipt(
                bad_admitted, trace_rows, self.EXPECTED_TRACE_LF_SHA256
            )

        with pytest.raises(ValueError, match="missing Refused_UnverifiedObstruction"):
            _validate_retained_replay_receipt(
                bad_obstruction, trace_rows, self.EXPECTED_TRACE_LF_SHA256
            )

        bad_digest = copy.deepcopy(receipt)
        bad_digest["source_trace_sha256"] = "0" * 64
        with pytest.raises(ValueError, match="source_trace_sha256"):
            _validate_retained_replay_receipt(
                bad_digest, trace_rows, self.EXPECTED_TRACE_LF_SHA256
            )


# ---------------------------------------------------------------------------
# 4. AUDIT-P009-014: Gate falsifier F1 replay
# ---------------------------------------------------------------------------


class TestGateFalsifierF1Replay:
    """Verifies AUDIT-P009-014: F1 triangle falsifier record, cohomology, and gate remediation."""

    AUDITED_COMMIT = "30609de2c3928238715375a9bac608256fa381d8"

    def test_retained_f1_record_and_replay_script_pin_cochain_zeroing_authorization(self) -> None:
        """Positive test: retained F1 JSON and replay script record 3 -> 0 cochain zeroing."""
        hist_dir = _PFP009_ROOT / "docs" / "historical_evidence"
        falsifiers_path = hist_dir / "adversary_gate_falsifiers.json"
        prov = json.loads((hist_dir / "provenance.json").read_text(encoding="utf-8"))

        assert prov["audited_gate_commit"] == self.AUDITED_COMMIT
        assert _lf_sha256(falsifiers_path) == (
            "770af5f4a052602ea138626714d8458cc665b1668e7a57145fb6e11ad2b38dbd"
        )
        assert _lf_sha256(_REPLAY_FALSIFIERS_PATH) == (
            "4a86607118d7f532864acb7c8aa572b4562b93499e3aee9608b6c6f9c3b6d405"
        )

        falsifiers = json.loads(falsifiers_path.read_text(encoding="utf-8"))
        assert falsifiers["audited_commit"] == self.AUDITED_COMMIT
        f1 = next(item for item in falsifiers["falsifiers"] if item["id"] == "F1")
        assert f1["observed"] == "AUTHORIZED"
        assert f1["is_authorized"] is True
        assert f1["trace"]["act2_before"] == [3.0, 0.0]
        assert f1["trace"]["act4_fired"] is True
        assert f1["trace"]["cochain_after_act4"] == [0.0]
        assert f1["trace"]["act2_after"] == [0.0, 0.0]

        # Confirm audited historical commit is outside this split checkout's Git object store.
        cat_res = subprocess.run(
            ["git", "cat-file", "-t", self.AUDITED_COMMIT],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert cat_res.returncode != 0

        # Inspect AST of replay_adversary_gate_falsifiers.py to confirm exact F1 input triple.
        script_source = _REPLAY_FALSIFIERS_PATH.read_text(encoding="utf-8")
        tree = ast.parse(script_source)
        func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        assert {"falsifiers", "replay"}.issubset(func_names)
        assert "edges=((0, 1), (1, 2), (2, 0))" in script_source
        assert "cochain = {(0, 1): 1.0, (1, 2): 1.0, (2, 0): 1.0}" in script_source

    def test_exact_triangle_cycle_sum_invariance_vs_zero_replacement(self) -> None:
        """Positive test: (1, 1, 1) keeps cycle sum 3 and l1 >= 3 across potentials; (0, 0, 0) -> 0."""
        tri = _triangle_mod()
        unit_claims = (Fraction(1), Fraction(1), Fraction(1))
        assert tri.cycle_sum(unit_claims) == Fraction(3)

        potentials = (
            (Fraction(0), Fraction(0), Fraction(0)),
            (Fraction(0), Fraction(1), Fraction(2)),
            (Fraction(-5, 3), Fraction(7, 4), Fraction(11, 6)),
            (Fraction(10), Fraction(-3, 7), Fraction(2, 5)),
        )
        for potential in potentials:
            coboundary = tri.edge_differences(potential)
            residual = tri.subtract(unit_claims, coboundary)
            l1_norm = sum(abs(v) for v in residual)
            assert tri.cycle_sum(coboundary) == Fraction(0)
            assert tri.cycle_sum(residual) == Fraction(3)
            assert l1_norm >= Fraction(3)

        # Quotient minimum 3 is attained at f = (0, 1, 2), giving residual (0, 0, 3).
        min_residual = tri.subtract(
            unit_claims,
            tri.edge_differences((Fraction(0), Fraction(1), Fraction(2))),
        )
        assert min_residual == (Fraction(0), Fraction(0), Fraction(3))
        assert sum(abs(v) for v in min_residual) == Fraction(3)

        # Zeroing the cochain changes the cohomology class from 3 to 0.
        zero_claims = (Fraction(0), Fraction(0), Fraction(0))
        assert tri.cycle_sum(zero_claims) == Fraction(0)
        assert tri.cycle_sum(zero_claims) != tri.cycle_sum(unit_claims)

    def test_current_adversary_gate_transports_cochain_and_refuses_f1_authorization(
        self,
        monkeypatch: pytest.MonkeyPatch,
        request: pytest.FixtureRequest,
    ) -> None:
        """Positive test: current ops/adversary preserves (1,1,1), refuses 3->0 lift, blocks auth."""
        mods = _load_adversary_gate_modules(monkeypatch, request)
        act_helpers = mods["act_helpers"]
        bout_service = mods["bout_service"]
        ports = mods["ports"]
        evidence = mods["evidence"]
        stage_domain = mods["stage_domain"]

        triangle = act_helpers.Network(
            nodes=(0, 1, 2),
            edges=((0, 1), (1, 2), (2, 0)),
            faces=(),
        )
        cochain = {
            (0, 1): Fraction(1),
            (1, 2): Fraction(1),
            (2, 0): Fraction(1),
        }

        # 1. NullCochainScoringAdapter now reports NOT_MEASURED, never raw l1 mass.
        null_res = ports.NullCochainScoringAdapter().identify_obstructions(triangle, cochain)
        assert null_res.is_ok
        null_meas = null_res.unwrap()
        assert null_meas.status is evidence.MeasurementStatus.NOT_MEASURED
        assert null_meas.phi1 is None and null_meas.gamma2 is None

        # 2. Act IV lift transports (1, 1, 1) unchanged onto original triangle edges.
        open_meas = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(3),
            gamma2=Fraction(0),
            defect_count=1,
            active_obstructions=("cycle_0_1_2",),
            certificate_verified=True,
            dual_witness=(("(0, 1)", Fraction(1)), ("(1, 2)", Fraction(1)), ("(2, 0)", Fraction(1))),
        )
        act4_res = act_helpers.execute_act4_gauge_break(
            None,
            triangle,
            cochain,
            (),
            [{"candidate_id": "cand_f1", "sbe": {"entropy_bits": "1", "purity": "1"}}],
            open_meas,
            run_key="f1_audit",
        )
        assert act4_res.is_ok
        fired, lifted_net, updated_cochain, telemetry, _ = act4_res.unwrap()
        assert fired is True
        assert set(triangle.edges).issubset(set(lifted_net.edges))
        assert len(lifted_net.edges) > len(triangle.edges)
        for edge in triangle.edges:
            assert updated_cochain[edge] == Fraction(1)
        for edge in set(lifted_net.edges) - set(triangle.edges):
            assert updated_cochain[edge] == Fraction(0)
        assert telemetry["lift"]["transported_edges"] == 3

        # 3. Any post-lift drop 3 -> 0 is refused with ADVERSARY_LIFT_LOWERED_OBSTRUCTION.
        zero_meas = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(0),
            gamma2=Fraction(0),
            defect_count=0,
            active_obstructions=(),
            certificate_verified=True,
        )
        assert bout_service._lift_lowered_obstruction(open_meas, zero_meas) is True
        lift_refusal = bout_service._lift_replaced_cochain(open_meas, zero_meas)
        assert lift_refusal is not None
        assert lift_refusal.is_err
        assert lift_refusal.error.code == "ADVERSARY_LIFT_LOWERED_OBSTRUCTION"

        # 4. Act VII refuses to authorize on open obstruction Phi1 = 3 even with ACCEPTED check.
        art_ref = "sha256:" + ("a" * 64)
        cand = stage_domain.CandidateProposalV1(
            producer_agent_id="seat_proposer",
            work_packet_id="sha256:" + ("b" * 64),
            artifact_refs=(art_ref,),
            prediction_receipt_id="sha256:" + ("c" * 64),
            nonclaims=("Scoped test candidate.",),
        )
        receipt_bytes = b'{"verdict":"ACCEPTED"}'
        check = evidence.CandidateCheckV1(
            verdict=evidence.CheckerVerdict.ACCEPTED,
            candidate_id=cand.candidate_id,
            candidate_content_sha256=art_ref,
            checker_id="checker_f1",
            checker_receipt_sha256=evidence.sha256_ref(receipt_bytes),
            checker_receipt_bytes=receipt_bytes,
        )
        act7_res = act_helpers.execute_act7_authorization_gate(
            None,
            "f1_audit",
            (cand,),
            (),
            {"residual_declared": True},
            open_meas,
            candidate_checks={cand.candidate_id: check},
            critique_verdicts={cand.candidate_id: "NON_BLOCKING"},
            fixture_seats=False,
        )
        assert act7_res.is_ok
        status, _, _, is_authorized, narrative = act7_res.unwrap()
        assert status == "BOUNDED_RESIDUAL"
        assert is_authorized is False
        assert "OPEN_OBSTRUCTION" in narrative["authorization_blockers"]

    def test_falsification_exact_zero_obstruction_with_bound_receipt_required_for_authorized(
        self,
        monkeypatch: pytest.MonkeyPatch,
        request: pytest.FixtureRequest,
    ) -> None:
        """Negative control: exact coboundary Phi1=0, Gamma2=0 + bound ACCEPTED check authorizes,
        while fixture seats or missing checker receipt block authorization."""
        mods = _load_adversary_gate_modules(monkeypatch, request)
        act_helpers = mods["act_helpers"]
        evidence = mods["evidence"]
        stage_domain = mods["stage_domain"]
        tri = _triangle_mod()

        # Genuine coboundary df = (1, 1, -2) from f = (0, 1, 2) has cycle sum 0.
        coboundary = tri.edge_differences((Fraction(0), Fraction(1), Fraction(2)))
        assert coboundary == (Fraction(1), Fraction(1), Fraction(-2))
        assert tri.cycle_sum(coboundary) == Fraction(0)

        zero_meas = evidence.ObstructionMeasurementV1(
            status=evidence.MeasurementStatus.MEASURED,
            backend="exact_triangle",
            phi1=Fraction(0),
            gamma2=Fraction(0),
            defect_count=0,
            active_obstructions=(),
            certificate_verified=True,
        )
        art_ref = "sha256:" + ("d" * 64)
        cand = stage_domain.CandidateProposalV1(
            producer_agent_id="seat_proposer",
            work_packet_id="sha256:" + ("e" * 64),
            artifact_refs=(art_ref,),
            prediction_receipt_id="sha256:" + ("f" * 64),
            nonclaims=("Scoped exact-coboundary candidate.",),
        )
        receipt_bytes = b'{"verdict":"ACCEPTED","exact_zero":true}'
        check = evidence.CandidateCheckV1(
            verdict=evidence.CheckerVerdict.ACCEPTED,
            candidate_id=cand.candidate_id,
            candidate_content_sha256=art_ref,
            checker_id="checker_exact",
            checker_receipt_sha256=evidence.sha256_ref(receipt_bytes),
            checker_receipt_bytes=receipt_bytes,
        )

        # Canned fixture_seats=True blocks with FIXTURE_ONLY.
        fixture_res = act_helpers.execute_act7_authorization_gate(
            None,
            "coboundary_fixture",
            (cand,),
            (),
            {"residual_declared": False},
            zero_meas,
            candidate_checks={cand.candidate_id: check},
            critique_verdicts={cand.candidate_id: "NON_BLOCKING"},
            fixture_seats=True,
        )
        assert fixture_res.unwrap()[0] == "FIXTURE_ONLY"
        assert fixture_res.unwrap()[3] is False

        # Live seats (fixture_seats=False) + exact joint zero + bound ACCEPTED check -> AUTHORIZED.
        live_res = act_helpers.execute_act7_authorization_gate(
            None,
            "coboundary_live",
            (cand,),
            (),
            {"residual_declared": False},
            zero_meas,
            candidate_checks={cand.candidate_id: check},
            critique_verdicts={cand.candidate_id: "NON_BLOCKING"},
            fixture_seats=False,
        )
        status, selected_id, _, is_authorized, _ = live_res.unwrap()
        assert status == "AUTHORIZED"
        assert selected_id == cand.candidate_id
        assert is_authorized is True

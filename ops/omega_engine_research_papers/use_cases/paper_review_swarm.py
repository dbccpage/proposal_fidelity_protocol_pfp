"""Eight-Stage Paper Review, Falsification, and Swarm Verification Pipeline.

AuthorityEffect: None.

Incorporates the 8-stage review pipeline and multi-round convergence loop from
omega-paper-review-swarm into the omega_engine_research_papers Clean Architecture package:
  Stage 0: Preflight, Deposit Envelope Purity & Layout
  Stage 1: Mathematical Foundations, Dialect Firewall & Old Man Red-Team
  Stage 2: Formal Mechanization & Lean 4 Verification
  Stage 3: Exact Computational Engine & Techne Code Swarm
  Stage 4: Interactive Pedagogy & Companion Replay
  Stage 5: Documentation, Formatting & Monograph
  Stage 6: Packaging, Release ZIP Bundling & Checksum Witness
  Stage Ω: Canonical Severe Zenodo Republication Gate
"""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .claim_hygiene_auditor import ClaimHygieneAuditor
from .hand_waving_lint import HandWavingLint
from .verification_52_gate import Verification52Gate, resolve_paper_paths


def _get_python_runner() -> List[str]:
    """Resolve Python interpreter honoring Windows Python 3.12 pinning."""
    if sys.platform == "win32" and sys.version_info >= (3, 14):
        try:
            res = subprocess.run(["py", "-3.12", "--version"], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                return ["py", "-3.12"]
        except Exception:
            pass
    return [sys.executable]


def _run_cmd(
    cmd: List[str],
    cwd: Optional[pathlib.Path] = None,
    timeout: int = 120,
) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except Exception as exc:
        return -1, "", str(exc)


@dataclass
class StageResult:
    """Receipt for a single stage in the 8-stage review pipeline."""

    stage_index: int
    stage_name: str
    status: str  # "PASS", "BLOCKED", "FAIL", "NOT_APPLICABLE", "SKIPPED"
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


@dataclass
class SwarmReviewReceipt:
    """Full 8-stage swarm review receipt with self-healing fuel loop."""

    receipt_schema: str = "omega.swarm_self_review.v1"
    review_id: str = ""
    paper_id: str = "UNKNOWN"
    paper_path: str = ""
    timestamp_utc: str = ""
    authority_effect: str = "None"
    overall_status: str = "BLOCKED"  # "PASS", "NEEDS_REVISION", "BLOCKED"
    stages: List[StageResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    nonclaims: List[str] = field(
        default_factory=lambda: [
            "AuthorityEffect: None",
            "Review findings are proposals; no automated promotion or publication.",
            "Swarm review receipt reflects local deterministic gate execution only.",
        ]
    )

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def extract_paper_metadata(monograph: pathlib.Path) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    if not monograph.exists():
        return meta
    text = monograph.read_text(encoding="utf-8", errors="replace")
    m_id = re.search(r'paper_id:\s*["\']?([^"\'\n]+)["\']?', text)
    if m_id:
        meta["paper_id"] = m_id.group(1).strip()
    m_ver = re.search(r'version:\s*["\']?([^"\'\n]+)["\']?', text)
    if m_ver:
        meta["version"] = m_ver.group(1).strip()
    return meta


# -----------------------------------------------------------------------------
# Stage 0: Preflight, Deposit Envelope Purity & Layout
# -----------------------------------------------------------------------------
def run_stage_0(paper_dir: pathlib.Path, monograph: pathlib.Path) -> StageResult:
    res = StageResult(0, "preflight_and_envelope_purity", "PASS")

    # 1. Path length check (Win32 <= 250 chars)
    deep_paths: List[str] = []
    for f in paper_dir.rglob("*"):
        if any(part in {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "_recovered"} for part in f.parts):
            continue
        if f.suffix == ".zip":
            continue
        if len(str(f)) > 250:
            deep_paths.append(str(f))
    if deep_paths:
        res.errors.append(f"Win32 MAX_PATH depth violation: {len(deep_paths)} files exceed 250 characters.")
        res.status = "BLOCKED"

    # 2. Envelope cleanliness (no forbidden directories)
    forbidden_dirs = ["evidence", "reconstruction_v1", "dist", "rt"]
    for d in forbidden_dirs:
        if (paper_dir / d).is_dir():
            res.errors.append(f"Deposit impurity: forbidden directory '{d}' present in paper root.")
            res.status = "BLOCKED"

    if not monograph.exists():
        res.errors.append(f"Monograph markdown not found at {monograph}")
        res.status = "BLOCKED"

    return res


# -----------------------------------------------------------------------------
# Stage 1: Mathematical Foundations, Dialect Firewall & Red-Team
# -----------------------------------------------------------------------------
def run_stage_1(paper_dir: pathlib.Path, monograph: pathlib.Path) -> StageResult:
    res = StageResult(1, "mathematical_foundations_and_dialect_firewall", "PASS")
    if not monograph.exists():
        res.status = "SKIPPED"
        return res

    body = monograph.read_text(encoding="utf-8", errors="replace")

    # Claim hygiene audit
    ch_report = ClaimHygieneAuditor.audit_text(body)
    if not ch_report.passed:
        for v in ch_report.violations:
            res.warnings.append(f"Line {v.line_number}: Restricted word '{v.matched_word}' -> suggest '{v.suggested_replacement}'")

    # Companion claim ledger check
    ledgers = list(paper_dir.glob("*claim_ledger.md"))
    if not ledgers:
        res.warnings.append("Missing companion claim ledger (*_claim_ledger.md)")
    else:
        res.details["claim_ledger"] = ledgers[0].name

    # Old Man ChatGPT Adversarial Red Team audit
    rt_report = HandWavingLint.scan(body)
    res.details["red_team_passed"] = rt_report.passed
    res.details["red_team_blocking_count"] = rt_report.blocking_count
    if not rt_report.passed:
        res.status = "FAIL"
        for f in rt_report.findings:
            if f.severity == "BLOCKING":
                res.errors.append(f"Old Man Red Team Blocker (line {f.line_number}): {f.objection}")

    return res


# -----------------------------------------------------------------------------
# Stage 2: Formal Mechanization & Lean 4 Verification
# -----------------------------------------------------------------------------
def run_stage_2(paper_dir: pathlib.Path) -> StageResult:
    res = StageResult(2, "formal_lean4_mechanization", "PASS")
    lean_dir = paper_dir / "lean4"
    lakefile = lean_dir / "lakefile.lean"
    if not lakefile.exists():
        lakefile_toml = lean_dir / "lakefile.toml"
        if not lakefile_toml.exists():
            res.status = "NOT_APPLICABLE"
            res.details["note"] = "No local Lean 4 lakefile present; paper is purely computational/monographic."
            return res

    code, stdout, stderr = _run_cmd(["lake", "build"], cwd=lean_dir, timeout=60)
    if code != 0:
        res.errors.append(f"lake build failed (exit {code}): {stderr or stdout}")
        res.status = "FAIL"
    else:
        res.details["lake_build"] = "PASS"
    return res


# -----------------------------------------------------------------------------
# Stage 3: Exact Computational Engine & Techne Code Swarm
# -----------------------------------------------------------------------------
def run_stage_3(paper_dir: pathlib.Path) -> StageResult:
    res = StageResult(3, "techne_code_swarm_and_tests", "PASS")
    py_runner = _get_python_runner()
    has_target = False

    # 1. Figure generation check (fail-closed)
    fig_script = paper_dir / "code" / "generate_figures.py"
    if fig_script.is_file():
        has_target = True
        code, stdout, stderr = _run_cmd([*py_runner, str(fig_script.resolve())], cwd=paper_dir)
        if code != 0:
            res.errors.append(f"Figure generation failed in code/generate_figures.py (exit {code}): {stderr.strip() or stdout.strip()}")
            res.status = "FAIL"
        else:
            res.details["generate_figures"] = "PASS"

    # 2. Package consistency verifier check if present
    verify_pkg = paper_dir / "code" / "verify_package.py"
    if verify_pkg.is_file():
        has_target = True
        code, stdout, stderr = _run_cmd([*py_runner, str(verify_pkg.resolve())], cwd=paper_dir)
        if code != 0:
            res.errors.append(f"Package verifier failed in code/verify_package.py (exit {code}): {stderr.strip() or stdout.strip()}")
            res.status = "FAIL"
        else:
            res.details["verify_package"] = "PASS"

    # 3. Unit and regression test execution
    tests_dir = paper_dir / "code" / "tests"
    if tests_dir.is_dir():
        has_target = True
        code, stdout, stderr = _run_cmd([*py_runner, "-m", "pytest", str(tests_dir.resolve()), "-q"], cwd=paper_dir)
        if code != 0:
            res.errors.append(f"pytest failed in code/tests/ (exit {code}): {stderr.strip() or stdout.strip()}")
            res.status = "FAIL"
        else:
            res.details["pytest_summary"] = stdout.strip().splitlines()[-1] if stdout else "PASS"

    if not has_target:
        res.status = "NOT_APPLICABLE"
        res.details["note"] = "No local code/tests, generate_figures.py, or verify_package.py found."

    return res


# -----------------------------------------------------------------------------
# Stage 4: Interactive Pedagogy & Companion Replay
# -----------------------------------------------------------------------------
def run_stage_4(paper_dir: pathlib.Path) -> StageResult:
    res = StageResult(4, "interactive_pedagogy_and_replay", "PASS")
    code_dir = paper_dir / "code"
    receipts = list(code_dir.glob("*execution_receipt*.json")) if code_dir.is_dir() else []
    if receipts:
        receipt_file = receipts[0]
        try:
            data = json.loads(receipt_file.read_text(encoding="utf-8", errors="replace"))
            res.details["execution_receipt"] = receipt_file.name
            res.details["scenarios_count"] = len(data.get("scenarios", []))
            res.details["receipt_status"] = data.get("summary", {}).get("status", "UNKNOWN")
        except Exception as e:
            res.warnings.append(f"Could not parse companion execution receipt: {e}")
    else:
        res.details["note"] = "No companion execution receipt found in code/."
    return res


# -----------------------------------------------------------------------------
# Stage 5: Documentation, Formatting & Monograph
# -----------------------------------------------------------------------------
def run_stage_5(paper_dir: pathlib.Path, monograph: pathlib.Path) -> StageResult:
    res = StageResult(5, "documentation_and_monograph", "PASS")
    changelogs = list(paper_dir.glob("*change_log.md"))
    if not changelogs:
        res.warnings.append("Missing companion change log (*_change_log.md)")
    else:
        res.details["change_log"] = changelogs[0].name
    return res


# -----------------------------------------------------------------------------
# Stage 6: Packaging, Release ZIP Bundling & Checksum Witness
# -----------------------------------------------------------------------------
def run_stage_6(paper_dir: pathlib.Path, prior_stages: List[StageResult]) -> StageResult:
    res = StageResult(6, "packaging_and_release_bundle", "PASS")
    blockers = [s for s in prior_stages if s.status in ("BLOCKED", "FAIL")]
    if blockers:
        res.status = "BLOCKED"
        for b in blockers:
            res.errors.append(f"Release bundling blocked by Stage {b.stage_index} ({b.stage_name}) defects.")
    return res


# -----------------------------------------------------------------------------
# Stage Ω: Canonical Severe Zenodo Republication Gate
# -----------------------------------------------------------------------------
def run_stage_omega(
    paper_dir: pathlib.Path,
    monograph: pathlib.Path,
    evidence_path: Optional[pathlib.Path] = None,
) -> StageResult:
    receipt = Verification52Gate.audit_paper_package(paper_dir, monograph, evidence_path)
    res = StageResult(
        99,
        "canonical_severe_zenodo_republication_gate",
        receipt.status,
        details=receipt.to_dict(),
        errors=list(receipt.errors),
    )
    return res


# -----------------------------------------------------------------------------
# Multi-Round Review Swarm Orchestrator
# -----------------------------------------------------------------------------
def run_swarm_review(
    paper_path_input: str,
    output_path: Optional[str] = None,
    fuel: int = 3,
    verbose: bool = False,
) -> SwarmReviewReceipt:
    paper_dir, monograph = resolve_paper_paths(paper_path_input)
    meta = extract_paper_metadata(monograph)

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    review_id = f"SWARM_REV_{now_utc.strftime('%Y%m%d_%H%M%S')}"

    receipt = SwarmReviewReceipt(
        review_id=review_id,
        paper_id=meta.get("paper_id", paper_dir.name),
        paper_path=str(monograph),
        timestamp_utc=now_utc.isoformat(),
        authority_effect="None",
    )

    remaining_fuel = fuel
    round_index = 1
    while True:
        if verbose:
            print(f"[omega_engine_research_papers] === Review Round {round_index} (Remaining Fuel: {remaining_fuel}) ===")

        st0 = run_stage_0(paper_dir, monograph)
        st1 = run_stage_1(paper_dir, monograph)
        st2 = run_stage_2(paper_dir)
        st3 = run_stage_3(paper_dir)
        st4 = run_stage_4(paper_dir)
        st5 = run_stage_5(paper_dir, monograph)
        st6 = run_stage_6(paper_dir, [st0, st1, st2, st3, st4, st5])
        st_omega = run_stage_omega(paper_dir, monograph)

        receipt.stages = [st0, st1, st2, st3, st4, st5, st6, st_omega]
        blocked_count = sum(1 for s in receipt.stages if s.status not in ("PASS", "NOT_APPLICABLE"))

        if blocked_count == 0 or remaining_fuel <= 0:
            break

        remaining_fuel -= 1
        round_index += 1

    total_errors = sum(len(s.errors) for s in receipt.stages)
    total_warnings = sum(len(s.warnings) for s in receipt.stages)
    blocked_count = sum(1 for s in receipt.stages if s.status not in ("PASS", "NOT_APPLICABLE"))

    if blocked_count > 0:
        receipt.overall_status = "NEEDS_REVISION"
        receipt.summary = {
            "verdict": "NOT READY FOR ZENODO REPUBLICATION",
            "stages_run": len(receipt.stages),
            "stages_passed": sum(1 for s in receipt.stages if s.status in ("PASS", "NOT_APPLICABLE")),
            "stages_blocked": blocked_count,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "rounds_executed": round_index,
            "obstruction_report": {
                "status": "TERMINAL_OBSTRUCTION",
                "blocked_stages": [f"Stage {s.stage_index} ({s.stage_name})" for s in receipt.stages if s.status not in ("PASS", "NOT_APPLICABLE")],
                "unresolved_errors": [err for s in receipt.stages for err in s.errors],
                "required_work": (
                    "Automated review exhausted fuel without resolving all gates. "
                    "Unresolved defects require manual editing or mathematical research before publication."
                ),
            },
        }
    else:
        receipt.overall_status = "PASS"
        receipt.summary = {
            "verdict": "READY FOR ZENODO REPUBLICATION",
            "stages_run": len(receipt.stages),
            "stages_passed": len(receipt.stages),
            "stages_blocked": 0,
            "total_errors": 0,
            "total_warnings": total_warnings,
            "rounds_executed": round_index,
        }

    if output_path:
        out_p = pathlib.Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")

    return receipt

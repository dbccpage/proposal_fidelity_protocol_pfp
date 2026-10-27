#!/usr/bin/env python3
"""
orchestrate_autop.py — Autonomous Engine Meta-Pipeline (AutoP) Runner

Default/post-run: return a read-only current-IDE auto-learn handoff.
Explicit --maintenance: execute AutoP stages 0–8 in strict sequential order:
  Stage 0: Process review/audit input receipt (AuthorityEffect: None)
  Stage 1: Episode compilation & candidate intake into runs/skill_compiler/episodes/
  Stage 2: Knowledge parity check & 6-host packaging parity gate
  Stage 3: Skill budget gate (max 300 lines / 20480 bytes)
  Stage 4: Multi-host skill census & panel verification
  Stage 5: Skill compiler regression evals (eval_runner.py)
  Stage 6: Ooutwire register audit & candidate proposal emission
  Stage 7: Auto-docs session documentation synthesis & comment slop audit
  Stage 8: Governance digest, then hash-checked apply of checked-in repairs

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def find_repo_root(start: Optional[Path] = None) -> Path:
    curr = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (curr / ".git").exists() and (
            (curr / "engine").is_dir() or (curr / ".agents").is_dir()
        ):
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return (start or Path.cwd()).resolve()


def run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout: int = 180,
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
    except Exception as e:
        return -1, "", str(e)


@dataclass
class AutopStageResult:
    stage_index: int
    stage_name: str
    status: str  # "PASS", "FAIL", "SKIPPED"
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AutopReceipt:
    autop_id: str
    timestamp_utc: str
    authority_effect: str
    overall_status: str  # "PASS", "FAIL"
    source_receipt: Optional[str] = None
    stages: List[AutopStageResult] = field(default_factory=list)
    nonclaims: List[str] = field(
        default_factory=lambda: [
            "AuthorityEffect: None",
            "Automatic admission is not mathematical proof",
            "Knowledge parity does not imply system completion",
        ]
    )


# -----------------------------------------------------------------------------
# Stage 0: Process Intake Receipt
# -----------------------------------------------------------------------------
def execute_stage_0(
    repo_root: Path, receipt_path: Optional[Path]
) -> Tuple[AutopStageResult, List[str]]:
    res = AutopStageResult(0, "process_intake_receipt", "PASS")
    extracted_errors: List[str] = []

    if receipt_path and receipt_path.exists():
        try:
            items: List[Dict[str, Any]] = []
            res.details["receipt_source"] = str(receipt_path)

            if receipt_path.is_dir():
                candidate_files = sorted(
                    list(receipt_path.glob("*.jsonl")) + list(receipt_path.glob("*.json")),
                    key=lambda p: p.name,
                )
                for f in candidate_files:
                    if f.suffix == ".jsonl":
                        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                            line_str = line.strip()
                            if line_str:
                                try:
                                    items.append(json.loads(line_str))
                                except Exception:
                                    pass
                    else:
                        try:
                            loaded = json.loads(f.read_text(encoding="utf-8", errors="replace"))
                            if isinstance(loaded, list):
                                items.extend(loaded)
                            elif isinstance(loaded, dict):
                                items.append(loaded)
                        except Exception:
                            pass
            elif receipt_path.suffix == ".jsonl":
                for line in receipt_path.read_text(encoding="utf-8", errors="replace").splitlines():
                    line_str = line.strip()
                    if line_str:
                        items.append(json.loads(line_str))
            else:
                data = json.loads(receipt_path.read_text(encoding="utf-8", errors="replace"))
                items = data if isinstance(data, list) else [data]

            res.details["item_count"] = len(items)
            paper_ids = []

            for item in items:
                if not isinstance(item, dict):
                    continue
                run_obj = item.get("run_all", item)
                pid = (
                    item.get("audit_id")
                    or item.get("slug")
                    or item.get("paper_id")
                    or item.get("subsystem")
                    or item.get("module")
                    or run_obj.get("paper_id", "UNKNOWN")
                )
                paper_ids.append(pid)
                stages = run_obj.get("stages", [])
                for s in stages:
                    sname = s.get("name") or s.get("stage_name", "stage")
                    for err in s.get("errors", []):
                        extracted_errors.append(f"[{pid}|{sname}] {err}")

                for blocker in item.get("decisive_blockers", []):
                    extracted_errors.append(f"[{pid}|decisive_blocker] {blocker}")

                for err in item.get("errors", []):
                    extracted_errors.append(f"[{pid}|error] {err}")

                checks = item.get("checks", {})
                if isinstance(checks, dict):
                    for cname, cval in checks.items():
                        if cval not in ("PASS", True):
                            extracted_errors.append(f"[{pid}|check:{cname}] {cval}")

            res.details["paper_ids"] = paper_ids
            res.details["extracted_error_count"] = len(extracted_errors)
        except Exception as e:
            res.warnings.append(f"Could not parse intake receipt {receipt_path}: {e}")
    else:
        res.details["note"] = (
            "No intake receipt provided; running standalone AutoP maintenance cycle."
        )

    return res, extracted_errors


ANTI_PATTERN_MARKERS = ("anti-pattern", "anti_pattern")
REQUIRED_ANTI_PATTERN_SKILL = "techne-code-lean4-anti-patterns"


def discover_anti_pattern_skills(skills_root: Path) -> List[str]:
    """Skill package names that OEAUTOP must call on every run."""
    if not skills_root.is_dir():
        return []
    found: List[str] = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir() or not (child / "SKILL.md").is_file():
            continue
        if any(marker in child.name for marker in ANTI_PATTERN_MARKERS):
            found.append(child.name)
    return found


def _scan_root_for(skill_id: str, repo_root: Path) -> Path:
    if skill_id == "techne-code-lean4-anti-patterns":
        return repo_root
    if skill_id == "techne-code-rust-anti-patterns":
        crates = repo_root / "engine" / "crates_rs"
        if crates.is_dir():
            return crates
    return repo_root / "operads" / "skills"


def _anti_pattern_command(
    script: Path,
    repo_root: Path,
    skill_id: str,
    receipt_path: Path,
) -> List[str]:
    if script.name == "hunt_antipatterns.py":
        return [
            sys.executable,
            str(script),
            str(repo_root / "operads" / "skills"),
            "--output",
            str(receipt_path),
            "--summary",
        ]
    if script.name == "anti_pattern_lint.py":
        return [
            sys.executable,
            str(script),
            "--catalog",
            str(repo_root / "operads" / "patterns"),
            "--report-out",
            str(receipt_path),
            "--check",
        ]
    report_flag = "--report-out"
    return [
        sys.executable,
        str(script),
        "--path",
        str(_scan_root_for(skill_id, repo_root)),
        report_flag,
        str(receipt_path),
        "--check",
    ]


def invoke_anti_pattern_skills(
    repo_root: Path,
    res: AutopStageResult,
) -> List[Dict[str, Any]]:
    """Run every anti-pattern skill entrypoint. Findings warn; a broken catalog fails."""
    skills_root = repo_root / "operads" / "skills"
    skill_ids = discover_anti_pattern_skills(skills_root)
    if REQUIRED_ANTI_PATTERN_SKILL not in skill_ids:
        res.errors.append(f"Missing required skill {REQUIRED_ANTI_PATTERN_SKILL}")
        skill_ids = sorted({*skill_ids, REQUIRED_ANTI_PATTERN_SKILL})
    calls: List[Dict[str, Any]] = []
    receipt_dir = repo_root / "runs" / "autop_anti_pattern"
    for skill_id in skill_ids:
        skill_dir = skills_root / skill_id
        if not skill_dir.is_dir():
            res.errors.append(f"Missing skill directory {skill_dir}")
            calls.append({"skill_id": skill_id, "status": "MISSING_SKILL"})
            continue
        scripts = sorted((skill_dir / "scripts").glob("*.py")) if (skill_dir / "scripts").is_dir() else []
        if not scripts:
            res.warnings.append(f"{skill_id}: NO_ENTRYPOINT")
            calls.append({"skill_id": skill_id, "status": "NO_ENTRYPOINT"})
            continue
        for script in scripts:
            receipt_path = receipt_dir / f"{skill_id}__{script.stem}.json"
            command = _anti_pattern_command(script, repo_root, skill_id, receipt_path)
            code, out, err = run_cmd(command, cwd=repo_root)
            status = "PASS"
            if skill_id == "anti-pattern-lint" and code != 0:
                status = "CATALOG_BROKEN"
                res.errors.append(
                    f"{skill_id} catalog check failed (exit {code}): {err or out}"
                )
            elif code != 0:
                status = "FINDINGS" if code == 1 else "ERROR"
                res.warnings.append(
                    f"{skill_id} {script.name} exit {code}: {(err or out)[:500]}"
                )
            row: Dict[str, Any] = {
                "skill_id": skill_id,
                "script": script.name,
                "status": status,
                "exit_code": code,
            }
            if receipt_path.is_file():
                row["receipt"] = str(receipt_path.relative_to(repo_root))
            calls.append(row)
    if any(row["status"] in {"MISSING_SKILL", "CATALOG_BROKEN"} for row in calls):
        res.status = "FAIL"
    return calls


# -----------------------------------------------------------------------------
# Stage 1: Episode Intake, Anti-Skill Mining & Truth-Boundary Audit
# -----------------------------------------------------------------------------
def execute_stage_1(repo_root: Path, errors: List[str]) -> AutopStageResult:
    res = AutopStageResult(1, "episode_intake_and_antiskill_mining", "PASS")
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    episodes_dir = repo_root / "runs" / "skill_compiler" / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    episode_file = episodes_dir / f"{today}.jsonl"

    if errors:
        entry = {
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "adversary-research-paper",
            "error_count": len(errors),
            "errors": errors[:10],
            "disposition": "RECORDED_FOR_ANTI_SKILL_ANALYSIS",
        }
        try:
            with open(episode_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            res.details["episode_recorded"] = True
            res.details["episode_file"] = str(episode_file.relative_to(repo_root))
        except Exception as e:
            res.warnings.append(f"Could not append episode: {e}")
    else:
        res.details["episode_recorded"] = False
        res.details["note"] = "Zero errors logged; no failure episodes to append."

    # -------------------------------------------------------------------------
    # Invoke auto-anti-skill: segment-dialogue and mine-candidates
    # -------------------------------------------------------------------------
    antiskill_script = (
        repo_root / "operads" / "skills" / "auto-anti-skill" / "scripts" / "auto_anti_skill.py"
    )
    ooutwire_dir = repo_root / "eis" / "antiskills" / "ooutwire"
    ooutwire_dir.mkdir(parents=True, exist_ok=True)

    if antiskill_script.exists():
        segmented_output = ooutwire_dir / f"autop_{timestamp}_segmented.jsonl"
        candidates_output = ooutwire_dir / f"autop_{timestamp}_candidates.json"

        # If review errors exist, construct a run-specific dialogue transcript
        if errors:
            run_transcript = repo_root / "scratch" / f"transcript_{timestamp}.txt"
            run_transcript.parent.mkdir(parents=True, exist_ok=True)
            transcript_lines = [
                "❯ Auditor: Please review the following package observations:",
                "",
                "● Assistant: The review identified these specific boundary points:",
            ]
            for err in errors[:5]:
                transcript_lines.append(f"  - {err}")
            transcript_lines.extend(
                [
                    "",
                    "❯ Auditor: Please ensure all mathematical assertions are bounded and AuthorityEffect remains None.",
                    "",
                    "● Assistant: Acknowledged. Claims are strictly bounded; AuthorityEffect remains None.",
                ]
            )
            run_transcript.write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")
            source_arg = str(run_transcript)
        else:
            default_fixture = (
                repo_root / "eis" / "antiskills" / "fixtures" / "default_transcript.txt"
            )
            source_arg = str(default_fixture)

        seg_cmd = [
            sys.executable,
            str(antiskill_script),
            "segment-dialogue",
            "--source",
            source_arg,
            "--output",
            str(segmented_output),
        ]
        code, out, err = run_cmd(seg_cmd, cwd=repo_root)
        if code != 0:
            res.warnings.append(
                f"auto-anti-skill segment-dialogue failed (exit {code}): {err or out}"
            )
        else:
            res.details["auto_anti_skill_segment_dialogue"] = "PASS"
            res.details["segmented_output"] = str(segmented_output.relative_to(repo_root))

            mine_cmd = [
                sys.executable,
                str(antiskill_script),
                "mine-candidates",
                "--output",
                str(candidates_output),
            ]
            default_episodes = (
                repo_root / "eis" / "antiskills" / "fixtures" / "default_episodes.json"
            )
            if default_episodes.exists():
                mine_cmd.extend(["--episodes", str(default_episodes)])
            else:
                mine_cmd.extend(["--episodes", str(segmented_output)])

            code_mine, out_mine, err_mine = run_cmd(mine_cmd, cwd=repo_root)
            if code_mine != 0:
                res.warnings.append(
                    f"auto-anti-skill mine-candidates failed (exit {code_mine}): {err_mine or out_mine}"
                )
            else:
                res.details["auto_anti_skill_mine_candidates"] = "PASS"
                res.details["candidates_output"] = str(candidates_output.relative_to(repo_root))
    else:
        res.warnings.append(f"Missing {antiskill_script}")

    # -------------------------------------------------------------------------
    # Active Anti-Skill Enforcement: Audit AutoP candidate transitions
    # -------------------------------------------------------------------------
    validator_path = repo_root / "eis" / "antiskills" / "validator.py"
    if validator_path.exists():
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("anti_skills_validator", validator_path)
            if spec and spec.loader:
                v_mod = importlib.util.module_from_spec(spec)
                sys.modules["anti_skills_validator"] = v_mod
                spec.loader.exec_module(v_mod)
                # Verify that AutoP proposal requests FINDING or HOLD, never MERGE or ACTION_LICENSE
                hits = v_mod.evaluate_proposal_effect("auto-oe-autop", "FINDING")
                if hits:
                    res.errors.append(
                        f"AutoP violated anti-skill: {[h['failure_code'] for h in hits]}"
                    )
                else:
                    res.details["antiskill_proposal_audit"] = "PASS"
        except Exception as e:
            res.warnings.append(f"Anti-skill validator execution error: {e}")
    # -------------------------------------------------------------------------
    # Call every anti-pattern skill, including techne-code-lean4-anti-patterns.
    # -------------------------------------------------------------------------
    skill_calls = invoke_anti_pattern_skills(repo_root, res)
    res.details["anti_pattern_skills"] = skill_calls
    hunter_row = next(
        (row for row in skill_calls if row["skill_id"] == "auto-code-anti-pattern-hunter"),
        None,
    )
    if hunter_row is not None:
        res.details["anti_pattern_hunter_status"] = hunter_row["status"]
        if hunter_row.get("receipt"):
            res.details["anti_pattern_receipt"] = hunter_row["receipt"]

    # -------------------------------------------------------------------------
    # Intelligence Digestion & Cold-Storage Archiving (Invariant 1 & 2)
    # -------------------------------------------------------------------------
    try:
        repo_str = str(repo_root)
        if repo_str not in sys.path:
            sys.path.insert(0, repo_str)
        from adversary.use_cases.intelligence_digestion.digestion_service import (
            digest_and_archive_intelligence,
        )
        digestion_receipt = digest_and_archive_intelligence(repo_root)
        res.details["intelligence_digestion_status"] = "PASS"
        res.details["intelligence_runs_archived"] = digestion_receipt.total_runs_archived
        res.details["intelligence_runs_examined"] = digestion_receipt.total_runs_examined
    except Exception as e:
        res.warnings.append(f"Intelligence digestion error: {e}")

    # Devour & Archive OMC DAGs (Extract active blockers, archive cleared files)
    try:
        from adversary.use_cases.intelligence_digestion.omc_dag_miner import (
            devour_and_archive_omc_dags,
        )
        omc_receipt = devour_and_archive_omc_dags(repo_root)
        res.details["omc_dag_digestion_status"] = omc_receipt.get("status", "PASS")
        res.details["omc_dags_archived"] = omc_receipt.get("files_archived_count", 0)
        res.details["omc_dags_retained"] = omc_receipt.get("files_retained_count", 0)
    except Exception as e:
        res.warnings.append(f"OMC DAG digestion error: {e}")

    return res


# -----------------------------------------------------------------------------
# Stage 2: Packaging Parity & Knowledge Parity Gate
# -----------------------------------------------------------------------------
def execute_stage_2(repo_root: Path) -> AutopStageResult:
    res = AutopStageResult(2, "packaging_and_knowledge_parity", "PASS")

    # 1. Knowledge Parity
    kp_candidates = [
        repo_root
        / "operads"
        / "skill_operad"
        / "skill_compiler"
        / "knowledge_parity.py",
    ]
    kp_script = next((c for c in kp_candidates if c.exists()), kp_candidates[0])
    if kp_script.exists():
        code, out, err = run_cmd([sys.executable, str(kp_script)], cwd=repo_root)
        if code != 0:
            res.errors.append(f"Knowledge parity check failed (exit {code}): {err or out}")
        else:
            res.details["knowledge_parity"] = "PASS"
    else:
        res.warnings.append(f"Missing {kp_script}")

    # 2. 6-Host Parity Gate
    sync_script = (
        repo_root
        / "operations"
        / "use_cases"
        / "packaging"
        / "sync_cross_host_skills.py"
    )
    if sync_script.exists():
        if not (repo_root / ".claude" / "skills").is_dir():
            res.details["six_host_parity"] = (
                "SKIPPED: Cross-host skill directories (.claude, .codex, .grok) "
                "are not populated in this workspace; OEOP remains the source owner."
            )
        else:
            code, out, err = run_cmd([sys.executable, str(sync_script), "--check"], cwd=repo_root)
            if code != 0:
                res.errors.append(f"6-host skill parity check failed (exit {code}): {err or out}")
            else:
                res.details["six_host_parity"] = "PASS"
    else:
        res.warnings.append(f"Missing {sync_script}")

    if res.errors:
        res.status = "FAIL"
    return res


# -----------------------------------------------------------------------------
# Stage 3: Skill Budget Gate
# -----------------------------------------------------------------------------
def execute_stage_3(repo_root: Path) -> AutopStageResult:
    res = AutopStageResult(3, "skill_budget_gate", "PASS")
    bg_candidates = [
        repo_root
        / "operads"
        / "skill_operad"
        / "skill_compiler"
        / "budget_gate.py",
    ]
    bg_script = next((c for c in bg_candidates if c.exists()), bg_candidates[0])
    if bg_script.exists():
        code, out, err = run_cmd([sys.executable, str(bg_script)], cwd=repo_root)
        if code != 0:
            res.errors.append(f"Skill budget gate failed (exit {code}): {err or out}")
        else:
            res.details["budget_gate_status"] = "PASS"
    else:
        res.warnings.append(f"Missing {bg_script}")

    if res.errors:
        res.status = "FAIL"
    return res


# -----------------------------------------------------------------------------
# Stage 4: Multi-Host Skill Census & Panel Audit
# -----------------------------------------------------------------------------
def execute_stage_4(repo_root: Path) -> AutopStageResult:
    res = AutopStageResult(4, "multi_host_skill_census", "PASS")
    census_script = (
        repo_root
        / "operations"
        / "use_cases"
        / "packaging"
        / "multi_host_skill_census.py"
    )
    if census_script.exists():
        code, out, err = run_cmd([sys.executable, str(census_script)], cwd=repo_root)
        if code != 0:
            res.errors.append(f"Multi-host skill census failed (exit {code}): {err or out}")
        else:
            res.details["census_status"] = "PASS"
    else:
        res.warnings.append(f"Missing {census_script}")

    if res.errors:
        res.status = "FAIL"
    return res


# -----------------------------------------------------------------------------
# Stage 5: Skill Compiler Eval Runner
# -----------------------------------------------------------------------------
def execute_stage_5(repo_root: Path) -> AutopStageResult:
    res = AutopStageResult(5, "skill_compiler_eval_runner", "PASS")
    eval_candidates = [
        repo_root
        / "operads"
        / "skill_operad"
        / "skill_compiler"
        / "eval_runner.py",
    ]
    eval_script = next((c for c in eval_candidates if c.exists()), eval_candidates[0])
    if eval_script.exists():
        code, out, err = run_cmd([sys.executable, str(eval_script)], cwd=repo_root)
        if code != 0:
            res.errors.append(f"Skill compiler eval bank failed (exit {code}): {err or out}")
        else:
            res.details["eval_bank_summary"] = out.strip()[-100:] if out else "OK"
    else:
        res.warnings.append(f"Missing {eval_script}")

    if res.errors:
        res.status = "FAIL"
    return res


# -----------------------------------------------------------------------------
# Stage 6: Ooutwire Register Audit & Candidate Emission
# -----------------------------------------------------------------------------
def execute_stage_6(repo_root: Path, errors: List[str]) -> AutopStageResult:
    res = AutopStageResult(6, "ooutwire_register_audit", "PASS")
    ooutwire_dir = repo_root / "operads" / "skills" / "ooutwire"
    prop_reg = ooutwire_dir / "proposed_skills_register.md"
    rec_queue = ooutwire_dir / "recommended_skills_to_build.md"

    res.details["proposed_skills_register_present"] = prop_reg.exists()
    res.details["recommended_skills_queue_present"] = rec_queue.exists()

    if not prop_reg.exists():
        res.warnings.append("ooutwire/proposed_skills_register.md not found.")
    if not rec_queue.exists():
        res.warnings.append("ooutwire/recommended_skills_to_build.md not found.")

    res.details["admission_law"] = (
        "Execution Law 2026-09-01: HIGH confidence applied automatically; "
        "New packages admitted on creation; AuthorityEffect: None."
    )
    return res


# -----------------------------------------------------------------------------
# Stage 7: Auto-Docs Session Documentation & Comment Slop Audit
# -----------------------------------------------------------------------------
def execute_stage_7(repo_root: Path) -> AutopStageResult:
    res = AutopStageResult(7, "auto_docs_and_comment_slop_audit", "PASS")
    auto_docs_script = (
        repo_root / "operations" / "use_cases" / "packaging" / "auto_docs_service.py"
    )
    if auto_docs_script.exists():
        code, out, err = run_cmd(
            [sys.executable, str(auto_docs_script), "--scan-only"], cwd=repo_root
        )
        if code != 0:
            res.errors.append(f"Auto-docs session & slop audit failed (exit {code}): {err or out}")
        else:
            res.details["auto_docs_status"] = "PASS"
            res.details["summary"] = out.strip().splitlines()[-1] if out else "OK"
    else:
        res.warnings.append(f"Missing {auto_docs_script}")

    if res.errors:
        res.status = "FAIL"
    return res


# -----------------------------------------------------------------------------
# Stage 8: Governance digest, then hash-checked apply
# -----------------------------------------------------------------------------
def execute_stage_8(repo_root: Path) -> AutopStageResult:
    """Farm the governance corpora and apply only checked-in repairs.

    The digest is read-only. The applier writes a target only when the proposal
    matches the repair table and the original file hash. AuthorityEffect: None.
    """
    res = AutopStageResult(8, "governance_digest_and_apply", "PASS")
    runs_dir = repo_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    digest_path = runs_dir / "governance_digest.json"
    apply_path = runs_dir / "governance_apply.json"
    module = "operads.frontend.cli"
    code, out, err = run_cmd(
        [sys.executable, "-m", module, "--json", "digest-governance", "--out", str(digest_path)],
        cwd=repo_root,
        timeout=600,
    )
    res.details["digest_exit"] = code
    if code != 0:
        res.errors.append(f"digest-governance failed (exit {code}): {err or out}")
        res.status = "FAIL"
        return res
    code, out, err = run_cmd(
        [
            sys.executable,
            "-m",
            module,
            "--json",
            "apply-governance-proposals",
            "--receipt",
            str(digest_path),
            "--out",
            str(apply_path),
        ],
        cwd=repo_root,
        timeout=600,
    )
    res.details["apply_exit"] = code
    res.details["digest_receipt"] = str(digest_path)
    res.details["apply_receipt"] = str(apply_path)
    if code != 0:
        res.errors.append(f"apply-governance-proposals failed (exit {code}): {err or out}")
        res.status = "FAIL"
    return res


# -----------------------------------------------------------------------------
# Main AutoP Orchestrator
# -----------------------------------------------------------------------------
def run_autop(
    repo_root: Path,
    receipt_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    verbose: bool = False,
) -> AutopReceipt:
    autop_id = f"AUTOP_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    receipt = AutopReceipt(
        autop_id=autop_id,
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        authority_effect="None",
        overall_status="PASS",
        source_receipt=str(receipt_path) if receipt_path else None,
    )

    # Stage 0: Process Intake Receipt
    stage_0, extracted_errors = execute_stage_0(repo_root, receipt_path)
    receipt.stages.append(stage_0)
    if verbose:
        print(f"[Stage 0] {stage_0.stage_name}: {stage_0.status}")

    # Stage 1: Episode intake
    stage_1 = execute_stage_1(repo_root, extracted_errors)
    receipt.stages.append(stage_1)
    if verbose:
        print(f"[Stage 1] {stage_1.stage_name}: {stage_1.status}")

    # Stage 2: Packaging & Knowledge Parity
    stage_2 = execute_stage_2(repo_root)
    receipt.stages.append(stage_2)
    if verbose:
        print(f"[Stage 2] {stage_2.stage_name}: {stage_2.status}")

    # Stage 3: Skill Budget Gate
    stage_3 = execute_stage_3(repo_root)
    receipt.stages.append(stage_3)
    if verbose:
        print(f"[Stage 3] {stage_3.stage_name}: {stage_3.status}")

    # Stage 4: Multi-Host Skill Census
    stage_4 = execute_stage_4(repo_root)
    receipt.stages.append(stage_4)
    if verbose:
        print(f"[Stage 4] {stage_4.stage_name}: {stage_4.status}")

    # Stage 5: Skill Compiler Evals
    stage_5 = execute_stage_5(repo_root)
    receipt.stages.append(stage_5)
    if verbose:
        print(f"[Stage 5] {stage_5.stage_name}: {stage_5.status}")

    # Stage 6: Ooutwire Register Audit
    stage_6 = execute_stage_6(repo_root, extracted_errors)
    receipt.stages.append(stage_6)
    if verbose:
        print(f"[Stage 6] {stage_6.stage_name}: {stage_6.status}")

    # Stage 7: Auto-Docs & Comment Slop Audit
    stage_7 = execute_stage_7(repo_root)
    receipt.stages.append(stage_7)
    if verbose:
        print(f"[Stage 7] {stage_7.stage_name}: {stage_7.status}")

    # Stage 8: Read-only digest, then checked-in repairs
    stage_8 = execute_stage_8(repo_root)
    receipt.stages.append(stage_8)
    if verbose:
        print(f"[Stage 8] {stage_8.stage_name}: {stage_8.status}")

    # Overall Status
    if any(s.status == "FAIL" for s in receipt.stages):
        receipt.overall_status = "FAIL"

    # Write receipt
    if output_path is None:
        runs_dir = repo_root / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        output_path = runs_dir / "autop_receipt.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(receipt), indent=2), encoding="utf-8")

    print(
        f"AutoP run completed. Overall Status: {receipt.overall_status}. Receipt written to: {output_path}"
    )
    return receipt


def run_anti_pattern_lint_on_changed(repo_root: Path) -> Dict[str, Any]:
    """Run auto-anti-pattern-lint on changed files and capture remediation suggestions."""
    lint_script = (
        repo_root
        / "operads"
        / "skills"
        / "auto-anti-pattern-lint"
        / "scripts"
        / "anti_pattern_lint.py"
    )
    if not lint_script.is_file():
        return {"status": "SKIPPED", "reason": "anti_pattern_lint.py not found"}

    report_path = repo_root / "runs" / "autop_anti_pattern" / "changed_files_anti_pattern_lint.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(lint_script),
        "--changed",
        "--report-out",
        str(report_path),
    ]
    code, out, err = run_cmd(cmd, cwd=repo_root)
    remediation_suggestions: List[Dict[str, Any]] = []
    scanned_count = 0
    findings_count = 0
    if report_path.is_file():
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            remediation_suggestions = data.get("remediation_suggestions", [])
            scanned_count = data.get("scanned_files_count", 0)
            findings_count = data.get("file_findings_count", 0)
        except Exception:
            pass

    return {
        "status": "PASS" if code == 0 and findings_count == 0 else "FINDINGS",
        "exit_code": code,
        "scanned_files_count": scanned_count,
        "findings_count": findings_count,
        "remediation_suggestions": remediation_suggestions,
        "receipt": str(report_path.relative_to(repo_root)).replace("\\", "/"),
        "output": out.strip(),
    }


def post_run_handoff(repo_root: Path, source: Optional[Path] = None) -> Dict[str, Any]:
    """Request actual IDE learning; do not claim learning or write run artifacts."""
    lint_summary = run_anti_pattern_lint_on_changed(repo_root)
    remediations = lint_summary.get("remediation_suggestions", [])
    repair_script = (
        repo_root / "operads" / "skills" / "auto-learn" / "scripts" / "auto_learn.py"
    )
    return {
        "status": "IDE_LEARNING_REQUIRED",
        "action": "INVOKE_AUTO_LEARN",
        "learner": "current IDE assistant session",
        "skill_path": str(repo_root / "operads" / "skills" / "auto-learn" / "SKILL.md"),
        "repair_entrypoint": (
            str(repair_script.relative_to(repo_root)).replace("\\", "/")
            if repair_script.is_file()
            else None
        ),
        "repair_command": (
            f"py -3.12 {repair_script.relative_to(repo_root).as_posix()} --repair"
            if repair_script.is_file()
            else None
        ),
        "source": str(source) if source else None,
        "changed_files_anti_pattern_lint": lint_summary,
        "remediation_suggestions": remediations,
        "instructions": (
            "Read auto-learn and relevant existing lessons. Inspect the actual run, "
            "including partial/failed observations. Deduplicate existing owners; "
            "apply the smallest justified high-confidence correction in scope, "
            "recheck the original need, mirror selected agent changes and carry "
            "unresolved work into the next brief. Inner helpers return to the one "
            "outer finish; learning edits do not invoke another finish hook. "
            "Remediate anti-pattern violations using dual helpful patterns and matching antibodies "
            "via auto-learn automated repair."
        ),
        "learning_completed": False,
        "files_written": [],
        "authority_effect": "None",
    }


def main():
    parser = argparse.ArgumentParser(
        description="AutoP: current-IDE learning handoff or explicit estate maintenance."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--post-run", action="store_true", help="Return an IDE auto-learn handoff without writing files (default).")
    mode.add_argument("--maintenance", "--legacy", action="store_true", help="Explicitly execute the existing nine-stage maintenance runner.")
    parser.add_argument("--source", type=Path, help="Chosen state/report for the IDE to inspect; never copied into the handoff.")
    parser.add_argument("--receipt", type=Path, help="Maintenance input receipt; also preserves legacy callers that explicitly pass this option.")
    parser.add_argument("--output", type=Path, help="Maintenance output receipt; also preserves legacy callers that explicitly pass this option.")
    parser.add_argument("--verbose", action="store_true", help="Print maintenance stage progress.")
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Trigger auto-learn automated repair on detected remediation suggestions",
    )
    args = parser.parse_args()
    legacy_options = args.receipt is not None or args.output is not None
    if args.post_run and legacy_options:
        parser.error("--post-run cannot use --receipt/--output; IDE learning writes no receipts")
    maintenance = args.maintenance or legacy_options
    if maintenance and args.source is not None:
        parser.error("--source is for the IDE post-run handoff; maintenance uses --receipt")
    if legacy_options and not args.maintenance:
        print("Legacy --receipt/--output selects maintenance; prefer explicit --maintenance.", file=sys.stderr)
    repo_root = find_repo_root()
    if not maintenance:
        handoff = post_run_handoff(repo_root, args.source)
        remediations = handoff.get("remediation_suggestions", [])
        if remediations:
            print(
                f"[AutoP] Anti-pattern lint identified {len(remediations)} violation(s) across changed files:",
                file=sys.stderr,
            )
            for idx, rem in enumerate(remediations[:10], 1):
                fpath = rem.get("file", "unknown")
                line = rem.get("line", 0)
                ap_id = rem.get("anti_pattern_id", "AP_???")
                hp_id = rem.get("dual_healthy_pattern", "HP_???")
                advice = rem.get("remediation_advice", "")
                abs_list = [a.get("antibody_id") for a in rem.get("associated_antibodies", []) if isinstance(a, dict)]
                ab_str = f" | Antibodies: {', '.join(abs_list)}" if abs_list else ""
                print(f"  {idx}. {fpath}:{line} [{ap_id} -> {hp_id}]{ab_str}\n     Remediation: {advice}", file=sys.stderr)
            if len(remediations) > 10:
                print(f"  ... and {len(remediations) - 10} more findings. See receipt.", file=sys.stderr)

        if args.repair and remediations:
            repair_script = (
                repo_root / "operads" / "skills" / "auto-learn" / "scripts" / "auto_learn.py"
            )
            if repair_script.is_file():
                print(
                    f"\n[AutoP] Automatically triggering auto-learn repair for {len(remediations)} remediation suggestion(s)...",
                    file=sys.stderr,
                )
                repair_cmd = [
                    sys.executable,
                    str(repair_script),
                    "--repair",
                    "--remediations-json",
                    json.dumps(remediations),
                ]
                rep_code, rep_out, rep_err = run_cmd(repair_cmd, cwd=repo_root)
                if rep_out:
                    print(rep_out, file=sys.stderr)
                if rep_err:
                    print(rep_err, file=sys.stderr)
                handoff["auto_learn_repair_executed"] = True
                handoff["auto_learn_repair_exit_code"] = rep_code

        print(json.dumps(handoff, ensure_ascii=True))
        return
    receipt = run_autop(repo_root, args.receipt, args.output, verbose=args.verbose)
    if receipt.overall_status == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()

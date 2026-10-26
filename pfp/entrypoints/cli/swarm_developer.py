"""Single Point of Entry (SPOE) Composite Swarm Developer CLI.

Coordinates teamwork-preview (Mode B), woland cognition, omega-old-man-red-team,
and deterministic host verification under mandatory governance-pfp invariants.

Exit codes:
  0: Completed and verified / persisted.
  2: Typed refusal (message on stderr).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shlex
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    try_resolve_intelligence_repo_root,
)
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

FORBIDDEN_HYPE_WORDS = [
    "proves",
    "guarantees",
    "mathematically verifies",
    "fundamentally",
    "true intelligence",
    "impossible",
    "universal",
    "flawless",
    "perfectly",
    "clearly",
    "obviously",
    "simply",
    "merely",
    "weaponized",
]


class CodeCheckoutUnresolved(Exception):
    """No .git checkout contains the working directory or this source file."""


def resolve_repo_root() -> Path:
    """Return the git checkout that contains this process or this source file.

    A linked worktree has its own top-level ``.git`` file. The intelligence-root
    helper points durable run folders at the main checkout and is not this root.
    """
    seeds = (Path.cwd(), Path(__file__).resolve())
    seen: set[Path] = set()
    for seed in seeds:
        for candidate in (seed, *seed.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            marker = candidate / ".git"
            if marker.is_file() or marker.is_dir():
                return candidate
    raise CodeCheckoutUnresolved(
        "no .git checkout contains the working directory or swarm_developer.py"
    )


def compute_file_sha256(path: Path) -> str:
    """Compute standard SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_governance_skill(repo_root: Path) -> Result[str, Refusal]:
    """Verify that governance-pfp exists and compute its SHA-256 digest."""
    gov_path = repo_root / "omega_engine_operads" / "skills" / "governance-pfp" / "SKILL.md"
    if not gov_path.is_file():
        return Err(
            Refusal(
                "SWARM_GOVERNANCE_MISSING",
                f"Mandatory governance skill missing: {gov_path}",
            )
        )
    return Ok(compute_file_sha256(gov_path))


def execute_pre_clean_harvest(repo_root: Path) -> Result[str, Refusal]:
    """Execute pre-clean harvest gate to seal ephemeral state into CAS vault."""
    try:
        from omega_engine_operads.frontend.cli.harvest_cli import run_harvest_cli

        ret = run_harvest_cli(["pre-clean-teamwork"])
        if ret != 0:
            return Err(
                Refusal(
                    "PRE_CLEAN_HARVEST_FAILED",
                    f"harvest_cli pre-clean-teamwork exited with code {ret}",
                )
            )
        return Ok("PRE_CLEAN_HARVEST_OK")
    except Exception as exc:
        return Err(
            Refusal(
                "PRE_CLEAN_HARVEST_EXCEPTION",
                f"Harvest gate execution raised: {exc}",
            )
        )


def load_task_contract(contract_path: Path) -> Result[dict[str, Any], Refusal]:
    """Load and validate SwarmTaskContractV1 JSON or YAML."""
    if not contract_path.is_file():
        return Err(
            Refusal(
                "CONTRACT_NOT_FOUND",
                f"Task contract file does not exist: {contract_path}",
            )
        )
    text = contract_path.read_text(encoding="utf-8")
    try:
        if contract_path.suffix in {".yaml", ".yml"}:
            import yaml

            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except Exception as exc:
        return Err(
            Refusal(
                "CONTRACT_PARSE_ERROR",
                f"Failed to parse task contract: {exc}",
            )
        )

    if not isinstance(data, dict):
        return Err(
            Refusal("CONTRACT_INVALID_TYPE", "Task contract must be a dictionary/mapping")
        )

    version = data.get("contract_version") or data.get("version")
    if version != "SwarmTaskContractV1":
        return Err(
            Refusal(
                "UNSUPPORTED_CONTRACT_VERSION",
                f"Expected SwarmTaskContractV1, got: {version}",
            )
        )

    return Ok(data)


def audit_candidate_claim_hygiene(text: str) -> list[str]:
    """Scan text for forbidden ungrounded hype verbs."""
    lowered = text.lower()
    violations = []
    for word in FORBIDDEN_HYPE_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        if re.search(pattern, lowered):
            violations.append(word)
    return violations


def audit_clean_architecture_boundaries(source_path: Path) -> list[str]:
    """Audit source files in domain/ for outer-layer imports."""
    violations = []
    if "domain" not in source_path.parts:
        return violations
    try:
        content = source_path.read_text(encoding="utf-8")
    except Exception:
        return violations

    forbidden_layers = {
        "use_cases",
        "infrastructure",
        "controllers",
        "frontend",
        "entrypoints",
    }
    for line_idx, line in enumerate(content.splitlines(), start=1):
        clean_line = line.strip()
        if not clean_line.startswith(("import ", "from ")):
            continue
        tokens = clean_line.split()
        if not tokens or len(tokens) < 2:
            continue
        mod = tokens[1]
        segments = mod.split(".")
        for forbidden in forbidden_layers:
            if any(seg == forbidden or seg.endswith(f"_{forbidden}") for seg in segments):
                violations.append(
                    f"{source_path}:{line_idx} domain imports outer layer {forbidden}"
                )
    return violations


def is_claim_hygiene_scanner_or_test(path: Path) -> bool:
    """Return True if path is a rule definition, claim scanner, or scanner test."""
    p_str = path.as_posix().lower()
    if "rl_" in path.name or "/rules/" in p_str:
        return True
    if path.name in {"swarm_developer.py", "test_swarm_developer.py"}:
        return True
    if "claim_hygiene" in p_str or "red_team" in p_str or "fireproof" in p_str:
        return True
    return False


def execute_fireproof_audit(
    target_path: Path,
    profile: str,
    repo_root: Path,
) -> tuple[list[dict[str, Any]], bool]:
    """Execute read-only Old Man fireproof audit against candidate files.

    Returns:
      (findings, has_blocking)
    """
    findings: list[dict[str, Any]] = []
    has_blocking = False

    ignored_dir_names = {
        ".git",
        ".venv",
        ".worktrees",
        "target",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "dist",
        "build",
    }

    paths_to_audit: list[Path] = []
    if target_path.is_file():
        paths_to_audit.append(target_path)
    elif target_path.is_dir():
        for ext in ["*.py", "*.md", "*.rs", "*.json"]:
            for candidate in target_path.rglob(ext):
                if any(part in ignored_dir_names for part in candidate.parts):
                    continue
                try:
                    if candidate.stat().st_size > 1_000_000:
                        continue
                except OSError:
                    continue
                paths_to_audit.append(candidate)

    for p in paths_to_audit:
        try:
            rel = p.relative_to(repo_root)
        except ValueError:
            rel = p
        content = p.read_text(encoding="utf-8", errors="ignore")

        # 1. Clean architecture check for python domain modules
        if p.suffix == ".py":
            ca_violations = audit_clean_architecture_boundaries(p)
            for viol in ca_violations:
                finding = {
                    "finding_id": f"OMC-CA-{len(findings) + 1:03d}",
                    "target_file": str(rel),
                    "claim_id": "CLEAN_ARCHITECTURE_INWARD_PURITY",
                    "gate": "architecture_boundary",
                    "severity": "BLOCKER",
                    "blocking": True,
                    "counterexample": viol,
                    "required_repair": "Relocate outer dependencies to domain ports/interfaces",
                }
                findings.append(finding)
                has_blocking = True

        # 2. Claim hygiene audit for markdown, docstrings, or papers
        if p.suffix in {".md", ".py"}:
            if not is_claim_hygiene_scanner_or_test(p):
                hype_words = audit_candidate_claim_hygiene(content)
                if hype_words:
                    finding = {
                        "finding_id": f"OMC-HYP-{len(findings) + 1:03d}",
                        "target_file": str(rel),
                        "claim_id": "CLAIM_HYGIENE_DISCIPLINE",
                        "gate": "claim_hygiene",
                        "severity": "BLOCKER" if profile in {"natural_science", "paper_release"} else "MAJOR",
                        "blocking": profile in {"natural_science", "paper_release"},
                        "counterexample": f"Forbidden hype vocabulary detected: {', '.join(hype_words)}",
                        "required_repair": "Replace with narrow claim defaults ('supports', 'shows in this setting')",
                    }
                    findings.append(finding)
                    if finding["blocking"]:
                        has_blocking = True

    return findings, has_blocking


def run_verifier_routes(
    routes: Sequence[str], repo_root: Path
) -> tuple[list[dict[str, Any]], bool]:
    """Execute declared verifier routes (targeted test commands)."""
    receipts: list[dict[str, Any]] = []
    all_passed = True

    for cmd_str in routes:
        cmd_tokens = shlex.split(cmd_str, posix=sys.platform != "win32")
        # Ensure Windows python launcher compatibility
        if cmd_tokens and cmd_tokens[0] in {"python", "py", "pytest"}:
            if cmd_tokens[0] == "pytest":
                cmd_tokens = [sys.executable, "-m", "pytest"] + cmd_tokens[1:]
            elif cmd_tokens[0] in {"python", "py"}:
                # Use current running python interpreter for fidelity
                if len(cmd_tokens) > 1 and re.match(r"^-3(\.\d+)?$", cmd_tokens[1]):
                    cmd_tokens = [sys.executable] + cmd_tokens[2:]
                else:
                    cmd_tokens = [sys.executable] + cmd_tokens[1:]

        try:
            res = subprocess.run(
                cmd_tokens,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            passed = res.returncode == 0
            receipt = {
                "command": cmd_str,
                "exit_code": res.returncode,
                "passed": passed,
                "stdout_sample": res.stdout[-400:] if res.stdout else "",
                "stderr_sample": res.stderr[-400:] if res.stderr else "",
            }
            receipts.append(receipt)
            if not passed:
                all_passed = False
        except subprocess.TimeoutExpired as exc:
            receipts.append(
                {
                    "command": cmd_str,
                    "exit_code": -1,
                    "passed": False,
                    "error": f"Timeout expired after {exc.timeout}s",
                }
            )
            all_passed = False
        except Exception as exc:
            receipts.append(
                {
                    "command": cmd_str,
                    "exit_code": -1,
                    "passed": False,
                    "error": str(exc),
                }
            )
            all_passed = False

    return receipts, all_passed


def trigger_autop_repair(
    repo_root: Path,
    contract: dict[str, Any],
    verifier_receipts: list[dict[str, Any]],
    audit_findings: list[dict[str, Any]],
    round_num: int,
    output_receipt_path: Path | None = None,
) -> Result[Path, Refusal]:
    """Trigger the auto-oe-autop meta-pipeline with failure receipt data."""
    candidate_scripts = [
        repo_root / "omega_engine_operads" / "skills" / "auto-oe-autop" / "scripts" / "orchestrate_autop.py",
        Path(__file__).resolve().parents[3] / "omega_engine_operads" / "skills" / "auto-oe-autop" / "scripts" / "orchestrate_autop.py",
    ]
    autop_script = next((s for s in candidate_scripts if s.is_file()), None)
    if autop_script is None:
        return Err(
            Refusal(
                "AUTOP_SCRIPT_MISSING",
                f"AutoP orchestrator script missing: {candidate_scripts[0]}",
            )
        )

    intake_dir = repo_root / "runs" / "autop_intake"
    intake_dir.mkdir(parents=True, exist_ok=True)
    task_id = contract.get("contract_id", "SWARM-TASK")
    intake_path = intake_dir / f"intake_{task_id}_r{round_num}.json"

    errors = [
        f"{r.get('command')}: exit {r.get('exit_code')}"
        + (f" ({r.get('error')})" if r.get("error") else "")
        + (f" stderr: {r.get('stderr_sample', '').strip()}" if r.get("stderr_sample") else "")
        for r in verifier_receipts
        if not r.get("passed")
    ]
    blockers = [
        f"{f.get('target_file')}: [{f.get('claim_id')}] {f.get('counterexample')}"
        for f in audit_findings
        if f.get("blocking")
    ]

    intake_payload = {
        "authority_effect": "None",
        "contract_id": task_id,
        "audit_id": f"WOLAND-REPAIR-{task_id}-R{round_num}",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "errors": errors,
        "decisive_blockers": blockers,
        "checks": {
            "verifier_routes": "PASS" if not errors else "FAIL",
            "fireproof_audit": "PASS" if not blockers else "FAIL",
        },
        "target_paths": (
            contract.get("target_paths")
            or contract.get("candidate_paths")
            or contract.get("allowed_paths", [])
        ),
    }

    intake_path.write_text(json.dumps(intake_payload, indent=2), encoding="utf-8")

    out_path = output_receipt_path or (repo_root / "runs" / "autop_receipt.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(autop_script),
        "--receipt",
        str(intake_path),
        "--output",
        str(out_path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if out_path.is_file():
            return Ok(out_path)
        return Err(
            Refusal(
                "AUTOP_EXECUTION_FAILED",
                f"AutoP exited {proc.returncode} without writing receipt: {proc.stderr[:400]}",
            )
        )
    except subprocess.TimeoutExpired as exc:
        return Err(
            Refusal(
                "AUTOP_TIMEOUT",
                f"AutoP timed out after {exc.timeout}s",
            )
        )
    except Exception as exc:
        return Err(
            Refusal(
                "AUTOP_EXECUTION_EXCEPTION",
                f"AutoP execution raised: {exc}",
            )
        )


def emit_structurebench_quad_bundle(
    output_dir: Path,
    contract: dict[str, Any],
    verifier_receipts: list[dict[str, Any]],
    audit_findings: list[dict[str, Any]],
    disposition: str,
    terminal_status: str,
    autop_receipts: list[dict[str, Any]] | None = None,
) -> Path:
    """Emit the StructureBench quad artifacts and SwarmEvidenceEnvelopeV1."""
    output_dir.mkdir(parents=True, exist_ok=True)
    task_id = contract.get("contract_id", "SWARM-TASK")
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    autop_list = autop_receipts or []

    # 1. novella.md
    novella_path = output_dir / "novella.md"
    novella_content = (
        f"# Swarm Novella: {task_id}\n\n"
        f"**Timestamp:** `{timestamp}`  \n"
        f"**Objective:** {contract.get('task_objective', 'N/A')}  \n"
        f"**Terminal Status:** `{terminal_status}`  \n"
        f"**Woland Disposition:** `{disposition}`  \n\n"
        f"## Scene 1: Task Contract Ingestion\n"
        f"Loaded and verified contract `{contract.get('contract_id')}`.\n"
        f"Allowed paths: {contract.get('allowed_paths', [])}\n\n"
        f"## Scene 2: Deterministic Verification\n"
        f"Executed {len(verifier_receipts)} verifier routes.\n\n"
        f"## Scene 3: Old Man Fireproof Audit\n"
        f"Audited candidate against profile `{contract.get('audit_profile', 'software')}`. "
        f"Findings count: {len(audit_findings)}.\n\n"
        f"## Scene 4: Reality Gate Verdict\n"
        f"Woland evaluated evidence and emitted `{disposition}`.\n"
    )
    if autop_list:
        novella_content += (
            f"\n## Scene 5: Autopoietic Repair Pipeline\n"
            f"AutoP triggered with {len(autop_list)} execution run receipts.\n"
        )
    novella_path.write_text(novella_content, encoding="utf-8")

    # 2. dda_actions.jsonl
    dda_path = output_dir / "dda_actions.jsonl"
    actions = [
        {"action": "INGEST_CONTRACT", "letter": "I", "step": 1, "task_id": task_id, "timestamp": timestamp},
        {"action": "DISPATCH_HOST_TESTS", "letter": "E", "step": 2, "task_id": task_id, "timestamp": timestamp},
        {"action": "OLD_MAN_AUDIT", "letter": "C", "step": 3, "task_id": task_id, "timestamp": timestamp},
        {"action": "WOLAND_TERMINAL_GATE", "letter": "T", "step": 4, "task_id": task_id, "timestamp": timestamp},
    ]
    with dda_path.open("w", encoding="utf-8") as f:
        for a in actions:
            f.write(json.dumps(a, sort_keys=True) + "\n")

    # 3. summary.json
    summary_path = output_dir / "summary.json"
    summary_data = {
        "authority_effect": "None",
        "contract_id": task_id,
        "disposition": disposition,
        "terminal_status": terminal_status,
        "timestamp": timestamp,
        "total_audit_findings": len(audit_findings),
        "total_autop_runs": len(autop_list),
        "total_verifier_routes": len(verifier_receipts),
    }
    summary_path.write_text(json.dumps(summary_data, indent=2, sort_keys=True), encoding="utf-8")

    # 4. receipt.json
    receipt_path = output_dir / "receipt.json"
    artifact_hashes = {
        "dda_actions.jsonl": compute_file_sha256(dda_path),
        "novella.md": compute_file_sha256(novella_path),
        "summary.json": compute_file_sha256(summary_path),
    }
    receipt_data = {
        "artifact_hashes": artifact_hashes,
        "authority_effect": "None",
        "contract_id": task_id,
        "disposition": disposition,
        "receipt_version": "StructureBenchQuadV1",
        "terminal_status": terminal_status,
        "timestamp": timestamp,
    }
    receipt_path.write_text(json.dumps(receipt_data, indent=2, sort_keys=True), encoding="utf-8")

    # 5. evidence_envelope.json (SwarmEvidenceEnvelopeV1)
    envelope_path = output_dir / "evidence_envelope.json"
    envelope_data = {
        "authority_effect": "None",
        "claim_hygiene": {
            "does_not_support": "Does not support unverified universal proofs, ungrounded general claims, or whole-suite test sweeps.",
            "narrowest_defensible_claim": f"Task {task_id} executed against declared acceptance predicates with disposition {disposition} under local test verification.",
            "next_test_needed": "Independent peer audit and integration into live estate release gates.",
            "supports": f"Supports deterministic local execution and verification of task objective: {contract.get('task_objective', '')}.",
        },
        "contract_id": task_id,
        "evidence": {
            "audit_findings": audit_findings,
            "autop_receipts": autop_list,
            "quad_hashes": artifact_hashes,
            "verifier_receipts": verifier_receipts,
        },
        "executor_stack": [
            "teamwork-preview",
            "woland",
            "omega-old-man-red-team",
            "deterministic-host",
            "human-principal",
        ],
        "governance_terminal": terminal_status,
        "local_dispositions": {
            "old_man": "BLOCKER" if any(f.get("blocking") for f in audit_findings) else "GO",
            "woland": disposition,
        },
        "run_id": output_dir.name,
        "timestamp": timestamp,
    }
    envelope_path.write_text(json.dumps(envelope_data, indent=2, sort_keys=True), encoding="utf-8")
    return envelope_path


def cmd_validate_contract(args: argparse.Namespace) -> int:
    """Validate a SwarmTaskContractV1 file."""
    try:
        repo_root = resolve_repo_root()
    except CodeCheckoutUnresolved as exc:
        sys.stderr.write(f"REFUSED: CODE_CHECKOUT_UNRESOLVED: {exc}\n")
        return 2
    gov_res = verify_governance_skill(repo_root)
    if isinstance(gov_res, Err):
        sys.stderr.write(f"REFUSED: {gov_res.error.code}: {gov_res.error.message}\n")
        return 2

    contract_path = Path(args.contract)
    if not contract_path.is_file() and (repo_root / contract_path).is_file():
        contract_path = repo_root / contract_path

    contract_res = load_task_contract(contract_path)
    if isinstance(contract_res, Err):
        sys.stderr.write(f"REFUSED: {contract_res.error.code}: {contract_res.error.message}\n")
        return 2

    contract = contract_res.value
    gov_digest = gov_res.value

    # Validate declared governance digest if present
    declared_gov = contract.get("governance_precondition", {}).get("sha256")
    if declared_gov and declared_gov != gov_digest:
        sys.stderr.write(
            f"REFUSED: GOVERNANCE_DIGEST_MISMATCH: expected {declared_gov}, got {gov_digest}\n"
        )
        return 2

    print(f"Contract {contract.get('contract_id')} validated successfully.")
    print(f"  Objective: {contract.get('task_objective')}")
    print(f"  Allowed Paths: {len(contract.get('allowed_paths', []))}")
    print(f"  Protected Paths: {len(contract.get('protected_paths', []))}")
    print(f"  Verifier Routes: {len(contract.get('verifier_routes', []))}")
    print(f"  Governance Digest: {gov_digest[:16]}...")
    return 0


def cmd_fireproof_audit(args: argparse.Namespace) -> int:
    """Execute standalone Old Man fireproof audit."""
    try:
        repo_root = resolve_repo_root()
    except CodeCheckoutUnresolved as exc:
        sys.stderr.write(f"REFUSED: CODE_CHECKOUT_UNRESOLVED: {exc}\n")
        return 2
    profile = args.profile or "software"

    if getattr(args, "contract", None):
        contract_path = Path(args.contract)
        if not contract_path.is_file() and (repo_root / contract_path).is_file():
            contract_path = repo_root / contract_path
        contract_res = load_task_contract(contract_path)
        if isinstance(contract_res, Err):
            sys.stderr.write(f"REFUSED: {contract_res.error.code}: {contract_res.error.message}\n")
            return 2
        contract = contract_res.value
        targets = (
            contract.get("target_paths")
            or contract.get("candidate_paths")
            or contract.get("allowed_paths", [])
        )
        findings = []
        has_blocking = False
        profile = args.profile or contract.get("audit_profile", profile)
        for rel_str in targets:
            tp = repo_root / rel_str
            if tp.exists():
                f_list, blocking = execute_fireproof_audit(tp, profile, repo_root)
                findings.extend(f_list)
                if blocking:
                    has_blocking = True
    else:
        target_path = Path(args.patch) if args.patch else (Path(args.target) if hasattr(args, "target") and args.target else repo_root)
        findings, has_blocking = execute_fireproof_audit(target_path, profile, repo_root)

    report_out = Path(args.report_out) if getattr(args, "report_out", None) else None
    if report_out is not None:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        with report_out.open("w", encoding="utf-8") as f:
            for item in findings:
                f.write(json.dumps(item, sort_keys=True) + "\n")
        print(f"Report written to {report_out}")

    print(f"Old Man Audit completed: {len(findings)} findings (has_blocking={has_blocking}).")
    if has_blocking:
        sys.stderr.write("REFUSED: Blocking audit findings encountered.\n")
        return 2
    return 0


def cmd_run_swarm(args: argparse.Namespace) -> int:
    """Execute the full composite developer swarm turn (SPOE entrypoint)."""
    try:
        repo_root = resolve_repo_root()
    except CodeCheckoutUnresolved as exc:
        sys.stderr.write(f"REFUSED: CODE_CHECKOUT_UNRESOLVED: {exc}\n")
        return 2

    # Step 0: Pre-clean harvest gate
    if not getattr(args, "skip_harvest", False):
        harvest_res = execute_pre_clean_harvest(repo_root)
        if isinstance(harvest_res, Err):
            sys.stderr.write(f"REFUSED: {harvest_res.error.code}: {harvest_res.error.message}\n")
            return 2

    # Step 1: Governance skill verification (fail-closed)
    gov_res = verify_governance_skill(repo_root)
    if isinstance(gov_res, Err):
        sys.stderr.write(f"REFUSED: {gov_res.error.code}: {gov_res.error.message}\n")
        return 2
    gov_digest = gov_res.value

    # Step 2: Load and validate SwarmTaskContractV1
    contract_path = Path(args.contract)
    if not contract_path.is_file() and (repo_root / contract_path).is_file():
        contract_path = repo_root / contract_path

    contract_res = load_task_contract(contract_path)
    if isinstance(contract_res, Err):
        sys.stderr.write(f"REFUSED: {contract_res.error.code}: {contract_res.error.message}\n")
        return 2
    contract = contract_res.value

    # Assert governance skill digest match if contract declares expected digest
    declared_gov = contract.get("governance_precondition", {}).get("sha256")
    if declared_gov and declared_gov != gov_digest:
        sys.stderr.write(
            f"REFUSED: GOVERNANCE_DIGEST_MISMATCH: expected {declared_gov}, got {gov_digest}\n"
        )
        return 2

    max_rounds = max(1, getattr(args, "max_rounds", 3))
    verifier_receipts: list[dict[str, Any]] = []
    audit_findings: list[dict[str, Any]] = []
    autop_receipts: list[dict[str, Any]] = []
    tests_passed = False
    has_blocking = False

    for _round_num in range(1, max_rounds + 1):
        # Step 3: Run deterministic host verification routes
        routes = contract.get("verifier_routes", [])
        verifier_receipts, tests_passed = run_verifier_routes(routes, repo_root)

        # Step 4: Run Old Man fireproof audit on candidate target paths
        target_paths = (
            contract.get("target_paths")
            or contract.get("candidate_paths")
            or contract.get("allowed_paths", [])
        )
        profile = args.audit_profile or contract.get("audit_profile", "software")
        audit_findings = []
        has_blocking = False

        for rel_str in target_paths:
            target_p = repo_root / rel_str
            if target_p.exists():
                f_list, blocking = execute_fireproof_audit(target_p, profile, repo_root)
                audit_findings.extend(f_list)
                if blocking:
                    has_blocking = True

        if tests_passed and not has_blocking:
            break

        # Step 4.5: Auto-repair loop via AutoP if round failed and --auto-repair is set
        if getattr(args, "auto_repair", False):
            autop_out_arg = getattr(args, "autop_output", None)
            autop_res = trigger_autop_repair(
                repo_root=repo_root,
                contract=contract,
                verifier_receipts=verifier_receipts,
                audit_findings=audit_findings,
                round_num=_round_num,
                output_receipt_path=Path(autop_out_arg) if autop_out_arg else None,
            )
            if isinstance(autop_res, Ok):
                try:
                    autop_data = json.loads(autop_res.value.read_text(encoding="utf-8"))
                    autop_receipts.append(autop_data)
                except Exception:
                    pass

        # In standalone Mode B CLI execution without an active builder mutator,
        # one deterministic evaluation round determines the verdict unless auto-repair is enabled.
        if _round_num >= max_rounds or not getattr(args, "auto_repair", False):
            break

    # Step 5: Woland terminal disposition
    if not tests_passed:
        disposition = "REFUSE"
        terminal_status = "Refused"
    elif has_blocking:
        disposition = "REFUSE"
        terminal_status = "BlockedByEvidence"
    else:
        disposition = "PASS_TO_MASTER"
        terminal_status = "Verified"

    # Step 6: Output custody & evidence envelope emission
    if getattr(args, "output_dir", None):
        output_dir = Path(args.output_dir)
    else:
        durable = try_resolve_intelligence_repo_root(Path.cwd())
        if isinstance(durable, Err):
            sys.stderr.write(f"REFUSED: {durable.error.code}: {durable.error.message}\n")
            return 2
        if not isinstance(durable, Ok):
            sys.stderr.write(
                "REFUSED: INTELLIGENCE_ROOT_UNRESOLVED: "
                "intelligence root helper returned an unexpected value\n"
            )
            return 2
        output_dir = (
            intelligence_path(durable.value, "_intelligence/swarm")
            / f"run_{contract.get('contract_id', 'task')}"
        )
    envelope_path = emit_structurebench_quad_bundle(
        output_dir=output_dir,
        contract=contract,
        verifier_receipts=verifier_receipts,
        audit_findings=audit_findings,
        disposition=disposition,
        terminal_status=terminal_status,
        autop_receipts=autop_receipts,
    )

    print(f"Swarm turn executed. Disposition: {disposition}, Terminal: {terminal_status}")
    print(f"Evidence envelope written to: {envelope_path}")

    if disposition == "REFUSE":
        sys.stderr.write(f"REFUSED: Swarm concluded in {terminal_status}\n")
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for swarm_developer."""
    parser = argparse.ArgumentParser(
        prog="swarm_developer",
        description="SPOE Composite Swarm Developer CLI for Omega Engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # 1. run-swarm
    p_run = sub.add_parser("run-swarm", help="Run full composite developer swarm turn")
    p_run.add_argument("--contract", required=True, help="Path to SwarmTaskContractV1 (JSON/YAML)")
    p_run.add_argument(
        "--audit-profile",
        choices=["software", "mathematics", "natural_science", "paper_release", "formal_proof"],
        default=None,
        help="Audit profile override",
    )
    p_run.add_argument("--output-dir", default=None, help="Directory to emit evidence envelope and quad bundle")
    p_run.add_argument("--skip-harvest", action="store_true", help="Skip pre-clean harvest gate")
    p_run.add_argument("--max-rounds", type=int, default=3, help="Maximum repair rounds (default: 3)")
    p_run.add_argument("--auto-repair", action="store_true", help="Enable autonomous repair loop")
    p_run.add_argument(
        "--autop-output",
        default=None,
        help="Explicit path to output AutoP JSON receipt (default: runs/autop_receipt.json)",
    )
    p_run.set_defaults(func=cmd_run_swarm)

    # 2. fireproof-audit
    p_audit = sub.add_parser("fireproof-audit", help="Run standalone Old Man fireproof audit")
    p_audit.add_argument("--contract", default=None, help="Path to SwarmTaskContractV1 to audit declared target paths")
    p_audit.add_argument("--patch", default=None, help="Candidate patch or directory to audit")
    p_audit.add_argument("--target", default=None, help="Target file or directory to audit")
    p_audit.add_argument(
        "--profile",
        choices=["software", "mathematics", "natural_science", "paper_release", "formal_proof"],
        default="software",
        help="Audit profile",
    )
    p_audit.add_argument("--report-out", default=None, help="Path to emit JSONL findings")
    p_audit.set_defaults(func=cmd_fireproof_audit)

    # 3. validate-contract
    p_val = sub.add_parser("validate-contract", help="Validate SwarmTaskContractV1 schema and governance")
    p_val.add_argument("--contract", required=True, help="Path to contract file")
    p_val.set_defaults(func=cmd_validate_contract)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

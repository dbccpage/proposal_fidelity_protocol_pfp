"""External Diff & Test Execution Oracle for Woland candidate checking.

Inspects candidate code edits against a base source module:
1. Computes unified diff against base module.
2. Performs AST syntax verification and static invariant checks (e.g. ZERO-FLOAT law).
3. Executes isolated external test runner (pytest) against candidate patch.
4. Generates deterministic, content-addressed receipt bound to exact candidate bytes.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Ok, Refusal, Result
from omega_engine_woland.domain.evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    sha256_ref,
)

_LOCUS = "omega_engine_woland.infrastructure.diff_oracle"


@dataclass
class DiffOracleInspectionRecordV1:
    """Inspection record capturing diff, ast, and test runner outputs."""

    candidate_id: str
    diff_text: str
    diff_sha256: str
    ast_valid: bool
    test_exit_code: int
    test_stdout: str
    test_stderr: str
    verdict: CheckerVerdict
    reason: str
    receipt_bytes: bytes


class DiffOracleCandidateChecker:
    """Exact external oracle inspecting candidate code edits and their diffs."""

    def __init__(
        self,
        *,
        checker_id: str = "external_diff_oracle",
        enforce_zero_float: bool = True,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.checker_id = checker_id
        self.enforce_zero_float = enforce_zero_float
        self.timeout_seconds = timeout_seconds
        self.inspection_history: dict[str, DiffOracleInspectionRecordV1] = {}

    def check_candidate(
        self,
        *,
        run_key: str,
        objective: str,
        candidate_id: str,
        candidate_bytes: bytes,
        carrier_context: Mapping[str, Any] | None,
    ) -> Result[CandidateCheckV1, Refusal]:
        del objective
        content_digest = sha256_ref(candidate_bytes)
        candidate_text = candidate_bytes.decode("utf-8", errors="replace")

        # Extract carrier context configuration
        ctx = carrier_context or {}
        base_file_raw = ctx.get("base_file_path")
        test_file_raw = ctx.get("test_file_path")
        workspace_raw = ctx.get("workspace_dir")

        base_path = Path(base_file_raw).resolve() if base_file_raw else None
        test_path = Path(test_file_raw).resolve() if test_file_raw else None
        workspace_path = Path(workspace_raw).resolve() if workspace_raw else (base_path.parent.parent if base_path else None)

        base_text = base_path.read_text(encoding="utf-8") if base_path and base_path.is_file() else ""
        base_sha256 = sha256_ref(base_text.encode("utf-8")) if base_text else sha256_ref(b"")

        # Step 1: Compute unified diff against base module
        diff_lines = list(
            difflib.unified_diff(
                base_text.splitlines(keepends=True),
                candidate_text.splitlines(keepends=True),
                fromfile=f"a/{base_path.name if base_path else 'base.py'}",
                tofile=f"b/{base_path.name if base_path else 'candidate.py'}",
            )
        )
        diff_text = "".join(diff_lines)
        diff_digest = sha256_ref(diff_text.encode("utf-8"))

        # Step 2: AST Syntax and Static Invariant Inspection
        ast_valid = True
        static_violation = ""
        try:
            tree = ast.parse(candidate_text)
            if self.enforce_zero_float:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, float):
                        ast_valid = False
                        static_violation = (
                            f"ZERO_FLOAT_LAW_VIOLATION: float literal {node.value} at line {node.lineno}"
                        )
                        break
        except SyntaxError as syn_err:
            ast_valid = False
            static_violation = f"SyntaxError: {syn_err.msg} at line {syn_err.lineno}"
        except Exception as exc:
            ast_valid = False
            static_violation = f"AST_INSPECTION_FAILED: {exc}"

        if not ast_valid:
            verdict = CheckerVerdict.REJECTED
            reason = static_violation
            receipt_dict = {
                "schema_version": "omega.woland.diff-oracle-check.v1",
                "authority_effect": "None",
                "run_key": run_key,
                "candidate_id": candidate_id,
                "candidate_content_sha256": content_digest,
                "base_file_sha256": base_sha256,
                "diff_sha256": diff_digest,
                "checker_id": self.checker_id,
                "verdict": verdict.value,
                "ast_valid": False,
                "test_exit_code": -1,
                "test_stdout": "",
                "test_stderr": static_violation,
                "reason": reason,
            }
            raw_receipt = json.dumps(receipt_dict, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            record = DiffOracleInspectionRecordV1(
                candidate_id=candidate_id,
                diff_text=diff_text,
                diff_sha256=diff_digest,
                ast_valid=False,
                test_exit_code=-1,
                test_stdout="",
                test_stderr=static_violation,
                verdict=verdict,
                reason=reason,
                receipt_bytes=raw_receipt,
            )
            self.inspection_history[candidate_id] = record
            return Ok(
                CandidateCheckV1(
                    verdict=verdict,
                    candidate_id=candidate_id,
                    candidate_content_sha256=content_digest,
                    checker_id=self.checker_id,
                    checker_receipt_sha256=sha256_ref(raw_receipt),
                    checker_receipt_bytes=raw_receipt,
                    reason=reason,
                )
            )

        # Step 3: Isolated External Test Runner Execution
        if not test_path or not test_path.is_file():
            verdict = CheckerVerdict.NOT_MEASURED
            reason = "No valid test file configured in carrier context."
            return Ok(
                CandidateCheckV1(
                    verdict=verdict,
                    candidate_id=candidate_id,
                    candidate_content_sha256=content_digest,
                    checker_id=self.checker_id,
                    reason=reason,
                )
            )

        # Set up hermetic execution tempdir
        with tempfile.TemporaryDirectory(prefix="woland_oracle_") as tmp_dir:
            temp_root = Path(tmp_dir)
            # If workspace is defined, copy workspace structure
            if workspace_path and workspace_path.is_dir():
                target_copy_dir = temp_root / workspace_path.name
                shutil.copytree(workspace_path, target_copy_dir, dirs_exist_ok=True)
                # Overwrite base file in copy with candidate text
                rel_base = base_path.relative_to(workspace_path)
                cand_target = target_copy_dir / rel_base
                cand_target.write_text(candidate_text, encoding="utf-8")
                test_run_target = target_copy_dir / test_path.relative_to(workspace_path)
                cwd = str(target_copy_dir)
                target_test_str = str(test_run_target)
            else:
                target_domain = temp_root / "domain"
                target_domain.mkdir(parents=True, exist_ok=True)
                (target_domain / "__init__.py").write_text("", encoding="utf-8")
                cand_target = target_domain / (base_path.name if base_path else "target.py")
                cand_target.write_text(candidate_text, encoding="utf-8")

                target_tests = temp_root / "tests"
                target_tests.mkdir(parents=True, exist_ok=True)
                (target_tests / "__init__.py").write_text("", encoding="utf-8")
                test_target = target_tests / test_path.name
                test_target.write_text(test_path.read_text(encoding="utf-8"), encoding="utf-8")
                cwd = str(temp_root)
                target_test_str = str(test_target)

            env = os.environ.copy()
            env["PYTHONPATH"] = f"{cwd}{os.pathsep}{env.get('PYTHONPATH', '')}"

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                target_test_str,
                "-v",
                "-o",
                "addopts=",
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
                exit_code = proc.returncode
                stdout_text = proc.stdout
                stderr_text = proc.stderr
            except subprocess.TimeoutExpired:
                exit_code = 124
                stdout_text = ""
                stderr_text = f"Test execution timed out after {self.timeout_seconds} seconds"
            except Exception as run_err:
                exit_code = 1
                stdout_text = ""
                stderr_text = f"Execution error: {run_err}"

        # Evaluate verdict based on test outcome
        if exit_code == 0:
            verdict = CheckerVerdict.ACCEPTED
            reason = "All oracle tests passed successfully."
        else:
            verdict = CheckerVerdict.REJECTED
            # Extract key failure line
            lines = [line.strip() for line in (stdout_text + "\n" + stderr_text).splitlines() if line.strip()]
            failures = [
                line
                for line in lines
                if any(
                    k in line
                    for k in (
                        "FAILED",
                        "Error",
                        "AssertionError",
                        "Failed:",
                        "DID NOT RAISE",
                        "Violation",
                    )
                )
            ]
            reason = f"Test suite failed (exit {exit_code}): " + ("; ".join(failures[-3:]) if failures else "Non-zero exit")

        receipt_dict = {
            "schema_version": "omega.woland.diff-oracle-check.v1",
            "authority_effect": "None",
            "run_key": run_key,
            "candidate_id": candidate_id,
            "candidate_content_sha256": content_digest,
            "base_file_sha256": base_sha256,
            "diff_sha256": diff_digest,
            "diff_line_count": len(diff_lines),
            "checker_id": self.checker_id,
            "verdict": verdict.value,
            "ast_valid": True,
            "test_exit_code": exit_code,
            "test_stdout_excerpt": stdout_text[-1000:],
            "test_stderr_excerpt": stderr_text[-500:],
            "reason": reason,
        }
        raw_receipt = json.dumps(receipt_dict, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

        record = DiffOracleInspectionRecordV1(
            candidate_id=candidate_id,
            diff_text=diff_text,
            diff_sha256=diff_digest,
            ast_valid=True,
            test_exit_code=exit_code,
            test_stdout=stdout_text,
            test_stderr=stderr_text,
            verdict=verdict,
            reason=reason,
            receipt_bytes=raw_receipt,
        )
        self.inspection_history[candidate_id] = record

        return Ok(
            CandidateCheckV1(
                verdict=verdict,
                candidate_id=candidate_id,
                candidate_content_sha256=content_digest,
                checker_id=self.checker_id,
                checker_receipt_sha256=sha256_ref(raw_receipt),
                checker_receipt_bytes=raw_receipt,
                reason=reason,
            )
        )

# AuthorityEffect: None.
"""
Lean 4 Subprocess Compiler and Diagnostic / Axiom Parser for C041.

Wraps native `lean` CLI execution, enforcing:
1. Subprocess sandboxing with timeout (default 30s).
2. Diagnostic parsing (errors, warnings, heartbeats).
3. Whitelisted axiom closure checking from `#print axioms`.
4. AST command structure / banned keyword scanner.

Submissions are checked by ``verify_submission``: the submission is compiled on its own to
``Submission.olean``, and a separate judge-written file imports it, checks the theorem's
type against a judge-written copy of the target, and runs ``#print axioms``. Only the judge
file's output is parsed, so nothing the submission prints can stand in for the axiom report.
Banned tokens (``sorryAx``, ``#eval``, ``run_cmd``, ``IO``, ``set_option`` and other escapes)
are scanned in the raw submission text, comments included. ``lean --version`` is recorded.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

BANNED_COMMAND_PATTERNS = [
    r"\bsorry\b",
    r"\baxiom\b",
    r"\bopaque\b",
    r"\bunsafe\b",
    r"\bpartial\b",
    r"@\[extern",
    r"@\[implemented_by",
    r"\bnotation\b",
    r"\bmacro\b",
    r"\bsyntax\b",
    r"\belab\b",
    r"\binstance\b",
    r"\bset_option\b",
    r"\bnative_decide\b",
]

# Extra patterns applied to submission text only (the judge writes its own #print, namespace, end).
SUBMISSION_BANNED_PATTERNS = BANNED_COMMAND_PATTERNS + [
    r"\bsorryAx\b",
    r"\badmit\b",
    r"\bstop\b",
    r"#eval\b",
    r"#print\b",
    r"#exit\b",
    r"#reduce\b",
    r"\brun_cmd\b",
    r"\brun_tac\b",
    r"\brun_elab\b",
    r"\brun_meta\b",
    r"\bIO\b",
    r"\binitialize\b",
    r"\bbuiltin_initialize\b",
    r"\belab_rules\b",
    r"\bmacro_rules\b",
    r"\bdeclare_syntax_cat\b",
    r"\bimport\b",
    r"\bnamespace\b",
    r"\bsection\b",
    r"\bend\b",
    r"_root_",
    r"\bexport\b",
    r"@\[csimp",
    r"@\[export",
    r"@\[init",
    r"\bLean\.",
    r"\bofReduceBool\b",
    r"\btrustCompiler\b",
    r"\bimplemented_by\b",
    r"\bextern\b",
]

WHITELISTED_AXIOMS: Set[str] = {"propext", "Quot.sound"}


@dataclass(frozen=True)
class LeanCompilationResult:
    success: bool
    return_code: int
    stdout: str
    stderr: str
    axioms: List[str]
    errors: List[str]
    warnings: List[str]
    banned_tokens_found: List[str] = field(default_factory=list)
    infra_error: bool = False


@dataclass(frozen=True)
class SubmissionVerification:
    """Outcome of the two-stage check of one submitted theorem."""

    success: bool
    infra_error: bool
    axioms: List[str]
    errors: List[str]
    lean_version: str
    banned_tokens_found: List[str] = field(default_factory=list)
    judge_output: str = ""


def check_banned_tokens(code: str, patterns: Optional[List[str]] = None) -> List[str]:
    """Scans the raw code (comments and strings included) for prohibited tokens.

    Comments are not stripped: a regex cannot follow Lean's nested comments and string
    literals, and stripping let live code after a "/-" inside a string escape the scan.
    """
    found: List[str] = []
    for pat in patterns if patterns is not None else BANNED_COMMAND_PATTERNS:
        match = re.search(pat, code)
        if match:
            found.append(match.group(0))
    return found


def parse_axioms_from_output(output: str, target_name: str) -> Tuple[bool, List[str]]:
    """
    Parses `#print axioms <target_name>` output from Lean 4.
    Patterns:
      '<target>' does not depend on any axioms
      '<target>' depends on axioms: [propext, Quot.sound]
    """
    # Regex for depends on axioms
    m_no_ax = re.search(rf"'{re.escape(target_name)}' does not depend on any axioms", output)
    if m_no_ax:
        return True, []

    m_ax = re.search(rf"'{re.escape(target_name)}' depends on axioms:\s*\[(.*?)\]", output)
    if m_ax:
        raw_items = m_ax.group(1).split(",")
        axioms = [item.strip() for item in raw_items if item.strip()]
        return True, axioms

    # In case namespace prefix was omitted in print output
    short_name = target_name.split(".")[-1]
    m_short_no_ax = re.search(rf"'{re.escape(short_name)}' does not depend on any axioms", output)
    if m_short_no_ax:
        return True, []

    m_short_ax = re.search(rf"'{re.escape(short_name)}' depends on axioms:\s*\[(.*?)\]", output)
    if m_short_ax:
        raw_items = m_short_ax.group(1).split(",")
        axioms = [item.strip() for item in raw_items if item.strip()]
        return True, axioms

    return False, []


def compile_lean4_code(
    code: str,
    target_name: Optional[str] = None,
    timeout_sec: float = 30.0,
    check_banned: bool = True,
) -> LeanCompilationResult:
    """
    Compiles Lean 4 code via `lean --stdin` or temporary file, returning structured diagnostics.
    """
    banned_tokens = check_banned_tokens(code) if check_banned else []
    if banned_tokens:
        return LeanCompilationResult(
            success=False,
            return_code=1,
            stdout="",
            stderr=f"Banned tokens detected in submission: {banned_tokens}",
            axioms=[],
            errors=[f"BANNED_TOKEN: {tok}" for tok in banned_tokens],
            warnings=[],
            banned_tokens_found=banned_tokens,
        )

    lean_bin = shutil.which("lean")
    if lean_bin is None:
        return LeanCompilationResult(
            success=False,
            return_code=-2,
            stdout="",
            stderr="lean not on PATH",
            axioms=[],
            errors=["SYSTEM_ERROR: lean not on PATH"],
            warnings=[],
            banned_tokens_found=[],
            infra_error=True,
        )

    try:
        proc = subprocess.run(
            [lean_bin, "--stdin"],
            input=code,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            encoding="utf-8",
            check=False,
        )
    except subprocess.TimeoutExpired:
        return LeanCompilationResult(
            success=False,
            return_code=-1,
            stdout="",
            stderr=f"Compilation timed out after {timeout_sec}s",
            axioms=[],
            errors=["TIMEOUT: Execution exceeded time limit"],
            warnings=[],
            banned_tokens_found=[],
            infra_error=True,
        )
    except Exception as e:
        return LeanCompilationResult(
            success=False,
            return_code=-2,
            stdout="",
            stderr=str(e),
            axioms=[],
            errors=[f"SYSTEM_ERROR: {str(e)}"],
            warnings=[],
            banned_tokens_found=[],
            infra_error=True,
        )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    combined = stdout + "\n" + stderr

    errors: List[str] = []
    warnings: List[str] = []
    for line in combined.splitlines():
        if "error:" in line or "error(" in line or ": error" in line:
            errors.append(line.strip())
        elif "warning:" in line or "warning(" in line or ": warning" in line:
            warnings.append(line.strip())

    if proc.returncode != 0 and not errors:
        errors.append(f"LEAN_ERROR (exit {proc.returncode}): {stderr.strip() or stdout.strip()}")

    axioms: List[str] = []
    if target_name:
        parsed_ok, found_axioms = parse_axioms_from_output(combined, target_name)
        if parsed_ok:
            axioms = found_axioms
        elif proc.returncode == 0:
            # If compile succeeded but #print axioms was not matched, record error
            errors.append(f"AXIOM_PARSE_FAIL: Could not locate #print axioms for '{target_name}'")

    success = (proc.returncode == 0) and (len(errors) == 0)

    return LeanCompilationResult(
        success=success,
        return_code=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        axioms=axioms,
        errors=errors,
        warnings=warnings,
        banned_tokens_found=[],
    )


_LEAN_VERSION: Optional[str] = None


def lean_version() -> str:
    """The `lean --version` line of the toolchain in use (cached), or UNAVAILABLE."""
    global _LEAN_VERSION
    if _LEAN_VERSION is None:
        lean_bin = shutil.which("lean")
        if lean_bin is None:
            _LEAN_VERSION = "UNAVAILABLE: lean not on PATH"
        else:
            try:
                proc = subprocess.run(
                    [lean_bin, "--version"], capture_output=True, text=True, timeout=30, check=False
                )
                _LEAN_VERSION = (
                    proc.stdout or proc.stderr
                ).strip() or f"UNAVAILABLE: exit {proc.returncode}"
            except (OSError, subprocess.SubprocessError) as exc:
                _LEAN_VERSION = f"UNAVAILABLE: {exc}"
    return _LEAN_VERSION


def _run_lean(
    args: List[str], cwd: str, timeout_sec: float, env: Optional[Dict[str, str]] = None
) -> Tuple[int, str, bool]:
    """Returns (return code, combined output, infra_error)."""
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_sec,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout_sec}s", True
    except OSError as exc:
        return -2, f"SYSTEM_ERROR: {exc}", True
    return proc.returncode, (proc.stdout or "") + "\n" + (proc.stderr or ""), False


def _error_lines(output: str) -> List[str]:
    return [
        ln.strip()
        for ln in output.splitlines()
        if "error:" in ln or "error(" in ln or ": error" in ln
    ]


def verify_submission(
    prelude: str,
    aux_list: List[str],
    thm_name: str,
    target_prop: str,
    proof: str,
    timeout_sec: float = 30.0,
) -> SubmissionVerification:
    """Two-stage check: compile the submission, then audit it from a judge-written file.

    The judge-authored target definition precedes all submission text, so the submission
    cannot change what it means; the judge file checks the theorem against it and prints
    the axioms. Only the judge file's output is parsed.
    """
    version = lean_version()
    banned = check_banned_tokens("\n".join(aux_list) + "\n" + proof, SUBMISSION_BANNED_PATTERNS)
    if banned:
        return SubmissionVerification(
            False, False, [], [f"BANNED_TOKEN: {tok}" for tok in banned], version, banned
        )
    lean_bin = shutil.which("lean")
    if lean_bin is None:
        return SubmissionVerification(False, True, [], ["INFRA_ERROR: lean not on PATH"], version)

    expected_name = f"C41JudgeExpected_{thm_name}"
    aux_block = "\n\n".join(aux_list)
    submission = (
        f"{prelude}\n\n"
        f"def {expected_name} : Prop := {target_prop}\n\n"
        "namespace Submission\n"
        f"{aux_block}\n\n"
        f"theorem {thm_name} : {target_prop} := {proof}\n"
        "end Submission\n"
    )
    judge = (
        "import Submission\n\n"
        f"example : {expected_name} := Submission.{thm_name}\n\n"
        f"#print axioms Submission.{thm_name}\n"
    )
    with tempfile.TemporaryDirectory(prefix="c041_") as work:
        Path(work, "Submission.lean").write_text(submission, encoding="utf-8")
        Path(work, "Judge.lean").write_text(judge, encoding="utf-8")
        rc, out, infra = _run_lean(
            [lean_bin, "-o", "Submission.olean", "Submission.lean"], work, timeout_sec
        )
        if infra:
            return SubmissionVerification(False, True, [], [out], version)
        errors = _error_lines(out)
        if rc != 0 or errors:
            return SubmissionVerification(
                False, False, [], errors or [f"LEAN_ERROR (exit {rc})"], version
            )
        env = dict(os.environ)
        env["LEAN_PATH"] = work
        rc, judge_out, infra = _run_lean([lean_bin, "Judge.lean"], work, timeout_sec, env)
        if infra:
            return SubmissionVerification(
                False, True, [], [judge_out], version, judge_output=judge_out
            )
        errors = _error_lines(judge_out)
        if rc != 0 or errors:
            return SubmissionVerification(
                False,
                False,
                [],
                errors or [f"JUDGE_ERROR (exit {rc})"],
                version,
                judge_output=judge_out,
            )
        parsed, axioms = parse_axioms_from_output(judge_out, f"Submission.{thm_name}")
        if not parsed:
            return SubmissionVerification(
                False, False, [], ["AXIOM_PARSE_FAIL"], version, judge_output=judge_out
            )
        return SubmissionVerification(True, False, axioms, [], version, judge_output=judge_out)

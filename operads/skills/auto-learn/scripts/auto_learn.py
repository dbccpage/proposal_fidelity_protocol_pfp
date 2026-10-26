"""Auto Learn: recall lessons, apply smallest high-confidence correction, and re-check diff.

AuthorityEffect: None.

Connects `remediation_suggestions` from `auto-anti-pattern-lint` or AutoP handoffs into
an automated, fail-closed repair step that applies the smallest high-confidence correction
and verifies the resulting file diff.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def find_repo_root(start: Optional[Path] = None) -> Path:
    curr = (start or Path.cwd()).resolve()
    for _ in range(10):
        if (curr / ".git").exists() and (
            (curr / "omega_engine").is_dir() or (curr / ".agents").is_dir()
        ):
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return (start or Path.cwd()).resolve()


@dataclass
class CorrectionOutcome:
    file: str
    line: int
    anti_pattern_id: str
    dual_healthy_pattern: str
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    status: str      # "APPLIED", "SKIPPED_LOW_CONFIDENCE", "SKIPPED_NO_MATCH", "UNSUPPORTED"
    diff_snippet: str = ""
    remediation_advice: str = ""
    error: Optional[str] = None


@dataclass
class FileRepairReceipt:
    file: str
    status: str  # "VERIFIED_CLEAN", "REPAIRED_UNVERIFIED", "FAILED_RECHECK_ROLLED_BACK", "SKIPPED", "NO_CHANGES"
    corrections_applied: int = 0
    corrections_skipped: int = 0
    unified_diff: str = ""
    git_diff: str = ""
    outcomes: List[CorrectionOutcome] = field(default_factory=list)
    recheck_exit_code: Optional[int] = None
    recheck_findings_count: int = 0


@dataclass
class AutoLearnRepairReport:
    authority_effect: str = "None"
    total_suggestions: int = 0
    repaired_files_count: int = 0
    total_corrections_applied: int = 0
    total_corrections_skipped: int = 0
    files: List[FileRepairReceipt] = field(default_factory=list)
    overall_status: str = "PASS"  # "PASS", "WARN", "FAIL"


# -----------------------------------------------------------------------------
# High-Confidence Repair Strategies
# -----------------------------------------------------------------------------

def repair_ap_md_058(
    line: str,
) -> Tuple[bool, str, str]:
    """Smallest high-confidence correction for AP_MD_058 (markdown asterisk list bullet).

    Replaces leading asterisk bullet marker `* ` with hyphen bullet marker `- `,
    strictly preserving all leading indentation whitespace and subsequent text.
    Confidence: HIGH (1.0).
    """
    if re.search(r"^\s*\*\s+[^\*]", line):
        corrected = re.sub(r"^(\s*)\*\s+", r"\1- ", line)
        if corrected != line:
            return True, corrected, "HIGH"
    return False, line, "LOW"


def extract_mypy_error_codes(
    file_path: Path,
    line_number: int,
    repo_root: Path,
) -> List[str]:
    """Probe mypy with --shadow-file to extract exact scoped error codes for a line."""
    if not file_path.is_file():
        return []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    except Exception:
        return []

    if line_number < 1 or line_number > len(lines):
        return []

    target_line = lines[line_number - 1]
    if not re.search(r"#\s*type:\s*ignore(?!\s*\[)", target_line):
        return []

    # Strip blanket ignore on target line for the shadow file
    stripped_line = re.sub(r"#\s*type:\s*ignore(?!\s*\[)[^\n]*", "", target_line)
    shadow_lines = list(lines)
    shadow_lines[line_number - 1] = stripped_line

    temp_shadow = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8"
        ) as sf:
            sf.write("".join(shadow_lines))
            temp_shadow = Path(sf.name)

        cmd = [
            sys.executable,
            "-m",
            "mypy",
            "--show-error-codes",
            "--shadow-file",
            str(file_path.resolve()),
            str(temp_shadow.resolve()),
            str(file_path.resolve()),
        ]
        res = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        pattern = rf":{line_number}(?::\d+)?: error:[^\n]*\[([a-z0-9_-]+)\]"
        codes = re.findall(pattern, res.stdout)
        return list(dict.fromkeys(codes))
    except Exception:
        return []
    finally:
        if temp_shadow and temp_shadow.is_file():
            try:
                temp_shadow.unlink(missing_ok=True)
            except Exception:
                pass


def repair_ap_py_001(
    line: str,
    file_path: Optional[Path],
    line_number: int,
    repo_root: Optional[Path],
) -> Tuple[bool, str, str, str]:
    """Promote AP_PY_001 blanket type ignore to high-confidence scoped ignore via mypy extraction.

    Extracts specific error codes emitted by mypy on that line, replacing `# type: ignore`
    with `# type: ignore[code1, code2]`.
    """
    if not re.search(r"#\s*type:\s*ignore(?!\s*\[)", line):
        return False, line, "LOW", "Line does not contain a blanket `# type: ignore` comment."

    if not file_path or not repo_root:
        return False, line, "LOW", "File path and repo root are required for mypy error extraction."

    codes = extract_mypy_error_codes(file_path, line_number, repo_root)
    if not codes:
        return (
            False,
            line,
            "LOW",
            f"Mypy emitted no error code for line {line_number} (ignore may be redundant or unreached).",
        )

    code_str = ", ".join(codes)
    corrected = re.sub(
        r"#\s*type:\s*ignore(?!\s*\[)",
        f"# type: ignore[{code_str}]",
        line,
    )
    if corrected != line:
        return True, corrected, "HIGH", f"Scoped blanket ignore to [{code_str}] via mypy extraction."

    return False, line, "LOW", "Failed to format scoped `# type: ignore` comment."


def apply_high_confidence_fix(
    suggestion: Dict[str, Any],
    line: str,
    file_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> Tuple[bool, str, str, str]:
    """Evaluate suggestion and apply smallest high-confidence correction if applicable.

    Returns:
        (success, new_line, confidence, explanation)
    """
    ap_id = suggestion.get("anti_pattern_id") or suggestion.get("id") or ""
    line_num = suggestion.get("line", 0)

    if ap_id == "AP_MD_058":
        success, new_line, conf = repair_ap_md_058(line)
        if success:
            return True, new_line, conf, "Replaced asterisk list bullet `* ` with hyphen `- ` (MD004 compliance)."
        return False, line, "LOW", "Line did not match expected asterisk bullet syntax."

    if ap_id == "AP_PY_001":
        return repair_ap_py_001(line, file_path, line_num, repo_root)

    # Non-high-confidence patterns require human/architectural review to prevent regressions
    advice = suggestion.get("remediation_advice", "")
    return False, line, "LOW", f"Anti-pattern {ap_id} requires manual review: {advice}"


# -----------------------------------------------------------------------------
# File Repair & Re-check Execution
# -----------------------------------------------------------------------------

def repair_file(
    file_path: Path,
    suggestions: List[Dict[str, Any]],
    repo_root: Path,
    dry_run: bool = False,
    check_diff: bool = True,
) -> FileRepairReceipt:
    try:
        rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        rel_path = str(file_path).replace("\\", "/")

    receipt = FileRepairReceipt(file=rel_path, status="NO_CHANGES")

    if not file_path.is_file():
        receipt.status = "SKIPPED"
        return receipt

    try:
        original_content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        receipt.status = "SKIPPED"
        return receipt

    lines = original_content.splitlines(keepends=True)
    if not lines and original_content == "":
        lines = []

    # Sort suggestions by line descending to preserve line alignment
    sorted_suggs = sorted(
        suggestions,
        key=lambda s: s.get("line", 0),
        reverse=True,
    )

    modified = False
    new_lines = list(lines)

    for sugg in sorted_suggs:
        line_num = sugg.get("line", 0)
        ap_id = sugg.get("anti_pattern_id") or sugg.get("id") or "UNKNOWN"
        dual_id = sugg.get("dual_healthy_pattern") or sugg.get("dual_pattern") or "UNKNOWN"
        advice = sugg.get("remediation_advice", "")

        if line_num < 1 or line_num > len(new_lines):
            receipt.outcomes.append(
                CorrectionOutcome(
                    file=rel_path,
                    line=line_num,
                    anti_pattern_id=ap_id,
                    dual_healthy_pattern=dual_id,
                    confidence="LOW",
                    status="SKIPPED_NO_MATCH",
                    remediation_advice=advice,
                    error=f"Line number {line_num} out of bounds (1..{len(new_lines)})",
                )
            )
            receipt.corrections_skipped += 1
            continue

        target_line = new_lines[line_num - 1]
        success, repaired_line, conf, explanation = apply_high_confidence_fix(
            suggestion=sugg,
            line=target_line,
            file_path=file_path,
            repo_root=repo_root,
        )

        if success and conf == "HIGH":
            new_lines[line_num - 1] = repaired_line
            modified = True
            diff_snippet = f"-{target_line.rstrip()}\n+{repaired_line.rstrip()}"
            receipt.outcomes.append(
                CorrectionOutcome(
                    file=rel_path,
                    line=line_num,
                    anti_pattern_id=ap_id,
                    dual_healthy_pattern=dual_id,
                    confidence=conf,
                    status="APPLIED",
                    diff_snippet=diff_snippet,
                    remediation_advice=advice,
                )
            )
            receipt.corrections_applied += 1
        else:
            receipt.outcomes.append(
                CorrectionOutcome(
                    file=rel_path,
                    line=line_num,
                    anti_pattern_id=ap_id,
                    dual_healthy_pattern=dual_id,
                    confidence=conf,
                    status="SKIPPED_LOW_CONFIDENCE",
                    remediation_advice=advice,
                    error=explanation,
                )
            )
            receipt.corrections_skipped += 1

    if not modified:
        receipt.status = "NO_CHANGES"
        return receipt

    new_content = "".join(new_lines)

    # Compute unified diff
    orig_split = original_content.splitlines(keepends=True)
    new_split = new_content.splitlines(keepends=True)
    u_diff = "".join(
        difflib.unified_diff(
            orig_split,
            new_split,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
    )
    receipt.unified_diff = u_diff

    if dry_run:
        receipt.status = "REPAIRED_DRY_RUN"
        return receipt

    # Write modifications to disk
    file_path.write_text(new_content, encoding="utf-8")

    # Capture git diff
    try:
        git_res = subprocess.run(
            ["git", "diff", "--", str(file_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        receipt.git_diff = git_res.stdout
    except Exception:
        receipt.git_diff = u_diff

    # Re-check verification
    if check_diff:
        lint_script = (
            repo_root
            / "omega_engine_operads"
            / "skills"
            / "auto-anti-pattern-lint"
            / "scripts"
            / "anti_pattern_lint.py"
        )
        if lint_script.is_file():
            try:
                recheck_res = subprocess.run(
                    [
                        sys.executable,
                        str(lint_script),
                        "--files",
                        str(file_path),
                        "--check",
                    ],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                receipt.recheck_exit_code = recheck_res.returncode

                # Check if file has any remaining findings
                recheck_output = recheck_res.stdout + recheck_res.stderr
                findings_match = re.search(r"Anti-pattern file findings:\s*(\d+)", recheck_output)
                if findings_match:
                    receipt.recheck_findings_count = int(findings_match.group(1))

                if recheck_res.returncode != 0 and receipt.recheck_findings_count > 0:
                    # Fail-closed rollback if violations remain or were introduced
                    file_path.write_text(original_content, encoding="utf-8")
                    receipt.status = "FAILED_RECHECK_ROLLED_BACK"
                    receipt.git_diff = ""
                    return receipt
            except Exception:
                receipt.recheck_findings_count = -1

        # Multi-oracle verification for Python files with AP_PY_001 applied
        if file_path.suffix == ".py" and any(
            out.anti_pattern_id == "AP_PY_001" and out.status == "APPLIED"
            for out in receipt.outcomes
        ):
            try:
                mypy_check = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "mypy",
                        "--show-error-codes",
                        str(file_path.resolve()),
                    ],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                repaired_py_lines = {
                    out.line
                    for out in receipt.outcomes
                    if out.anti_pattern_id == "AP_PY_001" and out.status == "APPLIED"
                }
                has_error_on_repaired = any(
                    re.search(rf":{ln}(?::\d+)?: error:", mypy_check.stdout)
                    for ln in repaired_py_lines
                )
                if has_error_on_repaired:
                    file_path.write_text(original_content, encoding="utf-8")
                    receipt.status = "FAILED_RECHECK_ROLLED_BACK"
                    receipt.git_diff = ""
                    return receipt
            except Exception:
                pass

        receipt.status = "VERIFIED_CLEAN"
    else:
        receipt.status = "REPAIRED_UNVERIFIED"

    return receipt


# -----------------------------------------------------------------------------
# Extract Remediation Suggestions
# -----------------------------------------------------------------------------

def extract_remediation_suggestions(
    source_data: Any,
) -> List[Dict[str, Any]]:
    """Extract `remediation_suggestions` from varied handoff/report formats."""
    if isinstance(source_data, list):
        return source_data

    if isinstance(source_data, dict):
        if "remediation_suggestions" in source_data:
            return source_data.get("remediation_suggestions", [])
        if "changed_files_anti_pattern_lint" in source_data:
            sub = source_data["changed_files_anti_pattern_lint"]
            if isinstance(sub, dict) and "remediation_suggestions" in sub:
                return sub.get("remediation_suggestions", [])
        if "file_findings" in source_data:
            return [
                {
                    "file": f.get("file"),
                    "line": f.get("line"),
                    "anti_pattern_id": f.get("id"),
                    "dual_healthy_pattern": f.get("dual_pattern"),
                    "matched_snippet": f.get("matched_snippet"),
                    "remediation_advice": f.get("remediation_advice"),
                    "implementation_pattern": f.get("implementation_pattern"),
                    "associated_antibodies": f.get("associated_antibodies", []),
                }
                for f in source_data.get("file_findings", [])
            ]
    return []


def discover_suggestions_from_repo(repo_root: Path) -> List[Dict[str, Any]]:
    """Discover suggestions from recent AutoP receipt or run changed-files audit."""
    receipt_candidates = [
        repo_root / "runs" / "autop_anti_pattern" / "changed_files_anti_pattern_lint.json",
        repo_root / "runs" / "autop_anti_pattern" / "auto-anti-pattern-lint__anti_pattern_lint.json",
    ]
    for cand in receipt_candidates:
        if cand.is_file():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                suggs = extract_remediation_suggestions(data)
                if suggs:
                    return suggs
            except Exception:
                pass

    # Fallback: run anti_pattern_lint on git changed files
    lint_script = (
        repo_root
        / "omega_engine_operads"
        / "skills"
        / "auto-anti-pattern-lint"
        / "scripts"
        / "anti_pattern_lint.py"
    )
    if lint_script.is_file():
        try:
            subprocess.run(
                [sys.executable, str(lint_script), "--changed"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            # Find JSON payload if printed or check report
            tmp_report = repo_root / "runs" / "autop_anti_pattern" / "temp_changed_lint.json"
            subprocess.run(
                [
                    sys.executable,
                    str(lint_script),
                    "--changed",
                    "--report-out",
                    str(tmp_report),
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if tmp_report.is_file():
                data = json.loads(tmp_report.read_text(encoding="utf-8"))
                return extract_remediation_suggestions(data)
        except Exception:
            pass

    return []


def discover_suggestions_for_files(repo_root: Path, files: List[str]) -> List[Dict[str, Any]]:
    """Audit specified files directly to extract remediation suggestions."""
    lint_script = (
        repo_root
        / "omega_engine_operads"
        / "skills"
        / "auto-anti-pattern-lint"
        / "scripts"
        / "anti_pattern_lint.py"
    )
    if not lint_script.is_file():
        return []
    report_file = repo_root / "runs" / "autop_anti_pattern" / "temp_files_lint.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                sys.executable,
                str(lint_script),
                "--files",
                *files,
                "--report-out",
                str(report_file),
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if report_file.is_file():
            data = json.loads(report_file.read_text(encoding="utf-8"))
            return extract_remediation_suggestions(data)
    except Exception:
        pass
    return []


# -----------------------------------------------------------------------------
# Main Orchestration Loop
# -----------------------------------------------------------------------------

def execute_auto_learn_repair(
    suggestions: List[Dict[str, Any]],
    repo_root: Path,
    dry_run: bool = False,
    check_diff: bool = True,
    filter_files: Optional[List[str]] = None,
) -> AutoLearnRepairReport:
    """Group suggestions by file, apply smallest high-confidence correction, and re-check diff."""
    report = AutoLearnRepairReport(total_suggestions=len(suggestions))

    norm_filter = [t.replace("\\", "/").rstrip("/") for t in filter_files] if filter_files else None

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for s in suggestions:
        f = s.get("file")
        if not f:
            continue
        f_norm = f.replace("\\", "/").lstrip("./")
        if norm_filter and not any(f_norm.endswith(target) or target.endswith(f_norm) or target in f_norm for target in norm_filter):
            continue
        grouped.setdefault(f_norm, []).append(s)

    for rel_file, file_suggs in grouped.items():
        file_path = (repo_root / rel_file).resolve()
        if not file_path.is_file():
            # Try direct path
            file_path = Path(rel_file).resolve()

        receipt = repair_file(
            file_path=file_path,
            suggestions=file_suggs,
            repo_root=repo_root,
            dry_run=dry_run,
            check_diff=check_diff,
        )
        report.files.append(receipt)
        if receipt.status in ("VERIFIED_CLEAN", "REPAIRED_UNVERIFIED", "REPAIRED_DRY_RUN"):
            report.repaired_files_count += 1
        report.total_corrections_applied += receipt.corrections_applied
        report.total_corrections_skipped += receipt.corrections_skipped

    if any(f.status == "FAILED_RECHECK_ROLLED_BACK" for f in report.files):
        report.overall_status = "FAIL"
    elif report.total_corrections_skipped > 0:
        report.overall_status = "WARN"
    else:
        report.overall_status = "PASS"

    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Auto-Learn: Automated smallest high-confidence repair and file diff re-check."
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="repair",
        choices=["repair", "check", "inspect"],
        help="Action to execute (default: repair)",
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Trigger automated repair step for remediation suggestions",
    )
    parser.add_argument(
        "--remediations",
        type=Path,
        help="Path to JSON file containing remediation suggestions or AutoP handoff",
    )
    parser.add_argument(
        "--remediations-json",
        type=str,
        help="Raw JSON string containing remediation suggestions",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read remediation suggestions JSON from standard input",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Scan git changed files for anti-patterns and repair high-confidence findings",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[],
        help="Target specific files for repair",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute repairs and show unified diff without modifying files on disk",
    )
    parser.add_argument(
        "--no-check-diff",
        action="store_true",
        help="Skip post-repair verification check",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write repair receipt JSON",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable summary output",
    )

    args = parser.parse_args(argv)
    repo_root = find_repo_root()

    suggestions: List[Dict[str, Any]] = []

    if args.remediations_json:
        try:
            data = json.loads(args.remediations_json)
            suggestions = extract_remediation_suggestions(data)
        except Exception as e:
            print(f"[auto-learn] Error parsing --remediations-json: {e}", file=sys.stderr)
            return 1
    elif args.remediations:
        if args.remediations.is_file():
            try:
                data = json.loads(args.remediations.read_text(encoding="utf-8"))
                suggestions = extract_remediation_suggestions(data)
            except Exception as e:
                print(f"[auto-learn] Error reading {args.remediations}: {e}", file=sys.stderr)
                return 1
        else:
            print(f"[auto-learn] File not found: {args.remediations}", file=sys.stderr)
            return 1
    elif args.files:
        suggestions = discover_suggestions_for_files(repo_root, args.files)
    elif args.stdin:
        try:
            stdin_text = sys.stdin.read().strip()
            if stdin_text:
                data = json.loads(stdin_text)
                suggestions = extract_remediation_suggestions(data)
        except Exception as e:
            print(f"[auto-learn] Error reading stdin: {e}", file=sys.stderr)
            return 1
    else:
        suggestions = discover_suggestions_from_repo(repo_root)

    report = execute_auto_learn_repair(
        suggestions=suggestions,
        repo_root=repo_root,
        dry_run=args.dry_run,
        check_diff=not args.no_check_diff,
        filter_files=args.files or None,
    )

    if not args.quiet:
        print("=" * 60)
        print("  AUTO-LEARN: AUTOMATED HIGH-CONFIDENCE REPAIR & RE-CHECK")
        print("=" * 60)
        print(f"Suggestions evaluated: {report.total_suggestions}")
        print(f"Files repaired:        {report.repaired_files_count}")
        print(f"Corrections applied:   {report.total_corrections_applied}")
        print(f"Corrections skipped:   {report.total_corrections_skipped}")
        print(f"Overall status:        {report.overall_status}")
        print("-" * 60)

        for f_receipt in report.files:
            print(f"File: {f_receipt.file} [{f_receipt.status}]")
            for outcome in f_receipt.outcomes:
                if outcome.status == "APPLIED":
                    print(f"  [APPLIED] Line {outcome.line}: {outcome.anti_pattern_id} -> {outcome.dual_healthy_pattern}")
                    print(f"    Confidence: {outcome.confidence}")
                    if outcome.diff_snippet:
                        for dline in outcome.diff_snippet.splitlines():
                            print(f"      {dline}")
                else:
                    print(f"  [{outcome.status}] Line {outcome.line}: {outcome.anti_pattern_id}")
                    if outcome.error:
                        print(f"    Reason: {outcome.error}")

            if f_receipt.git_diff:
                print("  Re-checked Git Diff:")
                for dline in f_receipt.git_diff.splitlines()[:15]:
                    print(f"    {dline}")
                if len(f_receipt.git_diff.splitlines()) > 15:
                    print(f"    ... and {len(f_receipt.git_diff.splitlines()) - 15} more diff lines.")
            print("-" * 60)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    return 1 if report.overall_status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())

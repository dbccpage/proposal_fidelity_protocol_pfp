"""Check pattern catalog layout and audit changed files for anti-patterns.

Required language folders must exist under anti/ and helpful/ subfolders.
Every AP_*.md pattern must name a dual_pattern file. Empty catalog slots are valid.
When triggered with --changed or --files, audits changed files for registered anti-patterns
and attaches dual healthy patterns (HPs) and matching immune antibodies (ABs).

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

REQUIRED_CATALOGS = (
    "autop",
    "html",
    "javascript",
    "json",
    "lean4",
    "manim",
    "markdown",
    "python",
    "rust",
    "sql",
    "svg",
)

IGNORED_DIRS: Set[str] = {
    ".git",
    ".lake",
    "target",
    "node_modules",
    ".venv",
    "venv",
    "site-packages",
    ".elan",
    "__pycache__",
    "quarantine",
    "archive",
    ".pixi",
}

# Known mappings from Anti-Patterns to primary Antibodies
AP_ANTIBODY_MAPPING: Dict[str, List[str]] = {
    "AP_MD_058": ["ab_pattern_estate_naming_and_id_collision"],
    "AP_PY_001": ["ab_vacuous_test_mock_facade"],
    "AP_PY_006": ["ab_origin_invariant_causal_refinement"],
    "AP_RS_002": ["ab_pattern_estate_naming_and_id_collision"],
    "AP_LN_001": ["ab_empty_axiom_audit_cannot_pass"],
    "AP_SQL_001": ["ab_checked_arithmetic_every_estimate_producer"],
    "AP_SQL_002": ["ab_checked_arithmetic_every_estimate_producer"],
}


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


def _frontmatter(text: str) -> Dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fields: Dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def _extract_section(content: str, headers: tuple[str, ...]) -> str:
    for h in headers:
        pattern = rf"##\s+{re.escape(h)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _load_healthy_pattern(dual_name: str, repo_root: Path, lang: str) -> Dict[str, str]:
    if not dual_name:
        return {}
    if not dual_name.endswith(".md"):
        dual_name = f"{dual_name}.md"
    hp_path = repo_root / "omega_engine_operads" / "patterns" / "helpful" / lang / dual_name
    if not hp_path.is_file():
        candidates = list((repo_root / "omega_engine_operads" / "patterns" / "helpful").glob(f"*/{dual_name}"))
        if candidates:
            hp_path = candidates[0]
    if not hp_path.is_file():
        return {}
    content = hp_path.read_text(encoding="utf-8", errors="replace")
    return {
        "dual_pattern_path": str(hp_path.relative_to(repo_root)).replace("\\", "/"),
        "implementation_pattern": _extract_section(
            content,
            ("Remediation & Implementation", "Implementation Pattern", "Implementation", "Resolution"),
        ),
        "resolution": _extract_section(content, ("Resolution", "Prevention & Resolution")),
    }


def _load_antibodies(repo_root: Path) -> Dict[str, Dict[str, Any]]:
    abs_dict: Dict[str, Dict[str, Any]] = {}
    ab_dir = repo_root / "omega_engine_epistemic_immune_system" / "antibodies"
    if not ab_dir.is_dir():
        return abs_dict
    for f in ab_dir.glob("ab_*.json"):
        if f.name == "pharmacy_catalog.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            aid = data.get("antibody_id") or f.stem
            abs_dict[aid] = {
                "antibody_id": aid,
                "title": data.get("title") or data.get("description", ""),
                "description": data.get("description", ""),
                "trigger": data.get("trigger", ""),
                "check": data.get("check", ""),
                "failure_class": data.get("failure_class", ""),
                "negative_fixture": data.get("negative_fixture", ""),
                "positive_fixture": data.get("positive_fixture", ""),
            }
        except Exception:
            pass
    return abs_dict


def audit_catalog(catalog: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if not catalog.is_dir():
        return [
            {
                "id": "CATALOG_MISSING",
                "file": catalog.as_posix(),
                "anti_pattern": "patterns catalog directory is absent",
            }
        ]

    anti_root = catalog / "anti" if (catalog / "anti").is_dir() else catalog
    helpful_root = catalog / "helpful" if (catalog / "helpful").is_dir() else catalog

    for name in REQUIRED_CATALOGS:
        slot = anti_root / name
        if not slot.is_dir():
            findings.append(
                {
                    "id": "CATALOG_SLOT_MISSING",
                    "file": slot.as_posix(),
                    "anti_pattern": f"required catalog slot {name} is absent",
                }
            )
        if helpful_root != anti_root:
            h_slot = helpful_root / name
            if not h_slot.is_dir():
                findings.append(
                    {
                        "id": "CATALOG_SLOT_MISSING",
                        "file": h_slot.as_posix(),
                        "anti_pattern": f"required helpful catalog slot {name} is absent",
                    }
                )

    for pattern in sorted(anti_root.glob("*/*.md")):
        if not pattern.name.startswith("AP_"):
            continue
        fields = _frontmatter(pattern.read_text(encoding="utf-8"))
        dual = fields.get("dual_pattern", "")
        if not dual:
            findings.append(
                {
                    "id": "DUAL_MISSING",
                    "file": pattern.as_posix(),
                    "anti_pattern": "AP pattern has no dual_pattern",
                }
            )
            continue
        dual_name = dual if dual.endswith(".md") else f"{dual}.md"
        dual_path = helpful_root / pattern.parent.name / dual_name
        if not dual_path.is_file():
            dual_path = pattern.parent / dual_name
        if not dual_path.is_file():
            findings.append(
                {
                    "id": "DUAL_FILE_MISSING",
                    "file": pattern.as_posix(),
                    "anti_pattern": f"dual pattern file {dual} is absent",
                }
            )
    return findings


def get_changed_files(repo_root: Path) -> List[Path]:
    """Retrieve modified, added, or untracked files in the repository using git."""
    changed: List[Path] = []
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if len(line) < 4:
                    continue
                status = line[:2]
                if status == " D" or status == "D ":
                    continue
                path_str = line[3:].strip()
                if " -> " in path_str:
                    path_str = path_str.split(" -> ")[1].strip()
                path_str = path_str.strip("\"'")
                file_path = repo_root / path_str
                if file_path.is_file():
                    parts = set(file_path.relative_to(repo_root).parts)
                    if not parts.intersection(IGNORED_DIRS):
                        changed.append(file_path)
    except Exception:
        pass
    return changed


def audit_file(
    file_path: Path,
    repo_root: Path,
    ab_index: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Scan an individual file for anti-pattern violations with dual HP and AB binding."""
    findings: List[Dict[str, Any]] = []
    suffix = file_path.suffix.lower()
    try:
        rel_path = str(file_path.relative_to(repo_root)).replace("\\", "/")
    except ValueError:
        rel_path = str(file_path).replace("\\", "/")

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    lines = content.splitlines()

    def _enrich(
        finding_id: str,
        name: str,
        lang: str,
        dual_id: str,
        line_num: int,
        snippet: str,
        advice: str,
        anti_desc: str,
    ) -> Dict[str, Any]:
        hp_info = _load_healthy_pattern(dual_id, repo_root, lang)
        associated_ab_ids = AP_ANTIBODY_MAPPING.get(finding_id, [])
        associated_abs: List[Dict[str, Any]] = []
        if ab_index:
            for ab_id in associated_ab_ids:
                if ab_id in ab_index:
                    associated_abs.append(ab_index[ab_id])
                else:
                    associated_abs.append({"antibody_id": ab_id})
        else:
            for ab_id in associated_ab_ids:
                associated_abs.append({"antibody_id": ab_id})

        return {
            "id": finding_id,
            "pattern_name": name,
            "file": rel_path,
            "line": line_num,
            "matched_snippet": snippet,
            "dual_pattern": dual_id,
            "anti_pattern": anti_desc,
            "remediation_advice": advice,
            "dual_pattern_path": hp_info.get("dual_pattern_path", ""),
            "implementation_pattern": hp_info.get("implementation_pattern", ""),
            "resolution": hp_info.get("resolution", ""),
            "associated_antibodies": associated_abs,
            "authority_effect": "None",
        }

    # 1. Markdown: AP_MD_058 (Asterisk list syntax)
    if suffix == ".md":
        in_code_block = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code_block = not in_code_block
                continue
            if not in_code_block and re.search(r"^\s*\*\s+[^\*]", line):
                findings.append(
                    _enrich(
                        finding_id="AP_MD_058",
                        name="markdown_asterisk_list_syntax",
                        lang="markdown",
                        dual_id="HP_MD_058_hyphen_list_bullet_syntax",
                        line_num=i,
                        snippet=line.strip(),
                        advice="Replace asterisk bullet marker `* ` with hyphen bullet marker `- ` to conform to MD004.",
                        anti_desc="Asterisk list marker violates MD004 hyphen convention and triggers republication check C03.",
                    )
                )

    # 2. Python
    elif suffix == ".py":
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
            for tok in tokens:
                if tok.type == tokenize.COMMENT and re.search(
                    r"#\s*type:\s*ignore(?!\s*\[)", tok.string
                ):
                    findings.append(
                        _enrich(
                            finding_id="AP_PY_001",
                            name="blanket_mypy_ignore",
                            lang="python",
                            dual_id="HP_PY_001_scoped_mypy_overrides",
                            line_num=tok.start[0],
                            snippet=tok.string.strip(),
                            advice="Replace blanket `# type: ignore` with specific mypy error code, e.g. `# type: ignore[attr-defined]`, or declare scoped overrides in pyproject.toml.",
                            anti_desc="Blanket type ignore suppresses all static typing checks across the line.",
                        )
                    )
        except (tokenize.TokenError, IndentationError):
            for i, line in enumerate(lines, 1):
                if re.search(r"#\s*type:\s*ignore(?!\s*\[)", line):
                    findings.append(
                        _enrich(
                            finding_id="AP_PY_001",
                            name="blanket_mypy_ignore",
                            lang="python",
                            dual_id="HP_PY_001_scoped_mypy_overrides",
                            line_num=i,
                            snippet=line.strip(),
                            advice="Replace blanket `# type: ignore` with specific mypy error code, e.g. `# type: ignore[attr-defined]`, or declare scoped overrides in pyproject.toml.",
                            anti_desc="Blanket type ignore suppresses all static typing checks across the line.",
                        )
                    )

        is_test_or_pattern = (
            "tests" in rel_path.split("/")
            or rel_path.endswith("_test.py")
            or Path(rel_path).name.startswith("test_")
            or "patterns" in rel_path
            or "anti_pattern" in rel_path
        )
        for i, line in enumerate(lines, 1):
            if not is_test_or_pattern and (
                re.search(r"['\"]file:///[a-zA-Z]:", line)
                or re.search(r"['\"][a-zA-Z]:[/\\]Users[/\\]", line)
            ):
                findings.append(
                    _enrich(
                        finding_id="AP_PY_006",
                        name="host_absolute_path_injection",
                        lang="python",
                        dual_id="HP_PY_006_dynamic_repository_relative_resolution",
                        line_num=i,
                        snippet=line.strip(),
                        advice="Replace hardcoded host-absolute path with dynamic repo-relative resolution via Path(__file__).resolve().",
                        anti_desc="Hardcoded host-absolute path breaks portability across developer workstations and CI runners.",
                    )
                )

            if re.search(r"cursor\.execute\s*\(\s*f[\"']", line) or re.search(
                r"\.execute\s*\(\s*f[\"']\s*(?:SELECT|INSERT|UPDATE|DELETE)", line, re.IGNORECASE
            ):
                findings.append(
                    _enrich(
                        finding_id="AP_SQL_001",
                        name="unparameterized_string_query",
                        lang="sql",
                        dual_id="HP_SQL_001_parameterized_query_binding",
                        line_num=i,
                        snippet=line.strip(),
                        advice="Use parameterized query tuple/dict binding instead of f-string interpolation.",
                        anti_desc="Unparameterized f-string query in execute call exposes SQL injection vulnerability.",
                    )
                )

    # 3. Rust: AP_RS_002
    elif suffix == ".rs":
        if "crates_rs" in rel_path:
            for i, line in enumerate(lines, 1):
                if re.search(r"^\s*pub\s+enum\s+\w+", line):
                    preceding = " ".join(lines[max(0, i - 5) : i - 1])
                    if "#[derive(" in preceding and "Ord" not in preceding:
                        findings.append(
                            _enrich(
                                finding_id="AP_RS_002",
                                name="domain_enum_missing_ord",
                                lang="rust",
                                dual_id="HP_RS_002_deterministic_key_trait_derive",
                                line_num=i,
                                snippet=line.strip(),
                                advice="Derive PartialEq, Eq, PartialOrd, Ord, Hash on domain enums for deterministic collections.",
                                anti_desc="Domain enum derived without Ord trait causes non-deterministic ordering in collections.",
                            )
                        )

    # 4. Lean 4: AP_LN_001
    elif suffix == ".lean":
        in_block_comment = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if in_block_comment:
                if "-/" in stripped:
                    in_block_comment = False
                    code_part = stripped.split("-/", 1)[1]
                else:
                    continue
            elif "/-" in stripped:
                if "-/" in stripped and stripped.find("-/") > stripped.find("/-"):
                    before = stripped[: stripped.find("/-")]
                    after = stripped[stripped.find("-/") + 2 :]
                    code_part = before + " " + after
                else:
                    in_block_comment = True
                    code_part = stripped[: stripped.find("/-")]
            else:
                code_part = stripped

            code_line = code_part.split("--")[0].strip()
            if code_line and re.search(r"\bsorry\b", code_line):
                findings.append(
                    _enrich(
                        finding_id="AP_LN_001",
                        name="unmechanized_sorry_proof_claim",
                        lang="lean4",
                        dual_id="HP_LN_001_zero_sorry_axiom_allowlist",
                        line_num=i,
                        snippet=line.strip(),
                        advice="Close proof obligation fully without sorry; verify declarations via #print axioms.",
                        anti_desc="Unmechanized sorry leaves formal proof obligation open.",
                    )
                )

    # 5. SQL: AP_SQL_002
    elif suffix == ".sql":
        for i, line in enumerate(lines, 1):
            if re.search(r"--\s*TODO\s*transaction", line, re.IGNORECASE):
                findings.append(
                    _enrich(
                        finding_id="AP_SQL_002",
                        name="unbounded_transaction_leak",
                        lang="sql",
                        dual_id="HP_SQL_002_unit_of_work_transaction_fence",
                        line_num=i,
                        snippet=line.strip(),
                        advice="Enclose operations in atomic Unit of Work transaction context managers.",
                        anti_desc="Unbounded transaction leak placeholder in SQL.",
                    )
                )

    return findings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Pattern catalog and changed files anti-pattern lint")
    repo_root = find_repo_root()
    default_cat = repo_root / "omega_engine_operads" / "patterns"
    parser.add_argument(
        "--catalog",
        default=str(default_cat),
        help="Catalog root directory",
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Audit all git changed files for anti-patterns",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=[],
        help="Specific files to audit for anti-patterns",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Specific file or directory path to audit for anti-patterns",
    )
    parser.add_argument("--report-out", default=None, help="Output path for JSON report")
    parser.add_argument("--check", action="store_true", help="Fail closed (exit 1) if any findings exist")
    args = parser.parse_args(argv)

    catalog = Path(args.catalog)
    catalog_findings: List[Dict[str, Any]] = []
    if catalog.is_dir():
        catalog_findings = audit_catalog(catalog)

    # Load antibodies index for enrichment
    ab_index = _load_antibodies(repo_root)

    # Determine files to audit
    files_to_audit: List[Path] = []
    if args.files:
        for f in args.files:
            fp = Path(f)
            if fp.is_file():
                files_to_audit.append(fp.resolve())
            elif fp.is_dir():
                for sub in fp.rglob("*"):
                    if sub.is_file():
                        files_to_audit.append(sub.resolve())

    if args.path:
        p = Path(args.path)
        if p.is_file():
            files_to_audit.append(p.resolve())
        elif p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file():
                    files_to_audit.append(sub.resolve())

    if args.changed:
        changed_git_files = get_changed_files(repo_root)
        files_to_audit.extend(changed_git_files)

    # Deduplicate files
    seen_files: Set[Path] = set()
    unique_files: List[Path] = []
    for fp in files_to_audit:
        if fp not in seen_files:
            seen_files.add(fp)
            unique_files.append(fp)

    file_findings: List[Dict[str, Any]] = []
    for file_path in unique_files:
        file_findings.extend(audit_file(file_path, repo_root, ab_index=ab_index))

    remediation_suggestions = [
        {
            "file": f["file"],
            "line": f["line"],
            "anti_pattern_id": f["id"],
            "anti_pattern_name": f["pattern_name"],
            "dual_healthy_pattern": f.get("dual_pattern"),
            "matched_snippet": f.get("matched_snippet"),
            "remediation_advice": f.get("remediation_advice"),
            "implementation_pattern": f.get("implementation_pattern"),
            "associated_antibodies": f.get("associated_antibodies", []),
        }
        for f in file_findings
    ]

    total_findings = len(catalog_findings) + len(file_findings)
    payload = {
        "authority_effect": "None",
        "catalog": str(catalog),
        "catalog_findings_count": len(catalog_findings),
        "catalog_findings": catalog_findings,
        "scanned_files_count": len(unique_files),
        "file_findings_count": len(file_findings),
        "file_findings": file_findings,
        "remediation_suggestions": remediation_suggestions,
        "total_findings": total_findings,
    }

    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Anti-pattern catalog findings: {len(catalog_findings)}")
    if unique_files or args.changed:
        print(f"Anti-pattern file findings: {len(file_findings)} (across {len(unique_files)} files)")
        if remediation_suggestions:
            print(f"Remediation suggestions generated: {len(remediation_suggestions)}")

    if args.check and total_findings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

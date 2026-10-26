"""Deposit Consistency Gate Rules.

AuthorityEffect: None.

Nine checks distilled from the 2026-10-12 Zenodo review of the MUB(6) deposit
(``F004_papers/010_mub6``). Each one names a defect that a reviewer found by
hand and that a script can find instead:

1. Claim-ledger evidence (test files, test nodes, Lean modules, Lean
   declarations) must resolve inside the package.
2. Active prose must not call a result "unconditional" while a gap registry in
   the same package still lists an OPEN gap.
3. Relative Markdown links must resolve and stay inside the package.
4. Text files must not carry absolute host paths (``C:\\Users\\...``).
5. Every license named in LICENSE, the paper header, release metadata or
   build manifests must also be named in the README.
6. Release/manifest tests must assert exact custody counts, not floors.
7. The manuscript must not narrate the editing session.
8. Prose of the form "``X.sha256`` contains N entries" must match the file.
9. Deposit verifiers must not swallow ImportError/Exception with ``pass``.

A PASS from any of these rules shows only that the named pattern was not
found. It is not evidence that the paper's mathematics is correct.
"""

from __future__ import annotations

import ast
import json
import posixpath
import re
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)

ARCHIVE_DIR_NAMES = frozenset({"archive", "archives", "_archive"})
SUPERSEDED_NOTICE_NAME = "superseded_notice.md"
MAX_FINDINGS = 50
MAX_TEXT_BYTES = 3 * 1024 * 1024
TEXT_SUFFIXES = frozenset({
    ".md", ".json", ".yaml", ".yml", ".py", ".rs", ".lean", ".tex", ".txt",
    ".toml", ".ipynb", ".sh", ".ps1", ".cfg", ".ini", ".csv", ".bib",
})
CHECKSUM_FILE_NAMES = frozenset({"SHA256SUMS", "MANIFEST.sha256"})

_LEAN_DECL = re.compile(
    r"^[ \t]*(?:@\[[^\]]*\][ \t]*)?(?:(?:private|protected|noncomputable|partial|unsafe)[ \t]+)*"
    r"(?:theorem|lemma|def|abbrev|structure|class|inductive|instance|axiom|opaque)[ \t]+([\w.'!?]+)",
    re.MULTILINE,
)
_MD_LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_FENCED_CODE = re.compile(r"^(`{3,}|~{3,}).*?^\1", re.DOTALL | re.MULTILINE)
_INLINE_CODE = re.compile(r"(`+)(?!`).+?(?<!`)\1")
_HOST_PATH = re.compile(
    r"[A-Za-z]:(?:\\\\|\\|/)Users(?:\\\\|\\|/)[A-Za-z0-9_.-]+"
    r"|/home/[a-z_][a-z0-9_-]*/"
    r"|/Users/[A-Za-z][A-Za-z0-9_.-]*/"
    r"|\.codex(?:\\\\|\\|/)+worktrees"
)
_UNCONDITIONAL_CLAIM = re.compile(
    r"\bunconditional(?:ly)?\b[^.\n]*\b(?:resolved|established|mechani[sz]ed|derived|proved|proven|discharged|settled)\b"
    r"|\b(?:resolved|established|mechani[sz]ed|derived|proved|proven|discharged|settled)\b[^.\n]*\bunconditional(?:ly)?\b"
    r"|\bresolved in the negative\b",
    re.IGNORECASE,
)
_NEGATION = re.compile(
    r"\b(?:not|no longer|withdrawn|superseded|retracted|does not|is open|remains open|historical)\b",
    re.IGNORECASE,
)
_NARRATION = re.compile(
    r"\bat the (?:user'?s |author'?s )?instruction\b"
    r"|\bpublish the changes and stop\b"
    r"|\bas (?:you|the user) (?:asked|requested)\b"
    r"|\bthe user (?:asked|requested|instructed)\b"
    r"|\bin this (?:chat|session|conversation)\b"
    r"|\bI (?:was|have been) (?:asked|instructed)\b",
    re.IGNORECASE,
)
_COUNT_PROSE = re.compile(
    r"`?((?:[\w.-]+/)*(?:[\w.-]+\.sha256|SHA256SUMS))`?\s+(?:contains|has|holds|lists)\s+"
    r"(\d[\d,]*)\s+(?:entries|lines|files|members)",
)
_SPDX_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("Apache-2.0", re.compile(r"Apache-2\.0|Apache License,?\s+(?:Version\s+)?2\.0", re.IGNORECASE)),
    ("CC-BY-4.0", re.compile(r"CC[- ]BY[- ]4\.0|Creative Commons Attribution 4\.0", re.IGNORECASE)),
    ("MIT", re.compile(r"\bMIT License\b|\"MIT\"|\bMIT\b(?=\s*$)", re.MULTILINE)),
    ("BSD-3-Clause", re.compile(r"BSD-3-Clause|BSD 3-Clause", re.IGNORECASE)),
)
_README_SPDX: Dict[str, re.Pattern[str]] = {
    "Apache-2.0": re.compile(r"Apache-2\.0|Apache License,?\s+(?:Version\s+)?2\.0", re.IGNORECASE),
    "CC-BY-4.0": re.compile(r"CC[- ]BY[- ]4\.0|Creative Commons Attribution 4\.0", re.IGNORECASE),
    "MIT": re.compile(r"\bMIT\b"),
    "BSD-3-Clause": re.compile(r"BSD-3-Clause|BSD 3-Clause", re.IGNORECASE),
}
_CUSTODY_TEST_FILE = re.compile(r"(manifest|archive|release|custody|checksum|sha256)", re.IGNORECASE)
_CUSTODY_NAME = re.compile(r"(count|entries|lines|members|files)", re.IGNORECASE)
_FAIL_OPEN_TYPES = frozenset({"Exception", "BaseException", "ImportError", "ModuleNotFoundError"})


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _is_archived(path: str) -> bool:
    return any(part.lower() in ARCHIVE_DIR_NAMES for part in PurePosixPath(path).parts[:-1])


def _superseded_paths(ctx: PaperContext) -> Set[str]:
    """Paths named in backticks inside any ``superseded_notice.md``."""
    named: Set[str] = set()
    for path in ctx.list_paths():
        if PurePosixPath(path).name != SUPERSEDED_NOTICE_NAME:
            continue
        named.add(path)
        for token in re.findall(r"`([^`\s]+)`", ctx.read_text(path)):
            named.add(token.lstrip("./"))
    return named


def _active_markdown(ctx: PaperContext, exempt: Set[str]) -> Iterator[str]:
    for path in ctx.list_paths():
        if path.endswith(".md") and not _is_archived(path) and path not in exempt:
            yield path


def _strip_code(text: str) -> str:
    """Blank fenced and inline code while keeping line numbers stable."""
    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return _INLINE_CODE.sub(blank, _FENCED_CODE.sub(blank, text))


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _normalize_inside(base_dir: str, target: str) -> Optional[str]:
    """Join ``target`` to ``base_dir``; ``None`` when the result leaves the package."""
    joined = posixpath.normpath(posixpath.join(base_dir, target)) if base_dir else posixpath.normpath(target)
    if joined == ".." or joined.startswith("../") or joined.startswith("/"):
        return None
    return "" if joined == "." else joined


def _path_exists(ctx: PaperContext, rel: str, paths: Sequence[str]) -> bool:
    if rel == "" or ctx.has_file(rel):
        return True
    prefix = rel.rstrip("/") + "/"
    return any(p.startswith(prefix) for p in paths)


def _cap(findings: List[RuleFinding]) -> List[RuleFinding]:
    return findings[:MAX_FINDINGS]


def _walk_json(node: Any) -> Iterator[Dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_json(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_json(item)


# ---------------------------------------------------------------------------
# 1. Claim-ledger evidence resolution
# ---------------------------------------------------------------------------


def _load_yaml(text: str) -> Any:
    import yaml  # PyYAML; an ImportError is reported by the caller.

    return yaml.safe_load(text)


def _lean_declarations(text: str) -> Set[str]:
    return {name.rsplit(".", 1)[-1] for name in _LEAN_DECL.findall(text)}


class _LeanSource:
    """Reads Lean modules from the package, or from disk for out-of-package roots."""

    def __init__(self, ctx: PaperContext, ledger_path: str, lean_root: Optional[str]) -> None:
        self.ctx = ctx
        ledger_dir = posixpath.dirname(ledger_path)
        self.inside: Optional[str] = None
        self.outside: Optional[Path] = None
        if lean_root is None:
            self.inside = ""
            return
        self.inside = _normalize_inside(ledger_dir, lean_root)
        if self.inside is None and ctx.package_dir is not None:
            self.outside = (ctx.package_dir / ledger_dir / lean_root).resolve()

    @property
    def escapes(self) -> bool:
        return self.inside is None

    def read_module(self, module: str) -> Optional[str]:
        rel = module.replace(".", "/") + ".lean"
        if self.inside is not None:
            candidates = [posixpath.join(self.inside, rel) if self.inside else rel]
            if not self.inside:
                candidates.append(posixpath.join("lean4", rel))
            for cand in candidates:
                if self.ctx.has_file(cand):
                    return self.ctx.read_text(cand)
            return None
        if self.outside is not None and (self.outside / rel).is_file():
            return (self.outside / rel).read_text(encoding="utf-8", errors="replace")
        return None


def _test_ref_findings(ctx: PaperContext, rule_id: str, sev: RuleSeverity, ledger: str,
                       claim_id: str, refs: Iterable[Any]) -> List[RuleFinding]:
    findings: List[RuleFinding] = []
    for ref in refs:
        if not isinstance(ref, str):
            continue
        file_part, _, node = ref.partition("::")
        if not ctx.has_file(file_part):
            findings.append(RuleFinding(rule_id, sev, f"{claim_id}: test file `{file_part}` is not in the package.",
                                        ledger, remediation="Point the claim at an existing test or drop the reference."))
            continue
        node_name = node.split("::")[-1].split("[")[0] if node else ""
        if node_name and not re.search(rf"^\s*(?:async\s+)?def\s+{re.escape(node_name)}\s*\(",
                                       ctx.read_text(file_part), re.MULTILINE):
            findings.append(RuleFinding(rule_id, sev, f"{claim_id}: test node `{node_name}` is not defined in `{file_part}`.",
                                        ledger, remediation="Use the test function name that exists."))
    return findings


def _lean_ref_findings(source: _LeanSource, rule_id: str, sev: RuleSeverity, ledger: str,
                       claim_id: str, lean: Dict[str, Any]) -> List[RuleFinding]:
    module = lean.get("module")
    if not isinstance(module, str) or not module:
        return []
    text = source.read_module(module)
    if text is None:
        return [RuleFinding(rule_id, sev, f"{claim_id}: Lean module `{module}` was not found under the declared Lean root.",
                            ledger, remediation="Correct the module name or the ledger's lean4_root.")]
    declared = _lean_declarations(text)
    findings: List[RuleFinding] = []
    for theorem in lean.get("theorems") or []:
        if isinstance(theorem, str) and theorem.rsplit(".", 1)[-1] not in declared:
            findings.append(RuleFinding(rule_id, sev, f"{claim_id}: `{theorem}` is not declared in Lean module `{module}`.",
                                        ledger, remediation="Cite a declaration that exists in that module."))
    return findings


class ClaimLedgerEvidenceResolvesRule(BasePaperRule):
    """Claim-ledger test and Lean references must resolve to real files and declarations."""

    @property
    def rule_id(self) -> str:
        return "R_CLAIM_LEDGER_EVIDENCE_RESOLVES"

    @property
    def name(self) -> str:
        return "Claim-Ledger Evidence Resolves"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return ("Every test file, test node, Lean module and Lean declaration cited by a "
                "*_claim_ledger.yaml must exist, and the Lean root must sit inside the package.")

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        ledgers = ctx.find_files(r"_claim_ledger\.ya?ml$")
        if not ledgers:
            return self.pass_result({"ledgers": 0})
        findings: List[RuleFinding] = []
        for ledger in ledgers:
            findings.extend(self._check_ledger(ctx, ledger))
        if findings:
            return self.fail_result(_cap(findings), {"ledgers": len(ledgers), "findings": len(findings)})
        return self.pass_result({"ledgers": len(ledgers)})

    def _check_ledger(self, ctx: PaperContext, ledger: str) -> List[RuleFinding]:
        try:
            data = _load_yaml(ctx.read_text(ledger))
        except ImportError:
            return [RuleFinding(self.rule_id, self.severity, "PyYAML is not installed; the ledger was not checked.", ledger)]
        except Exception as exc:  # yaml.YAMLError and friends
            return [RuleFinding(self.rule_id, self.severity, f"Ledger does not parse: {exc}", ledger)]
        if not isinstance(data, dict):
            return [RuleFinding(self.rule_id, self.severity, "Ledger root is not a mapping.", ledger)]
        lean_root = data.get("lean4_root")
        source = _LeanSource(ctx, ledger, lean_root if isinstance(lean_root, str) else None)
        findings: List[RuleFinding] = []
        if source.escapes:
            findings.append(RuleFinding(
                self.rule_id, self.severity,
                f"lean4_root `{lean_root}` leaves the package; a downloaded deposit cannot replay the Lean evidence.",
                ledger, remediation="Vendor the cited Lean modules into the package, or mark the claims as monorepo-only.",
            ))
        for claim in data.get("claims") or []:
            if isinstance(claim, dict):
                findings.extend(self._check_claim(ctx, source, ledger, claim))
        return findings

    def _check_claim(self, ctx: PaperContext, source: _LeanSource, ledger: str,
                     claim: Dict[str, Any]) -> List[RuleFinding]:
        claim_id = str(claim.get("id", "<no id>"))
        evidence = claim.get("code_evidence") or {}
        tests = evidence.get("tests") if isinstance(evidence, dict) else None
        findings = _test_ref_findings(ctx, self.rule_id, self.severity, ledger, claim_id, tests or [])
        lean = claim.get("lean4")
        if isinstance(lean, dict):
            findings.extend(_lean_ref_findings(source, self.rule_id, self.severity, ledger, claim_id, lean))
        return findings


# ---------------------------------------------------------------------------
# 2. Unconditional prose while a gap is OPEN
# ---------------------------------------------------------------------------


def _open_gaps(ctx: PaperContext) -> List[str]:
    opened: List[str] = []
    for path in ctx.find_files(r"gap_registry[^/]*\.json$"):
        try:
            data = json.loads(ctx.read_text(path))
        except json.JSONDecodeError:
            continue
        for node in _walk_json(data):
            if str(node.get("status", "")).upper() == "OPEN":
                opened.append(str(node.get("id") or node.get("gap_id") or node.get("name") or "?"))
    return opened


class OpenGapResolutionProseRule(BasePaperRule):
    """No 'unconditionally resolved' prose while the package's gap registry lists an OPEN gap."""

    @property
    def rule_id(self) -> str:
        return "R_OPEN_GAP_RESOLUTION_PROSE"

    @property
    def name(self) -> str:
        return "No Unconditional-Resolution Prose With Open Gaps"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return ("When a gap registry lists an OPEN gap, active Markdown outside archive/ and outside "
                "files named in superseded_notice.md must not call a result unconditional or resolved.")

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        gaps = _open_gaps(ctx)
        if not gaps:
            return self.pass_result({"open_gaps": 0})
        findings: List[RuleFinding] = []
        for path in _active_markdown(ctx, _superseded_paths(ctx)):
            for number, line in enumerate(_strip_code(ctx.read_text(path)).splitlines(), start=1):
                if _UNCONDITIONAL_CLAIM.search(line) and not _NEGATION.search(line):
                    findings.append(RuleFinding(
                        self.rule_id, self.severity,
                        f"Unconditional-resolution wording while gaps {sorted(set(gaps))} are OPEN: {line.strip()[:160]}",
                        path, number,
                        remediation="State the premise, or list the file in superseded_notice.md if its bytes are pinned.",
                    ))
        if findings:
            return self.fail_result(_cap(findings), {"open_gaps": sorted(set(gaps))})
        return self.pass_result({"open_gaps": sorted(set(gaps))})


# ---------------------------------------------------------------------------
# 3. Relative Markdown links
# ---------------------------------------------------------------------------


def _link_targets(text: str) -> Iterator[Tuple[int, str]]:
    stripped = _strip_code(text)
    for match in _MD_LINK.finditer(stripped):
        target = match.group(1).strip("<>")
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
            continue
        yield _line_of(stripped, match.start()), target.split("#", 1)[0]


class DepositRelativeLinksResolveRule(BasePaperRule):
    """Relative Markdown links must resolve inside the package."""

    @property
    def rule_id(self) -> str:
        return "R_DEPOSIT_RELATIVE_LINKS_RESOLVE"

    @property
    def name(self) -> str:
        return "Relative Links Resolve Inside Package"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Relative links in active Markdown must point at files or directories inside the package."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        paths = ctx.list_paths()
        findings: List[RuleFinding] = []
        for md in _active_markdown(ctx, set()):
            base = posixpath.dirname(md)
            for line, target in _link_targets(ctx.read_text(md)):
                if not target:
                    continue
                rel = _normalize_inside(base, target)
                if rel is None:
                    findings.append(RuleFinding(self.rule_id, self.severity, f"Link `{target}` leaves the package.", md, line,
                                                remediation="Write the path as code text and say it lives in the source repository."))
                elif not _path_exists(ctx, rel, paths):
                    findings.append(RuleFinding(self.rule_id, self.severity, f"Link `{target}` does not resolve.", md, line,
                                                remediation="Fix the path or remove the link."))
        if findings:
            return self.fail_result(_cap(findings), {"broken_links": len(findings)})
        return self.pass_result()


# ---------------------------------------------------------------------------
# 4. Absolute host paths
# ---------------------------------------------------------------------------


class NoAbsoluteHostPathsRule(BasePaperRule):
    """Text files must not embed absolute paths from an author's machine."""

    @property
    def rule_id(self) -> str:
        return "R_NO_ABSOLUTE_HOST_PATHS"

    @property
    def name(self) -> str:
        return "No Absolute Host Paths"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Text files under 3 MB must not contain C:\\Users\\..., /home/<user>/, /Users/<user>/ or .codex/worktrees."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in ctx.list_paths():
            pure = PurePosixPath(path)
            if pure.suffix.lower() not in TEXT_SUFFIXES or pure.name in CHECKSUM_FILE_NAMES:
                continue
            data = ctx.read_bytes(path)
            if len(data) > MAX_TEXT_BYTES:
                continue
            text = data.decode("utf-8", errors="replace")
            match = _HOST_PATH.search(text)
            if match:
                findings.append(RuleFinding(
                    self.rule_id, self.severity,
                    f"Absolute host path `{match.group(0)}` ({len(_HOST_PATH.findall(text))} occurrence(s)).",
                    path, _line_of(text, match.start()),
                    remediation="Replace the prefix with a repository-relative path such as `<repo>/...`.",
                ))
        if findings:
            return self.fail_result(_cap(findings), {"files": len(findings)})
        return self.pass_result()


# ---------------------------------------------------------------------------
# 5. License declaration consistency
# ---------------------------------------------------------------------------


def _spdx_in(text: str) -> Set[str]:
    return {spdx for spdx, pattern in _SPDX_PATTERNS if pattern.search(text)}


def _license_sources(ctx: PaperContext) -> Dict[str, Set[str]]:
    sources: Dict[str, Set[str]] = {}
    if ctx.has_file("LICENSE"):
        sources["LICENSE"] = _spdx_in("\n".join(ctx.read_text("LICENSE").splitlines()[:5]))
    for path in ("paper.md", "papers/paper.md"):
        if ctx.has_file(path):
            header = [ln for ln in ctx.read_text(path).splitlines()[:40] if "license" in ln.lower()]
            sources[path] = _spdx_in("\n".join(header))
    for path in ctx.find_files(r"(^|/)(zenodo[^/]*\.json|release_manifest\.json)$"):
        try:
            data = json.loads(ctx.read_text(path))
        except json.JSONDecodeError:
            continue
        values = [str(n.get(k)) for n in _walk_json(data) for k in ("license", "manuscript_license") if n.get(k)]
        sources[path] = _spdx_in("\n".join(values))
    for path in ctx.find_files(r"(^|/)(Cargo\.toml|pyproject\.toml)$"):
        lines = [ln for ln in ctx.read_text(path).splitlines() if re.match(r"\s*license\s*=", ln)]
        sources[path] = _spdx_in("\n".join(lines))
    return {k: v for k, v in sources.items() if v}


class LicenseDeclarationConsistencyRule(BasePaperRule):
    """Every license declared anywhere in the package must be declared in the README."""

    @property
    def rule_id(self) -> str:
        return "R_LICENSE_DECLARATION_CONSISTENCY"

    @property
    def name(self) -> str:
        return "License Declarations Consistent"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return ("Licenses named by LICENSE, the paper header, release JSON and build manifests must each be "
                "named in README.md, so readers see which license covers text and which covers code.")

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        sources = _license_sources(ctx)
        if not sources:
            return self.pass_result({"licenses": []})
        readme = ctx.read_text("README.md") if ctx.has_file("README.md") else ""
        findings: List[RuleFinding] = []
        for source, spdx_ids in sorted(sources.items()):
            for spdx in sorted(spdx_ids):
                if not _README_SPDX[spdx].search(readme):
                    findings.append(RuleFinding(
                        self.rule_id, self.severity,
                        f"`{source}` declares {spdx}, but README.md does not name it.", "README.md",
                        remediation="Add a license table to README.md that maps each material to its license.",
                    ))
        details = {"licenses": {k: sorted(v) for k, v in sources.items()}}
        return self.fail_result(findings, details) if findings else self.pass_result(details)


# ---------------------------------------------------------------------------
# 6. Floor assertions on custody counts
# ---------------------------------------------------------------------------


def _mentions_custody_quantity(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == "len":
            return True
        if isinstance(sub, ast.Name) and _CUSTODY_NAME.search(sub.id):
            return True
        if isinstance(sub, ast.Attribute) and _CUSTODY_NAME.search(sub.attr):
            return True
    return False


def _is_large_int(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and type(node.value) is int and node.value >= 10


def _floor_asserts(tree: ast.AST) -> Iterator[ast.Assert]:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
            continue
        cmp = node.test
        if len(cmp.ops) != 1 or not isinstance(cmp.ops[0], (ast.GtE, ast.LtE, ast.Gt, ast.Lt)):
            continue
        left, right = cmp.left, cmp.comparators[0]
        if (_is_large_int(right) and _mentions_custody_quantity(left)) or (
            _is_large_int(left) and _mentions_custody_quantity(right)
        ):
            yield node


class NoFloorAssertionsOnCustodyCountsRule(BasePaperRule):
    """Release/manifest tests must assert exact counts, not lower or upper bounds."""

    @property
    def rule_id(self) -> str:
        return "R_NO_FLOOR_ASSERTIONS_ON_CUSTODY_COUNTS"

    @property
    def name(self) -> str:
        return "Exact Custody Counts In Tests"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return ("In test files about manifests, archives or releases, `len(x) >= N` style assertions on "
                "entry counts let silent additions or losses pass; assert equality with a recorded count.")

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in ctx.find_files(r"(^|/)test_[^/]*\.py$"):
            if _is_archived(path) or not _CUSTODY_TEST_FILE.search(PurePosixPath(path).name):
                continue
            try:
                tree = ast.parse(ctx.read_text(path))
            except SyntaxError:
                continue
            for node in _floor_asserts(tree):
                findings.append(RuleFinding(
                    self.rule_id, self.severity, f"Floor assertion on a custody count: `{ast.unparse(node.test)}`.",
                    path, node.lineno,
                    remediation="Record the exact count in the release manifest and assert equality with it.",
                ))
        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# 7. Session narration in the manuscript
# ---------------------------------------------------------------------------


def _manuscripts(ctx: PaperContext) -> List[str]:
    found = [p for p in ctx.list_paths() if PurePosixPath(p).name == "paper.md" and not _is_archived(p)]
    primary = ctx.get_primary_markdown_path()
    if primary and primary not in found:
        found.append(primary)
    return found


class NoSessionNarrationInManuscriptRule(BasePaperRule):
    """The manuscript must not describe the editing session or instructions given to an agent."""

    @property
    def rule_id(self) -> str:
        return "R_NO_SESSION_NARRATION_IN_MANUSCRIPT"

    @property
    def name(self) -> str:
        return "No Session Narration In Manuscript"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.CLAIM_HYGIENE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Phrases such as 'at the instruction to publish' or 'the user asked' do not belong in a manuscript."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in _manuscripts(ctx):
            text = _strip_code(ctx.read_text(path))
            for match in _NARRATION.finditer(text):
                findings.append(RuleFinding(
                    self.rule_id, self.severity, f"Session narration: `{match.group(0)}`.", path, _line_of(text, match.start()),
                    remediation="State what was run and its result; drop who asked for it.",
                ))
        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# 8. Manifest counts stated in prose
# ---------------------------------------------------------------------------


def _resolve_checksum_name(ctx: PaperContext, name: str, paths: Sequence[str]) -> Optional[str]:
    if "/" in name:
        return name if ctx.has_file(name) else None
    matches = [p for p in paths if PurePosixPath(p).name == name]
    return matches[0] if len(matches) == 1 else None


def _entry_count(text: str) -> int:
    return sum(1 for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#"))


class ManifestCountProseMatchesRule(BasePaperRule):
    """'X.sha256 contains N entries' in prose must equal the file's entry count."""

    @property
    def rule_id(self) -> str:
        return "R_MANIFEST_COUNT_PROSE_MATCHES"

    @property
    def name(self) -> str:
        return "Manifest Counts In Prose Match Files"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PACKAGING

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "A stated entry count for a checksum file must equal its number of non-empty, non-comment lines."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        paths = ctx.list_paths()
        findings: List[RuleFinding] = []
        for md in _active_markdown(ctx, set()):
            text = ctx.read_text(md)
            for match in _COUNT_PROSE.finditer(text):
                target = _resolve_checksum_name(ctx, match.group(1), paths)
                if target is None:
                    continue
                stated, actual = int(match.group(2).replace(",", "")), _entry_count(ctx.read_text(target))
                if stated != actual:
                    findings.append(RuleFinding(
                        self.rule_id, self.severity, f"Prose says `{match.group(1)}` has {stated} entries; it has {actual}.",
                        md, _line_of(text, match.start()), remediation="Update the stated count.",
                    ))
        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


# ---------------------------------------------------------------------------
# 9. Fail-open deposit verifiers
# ---------------------------------------------------------------------------


def _handler_type_names(handler: ast.ExceptHandler) -> Set[str]:
    if handler.type is None:
        return {"<bare>"}
    nodes = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return {n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else "?" for n in nodes}


def _body_is_silent(body: Sequence[ast.stmt]) -> bool:
    return all(
        isinstance(stmt, (ast.Pass, ast.Continue))
        or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
        for stmt in body
    )


class VerifierNoFailOpenRule(BasePaperRule):
    """Deposit verifiers must not silence ImportError/Exception with a bare ``pass``."""

    @property
    def rule_id(self) -> str:
        return "R_VERIFIER_NO_FAIL_OPEN"

    @property
    def name(self) -> str:
        return "Verifiers Fail Closed"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.PYTHON_CODE

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return ("In verify*.py outside tests/, an `except` for ImportError, Exception, BaseException or a bare "
                "except whose body is only `pass`/`continue` turns a skipped check into a pass.")

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        findings: List[RuleFinding] = []
        for path in ctx.find_files(r"(^|/)verify[^/]*\.py$"):
            if _is_archived(path) or "/tests/" in f"/{path}":
                continue
            try:
                tree = ast.parse(ctx.read_text(path))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler) or not _body_is_silent(node.body):
                    continue
                names = _handler_type_names(node)
                if names & (_FAIL_OPEN_TYPES | {"<bare>"}):
                    findings.append(RuleFinding(
                        self.rule_id, self.severity, f"Silent `except {', '.join(sorted(names))}` in a verifier.",
                        path, node.lineno,
                        remediation="Record an error, or require an explicit skip flag and print SKIPPED.",
                    ))
        if findings:
            return self.fail_result(_cap(findings))
        return self.pass_result()


DEPOSIT_CONSISTENCY_RULES: Tuple[type[BasePaperRule], ...] = (
    ClaimLedgerEvidenceResolvesRule,
    OpenGapResolutionProseRule,
    DepositRelativeLinksResolveRule,
    NoAbsoluteHostPathsRule,
    LicenseDeclarationConsistencyRule,
    NoFloorAssertionsOnCustodyCountsRule,
    NoSessionNarrationInManuscriptRule,
    ManifestCountProseMatchesRule,
    VerifierNoFailOpenRule,
)

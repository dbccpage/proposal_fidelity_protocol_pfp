#!/usr/bin/env python3
"""Rule gate: checks the host rule trees against the machine-readable rule register.

The register is ``skill_operad/yaml/rules_registry.yaml``; the law it enforces is
``rules/core/rl_rules_as_code_registry.md``. Each check returns typed findings, and
``run_gate`` reports invariant counts by status so the share of rules that are still
``CANDIDATE`` (prose without an executable check) stays visible.

AuthorityEffect: None. Reads the tree; only ``--write-register`` and ``--write-scope`` edit
files: the register table inside the register documents, and the ``paths`` frontmatter of
registered rule files (see ``rule_scope``).
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

from omega_engine_operads.skill_operad.skill_compiler import rule_scope

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "yaml" / "rules_registry.yaml"
REGISTER_HEADING = "## Progressive Disclosure & Domain Invariant Rule Register"
REGISTER_TABLE_HEADER = (
    "| Domain Topic | Canonical Rule Path | Primary Governance Skills | Key Governing Invariants |\n"
    "|---|---|---|---|\n"
)
STATUSES = frozenset({"ENFORCED", "PARTIAL", "CANDIDATE"})
INVARIANT_ID = re.compile(r"\b(RULE_[A-Z0-9_]+_[0-9]{3}|AGT-[A-Z]+-[0-9]{4})\b")
RULE_FILENAME = re.compile(r"rl_[a-z0-9_]+\.md")
HEADER_LINE = re.compile(r"^\*\*AuthorityEffect:\*\* None\.[ \t]*$", re.MULTILINE)
MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")
FENCE_OPEN = re.compile(r"^(?P<marker>`{3,}|~{3,})")
SKIPPED_LINK_PREFIXES = ("http://", "https://", "mailto:", "#")

#: Relative POSIX path of a rule file -> its raw bytes, read once per gate run.
RuleTree = dict[str, bytes]


class RegistryError(ValueError):
    """The register itself is malformed; no rule check can be trusted."""


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    message: str

    def render(self) -> str:
        return f"[{self.code}] {self.path}: {self.message}"


@dataclass(frozen=True)
class GateReport:
    findings: tuple[Finding, ...]
    rule_count: int
    status_counts: tuple[tuple[str, int], ...]
    always_loaded_bytes: int = 0

    @property
    def passed(self) -> bool:
        return not self.findings


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RegistryError(message)


def _validate_invariants(owner: str, invariants: object) -> None:
    _require(type(invariants) is list, f"{owner}: invariants must be a list")
    for invariant in invariants:  # type: ignore[union-attr]
        _require(type(invariant) is dict, f"{owner}: each invariant must be a mapping")
        _require(type(invariant.get("id")) is str, f"{owner}: invariant id must be a string")
        _require(type(invariant.get("status")) is str, f"{owner}: invariant status must be a string")
        for optional in ("enforced_by", "scope", "note"):
            value = invariant.get(optional)
            _require(value is None or type(value) is str, f"{owner}: {optional} must be a string")


def load_registry(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise RegistryError(f"cannot read register {path}: {exc}") from exc
    _require(type(data) is dict, "register must be a mapping")
    _require(data.get("authority_effect") == "None", "register authority_effect must be 'None'")
    for key, kind in (
        ("rules_root", str),
        ("host_roots", list),
        ("size_ceiling_bytes", int),
        ("register_documents", list),
        ("taxonomy", list),
        ("rules", list),
        ("external_sources", list),
    ):
        _require(type(data.get(key)) is kind, f"register field {key!r} must be {kind.__name__}")
    _require(len(data["host_roots"]) >= 1, "register needs at least one host root")
    for key in ("host_roots", "register_documents", "taxonomy"):
        _require(all(type(item) is str for item in data[key]), f"{key} entries must be strings")
    paths: list[str] = []
    for entry in data["rules"]:
        _require(type(entry) is dict, "every rule entry must be a mapping")
        for field in ("path", "topic", "summary"):
            _require(type(entry.get(field)) is str, f"rule entry {field!r} must be a string")
        skills = entry.get("skills")
        _require(
            type(skills) is list and all(type(s) is str for s in skills),
            f"{entry['path']}: skills must be a list of strings",
        )
        _validate_invariants(entry["path"], entry.get("invariants"))
        load_paths = entry.get("load_paths", [])
        _require(
            type(load_paths) is list and all(type(g) is str and g for g in load_paths),
            f"{entry['path']}: load_paths must be a list of non-empty strings",
        )
        paths.append(entry["path"])
    _require(len(set(paths)) == len(paths), "rule paths must be unique")
    ceiling = data.get("always_loaded_ceiling_bytes")
    _require(ceiling is None or type(ceiling) is int, "always_loaded_ceiling_bytes must be an int")
    for source in data["external_sources"]:
        _require(type(source) is dict and type(source.get("path")) is str,
                 "every external source must be a mapping with a string path")
        _validate_invariants(source["path"], source.get("invariants"))
    return data


def _invariants(entries: list[dict]) -> list[tuple[str, dict]]:
    return [(entry["path"], invariant) for entry in entries for invariant in entry["invariants"]]


def read_rule_tree(root: Path) -> RuleTree:
    """Read every ``*.md`` under one host's rules directory, once."""
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*.md"))
        if path.is_file()
    }


def _decoded(tree: RuleTree) -> dict[str, str]:
    texts: dict[str, str] = {}
    for relative, raw in tree.items():
        try:
            texts[relative] = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
    return texts


def check_registration(tree: RuleTree, registry: dict) -> list[Finding]:
    registered = {entry["path"] for entry in registry["rules"]}
    findings = [
        Finding("R1_UNREGISTERED", path, "rule file has no register entry")
        for path in sorted(set(tree) - registered)
    ]
    findings += [
        Finding("R1_MISSING_FILE", path, "register entry names no file")
        for path in sorted(registered - set(tree))
    ]
    return findings


def check_size(tree: RuleTree, registry: dict) -> list[Finding]:
    """R2 measures the rule body; the generated ``paths:`` frontmatter is not counted."""
    ceiling = registry["size_ceiling_bytes"]
    findings: list[Finding] = []
    for relative, raw in tree.items():
        size = len(rule_scope.FRONTMATTER.sub("", raw.decode("utf-8", errors="replace"), count=1).encode("utf-8"))
        if size > ceiling:
            findings.append(
                Finding("R2_OVERSIZE", relative, f"{size} bytes exceeds the {ceiling}-byte ceiling")
            )
    return findings


def check_hygiene(tree: RuleTree) -> list[Finding]:
    findings: list[Finding] = []
    texts = _decoded(tree)
    for relative, raw in tree.items():
        if RULE_FILENAME.fullmatch(PurePosixPath(relative).name) is None:
            findings.append(
                Finding("R3_FILENAME", relative, "filename must be lowercase snake case rl_*.md")
            )
        if raw.startswith(b"\xef\xbb\xbf"):
            findings.append(Finding("R3_BOM", relative, "file starts with a UTF-8 BOM"))
        if relative not in texts:
            findings.append(Finding("R3_ENCODING", relative, "file is not valid UTF-8"))
        elif HEADER_LINE.search(texts[relative]) is None:
            findings.append(
                Finding("R3_HEADER", relative, "missing the line '**AuthorityEffect:** None.'")
            )
    return findings


def strip_fenced_code(text: str) -> str:
    """Blank out fenced code blocks, including indented and blockquoted fences.

    A fence opens with three or more backticks or tildes after optional indentation and
    ``>`` markers, and closes with at least as many of the same character.
    """
    kept: list[str] = []
    open_marker: str | None = None
    for line in text.split("\n"):
        stripped = line.lstrip(" \t>")
        match = FENCE_OPEN.match(stripped)
        if open_marker is None:
            if match is not None:
                open_marker = match.group("marker")
                kept.append("")
                continue
            kept.append(line)
        else:
            if (
                match is not None
                and match.group("marker")[0] == open_marker[0]
                and len(match.group("marker")) >= len(open_marker)
                and not stripped[len(match.group("marker")) :].strip()
            ):
                open_marker = None
            kept.append("")
    return "\n".join(kept)


def _relative_link_exists(folder: Path, local: str) -> bool:
    """Resolve a link through exact directory-entry names.

    ``Path.exists`` folds case on Windows, so a wrong-case target would pass
    on the machine that edits the rules and fail on a case-sensitive tree.
    """
    current = folder
    parts = [part for part in PurePosixPath(local).parts if part not in {"", "."}]
    if not parts:
        return False
    for part in parts:
        if part == "..":
            current = current.parent
            continue
        try:
            match = next((child for child in current.iterdir() if child.name == part), None)
        except OSError:
            return False
        if match is None:
            return False
        current = match
    return current.exists()


def check_links(tree: RuleTree, rules_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for relative, text in _decoded(tree).items():
        folder = (rules_dir / relative).parent
        for match in MARKDOWN_LINK.finditer(strip_fenced_code(text)):
            target = match.group(1)
            if target.startswith(SKIPPED_LINK_PREFIXES):
                continue
            if target.startswith("file:"):
                findings.append(
                    Finding("R4_HOST_ABSOLUTE_LINK", relative, f"link target {target!r}")
                )
                continue
            local = target.split("#", 1)[0]
            if local and not _relative_link_exists(folder, local):
                findings.append(Finding("R4_BROKEN_LINK", relative, f"link target {target!r}"))
    return findings


def check_taxonomy(rules_dir: Path, registry: dict) -> list[Finding]:
    folders = set(registry["taxonomy"])
    findings: list[Finding] = []
    for entry in registry["rules"]:
        parts = PurePosixPath(entry["path"]).parts
        if len(parts) != 2 or parts[0] not in folders:
            findings.append(
                Finding("R5_TAXONOMY", entry["path"], "rule must sit in exactly one taxonomy folder")
            )
    if rules_dir.is_dir():
        for child in sorted(rules_dir.iterdir()):
            if child.is_dir() and child.name not in folders:
                findings.append(
                    Finding("R5_TAXONOMY", child.name, "folder is not in the closed taxonomy")
                )
    return findings


def _defines_symbol(path: Path, symbol: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        tree = ast.parse(text, filename=str(path))
        return any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == symbol
            for node in ast.walk(tree)
        )
    if path.suffix == ".rs":
        return re.search(rf"\bfn\s+{re.escape(symbol)}\b", text) is not None
    return symbol in text


def _check_enforcement(repo_root: Path, owner: str, invariant: dict) -> list[Finding]:
    identifier = invariant["id"]
    status = invariant["status"]
    if status not in STATUSES:
        return [Finding("R6_STATUS", owner, f"{identifier}: unknown status {status!r}")]
    enforced_by = invariant.get("enforced_by")
    if status == "CANDIDATE":
        if enforced_by is not None:
            return [Finding("R6_STATUS", owner, f"{identifier}: CANDIDATE must not name enforced_by")]
        return []
    if not enforced_by:
        return [Finding("R6_ENFORCED_BY", owner, f"{identifier}: {status} needs enforced_by")]
    if status == "PARTIAL" and not invariant.get("scope"):
        return [Finding("R6_SCOPE", owner, f"{identifier}: PARTIAL needs a scope statement")]
    file_part, _, symbol = enforced_by.partition("::")
    target = repo_root / Path(*PurePosixPath(file_part).parts)
    if not target.is_file():
        return [Finding("R6_ENFORCED_BY", owner, f"{identifier}: {file_part} does not exist")]
    try:
        defined = not symbol or _defines_symbol(target, symbol)
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        return [Finding("R6_ENFORCED_BY", owner, f"{identifier}: cannot read {file_part}: {exc}")]
    if not defined:
        return [
            Finding("R6_ENFORCED_BY", owner, f"{identifier}: {symbol} is not defined in {file_part}")
        ]
    return []


def _claim_invariant(
    findings: list[Finding],
    owners: dict[str, list[str]],
    repo_root: Path,
    owner: str,
    invariant: dict,
    body: str | None,
) -> None:
    """Record one owner. Rules and external sources share this map."""
    identifier = invariant["id"]
    if INVARIANT_ID.fullmatch(identifier) is None:
        findings.append(Finding("R6_ID", owner, f"malformed invariant id {identifier!r}"))
        return
    owners.setdefault(identifier, []).append(owner)
    findings += _check_enforcement(repo_root, owner, invariant)
    if body is not None and identifier not in body:
        findings.append(
            Finding("R6_NOT_IN_OWNER", owner, f"{identifier} does not appear in its owner")
        )


def check_ownership(repo_root: Path, tree: RuleTree, registry: dict) -> list[Finding]:
    findings: list[Finding] = []
    texts = _decoded(tree)
    owners: dict[str, list[str]] = {}
    for owner, invariant in _invariants(registry["rules"]):
        _claim_invariant(findings, owners, repo_root, owner, invariant, texts.get(owner))
    for source in registry["external_sources"]:
        source_path = repo_root / Path(*PurePosixPath(source["path"]).parts)
        try:
            text = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            findings.append(Finding("R6_EXTERNAL_SOURCE", source["path"], "external source unreadable"))
            continue
        for invariant in source["invariants"]:
            _claim_invariant(findings, owners, repo_root, source["path"], invariant, text)
    for identifier, owner_paths in sorted(owners.items()):
        if len(owner_paths) > 1:
            findings.append(
                Finding("R6_DUPLICATE_OWNER", identifier, f"owned by {sorted(owner_paths)}")
            )
    seen = {match for text in texts.values() for match in INVARIANT_ID.findall(text)}
    for identifier in sorted(seen - set(owners)):
        findings.append(Finding("R6_UNOWNED", identifier, "invariant id appears in rules but has no owner"))
    return findings


def check_host_parity(canon: RuleTree, mirrors: dict[str, RuleTree]) -> list[Finding]:
    findings: list[Finding] = []
    for host, mirror in mirrors.items():
        for relative in sorted(set(canon) | set(mirror)):
            if relative not in mirror:
                findings.append(Finding("R7_HOST_MISSING", f"{host}/{relative}", "absent in mirror"))
            elif relative not in canon:
                findings.append(Finding("R7_HOST_EXTRA", f"{host}/{relative}", "absent in canon"))
            elif canon[relative] != mirror[relative]:
                findings.append(Finding("R7_HOST_DRIFT", f"{host}/{relative}", "bytes differ from canon"))
    return findings


def _register_table(text: str) -> tuple[int, int] | None:
    """Locate the register table: its header plus every contiguous ``|`` row that follows."""
    start = text.find(REGISTER_HEADING)
    if start < 0:
        return None
    section_end = text.find("\n## ", start + len(REGISTER_HEADING))
    section_end = len(text) if section_end < 0 else section_end
    table_start = text.find(REGISTER_TABLE_HEADER, start, section_end)
    if table_start < 0:
        return None
    cursor = table_start + len(REGISTER_TABLE_HEADER)
    while cursor < section_end and text.startswith("|", cursor):
        line_end = text.find("\n", cursor)
        cursor = len(text) if line_end < 0 else line_end + 1
    return table_start, cursor


def render_register_table(registry: dict) -> str:
    """Render the register table rows, in register order, from the register entries."""
    root = registry["rules_root"]
    rows = []
    for entry in registry["rules"]:
        path = f"omega_engine_operads/{root}/{entry['path']}"
        skills = ", ".join(f"`{skill}`" for skill in entry["skills"])
        rows.append(f"| **{entry['topic']}** | [`{path}`]({path}) | {skills} | {entry['summary']} |")
    return REGISTER_TABLE_HEADER + "\n".join(rows) + "\n"


def check_register_documents(repo_root: Path, registry: dict) -> list[Finding]:
    documents = registry["register_documents"]
    findings: list[Finding] = []
    payloads: dict[str, bytes] = {}
    for document in documents:
        path = repo_root / Path(*PurePosixPath(document).parts)
        if not path.is_file():
            findings.append(Finding("R8_REGISTER_MISSING", document, "register document missing"))
            continue
        payloads[document] = path.read_bytes()
    if len(set(payloads.values())) > 1:
        findings.append(
            Finding("R8_REGISTER_DRIFT", ", ".join(documents), "register documents are not byte-identical")
        )
    expected = render_register_table(registry)
    for document, payload in payloads.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("R8_REGISTER_ENCODING", document, "register document is not UTF-8"))
            continue
        span = _register_table(text)
        if span is None:
            findings.append(Finding("R8_REGISTER_TABLE", document, "register table not found"))
        elif text[span[0] : span[1]] != expected:
            findings.append(
                Finding("R8_REGISTER_TABLE", document, "register table does not equal the register")
            )
    return findings


def write_register(repo_root: Path, registry: dict) -> list[str]:
    """Replace the register table in every register document with the rendered table."""
    table = render_register_table(registry)
    written = []
    for document in registry["register_documents"]:
        path = repo_root / Path(*PurePosixPath(document).parts)
        text = path.read_text(encoding="utf-8")
        span = _register_table(text)
        if span is None:
            raise RegistryError(f"{document}: register table not found")
        path.write_text(text[: span[0]] + table + text[span[1] :], encoding="utf-8", newline="\n")
        written.append(document)
    return written


def run_gate(repo_root: Path, registry_path: Path = DEFAULT_REGISTRY) -> GateReport:
    registry = load_registry(registry_path)
    hosts = registry["host_roots"]
    owned_estate = (repo_root / "omega_engine_operads").is_dir()
    source = repo_root / "omega_engine_operads" / registry["rules_root"]
    rules_dir = source if owned_estate else repo_root / hosts[0] / registry["rules_root"]
    canon = read_rule_tree(rules_dir)
    compared_hosts = hosts if owned_estate else hosts[1:]
    mirrors = {host: read_rule_tree(repo_root / host / registry["rules_root"]) for host in compared_hosts}
    findings: list[Finding] = []
    findings += check_registration(canon, registry)
    findings += check_size(canon, registry)
    findings += check_hygiene(canon)
    findings += check_links(canon, rules_dir)
    findings += check_taxonomy(rules_dir, registry)
    findings += check_ownership(repo_root, canon, registry)
    findings += check_host_parity(canon, mirrors)
    findings += check_register_documents(repo_root, registry)
    scope_findings, always_loaded = rule_scope.check_load_scope(repo_root, _decoded(canon), registry)
    findings += [Finding(f.code, f.path, f.message) for f in scope_findings]
    counts = Counter(invariant["status"] for _, invariant in _invariants(registry["rules"]))
    for source in registry["external_sources"]:
        counts.update(invariant["status"] for invariant in source["invariants"])
    return GateReport(
        findings=tuple(findings),
        rule_count=len(registry["rules"]),
        status_counts=tuple(sorted(counts.items())),
        always_loaded_bytes=always_loaded,
    )


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    raise RegistryError(f"no repository root with .git and .agents above {here}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument(
        "--write-register",
        action="store_true",
        help="rewrite the register table in the register documents, then run the gate",
    )
    parser.add_argument(
        "--write-scope",
        action="store_true",
        help="rewrite the paths frontmatter of every host rule from register load_paths, then run the gate",
    )
    args = parser.parse_args(argv)
    try:
        root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
        registry_path = Path(args.registry)
        if args.write_register:
            for document in write_register(root, load_registry(registry_path)):
                print(f"wrote register table: {document}")
        if args.write_scope:
            for written in rule_scope.write_frontmatter(root, load_registry(registry_path)):
                print(f"wrote scope frontmatter: {written}")
        report = run_gate(root, registry_path)
    except RegistryError as exc:
        print(f"REFUSED: {exc}")
        return 2
    print(f"=== RULE GATE ({report.rule_count} registered rules) ===")
    for finding in report.findings:
        print(f"  {finding.render()}")
    counts = ", ".join(f"{status}={count}" for status, count in report.status_counts)
    print(f"invariants: {counts}")
    print(f"always-loaded rule bytes: {report.always_loaded_bytes}")
    if report.findings:
        print(f"FAIL: {len(report.findings)} finding(s).")
        return 1
    print("PASS: rule trees match the register.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

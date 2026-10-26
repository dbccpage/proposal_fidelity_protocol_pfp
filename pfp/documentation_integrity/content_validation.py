"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from .domain import (
    DOC_ROOT,
    HEADING_RE,
    HTML_ANCHOR_RE,
    HTML_IMAGE_RE,
    IMAGE_LINK_RE,
    INLINE_LINK_RE,
    MARKDOWN_SUFFIXES,
    MOJIBAKE_MARKERS,
    Findings,
    absolute_repo_path,
    repo_relative,
    yaml,
)
from .git_adapter import git_changed_paths


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, int, str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0, None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            payload = "\n".join(lines[1:index])
            if yaml is None:
                return None, index + 1, "PyYAML is required to validate frontmatter"
            try:
                value = yaml.safe_load(payload)
            except Exception as error:  # yaml exposes several exception classes.
                return None, index + 1, f"invalid YAML frontmatter: {error}"
            if not isinstance(value, dict):
                return None, index + 1, "frontmatter must be a YAML object"
            return value, index + 1, None
    return None, 0, "frontmatter opening delimiter has no closing delimiter"


def frontmatter_is_governed(text: str, contract: dict[str, Any]) -> bool:
    if not text.startswith("---"):
        return False
    key = contract["canonical_frontmatter"]["contract_key"]
    return re.search(rf"(?m)^{re.escape(key)}\s*:", text) is not None


def canonical_markdown_paths(repo_root: Path, contract: dict[str, Any]) -> list[str]:
    documentation_root = contract["documentation_root"].rstrip("/")
    raw_prefix = contract["raw_archive_prefix"].rstrip("/") + "/"
    copy_prefixes = tuple(
        copy_set["destination_prefix"].rstrip("/") + "/"
        for copy_set in contract["education_copy_sets"]
    )
    paths: list[str] = []
    for path in absolute_repo_path(repo_root, documentation_root).rglob("*"):
        if not path.is_file() or path.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        relative = repo_relative(repo_root, path)
        if (
            relative.startswith(raw_prefix)
            or relative.startswith(copy_prefixes)
            or "/_meta/" in relative
            or "/scripts/" in relative
        ):
            continue
        paths.append(relative)
    return sorted(paths)


def selected_content_paths(
    repo_root: Path,
    contract: dict[str, Any],
    scope: str,
    changed_base: str | None,
    include_changed_content: bool,
) -> list[str]:
    candidates = canonical_markdown_paths(repo_root, contract)
    archive_records_prefix = contract["documentation_root"].rstrip("/") + "/archive/records/"
    selected: set[str] = set()
    if scope == "all":
        selected.update(candidates)
    else:
        for path in candidates:
            # A record manifest and raw-hash check cover the large generated
            # archive estate in foundation CI. Full release validation still
            # reaches every record through --strict-content.
            if path.startswith(archive_records_prefix):
                continue
            try:
                text = absolute_repo_path(repo_root, path).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if frontmatter_is_governed(text, contract):
                selected.add(path)
    if changed_base and include_changed_content:
        changed = git_changed_paths(repo_root, changed_base)
        selected.update(path for path in candidates if path in changed)
    return sorted(selected)


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    anchors.update(match.group(2) for match in HTML_ANCHOR_RE.finditer(text))
    counts: defaultdict[str, int] = defaultdict(int)
    in_fence = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = re.sub(r"[`*_~]", "", match.group(2)).strip().lower()
        title = unicodedata.normalize("NFKD", title)
        title = "".join(char for char in title if char.isalnum() or char in {" ", "-"})
        slug = re.sub(r"[\s-]+", "-", title).strip("-")
        occurrence = counts[slug]
        counts[slug] += 1
        anchors.add(slug if occurrence == 0 else f"{slug}-{occurrence}")
    return anchors


def strip_code_fences(text: str) -> list[str]:
    result: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
            result.append("")
        elif in_fence:
            result.append("")
        else:
            result.append(line)
    return result


def resolve_local_link(
    repo_root: Path, source_path: str, raw_target: str
) -> tuple[Path | None, str | None]:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    target = re.split(r"\s+(?=[\"'])", target, maxsplit=1)[0]
    parsed = urlsplit(target)
    if (
        parsed.scheme
        or parsed.netloc
        or target.startswith(("#", "mailto:", "data:", "javascript:"))
    ):
        if target.startswith("#"):
            return absolute_repo_path(repo_root, source_path), unquote(target[1:])
        return None, None
    location = unquote(parsed.path)
    fragment = unquote(parsed.fragment) if parsed.fragment else None
    if not location:
        return absolute_repo_path(repo_root, source_path), fragment
    if location.startswith("/"):
        target_path = repo_root.joinpath(*location.lstrip("/").split("/"))
    else:
        target_path = absolute_repo_path(repo_root, source_path).parent.joinpath(
            *location.split("/")
        )
    return target_path.resolve(), fragment


def check_links(repo_root: Path, source_path: str, text: str, findings: Findings) -> None:
    lines = strip_code_fences(text)
    visible = "\n".join(lines)
    for match in list(INLINE_LINK_RE.finditer(visible)) + list(IMAGE_LINK_RE.finditer(visible)):
        raw_target = match.group(1) if match.re is INLINE_LINK_RE else match.group(2)
        target_path, fragment = resolve_local_link(repo_root, source_path, raw_target)
        if target_path is None:
            continue
        if not target_path.exists() or not target_path.is_file():
            findings.error(f"Broken local link in {source_path}: {raw_target}")
            continue
        if fragment and target_path.suffix.lower() in MARKDOWN_SUFFIXES:
            try:
                target_text = target_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                findings.error(
                    f"Cannot check non-UTF-8 anchor target in {source_path}: {raw_target}"
                )
                continue
            if fragment not in heading_anchors(target_text):
                findings.error(f"Broken anchor in {source_path}: {raw_target}")


def nontrivial_visual_text(value: str) -> bool:
    simplified = re.sub(r"\s+", " ", value.strip().lower())
    return len(simplified) >= 8 and simplified not in {
        "image",
        "diagram",
        "figure",
        "screenshot",
        "graphic",
    }


def check_visual_descriptions(source_path: str, text: str, findings: Findings) -> None:
    lines = strip_code_fences(text)
    for index, line in enumerate(lines):
        for match in IMAGE_LINK_RE.finditer(line):
            alt = match.group(1)
            context = "\n".join(lines[max(0, index - 2) : min(len(lines), index + 3)]).lower()
            if not nontrivial_visual_text(alt):
                findings.error(f"Image in {source_path} needs descriptive alt text")
            if not re.search(r"(?:visual|diagram|figure) description\s*:", context):
                findings.error(f"Image in {source_path} needs an adjacent visual description")
        for match in HTML_IMAGE_RE.finditer(line):
            if not nontrivial_visual_text(match.group(2)):
                findings.error(f"HTML image in {source_path} needs descriptive alt text")
    for index, line in enumerate(lines):
        if re.match(r"^\s*```mermaid\s*$", line, re.IGNORECASE):
            context = "\n".join(lines[max(0, index - 2) : min(len(lines), index + 2)]).lower()
            if not re.search(r"(?:visual|diagram|figure) description\s*:", context):
                findings.error(
                    f"Mermaid diagram in {source_path} needs an adjacent visual description"
                )


def markdownlint_settings(repo_root: Path) -> dict[str, Any]:
    config_path = repo_root / ".markdownlint.json"
    if not config_path.exists():
        return {"default": True}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"default": True}


def markdown_rule_enabled(config: dict[str, Any], rule: str) -> bool:
    value = config.get(rule, config.get("default", True))
    return value is not False


def _check_trailing_spaces(source_path: str, lines: list[str], findings: Findings) -> None:
    for number, line in enumerate(lines, start=1):
        if len(line) - len(line.rstrip(" ")) > 2:
            findings.error(
                f"Markdownlint MD009 in {source_path}:{number} (more than two trailing spaces)"
            )


def _check_tabs(source_path: str, lines: list[str], findings: Findings) -> None:
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
        elif not in_fence and "\t" in line:
            findings.error(f"Markdownlint MD010 in {source_path}:{number} (tab outside code fence)")


def _check_duplicate_headings(source_path: str, text: str, findings: Findings) -> None:
    counts: defaultdict[tuple[tuple[str, ...], int, str], int] = defaultdict(int)
    parents: dict[int, str] = {}
    for number, line in enumerate(strip_code_fences(text), start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        level, name = len(match.group(1)), match.group(2).strip().lower()
        parents = {key: value for key, value in parents.items() if key < level}
        key = (tuple(parents[item] for item in sorted(parents)), level, name)
        counts[key] += 1
        if counts[key] > 1:
            findings.error(f"Markdownlint MD024 in {source_path}:{number} (duplicate heading)")
        parents[level] = name


def check_markdown_style(repo_root: Path, source_path: str, text: str, findings: Findings) -> None:
    config, lines = markdownlint_settings(repo_root), text.splitlines()
    if markdown_rule_enabled(config, "MD009"):
        _check_trailing_spaces(source_path, lines, findings)
    if markdown_rule_enabled(config, "MD010"):
        _check_tabs(source_path, lines, findings)
    if markdown_rule_enabled(config, "MD024"):
        _check_duplicate_headings(source_path, text, findings)


def _frontmatter_field_error(field: str, value: Any) -> str | None:
    if field in {"aliases", "related", "prerequisites"}:
        valid = isinstance(value, list) and all(isinstance(item, str) for item in value)
        return None if valid else "must be a string list"
    if field == "audience":
        valid_string = isinstance(value, str) and bool(value.strip())
        valid_list = (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and item.strip() for item in value)
        )
        return None if valid_string or valid_list else "must be a non-empty string or string list"
    if field == "source_paths":
        valid = (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and item for item in value)
        )
        return None if valid else "must be a non-empty string list"
    if field == "authority_effect":
        return None if value == "None" else "must be quoted None"
    if field == "verification":
        return None if isinstance(value, (str, list)) and bool(value) else "must be non-empty"
    return None if isinstance(value, str) and bool(value.strip()) else "must be a non-empty string"


def check_frontmatter(
    source_path: str, text: str, contract: dict[str, Any], findings: Findings
) -> None:
    value, _, error = parse_frontmatter(text)
    if error:
        findings.error(f"Frontmatter error in {source_path}: {error}")
        return
    if value is None:
        findings.error(f"Missing frontmatter in {source_path}")
        return
    schema = contract["canonical_frontmatter"]
    contract_key = schema["contract_key"]
    if value.get(contract_key) != schema["contract_value"]:
        findings.error(f"Frontmatter contract marker missing or invalid in {source_path}")
    for field in schema["required"]:
        if field not in value:
            findings.error(f"Frontmatter field {field} missing in {source_path}")
            continue
        if message := _frontmatter_field_error(field, value[field]):
            findings.error(f"Frontmatter field {field} {message} in {source_path}")


def check_encoding(source_path: str, raw: bytes, text: str, findings: Findings) -> None:
    if raw.startswith(b"\xef\xbb\xbf"):
        findings.error(f"UTF-8 BOM is not allowed in {source_path}")
    for marker in MOJIBAKE_MARKERS:
        if marker in text:
            findings.error(f"Possible mojibake ({marker!r}) in {source_path}")
            break


def is_generated_archive_markdown(source_path: str, contract: dict[str, Any]) -> bool:
    """Generated records preserve historical formatting and are not authored lint inputs."""

    prefix = contract["documentation_root"].rstrip("/") + "/archive/"
    return source_path.startswith(prefix + "records/") or source_path.startswith(
        prefix + "catalogs/"
    )


@dataclass(frozen=True, slots=True)
class ContentSelection:
    scope: str
    changed_base: str | None = None
    include_changed_content: bool = False


def check_content(
    repo_root: Path,
    contract: dict[str, Any],
    findings: Findings,
    selection: ContentSelection,
) -> None:
    paths = selected_content_paths(
        repo_root,
        contract,
        selection.scope,
        selection.changed_base,
        selection.include_changed_content,
    )
    for source_path in paths:
        path = absolute_repo_path(repo_root, source_path)
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            findings.error(f"UTF-8 decode error in {source_path}: {error}")
            continue
        check_encoding(source_path, raw, text, findings)
        check_frontmatter(source_path, text, contract, findings)
        if not is_generated_archive_markdown(source_path, contract):
            check_markdown_style(repo_root, source_path, text, findings)
        check_links(repo_root, source_path, text, findings)
        check_visual_descriptions(source_path, text, findings)
    findings.checked(
        f"content metadata, links, anchors, encoding, visuals, and local lint ({len(paths)} Markdown files)"
    )


def _check_llms_target(number: int, normalized: str, findings: Findings) -> None:
    if "_archive/" in normalized or "llms-full" in normalized.lower():
        findings.error(f"llms.txt:{number} exposes raw archive material or a full-corpus bundle")
    allowed_archive = {"archive/README.md", "archive/readme.md"}
    if (
        normalized.startswith("archive/")
        and normalized not in allowed_archive
        and not normalized.startswith("archive/catalogs/")
    ):
        findings.error(
            f"llms.txt:{number} may list only archive category catalogues, not archive records"
        )
    if normalized.endswith(".md") and not DOC_ROOT.joinpath(*normalized.split("/")).exists():
        findings.error(f"llms.txt:{number} points to a missing page: {normalized}")


def check_llms(
    repo_root: Path, contract: dict[str, Any], findings: Findings, *, required: bool
) -> None:
    llms = DOC_ROOT / "llms.txt"
    if not llms.exists():
        if required:
            findings.error("llms.txt is required for the final documentation stage")
        else:
            findings.warning("llms.txt is pending during foundation stage")
        return
    try:
        content = llms.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        findings.error(f"llms.txt must be UTF-8: {error}")
        return
    for number, line in enumerate(content.splitlines(), start=1):
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        targets = [match.group(1).strip() for match in re.finditer(r"\]\(([^)]+)\)", item)]
        if not targets and item.startswith("- "):
            targets = [item[2:].split(maxsplit=1)[0]]
        for target in targets:
            normalized = target.strip("<>").split(maxsplit=1)[0]
            _check_llms_target(number, normalized, findings)
    findings.checked("llms.txt scope")

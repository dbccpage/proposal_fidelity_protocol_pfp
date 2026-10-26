"""Rule load scope: which host rules an IDE loads on every turn, and which only near their files.

A rule file may open with YAML frontmatter ``paths: [glob, ...]``. Claude Code then loads it
only when the session touches a matching file; without ``paths`` it loads on every turn.
The register (``rules_registry.yaml``) is the source of truth: each rule entry may carry
``load_paths``, and the frontmatter of every host copy must equal it. Rules with no
``load_paths`` are *always loaded*, and their total size is held under
``always_loaded_ceiling_bytes`` so the per-turn context cost cannot grow back silently.

The glob dialect follows the host's documented matcher: ``**``, ``*``, ``?``, brace
expansion ``{a,b}`` and bracket expressions ``[abc]``. An unreadable bracket matches
nothing, as it does in the host. ``paths`` may be a list or a comma-separated string.
Other frontmatter keys are ignored by the host and preserved by ``write_frontmatter``.

AuthorityEffect: None. Reads the tree; only ``write_frontmatter`` edits files, and only the
frontmatter block of registered rule files.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n\n?", re.DOTALL)
PRUNED_DIRS = frozenset({".git", ".venv", ".worktrees", "target", "__pycache__", "node_modules", ".lake"})
GIT_TIMEOUT_SECONDS = 120
#: A pattern the host cannot read matches no file.
MATCH_NOTHING = re.compile(r"(?!)")


@dataclass(frozen=True)
class ScopeFinding:
    code: str
    path: str
    message: str


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter mapping, body after the frontmatter); ``{}`` when there is none."""
    match = FRONTMATTER.match(text)
    if match is None:
        return {}, text
    data = yaml.safe_load(match.group(1))
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a mapping")
    return data, text[match.end():]


def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    """Return (``paths`` from the frontmatter or None, body after the frontmatter)."""
    data, body = parse_frontmatter(text)
    paths = data.get("paths")
    if isinstance(paths, str):
        paths = [part.strip() for part in paths.split(",") if part.strip()]
    if paths is not None and not (isinstance(paths, list) and all(isinstance(p, str) for p in paths)):
        raise ValueError("frontmatter 'paths' must be a list of strings")
    return paths, body


def render_frontmatter(paths: list[str], body: str, extra: dict | None = None) -> str:
    """Render ``paths`` above ``body``, keeping any other frontmatter keys in ``extra``."""
    kept = {key: value for key, value in (extra or {}).items() if key != "paths"}
    if not paths and not kept:
        return body
    lines = ["---"]
    if kept:
        lines.append(yaml.safe_dump(kept, sort_keys=False, allow_unicode=True).rstrip("\n"))
    if paths:
        lines += ["paths:"] + [f'  - "{glob}"' for glob in paths]
    lines += ["---", ""]
    return "\n".join(lines) + "\n" + body


def glob_regex(glob: str) -> re.Pattern[str]:
    """Translate a repo-relative glob into an anchored regex.

    ``**/`` spans directories, ``*`` and ``?`` stay inside one segment, ``{a,b}`` alternates
    and ``[...]`` is a bracket expression. Braces that do not balance are literal, and an
    unterminated bracket makes the whole pattern match nothing.
    """
    braces = glob.count("{") == glob.count("}")
    out: list[str] = []
    depth = 0
    i = 0
    while i < len(glob):
        char = glob[i]
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        elif char == "{" and braces:
            out.append("(?:")
            depth += 1
            i += 1
        elif char == "}" and depth:
            out.append(")")
            depth -= 1
            i += 1
        elif char == "," and depth:
            out.append("|")
            i += 1
        elif char == "[":
            end = glob.find("]", i + 2)
            if end < 0:
                return MATCH_NOTHING
            body = glob[i + 1 : end]
            if body.startswith("!"):
                body = "^" + body[1:]
            out.append("[" + body.replace("\\", "\\\\") + "]")
            i = end + 1
        elif char == "\\" and i + 1 < len(glob):
            out.append(re.escape(glob[i + 1]))
            i += 2
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _git_toplevel(repo_root: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return Path(result.stdout.decode("utf-8", "replace").strip()).resolve()


def tracked_files(repo_root: Path) -> list[str]:
    """Repo-relative POSIX paths: ``git ls-files`` when ``repo_root`` is a repository's own
    top level, else a pruned walk. A root nested inside some other repository is walked, so
    its globs are checked against its own files and not the enclosing index."""
    if _git_toplevel(repo_root) == repo_root.resolve():
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), "ls-files", "-z"],
                capture_output=True,
                check=False,
                timeout=GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result is not None and result.returncode == 0:
            return [p for p in result.stdout.decode("utf-8", "replace").split("\0") if p]
    files: list[str] = []
    for path in repo_root.rglob("*"):
        rel = path.relative_to(repo_root)
        if any(part in PRUNED_DIRS for part in rel.parts) or not path.is_file():
            continue
        files.append(rel.as_posix())
    return files


def check_load_scope(repo_root: Path, texts: dict[str, str], registry: dict) -> tuple[list[ScopeFinding], int]:
    """Check frontmatter against the register, dead globs, and the always-loaded budget.

    Returns the findings and the always-loaded byte count of the canonical tree. The count
    covers rule bodies only, as the host strips the frontmatter before loading a rule.
    """
    findings: list[ScopeFinding] = []
    files: list[str] | None = None
    alive: dict[str, bool] = {}
    always_loaded = 0
    for entry in registry["rules"]:
        relative = entry["path"]
        text = texts.get(relative)
        if text is None:
            continue
        declared = list(entry.get("load_paths") or [])
        try:
            found, body = split_frontmatter(text)
        except (ValueError, yaml.YAMLError) as exc:
            findings.append(ScopeFinding("R9_FRONTMATTER", relative, str(exc)))
            continue
        if (found or []) != declared:
            findings.append(ScopeFinding("R9_SCOPE_DRIFT", relative, "frontmatter paths differ from register load_paths"))
        if not declared:
            always_loaded += len(body.encode("utf-8"))
            continue
        if files is None:
            files = tracked_files(repo_root)
        for glob in declared:
            if glob not in alive:
                pattern = glob_regex(glob)
                alive[glob] = any(pattern.match(f) for f in files)
            if not alive[glob]:
                findings.append(ScopeFinding("R9_DEAD_GLOB", relative, f"{glob!r} matches no tracked file"))
    ceiling = registry.get("always_loaded_ceiling_bytes")
    if ceiling is not None and always_loaded > ceiling:
        findings.append(
            ScopeFinding("R9_ALWAYS_LOADED_BUDGET", "rules", f"{always_loaded} always-loaded bytes exceed {ceiling}")
        )
    return findings, always_loaded


def write_frontmatter(repo_root: Path, registry: dict) -> list[str]:
    """Rewrite the ``paths`` frontmatter of every registered rule in every host from the register.

    Other frontmatter keys are kept; only ``paths`` is replaced. Bytes are read and written
    as they are, so a CRLF file is neither translated nor reported as unchanged by mistake.
    """
    written: list[str] = []
    for host in registry["host_roots"]:
        rules_dir = repo_root / host / registry["rules_root"]
        for entry in registry["rules"]:
            path = rules_dir / entry["path"]
            if not path.is_file():
                continue
            original = path.read_bytes().decode("utf-8")
            try:
                data, body = parse_frontmatter(original)
            except (ValueError, yaml.YAMLError) as exc:
                raise ValueError(f"{path.relative_to(repo_root).as_posix()}: {exc}") from exc
            updated = render_frontmatter(list(entry.get("load_paths") or []), body, extra=data)
            if updated != original:
                path.write_bytes(updated.encode("utf-8"))
                written.append(path.relative_to(repo_root).as_posix())
    return written

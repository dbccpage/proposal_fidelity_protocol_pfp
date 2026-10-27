#!/usr/bin/env python3
"""Hold `_shared/` and `_templates/` to a declared shape.

`_shared` is the library every skill package reads from. It had 27 files, three
competing naming conventions, at least eight distinct kinds of document
flattened together with nothing declaring which was which, and -- of 24 markdown
files -- exactly one carrying any frontmatter at all. Three files exceed the
20 KB budget that governs `SKILL.md` and does not reach here.

The kinds are not decoration. `family_registry.md` is generated and must never be
hand-edited; `test_quality_law.md` is binding and must be obeyed;
`constraint_audit_report.md` is a one-off report from a campaign that ended and
must not be cited as law. Flattened together, a reader cannot tell which is
which, and neither can a gate.

`gate` and `tool` are separate kinds deliberately. `verify_skill_names.py` has a
`--fix` mode that rewrites the files it inspects; something that can mutate its
own subject is not evidence about that subject, so it is a tool, and a gate must
be read-only.

Stdlib only, matching `agent_skill_manifest_audit.py`: a missing YAML package
must not disable a governance check.

`AuthorityEffect: None`. A pass certifies nothing beyond the comparisons made.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence

KINDS = (
    "law",         # binding constraint; cited and obeyed, never executed
    "gate",        # executable, read-only, exits non-zero, CI-wireable
    "tool",        # executable and mutating; never a gate
    "generated",   # machine-written, has a named regenerator, never hand-edited
    "template",    # scaffold to be copied
    "checklist",   # ordered verification list
    "note",        # explanation, non-binding
    "historical",  # one-off report, superseded, NOT citable as law
)

#: `README.md` keeps its conventional casing. Declared, not assumed.
NAMING_EXEMPT = frozenset({"README.md"})

MAX_LINES = 300
MAX_BYTES = 20 * 1024
#: `law` may exceed the byte budget only from `_shared/laws/`, beside an index.
BUDGETED_KINDS = frozenset({"note", "checklist", "template"})
#: Bytes bound context cost; lines are a proxy for it that misreads a scaffold.
#: A template is many short lines by construction -- `skill_family_template.md`
#: is 309 lines and 9,801 bytes, less than half the byte budget. Holding it to
#: the line count would mean deleting worked examples to satisfy an instrument
#: that was never measuring the thing it stands for.
LINE_BUDGETED_KINDS = frozenset({"note", "checklist"})

MANIFEST_NAME = "_manifest.json"
MANIFEST_SCHEMA = "core.skill_garden.shared_manifest.v1"

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
_SHARED_REF = re.compile(r"_shared/([A-Za-z0-9_./-]+\.(?:md|py|sh))(#[A-Za-z0-9._-]+)?")
_SNAKE = re.compile(r"\A[a-z0-9]+(?:_[a-z0-9]+)*\Z")

#: Pathlib on a case-insensitive host folds these. git does not.
FOUR_HOST_SKILL_ROOTS = (
    ".agents/skills",
    ".claude/skills",
    ".codex/skills",
    ".grok/skills",
)
CANONICAL_SKILL_ROOT = "operads/skills"


def source_prefix(repo_root: Path) -> str:
    """Use authored sources in the current estate; retain host-only fixtures."""
    if (repo_root / CANONICAL_SKILL_ROOT).is_dir():
        return CANONICAL_SKILL_ROOT
    return FOUR_HOST_SKILL_ROOTS[0]


class Finding(NamedTuple):
    severity: str
    code: str
    locus: str
    message: str

    def render(self) -> str:
        return f"[{self.severity}] {self.code}: {self.locus}: {self.message}"


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    return Path.cwd().resolve()


def git_tracked_relpaths(repo_root: Path, prefix: str) -> list[str] | None:
    """Tracked paths under ``prefix``, as git stores them (case-preserving).

    ``Path.rglob`` on this Windows host folds ``ARCHITECTURE.md`` into
    ``architecture.md``. The index does not. Returns ``None`` when git cannot
    answer -- throwaway fixtures that only ``mkdir`` a ``.git`` directory --
    so those tests keep using the pathlib walk.

    ``--git-dir`` is pinned so a fixture whose ``.git`` is an empty directory
    cannot walk up into the real checkout. That walk is how a ``git add -A``
    in a test once committed against this repository.
    """
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return None
    proc = subprocess.run(
        [
            "git",
            "--git-dir",
            str(git_dir),
            "--work-tree",
            str(repo_root),
            "ls-files",
            "--full-name",
            "-z",
            "--",
            prefix,
        ],
        cwd=str(repo_root),
        capture_output=True,
        env={**os.environ, "GIT_CONFIG_GLOBAL": str(repo_root / ".gitconfig-none")},
    )
    if proc.returncode != 0:
        return None
    prefix_slash = prefix.replace("\\", "/").rstrip("/") + "/"
    rels: list[str] = []
    for line in proc.stdout.decode("utf-8", "replace").split("\0"):
        if not line:
            continue
        path = line.replace("\\", "/")
        if path.startswith(prefix_slash):
            rels.append(path[len(prefix_slash):])
    return rels


def four_host_rel_diff(
    canon: Sequence[str], other: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Case-sensitive symmetric difference. Do not fold."""
    left, right = set(canon), set(other)
    return sorted(left - right), sorted(right - left)


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Flat `key: value` only, matching the SKILL.md parser's contract."""
    match = _FRONTMATTER.match(text)
    if not match:
        return None
    data: dict[str, str] = {}
    for line in match.group(1).split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, raw = stripped.split(":", 1)
        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        data[key.strip()] = value
    return data


def load_manifest(shared: Path) -> dict[str, Any]:
    path = shared / MANIFEST_NAME
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.name != MANIFEST_NAME and "__pycache__" not in path.parts
    )


def verify(repo_root: Path) -> list[Finding]:
    source = source_prefix(repo_root)
    shared = repo_root / source / "_shared"
    templates = repo_root / source / "_templates"
    findings: list[Finding] = []

    manifest = load_manifest(shared)
    entries: dict[str, dict[str, Any]] = manifest.get("entries", {})

    tracked = _iter_files(shared) + _iter_files(templates)
    relative = {}
    for path in tracked:
        base = shared if shared in path.parents else templates
        prefix = "_shared" if base is shared else "_templates"
        relative[path] = f"{prefix}/{path.relative_to(base).as_posix()}"

    # -- C1 / C1b: every file declared, and the two declarations agreeing ----
    for path, rel in relative.items():
        entry = entries.get(rel)
        if entry is None:
            findings.append(
                Finding("ERROR", "UNDECLARED_FILE", rel,
                        f"absent from {MANIFEST_NAME}; every file needs a kind")
            )
            continue
        kind = entry.get("kind")
        if kind not in KINDS:
            findings.append(
                Finding("ERROR", "UNKNOWN_KIND", rel,
                        f"kind {kind!r} is not one of {list(KINDS)}")
            )
        if entry.get("authority_effect") != "None":
            findings.append(
                Finding("ERROR", "AUTHORITY_DECLARED", rel,
                        "every shared file must declare authority_effect: None")
            )
        if path.suffix == ".md":
            front = parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
            if front is None:
                findings.append(
                    Finding("ERROR", "MISSING_FRONTMATTER", rel,
                            "markdown in _shared/_templates must carry frontmatter")
                )
            else:
                if front.get("kind") != kind:
                    findings.append(
                        Finding("ERROR", "MANIFEST_FRONTMATTER_DRIFT", rel,
                                f"frontmatter kind {front.get('kind')!r} != manifest "
                                f"{kind!r}; two declarations that disagree are worse "
                                "than one")
                    )
                if front.get("authority_effect") != "None":
                    findings.append(
                        Finding("ERROR", "AUTHORITY_DECLARED", rel,
                                "frontmatter must carry authority_effect: None")
                    )

    for rel in sorted(set(entries) - set(relative.values())):
        findings.append(
            Finding("ERROR", "MANIFEST_ORPHAN", rel,
                    "declared in the manifest but absent from disk")
        )

    # -- C3: a code fence swallowed into a heading --------------------------
    for path, rel in relative.items():
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        swallowed = len(re.findall(r"^#+\s+`{3}", text, re.M))
        if swallowed:
            findings.append(
                Finding("ERROR", "HEADING_SWALLOWED_FENCE", rel,
                        f"{swallowed} code fence(s) parsed as headings; a "
                        "`markdownlint --fix` sweep did this once already and "
                        "destroyed 17 skill descriptions")
            )

    # -- C5: one naming convention ------------------------------------------
    for path, rel in relative.items():
        if path.name in NAMING_EXEMPT:
            continue
        if not _SNAKE.match(path.stem):
            findings.append(
                Finding("ERROR", "NAMING_CONVENTION", rel,
                        f"{path.stem!r} is not lower_snake_case. This tree is "
                        "authored on a case-insensitive host and consumed by a "
                        "case-sensitive one")
            )

    # -- C5b: git-tracked names, not pathlib ---------------------------------
    # A fresh checkout of this branch stored ARCHITECTURE.md under .agents
    # and architecture.md under the other three hosts (same blob). Path.rglob
    # on a worktree that already had architecture.md folded them equal; git
    # ls-files did not. The index is the name Ubuntu will see.
    tracked_shared = git_tracked_relpaths(
        repo_root, f"{source}/_shared"
    )
    tracked_templates = git_tracked_relpaths(
        repo_root, f"{source}/_templates"
    )
    for prefix, tracked in (
        ("_shared", tracked_shared),
        ("_templates", tracked_templates),
    ):
        if tracked is None:
            continue
        for rel in tracked:
            name = Path(rel).name
            if name == MANIFEST_NAME or name in NAMING_EXEMPT:
                continue
            stem = Path(name).stem
            if not _SNAKE.match(stem):
                findings.append(
                    Finding("ERROR", "NAMING_CONVENTION", f"{prefix}/{rel}",
                            f"{stem!r} is not lower_snake_case in the git "
                            "index (pathlib on this host is not evidence)")
                )

    # -- C5c: four-host path strings, case-sensitive ------------------------
    for sub in ("_shared", "_templates"):
        canon_prefix = f"{source}/{sub}"
        canon = git_tracked_relpaths(repo_root, canon_prefix)
        if canon is None:
            continue
        for host in FOUR_HOST_SKILL_ROOTS:
            if host == source:
                continue
            other = git_tracked_relpaths(repo_root, f"{host}/{sub}")
            if other is None:
                continue
            only_canon, only_other = four_host_rel_diff(canon, other)
            if only_canon or only_other:
                findings.append(
                    Finding(
                        "ERROR",
                        "FOUR_HOST_PATH_CASE",
                        f"{host}/{sub}",
                        f"git-tracked names differ from {source} "
                        "(case-sensitive; Windows pathlib folding is not "
                        f"a pass): only source={only_canon[:8]!r} "
                        f"only other={only_other[:8]!r}",
                    )
                )

    # -- C6: size budget -----------------------------------------------------
    for path, rel in relative.items():
        entry = entries.get(rel, {})
        kind = entry.get("kind")
        size = path.stat().st_size
        lines = len(path.read_bytes().splitlines())
        if kind in BUDGETED_KINDS and size > MAX_BYTES:
            findings.append(
                Finding("ERROR", "SIZE_BUDGET", rel,
                        f"{size} bytes exceeds {MAX_BYTES} for kind {kind!r}")
            )
        if kind in LINE_BUDGETED_KINDS and lines > MAX_LINES:
            findings.append(
                Finding("ERROR", "LINE_BUDGET", rel,
                        f"{lines} lines exceeds {MAX_LINES} for kind {kind!r}; "
                        "prose of this kind should stay skimmable")
            )
        if kind == "law" and size > MAX_BYTES and "/laws/" not in rel:
            findings.append(
                Finding("WARN", "OVERSIZE_LAW", rel,
                        f"{size} bytes. A law past {MAX_BYTES} belongs in "
                        "_shared/laws/ beside an anchor index, so a citing skill "
                        "pulls a section rather than the whole document")
            )

    # -- C9: a historical report must not be cited as live law ---------------
    citations = _collect_citations(repo_root)
    for rel, entry in entries.items():
        if entry.get("kind") != "historical":
            continue
        name = rel.split("/", 1)[-1]
        citers = citations.get(name, [])
        if citers:
            findings.append(
                Finding("ERROR", "HISTORICAL_CITED_AS_LAW", rel,
                        f"cited by {len(citers)} live surface(s) "
                        f"({', '.join(citers[:3])}). Reclassify it or unwire them")
            )

    # -- C7: whole-file citations (the context leak) -------------------------
    unanchored = sum(1 for _, anchored in _citation_pairs(repo_root) if not anchored)
    total = len(_citation_pairs(repo_root))
    if unanchored:
        findings.append(
            Finding("WARN", "UNANCHORED_SHARED_REF", "_shared",
                    f"{unanchored} of {total} citations name a whole file rather "
                    "than a section, so a skill pulls the entire document into hot "
                    "context -- up to 41 KB")
        )

    return findings


def _citation_pairs(repo_root: Path) -> list[tuple[str, bool]]:
    pairs: list[tuple[str, bool]] = []
    for path in sorted((repo_root / source_prefix(repo_root)).glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, anchor in _SHARED_REF.findall(text):
            pairs.append((name, bool(anchor)))
    return pairs


def _collect_citations(repo_root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    surfaces = list((repo_root / source_prefix(repo_root)).glob("*/SKILL.md"))
    surfaces += list((repo_root / "operads" / "skill_operad" / "skill_compiler").glob("routes.yaml"))
    for path in sorted(surfaces):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, _anchor in _SHARED_REF.findall(text):
            found.setdefault(name, []).append(path.parent.name)
    return found


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the _shared/_templates standard.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--strict", action="store_true", help="treat WARN findings as failures"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()

    findings = verify(root)
    errors = [finding for finding in findings if finding.severity == "ERROR"]
    warns = [finding for finding in findings if finding.severity == "WARN"]

    print("=== SHARED CORPUS STANDARD ===")
    for finding in findings:
        print("  " + finding.render())
    print()
    print(f"errors={len(errors)} warnings={len(warns)}")
    if errors or (args.strict and warns):
        print("REFUSED. AuthorityEffect: None.")
        return 1
    print("PASS. AuthorityEffect: None.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

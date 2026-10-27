"""Does the committed evidence still describe the code it names?

The gap this closes, and it was predicted before it was exploited
-------------------------------------------------------------------

On 2026-09-03 this estate's own review named evidence freshness as "the one real
hole ... nothing checks that the committed mutation table's `head_sha` matches
the code it describes, and a stale evidence file is byte-indistinguishable from
a fresh one." It was not built. On 2026-09-04 the adversarial campaign's seed
defect 10 found exactly that: the shipped mutation receipt names head
`97dacc1894` while main had moved on, so its rows could not establish present
coverage.

A prediction that is recorded and not acted on is worth slightly less than no
prediction at all, because it also demonstrates the gap was understood.

What "stale" precisely means
----------------------------

Not simply ``head_sha != HEAD``. Evidence is generated at some commit and
committed in the next one, so a mismatch is the normal case and gating on it
would cry wolf on every honest run.

The question that actually matters is narrower and is decidable from git when
the caller names the receipts in scope:

    **Has any file the evidence describes changed between the commit it was
    generated at and now?**

If nothing it mutated has moved, the evidence still describes the current code
however many commits have passed. If even one target has moved, every row about
that target is a claim about bytes that no longer exist -- and the file gives a
reader no way to tell.

Failure direction
-----------------

This gate fails CLOSED, in the estate's usual sense. An evidence file whose
`head_sha` is not a commit this repository knows, or whose targets cannot be
resolved, is reported STALE rather than skipped: an artifact we cannot place in
history is not an artifact we can rely on.

AuthorityEffect: None. This reports whether a receipt is current. It does not
make it true.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

__all__ = ["FreshnessVerdict", "check_evidence", "main"]

_FULL_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


@dataclass(frozen=True, slots=True)
class FreshnessVerdict:
    """What this gate established about one evidence artifact."""

    path: str
    #: CURRENT | STALE | UNPLACEABLE
    status: str
    head_sha: str = ""
    targets: int = 0
    moved: tuple[str, ...] = field(default_factory=tuple)
    detail: str = ""

    @property
    def is_current(self) -> bool:
        return self.status == "CURRENT"


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True
        )
    except OSError as error:  # pragma: no cover - git absent is environmental
        return 1, str(error)
    return completed.returncode, completed.stdout


def _literal_target(value: object) -> tuple[str | None, str]:
    """Validate one evidence target as a literal repository-relative Git path."""
    if not isinstance(value, str) or not value:
        return None, "target is not a nonempty string"
    if value.startswith(":"):
        return None, "Git pathspec magic is forbidden"
    if "\\" in value:
        return None, "backslashes are not repository-relative separators"
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None, "control characters are forbidden"
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or value.startswith("/"):
        return None, "absolute paths are forbidden"
    if len(value) >= 2 and value[1] == ":":
        return None, "drive-qualified paths are forbidden"
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return None, "empty, dot, and traversal components are forbidden"
    if candidate.as_posix() != value:
        return None, "target is not a normalized repository-relative path"
    return value, ""


def _blob_exists_at(root: Path, head_sha: str, target: str) -> bool:
    """Return whether ``target`` names an exact blob at ``head_sha``.

    ``--literal-pathspecs`` and an exact decoded-path comparison are both
    intentional. Without them, a target such as ``:(exclude)*`` can turn a
    missing-target check into a query about some other set of paths.
    """
    code, out = _git(
        root,
        "--literal-pathspecs",
        "ls-tree",
        "-z",
        "--full-tree",
        head_sha,
        "--",
        target,
    )
    if code != 0:
        return False
    for entry in out.split("\0"):
        if not entry or "\t" not in entry:
            continue
        metadata, path = entry.split("\t", 1)
        fields = metadata.split()
        if path == target and len(fields) == 3 and fields[1] == "blob":
            return True
    return False


def _load_evidence_document(
    path: Path, rel: str
) -> FreshnessVerdict | tuple[str, list]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return FreshnessVerdict(rel, "UNPLACEABLE", detail=f"unreadable: {error}")
    head_sha = str(body.get("head_sha", "")).strip()
    if not head_sha:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            detail=(
                "no head_sha: the artifact does not say which commit it describes, "
                "so nothing can decide whether it is current"
            ),
        )
    if _FULL_OBJECT_ID.fullmatch(head_sha) is None:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            head_sha,
            detail=(
                "head_sha must be an exact full lowercase Git object ID; "
                "symbolic refs, tags, and abbreviated IDs are forbidden"
            ),
        )
    results = body.get("results")
    if not isinstance(results, list) or not results:
        return FreshnessVerdict(
            rel, "UNPLACEABLE", head_sha, detail="no results to place in history"
        )
    return head_sha, results


def _evidence_targets(
    rel: str, head_sha: str, results: list
) -> FreshnessVerdict | list[str]:
    targets_set: set[str] = set()
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            return FreshnessVerdict(
                rel,
                "UNPLACEABLE",
                head_sha,
                detail=f"results[{index}] is not an object with a literal target",
            )
        target, problem = _literal_target(result.get("target"))
        if target is None:
            return FreshnessVerdict(
                rel,
                "UNPLACEABLE",
                head_sha,
                detail=f"invalid target at results[{index}]: {problem}",
            )
        targets_set.add(target)
    targets = sorted(targets_set)
    if not targets:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            head_sha,
            detail="results name no targets, so the artifact describes nothing checkable",
        )
    return targets


def _place_evidence_commit(
    root: Path, rel: str, head_sha: str, targets: list[str]
) -> FreshnessVerdict | None:
    code, _ = _git(root, "cat-file", "-e", f"{head_sha}^{{commit}}")
    if code != 0:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            head_sha,
            len(targets),
            detail=(
                f"{head_sha} is not a commit this repository knows; an artifact "
                "that cannot be placed in history cannot be relied on"
            ),
        )
    code, resolved = _git(root, "rev-parse", "--verify", f"{head_sha}^{{commit}}")
    if code != 0 or resolved.strip() != head_sha:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            head_sha,
            len(targets),
            detail="head_sha does not canonically identify the recorded commit",
        )
    missing = tuple(
        target for target in targets if not _blob_exists_at(root, head_sha, target)
    )
    if missing:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            head_sha,
            len(targets),
            detail=(
                "target is not a blob at the recorded commit: "
                + ", ".join(missing[:5])
            ),
        )
    return None


def _diff_evidence_targets(
    root: Path, rel: str, head_sha: str, targets: list[str]
) -> FreshnessVerdict:
    code, out = _git(
        root,
        "--literal-pathspecs",
        "diff",
        "--name-only",
        "-z",
        head_sha,
        "HEAD",
        "--",
        *targets,
    )
    if code != 0:
        return FreshnessVerdict(
            rel,
            "UNPLACEABLE",
            head_sha,
            len(targets),
            detail="git could not compare the recorded commit with HEAD",
        )
    moved = tuple(name for name in out.split("\0") if name)
    if moved:
        return FreshnessVerdict(
            rel,
            "STALE",
            head_sha,
            len(targets),
            moved,
            detail=(
                f"{len(moved)} of {len(targets)} described file(s) changed since "
                f"{head_sha}; every row about them describes bytes that no longer exist"
            ),
        )
    return FreshnessVerdict(
        rel,
        "CURRENT",
        head_sha,
        len(targets),
        detail=(
            f"no described file has changed since {head_sha}, so the artifact still "
            "describes the current tree"
        ),
    )


def check_evidence(path: Path, root: Path) -> FreshnessVerdict:
    """Decide whether one evidence artifact still describes the current tree."""
    rel = path.relative_to(root).as_posix() if path.is_absolute() else str(path)
    loaded = _load_evidence_document(path, rel)
    if isinstance(loaded, FreshnessVerdict):
        return loaded
    head_sha, results = loaded
    targets = _evidence_targets(rel, head_sha, results)
    if isinstance(targets, FreshnessVerdict):
        return targets
    placed = _place_evidence_commit(root, rel, head_sha, targets)
    if placed is not None:
        return placed
    return _diff_evidence_targets(root, rel, head_sha, targets)


def render(verdicts: list[FreshnessVerdict]) -> str:
    lines: list[str] = []
    for verdict in verdicts:
        lines.append(f"[{verdict.status:11}] {verdict.path}")
        lines.append(f"              generated at {verdict.head_sha or '(none)'}, "
                     f"{verdict.targets} target(s)")
        if verdict.detail:
            lines.append(f"              {verdict.detail}")
        for name in verdict.moved[:10]:
            lines.append(f"                moved: {name}")
        if len(verdict.moved) > 10:
            lines.append(f"                ... and {len(verdict.moved) - 10} more")
        lines.append("")
    stale = [v for v in verdicts if not v.is_current]
    lines.append(
        f"{len(verdicts) - len(stale)} of {len(verdicts)} evidence artifact(s) current."
    )
    if stale:
        lines.append(
            "Regenerate the stale ones, or mark them explicitly historical. A "
            "receipt that is byte-indistinguishable from a fresh one, and is not, "
            "is the failure this gate exists to prevent."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evidence_freshness",
        description="Check whether committed evidence still describes the current tree.",
    )
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--receipt-dir",
        default=None,
        help="Caller-selected directory scanned for *.json receipts carrying a head_sha",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help=(
            "Report without failing. For a first landing, before the stale "
            "artifacts have been regenerated -- not a permanent mode."
        ),
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if args.receipt_dir is None:
        retired = root / "operations" / "evidence"
        if retired.exists() or retired.is_symlink():
            print(
                "retired repository evidence directory is present; live receipt "
                "scope must be caller-selected with --receipt-dir",
                file=sys.stderr,
            )
            return 1
        print(
            "repository evidence directory is retired; provide --receipt-dir "
            "to evaluate a named receipt scope"
        )
        return 0

    directory = root / args.receipt_dir
    if not directory.is_dir():
        print(f"no receipt directory at {args.receipt_dir}", file=sys.stderr)
        return 1

    candidates = sorted(
        path
        for path in directory.glob("*.json")
        if "head_sha" in path.read_text(encoding="utf-8", errors="ignore")
    )
    if not candidates:
        # Zero artifacts is not a pass. A gate over an empty set reports green
        # forever, which is the shape this estate keeps finding.
        print(
            f"no receipt under {args.receipt_dir} carries a head_sha; "
            "a gate over an empty set cannot fail",
            file=sys.stderr,
        )
        return 1

    verdicts = [check_evidence(path, root) for path in candidates]
    print(render(verdicts))

    stale = [v for v in verdicts if not v.is_current]
    if stale and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

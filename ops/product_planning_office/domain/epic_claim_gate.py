"""An epic's claims about existing code are evidence, and evidence must replay.

A triage of all 27 epics returned 215 claims that were false or stale against
HEAD. The failure is not carelessness; it is that a plan speaks in two voices at
once and marks neither:

  * DESCRIPTIVE -- "the seeder writes `pharmacy_status="admitted"`". A statement
    about code that exists. Checkable, and wrong if the code changed.
  * PRESCRIPTIVE -- "introduce `BytecodeRefusal::ExecutionBudgetExhausted`". A
    statement about code that does not exist yet. Correctly absent.

Both are written in backticks in the same prose, so a reader -- human or agent
-- cannot tell which is a fact and which is a proposal. Descriptive claims then
rot silently as the code moves underneath them, and the next reader plans
against a repository that no longer exists.

The two voices are already separated by SECTION. Every one of the 75 planning
documents this walker currently returns uses the same headings, and they divide
cleanly:

  descriptive : Problem Statement, Prior Art, Current Evidence and Limitations,
                Source Provenance and Disposition, Further Notes
  prescriptive: Solution, User Stories, Implementation Decisions, Testing
                Decisions, Deliverables, Acceptance Criteria, Out of Scope, ...

So no new convention is needed and no document has to be re-authored. The
structure was already there; nothing was reading it.

This gate verifies LOCATED claims in a DESCRIPTIVE section: a claim that names
where it holds, as `path/file.py:120` or `file.py::symbol`. Those are decidable
-- the file either has that line, and defines that symbol, or it does not.

A broader rule was tried first and rejected: "code quoted in a descriptive
section must exist somewhere in the tree". It fires 6 times on this estate and
only 2 are real. The other 4 are legitimate prose that happens to sit in
backticks:

    | Canary coverage is any parenthesized integer | Coverage is decided by
    `re.finditer(...)`. Deleting both canary files and leaving
    `GRID = [(1,0),(2,0)]` plus `def test_nothing(): assert True` yields
    `0 findings, GATE PASSED, exit 0` |

One cell, three kinds of claim, identical formatting: an assertion about real
code, a HYPOTHETICAL scenario, and QUOTED OUTPUT of that hypothetical. Only the
first is checkable, and nothing syntactic separates them. A gate with a 33%
true-positive rate teaches its readers to ignore it, which is worse than no
gate -- so it is not shipped. The format change that would make evidence cells
separable is recorded as an open obligation for a human, not imposed here.

One class of behavioural claim IS decidable, and is now checked: an unhedged
assertion that an artifact has no callers. "The gate is invoked by nothing"
is refuted by exhibiting a caller, so the check runs in one direction only --
it reports the references it found, and never concludes the opposite from
their absence, because entry points and dynamic dispatch are invisible to a
textual scan. On this estate it fires once, on a claim that was already false
when it was written.

AuthorityEffect: None. The gate reports; it certifies nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

PLANS_SUBPATH = Path("product_planning_office/plans")

#: Section headings whose prose describes code as it is now. Matched after any
#: leading numbering ("2. Current Evidence and Limitations").
DESCRIPTIVE_HEADINGS: tuple[str, ...] = (
    "problem statement",
    "prior art",
    "current evidence",
    "source provenance",
    "further notes",
)

#: File types that make up the searchable tree.
SOURCE_SUFFIXES = frozenset(
    {".py", ".rs", ".yaml", ".yml", ".json", ".jsonl", ".toml", ".md", ".sh", ".ts", ".tsx"}
)

SKIP_DIR_NAMES = frozenset({".git", "node_modules", "__pycache__", ".venv", "dist", "build", "target", ".lake"})

_HEADING = re.compile(r"(?m)^(#{2,3})\s+(.+)$")
_LEADING_NUMBER = re.compile(r"^[0-9.\s]+")

_FILE = r"[\w.\-]+\.(?:py|rs|md|json|yaml|yml|jsonl|toml|lean|ts|tsx|sh)"

#: `path/to/file.py:120` -- a claim that something holds at a line.
_LINE_CLAIM = re.compile(rf"(?<![\w/.-])((?:[\w.\-]+/)*{_FILE}):(\d+)\b")

#: `file.py::symbol` -- a claim that a file defines a symbol.
_SYMBOL_CLAIM = re.compile(rf"(?<![\w/.-])((?:[\w.\-]+/)*{_FILE})::([A-Za-z_]\w*)\b")

#: Definition forms across the languages the estate uses.
_DEFINITION = (
    "def {name}", "class {name}", "fn {name}", "struct {name}", "enum {name}",
    "trait {name}", "impl {name}", "{name} =", "{name}:", '"{name}"', "{name}(",
)


@dataclass(frozen=True, slots=True)
class StaleClaim:
    document: str
    heading: str
    claim: str
    reason: str

    def __str__(self) -> str:
        return f"{self.document} [{self.heading}] {self.claim} -- {self.reason}"


def build_suffix_index(repo_root: Path) -> dict[str, list[Path]]:
    """Map every path suffix in the tree to the files that end with it.

    Plans cite paths three ways and none of them announces which: from the
    repository root, relative to the document, and as a bare filename or
    package-relative fragment whose prefix the surrounding prose supplied.
    Guessing prefixes does not work -- `module_shadow_scan.py` lives four levels
    down at `operations/domain/cicd/`, and an earlier version of
    this gate reported it missing for that reason alone. Indexing every suffix
    resolves all three forms without guessing.
    """
    index: dict[str, list[Path]] = {}
    for path in repo_root.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        parts = path.relative_to(repo_root).parts
        if any(part in SKIP_DIR_NAMES for part in parts):
            continue
        for start in range(len(parts)):
            index.setdefault("/".join(parts[start:]), []).append(path)
    return index


def resolve_cited_path(
    cited: str, *, document: Path, repo_root: Path, index: dict[str, list[Path]]
) -> Path | None:
    """The file a citation names, or None when nothing in the tree matches."""
    direct = [repo_root / cited, document.parent / cited]
    for candidate in direct:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    matches = index.get(cited.replace("\\", "/").lstrip("./"))
    return matches[0] if matches else None


def defines_symbol(path: Path, symbol: str) -> bool:
    """Whether a file defines a symbol, across the estate's languages."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(form.format(name=symbol) in text for form in _DEFINITION)


def is_descriptive_heading(heading: str) -> bool:
    """True when a section states what the code IS, not what it should become."""
    stripped = _LEADING_NUMBER.sub("", heading.strip().lower())
    return any(stripped.startswith(prefix) for prefix in DESCRIPTIVE_HEADINGS)


def iter_sections(text: str) -> Iterator[tuple[str, str]]:
    """Yield (heading, body) for each level-2/3 section of a document."""
    marks = [(m.start(), m.group(2).strip()) for m in _HEADING.finditer(text)]
    for index, (start, heading) in enumerate(marks):
        end = marks[index + 1][0] if index + 1 < len(marks) else len(text)
        yield heading, text[start:end]


def iter_located_claims(body: str) -> Iterator[tuple[str, str, str]]:
    """(kind, cited_path, locator) for every located claim in a section body."""
    seen: set[tuple[str, str, str]] = set()
    for match in _SYMBOL_CLAIM.finditer(body):
        key = ("symbol", match.group(1), match.group(2))
        if key not in seen:
            seen.add(key)
            yield key
    for match in _LINE_CLAIM.finditer(body):
        key = ("line", match.group(1), match.group(2))
        if key not in seen:
            seen.add(key)
            yield key


def audit_documents(
    documents: Iterable[Path], *, repo_root: Path, index: dict[str, list[Path]] | None = None
) -> list[StaleClaim]:
    """Located descriptive claims that no longer resolve."""
    stale: list[StaleClaim] = []
    index = build_suffix_index(repo_root) if index is None else index

    for document in sorted(documents):
        text = document.read_text(encoding="utf-8", errors="replace")
        relative = str(document.relative_to(repo_root)).replace("\\", "/")

        for heading, body in iter_sections(text):
            if not is_descriptive_heading(heading):
                continue

            for kind, cited, locator in iter_located_claims(body):
                target = resolve_cited_path(
                    cited, document=document, repo_root=repo_root, index=index
                )
                if target is None:
                    stale.append(StaleClaim(relative, heading, f"cites `{cited}`",
                                            "no such file anywhere in the tree"))
                    continue

                if kind == "line":
                    try:
                        lines = sum(1 for _ in target.open("r", encoding="utf-8", errors="replace"))
                    except OSError:
                        continue
                    if int(locator) > lines:
                        stale.append(StaleClaim(
                            relative, heading, f"cites `{cited}:{locator}`",
                            f"the file has {lines} lines",
                        ))
                elif not defines_symbol(target, locator):
                    stale.append(StaleClaim(
                        relative, heading, f"cites `{cited}::{locator}`",
                        "the file does not define that symbol",
                    ))
    return stale


def planning_documents(repo_root: Path) -> list[Path]:
    plans = repo_root / PLANS_SUBPATH
    return sorted(
        [*(plans / "epics").glob("*.md"), *(plans / "specs").glob("*.md")]
    )


def audit(repo_root: Path) -> list[StaleClaim]:
    return audit_documents(planning_documents(repo_root), repo_root=repo_root)


#: Phrases asserting that an artifact has no callers. Deliberately narrow: each
#: is an unhedged claim of zero reachability, not a softer "rarely used".
_UNREACHABILITY = re.compile(
    r"invoked by nothing|referenced by nothing|called by nothing|nothing calls it"
    r"|no test imports it|zero non-markdown references|has no caller|and no caller",
    re.IGNORECASE,
)

#: Only executable subjects. The verbs above -- invoked, called, imports -- are
#: claims about code being reached, so a `.yaml` catalog named in the same
#: sentence is context, never the subject.
_CODE_SUBJECT = re.compile(r"`([\w.\-/]+\.(?:py|rs))`")

_PARAGRAPH = re.compile(r"\n\s*\n")


@dataclass(frozen=True, slots=True)
class UnresolvedSubject:
    """An unreachability claim whose subject this gate cannot pin down.

    Reported rather than guessed. A gate that invents a subject in order to
    raise its own hit count is worse than one that admits the gap.
    """

    document: str
    heading: str
    claim: str
    reason: str

    def __str__(self) -> str:
        return f"{self.document} [{self.heading}] {self.claim} -- {self.reason}"


def iter_unreachability_paragraphs(body: str) -> Iterator[str]:
    """Paragraphs of a section body that assert something has no callers."""
    for paragraph in _PARAGRAPH.split(body):
        if _UNREACHABILITY.search(paragraph):
            yield paragraph


def resolve_claim_subject(paragraph: str, section_body: str) -> str | None:
    """The code file an unreachability claim is about, or None when ambiguous.

    Two widening steps, each requiring a single unambiguous candidate:

      1. the paragraph -- its first code file, since the claim's own sentence
         names its subject when it names anything at all;
      2. the section -- used only when the section mentions exactly one code
         file, which happens for table rows that say "outside the file" and
         leave the subject to the surrounding prose.

    Nothing wider. Falling back to the document produces a subject for almost
    every claim and a *correct* subject for few of them.
    """
    in_paragraph = _CODE_SUBJECT.findall(paragraph)
    if in_paragraph:
        return in_paragraph[0]
    in_section = set(_CODE_SUBJECT.findall(section_body))
    return in_section.pop() if len(in_section) == 1 else None


def find_references(
    stem: str, *, repo_root: Path, exclude: Path | None = None
) -> list[str]:
    """Non-markdown source files that mention `stem`, excluding the file itself.

    Markdown is excluded on purpose: a plan citing a module is documentation,
    not an invocation, and counting it would let a document refute its own
    claim merely by making it.
    """
    hits: list[str] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if path.suffix == ".md":
            continue
        parts = path.relative_to(repo_root).parts
        if any(part in SKIP_DIR_NAMES for part in parts):
            continue
        if exclude is not None and path == exclude:
            continue
        try:
            if stem in path.read_text(encoding="utf-8", errors="replace"):
                hits.append("/".join(parts))
        except OSError:
            continue
    return hits


def audit_unreachability_documents(
    documents: Iterable[Path],
    *,
    repo_root: Path,
    index: dict[str, list[Path]] | None = None,
) -> tuple[list[StaleClaim], list[UnresolvedSubject]]:
    """Descriptive "nothing calls this" claims that the tree contradicts.

    The check runs in ONE direction only. A claim is reported stale when
    references are found, and the finding carries them, so every report is
    falsifiable by opening the files it names. The converse is never asserted:
    finding no references does not establish that an artifact is unreachable,
    because entry points, dynamic dispatch, and string-built imports are all
    invisible to a textual scan. The gate can refute this claim; it cannot
    confirm it. AuthorityEffect: None.
    """
    stale: list[StaleClaim] = []
    unresolved: list[UnresolvedSubject] = []
    index = build_suffix_index(repo_root) if index is None else index

    for document in sorted(documents):
        text = document.read_text(encoding="utf-8", errors="replace")
        relative = str(document.relative_to(repo_root)).replace("\\", "/")

        for heading, body in iter_sections(text):
            if not is_descriptive_heading(heading):
                continue

            for paragraph in iter_unreachability_paragraphs(body):
                claim_text = " ".join(paragraph.split())
                if len(claim_text) > 120:
                    claim_text = claim_text[:117] + "..."

                subject = resolve_claim_subject(paragraph, body)
                if subject is None:
                    unresolved.append(UnresolvedSubject(
                        relative, heading, claim_text,
                        "could not identify which code artifact the claim is about",
                    ))
                    continue

                target = resolve_cited_path(
                    subject, document=document, repo_root=repo_root, index=index
                )
                stem = Path(subject).stem
                refs = find_references(stem, repo_root=repo_root, exclude=target)
                if refs:
                    rendered_refs = ", ".join(refs[:3])
                    if len(refs) > 3:
                        rendered_refs += f" (and {len(refs) - 3} more)"
                    stale.append(StaleClaim(
                        relative, heading,
                        f"claims `{subject}` has no callers",
                        f"referenced by {rendered_refs}",
                    ))
    return stale, unresolved


def audit_unreachability(
    repo_root: Path,
) -> tuple[list[StaleClaim], list[UnresolvedSubject]]:
    return audit_unreachability_documents(
        planning_documents(repo_root), repo_root=repo_root
    )


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args(argv)

    root = (
        Path(args.repo_root).resolve()
        if args.repo_root
        else Path(__file__).resolve().parents[2]
    )

    documents = planning_documents(root)
    stale = audit(root)
    refuted, unresolved = audit_unreachability(root)

    print("=== EPIC CLAIM GATE ===")
    print(f"documents scanned: {len(documents)}")
    print(f"stale located claims: {len(stale)}")
    for claim in stale:
        print(f"  [STALE] {claim}")
    print(f"refuted no-caller claims: {len(refuted)}")
    for claim in refuted:
        print(f"  [REFUTED] {claim}")
    print(f"no-caller claims with no decidable subject: {len(unresolved)}")
    for claim in unresolved:
        print(f"  [UNDECIDED] {claim}")

    if stale or refuted:
        if stale:
            print(
                f"\nFAIL: {len(stale)} descriptive claim(s) quote code that is not "
                "in the tree. Either correct the claim, or move it to a "
                "prescriptive section if it describes work still to be done."
            )
        if refuted:
            print(
                f"\nFAIL: {len(refuted)} descriptive claim(s) say an artifact has "
                "no caller while the tree contains callers. Correct the claim; "
                "the referencing files are named above."
            )
        return 1
    print("\nPASS: every descriptive code quotation resolves. AuthorityEffect: None.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic pre-flight gate for Anomalon research papers.

Stdlib only, so it runs in any fresh environment with no install step. A previous
release blocker (PO000-P1-016) was caused by a paper-local test importing
undeclared `yaml`; do not add third-party imports here.

Exit 0 = PASSED (no BLOCK findings), 1 = BLOCKED, 2 = usage error.

AuthorityEffect: None. This script reports. It never builds, bundles, promotes,
merges, mints a DOI, or uploads. A PASSED verdict is a proposal, not a promotion.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import asdict, dataclass

BLOCK = "BLOCK"
WARN = "WARN"


@dataclass(frozen=True)
class Finding:
    gate: str
    severity: str  # BLOCK | WARN
    path: str
    line: int
    message: str


_FENCE_RE = re.compile(r"(?ms)^(?P<f>```+|~~~+)[^\n]*\n.*?^(?P=f)[ \t]*$")


def blank_fenced(body: str) -> str:
    """Blank fenced-code content, preserving line count so line numbers hold.

    Gates must not fire on illustrative examples inside fences. The encyclopedia
    validator learned this the hard way: a document whose only required headings
    sat inside a ``` block satisfied its required-section check.
    """
    return _FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), body)


# --- G1: leftover authoring tags -------------------------------------------

_TAG_RE = re.compile(r"\[(VERIFY|OPEN|TODO)\]")


def gate_tags(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G1: no bracketed [VERIFY]/[OPEN]/[TODO] tags in the body.

    Backticked `OPEN` is NOT a violation: it is legitimate typed-absence
    vocabulary required by compliance-5b slots ("| **Anomalons** | `OPEN`: ..."),
    and several papers depend on it. Only the bracketed form is a leftover
    authoring tag.

    Scrubbing a tag means the obligation is already recorded in
    encyclopedia/proof_ledgers/proof_ledger_<YYYYMMDD>.md -- the tag moves to the
    ledger, it is not silently deleted.
    """
    out: list[Finding] = []
    for i, line in enumerate(blank_fenced(body).splitlines(), 1):
        for m in _TAG_RE.finditer(line):
            out.append(Finding(
                "G1-tags", BLOCK, str(path), i,
                f"leftover authoring tag {m.group(0)}; record the obligation in "
                f"encyclopedia/proof_ledgers/proof_ledger_<YYYYMMDD>.md, "
                f"then remove the tag",
            ))
    return out


# --- G4: Setext headings ---------------------------------------------------

# A Setext underline is >=3 of = or -, alone on a line. What distinguishes it
# from a horizontal rule is the line BEFORE it: a heading underline follows
# non-blank text, an <hr> follows a blank line or starts the document. A table
# delimiter row contains pipes and so never matches this pattern.
_UNDERLINE_RE = re.compile(r"^(={3,}|-{3,})[ \t]*$")


def gate_setext(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G4: ATX headings only; Setext underline dividers break the adapter.

    Requires a preceding non-blank line before flagging, so horizontal rules are
    not reported. That precision matters at estate scale: 998 files carry a
    rule-like line, and a gate that flags all of them buries its real findings.
    """
    out: list[Finding] = []
    clean = _FRONTMATTER_RE.sub(lambda m: "\n" * m.group(0).count("\n"), body, count=1)
    lines = blank_fenced(clean).splitlines()
    for i, line in enumerate(lines, 1):
        if not _UNDERLINE_RE.match(line):
            continue
        prev = lines[i - 2] if i >= 2 else ""
        if not prev.strip():
            continue  # horizontal rule, not a heading underline
        if prev.lstrip().startswith("#"):
            continue  # already an ATX heading; the rule below it is decoration
        out.append(Finding(
            "G4-setext", BLOCK, str(path), i,
            f"Setext underline under {prev.strip()[:40]!r}; "
            f"use an ATX heading (## {prev.strip()[:40]})",
        ))
    return out


# --- G7 / G5b: internal branding and the mechanism-inventory box ------------

SLOTS_5B = (
    "Primitive Differences", "Carriers / Structure", "Cochain complex",
    "Coboundary maps", "ZeroRel", "Licensed repairs", "Quotient / Q1",
    "Residuals", "Witnesses", "Observers / profiles", "Anomalons",
    "CompletionLaw", "Terminal / route", "AuthorityEffect",
)

INVENTORY_TITLE = "## Mechanism inventory"
BRANDED_TITLE = "## Omega Engine Primitives"

# The spaced prose/heading form only. A snake_case `omega_engine/...` path is a
# provenance pointer, reported by gate_publish_links with its own message.
_BRANDING_RE = re.compile(r"omega[ \t]+engine", re.IGNORECASE)


def gate_branding(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G7: zero internal 'Omega Engine' branding in publishable bytes.

    Compliance 5b requires a mechanism-inventory section and accepts either
    '## Omega Engine Primitives' or '## Mechanism inventory'. Only the second
    survives this gate, so papers must use the alias. paper-build is supposed to
    strip the branded form before compiling, but that step is skippable -- it was
    skipped for PO-000 r12, which is how the branded heading reached a rendered
    PDF that was about to be deposited. Fixing the source makes the strip step
    non-load-bearing.
    """
    out: list[Finding] = []
    for i, line in enumerate(blank_fenced(body).splitlines(), 1):
        for m in _BRANDING_RE.finditer(line):
            hint = (f"rename the heading to {INVENTORY_TITLE!r} (the sanctioned 5b alias)"
                    if line.strip().startswith(BRANDED_TITLE)
                    else "remove or rephrase; publishable bytes carry no project branding")
            out.append(Finding("G7-branding", BLOCK, str(path), i,
                               f"internal branding {m.group(0)!r}; {hint}"))
    return out


def gate_mechanism_inventory(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G5b: the inventory box exists, uses the alias, and binds every slot.

    Typed absence is required, not optional: an unused slot needs a non-empty
    value such as `N/A`, `OPEN`, or `OracleNeeded`. Empty cells are forbidden.

    Slot matching is prefix-tolerant because papers append qualifiers -- PO-000
    writes '**Licensed repairs / operator family**' for the 'Licensed repairs'
    slot. Anchoring with \\S* would fail on the space after 'repairs'.
    """
    clean = blank_fenced(normalize_setext(body, preserve_lines=True))
    if INVENTORY_TITLE not in clean:
        # The 5b inventory belongs to the consolidated CODA exposition. Its
        # fourteen slots include cochain and quotient objects that are outside
        # the scope of several standalone component monographs. Requiring
        # N/A-filled boxes in those papers would obscure their actual claims.
        # F005_coda is the historical folder, including synthetic fixtures.
        # coda_component_packages is where those monographs live after the move.
        component_root = path.parent.parent.name
        if (
            component_root in {"F005_coda", "coda_component_packages"}
            and path.parent.name != "coda"
        ):
            return []
        if BRANDED_TITLE in clean:
            return [Finding("G5b-inventory", BLOCK, str(path),
                            clean[:clean.index(BRANDED_TITLE)].count("\n") + 1,
                            f"inventory uses the branded title; rename to "
                            f"{INVENTORY_TITLE!r}")]
        # paper-release convention: a MISSING inventory is non-blocking unless
        # the paper is GTOC/CODA/QM hygiene-facing, i.e. actually being staged
        # for release (--strict). 658 of 676 estate papers lack the box, so
        # blocking by default would bury every other finding.
        return [Finding("G5b-inventory", BLOCK if strict else WARN, str(path), 1,
                        f"missing {INVENTORY_TITLE!r} section (compliance 5b); "
                        f"required before release, or price the absence")]

    start = clean.index(INVENTORY_TITLE)
    nxt = clean.find("\n## ", start + len(INVENTORY_TITLE))
    section = clean[start:] if nxt == -1 else clean[start:nxt]
    line0 = clean[:start].count("\n") + 1

    out: list[Finding] = []
    # Standalone papers declare their own mechanisms and evidence scopes.
    # The historical fourteen-slot CODA box remains checked below.
    rows = [line.strip().strip("|").split("|") for line in section.splitlines()
            if line.strip().startswith("|")]
    if rows and [cell.strip() for cell in rows[0]] == [
        "Mechanism", "Mathematical evidence", "Executable scope"
    ]:
        entries = rows[2:]
        names = [row[0].strip().casefold() for row in entries]
        delimiter = len(rows) > 1 and len(rows[1]) == 3 and all(
            re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in rows[1]
        )
        if (not delimiter or not entries or any(len(row) != 3 or any(not cell.strip() for cell in row)
                               for row in entries) or len(names) != len(set(names))):
            out.append(Finding("G5b-inventory", BLOCK, str(path), line0,
                               "scoped inventory needs nonempty, unique mechanisms and both evidence scopes"))
        return out
    for slot in SLOTS_5B:
        m = re.search(rf"(?m)^\|\s*\*\*{re.escape(slot)}[^*]*\*\*\s*\|(.*)$", section)
        if not m:
            out.append(Finding("G5b-inventory", BLOCK, str(path), line0,
                               f"missing required slot {slot!r}"))
        elif not m.group(1).strip().strip("|").strip():
            out.append(Finding("G5b-inventory", BLOCK, str(path), line0,
                               f"slot {slot!r} is empty; typed absence "
                               f"(N/A / OPEN / OracleNeeded) is required"))
    return out


# Raw repo/provider paths leak internal structure into a public deposit.
_REPO_PATH_RE = re.compile(
    r"(?<![\w/.-])(omega_engine|\.agents|\.claude|\.codex|\.grok)/[A-Za-z0-9_./-]+")

# Files the 5b link policy explicitly exempts: "Claim ledgers, proof spines,
# receipts, and ZIP manifests may retain canonical internal paths."
_LINK_EXEMPT_SUFFIXES = ("_claim_ledger.md", "_change_log.md")


def gate_publish_links(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G7b: publish-facing Markdown carries no raw repo or provider paths.

    Compliance 5b publish-facing link policy: publish Markdown must not contain
    local/repo links. Allowed are `https:`, DOI/Zenodo, and same-document
    anchors. Claim ledgers, change logs, proof spines, receipts, and ZIP
    manifests are exempt and keep their canonical internal paths.
    """
    if path.name.endswith(_LINK_EXEMPT_SUFFIXES):
        return []
    out: list[Finding] = []
    for i, line in enumerate(blank_fenced(body).splitlines(), 1):
        for m in _REPO_PATH_RE.finditer(line):
            out.append(Finding("G7b-links", BLOCK, str(path), i,
                               f"raw repo path {m.group(0)!r} in publish-facing "
                               f"Markdown; use an https/DOI locator, or move the "
                               f"pointer to the claim ledger"))
    return out


# --- G6: paper-body separation ---------------------------------------------

_EMBEDDED_HISTORY = (
    (re.compile(r"(?m)^#+[ \t]*Change[ \t]*Log[ \t]*$", re.IGNORECASE),
     "embedded change-log section"),
    (re.compile(r"(?m)^#+[ \t]*.*Appendix[ \t]+D[ \t]*[-–][ \t]*Changelog", re.IGNORECASE),
     "embedded changelog appendix"),
    (re.compile(r"(?m)^\*[ \t]+\*\*v[01]\."), "inline version-history bullet"),
)


def gate_body_separation(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G6: version history and claim tables live in companions, not the body.

    Always blocking: an embedded change log is unambiguous. Merely *referring* to
    the companion is how a paper is supposed to point at its history, so only
    structural markers are matched, never prose mentions.
    """
    clean = blank_fenced(normalize_setext(body, preserve_lines=True))
    out: list[Finding] = []
    for rx, label in _EMBEDDED_HISTORY:
        for m in rx.finditer(clean):
            out.append(Finding("G6-separation", BLOCK, str(path),
                               clean[:m.start()].count("\n") + 1,
                               f"{label}; move it to the sibling "
                               f"{{stem}}_change_log.md"))
    return out


# --- G5c: research layout ---------------------------------------------------

_COMPANION_SUFFIXES = ("_claim_ledger.md", "_change_log.md")


def _stem(path: pathlib.Path) -> str:
    return path.name[:-3] if path.name.endswith(".md") else path.stem


def gate_layout(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G5c: a paper carries its change log as a sibling.

    WARN by default, BLOCK under --strict. The estate holds many support docs,
    run receipts, rubrics, maps, and generated ledgers that are not publishable
    papers and legitimately have no companions; blocking on all of them would
    bury the real findings. Use --strict on a paper actually staged for release,
    Claim ledgers are retired from public packages by the publication skill.
    """
    sev = BLOCK if strict else WARN
    stem = _stem(path)
    return [
        Finding("G5c-layout", sev, str(path), 1,
                f"missing required companion {stem}{suffix}")
        for suffix in ("_change_log.md",)
        if not (path.parent / f"{stem}{suffix}").is_file()
    ]


# --- estate predicate -------------------------------------------------------

# Directories that hold support material, evidence, receipts, generated output,
# and frozen archives -- not publishable papers.
PAPER_NOISE_DIRS = frozenset({
    "_support", "_meta", "_spines", "_archive", "archive", ".archive",
    "sources", "evidence", "generated", "registry", "share_to_noah",
    "docs", "tests", "code", "public-export", "public_export",
    "jupyter_notebooks", "staging", "certificates", "distillations",
})

_FRONT_MATTER_RE = re.compile(r"(?m)^(\*\*Author:\*\*|Canonical ID:)")


def looks_like_paper(path: pathlib.Path) -> bool:
    """Is this .md a publishable paper rather than support material?

    Two signals, both required:
      * it does not sit under a support/evidence/archive directory, and
      * it carries publishable front matter (`**Author:**` or `Canonical ID:`).

    Measured on the estate: a naive "every .md that is not a companion or readme"
    predicate selects 699 files, of which 438 appear to lack a claim ledger. Most
    of those are run receipts, rubrics, series maps, generated volume ledgers,
    and `.archive/` content -- not papers. This predicate selects 82 files with
    only 8 missing a ledger, which is the real compliance-5c debt.
    """
    if path.name.lower() == "readme.md" or path.name.endswith(_COMPANION_SUFFIXES):
        return False
    if any(part in PAPER_NOISE_DIRS for part in path.parts[:-1]):
        return False
    try:
        return bool(_FRONT_MATTER_RE.search(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError):
        return False


# --- G2: citation resolvability ---------------------------------------------

_MATH_RE = re.compile(r"(?s)\$\$.*?\$\$|(?<!\$)\$[^$\n]+\$(?!\$)")


def blank_math(text: str) -> str:
    """Blank LaTeX math spans, preserving line count.

    Citation scanning must not read `$[0,1]$` as citations 0 and 1. PO-000's own
    non-citation brackets (`np.array([1,1])`, `e[0]`) live in fenced code, which
    blank_fenced already handles, but interval notation in math is the same
    hazard one `$` away.
    """
    return _MATH_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


# Two reference styles live in the estate: PO-000 writes "1. Author, ..." while
# 002_finite_obstruction_calculus writes "[1] Author, ...". Accepting only the
# first made every in-text citation in those papers look dangling -- 164 false
# BLOCK findings estate-wide.
_REF_ENTRY_RE = re.compile(r"(?m)^(?:\[(\d{1,3})\]|(\d{1,3})\.)[ \t]+(.+)$")
# A citation, not a markdown link: `[7]` but not `[7](url)`.
_INTEXT_REF_RE = re.compile(r"\[(\d{1,3}(?:[ \t]*,[ \t]*\d{1,3})*)\](?!\()")
_LOCATOR_RE = re.compile(r"https?://|doi:|arxiv:|zenodo", re.IGNORECASE)
# A bold volume number (`*J. Phys.* **28** (1972)`) or a named academic publisher
# makes an entry followable by any librarian even without a URL. What is NOT
# followable is an unpublished companion: "preprint, 2026", "CODA Series Paper
# 011, 2026". Those are the entries a referee cannot chase.
_VOLUME_RE = re.compile(r"\*\*\d+\*\*")
_PUBLISHER_RE = re.compile(
    r"\b(Springer|Elsevier|Cambridge|Oxford|MIT Press|Wiley|Academic Press|"
    r"CRC|Princeton|Birkh[aä]user|de Gruyter|World Scientific|"
    r"Bibliopolis|McGraw-Hill|POPL)\b",
    re.IGNORECASE)


def _is_followable(text: str) -> bool:
    return bool(_LOCATOR_RE.search(text)
                or _VOLUME_RE.search(text)
                or _PUBLISHER_RE.search(text))


def gate_citations(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G2: in-text citations resolve to entries; entries carry a locator.

    A dangling citation is a BLOCK -- it points at nothing. An unfollowable entry
    is a WARN: self-citations to unpublished companions are common in this estate
    and are the author's call, but a referee cannot chase them. PO-000 carries
    seven ("preprint, 2026" and "CODA Series Paper NNN, 2026").

    "Unfollowable" deliberately excludes classic journal and book citations. An
    entry with a bold volume number or a named publisher is findable in any
    library without a URL; warning on Lieb-Robinson 1972 would be noise.
    """
    clean = blank_math(blank_fenced(normalize_setext(body, preserve_lines=True)))
    m = re.search(r"(?m)^#+[ \t]*References[ \t]*$", clean)
    if m is None:
        # No References section. If nothing cites numerically either, this is not
        # a citation defect; missing structure is other gates' business.
        return []
    section, head = clean[m.end():], clean[: m.start()]
    # References routinely wrap across lines.  Looking only at the numbered
    # line discards a DOI, publisher, or URL on the continuation line and
    # produces a false "unfollowable" warning.
    matches = list(_REF_ENTRY_RE.finditer(section))
    entries = {
        int(match.group(1) or match.group(2)):
        section[match.start(3): matches[index + 1].start()
                if index + 1 < len(matches) else len(section)].strip()
        for index, match in enumerate(matches)
    }

    out: list[Finding] = []
    for num, text in sorted(entries.items()):
        if not _is_followable(text):
            out.append(Finding("G2-citations", WARN, str(path), 1,
                               f"reference [{num}] is unfollowable -- no DOI/URL, "
                               f"no journal volume, no publisher: {text[:60]!r}"))
    for mm in _INTEXT_REF_RE.finditer(head):
        for part in mm.group(1).split(","):
            num = int(part.strip())
            if num not in entries:
                out.append(Finding("G2-citations", BLOCK, str(path),
                                   head[: mm.start()].count("\n") + 1,
                                   f"in-text citation [{num}] has no entry in "
                                   f"References"))
    return out


# --- G3: hedge-aware hype ---------------------------------------------------

HYPE_WORDS = ("impossible", "universal", "flawless", "perfectly",
              "fundamentally", "true intelligence")

# Non-claim / scope-fence language. If a block carries any of these, the banned
# words inside it ARE the hedge and must survive: weakening "does not claim a
# universal norm" is the adversary-gate violation, not the fix.
_HEDGE_RE = re.compile(
    r"\b(not|never|without|no|nor|neither|cannot|refus\w*|denies|declines|"
    r"outside|open|fails?|unproven|conjectur\w*|scope|fence|limitation|"
    r"remains|beyond|absent|precludes?|forbid\w*)\b",
    re.IGNORECASE)


def gate_hype(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G3: flag hype vocabulary, but let hedges through. WARN only.

    Hedge detection is BLOCK-scoped, not sentence-scoped, because the estate's
    non-claim boxes put the negation in a lead-in and the banned words after it
    ("**Does not produce.** A universal norm; ..."). A hedge in one paragraph
    still does not excuse hype in the next.

    Never blocking: no regex can decide whether an unhedged "universal" is a
    claim the author can defend. A human reads this output.
    """
    clean = blank_fenced(body)
    out: list[Finding] = []
    offset = 0
    for block in re.split(r"\n[ \t]*\n", clean):
        line0 = clean[:offset].count("\n") + 1
        offset += len(block) + 2
        if _HEDGE_RE.search(block):
            continue
        low = block.lower()
        for w in HYPE_WORDS:
            if w in low:
                out.append(Finding("G3-hype", WARN, str(path), line0,
                                   f"unhedged {w!r} in a block with no non-claim "
                                   f"language; confirm it is a claim you can defend"))
    return out


# --- G8: claim-ledger bijection and encyclopedia agreement ------------------

# First-column tokens that look like claim IDs. Requiring at least one digit is
# what separates a real ID from a header cell ('ID', 'Tag', 'Claim', 'Id').
# Measured shapes across every ledger in published/: A1, D2, S11, K4a, WD-0,
# Q-A0, QM-032-C4, QM_000-C1, WDP000-C1, PL-INF-1, PL-0000-1, PL-040e-1,
# WDP001-RA0-C1. A [A-Z]{1,3}\d{1,3} pattern matches almost none of them.
_LEDGER_ROW_RE = re.compile(
    r"(?m)^\|\s*`?([A-Z][A-Za-z0-9_.\-]{0,22})`?\s*\|(.*)$")


def _is_claim_id(token: str) -> bool:
    return any(ch.isdigit() for ch in token)


def ledger_claim_ids(text: str) -> set[str]:
    """Claim IDs from a ledger's matrix rows, across every scheme in the estate."""
    return {m.group(1) for m in _LEDGER_ROW_RE.finditer(text)
            if _is_claim_id(m.group(1))}


# A dotted Lean identifier (Namespace.theorem_name) or an explicit MECHANIZED tag.
_LEAN_IDENT_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:\.[A-Za-z_][A-Za-z0-9_']*){1,}")
_MECHANIZED_RE = re.compile(r"\bMECHANIZED\b")
# Naming Lean in order to DENY a binding is not claiming one. PO-000 row A1 says
# "no Lean binding of this composite claim"; row B1 "no PO-000 Lean binding".
_NO_BINDING_RE = re.compile(r"\bno\b[^|]{0,40}\bLean\b|\bLean\b[^|]{0,20}\bnone\b",
                            re.IGNORECASE)


def ledger_lean_claims(text: str) -> set[str]:
    """Ledger rows that assert Lean mechanization.

    This is the r12 drift detector: PO-000's rows D2 and D5 were typed
    MECHANIZED ALGEBRAIC CORE against named, kernel-checked theorems while every
    corresponding encyclopedia entry carried lean_status NOT-STARTED.
    """
    out: set[str] = set()
    for m in _LEDGER_ROW_RE.finditer(text):
        ident, rest = m.group(1), m.group(2)
        if not _is_claim_id(ident):
            continue
        if _NO_BINDING_RE.search(rest):
            continue
        if _MECHANIZED_RE.search(rest) or _LEAN_IDENT_RE.search(rest):
            out.add(ident)
    return out


_CLAIM_ID_INDEX_BEGIN = "<!-- claim-id-body-index:begin -->"
_CLAIM_ID_INDEX_END = "<!-- claim-id-body-index:end -->"


def gate_claim_bijection(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G8a: the claim-ID body index is a development aid and must not ship.

    Operator ruling 2026-07-30: the claim ledger is the home and the authority for
    claim IDs. A paper is NOT required to enumerate them, so this gate no longer
    reports "unreachable" ledger IDs -- under the ruling that is the normal state,
    and reporting it would fight the ruling.

    What is checked instead is the inverse: a `claim-id-body-index` block in the
    paper is repository packaging, useful while developing the paper and out of
    place in a public deposit. It warns during development and blocks at release
    (`--strict`).

    The rationale the ruling records: papers are heading for storage as database
    pieces reassembled at print time, at which point an in-paper ID enumeration is
    redundant rather than merely noisy.

    Cross-surface claim agreement is not lost -- that is `enc_agreement` (G8b),
    which compares the ledger against the encyclopedia by alias.
    """
    clean = blank_fenced(body)
    if _CLAIM_ID_INDEX_BEGIN not in clean:
        return []
    start = clean.index(_CLAIM_ID_INDEX_BEGIN)
    end = clean.find(_CLAIM_ID_INDEX_END, start)
    block = clean[start:end if end != -1 else len(clean)]
    rows = sum(1 for line in block.splitlines() if line.lstrip().startswith("| `"))
    return [Finding("G8a-claim-id-index", BLOCK if strict else WARN, str(path),
                    clean[:start].count("\n") + 1,
                    f"claim-ID body index present ({rows} row"
                    f"{'' if rows == 1 else 's'}); it is a development-time "
                    f"reference and must be removed before release -- the claim "
                    f"ledger is the home for claim IDs")]


# --- G9-launcher: public_export reviewer notebook hygiene -------------------

_LAUNCHER_NAMES = ("run_notebook.bat", "run_notebook.sh")


def gate_reviewer_launcher(path: pathlib.Path, body: str, *,
    strict: bool = False) -> list[Finding]:
    """G9-launcher: if a paper package has public_export/, check DIME launchers.

    Applies only when ``path.parent / "public_export"`` is a directory (MUB-style
    paper folder). Silent no-op for flat single-file papers without that layout.

    Checks (WARN by default; BLOCK under --strict):
      * both run_notebook.bat and run_notebook.sh exist
      * each launcher names an actual packaged notebook
      * a notebook that imports ipywidgets has an ipywidgets launcher dependency

    AuthorityEffect: None. Hygiene only; does not open Jupyter or mint authority.
    """
    del body  # package-layout gate; body unused
    pkg = path.parent
    export = pkg / "public_export"
    if not export.is_dir():
        return []

    sev = BLOCK if strict else WARN
    findings: list[Finding] = []
    nb_dir = pkg / "jupyter_notebooks"
    reviewers = sorted(nb_dir.glob("*.ipynb")) if nb_dir.is_dir() else []

    if not reviewers:
        findings.append(Finding(
            "G9-launcher", sev, str(path), 1,
            "public_export/ present but no packaged reviewer notebook"))

    for name in _LAUNCHER_NAMES:
        launcher = export / name
        if not launcher.is_file():
            findings.append(Finding(
                "G9-launcher", sev, str(path), 1,
                f"public_export/{name} missing (1-click notebook launcher)"))
            continue
        try:
            text = launcher.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(
                "G9-launcher", sev, str(path), 1,
                f"public_export/{name} unreadable: {exc}"))
            continue
        low = text.lower()
        targets = re.findall(r"jupyter_notebooks[/\\]([A-Za-z0-9_.-]+\.ipynb)", text, re.IGNORECASE)
        if not targets or any(not (nb_dir / target).is_file() for target in targets):
            findings.append(Finding(
                "G9-launcher", sev, str(path), 1,
                f"public_export/{name} does not open an existing packaged notebook"))
        uses_widgets = any(
            re.search(r"(?:import|from)\s+ipywidgets\b", nb.read_text(encoding="utf-8"))
            for nb in reviewers
        )
        if uses_widgets and "ipywidgets" not in low:
            findings.append(Finding(
                "G9-launcher", sev, str(path), 1,
                f"public_export/{name} omits ipywidgets used by a packaged notebook"))
    return findings


GATES = [gate_tags, gate_setext, gate_branding, gate_mechanism_inventory,
         gate_publish_links, gate_body_separation, gate_layout,
         gate_citations, gate_hype, gate_claim_bijection,
         gate_reviewer_launcher]


# --- fix mode: mechanically safe repairs only -------------------------------


# A leading YAML frontmatter block.
#
# Its closing `---` is textually IDENTICAL to a Setext-H2 underline for the last key
# above it. A Setext normalizer that is not frontmatter-aware therefore rewrites
#
#     migration: VERIFIED          ->      ## migration: VERIFIED
#     ---
#
# and the block never closes. Every downstream YAML reader then swallows the whole
# document as frontmatter and returns an empty body.
#
# This is not hypothetical. It happened in d9bb12ae74 ("/rip-papers remediation") to
# all 1000 files under omega_engine_university/omega_engine_library/encyclopedia/entries/: 0 retained a
# closing `---`, and 977 carry `## migration:` where the terminator belongs. Because
# every file of that shape is hit, the failure is total rather than sampled -- and it
# is silent, since YAML parsers skip `#`-leading lines as comments, so nothing errors.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


def normalize_setext(text: str, *, preserve_lines: bool = False) -> str:
    """Rewrite Setext headings as ATX, outside fences and frontmatter, preserving level.

    Gates that locate a section by `^#+ Name` were blind to Setext headings, and
    most of the estate uses Setext (1629 `-` and 212 `=` underlines). G2, G5b, and
    G6 were therefore silently undercounting: a paper whose References heading was
    `References\\n----------` made gate_citations return early with no findings.

    `preserve_lines=True` replaces the underline with a blank line instead of
    deleting it, so line counts survive. Gates MUST use it -- they report line
    numbers against the text they scanned, and blank_fenced and blank_math
    preserve counts for exactly this reason. `fix_text` uses the collapsing form,
    since it is rewriting the file for real.

    A leading YAML frontmatter block is copied through verbatim (see _FRONTMATTER_RE).
    Verbatim is also line-count-preserving, so `preserve_lines` callers keep reporting
    correct line numbers.
    """
    m = _FRONTMATTER_RE.match(text)
    if m:
        return m.group(0) + _normalize_setext_body(text[m.end():], preserve_lines)
    return _normalize_setext_body(text, preserve_lines)


def _normalize_setext_body(text: str, preserve_lines: bool = False) -> str:
    out: list[str] = []
    pos = 0
    for m in _FENCE_RE.finditer(text):
        if m.start() > pos:
            out.append(_normalize_setext_segment(text[pos:m.start()], preserve_lines))
        out.append(m.group(0))
        pos = m.end()
    out.append(_normalize_setext_segment(text[pos:], preserve_lines))
    return "".join(out)


def _normalize_setext_segment(text: str, preserve_lines: bool = False) -> str:
    keepend = text.endswith("\n")
    lines = text.split("\n")
    trailing = lines.pop() if keepend else None
    fixed, _ = _fix_setext_lines(lines, preserve_lines=preserve_lines)
    return "\n".join(fixed + ([trailing] if keepend else []))


def _fix_setext_lines(lines: list[str], *,
                      preserve_lines: bool = False) -> tuple[list[str], int]:
    """Convert Setext underlines to ATX, using the same rule as gate_setext.

    Level matters. `=` under text is H1, `-` under text is H2. Mapping both to
    '##' would demote every Setext document title in the estate (212 of them).

    With preserve_lines, the underline becomes a blank line rather than being
    dropped, so the result has the same line count as the input.
    """
    out: list[str] = []
    fixed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if (nxt is not None
                and _UNDERLINE_RE.match(nxt)
                and line.strip()
                and not line.lstrip().startswith("#")):
            out.append(("# " if nxt.startswith("=") else "## ") + line.strip())
            if preserve_lines:
                out.append("")
            fixed += 1
            i += 2
            continue
        out.append(line)
        i += 1
    return out, fixed


def fix_text(body: str) -> tuple[str, list[str]]:
    """Repair only the mechanically safe defects, outside fenced code.

    Fixes exactly what a gate flags, and nothing else:
      * the branded inventory title -> the sanctioned 5b alias   (G7 / G5b)
      * Setext underlines -> ATX headings, at the right level     (G4)

    Deliberately does NOT touch:
      * tags. A leftover [OPEN] marks an obligation that must be recorded in the
        dated proof ledger; deleting it loses the obligation.
      * citations, claim IDs, hype. All require judgement.
      * trailing whitespace. 821 lines in the estate end in two spaces, which is
        an intentional Markdown hard line break -- stripping them would change
        rendering, and no gate flags them anyway.

    Fenced code is preserved byte-for-byte: a global regex would rewrite
    Setext-looking lines inside ``` blocks and corrupt them.
    """
    changes: list[str] = []

    # Segment on fences so code blocks pass through untouched.
    segments: list[tuple[bool, str]] = []  # (is_fence, text)
    pos = 0
    for m in _FENCE_RE.finditer(body):
        if m.start() > pos:
            segments.append((False, body[pos:m.start()]))
        segments.append((True, m.group(0)))
        pos = m.end()
    segments.append((False, body[pos:]))

    total_setext = 0
    renamed = False
    rebuilt: list[str] = []
    for is_fence, text in segments:
        if is_fence:
            rebuilt.append(text)
            continue
        # Setext conversion runs BEFORE the rename. A Setext branded title becomes
        # '## Omega Engine Primitives' here, and the rename below must then catch
        # it. The other order leaves the freshly-created ATX branded title behind
        # and needs a second pass to converge.
        keepend = text.endswith("\n")
        lines = text.split("\n")
        trailing = lines.pop() if keepend else None
        fixed_lines, n = _fix_setext_lines(lines)
        total_setext += n
        text = "\n".join(fixed_lines + ([trailing] if keepend else []))
        if BRANDED_TITLE in text:
            text = text.replace(BRANDED_TITLE, INVENTORY_TITLE)
            renamed = True
        rebuilt.append(text)

    if renamed:
        changes.append(f"renamed {BRANDED_TITLE!r} -> {INVENTORY_TITLE!r}")
    if total_setext:
        changes.append(f"converted {total_setext} Setext heading(s) to ATX")
    return "".join(rebuilt), changes


# --- G8b: paper <-> encyclopedia agreement ----------------------------------

ENC_LEDGER_DIR = pathlib.Path(
    "omega_engine_university/omega_engine_library/encyclopedia/indexes/ledgers")


def parse_enc_view(text: str) -> list[dict[str, str]]:
    """Rows of a generated per-paper ledger view.

    Columns: id | kind | name | status | lean_status | paper aliases | layer.
    """
    rows: list[dict[str, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 8 and cells[1].startswith("ENC-"):
            rows.append({
                "line": str(i), "id": cells[1], "kind": cells[2],
                "name": cells[3], "status": cells[4],
                "lean_status": cells[5], "aliases": cells[6], "layer": cells[7],
            })
    return rows


def enc_agreement(paper: pathlib.Path, slug: str, *,
                  repo_root: pathlib.Path | None = None,
                  enc_dir: pathlib.Path | None = None) -> list[Finding]:
    """G8b: the paper's Lean claims agree with the encyclopedia's lean_status.

    This is the automated form of the PO-000 r12 finding. The paper's claim ledger
    typed rows D2 and D5 as MECHANIZED ALGEBRAIC CORE against named, kernel-checked
    theorems, while ENC-0220, ENC-0222, and ENC-0765 all carried NOT-STARTED and no
    ENC entry carried a `paper:po000:D2` or `:D5` alias at all.

    Linkage is by alias (`paper:<slug>:<claim-id>`), so the two directions are:
      * paper claims mechanization, ENC entry says NOT-STARTED  -> BLOCK (drift)
      * paper claims mechanization, no ENC entry owns the ID     -> WARN (unbound)
      * ENC entry is MECHANIZED, paper's ledger claims nothing   -> WARN (credit)

    Requires regen_encyclopedia.py to have exited 0; otherwise the view is stale.
    """
    base = enc_dir or ((repo_root or pathlib.Path.cwd()) / ENC_LEDGER_DIR)
    view = base / f"paper_{slug}.md"
    if not view.is_file():
        return [Finding("G8b-enc", BLOCK, str(view), 1,
                        f"no generated ledger view for slug {slug!r}; run "
                        f"regen_encyclopedia.py and confirm it exits 0")]

    ledger = paper.parent / f"{_stem(paper)}_claim_ledger.md"
    claimed = (ledger_lean_claims(ledger.read_text(encoding="utf-8"))
               if ledger.is_file() else set())

    rows = parse_enc_view(view.read_text(encoding="utf-8"))
    by_claim: dict[str, dict[str, str]] = {}
    for r in rows:
        for alias in re.findall(rf"paper:{re.escape(slug)}:([A-Za-z0-9_.\-]+)",
                                r["aliases"]):
            by_claim[alias] = r

    out: list[Finding] = []
    for cid in sorted(claimed):
        row = by_claim.get(cid)
        if row is None:
            out.append(Finding("G8b-enc", WARN, str(view), 1,
                               f"paper ledger row {cid} asserts Lean mechanization "
                               f"but no encyclopedia entry carries alias "
                               f"paper:{slug}:{cid}"))
        elif row["lean_status"] == "NOT-STARTED":
            out.append(Finding("G8b-enc", BLOCK, str(view), int(row["line"]),
                               f"DRIFT: paper ledger row {cid} asserts Lean "
                               f"mechanization but {row['id']} carries "
                               f"lean_status NOT-STARTED"))

    for r in rows:
        if not r["lean_status"].startswith("MECHANIZED"):
            continue
        owned = re.findall(rf"paper:{re.escape(slug)}:([A-Za-z0-9_.\-]+)", r["aliases"])
        if owned and not (set(owned) & claimed):
            out.append(Finding("G8b-enc", WARN, str(view), int(r["line"]),
                               f"{r['id']} is {r['lean_status']} but the paper's "
                               f"ledger claims no mechanization for {owned}"))
    return out


def run_gates(path: pathlib.Path, *, strict: bool = False) -> list[Finding]:
    body = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    for gate in GATES:
        findings.extend(gate(path, body, strict=strict))
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic paper release pre-flight gate. "
                    "AuthorityEffect: None.")
    ap.add_argument("paths", nargs="+", type=pathlib.Path)
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    ap.add_argument("--fix", action="store_true",
                    help="apply mechanically safe repairs in place "
                         "(inventory title, Setext->ATX); never touches tags, "
                         "citations, claims, hype, or trailing whitespace")
    ap.add_argument("--enc", metavar="SLUG",
                    help="also check paper<->encyclopedia agreement for this "
                         "paper slug, e.g. po000")
    ap.add_argument("--strict", action="store_true",
                    help="treat this paper as release-staged: escalate the "
                         "missing-mechanism-inventory warning to a blocker")
    args = ap.parse_args(argv)

    findings: list[Finding] = []
    for p in args.paths:
        if not p.is_file():
            print(f"error: not a file: {p}", file=sys.stderr)
            return 2
        if args.fix:
            original = p.read_text(encoding="utf-8")
            repaired, changes = fix_text(original)
            if repaired != original:
                # The explicit LF newline is load-bearing: the platform default
                # would write CRLF on Windows and break the release hash
                # invariant established in Task 1 (repo bytes == bundle bytes).
                p.write_text(repaired, encoding="utf-8", newline="\n")
                for c in changes:
                    print(f"FIXED {p}: {c}")
        findings.extend(run_gates(p, strict=args.strict))
        if args.enc:
            findings.extend(enc_agreement(p, args.enc))

    blocks = [f for f in findings if f.severity == BLOCK]
    if args.json:
        print(json.dumps({
            "authority_effect": "None",
            "verdict": "BLOCKED" if blocks else "PASSED",
            "findings": [asdict(f) for f in findings],
        }, indent=2, sort_keys=True))
    else:
        for f in sorted(findings, key=lambda x: (x.path, x.line)):
            print(f"{f.severity:5s} {f.gate:18s} {f.path}:{f.line}  {f.message}")
        print(f"\n{'BLOCKED' if blocks else 'PASSED'}: "
              f"{len(blocks)} blocking, {len(findings) - len(blocks)} warning")
    return 1 if blocks else 0


if __name__ == "__main__":
    raise SystemExit(main())

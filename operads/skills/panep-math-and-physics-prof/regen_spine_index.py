#!/usr/bin/env python3
"""Regenerate spine_index.md for the panep-math-and-physics-prof skill.

Deterministic regeneration (not accretion) from source-of-truth:
  1. Paper index   -- dynamic, from omega_engine/research/published/
  2. GTOC tower    -- dynamic, from research/published/001_coda/
  3. Spine anchors -- dynamic, from canonical_omega_math_spine.md headings
  4. Routing table -- curated constant (5 primitives + 6-layer GT* map)

Running this from source produces a deterministic file, so the manifest cannot
rot relative to the papers/spine. stdlib only; no logging infra dependency.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _find_repo_root() -> Path:
    """Walk up until the research tree is found; see regen_encyclopedia.

    `parents[3]` assumed the skill sat at `.claude/skills/<name>/`; quarantining
    it added a directory level and broke that assumption silently.
    """
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "omega_engine" / "research" / "published").is_dir():
            return candidate
    return here.parents[3]


REPO_ROOT = _find_repo_root()
RESEARCH_DIR = REPO_ROOT / "omega_engine" / "research"
PUBLISHED_DIR = RESEARCH_DIR / "published"


def _find_spine_file() -> Path:
    """Locate the canonical math spine, tolerating relocation within research/.

    The single canonical spine is math_spines_v002/ (authoritative oracle per
    ADR-COM-001; carries §0.2.5 COM). The v1 copy was archived to
    math_spines/.archive/ in Sprint 121. We skip any .archive/ path (the archived
    copy still matches the glob, and '.archive' even sorts before 'math_spines_v002')
    and prefer math_spines_v002/ explicitly, so the index always reflects v002.
    """
    matches = sorted(
        m
        for m in RESEARCH_DIR.glob("**/canonical_omega_math_spine.md")
        if ".archive" not in m.parts
    )
    if matches:
        for m in matches:
            if "math_spines_v002" in m.parts:
                return m
        return matches[0]
    archived = (
        REPO_ROOT
        / "omega_engine"
        / ".omega_engine_official_archive"
        / "canonical_omega_math_spine.md"
    )
    if archived.exists():
        return archived
    # Stable fallback for error messaging if the file is absent entirely.
    return RESEARCH_DIR / "omega_engine_theory" / "canonical_omega_math_spine.md"


SPINE_FILE = _find_spine_file()
OUTPUT_FILE = Path(__file__).resolve().parent / "references" / "spine_index.md"

ROUTING_TABLE = """\
## Routing table (curated -- 5 primitives, 6-layer tower)

The per-layer GT* skills were RETIRED 2026-06-10; routed work loads the
panep-math-and-physics-prof **Authority Firewall** (universal + layer row) and reads the
encyclopedia layer via `indexes/by_layer.md` / `indexes/ledgers/`.

| Need / topic | Primitive | Layer (symbol) | ENC layer | Prof agent |
|---|---|---|---|---|
| residuals, defects, observable deltas | Difference (C^1) | Omega_d (L6) | gtfoc | math-prof |
| exact repair, coboundary | Repair (d0) | Omega_d (L6) | gtfoc | math-prof |
| witnessed sameness mod repair | Quotient (Q^1) | Omega_d (L6) | gtfoc | math-prof |
| consistency defect, closure | Closure (d1) | Omega_d (L6) | gtfoc | math-prof |
| finite descent, terminalization, authority | Authority (Pi#) | Omega_A (L5) | gtfda | math-prof |
| cross-representation transport, loss ledgers | -- | Omega_chi (L4) | gtmur | math-prof |
| comparison/completion, monodromy, anti-laundering | -- | Omega_O (L3) | gtor | math-prof |
| continuum objects, finite shadows, cofinality | -- | Omega_kappa (L2) | gttc | math-prof + physics-prof |
| residual closure, anomalons, horn-filling | -- | Omega_LO (L1) | gtta | math-prof |
| operator lattice, operad coherence, RG flow | -- | global | operad (+ operad-lattice skill) | math-prof |
| FSP gauge, deformation physics, sheaf Laplacian | -- | quantum realization | quantum | physics-prof |
| math NOT yet in spine foundations (e.g. Langlands) | -- | EXTENSION | flag as extension | math-prof + substrate-architect |

Foundations currently in the spine: Higher Category Theory, Homotopy Type
Theory, Homological Algebra. Anything outside these is a **spine extension** --
never fabricate authority for it; defer to the panep-math-and-physics-prof Authority
Firewall (consolidated forbidden claims).

Prof agents (math-prof/physics-prof) name the conceptual witness only; they are
dispatchable as Agent subagent_types only where registered. If not registered in
your environment, do not block or fabricate a verdict -- verify against the spine
directly or use substrate-architect (registered). See SKILL.md routing step 4.
"""


# EXACTLY three digits, matching `carrier.rs::paper_id_of` -- the single source
# of truth for the paper-id grammar in the Rust carrier. `\d+` accepted both a
# 2-digit prefix (999_gtoc/00_series_charter.md was indexed as paper "00", which
# is a series charter, not a publication) and a 4-digit one, which carrier.rs
# rejects outright rather than truncating. Two grammars disagreeing over what
# counts as a paper is how a non-paper file acquires a manifest.
_PAPER_ID = re.compile(r"^(qm_?\d{3}[a-z]?|\d{3}[a-z]?)[_ ]+(.*)$", re.IGNORECASE)
# Files inside a paper folder that are companions, not the paper itself.
_NON_PAPER_TOKENS = ("ledger", "claim", "adversarial", "review", "notes", "audit", "copy")

# Programme-local ids are qualified for display and encyclopedia projections.
# Longest path wins: the former ground-up programme now lives under CODA/GTOC
# but retains its collision-free `gg` identity.
_PROGRAMME_PATH_MNEMONICS = (
    (("001_coda", "gtoc"), "gg"),
    (("000_witnessed_difference",), "wd"),
    (("001_coda",), "gt"),
    (("002_finite_obstruction_calculus",), "foc"),
    (("003_quantum_foundations",), "qf"),
    (("004_projection_obstruction",), "po"),
    (("005_gauge_selection",), "gs"),
    (("006_ai_evaluation",), "ae"),
    (("007_authority_firewall",), "af"),
    (("008_engine_runtime",), "er"),
    (("010_general_relativity",), "gr"),
    (("011_mind_and_consciousness",), "mc"),
    (("012_mutually_unbiased_bases",), "mub"),
)


def qualify_paper_id(pid: str, rel_path: str) -> str:
    """Return the collision-free programme-qualified id for a paper path."""
    parts = Path(rel_path).as_posix().split("/")
    try:
        below = tuple(parts[parts.index("published") + 1 :])
    except ValueError:
        return pid
    for prefix, mnemonic in _PROGRAMME_PATH_MNEMONICS:
        if below[: len(prefix)] == prefix:
            return f"{mnemonic}{pid}"
    return pid


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _main_md_in_folder(folder: Path) -> Path | None:
    """Pick the paper's main .md inside a per-paper folder.

    Folders hold the paper plus companions (claim ledgers, reviews). The main
    paper is the first non-companion .md directly in the folder. A few papers
    (e.g. 021) nest the paper under version/`paper/` subdirs with no direct .md;
    for those we recurse and pick the non-companion file whose stem best matches
    the folder's human title (longest normalized common prefix).
    """
    direct = [
        md
        for md in sorted(folder.glob("*.md"))
        if not any(tok in md.stem.lower() for tok in _NON_PAPER_TOKENS)
    ]
    if direct:
        return direct[0]
    nested = [
        md
        for md in sorted(folder.rglob("*.md"))
        if not any(tok in md.stem.lower() for tok in _NON_PAPER_TOKENS)
    ]
    if not nested:
        return None
    title_norm = _norm(re.sub(r"^\d+[a-z]?[_ ]+", "", folder.name))

    def score(md: Path):
        stem_norm = _norm(md.stem)
        prefix = 0
        for a, b in zip(title_norm, stem_norm):
            if a != b:
                break
            prefix += 1
        # Prefer best title match, then shallowest nesting, then name for stability.
        return (prefix, -len(md.relative_to(folder).parts), md.name)

    return max(nested, key=score)


def _canonical_pid(pid: str) -> str:
    if pid.lower().startswith("qm_"):
        return f"QM_{pid[3:]}"
    return pid


def _paper_row(identity: str, manuscript: Path, root: Path):
    match = _PAPER_ID.match(identity)
    if match is None:
        return None
    pid = _canonical_pid(match.group(1))
    title = match.group(2).replace("_", " ").strip()
    if pid.startswith("QM_"):
        title = title.title().replace(" Qm", " QM")
    return pid, title, manuscript.relative_to(root).as_posix()


def extract_paper_rows(published_dir: Path, root: Path):
    """Discover papers without promoting programme or support documents.

    Each declared programme is scanned one paper-directory level deep. A paper
    directory may still choose a nested manuscript through `_main_md_in_folder`
    (the established Symbol Game monograph layout). CODA is handled explicitly:
    its direct 000--009 children belong to the separate tower index, while only
    `001_coda/gtoc/000..010` carry the retained `gg` paper identities.
    """
    rows: list[tuple[str, str, str]] = []

    def add_file(manuscript: Path, identity: str | None = None) -> None:
        row = _paper_row(identity or manuscript.stem, manuscript, root)
        if row is not None:
            rows.append(row)

    def add_folder(folder: Path) -> None:
        exact = folder / f"{folder.name}.md"
        manuscript = exact if exact.is_file() else _main_md_in_folder(folder)
        if manuscript is None:
            return
        identity = manuscript.stem if _PAPER_ID.match(manuscript.stem) else folder.name
        add_file(manuscript, identity)

    def scan_programme(programme: Path) -> None:
        for item in sorted(programme.iterdir(), key=lambda candidate: candidate.name):
            if item.is_file() and item.suffix.lower() == ".md":
                if item.stem != programme.name:
                    add_file(item)
            elif item.is_dir() and _PAPER_ID.match(item.name):
                add_folder(item)

    programme_names = {prefix[0] for prefix, _ in _PROGRAMME_PATH_MNEMONICS}
    for item in sorted(published_dir.iterdir(), key=lambda candidate: candidate.name):
        if item.is_file() and item.suffix.lower() == ".md":
            add_file(item)
        elif not item.is_dir():
            continue
        elif item.name == "001_coda":
            continue
        elif item.name in programme_names or item.name == "qm":
            scan_programme(item)
        elif _PAPER_ID.match(item.name):
            # Test fixtures and legacy flat estates may place a paper directory
            # directly under the supplied published root.
            add_folder(item)

    ground_up = published_dir / "001_coda" / "gtoc"
    if ground_up.is_dir():
        for folder in sorted(ground_up.iterdir(), key=lambda candidate: candidate.name):
            match = _PAPER_ID.match(folder.name)
            if not folder.is_dir() or match is None:
                continue
            bare_pid = match.group(1)
            if not bare_pid.isdigit() or int(bare_pid) > 10:
                continue
            manuscript = folder / f"{folder.name}.md"
            if manuscript.is_file():
                add_file(manuscript, folder.name)

    return sorted(
        set(rows),
        key=lambda row: (qualify_paper_id(row[0], row[2]), row[2]),
    )


# Entry document inside a GTOC tower paper dir, in preference order. Most dirs
# carry a canonical paper.md; 999_gtoc is a series whose entry point is its
# charter (the individual paper_N/unification_N files are reachable from it).
_GTOC_ENTRY_MDS = ("paper.md", "00_series_charter.md")
_GTOC_DIR_ID = re.compile(r"^(\d{3})_(.+)$")


def gtoc_papers_dir(root: Path) -> Path:
    return root / "omega_engine" / "research" / "published" / "001_coda"


# Legacy GT* layer names -> CODA labels (CODA estate renaming ruling 2026-07-28).
# The pairing of the old ENC directory to the new label is fixed by the Layer table
# in published/001_coda/009_coda/gt_tower_master_design.md -- note gttc -> CODA-CS
# and gtta -> CODA-A, which are NOT guessable from the abbreviations alone.
_LEGACY_TOWER_CLAIMS = {
    "gtfoc": "CODA-FOC",
    "gtfda": "CODA-FDA",
    "gtmur": "CODA-MUR",
    "gtor": "CODA-OR",
    "gttc": "CODA-CS",
    "gtta": "CODA-A",
    "gtla": "GTLA",
    "gtoc": "GTOC",
    "q": "Q",
}

# Relocated CODA estate: layer directories dropped their numeric prefix, so the
# gt id can no longer be read off the directory name. Authoritative source is the
# same Layer/Prose-dir/Lean-lib table: coda_foc=GT000 ... gtla=GT006 (capstone).
# Q is deliberately UNNUMBERED there (`Paper_Q`, `paper_9999.md`, quarantine), so
# it is labelled `gtq` rather than given an invented number. `gtoc` is the
# controls-and-charter series and `009_coda` the book; both sit outside the layer
# tower, which is why they take 008 and 009.
_CODA_LAYER_IDS = {
    "coda_foc": ("gt000", "CODA-FOC"),
    "coda_fda": ("gt001", "CODA-FDA"),
    "coda_mur": ("gt002", "CODA-MUR"),
    "coda_or": ("gt003", "CODA-OR"),
    "coda_cs": ("gt004", "CODA-CS"),
    "coda_a": ("gt005", "CODA-A"),
    "gtla": ("gt006", "GTLA"),
    "coda_q": ("gtq", "Q"),
    "gtoc": ("gt008", "GTOC"),
}


def _tower_claim(raw: str) -> str:
    """Layer label for a tower directory suffix, old or relocated naming.

    A numbered directory such as `006_coda_a` carries the CODA *book* chapter
    number in its prefix while its suffix names a tower layer, so the label has to
    be resolved from the suffix even when the gt id came from the prefix.
    """
    claim = raw.replace("_", " ").strip()
    key = claim.lower().replace(" ", "_")
    if key in _LEGACY_TOWER_CLAIMS:
        return _LEGACY_TOWER_CLAIMS[key]
    if key in _CODA_LAYER_IDS:
        return _CODA_LAYER_IDS[key][1]
    return claim


def _gtoc_entry(item: Path):
    """Locate a tower directory's paper file.

    Order matters. `paper.md` and `00_series_charter.md` are the historical names.
    The relocated estate instead names a paper after its own folder
    (`007_gtla/007_gtla.md`), or after the layer suffix once the numeric
    book-chapter prefix is dropped (`006_coda_a/coda_a.md`). Without these two
    fallbacks every relocated layer resolves to no entry and is silently dropped,
    which is why the tower rendered only its master-design row.
    """
    candidates = [*_GTOC_ENTRY_MDS, f"{item.name}.md"]
    match = _GTOC_DIR_ID.match(item.name)
    if match:
        candidates.append(f"{match.group(2)}.md")
    for name in candidates:
        candidate = item / name
        if candidate.is_file():
            return candidate
    return None


def extract_gtoc_rows(gtoc_dir: Path, root: Path):
    """Index the direct CODA tower and its relocated master design."""
    rows = []
    if not gtoc_dir.exists():
        return rows
    for item in sorted(gtoc_dir.iterdir(), key=lambda candidate: candidate.name):
        if not item.is_dir():
            continue
        match = _GTOC_DIR_ID.match(item.name)
        if match:
            paper_id = f"gt{match.group(1)}"
            claim = _tower_claim(match.group(2))
        else:
            # Relocated estate: no numeric prefix, so resolve by layer name.
            relocated = _CODA_LAYER_IDS.get(item.name.lower())
            if relocated is None:
                continue
            paper_id, claim = relocated
        entry = _gtoc_entry(item)
        if entry is None:
            continue
        rows.append((paper_id, claim, entry.relative_to(root).as_posix()))

    relocated_design = gtoc_dir / "009_coda" / "gt_tower_master_design.md"
    legacy_design = gtoc_dir / "gt_tower_master_design.md"
    if relocated_design.is_file():
        rows.append(
            (
                "gt009",
                "CODA tower master design",
                relocated_design.relative_to(root).as_posix(),
            )
        )
    elif legacy_design.is_file():
        rows.append(
            (
                "gt",
                "GT tower master design",
                legacy_design.relative_to(root).as_posix(),
            )
        )
    return rows


def extract_spine_headings(spine_file: Path):
    headings = []
    for line in spine_file.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{2,3} ", line):
            headings.append(line.strip())
    return headings


def render(rows, headings, gtoc_rows=()):
    out = [
        "# panep-math-and-physics-prof -- spine index (GENERATED)",
        "",
        "> Regenerate with `python .claude/skills/panep-math-and-physics-prof/regen_spine_index.py`.",
        "> Do not hand-edit; edits are overwritten on regen.",
        "",
        "## Paper index",
        "",
        "| id | claim | path |",
        "|---|---|---|",
    ]
    for pid, claim, path in rows:
        qualified = qualify_paper_id(pid, path)
        out.append(f"| {qualified} | {claim} | `{path}` |")
    if gtoc_rows:
        out.extend(
            [
                "",
                "## GTOC foundations tower",
                "",
                "One row per tower paper under",
                "`omega_engine/research/published/001_coda/`; ids are",
                "`gt`-prefixed so they cannot collide with the published `NNN` ids above.",
                "",
                "| id | claim | path |",
                "|---|---|---|",
            ]
        )
        for pid, claim, path in gtoc_rows:
            out.append(f"| {pid} | {claim} | `{path}` |")
    out.extend(["", "## Spine section anchors", ""])
    for h in headings:
        # This pattern was previously written with a doubled backslash before
        # the `s`. Inside a raw string that means a literal backslash, so it
        # never matched any heading: every anchor fell through to the
        # unindented else-branch below and kept its `##` prefix. Covered by
        # test_spine_anchors_strip_hashes_and_indent_by_level.
        m = re.match(r"^(#{2,3})\s+(.*)$", h)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            indent = "  " * (level - 2)
            out.append(f"{indent}- {text}")
        else:
            out.append(f"- {h}")
    out.extend(["", ROUTING_TABLE])
    return "\n".join(out) + "\n"


def generate(
    published_dir: Path = PUBLISHED_DIR, spine_file: Path = SPINE_FILE, root: Path = REPO_ROOT
) -> str:
    # The GTOC tower dir is derived from root so test roots without one simply
    # render no GTOC section (extract_gtoc_rows returns [] for a missing dir).
    return render(
        extract_paper_rows(published_dir, root),
        extract_spine_headings(spine_file),
        extract_gtoc_rows(gtoc_papers_dir(root), root),
    )


def main() -> int:
    # The `\n` below were `\\n`, which wrote a literal backslash-n to stderr
    # instead of ending the line.
    if not SPINE_FILE.exists():
        sys.stderr.write(f"Error: Spine file not found at {SPINE_FILE}\n")
        return 1
    if not PUBLISHED_DIR.exists():
        sys.stderr.write(f"Error: Published directory not found at {PUBLISHED_DIR}\n")
        return 1
    # generate() runs outside the guard: a defect in index construction should
    # surface with its traceback, not be flattened into "Error generating".
    index = generate()
    try:
        OUTPUT_FILE.write_text(index, encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"Error writing spine index to {OUTPUT_FILE}: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

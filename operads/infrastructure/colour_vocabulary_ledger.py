"""An owner ledger for the operad colour vocabulary.

`EPIC-OE-OEWAS-RUST-001` stage **M0** is a claim and owner ledger: freeze the
Python and Rust surfaces, classify what is canonical against what is a
duplicate, and "identify duplicate models, encoders, receipts, and lifecycle
labels." Its acceptance matrix opens with the ten colours, whose decisive
mutation is *"reorder, omit, or add one colour"*.

The vocabulary is declared in more than one place, and the code already knows
it. `omega_oewas/src/model.rs` carries this above `ADMITTED_COLOURS`:

    This is the single vocabulary. `omega_engine_operads`
    carries it twice more (a domain tuple and the machine registry
    `.agents/operad/operad_signature.json`); those three drifted apart once,
    dropping `Contract` and `Diagram`, which silently changed the arity of
    sixteen admitted skills. Keep all four in step.

That comment records a real incident and states a real obligation. **Nothing
enforces it.** No test compares the declarations, so the next drift would be
found the way the last one was.

The measurement that followed was historical: five declaration sites, a Rust
comment that said four, and hand agreement among those five. That tree is gone.

On 2026-10-05, `RUST_MODEL` is `MISSING` and `NONCLAIM`. `rust_model_status`
reports that standing and does not open the file. `read_rust_colours` and
`read_claimed_site_count` refuse with `NONCLAIM` rather than returning an empty
colour set. The site-count sentence in the missing comment is `UNVERIFIED`.
`.agents/operad/` is `HISTORICAL` and absent. This module does not recreate it
and does not create `omega_oewas`. A missing site stays on the record. The
sites that remain are not a closed owner set.

This ledger still compares declarations it can read, so a colour drift fails a
test rather than sixteen skills. It counts present declarations against the
number a present Rust comment claims. It does not choose an owner.

A distinction the ledger keeps, because M0 asks for it: a site that *declares*
the vocabulary is not the same as one that *uses* it. The historical consumer
`.agents/operad/agent_capability_slices.json` named colours and declared none
of them. That path is now `HISTORICAL` and absent. Counting a consumer as a
declaration would inflate the duplication; dropping a missing path would make
the remainder look consistent.

**This ledger does not choose an owner.** Epic section 4 says an ADR must select
one, and section 9 lists that decision as an open obligation. Picking one here
would be this pipeline making a governance decision it has no standing to make.
What it reports is that the decision is unmade and that five sites are
consequently peers.

`AuthorityEffect: None`.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# The ten, in the order the Rust constant lists them. Order is recorded because
# the acceptance matrix names reordering as a decisive mutation, even though the
# Python sites are sets and cannot express it.
CANONICAL_ORDER = (
    "State",
    "Proof",
    "Paper",
    "Code",
    "Contract",
    "Receipt",
    "Ledger",
    "Diagram",
    "Audit",
    "Post",
)

RUST_MODEL = Path("omega_engine/crates_rs/omega_oewas/src/model.rs")


@dataclass(frozen=True, slots=True)
class PathClaim:
    """Standing of one vocabulary path. Absence is data, not an empty vocabulary."""

    path: str
    standing: str
    claim: str
    detail: str


def rust_model_status(repo_root: Path) -> PathClaim:
    """Report `RUST_MODEL` without reading it.

    A present file is `PRESENT` / `DECLARED` only as a path fact. Callers that
    need the colour list open it themselves. A missing file is `MISSING` /
    `NONCLAIM` and is not a colour owner.
    """

    path = RUST_MODEL.as_posix()
    if (repo_root / RUST_MODEL).is_file():
        return PathClaim(
            path=path,
            standing="PRESENT",
            claim="DECLARED",
            detail="path exists; this status check did not read it",
        )
    return PathClaim(
        path=path,
        standing="MISSING",
        claim="NONCLAIM",
        detail="omega_oewas is not a workspace member; the file is not opened",
    )


def _refuse_missing_rust_model(repo_root: Path) -> None:
    status = rust_model_status(repo_root)
    if status.standing != "PRESENT":
        raise LedgerError(
            status.claim,
            f"{status.path} is {status.standing}; {status.detail}",
        )


PLANAR_SUBSTITUTION = Path(
    "omega_engine_operads/domain/planar_substitution.py"
)
OPERAD_COLOURS_MODULE = Path(".agents/operad/domain/colours.py")
OPERAD_SIGNATURE = Path(".agents/operad/operad_signature.json")
BULK_INGEST = Path(".agents/operad/bulk_operad_ingest.py")
CAPABILITY_SLICES = Path(".agents/operad/agent_capability_slices.json")

# Written as English in the Rust doc comment ("Keep all four in step"), so the
# claim has to be read as a word rather than a number.
NUMBER_WORDS = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


class LedgerError(RuntimeError):
    """A typed refusal naming what the ledger would not do."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class SiteRole(str, Enum):
    """Declares the vocabulary, or merely uses it.

    M0 asks for duplicates to be identified. A consumer is not a duplicate: it
    would not drift, because it holds no copy of the list. Conflating the two
    inflates the duplication count and hides which sites a future ADR actually
    has to reconcile.
    """

    DECLARATION = "DECLARATION"
    CONSUMER = "CONSUMER"


@dataclass(frozen=True, slots=True)
class VocabularySite:
    path: str
    symbol: str
    role: SiteRole
    colours: frozenset[str]

    def __post_init__(self) -> None:
        if not self.path or not self.symbol:
            raise LedgerError("BAD_SITE", "a site needs a path and a symbol")
        if self.role is SiteRole.DECLARATION and not self.colours:
            raise LedgerError(
                "EMPTY_DECLARATION",
                f"{self.path}:{self.symbol} declares no colours; an empty "
                f"vocabulary agrees with nothing and would read as consistent",
            )


def _string_constants(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def _python_string_collection(source: str, symbol: str) -> frozenset[str] | None:
    """Find `symbol = <collection of strings>` in a Python module.

    Both `ast.Assign` and `ast.AnnAssign` are handled. That is not a detail:
    `ADMITTED_FINITE_COLOURS` is annotated `FrozenSet[str]`, so a walker that
    only looked at `Assign` missed it -- which is exactly how the fifth
    declaration site went uncounted in the first place.
    """
    tree = ast.parse(source)
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = list(node.targets), node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == symbol:
                names = _string_constants(value)
                if names:
                    return frozenset(names)
    return None


def read_rust_colours(repo_root: Path) -> frozenset[str]:
    _refuse_missing_rust_model(repo_root)
    target = repo_root / RUST_MODEL
    source = target.read_text(encoding="utf-8")
    match = re.search(
        r"ADMITTED_COLOURS\s*:\s*\[&str;\s*(\d+)\]\s*=\s*\[(.*?)\];", source, re.S
    )
    if match is None:
        raise LedgerError(
            "RUST_UNREADABLE", "ADMITTED_COLOURS is no longer a fixed-size array"
        )
    declared_length = int(match.group(1))
    names = re.findall(r'"([^"]+)"', match.group(2))
    if declared_length != len(names):
        raise LedgerError(
            "RUST_LENGTH_MISMATCH",
            f"ADMITTED_COLOURS declares [&str; {declared_length}] "
            f"but lists {len(names)}",
        )
    return frozenset(names)


def read_claimed_site_count(repo_root: Path) -> int:
    """The number the Rust comment claims must be kept in step.

    Read from the comment rather than restated, for the same reason sprint 017's
    budget census reads the gate's limits from the gate: a number held in two
    places is a number that can differ.
    """
    _refuse_missing_rust_model(repo_root)
    target = repo_root / RUST_MODEL
    source = target.read_text(encoding="utf-8")
    match = re.search(r"Keep all (\w+) in step", source)
    if match is None:
        raise LedgerError(
            "CLAIM_ABSENT",
            "the Rust model no longer states how many sites must be kept in step",
        )
    word = match.group(1).lower()
    if word not in NUMBER_WORDS:
        raise LedgerError("CLAIM_UNREADABLE", f"{word!r} is not a number word")
    return NUMBER_WORDS[word]


def find_declaration_sites(repo_root: Path) -> tuple[VocabularySite, ...]:
    """Every place the vocabulary is written out in full.

    Each extractor is named and separate. A generic scan would be shorter and
    would silently return fewer sites when a file changed shape, which is the
    failure this module exists to prevent.
    """
    sites: list[VocabularySite] = []

    sites.append(
        VocabularySite(
            path=str(RUST_MODEL).replace("\\", "/"),
            symbol="ADMITTED_COLOURS",
            role=SiteRole.DECLARATION,
            colours=read_rust_colours(repo_root),
        )
    )

    for path, symbol in (
        (PLANAR_SUBSTITUTION, "OPERAD_COLOURS"),
        (OPERAD_COLOURS_MODULE, "ADMITTED_FINITE_COLOURS"),
    ):
        full = repo_root / path
        if not full.is_file():
            raise LedgerError("SITE_ABSENT", f"{path} is gone; the ledger is stale")
        colours = _python_string_collection(full.read_text(encoding="utf-8"), symbol)
        if colours is None:
            raise LedgerError(
                "SITE_UNREADABLE", f"{path} no longer declares {symbol}"
            )
        sites.append(
            VocabularySite(
                path=str(path).replace("\\", "/"),
                symbol=symbol,
                role=SiteRole.DECLARATION,
                colours=colours,
            )
        )

    signature = json.loads(
        (repo_root / OPERAD_SIGNATURE).read_text(encoding="utf-8")
    )
    declared = signature.get("colours")
    if not isinstance(declared, (dict, list)) or not declared:
        raise LedgerError(
            "SITE_UNREADABLE", f"{OPERAD_SIGNATURE} has no usable `colours`"
        )
    names = (
        list(declared)
        if isinstance(declared, dict)
        else [item if isinstance(item, str) else item.get("name") for item in declared]
    )
    sites.append(
        VocabularySite(
            path=str(OPERAD_SIGNATURE).replace("\\", "/"),
            symbol="colours",
            role=SiteRole.DECLARATION,
            colours=frozenset(str(name) for name in names),
        )
    )

    bulk = (repo_root / BULK_INGEST).read_text(encoding="utf-8")
    literal = frozenset(name for name in CANONICAL_ORDER if f'"{name}"' in bulk)
    if len(literal) < len(CANONICAL_ORDER):
        raise LedgerError(
            "SITE_UNREADABLE",
            f"{BULK_INGEST} names only {len(literal)} colours; it was a "
            f"declaration site when this ledger was written",
        )
    sites.append(
        VocabularySite(
            path=str(BULK_INGEST).replace("\\", "/"),
            symbol="inline literals",
            role=SiteRole.DECLARATION,
            colours=literal,
        )
    )

    return tuple(sites)


def find_consumers(repo_root: Path) -> tuple[VocabularySite, ...]:
    """Sites that use the vocabulary without holding a copy of it."""
    raw = (repo_root / CAPABILITY_SLICES).read_text(encoding="utf-8")
    document = json.loads(raw)
    if "colours" in document:
        raise LedgerError(
            "ROLE_CHANGED",
            f"{CAPABILITY_SLICES} now declares a `colours` key; it has become a "
            f"declaration site and must be counted as one",
        )
    used = frozenset(name for name in CANONICAL_ORDER if f'"{name}"' in raw)
    return (
        VocabularySite(
            path=str(CAPABILITY_SLICES).replace("\\", "/"),
            symbol="agents[].slices",
            role=SiteRole.CONSUMER,
            colours=used,
        ),
    )


def disagreements(sites: tuple[VocabularySite, ...]) -> tuple[str, ...]:
    """Every declaration site that differs from the first, named field by field."""
    declarations = [s for s in sites if s.role is SiteRole.DECLARATION]
    if len(declarations) < 2:
        raise LedgerError(
            "TOO_FEW_SITES",
            "comparing fewer than two declarations proves nothing about drift",
        )
    reference = declarations[0]
    problems: list[str] = []
    for site in declarations[1:]:
        missing = sorted(reference.colours - site.colours)
        extra = sorted(site.colours - reference.colours)
        if missing:
            problems.append(
                f"{site.path}:{site.symbol} is missing {', '.join(missing)}"
            )
        if extra:
            problems.append(
                f"{site.path}:{site.symbol} adds {', '.join(extra)}"
            )
    return tuple(problems)


@dataclass(frozen=True, slots=True)
class OwnerLedger:
    declarations: tuple[VocabularySite, ...]
    consumers: tuple[VocabularySite, ...]
    claimed_site_count: int

    def drift(self) -> tuple[str, ...]:
        return disagreements(self.declarations)

    def undercount(self) -> int:
        """How many declaration sites exist beyond the number claimed."""
        return len(self.declarations) - self.claimed_site_count

    def render(self) -> str:
        lines = [
            "=== OPERAD COLOUR VOCABULARY OWNER LEDGER ===",
            f"declaration sites : {len(self.declarations)}",
            f"claimed in source : {self.claimed_site_count}",
            f"consumers         : {len(self.consumers)}",
            f"canonical owner   : none selected (epic section 4 open obligation)",
            "",
            "declarations:",
        ]
        for site in self.declarations:
            lines.append(f"  {len(site.colours):2d}  {site.path}:{site.symbol}")
        lines.append("")
        lines.append("consumers:")
        for site in self.consumers:
            lines.append(f"  {len(site.colours):2d}  {site.path}:{site.symbol}")
        drift = self.drift()
        lines.append("")
        lines.append(f"drift: {'none' if not drift else ''}")
        lines.extend(f"  {problem}" for problem in drift)
        return "\n".join(lines)


def build_ledger(repo_root: Path) -> OwnerLedger:
    return OwnerLedger(
        declarations=find_declaration_sites(repo_root),
        consumers=find_consumers(repo_root),
        claimed_site_count=read_claimed_site_count(repo_root),
    )


__all__ = [
    "CANONICAL_ORDER",
    "LedgerError",
    "OwnerLedger",
    "PathClaim",
    "SiteRole",
    "VocabularySite",
    "build_ledger",
    "disagreements",
    "find_consumers",
    "find_declaration_sites",
    "read_claimed_site_count",
    "read_rust_colours",
    "rust_model_status",
]

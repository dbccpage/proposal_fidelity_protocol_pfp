"""Numbers stated in prose, bound to the measurement that produced them.

Seed defect 6 of the adversarial campaign found the threat model asserting "67
Rust types remain uncontracted" long after lane R had contracted 110 of them.
The real figure was 14. The defect was not the number -- it was a hand-maintained
count in a document with nothing keeping it honest, which is the same shape as a
mutation kill rate quoted from a script that no longer exists.

Note the direction. The stale figure made this estate look WORSE than it is.
Staleness is not only a risk in the flattering direction, and these tests exist
because a document whose numbers cannot be trusted either way is a document that
misleads.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
THREAT_MODEL = (
    REPO_ROOT / "education" / "documentation" / "the_symbol_game" / "adversary" / "threat_model.md"
    if (REPO_ROOT / "education" / "documentation" / "the_symbol_game" / "adversary" / "threat_model.md").exists()
    else REPO_ROOT / "pfp" / "documentation" / "adversary" / "threat_model.md"
    if (REPO_ROOT / "pfp" / "documentation" / "adversary" / "threat_model.md").exists()
    else REPO_ROOT / "pfp" / "documentation" / "THREAT_MODEL.md"
)
_GOV_CONTRACTS = REPO_ROOT / "governance" / "contracts"
CONTRACTS = (
    _GOV_CONTRACTS / "contracts_pfp"
    if (_GOV_CONTRACTS / "contracts_pfp").is_dir()
    else _GOV_CONTRACTS / "contracts_packets" / "symbol_game"
)
CRATES = (
    REPO_ROOT / "engine" / "crates_rs"
    if (REPO_ROOT / "engine" / "crates_rs").exists()
    else REPO_ROOT / "engine" / "engine" / "crates_rs"
)
RUST_SOURCES = (
    CRATES / "core_symbol_game_runtime" / "src",
    CRATES / "core_symbol_game" / "src",
)

_SERDE_TYPE = re.compile(
    r"#\[derive\(([^)]*)\)\]\s*(?:#\[serde\([^\]]*\)\]\s*)*pub (?:struct|enum) (\w+)"
)
_CONTRACT_TYPE = re.compile(r'^\s*(?:rust_type|python_type):\s*"([^"]+)"', re.M)


def measured_uncontracted() -> set[str]:
    """Rust serde types in the two Symbol Game crates with no contract."""
    contracted = set()
    for path in CONTRACTS.glob("*.contract.yaml"):
        match = _CONTRACT_TYPE.search(path.read_text(encoding="utf-8"))
        if match:
            contracted.add(match.group(1))

    serde_types: set[str] = set()
    for root in RUST_SOURCES:
        for path in root.rglob("*.rs"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for derives, name in _SERDE_TYPE.findall(text):
                if "Serialize" in derives or "Deserialize" in derives:
                    serde_types.add(name)
    return serde_types - contracted


def test_threat_model_numbers_are_current() -> None:
    """The figure in the prose equals the figure a measurement returns.

    Binding them is the point. Correcting the number without this test would
    leave the next reader trusting a count that nothing maintains, which is
    exactly the state the campaign found.
    """
    stated = re.findall(
        r"current figure is \*\*(\d+)\*\*", THREAT_MODEL.read_text(encoding="utf-8")
    )
    assert stated, "the threat model no longer states an uncontracted-type figure"
    assert len(stated) == 1, f"more than one figure stated: {stated}"

    measured = measured_uncontracted()
    assert int(stated[0]) == len(measured), (
        f"the threat model says {stated[0]} uncontracted Rust types; measurement "
        f"finds {len(measured)}: {sorted(measured)}"
    )


def test_every_uncontracted_type_is_a_named_deliberate_omission() -> None:
    """An uncontracted type is acceptable only when the ledger says why.

    This is the assertion that makes the figure above meaningful. Fourteen
    uncontracted types with fourteen stated reasons is a different situation
    from fourteen nobody has looked at, and the count alone cannot tell them
    apart.
    """
    ledger = (CONTRACTS / "UNCONTRACTED.md").read_text(encoding="utf-8")
    unexplained = sorted(name for name in measured_uncontracted() if name not in ledger)
    assert not unexplained, (
        "these types carry no contract and no entry in UNCONTRACTED.md, so nothing "
        f"records whether the omission was a decision: {unexplained}"
    )

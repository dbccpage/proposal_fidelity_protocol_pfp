"""C036: every invariant published in TASK.md must equal the reference solver's value.

Counterexample named by this test: TASK.md once published the sextic n_3 as 9299696544
(solver: 11900417220), the octic n_2 and n_3 as 72970528 and 384813583808 (solver:
128834912 and 1423720546880) and the decic n_1 and n_2 as 168280 and 1403698640 (solver:
231200 and 12215785600). A participant copying those values was scored wrong.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

from c036_quintic_gromov_witten_mirror.reference_solver.solver import (
    solve,
)

TASK_MD = Path(__file__).resolve().parent.parent / "participant_packet" / "TASK.md"

FAMILY_RE = re.compile(
    r"\*\*(?P<name>\w+)\*\*: \$\\mathbb\{WP\}\((?P<weights>[\d, ]+)\)\$, \$d = (?P<degree>\d+)\$, "
    r"\$\\kappa = (?P<kappa>\d+)\$, \$\\mu = [^=]+= (?P<mu>\d+)\$\.\n\s+\* \$(?P<values>[^$]+)\$\."
)
VALUE_RE = re.compile(r"n_(\d+) = (\d+)")


def _published_families() -> list[dict[str, object]]:
    text = TASK_MD.read_text(encoding="utf-8")
    section = text.split("## 3. Pinned One-Parameter Families", 1)[1].split("\n## ", 1)[0]
    families = []
    for m in FAMILY_RE.finditer(section):
        families.append(
            {
                "name": m.group("name"),
                "weights": [int(w) for w in m.group("weights").split(",")],
                "degree": int(m.group("degree")),
                "kappa": m.group("kappa"),
                "mu": int(m.group("mu")),
                "values": {int(k): v for k, v in VALUE_RE.findall(m.group("values"))},
            }
        )
    return families


def test_task_md_lists_four_families_with_twelve_invariants() -> None:
    families = _published_families()
    assert [f["name"] for f in families] == ["Quintic", "Sextic", "Octic", "Decic"]
    assert sum(len(f["values"]) for f in families) == 12


def test_every_published_invariant_matches_reference_solver() -> None:
    mismatches = []
    for fam in _published_families():
        values = fam["values"]
        result = solve(
            {
                "case_id": f"task_md_{fam['name']}",
                "weights": fam["weights"],
                "degree": fam["degree"],
                "max_curve_degree": max(values),
            }
        )
        assert result["status"] == "SOLVED", result
        if result["kappa"] != fam["kappa"]:
            mismatches.append((fam["name"], "kappa", fam["kappa"], result["kappa"]))
        for k, published in values.items():
            if result["gv"][str(k)] != published:
                mismatches.append((fam["name"], f"n_{k}", published, result["gv"][str(k)]))
    assert mismatches == []


def test_published_mu_equals_degree_power_over_weight_powers() -> None:
    for fam in _published_families():
        weights = fam["weights"]
        d = fam["degree"]
        mu = Fraction(d**d)
        for w in weights:
            mu /= Fraction(w**w)
        assert mu == fam["mu"], fam["name"]

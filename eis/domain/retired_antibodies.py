"""The retirement register: antibodies that may never be farmed again.

A retired antibody is **named, not deleted**. An unnamed gap is invisible debt:
delete the record and the next run harvests the same phantom, with nothing left
to say why it was wrong the first time.

Retirement is not rejection. `REJECTED` says a real defect was judged not worth
guarding. `RETIRED` says the defect never existed -- the detector was wrong, and
the antibody is an artifact of the detector's bug rather than evidence about the
world.

AuthorityEffect: None. Retiring an antibody removes a guard; it promotes
nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RetirementRecord:
    """Why one antibody was retired, in enough detail to audit the decision."""

    antibody_id: str
    #: The exact defect string that produced this id. Kept so the retirement can
    #: be replayed: hash it and you get the id back.
    defect: str
    #: What was actually wrong -- the defect, or the detector.
    reason: str
    #: The commit that fixed the detector, so a reader can check the claim.
    repaired_by: str
    #: Where the phantom came from.
    provenance: str


_PARSER_BUG = (
    "Phantom defect. The cochain audit reconstructed post-image files from a "
    "multi-file diff without separating them: non-Python paths were fed to "
    "ast.parse, and every non-hunk line was appended to whichever file was open "
    "at the time. On a diff touching more than one file that guaranteed a "
    "syntax error in all but the last. No syntax error existed in any of these "
    "files."
)

_PR_156 = (
    "Farmed from the PR #156 diff (0a59cd4658), which touched four files. The "
    "first three produced phantom syntax defects; the fourth, "
    "use_cases/councils/social_graph.py, was last in the diff and produced "
    "none. That asymmetry is the bug's signature, not a property of the code."
)

RETIRED_ANTIBODIES: Mapping[str, RetirementRecord] = MappingProxyType(
    {
        record.antibody_id: record
        for record in (
            RetirementRecord(
                antibody_id="ab_syntax_error_e033d14a",
                defect=(
                    "defect:syntax_error:omega_engine_governance.anomalon_councils"
                    ".ooutwire._docs._sap.ana_001_social_graph_v1.0.yaml"
                ),
                reason=(
                    _PARSER_BUG
                    + " This one is a YAML file: it was never Python to begin with."
                ),
                repaired_by="6e3a10af12",
                provenance=_PR_156,
            ),
            RetirementRecord(
                antibody_id="ab_syntax_error_4cb62bc5",
                defect="defect:syntax_error:omega_engine_operations.tests.unit.test_social_graph",
                reason=_PARSER_BUG,
                repaired_by="6e3a10af12",
                provenance=_PR_156,
            ),
            RetirementRecord(
                antibody_id="ab_syntax_error_bb7045c0",
                defect="defect:syntax_error:omega_engine_operations.use_cases.councils.__init__",
                reason=_PARSER_BUG,
                repaired_by="6e3a10af12",
                provenance=_PR_156,
            ),
        )
    }
)

RETIRED_ANTIBODY_IDS: frozenset[str] = frozenset(RETIRED_ANTIBODIES)


def is_retired(antibody_id: str) -> bool:
    """True when this antibody may not be farmed again."""
    return antibody_id in RETIRED_ANTIBODIES


def retirement_reason(antibody_id: str) -> str | None:
    """The recorded reason, or None if the antibody is not retired."""
    record = RETIRED_ANTIBODIES.get(antibody_id)
    return None if record is None else record.reason


__all__ = [
    "RETIRED_ANTIBODIES",
    "RETIRED_ANTIBODY_IDS",
    "RetirementRecord",
    "is_retired",
    "retirement_reason",
]

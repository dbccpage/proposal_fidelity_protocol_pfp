"""Report-only single and pair barrier ablations. AuthorityEffect: None."""

from itertools import combinations
from typing import Callable, Mapping

BARRIERS = ("packet_seat", "composition", "gate_receipt", "two_signal", "custody", "scope")


def barrier_ablation_matrix(
    fixtures: Mapping[str, object], guards: Mapping[str, Callable[[object], bool]],
) -> dict:
    """Evaluate real injected guards with each single/pair guard omitted.

    No provider is called by this reporter. A skipped guard is recorded explicitly;
    outcomes are fixture measurements, never a proof of general defense redundancy.
    """
    if set(guards) != set(BARRIERS):
        raise ValueError("COMPLETE_BARRIER_BINDINGS_REQUIRED")
    trials = []
    for count in (0, 1, 2):
        for disabled in combinations(BARRIERS, count):
            for fixture_id, fixture in sorted(fixtures.items()):
                failures = {}
                for name in BARRIERS:
                    if name in disabled:
                        continue
                    try:
                        accepted = guards[name](fixture)
                    except (ValueError, PermissionError, TypeError) as error:
                        failures[name] = str(error)
                    else:
                        if accepted is not True:
                            failures[name] = "BARRIER_REFUSED"
                trials.append({
                    "fixture_id": fixture_id, "disabled": list(disabled),
                    "accepted": not failures, "refusals": failures,
                })
    return {
        "authority_effect": "None", "report_only": True,
        "evidence_ceiling": "Measured behavior on supplied finite fixture bank",
        "barriers": list(BARRIERS), "trials": trials,
        "woland_ablation_flags": {},
        "woland_flags_note": "Existing no_obstruction_typing changes cochain typing; it does not disable these six boundary guards.",
    }

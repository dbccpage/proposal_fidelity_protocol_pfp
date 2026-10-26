"""Scoped, diagnostic failure guidance. Candidates never become admitted antibodies here."""

from collections import Counter
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class FailureObservationV1:
    scope: str
    signature: str
    reproducer: str
    benign_control: str
    benign_triggered: bool
    execution_error: bool
    provider_failure: bool = False


def failure_guidance(observations, *, scope, enabled=True):
    relevant = [o for o in observations if o.scope == scope and not o.provider_failure]
    if not enabled or not relevant:
        return ()
    errors = [o for o in relevant if o.execution_error]
    if 100 * len(errors) < 15 * len(relevant):
        return ()
    counts = Counter(
        o.signature
        for o in errors
        if o.signature and o.reproducer and o.benign_control and not o.benign_triggered
    )
    return tuple(
        signature for signature, _ in sorted(counts.items(), key=lambda p: (-p[1], p[0]))[:3]
    )


def memory_metrics(observations):
    controlled = [o for o in observations if o.benign_control]
    return {
        "controls": len(controlled),
        "false_positives": sum(o.benign_triggered for o in controlled),
        "provider_failures": sum(o.provider_failure for o in observations),
        "admission": "CANDIDATE_ONLY",
        "activation": "NOT_REQUESTED",
        "candidates": [asdict(o) for o in observations if o.execution_error],
    }

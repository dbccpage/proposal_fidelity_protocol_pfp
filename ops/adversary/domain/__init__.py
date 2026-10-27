"""Domain models and value objects for the Adversary Swarm.

AuthorityEffect: None.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .evidence import (
        CandidateCheckV1,
        CheckerVerdict,
        CritiqueStatus,
        MeasurementStatus,
        ObstructionMeasurementV1,
        StructuredCritiqueV1,
        parse_structured_critique,
    )
    from .models import AdversaryBoutOutcomeV1, AdversaryBoutRequestV1
    from .network import Network
    from .ports import (
        CandidateCheckerPort,
        CochainScoringPort,
        NullCandidateCheckerAdapter,
        NullCochainScoringAdapter,
    )

__all__ = [
    "CandidateCheckV1",
    "CandidateCheckerPort",
    "CheckerVerdict",
    "CochainScoringPort",
    "CritiqueStatus",
    "MeasurementStatus",
    "Network",
    "NullCandidateCheckerAdapter",
    "NullCochainScoringAdapter",
    "ObstructionMeasurementV1",
    "StructuredCritiqueV1",
    "AdversaryBoutRequestV1",
    "AdversaryBoutOutcomeV1",
    "parse_structured_critique",
]


def __getattr__(name: str):
    if name in (
        "CandidateCheckV1",
        "CheckerVerdict",
        "CritiqueStatus",
        "MeasurementStatus",
        "ObstructionMeasurementV1",
        "StructuredCritiqueV1",
        "parse_structured_critique",
    ):
        from . import evidence
        return getattr(evidence, name)
    if name in ("AdversaryBoutOutcomeV1", "AdversaryBoutRequestV1"):
        from . import models
        return getattr(models, name)
    if name == "Network":
        from . import network
        return getattr(network, name)
    if name in (
        "CandidateCheckerPort",
        "CochainScoringPort",
        "NullCandidateCheckerAdapter",
        "NullCochainScoringAdapter",
    ):
        from . import ports
        return getattr(ports, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


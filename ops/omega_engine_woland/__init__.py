"""Standalone Woland 7-Act Swarm Engine Package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib

__all__ = [
    "CodaEvaluationAdapter",
    "CodaEvaluationResult",
    "DualWitnessCertificate",
    "LggrGluingAdapter",
    "LggrGluingResult",
    "ResearchEvidenceEnvelopeV1",
    "ResearchTaskContractV1",
    "SymbolGameRequestV1",
    "WolandBoutOutcomeV1",
    "WolandBoutReceiptV1",
    "WolandBoutRequestV1",
    "WolandSwarmController",
    "WolandSwarmDeliberation",
    "WolandSwarmService",
    "build_woland_runtime",
    "build_woland_service",
    "default_pfp_model_port",
    "default_pfp_seat_transport",
    "execute_7act_woland_bout",
    "load_woland_council_profile",
    "render_7act_novella",
]

_EXPORTS = {
    "CodaEvaluationAdapter": (".infrastructure.coda_adapter", "CodaEvaluationAdapter"),
    "CodaEvaluationResult": (".domain.swarm_models", "CodaEvaluationResult"),
    "DualWitnessCertificate": (".domain.swarm_models", "DualWitnessCertificate"),
    "LggrGluingAdapter": (".infrastructure.lggr_adapter", "LggrGluingAdapter"),
    "LggrGluingResult": (".domain.swarm_models", "LggrGluingResult"),
    "ResearchEvidenceEnvelopeV1": (".domain.swarm_models", "ResearchEvidenceEnvelopeV1"),
    "ResearchTaskContractV1": (".domain.swarm_models", "ResearchTaskContractV1"),
    "SymbolGameRequestV1": (".domain.models", "SymbolGameRequestV1"),
    "WolandBoutOutcomeV1": (".domain.models", "WolandBoutOutcomeV1"),
    "WolandBoutReceiptV1": (".domain.models", "WolandBoutReceiptV1"),
    "WolandBoutRequestV1": (".domain.models", "WolandBoutRequestV1"),
    "WolandSwarmController": (".controllers.woland_controller", "WolandSwarmController"),
    "WolandSwarmDeliberation": (".domain.swarm_models", "WolandSwarmDeliberation"),
    "WolandSwarmService": (".use_cases.bout_service", "WolandSwarmService"),
    "build_woland_runtime": (".runtime", "build_woland_runtime"),
    "build_woland_service": (".runtime", "build_woland_service"),
    "default_pfp_model_port": (
        ".infrastructure.live_openrouter_transport",
        "default_pfp_model_port",
    ),
    "default_pfp_seat_transport": (
        ".infrastructure.live_openrouter_transport",
        "default_pfp_seat_transport",
    ),
    "execute_7act_woland_bout": (".use_cases.bout_service", "execute_7act_woland_bout"),
    "load_woland_council_profile": (".profile.profile_loader", "load_woland_council_profile"),
    "render_7act_novella": (".render.render_novella", "render_7act_novella"),
}


def __getattr__(name):
    if name in _EXPORTS:
        module_name, attribute = _EXPORTS[name]
        value = getattr(importlib.import_module(module_name, __name__), attribute)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(_EXPORTS))

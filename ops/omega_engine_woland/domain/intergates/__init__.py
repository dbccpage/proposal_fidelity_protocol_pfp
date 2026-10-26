"""intergates package
==================

10 PFP Intergate transition dynamics, curvature obstructions, and COGWAR defensive sieves.

Governing Epic: EPIC-OE-WOLAND-002
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_woland.domain.intergates.cogwar_shield import BANNED_HYPE_WORDS, FOUR_PART_SUMMARY_HEADERS, check_claim_hygiene, check_false_urgency, check_four_part_summary, check_manufactured_consensus, check_sycophantic_yielding
    from omega_engine_woland.domain.intergates.evaluator import IntergateEvaluator
    from omega_engine_woland.domain.intergates.intergate_loader import find_intergates_dir, load_intergate_specs
    from omega_engine_woland.domain.intergates.models import CurvatureObstruction, IntergateEvaluationResult, IntergateSpec

__all__ = ['BANNED_HYPE_WORDS', 'FOUR_PART_SUMMARY_HEADERS', 'CurvatureObstruction', 'IntergateEvaluationResult', 'IntergateEvaluator', 'IntergateSpec', 'check_claim_hygiene', 'check_false_urgency', 'check_four_part_summary', 'check_manufactured_consensus', 'check_sycophantic_yielding', 'find_intergates_dir', 'load_intergate_specs']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'BANNED_HYPE_WORDS': ('omega_engine_woland.domain.intergates.cogwar_shield', 'BANNED_HYPE_WORDS'),
    'FOUR_PART_SUMMARY_HEADERS': ('omega_engine_woland.domain.intergates.cogwar_shield', 'FOUR_PART_SUMMARY_HEADERS'),
    'check_claim_hygiene': ('omega_engine_woland.domain.intergates.cogwar_shield', 'check_claim_hygiene'),
    'check_false_urgency': ('omega_engine_woland.domain.intergates.cogwar_shield', 'check_false_urgency'),
    'check_four_part_summary': ('omega_engine_woland.domain.intergates.cogwar_shield', 'check_four_part_summary'),
    'check_manufactured_consensus': ('omega_engine_woland.domain.intergates.cogwar_shield', 'check_manufactured_consensus'),
    'check_sycophantic_yielding': ('omega_engine_woland.domain.intergates.cogwar_shield', 'check_sycophantic_yielding'),
    'IntergateEvaluator': ('omega_engine_woland.domain.intergates.evaluator', 'IntergateEvaluator'),
    'find_intergates_dir': ('omega_engine_woland.domain.intergates.intergate_loader', 'find_intergates_dir'),
    'load_intergate_specs': ('omega_engine_woland.domain.intergates.intergate_loader', 'load_intergate_specs'),
    'CurvatureObstruction': ('omega_engine_woland.domain.intergates.models', 'CurvatureObstruction'),
    'IntergateEvaluationResult': ('omega_engine_woland.domain.intergates.models', 'IntergateEvaluationResult'),
    'IntergateSpec': ('omega_engine_woland.domain.intergates.models', 'IntergateSpec'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

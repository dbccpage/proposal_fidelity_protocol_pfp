"""intergates package
==================

10 PFP Intergate transition dynamics, curvature obstructions, and COGWAR defensive sieves.

Governing Epic: EPIC-OE-ADVERSARY-002
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from adversary.domain.intergates.cogwar_shield import BANNED_HYPE_WORDS, FOUR_PART_SUMMARY_HEADERS, check_claim_hygiene, check_false_urgency, check_four_part_summary, check_manufactured_consensus, check_sycophantic_yielding
    from adversary.domain.intergates.evaluator import IntergateEvaluator
    from adversary.domain.intergates.intergate_loader import find_intergates_dir, load_intergate_specs
    from adversary.domain.intergates.models import CurvatureObstruction, IntergateEvaluationResult, IntergateSpec

__all__ = ['BANNED_HYPE_WORDS', 'FOUR_PART_SUMMARY_HEADERS', 'CurvatureObstruction', 'IntergateEvaluationResult', 'IntergateEvaluator', 'IntergateSpec', 'check_claim_hygiene', 'check_false_urgency', 'check_four_part_summary', 'check_manufactured_consensus', 'check_sycophantic_yielding', 'find_intergates_dir', 'load_intergate_specs']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'BANNED_HYPE_WORDS': ('adversary.domain.intergates.cogwar_shield', 'BANNED_HYPE_WORDS'),
    'FOUR_PART_SUMMARY_HEADERS': ('adversary.domain.intergates.cogwar_shield', 'FOUR_PART_SUMMARY_HEADERS'),
    'check_claim_hygiene': ('adversary.domain.intergates.cogwar_shield', 'check_claim_hygiene'),
    'check_false_urgency': ('adversary.domain.intergates.cogwar_shield', 'check_false_urgency'),
    'check_four_part_summary': ('adversary.domain.intergates.cogwar_shield', 'check_four_part_summary'),
    'check_manufactured_consensus': ('adversary.domain.intergates.cogwar_shield', 'check_manufactured_consensus'),
    'check_sycophantic_yielding': ('adversary.domain.intergates.cogwar_shield', 'check_sycophantic_yielding'),
    'IntergateEvaluator': ('adversary.domain.intergates.evaluator', 'IntergateEvaluator'),
    'find_intergates_dir': ('adversary.domain.intergates.intergate_loader', 'find_intergates_dir'),
    'load_intergate_specs': ('adversary.domain.intergates.intergate_loader', 'load_intergate_specs'),
    'CurvatureObstruction': ('adversary.domain.intergates.models', 'CurvatureObstruction'),
    'IntergateEvaluationResult': ('adversary.domain.intergates.models', 'IntergateEvaluationResult'),
    'IntergateSpec': ('adversary.domain.intergates.models', 'IntergateSpec'),
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

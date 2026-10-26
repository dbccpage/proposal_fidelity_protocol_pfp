"""OEWAS Anti-Skills domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .anti_skill_v2 import AntiSkillActivationProfileV1, AntiSkillCaseResultV1, AntiSkillEvaluationReceiptV2, AntiSkillFixtureBankV1, AntiSkillFixtureCaseV1, AntiSkillHitV1, AntiSkillSpecV2, AntiSkillSubjectV1, HumanAntiSkillAdmissionDecisionV1, PredicateAtomV1, PredicateExpressionV1, VerifiedAntiSkillRegistryV1, canonical_json_bytes
    from .canonical import canonical_id
    from .constants import AUTHORITY_EFFECT_NONE, DIGEST_PATTERN, IDENTIFIER_PATTERN
    from .json_wire import loads_strict_json
    from .ast_checkers import AntiSkillAstVisitor, AstAntiSkillFinding, scan_candidate_ast_for_anti_skills
    from .research_papers import ACTIVE_ANTI_SKILLS, AntiSkillDefinition, get_anti_skill_by_id, get_anti_skill_by_number, total_anti_skills_count

__all__ = ['ACTIVE_ANTI_SKILLS', 'AUTHORITY_EFFECT_NONE', 'AntiSkillActivationProfileV1', 'AntiSkillAstVisitor', 'AntiSkillCaseResultV1', 'AntiSkillDefinition', 'AntiSkillEvaluationReceiptV2', 'AntiSkillFixtureBankV1', 'AntiSkillFixtureCaseV1', 'AntiSkillHitV1', 'AntiSkillSpecV2', 'AntiSkillSubjectV1', 'AstAntiSkillFinding', 'DIGEST_PATTERN', 'HumanAntiSkillAdmissionDecisionV1', 'IDENTIFIER_PATTERN', 'PredicateAtomV1', 'PredicateExpressionV1', 'VerifiedAntiSkillRegistryV1', 'canonical_id', 'canonical_json_bytes', 'get_anti_skill_by_id', 'get_anti_skill_by_number', 'loads_strict_json', 'scan_candidate_ast_for_anti_skills', 'total_anti_skills_count']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AntiSkillActivationProfileV1': ('.anti_skill_v2', 'AntiSkillActivationProfileV1'),
    'AntiSkillCaseResultV1': ('.anti_skill_v2', 'AntiSkillCaseResultV1'),
    'AntiSkillEvaluationReceiptV2': ('.anti_skill_v2', 'AntiSkillEvaluationReceiptV2'),
    'AntiSkillFixtureBankV1': ('.anti_skill_v2', 'AntiSkillFixtureBankV1'),
    'AntiSkillFixtureCaseV1': ('.anti_skill_v2', 'AntiSkillFixtureCaseV1'),
    'AntiSkillHitV1': ('.anti_skill_v2', 'AntiSkillHitV1'),
    'AntiSkillSpecV2': ('.anti_skill_v2', 'AntiSkillSpecV2'),
    'AntiSkillSubjectV1': ('.anti_skill_v2', 'AntiSkillSubjectV1'),
    'HumanAntiSkillAdmissionDecisionV1': ('.anti_skill_v2', 'HumanAntiSkillAdmissionDecisionV1'),
    'PredicateAtomV1': ('.anti_skill_v2', 'PredicateAtomV1'),
    'PredicateExpressionV1': ('.anti_skill_v2', 'PredicateExpressionV1'),
    'VerifiedAntiSkillRegistryV1': ('.anti_skill_v2', 'VerifiedAntiSkillRegistryV1'),
    'canonical_json_bytes': ('.anti_skill_v2', 'canonical_json_bytes'),
    'canonical_id': ('.canonical', 'canonical_id'),
    'AUTHORITY_EFFECT_NONE': ('.constants', 'AUTHORITY_EFFECT_NONE'),
    'DIGEST_PATTERN': ('.constants', 'DIGEST_PATTERN'),
    'IDENTIFIER_PATTERN': ('.constants', 'IDENTIFIER_PATTERN'),
    'loads_strict_json': ('.json_wire', 'loads_strict_json'),
    'AntiSkillAstVisitor': ('.ast_checkers', 'AntiSkillAstVisitor'),
    'AstAntiSkillFinding': ('.ast_checkers', 'AstAntiSkillFinding'),
    'scan_candidate_ast_for_anti_skills': ('.ast_checkers', 'scan_candidate_ast_for_anti_skills'),
    'ACTIVE_ANTI_SKILLS': ('.research_papers', 'ACTIVE_ANTI_SKILLS'),
    'AntiSkillDefinition': ('.research_papers', 'AntiSkillDefinition'),
    'get_anti_skill_by_id': ('.research_papers', 'get_anti_skill_by_id'),
    'get_anti_skill_by_number': ('.research_papers', 'get_anti_skill_by_number'),
    'total_anti_skills_count': ('.research_papers', 'total_anti_skills_count'),
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

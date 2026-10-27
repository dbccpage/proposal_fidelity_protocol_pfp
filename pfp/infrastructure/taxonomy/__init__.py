"""PFP Infrastructure Taxonomy Package.

AuthorityEffect: None.
Canonical typed definitions, registries, and domain hooks for all PFP taxonomic domains.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .arithmetic_domains import (
        ArithmeticDomainDefinition,
        ArithmeticDomainEnum,
        ArithmeticDomainRegistry,
        VALID_ARITHMETIC_DOMAINS,
        get_valid_arithmetic_domains,
    )
    from .checkers import (
        CANONICAL_CHECKERS,
        CheckerContractDefinition,
        CheckerContractEnum,
        CheckerContractRegistry,
        CheckerEnum,
        get_valid_checkers,
    )
    from .claimed_moves import (
        ClaimedMoveDefinition,
        ClaimedMoveEnum,
        ClaimedMoveRegistry,
        VALID_CLAIMED_MOVES,
        get_valid_claimed_moves,
    )
    from .evaluation_statuses import (
        EvaluationStatusDefinition,
        EvaluationStatusEnum,
        EvaluationStatusRegistry,
        VALID_EVALUATION_STATUSES,
        get_valid_evaluation_statuses,
    )
    from .execution_modes import (
        ExecutionModeDefinition,
        ExecutionModeEnum,
        ExecutionModeRegistry,
        VALID_EXECUTION_MODES,
        get_valid_execution_modes,
    )
    from .task_families import (
        VALID_TASK_FAMILIES,
        TaskFamilyDefinition,
        TaskFamilyEnum,
        TaskFamilyRegistry,
        get_valid_task_families,
    )
    from .span_roles import (
        SpanRoleDefinition,
        SpanRoleEnum,
        SpanRoleRegistry,
        VALID_SPAN_ROLES,
        get_valid_span_roles,
    )
    from .trial_statuses import (
        TrialStatusDefinition,
        TrialStatusEnum,
        TrialStatusRegistry,
        VALID_TRIAL_STATUSES,
        get_valid_trial_statuses,
    )
    from .verification_rules import (
        VALID_VERIFICATION_RULES,
        VerificationRuleDefinition,
        VerificationRuleEnum,
        VerificationRuleRegistry,
        get_valid_verification_rules,
    )
    from .verification_statuses import (
        VALID_VERIFICATION_STATUSES,
        VerificationStatusDefinition,
        VerificationStatusEnum,
        VerificationStatusRegistry,
        get_valid_verification_statuses,
    )

__all__ = [
    "ArithmeticDomainDefinition",
    "ArithmeticDomainEnum",
    "ArithmeticDomainRegistry",
    "CANONICAL_CHECKERS",
    "CheckerContractDefinition",
    "CheckerContractEnum",
    "CheckerContractRegistry",
    "CheckerEnum",
    "ClaimedMoveDefinition",
    "ClaimedMoveEnum",
    "ClaimedMoveRegistry",
    "EvaluationStatusDefinition",
    "EvaluationStatusEnum",
    "EvaluationStatusRegistry",
    "ExecutionModeDefinition",
    "ExecutionModeEnum",
    "ExecutionModeRegistry",
    "TaskFamilyDefinition",
    "TaskFamilyEnum",
    "TaskFamilyRegistry",
    "SpanRoleDefinition",
    "SpanRoleEnum",
    "SpanRoleRegistry",
    "TrialStatusDefinition",
    "TrialStatusEnum",
    "TrialStatusRegistry",
    "VALID_ARITHMETIC_DOMAINS",
    "VALID_CLAIMED_MOVES",
    "VALID_EVALUATION_STATUSES",
    "VALID_EXECUTION_MODES",
    "VALID_TASK_FAMILIES",
    "VALID_SPAN_ROLES",
    "VALID_TRIAL_STATUSES",
    "VALID_VERIFICATION_RULES",
    "VALID_VERIFICATION_STATUSES",
    "VerificationRuleDefinition",
    "VerificationRuleEnum",
    "VerificationRuleRegistry",
    "VerificationStatusDefinition",
    "VerificationStatusEnum",
    "VerificationStatusRegistry",
    "get_valid_arithmetic_domains",
    "get_valid_checkers",
    "get_valid_claimed_moves",
    "get_valid_evaluation_statuses",
    "get_valid_execution_modes",
    "get_valid_task_families",
    "get_valid_span_roles",
    "get_valid_trial_statuses",
    "get_valid_verification_rules",
    "get_valid_verification_statuses",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "ArithmeticDomainDefinition": (".arithmetic_domains", "ArithmeticDomainDefinition"),
    "ArithmeticDomainEnum": (".arithmetic_domains", "ArithmeticDomainEnum"),
    "ArithmeticDomainRegistry": (".arithmetic_domains", "ArithmeticDomainRegistry"),
    "VALID_ARITHMETIC_DOMAINS": (".arithmetic_domains", "VALID_ARITHMETIC_DOMAINS"),
    "get_valid_arithmetic_domains": (".arithmetic_domains", "get_valid_arithmetic_domains"),
    "CANONICAL_CHECKERS": (".checkers", "CANONICAL_CHECKERS"),
    "CheckerContractDefinition": (".checkers", "CheckerContractDefinition"),
    "CheckerContractEnum": (".checkers", "CheckerContractEnum"),
    "CheckerContractRegistry": (".checkers", "CheckerContractRegistry"),
    "CheckerEnum": (".checkers", "CheckerEnum"),
    "get_valid_checkers": (".checkers", "get_valid_checkers"),
    "ClaimedMoveDefinition": (".claimed_moves", "ClaimedMoveDefinition"),
    "ClaimedMoveEnum": (".claimed_moves", "ClaimedMoveEnum"),
    "ClaimedMoveRegistry": (".claimed_moves", "ClaimedMoveRegistry"),
    "VALID_CLAIMED_MOVES": (".claimed_moves", "VALID_CLAIMED_MOVES"),
    "get_valid_claimed_moves": (".claimed_moves", "get_valid_claimed_moves"),
    "EvaluationStatusDefinition": (".evaluation_statuses", "EvaluationStatusDefinition"),
    "EvaluationStatusEnum": (".evaluation_statuses", "EvaluationStatusEnum"),
    "EvaluationStatusRegistry": (".evaluation_statuses", "EvaluationStatusRegistry"),
    "VALID_EVALUATION_STATUSES": (".evaluation_statuses", "VALID_EVALUATION_STATUSES"),
    "get_valid_evaluation_statuses": (".evaluation_statuses", "get_valid_evaluation_statuses"),
    "ExecutionModeDefinition": (".execution_modes", "ExecutionModeDefinition"),
    "ExecutionModeEnum": (".execution_modes", "ExecutionModeEnum"),
    "ExecutionModeRegistry": (".execution_modes", "ExecutionModeRegistry"),
    "VALID_EXECUTION_MODES": (".execution_modes", "VALID_EXECUTION_MODES"),
    "get_valid_execution_modes": (".execution_modes", "get_valid_execution_modes"),
    "VALID_TASK_FAMILIES": (".task_families", "VALID_TASK_FAMILIES"),
    "TaskFamilyDefinition": (".task_families", "TaskFamilyDefinition"),
    "TaskFamilyEnum": (".task_families", "TaskFamilyEnum"),
    "TaskFamilyRegistry": (".task_families", "TaskFamilyRegistry"),
    "get_valid_task_families": (".task_families", "get_valid_task_families"),
    "SpanRoleDefinition": (".span_roles", "SpanRoleDefinition"),
    "SpanRoleEnum": (".span_roles", "SpanRoleEnum"),
    "SpanRoleRegistry": (".span_roles", "SpanRoleRegistry"),
    "VALID_SPAN_ROLES": (".span_roles", "VALID_SPAN_ROLES"),
    "get_valid_span_roles": (".span_roles", "get_valid_span_roles"),
    "TrialStatusDefinition": (".trial_statuses", "TrialStatusDefinition"),
    "TrialStatusEnum": (".trial_statuses", "TrialStatusEnum"),
    "TrialStatusRegistry": (".trial_statuses", "TrialStatusRegistry"),
    "VALID_TRIAL_STATUSES": (".trial_statuses", "VALID_TRIAL_STATUSES"),
    "get_valid_trial_statuses": (".trial_statuses", "get_valid_trial_statuses"),
    "VALID_VERIFICATION_RULES": (".verification_rules", "VALID_VERIFICATION_RULES"),
    "VerificationRuleDefinition": (".verification_rules", "VerificationRuleDefinition"),
    "VerificationRuleEnum": (".verification_rules", "VerificationRuleEnum"),
    "VerificationRuleRegistry": (".verification_rules", "VerificationRuleRegistry"),
    "get_valid_verification_rules": (".verification_rules", "get_valid_verification_rules"),
    "VALID_VERIFICATION_STATUSES": (".verification_statuses", "VALID_VERIFICATION_STATUSES"),
    "VerificationStatusDefinition": (".verification_statuses", "VerificationStatusDefinition"),
    "VerificationStatusEnum": (".verification_statuses", "VerificationStatusEnum"),
    "VerificationStatusRegistry": (".verification_statuses", "VerificationStatusRegistry"),
    "get_valid_verification_statuses": (".verification_statuses", "get_valid_verification_statuses"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        module_name, attr_name = target
        module = importlib.import_module(module_name, __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted({*globals().keys(), *_LAZY_IMPORTS.keys()})


# Inject the maintained catalog without making domain imports perform file I/O.
from pfp.domain.value_objects.taxonomy import register_task_family_provider

register_task_family_provider(lambda: __getattr__("TaskFamilyRegistry").get_instance().all_ids())

# Wire checker providers into Domain Identifiers
try:
    from pfp.domain.value_objects.identifiers import (
        register_checker_id_provider,
    )

    register_checker_id_provider(lambda: __getattr__("CheckerContractRegistry").get_instance().all_ids())
except Exception:
    pass

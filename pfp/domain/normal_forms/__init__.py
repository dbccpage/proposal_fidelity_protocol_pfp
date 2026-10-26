"""Normal forms domain layer: relational dependency algebra, contract predicates, and Pydantic models.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .bqnf_validator import BqnfBoundary, BqnfCdcEvent, BqnfEvaluationResult, BqnfValidator
    from .contracts import NFClassification, NFIdentity, NFPurpose, NormalFormContract, NormalFormVerificationReceipt, ProofObligation
    from .examples import order_line, order_line_fails_second_normal_form, street_journal_title, street_journal_title_passes_third_and_fails_boyce_codd, street_journal_title_split
    from .nf_domain_index import NfDomainIndex, NfFamily, NfIndexEntry, is_tbnf_token_string

__all__ = ['BqnfBoundary', 'BqnfCdcEvent', 'BqnfEvaluationResult', 'BqnfValidator', 'NFIdentity', 'NFPurpose', 'NFClassification', 'ProofObligation', 'NormalFormContract', 'NormalFormVerificationReceipt', 'order_line', 'order_line_fails_second_normal_form', 'street_journal_title', 'street_journal_title_passes_third_and_fails_boyce_codd', 'street_journal_title_split', 'NfDomainIndex', 'NfFamily', 'NfIndexEntry', 'is_tbnf_token_string']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'BqnfBoundary': ('.bqnf_validator', 'BqnfBoundary'),
    'BqnfCdcEvent': ('.bqnf_validator', 'BqnfCdcEvent'),
    'BqnfEvaluationResult': ('.bqnf_validator', 'BqnfEvaluationResult'),
    'BqnfValidator': ('.bqnf_validator', 'BqnfValidator'),
    'NFClassification': ('.contracts', 'NFClassification'),
    'NFIdentity': ('.contracts', 'NFIdentity'),
    'NFPurpose': ('.contracts', 'NFPurpose'),
    'NormalFormContract': ('.contracts', 'NormalFormContract'),
    'NormalFormVerificationReceipt': ('.contracts', 'NormalFormVerificationReceipt'),
    'ProofObligation': ('.contracts', 'ProofObligation'),
    'order_line': ('.examples', 'order_line'),
    'order_line_fails_second_normal_form': ('.examples', 'order_line_fails_second_normal_form'),
    'street_journal_title': ('.examples', 'street_journal_title'),
    'street_journal_title_passes_third_and_fails_boyce_codd': ('.examples', 'street_journal_title_passes_third_and_fails_boyce_codd'),
    'street_journal_title_split': ('.examples', 'street_journal_title_split'),
    'NfDomainIndex': ('.nf_domain_index', 'NfDomainIndex'),
    'NfFamily': ('.nf_domain_index', 'NfFamily'),
    'NfIndexEntry': ('.nf_domain_index', 'NfIndexEntry'),
    'is_tbnf_token_string': ('.nf_domain_index', 'is_tbnf_token_string'),
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

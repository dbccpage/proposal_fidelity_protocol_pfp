"""Typed index of the ten PFP extended form contracts.

Models the "Contracts in This Domain" table and the taxonomy statement in
``normal_forms/README.md``: every contract in this domain is an extended form
contract that does not qualify as a true normal form and confers no
authorization.  The contract bodies stay in ``nf.*.yaml`` and are governed by
``normal_form_contract_schema.yaml``; this module checks only the index and
its agreement with each file's identity block.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictStr,
    model_validator,
)

TBNF_ALPHABET: frozenset[str] = frozenset("abcdefghijklmnopqrstuvwxyz0123456789<>")

DOMAIN_CONTRACT_IDS: frozenset[str] = frozenset(
    {
        "nf.experimental.qm_classical",
        "nf.pfp.pfnf",
        "nf.coda.eqnf",
        "nf.coda.gbqnf",
        "nf.compilation.cpnf",
        "nf.representation.tbnf",
        "nf.security.efnf",
        "nf.evidence.certificate",
        "nf.evidence.loss_ledger",
        "nf.logic.qanf",
    }
)


def is_tbnf_token_string(text: str) -> bool:
    """True iff every character lies in the 38-character TBNF alphabet."""
    return all(ch in TBNF_ALPHABET for ch in text)


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class NfFamily(str, Enum):
    """Family column values of the domain table."""

    CODA = "coda"
    EPISTEMIC = "epistemic"
    SECURITY = "security"
    CHANGE = "change"
    COMPILATION = "compilation"
    REPRESENTATION = "representation"
    EVIDENCE = "evidence"
    EXPERIMENTAL = "experimental"


class NfIndexEntry(_Frozen):
    """One row of the domain contract table."""

    nf_id: StrictStr = Field(pattern=r"^nf\.[a-z]+\.[a-z_]+$")
    short_name: StrictStr = Field(min_length=1)
    name: StrictStr = Field(min_length=1)
    family: NfFamily
    form_category: Literal["Extended Form Contract"]
    qualifies_as_true_normal_form: StrictBool
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _never_true_normal_form(self) -> NfIndexEntry:
        if self.qualifies_as_true_normal_form:
            raise ValueError("domain contracts must declare qualifies_as_true_normal_form false")
        return self


class NfDomainIndex(_Frozen):
    """The complete domain contract index with unique ids and short names."""

    contracts: tuple[NfIndexEntry, ...]
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _complete_and_unique(self) -> NfDomainIndex:
        ids = {c.nf_id for c in self.contracts}
        if len(ids) != len(self.contracts):
            raise ValueError("nf_id values must be unique")
        if ids != DOMAIN_CONTRACT_IDS:
            raise ValueError("domain index must contain the complete canonical contract set")
        if len({c.short_name for c in self.contracts}) != len(self.contracts):
            raise ValueError("short_name values must be unique")
        return self

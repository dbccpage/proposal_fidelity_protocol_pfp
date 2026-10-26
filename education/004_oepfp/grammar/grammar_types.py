"""Typed contracts for the PFP grammar inventory and conformance cases.

Models the grammar registry rows and conformance-case records described in
``README.md`` (inventory table, conformance suites) and ``grammars_readme.md``
(Sigma36 / Gamma38 alphabets, whole-input consumption).

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, model_validator

SIGMA36 = "abcdefghijklmnopqrstuvwxyz0123456789"
GAMMA38 = SIGMA36 + "<>"

_PROFILE_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")
_LOWER_FILE_RE = re.compile(r"^[a-z0-9_.\-]+\.ebnf$")


class GrammarBaseModel(BaseModel):
    """Immutable, strict base record."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ConformanceVerdict(str, Enum):
    """Whole-input verdict of a conformance case."""

    ACCEPT = "accept"
    REJECT = "reject"


class GrammarProfileEntry(GrammarBaseModel):
    """One row of the grammar inventory table."""

    grammar_file: Annotated[StrictStr, Field(min_length=1)]
    profile_id: Annotated[StrictStr, Field(min_length=1)]
    start_symbol: Annotated[StrictStr, Field(min_length=1)]
    scope: Annotated[StrictStr, Field(min_length=1)]
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _check_names(self) -> GrammarProfileEntry:
        if not _PROFILE_RE.match(self.profile_id):
            raise ValueError(f"malformed profile id: {self.profile_id!r}")
        if not _LOWER_FILE_RE.match(self.grammar_file):
            raise ValueError("grammar file name must be lowercase snake_case .ebnf")
        return self


class GrammarRegistry(GrammarBaseModel):
    """Inventory of grammars; profile ids and grammar files are unique."""

    governing_standard: StrictStr
    authority_effect: Literal["None"] = "None"
    profiles: Annotated[list[GrammarProfileEntry], Field(min_length=1)]

    @model_validator(mode="after")
    def _unique(self) -> GrammarRegistry:
        ids = [p.profile_id for p in self.profiles]
        files = [p.grammar_file for p in self.profiles]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate profile_id")
        if len(set(files)) != len(files):
            raise ValueError("duplicate grammar_file")
        return self


class PfpConformanceCase(GrammarBaseModel):
    """Case in ``pfp_conformance_cases.json``: keyed by start symbol."""

    id: Annotated[StrictStr, Field(pattern=r"^[A-Z0-9_]+$")]
    start: Annotated[StrictStr, Field(min_length=1)]
    text: StrictStr
    accept: StrictBool

    @property
    def verdict(self) -> ConformanceVerdict:
        return ConformanceVerdict.ACCEPT if self.accept else ConformanceVerdict.REJECT


class ProfileConformanceCase(GrammarBaseModel):
    """Case in ``conformance_cases.json``: keyed by profile id."""

    id: Annotated[StrictStr, Field(pattern=r"^[A-Za-z0-9_\-]+$")]
    profile: Annotated[StrictStr, Field(min_length=1)]
    text: StrictStr
    accept: StrictBool
    note: StrictStr | None = None
    runtime_accept: StrictBool | None = None

    @property
    def verdict(self) -> ConformanceVerdict:
        return ConformanceVerdict.ACCEPT if self.accept else ConformanceVerdict.REJECT


def in_gamma38(text: str) -> bool:
    """Return True when every character of ``text`` lies in Gamma38."""
    return all(ch in GAMMA38 for ch in text)

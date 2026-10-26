"""Pydantic v2 models for Woland Tribunal Gates (Gates 01 through 13).

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr


class WolandGateId(str, Enum):
    PFP_01_HELLA = "PFP-01-HELLA"
    CARRIER_GROUNDING = "PFP-01-HELLA"
    PFP_02_KOROVIEV = "PFP-02-KOROVIEV"
    PFP_03_BEGEMOT = "PFP-03-BEGEMOT"
    PFP_04_AZAZELLO = "PFP-04-AZAZELLO"
    PFP_05_ABADONNA = "PFP-05-ABADONNA"
    PFP_06_MARGARITA = "PFP-06-MARGARITA"
    PFP_07_MASTER = "PFP-07-MASTER"
    PFP_08_BEZDOMNY = "PFP-08-BEZDOMNY"
    PFP_09_BENGALSKY = "PFP-09-BENGALSKY"
    PFP_10_ANNUSHKA = "PFP-10-ANNUSHKA"
    PFP_11_STRAVINSKY = "PFP-11-STRAVINSKY"
    PFP_12_PILATE = "PFP-12-PILATE"
    PFP_13_WOLAND = "PFP-13-WOLAND"
    PFP_14_NATASHA = "PFP-14-NATASHA"
    PFP_15_JEREMY = "PFP-15-JEREMY"
    PFP_16_LIUDMILA = "PFP-16-LIUDMILA"
    PFP_17_POLINA = "PFP-17-POLINA"
    PFP_18_YAROSLAVA = "PFP-18-YAROSLAVA"
    PFP_19_LEVY_MATVEI = "PFP-19-LEVY-MATVEI"
    PFP_20_APHRANIUS = "PFP-20-APHRANIUS"
    PFP_21_YESHUA = "PFP-21-YESHUA"
    PFP_22_RATSLAYER = "PFP-22-RATSLAYER"


class GateSpec(BaseModel):
    """Specification of a Woland Tribunal Gate."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    gate_id: StrictStr = Field(min_length=1)
    name: StrictStr = Field(min_length=1)
    character: StrictStr = Field(min_length=1)
    role: StrictStr = Field(min_length=1)
    authority_effect: StrictStr = Field(default="None")
    version: StrictStr = Field(default="0.2.0")
    doctrine: StrictStr = Field(min_length=1)
    objective: StrictStr = Field(min_length=1)
    fences: List[StrictStr] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    expected_behavior: StrictStr = Field(default="")
    narrowest_defensible_claim: StrictStr = Field(default="")
    next_test_needed: StrictStr = Field(default="")


class GateVerdict(BaseModel):
    """Evaluation verdict for an individual gate."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    gate_id: StrictStr = Field(min_length=1)
    character: StrictStr = Field(min_length=1)
    passed: StrictBool
    refusal_code: Optional[StrictStr] = None
    observation: StrictStr = Field(default="")
    fences_violated: List[StrictStr] = Field(default_factory=list)
    counter_route: Optional[StrictStr] = None
    authority_effect: StrictStr = Field(default="None")


class GateReceipt(BaseModel):
    """Collation receipt after running candidate state through the tribunal gates."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    candidate_id: StrictStr = Field(min_length=1)
    verdicts: List[GateVerdict] = Field(default_factory=list)
    all_passed: StrictBool
    terminal_disposition: StrictStr = Field(default="Refused")
    receipt_sha256: StrictStr = Field(default="")
    authority_effect: StrictStr = Field(default="None")

    @property
    def demo_id(self) -> str:
        return self.candidate_id

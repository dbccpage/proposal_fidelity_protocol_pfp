"""Pydantic v2 models for Adversary Tribunal Gates (Gates 01 through 13).

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr


class AdversaryGateId(str, Enum):
    PFP_01_SYNTAX_PREFILTER = "PFP-01-SYNTAX-PREFILTER"
    CARRIER_GROUNDING = "PFP-01-SYNTAX-PREFILTER"
    PFP_02_DEFECT_HUNTER = "PFP-02-DEFECT-HUNTER"
    PFP_03_GAUGE_BREAKER = "PFP-03-GAUGE-BREAKER"
    PFP_04_SCOPE_GUARD = "PFP-04-SCOPE-GUARD"
    PFP_05_BACKDOOR_AUDITOR = "PFP-05-BACKDOOR-AUDITOR"
    PFP_06_PRIMAL_DUAL = "PFP-06-PRIMAL-DUAL"
    PFP_07_MASTER = "PFP-07-MASTER"
    PFP_08_SCAR_CHRONICLER = "PFP-08-SCAR-CHRONICLER"
    PFP_09_ANTI_HYPE = "PFP-09-ANTI-HYPE"
    PFP_10_BOUNDARY_FUZZER = "PFP-10-BOUNDARY-FUZZER"
    PFP_11_QUARANTINE = "PFP-11-QUARANTINE"
    PFP_12_INTEGRITY_AUDITOR = "PFP-12-INTEGRITY-AUDITOR"
    PFP_13_ADVERSARY = "PFP-13-REALITY-GATE"
    PFP_14_CONTEXT_TRANSPORT = "PFP-14-CONTEXT-TRANSPORT"
    PFP_15_BARE_METAL_ANCHOR = "PFP-15-BARE-METAL-ANCHOR"
    PFP_16_RESILIENCE = "PFP-16-RESILIENCE"
    PFP_17_OVERCONFIDENCE_PROBE = "PFP-17-OVERCONFIDENCE-PROBE"
    PFP_18_PUNCHLIST = "PFP-18-PUNCHLIST"
    PFP_19_LEVY_MATVEI = "PFP-19-CUSTODY"
    PFP_20_COVERT_VERIFIER = "PFP-20-COVERT-VERIFIER"
    PFP_21_TRUTH_REPAIR = "PFP-21-TRUTH-REPAIR"
    PFP_22_HARDWARE_CONSTRAINT = "PFP-22-HARDWARE-CONSTRAINT"


class GateSpec(BaseModel):
    """Specification of a Adversary Tribunal Gate."""

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

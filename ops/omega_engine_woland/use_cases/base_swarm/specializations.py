"""Retinue v0.1 workload profiles and the two exempt Woland swarms.

Ordinary domain workloads are immutable values, not additional swarm classes.
``specialize`` refuses widening; the composition root also checks each profile
with the native host before constructing the one Woland base.

AuthorityEffect: None.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import ClassVar

from omega_engine_woland.domain.specialization import (
    WOLAND_BASE_SPECIALIZATION_V1,
    PortName,
    SwarmSpecializationV1,
    SwarmTypeV1,
    specialize,
)

from .woland_swarm import OmegaEngineWolandSwarm

_ALL = WOLAND_BASE_SPECIALIZATION_V1.licensed_ports
_NO_MATH = _ALL - {PortName.CODA_EVALUATION, PortName.LGGR_GLUING}
_NO_MATH_NO_ENVELOPE = _NO_MATH - {PortName.ENVELOPE_STORE}


def _child(specialization_id: str, skill: str, ports: frozenset[PortName]) -> SwarmSpecializationV1:
    return specialize(
        WOLAND_BASE_SPECIALIZATION_V1,
        specialization_id=specialization_id,
        extra_skills=(skill,),
        licensed_ports=ports,
    )


# Research runs on /woland and its own workflow (.agents/workflows/woland.md); no
# separate /research skill exists or is required (Jeremy, 2026-10-15).
RESEARCH_PROFILE_V01 = specialize(
    WOLAND_BASE_SPECIALIZATION_V1,
    specialization_id="woland.research",
    licensed_ports=_ALL,
)


class OmegaEngineGoverningCouncilsSwarm(OmegaEngineWolandSwarm):
    """Council deliberation and Nomos compliance through Woland bouts."""

    SPECIALIZATION: ClassVar[SwarmSpecializationV1] = _child(
        "woland.governing_councils", "/governance-councils", _NO_MATH
    )


class OmegaEnginePaperReviewSwarm(OmegaEngineWolandSwarm):
    """Paper review stages through Woland bouts, with CODA and LGGR for claim checks."""

    SPECIALIZATION: ClassVar[SwarmSpecializationV1] = _child(
        "woland.paper_review", "/governance-research-paper-edit-publish", _ALL
    )


COGNITIVE_OPERATIONS_PROFILE_V01 = _child(
    "woland.cognitive_operations", "/governance-intelligence-metabolism", _ALL
)
SWARM_DEVELOPER_PROFILE_V01 = _child(
    "woland.swarm_developer", "/techne-oewas-developer", _NO_MATH
)
SOFTWARE_DEVELOPMENT_PROFILE_V01 = _child(
    "woland.software_development", "/techne-software-dev-manager", _NO_MATH
)
PROJECT_MANAGEMENT_PROFILE_V01 = _child(
    "woland.project_management", "/techne-sprint-manager", _NO_MATH_NO_ENVELOPE
)
# Preserve the compatibility profile and port ceiling after source-package cleanup.
TEAMWORK_PREVIEW_PROFILE_V01 = specialize(
    WOLAND_BASE_SPECIALIZATION_V1,
    specialization_id="woland.teamwork_preview",
    licensed_ports=_NO_MATH_NO_ENVELOPE,
)


RESEARCHER_PROFILE_V01: SwarmSpecializationV1 = specialize(
    WOLAND_BASE_SPECIALIZATION_V1,
    specialization_id="woland.researcher",
    licensed_ports=_NO_MATH,
)

SOFTWARE_DEV_PROFILE_V01: SwarmSpecializationV1 = _child(
    "woland.software_dev", "/techne-software-dev-manager", _NO_MATH
)
RESEARCH_PAPER_PROFILE_V01: SwarmSpecializationV1 = _child(
    "woland.research_paper", "/governance-research-paper-edit-publish", _ALL
)
PRODUCT_MGMT_PROFILE_V01: SwarmSpecializationV1 = _child(
    "woland.product_mgmt", "/oikonomia-product-manager", _NO_MATH_NO_ENVELOPE
)
GOVERNING_COUNCILS_PROFILE_V01: SwarmSpecializationV1 = _child(
    "woland.governing_councils", "/governance-councils", _NO_MATH
)
THANATOS_PROFILE_V01: SwarmSpecializationV1 = _child(
    "woland.thanatos", "/thanatos-nemesis", _ALL
)

SWARM_TYPE_PROFILES: MappingProxyType[SwarmTypeV1, SwarmSpecializationV1] = MappingProxyType({
    SwarmTypeV1.OPEN_TOPIC: WOLAND_BASE_SPECIALIZATION_V1,
    SwarmTypeV1.RESEARCH_PAPER: RESEARCH_PAPER_PROFILE_V01,
    SwarmTypeV1.SOFTWARE_DEV: SOFTWARE_DEV_PROFILE_V01,
    SwarmTypeV1.PRODUCT_MGMT: PRODUCT_MGMT_PROFILE_V01,
    SwarmTypeV1.GOVERNING_COUNCILS: GOVERNING_COUNCILS_PROFILE_V01,
    SwarmTypeV1.THANATOS: THANATOS_PROFILE_V01,
})


def resolve_swarm_type_profile(swarm_type: SwarmTypeV1 | str) -> SwarmSpecializationV1:
    st = SwarmTypeV1.from_str(swarm_type)
    return SWARM_TYPE_PROFILES[st]


# The composition root native-validates these exact values before building the base.
WORKLOAD_PROFILES_V01 = MappingProxyType({
    "research": RESEARCH_PROFILE_V01,
    "cognitive_operations": COGNITIVE_OPERATIONS_PROFILE_V01,
    "swarm_developer": SWARM_DEVELOPER_PROFILE_V01,
    "software_development": SOFTWARE_DEVELOPMENT_PROFILE_V01,
    "project_management": PROJECT_MANAGEMENT_PROFILE_V01,
    "teamwork_preview": TEAMWORK_PREVIEW_PROFILE_V01,
    "researcher": RESEARCHER_PROFILE_V01,
    "open_topic": WOLAND_BASE_SPECIALIZATION_V1,
    "software_dev": SOFTWARE_DEV_PROFILE_V01,
    "research_paper": RESEARCH_PAPER_PROFILE_V01,
    "product_mgmt": PRODUCT_MGMT_PROFILE_V01,
    "governing_councils": GOVERNING_COUNCILS_PROFILE_V01,
    "thanatos": THANATOS_PROFILE_V01,
})


SPECIALIZED_SWARMS: tuple[type[OmegaEngineWolandSwarm], ...] = (
    OmegaEngineGoverningCouncilsSwarm,
    OmegaEnginePaperReviewSwarm,
)

__all__ = [
    "SPECIALIZED_SWARMS",
    "SWARM_TYPE_PROFILES",
    "WORKLOAD_PROFILES_V01",
    "RESEARCHER_PROFILE_V01",
    "COGNITIVE_OPERATIONS_PROFILE_V01",
    "OmegaEngineGoverningCouncilsSwarm",
    "OmegaEnginePaperReviewSwarm",
    "PROJECT_MANAGEMENT_PROFILE_V01",
    "RESEARCH_PROFILE_V01",
    "SOFTWARE_DEVELOPMENT_PROFILE_V01",
    "SWARM_DEVELOPER_PROFILE_V01",
    "TEAMWORK_PREVIEW_PROFILE_V01",
    "SOFTWARE_DEV_PROFILE_V01",
    "RESEARCH_PAPER_PROFILE_V01",
    "PRODUCT_MGMT_PROFILE_V01",
    "GOVERNING_COUNCILS_PROFILE_V01",
    "THANATOS_PROFILE_V01",
    "resolve_swarm_type_profile",
]

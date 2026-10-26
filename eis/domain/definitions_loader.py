"""Parse OEEIS typed YAML definitions from text the caller already read.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

import yaml


def mapping_from_yaml_text(content: str | None) -> dict[str, Any]:
    """Parse one YAML mapping. Empty or non-mapping text is an empty mapping."""
    if not content:
        return {}
    data = yaml.safe_load(content)
    if isinstance(data, dict):
        return data
    return {}


def load_native_pharmacy(content: str | None = None) -> dict[str, Any]:
    """Parse native pharmacy mappings, or the embedded fallback."""
    data = mapping_from_yaml_text(content)
    if not data:
        return {
            "native_class_codes": {
                "SelfCertification": "SELF_CERTIFICATION",
                "FakeReceipt": "FAKE_RECEIPT",
                "ConclusionPreload": "CONCLUSION_PRELOAD",
                "SchemaSemanticLaundering": "SCHEMA_SEMANTIC_LAUNDERING",
                "TheoremNameLaundering": "THEOREM_NAME_LAUNDERING",
                "OptimalityHallucination": "OPTIMALITY_HALLUCINATION",
                "ComplexityHallucination": "COMPLEXITY_HALLUCINATION",
                "BranchDropExhaustion": "BRANCH_DROP_EXHAUSTION",
                "PersonaAuthorityLeak": "PERSONA_AUTHORITY_LEAK",
                "PrivateCotDependency": "PRIVATE_COT_DEPENDENCY",
                "VersionDuplication": "VERSION_DUPLICATION",
                "DetectRepairCoupling": "DETECT_REPAIR_COUPLING",
            },
            "native_dispositions": {
                "Finding": "FINDING",
                "Hold": "HOLD",
                "Refuse": "REFUSE",
            },
            "native_refusal_codes": [
                "HOST_BINARY_NOT_FOUND",
                "FFI_CROSSING_FAILED",
                "NATIVE_PHARMACY_REFUSED",
                "NATIVE_REPLY_MALFORMED",
            ],
        }
    return data


def load_screening_vocabulary(content: str | None = None) -> dict[str, Any]:
    """Parse screening vocabulary, or the embedded fallback."""
    data = mapping_from_yaml_text(content)
    if not data:
        return {
            "host_only_keys": [
                "canonical_digest", "verified", "admitted", "admission", "receipt",
                "receipt_hash", "authority_effect", "terminal_status", "outcome_root_sha256", "registry_mutation",
            ],
            "protected_field_keys": [
                "phi", "phi1", "phi2", "phi3", "phi4", "gamma", "gamma2", "xi",
                "verified", "certified", "authorityeffect",
            ],
            "self_certifying_values": [
                "verified", "certified", "authorized", "authorised", "admitted",
                "promoted", "globalgreen", "qed",
            ],
            "superlatives": [
                "optimal", "minimal", "best possible", "fastest", "smallest", "maximal",
            ],
            "complexity_markers": [
                "o(n", "o(1)", "polynomial time", "linear time", "constant time",
            ],
            "private_cot_markers": [
                "<think>", "chain of thought", "my internal reasoning", "as i reasoned privately",
            ],
            "unauthorized_persona_markers": [
                "senior principal architect", "system administrator", "sovereign arbiter", "unrestricted authority",
            ],
            "innate_patterns": {
                "PersonaAuthorityLeak": {
                    "patterns": ["system administrator", "authority override", "operational mode authorized"],
                    "rationale": "Unbacked system administration / persona authority claim without host receipt",
                },
                "SelfCertification": {
                    "patterns": ["verification bypassed", "self-certified", "self-certification"],
                    "rationale": "Self-certified verification or authorization bypass",
                },
                "FakeReceipt": {
                    "patterns": ["receipt", "fake_receipt"],
                    "rationale": "Host-only receipt assertion without host cryptographic signature",
                },
            },
        }
    return data


def load_failure_classes(content: str | None = None) -> dict[str, Any]:
    """Parse failure classes and routing dispositions."""
    return mapping_from_yaml_text(content)


def load_antibody_templates(content: str | None = None) -> dict[str, Any]:
    """Parse archetypal antibody templates."""
    return mapping_from_yaml_text(content)


def load_probing_domains(content: str | None = None) -> dict[str, Any]:
    """Parse physics domains and probe specs."""
    return mapping_from_yaml_text(content)


def load_danger_signals(content: str | None = None) -> dict[str, Any]:
    """Parse danger signals and boundaries."""
    return mapping_from_yaml_text(content)


__all__ = [
    "mapping_from_yaml_text",
    "load_native_pharmacy",
    "load_screening_vocabulary",
    "load_failure_classes",
    "load_antibody_templates",
    "load_probing_domains",
    "load_danger_signals",
]

"""Unit tests for OEEIS YAML definitions and definitions loader.

Validates that declarative YAML files in `.agents/oeeis/definitions/` conform
to typed immune schema versions, carry AuthorityEffect: None, and are correctly
bound to runtime Python modules.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest
import yaml

from omega_engine_epistemic_immune_system.domain.danger_signals import (
    FORBIDDEN_DANGER_OBSERVERS,
    HOST_DANGER_SIGNAL_KINDS,
    INDEPENDENCE_REFUSAL_CODES,
)
from omega_engine_epistemic_immune_system.domain.definitions_loader import (
    load_antibody_templates,
    load_danger_signals,
    load_failure_classes,
    load_native_pharmacy,
    load_probing_domains,
    load_screening_vocabulary,
)
from omega_engine_epistemic_immune_system.infrastructure.definitions_store import (
    definitions_dir,
    read_definition,
)
from omega_engine_epistemic_immune_system.domain.host_checks import (
    PROTECTED_FIELD_KEYS,
    UNAUTHORIZED_PERSONA_MARKERS,
)
from omega_engine_epistemic_immune_system.domain.pharmacy_templates import (
    ANTIBODY_TEMPLATES,
)
from omega_engine_epistemic_immune_system.domain.safe_pattern import (
    MAX_CHOICE_PRODUCT,
    MAX_PATTERN_LENGTH,
    MAX_REPEAT_BOUND,
    UNSAFE_PATTERN_CODES,
)
from omega_engine_epistemic_immune_system.infrastructure.mssn_domains import (
    DOMAIN_ALIASES,
    DOMAINS,
)
from omega_engine_epistemic_immune_system.infrastructure.mssn_pharmacy import (
    COMPLEXITY_MARKERS,
    HOST_ONLY_KEYS,
    PRIVATE_COT_MARKERS,
    SELF_CERTIFYING_VALUES,
    SUPERLATIVES,
    FailureClass,
)
from omega_engine_epistemic_immune_system.infrastructure.native_pharmacy import (
    NATIVE_CLASS_CODES,
    NATIVE_DISPOSITIONS,
    NATIVE_REFUSAL_CODES,
)

EXPECTED_YAML_FILES = (
    "native_pharmacy.yaml",
    "screening_vocabulary.yaml",
    "failure_classes.yaml",
    "antibody_templates.yaml",
    "probing_domains.yaml",
    "danger_signals.yaml",
)


class TestOEEISDefinitionsYAMLFiles:
    """Verifies existence, parseability, and schema metadata of OEEIS YAML files."""

    @pytest.mark.parametrize("filename", EXPECTED_YAML_FILES)
    def test_yaml_file_exists_and_parses(self, filename: str) -> None:
        path = definitions_dir() / filename
        assert path.is_file(), f"Missing definition file: {path}"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{filename} did not parse to a dictionary"
        assert data.get("authority_effect") == "None", f"{filename} missing AuthorityEffect: None"
        assert "schema_version" in data, f"{filename} missing schema_version"
        assert data["schema_version"].startswith("omega.immune.definitions.")


class TestNativePharmacyDefinitionsConfluence:
    """Validates native pharmacy mappings against YAML declarations."""

    def test_native_pharmacy_mappings(self) -> None:
        defs = load_native_pharmacy(read_definition("native_pharmacy.yaml"))
        assert len(defs["native_class_codes"]) == 12
        assert defs["native_class_codes"]["PersonaAuthorityLeak"] == "PERSONA_AUTHORITY_LEAK"
        for variant, code in defs["native_class_codes"].items():
            assert NATIVE_CLASS_CODES[variant] == code

        for disp, code in defs["native_dispositions"].items():
            assert NATIVE_DISPOSITIONS[disp] == code

        assert set(defs["native_refusal_codes"]) == set(NATIVE_REFUSAL_CODES)


class TestScreeningVocabularyDefinitionsConfluence:
    """Validates screening vocabulary and host protection keys against YAML declarations."""

    def test_host_only_keys_confluence(self) -> None:
        vocab = load_screening_vocabulary(read_definition("screening_vocabulary.yaml"))
        assert set(vocab["host_only_keys"]) == set(HOST_ONLY_KEYS)
        assert set(vocab["protected_field_keys"]) == set(PROTECTED_FIELD_KEYS)
        assert set(vocab["self_certifying_values"]) == set(SELF_CERTIFYING_VALUES)
        assert set(vocab["superlatives"]) == set(SUPERLATIVES)
        assert set(vocab["complexity_markers"]) == set(COMPLEXITY_MARKERS)
        assert set(vocab["private_cot_markers"]) == set(PRIVATE_COT_MARKERS)
        assert set(vocab["unauthorized_persona_markers"]) == set(UNAUTHORIZED_PERSONA_MARKERS)


class TestFailureClassesDefinitionsConfluence:
    """Validates failure classes definitions."""

    def test_twelve_failure_classes_defined(self) -> None:
        defs = load_failure_classes(read_definition("failure_classes.yaml"))
        classes = defs["failure_classes"]
        assert len(classes) == 12
        for fc in FailureClass:
            assert fc.value in classes
            entry = classes[fc.value]
            assert entry["code"] == fc.value
            assert entry["default_disposition"] == fc.default_disposition().value


class TestAntibodyTemplatesDefinitionsConfluence:
    """Validates antibody templates against YAML declarations."""

    def test_templates_confluence(self) -> None:
        defs = load_antibody_templates(read_definition("antibody_templates.yaml"))
        templates = defs["templates"]
        assert len(templates) >= 9
        for key in (
            "clean_arch_violation",
            "circular_import",
            "syntax_error",
            "unpriced_semantic_grounding",
            "sorry_used",
            "typeclass_synthesis_failure",
            "float_tolerance_leak",
            "implicit_credential_discovery",
            "limit_honesty_violation",
        ):
            assert key in templates
            assert key in ANTIBODY_TEMPLATES
            t_yaml = templates[key]
            t_obj = ANTIBODY_TEMPLATES[key]
            assert t_yaml["constraint_type"] == t_obj.constraint_type
            assert t_yaml["severity"] == t_obj.severity
            assert t_yaml["action"] == t_obj.action


class TestProbingDomainsDefinitionsConfluence:
    """Validates physics domains and probing specifications against YAML declarations."""

    def test_domains_and_aliases(self) -> None:
        defs = load_probing_domains(read_definition("probing_domains.yaml"))
        assert len(defs["domains"]) == 3
        for d_id in (
            "PHYSICS | SIGN PROBLEM | MERON",
            "PHYSICS | SIGN PROBLEM | HUBBARD",
            "PHYSICS | SIGN PROBLEM | FULL FERMION SIGN PROBLEM",
        ):
            assert d_id in defs["domains"]
            assert d_id in DOMAINS

        aliases = defs["domain_aliases"]
        for alias, target in DOMAIN_ALIASES.items():
            assert aliases[alias] == target


class TestDangerSignalsDefinitionsConfluence:
    """Validates danger signals, observers, refusal codes, and bounds against YAML."""

    def test_danger_signals_and_bounds(self) -> None:
        defs = load_danger_signals(read_definition("danger_signals.yaml"))
        assert set(defs["host_danger_signal_kinds"]) == set(HOST_DANGER_SIGNAL_KINDS)
        assert set(defs["forbidden_danger_observers"]) == set(FORBIDDEN_DANGER_OBSERVERS)
        assert set(defs["independence_refusal_codes"]) == set(INDEPENDENCE_REFUSAL_CODES)

        bounds = defs["safe_pattern_bounds"]
        assert bounds["max_pattern_length"] == MAX_PATTERN_LENGTH
        assert bounds["max_repeat_bound"] == MAX_REPEAT_BOUND
        assert bounds["max_choice_product"] == MAX_CHOICE_PRODUCT
        assert set(bounds["unsafe_pattern_codes"]) == set(UNSAFE_PATTERN_CODES)

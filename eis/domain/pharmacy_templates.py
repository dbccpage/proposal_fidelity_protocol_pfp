from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .pharmacy_models import ConstraintType, Operatorizability, RuntimeAction, Severity


@dataclass(frozen=True)
class AntibodyTemplate:
    constraint_type: str
    operatorizability: str
    action: str
    severity: str
    description: str
    negative_fixture: str
    positive_fixture: str

    def __getitem__(self, item: str) -> str:
        return getattr(self, item)


from .definitions_loader import load_antibody_templates

_raw_templates = load_antibody_templates().get("templates", {})


def _build_templates() -> Mapping[str, AntibodyTemplate]:
    if _raw_templates:
        return {
            key: AntibodyTemplate(
                constraint_type=data["constraint_type"],
                operatorizability=data["operatorizability"],
                action=data["action"],
                severity=data["severity"],
                description=data["description"],
                negative_fixture=data["negative_fixture"],
                positive_fixture=data["positive_fixture"],
            )
            for key, data in _raw_templates.items()
        }
    return {
        "clean_arch_violation": AntibodyTemplate(
            ConstraintType.PROJECT_OUT.value,
            Operatorizability.REPAIRABLE.value,
            RuntimeAction.REPAIR.value,
            Severity.P1.value,
            "Clean Architecture Layer Violation: Inner layers (domain/entities) must not import outer layers (infrastructure/adapters). Invert via Port interface.",
            "from infrastructure.database import query_db\nclass Order: pass\n",
            "from domain.ports import OrderRepositoryPort\nclass Order: pass\n",
        ),
        "circular_import": AntibodyTemplate(
            ConstraintType.PROJECT_OUT.value,
            Operatorizability.REPAIRABLE.value,
            RuntimeAction.REPAIR.value,
            Severity.P0.value,
            "Circular Module Dependency: Cycle detected between modules (gamma_2 > 0). Decouple via intermediary port or event bus.",
            "module_a imports module_b AND module_b imports module_a",
            "module_a and module_b import shared interface from module_c",
        ),
        "syntax_error": AntibodyTemplate(
            ConstraintType.RESTRAIN.value,
            Operatorizability.FATAL.value,
            RuntimeAction.ABORT.value,
            Severity.P0.value,
            "Unparseable Python AST Syntax Error: File contains invalid tokens or unterminated blocks.",
            "def broken_syntax( \n",
            "def broken_syntax(): pass\n",
        ),
        "unpriced_semantic_grounding": AntibodyTemplate(
            ConstraintType.ENFORCE.value,
            Operatorizability.REPAIRABLE.value,
            RuntimeAction.REPAIR.value,
            Severity.P2.value,
            "Ungrounded Indexical Ambiguity: Text requires priced semantic carrier import rather than unassisted cochain lift.",
            "The trophy would not fit in the brown suitcase because it was too big.",
            "The trophy would not fit in the brown suitcase [carrier_ref: spatial_containment_ontology_v1].",
        ),
        "sorry_used": AntibodyTemplate(
            ConstraintType.PROJECT_OUT.value,
            Operatorizability.FATAL.value,
            RuntimeAction.ABORT.value,
            Severity.P0.value,
            "Lean 4 sorry placeholder detected in non-toy proof kernel.",
            "theorem foo : P := by sorry",
            "theorem foo : P := by exact proof_term",
        ),
        "typeclass_synthesis_failure": AntibodyTemplate(
            ConstraintType.RESTRAIN.value,
            Operatorizability.REPAIRABLE.value,
            RuntimeAction.REPAIR.value,
            Severity.P1.value,
            "Typeclass instance resolution failure in formal proof elaboration.",
            "instance resolution failed for Decidable P",
            "open scoped Classical in theorem foo ...",
        ),
        "float_tolerance_leak": AntibodyTemplate(
            ConstraintType.PROJECT_OUT.value,
            Operatorizability.REPAIRABLE.value,
            RuntimeAction.REPAIR.value,
            Severity.P0.value,
            "Floating-point tolerance leak in exact algebraic carrier or detector band check. Mandates exact decimal rational constructors.",
            "def verify_winding(w: float) -> bool:\n    return abs(w - 1.0) < 1e-7\n",
            "from fractions import Fraction\ndef verify_winding(w: Fraction) -> bool:\n    return w == Fraction(1, 1)\n",
        ),
        "implicit_credential_discovery": AntibodyTemplate(
            ConstraintType.RESTRAIN.value,
            Operatorizability.FATAL.value,
            RuntimeAction.ABORT.value,
            Severity.P0.value,
            "Implicit parent credential traversal or unconfigured .env loading. Mandates fail-closed typed refusal.",
            "api_key = os.getenv('OPENROUTER_API_KEY') or load_dotenv('../.env')\n",
            "if not config.api_key:\n    return Err(Refusal(code='CREDENTIAL_NOT_CONFIGURED', locus='provider.adapter'))\n",
        ),
        "limit_honesty_violation": AntibodyTemplate(
            ConstraintType.RESTRAIN.value,
            Operatorizability.REPAIRABLE.value,
            RuntimeAction.REPAIR.value,
            Severity.P0.value,
            "Unhedged thermodynamic limit or asymptotic claim without finite observation realization proof.",
            "Claiming infinite-volume thermodynamic limit convergence without discrete cost tracking.",
            "Finite difference envelope with explicit bounded state transitions and non-zero residual recording.",
        ),
    }


ANTIBODY_TEMPLATES: Mapping[str, AntibodyTemplate] = _build_templates()


def generic_template(defect: str) -> AntibodyTemplate:
    return AntibodyTemplate(
        ConstraintType.RESTRAIN.value,
        Operatorizability.REPAIRABLE.value,
        RuntimeAction.REPAIR.value,
        Severity.P2.value,
        f"Custom obstruction defect: {defect}",
        f"Failing specimen: {defect}",
        f"Repaired invariant for {defect}",
    )


def classify_failure(defect: str) -> str:
    normalized = defect.lower()
    for key in ANTIBODY_TEMPLATES:
        if key in normalized or key.replace("_", " ") in normalized:
            return key
    return "general_obstruction"


# Legacy public shape retained for callers that index template dictionaries.
CANONICAL_ANTIBODY_TEMPLATES = {
    key: {
        "constraint_type": value.constraint_type,
        "operatorizability": value.operatorizability,
        "action": value.action,
        "severity": value.severity,
        "description": value.description,
        "negative_fixture": value.negative_fixture,
        "positive_fixture": value.positive_fixture,
    }
    for key, value in ANTIBODY_TEMPLATES.items()
}

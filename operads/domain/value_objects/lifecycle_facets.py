"""Orthogonal lifecycle facets for OEWAS V3 operations and skills."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .content_digest import ContentDigest


class DeclarationFacet(str, Enum):
    DECLARED = "Declared"
    ABSTRACT = "Abstract"
    SYNTHESIZED = "Synthesized"


class SchemaBindingFacet(str, Enum):
    UNBOUND = "Unbound"
    BOUND = "Bound"
    ANY_SCHEMA = "AnySchema"


class ExecutorBindingFacet(str, Enum):
    UNBOUND = "Unbound"
    BOUND = "Bound"
    EXTERNAL_SERVICE = "ExternalService"


class ValidationFacet(str, Enum):
    UNCHECKED = "Unchecked"
    VALIDATED = "Validated"
    FAILED = "Failed"


class AdmissionFacet(str, Enum):
    UNADMITTED = "Unadmitted"
    ADMITTED = "Admitted"
    RETIRED = "Retired"


@dataclass(frozen=True, slots=True)
class SkillLifecycleV3:
    declaration: DeclarationFacet
    schema_binding: SchemaBindingFacet
    executor_binding: ExecutorBindingFacet
    validation: ValidationFacet
    admission: AdmissionFacet
    schema_digest: Optional[ContentDigest] = None
    executor_digest: Optional[ContentDigest] = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.declaration == other.declaration
            and self.schema_binding == other.schema_binding
            and self.executor_binding == other.executor_binding
            and self.validation == other.validation
            and self.admission == other.admission
            and self.schema_digest == other.schema_digest
            and self.executor_digest == other.executor_digest
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.declaration,
            self.schema_binding,
            self.executor_binding,
            self.validation,
            self.admission,
            self.schema_digest,
            self.executor_digest,
        ))

    @property
    def is_executable(self) -> bool:
        return (
            self.declaration == DeclarationFacet.DECLARED
            and self.schema_binding == SchemaBindingFacet.BOUND
            and self.executor_binding == ExecutorBindingFacet.BOUND
            and self.validation == ValidationFacet.VALIDATED
            and self.admission == AdmissionFacet.ADMITTED
            and self.schema_digest is not None
            and self.executor_digest is not None
            and self.schema_digest != ContentDigest.sha256("0" * 64)
            and self.executor_digest != ContentDigest.sha256("0" * 64)
        )

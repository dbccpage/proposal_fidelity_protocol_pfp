"""Retired: compile parsed skill definitions into higher-operad OperationSpec terms.

The target type, `OperationSpec`, belonged to the Python higher-operad kernel,
retired in f4c6fcf3; `omega_engine/crates_rs/omega_operad_theory` is its Rust
successor and has no Python seam yet. Under RULE_RUST_CRATES_RS_EXCLUSIVE_001
both entry points fail closed with a typed `RUNTIME_RETIRED` refusal and compile
nothing. The implementation remains in git history before this retirement.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Refusal, Result

from ..kernel_retirement import kernel_retired
from ..models import SkillSpecV1

_LOCUS = "omega_engine_operads.legacy.compile_operad_terms"


class CompileOperadTermsUseCase:
    """Retired operad-term compiler; every call refuses."""

    def __init__(
        self,
        signature_path: Path | None = None,
        catalog_path: Path | None = None,
    ) -> None:
        self.signature_path = signature_path
        self.catalog_path = catalog_path

    def compile_skill(self, skill: SkillSpecV1) -> Result[Any, Refusal]:
        del skill
        return kernel_retired(_LOCUS)

    def compile_all(self, skills: Mapping[str, SkillSpecV1]) -> Result[Any, Refusal]:
        del skills
        return kernel_retired(_LOCUS)


__all__ = ["CompileOperadTermsUseCase"]

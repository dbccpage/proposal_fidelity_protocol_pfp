"""Retired: build the Adversary V2 projection from legacy-current ``.agents`` bytes.

The projection normalized each declared substitution with the Python
higher-operad kernel (`Primitive`, `substitute`) and compiled operations through
`CompileOperadTermsUseCase`; both are retired with that kernel (f4c6fcf3), whose
Rust successor `engine/crates_rs/core_operad_theory` has no Python seam
yet. Under RULE_RUST_CRATES_RS_EXCLUSIVE_001 the entry point fails closed with a
typed `RUNTIME_RETIRED` refusal; it reads no estate bytes and compiles no
catalog. The implementation remains in git history before this retirement.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from operations.domain.rop.result import Refusal, Result

from ..catalog_v2 import NodeAssignmentV1
from ..kernel_retirement import kernel_retired
from ..models import CatalogAntiSkillRefV1


def compile_adversary_projection(
    *,
    estate_root: Path,
    manifest_path: Path,
    anti_skills: Mapping[str, CatalogAntiSkillRefV1] | None = None,
    node_assignments: Sequence[NodeAssignmentV1] = (),
) -> Result[Any, Refusal]:
    """Refuse without reading the estate or the manifest."""
    del estate_root, manifest_path, anti_skills, node_assignments
    return kernel_retired("operads.legacy.adversary_projection")


__all__ = ["compile_adversary_projection"]

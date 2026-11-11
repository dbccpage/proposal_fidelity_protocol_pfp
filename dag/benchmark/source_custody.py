"""Source custody for the EIS/PCIV/OPERADS modules the QM workflows invoke (PR #63 review, P2).

Workflow pins used to cover only files in ``dag/benchmark``. The regulation code they
call (EIS consensus and antibodies, PCIV selection, OPERADS composition, and the ops
helpers those import) can change a decision without changing any pinned file. These
repository-relative paths are pinned too. ``test_source_custody`` re-derives the
runtime import closure in a fresh interpreter and fails if a module outside this list
appears, so the list cannot go stale silently.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

REGULATION_FILES = (
    "eis/__init__.py", "eis/domain/__init__.py", "eis/domain/allostery.py", "eis/domain/canonical.py",
    "eis/domain/clonal_selection.py", "eis/domain/danger_gate.py", "eis/domain/danger_signals.py",
    "eis/domain/definitions_loader.py", "eis/domain/guard_activation.py", "eis/domain/ports.py",
    "eis/domain/provisional_promotion.py", "eis/domain/safe_pattern.py", "eis/domain/thymus.py",
    "eis/domain/value_objects.py", "eis/use_cases/__init__.py", "eis/use_cases/mssn_immune.py",
    "eis/use_cases/two_signal_regulation.py",
    "operads/__init__.py", "operads/canon/__init__.py", "operads/canon/_generated.py", "operads/domain/__init__.py",
    "operads/domain/operad/__init__.py", "operads/domain/operad/colours.py", "operads/domain/operad/errors.py",
    "operads/domain/operad/operation.py", "operads/domain/operad/planar.py",
    "pciv/__init__.py", "pciv/domain/__init__.py", "pciv/domain/canonical.py", "pciv/domain/causal_witness.py",
    "pciv/domain/models.py", "pciv/use_cases/__init__.py", "pciv/use_cases/fitness.py", "pciv/use_cases/forge.py",
    "pciv/use_cases/genealogy.py", "pciv/use_cases/immunity.py", "pciv/use_cases/transitive_immunity.py",
    "ops/adversary/__init__.py", "ops/adversary/domain/__init__.py", "ops/adversary/domain/evidence.py",
    "ops/adversary/domain/native.py", "ops/adversary/stage/__init__.py", "ops/adversary/stage/domain/__init__.py",
    "ops/adversary/stage/domain/canonical.py", "ops/adversary/stage/domain/ddc.py",
    "ops/adversary/stage/domain/packets.py", "ops/adversary/stage/domain/topology.py",
    "ops/adversary/stage/profiles/__init__.py",
    "ops/operations/__init__.py", "ops/operations/domain/__init__.py", "ops/operations/domain/rop/__init__.py",
    "ops/operations/domain/rop/result.py", "ops/operations/domain/cicd/__init__.py",
    "ops/operations/domain/cicd/anchors.py", "ops/operations/domain/cicd/base.py",
    "ops/operations/domain/cicd/catalog.py", "ops/operations/domain/cicd/constants.py",
    "ops/operations/domain/cicd/digests.py", "ops/operations/domain/cicd/enums.py",
    "ops/operations/domain/cicd/errors.py", "ops/operations/domain/cicd/fields.py",
    "ops/operations/domain/cicd/gate_spec.py", "ops/operations/domain/cicd/invocation.py",
    "ops/operations/domain/cicd/manifest.py", "ops/operations/domain/cicd/models.py",
    "ops/operations/domain/cicd/protocols.py", "ops/operations/domain/cicd/receipt.py",
    "ops/operations/domain/cicd/result.py", "ops/operations/domain/cicd/routes.py",
    "ops/operations/domain/cicd/text_io.py", "ops/operations/domain/cicd/validators.py",
    "ops/operations/domain/cicd/verification_inputs.py",
)


_REPO_RELATIVE = frozenset(REGULATION_FILES)


def pin_path(name: str) -> Path:
    """Names in REGULATION_FILES are repository-relative; every other pin is relative to dag/benchmark."""
    return ROOT / name if name in _REPO_RELATIVE else HERE / name


def file_sha256(name: str) -> str:
    return hashlib.sha256(pin_path(name).read_bytes()).hexdigest()


def regulation_pins() -> dict[str, str]:
    return {name: file_sha256(name) for name in REGULATION_FILES if pin_path(name).is_file()}

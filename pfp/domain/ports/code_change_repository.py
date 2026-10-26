"""Code Change Repository Port Protocol."""

from __future__ import annotations

from typing import Protocol

from ..aggregates.code_change_run_root import (
    CodeChangePatchArtifactV1,
    CodeChangeRunRootV1,
    # The aggregate receipt, NOT `domain.entities.gate_receipt.GateReceiptV1`.
    # The two are not variants of one idea. The entity carries `gate_name`,
    # `disposition`, `message`, `retained_metrics` and `authority_effect` -- and
    # no `packet_id`, no `candidate_id`, no `evidence_sha256`. It is structurally
    # incapable of naming the candidate it describes, so a port declaring
    # `save_gate_receipt` against it promised to persist a receipt that could
    # never be bound to anything. Every receipt the controller actually produces
    # is this one.
    GateReceiptV1,
)


class ICodeChangeRepository(Protocol):
    """Protocol for Code Change Proposal persistence and retrieval.

    The canonical, typed port. A second, untyped `ICodeChangeRepository`
    (`save`/`find_by_id` over `Any`) previously sat in `ports/ports.py` with no
    direct consumer; it was deleted rather than maintained, so that this name has
    exactly one meaning.
    """

    def save_run_root(self, run_root: CodeChangeRunRootV1) -> None:
        ...

    def get_run_root(self, run_root_id: str) -> CodeChangeRunRootV1 | None:
        ...

    def save_patch_artifact(self, patch: CodeChangePatchArtifactV1) -> None:
        ...

    def get_patch_artifact(self, patch_id: str) -> CodeChangePatchArtifactV1 | None:
        ...

    def save_gate_receipt(self, receipt: GateReceiptV1) -> None:
        ...

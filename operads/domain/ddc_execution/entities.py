#!/usr/bin/env python3
"""Domain Entities for the operad Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

from omega_engine_operads.domain.ddc_execution.enums import MorphismExecutionStatus
from omega_engine_operads.domain.ddc_execution.errors import ArityMismatchError
from omega_engine_operads.domain.ddc_execution.value_objects import (
    ArtifactOutput,
    ExecutionRunRecord,
    OperadOperation,
)


class OperadMorphism:
    """Entity representing the runtime invocation lifecycle of an operad morphism."""

    def __init__(self, operation: OperadOperation) -> None:
        self.operation = operation
        self.status = MorphismExecutionStatus.SUCCESS
        self.last_run_record: Optional[ExecutionRunRecord] = None

    def validate_inputs(self, inputs: Sequence[str]) -> None:
        """Verify inputs against operation arity."""
        if len(inputs) != self.operation.arity:
            raise ArityMismatchError(
                self.operation.skill_id,
                self.operation.arity,
                len(inputs),
            )

    def complete_run(
        self,
        inputs: Sequence[str],
        output_path: str,
        output_sha256: str,
        residual_before: float,
        residual_after: float,
        findings_count: int,
        *,
        timestamp: str,
    ) -> ExecutionRunRecord:
        """Finalize run measurements and build an immutable record."""
        if not all(
            type(value) in (int, float) and math.isfinite(value) and value >= 0
            for value in (residual_before, residual_after)
        ):
            raise ValueError("residual measurements must be finite and nonnegative")
        if type(findings_count) is not int or findings_count < 0:
            raise ValueError("findings_count must be a nonnegative integer")
        delta = residual_after - residual_before
        is_contractive = residual_after < residual_before and findings_count == 0

        record = ExecutionRunRecord(
            timestamp=timestamp,
            skill_name=self.operation.skill_id,
            source_colours=self.operation.signature.source_colours,
            target_colour=self.operation.signature.target_colour,
            inputs=tuple(inputs),
            output=ArtifactOutput(path=output_path, sha256=output_sha256),
            residual_before=residual_before,
            residual_after=residual_after,
            residual_delta=delta,
            contractive=is_contractive,
            findings_count=findings_count,
        )
        self.last_run_record = record
        self.status = (
            MorphismExecutionStatus.CONTRACTIVE_PASS
            if is_contractive
            else MorphismExecutionStatus.NEUTRAL_PASS
        )
        return record

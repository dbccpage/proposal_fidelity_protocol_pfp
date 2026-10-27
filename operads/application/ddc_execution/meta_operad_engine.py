"""Validate and execute declared morphisms through explicitly bound ports."""

from collections.abc import Callable, Sequence

from operads.domain.ddc_execution.entities import OperadMorphism
from operads.domain.ddc_execution.errors import (
    OperadDomainError,
    PermissionDeniedError,
    Refusal,
)
from operads.domain.ddc_execution.execution import (
    ExecutionOutcome,
    ExecutionPlan,
)
from operads.domain.ddc_execution.protocols import (
    ArtifactCustodyPort,
    MorphismEvaluatorPort,
    OperadRegistryPort,
    TraceStoragePort,
)
from operads.domain.ddc_execution.value_objects import OperadOperation
from operads.domain.operad.errors import Err, Ok, Result


class MetaOperadEngineUseCase:
    def __init__(
        self,
        *,
        registry: OperadRegistryPort,
        traces: TraceStoragePort,
        evaluator: MorphismEvaluatorPort,
        artifacts: ArtifactCustodyPort,
        clock: Callable[[], str],
    ) -> None:
        self.registry = registry
        self.traces = traces
        self.evaluator = evaluator
        self.artifacts = artifacts
        self.clock = clock

    def resolve_operation(self, skill_id: str) -> OperadOperation:
        return self.registry.resolve_operation(skill_id)

    def check_agent_license(self, agent_id: str | None, skill_id: str) -> None:
        self.registry.check_agent_license(agent_id, skill_id)

    def execute_morphism(
        self,
        skill_id: str,
        inputs: Sequence[str],
        agent_id: str | None = None,
        output_hint: str | None = None,
        dry_run: bool = False,
    ) -> Result[ExecutionOutcome | ExecutionPlan, OperadDomainError]:
        try:
            operation = self.resolve_operation(skill_id)
            self.check_agent_license(agent_id, operation.skill_id)
            morphism = OperadMorphism(operation)
            if dry_run:
                if inputs:
                    morphism.validate_inputs(inputs)
                return Ok(ExecutionPlan(operation, tuple(inputs), agent_id, output_hint))
            if not self.evaluator.is_bound(operation.skill_id):
                return Err(
                    Refusal(
                        "NOT_EXECUTABLE",
                        f"Declared operation {operation.skill_id!r} has no bound evaluator",
                    )
                )
            if not agent_id:
                return Err(
                    PermissionDeniedError("", "Execution requires an explicit licensed agent")
                )
            morphism.validate_inputs(inputs)
            # A missing/damaged ledger must refuse before any evaluator effect.
            existing = self.traces.load_trace(operation.skill_id)
            signature = (
                f"({', '.join(operation.signature.source_colours)}) -> "
                f"{operation.signature.target_colour}"
            )
            if existing.signature != signature:
                return Err(
                    Refusal(
                        "TRACE_LEDGER_ERROR", "Trace signature differs from the declared operation"
                    )
                )
            result = self.evaluator.evaluate(operation.skill_id, inputs, output_hint)
            if isinstance(result, Err):
                return result
            observed = result.value
            if observed.findings_count != 0:
                return Err(
                    Refusal(
                        "MORPHISM_EVALUATION_REFUSED",
                        f"Evaluator reported {observed.findings_count} findings",
                    )
                )
            self.artifacts.verify(observed.output_path, observed.output_sha256)
            record = morphism.complete_run(
                inputs,
                observed.output_path,
                observed.output_sha256,
                observed.residual_before,
                observed.residual_after,
                observed.findings_count,
                timestamp=self.clock(),
            )
            signature = f"({', '.join(record.source_colours)}) -> {record.target_colour}"
            trace = self.traces.append_run(operation.skill_id, record, signature)
            return Ok(ExecutionOutcome(record, trace))
        except OperadDomainError as exc:
            return Err(exc)
        except (TypeError, ValueError) as exc:
            return Err(Refusal("MORPHISM_EVALUATION_INVALID", str(exc)))

"""Injected PFP turn executor for the existing planar resolver."""
from dataclasses import dataclass
import json

from omega_engine_pfp.infrastructure.task_turn import prepare_task_turn, PfpTurnRefusal
from omega_engine_operads.skill_operad.resolver.resolver import ExecutionResult


@dataclass
class PfpTurnExecutor:
    operation_id: str
    role_id: str
    role_version: str
    task_id: str
    attempt_id: str
    complete: object
    system: str = "Carry out the supplied operation. Return only the requested answer."
    answer_schema: dict | None = None
    lineage: tuple[str, ...] = ()
    prepare: object = None
    local_experiment_seed: int | None = None

    def __call__(self, *args):
        context = dict(operation_id=self.operation_id, role_id=self.role_id,
            role_version=self.role_version, lineage=list(self.lineage))
        if self.local_experiment_seed is not None:
            context.update(local_experiment_seed=self.local_experiment_seed,provider_seed='UNSUPPORTED')
        turn = self.prepare(args, context) if self.prepare is not None else prepare_task_turn(system=self.system,
            user=json.dumps(args, ensure_ascii=False, default=str), task_id=self.task_id,
            attempt_id=self.attempt_id, answer_schema=self.answer_schema,
            context=context, checker_id="operad-pfp-shape-v1")
        result = self.complete(turn)
        checked = result.get("checked")
        if not checked or checked.get('binding') != turn.binding:
            raise PfpTurnRefusal(dict(failure_class='OPERATION_BINDING_MISMATCH'))
        response=(result.get('outcome') or {}).get('response') or {}
        checked=(turn.check_completion(response['text']) if type(response.get('text')) is str
            else turn.replay(checked))
        if not checked or not checked.get("schema_valid") or checked.get("failure_class") != "NONE":
            raise PfpTurnRefusal(checked or dict(failure_class="UNAVAILABLE"))
        generation_id=response.get('id') or result.get('generation_id')
        return ExecutionResult(checked["answer"], model=result.get("model"),
            usage=result.get("usage"), cost_micro_usd=result.get("cost_microusd"),
            verdict=checked["evidence_grade"], context={**context, **turn.binding,
                "cost_basis": result.get("cost_basis", "UNKNOWN"),"generation_id":generation_id})

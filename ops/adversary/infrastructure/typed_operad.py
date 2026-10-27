"""Checked mission operations over the existing OEWAS execution and PFP ports."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel

from pfp.domain.entities.candidate_artifact import CandidateArtifactV1
from pfp.domain.pfp_ingress import strict_json
from pfp.domain.prompts.prompts import PromptPacket
from pfp.infrastructure.task_turn import prepare_task_turn
from pfp.use_cases.pfp_proposal import task_turn_validator
from adversary.infrastructure import operad_contracts as values
from adversary.domain.contracts import session_rewrite as session_values
from operads.application.commands.compile_catalog import (
    operation_content_digest,
)
from operads.contracts.typed_capabilities_v1 import canonical_bytes
from operads.domain.entities.operation_v3 import (
    OperationV3,
    PortSpecV3,
)
from operads.domain.value_objects.content_digest import ContentDigest
from operads.domain.value_objects.identifier import (
    ColourId,
    OperationId,
    SchemaRef,
)
from operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from operads.skill_operad.resolver.native_runtime import run_native
from operads.skill_operad.resolver.resolver import (
    ExecutionResult,
    Refusal,
    RunReceipt,
    digest,
)
from operads.skill_operad.skill_compiler.op_inventory import (
    HostBinding,
    OpInventory,
    OpSpec,
    SkillDecomposition,
    Wire,
)

_OPERATIONS = {
    "adversary.syntax_prefilter.sanitize.v1": ((values.RawPacket,), values.SanitizedPacket, "_syntax_prefilter"),
    "adversary.gauge_breaker.propose.v1": ((values.Contract, values.Context), values.CandidateProposal, "_gauge_breaker"),
    "adversary.defect_hunter.audit.v1": ((values.CandidateProposal, values.GroundTruth), values.FlawAudit, "_defect_hunter"),
    "adversary.primal_dual.verify-duality.v1": ((values.PrimalResidual, values.DualMultiplier), values.DualityReceipt, "_primal_dual"),
    session_values.HINT_OPERATION_ID: ((session_values.SessionHintRequest,),
        session_values.SessionHintResult, "insert_checked_session_hint"),
}
_COLOURS = {values.RawPacket: "State", values.SanitizedPacket: "State",
    values.Contract: "Contract", values.Context: "State", values.CandidateProposal: "State",
    values.GroundTruth: "State", values.FlawAudit: "Audit", values.PrimalResidual: "State",
    values.DualMultiplier: "State", values.DualityReceipt: "Receipt",
    values.RawSpan: "State", values.GateWitness: "Receipt",
    values.CochainDefect: "State", values.TerminalStatus: "State",
    session_values.SessionHintRequest: "Contract", session_values.SessionHintResult: "Receipt"}

_WIRE_COLOURS = {model.__name__: model for model in (
    values.RawSpan, values.GateWitness, values.CochainDefect, values.TerminalStatus)}

# Existing OperationV3 allowlists accept lowercase file-and-method references.
# These identify host capabilities, not automatic imports or admission grants:
# PfpLlmProviderPort, CandidateCheckerPort and RustSymbolGameHost respectively.
_HOST_METHODS = {
    "adversary.gauge_breaker.propose.v1": "python:pfp/domain/kernel/ports.py:generate_candidate",
    "adversary.defect_hunter.audit.v1": "python:adversary/domain/ports.py:check_candidate",
    "adversary.primal_dual.verify-duality.v1": "python:pfp/ffi.py:verify_l1_certificate",
    session_values.HINT_OPERATION_ID: "python:adversary/use_cases/checked_ddc_reuse.py:recheck_original_session",
}


def _digest(raw: bytes) -> ContentDigest:
    return ContentDigest.sha256(sha256(raw).hexdigest())


def _port(model, index: int) -> PortSpecV3:
    owner = session_values if model in (session_values.SessionHintRequest, session_values.SessionHintResult) else values
    return PortSpecV3(f"slot{index}", ColourId(_COLOURS[model]),
        SchemaRef("schema:core:adversary:" + model.__name__ + ":v1"),
        _digest(canonical_bytes(model.model_json_schema())),
        owner.__name__ + "::" + model.__name__,
        _digest(Path(owner.__file__).read_bytes()))


def wire_colour_ports() -> dict[str, PortSpecV3]:
    """Refined wire interpretations; the ten historical coarse colours stay fixed."""
    return {name: _port(model, 0) for name, model in _WIRE_COLOURS.items()}


def validate_wire_colour(name: str, value):
    """Run the exact validator named by the schema-bound refinement port."""
    return _snapshot(_WIRE_COLOURS[name], value)


def operation_declarations() -> tuple[OperationV3, ...]:
    """Host effect declarations, still Unchecked/Unadmitted in the existing estate.

    Normal typed compilation requires explicit effect/tool allowlists. This does
    not widen the separate guidance-only CapabilityWireV1 effect vocabulary.
    """
    executor_digest = _digest(Path(__file__).read_bytes())
    declarations = []
    for operation_id, (inputs, output, _) in _OPERATIONS.items():
        ports = tuple(_port(model, index) for index, model in enumerate(inputs))
        target = _port(output, 0)
        lifecycle = SkillLifecycleV3(DeclarationFacet.DECLARED, SchemaBindingFacet.BOUND,
            ExecutorBindingFacet.BOUND, ValidationFacet.UNCHECKED, AdmissionFacet.UNADMITTED,
            target.schema_digest, executor_digest)
        host_method = _HOST_METHODS.get(operation_id)
        declarations.append(OperationV3(OperationId(operation_id), ports, target, (),
            lifecycle, "unknown", effects=() if host_method is None else ("invoke:" + host_method,),
            tool_refs=() if host_method is None else (host_method,), invocation_grade="discipline"))
    return tuple(declarations)


def _token(port: PortSpecV3) -> str:
    contract = [str(port.colour_id), str(port.schema_ref), str(port.schema_digest),
        port.validator_ref, str(port.validator_digest)]
    return str(port.colour_id) + "." + values.value_digest(contract)


def _snapshot(model, value):
    raw = value.model_dump(mode="python") if isinstance(value, BaseModel) else value
    return model.model_validate_json(canonical_bytes(raw))


class TypedAdversaryOperad:
    """Opt-in host-selected operations, not replacements for the full22 State route.

    Native plan checking precedes external effects. The caller persists the
    returned receipt and any ``last_pfp_record`` captured on a failed proposal;
    captured bytes do not establish transport authentication or measured cost.
    """

    def __init__(self, *, native_host=None, provider=None, candidate_checker=None,
                 ground_truth: values.GroundTruth | None = None, exact_host=None,
                 occurrence_checker=None, session_hint_checker=None):
        self.native_host = native_host
        self.provider, self.candidate_checker, self.exact_host = provider, candidate_checker, exact_host
        self.occurrence_checker = occurrence_checker
        self.session_hint_checker = session_hint_checker
        self._ground_truth = None if ground_truth is None else _snapshot(values.GroundTruth, ground_truth)
        self.last_pfp_record: dict | None = None
        self.last_refusal: Refusal | None = None

    def execute(self, operation_id: str, inputs) -> RunReceipt:
        self.last_pfp_record = None
        self.last_refusal = None
        if operation_id not in _OPERATIONS:
            return RunReceipt(None, (), refusal=Refusal("NOT_EXECUTABLE", operation_id))
        models, output_model, method = _OPERATIONS[operation_id]
        declaration = next(op for op in operation_declarations() if str(op.operation_id) == operation_id)
        ports = tuple(_token(port) for port in declaration.inputs)
        output = _token(declaration.output)
        wire = Wire(op=operation_id, args=ports)
        try:
            if type(inputs) not in (list, tuple) or len(inputs) != len(models):
                raise ValueError("ORDERED_OPERANDS_REQUIRED")
            operands = [_snapshot(model, value) for model, value in zip(models, inputs, strict=True)]
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            return RunReceipt(wire, (), refusal=Refusal("OPERAND_INVALID", str(exc)))
        operation_digest = str(operation_content_digest(declaration))
        spec = OpSpec(op_id=operation_id, inputs=ports, output=output,
            summary="Concrete mission operation " + operation_digest,
            binding=HostBinding(target="adversary/infrastructure/typed_operad.py::TypedAdversaryOperad." + method))
        subcolours = {}
        for token in (*ports, output):
            colour, _, subtype = token.partition(".")
            subcolours[colour] = tuple(sorted(set((*subcolours.get(colour, ()), subtype))))
        inventory = OpInventory(schema_version="core.oewas.op_inventory.v3", subcolours=subcolours,
            skills=(SkillDecomposition(skill_id="adversary", ops=(spec,), wiring=wire),))

        def execute_checked(*arguments):
            try:
                checked = [_snapshot(model, arg) for model, arg in zip(models, arguments, strict=True)]
                result = _snapshot(output_model, getattr(self, method)(*checked))
                return ExecutionResult(result.model_dump(mode="json"), context={
                    "operation_declaration_digest": operation_digest,
                    "executor_digest": str(declaration.lifecycle.executor_digest),
                    "authority_effect": "None"})
            except Exception as exc:
                # The existing native executor converts thrown failures to its
                # EXECUTOR_FAILED rail. Retain concrete diagnostics separately.
                self.last_refusal = Refusal("MISSION_OPERATION_REFUSED", str(exc))
                raise

        supplied = [arg.model_dump(mode="json") for arg in operands]
        try:
            receipt = run_native(inventory, wire, supplied,
                {operation_id: execute_checked}, {}, host=self.native_host,
                occurrence_checker=self.occurrence_checker)
        except Exception as exc:
            return RunReceipt(wire, (), refusal=Refusal("NATIVE_OPERAD_UNAVAILABLE", str(exc)),
                input_digest=digest(supplied), inventory_digest=digest(inventory.model_dump(mode="json")),
                interpreter_version="core.oewas.native-plan-host.v1")
        if receipt.refusal and self.last_refusal:
            receipt = replace(receipt, refusal=Refusal(receipt.refusal.code,
                operation_id + ": " + self.last_refusal.message))
        return receipt

    def insert_checked_session_hint(self, request: session_values.SessionHintRequest) -> session_values.SessionHintResult:
        """Host-only executor, reusable in an existing native operation composition.

        The callback is selected by the operator, never decoded from a request.
        An admitted workflow caller supplies its existing ledgered recheck port.
        This method does not start another run or change a prepared prompt.
        """
        from .session_acset import decode_session, insert_checked_session_hint

        if not callable(self.session_hint_checker):
            raise ValueError("SESSION_HINT_CHECKER_UNAVAILABLE")
        request = _snapshot(session_values.SessionHintRequest, request)
        before = request.wire_digest()
        checked = insert_checked_session_hint(source=request.source, task=request.task,
            checker=request.checker, check=self.session_hint_checker, fuel=request.fuel)
        decoded = decode_session(checked.rewrite.session)
        if request.wire_digest() != before or sha256(decoded.source_wire).hexdigest() != request.source.sha256:
            raise ValueError("SESSION_HINT_REQUEST_CHANGED")
        graph, occurrence = checked.rewrite.session.graph, checked.occurrences
        return session_values.SessionHintResult(request=request, request_sha256=before,
            source=request.source, source_bytes=len(decoded.source_wire),
            source_documents=len(checked.rewrite.session.documents),
            before_graph_sha256=checked.rewrite.execution.before_digest,
            after_graph_sha256=checked.rewrite.execution.after_digest,
            parts_before=len(occurrence.host_part_ids), parts_after=len(graph.parts),
            links_before=len(occurrence.host_link_ids), links_after=len(graph.links),
            hint_part_id=occurrence.hint_part_id, context_link_id=occurrence.context_link_id,
            guidance=decoded.guidance, protected_source_unchanged=True,
            boundary_decision=checked.boundary_evaluation.decision,
            authorized=checked.boundary_evaluation.authorized,
            original_task_check=checked.original_task_check)

    @staticmethod
    def _syntax_prefilter(source: values.RawPacket) -> values.SanitizedPacket:
        payload = strict_json(source.raw_bytes().decode("utf-8"))
        if type(payload) is not dict:
            raise ValueError("PACKET_OBJECT_REQUIRED")
        if not task_turn_validator(source.payload_schema).is_valid(payload):
            raise ValueError("PACKET_SCHEMA_MISMATCH")
        return values.SanitizedPacket(source=source, payload=payload,
            payload_sha256=values.value_digest(payload))

    @staticmethod
    def _prepare(contract: values.Contract, context: values.Context):
        if contract.task_id != context.task_id:
            raise ValueError("CONTRACT_CONTEXT_TASK_MISMATCH")
        # Validate caller-declared schema before transport, including reference
        # restrictions, through the existing PFP schema boundary.
        task_turn_validator(contract.answer_schema)
        system = json.dumps({"task": contract.objective, "constraints": contract.constraints,
            "acceptance_criteria": contract.acceptance}, ensure_ascii=False)
        return prepare_task_turn(system=system,
            user=json.dumps(context.public_data, ensure_ascii=False), task_id=contract.task_id,
            attempt_id=context.attempt_id, answer_schema=contract.answer_schema,
            context={"contract_sha256": values.value_digest(contract.model_dump(mode="json"))},
            checker_id="adversary.gauge_breaker.proposal.v1")

    def _gauge_breaker(self, contract: values.Contract, context: values.Context) -> values.CandidateProposal:
        prepared = self._prepare(contract, context)
        if self.provider is None:
            raise ValueError("PROPOSER_PORT_UNAVAILABLE")
        prompt = prepared.prompt
        packet = PromptPacket(demo_id=contract.task_id, stage=2, system=prompt.system,
            user=prompt.user, response_schema=prompt.response_schema,
            system_sha256=sha256(prompt.system.encode()).hexdigest(),
            user_sha256=sha256(prompt.user.encode()).hexdigest(),
            schema_sha256=values.value_digest(prompt.response_schema))
        checked = strict_json(canonical_bytes(prepared.check_completion(
            self.provider.generate_candidate(packet))).decode("utf-8"))
        self.last_pfp_record = checked
        if checked.get("schema_valid") is not True:
            raise ValueError("PFP_" + checked.get("failure_class", "INVALID_REPLY"))
        artifact = CandidateArtifactV1(packet_id=values.value_digest(contract.model_dump(mode="json")),
            producer_id="gauge_breaker", payload=checked["answer"],
            witness="pfp-raw-sha256:" + checked["raw_reply_sha256"],
            metadata={"task_id": contract.task_id, "attempt_id": context.attempt_id})
        return values.CandidateProposal(contract=contract, context=context,
            artifact=artifact.to_dict(), pfp_record=checked)

    def _defect_hunter(self, candidate: values.CandidateProposal, truth: values.GroundTruth) -> values.FlawAudit:
        if self.candidate_checker is None or self._ground_truth is None:
            raise ValueError("GROUND_TRUTH_PORT_UNAVAILABLE")
        if truth != self._ground_truth or truth.task_id != candidate.contract.task_id:
            raise ValueError("GROUND_TRUTH_HOST_BINDING_MISMATCH")
        replay = self._prepare(candidate.contract, candidate.context).replay(candidate.pfp_record)
        if replay.get("schema_valid") is not True or canonical_bytes(replay.get("answer")) != candidate.payload_bytes():
            raise ValueError("CANDIDATE_REPLAY_REFUSED")
        response = self.candidate_checker.check_candidate(run_key=truth.task_id,
            objective=candidate.contract.objective, candidate_id=candidate.candidate().candidate_id,
            candidate_bytes=candidate.payload_bytes(),
            carrier_context={"reference_sha256": truth.reference_sha256})
        if response.is_err:
            raise ValueError("CHECKER_UNAVAILABLE: " + str(response.unwrap_err()))
        checked = response.unwrap()
        from adversary.domain.evidence import CandidateCheckV1
        if type(checked) is not CandidateCheckV1:
            raise ValueError("CHECKER_RESULT_TYPE")
        # FlawAudit revalidates candidate identity, exact bytes, checker identity,
        # receipt hash and the verdict stated inside those receipt bytes.
        return values.FlawAudit(candidate=candidate, ground_truth=truth, check=checked.to_dict())

    def _primal_dual(self, primal: values.PrimalResidual, dual: values.DualMultiplier) -> values.DualityReceipt:
        if (dual.primal_sha256 != values.value_digest(primal.model_dump(mode="json"))
            or len(dual.values) != len(primal.omega)):
            raise ValueError("DUAL_PROBLEM_BINDING_MISMATCH")
        if self.exact_host is None:
            raise ValueError("EXACT_VERIFIER_UNAVAILABLE")
        response = self.exact_host.verify_l1_certificate(primal.d0, primal.omega, primal.alpha, dual.values)
        if response.is_err:
            raise ValueError("EXACT_VERIFIER_UNAVAILABLE: " + str(response.unwrap_err()))
        return values.DualityReceipt(primal=primal, dual=dual, value=primal.value,
            native_result=dict(response.unwrap()))

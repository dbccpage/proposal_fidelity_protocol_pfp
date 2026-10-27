"""Prompt Hierarchy Gate Evaluator.

Evaluates prompt payloads against OEWAS procedural Anti-Ops and OEEIS empirical Antibodies
(gated by the Two-Signal Danger Gate).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from operads.domain.operad import (
    ColourSignature,
    ColouredOperad,
    OperationId,
    OperationSignature,
)

from .models import (
    DerivationMapOperadReport,
    OperadPromptBinding,
    PromptGateReceipt,
    PromptTreeNode,
)

# Default built-in detectors for standard PFP and claim hygiene anti-ops
DEFAULT_KEYWORD_PATTERNS: dict[str, Sequence[str]] = {
    "pfp.refuse_unlicensed_multiplication": ("multiplication", "multiply", "tensor_product"),
    "pfp.refuse_unlicensed_causality": ("causality", "causal_order", "arrow_of_time"),
    "pfp.refuse_unmapped_continuum_import": (
        "continuous physics",
        "lie algebra",
        "smooth manifold",
        "differential form",
    ),
    "pfp.refuse_scalar_proxy_theorem_substitution": (
        "three_ray_positivity_proxy",
        "parameter_count_equality_proxy",
        "single_nc_point_sample",
        "one_skeleton_euler_proxy",
    ),
    "pfp.refuse_target_fitting_constant_compensation": (
        "unpinned_additive_residual",
        "composite_sum_interval_only",
        "compensating_two_loop_offset",
    ),
    "pfp.refuse_witness_certificate_desynchronization": (
        "unverified_prose_witness_literal",
        "prose_certificate_witness_mismatch",
        "missing_inverse_tree_dressing",
    ),
    "glossa.refuse_missing_claim_envelope": (
        # Checked via structural absence if enforced
    ),
}


def _evaluate_operad_dof_locks(
    binding: OperadPromptBinding,
    payload: Mapping[str, Any],
) -> tuple[int, str | None, str | None]:
    """Verify operad slot bindings and compute residual degrees of freedom.

    Returns (residual_degrees_of_freedom, refusal_code, refusal_message).
    When all declared slots, sub-channel pins, cross-layer witness groups, and
    boundary falsifiers are satisfied, residual_degrees_of_freedom == 0.
    """
    residual_dof = binding.locked_constraint_count

    # 1. Verify slot_to_colour arity and presence
    if binding.slot_to_colour:
        declared_colours = tuple(binding.slot_to_colour.values())
        if declared_colours != binding.source_colours:
            return (
                residual_dof,
                "OPERAD_ARITY_OR_COLOUR_MISMATCH",
                f"slot_to_colour {declared_colours} does not match source_colours {binding.source_colours}",
            )
        for slot_name in binding.slot_to_colour:
            if slot_name not in payload or payload[slot_name] is None:
                return (
                    residual_dof,
                    "OPERAD_MISSING_SOURCE_SLOT",
                    f"Missing required operad source slot {slot_name!r} for {binding.operation_id}",
                )
            residual_dof -= 1
    else:
        residual_dof -= len(binding.source_colours)

    # 2. Verify independent sub-channel pins (eliminates target-fitting constant compensation)
    pins_map = payload.get("slot_pins")
    if binding.required_slot_pins:
        if not isinstance(pins_map, Mapping):
            return (
                residual_dof,
                "DOF_UNPINNED_SUBCHANNEL_COMPENSATION",
                f"Operad {binding.operation_id} requires independent slot_pins for {binding.required_slot_pins}",
            )
        free_params = payload.get("free_parameter_count", 0)
        if type(free_params) is not int or free_params != 0:
            return (
                residual_dof,
                "DOF_NONZERO_FREE_PARAMETERS",
                f"Operad {binding.operation_id} requires free_parameter_count == 0, got {free_params!r}",
            )
        for pin_slot in binding.required_slot_pins:
            if pin_slot not in payload or pin_slot not in pins_map:
                return (
                    residual_dof,
                    "DOF_UNPINNED_SUBCHANNEL_COMPENSATION",
                    f"Sub-channel {pin_slot!r} is missing from payload or independent slot_pins",
                )
            if type(payload[pin_slot]) is not type(pins_map[pin_slot]) or payload[pin_slot] != pins_map[pin_slot]:
                return (
                    residual_dof,
                    "DOF_UNPINNED_SUBCHANNEL_COMPENSATION",
                    f"Sub-channel {pin_slot!r} value {payload[pin_slot]!r} mismatches pinned value {pins_map[pin_slot]!r}",
                )
            residual_dof -= 1

    # 3. Verify cross-slot witness equality across Paper, Code, and Proof
    for group in binding.cross_slot_equality_groups:
        if len(group) < 2:
            return (
                residual_dof,
                "DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION",
                f"Cross-slot equality group {group!r} must contain at least 2 slots",
            )
        for slot_name in group:
            if slot_name not in payload:
                return (
                    residual_dof,
                    "DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION",
                    f"Missing witness slot {slot_name!r} in cross-layer equality group {group!r}",
                )
        first_val = payload[group[0]]
        for other_slot in group[1:]:
            other_val = payload[other_slot]
            if type(first_val) is not type(other_val) or first_val != other_val:
                return (
                    residual_dof,
                    "DOF_WITNESS_CERTIFICATE_DESYNCHRONIZATION",
                    f"Witness mismatch between {group[0]!r} ({first_val!r}) and {other_slot!r} ({other_val!r})",
                )
        residual_dof -= 1

    # 4. Verify boundary/counterexample falsifier witnesses (eliminates scalar-proxy substitution)
    for boundary_slot in binding.required_boundary_witness_slots:
        witness_val = payload.get(boundary_slot)
        if witness_val is None or witness_val is False or witness_val == "" or witness_val == ():
            return (
                residual_dof,
                "DOF_SCALAR_PROXY_SUBSTITUTION",
                f"Missing or vacuous boundary falsifier witness in slot {boundary_slot!r} for {binding.operation_id}",
            )
        residual_dof -= 1

    return (max(0, residual_dof), None, None)


def evaluate_prompt_gates(
    node: PromptTreeNode,
    payload: Mapping[str, Any],
    *,
    admitted_antibody_ids: Sequence[str] = (),
    host_danger_signals: Sequence[str] = (),
    custom_detectors: Mapping[str, Callable[[Any], bool]] | None = None,
) -> PromptGateReceipt:
    """Evaluate a candidate prompt execution payload against a PromptTreeNode's bound gates.

    1. Procedural Anti-Ops: Checked on the designated input slot.
    2. Empirical Antibodies: Checked only if ADMITTED, requiring both Signal 1 (Epitope match)
       and Signal 2 (Independent Host Danger Signal).
    3. Operad Degree-of-Freedom Locks: When `node.operad_binding` is attached, enforces
       source slot arity, independent sub-channel pins, cross-layer witness equality, and
       boundary counterexample witnesses so residual degrees of freedom drop to zero.
    """
    detectors = dict(custom_detectors or {})
    anti_ops_eval: list[str] = []
    anti_ops_fired: list[str] = []
    unavailable: list[str] = []
    op_id_str = node.operad_binding.operation_id if node.operad_binding is not None else None

    # 1. Evaluate OEWAS Anti-Ops
    for anti_op in node.anti_ops:
        anti_ops_eval.append(anti_op.op_id)
        slot_value = payload.get(anti_op.inspects_slot)
        if anti_op.inspects_slot not in payload:
            unavailable.append(f"{anti_op.op_id}: missing slot {anti_op.inspects_slot}")
            continue

        # A: Custom detector registered
        if anti_op.op_id in detectors:
            if detectors[anti_op.op_id](slot_value):
                anti_ops_fired.append(anti_op.op_id)
                return PromptGateReceipt(
                    prompt_uri=node.uri.raw_uri,
                    status="REFUSED",
                    anti_ops_evaluated=tuple(anti_ops_eval),
                    anti_ops_fired=tuple(anti_ops_fired),
                    operad_operation_id=op_id_str,
                    refusal_code=anti_op.refusal_code,
                    refusal_message=f"Anti-op {anti_op.op_id} fired on slot {anti_op.inspects_slot}: {anti_op.description}",
                )
            continue

        # B: Built-in keyword anti-op checking on string slots
        if isinstance(slot_value, str) and DEFAULT_KEYWORD_PATTERNS.get(anti_op.op_id):
            lower_text = slot_value.lower()
            for kw in DEFAULT_KEYWORD_PATTERNS[anti_op.op_id]:
                if kw in lower_text:
                    anti_ops_fired.append(anti_op.op_id)
                    return PromptGateReceipt(
                        prompt_uri=node.uri.raw_uri,
                        status="REFUSED",
                        anti_ops_evaluated=tuple(anti_ops_eval),
                        anti_ops_fired=tuple(anti_ops_fired),
                        operad_operation_id=op_id_str,
                        refusal_code=anti_op.refusal_code,
                        refusal_message=f"Forbidden keyword {kw!r} detected by {anti_op.op_id} in {anti_op.inspects_slot}",
                    )
        else:
            unavailable.append(f"{anti_op.op_id}: no executable detector for slot type")

    if unavailable:
        return PromptGateReceipt(
            prompt_uri=node.uri.raw_uri,
            status="REFUSED",
            anti_ops_evaluated=tuple(anti_ops_eval),
            operad_operation_id=op_id_str,
            refusal_code="NOT_EXECUTABLE",
            refusal_message="; ".join(unavailable),
        )

    # 2. Evaluate OEEIS Antibodies
    antibodies_eval: list[str] = []
    antibodies_fired: list[str] = []

    admitted_set = set(admitted_antibody_ids)

    for binding in node.antibodies:
        antibodies_eval.append(binding.antibody_id)

        # Unadmitted antibodies remain inert by design
        if binding.antibody_id not in admitted_set:
            continue

        # Signal 1: Epitope match in payload text or data
        epitope = binding.signal1_epitope.lower()
        signal1_matched = False
        for val in payload.values():
            if isinstance(val, str) and epitope and epitope in val.lower():
                signal1_matched = True
                break

        # Signal 2: Independent Host Danger Signal
        required_danger = binding.signal2_required_danger
        signal2_present = (
            bool(required_danger) and required_danger in host_danger_signals
            or "HOST_EVALUATOR_ALERT" in host_danger_signals
        )

        # Two-Signal Danger Gate: Both must be observed
        if signal1_matched and signal2_present:
            antibodies_fired.append(binding.antibody_id)
            return PromptGateReceipt(
                prompt_uri=node.uri.raw_uri,
                status="REFUSED",
                anti_ops_evaluated=tuple(anti_ops_eval),
                anti_ops_fired=tuple(anti_ops_fired),
                antibodies_evaluated=tuple(antibodies_eval),
                antibodies_fired=tuple(antibodies_fired),
                operad_operation_id=op_id_str,
                refusal_code=f"ANTIBODY_ACTIVATION:{binding.antibody_id}",
                refusal_message=f"Two-Signal Danger Gate tripped by admitted antibody {binding.antibody_id}: epitope '{binding.signal1_epitope}' + host danger '{binding.signal2_required_danger}'",
            )

    # 3. Evaluate Operad Degree-of-Freedom Locks if bound
    residual_dof = 0
    if node.operad_binding is not None:
        residual_dof, dof_code, dof_msg = _evaluate_operad_dof_locks(node.operad_binding, payload)
        if dof_code is not None:
            return PromptGateReceipt(
                prompt_uri=node.uri.raw_uri,
                status="REFUSED",
                anti_ops_evaluated=tuple(anti_ops_eval),
                anti_ops_fired=tuple(anti_ops_fired),
                antibodies_evaluated=tuple(antibodies_eval),
                antibodies_fired=tuple(antibodies_fired),
                operad_operation_id=op_id_str,
                residual_degrees_of_freedom=residual_dof,
                refusal_code=dof_code,
                refusal_message=dof_msg,
            )

    return PromptGateReceipt(
        prompt_uri=node.uri.raw_uri,
        status="PASS",
        anti_ops_evaluated=tuple(anti_ops_eval),
        anti_ops_fired=(),
        antibodies_evaluated=tuple(antibodies_eval),
        antibodies_fired=(),
        operad_operation_id=op_id_str,
        residual_degrees_of_freedom=residual_dof,
    )


def collect_derivation_map_operads(
    nodes: Sequence[PromptTreeNode],
    payloads_by_uri: Mapping[str, Mapping[str, Any]],
    *,
    admitted_antibody_ids: Sequence[str] = (),
    host_danger_signals: Sequence[str] = (),
    custom_detectors: Mapping[str, Callable[[Any], bool]] | None = None,
) -> DerivationMapOperadReport:
    """Collect every prompt's operad operation and bound antibodies across a derivation map.

    1. Verifies every prompt node in `nodes` declares a non-null `operad_binding`.
    2. Registers each operation into a `ColouredOperad` and sequentially composes
       stage operations where the output colour of stage k matches a source slot of stage k+1.
    3. Evaluates every prompt's anti-ops, antibodies, and degree-of-freedom locks against
       its payload in `payloads_by_uri`, ensuring zero residual degrees of freedom across
       the entire derivation chain.
    """
    if not nodes:
        return DerivationMapOperadReport(
            prompt_uris=(),
            operation_ids=(),
            composite_signature="",
            total_locked_constraints=0,
            residual_degrees_of_freedom=0,
            collected_antibody_ids=(),
            collected_anti_op_ids=(),
            status="REFUSED",
            refusal_code="EMPTY_DERIVATION_MAP",
            refusal_message="Derivation map must contain at least one prompt node",
        )

    operad = ColouredOperad()
    operad.ensure_units()

    prompt_uris: list[str] = []
    operation_ids: list[str] = []
    collected_antibodies: list[str] = []
    collected_anti_ops: list[str] = []
    total_locked = 0
    total_residual_dof = 0
    signatures: list[OperationSignature] = []

    for node in nodes:
        prompt_uris.append(node.uri.raw_uri)
        for op in node.anti_ops:
            if op.op_id not in collected_anti_ops:
                collected_anti_ops.append(op.op_id)
        for ab in node.antibodies:
            if ab.antibody_id not in collected_antibodies:
                collected_antibodies.append(ab.antibody_id)

        if node.operad_binding is None:
            return DerivationMapOperadReport(
                prompt_uris=tuple(prompt_uris),
                operation_ids=tuple(operation_ids),
                composite_signature="",
                total_locked_constraints=total_locked,
                residual_degrees_of_freedom=1,
                collected_antibody_ids=tuple(collected_antibodies),
                collected_anti_op_ids=tuple(collected_anti_ops),
                status="REFUSED",
                refusal_code="MISSING_PROMPT_OPERAD_BINDING",
                refusal_message=f"Prompt {node.uri.raw_uri} has no bound operad signature",
            )

        ob = node.operad_binding
        op_sig = OperationSignature(
            op_id=OperationId(ob.operation_id),
            signature=ColourSignature(source=ob.source_colours, target=ob.target_colour),
            equivariant=ob.equivariant,
            residual_effect=ob.residual_effect,
        )
        operad.add_operation(op_sig)
        signatures.append(op_sig)
        operation_ids.append(ob.operation_id)
        total_locked += ob.locked_constraint_count

        payload = payloads_by_uri.get(node.uri.raw_uri)
        if payload is None:
            return DerivationMapOperadReport(
                prompt_uris=tuple(prompt_uris),
                operation_ids=tuple(operation_ids),
                composite_signature="",
                total_locked_constraints=total_locked,
                residual_degrees_of_freedom=ob.locked_constraint_count,
                collected_antibody_ids=tuple(collected_antibodies),
                collected_anti_op_ids=tuple(collected_anti_ops),
                status="REFUSED",
                refusal_code="MISSING_PROMPT_PAYLOAD",
                refusal_message=f"Missing payload for prompt {node.uri.raw_uri}",
            )

        receipt = evaluate_prompt_gates(
            node,
            payload,
            admitted_antibody_ids=admitted_antibody_ids,
            host_danger_signals=host_danger_signals,
            custom_detectors=custom_detectors,
        )
        total_residual_dof += receipt.residual_degrees_of_freedom
        if not receipt.passed:
            return DerivationMapOperadReport(
                prompt_uris=tuple(prompt_uris),
                operation_ids=tuple(operation_ids),
                composite_signature="",
                total_locked_constraints=total_locked,
                residual_degrees_of_freedom=total_residual_dof,
                collected_antibody_ids=tuple(collected_antibodies),
                collected_anti_op_ids=tuple(collected_anti_ops),
                status="REFUSED",
                refusal_code=receipt.refusal_code,
                refusal_message=receipt.refusal_message,
            )

    # Compose the collected stage operads from first to last:
    # Stage k produces target colour C_k, which plugs into the matching source slot of Stage k+1.
    accumulated = signatures[0]
    for next_sig in signatures[1:]:
        slot_idx = next(
            (idx for idx, src_c in enumerate(next_sig.source) if src_c == accumulated.target),
            None,
        )
        if slot_idx is None:
            return DerivationMapOperadReport(
                prompt_uris=tuple(prompt_uris),
                operation_ids=tuple(operation_ids),
                composite_signature=str(accumulated.signature),
                total_locked_constraints=total_locked,
                residual_degrees_of_freedom=1,
                collected_antibody_ids=tuple(collected_antibodies),
                collected_anti_op_ids=tuple(collected_anti_ops),
                status="REFUSED",
                refusal_code="OPERAD_COMPOSITION_TYPE_MISMATCH",
                refusal_message=(
                    f"Operation {next_sig.op_id} source colours {next_sig.source_colours} "
                    f"cannot accept output colour {accumulated.target_colour!r} from {accumulated.op_id}"
                ),
            )
        comp_res = operad.partial_compose(next_sig, accumulated, slot_idx)
        if comp_res.is_err:
            return DerivationMapOperadReport(
                prompt_uris=tuple(prompt_uris),
                operation_ids=tuple(operation_ids),
                composite_signature=str(accumulated.signature),
                total_locked_constraints=total_locked,
                residual_degrees_of_freedom=1,
                collected_antibody_ids=tuple(collected_antibodies),
                collected_anti_op_ids=tuple(collected_anti_ops),
                status="REFUSED",
                refusal_code="OPERAD_COMPOSITION_ERROR",
                refusal_message=str(comp_res.error),
            )
        accumulated = comp_res.value

    return DerivationMapOperadReport(
        prompt_uris=tuple(prompt_uris),
        operation_ids=tuple(operation_ids),
        composite_signature=str(accumulated.signature),
        total_locked_constraints=total_locked,
        residual_degrees_of_freedom=total_residual_dof,
        collected_antibody_ids=tuple(collected_antibodies),
        collected_anti_op_ids=tuple(collected_anti_ops),
        status="PASS",
    )


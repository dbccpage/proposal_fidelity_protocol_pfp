"""Observable seed features, not a universal complexity or hallucination oracle."""

import json
import re
from hashlib import sha256


def measure_seed(spec, declarations=None):
    """Keep ex-ante seed features separate from model/workflow-generated material."""
    declarations = declarations or {}
    seed = spec["seed_prompt"]
    public_input = spec["input"]
    input_bytes = json.dumps(
        public_input, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode()
    seed_bytes = seed.encode("utf-8")
    family = (
        "integer_sum"
        if spec["checker"] == "integer_sum_v1"
        else declarations.get("family", "UNDECLARED")
    )
    task = dict(
        family=family,
        operand_count=None,
        operand_decimal_digits=None,
        max_operand_bits=None,
        reference_binary_additions=None,
        reference_balanced_addition_depth=None,
        declared_constraint_count=declarations.get("constraint_count"),
        declared_search_states=declarations.get("search_states"),
        external_knowledge_required=declarations.get("external_knowledge_required"),
        proof_scope=declarations.get("proof_scope", "UNDECLARED"),
    )
    if family == "integer_sum":
        values = public_input.get("values")
        if type(values) is not list or not values or any(type(v) is not int for v in values):
            raise ValueError("COMPLEXITY_INTEGER_INPUT_REQUIRED")
        task.update(
            operand_count=len(values),
            operand_decimal_digits=sum(len(str(abs(v))) for v in values),
            max_operand_bits=max(abs(v).bit_length() for v in values),
            reference_binary_additions=len(values) - 1,
            reference_balanced_addition_depth=(len(values) - 1).bit_length(),
            external_knowledge_required=False,
            proof_scope="ONE_DECLARED_FINITE_INSTANCE",
        )
    bounded = spec["checker"] == "integer_sum_v1" or declarations.get("bounded_instance", False)
    return dict(
        schema="pfp.seed-complexity.v1",
        seed_sha256=sha256(seed_bytes).hexdigest(),
        input_sha256=sha256(input_bytes).hexdigest(),
        surface=dict(
            characters=len(seed),
            utf8_bytes=len(seed_bytes),
            whitespace_words=len(seed.split()),
            digit_occurrences=len(re.findall(r"\d", seed)),
            input_json_bytes=len(input_bytes),
            model_token_count=None,
        ),
        task=task,
        verification=dict(
            checker=spec["checker"],
            task_correctness_check_available=spec["checker"] != "schema_only",
        ),
        scope=dict(
            bounded_instance=bounded,
            objective_kind=declarations.get(
                "objective_kind", "FINITE_TASK" if bounded else "UNDECLARED"
            ),
            needs_scope_contract=not bounded,
        ),
        scalar_complexity_score=None,
        calibration_status="UNVALIDATED_FEATURE_VECTOR",
        authority_effect="None",
    )

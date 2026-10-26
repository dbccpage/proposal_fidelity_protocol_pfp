"""Current numbered prompt construction; no provider calls or oracle imports.

The complete schema is a replay sidecar. The participant wire carries a compact
layout, the verbatim seed, source context and explicit conditional licenses.
Only a valid same-pilot, same-run workpad can enter the final stage.
This infrastructure boundary composes the Woland pilot PO035 task profile;
its original seeds, historical experiment profiles and judges stay with the pilots.
"""

import copy
import re
from pathlib import Path

import jsonschema
import yaml

from omega_engine_pfp.infrastructure.adapters.pfp_evidence import canonical, digest, resource_root
from omega_engine_pfp.use_cases.pfp_calculation_contracts import (
    calculation_schema,
    public_workpad_schema,
)

from omega_engine_woland.tests.pilots.relational_spacetime import trial_prompts as experiment_prompts
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import CERTIFICATES
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import array
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import obj
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import (
    response_schema as frozen_response_schema,
)

ROOT = resource_root(Path(__file__))
RECIPE = "PFP-R0001-v1.0.4"
VERSION = "1.0.4"
DEFAULT_RUN_ID = "po035_simplified_v1_0_4_20261013"
REGISTRY_PATH = (
    "omega_engine_pfp/infrastructure/yaml/prompts/templates/"
    "template_role_registry.yaml"
)
# Bound after the new role files are written; unversioned active registry.
REGISTRY_SHA256 = "b8935c6a105eb8bcf459c5b952e8b32e6941505748590b6510a720bf07a0dc78"
ROLES = ("SINGLE_SHOT", "PUBLIC_WORKPAD", "FINAL_FROM_WORKPAD")
ROLE_IDS = ("PFP-T0001", "PFP-T0002", "PFP-T0003")
STAGE_LIMITS = (2500, 600, 2500)

# Carrier names label seed inputs and mathematical objects, never fixture outputs.
FIELD_CARRIERS = {
    "pilot_0000199": {
        "l1_radius": "dilation_fixture.spatial_point.l1_norm",
        "euclidean_radius_squared": "dilation_fixture.spatial_point.euclidean_norm_squared",
        "interval_before": "dilation_fixture.spacetime_event.interval",
        "interval_after": "dilation_fixture.dilated_spacetime_event.interval",
        "null_envelope": "null_fixture.lr_upper_envelope",
        "cone_order_preserved": "spacetime_dilation.homogeneous_cone_relation",
    },
    "pilot_0000200": {
        "residual": "microscopic_fixture.projected_residual",
        "residual_derivative": "microscopic_fixture.full_projected_dynamics",
        "density_derivative": "microscopic_fixture.full_residual_density_derivative",
        "edge_flux": "microscopic_fixture.residual_only_edge_balance",
        "source": "microscopic_fixture.additional_projected_source",
    },
    "pilot_0000201": {
        "composite_transport": "specified_fibers.path_12_composed_01",
        "direct_transport": "specified_fibers.path_02",
        "covariant_delta": "specified_connection.oriented_covariant_difference",
        "flat_relation_holds": "specified_connection.two_cell_path_relation",
        "identity_delta": "identity_connection.oriented_difference",
        "identity_repair": "identity_connection.vertex_potential",
    },
    "pilot_0000202": {
        "cosine_before": "metric_star.original_central_triangle_angle",
        "cosine_after": "metric_star.stretched_central_triangle_angle",
        "curvature_before": "separate_triangle.d1_applied_to_delta",
        "curvature_after": "separate_triangle.d1_applied_to_delta_prime",
        "d1d0": "separate_triangle.cochain_operator_composition",
        "quotient_domain_degree": "separate_triangle.quotient_cochain_domain",
        "curvature_codomain_degree": "separate_triangle.curvature_cochain_codomain",
    },
    "pilot_0000203": {
        "alpha": "finite_triangle.primal_vertex_potential",
        "dual": "finite_triangle.dual_edge_witness",
        "primal_norm": "finite_triangle.primal_residual_l1_objective",
        "dual_value": "finite_triangle.dual_pairing_objective",
        "continuing_transition": "unbounded_counter_system.state_transition",
        "policy_halts": "declared_certificate_terminal_policy.behavior",
    },
}


class _Literal(str):
    """Render source input as a YAML block without changing its parsed value."""


class _Dumper(yaml.SafeDumper):
    pass


_Dumper.add_representer(
    _Literal,
    lambda dumper, value: dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|"),
)


def _pilot(pilot):
    if pilot not in BY_ID:
        raise ValueError("UNKNOWN_PO035_PILOT")
    return BY_ID[pilot]


def _resource_bytes(path):
    relocated = {
        "omega_engine_education/pilots/relational_spacetime/tasks.py":
            "omega_engine_woland/tests/pilots/relational_spacetime/tasks.py",
        "omega_engine_education/pilots/relational_spacetime/trial_prompts.py":
            "omega_engine_woland/tests/pilots/relational_spacetime/trial_prompts.py",
    }
    relative = path.relative_to(ROOT).as_posix()
    path = ROOT / relocated.get(relative, relative)
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise ValueError(
            f"VERSIONED_PROMPT_RESOURCE_UNAVAILABLE:{path.relative_to(ROOT).as_posix()}"
        ) from exc


def _registry():
    path = ROOT / REGISTRY_PATH
    data = _resource_bytes(path)
    if digest(data) != REGISTRY_SHA256:
        raise ValueError("PROMPT_ROLE_REGISTRY_CHANGED")
    registry = yaml.safe_load(data)
    for relative, expected in registry["file_sha256"].items():
        if digest(_resource_bytes(ROOT / relative)) != expected:
            raise ValueError(f"VERSIONED_PROMPT_INPUT_CHANGED:{relative}")
    return registry


def stage_config(stage):
    """Three declared stages; decoding metadata is not part of the user wire."""
    if type(stage) is not int or not 1 <= stage <= 3:
        raise ValueError("UNKNOWN_SIMPLIFIED_STAGE")
    return dict(
        stage_name=ROLES[stage - 1],
        max_output_tokens=STAGE_LIMITS[stage - 1],
        temperature=0,
        response_kind="public_workpad" if stage == 2 else "spk_final",
    )


def prompt_id(pilot, stage, *, run_id=DEFAULT_RUN_ID):
    _pilot(pilot)
    stage_config(stage)
    if type(run_id) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", run_id):
        raise ValueError("INVALID_SIMPLIFIED_RUN_ID")
    return f"{pilot}:{RECIPE}:{ROLE_IDS[stage - 1]}-v{VERSION}:{run_id}"


def _certificate(pilot):
    return copy.deepcopy(CERTIFICATES[_pilot(pilot)["number"] - 199])


def workpad_schema(pilot, *, prompt_id=None):
    _pilot(pilot)
    return public_workpad_schema(FIELD_CARRIERS[pilot], prompt_id=prompt_id)


def response_schema(pilot, *, prompt_id=None):
    """Preserve the SPK envelope; replace only this new recipe's row contract."""
    certificate = _certificate(pilot)
    calculations = calculation_schema(certificate, FIELD_CARRIERS[pilot])
    proposal = obj(
        {
            "prompt_id": {"const": prompt_id}
            if prompt_id is not None
            else {"type": "string", "minLength": 1, "maxLength": 200},
            "status": {"enum": ["PROPOSAL", "TYPED_REFUSAL"]},
            "derivation": obj(
                {
                    "argument": {"type": "string", "minLength": 1, "maxLength": 5000},
                    "open": {
                        "type": "array",
                        "minItems": 0,
                        "maxItems": 12,
                        "items": {"type": "string", "minLength": 1, "maxLength": 400},
                    },
                }
            ),
            "calculations": {"anyOf": [calculations, {"type": "null"}]},
            "certificate": {"anyOf": [certificate, {"type": "null"}]},
        }
    )
    proposal["allOf"] = [
        {
            "if": {"properties": {"status": {"const": "PROPOSAL"}}, "required": ["status"]},
            "then": {"properties": {"calculations": calculations, "certificate": certificate}},
            "else": {
                "properties": {
                    "calculations": {"type": "null"},
                    "certificate": {"type": "null"},
                }
            },
        }
    ]
    envelope = copy.deepcopy(frozen_response_schema(pilot))
    envelope["properties"]["sections"] = array(
        obj({"name": {"const": "po035_derivation"}, "rows": array(proposal, 1)}), 1
    )
    return envelope


def _type_label(schema):
    kind = schema.get("type")
    if kind == "string":
        return "rational string (integer or numerator/positive-denominator; max 100 chars)"
    if kind == "array":
        return f"array[{schema['minItems']}] of {_type_label(schema['items'])}"
    if kind in ("boolean", "integer"):
        return kind
    raise ValueError("UNSUPPORTED_CERTIFICATE_FIELD_TYPE")


def _output_layout(pilot, identity, stage):
    if stage == 2:
        return {
            "root_required_only": {
                "derived_under_policy": "SPK-001",
                "prompt_id": identity,
                "records": (
                    "array of 0..3 objects, required keys only: "
                    "field:one of field_carriers keys, expression:string(1..180), result:string(1..120)"
                ),
                "open": "array of 0..8 nonempty strings, each at most 160 chars",
            },
            "record_scope": "Public inspectable calculations or obligations, not hidden reasoning.",
            "field_carriers": copy.deepcopy(FIELD_CARRIERS[pilot]),
            "uniqueness": "Use each field at most once; at most three records total.",
        }
    fields = _certificate(pilot)["properties"]
    return {
        "root_required_only": {
            "derived_under_policy": "SPK-001",
            "summary": {
                "narrowest_defensible_thesis": "nonblank string",
                "evidence_scope": "nonblank string",
                "next_concrete_test": "nonblank string",
            },
            "process_integrity": {
                "seed_allows_theory_refutation": "boolean",
                "should_continue": "boolean",
                "detected_prompt_biases": "optional array of nonblank strings",
            },
            "sections": "array of exactly one {name: po035_derivation, rows: [one row]}",
        },
        "row_required_only": {
            "prompt_id": identity,
            "status": "PROPOSAL or TYPED_REFUSAL",
            "derivation": {
                "argument": "nonempty string, at most 5000 chars; full conditional argument",
                "open": "array of 0..12 nonempty strings, each at most 400 chars",
            },
            "calculations": (
                "PROPOSAL: object with exactly the certificate keys below; each value is "
                "{carrier: its exact tag below, expression: nonempty string up to 360 chars, "
                "result: same type and value as the matching certificate field}. "
                "TYPED_REFUSAL: null."
            ),
            "certificate": "PROPOSAL: object with exactly the typed fields below. TYPED_REFUSAL: null.",
        },
        "certificate_fields": {
            key: {"type": _type_label(value), "carrier": FIELD_CARRIERS[pilot][key]}
            for key, value in fields.items()
        },
        "typing": (
            "Rational strings match ^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$. "
            "Use native JSON booleans/integers and exact array lengths. No extra keys."
        ),
    }


def _own_workpad(pilot, context, *, run_id=DEFAULT_RUN_ID):
    expected_id = prompt_id(pilot, 2, run_id=run_id)
    supplied = context.get("workpad")
    missing = context.get("workpad_missing", False)
    if type(missing) is not bool:
        raise ValueError("INVALID_WORKPAD_MISSING_FLAG")
    if supplied is None:
        return None, missing
    if missing:
        raise ValueError("WORKPAD_AND_MISSING_FLAG_CONFLICT")
    schema = workpad_schema(pilot, prompt_id=expected_id)
    if not jsonschema.Draft202012Validator(schema).is_valid(supplied):
        raise ValueError("WORKPAD_SCHEMA_OR_IDENTITY_MISMATCH")
    fields = [record["field"] for record in supplied["records"]]
    if len(fields) != len(set(fields)):
        raise ValueError("DUPLICATE_WORKPAD_FIELD")
    return copy.deepcopy(supplied), False


def build_prompt(pilot, stage, context=None, *, run_id=DEFAULT_RUN_ID):
    """Compile one immutable numbered role; never carry a control response."""
    row = _pilot(pilot)
    config = stage_config(stage)
    identity = prompt_id(pilot, stage, run_id=run_id)
    if context is None:
        context = {}
    if type(context) is not dict:
        raise ValueError("INVALID_SIMPLIFIED_CONTEXT")
    registry = _registry()
    role_id = ROLE_IDS[stage - 1]
    role_file = registry["roles"][role_id]["path"]
    role = yaml.safe_load(_resource_bytes(ROOT / role_file))
    # Reuse only the existing scope, licenses, clarifications and pinned source input.
    prompt = experiment_prompts.build_prompt(pilot, 1, experiment="scratchpad")
    old_user = yaml.safe_load(prompt["user_prompt"])
    schema = (
        workpad_schema(pilot, prompt_id=identity)
        if stage == 2
        else response_schema(pilot, prompt_id=identity)
    )
    user = {
        "prompt_id": identity,
        "role": ROLES[stage - 1],
        "contract": role["instructions"],
        "original_seed": _Literal(row["text"]),
        "task_clarifications": old_user["task_clarifications"],
        "obligations_checklist": old_user["semantic_rewrite"],
        "granted_lifts": old_user["granted_lifts"],
        "procedural_advice_untrusted": [item["text"] for item in old_user["candidate_guidance"]],
        "output_layout": _output_layout(pilot, identity, stage),
    }
    if "source_context" in old_user:
        user["source_context"] = dict(old_user["source_context"])
        user["source_context"]["section_5"] = _Literal(user["source_context"]["section_5"])
    prior, missing = _own_workpad(pilot, context, run_id=run_id) if stage == 3 else (None, False)
    if stage == 3:
        user["public_workpad_untrusted"] = prior
        if missing:
            user["workpad_missing_untrusted"] = (
                "No schema-valid workpad was supplied. No mathematical failure or answer is inferred."
            )
    wire = yaml.dump(user, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=1000)
    prompt.update(
        prompt_id=identity,
        prompt_uri=f"prompt://pfp/roles/{role_id}/v{VERSION}/po035/{pilot}/runs/{run_id}",
        run_id=run_id,
        generation=stage,
        recipe=RECIPE,
        role=ROLES[stage - 1],
        role_id=f"{role_id}-v{VERSION}",
        guidance=copy.deepcopy(old_user["candidate_guidance"]),
        user_prompt=wire,
        response_schema=schema,
        response_schema_sha256=digest(canonical(schema)),
        parent_prompt_id=prior["prompt_id"] if prior else None,
        stage_config=config,
        max_output_tokens=config["max_output_tokens"],
        experiment_stage=ROLES[stage - 1],
        experiment_decoding={"temperature": 0, "seed": 20261012 + row["number"]},
        rendered_user_sha256=digest(wire.encode()),
        rendered_prompt_sha256=digest(
            canonical({"system_prompt": prompt["system_prompt"], "user_prompt": wire})
        ),
        registry_path=REGISTRY_PATH,
        registry_sha256=REGISTRY_SHA256,
        role_template_path=role_file,
        role_template_sha256=registry["file_sha256"][role_file],
        recipe_path=registry["recipes"][RECIPE]["path"],
        recipe_sha256=registry["file_sha256"][registry["recipes"][RECIPE]["path"]],
        construction_path=str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"),
        construction_sha256=digest(Path(__file__).read_bytes()),
        schema_sidecar_only=True,
        analytical_status="UNVERIFIED",
        provider_dispatches=0,
    )
    return prompt

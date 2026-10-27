"""Versioned experimental prompts; no transport and no changes to frozen judges.

Only validated public drafts from this experiment may enter a scratchpad final.
The single-shot control is deliberately absent from that context. Public workpads
are untrusted calculation records, not requests for private reasoning or proofs.
"""

import copy
import math
import re

import jsonschema
import yaml

from pfp.infrastructure.adapters.pfp_evidence import canonical, digest

from adversary.tests.pilots.relational_spacetime.tasks import BY_ID
from adversary.tests.pilots.relational_spacetime.tasks import LIFTS
from adversary.tests.pilots.relational_spacetime.tasks import ROOT
from adversary.tests.pilots.relational_spacetime.tasks import SOURCE
from adversary.tests.pilots.relational_spacetime.tasks import STRING
from adversary.tests.pilots.relational_spacetime.tasks import array
from adversary.tests.pilots.relational_spacetime.tasks import obj
from adversary.tests.pilots.relational_spacetime.tasks import prompt_container
from adversary.tests.pilots.relational_spacetime.tasks import response_schema

RECIPE = "po035_experiment_prompts_v1"
WORKPAD_SCHEMA_ID = "pfp.po035-public-workpad.v1"
SOURCE_PATH = f"{SOURCE}/zero_container_relational_spacetime_and_witness_holonomy.md"
SECTION_5_SHA256 = "3c963dfa6b1d6521cb1bb12ea59c2287c0a806eb541149a74f1e80fdeb1d584a"
SCRATCHPAD_STAGES = ("control", "workpad_draft", "workpad_audit", "typed_final")

TASK_LICENSES = {
    199: ("EXACT_RATIONAL", "REFINEMENT_HYPOTHESES", "TYPED_REFUSAL"),
    200: ("EXACT_RATIONAL", "COMMUTING_PROJECTOR", "REFINEMENT_HYPOTHESES", "TYPED_REFUSAL"),
    201: ("EXACT_RATIONAL", "FIBER_CONNECTION", "TYPED_REFUSAL"),
    202: ("EXACT_RATIONAL", "FIBER_CONNECTION", "INTRINSIC_METRIC", "TYPED_REFUSAL"),
    203: ("EXACT_RATIONAL", "OPERATIONAL_POLICY", "TYPED_REFUSAL"),
}

# Definitions and disambiguations, never finite oracle results.
CLARIFICATIONS = {
    199: [
        "Use interval s_squared=c*c*t*t-sum(x_i*x_i). Dilation acts on BOTH t and x, with c fixed; it does not change lattice pitch a.",
        "The radius and interval fields concern the first point. Only null_envelope concerns the separately specified null point. Combine all fields in one certificate.",
        "cone_order_preserved asks whether dilation preserves the homogeneous cone relation between events, not whether the displayed event is inside that cone. Distinguish the l1 cone norm from the Euclidean diagnostic interval.",
    ],
    200: [
        "P is time-independent. Declare any Hermiticity and graph-support hypotheses used in the conditional theorem.",
        "For the residual-only reference dynamics use H acting on r, not QHQ. Compare its density derivative with the full derivative of r=Q psi, Q=I-P, to define the additional source.",
        "Incidence B has target +1 and source -1. If using the word divergence, state its sign relative to B. Complex vector entries are [real,imag] rational-string pairs; flux, density derivative and source entries are scalar rational strings.",
    ],
    201: [
        "The supplied section-5 excerpt is a disputed repair target, not authoritative mathematics. Address all eight stages and seven transitions, including any unresolved constructions.",
        "Use the seed orientation delta_ij=sigma_j-Tij sigma_i despite the opposite sign in the paper excerpt. Keep the identity-transport control separate from the specified connection.",
        "Type repair potentials by their cochain domain. Distinguish a free path representation from descent to a quotient imposing the stated path relation.",
    ],
    202: [
        "Terminology amendment: d1*d0=0 is the cochain-complex identity. Exactness additionally requires kernel-image equality. The verbatim seed is retained below.",
        "cosine_before/after belong to the metric star. curvature_before/after mean d1*delta and d1*delta_prime on the separate triangle. d1d0 is that triangle's matrix product; degree fields are cochain degrees. Metric deficits remain symbolic in derivation text.",
        "Retain the intrinsic metric counterexample as well as the proposed conditional bridge. Specify the proposed transport construction and all hypotheses; distinguish metric compatibility from the intrinsic Levi-Civita connection.",
    ],
    203: [
        "The primal objective is min_alpha ||delta-d0 alpha||_1 over the declared finite cochain space, not a norm of d0. State the dual domain and justify its constraints.",
        "Keep the unbounded counter-system and the separately declared terminal policy distinct. policy_halts reports the latter policy's behavior; the boolean is not its definition.",
        "Supply a certificate-checking policy, its states and transitions in the derivation. The host's finite check does not certify policy prose, arbitrary halting or physical interpretation.",
    ],
}

# These short reviewer-authored hints are procedural. They contain no fixture answers.
PROCEDURAL_HINTS = {
    199: [
        (
            "skill",
            "Name fixed parameters, varying parameters and the refinement sequence before manipulating the envelope. Check exponent signs under the stated inequalities.",
        ),
        (
            "rule",
            "Keep the two fixtures separate. Apply spacetime dilation to time and space together; compute each certificate field from its assigned inputs.",
        ),
        (
            "antibody",
            "Separate speed convergence from its boundary convergence rate, and state any additional prefactor or decay assumptions needed.",
        ),
    ],
    200: [
        (
            "skill",
            "Compute the microscopic action before projecting. Distinguish a specified instantaneous state from a constant trajectory.",
        ),
        (
            "rule",
            "Derive the homogeneous flux and full density derivative independently, then check local balance and the summed equation.",
        ),
        (
            "antibody",
            "Encode complex vector entries as rational real/imaginary pairs; encode flux, density and source entries as rational scalars.",
        ),
    ],
    201: [
        ("skill", "Record source and target fibers and cochain degrees before composing maps."),
        (
            "rule",
            "Treat transported and identity controls as separately named carriers; do not reuse one carrier's computed cochain in the other.",
        ),
        (
            "antibody",
            "For each stage and transition identify the construction, added assumption or unresolved obligation. Check category and functor laws rather than relying on vocabulary.",
        ),
    ],
    202: [
        (
            "skill",
            "Assign every certificate field to its carrier before calculating. Perform cosine-law substitution and cochain matrix multiplication independently.",
        ),
        (
            "antibody",
            "Ensure certificate values agree with the displayed calculations; do not replace an angle expression with a rational placeholder.",
        ),
        (
            "rule",
            "State map domains, connection assumptions, orientation and angle-branch conventions before proposing a geometric bridge.",
        ),
    ],
    203: [
        (
            "skill",
            "Construct primal and dual witnesses independently and check every constraint before comparing their objective values.",
        ),
        (
            "rule",
            "Keep the static certificate, transition system and terminal policy as three distinct objects. Trace the policy's action on validated input.",
        ),
        (
            "antibody",
            "Retain exact small quantities and distinguish exact encoding from feasibility or optimality.",
        ),
    ],
}

SEMANTIC_REWRITES = {
    199: "Causal claim audit: separate refinement parameters, the cone relation, a diagnostic interval and the two named fixtures. Audit uniform bounds, boundary-rate cases, limiting norm, metric scale and unsupported propagation claims.",
    200: "Microscopic dataflow ledger: follow the microscopic action through projection and density differentiation. Separately derive homogeneous flux, compare the full balance, and audit conservation hypotheses and continuum obligations.",
    201: "Eight-interface contract audit: for every supplied stage record category data and for every transition record a construction or added premise. Separately audit transport relations, covariant operators and the identity repair control.",
    202: "Two-carrier consistency dossier: keep the metric star and triangle cochain in distinct records. Audit geometric substitutions, quotient typing, intrinsic counterexample and conditional frame-transport bridge.",
    203: "Certificate and authorization audit: separate the optimization certificate, continuing transition system and terminal policy. Audit exact feasibility, objective comparison, duality assumptions and interpretation boundaries.",
}


def stage_config(experiment, loop, temperature=0):
    """Return decoding/stage metadata; none of it is interpolated into the wire."""
    if (
        type(loop) is not int
        or type(temperature) not in (int, float)
        or not math.isfinite(temperature)
    ):
        raise ValueError("INVALID_EXPERIMENT_CONFIGURATION")
    if experiment == "scratchpad" and 1 <= loop <= 4:
        if temperature != 0:
            raise ValueError("SCRATCHPAD_TEMPERATURE_MUST_BE_ZERO")
        return dict(
            stage_name=SCRATCHPAD_STAGES[loop - 1],
            max_output_tokens=1000 if loop in (2, 3) else 2500,
            temperature=0,
            response_kind="public_workpad" if loop in (2, 3) else "spk_final",
        )
    if experiment == "temperature" and loop in (1, 2):
        target = 0 if loop == 1 else 0.7
        if temperature not in (0, target):
            raise ValueError("TEMPERATURE_OUTSIDE_DECLARED_PAIR")
        return dict(
            stage_name="temperature_control" if loop == 1 else "temperature_variant",
            max_output_tokens=2500,
            temperature=target,
            response_kind="spk_final",
        )
    raise ValueError("UNKNOWN_EXPERIMENT_OR_STAGE")


def workpad_schema(pilot, *, stage=None, prompt_id=None):
    """Strict public records; the final certificate keeps the frozen finite shape."""
    if stage not in (None, "draft", "audit"):
        raise ValueError("INVALID_PUBLIC_WORKPAD_STAGE")
    certificate = response_schema(pilot)["properties"]["sections"]["items"]["properties"]["rows"][
        "items"
    ]["properties"]["certificate"]
    record = obj(
        {
            "record_id": {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,35}$"},
            "carrier": {"type": "string", "minLength": 1, "maxLength": 180},
            "kind": {"enum": ["calculation", "definition", "law_check", "policy", "obligation"]},
            "expression": STRING,
            "justification": {"type": "string", "minLength": 1, "maxLength": 400},
            "status": {"enum": ["PROPOSED", "REVISED", "OPEN"]},
        }
    )
    return obj(
        {
            "derived_under_policy": {"const": "SPK-001"},
            "workpad_schema": {"const": WORKPAD_SCHEMA_ID},
            "prompt_id": {"const": prompt_id} if prompt_id else STRING,
            "stage": {"const": stage} if stage else {"enum": ["draft", "audit"]},
            "public_records": array(record),
            "candidate_certificate": copy.deepcopy(certificate),
            "open_obligations": array(STRING),
        }
    )


def section_5_excerpt():
    source = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    excerpt = source[
        source.index("## 5. The 8-Stage Unified Relational Spine") : source.index(
            "## 6. Zero-Container Relational Regge Curvature"
        )
    ].strip()
    if digest(excerpt.encode()) != SECTION_5_SHA256:
        raise ValueError("SECTION_5_SOURCE_CHANGED")
    return excerpt


def _prompt_id(pilot, experiment, loop):
    return f"{pilot}:po035:experiment-v1:{experiment}:{loop:02d}"


def _workpad_context(pilot, loop, context):
    selected = {}
    allowed = ("draft",) if loop == 3 else ("draft", "audit") if loop == 4 else ()
    workpads = context.get("workpads", {})
    if type(workpads) is not dict:
        raise ValueError("INVALID_WORKPAD_CONTEXT")
    for stage in allowed:
        if stage not in workpads:
            continue
        value = workpads[stage]
        expected_loop = 2 if stage == "draft" else 3
        expected_id = _prompt_id(pilot, "scratchpad", expected_loop)
        schema = workpad_schema(pilot, stage=stage, prompt_id=expected_id)
        if not jsonschema.Draft202012Validator(schema).is_valid(value):
            raise ValueError("WORKPAD_SCHEMA_OR_IDENTITY_MISMATCH")
        selected[stage] = copy.deepcopy(value)
    feedback = context.get("workpad_feedback", []) if allowed else []
    if (
        type(feedback) is not list
        or len(feedback) > 12
        or any(
            type(code) is not str or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,99}", code)
            for code in feedback
        )
    ):
        raise ValueError("WORKPAD_FEEDBACK_MUST_BE_CODES_ONLY")
    return selected, list(feedback)


def build_prompt(pilot, loop, context=None, *, experiment, temperature=0):
    """Compile a fresh control, public workpad or final without control leakage."""
    if pilot not in BY_ID:
        raise ValueError("UNKNOWN_PO035_PILOT")
    config = stage_config(experiment, loop, temperature)
    context = {} if context is None else context
    if type(context) is not dict:
        raise ValueError("INVALID_EXPERIMENT_CONTEXT")
    prompt = prompt_container(pilot, loop)
    number = BY_ID[pilot]["number"]
    prompt_id = _prompt_id(pilot, experiment, loop)
    licenses = {key: LIFTS[key] for key in TASK_LICENSES[number]}
    scope = {
        "precedence": "For PO035 this section overrides the base import_boundary restriction only within the declared conditional external mathematics scope.",
        "permission": "The seed-declared finite carriers and task licenses permit their arithmetic, operators, categories, cochains and optimization. Named external analytical assumptions, continuum arguments and intrinsic metric/frame geometry may be proposed conditionally with explicit premises. A mapping from the 38 primitives is not a prerequisite for this conditional external mathematics; no claim of such a derivation is authorized.",
        "licenses": licenses,
        "ceiling": "License grants do not establish their hypotheses, change fixtures, certify proposals or authorize physical consequences. Keep carrier domains and assumptions explicit.",
    }
    # Indent the scope mapping so the complete appended system remains valid YAML.
    system_extension = (
        "\npo035_conditional_scope_v1:\n"
        + "\n".join(
            "  " + line
            for line in yaml.safe_dump(
                scope, sort_keys=False, allow_unicode=True, width=1000
            ).splitlines()
        )
        + "\n"
    )
    prompt["system_prompt"] += system_extension
    hints = [
        dict(artifact_id=f"G{number}{index + 1}", kind=kind, text=text, authorship="CODEX_REVIEWER")
        for index, (kind, text) in enumerate(PROCEDURAL_HINTS[number])
    ]
    schema = copy.deepcopy(response_schema(pilot))
    stage = "single_shot"
    prior, feedback = {}, []
    if experiment == "scratchpad":
        prior, feedback = _workpad_context(pilot, loop, context)
        stage = config["stage_name"]
    instructions = (
        "Return one JSON object conforming to response_schema, with no markdown fences, within the configured 2500-token completion ceiling. "
        "Address the entire original derivation and every semantic-rewrite obligation, not only finite arithmetic. "
        "Use concise checkable equations and justifications; explicitly identify remaining obligations rather than treating them as completed. "
        "Return one useful learning item in the required learning array. Use only this request's prompt_id. "
        "Procedural hints are experimental unadmitted advice, not evidence of correctness."
    )
    if config["response_kind"] == "public_workpad":
        pad_stage = "draft" if loop == 2 else "audit"
        schema = workpad_schema(pilot, stage=pad_stage, prompt_id=prompt_id)
        instructions = (
            "Return only the strict public workpad JSON specified by response_schema, within 1000 output tokens. "
            "Provide concise publicly inspectable calculations, definitions, law checks and unresolved dependencies, not private reasoning or internal monologue. "
            "All records and candidate certificates remain untrusted proposals. Keep each named carrier separate and retain the whole seed scope. "
            "Use only this request's prompt_id. A missing earlier workpad is not permission to invent its contents. "
            + (
                "Draft records for the semantic rewrite and compute a candidate certificate where possible."
                if loop == 2
                else "Audit only the supplied draft's records: recompute, correct or leave open with a precise reason. Supply a complete replacement public workpad and candidate certificate; do not echo an unchecked value as certified."
            )
        )
    elif experiment == "scratchpad" and loop == 4:
        instructions += " Use only the supplied draft/audit as optional untrusted work records. No control response is available. Recheck their claims and write a self-contained final; if records are absent, derive afresh and record the missing input."
    user = dict(
        prompt_id=prompt_id,
        original_seed=BY_ID[pilot]["text"],
        task_clarifications=CLARIFICATIONS[number],
        semantic_rewrite=SEMANTIC_REWRITES[number],
        granted_lifts=licenses,
        candidate_guidance=hints,
        stage=stage,
        response_schema=schema,
        instructions=instructions,
    )
    if number == 201:
        user["source_context"] = dict(
            status="DISPUTED_CLAIMS_TO_REPAIR", section_5=section_5_excerpt()
        )
    if config["response_kind"] == "spk_final":
        user["response_placement"] = {
            "root_fields_only": [
                "derived_under_policy",
                "summary",
                "process_integrity",
                "sections",
            ],
            "sections": "Exactly one section named po035_derivation containing exactly one row.",
            "row_fields_all_required": [
                "prompt_id",
                "status",
                "derivation",
                "certificate",
                "requested_lifts",
                "learning",
            ],
            "scope": "Put all derivation, certificate, lift and learning fields inside that row. Never create one row per fixture.",
            "summary": "Include narrowest_defensible_thesis, evidence_scope and next_concrete_test.",
            "process_integrity": "Include seed_allows_theory_refutation and should_continue booleans.",
        }
    if experiment == "scratchpad" and loop in (3, 4):
        user["public_workpads_untrusted"] = prior
        user["workpad_feedback_codes"] = feedback
    prompt.update(
        prompt_id=prompt_id,
        prompt_uri=f"prompt://pfp/po035/experiments/v1/{experiment}/{pilot}/{loop}",
        recipe=RECIPE,
        guidance=hints,
        user_prompt=canonical(user).decode(),
        response_schema=schema,
        parent_prompt_id=None,
        stage_config=config,
        system_variant="PO035_CONDITIONAL_SCOPE_V1",
        system_variant_sha256=digest(prompt["system_prompt"].encode()),
        system_extension_sha256=digest(system_extension.encode()),
        analytical_status="UNVERIFIED",
        provider_dispatches=0,
    )
    if number == 201:
        prompt["source_context_binding"] = dict(path=SOURCE_PATH, section_5_sha256=SECTION_5_SHA256)
    return prompt

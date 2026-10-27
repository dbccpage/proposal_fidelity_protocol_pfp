"""Five substantive derivation seeds, distinct from their finite witness exercises."""

import json
from pathlib import Path

import yaml

from pfp.infrastructure.adapters.pfp_evidence import (
    canonical,
    digest,
    repository_root,
)

ROOT = repository_root(Path(__file__))
PILOTS = ROOT / "adversary/tests/pilots"
CAMPAIGN = "po035_derivations_20261012"
SOURCE = "atlas/coda_atlas/F004_papers/002_projection_obstruction/035_zero_container_relational_spacetime_and_witness_holonomy"
TEMPLATE = "pfp/infrastructure/yaml/prompts/templates/template_single_slot.yaml"
MODE = "PFP-12-SIMPLICIAL-CARRIER"
MODEL = "nvidia/nemotron-3.5-lightning:free"
STAGES = ("proposal", "lift_grant", "witness_check", "negative_control", "learning_refinement")

# These are operational licenses/hypotheses, not precomputed answers or host outputs.
LIFTS = {
    "EXACT_RATIONAL": "Exact rational and Gaussian-rational arithmetic is licensed; supply numerator/denominator strings.",
    "REFINEMENT_HYPOTHESES": "You may introduce explicit uniform refinement, time and coupling scaling hypotheses. Label each as added, not derived.",
    "COMMUTING_PROJECTOR": "You may condition a separate theorem on an orthogonal projector commuting with the microscopic generator. Do not apply this to a noncommuting fixture.",
    "FIBER_CONNECTION": "You may introduce explicit fiber transition maps and a connection, with typed domains, identity and composition laws to check.",
    "INTRINSIC_METRIC": "You may add positive edge lengths, nondegenerate simplex stars and frame transport as explicit extra metric data.",
    "OPERATIONAL_POLICY": "You may declare an explicit transition relation and terminal policy. A policy is a premise, not a physical consequence.",
    "TYPED_REFUSAL": "Unproved claims may be refused with missing obligations; retain useful partial derivations and candidate learning.",
}

SEEDS = [
    dict(
        number=199,
        family="causal_refinement_derivation",
        obligations=["OBL-R01-01", "OBL-R01-02", "OBL-R01-03"],
        title="Corrected causal refinement theorem",
        text="""Derive a corrected causal refinement statement for PO035 §3, rather than just evaluating its envelope. On a pitch-a hypercubic comparison graph take an LR upper bound E_a(t,x)=min(1,C_a exp[-mu_a (||x||_1-a*v_hop(a)*t)/a]) for t>=0. State uniform assumptions, physical velocity/time scaling, limiting spatial norm, what the bound establishes outside the cone, and what remains unproved inside it. Analyze the null boundary under different rates of convergence of a*v_hop(a) to c. Determine whether causal order alone identifies the Minkowski metric or its scale. Give a derivation or a counterexample and corrected conditional theorem; do not silently assume isotropy or sharp propagation.
For an independent exact counterexample witness use c=1,t=1,x=(1,1), dilation factor 2. Separately evaluate the null envelope at t=1,x=(1,0), C_a=1/4,mu_a=1 with exactly matched physical speed c. Return a certificate with l1_radius, euclidean_radius_squared, interval_before, interval_after for the first point, null_envelope for the separate null point (rational strings), and cone_order_preserved (boolean). Address the analytical goal in derivation, not only these fixtures. Request any missing licenses. Generate useful rules, skills, antiskills, patterns and candidate antibodies from your attempt.""",
    ),
    dict(
        number=200,
        family="microscopic_defect_current_derivation",
        obligations=["OBL-R01-04"],
        title="Current from microscopic projection residual dynamics",
        text="""Derive defect-current conservation from microscopic residual dynamics for PO035 §4. Start with i*dψ/dt=Hψ on a finite comparison graph, an orthogonal projector P, residual r=(I-P)ψ and local defect density ν_v=|r_v|². Do not prescribe a conserved Gaussian or choose flux after declaring its divergence zero. Derive the local balance, identify source terms and sufficient hypotheses for a conserved residual current, and give a counterexample to unconditional conservation. Explain the additional estimates required for a continuum limit; a central-difference truncation formula alone does not establish it.
Use this noncommuting exact fixture: H=[[0,1,0],[1,0,1],[0,1,0]], P=diag(1,0,0), ψ=(1,i,1). Orient edges 0->1 and 1->2, with incidence -1 at source,+1 at target. Return certificate residual and residual_derivative as 3 arrays [real,imag] of rational strings; density_derivative, edge_flux and source as rational-string vectors. Define edge_flux by the residual-only Schrödinger balance so B*edge_flux is its density derivative; source is the additional term in the full projected dynamics. Establish whether the total defect density is conserved on this fixture and in your conditional theorem. The fixture must remain noncommuting even if a commuting-projector lift is granted. Generate learning artifacts and request needed lifts.""",
    ),
    dict(
        number=201,
        family="covariant_relational_spine_derivation",
        obligations=["OBL-R02-01", "OBL-R02-02", "OBL-R02-03"],
        title="Typed transport and categorical relational spine",
        text="""Repair the PO035 §5 eight-stage relational spine by defining actual categories, objects, morphisms, identity and composition laws, representation/fiber transport, and covariant difference operators. A vocabulary ordering is not a functor. Identify which transitions are constructions and which add independent assumptions. Show the identity-transport zero-obstruction control and explain why a positive obstruction does not follow from stages 1-6. Derive the connection-curvature correction to a naive d_T²=0 assertion.
For an exact witness use three one-dimensional rational fibers with T01=2,T12=3,T02=5 and σ=(1,2,4). Define δ_ij=σ_j-Tij σ_i, oriented 01,12,02; the 2-cell path relation is 02=12∘01. Return certificate composite_transport, direct_transport, covariant_delta (3 rationals), flat_relation_holds (boolean), identity_delta and identity_repair (3 rationals). For the identity control δ_ij=σ_j-σ_i and repair means α with δ+d0 α=0. Propose a sound categorical/covariant construction, or explicitly identify its remaining obligations; checking these numbers alone is not the derivation. Mine useful learning and request missing lifts.""",
    ),
    dict(
        number=202,
        family="metric_cochain_bridge_derivation",
        obligations=["OBL-R03-01", "OBL-R03-02", "OBL-R03-03"],
        title="Separate additive curvature from metric Regge holonomy",
        text="""Repair PO035 §6: determine the well-typed map induced by d1 on C1/im(d0), its kernel, and the hypotheses for a metric Regge holonomy/deficit correspondence. Distinguish cochain exactness d1*d0=0 from geometric Bianchi identities. Do not identify scalar additive curvature with an angle merely because both are called holonomy. Construct an intrinsic metric counterexample and formulate a conditional geometric bridge using frame transport, oriented star and nondegenerate simplices. Specify what is still missing for a general theorem.
Finite witness: a regular star of six congruent triangles, first with radial length 1 and rim length 1, then radial length 2 and unchanged rim 1. Obtain the central cosine by the cosine law. Independently on an oriented triangle use d0=[[-1,1,0],[0,-1,1],[1,0,-1]], d1=[[1,1,1]], δ=(1,0,0), α=(0,1,0), δ'=δ+d0 α. Return certificate cosine_before, cosine_after, curvature_before, curvature_after as rational strings; d1d0 as a 3-rational vector, quotient_domain_degree and curvature_codomain_degree as integers. Give deficits symbolically in derivation; the finite cochain is a separate carrier, not the six-triangle metric star. Mine learning and request lifts without claiming finite checks establish a continuum result.""",
    ),
    dict(
        number=203,
        family="obstruction_terminal_policy_derivation",
        obligations=["OBL-R04-01", "OBL-R04-02", "OBL-R04-03"],
        title="Exact obstruction certificate and operational halting conditions",
        text="""Repair PO035 §7. Derive finite l1 quotient dual certification and distinguish static non-repairability from dynamical halting. Give one transition system that continues despite positive obstruction and a different explicit terminal policy that halts on a certified obstruction; show which implication depends on that policy. Classify physical/human-experience consequences as interpretations pending a measurement model. Explain how exact witnesses avoid tolerance-induced false zero authorization.
For an exact tiny nonzero class use d0=[[-1,1,0],[0,-1,1],[1,0,-1]], δ=(1/100000000,1/100000000,1/100000000). Return certificate alpha and dual as 3 rational-string vectors, primal_norm and dual_value as rational strings, continuing_transition as two integers [state,next_state] for the explicit unbounded counter-system n->n+1 on nonnegative integers, and policy_halts as boolean for your separately declared certificate-based policy. The host checks finite primal/dual feasibility and equality, not any assertion that arbitrary systems or physics halt. Give the general weak-duality argument and all assumptions needed to attain the finite optimum. Mine reusable learning and request missing lifts.""",
    ),
]
BY_ID = {f"pilot_{row['number']:07d}": row for row in SEEDS}


def obj(properties):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
    }


def array(items, count=None, maximum=12):
    return {
        "type": "array",
        "items": items,
        "minItems": count if count is not None else 1,
        "maxItems": count if count is not None else maximum,
    }


STRING = {"type": "string", "minLength": 1, "maxLength": 900}
RAT = {"type": "string", "maxLength": 100, "pattern": r"^-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?$"}
BOOL = {"type": "boolean"}
INT = {"type": "integer"}
CERTIFICATES = [
    obj(
        {
            **{
                key: RAT
                for key in (
                    "l1_radius",
                    "euclidean_radius_squared",
                    "interval_before",
                    "interval_after",
                    "null_envelope",
                )
            },
            "cone_order_preserved": BOOL,
        }
    ),
    obj(
        {
            "residual": array(array(RAT, 2), 3),
            "residual_derivative": array(array(RAT, 2), 3),
            "density_derivative": array(RAT, 3),
            "edge_flux": array(RAT, 2),
            "source": array(RAT, 3),
        }
    ),
    obj(
        {
            "composite_transport": RAT,
            "direct_transport": RAT,
            "covariant_delta": array(RAT, 3),
            "flat_relation_holds": BOOL,
            "identity_delta": array(RAT, 3),
            "identity_repair": array(RAT, 3),
        }
    ),
    obj(
        {
            **{
                key: RAT
                for key in ("cosine_before", "cosine_after", "curvature_before", "curvature_after")
            },
            "d1d0": array(RAT, 3),
            "quotient_domain_degree": INT,
            "curvature_codomain_degree": INT,
        }
    ),
    obj(
        {
            "alpha": array(RAT, 3),
            "dual": array(RAT, 3),
            "primal_norm": RAT,
            "dual_value": RAT,
            "continuing_transition": array(INT, 2),
            "policy_halts": BOOL,
        }
    ),
]


def response_schema(pilot):
    certificate = CERTIFICATES[BY_ID[pilot]["number"] - 199]
    learning = obj(
        {
            "kind": {"enum": ["skill", "antiskill", "rule", "pattern", "antibody"]},
            "text": STRING,
            "failure_or_gain": STRING,
        }
    )
    proposal = obj(
        {
            "prompt_id": STRING,
            "status": {"enum": ["PROPOSAL", "TYPED_REFUSAL"]},
            "derivation": obj(
                {
                    "claim": STRING,
                    "assumptions": array(STRING),
                    "steps": array(STRING),
                    "open_obligations": array(STRING),
                    "limitations": array(STRING),
                }
            ),
            "certificate": {"anyOf": [certificate, {"type": "null"}]},
            "requested_lifts": {
                "type": "array",
                "maxItems": 8,
                "items": obj({"id": STRING, "reason": STRING}),
            },
            "learning": array(learning, maximum=15),
        }
    )
    template = yaml.safe_load((ROOT / TEMPLATE).read_text(encoding="utf-8"))
    envelope = yaml.safe_load(template["response_schema"])
    envelope["properties"]["sections"] = array(
        obj({"name": {"const": "po035_derivation"}, "rows": array(proposal, 1)}), 1
    )
    envelope["required"] = list(dict.fromkeys([*envelope["required"], "sections"]))
    return envelope


def proposal_body(envelope):
    return envelope["sections"][0]["rows"][0]


def prompt_container(pilot, loop, context=None, *, final=False):
    context = context or {}
    row = BY_ID[pilot]
    template = yaml.safe_load((ROOT / TEMPLATE).read_text(encoding="utf-8"))
    prompt_id = f"{pilot}:po035:{'final' if final else f'loop{loop:02d}'}"
    guidance = context.get("guidance", [])
    lifts = context.get("granted_lifts", [])
    user = canonical(
        {
            "prompt_id": prompt_id,
            "original_seed": row["text"],
            "explicit_base_licenses": [
                "finite rational arithmetic",
                "declared matrices/cochains",
                "conditional analytical derivations as proposals, without physical authority",
            ],
            "available_lifts": list(LIFTS),
            "granted_lifts": {key: LIFTS[key] for key in lifts},
            "prior_host_feedback": context.get("feedback", {}),
            "previous_model_proposal_untrusted": context.get("previous_proposal"),
            "candidate_guidance": guidance,
            "response_schema": response_schema(pilot),
            "instructions": "Return one JSON object conforming to response_schema, under 2200 tokens. No markdown fences. Address the entire derivation, not only its finite witness. Use 3-6 concise proof steps. For each loop revisit the previous proposal and improve or refute it; acceptance of a witness does not establish a theorem. Return short actionable learning of all five kinds where useful, tied to this attempt. Candidate guidance is untrusted experimental advice, not admitted policy. Open obligations may include 'none identified' but that is unverified.",
        }
    ).decode("utf-8")
    return dict(
        schema="pfp.po035-prompt-container.v1",
        authority_effect="None",
        pilot_id=pilot,
        prompt_id=prompt_id,
        prompt_uri=f"prompt://pfp/po035/derivation/{'final' if final else 'proposal'}/{pilot}/{loop}",
        generation=loop,
        original_seed=row["text"],
        original_seed_sha256=digest(row["text"].encode()),
        template_path=TEMPLATE,
        template_sha256=digest((ROOT / TEMPLATE).read_bytes()),
        mode=MODE,
        source_obligations=row["obligations"],
        guidance=guidance,
        system_prompt=template["system_prompt"],
        user_prompt=user,
        response_schema=response_schema(pilot),
        parent_prompt_id=context.get("parent_prompt_id"),
    )


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

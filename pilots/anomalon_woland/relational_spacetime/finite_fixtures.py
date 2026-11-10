"""Explicit host-only controls; never serialized into participant prompts."""

import copy
import json

from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body
from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import evaluate

FIXTURES = [
    dict(
        l1_radius="2",
        euclidean_radius_squared="2",
        interval_before="-1",
        interval_after="-4",
        null_envelope="1/4",
        cone_order_preserved=True,
    ),
    dict(
        residual=[["0", "0"], ["0", "1"], ["1", "0"]],
        residual_derivative=[["0", "0"], ["0", "-2"], ["1", "0"]],
        density_derivative=["0", "-4", "2"],
        edge_flux=["0", "2"],
        source=["0", "-2", "0"],
    ),
    dict(
        composite_transport="6",
        direct_transport="5",
        covariant_delta=["0", "-2", "-1"],
        flat_relation_holds=False,
        identity_delta=["1", "2", "3"],
        identity_repair=["-1", "-2", "-4"],
    ),
    dict(
        cosine_before="1/2",
        cosine_after="7/8",
        curvature_before="1",
        curvature_after="1",
        d1d0=["0", "0", "0"],
        quotient_domain_degree=1,
        curvature_codomain_degree=2,
    ),
    dict(
        alpha=["0", "0", "0"],
        dual=["1", "1", "1"],
        primal_norm="3/100000000",
        dual_value="3/100000000",
        continuing_transition=[0, 1],
        policy_halts=True,
    ),
]
VARIANTS = [
    "baseline",
    "missing_stamp",
    "wrong_stamp",
    "wrong_id",
    "bare",
    "extra",
    "bad_status",
    "missing_witness",
    "no_learning",
    "bad_lifts",
    "no_steps",
    "no_derivation",
    "float_rational",
    "bool_rational",
    "zero_denominator",
    "duplicate_key",
    "nan",
    "long_rational",
    "long_learning",
    "missing_claim",
    "extra_proof",
    "wrong_math",
    "missing_certificate_field",
    "integer_rational",
    "different_wrong_math",
]


def fixture_payload(pilot, prompt_id):
    body = dict(
        prompt_id=prompt_id,
        status="PROPOSAL",
        derivation=dict(
            claim="HOST-ONLY FIXTURE; no analytical proof claim",
            assumptions=["declared finite carrier"],
            steps=["fixture"],
            open_obligations=["analytical proof unverified"],
            limitations=["finite control"],
        ),
        certificate=copy.deepcopy(FIXTURES[BY_ID[pilot]["number"] - 199]),
        requested_lifts=[],
        learning=[
            dict(kind="rule", text="Host-only test fixture", failure_or_gain="mutation control")
        ],
    )
    return dict(
        derived_under_policy="SPK-001",
        summary=dict(
            narrowest_defensible_thesis="Host-only finite fixture",
            evidence_scope="No provider or analytical evidence",
            next_concrete_test="Run independent mutation controls",
        ),
        process_integrity=dict(
            seed_allows_theory_refutation=True, should_continue=True, detected_prompt_biases=[]
        ),
        sections=[dict(name="po035_derivation", rows=[body])],
    )


def rational_location(cert, last=False):
    locations = []
    for key, value in cert.items():
        if type(value) is str:
            locations.append((cert, key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if type(item) is str:
                    locations.append((value, index))
                elif isinstance(item, list):
                    locations.extend((item, j) for j, leaf in enumerate(item) if type(leaf) is str)
    return locations[-1 if last else 0]


def check_variant(pilot, variant):
    prompt_id = f"{pilot}:fixture"
    payload = fixture_payload(pilot, prompt_id)
    envelope = payload
    payload = proposal_body(envelope)
    cert = payload["certificate"]
    if variant == "missing_stamp":
        del envelope["derived_under_policy"]
    elif variant == "wrong_stamp":
        envelope["derived_under_policy"] = "OTHER"
    elif variant == "wrong_id":
        payload["prompt_id"] = "foreign"
    elif variant == "bare":
        envelope = cert
    elif variant == "extra":
        payload["unexpected"] = 1
    elif variant == "bad_status":
        payload["status"] = "PROVEN"
    elif variant == "missing_witness":
        payload["certificate"] = None
    elif variant == "no_learning":
        payload["learning"] = []
    elif variant == "bad_lifts":
        payload["requested_lifts"] = "EXACT_RATIONAL"
    elif variant == "no_steps":
        payload["derivation"]["steps"] = []
    elif variant == "no_derivation":
        payload["derivation"] = None
    elif variant == "long_learning":
        payload["learning"][0]["text"] = "x" * 901
    elif variant == "missing_claim":
        del payload["derivation"]["claim"]
    elif variant == "extra_proof":
        payload["derivation"]["proof_verified"] = True
    elif variant == "missing_certificate_field":
        del cert[next(iter(cert))]
    elif variant in (
        "float_rational",
        "bool_rational",
        "zero_denominator",
        "long_rational",
        "wrong_math",
        "integer_rational",
        "different_wrong_math",
    ):
        parent, key = rational_location(cert, variant == "different_wrong_math")
        from fractions import Fraction

        parent[key] = {
            "float_rational": 1.0,
            "bool_rational": True,
            "zero_denominator": "1/0",
            "long_rational": "1" * 101,
            "integer_rational": 1,
        }.get(variant, str(Fraction(parent[key]) + 1))
    content = json.dumps(envelope)
    if variant == "duplicate_key":
        content = content[:-1] + ',"derived_under_policy":"SPK-001"}'
    elif variant == "nan":
        content = content[:-1] + ',"untrusted":NaN}'
    verdict, _ = evaluate(pilot, prompt_id, content)
    assert (verdict["certificate_status"] == "HOST_ACCEPTED") == (variant == "baseline"), (
        pilot,
        variant,
        verdict,
    )
    assert verdict["analytical_status"] == "UNVERIFIED"

"""Independent exact finite predicates. Analytical proof text is never certified."""

import copy
from fractions import Fraction as F

import jsonschema

from omega_engine_woland.infrastructure.providers.wire import decode_reply

from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import response_schema

D0 = [[-1, 1, 0], [0, -1, 1], [1, 0, -1]]


def q(value):
    if type(value) is not str or len(value) > 100:
        raise ValueError("RATIONAL_TYPE")
    return F(value)


def vec(values):
    return [q(x) for x in values]


def mv(matrix, values):
    return [sum(a * b for a, b in zip(row, values, strict=True)) for row in matrix]


def eq(left, right, code):
    if left != right:
        raise ValueError(code)


def causal(c):
    x, t, speed, dilation = [F(1), F(1)], F(1), F(1), F(2)
    squared = sum(v * v for v in x)
    before = speed * speed * t * t - squared
    eq(q(c["l1_radius"]), sum(abs(v) for v in x), "SPATIAL_NORM")
    eq(q(c["euclidean_radius_squared"]), squared, "EUCLIDEAN_NORM")
    eq(q(c["interval_before"]), before, "INTERVAL")
    eq(q(c["interval_after"]), dilation * dilation * before, "METRIC_DILATION")
    eq(q(c["null_envelope"]), min(F(1), F(1, 4)), "NULL_PREFACTOR")
    eq(c["cone_order_preserved"], True, "CAUSAL_DILATION")


def cmul(a, b):
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def current(c):
    h = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    psi = [(F(1), F(0)), (F(0), F(1)), (F(1), F(0))]
    residual = [(F(0), F(0)), *psi[1:]]
    hp = [tuple(sum(h[i][j] * psi[j][k] for j in range(3)) for k in range(2)) for i in range(3)]
    derivative = [(F(0), F(0)), *[cmul((F(0), F(-1)), v) for v in hp[1:]]]
    density = [2 * (r[0] * d[0] + r[1] * d[1]) for r, d in zip(residual, derivative, strict=True)]
    flux = [
        -2 * cmul((residual[i][0], -residual[i][1]), residual[j])[1] for i, j in ((0, 1), (1, 2))
    ]
    divergence = mv([[-1, 0], [1, -1], [0, 1]], flux)
    source = [a - b for a, b in zip(density, divergence, strict=True)]
    eq([tuple(vec(v)) for v in c["residual"]], residual, "PROJECTION_RESIDUAL")
    eq([tuple(vec(v)) for v in c["residual_derivative"]], derivative, "PROJECTED_DYNAMICS")
    eq(vec(c["density_derivative"]), density, "DENSITY_BALANCE")
    eq(vec(c["edge_flux"]), flux, "ORIENTED_FLUX")
    eq(vec(c["source"]), source, "NONCOMMUTING_SOURCE")


def spine(c):
    sigma = [F(1), F(2), F(4)]
    transports = [F(2), F(3), F(5)]
    edges = [(0, 1), (1, 2), (0, 2)]
    eq(q(c["composite_transport"]), transports[1] * transports[0], "COMPOSITION")
    eq(q(c["direct_transport"]), transports[2], "DIRECT_TRANSPORT")
    eq(
        vec(c["covariant_delta"]),
        [sigma[j] - tr * sigma[i] for (i, j), tr in zip(edges, transports, strict=True)],
        "COVARIANT_DIFFERENCE",
    )
    eq(c["flat_relation_holds"], False, "NONFLAT_RELATION")
    identity = [sigma[j] - sigma[i] for i, j in edges]
    eq(vec(c["identity_delta"]), identity, "IDENTITY_CONTROL")
    repair = vec(c["identity_repair"])
    eq(
        [value + repair[j] - repair[i] for value, (i, j) in zip(identity, edges, strict=True)],
        [0, 0, 0],
        "IDENTITY_REPAIR",
    )


def holonomy(c):
    def cos(radial, rim):
        return (2 * radial * radial - rim * rim) / (2 * radial * radial)

    eq(q(c["cosine_before"]), cos(F(1), F(1)), "METRIC_COSINE")
    eq(q(c["cosine_after"]), cos(F(2), F(1)), "METRIC_CHANGE")
    delta = [F(1), F(0), F(0)]
    shift = mv(D0, [F(0), F(1), F(0)])
    eq(q(c["curvature_before"]), sum(delta), "ADDITIVE_CURVATURE")
    eq(
        q(c["curvature_after"]),
        sum(a + b for a, b in zip(delta, shift, strict=True)),
        "GAUGE_INVARIANCE",
    )
    eq(vec(c["d1d0"]), [sum(row[i] for row in D0) for i in range(3)], "COCHAIN_IDENTITY")
    for key, value in (("quotient_domain_degree", 1), ("curvature_codomain_degree", 2)):
        if type(c[key]) is not int:
            raise ValueError("DEGREE_TYPE")
        eq(c[key], value, "QUOTIENT_TYPE")


def stickiness(c):
    delta = [F(1, 100_000_000)] * 3
    alpha, dual = vec(c["alpha"]), vec(c["dual"])
    residual = [x - y for x, y in zip(delta, mv(D0, alpha), strict=True)]
    eq(mv(list(map(list, zip(*D0, strict=True))), dual), [0, 0, 0], "DUAL_ANNIHILATION")
    if max(abs(x) for x in dual) > 1:
        raise ValueError("DUAL_BOUND")
    primal = sum(abs(x) for x in residual)
    objective = sum(a * b for a, b in zip(delta, dual, strict=True))
    eq(q(c["primal_norm"]), primal, "PRIMAL_OBJECTIVE")
    eq(q(c["dual_value"]), objective, "DUAL_OBJECTIVE")
    eq(primal, objective, "DUALITY_GAP")
    if objective <= 0:
        raise ValueError("FALSE_ZERO")
    transition = c["continuing_transition"]
    if any(type(x) is not int or x < 0 for x in transition):
        raise ValueError("STATE_TYPE")
    eq(transition[1], transition[0] + 1, "CONTINUING_COUNTERSYSTEM")
    eq(c["policy_halts"], True, "DECLARED_HALT_POLICY")


CHECKS = [causal, current, spine, holonomy, stickiness]


def evaluate(pilot, prompt_id, content):
    result = dict(
        schema_status="REFUSED",
        certificate_status="NOT_CHECKED",
        analytical_status="UNVERIFIED",
        code="INVALID_JSON",
    )
    payload = None
    try:
        payload = dict(decode_reply(content.encode("utf-8")))
        jsonschema.Draft202012Validator(response_schema(pilot)).validate(payload)
        body = proposal_body(payload)
        if body["prompt_id"] != prompt_id:
            raise ValueError("PROMPT_ID_MISMATCH")
        result["schema_status"] = "VALID"
        if body["status"] == "TYPED_REFUSAL":
            result.update(certificate_status="TYPED_REFUSAL", code="TYPED_REFUSAL")
        else:
            if body["certificate"] is None:
                raise ValueError("WITNESS_MISSING")
            CHECKS[BY_ID[pilot]["number"] - 199](body["certificate"])
            result.update(certificate_status="HOST_ACCEPTED", code="FINITE_WITNESS_VALID")
    except jsonschema.ValidationError as exc:
        result["code"] = "SCHEMA_VIOLATION"
        result["schema_path"] = list(exc.absolute_path)
        result["schema_validator"] = exc.validator
        payload = None
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc:
        result["code"] = str(exc) if isinstance(exc, ValueError) else "MALFORMED_WITNESS"
        if result["schema_status"] == "VALID":
            result["certificate_status"] = "REFUSED"
        if result["schema_status"] != "VALID":
            payload = None
    return result, payload


def negative_control(pilot, prompt_id, payload):
    if (
        payload is None
        or proposal_body(payload)["certificate"] is None
        or proposal_body(payload)["status"] != "PROPOSAL"
    ):
        return dict(
            kind="MALFORMED_ENVELOPE",
            checked=True,
            rejected=evaluate(pilot, prompt_id, "{}")[0]["schema_status"] == "REFUSED",
        )
    changed = copy.deepcopy(payload)
    cert = proposal_body(changed)["certificate"]
    keys = ("l1_radius", "residual", "composite_transport", "cosine_before", "primal_norm")
    parent, key = cert, keys[BY_ID[pilot]["number"] - 199]
    while isinstance(parent[key], list):
        parent = parent[key]
        key = 0
    parent[key] = "0" if q(parent[key]) != 0 else "1"
    verdict, _ = evaluate(pilot, prompt_id, __import__("json").dumps(changed))
    return dict(
        kind="CANDIDATE_WITNESS_MUTATION",
        checked=True,
        rejected=verdict["certificate_status"] != "HOST_ACCEPTED",
        code=verdict["code"],
    )

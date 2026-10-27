"""GATE11 residual dual fixtures + host replay (Symbol Game lab).

AuthorityEffect: None. Host verifies model proposals; never mints GlobalGreen.
Frozen K0 matches deepseek_reply_000 / SG-OESOS-GATE11-FW8-001 samples.

Every Phi1, Gamma2 and diagnostic class below comes from an
``ExactFunctionalPort`` -- in production the native host's ``core_functional``.
This module compares a proposal's claims against those receipts; it computes
none of the named functionals itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence

from pfp.domain.exact.errors import ExactRefusal
from pfp.domain.ports.exact_ports import ExactFunctionalPort
from pfp.domain.value_objects.functional_receipt import FunctionalReceipt


def Q(x: Any) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, bool):
        raise TypeError("bool refused")
    if isinstance(x, float):
        raise ValueError(f"float refused: {x}")
    if isinstance(x, int):
        return Fraction(x)
    s = str(x).strip()
    if "/" in s:
        a, b = s.split("/", 1)
        return Fraction(int(a), int(b))
    return Fraction(int(s))


# Phi1 was asked for on a fixture that carries only a bound on it, never a
# certificate pinning it. Recorded as a refusal rather than reported as a value.
REFUSAL_PHI1_NOT_CERTIFIED = "PHI1_NOT_CERTIFIED"

# DeepSeek / prompt sample K0
K0_NODES: tuple[int, ...] = (0, 1, 2, 3)
K0_EDGES: tuple[tuple[int, int], ...] = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (0, 2),
)
# face f0 ~ (e0, e1, -e4) as vertex triple for Network/CochainCarrier
K0_FACE_VERTICES: tuple[tuple[int, int, int], ...] = ((0, 1, 2),)


def k0_d0() -> list[list[Fraction]]:
    """Edge-node incidence: edge u->v has -1 at u, +1 at v."""
    n_e, n_v = len(K0_EDGES), len(K0_NODES)
    idx = {v: i for i, v in enumerate(K0_NODES)}
    d0 = [[Fraction(0) for _ in range(n_v)] for _ in range(n_e)]
    for ei, (u, v) in enumerate(K0_EDGES):
        d0[ei][idx[u]] = Fraction(-1)
        d0[ei][idx[v]] = Fraction(1)
    return d0


def k0_d1() -> list[list[Fraction]]:
    """Face-edge boundary: +e0 +e1 -e4 on triangle 0-1-2."""
    return [[Fraction(1), Fraction(1), Fraction(0), Fraction(0), Fraction(-1)]]


@dataclass(frozen=True, slots=True)
class Gate11Fixture:
    name: str  # Exact | StabilizedSurvivor | OpenObstruction
    omega: tuple[Fraction, ...]
    alpha_star: tuple[Fraction, ...] | None
    y_star: tuple[Fraction, ...] | None
    phi: Fraction
    gamma: Fraction


def frozen_fixtures() -> tuple[Gate11Fixture, ...]:
    return (
        Gate11Fixture(
            name="Exact",
            omega=tuple(Q(x) for x in (-1, 0, 0, 1, -1)),
            alpha_star=tuple(Q(x) for x in (1, 0, 0, 0)),
            y_star=tuple(Q(x) for x in (0, 0, 0, 0, 0)),
            phi=Q(0),
            gamma=Q(0),
        ),
        Gate11Fixture(
            name="StabilizedSurvivor",
            omega=tuple(Q(x) for x in (0, 0, 1, 1, 0)),
            alpha_star=None,
            y_star=tuple(Q(x) for x in (1, 1, 1, 1, 0)),
            phi=Q(2),
            gamma=Q(0),
        ),
        Gate11Fixture(
            name="OpenObstruction",
            omega=tuple(Q(x) for x in (0, 0, 0, 0, 1)),
            alpha_star=None,
            y_star=None,
            phi=Q(1),
            gamma=Q(1),
        ),
    )


@dataclass(frozen=True, slots=True)
class HostCheck:
    id: str
    passed: bool
    evidence: str


def _refused(check_id: str, refusal: ExactRefusal) -> HostCheck:
    return HostCheck(check_id, False, f"REFUSED:{refusal.code}:{refusal.detail}")


def verify_carrier(
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
) -> HostCheck:
    """``d1 d0 = 0``, decided by the native host before any functional runs.

    The zero cochain is evaluated because the host refuses a complex that breaks
    the chain law before it reads the residual.
    """
    try:
        receipt = port.evaluate(d0, d1, [Fraction(0)] * len(d0))
    except ExactRefusal as refusal:
        return _refused("G2_d1d0_zero", refusal)
    return HostCheck("G2_d1d0_zero", True, f"native chain law holds; digest={receipt.input_digest}")


def _claim_check(
    check_id: str,
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
    fx: Gate11Fixture,
    expected_class: str,
) -> HostCheck:
    """The fixture's claims against a Rust-issued receipt, compared exactly."""
    try:
        receipt = port.evaluate(d0, d1, fx.omega)
    except ExactRefusal as refusal:
        return _refused(check_id, refusal)
    ok = (
        receipt.diagnostic_class == expected_class
        and receipt.phi1 == fx.phi
        and receipt.gamma2 == fx.gamma
    )
    return HostCheck(
        check_id,
        ok,
        f"class={receipt.diagnostic_class} phi1={receipt.phi1} gamma2={receipt.gamma2} "
        f"claimed=({fx.phi},{fx.gamma}) digest={receipt.input_digest}",
    )


def verify_exact(
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
    fx: Gate11Fixture,
) -> HostCheck:
    return _claim_check("G4_exact", port, d0, d1, fx, "ExactRepair")


def verify_survivor(
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
    fx: Gate11Fixture,
) -> HostCheck:
    return _claim_check("G5_survivor", port, d0, d1, fx, "ClosedResidual")


def verify_open(
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
    fx: Gate11Fixture,
) -> HostCheck:
    return _claim_check("G6_open", port, d0, d1, fx, "ActiveClosureFailure")


def host_verify_fixtures(
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]] | None = None,
    d1: Sequence[Sequence[Fraction]] | None = None,
    fixtures: Sequence[Gate11Fixture] | None = None,
    *,
    authority_effect: str = "None",
) -> dict[str, Any]:
    d0 = list(d0) if d0 is not None else k0_d0()
    d1 = list(d1) if d1 is not None else k0_d1()
    fixtures = tuple(fixtures) if fixtures is not None else frozen_fixtures()
    checks: list[HostCheck] = [
        HostCheck("G7_authority_none", authority_effect == "None", authority_effect),
        verify_carrier(port, d0, d1),
    ]
    by_name = {f.name: f for f in fixtures}
    if "Exact" in by_name:
        checks.append(verify_exact(port, d0, d1, by_name["Exact"]))
    if "StabilizedSurvivor" in by_name:
        checks.append(verify_survivor(port, d0, d1, by_name["StabilizedSurvivor"]))
    if "OpenObstruction" in by_name:
        checks.append(verify_open(port, d0, d1, by_name["OpenObstruction"]))
    overall = all(c.passed for c in checks)
    return {
        "overall_passed": overall,
        "authority_effect": "None",
        "packet_id": "SG-OESOS-GATE11-FW8-001",
        "family": "residual_dual_exactness_v0",
        "functional_owner": "engine/crates_rs/core_functional",
        "checks": [
            {"id": c.id, "passed": c.passed, "evidence": c.evidence} for c in checks
        ],
        "host_terminal": "LabFixtureReplay" if overall else "OpenObstruction",
        "evidence_ceiling": "LocalReplay",
        "note": "Host LocalReplay only. Not GlobalGreen. Not AuthorityEffect.",
        "remaining_delta": (
            ["NEXT_PACKET:SG-OESOS-ROUTE-001"]
            if overall
            else [f"FAIL:{c.id}:{c.evidence}" for c in checks if not c.passed]
        ),
    }


def parse_rational_list(blob: str) -> tuple[Fraction, ...]:
    nums = re_findall_rationals(blob)
    return tuple(nums)


def re_findall_rationals(blob: str) -> list[Fraction]:
    import re

    out: list[Fraction] = []
    for m in re.finditer(r"-?\d+(?:/\d+)?", blob):
        out.append(Q(m.group(0)))
    return out


def parse_gate11_symbolic_reply(text: str, port: ExactFunctionalPort) -> dict[str, Any]:
    """Best-effort parse of residual_dual_exactness_v0 symbolic reply."""
    import re

    auth_m = re.search(r"authority_effect\s*:\s*(\S+)", text, re.I)
    authority = auth_m.group(1) if auth_m else "MISSING"

    def matrix_after(header: str) -> list[list[Fraction]]:
        m = re.search(header + r"\s*:?\s*\n(\[[\s\S]*?\])", text, re.I)
        if not m:
            raise ValueError(f"missing matrix {header}")
        rows: list[list[Fraction]] = []
        for line in m.group(1).splitlines():
            if re.search(r"\d+\s*x\s*\d+", line, re.I):
                continue
            cleaned = line.replace("[", " ").replace("]", " ").replace(";", " ")
            nums = re.findall(r"-?\d+", cleaned)
            if nums:
                rows.append([Q(n) for n in nums])
        if not rows:
            raise ValueError(f"empty matrix {header}")
        w = max(len(r) for r in rows)
        return [r for r in rows if len(r) == w]

    d0 = matrix_after(r"d0\s*\(\s*\d+\s*x\s*\d+\s*\)")
    d1 = matrix_after(r"d1\s*\(\s*\d+\s*x\s*\d+\s*\)")

    def fixture_block(name: str) -> str:
        m = re.search(
            rf"fixture<{name}>\s*([\s\S]*?)(?=fixture<|MACHINE\b|\Z)",
            text,
            re.I,
        )
        if not m:
            raise ValueError(f"fixture<{name}> missing")
        return m.group(0)

    def scalar(block: str, key: str) -> Fraction:
        m = re.search(rf"{key}\s*<\s*([^>]+)\s*>", block)
        if not m:
            raise ValueError(f"{key} missing in fixture")
        return Q(m.group(1).strip())

    def vec(block: str, key: str) -> tuple[Fraction, ...]:
        m = re.search(rf"{key}\s*<\s*\[([^\]]+)\]\s*>", block)
        if not m:
            raise ValueError(f"{key} vector missing")
        return tuple(Q(x.strip()) for x in m.group(1).split(",") if x.strip())

    fixtures: list[Gate11Fixture] = []
    for name in ("Exact", "StabilizedSurvivor", "OpenObstruction"):
        b = fixture_block(name)
        alpha = None
        y = None
        if re.search(r"alpha_star\s*<", b):
            alpha = vec(b, "alpha_star")
        if re.search(r"y_star\s*<", b):
            y = vec(b, "y_star")
        fixtures.append(
            Gate11Fixture(
                name=name,
                omega=vec(b, "omega"),
                alpha_star=alpha,
                y_star=y,
                phi=scalar(b, "Phi"),
                gamma=scalar(b, "Gamma"),
            )
        )

    result = host_verify_fixtures(port, d0, d1, fixtures, authority_effect=authority)
    result["source_kind"] = "symbolic_reply"
    result["self_cert_scan"] = bool(
        re.search(r"(?i)GlobalGreen\s*[:=]\s*true|IsAuth\s*[:=]\s*true", text)
    )
    if result["self_cert_scan"]:
        result["overall_passed"] = False
        result["remaining_delta"] = ["FAIL:self_cert"] + list(result["remaining_delta"])
    return result


def host_verify_self(port: ExactFunctionalPort) -> dict[str, Any]:
    """No model: host replays frozen fixtures (automate against yourself)."""
    result = host_verify_fixtures(port)
    result["source_kind"] = "frozen_self"
    return result


def certified_phi1(
    port: ExactFunctionalPort,
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
    fx: Gate11Fixture,
) -> tuple[FunctionalReceipt | None, str | None]:
    """The host's certified receipt for one fixture, or the refusal naming why not.

    Phi1 is certified by ``core_functional`` from a verified primal-dual pair,
    so it no longer depends on the fixture carrying its own certificate.
    """
    try:
        return port.evaluate(d0, d1, fx.omega), None
    except ExactRefusal as refusal:
        return None, f"{REFUSAL_PHI1_NOT_CERTIFIED}: {refusal.code}: {refusal.detail}"


def contract_bound_holds(gamma2: Fraction, phi1: Fraction | None) -> bool | None:
    """Evaluate ``Gamma2 <= Phi1`` exactly over Q.

    A named predicate rather than an inline comparison, because this is a
    functional law and a law deserves a place a test can reach. It was
    previously written as ``gamma2 <= phi1`` slackened by an epsilon of one
    billionth, which reports a violation of up to that size as compliance.

    ``None`` when Phi1 was never certified: the bound is then undetermined, not
    satisfied. Returning ``True`` there would be a fail-open.
    """
    if phi1 is None:
        return None
    return gamma2 <= phi1


def project_fixture_phi_gamma(port: ExactFunctionalPort, fx: Gate11Fixture) -> Mapping[str, Any]:
    """Rust-issued Phi1/Gamma2 for one frozen fixture over the K0 complex."""
    receipt, refusal = certified_phi1(port, k0_d0(), k0_d1(), fx)
    if receipt is None:
        return {
            "fixture": fx.name,
            "phi1": None,
            "gamma2": None,
            "phi1_refusal": refusal,
            "is_exact": False,
            "input_digest": None,
            "authority_effect": "None",
        }
    return {
        "fixture": fx.name,
        "phi1": receipt.phi1,
        "gamma2": receipt.gamma2,
        "phi1_refusal": None,
        "is_exact": receipt.diagnostic_class == "ExactRepair",
        "input_digest": receipt.input_digest,
        "authority_effect": "None",
    }

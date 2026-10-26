"""Concrete infrastructure cochain scoring adapter for Woland Swarm.

Phi1 comes from the native Rust host (``omega_solvers`` exact weighted L1
projection, certified against ``omega_functional``). The adapter accepts a
measurement only when the host reports ``certificate_verified: true`` and the
returned exact strings are internally consistent. Every other path -- no host,
a native refusal, an unverified certificate, a malformed carrier, an inexact
cochain value -- is ``NOT_MEASURED`` with its reason. There is no floating-point
fallback solver and no invented Phi1 or Gamma2.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping, Sequence

import numpy as np

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_pfp.ffi import RustSymbolGameHost, get_default_host
from omega_engine_woland.domain.evidence import (
    MeasurementStatus,
    ObstructionMeasurementV1,
    canonical_rational,
    parse_exact_rational,
)
from omega_engine_woland.domain.network import Network

_LOCUS = "omega_engine_woland.infrastructure.cochain_adapter"
_BACKEND = "rust_exact_omega_solvers"


def to_canonical_rational_str(val: Fraction | int | str) -> str:
    """Format an exact rational to the wire canonical string (no '/1' for integers).

    Floats and bools are refused: a float carries no exact value, and rounding
    one to a nearby fraction could cancel a positive defect.
    """
    if type(val) is bool or isinstance(val, (float, np.floating, np.bool_)):
        raise TypeError(f"exact rational required, got {type(val).__name__}")
    if isinstance(val, np.integer):
        val = int(val)
    return canonical_rational(parse_exact_rational(val))


def build_incidence(network: Network) -> tuple[np.ndarray, dict[Any, int]]:
    """Build boundary operator matrix d0 mapping 1-chains (edges) to 0-chains (nodes)."""
    node_idx = {n: i for i, n in enumerate(network.nodes)}
    n_e, n_v = len(network.edges), len(network.nodes)
    d0 = np.zeros((n_e, n_v), dtype=float)
    for e_i, (u, v) in enumerate(network.edges):
        d0[e_i, node_idx[u]] = -1.0
        d0[e_i, node_idx[v]] = 1.0
    return d0, node_idx


def build_exact_incidence(network: Network) -> tuple[list[list[str]], dict[Any, int]]:
    """Build exact rational boundary operator matrix d0 (edges x nodes)."""
    node_idx = {n: i for i, n in enumerate(network.nodes)}
    n_e, n_v = len(network.edges), len(network.nodes)
    matrix = [["0"] * n_v for _ in range(n_e)]
    for e_i, (u, v) in enumerate(network.edges):
        matrix[e_i][node_idx[u]] = "-1"
        matrix[e_i][node_idx[v]] = "1"
    return matrix, node_idx


def build_face_boundary(network: Network) -> np.ndarray:
    """Build boundary operator matrix d1 mapping 2-cells (faces) to 1-chains (edges)."""
    n_e, n_f = len(network.edges), len(network.faces)
    d1 = np.zeros((n_e, n_f), dtype=float)
    edge_idx = {e: i for i, e in enumerate(network.edges)}
    for j, (u, v, w) in enumerate(network.faces):
        for x, y in [(u, v), (v, w), (w, u)]:
            if (x, y) in edge_idx:
                d1[edge_idx[(x, y)], j] += 1.0
            elif (y, x) in edge_idx:
                d1[edge_idx[(y, x)], j] -= 1.0
    return d1


def build_exact_face_boundary(network: Network) -> tuple[list[list[str]], dict[tuple[Any, Any], int]]:
    """Build exact rational boundary operator matrix d1 (faces x edges for coboundary d1 @ r)."""
    n_e, n_f = len(network.edges), len(network.faces)
    edge_idx = {e: i for i, e in enumerate(network.edges)}
    matrix = [["0"] * n_e for _ in range(n_f)]
    for j, (u, v, w) in enumerate(network.faces):
        for x, y in [(u, v), (v, w), (w, u)]:
            if (x, y) in edge_idx:
                matrix[j][edge_idx[(x, y)]] = "1"
            elif (y, x) in edge_idx:
                matrix[j][edge_idx[(y, x)]] = "-1"
    return matrix, edge_idx


def _permutation_parity(a: Sequence[Any], b: Sequence[Any]) -> int:
    """Return +1 for even permutation, -1 for odd permutation."""
    if len(a) != len(b):
        return 1
    pos = {val: i for i, val in enumerate(b)}
    arr = [pos[x] for x in a if x in pos]
    if len(arr) != len(a):
        return 1
    inv = 0
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                inv += 1
    return 1 if inv % 2 == 0 else -1


def build_exact_tetrahedra_boundary(
    network: Network,
) -> tuple[list[list[str]], dict[tuple[Any, Any, Any], int], dict[tuple[Any, Any, Any, Any], int]]:
    """Build exact rational boundary operator matrix d2 (faces x tetrahedra)."""
    face_idx = {tuple(f): i for i, f in enumerate(network.faces)}
    tet_idx = {tuple(t): j for j, t in enumerate(network.tetrahedra)}
    n_f, n_t = len(network.faces), len(network.tetrahedra)
    matrix = [["0"] * n_t for _ in range(n_f)]

    for j, tet in enumerate(network.tetrahedra):
        v = sorted(tet)
        boundary_faces = [
            ((v[1], v[2], v[3]), 1),
            ((v[0], v[2], v[3]), -1),
            ((v[0], v[1], v[3]), 1),
            ((v[0], v[1], v[2]), -1),
        ]
        for f, sign in boundary_faces:
            if f in face_idx:
                matrix[face_idx[f]][j] = str(sign)
            else:
                for perm_f in face_idx:
                    if set(perm_f) == set(f):
                        p_sign = _permutation_parity(f, perm_f)
                        matrix[face_idx[perm_f]][j] = str(sign * p_sign)
                        break
    return matrix, face_idx, tet_idx


def build_exact_four_simplex_boundary(
    network: Network,
) -> tuple[list[list[str]], dict[tuple[Any, Any, Any, Any], int], dict[tuple[Any, ...], int]]:
    """Build exact rational boundary operator matrix d3 (tetrahedra x 4-simplices)."""
    tet_idx = {tuple(t): i for i, t in enumerate(network.tetrahedra)}
    simplex_idx = {tuple(s): j for j, s in enumerate(network.four_simplices)}
    n_t, n_s = len(network.tetrahedra), len(network.four_simplices)
    matrix = [["0"] * n_s for _ in range(n_t)]

    for j, s in enumerate(network.four_simplices):
        v = sorted(s)
        for i in range(5):
            face_tet = tuple(v[:i] + v[i + 1:])
            sign = 1 if i % 2 == 0 else -1
            if face_tet in tet_idx:
                matrix[tet_idx[face_tet]][j] = str(sign)
            else:
                for perm_t in tet_idx:
                    if set(perm_t) == set(face_tet):
                        p_sign = _permutation_parity(face_tet, perm_t)
                        matrix[tet_idx[perm_t]][j] = str(sign * p_sign)
                        break
    return matrix, tet_idx, simplex_idx


class DefaultCochainScoringAdapter:
    """Production cochain scoring adapter performing Hodge L1 gauge fixing and cycle defect evaluation.

    Connected to the native Rust FFI seam (RustSymbolGameHost) for exact rational arithmetic
    and certificate verification against omega_engine/crates_rs/omega_functional.
    """

    def __init__(self, host: RustSymbolGameHost | None = None) -> None:
        self._host = host

    def get_host(self) -> RustSymbolGameHost | None:
        """Resolve injected or default native Rust host seam; ``None`` when not built."""
        if self._host is not None:
            return self._host
        try:
            return get_default_host()
        except (FileNotFoundError, OSError, RuntimeError, ValueError):
            return None

    def verify_simplicial_boundary_law(
        self, network: Network
    ) -> Result[Mapping[str, Any], Refusal]:
        """Verify d o d = 0 for the network simplicial 2-complex through native Rust host."""
        host = self.get_host()
        if host is None:
            return Err(Refusal("NATIVE_HOST_UNAVAILABLE", "Rust host is unavailable"))
        node_idx = {n: i for i, n in enumerate(network.nodes)}
        simplices = []
        for face in network.faces:
            if len(face) >= 3:
                simplices.append([node_idx[u] for u in face[:3]])
        for tet in network.tetrahedra:
            if len(tet) >= 4:
                simplices.append([node_idx[u] for u in tet[:4]])
        for s in network.four_simplices:
            if len(s) >= 5:
                simplices.append([node_idx[u] for u in s[:5]])
        if not simplices:
            return Ok({
                "boundary_law_verified": True,
                "compositions": [],
                "euler_characteristic": len(network.nodes) - len(network.edges),
                "max_dimension": 1 if network.edges else 0,
                "simplex_counts_by_dim": [len(network.nodes), len(network.edges), 0],
            })
        return host.exact_verify_simplicial_boundary_law(simplices)

    def verify_exact_phi1_certificate(
        self,
        network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any],
        alpha: Sequence[Any],
        dual_witness: Sequence[Any],
    ) -> Result[Mapping[str, Any], Refusal]:
        """Verify exact rational Phi1 quotient certificate through native Rust FFI.

        Verifies that alpha and dual_witness prove Phi1(omega) = min ||omega - d0 alpha||_1 = <y, omega>
        matching omega_functional::phi1::Phi1Functional::verify_exact_certificate.
        """
        host = self.get_host()
        if host is None:
            return Err(Refusal("NATIVE_HOST_UNAVAILABLE", "Rust host is unavailable"))
        d0_matrix, _ = build_exact_incidence(network)
        omega = [to_canonical_rational_str(initial_cochain.get(e, 0)) for e in network.edges]
        p = [to_canonical_rational_str(a) for a in alpha]
        y = [to_canonical_rational_str(w) for w in dual_witness]
        return host.verify_l1_certificate(d0_matrix, omega, p, y)

    def compute_exact_gamma2(
        self,
        network: Network,
        residual: Mapping[tuple[Any, Any], Any] | Sequence[Any],
    ) -> Fraction:
        """Compute exact rational Gamma2 closure defect ||d1 h||_1.

        Matches omega_functional::gamma2::Gamma2Functional::try_compute_raw over BigRational.
        """
        if not network.faces:
            return Fraction(0, 1)
        if isinstance(residual, Mapping):
            h_vec = [Fraction(to_canonical_rational_str(residual.get(e, 0))) for e in network.edges]
        else:
            h_vec = [Fraction(to_canonical_rational_str(v)) for v in residual]

        edge_idx = {e: i for i, e in enumerate(network.edges)}
        total_coboundary_mass = Fraction(0, 1)
        for (u, v, w) in network.faces:
            face_flux = Fraction(0, 1)
            for x, y in [(u, v), (v, w), (w, u)]:
                if (x, y) in edge_idx:
                    face_flux += h_vec[edge_idx[(x, y)]]
                elif (y, x) in edge_idx:
                    face_flux -= h_vec[edge_idx[(y, x)]]
            total_coboundary_mass += abs(face_flux)
        return total_coboundary_mass

    def compute_exact_face_cochain(
        self,
        network: Network,
        residual: Mapping[tuple[Any, Any], Any] | Sequence[Any],
    ) -> dict[tuple[Any, Any, Any], Fraction]:
        """Compute exact rational face 2-cochain omega^(2) = delta^1 h."""
        if not network.faces:
            return {}
        if isinstance(residual, Mapping):
            h_vec = [Fraction(to_canonical_rational_str(residual.get(e, 0))) for e in network.edges]
        else:
            h_vec = [Fraction(to_canonical_rational_str(v)) for v in residual]

        edge_idx = {e: i for i, e in enumerate(network.edges)}
        face_cochain: dict[tuple[Any, Any, Any], Fraction] = {}
        for (u, v, w) in network.faces:
            face_flux = Fraction(0, 1)
            for x, y in [(u, v), (v, w), (w, u)]:
                if (x, y) in edge_idx:
                    face_flux += h_vec[edge_idx[(x, y)]]
                elif (y, x) in edge_idx:
                    face_flux -= h_vec[edge_idx[(y, x)]]
            face_cochain[(u, v, w)] = face_flux
        return face_cochain

    def compute_exact_delta2(
        self,
        network: Network,
        face_cochain: Mapping[tuple[Any, Any, Any], Any],
    ) -> dict[tuple[Any, Any, Any, Any], Fraction]:
        """Compute exact coboundary delta^2: C^2 -> C^3 on tetrahedra (Bianchi curvature defect)."""
        if not network.tetrahedra:
            return {}
        face_map: dict[tuple[Any, Any, Any], Fraction] = {
            f: Fraction(to_canonical_rational_str(val))
            for f, val in face_cochain.items()
        }
        res: dict[tuple[Any, Any, Any, Any], Fraction] = {}
        for tet in network.tetrahedra:
            v = sorted(tet)
            boundary_faces = [
                ((v[1], v[2], v[3]), 1),
                ((v[0], v[2], v[3]), -1),
                ((v[0], v[1], v[3]), 1),
                ((v[0], v[1], v[2]), -1),
            ]
            tet_flux = Fraction(0, 1)
            for f, sign in boundary_faces:
                if f in face_map:
                    tet_flux += sign * face_map[f]
                else:
                    for perm_f, val in face_map.items():
                        if set(perm_f) == set(f):
                            p_sign = _permutation_parity(f, perm_f)
                            tet_flux += sign * p_sign * val
                            break
            res[tuple(tet)] = tet_flux
        return res

    def compute_exact_delta3(
        self,
        network: Network,
        tet_cochain: Mapping[tuple[Any, Any, Any, Any], Any],
    ) -> dict[tuple[Any, ...], Fraction]:
        """Compute exact coboundary delta^3: C^3 -> C^4 on 4-simplices (4D Regge spacetime deficit closure)."""
        if not network.four_simplices:
            return {}
        tet_map: dict[tuple[Any, Any, Any, Any], Fraction] = {
            t: Fraction(to_canonical_rational_str(val))
            for t, val in tet_cochain.items()
        }
        res: dict[tuple[Any, ...], Fraction] = {}
        for s in network.four_simplices:
            v = sorted(s)
            s_flux = Fraction(0, 1)
            for i in range(5):
                face_tet = tuple(v[:i] + v[i + 1:])
                sign = 1 if i % 2 == 0 else -1
                if face_tet in tet_map:
                    s_flux += sign * tet_map[face_tet]
                else:
                    for perm_t, val in tet_map.items():
                        if set(perm_t) == set(face_tet):
                            p_sign = _permutation_parity(face_tet, perm_t)
                            s_flux += sign * p_sign * val
                            break
            res[tuple(s)] = s_flux
        return res

    def compute_regge_spacetime_deficits(
        self,
        network: Network,
        residual_or_cochain: Mapping[tuple[Any, Any], Any] | Sequence[Any],
    ) -> dict[str, Any]:
        """Compute 4D Regge spacetime deficits: Gamma2, Xi3 (delta^2), and Xi4 (delta^3)."""
        gamma2 = self.compute_exact_gamma2(network, residual_or_cochain)
        face_cochain = self.compute_exact_face_cochain(network, residual_or_cochain)
        delta2_cochain = self.compute_exact_delta2(network, face_cochain)
        xi3 = sum(abs(v) for v in delta2_cochain.values()) if delta2_cochain else Fraction(0, 1)
        delta3_cochain = self.compute_exact_delta3(network, delta2_cochain)
        xi4 = sum(abs(v) for v in delta3_cochain.values()) if delta3_cochain else Fraction(0, 1)

        bianchi_closed = (xi3 == Fraction(0, 1))
        spacetime_closed = (xi4 == Fraction(0, 1))
        converged = bool(bianchi_closed and spacetime_closed and gamma2 == Fraction(0, 1))

        return {
            "gamma2": gamma2,
            "xi3": xi3,
            "xi4": xi4,
            "delta2_cochain": delta2_cochain,
            "delta3_cochain": delta3_cochain,
            "bianchi_closed": bianchi_closed,
            "spacetime_closed": spacetime_closed,
            "regge_converged": converged,
        }

    def solve_exact_l1_primal_dual(
        self,
        network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any],
        weights: Sequence[Any] | None = None,
        budget: int | None = None,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Solve exact rational Hodge L1 gauge fixing and dual witness over Q via RustSymbolGameHost.

        Delegates to omega_solvers::exact_weighted_l1_lp::solve_weighted_l1_projection on the native Rust side.
        Returns exact alpha (gauge 0-cochain), residual z = omega - d0 alpha, dual witness y, and optimal Phi1,
        certified against omega_functional.
        """
        host = self.get_host()
        if host is None:
            return Err(Refusal("NATIVE_HOST_UNAVAILABLE", "Rust host is unavailable"))
        d0_matrix, node_idx = build_exact_incidence(network)
        target = [to_canonical_rational_str(initial_cochain.get(e, 0)) for e in network.edges]
        weights_canonical = (
            [to_canonical_rational_str(w) for w in weights] if weights is not None else None
        )
        res = host.exact_solve_l1_primal_dual(
            d0_matrix, target, weights=weights_canonical, budget=budget
        )
        if not res.is_ok:
            return res
        data = res.unwrap()
        if data.get("success") is not True or type(data.get("result")) is not dict:
            return Err(
                Refusal(
                    "NATIVE_SOLVER_REFUSED",
                    f"native exact_solve_l1_primal_dual did not succeed: {data.get('error')!r}",
                    _LOCUS,
                )
            )
        result_payload = dict(data["result"])
        if result_payload.get("certificate_verified") is not True:
            # The host reports whether omega_functional verified the primal-dual
            # certificate. Anything but an exact `true` fails closed.
            return Err(
                Refusal(
                    "CERTIFICATE_UNVERIFIED",
                    "the native Phi1 certificate was not verified by omega_functional",
                    _LOCUS,
                )
            )
        result_payload["node_index"] = node_idx
        result_payload["edge_index"] = {e: i for i, e in enumerate(network.edges)}
        return Ok(result_payload)

    def propose_gauge(
        self,
        network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any],
        weights: Sequence[Any] | None = None,
        budget: int | None = None,
    ) -> Result[tuple[dict[Any, Fraction], dict[tuple[Any, Any], Fraction], Fraction], Refusal]:
        """Propose exact gauge 0-cochain alpha and dual witness y minimizing ||cochain - d0 alpha||_1.

        Returns (alpha_map, dual_witness_map, exact_phi1).
        """
        res = self.solve_exact_l1_primal_dual(
            network, initial_cochain, weights=weights, budget=budget
        )
        if not res.is_ok:
            return Err(res.unwrap_err())
        sol = res.unwrap()
        node_idx_rev = {i: n for n, i in sol["node_index"].items()}
        alpha_map = {node_idx_rev[i]: Fraction(a) for i, a in enumerate(sol["alpha"])}
        dual_map = {e: Fraction(sol["dual_witness"][i]) for i, e in enumerate(network.edges)}
        phi1 = Fraction(sol["phi1"])
        return Ok((alpha_map, dual_map, phi1))

    def identify_obstructions(
        self,
        carrier_network: Network,
        initial_cochain: Mapping[tuple[Any, Any], Any],
        *,
        ablation_flags: Mapping[str, bool] | None = None,
    ) -> Result[ObstructionMeasurementV1, Refusal]:
        """Measure Phi1 and Gamma2 exactly, or say precisely why nothing was measured."""
        malformed = _carrier_defect(carrier_network, initial_cochain)
        if malformed:
            return Ok(ObstructionMeasurementV1.not_measured(malformed, backend="carrier_validation"))
        exact_cochain = {edge: parse_exact_rational(value) for edge, value in initial_cochain.items()}
        if ablation_flags and ablation_flags.get("no_obstruction_typing"):
            l1_mass = sum((abs(value) for value in exact_cochain.values()), Fraction(0))
            return Ok(
                ObstructionMeasurementV1.not_measured(
                    "ABLATION_NO_OBSTRUCTION_TYPING: the untyped scalar l1 mass "
                    f"{canonical_rational(l1_mass)} is not a quotient measurement",
                    backend="ablation_no_typing",
                )
            )
        host = self.get_host()
        if host is None:
            return Ok(
                ObstructionMeasurementV1.not_measured(
                    "NATIVE_HOST_UNAVAILABLE: the omega_symbol_game host binary is not built",
                    backend=_BACKEND,
                )
            )
        solved = self.solve_exact_l1_primal_dual(carrier_network, exact_cochain)
        if solved.is_err:
            refusal = solved.unwrap_err()
            return Ok(
                ObstructionMeasurementV1.not_measured(
                    f"{refusal.code}: {refusal.message}", backend=_BACKEND
                )
            )
        return Ok(self._measurement_from_payload(carrier_network, exact_cochain, solved.unwrap()))

    def _measurement_from_payload(
        self,
        network: Network,
        cochain: Mapping[tuple[Any, Any], Fraction],
        payload: Mapping[str, Any],
    ) -> ObstructionMeasurementV1:
        edges = tuple(network.edges)
        try:
            phi1 = parse_exact_rational(payload["phi1"])
            alpha = [parse_exact_rational(value) for value in payload["alpha"]]
            residual = [parse_exact_rational(value) for value in payload["residual"]]
            dual = [parse_exact_rational(value) for value in payload["dual_witness"]]
        except (KeyError, TypeError, ValueError) as exc:
            return ObstructionMeasurementV1.not_measured(
                f"HOST_PAYLOAD_INVALID: {exc}", backend=_BACKEND
            )
        if len(residual) != len(edges) or len(dual) != len(edges):
            return ObstructionMeasurementV1.not_measured(
                "HOST_PAYLOAD_INVALID: residual or dual witness length differs from the edge count",
                backend=_BACKEND,
            )
        if len(alpha) != len(network.nodes):
            return ObstructionMeasurementV1.not_measured(
                "HOST_PAYLOAD_INVALID: the gauge alpha length differs from the node count",
                backend=_BACKEND,
            )
        # The residual must be the input cochain minus the coboundary of the
        # returned gauge, edge by edge: residual_e = omega_e - (alpha_v - alpha_u).
        # A host (or a double) that returned any other vector -- zeros, say --
        # would otherwise launder the cochain through a consistent-looking phi1.
        potential = dict(zip(network.nodes, alpha, strict=True))
        expected = [
            cochain.get((u, v), Fraction(0)) - (potential[v] - potential[u]) for u, v in edges
        ]
        if residual != expected:
            return ObstructionMeasurementV1.not_measured(
                "HOST_PAYLOAD_INCONSISTENT: the residual is not omega - d0 alpha for the "
                "returned alpha",
                backend=_BACKEND,
            )
        if phi1 != sum((abs(value) for value in residual), Fraction(0)):
            return ObstructionMeasurementV1.not_measured(
                "HOST_PAYLOAD_INCONSISTENT: phi1 is not the l1 norm of the returned residual",
                backend=_BACKEND,
            )
        # Gamma2 on the verified residual (equal to ||d1 omega|| since d1 d0 = 0).
        gamma2 = self.compute_exact_gamma2(network, expected)
        active = tuple(
            f"{u}->{v}" for (u, v), value in zip(edges, residual, strict=True) if value != 0
        )
        return ObstructionMeasurementV1(
            status=MeasurementStatus.MEASURED,
            backend=_BACKEND,
            phi1=phi1,
            gamma2=gamma2,
            defect_count=len(active),
            active_obstructions=active,
            certificate_verified=True,
            dual_witness=tuple(
                (f"{u}->{v}", value) for (u, v), value in zip(edges, dual, strict=True)
            ),
        )


def _carrier_defect(network: Network, cochain: Mapping[tuple[Any, Any], Any]) -> str:
    """Name the first reason this carrier cannot be measured, or return ``""``."""
    if not network.edges:
        return "EMPTY_CARRIER: a carrier without edges has nothing to measure"
    edge_set = set(network.edges)
    if len(edge_set) != len(network.edges):
        return "MALFORMED_CARRIER: duplicate edge"
    for u, v in network.edges:
        if u == v:
            return f"MALFORMED_CARRIER: self-loop edge ({u}, {v})"
        if (v, u) in edge_set:
            return f"MALFORMED_CARRIER: edge ({u}, {v}) appears in both orientations"
    node_set = set(network.nodes)
    for face in network.faces:
        if len(face) != 3 or len(set(face)) != 3:
            return f"MALFORMED_FACE: {tuple(face)!r} is not a triangle of three distinct nodes"
        if not set(face) <= node_set:
            return f"MALFORMED_FACE: {tuple(face)!r} names a node outside the carrier"
        a, b, c = face
        for x, y in ((a, b), (b, c), (c, a)):
            if (x, y) not in edge_set and (y, x) not in edge_set:
                return f"MALFORMED_FACE: {tuple(face)!r} has no edge between {x} and {y}"
    for key, value in cochain.items():
        if key not in edge_set:
            return f"MALFORMED_COCHAIN: key {key!r} is not an edge of the carrier"
        try:
            parse_exact_rational(value)
        except (TypeError, ValueError) as exc:
            return f"INEXACT_COCHAIN_VALUE: {exc}"
    return ""


__all__ = [
    "DefaultCochainScoringAdapter",
    "build_incidence",
    "build_exact_incidence",
    "build_face_boundary",
    "build_exact_face_boundary",
    "build_exact_tetrahedra_boundary",
    "build_exact_four_simplex_boundary",
    "to_canonical_rational_str",
]

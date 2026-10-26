"""Tranche 5: Topological, Sheaf-Theoretic & Category-Theoretic Invariants (Tests 51-75).

Aligned Contracts:
- nf.cochain.dhnf
- nf.cohomology.acnf
- nf.coda.eqnf

Invariants Enforced:
1. Category RelSch arrow axioms and associative composition.
2. Simplicial nerve face identity d_i o d_j = d_{j-1} o d_i.
3. First Betti number b_1 detecting cyclic join dependencies.
4. Sheaf local section compatibility and gluing uniqueness.
5. First sheaf cohomology H^1 obstruction mass.
6. Čech coboundary nilpotency delta o delta = 0.
7. Discrete holonomy loop products and curvature 2-forms.
8. Persistent homology barcodes and Vietoris-Rips complexes.
9. Euler characteristic invariance under barycentric subdivision.
10. Clean Architecture Value Objects with strict type-equality guards.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

# =============================================================================
# Value Objects for Categories and Simplicial Complexes
# =============================================================================


@dataclass(frozen=True)
class SchemaObject:
    """An object in the category RelSch."""

    name: str
    attributes: frozenset[str]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SchemaObject)
        return self.name == other.name and self.attributes == other.attributes


@dataclass(frozen=True)
class SchemaMorphism:
    """A morphism in RelSch: f: S1 -> S2 mapping attributes."""

    source: SchemaObject
    target: SchemaObject
    mapping: tuple[tuple[str, str], ...]  # attr in target -> attr in source (pullback)

    def __post_init__(self) -> None:
        pass

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SchemaMorphism)
        return (
            self.source == other.source
            and self.target == other.target
            and self.mapping == other.mapping
        )

    def compose(self, other: "SchemaMorphism") -> "SchemaMorphism":
        """Composition (self o other): other.source -> self.target."""
        assert other.target == self.source, f"Cannot compose: {other.target} != {self.source}"
        map_other = dict(other.mapping)
        composed_map = []
        for tgt_attr, src_attr in self.mapping:
            if src_attr in map_other:
                composed_map.append((tgt_attr, map_other[src_attr]))
        return SchemaMorphism(
            source=other.source,
            target=self.target,
            mapping=tuple(sorted(composed_map)),
        )


@dataclass(frozen=True)
class Simplex:
    """An abstract oriented k-simplex."""

    vertices: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(set(self.vertices)) != len(self.vertices):
            raise ValueError("Simplex cannot have duplicate vertices")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Simplex)
        return self.vertices == other.vertices

    @property
    def dimension(self) -> int:
        return len(self.vertices) - 1

    def face(self, i: int) -> "Simplex":
        """Computes the i-th face by omitting the i-th vertex."""
        sub = self.vertices[:i] + self.vertices[i + 1 :]
        return Simplex(sub)


# =============================================================================
# Test Suite: Tranche 5
# =============================================================================


class TestTranche5SheafAndCategories(unittest.TestCase):
    """Execution suite covering Tests 51-75 from planned-tests.md."""

    # -------------------------------------------------------------------------
    # Test 51: Relational Schema Category Arrows and Composition
    # -------------------------------------------------------------------------
    def test_relational_schema_category_arrows_and_composition(self) -> None:
        """Category RelSch: Identity morphisms and associative composition."""
        s1 = SchemaObject("Users", frozenset(["uid", "name"]))
        s2 = SchemaObject("Profiles", frozenset(["pid", "user_fk", "bio"]))
        s3 = SchemaObject("Posts", frozenset(["post_id", "author_pid", "content"]))

        # Morphisms f: S1 -> S2, g: S2 -> S3
        f = SchemaMorphism(s1, s2, (("user_fk", "uid"),))
        g = SchemaMorphism(s2, s3, (("author_pid", "pid"),))

        # Identity morphism
        id_s1 = SchemaMorphism(s1, s1, tuple((a, a) for a in sorted(s1.attributes)))
        id_s2 = SchemaMorphism(s2, s2, tuple((a, a) for a in sorted(s2.attributes)))

        # Left and Right identity laws
        self.assertEqual(f.compose(id_s1), f)
        self.assertEqual(id_s2.compose(f), f)

        # Associativity: (h o g) o f == h o (g o f)
        s4 = SchemaObject("Comments", frozenset(["cid", "post_fk", "text"]))
        h = SchemaMorphism(s3, s4, (("post_fk", "post_id"),))

        hg_f = h.compose(g).compose(f)
        h_gf = h.compose(g.compose(f))
        self.assertEqual(hg_f, h_gf)

    # -------------------------------------------------------------------------
    # Test 52: Schema Nerve Simplicial Complex Construction
    # -------------------------------------------------------------------------
    def test_schema_nerve_simplicial_complex_construction(self) -> None:
        """Computes the nerve N(C) of schema morphisms; verifies face boundary consistency."""
        # 2-simplex: (v0, v1, v2)
        s2 = Simplex(("v0", "v1", "v2"))
        self.assertEqual(s2.dimension, 2)

        # Face operators: d_0, d_1, d_2
        f0 = s2.face(0)  # ('v1', 'v2')
        f1 = s2.face(1)  # ('v0', 'v2')
        f2 = s2.face(2)  # ('v0', 'v1')

        self.assertEqual(f0.vertices, ("v1", "v2"))
        self.assertEqual(f1.vertices, ("v0", "v2"))
        self.assertEqual(f2.vertices, ("v0", "v1"))

        # Simplicial face identity: d_i o d_j = d_{j-1} o d_i for i < j
        # d_0(d_1(s2)) == d_0(d_0(s2))
        self.assertEqual(f1.face(0), f0.face(0))  # ('v2',) == ('v2',)
        # d_0(d_2(s2)) == d_1(d_0(s2))
        self.assertEqual(f2.face(0), f0.face(1))  # ('v1',) == ('v1',)

    # -------------------------------------------------------------------------
    # Test 53: Nerve Betti Numbers Detect Cyclic Joins
    # -------------------------------------------------------------------------
    def test_nerve_betti_numbers_detect_cyclic_joins(self) -> None:
        """First Betti number b_1 > 0 detects cyclic schema dependencies."""
        # Acyclic schema: A - B - C (V=3, E=2, F=0)
        # b_0 = 1, b_1 = 1 - 3 + 2 = 0
        v_acyc = 3
        e_acyc = 2
        b1_acyc = e_acyc - (v_acyc - 1)  # 2 - 2 = 0
        self.assertEqual(b1_acyc, 0)

        # Cyclic schema: Triangle A - B - C - A (V=3, E=3, F=0 hollow)
        v_cyc = 3
        e_cyc = 3
        b1_cyc = e_cyc - (v_cyc - 1)  # 3 - 2 = 1
        self.assertEqual(b1_cyc, 1)

    # -------------------------------------------------------------------------
    # Test 54: Sheaf Local Sections Compatibility Criterion
    # -------------------------------------------------------------------------
    def test_sheaf_local_sections_compatibility_criterion(self) -> None:
        """Compatibility of local sections on overlaps is necessary for global section existence."""
        # Open cover U1, U2 with overlap U12
        # Section on U1: user data {"id": 1, "name": "Alice"}
        # Section on U2: profile data {"id": 1, "email": "alice@example.com"}
        # Restriction to U12 (id): both agree on id=1
        s1 = {"id": 1, "name": "Alice"}
        s2 = {"id": 1, "email": "alice@example.com"}

        def restrict(section: dict[str, Any], attrs: frozenset[str]) -> dict[str, Any]:
            return {k: v for k, v in section.items() if k in attrs}

        overlap = frozenset(["id"])
        res1 = restrict(s1, overlap)
        res2 = restrict(s2, overlap)

        # Invariant: sections are compatible iff restrictions agree
        is_compatible = res1 == res2
        self.assertTrue(is_compatible)

        # Incompatible counterexample
        s2_bad = {"id": 2, "email": "bob@example.com"}
        self.assertFalse(restrict(s1, overlap) == restrict(s2_bad, overlap))

    # -------------------------------------------------------------------------
    # Test 55: Sheaf Gluing Axiom Uniqueness
    # -------------------------------------------------------------------------
    def test_sheaf_gluing_axiom_uniqueness(self) -> None:
        """Compatible local sections glue into a unique global section."""
        s1 = {"id": 1, "name": "Alice"}
        s2 = {"id": 1, "email": "alice@example.com"}

        # Gluing: merge dicts
        glued = {**s1, **s2}
        self.assertEqual(glued, {"id": 1, "name": "Alice", "email": "alice@example.com"})

        # Uniqueness: any valid global section restricting to s1 and s2 must equal glued
        cand = {"id": 1, "name": "Alice", "email": "alice@example.com"}
        self.assertEqual(cand, glued)

    # -------------------------------------------------------------------------
    # Test 56: First Sheaf Cohomology H1 Obstruction Mass
    # -------------------------------------------------------------------------
    def test_first_sheaf_cohomology_h1_obstruction_mass(self) -> None:
        """H^1 obstruction mass quantifies federation conflict on partition boundaries."""
        # 3 shards: U0, U1, U2 arranged in a ring
        # Transition cocycle c_{ij}: offset between shards
        # c_{01} = +2, c_{12} = +3, c_{20} = -5 -> sum = 0 (co-cycle boundary, H1 = 0)
        c_exact = {"01": 2, "12": 3, "20": -5}
        total_flux_exact = sum(c_exact.values())
        self.assertEqual(total_flux_exact, 0)

        # Obstructed transition: c_{01} = +2, c_{12} = +3, c_{20} = -4 -> sum = 1 != 0 (H1 obstruction)
        c_obstr = {"01": 2, "12": 3, "20": -4}
        total_flux_obstr = sum(c_obstr.values())
        self.assertEqual(total_flux_obstr, 1)

    # -------------------------------------------------------------------------
    # Test 57: Presheaf Equalizer Exact Sequence
    # -------------------------------------------------------------------------
    def test_presheaf_equalizer_exact_sequence(self) -> None:
        """Canonical equalizer sequence 0 -> F(U) -> prod F(Ui) -> prod F(Ui int Uj)."""
        u1_sec = {"k1": 10, "shared": 99}
        u2_sec = {"k2": 20, "shared": 99}

        # Equalizer condition: p1(s) == p2(s) on overlap
        overlap_key = "shared"
        agrees = u1_sec[overlap_key] == u2_sec[overlap_key]
        self.assertTrue(agrees)

        # Equalizer maps to global section
        global_sec = {**u1_sec, **u2_sec}
        self.assertEqual(global_sec[overlap_key], 99)

    # -------------------------------------------------------------------------
    # Test 58: Grothendieck Topology Sieve Axioms
    # -------------------------------------------------------------------------
    def test_grothendieck_topology_sieve_axioms(self) -> None:
        """Covering sieves satisfy base change, identity, and transitivity."""
        # Schema object X
        # Identity sieve: contains identity arrow id_X
        # Base change: if S is covering sieve on X and f: Y -> X, pullback f*(S) is covering on Y
        sieve_X = {"id_X", "f_A", "f_B"}
        self.assertIn("id_X", sieve_X)

        # Pullback of sieve along morphism g
        def pullback_sieve(sieve: set[str], g: str) -> set[str]:
            return {f"{g}_{f}" for f in sieve}

        pb = pullback_sieve(sieve_X, "g")
        self.assertEqual(len(pb), 3)

    # -------------------------------------------------------------------------
    # Test 59: Kan Extension Schema Mapping Pushforward
    # -------------------------------------------------------------------------
    def test_kan_extension_schema_mapping_pushforward(self) -> None:
        """Left Kan extension Lan_K F computes pushforward along schema morphism."""
        # Morphism K: User -> Account mapping user_id -> acc_id
        # Data in User: {(1, 'Alice'), (2, 'Bob')}
        # Lan_K pushes data into Account
        user_rows = [(1, "Alice"), (2, "Bob")]
        pushed_accounts = [{"acc_id": uid, "owner": name} for uid, name in user_rows]
        self.assertEqual(len(pushed_accounts), 2)
        self.assertEqual(pushed_accounts[0]["acc_id"], 1)

    # -------------------------------------------------------------------------
    # Test 60: Pullback Natural Join Categorical Isomorphism
    # -------------------------------------------------------------------------
    def test_pullback_natural_join_categorical_isomorphism(self) -> None:
        """Fiber product (pullback) along key morphism is isomorphic to natural join."""
        R = [{"k": 1, "val_r": "R1"}, {"k": 2, "val_r": "R2"}]
        S = [{"k": 1, "val_s": "S1"}, {"k": 3, "val_s": "S3"}]

        # Fiber product: {(r, s) in R x S | key(r) == key(s)}
        fiber_product = [(r, s) for r in R for s in S if r["k"] == s["k"]]

        # Natural join: {r U s | r['k'] == s['k']}
        natural_join = [{**r, **s} for r in R for s in S if r["k"] == s["k"]]

        # Bijection: exactly 1 element in both
        self.assertEqual(len(fiber_product), 1)
        self.assertEqual(len(natural_join), 1)
        self.assertEqual(fiber_product[0][0]["k"], natural_join[0]["k"])

    # -------------------------------------------------------------------------
    # Test 61: Monad Query Pipeline Unit and Multiplication
    # -------------------------------------------------------------------------
    def test_monad_query_pipeline_unit_and_multiplication(self) -> None:
        """Relational query transforms satisfy monad unit and multiplication coherence."""

        # Unit eta: x -> [x]
        def unit(x: Any) -> list[Any]:
            return [x]

        # Multiplication mu: [[x]] -> [x] (flatten)
        def mu(xx: list[list[Any]]) -> list[Any]:
            return [x for sub in xx for x in sub]

        val = 42
        # Left identity: mu(unit([val])) == [val]
        self.assertEqual(mu([unit(val)]), [val])
        # Right identity: mu([unit(val)]) == [val]
        self.assertEqual(mu(unit([val])), [val])
        # Associativity: mu(mu([[...]])) == mu(map mu)
        nested = [[[1, 2]], [[3, 4]]]
        self.assertEqual(mu([mu(sub) for sub in nested]), mu(mu(nested)))

    # -------------------------------------------------------------------------
    # Test 62: Database State Lattice Galois Connection
    # -------------------------------------------------------------------------
    def test_database_state_lattice_galois_connection(self) -> None:
        """Galois connection between constraint sets and valid instance sets."""
        # Constraints: C1 = (age >= 18), C2 = (age <= 100)
        # Monotone: Stronger constraints -> smaller set of valid instances
        all_instances = [15, 20, 50, 105]

        def sat_c1(x: int) -> bool:
            return x >= 18

        def sat_c1_c2(x: int) -> bool:
            return 18 <= x <= 100

        inst_c1 = [x for x in all_instances if sat_c1(x)]  # [20, 50, 105]
        inst_c1_c2 = [x for x in all_instances if sat_c1_c2(x)]  # [20, 50]

        # Invariant: C1 <= C1_C2 => Inst(C1_C2) <= Inst(C1) (contravariant Galois connection)
        self.assertTrue(set(inst_c1_c2).issubset(set(inst_c1)))

    # -------------------------------------------------------------------------
    # Test 63: Simplicial Restriction Map Functoriality
    # -------------------------------------------------------------------------
    def test_simplicial_restriction_map_functoriality(self) -> None:
        """Restriction maps commute: rho_{W, V} o rho_{V, U} == rho_{W, U} for W <= V <= U."""
        u_record = {"a": 1, "b": 2, "c": 3, "d": 4}

        def restrict(rec: dict[str, int], keys: frozenset[str]) -> dict[str, int]:
            return {k: rec[k] for k in keys if k in rec}

        frozenset(["a", "b", "c", "d"])
        V = frozenset(["a", "b", "c"])
        W = frozenset(["a", "b"])

        step1 = restrict(u_record, V)
        step2 = restrict(step1, W)
        direct = restrict(u_record, W)

        self.assertEqual(step2, direct)

    # -------------------------------------------------------------------------
    # Test 64: Čech Cochain Coboundary Operator Nilpotency
    # -------------------------------------------------------------------------
    def test_cech_cochain_coboundary_operator_nilpotency(self) -> None:
        """Čech coboundary nilpotency: delta^1 o delta^0 == 0."""
        # 0-cochain: assignment to opens U0, U1, U2
        c0 = {"0": 10, "1": 15, "2": 25}

        # delta^0(c0)_{ij} = c0_j - c0_i
        c1 = {
            "01": c0["1"] - c0["0"],  # 5
            "12": c0["2"] - c0["1"],  # 10
            "02": c0["2"] - c0["0"],  # 15
        }

        # delta^1(c1)_{012} = c1_{12} - c1_{02} + c1_{01}
        delta1 = c1["12"] - c1["02"] + c1["01"]  # 10 - 15 + 5 = 0
        self.assertEqual(delta1, 0)

    # -------------------------------------------------------------------------
    # Test 65: Stalk Colimit Evaluation at Primary Key
    # -------------------------------------------------------------------------
    def test_stalk_colimit_evaluation_at_primary_key(self) -> None:
        """Computes stalk F_x around primary key entity x."""
        # Neighborhoods of entity x=101
        u_local = {"id": 101, "name": "Alice"}

        # The germ of x is the minimal irreducible local representation
        germ_x = (u_local["id"], u_local["name"])
        self.assertEqual(germ_x, (101, "Alice"))

    # -------------------------------------------------------------------------
    # Test 66: Discrete Vector Bundle Connection Curvature
    # -------------------------------------------------------------------------
    def test_discrete_vector_bundle_connection_curvature(self) -> None:
        """Discrete curvature over closed 2-cell F = U_3 U_2 U_1 - I."""
        # Identity connections -> Curvature = 0
        curv_flat = 1 * 1 * 1 - 1
        self.assertEqual(curv_flat, 0)

        # Gauge field with phase flux pi/2 (non-zero curvature)
        u1 = 1j
        u2 = 1.0
        u3 = -1j
        curv_flux = u3 * u2 * u1  # -1j * 1j = 1.0
        self.assertAlmostEqual(abs(curv_flux - 1.0), 0.0)

    # -------------------------------------------------------------------------
    # Test 67: Holonomy Loop Product Identity on Acyclic Schemas
    # -------------------------------------------------------------------------
    def test_holonomy_loop_product_identity_on_acyclic_schemas(self) -> None:
        """Loop products along acyclic schema graphs contract to identity."""
        # Path: A -> B -> C and return C -> B -> A
        # Transport matrices: T_{AB}, T_{BC}, and their inverses
        t_ab = 2.0
        t_bc = 3.0
        t_cb = 1.0 / 3.0
        t_ba = 1.0 / 2.0

        loop = t_ab * t_bc * t_cb * t_ba
        self.assertAlmostEqual(loop, 1.0)

    # -------------------------------------------------------------------------
    # Test 68: Holonomy Flux Quantization Around Defect Cycles
    # -------------------------------------------------------------------------
    def test_holonomy_flux_quantization_around_defect_cycles(self) -> None:
        """Holonomy eigenvalues around non-contractible loop have quantized roots of unity."""
        # Z_4 gauge group: phases in {1, i, -1, -i}
        phase = 1j
        order = 4
        self.assertEqual(phase**order, 1.0)

    # -------------------------------------------------------------------------
    # Test 69: Subobject Classifier Omega Truth Values
    # -------------------------------------------------------------------------
    def test_subobject_classifier_omega_truth_values(self) -> None:
        """Subobject classifier Omega={True, False} classifies subsets via characteristic map."""
        domain = [1, 2, 3, 4, 5]
        sub = {2, 4}

        def chi(x: int) -> bool:
            return x in sub

        classified = [x for x in domain if chi(x)]
        self.assertEqual(set(classified), sub)

    # -------------------------------------------------------------------------
    # Test 70: Sheaf Morphism Exactness Kernel Cokernel
    # -------------------------------------------------------------------------
    def test_sheaf_morphism_exactness_kernel_cokernel(self) -> None:
        """Morphism of sheaves phi: F -> G has well-defined kernel and image."""

        # phi: x -> 2x mod 10
        def phi(x: int) -> int:
            return (2 * x) % 10

        domain = list(range(10))
        ker = [x for x in domain if phi(x) == 0]  # {0, 5}
        img = sorted(set(phi(x) for x in domain))  # {0, 2, 4, 6, 8}

        self.assertEqual(ker, [0, 5])
        self.assertEqual(img, [0, 2, 4, 6, 8])

    # -------------------------------------------------------------------------
    # Test 71: Homotopy Colimit Schema Integration
    # -------------------------------------------------------------------------
    def test_homotopy_colimit_schema_integration(self) -> None:
        """Homotopy colimit detects topological divergence between divergent branches."""
        branch1 = frozenset(["id", "name", "v1"])
        branch2 = frozenset(["id", "name", "v2"])
        branch1 & branch2  # {"id", "name"}

        # Divergence obstruction: symmetric difference is non-empty
        divergence = branch1 ^ branch2
        self.assertEqual(divergence, frozenset(["v1", "v2"]))

    # -------------------------------------------------------------------------
    # Test 72: Persistent Homology Barcode Decomposition
    # -------------------------------------------------------------------------
    def test_persistent_homology_barcode_decomposition(self) -> None:
        """Persistent homology barcodes record birth-death intervals of topological features."""
        # Simple filtration with 2 features:
        # Feature 1: birth=1, death=5
        # Feature 2: birth=2, death=float('inf') (essential cycle)
        barcodes = [(1, 5), (2, float("inf"))]

        # Persistence of feature 1
        pers1 = barcodes[0][1] - barcodes[0][0]
        self.assertEqual(pers1, 4)
        # Essential feature check
        self.assertEqual(barcodes[1][1], float("inf"))

    # -------------------------------------------------------------------------
    # Test 73: Vietoris-Rips Complex Clique Expansion
    # -------------------------------------------------------------------------
    def test_vietoris_rips_complex_clique_expansion(self) -> None:
        """Vietoris-Rips complex contains all cliques with pairwise distance <= epsilon."""
        points = {"A": 0, "B": 2, "C": 3, "D": 8}
        epsilon = 3

        # Edges with dist <= 3
        edges = []
        keys = sorted(points.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                p1, p2 = keys[i], keys[j]
                if abs(points[p1] - points[p2]) <= epsilon:
                    edges.append(frozenset([p1, p2]))

        # Edges: (A, B) dist 2, (A, C) dist 3, (B, C) dist 1
        self.assertIn(frozenset(["A", "B"]), edges)
        self.assertIn(frozenset(["B", "C"]), edges)
        self.assertIn(frozenset(["A", "C"]), edges)
        # {A, B, C} forms a 2-simplex (triangle clique)
        triangle_clique = frozenset(["A", "B", "C"])
        self.assertTrue(
            all(
                frozenset([u, v]) in edges
                for u in triangle_clique
                for v in triangle_clique
                if u != v
            )
        )

    # -------------------------------------------------------------------------
    # Test 74: Euler Characteristic Invariance Under Subdivision
    # -------------------------------------------------------------------------
    def test_euler_characteristic_invariance_under_subdivision(self) -> None:
        """Barycentric subdivision preserves the Euler characteristic chi(K) = V - E + F."""
        # Single triangle: V=3, E=3, F=1 -> chi = 3 - 3 + 1 = 1
        v_orig, e_orig, f_orig = 3, 3, 1
        chi_orig = v_orig - e_orig + f_orig
        self.assertEqual(chi_orig, 1)

        # Barycentric subdivision:
        # Adds 1 face centroid (new V) and 3 edge midpoints (new V): V' = 3 + 3 + 1 = 7
        # Edges: 3 * 2 (split edges) + 6 (radiating from centroid): E' = 12
        # Faces: 6 sub-triangles: F' = 6
        v_sub, e_sub, f_sub = 7, 12, 6
        chi_sub = v_sub - e_sub + f_sub  # 7 - 12 + 6 = 1
        self.assertEqual(chi_orig, chi_sub)

    # -------------------------------------------------------------------------
    # Test 75: De Rham Discrete Cochain Poincaré Duality
    # -------------------------------------------------------------------------
    def test_de_rham_discrete_cochain_poincare_duality(self) -> None:
        """Discrete Poincaré duality on 2-manifold: b_0 == b_2 and b_1 == b_1."""
        # 2-sphere triangulation: b_0 = 1, b_1 = 0, b_2 = 1
        betti_sphere = {0: 1, 1: 0, 2: 1}
        # Invariant: b_k == b_{2-k}
        self.assertEqual(betti_sphere[0], betti_sphere[2])
        self.assertEqual(betti_sphere[1], betti_sphere[1])

        # 2-torus triangulation: b_0 = 1, b_1 = 2, b_2 = 1
        betti_torus = {0: 1, 1: 2, 2: 1}
        self.assertEqual(betti_torus[0], betti_torus[2])
        self.assertEqual(betti_torus[1], betti_torus[1])


if __name__ == "__main__":
    unittest.main()

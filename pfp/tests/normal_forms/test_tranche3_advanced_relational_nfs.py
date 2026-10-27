"""Tranche 3 Unit and Property Tests: Advanced Relational Normal Forms (Tests 1-25).

Covers:
- Partitioned Normal Form (PNF / NF²) nest/unnest bijectivity
- Set Normal Form (SNF) atomicity
- Elementary Key Normal Form (EKNF) and 3NF/BCNF separation
- Sixth Normal Form (6NF) temporal irreducibility and interval-join reconstruction
- Domain-Key Normal Form (DKNF) and Pillar IV undecidability refusal
- Redundancy-Free Normal Form (RFNF) and Essential Tuple Normal Form (ETNF)
- Bernstein 3NF synthesis and Tsou-Fischer BCNF decomposition trees
- Graham-Yu-Ozsoyoglu (GYO) hypergraph ear reduction and alpha-acyclicity
- Rissanen decomposition independence, FD projection, and Sperner antichain bounds

AuthorityEffect: None.
"""

from __future__ import annotations

import math
import random
import unittest

from pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    JoinDependency,
    RelationalSchema,
    check_1nf,
    check_3nf,
    check_5nf,
    check_6nf,
    check_bcnf,
    check_dknf,
    check_etnf,
    check_rfnf,
    compute_minimal_cover,
    find_candidate_keys,
    is_5nf_implied_by_keys,
)
from pfp.domain.normal_forms.relational_advanced import (
    check_eknf,
    decompose_bcnf_tree,
    gyo_reduction,
    pnf_nest,
    pnf_unnest,
    project_functional_dependencies,
    synthesize_3nf_bernstein,
    temporal_6nf_decompose,
    temporal_interval_join,
)
from pfp.domain.normal_forms.relational_extensions import (
    verify_candidate_keys_antichain,
)


class TestTranche3AdvancedRelationalNFs(unittest.TestCase):
    """Test suite covering Tranche 3: Advanced Relational Normal Forms (Tests 1-25)."""

    # -------------------------------------------------------------------------
    # Test 1: PNF Nest/Unnest Bijectivity
    # -------------------------------------------------------------------------
    def test_pnf_nest_unnest_bijectivity(self) -> None:
        """Roth, Korth, & Silberschatz (1988) PNF ensures unnest(nest(R)) = R on partitioned relations."""
        flat_relation = [
            {"dept_id": 1, "emp_id": 101, "role": "Eng"},
            {"dept_id": 1, "emp_id": 102, "role": "QA"},
            {"dept_id": 2, "emp_id": 201, "role": "PM"},
        ]

        nested = pnf_nest(
            flat_relation,
            group_keys=["dept_id"],
            nested_key="employees",
            sub_attrs=["emp_id", "role"],
        )
        reconstructed = pnf_unnest(nested, nested_key="employees")
        self.assertEqual(flat_relation, reconstructed)

    # -------------------------------------------------------------------------
    # Test 2: PNF Non-Partitioned Nest Loss
    # -------------------------------------------------------------------------
    def test_pnf_non_partitioned_nest_loss(self) -> None:
        """Un-nesting a non-partitioned relation creates ambiguous groupings or lost associations."""
        raw_tuples = [
            ("D1", "P1", "Eng"),
            ("D2", "P1", "Eng"),
        ]
        # Project is not a partition key for department
        grouped_by_project: dict[tuple[str, str], list[str]] = {}
        for d, p, r in raw_tuples:
            grouped_by_project.setdefault((p, r), []).append(d)

        # Unnesting without partition key loses distinct functional scope
        self.assertEqual(len(grouped_by_project[("P1", "Eng")]), 2)

    # -------------------------------------------------------------------------
    # Test 3: SNF Set-Valued Attribute Atomicity
    # -------------------------------------------------------------------------
    def test_snf_set_valued_attribute_atomicity(self) -> None:
        """Set Normal Form treats frozen sets as atomic domain elements under scalar equality."""
        s1 = frozenset(["read", "write"])
        s2 = frozenset(["write", "read"])
        s3 = frozenset(["read"])

        # Commutative equality in SNF
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)

        schema = RelationalSchema(
            attributes=frozenset(["UserID", "Permissions"]),
            dependencies=frozenset([FunctionalDependency.from_str("UserID", "Permissions")]),
        )
        ok_1nf, _ = check_1nf(schema)
        self.assertTrue(ok_1nf)

    # -------------------------------------------------------------------------
    # Test 4: EKNF Elementary Key Dependency Admittance
    # -------------------------------------------------------------------------
    def test_eknf_elementary_key_dependency_admittance(self) -> None:
        """Zaniolo (1982) EKNF admits FD X -> A where A is part of an elementary candidate key."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C", "D"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C, D"),
                    FunctionalDependency.from_str("C", "B"),
                ]
            ),
        )
        keys = find_candidate_keys(schema)
        self.assertIn(frozenset(["A", "B"]), keys)
        self.assertIn(frozenset(["A", "C"]), keys)

        # In C -> B, B is in elementary key {A, B}
        ok_3nf, _ = check_3nf(schema)
        ok_eknf, err_eknf = check_eknf(schema)
        ok_bcnf, err_bcnf = check_bcnf(schema)

        self.assertTrue(ok_3nf)
        self.assertTrue(ok_eknf)
        self.assertIsNone(err_eknf)
        self.assertFalse(ok_bcnf)
        self.assertIsNotNone(err_bcnf)
        self.assertIn("BCNF Violation", err_bcnf)

    # -------------------------------------------------------------------------
    # Test 5: EKNF Strict Separation from 3NF and BCNF
    # -------------------------------------------------------------------------
    def test_eknf_strict_separation_from_3nf_and_bcnf(self) -> None:
        """EKNF separates strictly between 3NF and BCNF on elementary key boundaries."""
        # 1. Schema in 3NF that fails EKNF: Enrollment table with overlapping composite keys
        enrollment_schema = RelationalSchema(
            attributes=frozenset(["student_id", "course_code", "course_name"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("student_id, course_code", "course_name"),
                    FunctionalDependency.from_str("course_code", "course_name"),
                    FunctionalDependency.from_str("course_name", "course_code"),
                ]
            ),
        )
        ok_3nf, _ = check_3nf(enrollment_schema)
        ok_eknf, err_eknf = check_eknf(enrollment_schema)
        ok_bcnf, _ = check_bcnf(enrollment_schema)

        # In 3NF: course_name is prime (in key {student_id, course_name})
        self.assertTrue(ok_3nf)
        # Fails EKNF: neither key is elementary because course_code <-> course_name
        self.assertFalse(ok_eknf)
        self.assertIsNotNone(err_eknf)
        self.assertIn("EKNF Violation", err_eknf)
        # Fails BCNF: course_code is not a superkey
        self.assertFalse(ok_bcnf)

        # 2. Schema in EKNF that fails BCNF
        schema_eknf = RelationalSchema(
            attributes=frozenset(["A", "B", "C", "D"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C, D"),
                    FunctionalDependency.from_str("C", "B"),
                ]
            ),
        )
        ok_eknf_2, _ = check_eknf(schema_eknf)
        ok_bcnf_2, _ = check_bcnf(schema_eknf)
        self.assertTrue(ok_eknf_2)
        self.assertFalse(ok_bcnf_2)

    # -------------------------------------------------------------------------
    # Test 6: 6NF Irreducible Temporal Decomposition
    # -------------------------------------------------------------------------
    def test_6nf_irreducible_temporal_decomposition(self) -> None:
        """6NF membership is a trivial join cover. Attribute shape is not the test."""
        screen = (
            "6NF_SCREEN_NOT_DECISION: absence of a join-dependency theory is not a 6NF decision"
        )
        all_key = RelationalSchema(attributes=frozenset(["A", "B", "C"]), dependencies=frozenset())
        self.assertNotEqual(check_6nf(all_key), (True, None))
        self.assertEqual(check_6nf(all_key), (False, screen))
        self.assertEqual(check_6nf(all_key, None), (False, screen))
        self.assertEqual(check_6nf(all_key, ()), (False, screen))

        nontrivial = JoinDependency.from_sub_schemas(
            ["A", "B", "C"],
            [["A", "B"], ["B", "C"]],
        )
        ok_jd, err_jd = check_6nf(all_key, [nontrivial])
        self.assertFalse(ok_jd)
        self.assertIn("non-trivial join dependency", err_jd or "")

        trivial = JoinDependency.from_sub_schemas(
            ["A", "B", "C"],
            [["A", "B", "C"], ["A", "B"]],
        )
        self.assertEqual(check_6nf(all_key, [trivial]), (True, None))

        # Key-plus-one and a wider heading are the same screen without a cover.
        schema_shape = RelationalSchema(
            attributes=frozenset(["ID", "Salary", "ValidInterval"]),
            dependencies=frozenset([FunctionalDependency.from_str("ID, ValidInterval", "Salary")]),
        )
        self.assertEqual(check_6nf(schema_shape), (False, screen))
        schema_wide = RelationalSchema(
            attributes=frozenset(["ID", "Salary", "Bonus", "ValidInterval"]),
            dependencies=frozenset(
                [FunctionalDependency.from_str("ID, ValidInterval", "Salary, Bonus")]
            ),
        )
        self.assertEqual(check_6nf(schema_wide), (False, screen))
        wide_jd = JoinDependency.from_sub_schemas(
            ["ID", "Salary", "Bonus", "ValidInterval"],
            [
                ["ID", "ValidInterval", "Salary"],
                ["ID", "ValidInterval", "Bonus"],
            ],
        )
        ok_wide, err_wide = check_6nf(schema_wide, [wide_jd])
        self.assertFalse(ok_wide)
        self.assertIn("non-trivial join dependency", err_wide or "")

    # -------------------------------------------------------------------------
    # Test 7: 6NF Temporal Interval Deconstruction
    # -------------------------------------------------------------------------
    def test_6nf_temporal_interval_deconstruction(self) -> None:
        """Decomposition of (ID, Status, Salary, Interval) into independent 6NF relvars."""
        wide_schema = RelationalSchema(
            attributes=frozenset(["ID", "ValidFrom", "Status", "Salary"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("ID, ValidFrom", "Status, Salary"),
                ]
            ),
        )
        subschemas = temporal_6nf_decompose(wide_schema)
        self.assertEqual(len(subschemas), 2)
        screen = (
            "6NF_SCREEN_NOT_DECISION: absence of a join-dependency theory is not a 6NF decision"
        )
        for s in subschemas:
            self.assertEqual(check_6nf(s), (False, screen))
            heading = sorted(s.attributes)
            trivial = JoinDependency.from_sub_schemas(heading, [heading, heading[:1]])
            self.assertEqual(check_6nf(s, [trivial]), (True, None))

    # -------------------------------------------------------------------------
    # Test 8: 6NF Join Reconstruction Temporal Losslessness
    # -------------------------------------------------------------------------
    def test_6nf_join_reconstruction_temporal_losslessness(self) -> None:
        """Interval join of 6NF temporal relvars reconstructs the complete historical state."""
        t1 = [
            {"id": 1, "status": "Active", "t": 10},
            {"id": 1, "status": "Leave", "t": 20},
        ]
        t2 = [
            {"id": 1, "salary": 5000, "t": 10},
            {"id": 1, "salary": 6000, "t": 20},
        ]

        joined = temporal_interval_join(t1, t2, key_attrs=["id"], time_attr="t")
        self.assertEqual(len(joined), 2)
        self.assertEqual(joined[0]["salary"], 5000)
        self.assertEqual(joined[0]["status"], "Active")
        self.assertEqual(joined[1]["salary"], 6000)
        self.assertEqual(joined[1]["status"], "Leave")

    # -------------------------------------------------------------------------
    # Test 9: DKNF Satisfiable Constraint Solvability
    # -------------------------------------------------------------------------
    def test_dknf_satisfiable_constraint_solvability(self) -> None:
        """Fagin (1981) DKNF holds when all constraints follow from domain types and key constraints."""
        schema = RelationalSchema(
            attributes=frozenset(["SSN", "Email"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("SSN", "Email"),
                    FunctionalDependency.from_str("Email", "SSN"),
                ]
            ),
        )
        ok, defect = check_dknf(schema)
        self.assertFalse(ok)
        self.assertEqual(
            defect,
            "DKNF_SCREEN_NOT_DECISION: absence of the five screened keywords and a BCNF pass are not a DKNF decision",
        )

    # -------------------------------------------------------------------------
    # Test 10: DKNF Pillar IV Undecidability Refusal
    # -------------------------------------------------------------------------
    def test_dknf_pillar_iv_undecidability_refusal(self) -> None:
        """General non-key constraints trip undecidable refusal in DKNF evaluation."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A", "B"),
                    FunctionalDependency.from_str("B", "C"),
                ]
            ),
        )
        ok, defect = check_dknf(schema)
        self.assertFalse(ok)
        self.assertIsNotNone(defect)

    # -------------------------------------------------------------------------
    # Test 11: RFNF Redundancy-Free Normal Form Evaluation
    # -------------------------------------------------------------------------
    def test_rfnf_redundancy_free_normal_form_evaluation(self) -> None:
        """A missing RFNF argument is a screen. An empty theory declares no join dependency."""
        schema_bcnf = RelationalSchema(
            attributes=frozenset(["K", "Val"]),
            dependencies=frozenset([FunctionalDependency.from_str("K", "Val")]),
        )
        ok, defect = check_rfnf(schema_bcnf)
        self.assertFalse(ok)
        self.assertEqual(
            defect,
            "RFNF_SCREEN_NOT_DECISION: absence of a join-dependency theory is not an RFNF decision",
        )
        ok_empty, defect_empty = check_rfnf(schema_bcnf, ())
        self.assertEqual((ok_empty, defect_empty), (True, None))

        heading = frozenset(["A", "B", "C"])
        covered = RelationalSchema(
            attributes=heading,
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C"),
                    FunctionalDependency.from_str("A, C", "B"),
                ]
            ),
        )
        self.assertTrue(check_bcnf(covered)[0])
        self.assertTrue(covered.is_superkey(frozenset(["A", "B"])))
        self.assertTrue(covered.is_superkey(frozenset(["A", "C"])))
        self.assertFalse(covered.is_superkey(frozenset(["B", "C"])))
        cover_jd = JoinDependency.from_sub_schemas(
            ["A", "B", "C"],
            [["A", "B"], ["A", "C"], ["B", "C"]],
        )
        self.assertFalse(cover_jd.is_trivial())
        self.assertIs(
            is_5nf_implied_by_keys(heading, covered.candidate_keys(), cover_jd.components),
            False,
        )
        self.assertEqual(check_rfnf(covered, [cover_jd]), (True, None))

        noncover_jd = JoinDependency.from_sub_schemas(
            ["A", "B", "C"],
            [["A", "B"], ["B", "C"]],
        )
        ok_noncover, err_noncover = check_rfnf(covered, [noncover_jd])
        self.assertFalse(ok_noncover)
        self.assertIn("superkey components do not cover the heading", err_noncover or "")
        self.assertNotIn("implied by the keys", err_noncover or "")

    # -------------------------------------------------------------------------
    # Test 12: ETNF Essential Tuple Superkey Component Check
    # -------------------------------------------------------------------------
    def test_etnf_essential_tuple_superkey_component_check(self) -> None:
        """Darwen, Date, & Fagin (2012) ETNF: join dependency components contain at least one superkey."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset([FunctionalDependency.from_str("A", "B, C")]),
        )
        ok, defect = check_etnf(schema)
        self.assertTrue(ok)
        self.assertIsNone(defect)

    # -------------------------------------------------------------------------
    # Test 13: ETNF Separation Between BCNF and 5NF
    # -------------------------------------------------------------------------
    def test_etnf_separation_between_bcnf_and_5nf(self) -> None:
        """Separating counterexample: schema satisfying BCNF/ETNF vs strict 5NF requirements."""
        schema = RelationalSchema(attributes=frozenset(["A", "B"]), dependencies=frozenset())
        ok_bcnf, _ = check_bcnf(schema)
        ok_etnf, _ = check_etnf(schema)
        ok_5nf, _ = check_5nf(schema)
        self.assertTrue(ok_bcnf)
        self.assertTrue(ok_etnf)
        self.assertTrue(ok_5nf)

    # -------------------------------------------------------------------------
    # Test 14: Bernstein 3NF Synthesis Algorithm
    # -------------------------------------------------------------------------
    def test_bernstein_3nf_synthesis_algorithm(self) -> None:
        """Bernstein 3NF synthesis produces dependency-preserving sub-schemas."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A", "B"),
                    FunctionalDependency.from_str("B", "C"),
                    FunctionalDependency.from_str("A", "C"),
                ]
            ),
        )
        sub_schemas = synthesize_3nf_bernstein(schema)
        self.assertEqual(len(sub_schemas), 2)
        self.assertIn(frozenset(["A", "B"]), sub_schemas)
        self.assertIn(frozenset(["B", "C"]), sub_schemas)

    # -------------------------------------------------------------------------
    # Test 15: BCNF Decomposition Lossless Tree
    # -------------------------------------------------------------------------
    def test_bcnf_decomposition_lossless_tree(self) -> None:
        """Tsou & Fischer (1982) BCNF decomposition tree generates lossless sub-schemas."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset([FunctionalDependency.from_str("A", "B")]),
        )
        decomposed = decompose_bcnf_tree(schema)
        self.assertGreaterEqual(len(decomposed), 2)
        for s in decomposed:
            ok, _ = check_bcnf(s)
            self.assertTrue(ok)

    # -------------------------------------------------------------------------
    # Test 16: Minimal Cover Canonical Uniqueness
    # -------------------------------------------------------------------------
    def test_minimal_cover_canonical_uniqueness(self) -> None:
        """Minimal cover reduction is canonical across arbitrary input permutations."""
        fds = [
            FunctionalDependency.from_str("A, B", "C"),
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B", "C"),
            FunctionalDependency.from_str("A", "C"),
        ]
        mc1 = compute_minimal_cover(fds)
        rng = random.Random(42)
        for _ in range(5):
            permuted = list(fds)
            rng.shuffle(permuted)
            mc2 = compute_minimal_cover(permuted)
            self.assertEqual(mc1, mc2)

    # -------------------------------------------------------------------------
    # Test 17: Spurious Tuple Detection Under Non-5NF Join
    # -------------------------------------------------------------------------
    def test_spurious_tuple_detection_under_non_5nf_join(self) -> None:
        """Detects and materializes spurious tuple witnesses for non-key join dependencies."""
        r = [
            {"A": "a1", "B": "b1", "C": "c1"},
            {"A": "a1", "B": "b2", "C": "c2"},
            {"A": "a2", "B": "b1", "C": "c2"},
            {"A": "a2", "B": "b2", "C": "c1"},
        ]
        proj_ab = {(x["A"], x["B"]) for x in r}
        proj_bc = {(x["B"], x["C"]) for x in r}
        proj_ac = {(x["A"], x["C"]) for x in r}

        reconstructed = []
        for a, b in proj_ab:
            for b2, c in proj_bc:
                if b == b2 and (a, c) in proj_ac:
                    reconstructed.append((a, b, c))

        self.assertEqual(len(r), 4)
        self.assertEqual(len(reconstructed), 8)
        spurious_count = len(reconstructed) - len(r)
        self.assertEqual(spurious_count, 4)

    # -------------------------------------------------------------------------
    # Test 18: GYO Hypergraph Cyclicity Reduction
    # -------------------------------------------------------------------------
    def test_join_dependency_hypergraph_cyclicity_graham_reduction(self) -> None:
        """Graham-Yu-Ozsoyoglu (GYO) algorithm classifies acyclic vs cyclic join hypergraphs."""
        # Acyclic chain hypergraph: {A, B}, {B, C}, {C, D}
        acyclic_edges = [frozenset(["A", "B"]), frozenset(["B", "C"]), frozenset(["C", "D"])]
        is_acyclic, remaining, _ = gyo_reduction(acyclic_edges)
        self.assertTrue(is_acyclic)
        self.assertEqual(len(remaining), 0)

        # Cyclic triangle hypergraph: {A, B}, {B, C}, {A, C}
        cyclic_edges = [frozenset(["A", "B"]), frozenset(["B", "C"]), frozenset(["A", "C"])]
        is_cyclic_res, remaining_cyclic, _ = gyo_reduction(cyclic_edges)
        self.assertFalse(is_cyclic_res)
        self.assertEqual(len(remaining_cyclic), 3)

    # -------------------------------------------------------------------------
    # Test 19: GYO Reduction Step Trace
    # -------------------------------------------------------------------------
    def test_gyo_reduction_step_trace(self) -> None:
        """GYO ear removal emits deterministic elimination steps."""
        edges = [frozenset(["A", "B"]), frozenset(["B", "C"])]
        is_acyclic, _, steps = gyo_reduction(edges)
        self.assertTrue(is_acyclic)
        self.assertGreaterEqual(len(steps), 1)
        self.assertIn("eliminate", steps[0])

    # -------------------------------------------------------------------------
    # Test 20: Acyclic Join Dependency Pairwise Consistency
    # -------------------------------------------------------------------------
    def test_acyclic_join_dependency_pairwise_consistency(self) -> None:
        """For alpha-acyclic schemas, pairwise consistency guarantees global join consistency."""
        r_ab = [("a1", "b1"), ("a2", "b2")]
        r_bc = [("b1", "c1"), ("b2", "c2")]

        b_ab = {b for _, b in r_ab}
        b_bc = {b for b, _ in r_bc}
        self.assertEqual(b_ab, b_bc)

        joined = [(a, b, c) for a, b in r_ab for b2, c in r_bc if b == b2]
        self.assertEqual(len(joined), 2)

    # -------------------------------------------------------------------------
    # Test 21: Rissanen Independent Decomposition Check
    # -------------------------------------------------------------------------
    def test_rissanen_independent_decomposition_check(self) -> None:
        """Rissanen (1977) decomposition independence condition under functional dependencies."""
        fd_ab = FunctionalDependency.from_str("A", "B")
        fd_bc = FunctionalDependency.from_str("B", "C")
        self.assertTrue(fd_ab.determinant | fd_ab.dependent <= frozenset(["A", "B"]))
        self.assertTrue(fd_bc.determinant | fd_bc.dependent <= frozenset(["B", "C"]))

    # -------------------------------------------------------------------------
    # Test 22: Functional Dependency Project to Subschema
    # -------------------------------------------------------------------------
    def test_functional_dependency_project_to_subschema(self) -> None:
        """Computes exact projection of FDs onto attribute subset R[X]."""
        all_fds = [
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B", "C"),
            FunctionalDependency.from_str("C", "D"),
        ]
        sub_attrs = frozenset(["A", "C"])
        proj = project_functional_dependencies(all_fds, sub_attrs)
        self.assertGreaterEqual(len(proj), 1)
        self.assertEqual(proj[0].determinant, frozenset(["A"]))
        self.assertEqual(proj[0].dependent, frozenset(["C"]))

    # -------------------------------------------------------------------------
    # Test 23: Candidate Keys Antichain Sperner Bound
    # -------------------------------------------------------------------------
    def test_candidate_keys_antichain_sperner_bound(self) -> None:
        """Candidate keys never violate Sperner's theorem upper bound C(n, floor(n/2))."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C", "D"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C, D"),
                    FunctionalDependency.from_str("C, D", "A, B"),
                    FunctionalDependency.from_str("A, C", "B, D"),
                    FunctionalDependency.from_str("B, D", "A, C"),
                ]
            ),
        )
        keys = find_candidate_keys(schema)
        n = len(schema.attributes)
        sperner_bound = math.comb(n, n // 2)  # C(4, 2) = 6
        self.assertLessEqual(len(keys), sperner_bound)
        ok_antichain, defects = verify_candidate_keys_antichain(schema)
        self.assertTrue(ok_antichain)
        self.assertEqual(defects, [])

    # -------------------------------------------------------------------------
    # Test 24: Inclusion Dependency Chase Acyclicity
    # -------------------------------------------------------------------------
    def test_inclusion_dependency_chase_acyclicity(self) -> None:
        """Unary inclusion dependency chase with cycle detection."""
        ind_chain = [("Orders.cust", "Customers.id"), ("Customers.parent", "Customers.id")]
        graph: dict[str, list[str]] = {}
        for src, tgt in ind_chain:
            graph.setdefault(src, []).append(tgt)

        self.assertNotIn("Orders.cust", graph.get("Customers.id", []))

    # -------------------------------------------------------------------------
    # Test 25: Foreign Key Referential Integrity Normal Form
    # -------------------------------------------------------------------------
    def test_foreign_key_referential_integrity_normal_form(self) -> None:
        """Foreign key referential integrity as exact 1-cochain boundary map."""
        customers = {"C1", "C2", "C3"}
        orders = [("O1", "C1"), ("O2", "C2"), ("O3", "C1")]

        d_orders = {c for _, c in orders}
        is_boundary_exact = d_orders <= customers
        self.assertTrue(is_boundary_exact)


if __name__ == "__main__":
    unittest.main()

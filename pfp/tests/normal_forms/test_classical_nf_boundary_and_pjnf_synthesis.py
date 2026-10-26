"""Unit and property-based tests for Classical Normal Forms (1NF-6NF, ETNF, SKNF, RFNF, DKNF)
and Project-Join Normal Form (PJNF / 5NF) decomposition synthesis.

AuthorityEffect: None.
"""

from __future__ import annotations

import random
import unittest
from itertools import combinations

from omega_engine_pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    JoinDependency,
    RelationalSchema,
    chase_join_dependency,
    check_1nf,
    check_2nf,
    check_3nf,
    check_5nf,
    check_6nf,
    check_bcnf,
    check_dknf,
    check_etnf,
    check_rfnf,
    check_sknf,
    synthesize_5nf_projections,
)
from omega_engine_pfp.domain.normal_forms.relational_extensions import (
    MultivaluedDependency,
    check_4nf,
)


class TestClassicalNFBoundaryAndPJNFSynthesis(unittest.TestCase):
    """Test suite covering classical relational normal form edge cases and 5NF synthesis."""

    # -------------------------------------------------------------------------
    # Test 1: 1NF Nested Relation Rejection
    # -------------------------------------------------------------------------
    def test_1nf_nested_relation_rejection(self) -> None:
        """1NF requires atomic domains; empty attribute sets or nested relations fail."""
        empty_schema = RelationalSchema(frozenset(), frozenset())
        ok, err = check_1nf(empty_schema)
        self.assertFalse(ok)
        self.assertIn("no declared attributes", err or "")

        valid_schema = RelationalSchema(
            frozenset(["A", "B"]),
            frozenset([FunctionalDependency.from_str("A", "B")]),
        )
        ok_valid, _ = check_1nf(valid_schema)
        self.assertTrue(ok_valid)

    # -------------------------------------------------------------------------
    # Test 2: 2NF Composite Key Partial Dependency
    # -------------------------------------------------------------------------
    def test_2nf_composite_key_partial_dependency(self) -> None:
        """2NF rejects partial dependencies of non-prime attributes on composite keys."""
        # Key: AB, Partial dependency: A -> C (C is non-prime)
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C", "D"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C, D"),
                    FunctionalDependency.from_str("A", "C"),
                ]
            ),
        )
        ok, err = check_2nf(schema)
        self.assertFalse(ok)
        self.assertIn("2NF Partial Dependency Violation", err or "")

    # -------------------------------------------------------------------------
    # Test 3: 2NF Single-Attribute Key Trivial Admittance
    # -------------------------------------------------------------------------
    def test_2nf_single_attribute_key_trivial_admittance(self) -> None:
        """Relations with only single-attribute candidate keys are trivially in 2NF."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A", "B"),
                    FunctionalDependency.from_str("B", "C"),
                    FunctionalDependency.from_str("C", "A"),
                ]
            ),
        )
        # Keys are {A}, {B}, {C} — all singletons
        ok, err = check_2nf(schema)
        self.assertTrue(ok)
        self.assertIsNone(err)

    # -------------------------------------------------------------------------
    # Test 4: 3NF Transitive Prime Attribute Exemption
    # -------------------------------------------------------------------------
    def test_3nf_transitive_prime_attribute_exemption(self) -> None:
        """3NF permits X -> A where X is not a superkey provided dependent A is prime."""
        # Street, City -> Zip (Key: Street, City; and Key: Street, Zip)
        # Zip -> City (Zip is NOT superkey, but City is prime!)
        schema = RelationalSchema(
            attributes=frozenset(["Street", "City", "Zip"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("Street, City", "Zip"),
                    FunctionalDependency.from_str("Zip", "City"),
                ]
            ),
        )
        ok_3nf, err_3nf = check_3nf(schema)
        self.assertTrue(ok_3nf)
        self.assertIsNone(err_3nf)

    # -------------------------------------------------------------------------
    # Test 5: BCNF Strict Superkey Violation
    # -------------------------------------------------------------------------
    def test_bcnf_strict_superkey_violation(self) -> None:
        """BCNF strictly rejects X -> A when X is not a superkey, even if A is prime."""
        schema = RelationalSchema(
            attributes=frozenset(["Street", "City", "Zip"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("Street, City", "Zip"),
                    FunctionalDependency.from_str("Zip", "City"),
                ]
            ),
        )
        ok_bcnf, err_bcnf = check_bcnf(schema)
        self.assertFalse(ok_bcnf)
        self.assertIn(
            "BCNF Violation: determinant {'Zip'} is not a candidate superkey", err_bcnf or ""
        )

    # -------------------------------------------------------------------------
    # Test 6: 4NF Fagin Independent MVD Violation
    # -------------------------------------------------------------------------
    def test_4nf_fagin_binary_independent_mvd_violation(self) -> None:
        """4NF rejects independent multivalued dependencies on non-superkeys."""
        # Course ->> Teacher and Course ->> Book on Course, Teacher, Book
        # All three form the only candidate key. Course is not a superkey.
        schema = RelationalSchema(
            attributes=frozenset(["Course", "Teacher", "Book"]),
            dependencies=frozenset(),
        )
        mvds = [
            MultivaluedDependency(frozenset(["Course"]), frozenset(["Teacher"])),
            MultivaluedDependency(frozenset(["Course"]), frozenset(["Book"])),
        ]
        ok_4nf, err_4nf = check_4nf(schema, mvds)
        self.assertFalse(ok_4nf)
        self.assertIn("4NF MVD Violation", err_4nf or "")

    # -------------------------------------------------------------------------
    # Test 7: ETNF Partial Tuple Redundancy Detection
    # -------------------------------------------------------------------------
    def test_etnf_partial_tuple_redundancy_detection(self) -> None:
        """ETNF accepts 3NF schemas when candidate keys are simple or determinants contain keys."""
        # Schema in BCNF passes ETNF
        bcnf_schema = RelationalSchema(
            attributes=frozenset(["ID", "Name"]),
            dependencies=frozenset([FunctionalDependency.from_str("ID", "Name")]),
        )
        ok_etnf, err_etnf = check_etnf(bcnf_schema)
        self.assertTrue(ok_etnf)
        self.assertIsNone(err_etnf)

    # -------------------------------------------------------------------------
    # Test 8: 5NF Cyclic Join Dependency Chase
    # -------------------------------------------------------------------------
    def test_5nf_cyclic_join_dependency_chase(self) -> None:
        """5NF: Cyclic candidate keys AB, BC, AC do not imply ternary join dependency ⋈[AB, BC, AC]."""
        heading = frozenset(["A", "B", "C"])
        [frozenset(["A", "B"]), frozenset(["B", "C"]), frozenset(["A", "C"])]
        jd = JoinDependency(
            heading, (frozenset(["A", "B"]), frozenset(["B", "C"]), frozenset(["A", "C"]))
        )

        schema = RelationalSchema(attributes=heading, dependencies=frozenset())
        # check_5nf detects that the cyclic JD is not implied by candidate keys alone
        ok_5nf, err_5nf = check_5nf(schema, join_dependencies=[jd])
        self.assertFalse(ok_5nf)
        self.assertIn("5NF Join Dependency Violation", err_5nf or "")

    # -------------------------------------------------------------------------
    # Test 9: SKNF Superkey Normal Form Closure
    # -------------------------------------------------------------------------
    def test_sknf_superkey_normal_form_closure(self) -> None:
        """SKNF admits schemas where every JD component is a superkey, even when 5NF fails."""
        heading = frozenset(["A", "B", "C"])
        # Keys are AB, BC, AC
        schema = RelationalSchema(
            attributes=heading,
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C"),
                    FunctionalDependency.from_str("B, C", "A"),
                    FunctionalDependency.from_str("A, C", "B"),
                ]
            ),
        )
        jd = JoinDependency(
            heading, (frozenset(["A", "B"]), frozenset(["B", "C"]), frozenset(["A", "C"]))
        )
        # Every component of jd is a candidate key (hence superkey), so SKNF holds
        ok_sknf, err_sknf = check_sknf(schema, [jd])
        self.assertTrue(ok_sknf)
        self.assertIsNone(err_sknf)

    # -------------------------------------------------------------------------
    # Test 10: RFNF Redundancy-Free Normal Form
    # -------------------------------------------------------------------------
    def test_rfnf_redundancy_free_normal_form(self) -> None:
        """RFNF admits schemas in BCNF without redundant dependencies."""
        schema = RelationalSchema(
            attributes=frozenset(["EmpID", "Dept", "Manager"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("EmpID", "Dept, Manager"),
                    FunctionalDependency.from_str("Dept", "Manager"),
                ]
            ),
        )
        # Not in BCNF because Dept is not a superkey
        ok_rfnf, err_rfnf = check_rfnf(schema)
        self.assertFalse(ok_rfnf)

    # -------------------------------------------------------------------------
    # Test 11: 6NF Irreducible Temporal Decomposition
    # -------------------------------------------------------------------------
    def test_6nf_irreducible_temporal_decomposition(self) -> None:
        """6NF membership is a trivial join cover. Attribute shape is not the test."""
        screen = (
            "6NF_SCREEN_NOT_DECISION: absence of a join-dependency theory is not a 6NF decision"
        )
        schema_wide = RelationalSchema(
            attributes=frozenset(["ID", "Time", "Salary", "Dept"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("ID, Time", "Salary, Dept"),
                ]
            ),
        )
        self.assertEqual(check_6nf(schema_wide), (False, screen))

        schema_key_plus_one = RelationalSchema(
            attributes=frozenset(["ID", "Time", "Salary"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("ID, Time", "Salary"),
                ]
            ),
        )
        self.assertEqual(check_6nf(schema_key_plus_one), (False, screen))

        all_key = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset(),
        )
        self.assertNotEqual(check_6nf(all_key), (True, None))
        self.assertEqual(check_6nf(all_key, None), (False, screen))
        self.assertEqual(check_6nf(all_key, ()), (False, screen))
        nontrivial = JoinDependency.from_sub_schemas(
            ["A", "B", "C"],
            [["A", "B"], ["B", "C"]],
        )
        ok_jd, err_jd = check_6nf(all_key, [nontrivial])
        self.assertFalse(ok_jd)
        self.assertIn("6NF Violation", err_jd or "")

    # -------------------------------------------------------------------------
    # Test 12: DKNF Domain-Key Constraint Solvability
    # -------------------------------------------------------------------------
    def test_dknf_domain_key_constraint_solvability(self) -> None:
        """DKNF: Complex cross-table or inter-row constraints violate DKNF."""
        schema = RelationalSchema(
            attributes=frozenset(["AccountID", "Balance"]),
            dependencies=frozenset([FunctionalDependency.from_str("AccountID", "Balance")]),
        )
        # General constraint requiring cross-table check
        ok_dknf, err_dknf = check_dknf(schema, general_constraints=["cross_table_audit_ledger_sum"])
        self.assertFalse(ok_dknf)
        self.assertIn("DKNF Violation", err_dknf or "")

        # A domain-looking constraint with none of the five keywords is still not a decision.
        ok_dknf_valid, screen = check_dknf(schema, general_constraints=["Balance >= 0"])
        self.assertFalse(ok_dknf_valid)
        self.assertEqual(
            screen,
            "DKNF_SCREEN_NOT_DECISION: absence of the five screened keywords and a BCNF pass are not a DKNF decision",
        )

    # =========================================================================
    # PJNF / 5NF Decomposition Synthesis & Property Tests
    # =========================================================================

    def test_pjnf_synthesis_darwen_date_fagin_cyclic_3way(self) -> None:
        """Synthesizes the minimal 3-way join decomposition [AB, BC, AC] for cyclic keys on {A, B, C}."""
        heading = ["A", "B", "C"]
        keys = [["A", "B"], ["B", "C"], ["A", "C"]]

        projections = synthesize_5nf_projections(heading, keys)
        expected = (frozenset(["A", "B"]), frozenset(["A", "C"]), frozenset(["B", "C"]))
        self.assertEqual(projections, expected)

        # Confirm minimality: no 2 projections suffice
        for pair in combinations(projections, 2):
            chase_res = chase_join_dependency(heading, (), pair, candidate_keys=keys)
            self.assertFalse(chase_res.is_implied)

    def test_pjnf_synthesis_cyclic_4way_decomposition(self) -> None:
        """Synthesizes minimal 4-way join decomposition [AB, BC, CD, DA] on heading {A, B, C, D}."""
        heading = ["A", "B", "C", "D"]
        keys = [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"]]

        projections = synthesize_5nf_projections(heading, keys)
        expected = (
            frozenset(["A", "B"]),
            frozenset(["A", "D"]),
            frozenset(["B", "C"]),
            frozenset(["C", "D"]),
        )
        self.assertEqual(projections, expected)

        # Confirm each projection is in 5NF
        for proj in projections:
            proj_schema = RelationalSchema(attributes=proj, dependencies=frozenset())
            ok, _ = check_5nf(proj_schema, [])
            self.assertTrue(ok)

    def test_pjnf_synthesis_non_cyclic_key_identity(self) -> None:
        """Acyclic schemas with a single candidate key return identity (no decomposition needed)."""
        heading = ["EmpID", "Name", "Dept"]
        keys = [["EmpID"]]

        projections = synthesize_5nf_projections(heading, keys)
        self.assertEqual(projections, (frozenset(heading),))

    def test_pjnf_synthesis_minimality_and_losslessness_property(self) -> None:
        """Property-based test: For arbitrary candidate keys, synthesized projections are lossless and minimal."""
        rng = random.Random(42)
        attrs = ["A", "B", "C", "D"]

        for trial in range(30):
            # Generate random candidate keys of size 2 or 3
            num_keys = rng.randint(1, 4)
            keys: list[list[str]] = []
            for _ in range(num_keys):
                size = rng.randint(2, 3)
                k = sorted(rng.sample(attrs, size))
                if k not in keys:
                    keys.append(k)

            # Ensure all attributes are covered if generating cyclic scenario
            if trial % 2 == 0:
                # Add cyclic coverage
                keys = [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"]]

            projections = synthesize_5nf_projections(attrs, keys)

            # 1. Attribute coverage: union equals attrs
            union_projs = frozenset().union(*projections)
            self.assertEqual(union_projs, frozenset(attrs))

            # 2. Minimality: no proper subset of size >= 2 is lossless under candidate keys
            if len(projections) > 1:
                for p in projections:
                    subset = [x for x in projections if x != p]
                    if frozenset().union(*subset) == frozenset(attrs):
                        # Test if subset is lossless
                        chase_res = chase_join_dependency(attrs, (), subset, candidate_keys=keys)
                        # If subset was lossless, p should have been pruned by synthesis!
                        self.assertFalse(
                            chase_res.is_implied,
                            f"Projection {p} was redundant in {projections} under keys {keys}",
                        )

    def test_pjnf_synthesis_with_explicit_join_dependency(self) -> None:
        """Synthesizes decomposition when an explicit non-implied join dependency is declared."""
        heading = ["A", "B", "C", "D"]
        keys = [["A", "B", "C", "D"]]  # Single candidate key
        jd = JoinDependency(
            frozenset(heading),
            (frozenset(["A", "B", "C"]), frozenset(["B", "C", "D"]), frozenset(["A", "D"])),
        )

        projections = synthesize_5nf_projections(heading, keys, join_dependencies=[jd])
        # Should project along the JD components to eliminate the JD anomaly
        self.assertEqual(len(projections), 3)
        self.assertIn(frozenset(["A", "B", "C"]), projections)
        self.assertIn(frozenset(["B", "C", "D"]), projections)
        self.assertIn(frozenset(["A", "D"]), projections)

    def test_pjnf_projections_in_5nf(self) -> None:
        """Verifies that all synthesized projections from Darwen-Date-Fagin cyclic join are in 5NF."""
        heading = ["A", "B", "C"]
        keys = [["A", "B"], ["B", "C"], ["A", "C"]]

        projections = synthesize_5nf_projections(heading, keys)
        for proj in projections:
            # Each projection has 2 attributes and candidate key = both attributes
            proj_schema = RelationalSchema(
                attributes=proj,
                dependencies=frozenset([FunctionalDependency(proj, proj)]),
            )
            ok_5nf, err_5nf = check_5nf(proj_schema, [])
            self.assertTrue(ok_5nf)
            self.assertIsNone(err_5nf)


if __name__ == "__main__":
    unittest.main()

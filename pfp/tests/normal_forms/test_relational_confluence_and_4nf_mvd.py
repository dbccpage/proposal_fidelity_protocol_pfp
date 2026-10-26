"""Targeted unit and property tests for Chase Confluence, 4NF MVD, Armstrong Axioms, and Candidate Key Antichains.

AuthorityEffect: None.

Tests:
1. Chase Confluence and Order-Invariance: Permuting the sequence of FD applications preserves
   tableau cell partitions and implication verdicts identically (Church-Rosser property).
2. Multivalued Dependency (MVD) Chase Evaluator & 4NF: Evaluates TGD tuple generation on
   Fagin's classical Employee-Skill-Language schema and verifies 4NF losslessness.
3. Armstrong Axiom Closure Properties: Verifies reflexivity, idempotence, monotonicity,
   augmentation, and transitivity across all attribute subsets.
4. Candidate Key Antichain Minimality: Verifies that candidate keys form strict antichains
   with zero proper supersets or redundant components.
"""

from __future__ import annotations

import random
import unittest

from omega_engine_pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    RelationalSchema,
    chase_join_dependency,
)
from omega_engine_pfp.domain.normal_forms.relational_extensions import (
    MultivaluedDependency,
    chase_mvd,
    chase_tableau_cell_partition,
    check_4nf,
    verify_armstrong_closure_axioms,
    verify_candidate_keys_antichain,
)


class TestChaseConfluenceAndOrderInvariance(unittest.TestCase):
    """Verifies confluence / order-invariance of the relational chase under EGD rewriting."""

    def test_diamond_fd_confluence(self) -> None:
        """Diamond dependency topology: A -> B, A -> C, B -> D, C -> D on heading ABCD.
        Permuting the order of evaluating [B -> D] before [A -> B] versus after
        must arrive at the identical final cell partition.
        """
        heading = ["A", "B", "C", "D"]
        components = [["A"], ["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]]

        fd1 = FunctionalDependency.from_str("A", "B")
        fd2 = FunctionalDependency.from_str("A", "C")
        fd3 = FunctionalDependency.from_str("B", "D")
        fd4 = FunctionalDependency.from_str("C", "D")

        order_forward = [fd1, fd2, fd3, fd4]
        order_reverse = [fd4, fd3, fd2, fd1]
        order_interleaved = [fd3, fd1, fd4, fd2]

        res_fwd = chase_join_dependency(heading, order_forward, components, early_exit=False)
        res_rev = chase_join_dependency(heading, order_reverse, components, early_exit=False)
        res_int = chase_join_dependency(heading, order_interleaved, components, early_exit=False)

        self.assertTrue(res_fwd.is_implied)
        self.assertTrue(res_rev.is_implied)
        self.assertTrue(res_int.is_implied)

        # Assert cell partitions are identical
        part_fwd = chase_tableau_cell_partition(res_fwd.final_tableau, heading)
        part_rev = chase_tableau_cell_partition(res_rev.final_tableau, heading)
        part_int = chase_tableau_cell_partition(res_int.final_tableau, heading)

        self.assertEqual(part_fwd, part_rev)
        self.assertEqual(part_fwd, part_int)

    def test_randomized_chase_order_confluence_property(self) -> None:
        """Property test: for 20 randomized schemas with overlapping FDs,
        shuffling the FD application list produces identical implication outcomes.
        """
        universe = ["A", "B", "C", "D", "E"]

        for seed in range(20):
            rng = random.Random(seed)
            attrs = universe[:4]

            # Generate 3 components
            components = [
                sorted(rng.sample(attrs, 3)),
                sorted(rng.sample(attrs, 3)),
                sorted(rng.sample(attrs, 2)),
            ]
            # Ensure coverage
            uncovered = set(attrs) - set().union(*(set(c) for c in components))
            for u in uncovered:
                components[0].append(u)
            components = [sorted(set(c)) for c in components]

            # Generate 3 overlapping FDs
            fds = [
                FunctionalDependency.from_str("A", "B"),
                FunctionalDependency.from_str("B", "C"),
                FunctionalDependency.from_str("C", "D"),
            ]

            baseline_res = chase_join_dependency(attrs, fds, components)

            # Test 5 distinct random shuffles
            for p_idx in range(5):
                shuffled_fds = list(fds)
                rng.shuffle(shuffled_fds)
                perm_res = chase_join_dependency(attrs, shuffled_fds, components)
                self.assertEqual(
                    baseline_res.is_implied,
                    perm_res.is_implied,
                    f"Implication diverged under permutation on seed {seed}, perm {p_idx}",
                )


class TestMultivaluedDependencyAnd4NF(unittest.TestCase):
    """Verifies Multivalued Dependencies (MVDs) and Fourth Normal Form (4NF)."""

    def test_fagin_textbook_4nf_counterexample(self) -> None:
        """Fagin (1977) textbook schema:
        Heading: Employee, Skill, Language (E, S, L).
        Dependencies: Employee ->> Skill, Employee ->> Language.
        Candidate Key: {Employee, Skill, Language}.
        BCNF holds (no non-trivial FDs exist).
        4NF fails: Employee is not a superkey.
        """
        heading = frozenset({"Employee", "Skill", "Language"})
        schema = RelationalSchema(
            attributes=heading,
            dependencies=frozenset(),  # No functional dependencies
        )

        mvds = [
            MultivaluedDependency.from_str("Employee", "Skill"),
            MultivaluedDependency.from_str("Employee", "Language"),
        ]

        # 1. 4NF violation verification
        is_4nf, err_4nf = check_4nf(schema, mvds)
        self.assertFalse(is_4nf)
        self.assertIsNotNone(err_4nf)
        self.assertIn("4NF MVD Violation", err_4nf)

        # 2. Decomposition into [Employee, Skill] and [Employee, Language] is lossless under MVD
        components_lossless = [["Employee", "Skill"], ["Employee", "Language"]]
        res_lossless = chase_mvd(
            heading=["Employee", "Skill", "Language"],
            dependencies=(),
            mvds=mvds,
            components=components_lossless,
        )
        self.assertTrue(res_lossless.is_implied)
        self.assertIsNotNone(res_lossless.distinguished_row_index)
        self.assertGreater(res_lossless.mvd_tuples_generated, 0)

        # 3. Arbitrary lossy decomposition into [Skill, Language] and [Employee] fails
        components_lossy = [["Skill", "Language"], ["Employee"]]
        res_lossy = chase_mvd(
            heading=["Employee", "Skill", "Language"],
            dependencies=(),
            mvds=mvds,
            components=components_lossy,
        )
        self.assertFalse(res_lossy.is_implied)
        self.assertIsNone(res_lossy.distinguished_row_index)

    def test_mvd_triviality(self) -> None:
        """Verifies trivial MVD identification (Y ⊆ X or X ∪ Y = H)."""
        heading = frozenset({"A", "B", "C"})

        trivial_subset = MultivaluedDependency.from_str("A,B", "A")
        self.assertTrue(trivial_subset.is_trivial(heading))

        trivial_union = MultivaluedDependency.from_str("A", "B,C")
        self.assertTrue(trivial_union.is_trivial(heading))

        non_trivial = MultivaluedDependency.from_str("A", "B")
        self.assertFalse(non_trivial.is_trivial(heading))


class TestArmstrongAxiomClosureProperties(unittest.TestCase):
    """Verifies that attribute closure satisfies the Kuratowski and Armstrong axioms."""

    def test_armstrong_closure_axioms_on_sample_schemas(self) -> None:
        """Verifies reflexivity, idempotence, monotonicity, augmentation, and transitivity."""
        heading = ["A", "B", "C", "D"]
        fds = [
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B,C", "D"),
        ]

        report = verify_armstrong_closure_axioms(heading, fds)
        self.assertTrue(report["reflexivity"])
        self.assertTrue(report["idempotence"])
        self.assertTrue(report["monotonicity"])
        self.assertTrue(report["augmentation"])
        self.assertTrue(report["transitivity"])
        self.assertTrue(report["all_satisfied"])

    def test_armstrong_axioms_randomized_schemas(self) -> None:
        """Property test across 25 random dependency sets."""
        universe = ["A", "B", "C", "D"]
        for seed in range(25):
            rng = random.Random(seed)
            fds = []
            for _ in range(3):
                x = set(rng.sample(universe, rng.randint(1, 2)))
                y = set(rng.sample(universe, rng.randint(1, 2)))
                fds.append(FunctionalDependency(frozenset(x), frozenset(y)))

            report = verify_armstrong_closure_axioms(universe, fds)
            self.assertTrue(report["all_satisfied"], f"Axiom failure on seed {seed}: {report}")


class TestCandidateKeyAntichainMinimality(unittest.TestCase):
    """Verifies candidate key minimality and antichain conditions."""

    def test_pairwise_keys_antichain(self) -> None:
        """Schema R(A, B, C) with dependencies AB -> C, BC -> A, AC -> B.
        Candidate keys are AB, BC, AC. None is a subset of another.
        """
        schema = RelationalSchema(
            attributes=frozenset({"A", "B", "C"}),
            dependencies=frozenset(
                {
                    FunctionalDependency.from_str("A,B", "C"),
                    FunctionalDependency.from_str("B,C", "A"),
                    FunctionalDependency.from_str("A,C", "B"),
                }
            ),
        )
        is_antichain, defects = verify_candidate_keys_antichain(schema)
        self.assertTrue(is_antichain, f"Defects: {defects}")
        self.assertEqual(len(schema.candidate_keys()), 3)

    def test_redundant_superkey_exclusion(self) -> None:
        """Schema R(A, B, C) with key A (A -> B, A -> C).
        Superkey AB must NOT be in candidate keys.
        """
        schema = RelationalSchema(
            attributes=frozenset({"A", "B", "C"}),
            dependencies=frozenset(
                {
                    FunctionalDependency.from_str("A", "B"),
                    FunctionalDependency.from_str("A", "C"),
                }
            ),
        )
        keys = schema.candidate_keys()
        self.assertEqual(keys, [frozenset({"A"})])
        is_antichain, defects = verify_candidate_keys_antichain(schema)
        self.assertTrue(is_antichain)


if __name__ == "__main__":
    unittest.main()

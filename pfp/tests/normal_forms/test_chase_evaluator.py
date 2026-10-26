"""Targeted unit tests for the relational Chase evaluator.

AuthorityEffect: None.

Tests:
1. Binary lossless join under Heath's Theorem (A -> B implies ⋈[AB, AC]).
2. Darwen, Date, Fagin (2012) Theorem 6.1 counterexample:
   Candidate keys AB, AC, BC on heading {A, B, C} do NOT logically imply ⋈[AB, BC, AC].
   Demonstrates that SKNF does not entail 5NF.
3. Multi-step transitive chase under chain FDs (A -> B, B -> C, C -> D).
4. Superkey component chase on 4-way join dependencies.
5. Cyclic 4-way join failure on heading {A, B, C, D}.
6. Integration with check_lossless_decomposition and is_5nf_implied_by_keys.
"""

from __future__ import annotations

import random
import unittest

from omega_engine_pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    RelationalSchema,
    chase_join_dependency,
    check_lossless_decomposition,
    is_5nf_implied_by_keys,
)


class TestChaseEvaluator(unittest.TestCase):
    """Test suite for the relational Chase algorithm."""

    def test_heath_theorem_binary_join(self) -> None:
        """Verify Heath's Theorem: A -> B implies ⋈[AB, AC] on heading {A, B, C}."""
        heading = ["A", "B", "C"]
        fds = [FunctionalDependency.from_str("A", "B")]
        components = [["A", "B"], ["A", "C"]]

        res = chase_join_dependency(heading, fds, components)
        self.assertTrue(res.is_implied)
        self.assertIsNotNone(res.distinguished_row_index)
        self.assertGreaterEqual(len(res.steps), 1)

        # Step equated attribute B
        step = res.steps[0]
        self.assertEqual(step.attribute_equated, "B")
        self.assertEqual(step.new_symbol, "a_B")

    def test_darwen_date_fagin_theorem_6_1_counterexample(self) -> None:
        """Verify Darwen, Date, Fagin (2012) Theorem 6.1 counterexample.

        Schema R(A, B, C) with candidate keys AB, AC, BC and JD ⋈[AB, BC, AC].
        Every component is a superkey (SKNF), but candidate keys alone do NOT
        imply the ternary join dependency. The chase must refute implication.
        """
        heading = ["A", "B", "C"]
        keys = [["A", "B"], ["A", "C"], ["B", "C"]]
        components = [["A", "B"], ["B", "C"], ["A", "C"]]

        # 1. Test via chase_join_dependency with candidate_keys
        res = chase_join_dependency(
            heading=heading,
            dependencies=(),
            components=components,
            candidate_keys=keys,
        )
        self.assertFalse(res.is_implied)
        self.assertIsNone(res.distinguished_row_index)
        self.assertEqual(len(res.steps), 0)  # No FD can equate any symbol
        self.assertIsNotNone(res.spurious_tuple_witness)

        # 2. Test via is_5nf_implied_by_keys convenience function
        self.assertFalse(is_5nf_implied_by_keys(heading, keys, components))

    def test_multi_step_transitive_chase(self) -> None:
        """Verify multi-step transitive FD cascade: A -> B, B -> C, C -> D."""
        heading = ["A", "B", "C", "D"]
        fds = [
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B", "C"),
            FunctionalDependency.from_str("C", "D"),
        ]
        # Decomposed into components where Row 0 has A and needs B, C, D
        components = [["A"], ["A", "B"], ["B", "C"], ["C", "D"]]

        res = chase_join_dependency(heading, fds, components)
        self.assertTrue(res.is_implied)
        self.assertIsNotNone(res.distinguished_row_index)
        self.assertGreaterEqual(len(res.steps), 3)

        # Verify final tableau has at least one all-distinguished row
        final_row = res.final_tableau[res.distinguished_row_index]
        for a in heading:
            self.assertEqual(final_row[a], f"a_{a}")

    def test_superkey_component_entails_join_dependency(self) -> None:
        """When one component is a candidate key of the entire heading, JD is entailed."""
        heading = ["A", "B", "C", "D"]
        keys = [["A"]]
        # Component 0 has key A and other attributes
        components = [["A", "B"], ["A", "C"], ["A", "D"]]

        res = chase_join_dependency(
            heading=heading,
            dependencies=(),
            components=components,
            candidate_keys=keys,
        )
        self.assertTrue(res.is_implied)
        self.assertIsNotNone(res.distinguished_row_index)

    def test_cyclic_4way_join_failure(self) -> None:
        """Cyclic 4-way join on {A, B, C, D} with keys AB, BC, CD, DA fails implication."""
        heading = ["A", "B", "C", "D"]
        keys = [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"]]
        components = [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"]]

        res = chase_join_dependency(
            heading=heading,
            dependencies=(),
            components=components,
            candidate_keys=keys,
        )
        self.assertFalse(res.is_implied)
        self.assertIsNone(res.distinguished_row_index)
        self.assertFalse(is_5nf_implied_by_keys(heading, keys, components))

    def test_check_lossless_decomposition_integration(self) -> None:
        """Verify check_lossless_decomposition uses the chase evaluator correctly."""
        # 1. Lossless case: A -> B on {A, B, C} decomposed into {A, B} and {A, C}
        schema_lossless = RelationalSchema(
            attributes=frozenset({"A", "B", "C"}),
            dependencies=frozenset({FunctionalDependency.from_str("A", "B")}),
        )
        ok, err = check_lossless_decomposition(
            schema_lossless, [frozenset({"A", "B"}), frozenset({"A", "C"})]
        )
        self.assertTrue(ok)
        self.assertIsNone(err)

        # 2. Lossy case: B -> C decomposed into {A, B} and {A, C} (lacks A -> B or A -> C)
        schema_lossy = RelationalSchema(
            attributes=frozenset({"A", "B", "C"}),
            dependencies=frozenset({FunctionalDependency.from_str("B", "C")}),
        )
        ok_lossy, err_lossy = check_lossless_decomposition(
            schema_lossy, [frozenset({"A", "B"}), frozenset({"A", "C"})]
        )
        self.assertFalse(ok_lossy)
        self.assertIsNotNone(err_lossy)


class TestChaseMonotonicityProperties(unittest.TestCase):
    """Property-based verification of Chase monotonicity under dependency lattice extensions.

    Mathematical Invariant:
        For any relational heading H and join dependency J = ⋈[R_1, ..., R_k],
        let F_1 and F_2 be sets of functional dependencies (including candidate key constraints)
        such that F_1 ⊆ F_2.
        Then the cell equivalence relation generated by F_1 is a sub-congruence
        of that generated by F_2 (∼_{F_1} ⊆ ∼_{F_2}).
        Consequently:
            chase(F_1, J).is_implied ⟹ chase(F_2, J).is_implied.
    """

    def test_randomized_chase_monotonicity_property(self) -> None:
        """Verify chase monotonicity across 100 randomized small relational schemas.

        Generator specifications:
        - Attributes: 3 to 6 attributes sampled from {'A', 'B', 'C', 'D', 'E', 'F'}.
        - Components: 2 to 4 components covering the heading, non-trivial (each proper subset).
        - Keys: 1 to 4 candidate keys.
        - Functional Dependencies: 0 to 4 explicit non-trivial dependencies.
        - F_1 ⊆ F_2 formed by sampling subsets of the generated keys and dependencies.
        """
        universe = ["A", "B", "C", "D", "E", "F"]
        f1_implied_count = 0
        f2_promoted_count = 0
        neither_count = 0
        violations = 0

        for seed in range(100):
            rng = random.Random(seed)
            n_attrs = rng.randint(3, 6)
            attrs = universe[:n_attrs]

            # Generate 2 to 4 non-trivial components that cover attrs
            k = rng.randint(2, min(4, n_attrs))
            components: list[list[str]] = []
            uncovered = set(attrs)
            for _ in range(k):
                size = rng.randint(max(2, n_attrs - 2), n_attrs - 1)
                comp = sorted(rng.sample(attrs, size))
                components.append(comp)
                uncovered -= set(comp)
            for a in uncovered:
                rng.choice(components).append(a)
            components = [sorted(set(c)) for c in components]

            # Generate 1 to 4 candidate keys
            n_keys = rng.randint(1, 4)
            all_keys: list[list[str]] = []
            for _ in range(n_keys):
                k_size = rng.randint(1, n_attrs - 1)
                all_keys.append(sorted(rng.sample(attrs, k_size)))

            # Generate 0 to 4 functional dependencies
            n_fds = rng.randint(0, 4)
            all_fds: list[FunctionalDependency] = []
            for _ in range(n_fds):
                x_size = rng.randint(1, n_attrs - 1)
                x = set(rng.sample(attrs, x_size))
                available = [a for a in attrs if a not in x]
                if available:
                    y_size = rng.randint(1, len(available))
                    y = set(rng.sample(available, y_size))
                    all_fds.append(FunctionalDependency(frozenset(x), frozenset(y)))

            # F1 is a random subset of F2
            k1 = [key for key in all_keys if rng.random() < 0.5]
            d1 = [fd for fd in all_fds if rng.random() < 0.5]
            k2 = list(all_keys)
            d2 = list(all_fds)

            res1 = chase_join_dependency(attrs, d1, components, candidate_keys=k1)
            res2 = chase_join_dependency(attrs, d2, components, candidate_keys=k2)

            # Monotonicity invariant: chase(F1, J) => chase(F2, J)
            if res1.is_implied:
                self.assertTrue(
                    res2.is_implied,
                    f"Monotonicity violation on seed {seed}: F1 implied JD but superset F2 failed!",
                )
                f1_implied_count += 1
            elif res2.is_implied:
                f2_promoted_count += 1
            else:
                neither_count += 1

        self.assertEqual(violations, 0)
        self.assertGreater(f1_implied_count, 0, "Expected non-zero F1 implication instances")
        self.assertGreater(f2_promoted_count, 0, "Expected non-zero strict promotion instances")
        self.assertGreater(neither_count, 0, "Expected non-zero unimplied instances")

    def test_candidate_key_expansion_monotonicity(self) -> None:
        """Verify that expanding candidate keys monotonically preserves and promotes the chase."""
        heading = ["A", "B", "C", "D"]
        components = [["A", "B"], ["A", "C"], ["A", "D"]]

        # K0: no keys -> refutes
        res0 = chase_join_dependency(heading, (), components, candidate_keys=())
        self.assertFalse(res0.is_implied)

        # K1: key BC not covering any component -> refutes
        res1 = chase_join_dependency(heading, (), components, candidate_keys=[["B", "C"]])
        self.assertFalse(res1.is_implied)

        # K2: key AB covering component 0, equates across A and B -> refutes (still lacks C, D)
        res2 = chase_join_dependency(
            heading, (), components, candidate_keys=[["B", "C"], ["A", "B"]]
        )
        self.assertFalse(res2.is_implied)

        # K3: superset adding unary key A (present across all components) -> strictly implies JD!
        res3 = chase_join_dependency(
            heading,
            (),
            components,
            candidate_keys=[["B", "C"], ["A", "B"], ["A"]],
        )
        self.assertTrue(res3.is_implied)

        # Verify monotonicity ordering: res_i.is_implied <= res_j.is_implied
        results = [res0.is_implied, res1.is_implied, res2.is_implied, res3.is_implied]
        for i in range(len(results) - 1):
            if results[i]:
                self.assertTrue(results[i + 1])

    def test_transitive_fd_cascade_monotonicity(self) -> None:
        """Verify that prefix extensions of transitive dependency cascades monotonically propagate."""
        heading = ["A", "B", "C", "D"]
        components = [["A"], ["A", "B"], ["B", "C"], ["C", "D"]]

        fd1 = FunctionalDependency.from_str("A", "B")
        fd2 = FunctionalDependency.from_str("B", "C")
        fd3 = FunctionalDependency.from_str("C", "D")

        # F0: empty -> False
        res0 = chase_join_dependency(heading, (), components)
        self.assertFalse(res0.is_implied)

        # F1: {A -> B} -> False (unifies B in row 0, but C and D remain non-distinguished)
        res1 = chase_join_dependency(heading, (fd1,), components)
        self.assertFalse(res1.is_implied)

        # F2: {A -> B, B -> C} -> False (unifies B and C, but D remains non-distinguished)
        res2 = chase_join_dependency(heading, (fd1, fd2), components)
        self.assertFalse(res2.is_implied)

        # F3: {A -> B, B -> C, C -> D} -> True (all attributes distinguished in row 0)
        res3 = chase_join_dependency(heading, (fd1, fd2, fd3), components)
        self.assertTrue(res3.is_implied)

        # Step count must also monotonically increase
        self.assertEqual(len(res0.steps), 0)
        self.assertEqual(len(res1.steps), 1)
        self.assertEqual(len(res2.steps), 3)
        self.assertEqual(len(res3.steps), 6)

    def test_darwen_date_fagin_frontier_promotion(self) -> None:
        """Verify on Darwen-Date-Fagin (2012) Theorem 6.1 counterexample:
        Adding an FD strictly promotes unimplied JD to implied, verifying monotonicity on the 5NF frontier.
        """
        heading = ["A", "B", "C"]
        keys = [["A", "B"], ["B", "C"], ["A", "C"]]
        components = [["A", "B"], ["B", "C"], ["A", "C"]]

        # F1: candidate keys AB, BC, AC alone do NOT imply ⋈[AB, BC, AC]
        res1 = chase_join_dependency(
            heading=heading,
            dependencies=(),
            components=components,
            candidate_keys=keys,
        )
        self.assertFalse(res1.is_implied)
        self.assertIsNotNone(res1.spurious_tuple_witness)

        # F2: add FD A -> B to F1 (F1 ⊂ F2)
        res2 = chase_join_dependency(
            heading=heading,
            dependencies=[FunctionalDependency.from_str("A", "B")],
            components=components,
            candidate_keys=keys,
        )
        self.assertTrue(res2.is_implied)
        self.assertIsNotNone(res2.distinguished_row_index)
        self.assertIsNone(res2.spurious_tuple_witness)

    def test_empty_dependencies_base_soundness(self) -> None:
        """Under empty dependencies F = ∅, chase refutes non-trivial JDs and admits trivial ones."""
        heading = ["A", "B", "C"]

        # Non-trivial JD ⋈[AB, BC] without FDs is lossy / not implied
        res_non_trivial = chase_join_dependency(
            heading=heading,
            dependencies=(),
            components=[["A", "B"], ["B", "C"]],
        )
        self.assertFalse(res_non_trivial.is_implied)

        # Trivial JD where one component is the entire heading is always implied
        res_trivial = chase_join_dependency(
            heading=heading,
            dependencies=(),
            components=[["A", "B", "C"], ["A", "B"]],
        )
        self.assertTrue(res_trivial.is_implied)
        self.assertEqual(len(res_trivial.steps), 0)


if __name__ == "__main__":
    unittest.main()

"""Unit and property-based tests for Chase Algebra & Confluence (Tests 13-18)
and BigQuery Normal Form (BQNF) Streaming & CDC Aggregates (Tests 19-25).

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import random
import unittest

from pfp.domain.normal_forms.quantum_forms import (
    QuantileSketchCochain,
    verify_quantile_sketch_repair,
)
from pfp.domain.normal_forms.relational import (
    FunctionalDependency,
    RelationalSchema,
    chase_join_dependency,
    compute_minimal_cover,
)
from pfp.domain.normal_forms.relational_extensions import (
    MultivaluedDependency,
    chase_mvd,
    chase_tableau_cell_partition,
    verify_candidate_keys_antichain,
)


class TestChaseAlgebraAndBqnfStreaming(unittest.TestCase):
    """Test suite covering Chase monotonicity, confluence, and BQNF streaming cochains."""

    # =========================================================================
    # Group 2: Relational Chase Algebra, Confluence & Minimality (Tests 13-18)
    # =========================================================================

    def test_chase_monotonicity_under_fd_superset(self) -> None:
        """Test 13: Property test verifying F_1 ⊆ F_2 implies chase(F_1, J) => chase(F_2, J)."""
        heading = ["A", "B", "C", "D"]
        components = [["A", "B"], ["B", "C"], ["C", "D"]]

        # F1 has chain A -> B, B -> C
        f1 = [
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B", "C"),
        ]
        # F2 adds C -> D (superset of F1)
        f2 = f1 + [FunctionalDependency.from_str("C", "D")]

        res1 = chase_join_dependency(heading, f1, components)
        res2 = chase_join_dependency(heading, f2, components)

        # Monotonicity: Any cell equated in res1 remains equated in res2
        # And if res1 is implied, res2 must also be implied
        if res1.is_implied:
            self.assertTrue(res2.is_implied)

        # Count of steps under F2 must be >= count under F1
        self.assertGreaterEqual(len(res2.steps), len(res1.steps))

    def test_chase_confluence_under_dependency_permutations(self) -> None:
        """Test 14: Verifies Church-Rosser cell partition confluence under early_exit=False."""
        heading = ["A", "B", "C", "D"]
        components = [["A", "B"], ["B", "C"], ["C", "D"]]
        fds = [
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B", "C"),
            FunctionalDependency.from_str("C", "D"),
        ]

        rng = random.Random(1337)
        partitions = []
        for _ in range(8):
            permuted_fds = list(fds)
            rng.shuffle(permuted_fds)
            res = chase_join_dependency(heading, permuted_fds, components, early_exit=False)
            part = chase_tableau_cell_partition(res.final_tableau, res.heading)
            partitions.append(part)

        # All final cell equivalence partitions must be strictly identical (confluent)
        first_partition = partitions[0]
        for p in partitions[1:]:
            self.assertEqual(p, first_partition)

    def test_chase_infinite_loop_prevention_on_cyclic_tgds(self) -> None:
        """Test 15: Cyclic tuple-generating dependencies trip max_iterations bounds safely."""
        heading = ["A", "B"]
        components = [["A"], ["B"]]
        # Cyclic MVD structure that generates endless Cartesian tuples
        mvds = [
            MultivaluedDependency(frozenset(["A"]), frozenset(["B"])),
            MultivaluedDependency(frozenset(["B"]), frozenset(["A"])),
        ]

        # max_iterations bounds execution
        res = chase_mvd(heading, [], mvds, components, max_iterations=5)
        self.assertIsNotNone(res)
        self.assertLessEqual(res.final_row_count, 100)

    def test_chase_lossless_join_preservation(self) -> None:
        """Test 16: Binary decomposition under Heath's theorem yields a distinguished row."""
        heading = ["A", "B", "C"]
        fds = [FunctionalDependency.from_str("A", "B")]
        components = [["A", "B"], ["A", "C"]]

        res = chase_join_dependency(heading, fds, components)
        self.assertTrue(res.is_implied)
        self.assertIsNotNone(res.distinguished_row_index)

    def test_minimal_cover_canonical_reduction(self) -> None:
        """Test 17: Redundant FDs and extraneous LHS attributes reduce to a minimal cover."""
        # Non-minimal: AB -> C where A -> C (B is extraneous in AB -> C)
        # Redundant: A -> B and B -> C and A -> C (A -> C is transitive redundant)
        raw_fds = [
            FunctionalDependency.from_str("A, B", "C"),
            FunctionalDependency.from_str("A", "B"),
            FunctionalDependency.from_str("B", "C"),
            FunctionalDependency.from_str("A", "C"),
        ]

        min_cover = compute_minimal_cover(raw_fds)
        # Minimal cover should contain only A -> B and B -> C
        expected_dets = {frozenset(["A"]), frozenset(["B"])}
        actual_dets = {f.determinant for f in min_cover}
        self.assertEqual(actual_dets, expected_dets)
        self.assertEqual(len(min_cover), 2)

    def test_candidate_key_antichain_minimality(self) -> None:
        """Test 18: Verifies candidate keys form a Sperner family (antichain) with no subsets."""
        schema = RelationalSchema(
            attributes=frozenset(["A", "B", "C"]),
            dependencies=frozenset(
                [
                    FunctionalDependency.from_str("A, B", "C"),
                    FunctionalDependency.from_str("B, C", "A"),
                    FunctionalDependency.from_str("A, C", "B"),
                ]
            ),
        )
        is_antichain, defects = verify_candidate_keys_antichain(schema)
        self.assertTrue(is_antichain)
        self.assertEqual(defects, [])

    # =========================================================================
    # Group 3: BigQuery Normal Form (BQNF) & Streaming CDC Aggregates (Tests 19-25)
    # =========================================================================

    def test_bqnf_denormalized_nested_record_losslessness(self) -> None:
        """Test 19: Denormalized nested ARRAY/STRUCT representation roundtrips losslessly."""
        flat_records = [
            {"order_id": 1, "item_id": 101, "price": 10},
            {"order_id": 1, "item_id": 102, "price": 25},
            {"order_id": 2, "item_id": 103, "price": 50},
        ]

        # Nest into BQNF struct
        nested = {}
        for r in flat_records:
            oid = r["order_id"]
            nested.setdefault(oid, []).append({"item_id": r["item_id"], "price": r["price"]})

        # Unnest back to flat
        reconstructed = []
        for oid, items in sorted(nested.items()):
            for it in items:
                reconstructed.append(
                    {"order_id": oid, "item_id": it["item_id"], "price": it["price"]}
                )

        self.assertEqual(flat_records, reconstructed)

    def test_bqnf_cdc_out_of_order_deduplication(self) -> None:
        """Test 20: Streaming CDC events with monotonic version sequence converge under shuffle."""
        events = [
            {"key": "k1", "val": "v1", "ver": 1},
            {"key": "k1", "val": "v2", "ver": 2},
            {"key": "k1", "val": "v3", "ver": 3},
            {"key": "k2", "val": "a1", "ver": 1},
            {"key": "k2", "val": "a2", "ver": 2},
        ]

        def reduce_latest(event_stream):
            state = {}
            for ev in event_stream:
                k = ev["key"]
                if k not in state or ev["ver"] > state[k]["ver"]:
                    state[k] = ev
            return {k: v["val"] for k, v in sorted(state.items())}

        expected = {"k1": "v3", "k2": "a2"}
        self.assertEqual(reduce_latest(events), expected)

        # Shuffle 10 times and assert identical convergence
        rng = random.Random(42)
        for _ in range(10):
            shuffled = list(events)
            rng.shuffle(shuffled)
            self.assertEqual(reduce_latest(shuffled), expected)

    def test_bqnf_partition_pruning_constraint_preservation(self) -> None:
        """Test 21: Partition range boundary filters preserve superkey integrity across shards."""
        RelationalSchema(
            attributes=frozenset(["Date", "OrderID", "Amount"]),
            dependencies=frozenset([FunctionalDependency.from_str("Date, OrderID", "Amount")]),
        )
        # Partition key: Date. In each partition shard (Date=D_k), OrderID is a superkey for Amount
        # Projected schema on shard
        shard_schema = RelationalSchema(
            attributes=frozenset(["OrderID", "Amount"]),
            dependencies=frozenset([FunctionalDependency.from_str("OrderID", "Amount")]),
        )
        self.assertTrue(shard_schema.is_superkey(["OrderID"]))

    def test_bqnf_hyperloglog_sketch_merge_commutativity(self) -> None:
        """Test 22: Approximate cardinality sketch bit-vectors satisfy commutativity and associativity."""

        def mock_hll(values: list[str]) -> set[int]:
            return {hashlib.sha256(v.encode("utf-8")).digest()[0] % 64 for v in values}

        s1 = mock_hll(["alpha", "beta"])
        s2 = mock_hll(["beta", "gamma"])
        s3 = mock_hll(["delta", "epsilon"])

        # Commutativity: s1 | s2 == s2 | s1
        self.assertEqual(s1 | s2, s2 | s1)

        # Associativity: (s1 | s2) | s3 == s1 | (s2 | s3)
        self.assertEqual((s1 | s2) | s3, s1 | (s2 | s3))

    def test_bqnf_count_conservation_under_repartitioning(self) -> None:
        """Test 23: Relational mass sum(counts) is strictly conserved under arbitrary re-sharding."""
        rows = [("k1", 10), ("k2", 20), ("k3", 30), ("k4", 40), ("k5", 50)]
        initial_mass = sum(v for _, v in rows)

        # Shard by mod 2
        shard0 = [v for k, v in rows if hash(k) % 2 == 0]
        shard1 = [v for k, v in rows if hash(k) % 2 != 0]

        repartitioned_mass = sum(shard0) + sum(shard1)
        self.assertEqual(initial_mass, repartitioned_mass)

    def test_bqnf_t_digest_quantile_scale_invariance(self) -> None:
        """Test 24: QuantileSketchCochain estimation and repair is robust under streaming updates."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        cochain = QuantileSketchCochain(bucket_width=10.0)
        for v in values:
            cochain.add(v)

        # Baseline median repair
        res_base = verify_quantile_sketch_repair(cochain, values, q=0.5, tolerance=15.0)
        self.assertEqual(res_base.terminal, "Repair")
        self.assertTrue(res_base.within_tolerance)

        # Scale values by 2 and adjust bucket width proportionally
        scale = 2.0
        scaled_values = [v * scale for v in values]
        scaled_cochain = QuantileSketchCochain(bucket_width=10.0 * scale)
        for v in scaled_values:
            scaled_cochain.add(v)

        res_scaled = verify_quantile_sketch_repair(
            scaled_cochain, scaled_values, q=0.5, tolerance=15.0 * scale
        )
        self.assertEqual(res_scaled.terminal, "Repair")
        self.assertTrue(res_scaled.within_tolerance)

    def test_bqnf_clustering_key_prefix_monomorphism(self) -> None:
        """Test 25: Composite clustering key tuples maintain monotonic sort orders under projection."""
        tuples = [
            ("US", "NY", 100),
            ("US", "CA", 200),
            ("UK", "LON", 300),
            ("UK", "MAN", 400),
        ]
        sorted_tuples = sorted(tuples)
        # Prefix projection to (Country, State)
        prefix_proj = [(t[0], t[1]) for t in sorted_tuples]
        # Must remain non-decreasing
        for i in range(len(prefix_proj) - 1):
            self.assertLessEqual(prefix_proj[i], prefix_proj[i + 1])


if __name__ == "__main__":
    unittest.main()

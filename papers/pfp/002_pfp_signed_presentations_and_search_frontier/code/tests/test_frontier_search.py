"""Finite, representation-scoped tests for frontier_search."""

import sys
import unittest
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

_here = Path(__file__).resolve().parent
_candidates = [
    _here,
    _here.parent / "genesis_alpha",
    _here.parent / "code" / "genesis_alpha",
    _here.parents[1] / "code" / "genesis_alpha",
]
_module_dir = next((p for p in _candidates if (p / "frontier_search.py").is_file()), None)
if _module_dir is None:
    raise FileNotFoundError("frontier_search.py not found beside test or under code/genesis_alpha")
sys.path.insert(0, str(_module_dir))

from frontier_search import (  # noqa: E402
    CHECKER_VERSION,
    DIAGONAL_Z2_GRAMMAR,
    CandidateCheck,
    GaugeFrontier,
    PresentationIndex,
    PresentationKey,
    _seal_receipt,
    exact_matrix_digest,
    search_exact_matrix,
    search_sign_graph,
    verify_search_receipt,
)
from sign_graph import (  # noqa: E402
    GaugeWitness,
    OddCycleWitness,
    SignedRewrite,
    verify_gauge,
    verify_odd_cycle,
)


def key(hamiltonian_digest="0" * 64, representation="ordered_paths"):
    return PresentationKey(
        hamiltonian_digest=hamiltonian_digest,
        basis="occupation:0,1,2",
        ensemble="canonical",
        filling="N=1",
        boundary="open",
        representation=representation,
        estimator="finite path sum",
        observables=("partition",),
        beta="1/2",
        parameters=(("U", "0"), ("t", "1")),
        transformation_grammar=DIAGONAL_Z2_GRAMMAR,
        adapter_digest="a" * 64,
        checker_version=CHECKER_VERSION,
    )


class FrontierSearchTests(unittest.TestCase):
    def setUp(self):
        self.vertices = ("a", "b", "c")
        self.edges = (SignedRewrite("a", "b", 1), SignedRewrite("b", "c", 0))

    def test_parallel_search_finds_exact_gauge_and_replays_receipt(self):
        result = search_sign_graph(self.vertices, self.edges, key(), node_budget=8, workers=4)
        self.assertEqual(result.status, "GAUGE_VERIFIED")
        self.assertIsInstance(result.witness, GaugeWitness)
        self.assertEqual(result.witness.bits, (0, 1, 1))
        self.assertTrue(verify_gauge(self.vertices, self.edges, result.witness))
        self.assertTrue(verify_search_receipt(self.vertices, self.edges, key(), result))
        self.assertFalse(result.complete_oracle_used)

    def test_parallel_schedule_does_not_change_selected_result_or_receipt(self):
        single = search_sign_graph(self.vertices, self.edges, key(), node_budget=8, workers=1)
        parallel = search_sign_graph(self.vertices, self.edges, key(), node_budget=8, workers=4)
        self.assertEqual(single, parallel)
        self.assertEqual(single.receipt_sha256, parallel.receipt_sha256)
        self.assertEqual(tuple(c.index for c in parallel.checks), tuple(range(8)))

    def test_budget_unknown_retains_exact_untested_frontier_for_resume(self):
        first = search_sign_graph(self.vertices, self.edges, key(), node_budget=2, workers=4)
        self.assertEqual(first.status, "UNKNOWN")
        self.assertEqual(first.frontier.next_index, 2)
        self.assertEqual(first.frontier.stop_index, 8)
        self.assertIsNone(first.witness)
        self.assertFalse(first.complete_oracle_used)
        self.assertTrue(verify_search_receipt(self.vertices, self.edges, key(), first))
        second = search_sign_graph(self.vertices, self.edges, key(), node_budget=2,
                                   workers=4, frontier=first.frontier,
                                   prior_receipts=(first,))
        self.assertEqual(second.status, "GAUGE_VERIFIED")
        self.assertEqual(tuple(c.index for c in second.checks), (2, 3))
        self.assertEqual(second.witness.bits, (0, 1, 1))
        self.assertFalse(verify_search_receipt(self.vertices, self.edges, key(), second))
        self.assertTrue(verify_search_receipt(self.vertices, self.edges, key(),
                                              second, prior_receipts=(first,)))

    def test_zero_budget_does_not_advance_frontier(self):
        initial = search_sign_graph(self.vertices, self.edges, key(), node_budget=0)
        self.assertEqual(initial.status, "UNKNOWN")
        self.assertEqual(initial.frontier, GaugeFrontier(initial.graph_digest, 0, 8))
        self.assertEqual(initial.checks, ())

    def test_odd_cycle_only_after_exhausting_finite_grammar(self):
        triangle = (SignedRewrite("a", "b", 1), SignedRewrite("b", "c", 1),
                    SignedRewrite("c", "a", 1))
        partial = search_sign_graph(self.vertices, triangle, key(), node_budget=7)
        self.assertEqual(partial.status, "UNKNOWN")
        self.assertFalse(partial.complete_oracle_used)
        final = search_sign_graph(self.vertices, triangle, key(), node_budget=1,
                                  frontier=partial.frontier,
                                  prior_receipts=(partial,))
        self.assertEqual(final.status, "RESTRICTED_OBSTRUCTION")
        self.assertIsInstance(final.witness, OddCycleWitness)
        self.assertTrue(final.complete_oracle_used)
        self.assertTrue(verify_odd_cycle(self.vertices, triangle, final.witness))
        self.assertFalse(verify_search_receipt(self.vertices, triangle, key(), final))
        self.assertTrue(verify_search_receipt(self.vertices, triangle, key(),
                                              final, prior_receipts=(partial,)))

    def test_resealed_final_suffix_needs_independently_replayed_prior_chain(self):
        triangle = (SignedRewrite("a", "b", 1), SignedRewrite("b", "c", 1),
                    SignedRewrite("c", "a", 1))
        partial = search_sign_graph(self.vertices, triangle, key(), node_budget=7)
        final = search_sign_graph(self.vertices, triangle, key(), node_budget=1,
                                  frontier=partial.frontier,
                                  prior_receipts=(partial,))
        forged_suffix = _seal_receipt("RESTRICTED_OBSTRUCTION", key(),
                                      final.graph_digest, 7, 1, final.checks,
                                      final.frontier, final.witness, True)
        self.assertFalse(verify_search_receipt(self.vertices, triangle,
                                               key(), forged_suffix))
        self.assertTrue(verify_search_receipt(self.vertices, triangle,
                                              key(), forged_suffix,
                                              prior_receipts=(partial,)))
        self.assertFalse(verify_search_receipt(self.vertices, triangle,
                                               key(), forged_suffix,
                                               prior_receipts=(replace(partial, checks=()),)))

    def test_matrix_digest_pins_exact_input(self):
        matrix = ((0, Fraction(1, 2)), (Fraction(1, 2), 0))
        pinned = key(exact_matrix_digest(matrix))
        result = search_exact_matrix(matrix, pinned, node_budget=4)
        self.assertEqual(result.status, "GAUGE_VERIFIED")
        with self.assertRaisesRegex(ValueError, "digest"):
            search_exact_matrix(matrix, key(), node_budget=4)

    def test_one_shot_matrix_is_digested_and_checked_from_one_snapshot(self):
        triangle = ((0, 1, 1), (1, 0, 1), (1, 1, 0))
        pinned = key(exact_matrix_digest(triangle))
        self.assertEqual(exact_matrix_digest(iter(triangle)), pinned.hamiltonian_digest)
        result = search_exact_matrix(iter(triangle), pinned, node_budget=8)
        self.assertEqual(result.status, "RESTRICTED_OBSTRUCTION")
        self.assertTrue(verify_odd_cycle(("0", "1", "2"),
                                         (SignedRewrite("0", "1", 1),
                                          SignedRewrite("0", "2", 1),
                                          SignedRewrite("1", "2", 1)), result.witness))
        with self.assertRaisesRegex(ValueError, "digest"):
            search_exact_matrix(iter(triangle), key(exact_matrix_digest(())), node_budget=8)

    def test_graph_entrypoint_records_but_cannot_bind_hamiltonian_digest(self):
        first = search_sign_graph(self.vertices, self.edges, key("0" * 64), node_budget=8)
        second = search_sign_graph(self.vertices, self.edges, key("1" * 64), node_budget=8)
        self.assertEqual(first.graph_digest, second.graph_digest)
        self.assertNotEqual(first.presentation_digest, second.presentation_digest)
        self.assertEqual(first.witness, second.witness)
        # This demonstrates why H-to-graph import needs a separate adapter proof.

    def test_changing_transformation_grammar_cannot_run_or_replay(self):
        pinned = key()
        other = replace(pinned, transformation_grammar="arbitrary-basis-change-v1")
        valid = search_sign_graph(self.vertices, self.edges, pinned, node_budget=8)
        with self.assertRaisesRegex(ValueError, "grammar"):
            search_sign_graph(self.vertices, self.edges, other, node_budget=8)
        self.assertFalse(verify_search_receipt(self.vertices, self.edges, other, valid))
        resealed = _seal_receipt(valid.status, other, valid.graph_digest,
                                 valid.start_index, valid.node_budget, valid.checks,
                                 valid.frontier, valid.witness,
                                 valid.complete_oracle_used)
        self.assertFalse(verify_search_receipt(self.vertices, self.edges, other, resealed))

    def test_changed_or_malformed_frontier_is_refused(self):
        partial = search_sign_graph(self.vertices, self.edges, key(), node_budget=2)
        with self.assertRaisesRegex(ValueError, "frontier"):
            search_sign_graph(self.vertices, self.edges, key(), node_budget=2,
                              frontier=replace(partial.frontier, graph_digest="f" * 64))
        with self.assertRaisesRegex(ValueError, "frontier"):
            search_sign_graph(self.vertices, self.edges, key(), node_budget=2,
                              frontier=replace(partial.frontier, next_index=9))
        with self.assertRaisesRegex(ValueError, "prior receipts"):
            search_sign_graph(self.vertices, self.edges, key(), node_budget=1,
                              frontier=GaugeFrontier(partial.graph_digest, 7, 8))
        with self.assertRaisesRegex(ValueError, "prior receipts"):
            search_sign_graph(self.vertices, self.edges, key(), node_budget=1,
                              frontier=GaugeFrontier(partial.graph_digest, 7, 8),
                              prior_receipts=(partial,))
        with self.assertRaisesRegex(ValueError, "prior receipts"):
            search_sign_graph(self.vertices, self.edges, key(), node_budget=1,
                              frontier=partial.frontier,
                              prior_receipts=(replace(partial, checks=()),))

    def test_resume_chain_covers_every_prior_index(self):
        first = search_sign_graph(self.vertices, self.edges, key(), node_budget=2)
        second = search_sign_graph(self.vertices, self.edges, key(), node_budget=1,
                                   frontier=first.frontier, prior_receipts=(first,))
        self.assertEqual(second.status, "UNKNOWN")
        self.assertEqual(second.frontier.next_index, 3)
        third = search_sign_graph(self.vertices, self.edges, key(), node_budget=1,
                                  frontier=second.frontier,
                                  prior_receipts=(first, second))
        self.assertEqual(third.status, "GAUGE_VERIFIED")
        self.assertEqual(tuple(c.index for c in third.checks), (3,))
        self.assertFalse(verify_search_receipt(self.vertices, self.edges, key(), third,
                                               prior_receipts=(second,)))
        self.assertTrue(verify_search_receipt(self.vertices, self.edges, key(), third,
                                              prior_receipts=(first, second)))

    def test_index_separates_presentations_and_does_not_certify(self):
        index = PresentationIndex()
        path_key = key(representation="ordered_paths")
        determinant_key = key(representation="determinant")
        index.add(path_key, (0, 0, 0), "unchecked model hint")
        self.assertEqual(index.lookup_exact(determinant_key), ())
        retrieved = index.lookup_exact(path_key)
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].authority_effect, "None")
        self.assertFalse(verify_gauge(self.vertices, self.edges,
                                      GaugeWitness(self.vertices, retrieved[0].bits)))
        # A malicious hint does not change the exact search result.
        result = search_sign_graph(self.vertices, self.edges, path_key, node_budget=8)
        self.assertEqual(result.witness.bits, (0, 1, 1))

    def test_receipt_replay_detects_modified_checks(self):
        result = search_sign_graph(self.vertices, self.edges, key(), node_budget=8)
        tampered = replace(result, checks=())
        self.assertFalse(verify_search_receipt(self.vertices, self.edges, key(), tampered))

    def test_receipt_replay_requires_canonical_batch_even_when_resealed(self):
        result = search_sign_graph(self.vertices, self.edges, key(), node_budget=8)
        impossible = _seal_receipt("GAUGE_VERIFIED", key(), result.graph_digest,
                                   0, 8, result.checks[:4],
                                   GaugeFrontier(result.graph_digest, 4, 8),
                                   result.witness, False)
        self.assertFalse(verify_search_receipt(self.vertices, self.edges,
                                               key(), impossible))

    def test_malformed_receipt_fails_closed(self):
        result = search_sign_graph(self.vertices, self.edges, key(), node_budget=1)
        malformed = _seal_receipt("UNKNOWN", key(), result.graph_digest, 0, 1,
                                  (CandidateCheck(0.0, (False, False, False), False),),
                                  GaugeFrontier(result.graph_digest, 1, 8), None, False)
        self.assertFalse(verify_search_receipt(self.vertices, self.edges,
                                               key(), malformed))
        self.assertFalse(verify_search_receipt(self.vertices, self.edges,
                                               key(), replace(result, checks=None)))


if __name__ == "__main__":
    unittest.main()

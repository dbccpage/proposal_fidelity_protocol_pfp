"""Targeted unit tests for Three-Layer Sovereignty (Directive 33).

Verifies the mathematical and architectural separation between:
- Layer 1: Internal model forward-pass attention key/query masking.
- Layer 2: Next-token logit carrier projection / support restriction.
- Layer 3: Independent host evaluation, recomputation, and terminal gating.
"""

from fractions import Fraction
import math
import unittest


class TestThreeLayerSovereignty(unittest.TestCase):
    def test_simplex_l1_norm_invariance(self):
        """Probability vector l1 norm is identically 1 and cannot induce sparsity."""
        # Test across multiple probability vectors
        p_distributions = [
            [0.2, 0.3, 0.5],
            [0.1, 0.1, 0.1, 0.7],
            [1.0, 0.0, 0.0],
            [0.25, 0.25, 0.25, 0.25],
        ]
        for p in p_distributions:
            l1_norm = sum(abs(x) for x in p)
            self.assertAlmostEqual(l1_norm, 1.0, places=7)

        # On the probability simplex, lambda * ||p||_1 is constant:
        lambda_penalty = 0.5
        for p in p_distributions:
            penalty_val = lambda_penalty * sum(abs(x) for x in p)
            self.assertAlmostEqual(penalty_val, 0.5, places=7)

    def test_layer2_carrier_mask_does_not_certify_correctness(self):
        """Restricting output to carrier token IDs does not guarantee mathematical truth."""
        # Simulated carrier constraint: only digits '0'-'9' allowed
        carrier_tokens = set("0123456789")
        model_output = "555555"

        # Output complies with Layer 2 carrier restriction
        self.assertTrue(all(char in carrier_tokens for char in model_output))

        # But Layer 3 independent host evaluation checks task ground truth
        expected_answer = 3 + 4  # = 7
        actual_val = int(model_output)

        host_disposition = "ACCEPTED" if actual_val == expected_answer else "REFUSED_ARITHMETIC_MISMATCH"
        self.assertEqual(host_disposition, "REFUSED_ARITHMETIC_MISMATCH")

    def test_layer1_key_mask_receipt_tagging(self):
        """Layer 1 interventions must be tagged explicitly and reject hosted API claims."""
        valid_layer1_receipt = {
            "intervention_level": "LAYER_1_ATTENTION_KEY_MASK",
            "model_type": "LOCAL_OPEN_WEIGHTS",
            "target": "key_positions_across_heads_and_layers",
            "verified_in_host": True,
        }
        self.assertEqual(valid_layer1_receipt["intervention_level"], "LAYER_1_ATTENTION_KEY_MASK")
        self.assertEqual(valid_layer1_receipt["model_type"], "LOCAL_OPEN_WEIGHTS")

        # An API logit bias must never be labeled Layer 1
        with self.assertRaises(ValueError):
            def validate_receipt(r):
                if r["model_type"] == "HOSTED_API" and r["intervention_level"] == "LAYER_1_ATTENTION_KEY_MASK":
                    raise ValueError("Cannot claim Layer 1 intervention on hosted proprietary API")
            validate_receipt({"model_type": "HOSTED_API", "intervention_level": "LAYER_1_ATTENTION_KEY_MASK"})

    def test_layer3_independent_recomputation_mandate(self):
        """Host must independently recompute Phi_1 and ignore untrusted self-certifications."""
        # Spanning tree potentials: f(a)=0, f(b)=1, f(c)=-3
        potentials = {"a": 0, "b": 1, "c": -3}
        # Untrusted model packet claiming phi1 = 0 but with defective chord c->b
        model_packet = {
            "proposed_claims": {
                "a->b": 1,
                "c->a": 3,
                "c->b": -1,  # Error! True coboundary is f(b) - f(c) = 1 - (-3) = 4
            },
            "self_reported_phi1": 0,  # Semantic lie / hallucination
            "self_reported_status": "ACCEPTED_ZERO_DEFECT",
        }

        # Layer 3 host recomputes exact coboundary defect:
        # Coboundary of c->b is f(b) - f(c) = 1 - (-3) = 4
        # Claim is -1, so defect is |-1 - 4| = 5
        true_coboundary_cb = potentials["b"] - potentials["c"]
        host_computed_phi1 = abs(model_packet["proposed_claims"]["c->b"] - true_coboundary_cb)

        self.assertNotEqual(host_computed_phi1, model_packet["self_reported_phi1"])
        self.assertEqual(host_computed_phi1, 5)

        # Host ignores self-certification and rejects the proposal
        host_verdict = "ACCEPTED" if host_computed_phi1 == 0 else "REFUSED_COBOUNDARY_DEFECT"
        self.assertEqual(host_verdict, "REFUSED_COBOUNDARY_DEFECT")

    def test_claim_discipline_on_dimensional_collapse(self):
        """Dimensional collapse claims require singular value spectrum, not entropy alone."""
        # Simulated measurement: top-5 normalized transition entropy
        entropy_measurement = {"top5_entropy": 0.2233, "singular_values": None}

        def verify_dimensional_collapse_claim(m: dict) -> bool:
            # Rule: Cannot assert dimensional collapse without singular value spectrum
            if m.get("singular_values") is None:
                return False
            return True

        self.assertFalse(verify_dimensional_collapse_claim(entropy_measurement))

        # When singular value spectrum is provided, claim can be evaluated
        spectrum_measurement = {"top5_entropy": 0.2233, "singular_values": [1.0, 0.05, 0.001]}
        self.assertTrue(verify_dimensional_collapse_claim(spectrum_measurement))


if __name__ == "__main__":
    unittest.main()

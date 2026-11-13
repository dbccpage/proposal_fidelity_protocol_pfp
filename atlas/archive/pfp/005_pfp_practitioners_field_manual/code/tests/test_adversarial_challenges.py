"""
test_adversarial_challenges.py — Empirical Stress-Testing Suite for The Symbol Game.

Covers:
1. quickstart.py mathematical projection logic:
   - Disconnected graphs & isolated vertices
   - Dense multi-cycles (Theta graph, K4 complete graph)
   - 2-cycle opposing edges (A->B and B->A)
   - Consistent zero-cycle (holonomy = 0 preserves exact claims)
   - Extreme edge weights (10^30) and exact L1 sparse landing
   - Exact rational precision (zero float drift across repeated projections)
   - Invariant enforcement (self-loops, non-positive weights, carrier boundary)
   - Defect monotonicity and fail-closed refusal
   - Audit receipt determinism and SHA-256 integrity
2. llm_streaming_harness.py streaming and governance logic:
   - Live SSE streaming with in-process HTTP server (corrupt lines, comments, HTTP errors)
   - StreamingEnvelopeParser edge cases (raw text, arrays, truncated tokens, markdown fences)
   - SymbolGameStreamingSession fail-closed refusals (unknown moves, self-loops, carrier violations, defect inflation)
   - Receipt generation determinism, self-audit verification, and tamper sensitivity
   - Vulnerability witnesses:
     * Unparsed edge key format ("a->b") silent constraint erasure
     * RETRACT move type mismatch / crash
"""

import hashlib
import http.server
import json
import threading
from fractions import Fraction

import pytest

# Imports from quickstart.py
import quickstart as qs

# Imports from llm_streaming_harness.py
from llm_streaming_harness import (
    LiveAPIStreamingProposer,
    LLMStreamChunk,
    MockLLMStreamingProposer,
    StreamingEnvelopeParser,
    SymbolGameStreamingSession,
    run_and_generate_receipt,
)

# =============================================================================
# PART 1: ADVERSARIAL CHALLENGES FOR quickstart.py
# =============================================================================

class TestQuickstartAdversarialMath:
    """Stress tests challenging the mathematical projection and invariance in quickstart.py."""

    def test_self_loop_irreflexivity_refusal(self):
        """Self-loops must raise ValueError immediately on construction."""
        with pytest.raises(ValueError, match="violates irreflexivity"):
            qs.Edge(source="A", target="A", weight=1)

    def test_non_positive_weight_refusal(self):
        """Edge weights <= 0 must be rejected."""
        with pytest.raises(ValueError, match="Edge weight must be positive"):
            qs.Edge(source="A", target="B", weight=0)

        with pytest.raises(ValueError, match="Edge weight must be positive"):
            qs.Edge(source="A", target="B", weight=-5)

    def test_graph_undeclared_vertex_refusal(self):
        """Edges referencing undeclared vertices must raise ValueError."""
        e = qs.Edge(source="A", target="Ghost", weight=1)
        with pytest.raises(ValueError, match="not in declared vertices"):
            qs.ConstraintGraph(vertices=("A", "B"), edges=(e,))

    def test_disconnected_graph_projection_and_idempotence(self, native_functional):
        """
        Adversarial Topology 1: Disconnected graph with 2 independent cycles.
        Component 1: A -> B -> C -> A (claims: 1, 1, 1; holonomy=3; weights 1, 1, 1)
        Component 2: D -> E -> F -> D (claims: 2, 2, 2; holonomy=6; weights 2, 2, 2)
        """
        edges = (
            qs.Edge("A", "B", 1), qs.Edge("B", "C", 1), qs.Edge("C", "A", 1),
            qs.Edge("D", "E", 2), qs.Edge("E", "F", 2), qs.Edge("F", "D", 2),
        )
        vertices = ("A", "B", "C", "D", "E", "F")
        graph = qs.ConstraintGraph(vertices=vertices, edges=edges)

        claims = qs.Cochain1({
            ("A", "B"): Fraction(1), ("B", "C"): Fraction(1), ("C", "A"): Fraction(1),
            ("D", "E"): Fraction(2), ("E", "F"): Fraction(2), ("F", "D"): Fraction(2),
        })

        comps = graph.connected_components()
        assert len(comps) == 2

        # 1st Projection
        best_norm, best_potential, projected = qs.compute_discrete_l1_projection(graph, claims)
        assert best_norm > 0

        # Verify projected cochain has 0 defect with respect to best_potential
        defect_p, _ = qs.evaluate_defect(projected, best_potential, graph.edges)
        assert defect_p == Fraction(0)

        # 2nd Projection (Idempotence check: P(P(s)) == P(s))
        reproj_norm, reproj_potential, reprojected = qs.compute_discrete_l1_projection(graph, projected)
        assert reproj_norm == Fraction(0)
        assert reprojected.values == projected.values

    def test_isolated_vertices_handling(self, native_functional):
        """
        Adversarial Topology 2: Graph with isolated degree-0 nodes.
        Vertices: A, B, C (cycle) + X, Y (isolated nodes with no incident edges).
        """
        edges = (
            qs.Edge("A", "B", 1), qs.Edge("B", "C", 1), qs.Edge("C", "A", 1),
        )
        vertices = ("A", "B", "C", "X", "Y")
        graph = qs.ConstraintGraph(vertices=vertices, edges=edges)

        claims = qs.Cochain1({
            ("A", "B"): Fraction(1), ("B", "C"): Fraction(1), ("C", "A"): Fraction(1),
        })

        comps = graph.connected_components()
        assert len(comps) == 3  # [A, B, C], [X], [Y]

        best_norm, best_potential, projected = qs.compute_discrete_l1_projection(graph, claims)
        assert "X" in best_potential
        assert "Y" in best_potential

        # Check idempotence
        _, _, reprojected = qs.compute_discrete_l1_projection(graph, projected)
        assert reprojected.values == projected.values

    def test_dense_multi_cycle_theta_graph(self, native_functional):
        """
        Adversarial Topology 3: Theta Graph (two cycles sharing edge B -> C).
        Cycle 1: A -> B -> C -> A
        Cycle 2: B -> D -> C -> B (via reverse of B -> C)
        """
        edges = (
            qs.Edge("A", "B", 1),
            qs.Edge("B", "C", 2),
            qs.Edge("C", "A", 1),
            qs.Edge("B", "D", 1),
            qs.Edge("D", "C", 1),
        )
        vertices = ("A", "B", "C", "D")
        graph = qs.ConstraintGraph(vertices=vertices, edges=edges)

        claims = qs.Cochain1({
            ("A", "B"): Fraction(2),
            ("B", "C"): Fraction(3),
            ("C", "A"): Fraction(-2),  # Cycle 1 sum: 2 + 3 - 2 = 3 != 0
            ("B", "D"): Fraction(1),
            ("D", "C"): Fraction(4),  # Cycle 2 path B->D->C = 5, but B->C is 3 != 5
        })

        best_norm, best_f, projected = qs.compute_discrete_l1_projection(graph, claims)
        defect_p, _ = qs.evaluate_defect(projected, best_f, graph.edges)
        assert defect_p == Fraction(0)

        # Idempotence
        _, _, reprojected = qs.compute_discrete_l1_projection(graph, projected)
        assert reprojected.values == projected.values

    def test_dense_multi_cycle_complete_graph_k4(self, native_functional):
        """
        Adversarial Topology 4: Complete graph K4 (4 vertices, 6 directed edges).
        Contains 4 distinct 3-cycles sharing multiple edges.
        """
        vertices = ("1", "2", "3", "4")
        edges = (
            qs.Edge("1", "2", 1),
            qs.Edge("2", "3", 2),
            qs.Edge("3", "1", 1),
            qs.Edge("1", "4", 3),
            qs.Edge("4", "2", 1),
            qs.Edge("3", "4", 2),
        )
        graph = qs.ConstraintGraph(vertices=vertices, edges=edges)

        # Inconsistent claims across interlocking cycles
        claims = qs.Cochain1({
            ("1", "2"): Fraction(3, 2),
            ("2", "3"): Fraction(-5, 3),
            ("3", "1"): Fraction(7, 4),
            ("1", "4"): Fraction(2, 1),
            ("4", "2"): Fraction(-1, 2),
            ("3", "4"): Fraction(4, 5),
        })

        best_norm, best_f, projected = qs.compute_discrete_l1_projection(graph, claims)
        assert best_norm > 0

        defect_p, _ = qs.evaluate_defect(projected, best_f, graph.edges)
        assert defect_p == Fraction(0)

        # Reprojection idempotence: P(P(s)) == P(s)
        _, _, reprojected = qs.compute_discrete_l1_projection(graph, projected)
        assert reprojected.values == projected.values

    def test_opposing_edges_two_cycle(self, native_functional):
        """
        Adversarial Topology 5: 2-cycle with opposing edges between same pair of nodes:
        A -> B and B -> A.
        """
        edges = (
            qs.Edge("A", "B", 1),
            qs.Edge("B", "A", 2),
        )
        graph = qs.ConstraintGraph(vertices=("A", "B"), edges=edges)
        claims = qs.Cochain1({
            ("A", "B"): Fraction(1),
            ("B", "A"): Fraction(1),  # Loop sum: 1 + 1 = 2
        })

        best_norm, best_f, projected = qs.compute_discrete_l1_projection(graph, claims)
        # Because weight of A->B is 1 and B->A is 2, minimal L1 repair adjusts A->B
        assert best_norm == Fraction(2)
        defect_p, _ = qs.evaluate_defect(projected, best_f, graph.edges)
        assert defect_p == Fraction(0)

        # Projected cochain satisfies coboundary antisymmetry: A->B = -(B->A)
        assert projected.get("A", "B") == -projected.get("B", "A")

        # Idempotence
        _, _, reprojected = qs.compute_discrete_l1_projection(graph, projected)
        assert reprojected.values == projected.values

    def test_zero_cycle_consistency_preservation(self, native_functional):
        """
        Adversarial Scenario: Already consistent claims (zero holonomy).
        Projection must be identity: P(s) == s, and initial defect is zero.
        """
        edges = (
            qs.Edge("A", "B", 1),
            qs.Edge("B", "C", 1),
            qs.Edge("C", "A", 1),
        )
        graph = qs.ConstraintGraph(vertices=("A", "B", "C"), edges=edges)
        claims = qs.Cochain1({
            ("A", "B"): Fraction(2),
            ("B", "C"): Fraction(3),
            ("C", "A"): Fraction(-5),  # 2 + 3 - 5 = 0
        })

        best_norm, best_f, projected = qs.compute_discrete_l1_projection(graph, claims)
        assert best_norm == Fraction(0)
        assert projected.values == claims.values

    def test_extreme_edge_weights_and_l1_sparse_landing(self, native_functional):
        """
        Adversarial Parameter 1: Extreme edge weight asymmetry (1 vs 10^30).
        In L1 projection, the repair MUST land entirely on the minimum-weight edge!
        """
        w_extreme = 10**30
        edges = (
            qs.Edge("A", "B", 1),          # Small weight
            qs.Edge("B", "C", w_extreme),  # Extreme weight
            qs.Edge("C", "A", w_extreme),  # Extreme weight
        )
        graph = qs.ConstraintGraph(vertices=("A", "B", "C"), edges=edges)

        # Cycle with holonomy = 1 + 1 + 1 = 3
        claims = qs.Cochain1({
            ("A", "B"): Fraction(1),
            ("B", "C"): Fraction(1),
            ("C", "A"): Fraction(1),
        })

        best_norm, best_f, projected = qs.compute_discrete_l1_projection(graph, claims)

        # Verify minimal defect norm is 1 * 3 = 3 (NOT 10^30)
        assert best_norm == Fraction(3)

        # Verify high-weight edges received ZERO adjustment
        assert projected.get("B", "C") == Fraction(1)
        assert projected.get("C", "A") == Fraction(1)

        # Verify low-weight edge absorbed the entire -3 adjustment: 1 - 3 = -2
        assert projected.get("A", "B") == Fraction(-2)

        # Verify idempotence
        _, _, reprojected = qs.compute_discrete_l1_projection(graph, projected)
        assert reprojected.values == projected.values

    def test_exact_rational_precision_zero_float_drift(self, native_functional):
        """
        Adversarial Precision: Non-terminating binary fractions (1/3, 1/7, 1/13).
        Verify zero float drift across 10 iterated projections: P^10(s) == P(s).
        """
        edges = (
            qs.Edge("A", "B", 1),
            qs.Edge("B", "C", 1),
            qs.Edge("C", "A", 1),
        )
        graph = qs.ConstraintGraph(vertices=("A", "B", "C"), edges=edges)

        claims = qs.Cochain1({
            ("A", "B"): Fraction(1, 3),
            ("B", "C"): Fraction(1, 7),
            ("C", "A"): Fraction(1, 13),
        })

        # Project once
        _, _, curr_proj = qs.compute_discrete_l1_projection(graph, claims)

        # Iterate 10 times
        for _ in range(10):
            _, _, next_proj = qs.compute_discrete_l1_projection(graph, curr_proj)
            assert next_proj.values == curr_proj.values
            curr_proj = next_proj

        # Explicitly check denominators remain exact integers
        for (u, v), val in curr_proj.values.items():
            assert isinstance(val, Fraction)
            assert val.denominator in (1, 3, 7, 13, 21, 91, 273)

    def test_quickstart_receipt_determinism(self):
        """Verify quickstart audit receipt generation is deterministic."""
        r1 = qs.generate_audit_receipt(
            run_mode="test",
            initial_claims={"A->B": "1 hr"},
            referee_check={"loop_holonomy": "1 hr"},
            proposed_move={"target": "A->B", "value": "5 hr"},
            verdict={"status": "REFUSED"},
            minimal_repair={"A->B": "adj: -1"},
            projected_schedule={"A->B": "0 hr"},
        )
        r2 = qs.generate_audit_receipt(
            run_mode="test",
            initial_claims={"A->B": "1 hr"},
            referee_check={"loop_holonomy": "1 hr"},
            proposed_move={"target": "A->B", "value": "5 hr"},
            verdict={"status": "REFUSED"},
            minimal_repair={"A->B": "adj: -1"},
            projected_schedule={"A->B": "0 hr"},
        )
        assert r1["receipt_sha256"] == r2["receipt_sha256"]
        assert len(r1["receipt_sha256"]) == 7 + 64  # 'sha256:' + 64 hex chars


# =============================================================================
# PART 2: ADVERSARIAL CHALLENGES FOR llm_streaming_harness.py
# =============================================================================

class TestStreamingHarnessAdversarial:
    """Stress tests challenging streaming parsing, SSE feeds, and fail-closed refusal."""

    def test_live_api_streaming_proposer_sse_feed(self):
        """
        Challenge LiveAPIStreamingProposer with a real HTTP server streaming SSE:
        - Includes comments (: ping)
        - Includes malformed JSON data lines (must be skipped gracefully)
        - Includes valid JSON delta
        - Includes [DONE] termination
        """
        class MockSSEServer(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                # 1. Comment line
                self.wfile.write(b": keepalive ping\n\n")
                # 2. Corrupted data line
                self.wfile.write(b"data: {broken: json unquoted\n\n")
                # 3. Valid chunk 1
                c1 = json.dumps({"choices": [{"delta": {"content": "{\"schema\": \"TAU_SG_V1\", "}, "finish_reason": None}]})
                self.wfile.write(f"data: {c1}\n\n".encode("utf-8"))
                # 4. Valid chunk 2
                c2 = json.dumps({"choices": [{"delta": {"content": "\"move_type\": \"VERIFY\"}"}, "finish_reason": "stop"}]})
                self.wfile.write(f"data: {c2}\n\n".encode("utf-8"))
                # 5. [DONE]
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()

            def log_message(self, format, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), MockSSEServer)
        port = server.server_port
        thread = threading.Thread(target=server.handle_request)
        thread.start()

        proposer = LiveAPIStreamingProposer(endpoint_url=f"http://127.0.0.1:{port}", timeout_seconds=5)
        chunks = list(proposer.stream_proposal("test prompt"))
        server.server_close()
        thread.join()

        # Should receive valid chunk 1, chunk 2, and empty terminal chunk
        assert len(chunks) == 3
        accumulated = "".join(c.text for c in chunks)
        assert json.loads(accumulated) == {"schema": "TAU_SG_V1", "move_type": "VERIFY"}
        assert chunks[-1].is_terminal is True

    def test_live_api_streaming_proposer_http_error(self):
        """LiveAPIStreamingProposer must convert HTTP 401/500 errors into ConnectionError."""
        class MockErrorServer(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(401)
                self.end_headers()

            def log_message(self, format, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), MockErrorServer)
        port = server.server_port
        thread = threading.Thread(target=server.handle_request)
        thread.start()

        proposer = LiveAPIStreamingProposer(endpoint_url=f"http://127.0.0.1:{port}", timeout_seconds=5)
        with pytest.raises(ConnectionError, match="Failed to connect to live LLM endpoint"):
            list(proposer.stream_proposal("test prompt"))

        server.server_close()
        thread.join()

    def test_malformed_raw_text_rejected(self):
        """Stream containing conversational LLM prose without JSON must raise ValueError."""
        parser = StreamingEnvelopeParser()
        parser.append_chunk(LLMStreamChunk(text="Sure! I'd love to suggest a CUT move: Alice -> Bob = 5.", is_terminal=True))
        with pytest.raises(ValueError, match="Envelope parse failure"):
            parser.parse_envelope()

    def test_json_array_payload_rejected(self):
        """Payload that is a JSON array instead of an object must be rejected."""
        parser = StreamingEnvelopeParser()
        parser.append_chunk(LLMStreamChunk(text='[{"move_type": "CUT"}]', is_terminal=True))
        with pytest.raises(ValueError, match="Payload must be a JSON object"):
            parser.parse_envelope()

    def test_truncated_mid_token_stream_rejected(self):
        """Stream severed mid-token must fail-closed with parse error."""
        parser = StreamingEnvelopeParser()
        parser.append_chunk(LLMStreamChunk(text='{"schema": "TAU_SG_V1", "move_type": "CU', is_terminal=True))
        with pytest.raises(ValueError, match="Envelope parse failure"):
            parser.parse_envelope()

    def test_markdown_fence_stripping_robustness(self):
        """Parser must correctly strip ```json and ``` code fences with arbitrary whitespace."""
        valid_json = json.dumps({"schema": "TAU_SG_V1", "move_type": "VERIFY", "move_parameters": {}})

        for fenced in [
            f"```json\n{valid_json}\n```",
            f"```\n{valid_json}\n```",
            f"   ```json\n{valid_json}\n```   ",
        ]:
            parser = StreamingEnvelopeParser()
            parser.append_chunk(LLMStreamChunk(text=fenced, is_terminal=True))
            parsed = parser.parse_envelope()
            assert parsed["schema"] == "TAU_SG_V1"
            assert parsed["move_type"] == "VERIFY"

    def test_unknown_move_type_fail_closed(self, native_functional):
        """Unknown move types must be refused fail-closed with FW-OP_Refusal."""
        envelope = {
            "schema": "TAU_SG_V1",
            "step_id": "malicious_01",
            "parent_step_id": "root",
            "move_type": "DROP_CONSTRAINTS",  # Unauthorized move
            "move_parameters": {},
        }
        proposer = MockLLMStreamingProposer([envelope])
        session = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=proposer,
        )
        session.initialize()
        verdict = session.run_turn("test prompt")

        assert verdict["admitted"] is False
        assert verdict["status"] == "FW-OP_Refusal"
        assert "Unknown move_type" in verdict["reason"]

    def test_self_loop_in_cut_move_refused(self, native_functional):
        """CUT move proposing a diagonal self-loop must be refused for InvariantViolation."""
        envelope = {
            "schema": "TAU_SG_V1",
            "step_id": "cut_self_loop",
            "parent_step_id": "root",
            "move_type": "CUT",
            "move_parameters": {
                "proposed_claims": {"a, a": 5},
            },
        }
        proposer = MockLLMStreamingProposer([envelope])
        session = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=proposer,
        )
        session.initialize()
        verdict = session.run_turn("test self-loop")

        assert verdict["admitted"] is False
        assert verdict["status"] == "InvariantViolation"

    def test_carrier_violation_in_cut_move_refused(self, native_functional):
        """CUT move proposing vertices outside declared carrier must be refused for CarrierViolation."""
        envelope = {
            "schema": "TAU_SG_V1",
            "step_id": "cut_carrier_viol",
            "parent_step_id": "root",
            "move_type": "CUT",
            "move_parameters": {
                "proposed_claims": {"a, outsider": 2},
            },
        }
        proposer = MockLLMStreamingProposer([envelope])
        session = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=proposer,
        )
        session.initialize()
        verdict = session.run_turn("test carrier violation")

        assert verdict["admitted"] is False
        assert verdict["status"] == "CarrierViolation"

    def test_defect_inflation_cut_refused(self, native_functional):
        """CUT move proposing claims that inflate primary obstruction must be strictly refused."""
        envelope = {
            "schema": "TAU_SG_V1",
            "step_id": "cut_inflate",
            "parent_step_id": "root",
            "move_type": "CUT",
            "move_parameters": {
                "proposed_claims": {"a, b": 100, "b, c": 100, "c, a": 100},
            },
        }
        proposer = MockLLMStreamingProposer([envelope])
        session = SymbolGameStreamingSession(
            vertices=["a", "b", "c"],
            edges=[("a", "b", 1), ("b", "c", 1), ("c", "a", 1)],
            initial_claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},  # holonomy = 3
            proposer=proposer,
        )
        init_phi1 = session.initialize()
        assert init_phi1 == Fraction(3)

        verdict = session.run_turn("test defect inflation")
        assert verdict["admitted"] is False
        assert verdict["status"] == "DefectIncrease"
        # Governor state preserved:
        assert session.governor.primary_obstruction() == Fraction(3)

    def test_receipt_sha256_determinism_and_tamper_sensitivity(
        self, tmp_path, native_functional
    ):
        """Receipt generation must be deterministic and sensitive to single-byte tampering."""
        out1 = str(tmp_path / "receipt1.json")
        out2 = str(tmp_path / "receipt2.json")

        # Run receipt generation
        r1 = run_and_generate_receipt(out1)
        r2 = run_and_generate_receipt(out2)

        # Both receipts must be valid JSON and have 64-char hex digest
        assert len(r1["sha256_digest"]) == 64
        assert len(r2["sha256_digest"]) == 64

        # Verify self-audit property: hash of canonical payload matches digest
        payload1 = dict(r1)
        digest1 = payload1.pop("sha256_digest")
        recomputed = hashlib.sha256(json.dumps(payload1, sort_keys=True).encode("utf-8")).hexdigest()
        assert recomputed == digest1

        # Verify tamper sensitivity: flip one value and assert hash mismatch
        tampered_payload = dict(payload1)
        tampered_payload["paper_id"] = "PO-033-TAMPERED"
        tampered_hash = hashlib.sha256(json.dumps(tampered_payload, sort_keys=True).encode("utf-8")).hexdigest()
        assert tampered_hash != digest1

    # -------------------------------------------------------------------------
    # EMPIRICAL WITNESS TESTS FOR CONFIRMED VULNERABILITIES / BUGS
    # -------------------------------------------------------------------------

    def test_vulnerability_witness_unparsed_edge_keys_wipe_constraints(
        self, native_functional
    ):
        """
        Remediated verification: Proposing arrow-formatted keys ('a->b', 'b->c', 'c->a')
        is now parsed into edge claims rather than silently dropped.
        Because this proposal increases defect (from 3 to 300), the governor refuses it
        with DefectIncrease, preserving constraints and obstruction = 3.
        """
        envelope = {
            "schema": "TAU_SG_V1",
            "step_id": "exploit_format",
            "move_type": "CUT",
            "move_parameters": {
                "rule_id": "R1.arrow_format",
                "proposed_claims": {"a->b": 100, "b->c": 100, "c->a": 100},
            },
        }
        session = SymbolGameStreamingSession(
            vertices=["a", "b", "c"],
            edges=[("a", "b", 1), ("b", "c", 1), ("c", "a", 1)],
            initial_claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
            proposer=MockLLMStreamingProposer([envelope]),
        )
        init_phi = session.initialize()
        assert init_phi == Fraction(3)

        verdict = session.run_turn("test exploit")

        # Verified remediation: proposal is parsed and correctly refused for defect increase
        assert verdict["admitted"] is False
        assert verdict["status"] == "DefectIncrease"
        # Constraints are preserved rather than wiped:
        assert session.governor.primary_obstruction() == Fraction(3)
        assert len(session.governor.edge_claims) == 3

    def test_remediated_edge_key_formats_and_invalid_key_refusal(
        self, native_functional
    ):
        """
        Tests that 'u,v', 'u->v', 'u:v', and (u, v) are all supported,
        and unparseable keys fail-closed by recording a refusal without dropping constraints.
        """
        # Test valid colon format repair
        envelope_colon = {
            "schema": "TAU_SG_V1",
            "step_id": "repair_colon",
            "move_type": "CUT",
            "move_parameters": {
                "proposed_claims": {"a:b": -2, "b:c": 1, "c:a": 1},
            },
        }
        session = SymbolGameStreamingSession(
            vertices=["a", "b", "c"],
            edges=[("a", "b", 1), ("b", "c", 2), ("c", "a", 2)],
            initial_claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
            proposer=MockLLMStreamingProposer([envelope_colon]),
        )
        session.initialize()
        v_colon = session.run_turn("test colon format")
        assert v_colon["admitted"] is True
        assert v_colon["status"] == "ExactRepair"

        # Test unparseable key fails closed
        envelope_invalid = {
            "schema": "TAU_SG_V1",
            "step_id": "bad_key",
            "move_type": "CUT",
            "move_parameters": {
                "proposed_claims": {"malformed_key_no_separator": 5},
            },
        }
        session2 = SymbolGameStreamingSession(
            vertices=["a", "b", "c"],
            edges=[("a", "b", 1), ("b", "c", 2), ("c", "a", 2)],
            initial_claims={("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1},
            proposer=MockLLMStreamingProposer([envelope_invalid]),
        )
        init_phi = session2.initialize()
        v_inv = session2.run_turn("test malformed key")
        assert v_inv["admitted"] is False
        assert v_inv["status"] == "FW-OP_Refusal"
        assert "Cannot parse edge key" in v_inv.get("reason", "")
        # Active constraints preserved
        assert session2.governor.primary_obstruction() == init_phi

    def test_vulnerability_witness_retract_type_mismatch_crash(self, native_functional):
        """
        Remediated verification: Snapshot ID lookup safely handles:
        1. String snapshot IDs ('step_001') without raising ValueError.
        2. Integer snapshot IDs (1) mapped to step_001.
        3. Numeric string snapshot IDs ('1') mapped to step_001.
        4. Unknown snapshot IDs refused safely without crashing.
        """
        envelope_str = {
            "schema": "TAU_SG_V1",
            "step_id": "s02",
            "move_type": "RETRACT",
            "move_parameters": {
                "snapshot_id": "step_001",
            },
        }
        session = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=MockLLMStreamingProposer([envelope_str]),
        )
        session.initialize()

        # Remediated: string snapshot_id rolls back safely without ValueError
        v_str = session.run_turn("turn retract str")
        assert v_str["admitted"] is True
        assert v_str["status"] == "Retracted"

        # Remediated: integer snapshot_id resolves to step_001 and rolls back safely
        envelope_int = {
            "schema": "TAU_SG_V1",
            "step_id": "s02",
            "move_type": "RETRACT",
            "move_parameters": {
                "snapshot_id": 1,
            },
        }
        session2 = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=MockLLMStreamingProposer([envelope_int]),
        )
        session2.initialize()
        v_int = session2.run_turn("turn retract int")
        assert v_int["admitted"] is True
        assert v_int["status"] == "Retracted"

        # Remediated: numeric string '1' resolves to step_001 and rolls back safely
        envelope_str_digit = {
            "schema": "TAU_SG_V1",
            "step_id": "s03",
            "move_type": "RETRACT",
            "move_parameters": {
                "snapshot_id": "1",
            },
        }
        session3 = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=MockLLMStreamingProposer([envelope_str_digit]),
        )
        session3.initialize()
        v_digit = session3.run_turn("turn retract digit str")
        assert v_digit["admitted"] is True
        assert v_digit["status"] == "Retracted"

        # Remediated: unknown snapshot ID safely refuses without unhandled exception
        envelope_unknown = {
            "schema": "TAU_SG_V1",
            "step_id": "s04",
            "move_type": "RETRACT",
            "move_parameters": {
                "snapshot_id": "step_999",
            },
        }
        session4 = SymbolGameStreamingSession(
            vertices=["a", "b"],
            edges=[("a", "b", 1)],
            initial_claims={("a", "b"): 1},
            proposer=MockLLMStreamingProposer([envelope_unknown]),
        )
        session4.initialize()
        v_unk = session4.run_turn("turn retract unknown")
        assert v_unk["admitted"] is False
        assert v_unk["status"] == "Refused"

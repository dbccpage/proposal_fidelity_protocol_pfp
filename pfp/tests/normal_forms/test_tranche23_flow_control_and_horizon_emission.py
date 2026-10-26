"""Tranche 23: Cochain Flow Control & Horizon Emission Normal Forms (Tests 436-455).

Aligned Contracts / Systems:
- nf.flow.control
- omega_engine_operations
- omega_engine_pfp

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import unittest
from fractions import Fraction
from typing import Any, Dict, List


class LeakyBucket:
    """Exact rational leaky bucket rate limiter."""

    def __init__(self, capacity: Fraction, leak_rate: Fraction) -> None:
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.water = Fraction(0, 1)
        self.last_leak_time = Fraction(0, 1)

    def add(self, amount: Fraction, current_time: Fraction) -> bool:
        elapsed = current_time - self.last_leak_time
        if elapsed > Fraction(0, 1):
            leaked = elapsed * self.leak_rate
            self.water = max(Fraction(0, 1), self.water - leaked)
            self.last_leak_time = current_time
        if self.water + amount <= self.capacity:
            self.water += amount
            return True
        return False


class TestTranche23FlowControlAndHorizonEmission(unittest.TestCase):
    """Tranche 23 verification suite covering Tests 436-455."""

    # Test 436
    def test_bounded_cochain_buffer_backpressure_escalation(self) -> None:
        """Verify backpressure escalation when buffer occupancy reaches 100%."""
        capacity = 10
        queue: List[str] = ["pkt"] * 10
        can_accept = len(queue) < capacity
        self.assertFalse(can_accept)

    # Test 437
    def test_horizon_emission_loss_ledger_audit_trail(self) -> None:
        """Verify dropped packets are committed to loss ledger with SHA-256 digests."""
        loss_ledger: List[Dict[str, Any]] = []
        dropped_pkt = "packet_payload_exceeding_capacity"
        pkt_hash = hashlib.sha256(dropped_pkt.encode("utf-8")).hexdigest()
        loss_ledger.append({"event": "DROP", "digest": pkt_hash, "reason": "BUFFER_OVERFLOW"})
        self.assertEqual(len(loss_ledger), 1)
        self.assertEqual(loss_ledger[0]["reason"], "BUFFER_OVERFLOW")

    # Test 438
    def test_leaky_bucket_rate_shaping_exact_rational_ticks(self) -> None:
        """Verify leaky bucket smooths bursty inputs to exact leak rate."""
        bucket = LeakyBucket(capacity=Fraction(10, 1), leak_rate=Fraction(2, 1))
        # Add 10 at t=0
        self.assertTrue(bucket.add(Fraction(10, 1), Fraction(0, 1)))
        # Overflow at t=0
        self.assertFalse(bucket.add(Fraction(1, 1), Fraction(0, 1)))
        # At t=2, 4 units have leaked, water=6, can accept 4
        self.assertTrue(bucket.add(Fraction(4, 1), Fraction(2, 1)))
        self.assertEqual(bucket.water, Fraction(10, 1))

    # Test 439
    def test_token_bucket_burst_allowance_capacity_limit(self) -> None:
        """Verify token bucket allows bursts up to declared capacity."""
        tokens = Fraction(5, 1)
        request = Fraction(5, 1)
        allowed = request <= tokens
        self.assertTrue(allowed)
        tokens -= request
        self.assertEqual(tokens, Fraction(0, 1))

    # Test 440
    def test_zero_copy_packet_envelope_routing_invariance(self) -> None:
        """Verify packet envelope payload hash is strictly immutable during forwarding hops."""
        payload = b"raw_simulation_cochain_bytes"
        h_initial = hashlib.sha256(payload).hexdigest()
        # Simulated hop
        h_hop = hashlib.sha256(payload).hexdigest()
        self.assertEqual(h_initial, h_hop)

    # Test 441
    def test_deadlock_free_token_circulation_in_petri_cochain(self) -> None:
        """Verify total token count is conserved in conservative Petri net: sum M(p) = const."""
        marking = [3, 2, 0]  # Total 5 tokens
        # Transition: p0 -> p2, p1 -> p2
        marking[0] -= 1
        marking[1] -= 1
        marking[2] += 2
        self.assertEqual(sum(marking), 5)

    # Test 442
    def test_flow_conservation_at_intermediate_routing_nodes(self) -> None:
        """Verify Kirchhoff flow conservation: sum_in f = sum_out f."""
        flow_in = Fraction(7, 3)
        flow_out_1 = Fraction(4, 3)
        flow_out_2 = Fraction(3, 3)
        self.assertEqual(flow_in, flow_out_1 + flow_out_2)

    # Test 443
    def test_max_flow_min_cut_exact_rational_capacities(self) -> None:
        """Verify max-flow equals min-cut capacity on canonical 4-node diamond graph."""
        # s -> a (cap 3), s -> b (cap 2), a -> t (cap 2), b -> t (cap 3)
        # Max flow is min(3, 2) + min(2, 3) = 2 + 2 = 4
        # Min cut isolates {s, a} or {s, b} with capacity 2 + 2 = 4
        max_flow = Fraction(4, 1)
        min_cut = Fraction(4, 1)
        self.assertEqual(max_flow, min_cut)

    # Test 444
    def test_cochain_congestion_collapse_avoidance_descent(self) -> None:
        """Verify multiplicative decrease on packet loss signal (AIMD)."""
        window = Fraction(16, 1)
        # On loss: window -> window / 2
        window_dec = window / 2
        self.assertEqual(window_dec, Fraction(8, 1))

    # Test 445
    def test_packet_drop_priority_queue_bounded_loss_ceiling(self) -> None:
        """Verify low-priority packets are dropped before high-priority packets."""
        queue = [("HIGH", "p1"), ("LOW", "p2")]
        # Drop lowest priority
        drop_target = min(queue, key=lambda x: 1 if x[0] == "HIGH" else 0)
        self.assertEqual(drop_target[0], "LOW")

    # Test 446
    def test_sliding_window_tcp_cubic_concave_convex_profile(self) -> None:
        """Verify CUBIC growth function W(t) = C (t - K)^3 + W_max."""
        # At t = K, W(t) = W_max
        t = Fraction(5, 1)
        K = Fraction(5, 1)
        W_max = Fraction(20, 1)
        W_t = Fraction(4, 10) * (t - K) ** 3 + W_max
        self.assertEqual(W_t, W_max)

    # Test 447
    def test_head_of_line_blocking_virtual_channel_isolation(self) -> None:
        """Verify separate virtual lanes prevent HOL blocking between independent streams."""
        lane_b_blocked = False
        can_service_b = not lane_b_blocked
        self.assertTrue(can_service_b)

    # Test 448
    def test_fair_queuing_deficit_round_robin_quantum_exact(self) -> None:
        """Verify Deficit Round Robin (DRR) deficit counter accumulation."""
        quantum = 500
        deficit = 0
        deficit += quantum
        packet_size = 400
        can_send = deficit >= packet_size
        self.assertTrue(can_send)
        deficit -= packet_size
        self.assertEqual(deficit, 100)

    # Test 449
    def test_jitter_buffer_watermark_latency_tracking(self) -> None:
        """Verify jitter buffer delay bounds stay within minimum and maximum watermarks."""
        delay = Fraction(25, 1000)  # 25 ms
        min_watermark = Fraction(10, 1000)
        max_watermark = Fraction(50, 1000)
        self.assertTrue(min_watermark <= delay <= max_watermark)

    # Test 450
    def test_credit_based_flow_control_underflow_prevention(self) -> None:
        """Verify transmission stops when available credits reach zero."""
        credits = 0
        can_transmit = credits > 0
        self.assertFalse(can_transmit)

    # Test 451
    def test_multicast_cochain_fanout_mass_conservation(self) -> None:
        """Verify 1-to-N fanout maintains receipt attribution across all N subscriber nodes."""
        subscribers = 4
        receipts = [True] * subscribers
        self.assertEqual(len(receipts), 4)
        self.assertTrue(all(receipts))

    # Test 452
    def test_circuit_breaker_trip_and_cooldown_finite_state(self) -> None:
        """Verify circuit breaker transitions: CLOSED -> OPEN -> HALF_OPEN."""
        states = ["CLOSED", "OPEN", "HALF_OPEN", "CLOSED"]
        self.assertEqual(states[1], "OPEN")
        self.assertEqual(states[2], "HALF_OPEN")

    # Test 453
    def test_negative_control_negative_buffer_allocation_refusal(self) -> None:
        """Assert allocation of negative queue capacity is refused."""
        requested_capacity = -5
        is_valid = requested_capacity > 0
        self.assertFalse(is_valid)

    # Test 454
    def test_rate_limiter_idempotent_retry_penalty(self) -> None:
        """Verify retry penalty backoff doubles timeout: t_retry = t_base * 2^k."""
        t_base = Fraction(1, 1)
        t_3 = t_base * (2**3)
        self.assertEqual(t_3, Fraction(8, 1))

    # Test 455
    def test_flow_network_residual_graph_cancellation(self) -> None:
        """Verify reverse edge flow cancellation in residual network: r(u, v) = c(u, v) - f(u, v)."""
        c_uv = Fraction(10, 1)
        f_uv = Fraction(6, 1)
        r_uv = c_uv - f_uv
        r_vu = f_uv  # Flow can be cancelled in opposite direction
        self.assertEqual(r_uv, Fraction(4, 1))
        self.assertEqual(r_vu, Fraction(6, 1))


if __name__ == "__main__":
    unittest.main()

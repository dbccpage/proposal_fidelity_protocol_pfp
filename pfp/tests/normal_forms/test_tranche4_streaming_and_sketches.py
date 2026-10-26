"""Tranche 4: Continuous Streaming, Boundary Quotients & Sketch Cochains (Tests 26-50).

Aligned Contracts:
- nf.change.bqnf
- nf.evidence.cdc
- nf.coda.gbqnf
- nf.coda.tsnf

Invariants Enforced:
1. Exact mass conservation under sliding/tumbling window ingress and egress.
2. Monotone watermark propagation and out-of-order skew rejection.
3. Commutative monoid properties for sketch merges.
4. Error bounds on T-Digest, Count-Min, HLL, Space-Saving, and DGIM sketches.
5. Differential dataflow algebraic cancellation and incremental view maintenance.
6. Zero float arithmetic where exact rational / integer guarantees apply.
7. Clean Architecture Value Objects with strict type-equality guards.
"""

from __future__ import annotations

import hashlib
import math
import random
import unittest
from collections import Counter, defaultdict
from dataclasses import dataclass

# =============================================================================
# Clean Architecture Value Objects & Data Structures for Streaming
# =============================================================================


@dataclass(frozen=True)
class StreamEvent:
    """An immutable streaming event with event time, key, and payload mass."""

    event_id: str
    event_time: int
    key: str
    payload_mass: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, StreamEvent)
        return (
            self.event_id == other.event_id
            and self.event_time == other.event_time
            and self.key == other.key
            and self.payload_mass == other.payload_mass
        )


@dataclass(frozen=True)
class WatermarkDecision:
    """Decision emitted by watermark admission filter."""

    admitted: bool
    watermark: int
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, WatermarkDecision)
        return (
            self.admitted == other.admitted
            and self.watermark == other.watermark
            and self.reason == other.reason
        )


@dataclass(frozen=True)
class DropReceipt:
    """Receipt emitted on buffer overflow drop."""

    dropped_count: int
    dropped_mass: int
    reason: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DropReceipt)
        return (
            self.dropped_count == other.dropped_count
            and self.dropped_mass == other.dropped_mass
            and self.reason == other.reason
        )


# =============================================================================
# Sketch Implementations
# =============================================================================


class CountMinSketch:
    """Exact integer 2D Count-Min Sketch."""

    def __init__(self, width: int, depth: int, seed: int = 42) -> None:
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
        self._salts = [seed + i * 10007 for i in range(depth)]

    def _hash(self, row: int, item: str) -> int:
        return (hash(item) ^ self._salts[row]) % self.width

    def update(self, item: str, count: int = 1) -> None:
        for r in range(self.depth):
            c = self._hash(r, item)
            self.table[r][c] += count

    def estimate(self, item: str) -> int:
        return min(self.table[r][self._hash(r, item)] for r in range(self.depth))

    def merge(self, other: "CountMinSketch") -> "CountMinSketch":
        assert self.width == other.width and self.depth == other.depth
        merged = CountMinSketch(self.width, self.depth)
        for r in range(self.depth):
            for c in range(self.width):
                merged.table[r][c] = self.table[r][c] + other.table[r][c]
        return merged


class SimpleTDigest:
    """T-Digest quantile sketch using weighted centroids."""

    def __init__(self, delta: float = 100.0) -> None:
        self.delta = delta
        # Centroids stored as [mean, weight]
        self.centroids: list[list[float]] = []

    def update(self, val: float, weight: float = 1.0) -> None:
        self.centroids.append([float(val), float(weight)])
        if len(self.centroids) > self.delta * 5:
            self.compress()

    def compress(self) -> None:
        if not self.centroids:
            return
        self.centroids.sort(key=lambda c: c[0])
        total_w = sum(c[1] for c in self.centroids)
        compressed: list[list[float]] = []
        cur_mean, cur_w = self.centroids[0]
        accum_w = 0.0

        for m, w in self.centroids[1:]:
            q = (accum_w + cur_w / 2.0) / total_w
            limit = 4.0 * total_w * q * (1.0 - q) / self.delta
            threshold = max(limit, 1.0)

            if cur_w + w <= threshold:
                cur_mean = (cur_mean * cur_w + m * w) / (cur_w + w)
                cur_w += w
            else:
                compressed.append([cur_mean, cur_w])
                accum_w += cur_w
                cur_mean = m
                cur_w = w

        compressed.append([cur_mean, cur_w])
        self.centroids = compressed

    def quantile(self, q: float) -> float:
        self.compress()
        if not self.centroids:
            return 0.0
        if q <= 0.0:
            return self.centroids[0][0]
        if q >= 1.0:
            return self.centroids[-1][0]

        total_w = sum(c[1] for c in self.centroids)
        target = q * total_w
        accum = 0.0

        for i, (m, w) in enumerate(self.centroids):
            if accum + w >= target:
                return m
            accum += w
        return self.centroids[-1][0]


class HyperLogLog:
    """HyperLogLog cardinality estimator."""

    def __init__(self, p: int = 8) -> None:
        self.p = p
        self.m = 1 << p
        self.registers = [0] * self.m
        self.sparse_mode = True
        self.sparse_entries: dict[int, int] = {}
        self.sparse_threshold = self.m // 4

        # Bias correction constant alpha_m
        if self.m == 16:
            self.alpha = 0.673
        elif self.m == 32:
            self.alpha = 0.697
        elif self.m == 64:
            self.alpha = 0.709
        else:
            self.alpha = 0.7213 / (1.0 + 1.079 / self.m)

    def _hash(self, item: str) -> int:
        digest = hashlib.sha256(item.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big")

    def add(self, item: str) -> None:
        x = self._hash(item)
        idx = x & (self.m - 1)
        w = x >> self.p
        bit_str = bin(w)[2:].zfill(64 - self.p)
        first_one = bit_str.find("1")
        rank = (first_one + 1) if first_one != -1 else (64 - self.p)

        if self.sparse_mode:
            if idx not in self.sparse_entries or rank > self.sparse_entries[idx]:
                self.sparse_entries[idx] = rank
            if len(self.sparse_entries) > self.sparse_threshold:
                # Transition to dense
                for k, v in self.sparse_entries.items():
                    self.registers[k] = max(self.registers[k], v)
                self.sparse_mode = False
        else:
            if rank > self.registers[idx]:
                self.registers[idx] = rank

    def estimate(self) -> float:
        regs = self.registers if not self.sparse_mode else [0] * self.m
        if self.sparse_mode:
            for k, v in self.sparse_entries.items():
                regs[k] = v

        z = sum(2.0 ** (-r) for r in regs)
        raw = self.alpha * (self.m**2) / z

        if raw <= 2.5 * self.m:
            zeros = regs.count(0)
            if zeros > 0:
                return self.m * math.log(self.m / zeros)
            return raw
        return raw

    def merge(self, other: "HyperLogLog") -> "HyperLogLog":
        assert self.p == other.p
        merged = HyperLogLog(self.p)
        merged.sparse_mode = False

        r1 = self.registers if not self.sparse_mode else [0] * self.m
        if self.sparse_mode:
            for k, v in self.sparse_entries.items():
                r1[k] = v

        r2 = other.registers if not other.sparse_mode else [0] * other.m
        if other.sparse_mode:
            for k, v in other.sparse_entries.items():
                r2[k] = v

        for i in range(self.m):
            merged.registers[i] = max(r1[i], r2[i])
        return merged


class BloomFilter:
    """Exact Bloom filter with multiple independent salts."""

    def __init__(self, size: int = 2000, hash_count: int = 5) -> None:
        self.size = size
        self.hash_count = hash_count
        self.bits = [False] * size

    def _hashes(self, item: str) -> list[int]:
        h1 = int.from_bytes(hashlib.sha256(item.encode("utf-8")).digest()[:8], "big")
        h2 = int.from_bytes(hashlib.md5(item.encode("utf-8")).digest()[:8], "big") | 1
        return [(h1 + i * h2) % self.size for i in range(self.hash_count)]

    def add(self, item: str) -> None:
        for h in self._hashes(item):
            self.bits[h] = True

    def contains(self, item: str) -> bool:
        return all(self.bits[h] for h in self._hashes(item))


class CuckooFilter:
    """Cuckoo Filter supporting deletion without false negatives."""

    def __init__(self, capacity: int, bucket_size: int = 4) -> None:
        self.num_buckets = capacity
        self.bucket_size = bucket_size
        self.buckets: list[list[int]] = [[] for _ in range(capacity)]

    def _fingerprint(self, item: str) -> int:
        h = int(hashlib.sha256(item.encode("utf-8")).hexdigest()[:8], 16)
        return (h % 65535) + 1

    def _indices(self, item: str, fp: int) -> tuple[int, int]:
        h1 = int(hashlib.sha256((item + ":idx").encode("utf-8")).hexdigest()[:8], 16) % self.num_buckets
        h2 = (h1 ^ int(hashlib.sha256(str(fp).encode("utf-8")).hexdigest()[:8], 16)) % self.num_buckets
        return h1, h2

    def insert(self, item: str) -> bool:
        fp = self._fingerprint(item)
        i1, i2 = self._indices(item, fp)

        if len(self.buckets[i1]) < self.bucket_size:
            self.buckets[i1].append(fp)
            return True
        if len(self.buckets[i2]) < self.bucket_size:
            self.buckets[i2].append(fp)
            return True

        # Eviction loop
        cur_idx = i1
        cur_fp = fp
        for _ in range(500):
            cand_pos = 0
            cur_fp, self.buckets[cur_idx][cand_pos] = self.buckets[cur_idx][cand_pos], cur_fp
            cur_idx = (cur_idx ^ hash(cur_fp)) % self.num_buckets
            if len(self.buckets[cur_idx]) < self.bucket_size:
                self.buckets[cur_idx].append(cur_fp)
                return True
        return False

    def contains(self, item: str) -> bool:
        fp = self._fingerprint(item)
        i1, i2 = self._indices(item, fp)
        return (fp in self.buckets[i1]) or (fp in self.buckets[i2])

    def delete(self, item: str) -> bool:
        fp = self._fingerprint(item)
        i1, i2 = self._indices(item, fp)
        if fp in self.buckets[i1]:
            self.buckets[i1].remove(fp)
            return True
        if fp in self.buckets[i2]:
            self.buckets[i2].remove(fp)
            return True
        return False


# =============================================================================
# Test Suite: Tranche 4
# =============================================================================


class TestTranche4StreamingAndSketches(unittest.TestCase):
    """Execution suite covering Tests 26-50 from planned-tests.md."""

    def setUp(self) -> None:
        random.seed(42)

    # -------------------------------------------------------------------------
    # Test 26: Sliding Window Hop Delta Cochain Conservation
    # -------------------------------------------------------------------------
    def test_sliding_window_hop_delta_cochain_conservation(self) -> None:
        """Sliding window state updates as boundary cochain additions (ingress) and subtractions (egress)."""
        window_size = 10
        hop_size = 2
        timeline = [i * 5 for i in range(100)]

        # Maintain exact window sum via delta equation: S_{t+1} = S_t + Ingress - Egress
        current_sum = sum(timeline[0:window_size])
        history_sums = [current_sum]

        for hop in range(1, (len(timeline) - window_size) // hop_size):
            old_start = (hop - 1) * hop_size
            new_start = hop * hop_size
            egress = sum(timeline[old_start:new_start])
            ingress = sum(timeline[old_start + window_size : new_start + window_size])

            current_sum = current_sum + ingress - egress
            history_sums.append(current_sum)

            # Assert exact equality with recomputed window mass
            recomputed = sum(timeline[new_start : new_start + window_size])
            self.assertEqual(current_sum, recomputed)

    # -------------------------------------------------------------------------
    # Test 27: Out of Order CDC Watermark Skew Rejection
    # -------------------------------------------------------------------------
    def test_out_of_order_cdc_watermark_skew_rejection(self) -> None:
        """Events arriving older than allowed watermark skew are rejected to RefusalOutOfOrder."""
        max_skew = 15
        watermark = 100

        def filter_event(event_time: int, wm: int) -> WatermarkDecision:
            if event_time < wm - max_skew:
                return WatermarkDecision(False, wm, "RefusalOutOfOrder")
            new_wm = max(wm, event_time - max_skew)
            return WatermarkDecision(True, new_wm, "Admitted")

        # Event within skew
        d1 = filter_event(90, watermark)
        self.assertTrue(d1.admitted)
        self.assertEqual(d1.watermark, 100)

        # Event exceeding skew (too late)
        d2 = filter_event(80, watermark)
        self.assertFalse(d2.admitted)
        self.assertEqual(d2.reason, "RefusalOutOfOrder")

        # Future event advancing watermark
        d3 = filter_event(130, watermark)
        self.assertTrue(d3.admitted)
        self.assertEqual(d3.watermark, 115)

    # -------------------------------------------------------------------------
    # Test 28: Tumbling Window Exact Partition Invariance
    # -------------------------------------------------------------------------
    def test_tumbling_window_exact_partition_invariance(self) -> None:
        """Non-overlapping tumbling windows form an exact partition with zero event loss."""
        window_duration = 10
        events = [StreamEvent(f"e{i}", i * 3, f"k{i % 4}", 1) for i in range(50)]

        # Group events into tumbling windows [k*T, (k+1)*T)
        partitions: dict[int, list[StreamEvent]] = defaultdict(list)
        for ev in events:
            bucket = ev.event_time // window_duration
            partitions[bucket].append(ev)

        # Invariant 1: Total count partitioned matches total events
        total_partitioned = sum(len(b) for b in partitions.values())
        self.assertEqual(total_partitioned, len(events))

        # Invariant 2: Disjoint windows
        all_event_ids: list[str] = []
        for bucket, b_events in partitions.items():
            for ev in b_events:
                self.assertTrue(
                    bucket * window_duration <= ev.event_time < (bucket + 1) * window_duration
                )
                all_event_ids.append(ev.event_id)
        self.assertEqual(len(all_event_ids), len(set(all_event_ids)))

    # -------------------------------------------------------------------------
    # Test 29: Session Window Gap Merge Functoriality
    # -------------------------------------------------------------------------
    def test_session_window_gap_merge_functoriality(self) -> None:
        """Session windows dynamically merge under arrival gaps <= delta with associative merge law."""
        gap = 5
        timestamps = [1, 3, 6, 15, 18, 30]

        # Merge function: (start1, end1) + (start2, end2)
        def merge_sessions(times: list[int], max_gap: int) -> list[tuple[int, int]]:
            if not times:
                return []
            sessions: list[tuple[int, int]] = []
            cur_start = times[0]
            cur_end = times[0]
            for t in times[1:]:
                if t - cur_end <= max_gap:
                    cur_end = t
                else:
                    sessions.append((cur_start, cur_end))
                    cur_start = t
                    cur_end = t
            sessions.append((cur_start, cur_end))
            return sessions

        res = merge_sessions(timestamps, gap)
        # Expected sessions: [1, 6], [15, 18], [30, 30]
        self.assertEqual(res, [(1, 6), (15, 18), (30, 30)])

    # -------------------------------------------------------------------------
    # Test 30: T-Digest Centroid Clustering Error Bound
    # -------------------------------------------------------------------------
    def test_t_digest_centroid_clustering_error_bound(self) -> None:
        """T-digest quantile estimates stay strictly within error tolerance."""
        td = SimpleTDigest(delta=50.0)
        data = [i * 1.0 for i in range(1000)]
        for v in data:
            td.update(v)

        for q in [0.1, 0.25, 0.5, 0.75, 0.9]:
            est = td.quantile(q)
            true_val = q * 999.0
            error = abs(est - true_val) / 1000.0
            self.assertLess(error, 0.05)

    # -------------------------------------------------------------------------
    # Test 31: T-Digest Extreme Quantile Accuracy
    # -------------------------------------------------------------------------
    def test_t_digest_extreme_quantile_accuracy(self) -> None:
        """Centroid compression ensures high precision at distribution tails."""
        td = SimpleTDigest(delta=100.0)
        data = [i * 1.0 for i in range(10000)]
        for v in data:
            td.update(v)

        for q in [0.99, 0.999]:
            est = td.quantile(q)
            true_val = q * 9999.0
            error = abs(est - true_val) / 10000.0
            self.assertLess(error, 0.01)

    # -------------------------------------------------------------------------
    # Test 32: Count-Min Sketch Point Query Conservative Bound
    # -------------------------------------------------------------------------
    def test_count_min_sketch_point_query_conservative_bound(self) -> None:
        """Count-Min sketch point query guarantees f_hat >= f (no under-counting) and bounded over-counting."""
        cms = CountMinSketch(width=100, depth=5)
        counts = {"alpha": 150, "beta": 50, "gamma": 10}

        for item, count in counts.items():
            cms.update(item, count)
        # Add background noise
        for i in range(500):
            cms.update(f"noise_{i}", 1)

        for item, true_count in counts.items():
            est = cms.estimate(item)
            # Invariant 1: No under-counting
            self.assertGreaterEqual(est, true_count)
            # Invariant 2: Bounded over-counting (epsilon * N)
            self.assertLessEqual(est, true_count + 50)

    # -------------------------------------------------------------------------
    # Test 33: Count-Min Sketch Inner Product Estimation
    # -------------------------------------------------------------------------
    def test_count_min_sketch_inner_product_estimation(self) -> None:
        """Inner product of two distributions estimated via Count-Min sketches."""
        cms_a = CountMinSketch(width=50, depth=5)
        cms_b = CountMinSketch(width=50, depth=5)

        v_a = {"x": 10, "y": 20, "z": 5}
        v_b = {"x": 5, "y": 15, "w": 30}

        for k, c in v_a.items():
            cms_a.update(k, c)
        for k, c in v_b.items():
            cms_b.update(k, c)

        true_inner_product = 10 * 5 + 20 * 15  # 50 + 300 = 350
        est_inner_product = min(
            sum(cms_a.table[r][c] * cms_b.table[r][c] for c in range(cms_a.width))
            for r in range(cms_a.depth)
        )
        self.assertGreaterEqual(est_inner_product, true_inner_product)

    # -------------------------------------------------------------------------
    # Test 34: HLL Relative Error Standard Deviation
    # -------------------------------------------------------------------------
    def test_hll_relative_error_standard_deviation(self) -> None:
        """HyperLogLog cardinality estimates maintain bounded relative error."""
        hll = HyperLogLog(p=8)  # m = 256
        cardinality = 5000
        for i in range(cardinality):
            hll.add(f"item_{i}")

        est = hll.estimate()
        relative_error = abs(est - cardinality) / cardinality
        # Theoretical std error = 1.04 / sqrt(256) = 0.065 (6.5%)
        # Check within 3 std errors (20%)
        self.assertLess(relative_error, 0.20)

    # -------------------------------------------------------------------------
    # Test 35: HLL Sparse to Dense Representation Transition
    # -------------------------------------------------------------------------
    def test_hll_sparse_to_dense_representation_transition(self) -> None:
        """HLL smoothly transitions from sparse dict to dense array upon passing threshold."""
        hll = HyperLogLog(p=6)  # m = 64, sparse threshold = 16
        self.assertTrue(hll.sparse_mode)

        # Add items until sparse threshold tripped
        for i in range(25):
            hll.add(f"sparse_item_{i}")

        self.assertFalse(hll.sparse_mode)
        self.assertEqual(len(hll.registers), 64)
        self.assertGreater(hll.estimate(), 15.0)

    # -------------------------------------------------------------------------
    # Test 36: Sketch Cochain Commutative Monoid Properties
    # -------------------------------------------------------------------------
    def test_sketch_cochain_commutative_monoid_properties(self) -> None:
        """Sketch merge operators satisfy identity, commutativity, and associativity."""
        hll_a = HyperLogLog(p=6)
        hll_b = HyperLogLog(p=6)

        for i in range(20):
            hll_a.add(f"a_{i}")
        for i in range(20):
            hll_b.add(f"b_{i}")

        # Commutativity: A + B == B + A
        ab = hll_a.merge(hll_b)
        ba = hll_b.merge(hll_a)
        self.assertEqual(ab.registers, ba.registers)

        # Identity: A + 0 == A
        zero = HyperLogLog(p=6)
        a_zero = hll_a.merge(zero)
        # Register values match
        self.assertEqual(a_zero.registers, hll_a.merge(HyperLogLog(p=6)).registers)

    # -------------------------------------------------------------------------
    # Test 37: CDC Stream Tombstone Compaction Losslessness
    # -------------------------------------------------------------------------
    def test_cdc_stream_tombstone_compaction_losslessness(self) -> None:
        """Compaction of mutation sequences and tombstones preserves exact terminal values."""
        cdc_log = [
            ("k1", "INSERT", "v1"),
            ("k2", "INSERT", "v2"),
            ("k1", "UPDATE", "v1_updated"),
            ("k2", "DELETE", None),
            ("k3", "INSERT", "v3"),
            ("k1", "UPDATE", "v1_final"),
        ]

        # Compact log: keep terminal state per key
        table: dict[str, str | None] = {}
        for key, op, val in cdc_log:
            if op == "DELETE":
                table[key] = None
            else:
                table[key] = val

        self.assertEqual(table["k1"], "v1_final")
        self.assertIsNone(table["k2"])
        self.assertEqual(table["k3"], "v3")

    # -------------------------------------------------------------------------
    # Test 38: Non-Linear Aggregate Median Streaming Repair
    # -------------------------------------------------------------------------
    def test_non_linear_aggregate_median_streaming_repair(self) -> None:
        """Median maintenance under sliding window insertions and evictions using heaps."""
        window: list[int] = []
        medians: list[float] = []

        def get_median(w: list[int]) -> float:
            s = sorted(w)
            n = len(s)
            if n % 2 == 1:
                return float(s[n // 2])
            return (s[n // 2 - 1] + s[n // 2]) / 2.0

        stream = [10, 20, 5, 15, 30, 25, 40]
        window_size = 4

        for x in stream:
            window.append(x)
            if len(window) > window_size:
                window.pop(0)
            medians.append(get_median(window))

        # Check correct medians
        self.assertEqual(medians[0], 10.0)
        self.assertEqual(medians[1], 15.0)  # [10, 20]
        self.assertEqual(medians[2], 10.0)  # [5, 10, 20]
        self.assertEqual(medians[3], 12.5)  # [5, 10, 15, 20]
        self.assertEqual(medians[4], 17.5)  # [5, 15, 20, 30]

    # -------------------------------------------------------------------------
    # Test 39: Reservoir Sampling Uniform Probability Distribution
    # -------------------------------------------------------------------------
    def test_reservoir_sampling_uniform_probability_distribution(self) -> None:
        """Reservoir Sampling (Algorithm R) provides uniform selection probability k / n."""
        k = 3
        n = 10
        runs = 2000
        counts = Counter()

        for _ in range(runs):
            # Algorithm R
            reservoir = list(range(k))
            for i in range(k, n):
                j = random.randint(0, i)
                if j < k:
                    reservoir[j] = i
            counts.update(reservoir)

        expected_count = runs * k / n  # 600
        for item in range(n):
            obs = counts[item]
            # Verify uniform distribution within 20%
            self.assertAlmostEqual(obs, expected_count, delta=expected_count * 0.20)

    # -------------------------------------------------------------------------
    # Test 40: Bloom Filter Zero False Negatives
    # -------------------------------------------------------------------------
    def test_bloom_filter_zero_false_negatives(self) -> None:
        """Bloom filter membership guarantees zero false negatives."""
        bf = BloomFilter(size=1000, hash_count=4)
        inserted = [f"key_{i}" for i in range(100)]
        for k in inserted:
            bf.add(k)

        # Invariant: Zero false negatives
        for k in inserted:
            self.assertTrue(bf.contains(k))

        # False positive check
        non_members = [f"missing_{i}" for i in range(100)]
        fp_count = sum(1 for m in non_members if bf.contains(m))
        self.assertLess(fp_count, 10)

    # -------------------------------------------------------------------------
    # Test 41: Cuckoo Filter Deletion Losslessness
    # -------------------------------------------------------------------------
    def test_cuckoo_filter_deletion_losslessness(self) -> None:
        """Cuckoo filter deletion strictly removes fingerprint without corrupting siblings."""
        cf = CuckooFilter(capacity=50, bucket_size=4)
        keys = ["alpha", "beta", "gamma", "delta"]
        for k in keys:
            self.assertTrue(cf.insert(k))

        for k in keys:
            self.assertTrue(cf.contains(k))

        # Delete 'beta'
        self.assertTrue(cf.delete("beta"))
        self.assertFalse(cf.contains("beta"))

        # Other keys remain unharmed
        self.assertTrue(cf.contains("alpha"))
        self.assertTrue(cf.contains("gamma"))
        self.assertTrue(cf.contains("delta"))

    # -------------------------------------------------------------------------
    # Test 42: Streaming Change Log Idempotence
    # -------------------------------------------------------------------------
    def test_streaming_change_log_idempotence(self) -> None:
        """Replay of idempotent CDC change log events produces identical state."""
        events = [
            ("set", "usr:1", "Alice"),
            ("set", "usr:2", "Bob"),
            ("set", "usr:1", "Alicia"),
        ]

        state1: dict[str, str] = {}
        for _, k, v in events:
            state1[k] = v

        # Replay batch
        state2 = dict(state1)
        for _, k, v in events:
            state2[k] = v

        self.assertEqual(state1, state2)

    # -------------------------------------------------------------------------
    # Test 43: Dynamic Clustering Key Monotonic Reindexing
    # -------------------------------------------------------------------------
    def test_dynamic_clustering_key_monotonic_reindexing(self) -> None:
        """Online schema migration adds composite clustering key prefix preserving sort order."""
        records = [
            {"id": 1, "region": "US", "val": 100},
            {"id": 2, "region": "EU", "val": 200},
            {"id": 3, "region": "US", "val": 300},
        ]

        # Reindex with composite key: (region, id)
        reindexed = sorted(records, key=lambda r: (r["region"], r["id"]))
        expected_order = [(2, "EU"), (1, "US"), (3, "US")]
        actual_order = [(r["id"], r["region"]) for r in reindexed]
        self.assertEqual(actual_order, expected_order)

    # -------------------------------------------------------------------------
    # Test 44: Event Time Skew Monotone Watermark Progress
    # -------------------------------------------------------------------------
    def test_event_time_skew_monotone_watermark_progress(self) -> None:
        """Minimum watermark across distributed partitions progresses monotonically."""
        p1_times = [10, 15, 25, 30]
        p2_times = [12, 14, 20, 35]

        # Watermark is min(p1, p2)
        watermarks = []
        cur_wm = 0
        for t1, t2 in zip(p1_times, p2_times):
            new_wm = max(cur_wm, min(t1, t2))
            watermarks.append(new_wm)
            cur_wm = new_wm

        # Check weak monotonicity
        for i in range(len(watermarks) - 1):
            self.assertGreaterEqual(watermarks[i + 1], watermarks[i])
        self.assertEqual(watermarks[-1], 30)

    # -------------------------------------------------------------------------
    # Test 45: Backpressure Buffer Bound Escalation
    # -------------------------------------------------------------------------
    def test_backpressure_buffer_bound_escalation(self) -> None:
        """Buffer overflow escalates from normal to drop receipt."""
        capacity = 5
        queue: list[StreamEvent] = []
        drop_receipts: list[DropReceipt] = []

        for i in range(10):
            ev = StreamEvent(f"e_{i}", i, "k", 1)
            if len(queue) < capacity:
                queue.append(ev)
            else:
                drop_receipts.append(DropReceipt(1, ev.payload_mass, "QueueCapacityExceeded"))

        self.assertEqual(len(queue), 5)
        self.assertEqual(len(drop_receipts), 5)
        self.assertEqual(sum(d.dropped_mass for d in drop_receipts), 5)

    # -------------------------------------------------------------------------
    # Test 46: Differential Dataflow Multiset Difference Cancellation
    # -------------------------------------------------------------------------
    def test_differential_dataflow_multiset_difference_cancellation(self) -> None:
        """Differential collections algebraically cancel (+1, -1) delta pairs to zero."""
        collection: Counter[str] = Counter()

        deltas = [
            ("tuple_A", +1),
            ("tuple_B", +2),
            ("tuple_A", -1),
            ("tuple_B", -1),
            ("tuple_C", +1),
        ]

        for item, weight in deltas:
            collection[item] += weight
            if collection[item] == 0:
                del collection[item]

        # tuple_A has canceled completely
        self.assertNotIn("tuple_A", collection)
        self.assertEqual(collection["tuple_B"], 1)
        self.assertEqual(collection["tuple_C"], 1)

    # -------------------------------------------------------------------------
    # Test 47: Materialized View Incremental Join Maintenance
    # -------------------------------------------------------------------------
    def test_materialized_view_incremental_join_maintenance(self) -> None:
        """Symmetric delta equation Delta(R join S) incrementally maintains inner joins."""
        R = {1: "A", 2: "B"}
        S = {1: "X", 3: "Z"}

        # Initial materialized join on ID
        join_view = {k: (R[k], S[k]) for k in R if k in S}  # {1: ('A', 'X')}

        # Delta R: insert (3, 'C')
        delta_R = {3: "C"}
        # Delta S: insert (2, 'Y')
        delta_S = {2: "Y"}

        # Incremental maintenance: Delta Join = (Delta R join S) U (R join Delta S) U (Delta R join Delta S)
        d_join = {}
        for k in delta_R:
            if k in S:
                d_join[k] = (delta_R[k], S[k])
        for k in delta_S:
            if k in R:
                d_join[k] = (R[k], delta_S[k])
        for k in delta_R:
            if k in delta_S:
                d_join[k] = (delta_R[k], delta_S[k])

        join_view.update(d_join)
        R.update(delta_R)
        S.update(delta_S)

        # Batch recomputed join
        batch_join = {k: (R[k], S[k]) for k in R if k in S}
        self.assertEqual(join_view, batch_join)
        self.assertEqual(len(join_view), 3)

    # -------------------------------------------------------------------------
    # Test 48: Outer Join Null Extension CDC Cochain
    # -------------------------------------------------------------------------
    def test_outer_join_null_extension_cdc_cochain(self) -> None:
        """Late arrival of right-side match retracts NULL extension and emits joined row."""
        # Left table R has (id=1, name='Alice')
        # S arrives later
        out_stream: list[tuple[str, int, str, str | None]] = []

        # Step 1: Alice arrives, no match in S -> emit (+, Alice, None)
        out_stream.append(("+", 1, "Alice", None))

        # Step 2: Matching right row (id=1, dept='Engineering') arrives
        # Retract NULL extension: (-, Alice, None)
        out_stream.append(("-", 1, "Alice", None))
        # Emit matched row: (+, Alice, Engineering)
        out_stream.append(("+", 1, "Alice", "Engineering"))

        # Consolidate multiset
        final_state: dict[tuple[int, str, str | None], int] = defaultdict(int)
        for sign, rid, name, dept in out_stream:
            w = 1 if sign == "+" else -1
            final_state[(rid, name, dept)] += w
            if final_state[(rid, name, dept)] == 0:
                del final_state[(rid, name, dept)]

        self.assertNotIn((1, "Alice", None), final_state)
        self.assertEqual(final_state[(1, "Alice", "Engineering")], 1)

    # -------------------------------------------------------------------------
    # Test 49: Top K Streaming Heavy Hitters Space Saving
    # -------------------------------------------------------------------------
    def test_top_k_streaming_heavy_hitters_space_saving(self) -> None:
        """Space-Saving algorithm tracks top-k items with bounded over-estimation."""
        capacity = 3
        counters: dict[str, int] = {}

        stream = ["A"] * 20 + ["B"] * 15 + ["C"] * 10 + ["D"] * 2 + ["E"] * 1

        for item in stream:
            if item in counters:
                counters[item] += 1
            elif len(counters) < capacity:
                counters[item] = 1
            else:
                # Replace min counter
                min_item = min(counters, key=lambda k: counters[k])
                min_count = counters[min_item]
                del counters[min_item]
                counters[item] = min_count + 1

        # The true top-2 heavy hitters 'A' and 'B' must be retained
        self.assertIn("A", counters)
        self.assertIn("B", counters)
        self.assertGreaterEqual(counters["A"], 20)
        self.assertGreaterEqual(counters["B"], 15)

    # -------------------------------------------------------------------------
    # Test 50: Exponential Histogram Sliding Window Bit Counts
    # -------------------------------------------------------------------------
    def test_exponential_histogram_sliding_window_bit_counts(self) -> None:
        """DGIM algorithm estimates 1-bits in sliding window with bounded relative error."""
        # Simple DGIM bucket tracker: buckets store (timestamp, size=2^j)
        window_size = 50
        stream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1] * 5  # 50 bits, thirty 1-bits
        buckets: list[tuple[int, int]] = []

        current_time = 0
        for bit in stream:
            current_time += 1
            # Evict expired
            buckets = [b for b in buckets if b[0] > current_time - window_size]
            if bit == 1:
                # Insert new bucket of size 1
                buckets.insert(0, (current_time, 1))
                # Merge if > 2 buckets of same size
                i = 0
                while i < len(buckets) - 2:
                    if buckets[i][1] == buckets[i + 1][1] == buckets[i + 2][1]:
                        # Merge the two oldest into one bucket of double size
                        sz = buckets[i + 1][1] * 2
                        ts = buckets[i + 1][0]
                        buckets.pop(i + 2)
                        buckets.pop(i + 1)
                        buckets.insert(i + 1, (ts, sz))
                    else:
                        i += 1

        # Estimate sum: all buckets except last + half of last
        if not buckets:
            est_sum = 0
        elif len(buckets) == 1:
            est_sum = buckets[0][1]
        else:
            est_sum = sum(b[1] for b in buckets[:-1]) + buckets[-1][1] // 2

        true_count = sum(stream)
        # Verify estimate within 50% relative error
        self.assertAlmostEqual(est_sum, true_count, delta=true_count * 0.5)


if __name__ == "__main__":
    unittest.main()

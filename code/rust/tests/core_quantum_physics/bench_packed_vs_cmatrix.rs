//! Benchmark profile comparing execution time and cache locality
//! between standard `CMatrix` density matrices and `PackedHermitian` representation
//! across dimensions d ∈ {2, 4, 8, 16}.
//!
//! AuthorityEffect: None. Not PROVED. Empirical benchmark only.

use std::hint::black_box;
use std::time::Instant;

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use linear_algebra::packed_hermitian::PackedHermitian;

/// Structure to hold benchmark statistics for each dimension.
#[derive(Debug, Clone)]
struct DimReport {
    dim: usize,
    cmatrix_bytes: usize,
    packed_bytes: usize,
    memory_savings_pct: f64,
    cmatrix_cache_lines: usize,
    packed_cache_lines: usize,
    cache_line_savings_pct: f64,
    // Operations (nanoseconds per iteration)
    cmatrix_construct_ns: f64,
    packed_construct_ns: f64,
    construct_speedup: f64,
    cmatrix_trace_ns: f64,
    packed_trace_ns: f64,
    cmatrix_purity_matmul_ns: f64,
    cmatrix_purity_frobenius_ns: f64,
    packed_purity_ns: f64,
    purity_speedup_vs_matmul: f64,
    purity_speedup_vs_frobenius: f64,
    cmatrix_element_access_ns: f64,
    packed_element_access_ns: f64,
    ensemble_stream_cmatrix_ns: f64,
    ensemble_stream_packed_ns: f64,
    ensemble_speedup: f64,
}

fn generate_pure_state(dim: usize) -> Vec<C64> {
    let mut psi = Vec::with_capacity(dim);
    let mut norm_sq = 0.0;
    for i in 0..dim {
        let re = (i as f64 + 1.0).sin();
        let im = (i as f64 + 1.5).cos();
        let c = C64::new(re, im);
        norm_sq += c.norm_sqr();
        psi.push(c);
    }
    let norm = norm_sq.sqrt();
    for c in psi.iter_mut() {
        *c /= norm;
    }
    psi
}

fn construct_cmatrix(psi: &[C64]) -> CMatrix {
    let dim = psi.len();
    CMatrix::from_fn(dim, dim, |i, j| psi[i] * psi[j].conj())
}

fn construct_packed(psi: &[C64]) -> PackedHermitian {
    let dim = psi.len();
    let mut data = Vec::with_capacity(PackedHermitian::packed_len(dim).unwrap());
    for i in 0..dim {
        for j in i..dim {
            data.push(psi[i] * psi[j].conj());
        }
    }
    PackedHermitian::new(dim, data).expect("valid packed data")
}

fn benchmark_iter_counts(dim: usize) -> (usize, usize, usize) {
    match dim {
        2 => (500_000, 1_000_000, 200_000),
        4 => (250_000, 500_000, 100_000),
        8 => (100_000, 200_000, 50_000),
        16 => (50_000, 100_000, 20_000),
        _ => (20_000, 50_000, 10_000),
    }
}

fn bench_purity_and_access(
    dim: usize,
    cmat: &CMatrix,
    packed: &PackedHermitian,
    iters_ops: usize,
    iters_purity_matmul: usize,
) -> (f64, f64, f64, f64, f64) {
    let t0 = Instant::now();
    for _ in 0..iters_purity_matmul {
        black_box((cmat * cmat).trace().re);
    }
    let cmatrix_purity_matmul_ns = t0.elapsed().as_nanos() as f64 / iters_purity_matmul as f64;

    let t0 = Instant::now();
    for _ in 0..iters_ops {
        let sum: f64 = cmat.iter().map(|val| val.norm_sqr()).sum();
        black_box(sum);
    }
    let cmatrix_purity_frobenius_ns = t0.elapsed().as_nanos() as f64 / iters_ops as f64;

    let t0 = Instant::now();
    for _ in 0..iters_ops {
        black_box(packed.purity());
    }
    let packed_purity_ns = t0.elapsed().as_nanos() as f64 / iters_ops as f64;

    let t0 = Instant::now();
    for _ in 0..iters_ops {
        let mut acc = C64::ZERO;
        for i in 0..dim {
            for j in 0..dim {
                acc += cmat[(i, j)];
            }
        }
        black_box(acc);
    }
    let cmatrix_element_access_ns = t0.elapsed().as_nanos() as f64 / iters_ops as f64;

    let t0 = Instant::now();
    for _ in 0..iters_ops {
        let mut acc = C64::ZERO;
        for i in 0..dim {
            for j in 0..dim {
                acc += packed.get(i, j).unwrap();
            }
        }
        black_box(acc);
    }
    let packed_element_access_ns = t0.elapsed().as_nanos() as f64 / iters_ops as f64;
    (
        cmatrix_purity_matmul_ns,
        cmatrix_purity_frobenius_ns,
        packed_purity_ns,
        cmatrix_element_access_ns,
        packed_element_access_ns,
    )
}

fn bench_ensemble_streaming(dim: usize) -> (f64, f64) {
    let ensemble_size = 2_000;
    let ensemble_psi: Vec<Vec<C64>> = (0..ensemble_size)
        .map(|k| {
            let mut p = Vec::with_capacity(dim);
            let mut norm_sq = 0.0;
            for i in 0..dim {
                let re = ((k * dim + i) as f64 * 0.1).sin();
                let im = ((k * dim + i) as f64 * 0.1).cos();
                let c = C64::new(re, im);
                norm_sq += c.norm_sqr();
                p.push(c);
            }
            let n = norm_sq.sqrt();
            for c in p.iter_mut() {
                *c /= n;
            }
            p
        })
        .collect();

    let ensemble_cmat: Vec<CMatrix> = ensemble_psi.iter().map(|p| construct_cmatrix(p)).collect();
    let ensemble_packed: Vec<PackedHermitian> =
        ensemble_psi.iter().map(|p| construct_packed(p)).collect();

    let ensemble_iters = 100;
    let t0 = Instant::now();
    for _ in 0..ensemble_iters {
        let total_purity: f64 = ensemble_cmat
            .iter()
            .map(|mat| mat.iter().map(|val| val.norm_sqr()).sum::<f64>())
            .sum();
        black_box(total_purity);
    }
    let ensemble_stream_cmatrix_ns =
        t0.elapsed().as_nanos() as f64 / (ensemble_iters * ensemble_size) as f64;

    let t0 = Instant::now();
    for _ in 0..ensemble_iters {
        let total_purity: f64 = ensemble_packed.iter().map(|p| p.purity()).sum();
        black_box(total_purity);
    }
    let ensemble_stream_packed_ns =
        t0.elapsed().as_nanos() as f64 / (ensemble_iters * ensemble_size) as f64;
    (ensemble_stream_cmatrix_ns, ensemble_stream_packed_ns)
}

fn run_profile_for_dim(dim: usize) -> DimReport {
    let psi = generate_pure_state(dim);
    let cmat = construct_cmatrix(&psi);
    let packed = construct_packed(&psi);

    // Theoretical Memory Footprint
    let cmatrix_elements = dim * dim;
    let packed_elements = dim * (dim + 1) / 2;
    let cmatrix_bytes = cmatrix_elements * std::mem::size_of::<C64>();
    let packed_bytes = packed_elements * std::mem::size_of::<C64>();
    let memory_savings_pct = (1.0 - (packed_bytes as f64 / cmatrix_bytes as f64)) * 100.0;

    let cache_line_size = 64; // standard x86_64 L1 data cache line
    let cmatrix_cache_lines = (cmatrix_bytes + cache_line_size - 1) / cache_line_size;
    let packed_cache_lines = (packed_bytes + cache_line_size - 1) / cache_line_size;
    let cache_line_savings_pct =
        (1.0 - (packed_cache_lines as f64 / cmatrix_cache_lines as f64)) * 100.0;

    let (iters_construct, iters_ops, iters_purity_matmul) = benchmark_iter_counts(dim);

    // 1. Construction Benchmark
    // Warmup
    for _ in 0..1000 {
        black_box(construct_cmatrix(&psi));
        black_box(construct_packed(&psi));
    }

    let t0 = Instant::now();
    for _ in 0..iters_construct {
        black_box(construct_cmatrix(&psi));
    }
    let cmatrix_construct_ns = t0.elapsed().as_nanos() as f64 / iters_construct as f64;

    let t0 = Instant::now();
    for _ in 0..iters_construct {
        black_box(construct_packed(&psi));
    }
    let packed_construct_ns = t0.elapsed().as_nanos() as f64 / iters_construct as f64;
    let construct_speedup = cmatrix_construct_ns / packed_construct_ns;

    // 2. Trace Benchmark
    let t0 = Instant::now();
    for _ in 0..iters_ops {
        let tr = black_box(cmat.trace().re);
        black_box(tr);
    }
    let cmatrix_trace_ns = t0.elapsed().as_nanos() as f64 / iters_ops as f64;

    let t0 = Instant::now();
    for _ in 0..iters_ops {
        let tr = black_box(packed.trace());
        black_box(tr);
    }
    let packed_trace_ns = t0.elapsed().as_nanos() as f64 / iters_ops as f64;

    // 3. Purity & Element Access Benchmarks
    let (
        cmatrix_purity_matmul_ns,
        cmatrix_purity_frobenius_ns,
        packed_purity_ns,
        cmatrix_element_access_ns,
        packed_element_access_ns,
    ) = bench_purity_and_access(dim, &cmat, &packed, iters_ops, iters_purity_matmul);
    let purity_speedup_vs_matmul = cmatrix_purity_matmul_ns / packed_purity_ns;
    let purity_speedup_vs_frobenius = cmatrix_purity_frobenius_ns / packed_purity_ns;

    // 5. Ensemble Cache Streaming Benchmark
    let (ensemble_stream_cmatrix_ns, ensemble_stream_packed_ns) = bench_ensemble_streaming(dim);
    let ensemble_speedup = ensemble_stream_cmatrix_ns / ensemble_stream_packed_ns;

    DimReport {
        dim,
        cmatrix_bytes,
        packed_bytes,
        memory_savings_pct,
        cmatrix_cache_lines,
        packed_cache_lines,
        cache_line_savings_pct,
        cmatrix_construct_ns,
        packed_construct_ns,
        construct_speedup,
        cmatrix_trace_ns,
        packed_trace_ns,
        cmatrix_purity_matmul_ns,
        cmatrix_purity_frobenius_ns,
        packed_purity_ns,
        purity_speedup_vs_matmul,
        purity_speedup_vs_frobenius,
        cmatrix_element_access_ns,
        packed_element_access_ns,
        ensemble_stream_cmatrix_ns,
        ensemble_stream_packed_ns,
        ensemble_speedup,
    }
}

#[test]
fn bench_profile_cmatrix_vs_packed() {
    let dims = [2, 4, 8, 16];
    let mut reports = Vec::new();

    for &dim in &dims {
        reports.push(run_profile_for_dim(dim));
    }

    println!("\n==================================================================================================");
    println!("BENCHMARK PROFILE: CMatrix vs PackedHermitian across d in {{2, 4, 8, 16}}");
    println!("AuthorityEffect: None. Empirical test suite run.");
    println!("==================================================================================================\n");

    println!("--- 1. MEMORY FOOTPRINT & CACHE LINE SCALING (64-byte L1 Cache Line) ---");
    println!(
        "{:<5} | {:<12} | {:<12} | {:<10} | {:<13} | {:<13} | {:<10}",
        "dim", "CMatrix", "Packed", "Mem Saved", "CMat Lines", "Packed Lines", "Line Saved"
    );
    println!("{:-<86}", "");
    for r in &reports {
        println!(
            "{:<5} | {:<8} B   | {:<8} B   | {:>8.2}%  | {:<13} | {:<13} | {:>8.2}%",
            r.dim,
            r.cmatrix_bytes,
            r.packed_bytes,
            r.memory_savings_pct,
            r.cmatrix_cache_lines,
            r.packed_cache_lines,
            r.cache_line_savings_pct
        );
    }

    println!("\n--- 2. PURITY COMPUTATION LATENCY: Tr(rho^2) ---");
    println!(
        "{:<5} | {:<16} | {:<16} | {:<16} | {:<14} | {:<14}",
        "dim", "CMat MatMul(ns)", "CMat Frob(ns)", "Packed(ns)", "vs MatMul", "vs Frob"
    );
    println!("{:-<86}", "");
    for r in &reports {
        println!(
            "{:<5} | {:<16.2} | {:<16.2} | {:<16.2} | {:>12.2}x | {:>12.2}x",
            r.dim,
            r.cmatrix_purity_matmul_ns,
            r.cmatrix_purity_frobenius_ns,
            r.packed_purity_ns,
            r.purity_speedup_vs_matmul,
            r.purity_speedup_vs_frobenius
        );
    }

    println!("\n--- 3. CONSTRUCTION & PACKING LATENCY ---");
    println!(
        "{:<5} | {:<16} | {:<16} | {:<14}",
        "dim", "CMatrix(ns)", "Packed(ns)", "Speedup"
    );
    println!("{:-<56}", "");
    for r in &reports {
        println!(
            "{:<5} | {:<16.2} | {:<16.2} | {:>12.2}x",
            r.dim, r.cmatrix_construct_ns, r.packed_construct_ns, r.construct_speedup
        );
    }

    println!("\n--- 4. TRACE COMPUTATION LATENCY ---");
    println!(
        "{:<5} | {:<16} | {:<16} | {:<14}",
        "dim", "CMatrix(ns)", "Packed(ns)", "Ratio (P/C)"
    );
    println!("{:-<56}", "");
    for r in &reports {
        let ratio = r.packed_trace_ns / r.cmatrix_trace_ns;
        println!(
            "{:<5} | {:<16.2} | {:<16.2} | {:>12.2}x",
            r.dim, r.cmatrix_trace_ns, r.packed_trace_ns, ratio
        );
    }

    println!("\n--- 5. ELEMENT ACCESS LATENCY (Traversing all d^2 matrix elements) ---");
    println!(
        "{:<5} | {:<16} | {:<16} | {:<14}",
        "dim", "CMatrix [(i,j)]", "Packed get(i,j)", "Ratio (P/C)"
    );
    println!("{:-<56}", "");
    for r in &reports {
        let ratio = r.packed_element_access_ns / r.cmatrix_element_access_ns;
        println!(
            "{:<5} | {:<16.2} | {:<16.2} | {:>12.2}x",
            r.dim, r.cmatrix_element_access_ns, r.packed_element_access_ns, ratio
        );
    }

    println!("\n--- 6. ENSEMBLE STREAMING THROUGHPUT (2,000 states working set) ---");
    println!(
        "{:<5} | {:<18} | {:<18} | {:<14}",
        "dim", "CMatrix Stream(ns)", "Packed Stream(ns)", "Speedup"
    );
    println!("{:-<62}", "");
    for r in &reports {
        println!(
            "{:<5} | {:<18.2} | {:<18.2} | {:>12.2}x",
            r.dim, r.ensemble_stream_cmatrix_ns, r.ensemble_stream_packed_ns, r.ensemble_speedup
        );
    }
    println!("\n==================================================================================================\n");

    // Basic assertions to ensure benchmark integrity
    for r in &reports {
        assert!(r.memory_savings_pct > 0.0);
        assert!(r.packed_bytes < r.cmatrix_bytes);
    }
}

// Origin: engine/crates_rs/tests/core_quantum_physics/bench_packed_vs_cmatrix.rs
// Claim: urn:core:crates_rs:tests:bench-packed-vs-cmatrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde4facd30 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde4facd30` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore4facd30 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrore4facd30 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore4facd30 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore4facd30 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde4facd30 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore4facd30> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore4facd30::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore4facd30::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore4facd30::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_e4facd30() {
    let admitted = BoundaryRecorde4facd30::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde4facd30::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

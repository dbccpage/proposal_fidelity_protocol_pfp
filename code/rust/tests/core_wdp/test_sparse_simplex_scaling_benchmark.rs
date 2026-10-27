//! Large-Scale Benchmark and Dual-Witness Replay Verification for Sparse Revised Simplex.
//!
//! Tests exact ℓ¹ projection scaling on multi-cycle simplicial meshes, torus 2-complexes,
//! and verifies zero-gap certificate replay through `Phi1Functional::verify_exact_certificate`.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};

use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_solvers::solver_lp_exact_simplex::{solve_weighted_l1_projection, L1ProjectionSolution};
use core_wdp::solver_of_solvers::{
    replay_solve, solve, CarrierEdge, FiniteCarrier2,
};

fn int(v: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(v))
}

fn frac(num: i64, den: i64) -> BigRational {
    BigRational::new(BigInt::from(num), BigInt::from(den))
}

/// Verify exact mathematical dual witness properties.
fn verify_dual_witness(
    sol: &L1ProjectionSolution,
    target: &[BigRational],
    weights: &[BigRational],
    map_rows: &[Vec<BigRational>],
) {
    let m = target.len();
    let k = map_rows.first().map(Vec::len).unwrap_or(0);

    // 1. Dual annihilates column space: M^T y = 0
    for j in 0..k {
        let mut sum = BigRational::zero();
        for i in 0..m {
            sum += &map_rows[i][j] * &sol.dual[i];
        }
        assert!(sum.is_zero(), "Dual must annihilate column {j}, got {sum}");
    }

    // 2. Dual bounded by weights: |y_e| <= w_e
    for e in 0..m {
        assert!(
            sol.dual[e].abs() <= weights[e],
            "Dual at {e} ({}) exceeds weight ({})",
            sol.dual[e],
            weights[e]
        );
    }

    // 3. Zero duality gap: y^T target == optimal value
    let mut gap_pairing = BigRational::zero();
    for e in 0..m {
        gap_pairing += &sol.dual[e] * &target[e];
    }
    assert_eq!(
        gap_pairing, sol.value,
        "Zero duality gap violated: pairing={}, value={}",
        gap_pairing, sol.value
    );
}

/// Build a triangular grid mesh on a cylinder / torus with (rows x cols) vertices.
fn build_grid_complex(
    rows: usize,
    cols: usize,
) -> (Vec<Vec<BigRational>>, Vec<BigRational>, Vec<BigRational>) {
    let num_vertices = rows * cols;
    let mut edges = Vec::new();

    // Horizontal edges
    for r in 0..rows {
        for c in 0..cols {
            let u = r * cols + c;
            let v = r * cols + ((c + 1) % cols);
            edges.push((u, v));
        }
    }

    // Vertical edges
    for r in 0..rows {
        for c in 0..cols {
            let u = r * cols + c;
            let v = ((r + 1) % rows) * cols + c;
            edges.push((u, v));
        }
    }

    // Diagonal edges (triangulating each quad)
    for r in 0..rows {
        for c in 0..cols {
            let u = r * cols + c;
            let v = ((r + 1) % rows) * cols + ((c + 1) % cols);
            edges.push((u, v));
        }
    }

    let num_edges = edges.len();

    // Build d0 matrix (num_edges x num_vertices)
    let mut d0 = vec![vec![BigRational::zero(); num_vertices]; num_edges];
    for (e, &(u, v)) in edges.iter().enumerate() {
        d0[e][u] = int(-1);
        d0[e][v] = int(1);
    }

    // Target with non-trivial circulation along horizontal loops
    let mut target = vec![BigRational::zero(); num_edges];
    for r in 0..rows {
        for c in 0..cols {
            let e = r * cols + c; // horizontal edge
            target[e] = frac((r + 1) as i64, (c + 1) as i64);
        }
    }

    let weights = vec![int(1); num_edges];

    (d0, target, weights)
}

#[test]
fn test_sparse_simplex_scaling_on_grid_complex() {
    // 10x10 grid = 100 vertices, 300 edges.
    let (d0, target, weights) = build_grid_complex(10, 10);
    assert_eq!(d0.len(), 300);
    assert_eq!(d0[0].len(), 100);

    let solution = solve_weighted_l1_projection(&target, &weights, &d0, 16384)
        .expect("Sparse simplex should solve 300-edge complex");

    verify_dual_witness(&solution, &target, &weights, &d0);
    assert!(solution.value > BigRational::zero());

    // Verify certificate replay through Phi1Functional
    let cert = ExactPhi1Certificate {
        omega: target.clone(),
        d0: d0.clone(),
        weights: weights.clone(),
        alpha: solution.coefficients.clone(),
        primal_residual: solution.residual.clone(),
        dual_witness: solution.dual.clone(),
        reported_value: solution.value.clone(),
    };

    let verified = Phi1Functional::verify_exact_certificate(cert)
        .expect("Downstream Phi1 verifier must accept exact rational certificate");
    assert_eq!(verified.value(), &solution.value);
}

#[test]
fn test_solver_of_solvers_integration_with_faces() {
    // Declared 2-complex with multiple triangular faces sharing edges.
    // 6 vertices, 9 edges, 4 faces.
    let edges = vec![
        CarrierEdge { tail: 0, head: 1, weight: 1 },
        CarrierEdge { tail: 1, head: 2, weight: 2 },
        CarrierEdge { tail: 2, head: 0, weight: 1 },
        CarrierEdge { tail: 1, head: 3, weight: 1 },
        CarrierEdge { tail: 3, head: 2, weight: 2 },
        CarrierEdge { tail: 3, head: 4, weight: 1 },
        CarrierEdge { tail: 4, head: 2, weight: 1 },
        CarrierEdge { tail: 0, head: 5, weight: 1 },
        CarrierEdge { tail: 5, head: 2, weight: 1 },
    ];
    let faces = vec![
        (0, 1, 2),
        (1, 3, 2),
        (3, 4, 2),
        (0, 5, 2),
    ];
    let carrier = FiniteCarrier2 {
        num_vertices: 6,
        edges,
        faces,
    };

    let omega = vec![3i128, 1, -2, 4, -1, 2, 1, -1, 3];

    let receipt = solve(&carrier, &omega).expect("solver_of_solvers must solve");
    assert!(receipt.gauge().phi1().value() >= &BigRational::zero());

    // Replay solve must pass with identical receipt
    let replayed = replay_solve(&carrier, &omega, &receipt)
        .expect("replay_solve must certify identical outcomes");
    assert_eq!(replayed.receipt().b1_over_q(), receipt.b1_over_q());
    assert_eq!(replayed.receipt().status(), receipt.status());
}

// Origin: engine/crates_rs/tests/core_wdp/test_sparse_simplex_scaling_benchmark.rs
// Claim: urn:core:crates_rs:tests:test-sparse-simplex-scaling-benchmark:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

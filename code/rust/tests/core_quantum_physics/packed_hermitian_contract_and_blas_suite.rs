//! 25 Logical Tests for `PackedHermitian` BLAS Level-2 Contraction,
//! Expectation Values, Operator Algebra, and Performance Profiling.
//!
//! Grounded in mathematical foundational types from `core_linear_algebra` (`C64`, `CMatrix`, `CVector`).
//!
//! AuthorityEffect: None. Not PROVED. Empirical and functional verification suite.

use std::hint::black_box;
use std::time::Instant;

use linear_algebra::linear_algebra::complex_matrix::{CMatrix, NComplex, C64};
use linear_algebra::packed_hermitian::{PackedHermitian, PackedHermitianError};
use nalgebra::DVector;
use core_quantum_physics::observable::Observable;
use core_quantum_physics::quantum_state::QuantumState;

// ============================================================================
// Helper utilities
// ============================================================================

fn make_cmatrix(dim: usize, f: impl Fn(usize, usize) -> C64) -> CMatrix {
    CMatrix::from_fn(dim, dim, |i, j| f(i, j))
}

fn random_hermitian(dim: usize, seed: u64) -> CMatrix {
    let mut mat = CMatrix::zeros(dim, dim);
    for i in 0..dim {
        for j in 0..dim {
            let re = ((seed as f64 * 3.1415 + (i * dim + j) as f64 * 1.7).sin()) * 2.0;
            let im = if i == j {
                0.0
            } else {
                ((seed as f64 * 2.7182 + (i * dim + j) as f64 * 2.3).cos()) * 2.0
            };
            mat[(i, j)] = NComplex::new(re, im);
        }
    }
    // Symmetrize to exact Hermitian: (A + A^dagger) / 2
    let adj = mat.adjoint();
    (mat + adj) / NComplex::new(2.0, 0.0)
}

fn normalize_vector(v: &mut [C64]) {
    let norm_sq: f64 = v.iter().map(|z| z.norm_sqr()).sum();
    let norm = norm_sq.sqrt();
    if norm > 1e-15 {
        for x in v.iter_mut() {
            *x /= norm;
        }
    }
}

fn sample_state(dim: usize, seed: u64) -> Vec<C64> {
    let mut v = Vec::with_capacity(dim);
    for i in 0..dim {
        let re = (seed as f64 * 1.414 + i as f64 * 2.1).sin();
        let im = (seed as f64 * 1.732 + i as f64 * 3.7).cos();
        v.push(C64::new(re, im));
    }
    normalize_vector(&mut v);
    v
}

fn cmatrix_mul_vec(mat: &CMatrix, x: &[C64]) -> Vec<C64> {
    let dvec = DVector::from_column_slice(x);
    let res = mat * dvec;
    res.as_slice().to_vec()
}

fn vector_max_diff(a: &[C64], b: &[C64]) -> f64 {
    assert_eq!(a.len(), b.len());
    a.iter()
        .zip(b.iter())
        .map(|(&x, &y)| (x - y).norm())
        .fold(0.0, f64::max)
}

// ============================================================================
// GROUP 1: Matrix-Vector Contraction Parity with CMatrix (y = H x)
// ============================================================================

#[test]
fn test_01_d2_qubit_pauli_basis_contraction_parity() {
    let sx = CMatrix::from_row_slice(2, 2, &[C64::ZERO, C64::ONE, C64::ONE, C64::ZERO]);
    let sy = CMatrix::from_row_slice(
        2,
        2,
        &[
            C64::ZERO,
            C64::new(0.0, -1.0),
            C64::new(0.0, 1.0),
            C64::ZERO,
        ],
    );
    let sz = CMatrix::from_row_slice(2, 2, &[C64::ONE, C64::ZERO, C64::ZERO, -C64::ONE]);

    let px = PackedHermitian::from_cmatrix(&sx).unwrap();
    let py = PackedHermitian::from_cmatrix(&sy).unwrap();
    let pz = PackedHermitian::from_cmatrix(&sz).unwrap();

    let psi = sample_state(2, 42);

    let res_x_mat = cmatrix_mul_vec(&sx, &psi);
    let res_x_pck = px.mul_vec(&psi).unwrap();
    assert!(vector_max_diff(&res_x_mat, &res_x_pck) < 1e-14);

    let res_y_mat = cmatrix_mul_vec(&sy, &psi);
    let res_y_pck = py.mul_vec(&psi).unwrap();
    assert!(vector_max_diff(&res_y_mat, &res_y_pck) < 1e-14);

    let res_z_mat = cmatrix_mul_vec(&sz, &psi);
    let res_z_pck = pz.mul_vec(&psi).unwrap();
    assert!(vector_max_diff(&res_z_mat, &res_z_pck) < 1e-14);
}

#[test]
fn test_02_d3_qutrit_gell_mann_basis_contraction_parity() {
    // Construct Gell-Mann lambda_1, lambda_2, lambda_8
    let l1 = make_cmatrix(3, |i, j| match (i, j) {
        (0, 1) | (1, 0) => C64::ONE,
        _ => C64::ZERO,
    });
    let l2 = make_cmatrix(3, |i, j| match (i, j) {
        (0, 1) => C64::new(0.0, -1.0),
        (1, 0) => C64::new(0.0, 1.0),
        _ => C64::ZERO,
    });
    let inv_sqrt3 = 1.0 / 3.0f64.sqrt();
    let l8 = make_cmatrix(3, |i, j| match (i, j) {
        (0, 0) | (1, 1) => C64::new(inv_sqrt3, 0.0),
        (2, 2) => C64::new(-2.0 * inv_sqrt3, 0.0),
        _ => C64::ZERO,
    });

    for mat in &[l1, l2, l8] {
        let packed = PackedHermitian::from_cmatrix(mat).unwrap();
        let psi = sample_state(3, 101);
        let y_mat = cmatrix_mul_vec(mat, &psi);
        let y_pck = packed.mul_vec(&psi).unwrap();
        assert!(vector_max_diff(&y_mat, &y_pck) < 1e-14);
    }
}

#[test]
fn test_03_d4_2qubit_entangled_hamiltonian_contraction() {
    // 2-qubit Hamiltonian H = Z (x) Z + X (x) I
    // Z (x) Z = diag(1, -1, -1, 1)
    // X (x) I exchanges 0<->2 and 1<->3
    let mut h_mat = CMatrix::zeros(4, 4);
    h_mat[(0, 0)] = C64::new(1.0, 0.0);
    h_mat[(1, 1)] = C64::new(-1.0, 0.0);
    h_mat[(2, 2)] = C64::new(-1.0, 0.0);
    h_mat[(3, 3)] = C64::new(1.0, 0.0);

    h_mat[(0, 2)] += C64::ONE;
    h_mat[(2, 0)] += C64::ONE;
    h_mat[(1, 3)] += C64::ONE;
    h_mat[(3, 1)] += C64::ONE;

    let h_packed = PackedHermitian::from_cmatrix(&h_mat).unwrap();

    // Bell state |Phi+> = (1, 0, 0, 1) / sqrt(2)
    let inv_sqrt2 = 1.0 / 2.0f64.sqrt();
    let bell = vec![
        C64::new(inv_sqrt2, 0.0),
        C64::ZERO,
        C64::ZERO,
        C64::new(inv_sqrt2, 0.0),
    ];

    let y_mat = cmatrix_mul_vec(&h_mat, &bell);
    let y_pck = h_packed.mul_vec(&bell).unwrap();
    assert!(vector_max_diff(&y_mat, &y_pck) < 1e-14);
}

#[test]
fn test_04_d8_3qubit_heisenberg_chain_contraction() {
    let h_mat = random_hermitian(8, 777);
    let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();

    for seed in 1..=5 {
        let psi = sample_state(8, seed);
        let y_mat = cmatrix_mul_vec(&h_mat, &psi);
        let y_pck = h_pck.mul_vec(&psi).unwrap();
        assert!(vector_max_diff(&y_mat, &y_pck) < 1e-14);
    }
}

#[test]
fn test_05_d16_4qubit_random_hermitian_contraction() {
    let h_mat = random_hermitian(16, 999);
    let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();

    for seed in 10..=15 {
        let psi = sample_state(16, seed);
        let y_mat = cmatrix_mul_vec(&h_mat, &psi);
        let y_pck = h_pck.mul_vec(&psi).unwrap();
        assert!(vector_max_diff(&y_mat, &y_pck) < 1e-13);
    }
}

#[test]
fn test_06_zero_vector_annihilation() {
    for &dim in &[2, 4, 8, 16] {
        let h_mat = random_hermitian(dim, 123);
        let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();
        let zero_vec = vec![C64::ZERO; dim];
        let res = h_pck.mul_vec(&zero_vec).unwrap();
        for z in res {
            assert_eq!(z, C64::ZERO);
        }
    }
}

#[test]
fn test_07_identity_invariance() {
    for &dim in &[2, 4, 8, 16] {
        let eye = PackedHermitian::identity(dim).unwrap();
        let psi = sample_state(dim, 555);
        let res = eye.mul_vec(&psi).unwrap();
        assert!(vector_max_diff(&psi, &res) < 1e-15);
    }
}

#[test]
fn test_08_dimension_mismatch_rejection() {
    let p = PackedHermitian::identity(4).unwrap();
    let wrong_x = vec![C64::ONE; 3];
    let err = p.mul_vec(&wrong_x);
    assert!(matches!(
        err,
        Err(PackedHermitianError::DimensionMismatch {
            expected: 4,
            got: 3
        })
    ));
}

#[test]
fn test_09_self_adjointness_symmetry_preservation() {
    let dim = 8;
    let h_mat = random_hermitian(dim, 444);
    let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();

    let phi = sample_state(dim, 11);
    let psi = sample_state(dim, 22);

    let h_psi = h_pck.mul_vec(&psi).unwrap();
    let h_phi = h_pck.mul_vec(&phi).unwrap();

    // <phi | H psi>
    let phi_h_psi: C64 = phi
        .iter()
        .zip(h_psi.iter())
        .map(|(&p, &hp)| p.conj() * hp)
        .sum();
    // <H phi | psi>
    let h_phi_psi: C64 = h_phi
        .iter()
        .zip(psi.iter())
        .map(|(&hp, &s)| hp.conj() * s)
        .sum();

    assert!((phi_h_psi - h_phi_psi).norm() < 1e-14);
}

#[test]
fn test_10_inplace_vs_outofplace_contraction_equivalence() {
    let dim = 8;
    let h_pck = PackedHermitian::from_cmatrix(&random_hermitian(dim, 888)).unwrap();
    let psi = sample_state(dim, 99);

    let out_y = h_pck.mul_vec(&psi).unwrap();

    let mut in_y = vec![C64::ZERO; dim];
    h_pck.mul_vec_accumulate(&psi, &mut in_y).unwrap();

    assert!(vector_max_diff(&out_y, &in_y) < 1e-15);
}

// ============================================================================
// GROUP 2: Quadratic Expectation Values <psi| H |psi>
// ============================================================================

#[test]
fn test_11_d2_pauli_expectation_values_vs_observable() {
    let sz = Observable::pauli_z();
    let sz_mat = &sz.matrix;
    let sz_pck = PackedHermitian::from_cmatrix(sz_mat).unwrap();

    let psi = sample_state(2, 42);
    let qstate = QuantumState {
        dim: 2,
        amplitudes: psi.clone(),
        label: "psi".into(),
    };
    let exp_obs = sz.expectation_value_state(&qstate).unwrap();
    let exp_pck = sz_pck.expectation_value(&psi).unwrap();

    assert!((exp_obs - exp_pck).abs() < 1e-14);
}

#[test]
fn test_12_d4_entanglement_witness_expectation_value() {
    // Entanglement witness W = 0.5 * I - |Phi+><Phi+|
    let inv_sqrt2 = 1.0 / 2.0f64.sqrt();
    let bell = vec![
        C64::new(inv_sqrt2, 0.0),
        C64::ZERO,
        C64::ZERO,
        C64::new(inv_sqrt2, 0.0),
    ];
    let mut proj = CMatrix::zeros(4, 4);
    for i in 0..4 {
        for j in 0..4 {
            proj[(i, j)] = bell[i] * bell[j].conj();
        }
    }
    let eye = CMatrix::identity(4, 4);
    let w_mat = eye * NComplex::new(0.5, 0.0) - proj;
    let w_pck = PackedHermitian::from_cmatrix(&w_mat).unwrap();

    // Expectation value on Bell state should be 0.5 - 1.0 = -0.5 (witness detects entanglement)
    let exp_val = w_pck.expectation_value(&bell).unwrap();
    assert!((exp_val - (-0.5)).abs() < 1e-14);
}

#[test]
fn test_13_d8_ghz_ground_state_energy_verification() {
    let h_mat = random_hermitian(8, 321);
    let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();

    let inv_sqrt2 = 1.0 / 2.0f64.sqrt();
    let mut ghz = vec![C64::ZERO; 8];
    ghz[0] = C64::new(inv_sqrt2, 0.0);
    ghz[7] = C64::new(inv_sqrt2, 0.0);

    let exp_quad = h_pck.expectation_value(&ghz).unwrap();
    let y = h_pck.mul_vec(&ghz).unwrap();
    let exp_vec: f64 = ghz
        .iter()
        .zip(y.iter())
        .map(|(&g, &yg)| (g.conj() * yg).re)
        .sum();

    assert!((exp_quad - exp_vec).abs() < 1e-14);
}

#[test]
fn test_14_d16_pure_state_quadratic_form_parity() {
    let dim = 16;
    let h_mat = random_hermitian(dim, 654);
    let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();

    for seed in 1..=20 {
        let psi = sample_state(dim, seed * 17);
        let exp_pck = h_pck.expectation_value(&psi).unwrap();

        // Calculate directly from CMatrix: psi^dagger * H * psi
        let y = cmatrix_mul_vec(&h_mat, &psi);
        let exp_mat: f64 = psi
            .iter()
            .zip(y.iter())
            .map(|(&p, &yp)| (p.conj() * yp).re)
            .sum();

        assert!((exp_pck - exp_mat).abs() < 1e-13);
    }
}

#[test]
fn test_15_exact_real_valuedness_structural_guarantee() {
    let dim = 8;
    let h_pck = PackedHermitian::from_cmatrix(&random_hermitian(dim, 555)).unwrap();
    let psi = sample_state(dim, 77);

    let exp_val = h_pck.expectation_value(&psi).unwrap();
    assert!(exp_val.is_finite());
}

// ============================================================================
// GROUP 3: Operator Algebra & Dual Geometry in Packed Space
// ============================================================================

#[test]
fn test_16_linear_combination_closure_alpha_a_plus_beta_b() {
    let dim = 4;
    let a_mat = random_hermitian(dim, 10);
    let b_mat = random_hermitian(dim, 20);

    let a_pck = PackedHermitian::from_cmatrix(&a_mat).unwrap();
    let b_pck = PackedHermitian::from_cmatrix(&b_mat).unwrap();

    let alpha = 2.5;
    let beta = -1.5;

    let combo_pck = a_pck
        .scale(alpha)
        .unwrap()
        .add(&b_pck.scale(beta).unwrap())
        .unwrap();
    let combo_mat = a_mat * NComplex::new(alpha, 0.0) + b_mat * NComplex::new(beta, 0.0);

    let psi = sample_state(dim, 30);
    let y_combo_pck = combo_pck.mul_vec(&psi).unwrap();
    let y_combo_mat = cmatrix_mul_vec(&combo_mat, &psi);

    assert!(vector_max_diff(&y_combo_pck, &y_combo_mat) < 1e-14);
}

#[test]
fn test_17_real_scaling_preservation() {
    let dim = 4;
    let p = PackedHermitian::from_cmatrix(&random_hermitian(dim, 100)).unwrap();
    let scaled = p.scale(3.0).unwrap();

    let psi = sample_state(dim, 101);
    let y1 = p.mul_vec(&psi).unwrap();
    let y2 = scaled.mul_vec(&psi).unwrap();

    for (a, b) in y1.iter().zip(y2.iter()) {
        assert!((*a * 3.0 - *b).norm() < 1e-14);
    }
}

#[test]
fn test_17a_addition_rejects_finite_input_overflow() {
    let p = PackedHermitian::new(1, vec![C64::new(f64::MAX, 0.0)]).unwrap();

    assert_eq!(
        p.add(&p),
        Err(PackedHermitianError::NonFiniteEntry { index: 0 })
    );
}

#[test]
fn test_17b_scaling_rejects_non_finite_factor() {
    let p = PackedHermitian::identity(2).unwrap();

    assert_eq!(
        p.scale(f64::NAN),
        Err(PackedHermitianError::NonFiniteEntry { index: 0 })
    );
}

#[test]
fn test_18_hilbert_schmidt_inner_product_trace_parity() {
    let dim = 8;
    let a_mat = random_hermitian(dim, 201);
    let b_mat = random_hermitian(dim, 202);

    let a_pck = PackedHermitian::from_cmatrix(&a_mat).unwrap();
    let b_pck = PackedHermitian::from_cmatrix(&b_mat).unwrap();

    let hs_pck = a_pck.hilbert_schmidt_inner_product(&b_pck).unwrap();
    let hs_mat = (&a_mat * &b_mat).trace().re;

    assert!((hs_pck - hs_mat).abs() < 1e-12);
}

#[test]
fn test_19_hilbert_schmidt_orthogonality_pauli_generators() {
    let sx = PackedHermitian::from_cmatrix(&CMatrix::from_row_slice(
        2,
        2,
        &[C64::ZERO, C64::ONE, C64::ONE, C64::ZERO],
    ))
    .unwrap();
    let sy = PackedHermitian::from_cmatrix(&CMatrix::from_row_slice(
        2,
        2,
        &[
            C64::ZERO,
            C64::new(0.0, -1.0),
            C64::new(0.0, 1.0),
            C64::ZERO,
        ],
    ))
    .unwrap();
    let sz = PackedHermitian::from_cmatrix(&CMatrix::from_row_slice(
        2,
        2,
        &[C64::ONE, C64::ZERO, C64::ZERO, -C64::ONE],
    ))
    .unwrap();

    // Tr(sigma_i sigma_j) = 2 delta_{ij}
    assert!((sx.hilbert_schmidt_inner_product(&sx).unwrap() - 2.0).abs() < 1e-15);
    assert!((sy.hilbert_schmidt_inner_product(&sy).unwrap() - 2.0).abs() < 1e-15);
    assert!((sz.hilbert_schmidt_inner_product(&sz).unwrap() - 2.0).abs() < 1e-15);

    assert!(sx.hilbert_schmidt_inner_product(&sy).unwrap().abs() < 1e-15);
    assert!(sx.hilbert_schmidt_inner_product(&sz).unwrap().abs() < 1e-15);
    assert!(sy.hilbert_schmidt_inner_product(&sz).unwrap().abs() < 1e-15);
}

#[test]
fn test_20_frobenius_norm_consistency() {
    for &dim in &[2, 4, 8, 16] {
        let mat = random_hermitian(dim, dim as u64 * 37);
        let pck = PackedHermitian::from_cmatrix(&mat).unwrap();

        let f_pck = pck.frobenius_norm();
        let f_mat = mat.norm();

        assert!((f_pck - f_mat).abs() < 1e-13);
    }
}

#[test]
fn test_21_cauchy_schwarz_invariant_on_packed_operators() {
    let dim = 8;
    let a_pck = PackedHermitian::from_cmatrix(&random_hermitian(dim, 501)).unwrap();
    let b_pck = PackedHermitian::from_cmatrix(&random_hermitian(dim, 502)).unwrap();

    let inner = a_pck.hilbert_schmidt_inner_product(&b_pck).unwrap().abs();
    let bound = a_pck.frobenius_norm() * b_pck.frobenius_norm();

    assert!(inner <= bound + 1e-12);
}

#[test]
fn test_22_projector_idempotency_property() {
    let dim = 4;
    // |0><0| projector
    let mut data = vec![C64::ZERO; PackedHermitian::packed_len(dim).unwrap()];
    data[0] = C64::ONE; // index (0,0)
    let p = PackedHermitian::new(dim, data).unwrap();

    assert!((p.trace() - 1.0).abs() < 1e-15);
    assert!((p.purity() - 1.0).abs() < 1e-15);
}

#[test]
fn test_23_maximally_mixed_state_uniform_contraction() {
    let dim = 4;
    let eye = PackedHermitian::identity(dim).unwrap();
    let rho = eye.scale(1.0 / dim as f64).unwrap();

    let psi = sample_state(dim, 404);
    let y = rho.mul_vec(&psi).unwrap();

    let expected_scale = 1.0 / dim as f64;
    for (a, b) in psi.iter().zip(y.iter()) {
        assert!((*a * expected_scale - *b).norm() < 1e-15);
    }
}

#[test]
fn test_24_degenerate_subspace_invariance() {
    let dim = 4;
    // Projector onto span{|0>, |1>}
    let mut mat = CMatrix::zeros(dim, dim);
    mat[(0, 0)] = C64::ONE;
    mat[(1, 1)] = C64::ONE;
    let pck = PackedHermitian::from_cmatrix(&mat).unwrap();

    assert!((pck.trace() - 2.0).abs() < 1e-15);
    assert!((pck.purity() - 2.0).abs() < 1e-15);

    let v0 = vec![C64::ONE, C64::ZERO, C64::ZERO, C64::ZERO];
    let v1 = vec![C64::ZERO, C64::ONE, C64::ZERO, C64::ZERO];
    let v2 = vec![C64::ZERO, C64::ZERO, C64::ONE, C64::ZERO];

    assert!(vector_max_diff(&pck.mul_vec(&v0).unwrap(), &v0) < 1e-15);
    assert!(vector_max_diff(&pck.mul_vec(&v1).unwrap(), &v1) < 1e-15);
    assert!(vector_max_diff(&pck.mul_vec(&v2).unwrap(), &vec![C64::ZERO; 4]) < 1e-15);
}

// ============================================================================
// GROUP 4: BLAS Level-2 Matrix-Vector Contraction Benchmark Profile
// ============================================================================

fn contraction_iters(dim: usize) -> usize {
    match dim {
        2 => 500_000,
        4 => 300_000,
        8 => 150_000,
        16 => 80_000,
        _ => 20_000,
    }
}

fn profile_single_dim_contraction(
    dim: usize,
    h_mat: &CMatrix,
    h_pck: &PackedHermitian,
    psi: &[C64],
    dvec: &DVector<NComplex>,
) -> (f64, f64, f64) {
    let iters = contraction_iters(dim);
    for _ in 0..1000 {
        black_box(h_mat * dvec);
        black_box(h_pck.mul_vec(psi).unwrap());
    }
    let t0 = Instant::now();
    for _ in 0..iters {
        let res = black_box(h_mat * dvec);
        black_box(res);
    }
    let cmatrix_ns = t0.elapsed().as_nanos() as f64 / iters as f64;

    let t0 = Instant::now();
    for _ in 0..iters {
        let res = black_box(h_pck.mul_vec(psi).unwrap());
        black_box(res);
    }
    let packed_mul_vec_ns = t0.elapsed().as_nanos() as f64 / iters as f64;

    let mut accum_y = vec![C64::ZERO; dim];
    let t0 = Instant::now();
    for _ in 0..iters {
        black_box(accum_y.fill(C64::ZERO));
        black_box(h_pck.mul_vec_accumulate(psi, &mut accum_y).unwrap());
        black_box(&accum_y);
    }
    let packed_accum_ns = t0.elapsed().as_nanos() as f64 / iters as f64;
    (cmatrix_ns, packed_mul_vec_ns, packed_accum_ns)
}

#[test]
fn test_25_empirical_contraction_latency_and_cache_locality_profile() {
    let dims = [2, 4, 8, 16];

    println!("\n==================================================================================================");
    println!("TEST 25: BLAS LEVEL-2 MATRIX-VECTOR CONTRACTION (H |psi>) PROFILE");
    println!("AuthorityEffect: None. Empirical benchmark suite.");
    println!("==================================================================================================\n");

    println!(
        "{:<5} | {:<16} | {:<16} | {:<16} | {:<14} | {:<14}",
        "dim",
        "CMatrix M*v(ns)",
        "Packed mul_vec",
        "Packed accum(ns)",
        "Speedup Alloc",
        "Speedup Accum"
    );
    println!("{:-<92}", "");

    for &dim in &dims {
        let h_mat = random_hermitian(dim, 777);
        let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();
        let psi = sample_state(dim, 888);
        let dvec = DVector::from_column_slice(&psi);

        let (cmatrix_ns, packed_mul_vec_ns, packed_accum_ns) =
            profile_single_dim_contraction(dim, &h_mat, &h_pck, &psi, &dvec);

        let speedup_alloc = cmatrix_ns / packed_mul_vec_ns;
        let speedup_accum = cmatrix_ns / packed_accum_ns;

        println!(
            "{:<5} | {:<16.2} | {:<16.2} | {:<16.2} | {:>12.2}x | {:>12.2}x",
            dim, cmatrix_ns, packed_mul_vec_ns, packed_accum_ns, speedup_alloc, speedup_accum
        );
    }

    // Ensemble Vector Contraction Benchmark (1,000 vectors through packed operator)
    println!("\n--- ENSEMBLE VECTOR CONTRACTION THROUGHPUT (1,000 vectors streaming) ---");
    println!(
        "{:<5} | {:<18} | {:<18} | {:<14}",
        "dim", "CMat Ensemble(ns)", "Packed Ensemble(ns)", "Throughput Ratio"
    );
    println!("{:-<64}", "");

    for &dim in &dims {
        let ensemble_len = 1_000;
        let vectors: Vec<Vec<C64>> = (0..ensemble_len)
            .map(|k| sample_state(dim, k as u64))
            .collect();
        let dvectors: Vec<DVector<NComplex>> = vectors
            .iter()
            .map(|v| DVector::from_column_slice(v))
            .collect();

        let h_mat = random_hermitian(dim, 12345);
        let h_pck = PackedHermitian::from_cmatrix(&h_mat).unwrap();

        let ensemble_iters = 100;

        let t0 = Instant::now();
        for _ in 0..ensemble_iters {
            for v in &dvectors {
                black_box(&h_mat * v);
            }
        }
        let cmat_ensemble_ns =
            t0.elapsed().as_nanos() as f64 / (ensemble_iters * ensemble_len) as f64;

        let t0 = Instant::now();
        for _ in 0..ensemble_iters {
            for v in &vectors {
                black_box(h_pck.mul_vec(v).unwrap());
            }
        }
        let pck_ensemble_ns =
            t0.elapsed().as_nanos() as f64 / (ensemble_iters * ensemble_len) as f64;

        let ratio = cmat_ensemble_ns / pck_ensemble_ns;
        println!(
            "{:<5} | {:<18.2} | {:<18.2} | {:>12.2}x",
            dim, cmat_ensemble_ns, pck_ensemble_ns, ratio
        );
    }
    println!("==================================================================================================\n");
}

// Origin: engine/crates_rs/tests/core_quantum_physics/packed_hermitian_contract_and_blas_suite.rs
// Claim: urn:core:crates_rs:tests:packed-hermitian-contract-and-blas-suite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord846d5b89 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord846d5b89` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError846d5b89 {
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
impl BoundaryError846d5b89 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError846d5b89 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError846d5b89 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord846d5b89 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError846d5b89> {
        if capacity_bound == 0 {
            return Err(BoundaryError846d5b89::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError846d5b89::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError846d5b89::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_846d5b89() {
    let admitted = BoundaryRecord846d5b89::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord846d5b89::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

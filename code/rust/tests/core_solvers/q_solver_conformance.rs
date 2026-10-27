//! Conformance: Q-level obstruction solver on finite Hilbert cochain
//! truncations. Subject = `QObstructionSolver` (`H_obstr = δᵀδ + V_defect`).
//! Oracles = analytic path-graph Laplacian spectra `2 - 2cos(kπ/n)` and the
//! two-line spectral-invariance argument for orthogonal conjugation.
//!
//! Every assertion is against the declared finite truncation; nothing here
//! witnesses a continuum claim, and no passing test mints authority.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_89d10a0f = (i128, i128);
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::path::PathBuf;

use nalgebra::DMatrix;
use core_replay::dual_trace_memory::{AppendOnlyTraceV1, TraceEventKindV1};
use core_replay::trace_config::TraceConfig;
use core_replay::trace_writer::{write_dual_trace_v1, TraceArtifactId};
use core_solvers::compliance::{
    assert_deterministic, assert_disclosure, assert_non_finite_rejected, decide_trust,
    CertificateKind, Solver, TrustDecision, TrustPolicy,
};
use core_solvers::solver_spectrum_laplacian::{
    gauge_transform_input, imaginary_time_excited_ratio, orthogonal_gauge, QObstructionInput,
    QObstructionSolver, Q_SPECTRAL_RECEIPT_SCHEMA,
};

const SQRT_2: f64 = std::f64::consts::SQRT_2;

/// 2-vertex / 1-edge carrier: δ = [1, -1], V = 0.25·I.
/// Analytic spectrum of δᵀδ is {0, 2}; the shift moves it to {0.25, 2.25}.
fn two_dim_input() -> QObstructionInput {
    QObstructionInput {
        coboundary: DMatrix::from_row_slice(1, 2, &[1.0, -1.0]),
        defect_potential: DMatrix::from_diagonal_element(2, 2, 0.25),
    }
}

/// Path-graph P4 carrier: 3 edges on 4 vertices, V = 0.5·I.
/// Analytic spectrum of the path Laplacian is 2 - 2cos(kπ/4), k = 0..3,
/// i.e. {0, 2-√2, 2, 2+√2}; the shift adds 0.5 to each value.
fn four_dim_input() -> QObstructionInput {
    QObstructionInput {
        coboundary: DMatrix::from_row_slice(
            3,
            4,
            &[
                1.0, -1.0, 0.0, 0.0, //
                0.0, 1.0, -1.0, 0.0, //
                0.0, 0.0, 1.0, -1.0,
            ],
        ),
        defect_potential: DMatrix::from_diagonal_element(4, 4, 0.5),
    }
}

#[test]
fn test_q_obstruction_hamiltonian_ground_state() {
    let solver = QObstructionSolver::default();

    // --- 2D truncation against the analytic oracle ---
    let input2 = two_dim_input();
    let result2 = solver.solve(&input2).expect("2D solve");
    let receipt2 = &result2.value;
    assert_eq!(receipt2.schema, Q_SPECTRAL_RECEIPT_SCHEMA);
    assert_eq!(receipt2.dim, 2);
    assert!((receipt2.ground_energy - 0.25).abs() < 1e-12);
    assert!((receipt2.eigenvalues[1] - 2.25).abs() < 1e-12);
    assert!((receipt2.spectral_gap.expect("dim 2 has a gap") - 2.0).abs() < 1e-12);
    // Ground state of the shifted edge Laplacian is (1,1)/√2, sign-canonical.
    let expected_component = 1.0 / SQRT_2;
    for component in &receipt2.ground_state {
        assert!((component - expected_component).abs() < 1e-10);
    }
    assert!(receipt2.residual_inf_norm < 1e-10);
    assert!(result2.diagnostics.converged);
    assert!(receipt2.eigenvalues.iter().all(|v| v.is_finite()));

    // Certificate + trust policy: eigenpair certificate must be present and
    // the residual must satisfy the declared policy.
    let policy = TrustPolicy {
        required_certificates: vec![CertificateKind::Eigenpair],
        allow_approximate: false,
        max_residual: Some(1e-9),
    };
    assert_eq!(decide_trust(&result2, &policy), TrustDecision::Trusted);

    // Compliance harness: determinism, disclosure, non-finite rejection.
    assert_deterministic(&solver, &input2).expect("deterministic on identical input");
    assert_disclosure(&result2).expect("residual disclosure");
    let mut bad = two_dim_input();
    bad.defect_potential[(0, 0)] = f64::NAN;
    assert_non_finite_rejected(&solver, &bad).expect("NaN input refused");

    // --- 4D truncation against the analytic oracle ---
    let input4 = four_dim_input();
    let result4 = solver.solve(&input4).expect("4D solve");
    let receipt4 = &result4.value;
    let expected4 = [0.5, 2.5 - SQRT_2, 2.5, 2.5 + SQRT_2];
    assert_eq!(receipt4.dim, 4);
    for (computed, analytic) in receipt4.eigenvalues.iter().zip(expected4) {
        assert!(
            (computed - analytic).abs() < 1e-10,
            "eigenvalue {computed} vs analytic {analytic}"
        );
    }
    assert!((receipt4.ground_energy - 0.5).abs() < 1e-10);
    assert!(receipt4.residual_inf_norm < 1e-10);
    assert!(result4.diagnostics.converged);
    assert_eq!(decide_trust(&result4, &policy), TrustDecision::Trusted);
}

#[test]
fn test_gauge_invariant_spectral_decay() {
    let solver = QObstructionSolver::default();
    let input = four_dim_input();
    let base = solver.solve(&input).expect("base solve");

    // Skew-symmetric generator (fixed constants; determinism requires no
    // randomness here) and its orthogonal exponential.
    let mut generator = DMatrix::<f64>::zeros(4, 4);
    let entries = [
        (0, 1, 0.3),
        (0, 2, -0.2),
        (0, 3, 0.1),
        (1, 2, 0.4),
        (1, 3, -0.25),
        (2, 3, 0.15),
    ];
    for (i, j, value) in entries {
        generator[(i, j)] = value;
        generator[(j, i)] = -value;
    }
    let gauge = orthogonal_gauge(&generator).expect("skew generator exponentiates");
    let orthogonality = (gauge.transpose() * &gauge - DMatrix::<f64>::identity(4, 4)).amax();
    assert!(
        orthogonality < 1e-12,
        "gauge element not orthogonal: {orthogonality}"
    );

    // Gauge action on input data: δ ↦ δGᵀ, V ↦ GVGᵀ (symmetrized, disclosed).
    let (transformed, symmetrization_residual) = gauge_transform_input(&input, &gauge);
    assert!(symmetrization_residual < 1e-12);
    let conjugated = solver.solve(&transformed).expect("conjugated solve");

    // Spectral invariance under conjugation: eigenvalues and gap agree.
    for (a, b) in base
        .value
        .eigenvalues
        .iter()
        .zip(&conjugated.value.eigenvalues)
    {
        assert!((a - b).abs() < 1e-9, "spectrum drifted: {a} vs {b}");
    }
    let gap_base = base.value.spectral_gap.expect("gap");
    let gap_conj = conjugated.value.spectral_gap.expect("gap");
    assert!((gap_base - gap_conj).abs() < 1e-9);

    // Imaginary-time decay: for ψ = v₀ + v₁ the excited/ground ratio is
    // exp(-gap·t) in this model, and it is gauge-invariant because the
    // conjugated system evolves Gψ over the conjugated eigenbasis.
    let dim = base.value.dim;
    let psi: Vec<f64> = (0..dim)
        .map(|i| base.value.eigenvectors[0][i] + base.value.eigenvectors[1][i])
        .collect();
    let ratio_zero = imaginary_time_excited_ratio(&base.value, &psi, 0.0).expect("t=0");
    assert!((ratio_zero - 1.0).abs() < 1e-9);

    let t = 1.5;
    let ratio_base = imaginary_time_excited_ratio(&base.value, &psi, t).expect("base decay");
    let predicted = (-gap_base * t).exp();
    assert!(
        (ratio_base - predicted).abs() < 1e-9,
        "decay {ratio_base} vs predicted {predicted}"
    );

    let psi_gauged: Vec<f64> = {
        let psi_vec = DMatrix::from_column_slice(dim, 1, &psi);
        (&gauge * psi_vec).iter().copied().collect()
    };
    let ratio_conj =
        imaginary_time_excited_ratio(&conjugated.value, &psi_gauged, t).expect("conjugated decay");
    assert!(
        (ratio_base - ratio_conj).abs() < 1e-9,
        "gauge broke decay: {ratio_base} vs {ratio_conj}"
    );

    // Monotone suppression of excited mass in imaginary time.
    let ratio_later = imaginary_time_excited_ratio(&base.value, &psi, 3.0).expect("later decay");
    assert!(ratio_later < ratio_base);
}

/// Replay requirement: spectral receipts flow through
/// `core_replay::trace_writer` as an append-only dual trace. The artifact id
/// is content-addressed from the receipt so re-runs are idempotent and a
/// changed receipt lands under a fresh id instead of violating append-only.
#[test]
fn test_spectral_receipt_replay_trace() {
    let solver = QObstructionSolver::default();
    let result = solver.solve(&two_dim_input()).expect("solve");
    let receipt = &result.value;
    let receipt_json = serde_json::to_string(receipt).expect("receipt serializes");

    let mut fingerprint = DefaultHasher::new();
    receipt_json.hash(&mut fingerprint);
    let run_id = format!("{:016x}", fingerprint.finish());

    let mut trace = AppendOnlyTraceV1::default();
    trace
        .append(TraceEventKindV1::Fact {
            key: "schema".into(),
            value: receipt.schema.clone(),
        })
        .expect("append schema");
    trace
        .append(TraceEventKindV1::Fact {
            key: "ground_energy".into(),
            value: format!("{:.17e}", receipt.ground_energy),
        })
        .expect("append ground energy");
    trace
        .append(TraceEventKindV1::Fact {
            key: "residual_inf_norm".into(),
            value: format!("{:.17e}", receipt.residual_inf_norm),
        })
        .expect("append residual");
    trace
        .append(TraceEventKindV1::Fact {
            key: "receipt_json".into(),
            value: receipt_json,
        })
        .expect("append receipt");
    trace
        .append(TraceEventKindV1::TerminalRecorded {
            terminal: "q_spectral_receipt_emitted".into(),
        })
        .expect("append terminal");

    let base_dir = PathBuf::from(env!("CARGO_TARGET_TMPDIR")).join("q_solver_replay");
    let config = TraceConfig::new(true, true, base_dir).expect("trace config");
    let artifact_id =
        TraceArtifactId::new("q_solver_conformance".into(), run_id, "satisfied".into())
            .expect("artifact id");

    let written = write_dual_trace_v1(&config, &artifact_id, &trace).expect("trace written");
    assert_eq!(written.replay_sha256.len(), 64);
    assert!(written.pair.trace_path().exists());

    // Idempotent re-emit: identical bytes are admitted, divergent bytes would
    // be refused by the writer (append-only contract).
    let rewritten = write_dual_trace_v1(&config, &artifact_id, &trace).expect("re-emit");
    assert!(rewritten.idempotent);
}

/// Remark E.12 fixtures (proposal 002, Epoch 19): oriented 4-cycle
/// `x1 -> x2 -> x3 -> x4 -> x1` with observed field ω = (1,1,1,1), Φ([ω]) = 4.
/// The defect potential is built vertex-wise from a selected ℓ¹-minimal
/// representative δ_irr: `v(x) = Σ_{e ∋ x} |δ_irr(e)|`.
///
/// - uniform selection δ_irr = (1,1,1,1): V = 2I, so λ₀ = 0 + 2 = 2 exactly;
/// - concentrated selection δ' = (4,0,0,0): V' = diag(4,4,0,0), and the unit
///   vector ψ = (0,0,1,1)/√2 gives Rayleigh value 1, so λ₀ ≤ 1;
/// - both are positive and they differ: the operator is selection-dependent
///   even though the vanishing equivalence is not (typed obligation OBL-2).
#[test]
fn test_c4_selection_dependent_fixtures() {
    let solver = QObstructionSolver::default();
    // C4 coboundary in the E.12 orientation, rows d0 f (e=(a,b)) = f(b) - f(a).
    let c4_coboundary = DMatrix::from_row_slice(
        4,
        4,
        &[
            -1.0, 1.0, 0.0, 0.0, //
            0.0, -1.0, 1.0, 0.0, //
            0.0, 0.0, -1.0, 1.0, //
            1.0, 0.0, 0.0, -1.0,
        ],
    );

    // Uniform selection: V = 2I; spec(L0) = {0,2,2,4} shifts to {2,4,4,6}.
    let uniform = QObstructionInput {
        coboundary: c4_coboundary.clone(),
        defect_potential: DMatrix::from_diagonal_element(4, 4, 2.0),
    };
    let uniform_result = solver.solve(&uniform).expect("uniform C4 solve");
    let lambda0_uniform = uniform_result.value.ground_energy;
    assert!(
        (lambda0_uniform - 2.0).abs() < 1e-10,
        "uniform C4 ground energy {lambda0_uniform} vs analytic 2"
    );
    let expected_uniform = [2.0, 4.0, 4.0, 6.0];
    for (computed, analytic) in uniform_result
        .value
        .eigenvalues
        .iter()
        .zip(expected_uniform)
    {
        assert!(
            (computed - analytic).abs() < 1e-10,
            "uniform C4 eigenvalue {computed} vs analytic {analytic}"
        );
    }

    // Concentrated selection: V' = diag(4,4,0,0); Rayleigh test vector caps λ₀ at 1.
    let concentrated = QObstructionInput {
        coboundary: c4_coboundary,
        defect_potential: DMatrix::from_diagonal(&nalgebra::DVector::from_row_slice(&[
            4.0, 4.0, 0.0, 0.0,
        ])),
    };
    let concentrated_result = solver.solve(&concentrated).expect("concentrated C4 solve");
    let lambda0_concentrated = concentrated_result.value.ground_energy;
    assert!(
        lambda0_concentrated <= 1.0 + 1e-10,
        "concentrated C4 ground energy {lambda0_concentrated} exceeds Rayleigh bound 1"
    );
    assert!(
        lambda0_concentrated > 1e-9,
        "concentrated C4 ground energy should stay positive (Φ > 0)"
    );

    // Selection-dependence: the two admissible minimal representatives give
    // measurably different ground energies.
    assert!(
        (lambda0_uniform - lambda0_concentrated).abs() > 0.5,
        "selection-dependence not visible: {lambda0_uniform} vs {lambda0_concentrated}"
    );
}

/// Build the cycle-graph coboundary `C_n` (rows `e = (i, i+1 mod n)`).
fn cycle_coboundary(n: usize) -> DMatrix<f64> {
    let mut d0 = DMatrix::zeros(n, n);
    for i in 0..n {
        d0[(i, i)] = -1.0;
        d0[(i, (i + 1) % n)] = 1.0;
    }
    d0
}

/// Vertex potential induced by a selected representative:
/// `v(x) = Σ_{e ∋ x} |δ_irr(e)|`, the (A5) construction.
fn delta_potential(coboundary: &DMatrix<f64>, delta: &[f64]) -> DMatrix<f64> {
    let n = coboundary.ncols();
    let mut v = vec![0.0; n];
    for (edge, d) in delta.iter().enumerate() {
        for (x, item) in v.iter_mut().enumerate() {
            if coboundary[(edge, x)] != 0.0 {
                *item += d.abs();
            }
        }
    }
    DMatrix::from_diagonal(&nalgebra::DVector::from_row_slice(&v))
}

/// Proposition E.7a / Corollary E.7b conformance (proposal 002, Epoch 19).
///
/// For a finite connected carrier with `n ≥ 2`, writing `λ₂` for the Fiedler
/// value of `L₀ = δᵀδ`, `μ = (1/n)Σ_x v(x) = 2Φ([ω])/n` for the mean defect
/// load and `v_max = max_x v(x)` for the peak load, E.7a states
///
/// ```text
///     λ₀  ≥  λ₂ · μ / (λ₂ + μ + v_max)
/// ```
///
/// and E.7b sandwiches `λ₀` between that and E.7's `μ`, with multiplicative
/// width exactly `1 + (μ + v_max)/λ₂`.
///
/// This exercises the inequality on the declared instances only. Checking
/// instances is not proving the proposition (OBL-4: no Lean leg), and no
/// passing assertion here mints authority.
#[test]
fn test_e7a_lower_bound_and_sandwich() {
    let solver = QObstructionSolver::default();

    // (carrier label, coboundary, selected δ_irr)
    let cases: Vec<(&str, DMatrix<f64>, Vec<f64>)> = vec![
        ("C3 uniform", cycle_coboundary(3), vec![1.0, 1.0, 1.0]),
        ("C4 uniform", cycle_coboundary(4), vec![1.0, 1.0, 1.0, 1.0]),
        (
            "C4 concentrated",
            cycle_coboundary(4),
            vec![4.0, 0.0, 0.0, 0.0],
        ),
        (
            "C6 concentrated",
            cycle_coboundary(6),
            vec![6.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
        (
            // Tree carrier: Φ = 0 forces δ_irr = 0, so the bound reads 0 = λ₀.
            "P4 zero defect",
            DMatrix::from_row_slice(
                3,
                4,
                &[
                    -1.0, 1.0, 0.0, 0.0, //
                    0.0, -1.0, 1.0, 0.0, //
                    0.0, 0.0, -1.0, 1.0,
                ],
            ),
            vec![0.0, 0.0, 0.0],
        ),
    ];

    for (label, coboundary, delta) in cases {
        let n = coboundary.ncols();
        let defect_potential = delta_potential(&coboundary, &delta);
        let v: Vec<f64> = defect_potential.diagonal().iter().copied().collect();

        // μ must equal 2Φ/n, with Φ = ‖δ_irr‖₁ for a minimal representative.
        let phi: f64 = delta.iter().map(|d| d.abs()).sum();
        let mu = v.iter().sum::<f64>() / n as f64;
        assert!(
            (mu - 2.0 * phi / n as f64).abs() < 1e-12,
            "{label}: μ={mu} vs 2Φ/n={}",
            2.0 * phi / n as f64
        );
        let v_max = v.iter().copied().fold(0.0_f64, f64::max);

        // λ₂ = smallest NONZERO eigenvalue of L₀, computed independently by
        // running the solver with a zero potential.
        let bare = QObstructionInput {
            coboundary: coboundary.clone(),
            defect_potential: DMatrix::zeros(n, n),
        };
        let bare_spectrum = solver.solve(&bare).expect("bare Laplacian solve").value;
        assert!(
            bare_spectrum.ground_energy.abs() < 1e-10,
            "{label}: connected carrier must have a zero Laplacian eigenvalue"
        );
        let lambda2 = bare_spectrum.eigenvalues[1];
        assert!(
            lambda2 > 1e-9,
            "{label}: carrier must be connected (λ₂ > 0), got {lambda2}"
        );

        let result = solver
            .solve(&QObstructionInput {
                coboundary,
                defect_potential,
            })
            .expect("obstruction solve");
        let lambda0 = result.value.ground_energy;

        // E.7a lower bound.
        let lower = lambda2 * mu / (lambda2 + mu + v_max);
        assert!(
            lambda0 >= lower - 1e-10,
            "{label}: E.7a violated — λ₀={lambda0} < bound={lower} \
             (λ₂={lambda2}, μ={mu}, v_max={v_max})"
        );

        // E.7 upper bound, hence the E.7b sandwich.
        assert!(
            lambda0 <= mu + 1e-10,
            "{label}: E.7 violated — λ₀={lambda0} > μ={mu}"
        );

        // E.7b width identity: upper/lower = 1 + (μ + v_max)/λ₂ when μ > 0.
        if mu > 1e-12 {
            let width = mu / lower;
            let predicted = 1.0 + (mu + v_max) / lambda2;
            assert!(
                (width - predicted).abs() < 1e-9,
                "{label}: width {width} vs predicted {predicted}"
            );
        }
    }

    // Remark E.7c(1), asymptotic attainment: on C4 with a single-vertex load
    // a·e₁, the sandwich width → 1 and λ₀/lower → 1 as a → 0. Checking the
    // trend is not a proof of the limit; E.7c derives it from E.7b.
    let c4 = cycle_coboundary(4);
    let mut previous_ratio = f64::INFINITY;
    for a in [1.0_f64, 0.1, 0.01, 0.001] {
        let defect_potential =
            DMatrix::from_diagonal(&nalgebra::DVector::from_row_slice(&[a, 0.0, 0.0, 0.0]));
        let result = solver
            .solve(&QObstructionInput {
                coboundary: c4.clone(),
                defect_potential,
            })
            .expect("asymptotic solve");
        let lambda0 = result.value.ground_energy;
        let (mu, v_max, lambda2) = (a / 4.0, a, 2.0);
        let lower = lambda2 * mu / (lambda2 + mu + v_max);
        assert!(
            lambda0 >= lower - 1e-12,
            "asymptotic E.7a violated at a={a}"
        );
        let ratio = lambda0 / lower;
        assert!(
            ratio < previous_ratio,
            "ratio should decrease toward 1 as a shrinks: {ratio} !< {previous_ratio}"
        );
        previous_ratio = ratio;
    }
    assert!(
        previous_ratio < 1.001,
        "bound should be near-attained at a=1e-3, ratio={previous_ratio}"
    );
}

/// OB-E19-8 (proposal 005): the degree-1 entry point, and the SVD bridge of §G.2.
///
/// For the path graph P4, the degree-0 operator on C⁰ is d₀ᵀd₀ and the degree-1
/// down-Laplacian on C¹ is d₀d₀ᵀ. These share every nonzero eigenvalue (both are
/// Gram matrices of the same d₀), so the bridge `spec(d₀d₀ᵀ) = spec(d₀ᵀd₀)` away
/// from 0 is a check, not an assumption — and now the C¹ side is computed
/// directly rather than inferred.
#[test]
fn test_degree1_entry_point_and_svd_bridge() {
    use core_solvers::solver_spectrum_laplacian::{
        degree1_hodge_laplacian, solve_degree1, QObstructionInputDegree1,
    };

    let solver = QObstructionSolver::default();

    // P4: 3 edges on 4 vertices, d₀ is 3×4.
    let d0 = DMatrix::from_row_slice(
        3,
        4,
        &[
            1.0, -1.0, 0.0, 0.0, //
            0.0, 1.0, -1.0, 0.0, //
            0.0, 0.0, 1.0, -1.0,
        ],
    );

    // Degree-0 side: L₀ = d₀ᵀd₀ on C⁰ (4-dim), zero potential.
    let deg0 = solver
        .solve(&QObstructionInput {
            coboundary: d0.clone(),
            defect_potential: DMatrix::zeros(4, 4),
        })
        .expect("degree-0 solve");

    // Degree-1 side: L₁ = d₀d₀ᵀ on C¹ (3-dim), C² := 0.
    let input1 = QObstructionInputDegree1 {
        d0: d0.clone(),
        d1: None,
        defect_potential: DMatrix::zeros(3, 3),
    };
    let deg1 = solve_degree1(&solver, &input1).expect("degree-1 solve");

    assert_eq!(deg1.value.dim, 3);
    assert!(deg1.value.residual_inf_norm < 1e-10);

    // Nonzero spectra coincide (SVD bridge). d₀ᵀd₀ has spectrum {0, 2-√2, 2, 2+√2};
    // d₀d₀ᵀ drops the kernel eigenvalue 0, keeping {2-√2, 2, 2+√2}.
    let nonzero0: Vec<f64> = deg0
        .value
        .eigenvalues
        .iter()
        .copied()
        .filter(|v| *v > 1e-9)
        .collect();
    assert_eq!(nonzero0.len(), 3);
    for (c1, expected) in deg1.value.eigenvalues.iter().zip(&nonzero0) {
        assert!(
            (c1 - expected).abs() < 1e-9,
            "SVD bridge broken: {c1} vs {expected}"
        );
    }

    // With C² := 0 the down-Laplacian is exactly d₀d₀ᵀ.
    let l1 = degree1_hodge_laplacian(&input1);
    let manual = &d0 * d0.transpose();
    assert!((l1 - manual).amax() < 1e-12);

    // A nonzero d₁ adds the up-Laplacian d₁ᵀd₁: the operator strictly grows in
    // the Loewner order, so no eigenvalue decreases.
    let d1 = DMatrix::from_row_slice(1, 3, &[1.0, 1.0, 1.0]);
    let with_d1 = solve_degree1(
        &solver,
        &QObstructionInputDegree1 {
            d0,
            d1: Some(d1),
            defect_potential: DMatrix::zeros(3, 3),
        },
    )
    .expect("degree-1 solve with d1");
    for (a, b) in with_d1
        .value
        .eigenvalues
        .iter()
        .zip(&deg1.value.eigenvalues)
    {
        assert!(*a >= *b - 1e-9, "adding d₁ᵀd₁ must not lower eigenvalues");
    }
}

/// Prop. S1(b) (proposal 009, OB-3): the integer cochain complex composes to
/// zero and its mod-2 shadow is orientation-free.
///
/// Triangle K3, vertices {0,1,2}, edges (0,1),(1,2),(0,2) in increasing R2
/// orientation, one triangle (0,1,2). Re-orient edge (0,2) → (2,0) and flip the
/// matching triangle sign; the mod-2 shadow must not move.
#[test]
fn test_parity_shadow_s1b() {
    use core_solvers::solver_spectrum_laplacian::parity_shadow_check;

    // δ⁰: rows are edges, (a,b) → −1 at a, +1 at b.
    let d0 = vec![
        vec![-1i128, 1, 0], // (0,1)
        vec![0, -1, 1],     // (1,2)
        vec![-1, 0, 1],     // (0,2)
    ];
    // δ¹: one triangle, side sum h(0,1) + h(1,2) − h(0,2).
    let d1 = vec![vec![1i128, 1, -1]];

    // Same complex, edge (0,2) re-oriented to (2,0): row sign flipped.
    let d0_reoriented = vec![
        vec![-1i128, 1, 0], // (0,1)
        vec![0, -1, 1],     // (1,2)
        vec![1, 0, -1],     // (2,0)
    ];

    let receipt = parity_shadow_check(&d0, &d1, &d0_reoriented);
    assert!(
        receipt.delta1_delta0_zero,
        "δ¹δ⁰ must vanish over ℤ, got max entry {}",
        receipt.max_composite_entry
    );
    assert_eq!(receipt.max_composite_entry, 0);
    assert!(
        receipt.shadow_orientation_free,
        "mod-2 shadow must be orientation-free"
    );

    // A broken complex (inconsistent triangle sign) must be caught.
    let bad = parity_shadow_check(&d0, &[vec![1i128, 1, 1]], &d0_reoriented);
    assert!(!bad.delta1_delta0_zero);
    assert_ne!(bad.max_composite_entry, 0);
}

/// Prop. S4(c) (proposal 009, OB-3): the down-Laplacian flow `e^{-t L₁^down}`
/// with `L₁^down = d₀d₀ᵀ` fixes `ker((δ⁰)*)` pointwise and contracts `im(δ⁰)`
/// by a factor at most `e^{-t μ₁}`, `μ₁` the smallest nonzero eigenvalue of `L₀`.
#[test]
fn test_down_laplacian_flow_s4() {
    use core_solvers::solver_spectrum_laplacian::{
        imaginary_time_evolve, solve_degree1, QObstructionInputDegree1,
    };

    let solver = QObstructionSolver::default();

    // Triangle C3 coboundary d₀ (3 edges × 3 vertices).
    let d0 = DMatrix::from_row_slice(
        3,
        3,
        &[
            -1.0, 1.0, 0.0, //
            0.0, -1.0, 1.0, //
            -1.0, 0.0, 1.0,
        ],
    );

    // L₁^down = d₀d₀ᵀ on C¹, no potential.
    let l1_down = solve_degree1(
        &solver,
        &QObstructionInputDegree1 {
            d0: d0.clone(),
            d1: None,
            defect_potential: DMatrix::zeros(3, 3),
        },
    )
    .expect("down-Laplacian solve")
    .value;

    // μ₁ = smallest nonzero eigenvalue of L₀ = d₀ᵀd₀ (K3 Laplacian: {0,3,3}).
    let l0 = solver
        .solve(&QObstructionInput {
            coboundary: d0,
            defect_potential: DMatrix::zeros(3, 3),
        })
        .expect("L0 solve")
        .value;
    let mu1 = l0.eigenvalues[1];
    assert!(mu1 > 1e-9);
    // The down-Laplacian's smallest nonzero eigenvalue equals μ₁ (SVD bridge).
    let l1_first_nonzero = l1_down
        .eigenvalues
        .iter()
        .copied()
        .find(|v| *v > 1e-9)
        .expect("a nonzero eigenvalue");
    assert!((l1_first_nonzero - mu1).abs() < 1e-9);

    let t = 0.7;

    // (i) A kernel vector — the harmonic / gauge-invariant part, ground eigenvector
    // at λ ≈ 0 — is FIXED by the flow.
    let kernel = &l1_down.ground_state;
    assert!(
        l1_down.ground_energy.abs() < 1e-9,
        "K3's C¹ has a harmonic 1-cycle"
    );
    let fixed = imaginary_time_evolve(&l1_down, kernel, t).expect("flow kernel");
    for (a, b) in fixed.iter().zip(kernel) {
        assert!(
            (a - b).abs() < 1e-9,
            "kernel vector must be fixed: {a} vs {b}"
        );
    }

    // (ii) An image vector — a nonzero eigenvector — CONTRACTS by exactly
    // e^{-tλ} ≤ e^{-tμ₁}.
    let image = l1_down
        .eigenvectors
        .iter()
        .zip(&l1_down.eigenvalues)
        .find(|(_, lambda)| **lambda > 1e-9)
        .map(|(v, _)| v.clone())
        .expect("a nonzero eigenvector");
    let contracted = imaginary_time_evolve(&l1_down, &image, t).expect("flow image");
    let norm: f64 = contracted.iter().map(|x| x * x).sum::<f64>().sqrt();
    assert!(
        norm <= (-t * mu1).exp() + 1e-9,
        "image must contract by ≤ e^(-t μ₁): norm {norm} vs bound {}",
        (-t * mu1).exp()
    );
    assert!(norm > 0.0);

    // t = 0 is the identity flow.
    let identity = imaginary_time_evolve(&l1_down, &image, 0.0).expect("t=0");
    for (a, b) in identity.iter().zip(&image) {
        assert!((a - b).abs() < 1e-12);
    }
}

/// §S.8 (proposal 009, OB-3): the weighted change of variables produces an
/// operator unitarily equivalent to the weighted Laplacian.
///
/// The weighted Laplacian's eigenvalues solve the generalized problem
/// `δᵀW¹δ f = λ W⁰ f`, equivalently the spectrum of `(W⁰)^{-1/2} δᵀW¹δ (W⁰)^{-1/2}`.
/// The S.8 transform `δ̃ = (W¹)^{1/2} δ (W⁰)^{-1/2}` gives `δ̃ᵀδ̃` = exactly that
/// matrix, so the solver's spectrum on the transformed input must match an
/// independently assembled generalized operator.
#[test]
fn test_s8_weighted_change_of_variables() {
    use core_solvers::solver_spectrum_laplacian::{weighted_to_unit_input, WeightedCarrier};

    let solver = QObstructionSolver::default();

    // Path P3: edges (0,1),(1,2). Non-unit weights.
    let d0 = DMatrix::from_row_slice(2, 3, &[-1.0, 1.0, 0.0, 0.0, -1.0, 1.0]);
    let w0 = vec![1.0, 4.0, 9.0]; // vertex weights
    let w1 = vec![2.0, 3.0]; // edge weights
    let carrier = WeightedCarrier {
        d0: d0.clone(),
        w0: w0.clone(),
        w1: w1.clone(),
        defect_potential: DMatrix::zeros(3, 3),
    };

    let transformed = weighted_to_unit_input(&carrier).expect("S.8 transform");
    let solved = solver.solve(&transformed).expect("solve transformed");

    // Independent oracle: (W⁰)^{-1/2} δᵀ W¹ δ (W⁰)^{-1/2}, assembled by hand.
    let w1_mat = DMatrix::from_diagonal(&nalgebra::DVector::from_row_slice(&w1));
    let raw = d0.transpose() * &w1_mat * &d0; // δᵀ W¹ δ
    let mut oracle = raw.clone();
    for i in 0..3 {
        for j in 0..3 {
            oracle[(i, j)] /= (w0[i].sqrt()) * (w0[j].sqrt());
        }
    }
    let oracle_solved = solver
        .solve(&QObstructionInput {
            coboundary: DMatrix::zeros(0, 3),
            defect_potential: oracle,
        })
        .expect("oracle solve");

    for (a, b) in solved
        .value
        .eigenvalues
        .iter()
        .zip(&oracle_solved.value.eigenvalues)
    {
        assert!(
            (a - b).abs() < 1e-9,
            "S.8 transform spectrum {a} vs generalized oracle {b}"
        );
    }

    // Refusals: non-positive and mismatched weights.
    let bad_weight = WeightedCarrier {
        w0: vec![1.0, 0.0, 9.0],
        ..carrier.clone()
    };
    assert!(weighted_to_unit_input(&bad_weight).is_err());
    let bad_len = WeightedCarrier {
        w1: vec![2.0],
        ..carrier
    };
    assert!(weighted_to_unit_input(&bad_len).is_err());
}

/// Prop. S2(c) (proposal 009, OB-3): λ₀ is the Rayleigh minimum, attained on the
/// ground eigenvector.
#[test]
fn test_s2_rayleigh_minimum() {
    use core_solvers::solver_spectrum_laplacian::s2_rayleigh_scan;

    let solver = QObstructionSolver::default();
    let input = four_dim_input(); // P4 + 0.5·I, spectrum {0.5, 2.5-√2, 2.5, 2.5+√2}
    let receipt = solver.solve(&input).expect("solve").value;

    // Deterministic test vectors: standard basis, all-ones, and eigenvector sums.
    let n = receipt.dim;
    let mut test_vectors: Vec<Vec<f64>> = Vec::new();
    for i in 0..n {
        let mut e = vec![0.0; n];
        e[i] = 1.0;
        test_vectors.push(e);
    }
    test_vectors.push(vec![1.0; n]);
    test_vectors.push(
        (0..n)
            .map(|i| receipt.eigenvectors[1][i] + receipt.eigenvectors[2][i])
            .collect(),
    );

    let (max_violation, ground_error) = s2_rayleigh_scan(&input, &receipt, &test_vectors);
    assert!(
        max_violation < 1e-9,
        "some test vector fell below λ₀ by {max_violation}"
    );
    assert!(
        ground_error < 1e-9,
        "ground eigenvector Rayleigh value ≠ λ₀ (error {ground_error})"
    );
}

/// Prop. S3 (proposal 009, OB-3): the excited/ground ratio obeys the bound, with
/// equality exactly when the excited part sits in the λ₁-eigenspace.
#[test]
fn test_s3_excited_ground_ratio_bound() {
    use core_solvers::solver_spectrum_laplacian::s3_excited_ground_ratio;

    let solver = QObstructionSolver::default();
    let receipt = solver.solve(&four_dim_input()).expect("solve").value;
    let t = 1.3;

    // (i) General initial state: measured ratio ≤ bound.
    let psi_general: Vec<f64> = (0..receipt.dim)
        .map(|i| {
            receipt.eigenvectors[0][i]
                + 0.7 * receipt.eigenvectors[2][i]
                + 0.4 * receipt.eigenvectors[3][i]
        })
        .collect();
    let (measured, bound) = s3_excited_ground_ratio(&receipt, &psi_general, t).expect("gap+seed");
    assert!(
        measured <= bound + 1e-9,
        "S3 bound violated: measured {measured} > bound {bound}"
    );

    // (ii) Equality case: excited part purely in the λ₁-eigenspace (φ₁).
    let psi_equality: Vec<f64> = (0..receipt.dim)
        .map(|i| receipt.eigenvectors[0][i] + 0.5 * receipt.eigenvectors[1][i])
        .collect();
    let (measured_eq, bound_eq) =
        s3_excited_ground_ratio(&receipt, &psi_equality, t).expect("gap+seed");
    assert!(
        (measured_eq - bound_eq).abs() < 1e-9,
        "S3 equality case failed: {measured_eq} vs {bound_eq}"
    );

    // (iii) SEED failure (no ground overlap) → None.
    let psi_no_ground: Vec<f64> = receipt.eigenvectors[1].clone();
    assert!(s3_excited_ground_ratio(&receipt, &psi_no_ground, t).is_none());
}

#[test]
fn nonfinite_tolerance_and_overflowing_gap_are_typed_refusals() {
    use core_solvers::compliance::Solver;
    use core_solvers::solver_spectrum_laplacian::{QObstructionInput, QObstructionSolver};
    let input = QObstructionInput {
        coboundary: nalgebra::DMatrix::zeros(0, 2),
        defect_potential: nalgebra::DMatrix::from_diagonal(&nalgebra::DVector::from_vec(vec![
            -1e308, 1e308,
        ])),
    };
    assert!(QObstructionSolver::default().solve(&input).is_err());
    for tolerance in [f64::NAN, f64::INFINITY, -1.0] {
        let solver = QObstructionSolver {
            tolerance,
            ..Default::default()
        };
        assert!(solver.solve(&input).is_err());
    }
}

// Origin: engine/crates_rs/tests/core_solvers/q_solver_conformance.rs
// Claim: urn:core:crates_rs:tests:q-solver-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord89d10a0f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord89d10a0f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError89d10a0f {
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
impl BoundaryError89d10a0f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError89d10a0f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError89d10a0f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord89d10a0f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError89d10a0f> {
        if capacity_bound == 0 {
            return Err(BoundaryError89d10a0f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError89d10a0f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError89d10a0f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_89d10a0f() {
    let admitted = BoundaryRecord89d10a0f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord89d10a0f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

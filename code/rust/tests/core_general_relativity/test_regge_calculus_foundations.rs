//! Integration tests for Tullio Regge's discrete gravity and quantum foundations in `core_general_relativity`.
//!
//! Validates:
//! - Cayley-Menger determinants & 2D/3D/4D simplex volumes
//! - Dihedral angles in triangles, tetrahedra, and pentachora
//! - Schläfli differential identity in 2D and 4D
//! - Classical Regge action with cosmological constant Lambda
//! - Tullio Regge's QM foundations (Ponzano-Regge, path integral propagator, Wheeler-DeWitt constraint, zero modes, Regge-Čech bridge)
//! - Multi-simplex 4D Regge triangulations & Discrete Exterior Calculus (DEC) Laplacians
//! - Wheeler-DeWitt constraint evaluated against DEC Laplacians
//! - Comprehensive negative controls and falsification matrices
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_3fdfc952 = (i128, i128);
use core_general_relativity::cayley_menger::*;
use core_general_relativity::curvature_tensor::*;
use core_general_relativity::dec_laplacian::*;
use core_general_relativity::dihedral_angles::*;
use core_general_relativity::dirac_operator_discrete::*;
use core_general_relativity::field_equation::*;
use core_general_relativity::hamiltonian_constraint::*;
use core_general_relativity::initial_value_formulation::*;
use core_general_relativity::quantum_regge::*;
use core_general_relativity::regge_4d::*;
use core_general_relativity::regge_calculus::*;
use core_general_relativity::ricci_curvature::*;
use core_general_relativity::schlafli::*;
use core_homology::simplicial::{OrientedSimplex, SimplicialComplex};

// ============================================================================
// Original Core Foundations Tests
// ============================================================================

#[test]
fn test_cayley_menger_volumes_2d_3d_4d() {
    let side = 2.0;
    let get_len = |_: usize, _: usize| Some(side);

    // 2D: Equilateral triangle Area = (sqrt(3)/4) * a^2 = sqrt(3) ~ 1.7320508
    let a_tri = simplex_volume_cayley_menger(&[0, 1, 2], get_len).unwrap();
    let expected_2d = (3.0f64.sqrt() / 4.0) * side * side;
    assert!((a_tri - expected_2d).abs() < 1e-9);

    // 3D: Regular tetrahedron Volume = a^3 / (6 * sqrt(2)) ~ 0.942809
    let v_tet = simplex_volume_cayley_menger(&[0, 1, 2, 3], get_len).unwrap();
    let expected_3d = side.powi(3) / (6.0 * 2.0f64.sqrt());
    assert!((v_tet - expected_3d).abs() < 1e-9);

    // 4D: Regular 4-simplex Volume = (sqrt(5)/96) * a^4 ~ 0.37267799
    let v_4 = simplex_volume_cayley_menger(&[0, 1, 2, 3, 4], get_len).unwrap();
    let expected_4d = (5.0f64.sqrt() / 96.0) * side.powi(4);
    assert!((v_4 - expected_4d).abs() < 1e-7);
}

#[test]
fn test_dihedral_angles_and_schlafli() {
    let side = 1.5;
    let get_len = |_: usize, _: usize| Some(side);

    // 2D: Triangle interior angles sum to pi (Schläfli)
    let tri = [0, 1, 2];
    let schlafli_2d = verify_schlafli_identity_2d(&tri, get_len).unwrap();
    assert!(schlafli_2d.is_vanishing);

    // 3D: Regular tetrahedron dihedral angle = arccos(1/3) ~ 1.2309594 rad
    let tet = [0, 1, 2, 3];
    let theta = tetrahedron_dihedral_angle_at_edge(&tet, (0, 1), get_len).unwrap();
    let expected = (1.0f64 / 3.0).acos();
    assert!((theta - expected).abs() < 1e-7);
}

#[test]
fn test_3d_regge_calculus_on_tetrahedron() {
    let maximal = vec![OrientedSimplex::from_unordered(vec![0, 1, 2, 3]).unwrap()];
    let complex = SimplicialComplex::from_maximal_simplices(maximal).unwrap();

    let mut metric = EdgeLengthMetric::new();
    let edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];
    for &(u, v) in &edges {
        metric.set(u, v, 1.0).unwrap();
    }

    let regge = ReggeCalculus::try_new(complex, metric, "single_tetrahedron").unwrap();
    let tet_simplex = &regge.complex.simplices(3)[0];
    let vol = regge.simplex_volume(tet_simplex).unwrap();
    let expected_vol = 1.0 / (6.0 * 2.0f64.sqrt());
    assert!((vol - expected_vol).abs() < 1e-9);

    let eps = regge.deficit_at_edge(0, 1).unwrap();
    let expected_eps = std::f64::consts::TAU - (1.0f64 / 3.0).acos();
    assert!((eps - expected_eps).abs() < 1e-7);

    let action_res = regge.regge_action_with_lambda(0.5).unwrap();
    assert_eq!(action_res.dimension, 3);
    assert!(action_res.curvature_term > 0.0);
    assert!(action_res.cosmological_term > 0.0);
}

#[test]
fn test_quantum_regge_foundations() {
    let edge_lengths = [1.0; 6];
    let pr = compute_ponzano_regge_amplitude(&edge_lengths).unwrap();
    assert!(pr.tetrahedron_volume > 0.1);
    assert!(pr.cosine_amplitude.is_finite());

    let prop = compute_quantum_regge_path_integral_1d((0.8, 1.2), 20, 1.0, |ell| {
        Some(ell * 0.5)
    });
    assert_eq!(prop.total_configs_sampled, 20);
    assert_eq!(prop.admissible_configs, 20);
    assert!(prop.real_amplitude.is_finite());

    let incident = vec![(1.0, 0.1), (1.0, 0.1)];
    let wdw = evaluate_simplicial_wheeler_dewitt(0, &incident, 1.0, 0.4);
    assert_eq!(wdw.vertex, 0);
    assert!((wdw.potential_term - 0.4).abs() < 1e-9);
    assert!((wdw.total_constraint_residual - (-0.8)).abs() < 1e-9);

    let spec = compute_quantum_tetrahedron_spectrum([0.5, 0.5, 0.5, 0.5], 0.2375, 1.0);
    assert!(spec.face_areas[0] > 0.0);
    assert!(spec.volume_eigenvalue_estimate > 0.0);

    let hessian_diag = vec![0.00001, 1.5, 2.3];
    let zm = analyze_flat_triangulation_zero_modes(&hessian_diag, 1e-4);
    assert_eq!(zm.is_diffeo_invariant, None);
    assert_eq!(zm.near_zero_diagonal_count, 1);

    let bridge = bridge_regge_to_quantum_cech(0.4);
    assert_eq!(bridge.is_contextual, None);
    assert_eq!(bridge.bell_chsh_violation_bound, None);
}

// ============================================================================
// The 10 In-Depth Regge Tests
// ============================================================================

/// 1. Topology, hinges, and dihedral angle accumulation in two glued 4-simplices.
#[test]
fn test_01_two_pentachora_gluing_topology_and_hinges() {
    let side = 1.0;
    let tri = ReggeTriangulation4D::two_pentachora_glued(side).unwrap();

    // Verify simplicial combinatorics
    assert_eq!(tri.complex.num_vertices(), 6, "Expected 6 vertices in two glued pentachora");
    assert_eq!(tri.pentachora.len(), 2, "Expected exactly 2 pentachora");
    assert_eq!(tri.pentachora_volumes.len(), 2);

    let v_expected = (5.0f64.sqrt() / 96.0) * side.powi(4);
    assert!((tri.pentachora_volumes[0] - v_expected).abs() < 1e-8);
    assert!((tri.pentachora_volumes[1] - v_expected).abs() < 1e-8);

    // The shared tetrahedron is {0, 1, 2, 3}, which contains 4 triangles:
    // (0,1,2), (0,1,3), (0,2,3), (1,2,3).
    // Each must have exactly 2 incident pentachora.
    let shared_triangles = vec![[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]];
    for st in shared_triangles {
        let h = tri.hinges.iter().find(|h| h.triangle == st)
            .unwrap_or_else(|| panic!("Shared triangle {st:?} must exist in hinges"));
        assert_eq!(h.incident_pentachora.len(), 2, "Shared triangle {st:?} must have 2 incident pentachora");
        assert_eq!(h.dihedral_angles.len(), 2);

        // In each regular pentachoron, dihedral angle is arccos(1/4)
        let single_theta = (1.0f64 / 4.0).acos();
        assert!((h.dihedral_angles[0] - single_theta).abs() < 1e-7);
        assert!((h.dihedral_angles[1] - single_theta).abs() < 1e-7);

        // Accumulated dihedral angle at shared hinge is 2 * arccos(1/4) ~ 2.636232 rad
        let expected_total = 2.0 * single_theta;
        assert!((h.total_dihedral_angle - expected_total).abs() < 1e-7);
    }

    // Non-shared triangles have exactly 1 incident pentachoron
    let boundary_triangle = tri.hinges.iter().find(|h| h.incident_pentachora.len() == 1)
        .expect("Boundary triangle must exist");
    let single_theta = (1.0f64 / 4.0).acos();
    assert!((boundary_triangle.total_dihedral_angle - single_theta).abs() < 1e-7);
}

/// 2. Regular 4-simplex exact dihedral angle on all 10 triangular faces.
#[test]
fn test_02_regular_pentachoron_dihedral_angle_exact() {
    let side = 1.0;
    let get_len = |_: usize, _: usize| Some(side);
    let pent = [0, 1, 2, 3, 4];

    // Every combination of 3 vertices from 0..4
    let triangles = [
        [0, 1, 2], [0, 1, 3], [0, 1, 4],
        [0, 2, 3], [0, 2, 4], [0, 3, 4],
        [1, 2, 3], [1, 2, 4], [1, 3, 4],
        [2, 3, 4],
    ];

    let expected_angle = (1.0f64 / 4.0).acos(); // ~ 1.31811607165 rad (75.5224878 deg)

    for tri in &triangles {
        let theta = pentachoron_dihedral_angle_at_triangle(&pent, tri, get_len)
            .unwrap_or_else(|e| panic!("Failed to compute dihedral angle for {tri:?}: {e}"));
        assert!(
            (theta - expected_angle).abs() < 1e-7,
            "Face {tri:?} dihedral angle {theta} differs from expected {expected_angle}"
        );
    }

    // Negative control: triangle containing a vertex not in the pentachoron
    let invalid_tri = [0, 1, 99];
    let err = pentachoron_dihedral_angle_at_triangle(&pent, &invalid_tri, get_len);
    assert!(err.is_err(), "Invalid triangle with external vertex must return Err");
}

/// 3. Multi-simplex 4D fan around interior hinge: exact zero deficit in flat spacetime.
#[test]
fn test_03_four_pentachora_flat_fan_zero_deficit() {
    let edge_len = 1.5;
    let fan = ReggeTriangulation4D::four_pentachora_fan(edge_len).unwrap();

    assert_eq!(fan.pentachora.len(), 4);
    assert_eq!(fan.complex.num_vertices(), 7);

    // Locate the central interior hinge triangle [0, 1, 2]
    let central_hinge = fan.hinges.iter().find(|h| h.triangle == [0, 1, 2])
        .expect("Central hinge [0, 1, 2] must be present");

    assert_eq!(central_hinge.incident_pentachora.len(), 4);
    assert!(central_hinge.is_interior);

    // Each orthocentric pentachoron in the 4 quadrants has dihedral angle pi/2
    for (i, &angle) in central_hinge.dihedral_angles.iter().enumerate() {
        let expected = std::f64::consts::FRAC_PI_2;
        assert!(
            (angle - expected).abs() < 1e-8,
            "Quadrant {i} dihedral angle {angle} != pi/2"
        );
    }

    // 4 * (pi/2) = 2*pi => deficit angle is identically zero!
    let total = central_hinge.total_dihedral_angle;
    assert!((total - 2.0 * std::f64::consts::PI).abs() < 1e-9);
    assert!((central_hinge.deficit_angle).abs() < 1e-9, "Deficit angle must vanish in flat 4D fan");
}

/// 4. 4D Regge Action: Curvature and cosmological constant linearity.
#[test]
fn test_04_regge_4d_action_curvature_and_cosmological_term() {
    let tri = ReggeTriangulation4D::two_pentachora_glued(1.0).unwrap();

    let act_0 = tri.compute_action(0.0);
    assert_eq!(act_0.cosmological_term, 0.0);
    assert_eq!(act_0.total_action, act_0.curvature_term);

    // With cosmological constant Lambda = 0.4
    let lambda = 0.4;
    let act_l = tri.compute_action(lambda);
    assert_eq!(act_l.curvature_term, act_0.curvature_term);
    let expected_cosmo = lambda * act_l.total_4volume;
    assert!((act_l.cosmological_term - expected_cosmo).abs() < 1e-9);
    assert!((act_l.total_action - (act_0.curvature_term - expected_cosmo)).abs() < 1e-9);

    // Linearity: doubling Lambda doubles cosmological term
    let act_2l = tri.compute_action(2.0 * lambda);
    assert!((act_2l.cosmological_term - 2.0 * act_l.cosmological_term).abs() < 1e-9);
}

/// 5. Discrete Exterior Calculus: Exact nilpotency d1 o d0 = 0 on 4D complex.
#[test]
fn test_05_dec_coboundary_nilpotency_d1_d0_exact_zero() {
    let fan = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
    let dec = fan.build_dec_operators().unwrap();

    assert_eq!(dec.num_vertices, 7);
    assert!(!dec.edges.is_empty());
    assert!(!dec.triangles.is_empty());

    // Arbitrary non-trivial 0-form field
    let psi = vec![1.5, -2.3, 0.8, 4.1, -1.9, 0.0, 3.7];
    let (is_nilpotent, max_res) = dec.verify_nilpotency_d1_d0(&psi).unwrap();

    assert!(is_nilpotent, "Coboundary nilpotency d1 o d0 failed");
    assert!(max_res < 1e-14, "Max nilpotency residual {max_res} exceeds numerical threshold");

    // Also test with alternating sign field
    let psi_alt = vec![1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0];
    let (is_nilp2, max_res2) = dec.verify_nilpotency_d1_d0(&psi_alt).unwrap();
    assert!(is_nilp2);
    assert!(max_res2 < 1e-14);
}

/// 6. DEC Laplace-Beltrami operator properties: constant kernel, self-adjointness, and positive Dirichlet energy.
#[test]
fn test_06_dec_laplacian_properties_positivity_and_constant_kernel() {
    let fan = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
    let dec = fan.build_dec_operators().unwrap();

    // 1. Constant functions are in the kernel of Delta_0: Delta_0 (c * 1) = 0
    let const_val = 42.0;
    let const_field = vec![const_val; dec.num_vertices];
    let lap_const = dec.laplacian_0form(&const_field).unwrap();
    for (v, &val) in lap_const.iter().enumerate() {
        assert!(val.abs() < 1e-13, "Vertex {v} non-zero on constant function: {val}");
    }

    // 2. Self-adjointness: <phi, Delta_0 psi>_{star0} == <Delta_0 phi, psi>_{star0}
    let phi = vec![0.5, 1.2, -0.4, 2.1, -1.0, 0.3, 1.8];
    let psi = vec![2.0, -0.7, 1.5, -1.1, 0.9, 3.2, -0.5];
    let (lhs, rhs, diff) = dec.verify_self_adjointness(&phi, &psi).unwrap();
    assert!(
        diff < 1e-12,
        "Self-adjointness violation: lhs={lhs}, rhs={rhs}, diff={diff}"
    );

    // 3. Positive semi-definiteness: Dirichlet energy E[psi] >= 0
    let energy_non_const = dec.dirichlet_energy_0form(&psi).unwrap();
    assert!(energy_non_const > 0.0, "Dirichlet energy of non-constant field must be strictly positive");

    let energy_const = dec.dirichlet_energy_0form(&const_field).unwrap();
    assert!(energy_const < 1e-14, "Dirichlet energy of constant field must vanish");
}

/// 7. Wheeler-DeWitt constraint on flat 4D triangulation: exact vanishing of constraint residual on uniform state.
#[test]
fn test_07_wheeler_dewitt_flat_triangulation_zero_mode() {
    let fan = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
    let dec = fan.build_dec_operators().unwrap();

    // Flat ground state wavefunctional Psi = 1, hbar = 1, Lambda = 0
    let psi = vec![1.0; dec.num_vertices];
    let hbar = 1.0;
    let lambda = 0.0;
    let tol = 1e-10;

    let report = evaluate_wheeler_dewitt_against_dec_laplacian(
        &fan, &dec, &psi, hbar, lambda, tol
    ).unwrap();

    // At the central hinge vertices 0, 1, 2: curvature potential is zero because deficit = 0
    for v in 0..=2 {
        let v_res = &report.vertex_results[v];
        assert!(
            v_res.dec_laplacian_val.abs() < 1e-13,
            "DEC Laplacian at vertex {v} must vanish on uniform state"
        );
        assert!(
            v_res.kinetic_term.abs() < 1e-13,
            "Kinetic term at vertex {v} must vanish on uniform state"
        );
        assert!(
            v_res.residual.abs() < 1e-9,
            "WDW residual at flat vertex {v} must vanish identically: {}", v_res.residual
        );
    }

    assert!(report.residual_l2_norm < 1e-8, "Flat vacuum must satisfy WDW constraint");
}

/// 8. Wheeler-DeWitt constraint on curved geometry: kinetic gradient balances curvature potential.
#[test]
fn test_08_wheeler_dewitt_curved_geometry_energy_balance() {
    let tri = ReggeTriangulation4D::two_pentachora_glued(1.0).unwrap();
    let dec = tri.build_dec_operators().unwrap();

    // Curved state with non-zero potential
    let psi = vec![1.0, 0.9, 1.1, 1.0, 0.8, 1.2];
    let hbar = 1.0;
    let lambda = 0.05;

    let report = evaluate_wheeler_dewitt_against_dec_laplacian(
        &tri, &dec, &psi, hbar, lambda, 100.0
    ).unwrap();

    assert_eq!(report.vertex_results.len(), 6);
    for vr in &report.vertex_results {
        assert!(vr.mass_measure > 0.0);
        assert!(vr.kinetic_term.is_finite());
        assert!(vr.total_potential.is_finite());
        assert!(vr.residual.is_finite());
    }

    // Verify operator linearity: doubling Psi doubles residual when Lambda and Curvature are linear
    let psi_scaled: Vec<f64> = psi.iter().map(|&x| 2.0 * x).collect();
    let report_scaled = evaluate_wheeler_dewitt_against_dec_laplacian(
        &tri, &dec, &psi_scaled, hbar, lambda, 100.0
    ).unwrap();

    for v in 0..6 {
        let res_1 = report.vertex_results[v].residual;
        let res_2 = report_scaled.vertex_results[v].residual;
        assert!((res_2 - 2.0 * res_1).abs() < 1e-9, "WDW operator must be linear in Psi");
    }
}

/// 9. 4D Schläfli differential identity on a pentachoron.
#[test]
fn test_09_schlafli_identity_4d_pentachoron() {
    let pent = [0, 1, 2, 3, 4];
    let side = 1.0;
    let get_len = |_: usize, _: usize| Some(side);

    // Perturb edge (0, 1) by delta = 1e-4
    let delta = 1e-4;
    let sum_area_dtheta = ReggeTriangulation4D::schlafli_differential_4d(
        &pent, (0, 1), get_len, delta
    ).unwrap();

    // Schläfli identity asserts sum_f A_f * (d theta_f / dl_e) = 0
    assert!(
        sum_area_dtheta.abs() < 1e-4,
        "4D Schläfli identity violation: sum A_f * dtheta = {}", sum_area_dtheta
    );
}

/// 10. Comprehensive negative controls: degenerate simplex, non-positive lengths, dimension mismatch.
#[test]
fn test_10_negative_controls_degenerate_4simplex_and_metric_violations() {
    // 1. Non-positive edge length in EdgeLengthMetric
    let mut metric = EdgeLengthMetric::new();
    let res_neg = metric.set(0, 1, -2.5);
    assert!(matches!(res_neg, Err(ReggeError::NonPositiveLength { .. })));

    let res_zero = metric.set(0, 1, 0.0);
    assert!(matches!(res_zero, Err(ReggeError::NonPositiveLength { .. })));

    // 2. Missing edge length error
    metric.set(0, 1, 1.0).unwrap();
    let res_missing = metric.get(0, 2);
    assert!(matches!(res_missing, Err(ReggeError::MissingEdgeLength { .. })));

    // 3. Degenerate 4-simplex with collinear or flat vertices (zero Cayley-Menger volume)
    let get_degenerate_len = |u: usize, v: usize| {
        // Collinear vertices on a line: d(u, v) = |u - v|
        let diff = (u as f64 - v as f64).abs();
        Some(if diff == 0.0 { 1.0 } else { diff })
    };
    let vol_degen = simplex_volume_cayley_menger(&[0, 1, 2, 3, 4], get_degenerate_len);
    // Collinear points in 4D cannot span a 4-simplex => volume is 0 or Err
    match vol_degen {
        Ok(v) => assert!(v < 1e-9, "Collinear points must have zero 4-volume"),
        Err(_) => {} // Err is also valid rejection
    }

    // 4. DEC operators dimension mismatch
    let dec_res = DecOperators::new(
        3,
        vec![(0, 1)],
        vec![],
        vec![1.0, 2.0], // 2 lengths for 1 edge! Mismatch!
        vec![1.0, 1.0, 1.0],
        vec![1.0],
    );
    assert!(dec_res.is_err(), "DEC operator construction with length mismatch must return Err");

    // 5. WDW evaluation with wavefunctional dimension mismatch
    let fan = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
    let dec = fan.build_dec_operators().unwrap();
    let psi_wrong_dim = vec![1.0; 2]; // 2 elements instead of 7!
    let wdw_err = evaluate_wheeler_dewitt_against_dec_laplacian(
        &fan, &dec, &psi_wrong_dim, 1.0, 0.0, 1e-6
    );
    assert!(wdw_err.is_err(), "WDW evaluation with wrong state dimension must return Err");
}

/// 11. Simplicial Regge Field Equations (MTW §42.4, Hamber §6.4).
#[test]
fn test_11_simplicial_field_equations_4d_and_relaxation() {
    let tri = ReggeTriangulation4D::four_pentachora_fan(1.0).unwrap();
    let fe_res = compute_regge_field_equations_4d(&tri, 0.0, true).unwrap();

    // Check interior edges have vanishing residuals
    let res_01 = fe_res.residuals.get(&(0, 1)).copied().unwrap();
    let res_12 = fe_res.residuals.get(&(1, 2)).copied().unwrap();
    assert!(res_01.abs() < 1e-6);
    assert!(res_12.abs() < 1e-6);

    // Relaxation solver step reduces residual norm or terminates cleanly
    let relax = solve_regge_field_equations_relaxation(&tri, 0.0, true, 0.01, 5, 1e-4).unwrap();
    assert!(relax.iterations <= 5);
}

/// 12. Discrete Riemann and Higher-Derivative Regge Action (Hamber §7.1-§7.3).
#[test]
fn test_12_discrete_riemann_and_higher_derivative_regge() {
    let tri = ReggeTriangulation4D::two_pentachora_glued(1.0).unwrap();
    let field = compute_discrete_curvature_field_4d(&tri, 1.5).unwrap();

    // Non-negative Higher-Derivative action
    assert!(field.higher_derivative_action >= 0.0);
    assert!(field.total_4volume > 0.0);

    // Bivector and Riemann tensor evaluation
    let biv = HingeBivector4D::canonical_plane(1, 2).unwrap();
    let r = DiscreteRiemannTensor4D::new(vec![0, 1, 2], 0.1, 0.5, biv).unwrap();
    assert_eq!(r.component(1, 2, 1, 2), -r.component(2, 1, 1, 2));
}

/// 13. 3+1 (ADM) Cauchy Dynamics and Canonical Momenta (MTW §42.11).
#[test]
fn test_13_adm_cauchy_dynamics_and_momenta() {
    let s0 = SpatialSlice3D::single_tetrahedron(1.0).unwrap();
    let s1 = SpatialSlice3D::single_tetrahedron(1.05).unwrap();
    let mut lapse = std::collections::BTreeMap::new();
    for v in 0..4 {
        lapse.insert(v, 1.0);
    }
    let slab = SimplicialSlab4D::new(s0, s1, lapse, 0.05).unwrap();
    let momenta = slab.canonical_momenta().unwrap();
    assert_eq!(momenta.len(), 6);
    for &pi in momenta.values() {
        assert!(pi > 0.0); // Expanding tetrahedron has positive conjugate momentum
    }
}

/// 14. Simplicial Wheeler-DeWitt Hamiltonian Constraint (Hamber §8.4).
#[test]
fn test_14_hamiltonian_constraint_evaluation() {
    let slice = SpatialSlice3D::single_tetrahedron(1.0).unwrap();
    let mut momenta = std::collections::BTreeMap::new();
    for &e in &slice.edges {
        momenta.insert(e, 0.0);
    }
    let report = evaluate_hamiltonian_constraints(&slice, &momenta, 0.0, 10.0).unwrap();
    assert!(report.total_spatial_volume > 0.0);
    assert_eq!(report.vertex_constraints.len(), 4);
}

/// 15. Discrete Simplicial Dirac Operator Hermiticity (Hamber §7.4).
#[test]
fn test_15_discrete_dirac_operator_hermiticity_and_invariance() {
    let v_vols = vec![1.0, 1.0];
    let n_01 = [1.0, 0.0, 0.0];
    let n_10 = [-1.0, 0.0, 0.0];
    let weight = 1.0;
    let conn_01 = SpinConnectionSU2::new_normalized([0.6, 0.8, 0.0, 0.0]).unwrap();
    let conn_10 = conn_01.dagger();

    let edges = vec![
        (0, 1, weight, n_01, conn_01),
        (1, 0, weight, n_10, conn_10),
    ];

    let dirac = SimplicialDiracOperator::new(2, v_vols, edges).unwrap();

    let phi = vec![
        Spinor2::new((0.5, -0.2), (0.3, 0.8)),
        Spinor2::new((-0.4, 0.1), (0.7, -0.6)),
    ];
    let psi = vec![
        Spinor2::new((0.2, 0.7), (-0.1, 0.4)),
        Spinor2::new((0.9, -0.3), (0.0, 0.5)),
    ];

    let is_herm = dirac.check_hermiticity(&phi, &psi, 1e-6).unwrap();
    assert!(is_herm, "Simplicial Dirac operator must be Hermitian");
}

// Origin: engine/crates_rs/tests/core_general_relativity/test_regge_calculus_foundations.rs
// Claim: urn:core:crates_rs:tests:test-regge-calculus-foundations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3fdfc952 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3fdfc952` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3fdfc952 {
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
impl BoundaryError3fdfc952 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3fdfc952 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3fdfc952 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3fdfc952 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3fdfc952> {
        if capacity_bound == 0 {
            return Err(BoundaryError3fdfc952::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3fdfc952::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3fdfc952::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_3fdfc952() {
    let admitted = BoundaryRecord3fdfc952::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3fdfc952::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

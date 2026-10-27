// Executable finite evidence; AuthorityEffect: None.
//! # Core WDP (Witnessed Difference Programme)
//!
//! Foundational mathematics of the Witnessed Difference Programme:
//! Finite Obstruction Calculus, exact rational dual-certified cochains,
//! Moore behavioral quotients, presheaves, and connections to HoTT,
//! Higher Category Theory, Simplicial Homology, and Quantum Mechanics.
//!
//! Under Sentinel and CODA doctrine:
//! - All mathematical derivations and certificates carry `AuthorityEffect::None`.
//! - Discrete exactness is guaranteed using `num_rational::BigRational` for all cochains
//!   and carriers; there is no bounded-width rational type in this crate.
//! - Engine mathematics is not re-implemented here. Φ₁ (with its primal-dual
//!   certificate), Γ₂ and the exact trichotomy belong to `core_functional`;
//!   coboundary matrices, the chain law and Betti numbers to `core_homology`;
//!   exact rank to `core_linear_algebra`. This crate presents WDP carriers to them.
//! - [`genesis_questions`] binds protected questions, minimal report quotients,
//!   local report gluing, and exact information to replayed native histories.
//!   It is the first finite kernel of the working programme named `?`.
//! - Source-23 root normalization and its complete gradient/renaming key belong
//!   to `linear_algebra::gauge_pair_table`. [`genesis_gauge_result`] preserves
//!   the source's raw tables, observations and atomic raising histories.
//! - [`genesis_marked_result`] supplies source-25 fillings to the shared raw/gauge
//!   decoration owners under one writing and delegates balance arithmetic to
//!   the checked D_F/d0 owner. Carrier edits retain complete raw representatives.
//! - This crate is the single Rust WDP layer. It holds the CODA nine-stage
//!   runtime and its Q policy ([`coda`], [`coda::q`]), the Discrete Deformation
//!   Calculus ([`ddc`]), the Prime algorithms ([`prime_algos`]) and the CODA-bound
//!   solver orchestration ([`solver_of_solvers`], [`phi1_coda_adapter`],
//!   [`carrier_binding`], [`phi1_d_sel`]). Generic mathematics leaves this crate
//!   for its math owner over time; no math owner depends on this crate.
//! - [`coda::diagnostic_routing`] is CODA's replayed mathematical profile;
//!   [`prime_algos::finite_routing`] is Prime's finite lift/guard/terminal profile;
//!   [`path_kernel_gluing`] delegates to LGGR's exact matrix path kernels. These
//!   profiles do not substitute for operational continuation/authority gates.
//! - Root W (relational primitive difference, carrier symmetries, memory retention) and
//!   Root P (simplicial complex, cochain evaluation, quotient defects) are strictly demarcated.
//! - The quantum-mechanics route is finite and exact over Q and Q(i), each module a
//!   declared presentation, none a derivation of quantum theory:
//!   [`stochastic_package`] (`WDP-CH18-P07`, `P08`), [`empirical_adapter`]
//!   (`WDP-CH19-P02`, `P06`, `P07`, and the CHSH fixtures of `P05`: the PR-box run
//!   table, the global run tables and the `PairwiseBox` presentation),
//!   [`composition`] (`WDP-CH19-P08` to `P10`, and the PR-box fixture of `P05`),
//!   [`amplitude_bridge`] (`WDP-CH19-P11`, `P12`) and [`instrument_adapter`]
//!   (`WDP-CH19-P13`, `P14`).


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_94f3cca7;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_94f3cca7<T> = std::result::Result<T, BoundaryError_94f3cca7>;
pub mod amplitude_bridge;
pub mod authority_gap;
pub mod bridges;
pub mod cochains;
pub mod composition;
pub mod connection;
pub mod covering_edge_descent;
pub mod difference;
pub mod empirical_adapter;
pub mod error;
pub mod fenchel_duality;
pub mod gauge_classification;
pub mod genesis_carrier;
pub mod genesis_bell;
pub mod genesis_joint_dynamics;
pub mod genesis_construction;
pub mod genesis_geometry;
pub mod genesis_observer;
pub mod genesis_passage;
pub mod genesis_refusal;
pub mod guarded_chain_transport;
pub mod instrument_adapter;
pub mod kan_wdp_bridge;
pub mod meron_time_adapter;
pub mod observer;
pub mod observer_adapter_completeness;
pub mod observer_world_adapter;
pub mod obstruction;
pub mod path_kernel_gluing;
pub mod po000_projection_obstruction;
pub mod policy_observer_adapter;
pub mod presheaf;
pub mod primitive_axiomatics;
pub mod quantum_geometries;
pub mod question_preserving_encoding;
pub mod retention;
pub mod sql_normal_form;
pub mod stochastic_package;
pub mod types;
pub mod wdp_kernel_check;
pub mod wdp_lggr_chromatic;
pub mod wdp_rust_routes;
pub mod wdp_source_packet;
pub mod witnessed_reasoning;
pub mod witnessed_reasoning_replay;

/// CODA-bound solver orchestration over `core_solvers` and `coda::coda_gtla`.
pub mod carrier_binding;
/// CODA (Calculus of Obstruction, Descent, and Authority): nine-stage finite runtime and Q policy.
pub mod coda;
/// DDC (Discrete Deformation Calculus): operational trace alphabet, degree tower and finite Lambda ledger.
pub mod ddc;
pub mod phi1_coda_adapter;
pub mod phi1_d_sel;
/// Prime algorithms: Prime -1 candidate, Prime 000 admission, Prime 001 transport, Prime 002 continuation.
pub mod prime_algos;
pub mod solver_of_solvers;

// Re-export primary types for ease of sovereign consumption
pub use amplitude_bridge::{
    half_exponent_obstruction, readout_quadratic, readout_quartic, same_up_to_common_phase, u_pow,
    u_power_is_never_one, unit_phase, unit_square_root, Amplitude, EdgePath,
    HalfExponentObstruction, OrientedGraph, PathStep,
};
pub use authority_gap::{
    calculate_acr, calculate_acr_rate, calculate_backlog_accumulation, calculate_ngd,
    evaluate_exactness_fraud_criterion, Attestation, AuthorityPacket, GluingEvaluation,
    Institution, ObserverPacket, Proposal, Residual, Terminal, TerminalStatus, TraceRecord,
};
pub use bridges::{
    evaluate_path_homotopy, verify_cabello_18ray_parity, verify_kan_horn_filling,
    verify_sorkin_i3_cancellation, AlgebraicNonFactorableWitness, Cabello18RayWitness,
    Homotopy2CellObstruction, IdentityPathWitness, KanHornFillerWitness,
};
pub use carrier_binding::{
    carrier_manifest, to_homology_carrier, CarrierBindingError, IsingCycleGradientRepair,
};
pub use cochains::{solve_potential, FiniteComplex};
pub use composition::{
    composite_state_from_bilinear, composite_state_from_form, local_decoders, pr_box_fixture,
    BilinearForm, FormReceipt, JointState, PrBoxFixture,
};
pub use connection::U1Connection;
pub use difference::{primitive_difference, Carrier, DifferenceOutcome, PresentationMap};
pub use empirical_adapter::{
    adapt_exact, adapt_tolerant, chsh_cover, chsh_pairwise_box, chsh_value, frequencies,
    global_run_table, l1_distance_to_model, pr_box_run_table, signalling_defect,
    two_context_repair, AdapterRefusal, EmpiricalModel, MeasurementCover, RunTable, TolerantModel,
};
pub use error::WdpError;
pub use fenchel_duality::{EdgeSaturationStatus, FenchelDualityReceipt, WeightedComplex};
pub use gauge_classification::{
    evaluate_countermodels_ce1_to_ce5, single_cycle_quotient_rational,
    verify_triangle_separation_anomaly, ConvexPolyhedralGauge, GaugeClassificationReceipt,
    GraphOrbitWeightFactorizer, MixedClosureBoundChecker, MixedNormJ21, OrbitWeightRigidityReceipt,
    SingleCycleQuotientError, SoKRigidityReceipt, TransformationMonoid,
};
pub use instrument_adapter::{
    complex_phase_instrument, luders_instrument, measure_and_prepare_instrument,
    non_projective_instrument, InstrumentReceipt, OutcomeRunTable, QubitInstrument, QubitState,
};
pub use kan_wdp_bridge::{
    Hott2CellHomotopyWitness, KanHornFillingWitness, KanSimplicialComplex, ZeroDataLossReceipt,
};
pub use observer::{
    adapt_operational, adapt_quotient, adapt_retention, audit_functional_observer_relations,
    FunctionalObserverProfile, ObserverBridge, ObserverObject, OperationalObserverPacket,
    QuotientObserver,
};
pub use obstruction::{
    solve_exact_potential, solve_exact_potential_weighted, CertificateVerificationError, Cochain0,
    Cochain1, DualWitnessCertificate,
};
pub use path_kernel_gluing::{
    generate_canonical_lggr_counterexample, EvaluatedPathKernelGraph, EvaluationColor,
    LggrEvaluationReceipt, RationalMatrix2x2,
};
pub use po000_projection_obstruction::{DeclaredProjectionProblem, ProjectionObstructionReceipt};
pub use presheaf::{
    solve_observer_descent, CoveringSieve, DescentReceipt, LocalReportSection,
    SheafGluingObstruction,
};
pub use primitive_axiomatics::{
    EvaluationCarrier, EvaluationPreorder, GenesisAdmissionKernel, PrimitiveDifferenceAxiom,
    TriadSignature,
};
pub use quantum_geometries::{
    CptpChannel, QuantumDensityStalk, QuantumGeometryReceipt, QuantumObserverBundle,
};
pub use retention::{
    analyze_retention_packet, compute_behavioral_quotient, make_cm1_static_carrier,
    make_cm2_blind_readout, make_cm3_coarse_grained_report, make_cm4_nontrivial_tolerance,
    make_cm5_lossy_reset, make_cm6_trivial_carrier, make_cm7_lossy_blind, make_cm8_lossy_tolerance,
    tree_behavior_equivalent, RetentionPacket, RetentionPropertyVector,
};
pub use stochastic_package::{
    signed_shear_counterexample, ClassicalInstrument, FunctionMixture, LeftInverse,
    SignedShearReport, StochasticUpdate,
};
pub use types::{blake3_digest, sha256_digest, AuthorityEffect};
pub use wdp_lggr_chromatic::{ChromaticCertificate, ChromaticConstraintSystem};

// Origin: engine/crates_rs/core_wdp/src/lib.rs
// Claim: urn:core:crates_rs:core-wdp:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::Zero;
    use core_functional::phi1::Phi1Functional;
    use core_homology::scalar::{q, qr};
    use core_solvers::solver_lp_phi1_quotient::solve_exact_phi1;
    use std::collections::{BTreeMap, BTreeSet};

    #[test]
    fn test_end_to_end_wdp_foundations() {
        // 1. Primitive Difference & Carrier
        let carrier = Carrier::new(vec!["p0", "p1", "p2"]).unwrap();
        assert_eq!(carrier.size(), 3);
        assert_eq!(primitive_difference("p0", "p0"), DifferenceOutcome::Same);
        assert_eq!(
            primitive_difference("p0", "p1"),
            DifferenceOutcome::Different
        );

        // 2. Moore Behavioral Quotient on CM1
        let cm1 = make_cm1_static_carrier();
        let (num_blocks, _) = compute_behavioral_quotient(&cm1).unwrap();
        assert_eq!(num_blocks, 2);

        // 3. Exact Simplex and Duality Gap Certification (core_functional)
        let v = BTreeSet::from(["a".to_string(), "b".to_string(), "c".to_string()]);
        let e = vec![
            ("a".to_string(), "b".to_string()),
            ("b".to_string(), "c".to_string()),
            ("c".to_string(), "a".to_string()),
        ];
        let complex = FiniteComplex::new(v, e, vec![]).unwrap();
        let mut cochain = BTreeMap::new();
        cochain.insert(("a".to_string(), "b".to_string()), q(1));
        cochain.insert(("b".to_string(), "c".to_string()), q(1));
        cochain.insert(("c".to_string(), "a".to_string()), q(1));

        let space = complex
            .l1_quotient_presentation(&complex.edge_weights(None))
            .unwrap();
        let cert = solve_exact_phi1(&space, &complex.cochain_vector(&cochain).unwrap()).unwrap();
        assert_eq!(cert.value(), &q(3));
        // Zero duality gap: the exported primal-dual witness replays.
        let replayed =
            Phi1Functional::verify_exact_certificate(cert.certificate().clone()).unwrap();
        assert_eq!(replayed.value(), &q(3));

        // 4. Sheaf Descent
        let sieve_carrier = BTreeSet::from(["x0".to_string(), "x1".to_string()]);
        let contexts = BTreeMap::from([(
            "U0".to_string(),
            BTreeSet::from(["x0".to_string(), "x1".to_string()]),
        )]);
        let sieve = CoveringSieve::new(sieve_carrier, contexts).unwrap();
        let sec = LocalReportSection::new(
            "U0".to_string(),
            BTreeMap::from([
                ("x0".to_string(), "0".to_string()),
                ("x1".to_string(), "1".to_string()),
            ]),
        );
        let descent = solve_observer_descent(&sieve, &[sec]).unwrap();
        assert!(descent.is_compatible);

        // 5. Homology Betti Numbers (core_homology)
        let betti = KanSimplicialComplex::from_wdp_complex(&complex)
            .unwrap()
            .complex
            .rational_betti_numbers()
            .unwrap();
        assert_eq!(betti, vec![1, 1]);

        // 6. Cabello 18-ray Contextuality Parity Witness
        let cabello = verify_cabello_18ray_parity();
        assert!(cabello.is_parity_obstructed);
        assert_eq!(cabello.authority_effect, AuthorityEffect::None);
    }

    #[test]
    fn test_w10_to_w18_atlas_derivations() {
        // W10: Primitive Axiomatics
        let mut kernel =
            GenesisAdmissionKernel::new(BTreeSet::from(["x".to_string(), "y".to_string()]));
        assert!(kernel.admit_difference("x", "y", "token").is_ok());

        // W11: Fenchel-Rockafellar Duality
        let w_complex = WeightedComplex::new(
            vec!["0".to_string(), "1".to_string()],
            vec![("0".to_string(), "1".to_string())],
            vec![q(1)],
        );
        let fenchel = w_complex.solve_fenchel_duality(&[q(1)]).unwrap();
        assert!(fenchel.phi1().value().is_zero());
        Phi1Functional::verify_exact_certificate(fenchel.phi1().certificate().clone()).unwrap();

        // W12: LGGR Path Kernel Gluing Counterexample
        let (lggr_graph, cycle) = generate_canonical_lggr_counterexample();
        let (local_g, _) = lggr_graph.check_local_green(qr(1, 2)).unwrap();
        assert!(local_g);
        let (global_g, _) = lggr_graph.check_global_cycle(&cycle, qr(1, 10)).unwrap();
        assert!(!global_g); // LGGR Anomaly!

        // W13: Chromatic Obstruction Index
        let sys = ChromaticConstraintSystem {
            vertices: vec!["0".into(), "1".into(), "2".into()],
            edges: vec![
                ("0".into(), "1".into()),
                ("1".into(), "2".into()),
                ("2".into(), "0".into()),
            ],
            num_colors: 2,
            forbidden_color_pairs: BTreeSet::from([(0, 0), (1, 1)]),
        };
        assert_eq!(sys.evaluate(8, 24).unwrap().minimum.violated_edges.len(), 1);

        // W14: PO-000 exact first-order projection diagnostics.
        let p =
            linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(1, 1, vec![q(1)])
                .unwrap();
        let h =
            linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(1, 1, vec![q(0)])
                .unwrap();
        let problem = DeclaredProjectionProblem {
            first: p.clone(),
            second: p,
            generator: h,
            elapsed: qr(1, 10),
            state: vec![q(1)],
        };
        let bounds = problem.evaluate().unwrap();
        assert!(problem.verify(&bounds).unwrap());

        // W15: Quantum Density Stalks & Classical Shadow
        let rho = QuantumDensityStalk::maximally_mixed(2).unwrap();
        assert!(rho.is_valid_density_matrix());
        let shadow = rho.classical_population_shadow();
        assert_eq!(shadow, vec![qr(1, 2), qr(1, 2)]);

        // W16: Polyhedral Gauge
        let gauge = ConvexPolyhedralGauge::standard_l1(2);
        assert_eq!(gauge.evaluate(&[q(1), q(-2)]), q(3));

        // W17: Triangle Separation Anomaly
        let (l11, j21, anomaly) = verify_triangle_separation_anomaly();
        assert!(anomaly);
        assert!(j21 < l11);

        // W18: Countermodels CE1-CE5
        let ce_results = evaluate_countermodels_ce1_to_ce5();
        assert_eq!(ce_results.len(), 5);
        for (_, passes) in ce_results {
            assert!(passes);
        }
    }
}

pub mod calibration_adapter;

pub mod profile_evaluator;

pub mod clock_adequacy_adapter;

pub mod relational_retention;

pub mod functional_classification;

pub mod empirical_repair;
pub mod legacy_observer_adapters;
pub mod legacy_six_observer;
pub mod measurement_packet;
pub mod observer_site;
pub mod rational_phase_bridge;
pub mod self_reference_adapter;
pub mod tolerance_retention;

pub mod finite_cost_report;
pub mod genesis_admission_execution;
pub mod genesis_balance_transition;
pub mod genesis_gauge_result;
pub mod genesis_guard_report;
pub mod genesis_guarded_history;
pub mod genesis_marked_result;
pub mod genesis_ongoing_adapter;
pub mod genesis_primitive_execution;
pub mod genesis_source_execution;
pub mod genesis_transport_descent;
pub mod proposal_admission_bridge;

pub mod dyadic_character_adapter;
pub mod genesis_computation;
pub mod genesis_future_compression;
pub mod genesis_questions;
pub mod genesis_report_runtime;
pub mod genesis_realification_adapter;
pub mod meron_field_adapter;

/// Appendix X: calibrated interval reports, recovery-or-abstention and robust
/// observation cost.
pub mod calibrated_reports;
/// Appendix T: WDP-DIM-1 / WDP-DIM-R sharp observer completion with distinct
/// realization and repair images.
pub mod distinct_image_completion;
/// Appendix Y: joint report supports for shared affine error, with the
/// critical-value finite cost witness handed to `observation_cost`.
pub mod joint_support_recovery;
/// §14.6–14.7: complete fixed/adaptive priced-observation certificates
/// (native port of the paper's `finite_observation` reference).
pub mod observation_cost;

pub mod genesis_translation;

// Retained paper controls are private test modules, not runtime APIs.
#[cfg(test)]
extern crate self as core_wdp;
#[cfg(test)]
#[path = "../../tests/core_wdp/derivation_controls/mod.rs"]
mod paper_derivation_controls;
pub mod application_kernel;

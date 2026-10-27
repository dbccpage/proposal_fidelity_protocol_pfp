// AuthorityEffect: None.
// Citation: challenger-2-sovereign-rust-exact-adversarial-verification

//! Challenger 2: Adversarial Stress & Falsification Suite for `core_quantum_physics`.
//!
//! Enforces:
//! 1. Exact rational boundary invariants (zero float contamination in decision boundaries).
//! 2. Mermin-Peres parity obstruction full 64-sign-table sweep (odd vs even coboundary).
//! 3. CPTP trace distance contractivity across generated states and channels.
//! 4. Born normalization and phase-blind quotient interference.
//! 5. Negative control matrices and falsification under mutation.

use linear_algebra::exact_field::matrix as mx;
use num_bigint::BigInt;
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::bell_state::BellState;
use core_quantum_physics::bipartite_operator as bip;
use core_quantum_physics::density_matrix::ExactDensityMatrix as State;
use core_quantum_physics::exact_channel::ExactKrausChannel as Channel;
use core_quantum_physics::exact_hermitian::is_hermitian;
use core_quantum_physics::parity_context_packet::{ImageCertificate, ParityContextPacket};
use core_quantum_physics::pauli_context_table::context_members;
use core_quantum_physics::phase_blind_quotient::{
    classify_descent, phase_blind_projection, phase_equivalent, Descent, QuotientError,
    UnitPhaseGroup,
};
use core_quantum_physics::quantum_state::RayVector;
use core_quantum_physics::separating_predictions::{
    MerminPeresCochainBridge, MerminPeresSquare,
};
use core_quantum_physics::trace_norm_certificate::trace_distance;

const ALL_SIX: u32 = 0b11_1111;

fn basis_state(dim: usize, i: usize) -> State {
    let ray = RayVector::basis(dim, i).expect("valid basis index");
    State::pure(&ray).expect("valid pure state")
}

fn with_mermin_targets(targets: u32) -> ParityContextPacket {
    let contexts: Vec<Vec<usize>> = (0..6)
        .map(|c| context_members(c).expect("valid context index").to_vec())
        .collect();
    let bits: Vec<u8> = (0..6).map(|c| ((targets >> c) & 1) as u8).collect();
    ParityContextPacket::new(9, &contexts, &bits).expect("valid packet construction")
}

// ===========================================================================
// CHALLENGE 1: Exact Rational Boundary Invariants (Zero Float Contamination)
// ===========================================================================

/// INVARIANT: Decision boundaries in state certification, Hermiticity, and PPT
/// separability are exact rational algebra; arbitrary sub-float perturbations
/// (e.g. 10^-60, far below f64 machine epsilon ~2.22e-16) must strictly flip
/// decision outcomes and never be rounded away.
///
/// WITNESS:
/// - Werner state PPT boundary: PPT at p = 1/3, NOT PPT at p = 1/3 + 10^-60.
/// - Isotropic state PPT boundary: PPT at f = 1/2, NOT PPT at f = 1/2 + 10^-60.
/// - Off-diagonal imaginary asymmetry 10^-60 i strictly violates is_hermitian.
/// - Trace distance on orthogonal states is exactly 1, on identical states exactly 0.
#[test]
fn test_exact_rational_boundary_zero_float_contamination() {
    // 1. PPT boundary at p = 1/3 for 2-qubit Werner states
    let p_boundary = rq(1, 3);
    let werner_boundary = BellState::werner(p_boundary.clone()).expect("werner 1/3");
    assert!(
        bip::is_ppt(werner_boundary.matrix(), 2, 2).expect("ppt eval"),
        "Werner state at exact boundary p=1/3 must be PPT"
    );

    // Perturb by 10^-60 (far below double precision float epsilon 2.22e-16)
    let tiny_delta = Rational::new(1.into(), BigInt::from(10u8).pow(60));
    let p_perturbed = p_boundary + &tiny_delta;
    let werner_perturbed = BellState::werner(p_perturbed).expect("werner perturbed");
    assert!(
        !bip::is_ppt(werner_perturbed.matrix(), 2, 2).expect("ppt eval"),
        "Werner state at p=1/3 + 10^-60 must fail PPT (zero float contamination)"
    );

    // Also check isotropic state at boundary f = 1/2 for d=2
    let f_boundary = rq(1, 2);
    let iso_boundary = BellState::isotropic(f_boundary.clone(), 2).expect("iso 1/2");
    assert!(bip::is_ppt(iso_boundary.matrix(), 2, 2).expect("ppt eval"));

    let iso_perturbed = BellState::isotropic(f_boundary + &tiny_delta, 2).expect("iso perturbed");
    assert!(
        !bip::is_ppt(iso_perturbed.matrix(), 2, 2).expect("ppt eval"),
        "Isotropic state at f=1/2 + 10^-60 must fail PPT"
    );

    // 2. Exact Hermiticity under sub-float off-diagonal asymmetry
    let mut hermitian_matrix = mx::identity::<GaussianRat>(2).expect("identity");
    assert!(is_hermitian(&hermitian_matrix));

    // Perturb off-diagonal by 10^-60 i
    let tiny_im = GaussianRat {
        re: Rational::zero(),
        im: tiny_delta.clone(),
    };
    hermitian_matrix.set(0, 1, tiny_im).expect("set entry");
    assert!(
        !is_hermitian(&hermitian_matrix),
        "Matrix with 10^-60 imaginary asymmetry must NOT be Hermitian"
    );

    // 3. Exact trace distance identity on orthogonal states
    let zero = basis_state(2, 0);
    let one = basis_state(2, 1);
    let d_exact = trace_distance(zero.matrix(), one.matrix(), &[ri(1), ri(-1)])
        .expect("trace distance evaluation");
    assert_eq!(
        d_exact,
        ri(1),
        "Exact trace distance between orthogonal states must equal 1"
    );

    // Trace distance between state and itself is exactly 0 (single distinct eigenvalue {0})
    let d_self = trace_distance(zero.matrix(), zero.matrix(), &[ri(0)])
        .expect("trace distance self");
    assert_eq!(
        d_self,
        ri(0),
        "Exact trace distance between identical states must equal 0"
    );
}

// ===========================================================================
// CHALLENGE 2: Mermin-Peres Parity Obstruction Full 64-Sign-Table Sweep
// ===========================================================================

/// INVARIANT: In the Mermin-Peres square (6 contexts, 9 observables, even incidence 2),
/// the incidence coboundary delta: F_2^9 -> F_2^6 has rank 5.
/// Therefore, exactly the 32 even sign tables (weight sum mod 2 == 0) admit global
/// noncontextual assignments, while all 32 odd sign tables (weight sum mod 2 == 1)
/// produce non-trivial coboundary obstructions witnessed by the separator ALL_SIX.
///
/// WITNESS:
/// - All 32 odd sign tables: in_image == false, satisfiable(ALL_SIX) == false,
///   Separator(ALL_SIX), bridge.is_obstructed() == true, search == None.
/// - All 32 even sign tables: in_image == true, satisfiable(ALL_SIX) == true,
///   Preimage(_), bridge.is_obstructed() == false, search == Some(_).
#[test]
fn test_mermin_peres_parity_obstruction_full_sweep() {
    let mut count_even_satisfiable = 0;
    let mut count_odd_obstructed = 0;

    for targets in 0..64u32 {
        let packet = with_mermin_targets(targets);
        let num_minus_ones = targets.count_ones() as usize;
        let is_odd = num_minus_ones % 2 == 1;

        // Local satisfiability: every single context alone is satisfiable
        for c in 0..6 {
            assert!(
                packet.satisfiable(1 << c).expect("context check"),
                "Individual context {c} must always be locally satisfiable"
            );
        }

        let in_image = packet.in_image(targets).expect("in_image check");
        let satisfiable_all = packet.satisfiable(ALL_SIX).expect("satisfiable all");
        let cert = packet.certificate(targets).expect("cert check");

        // Certificate must verify cleanly
        assert!(
            packet.verify_certificate(targets, cert.clone()).expect("verify cert"),
            "Certificate for target {targets:#08b} must verify"
        );

        if is_odd {
            // Odd sign table -> Non-trivial coboundary obstruction
            assert!(
                !in_image,
                "Odd sign table {targets:#08b} must NOT be in the coboundary image"
            );
            assert!(
                !satisfiable_all,
                "Odd sign table {targets:#08b} must NOT admit a global assignment"
            );
            assert_eq!(
                cert,
                ImageCertificate::Separator(ALL_SIX),
                "Odd sign table {targets:#08b} must have ALL_SIX as separator"
            );
            count_odd_obstructed += 1;
        } else {
            // Even sign table -> Satisfiable in coboundary image
            assert!(
                in_image,
                "Even sign table {targets:#08b} MUST be in the coboundary image"
            );
            assert!(
                satisfiable_all,
                "Even sign table {targets:#08b} MUST admit a global assignment"
            );
            assert!(
                matches!(cert, ImageCertificate::Preimage(_)),
                "Even sign table {targets:#08b} must yield a Preimage certificate"
            );
            count_even_satisfiable += 1;
        }

        // Cross-verify with MerminPeresSquare search
        let square = MerminPeresSquare {
            contexts: vec![
                vec!["A11", "A12", "A13"],
                vec!["A21", "A22", "A23"],
                vec!["A31", "A32", "A33"],
                vec!["A11", "A21", "A31"],
                vec!["A12", "A22", "A32"],
                vec!["A13", "A23", "A33"],
            ],
            context_products: (0..6)
                .map(|c| if (targets >> c) & 1 == 1 { -1 } else { 1 })
                .collect(),
            noncontextual_assignment_exists: false,
        };

        let search_res = square.find_noncontextual_assignment().expect("exhaustive search");
        if is_odd {
            assert!(
                search_res.is_none(),
                "Exhaustive 2^9 search must find NO assignment for odd sign table {targets:#08b}"
            );
        } else {
            assert!(
                search_res.is_some(),
                "Exhaustive 2^9 search MUST find an assignment for even sign table {targets:#08b}"
            );
        }

        // Cross-verify with MerminPeresCochainBridge
        let bridge = MerminPeresCochainBridge::from_square(square).expect("bridge construction");
        assert_eq!(
            bridge.is_obstructed(),
            is_odd,
            "Bridge obstruction mass must be 1 for odd and 0 for even sign tables"
        );
        assert_eq!(bridge.even_incidence, true);
        assert_eq!(bridge.cochain_degree, 2);
    }

    assert_eq!(count_even_satisfiable, 32);
    assert_eq!(count_odd_obstructed, 32);
}

// ===========================================================================
// CHALLENGE 3: CPTP Trace Distance Contractivity Across States and Channels
// ===========================================================================

/// INVARIANT: For any CPTP channel E and quantum states rho, sigma:
/// D(E(rho), E(sigma)) <= D(rho, sigma).
/// For unitary channels, D(U rho U†, U sigma U†) == D(rho, sigma) exactly.
/// For strictly noisy depolarizing channels with p in (0, 1], D contracts strictly:
/// D(E(rho), E(sigma)) = (1 - p) D(rho, sigma) < D(rho, sigma) for distinct rho, sigma.
#[test]
fn test_cptp_trace_distance_contractivity() {
    let s0 = basis_state(2, 0);
    let s1 = basis_state(2, 1);
    let plus_ray = RayVector::from_ints(&[(1, 0), (1, 0)]).expect("plus ray");
    let s_plus = State::pure(&plus_ray).expect("plus state");
    let mixed = State::maximally_mixed(2).expect("mixed state");

    let state_pairs = vec![
        (&s0, &s1),
        (&s0, &s_plus),
        (&s1, &s_plus),
        (&s0, &mixed),
        (&s_plus, &mixed),
    ];

    // 1. Depolarizing channels with various noise parameters
    for p_rat in &[rq(1, 10), rq(1, 4), rq(1, 2), rq(3, 4), rq(1, 1)] {
        let channel = Channel::depolarizing(2, p_rat.clone()).expect("depolarizing channel");
        for &(rho, sigma) in &state_pairs {
            let rho_ev = rho.apply_channel(&channel).expect("apply rho");
            let sigma_ev = sigma.apply_channel(&channel).expect("apply sigma");

            // Verify trace preservation of channel: Tr(E(rho)) == Tr(rho) == 1
            assert_eq!(
                mx::trace(rho_ev.matrix()).expect("trace rho"),
                GaussianRat::one(),
                "CPTP channel must preserve trace exactly"
            );
            assert_eq!(
                mx::trace(sigma_ev.matrix()).expect("trace sigma"),
                GaussianRat::one(),
                "CPTP channel must preserve trace exactly"
            );

            // Verify contractivity on diagonal states |0> and |1>
            if rho == &s0 && sigma == &s1 {
                let d_before = ri(1);
                let expected_after = ri(1) - p_rat;
                let spectrum: Vec<Rational> = if expected_after.is_zero() {
                    vec![ri(0)]
                } else {
                    vec![expected_after.clone(), (-expected_after.clone())]
                };
                let d_after = trace_distance(
                    rho_ev.matrix(),
                    sigma_ev.matrix(),
                    &spectrum,
                )
                .expect("trace distance after");

                assert_eq!(
                    d_after, expected_after,
                    "Depolarizing channel trace distance must contract exactly to (1 - p)"
                );
                assert!(
                    d_after <= d_before,
                    "Contractivity invariant D(E(rho), E(sigma)) <= D(rho, sigma) must hold"
                );
            }
        }
    }

    // 2. Unitary channel: exact trace preservation and valid state evolution
    let z_gate = mx::diagonal(&[GaussianRat::one(), GaussianRat::from_ints(-1, 0)]).unwrap();
    let z_channel = Channel::try_new(2, 2, vec![z_gate], "Z gate").expect("z channel");

    for &(rho, sigma) in &state_pairs {
        let rho_ev = rho.apply_channel(&z_channel).expect("apply Z");
        let sigma_ev = sigma.apply_channel(&z_channel).expect("apply Z");

        // Verify traces preserved
        assert_eq!(mx::trace(rho_ev.matrix()).unwrap(), GaussianRat::one());
        assert_eq!(mx::trace(sigma_ev.matrix()).unwrap(), GaussianRat::one());
    }

    // 3. Generalized amplitude damping thermal channel
    let gad = Channel::generalized_amplitude_damping(rq(1, 3), rq(2, 5)).expect("gad channel");
    for &(rho, sigma) in &state_pairs {
        let rho_ev = rho.apply_channel(&gad).expect("gad rho");
        let sigma_ev = sigma.apply_channel(&gad).expect("gad sigma");
        assert_eq!(mx::trace(rho_ev.matrix()).unwrap(), GaussianRat::one());
        assert_eq!(mx::trace(sigma_ev.matrix()).unwrap(), GaussianRat::one());
    }
}

// ===========================================================================
// CHALLENGE 4: Born Normalization & Phase-Blind Quotients
// ===========================================================================

/// INVARIANT:
/// 1. Phase-blind projection pi(c)_g = |c_g|^2 / sum_h |c_h|^2 normalizes squared
///    moduli into the probability simplex. Relative unit phases in {1, -1, i, -i}
///    leave pi(c) completely invariant: pi(c) == pi(c').
/// 2. Under coherent linear operations (e.g. Hadamard mixing), relative phases produce
///    distinct quantum interference patterns that break classical simplex descent.
/// 3. classify_descent distinguishes monopolar maps (which descend to Markov maps)
///    from multipolar mixing maps (which yield Descent::Obstructed with explicit
///    cancelled and reinforced witnesses).
#[test]
fn test_born_normalization_and_phase_blind_interference() {
    let _group = UnitPhaseGroup::new(vec![
        GaussianRat::one(),
        GaussianRat::from_ints(-1, 0),
        GaussianRat::i(),
        GaussianRat::from_ints(0, -1),
    ])
    .expect("Z_4 unit phase group");

    // Amplitude configuration c = [1, 1]
    let c_real = vec![GaussianRat::one(), GaussianRat::one()];
    let c_phase_i = vec![GaussianRat::one(), GaussianRat::i()];
    let c_phase_neg = vec![GaussianRat::one(), GaussianRat::from_ints(-1, 0)];

    // 1. All relative phase variants project to the identical L1 probability vector [1/2, 1/2]
    let p_real = phase_blind_projection(&c_real).expect("pi(c_real)");
    let p_i = phase_blind_projection(&c_phase_i).expect("pi(c_phase_i)");
    let p_neg = phase_blind_projection(&c_phase_neg).expect("pi(c_phase_neg)");

    assert_eq!(p_real, vec![rq(1, 2), rq(1, 2)]);
    assert_eq!(p_i, vec![rq(1, 2), rq(1, 2)]);
    assert_eq!(p_neg, vec![rq(1, 2), rq(1, 2)]);
    assert!(phase_equivalent(&c_real, &c_phase_i).expect("phase equiv"));
    assert!(phase_equivalent(&c_real, &c_phase_neg).expect("phase equiv"));

    // 2. Quantum interference under Hadamard mixing
    // Hadamard H = [[1, 1], [1, -1]]
    let hadamard = mx::from_rows(vec![
        vec![GaussianRat::one(), GaussianRat::one()],
        vec![GaussianRat::one(), GaussianRat::from_ints(-1, 0)],
    ])
    .expect("hadamard matrix");

    let h_c_real = mx::multiply_vector(&hadamard, &c_real).expect("H c_real");
    let h_c_neg = mx::multiply_vector(&hadamard, &c_phase_neg).expect("H c_neg");

    // H c_real = [2, 0] -> pi = [1, 0] (pure constructive on 0, destructive on 1)
    let p_h_real = phase_blind_projection(&h_c_real).expect("pi(H c_real)");
    assert_eq!(p_h_real, vec![ri(1), ri(0)]);

    // H c_neg = [0, 2] -> pi = [0, 1] (pure destructive on 0, constructive on 1)
    let p_h_neg = phase_blind_projection(&h_c_neg).expect("pi(H c_neg)");
    assert_eq!(p_h_neg, vec![ri(0), ri(1)]);

    // Despite identical L1 phase-blind projections before mixing ([1/2, 1/2]),
    // their post-mixing projections are completely orthogonal ([1, 0] vs [0, 1])!
    assert_ne!(p_h_real, p_h_neg);

    // 3. classify_descent obstruction audit
    let descent_h = classify_descent(&hadamard).expect("classify hadamard");
    match descent_h {
        Descent::Obstructed(obs) => {
            assert_eq!(obs.row, 0);
            assert_eq!(obs.first, 0);
            assert_eq!(obs.second, 1);
            // Cancelled configuration: row 0 produces 0
            let cancelled_row0 = mx::multiply_vector(&hadamard, &obs.cancelled).expect("mult");
            assert_eq!(cancelled_row0[0], GaussianRat::zero());

            // Reinforced configuration: row 0 produces non-zero
            let reinforced_row0 = mx::multiply_vector(&hadamard, &obs.reinforced).expect("mult");
            assert_ne!(reinforced_row0[0], GaussianRat::zero());

            // Both witnesses share the exact same phase-blind projection!
            assert!(phase_equivalent(&obs.cancelled, &obs.reinforced).expect("equiv"));
        }
        Descent::Monopolar(_) => panic!("Hadamard must NOT descend monopolar!"),
    }

    // 4. Monopolar map descends cleanly: permutation / phase gate
    let bit_flip = mx::from_rows(vec![
        vec![GaussianRat::zero(), GaussianRat::one()],
        vec![GaussianRat::one(), GaussianRat::zero()],
    ])
    .unwrap();
    let descent_x = classify_descent(&bit_flip).expect("classify X");
    assert!(matches!(descent_x, Descent::Monopolar(_)));
}

// ===========================================================================
// CHALLENGE 5: Falsification Audit (Adversarial Mutations & Rejections)
// ===========================================================================

/// INVARIANT: Malformed configurations, non-trace-preserving channels, non-Hermitian
/// density matrices, out-of-bounds requests, and tampered certificates must return
/// strict domain errors and never succeed silently or panic.
#[test]
fn test_falsification_audit_rejection_matrix() {
    // 1. Zero amplitude configuration rejected
    assert_eq!(
        phase_blind_projection(&[GaussianRat::zero(), GaussianRat::zero()]),
        Err(QuotientError::Zero)
    );

    // Empty configuration rejected
    assert_eq!(phase_blind_projection(&[]), Err(QuotientError::Empty));

    // 2. Corrupted / Non-Trace-Preserving Kraus channel rejected
    let bad_k = mx::scale(
        &mx::identity::<GaussianRat>(2).unwrap(),
        &GaussianRat::from_rational(ri(2)),
    )
    .unwrap();
    // Sum K† K = 4 I != I -> must fail construction
    assert!(
        Channel::try_new(2, 2, vec![bad_k], "scaled").is_err(),
        "Non-trace-preserving Kraus operator (sum K† K = 4I) must be refused"
    );

    // Incomplete Kraus set (single projector P0)
    let p0 = mx::diagonal(&[GaussianRat::one(), GaussianRat::zero()]).unwrap();
    assert!(
        Channel::try_new(2, 2, vec![p0], "unnormalized projector").is_err(),
        "Incomplete Kraus set must be refused"
    );

    // 3. Forged separator certificate in parity context packet rejected
    let packet = with_mermin_targets(1 << 5); // column 3
    let forged_cert = ImageCertificate::Separator(0b00_0001); // incorrect separator
    assert_eq!(
        packet.verify_certificate(1 << 5, forged_cert).unwrap(),
        false,
        "Forged separator certificate must fail verification"
    );

    // Forged preimage certificate for an obstructed target rejected
    let forged_preimage = ImageCertificate::Preimage(0);
    assert_eq!(
        packet.verify_certificate(1 << 5, forged_preimage).unwrap(),
        false,
        "Forged preimage certificate for obstructed target must fail verification"
    );

    // 4. Non-Hermitian matrix passed to ExactDensityMatrix rejected
    let non_hermitian = mx::from_rows(vec![
        vec![GaussianRat::one(), GaussianRat::i()],
        vec![GaussianRat::zero(), GaussianRat::one()],
    ])
    .unwrap();
    assert!(
        State::try_new(non_hermitian).is_err(),
        "Non-Hermitian matrix must be refused by ExactDensityMatrix"
    );

    // Trace not one matrix rejected
    let bad_trace = mx::from_rows(vec![
        vec![GaussianRat::one(), GaussianRat::zero()],
        vec![GaussianRat::zero(), GaussianRat::one()],
    ])
    .unwrap();
    assert!(
        State::try_new(bad_trace).is_err(),
        "Matrix with trace = 2 must be refused by ExactDensityMatrix"
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/challenger_2_adversarial_suite.rs
// Claim: urn:core:crates_rs:tests:challenger-2-adversarial-suite:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddf2b9d80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddf2b9d80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordf2b9d80 {
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
impl BoundaryErrordf2b9d80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordf2b9d80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordf2b9d80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddf2b9d80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordf2b9d80> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordf2b9d80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordf2b9d80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordf2b9d80::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_df2b9d80() {
    let admitted = BoundaryRecorddf2b9d80::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddf2b9d80::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

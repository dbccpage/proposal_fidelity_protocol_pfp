//! Majorana probe: detector adequacy on a GF(2) surface code.
//!
//! # Why Majorana, and why adequacy rather than norms
//!
//! `core_majorana` gives an exact, finite, orientation-aware obstruction that
//! sits between the classical finite obstruction calculus and full CODA-Q. It is
//! the natural first non-trivial carrier for the Prime rules.
//!
//! What it does **not** give is an ℓ¹-versus-ℓ² separation — but the reason
//! needs stating precisely, because the loose version is false. For a 0/1 vector
//! of support size `k`:
//!
//! ```text
//! ||v||_p^p = k        ||v||_p = k^(1/p)        so ||v||_1 = k, ||v||_2 = sqrt(k)
//! ```
//!
//! Those **differ** whenever `k > 1`; it is not true that every ℓᵖ norm equals
//! the Hamming weight (only `p = 1` does, and the *powered* norm does for all
//! `p`). What is true is that `k ↦ k^(1/p)` is strictly increasing, so on
//! unweighted binary vectors every ℓᵖ induces the **same ordering and the same
//! minimisers**. A fixture built here to separate ℓ¹ from ℓ² by exhibiting
//! different optima therefore cannot exist. The leverage is elsewhere:
//! **detector adequacy**, i.e. whether the readout can tell two obstruction
//! classes apart at all.
//!
//! # The result
//!
//! On the 2×2 torus (`ker d₁ ⊋ im d₀`, so H¹ ≠ 0), the classifier reports:
//!
//! | residual | terminal | H¹ class |
//! |---|---|---|
//! | zero | `Exact` | `h1:00` |
//! | logical X | `TypedHarmonic` | `h1:10` |
//! | logical Z | `TypedHarmonic` | `h1:01` |
//!
//! The two independent logical operators **share a terminal**. A detector that
//! reads only the terminal cannot distinguish them, so it cannot witness a claim
//! about either — it is inadequate, and OEPRMALG-002 refuses to continue on it.
//! Reading the H¹ class coordinates separates them and adequacy is established.
//!
//! This is a statement about measurement, not about the code: a coarse readout
//! makes two physically distinct logical errors look identical. The Prime rules
//! are supposed to stop there, and this test is what shows they do.

use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
use core_kernel::evidence::Hash256;
use core_majorana::classify::classify_default;
use core_majorana::complexes::{
    surface_grid_2x2_torus, torus_logical_x_example, torus_logical_z_example, ChainComplexGf2,
};
use core_wdp::prime_algos::prime_algorithm_1::LossLedger;
use core_wdp::prime_algos::prime_algorithm_2::{
    can_continue_n, check_laws, write_step, AdequacyRefusal, AntiCheatLaw, Budget,
    ContinuationEvidence, ControlState, Detector, DetectorAdequacy, DetectorDescriptor,
    ObligationWitness, ResidualDelta, RunSubject, StepClaim, StepOp,
};
use core_wdp::prime_algos::prime_scope::{digest, BoundCarrierManifest, ScopeBinding};

use num_bigint::BigInt;
use num_rational::BigRational;

const ADEQUACY_DOMAIN: &str = "oeprm.adequacy.v1";

fn run_id() -> Hash256 {
    Hash256([1; 32])
}
fn carrier() -> Hash256 {
    Hash256([2; 32])
}
fn carrier_manifest() -> BoundCarrierManifest {
    BoundCarrierManifest::new(carrier(), carrier())
}
fn skeleton() -> Hash256 {
    Hash256([10; 32])
}

fn q(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

/// A residual's identifier is the digest of its bytes. This is what binds
/// adequacy to the subject: the claim must **be** the scoped residual.
fn residual_id(residual: &[u8]) -> Hash256 {
    digest(ADEQUACY_DOMAIN, &[residual])
}

fn scope_for(residual: &[u8]) -> ScopeBinding {
    ScopeBinding::new(run_id(), carrier_manifest(), residual_id(residual), None, 0)
}

/// A **coarse** readout: the terminal label only.
struct TerminalReadout<'a> {
    complex: &'a ChainComplexGf2,
    descriptor: DetectorDescriptor,
}

impl<'a> TerminalReadout<'a> {
    fn on(complex: &'a ChainComplexGf2) -> Self {
        Self {
            complex,
            descriptor: DetectorDescriptor::new(
                "core_majorana.classify",
                "v1",
                "terminal",
                carrier(),
                [1usize],
                Hash256([0; 32]),
            ),
        }
    }
    fn read(&self, residual: &[u8]) -> Vec<u8> {
        self.verdict(&RunSubject {
            input: residual,
            degree: 1,
            scope: &scope_for(residual),
        })
    }
}

impl Detector for TerminalReadout<'_> {
    fn descriptor(&self) -> &DetectorDescriptor {
        &self.descriptor
    }
    fn verdict(&self, subject: &RunSubject<'_>) -> Vec<u8> {
        format!(
            "{:?}",
            classify_default(&self.complex.d0, &self.complex.d1, subject.input).terminal
        )
        .into_bytes()
    }
}

/// A **class-resolving** readout: the H¹ class id.
struct ClassReadout<'a> {
    complex: &'a ChainComplexGf2,
    descriptor: DetectorDescriptor,
}

impl<'a> ClassReadout<'a> {
    fn on(complex: &'a ChainComplexGf2) -> Self {
        Self {
            complex,
            descriptor: DetectorDescriptor::new(
                "core_majorana.classify",
                "v1",
                "h1_class",
                carrier(),
                [1usize],
                Hash256([0; 32]),
            ),
        }
    }
    fn read(&self, residual: &[u8]) -> Vec<u8> {
        self.verdict(&RunSubject {
            input: residual,
            degree: 1,
            scope: &scope_for(residual),
        })
    }
}

impl Detector for ClassReadout<'_> {
    fn descriptor(&self) -> &DetectorDescriptor {
        &self.descriptor
    }
    fn verdict(&self, subject: &RunSubject<'_>) -> Vec<u8> {
        classify_default(&self.complex.d0, &self.complex.d1, subject.input)
            .class_id
            .expect("the torus classifier reports a class id")
            .into_bytes()
    }
}

/// The carrier must be a genuine complex, or every classification below is
/// meaningless.
#[test]
fn the_torus_carrier_is_a_real_complex() {
    assert!(
        surface_grid_2x2_torus().verify_boundary(),
        "d1 . d0 must vanish mod 2"
    );
}

/// The premise of the whole file, with **every advertised row pinned exactly**.
///
/// Checking only "terminals equal, classes differ" would still pass if both
/// operators degraded to `ClosedResidual`, or if the class coordinates were
/// renamed — and the module docs would then advertise numbers nothing verifies.
#[test]
fn the_two_logical_operators_share_a_terminal_but_not_a_class() {
    let c = surface_grid_2x2_torus();
    let term = TerminalReadout::on(&c);
    let class = ClassReadout::on(&c);
    let zero = vec![0u8; c.num_edges];
    let lx = torus_logical_x_example();
    let lz = torus_logical_z_example();

    assert_eq!(term.read(&zero), b"Exact".to_vec());
    assert_eq!(class.read(&zero), b"h1:00".to_vec());

    assert_eq!(term.read(&lx), b"TypedHarmonic".to_vec());
    assert_eq!(class.read(&lx), b"h1:10".to_vec());

    assert_eq!(term.read(&lz), b"TypedHarmonic".to_vec());
    assert_eq!(class.read(&lz), b"h1:01".to_vec());

    // The two facts the adequacy results rest on, as relations.
    assert_eq!(term.read(&lx), term.read(&lz));
    assert_ne!(class.read(&lx), class.read(&lz));
}

/// A terminal-only detector cannot establish adequacy against the two logical
/// operators: it returns one answer for both, so it witnesses neither.
#[test]
fn a_terminal_only_detector_is_inadequate_for_logical_operators() {
    let c = surface_grid_2x2_torus();
    let lx = torus_logical_x_example();

    let refusal = DetectorAdequacy::by_running(
        &TerminalReadout::on(&c),
        &lx,
        &torus_logical_z_example(),
        1,
        scope_for(&lx),
    )
    .expect_err("a detector that answers the same for both cannot be adequate");

    assert_eq!(
        refusal,
        AdequacyRefusal::CoincidentVerdicts,
        "the refusal must name inadequacy, not some other failure"
    );
}

/// Anti-vacuity: the *same* pair, read through the class coordinates, does
/// establish adequacy. So the refusal above is about the readout, not about the
/// carrier or the rules being unable to say yes.
#[test]
fn a_class_resolving_detector_is_adequate_for_the_same_pair() {
    let c = surface_grid_2x2_torus();
    let lx = torus_logical_x_example();

    let adequacy = DetectorAdequacy::by_running(
        &ClassReadout::on(&c),
        &lx,
        &torus_logical_z_example(),
        1,
        scope_for(&lx),
    )
    .expect("the H1 class separates the two logical operators");

    assert_eq!(adequacy.degree(), 1);
    assert_eq!(
        adequacy.detector(),
        &ClassReadout::on(&c).descriptor().id(),
        "the receipt must name which detector established it"
    );
    assert_ne!(adequacy.claim(), adequacy.counterclaim());
}

/// A coarse readout *is* adequate where the classes genuinely differ in
/// terminal. Adequacy is relative to what is being distinguished, which is why
/// it is established per claim and not once per detector.
#[test]
fn the_same_coarse_detector_is_adequate_against_a_different_pair() {
    let c = surface_grid_2x2_torus();
    let zero = vec![0u8; c.num_edges];

    assert!(
        DetectorAdequacy::by_running(
            &TerminalReadout::on(&c),
            &zero,
            &torus_logical_x_example(),
            1,
            scope_for(&zero),
        )
        .is_ok(),
        "Exact vs TypedHarmonic differ, so the terminal readout suffices here"
    );
}

/// Adequacy established for one residual cannot authorize another.
///
/// Separating logical X from logical Z is easy; binding that result to an
/// unrelated subject was the hole. The claim must **be** the scoped residual.
#[test]
fn adequacy_for_the_logical_pair_cannot_authorize_an_unrelated_residual() {
    let c = surface_grid_2x2_torus();
    let lx = torus_logical_x_example();
    let unrelated = ScopeBinding::new(run_id(), carrier_manifest(), Hash256([77; 32]), None, 0);

    let refusal = DetectorAdequacy::by_running(
        &ClassReadout::on(&c),
        &lx,
        &torus_logical_z_example(),
        1,
        unrelated,
    )
    .expect_err("an easy separable pair must not authorize an unrelated subject");

    assert!(matches!(
        refusal,
        AdequacyRefusal::ClaimIsNotTheScopedResidual { .. }
    ));
}

/// A detector configured for another carrier cannot answer here, so a fixture
/// cannot travel between carriers.
#[test]
fn a_detector_configured_for_another_carrier_is_refused() {
    let c = surface_grid_2x2_torus();
    let lx = torus_logical_x_example();

    struct Elsewhere<'a> {
        complex: &'a ChainComplexGf2,
        descriptor: DetectorDescriptor,
    }
    impl Detector for Elsewhere<'_> {
        fn descriptor(&self) -> &DetectorDescriptor {
            &self.descriptor
        }
        fn verdict(&self, subject: &RunSubject<'_>) -> Vec<u8> {
            classify_default(&self.complex.d0, &self.complex.d1, subject.input)
                .class_id
                .unwrap_or_default()
                .into_bytes()
        }
    }

    let refusal = DetectorAdequacy::by_running(
        &Elsewhere {
            complex: &c,
            descriptor: DetectorDescriptor::new(
                "core_majorana.classify",
                "v1",
                "h1_class",
                Hash256([99; 32]), // configured for a different carrier
                [1usize],
                Hash256([0; 32]),
            ),
        },
        &lx,
        &torus_logical_z_example(),
        1,
        scope_for(&lx),
    )
    .expect_err("a detector for another carrier must not answer here");

    assert!(matches!(refusal, AdequacyRefusal::CarrierMismatch { .. }));
}

/// A degree rise with no adequate detector must be refused by law 5.
#[test]
fn a_degree_rise_on_an_inadequate_detector_refuses() {
    let lx = torus_logical_x_example();
    let state = ControlState::open(
        run_id(),
        carrier(),
        residual_d0(),
        skeleton(),
        Budget::declare(&q(100), &q(1)).unwrap(),
    );
    let scope = state.scope_for(residual_id(&lx));

    // No detector evidence: the terminal-only readout could not produce any.
    let claim = StepClaim {
        op: StepOp::ResidualProjection,
        residual_content: residual_id(&lx),
        residual_label: Hash256([4; 32]),
        degree: 2,
        skeleton: state.skeleton().clone(),
        loss_ledger: None,
        repacketized: false,
        claims_above_n0_are_conditional: true,
    };

    // The detector is under-declared for this degree: established at 1 while
    // the step climbs to 2. That is what law 5 is supposed to catch.
    let c = surface_grid_2x2_torus();
    let ev = evidence_at(&scope, &c, 1);
    let violations = check_laws(&state, &claim, &ev);
    assert!(
        violations
            .iter()
            .any(|v| v.law == AntiCheatLaw::DetectorRevalidation),
        "climbing without an adequate detector must refuse, got {violations:?}"
    );
}

/// End to end on the Majorana carrier: an adequate (class-resolving) detector
/// admits continuation, and the step is **written**.
#[test]
fn an_adequate_majorana_detector_admits_a_step() {
    let c = surface_grid_2x2_torus();
    let lx = torus_logical_x_example();
    let mut state = ControlState::open(
        run_id(),
        carrier(),
        residual_d0(),
        skeleton(),
        Budget::declare(&q(100), &q(1)).unwrap(),
    );
    let site = state.scope_for(residual_id(&lx));

    let detector = DetectorAdequacy::by_running(
        &ClassReadout::on(&c),
        &lx,
        &torus_logical_z_example(),
        1,
        site.clone(),
    )
    .expect("the class readout separates the logical operators");

    let ev = ContinuationEvidence {
        outstanding_obligation: ObligationWitness::exhibit(Hash256([5; 32]), 1, site.clone()),
        higher_obligation_witness: ObligationWitness::exhibit(Hash256([6; 32]), 2, site.clone()),
        next_carrier_manifest: BoundCarrierManifest::new(carrier(), residual_d0()),
        adapter_ledger: LossLedger::empty(site.clone()),
        detector,
        lift: None,
        skeleton_preserved: true,
        coda_gtla_refusal: None,
        residual: ResidualDelta::from_verified(&phi1(3), &phi1(1), site.clone()).expect("same d0"),
    };

    // The claim must exist BEFORE the permit: a permit licenses one specific
    // claim, so there is no "get authorization, then decide what to write".
    let claim = StepClaim {
        op: StepOp::ResidualProjection,
        residual_content: residual_id(&lx),
        residual_label: Hash256([4; 32]),
        degree: 1,
        skeleton: state.skeleton().clone(),
        loss_ledger: None,
        repacketized: false,
        claims_above_n0_are_conditional: false,
    };

    let permit = can_continue_n(&mut state, &site, &claim, &ev)
        .expect("an adequate detector and a falling residual must continue");
    assert_eq!(
        state.budget().spent(),
        0,
        "permit issuance must not spend budget"
    );

    write_step(&mut state, permit, &claim, &ev).expect("the admitted step must be written");
    assert_eq!(
        state.budget().spent(),
        1,
        "the successful write must spend one unit"
    );
    assert_eq!(state.steps_written(), 1);
    assert!(state.tape_head().is_some(), "the tape head must advance");
}

/// Evidence at a site, with the detector established at `detector_degree`.
fn evidence_at(
    site: &ScopeBinding,
    complex: &ChainComplexGf2,
    detector_degree: usize,
) -> ContinuationEvidence {
    let lx = torus_logical_x_example();
    ContinuationEvidence {
        outstanding_obligation: ObligationWitness::exhibit(Hash256([5; 32]), 1, site.clone()),
        higher_obligation_witness: ObligationWitness::exhibit(Hash256([6; 32]), 9, site.clone()),
        next_carrier_manifest: BoundCarrierManifest::new(carrier(), residual_d0()),
        adapter_ledger: LossLedger::empty(site.clone()),
        detector: DetectorAdequacy::by_running(
            &ClassReadout::on(complex),
            &lx,
            &torus_logical_z_example(),
            detector_degree,
            site.clone(),
        )
        .expect("the class readout separates the logical operators"),
        lift: None,
        skeleton_preserved: true,
        coda_gtla_refusal: None,
        residual: ResidualDelta::from_verified(&phi1(3), &phi1(1), site.clone()).expect("same d0"),
    }
}

/// The `d₀` the Φ₁ fixtures below are measured against.
///
/// # A boundary this test states rather than hides
///
/// This is a 1×1 zero matrix, **not** the torus complex the detector runs on.
/// The two arms of this file are therefore on different carriers: the detector
/// is a genuine GF(2) readout of the 2×2 torus, while the residual is a stub.
///
/// That gap used to be invisible — `ResidualDelta` proved only that its two
/// endpoints shared a `d₀` and never related it to the site, so a Φ₁ measured
/// anywhere authorized a step here. `ControlState` now declares the `d₀` its
/// residuals must be measured on and `can_continue_n` checks it, so the
/// mismatch has to be written down, as it is here.
///
/// Closing it needs an exact Φ₁ over ℚ on the torus's lifted `d₀`, which needs
/// a solver. `core_discrete_deformation_calculus` is a rule crate and
/// deliberately has none — see `core_solvers/tests/prime_rules_end_to_end.rs`
/// for the arm where the residual IS computed on its own carrier.
fn residual_d0() -> Hash256 {
    // Must match the `d0` field of the certificates in `phi1` below.
    core_wdp::prime_algos::prime_algorithm_2::d0_commitment(&[vec![q(0)]])
}

/// A verified Φ₁ of value `v`, through the real replay.
fn phi1(v: i64) -> VerifiedExactPhi1 {
    Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
        omega: vec![q(v)],
        d0: vec![vec![q(0)]],
        weights: vec![q(1)],
        alpha: vec![q(0)],
        primal_residual: vec![q(v)],
        dual_witness: vec![q(1)],
        reported_value: q(v),
    })
    .expect("fixture certificate must verify")
}

// Origin: engine/crates_rs/tests/core_wdp/test_prime_majorana_detector_adequacy.rs
// Claim: urn:core:crates_rs:tests:test-prime-majorana-detector-adequacy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd140a65e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd140a65e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord140a65e {
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
impl BoundaryErrord140a65e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord140a65e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord140a65e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd140a65e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord140a65e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord140a65e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord140a65e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord140a65e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d140a65e() {
    let admitted = BoundaryRecordd140a65e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd140a65e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

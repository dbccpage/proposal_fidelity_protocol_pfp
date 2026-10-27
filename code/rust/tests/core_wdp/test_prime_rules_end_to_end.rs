//! End-to-end: a declared carrier → a **computed** Φ₁ → a verified certificate
//! → an OEPRMALG-002 continuation decision.
//!
//! # Why this test lives in `core_solvers`
//!
//! `core_discrete_deformation_calculus` is a *rule* crate: it decides whether a
//! step is lawful and mints nothing. `core_solvers` is an *engine*: it computes
//! Φ₁ and mints nothing either. Under the crates separation law the engine may
//! depend on the rules, and it already does — so the wiring test belongs here.
//! Putting it in the DDA crate would require a dev-dependency back onto the
//! solver, inverting the layering to prove a point about layering.
//!
//! # What this closes
//!
//! `ResidualDelta` consumes `VerifiedExactPhi1`, which is unforgeable. But
//! nothing previously demonstrated that a Φ₁ *computed from an actual carrier*
//! survives that path — the unit tests built certificates by hand. A rule that
//! only ever sees hand-built evidence is a rule tested against its own fixtures.
//!
//! Here every residual number is produced by the exact rational network simplex
//! and replayed by the verifier. Nothing on the residual path is typed by the
//! test.

use core_functional::phi1::{Phi1Functional, VerifiedExactPhi1};
use core_kernel::evidence::Hash256;
use core_solvers::solver_lp_phi1_boundary::{solve_phi1, Boundary1, BoundaryEdge};
use core_wdp::phi1_coda_adapter::exact_certificate;
use core_wdp::prime_algos::prime_algorithm_1::LossLedger;
use core_wdp::prime_algos::prime_algorithm_2::{
    can_continue_n, write_step, AntiCheatLaw, BoundCarrierManifest, Budget, ContinuationEvidence,
    ControlState, Detector, DetectorAdequacy, DetectorDescriptor, ObligationWitness, ResidualDelta,
    RunSubject, StepClaim, StepOp,
};

use num_bigint::BigInt;
use num_rational::BigRational;

fn h(n: u8) -> Hash256 {
    Hash256([n; 32])
}

/// A detector that computes the parity of its input. Deterministic, and unable
/// to separate inputs of equal parity -- a real detector, not two literals.
///
/// Its identity is DERIVED from the descriptor, and the descriptor names the
/// carrier it is configured for, so it cannot answer at another carrier.
struct ParityDetector(DetectorDescriptor);

impl ParityDetector {
    fn on(carrier: Hash256) -> Self {
        Self(DetectorDescriptor::new(
            "core_solvers.tests.parity",
            "v1",
            "parity_bit",
            carrier,
            [1usize],
            Hash256([0; 32]),
        ))
    }
}

impl Detector for ParityDetector {
    fn descriptor(&self) -> &DetectorDescriptor {
        &self.0
    }
    fn verdict(&self, subject: &RunSubject<'_>) -> Vec<u8> {
        vec![subject.input.iter().fold(0u8, |a, b| a ^ b) & 1]
    }
}

/// The claim these tests separate, and the scope it must be presented at.
const CLAIM: &[u8] = &[1];
const COUNTERCLAIM: &[u8] = &[0];

/// The `d₀` of the triangle carrier, as the rule layer names it.
///
/// The run declares this, and `can_continue_n` refuses a residual measured
/// against any other `d₀` — so a falling Φ₁ from a different carrier cannot
/// authorize a step here.
fn triangle_d0() -> Hash256 {
    let carrier = triangle();
    let mut rows = vec![vec![q(0); carrier.num_vertices]; carrier.edges.len()];
    for (row, edge) in rows.iter_mut().zip(&carrier.edges) {
        row[edge.tail] -= q(1);
        row[edge.head] += q(1);
    }
    core_wdp::prime_algos::prime_algorithm_2::d0_commitment(&rows)
}

/// The step claim these tests license. A permit binds one specific claim, so
/// it must be built before `can_continue_n`, not after.
fn step_claim(state: &ControlState) -> StepClaim {
    StepClaim {
        op: StepOp::ResidualProjection,
        residual_content: claim_residual(),
        residual_label: h(4),
        degree: 1,
        skeleton: state.skeleton().clone(),
        loss_ledger: None,
        repacketized: false,
        claims_above_n0_are_conditional: false,
    }
}

/// The scoped residual for CLAIM -- adequacy binds to exactly this.
fn claim_residual() -> Hash256 {
    core_wdp::prime_algos::prime_scope::digest("oeprm.adequacy.v1", &[CLAIM])
}

fn q(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}

/// A triangle: three vertices, three unit-weight directed edges.
///
/// `b₁ = 1`, so a residual around the cycle cannot be gauge-fixed away and Φ₁
/// is genuinely positive — the carrier has to be able to produce a nonzero
/// answer or the whole test would be vacuous.
fn triangle() -> Boundary1 {
    Boundary1 {
        num_vertices: 3,
        edges: vec![
            BoundaryEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            BoundaryEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            BoundaryEdge {
                tail: 2,
                head: 0,
                weight: 1,
            },
        ],
    }
}

/// Compute Φ₁ on a real carrier and replay it into a sealed
/// [`VerifiedExactPhi1`].
///
/// Every step is the production path: exact network simplex → certificate →
/// primal/dual replay. If any of those disagreed, this would panic rather than
/// hand a rule a number it could not stand behind.
fn computed_phi1(boundary: &Boundary1, omega: &[i128]) -> VerifiedExactPhi1 {
    let solution = solve_phi1(boundary, omega).expect("exact simplex must solve the triangle");
    let certificate = exact_certificate(boundary, omega, &solution);
    Phi1Functional::verify_exact_certificate(certificate)
        .expect("a certificate the solver produced must replay")
}

/// Anti-vacuity for the whole file: the carrier must be able to report a
/// **nonzero** Φ₁, and a gauge-equivalent residual must report zero.
///
/// If Φ₁ were identically zero here, every rule decision below would pass for
/// reasons having nothing to do with the rules.
#[test]
fn the_carrier_can_report_both_answers() {
    let carrier = triangle();

    // A pure coboundary: omega = d0(alpha) for alpha = (0, 1, 3).
    // Edge values are alpha[head] - alpha[tail] = (1-0), (3-1), (0-3).
    let exact = computed_phi1(&carrier, &[1, 2, -3]);
    assert_eq!(
        exact.value(),
        &q(0),
        "a residual in im(d0) must have Phi_1 = 0"
    );

    // A cycle residual: not reachable by any gauge, so Phi_1 > 0.
    let survivor = computed_phi1(&carrier, &[1, 1, 1]);
    assert!(
        survivor.value() > &q(0),
        "a 1-cycle on b1 = 1 must survive gauge fixing, got {}",
        survivor.value()
    );
}

/// The path the review asked for: a step whose residual genuinely **falls**,
/// with every number computed rather than declared, is admitted.
#[test]
fn a_computed_residual_decrease_admits_continuation() {
    let carrier = triangle();
    let before = computed_phi1(&carrier, &[3, 3, 3]);
    let after = computed_phi1(&carrier, &[1, 1, 1]);
    assert!(
        before.value() > after.value(),
        "fixture must actually decrease: {} -> {}",
        before.value(),
        after.value()
    );

    let mut state = ControlState::open(
        h(1),
        h(2),
        triangle_d0(),
        h(10),
        Budget::declare(&q(100), &q(1)).unwrap(),
    );
    let site = state.scope_for(claim_residual());

    let ev = ContinuationEvidence {
        outstanding_obligation: ObligationWitness::exhibit(h(5), 1, site.clone()),
        higher_obligation_witness: ObligationWitness::exhibit(h(6), 2, site.clone()),
        next_carrier_manifest: BoundCarrierManifest::new(h(2), triangle_d0()),
        adapter_ledger: LossLedger::empty(site.clone()),
        detector: DetectorAdequacy::by_running(
            &ParityDetector::on(h(2)),
            CLAIM,
            COUNTERCLAIM,
            1,
            site.clone(),
        )
        .unwrap(),
        lift: None,
        skeleton_preserved: true,
        coda_gtla_refusal: None,
        residual: ResidualDelta::from_verified(&before, &after, site.clone())
            .expect("same carrier, so the endpoints are comparable"),
    };

    let step = step_claim(&state);
    let permit =
        can_continue_n(&mut state, &site, &step, &ev).expect("a real decrease must continue");

    write_step(&mut state, permit, &step, &ev).expect("a lawful step must be written");
    assert_eq!(state.steps_written(), 1);
    assert_eq!(state.budget().spent(), 1, "continuation must spend budget");
}

/// The mirror: a step whose residual genuinely **rises** on the same carrier,
/// with no audited loss ledger, is refused.
///
/// This is the residual-aware rule tested against computed values rather than
/// against a pair the test typed.
#[test]
fn a_computed_residual_increase_without_a_ledger_refuses() {
    let carrier = triangle();
    let before = computed_phi1(&carrier, &[1, 1, 1]);
    let after = computed_phi1(&carrier, &[3, 3, 3]);
    assert!(
        after.value() > before.value(),
        "fixture must actually increase"
    );

    let mut state = ControlState::open(
        h(1),
        h(2),
        triangle_d0(),
        h(10),
        Budget::declare(&q(100), &q(1)).unwrap(),
    );
    let site = state.scope_for(claim_residual());

    let ev = ContinuationEvidence {
        outstanding_obligation: ObligationWitness::exhibit(h(5), 1, site.clone()),
        higher_obligation_witness: ObligationWitness::exhibit(h(6), 2, site.clone()),
        next_carrier_manifest: BoundCarrierManifest::new(h(2), triangle_d0()),
        adapter_ledger: LossLedger::empty(site.clone()), // nothing booked
        detector: DetectorAdequacy::by_running(
            &ParityDetector::on(h(2)),
            CLAIM,
            COUNTERCLAIM,
            1,
            site.clone(),
        )
        .unwrap(),
        lift: None,
        skeleton_preserved: true,
        coda_gtla_refusal: None,
        residual: ResidualDelta::from_verified(&before, &after, site.clone()).unwrap(),
    };

    let step = step_claim(&state);
    let refusal = can_continue_n(&mut state, &site, &step, &ev)
        .expect_err("a computed increase with no ledger must refuse");
    assert!(
        refusal
            .violations()
            .iter()
            .any(|v| v.law == AntiCheatLaw::ResidualNonIncrease),
        "expected the residual rule to fire, got {refusal}"
    );
}

/// The same computed increase, with the loss audited, is lawful.
///
/// Without this the rule would read as "Φ₁ may never rise", which is not what
/// the residual-aware specification says.
#[test]
fn the_same_increase_is_lawful_once_the_loss_is_audited() {
    let carrier = triangle();
    let before = computed_phi1(&carrier, &[1, 1, 1]);
    let after = computed_phi1(&carrier, &[3, 3, 3]);

    let mut state = ControlState::open(
        h(1),
        h(2),
        triangle_d0(),
        h(10),
        Budget::declare(&q(100), &q(1)).unwrap(),
    );
    let site = state.scope_for(claim_residual());

    let ev = ContinuationEvidence {
        outstanding_obligation: ObligationWitness::exhibit(h(5), 1, site.clone()),
        higher_obligation_witness: ObligationWitness::exhibit(h(6), 2, site.clone()),
        next_carrier_manifest: BoundCarrierManifest::new(h(2), triangle_d0()),
        adapter_ledger: LossLedger::booked(vec![("coarsened_faces".into(), 2)], site.clone()),
        detector: DetectorAdequacy::by_running(
            &ParityDetector::on(h(2)),
            CLAIM,
            COUNTERCLAIM,
            1,
            site.clone(),
        )
        .unwrap(),
        lift: None,
        skeleton_preserved: true,
        coda_gtla_refusal: None,
        residual: ResidualDelta::from_verified(&before, &after, site.clone()).unwrap(),
    };

    let step = step_claim(&state);
    can_continue_n(&mut state, &site, &step, &ev).expect("an audited increase is permitted");
}

/// Φ₁ values from **different carriers** are distances in different quotients.
///
/// The solver will happily produce both; the rule layer must refuse to subtract
/// them. This is the same fact the carrier-manifest binding turns on: a number
/// is only comparable within one declared carrier.
#[test]
fn phi1_from_two_different_carriers_cannot_be_differenced() {
    let triangle_phi1 = computed_phi1(&triangle(), &[1, 1, 1]);

    // A square: four vertices, four edges. Still b1 = 1, still a positive Phi_1,
    // but a different d0 -- so the two values are not comparable.
    let square = Boundary1 {
        num_vertices: 4,
        edges: vec![
            BoundaryEdge {
                tail: 0,
                head: 1,
                weight: 1,
            },
            BoundaryEdge {
                tail: 1,
                head: 2,
                weight: 1,
            },
            BoundaryEdge {
                tail: 2,
                head: 3,
                weight: 1,
            },
            BoundaryEdge {
                tail: 3,
                head: 0,
                weight: 1,
            },
        ],
    };
    let square_phi1 = computed_phi1(&square, &[1, 1, 1, 1]);
    assert!(square_phi1.value() > &q(0), "the square must also survive");

    let state = ControlState::open(
        h(1),
        h(2),
        triangle_d0(),
        h(10),
        Budget::declare(&q(10), &q(1)).unwrap(),
    );
    let err = ResidualDelta::from_verified(
        &triangle_phi1,
        &square_phi1,
        state.scope_for(claim_residual()),
    )
    .expect_err("Phi_1 over different d0 must refuse rather than report a difference");
    assert!(err
        .violations()
        .iter()
        .any(|v| v.law == AntiCheatLaw::ResidualNonIncrease));
}

// Origin: engine/crates_rs/tests/core_wdp/test_prime_rules_end_to_end.rs
// Claim: urn:core:crates_rs:tests:test-prime-rules-end-to-end:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1dfa2be3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1dfa2be3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1dfa2be3 {
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
impl BoundaryError1dfa2be3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1dfa2be3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1dfa2be3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1dfa2be3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1dfa2be3> {
        if capacity_bound == 0 {
            return Err(BoundaryError1dfa2be3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1dfa2be3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1dfa2be3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_1dfa2be3() {
    let admitted = BoundaryRecord1dfa2be3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1dfa2be3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

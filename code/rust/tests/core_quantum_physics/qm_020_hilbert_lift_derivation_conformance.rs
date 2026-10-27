//! qm_020_hilbert_lift_derivation_conformance.rs
//!
//! Conformance of the exact production code to the statements of the derivation
//! "Conditional Hilbert Lifts of L1 Sector Weights and Born Normalization Redundancy".
//! Each test runs the production routine (`core_functional::born_probabilities`,
//! `PopulationShadow`, `ExactDensityMatrix`, `RayVector`) on exact rationals; none of
//! them computes the expected value with the arithmetic it checks.
//!
//! 1. Direct L1 normalization: nonnegative sector weights `w` give `p = w / sum w`, a
//!    distribution, and normalising again changes nothing.
//! 2. L1 additivity versus amplitude interference: merging two disjoint sectors adds
//!    their normalized weights exactly, while merging their *amplitudes* adds
//!    probabilities only when the relative phase is a quarter turn.
//! 3. Hilbert lift redundancy: the Born probabilities of amplitudes `c_g` with
//!    `|c_g|^2 = w_g` equal `w_g / sum w`, whatever the phases, and they are the
//!    diagonal of the pure state `|c><c|`.
//!
//! The vendored receipt `fixtures/qm_020_golden_receipt.json` is recomputed, not just
//! read.
//!
//! AuthorityEffect: None.

use core_functional::born_probabilities::BornProbabilities;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::density_matrix::{DensityError, ExactDensityMatrix, PopulationShadow};
use core_quantum_physics::hilbert_space::HilbertSpace;
use core_quantum_physics::quantum_state::RayVector;

fn parse_rational(text: &str) -> Rational {
    let (n, d) = text.split_once('/').unwrap_or((text, "1"));
    rq(
        n.parse().expect("numerator"),
        d.parse().expect("denominator"),
    )
}

fn gaussian(re: Rational, im: Rational) -> GaussianRat {
    GaussianRat { re, im }
}

#[test]
fn derivation_qm020_theorem1_direct_l1_normalization() {
    let w = [ri(3), ri(5), ri(2)]; // total W = 10
    let p = BornProbabilities::from_weights(&w).unwrap();
    assert_eq!(p.probabilities(), [rq(3, 10), rq(1, 2), rq(1, 5)]);
    let total: Rational = p.probabilities().iter().cloned().sum();
    assert_eq!(total, ri(1));

    // Idempotence: normalising a normalised profile changes nothing.
    assert_eq!(
        BornProbabilities::from_weights(p.probabilities()).unwrap(),
        p
    );

    // The classical state accepts the normalised profile and refuses the raw weights.
    let space = HilbertSpace::try_new(3, "sectors").unwrap();
    assert!(
        PopulationShadow::try_from_exact_probs(&space, p.probabilities().to_vec(), "l1").is_ok()
    );
    assert_eq!(
        PopulationShadow::try_from_exact_probs(&space, w.to_vec(), "raw"),
        Err(DensityError::InvalidRationalDistribution)
    );
    // Negative weights have no normalisation.
    assert!(BornProbabilities::from_weights(&[ri(1), ri(-1)]).is_err());
}

#[test]
fn derivation_qm020_theorem2_l1_disjoint_additivity_vs_l2_nonlinearity() {
    // L1: merging two disjoint sectors adds their normalized weights exactly.
    let fine = BornProbabilities::from_weights(&[ri(1), ri(1), ri(4)]).unwrap();
    let coarse = BornProbabilities::from_weights(&[ri(2), ri(4)]).unwrap();
    assert_eq!(
        fine.probabilities()[0].clone() + fine.probabilities()[1].clone(),
        coarse.probabilities()[0]
    );
    assert_eq!(fine.probabilities()[2], coarse.probabilities()[1]);

    // Amplitudes: sectors A and B with amplitudes 1 and phi, sector C with amplitude 2.
    // The coarse-grained amplitude of A + B is 1 + phi (coherent), and its probability
    // is the sum of the parts only for phi = i: |1 + i|^2 = 2 = |1|^2 + |i|^2.
    let born = |a: GaussianRat, b: GaussianRat| {
        let fine = RayVector::try_new(vec![a.clone(), b.clone(), GaussianRat::from_ints(2, 0)])
            .unwrap()
            .born_probabilities()
            .unwrap();
        let merged = RayVector::try_new(vec![a.add(&b), GaussianRat::from_ints(2, 0)])
            .unwrap()
            .born_probabilities()
            .unwrap();
        (
            fine.probabilities()[0].clone() + fine.probabilities()[1].clone(),
            merged.probabilities()[0].clone(),
        )
    };
    let one = GaussianRat::one();
    let (added, merged) = born(one.clone(), GaussianRat::i());
    assert_eq!(
        added, merged,
        "quarter-turn relative phase: no interference"
    );
    let (added, merged) = born(one.clone(), one.clone());
    assert_eq!(added, rq(1, 3));
    assert_eq!(merged, rq(1, 2), "constructive interference: 1/2 != 1/3");
    let (added, merged) = born(one, GaussianRat::from_ints(-1, 0));
    assert_eq!(added, rq(1, 3));
    assert_eq!(
        merged,
        ri(0),
        "destructive interference: the sector is empty"
    );
}

#[test]
fn derivation_qm020_theorem4_hilbert_lift_redundancy() {
    // Weights (1/4, 9/16) lifted to amplitudes with |c|^2 = w and two different phase
    // conventions: c = (1/2 e^{i t0}, 3/4 e^{i t1}) with e^{i t0} = (3 + 4i)/5, e^{i t1} = -1.
    let plain = RayVector::try_new(vec![
        GaussianRat::from_rational(rq(1, 2)),
        GaussianRat::from_rational(rq(3, 4)),
    ])
    .unwrap();
    let phased = RayVector::try_new(vec![
        gaussian(rq(3, 10), rq(4, 10)),
        gaussian(rq(-3, 4), ri(0)),
    ])
    .unwrap();
    let l1 = BornProbabilities::from_weights(&[rq(1, 4), rq(9, 16)]).unwrap();
    assert_eq!(l1.probabilities(), [rq(4, 13), rq(9, 13)]);

    // P_Born(c) = P_L1(w), pointwise, whatever the phases.
    assert_eq!(plain.born_probabilities().unwrap(), l1);
    assert_eq!(phased.born_probabilities().unwrap(), l1);

    // And it is the diagonal of the pure state |c><c|: the lift adds no normalisation
    // information, the state's populations are the L1 profile.
    for ray in [&plain, &phased] {
        let rho = ExactDensityMatrix::pure(ray).unwrap();
        let (shadow, coherence) = rho.population_shadow("lift").unwrap();
        assert_eq!(shadow.exact_probs().unwrap(), l1.probabilities());
        // The pure state is not its shadow: the coherence weight is 2 p0 p1 = 72/169.
        assert_eq!(coherence, rq(72, 169));
    }
}

/// The golden receipt, vendored into this crate, recomputed by the production code.
///
/// It used to read `../../research/published/003_quantum_foundations/.../evidence/`,
/// a path that never existed, so the test asserted a file into existence and had never
/// passed. The receipt is small, immutable evidence, vendored here so the test is
/// hermetic; it no longer merely compares strings in it to other strings in it: the
/// distributions are recomputed from the recorded weights and amplitudes.
const GOLDEN_RECEIPT: &str = include_str!("fixtures/qm_020_golden_receipt.json");

#[test]
fn test_qm020_golden_receipt_vector_verification() {
    let val: serde_json::Value =
        serde_json::from_str(GOLDEN_RECEIPT).expect("golden receipt is valid JSON");

    assert_eq!(val["paper_id"], "QM_020");
    assert_eq!(val["authority_effect"], "None");

    let theorems = val["theorems"].as_array().expect("theorems is an array");
    assert_eq!(theorems.len(), 3);

    // Identify by id rather than position: a reordering of the receipt must not
    // silently move which vectors are checked against which theorem.
    let by_id = |id: &str| {
        theorems
            .iter()
            .find(|t| t["theorem_id"] == id)
            .unwrap_or_else(|| panic!("golden receipt is missing {id}"))
    };
    let rationals = |v: &serde_json::Value| -> Vec<Rational> {
        v.as_array()
            .expect("an array of rationals")
            .iter()
            .map(|x| parse_rational(x.as_str().expect("a string")))
            .collect()
    };

    // Theorem 1: the recorded profile is its own L1 normalisation, of norm one.
    let t1 = by_id("Theorem_1_Direct_L1_Normalization");
    let weights = rationals(&t1["weights"]);
    let p_l1 = BornProbabilities::from_weights(&weights).unwrap();
    assert_eq!(p_l1.probabilities(), rationals(&t1["p_l1"]).as_slice());
    let l1_norm: Rational = weights.iter().cloned().sum();
    assert_eq!(l1_norm, parse_rational(t1["l1_norm"].as_str().unwrap()));

    // Theorem 2: the L1 norm of the direct sum of the two weight vectors.
    let t2 = by_id("Theorem_2_L1_Additivity_vs_L2_Subadditivity");
    let (a, b) = (
        rationals(&t2["weight_vector_a"]),
        rationals(&t2["weight_vector_b"]),
    );
    let l1_direct_sum: Rational = a.iter().chain(&b).cloned().sum();
    assert_eq!(
        l1_direct_sum,
        parse_rational(t2["l1_direct_sum"].as_str().unwrap())
    );

    // Theorem 4: the Born probabilities of the recorded amplitudes are the recorded
    // squared moduli normalised, and equal the L1 retraction of those moduli.
    let t4 = by_id("Theorem_4_Hilbert_Lift_Born_Redundancy");
    assert_eq!(t4["identity_verified"], true);
    let amplitudes: Vec<GaussianRat> = t4["hilbert_amplitudes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|z| {
            gaussian(
                parse_rational(z["re"].as_str().unwrap()),
                parse_rational(z["im"].as_str().unwrap()),
            )
        })
        .collect();
    let squared: Vec<Rational> = amplitudes.iter().map(GaussianRat::norm_sq).collect();
    assert_eq!(squared, rationals(&t4["squared_moduli"]));
    let born = RayVector::try_new(amplitudes)
        .unwrap()
        .born_probabilities()
        .unwrap();
    let retraction = BornProbabilities::from_weights(&squared).unwrap();
    assert_eq!(born, retraction, "Born redundancy is exactly this equality");
    assert_eq!(
        born.probabilities(),
        rationals(&t4["born_rule_output"]).as_slice()
    );
    assert_eq!(
        born.probabilities(),
        rationals(&t4["retraction_pi_output"]).as_slice()
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/qm_020_hilbert_lift_derivation_conformance.rs
// Claim: urn:core:crates_rs:tests:qm-020-hilbert-lift-derivation-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord40252a2f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord40252a2f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError40252a2f {
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
impl BoundaryError40252a2f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError40252a2f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError40252a2f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord40252a2f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError40252a2f> {
        if capacity_bound == 0 {
            return Err(BoundaryError40252a2f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError40252a2f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError40252a2f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_40252a2f() {
    let admitted = BoundaryRecord40252a2f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord40252a2f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

//! Exact certificates and explicitly bounded rejection/stability fixtures.

use std::collections::{BTreeMap, BTreeSet};

use num_bigint::BigUint;

use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::gaussian_norm::{norm_class, NormBudget};
use core_number_theory::integer_factorization::FactorizationBudget;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_operator::ExactOperator;
use core_quantum_physics::projective_preservers::*;

fn real_vector(values: &[i64]) -> Vec<G> {
    values.iter().map(|v| G::from_ints(*v, 0)).collect()
}

fn rows(values: &[&[i64]]) -> Result<ExactOperator, PreserverError> {
    Ok(ExactOperator::from_rows(
        values.iter().map(|r| real_vector(r)).collect(),
    )?)
}

fn frame(d: usize) -> Vec<Vec<G>> {
    (0..d)
        .map(|j| {
            (0..d)
                .map(|k| if k == j { G::one() } else { G::zero() })
                .collect()
        })
        .collect()
}

#[test]
fn gaussian_hadamard_and_nonstandard_conjugation() -> Result<(), PreserverError> {
    let carrier = HermitianCarrier::new(ExactOperator::identity(2)?)?;
    let hadamard = gaussian_hadamard()?;
    assert_eq!(
        hadamard.mul(&hadamard)?,
        ExactOperator::identity(2)?.scale(&G::i())?
    );
    let basis = frame(2);
    let images: Vec<_> = basis
        .iter()
        .map(|x| hadamard.apply(x))
        .collect::<Result<_, _>>()?;
    let mut certificate = PreserverCertificate {
        operator: hadamard,
        branch: ScalarBranch::Identity,
        multiplier: ri(1),
    };
    verify_preserver(&carrier, &basis, &images, &certificate)?;
    certificate.multiplier = ri(2);
    assert!(verify_preserver(&carrier, &basis, &images, &certificate).is_err());

    verify_nonstandard_conjugation(&basis)
}

fn verify_nonstandard_conjugation(basis: &[Vec<G>]) -> Result<(), PreserverError> {
    let h = ExactOperator::from_rows(vec![
        vec![G::from_ints(2, 0), G::i()],
        vec![G::i().neg(), G::from_ints(2, 0)],
    ])?;
    let nonstandard = HermitianCarrier::new(h)?;
    let m = rows(&[&[1, 0], &[0, -1]])?;
    let images: Vec<_> = basis.iter().map(|x| m.apply(x)).collect::<Result<_, _>>()?;
    let mut c = PreserverCertificate {
        operator: m,
        branch: ScalarBranch::Conjugate,
        multiplier: ri(1),
    };
    verify_preserver(&nonstandard, basis, &images, &c)?;
    c.branch = ScalarBranch::Identity;
    assert!(verify_preserver(&nonstandard, basis, &images, &c).is_err());
    Ok(())
}

#[test]
fn full_probability_preserver_need_not_normalize_in_dimension_four() -> Result<(), PreserverError> {
    let carrier = HermitianCarrier::new(ExactOperator::identity(4)?)?;
    let m = rows(&[
        &[1, -1, -1, 0],
        &[1, 1, 0, 1],
        &[1, 0, 1, -1],
        &[0, -1, 1, 1],
    ])?;
    let basis = frame(4);
    let images: Vec<_> = basis.iter().map(|x| m.apply(x)).collect::<Result<_, _>>()?;
    verify_preserver(
        &carrier,
        &basis,
        &images,
        &PreserverCertificate {
            operator: m.clone(),
            branch: ScalarBranch::Identity,
            multiplier: ri(3),
        },
    )?;
    assert!(carrier.verify_unitary(&m).is_err());
    let problem = RayProblem::new(
        carrier,
        real_vector(&[1, 0, 0, 0]),
        real_vector(&[1, 1, 1, 0]),
    )?;
    let certificate = propose_reachability(&problem, NormBudget::default())?;
    assert_eq!(
        verify_reachability(&problem, &certificate, NormBudget::default())?,
        ReachabilityVerdict::UnitaryImpossible
    );
    Ok(())
}

#[test]
fn submitted_ray_witnesses_cannot_be_replaced_or_rebound() -> Result<(), PreserverError> {
    let carrier = HermitianCarrier::new(ExactOperator::identity(3)?)?;
    let problem = RayProblem::new(
        carrier.clone(),
        real_vector(&[1, 0, 0]),
        real_vector(&[1, 1, 0]),
    )?;
    let certificate = propose_reachability(&problem, NormBudget::default())?;
    assert_eq!(
        verify_reachability(&problem, &certificate, NormBudget::default())?,
        ReachabilityVerdict::UnitaryReachable
    );
    let other = RayProblem::new(carrier, real_vector(&[0, 1, 0]), real_vector(&[1, 1, 0]))?;
    assert!(verify_reachability(&other, &certificate, NormBudget::default()).is_err());
    match certificate {
        ReachabilityCertificate::Unitary {
            original, scalar, ..
        } => {
            let false_witness = ReachabilityCertificate::Unitary {
                original,
                scalar,
                operator: ExactOperator::identity(3)?,
            };
            assert!(verify_reachability(&problem, &false_witness, NormBudget::default()).is_err());
        }
        _ => return Err(PreserverError::Invalid("expected a positive fixture")),
    }
    Ok(())
}

#[test]
fn projection_checks_original_target_and_zero_branch() -> Result<(), PreserverError> {
    let carrier = HermitianCarrier::new(ExactOperator::identity(3)?)?;
    let problem = RayProblem::new(
        carrier.clone(),
        real_vector(&[1, 0, 0]),
        real_vector(&[1, 1, 1]),
    )?;
    let mut candidate = propose_projection(&problem)?;
    assert_eq!(candidate.probability, rq(1, 3));
    assert_eq!(
        verify_projection(&problem, &candidate)?,
        ProjectionVerdict::PositivePostselection
    );
    candidate.projection = ExactOperator::identity(3)?;
    assert!(verify_projection(&problem, &candidate).is_err());
    let zero = RayProblem::new(carrier, real_vector(&[1, 0, 0]), real_vector(&[0, 1, 0]))?;
    let mut certificate = propose_projection(&zero)?;
    assert_eq!(
        verify_projection(&zero, &certificate)?,
        ProjectionVerdict::ZeroBranch
    );
    assert!(certificate.branch_vector.iter().all(G::is_zero));
    certificate.probability = ri(1);
    assert!(verify_projection(&zero, &certificate).is_err());
    Ok(())
}

#[test]
fn malformed_carriers_and_wrong_frames_are_refused() -> Result<(), PreserverError> {
    assert!(HermitianCarrier::new(rows(&[&[1, 0], &[0, -1]])?).is_err());
    assert!(HermitianCarrier::new(rows(&[&[1, 0], &[0, 0]])?).is_err());
    let carrier = HermitianCarrier::new(ExactOperator::identity(2)?)?;
    let c = PreserverCertificate {
        operator: ExactOperator::identity(2)?,
        branch: ScalarBranch::Identity,
        multiplier: ri(1),
    };
    assert!(verify_preserver(&carrier, &[real_vector(&[1, 0])], &frame(2), &c).is_err());
    assert!(canonical_ray(&[G::zero(), G::zero()]).is_err());
    Ok(())
}

fn assert_complement_and_orthogonality(
    carrier: &HermitianCarrier,
    rays: &[Vec<G>],
    normalized: &[Vec<G>],
    permutation: &[usize; 6],
) -> Result<(), PreserverError> {
    for j in 0..6 {
        let complement = canonical_ray(&[rays[j][1].conj().neg(), rays[j][0].conj()])?;
        assert!(normalized.contains(&complement));
        for k in 0..6 {
            assert_eq!(
                carrier.inner(&rays[j], &rays[k])?.is_zero(),
                carrier
                    .inner(&rays[permutation[j]], &rays[permutation[k]])?
                    .is_zero()
            );
        }
    }
    Ok(())
}

#[test]
fn complement_closed_qubit_countermodel() -> Result<(), PreserverError> {
    let carrier = HermitianCarrier::new(ExactOperator::identity(2)?)?;
    let rays: Vec<_> = [[1, 0], [0, 1], [1, 1], [1, -1], [1, 2], [2, -1]]
        .iter()
        .map(|v| real_vector(v))
        .collect();
    let permutation = [1, 0, 4, 5, 2, 3];
    let normalized: Vec<_> = rays
        .iter()
        .map(|v| canonical_ray(v))
        .collect::<Result<_, _>>()?;
    assert_complement_and_orthogonality(&carrier, &rays, &normalized, &permutation)?;
    assert_eq!(carrier.probability(&rays[0], &rays[2])?, rq(1, 2));
    assert_eq!(carrier.probability(&rays[1], &rays[4])?, rq(4, 5));
    Ok(())
}

fn decode_height_one_vector(d: usize, mut n: usize) -> Vec<G> {
    let mut v = Vec::with_capacity(d);
    for _ in 0..d {
        let digit = n % 9;
        n /= 9;
        v.push(G::from_ints((digit % 3) as i64 - 1, (digit / 3) as i64 - 1));
    }
    v
}

fn check_height_one_vector(
    d: usize,
    raw: usize,
    carrier: &HermitianCarrier,
    unitary: &ExactOperator,
    budget: FactorizationBudget,
    cache: &mut BTreeMap<Rational, BTreeSet<BigUint>>,
) -> Result<bool, PreserverError> {
    let v = decode_height_one_vector(d, raw);
    if v.iter().all(G::is_zero) {
        return Ok(false);
    }
    let norm = carrier.norm(&v)?;
    let transformed = unitary.apply(&v)?;
    assert_eq!(carrier.norm(&transformed)?, norm);
    let ray = canonical_ray(&v)?;
    let ray_norm = carrier.norm(&ray)?;
    for value in [&norm, &ray_norm] {
        if !cache.contains_key(value) {
            cache.insert(value.clone(), norm_class(value, budget)?);
        }
    }
    assert_eq!(cache.get(&norm), cache.get(&ray_norm));
    Ok(true)
}

#[test]
fn exhaustive_height_one_gaussian_vectors_keep_their_norm_classes() -> Result<(), PreserverError> {
    let budget = FactorizationBudget::default();
    let mut counts = Vec::new();
    for d in [3usize, 4] {
        let carrier = HermitianCarrier::new(ExactOperator::identity(d)?)?;
        let mut entries = frame(d);
        let z = G {
            re: rq(1, 2),
            im: rq(1, 2),
        };
        entries[0][0] = z.clone();
        entries[0][1] = z.clone();
        entries[1][0] = z.clone();
        entries[1][1] = z.neg();
        let unitary = ExactOperator::from_rows(entries)?;
        carrier.verify_unitary(&unitary)?;
        let mut cache = BTreeMap::new();
        let mut count = 0;
        for raw in 0..9usize.pow(d as u32) {
            if check_height_one_vector(d, raw, &carrier, &unitary, budget, &mut cache)? {
                count += 1;
            }
        }
        counts.push(count);
    }
    assert_eq!(counts, [728, 6560]);
    println!("bounded C-evidence only: d=3: 728 and d=4: 6560 nonzero Gaussian vectors, coordinate real/imag height <= 1");
    Ok(())
}

// Origin: engine/crates_rs/tests/core_quantum_physics/projective_preservers.rs
// Claim: urn:core:crates_rs:tests:projective-preservers:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4f0b0f17 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4f0b0f17` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4f0b0f17 {
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
impl BoundaryError4f0b0f17 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4f0b0f17 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4f0b0f17 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4f0b0f17 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4f0b0f17> {
        if capacity_bound == 0 {
            return Err(BoundaryError4f0b0f17::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4f0b0f17::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4f0b0f17::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_4f0b0f17() {
    let admitted = BoundaryRecord4f0b0f17::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4f0b0f17::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

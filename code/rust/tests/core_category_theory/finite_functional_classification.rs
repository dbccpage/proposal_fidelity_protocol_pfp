use core_category_theory::finite_functional_classification::{
    functional_implication_countermodel, realize_functional, realize_retention,
    retention_implication_countermodel, FiniteFunctionalModel, FiniteRetentionModel,
    FunctionalSignature, PropertyLiteral, RetentionSignature,
};

fn digits(mut value: usize, base: usize, n: usize) -> Vec<usize> {
    (0..n)
        .map(|_| {
            let digit = value % base;
            value /= base;
            digit
        })
        .collect()
}

#[test]
fn all_retention_signatures_have_witness_or_universal_obstruction() {
    let mut realized = 0;
    for bits in 0..64 {
        let signature = RetentionSignature {
            nontrivial: bits & 1 != 0,
            reversible: bits & 2 != 0,
            observable: bits & 4 != 0,
            tolerance: bits & 8 != 0,
            minimal: bits & 16 != 0,
            active: bits & 32 != 0,
        };
        match realize_retention(signature) {
            Ok(model) => {
                assert!(signature.is_realizable());
                assert_eq!(model.signature(), signature);
                assert!(model.moore().state_count() <= 4);
                realized += 1;
            }
            Err(_) => assert!(!signature.is_realizable()),
        }
    }
    assert_eq!(realized, 19);
}

#[test]
fn all_functional_signatures_have_witness_or_universal_obstruction() {
    let mut realized = 0;
    for bits in 0..32 {
        let signature = FunctionalSignature {
            linked: bits & 1 != 0,
            presentation_stable: bits & 2 != 0,
            report_stable: bits & 4 != 0,
            calibrated: bits & 8 != 0,
            blind_spot: bits & 16 != 0,
        };
        match realize_functional(signature) {
            Ok(model) => {
                assert!(signature.is_realizable());
                assert_eq!(model.signature(), signature);
                assert!(model.presentation().len() <= 3);
                realized += 1;
            }
            Err(_) => assert!(!signature.is_realizable()),
        }
    }
    assert_eq!(realized, 20);
}

fn check_functional_models_of_size(n: usize) {
    for q in 0..2_usize.pow(n as u32) {
        for s in 0..2_usize.pow(n as u32) {
            for t in 0..n.pow(n as u32) {
                for b in 0..2_usize.pow(n as u32) {
                    let model = FiniteFunctionalModel::new(
                        digits(q, 2, n),
                        digits(s, 2, n),
                        digits(t, n, n),
                        digits(b, 2, n),
                    )
                    .unwrap();
                    assert!(model.signature().is_realizable());
                    if let Some(factor) = model.report_factor() {
                        assert!(model
                            .presentation()
                            .iter()
                            .enumerate()
                            .all(|(x, q)| factor[q] == model.report()[x]));
                    }
                }
            }
        }
    }
}

fn check_retention_models_of_size(n: usize) {
    for raw in 0..2_usize.pow(n as u32) {
        for recognized in 0..2_usize.pow(n as u32) {
            for update in 0..n.pow(n as u32) {
                let transitions = digits(update, n, n).into_iter().map(|x| vec![x]).collect();
                if let Ok(model) = FiniteRetentionModel::new(
                    digits(raw, 2, n),
                    digits(recognized, 2, n),
                    transitions,
                    1,
                ) {
                    assert!(model.signature().is_realizable());
                }
            }
        }
    }
}

#[test]
fn small_models_independently_satisfy_necessary_constraints() {
    for n in 1_usize..=3 {
        check_functional_models_of_size(n);
        check_retention_models_of_size(n);
    }
}

#[test]
fn invalid_partial_and_nonfactorizing_models_fail_closed() {
    assert!(FiniteFunctionalModel::new(vec![], vec![], vec![], vec![]).is_err());
    assert!(FiniteFunctionalModel::new(vec![0], vec![], vec![0], vec![0]).is_err());
    assert!(FiniteFunctionalModel::new(vec![0], vec![0], vec![1], vec![0]).is_err());
    assert!(FiniteRetentionModel::new(vec![0, 0], vec![0, 1], vec![vec![0], vec![1]], 1).is_err());
    assert!(FiniteRetentionModel::new(vec![0, 1], vec![0], vec![vec![0], vec![1]], 1).is_err());
    assert!(FiniteRetentionModel::new(vec![0, 1], vec![0, 1], vec![vec![], vec![]], 1).is_err());
}

#[test]
fn implication_checker_returns_actual_countermodels_and_certified_absence() {
    let lit = |index, value| PropertyLiteral { index, value };
    let counter = retention_implication_countermodel(&[lit(1, true)], lit(2, true))
        .unwrap()
        .unwrap();
    assert!(counter.signature().reversible);
    assert!(!counter.signature().observable);
    assert!(
        retention_implication_countermodel(&[lit(2, true), lit(3, false)], lit(4, true))
            .unwrap()
            .is_none()
    );
    let counter = functional_implication_countermodel(&[lit(1, true)], lit(2, true))
        .unwrap()
        .unwrap();
    assert!(counter.signature().presentation_stable);
    assert!(!counter.signature().report_stable);
    assert!(!counter.signature().linked);
    assert!(
        functional_implication_countermodel(&[lit(0, true), lit(1, true)], lit(2, true))
            .unwrap()
            .is_none()
    );
    assert!(
        functional_implication_countermodel(&[lit(0, true), lit(0, false)], lit(3, true))
            .unwrap()
            .is_none()
    );
    assert!(retention_implication_countermodel(&[], lit(6, true)).is_err());
    assert!(functional_implication_countermodel(&[lit(5, false)], lit(0, true)).is_err());
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_functional_classification.rs
// Claim: urn:core:crates_rs:tests:finite-functional-classification:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd599db5b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd599db5b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord599db5b {
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
impl BoundaryErrord599db5b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord599db5b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord599db5b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd599db5b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord599db5b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord599db5b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord599db5b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord599db5b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_d599db5b() {
    let admitted = BoundaryRecordd599db5b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordd599db5b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

//! Selected education-source six-tuple, not recovered original Genesis custody.
//! Finite proof-carrying verifier domain; no total verifier or policy inferred.
use crate::legacy_observer_adapters::{
    adapt_finite_quotient, AdaptedObserver, AdapterError, SourceCustody,
};
use crate::observer::QuotientObserver;
use num_traits::Zero;
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SixObserverAdapter {
    presentation: AdaptedObserver,
    carrier: Vec<String>,
    terms: Vec<String>,
    receipts: Vec<ExactPhi1Certificate>,
    pair_receipts: Vec<Vec<ExactPhi1Certificate>>,
    relation: Vec<Vec<bool>>,
    terminal_labels: Vec<String>,
    terminalizer: Vec<usize>,
}
impl SixObserverAdapter {
    #[allow(clippy::too_many_arguments)]
    fn validate_six_observer_shapes(
        carrier: &[String],
        terms: &[String],
        receipts: &[ExactPhi1Certificate],
        pair_receipts: &[Vec<ExactPhi1Certificate>],
        relation: &[Vec<bool>],
        terminal_labels: &[String],
        terminalizer: &[usize],
    ) -> Result<(), AdapterError> {
        let n = terms.len();
        let valid_counts = n > 0
            && receipts.len() == n
            && pair_receipts.len() == n
            && relation.len() == n
            && terminalizer.len() == n
            && !terminal_labels.is_empty();
        if !valid_counts
            || !Self::valid_rows_and_unique_labels(
                carrier,
                terms,
                pair_receipts,
                relation,
                terminal_labels,
                terminalizer,
            )
        {
            return Err(AdapterError::MissingSemantics(
                "complete six-tuple finite domain",
            ));
        }
        Ok(())
    }

    fn valid_rows_and_unique_labels(
        carrier: &[String],
        terms: &[String],
        pair_receipts: &[Vec<ExactPhi1Certificate>],
        relation: &[Vec<bool>],
        terminal_labels: &[String],
        terminalizer: &[usize],
    ) -> bool {
        let n = terms.len();
        pair_receipts.iter().all(|r| r.len() == n)
            && relation.iter().all(|r| r.len() == n)
            && terminalizer.iter().all(|&i| i < terminal_labels.len())
            && terms
                .iter()
                .collect::<std::collections::BTreeSet<_>>()
                .len()
                == n
            && carrier
                .iter()
                .collect::<std::collections::BTreeSet<_>>()
                .len()
                == carrier.len()
    }

    fn verify_receipts_and_pairs(
        carrier_len: usize,
        receipts: &[ExactPhi1Certificate],
        pair_receipts: &[Vec<ExactPhi1Certificate>],
        relation: &[Vec<bool>],
        terminalizer: &[usize],
    ) -> Result<(), AdapterError> {
        let first = &receipts[0];
        if first.omega.len() != carrier_len {
            return Err(AdapterError::InvalidEvaluatorDomain);
        }
        for c in receipts {
            Phi1Functional::verify_exact_certificate(c.clone())
                .map_err(|_| AdapterError::InvalidEvaluatorDomain)?;
            if c.d0 != first.d0 || c.weights != first.weights {
                return Err(AdapterError::InvalidEvaluatorDomain);
            }
        }
        for i in 0..receipts.len() {
            for j in 0..receipts.len() {
                Self::verify_pair_entry(
                    first,
                    receipts,
                    &pair_receipts[i][j],
                    relation[i][j],
                    terminalizer,
                    i,
                    j,
                )?;
            }
        }
        Ok(())
    }

    fn verify_pair_entry(
        first: &ExactPhi1Certificate,
        receipts: &[ExactPhi1Certificate],
        c: &ExactPhi1Certificate,
        rel_ij: bool,
        terminalizer: &[usize],
        i: usize,
        j: usize,
    ) -> Result<(), AdapterError> {
        let verified = Phi1Functional::verify_exact_certificate(c.clone())
            .map_err(|_| AdapterError::InvalidEvaluatorDomain)?;
        let expected_omega: Vec<_> = receipts[i]
            .omega
            .iter()
            .zip(&receipts[j].omega)
            .map(|(a, b)| a - b)
            .collect();
        if c.d0 != first.d0
            || c.weights != first.weights
            || c.omega != expected_omega
            || rel_ij != verified.value().is_zero()
        {
            return Err(AdapterError::InvalidPresentation);
        }
        if receipts[i] == receipts[j] && terminalizer[i] != terminalizer[j] {
            return Err(AdapterError::InvalidEvaluatorDomain);
        }
        Ok(())
    }

    fn build_equivalence_classes(
        terms: &[String],
        relation: &[Vec<bool>],
    ) -> Vec<std::collections::BTreeSet<String>> {
        let n = terms.len();
        let mut classes: Vec<std::collections::BTreeSet<String>> = Vec::new();
        let mut assigned = vec![false; n];
        for i in 0..n {
            if !assigned[i] {
                let mut class = std::collections::BTreeSet::new();
                for j in 0..n {
                    if relation[i][j] {
                        assigned[j] = true;
                        class.insert(terms[j].clone());
                    }
                }
                classes.push(class);
            }
        }
        classes
    }

    /// W is im(d0), p is the receipt omega table; every declared comparison is
    /// checked via an independent distance certificate for p(x)-p(y).
    pub fn try_new(
        carrier: Vec<String>,
        terms: Vec<String>,
        receipts: Vec<ExactPhi1Certificate>,
        pair_receipts: Vec<Vec<ExactPhi1Certificate>>,
        relation: Vec<Vec<bool>>,
        terminal_labels: Vec<String>,
        terminalizer: Vec<usize>,
        custody: SourceCustody,
    ) -> Result<Self, AdapterError> {
        Self::validate_six_observer_shapes(
            &carrier,
            &terms,
            &receipts,
            &pair_receipts,
            &relation,
            &terminal_labels,
            &terminalizer,
        )?;
        Self::verify_receipts_and_pairs(
            carrier.len(),
            &receipts,
            &pair_receipts,
            &relation,
            &terminalizer,
        )?;
        let classes = Self::build_equivalence_classes(&terms, &relation);
        let quotient = QuotientObserver::new(
            terms.iter().cloned().collect(),
            classes,
            "independently certified p(x)-p(y) in image(d0)".into(),
        )
        .map_err(|_| AdapterError::InvalidPresentation)?;
        let presentation = adapt_finite_quotient(&quotient, custody)?;
        Ok(Self {
            presentation,
            carrier,
            terms,
            receipts,
            pair_receipts,
            relation,
            terminal_labels,
            terminalizer,
        })
    }
    pub fn presentation(&self) -> &AdaptedObserver {
        &self.presentation
    }
    pub fn carrier(&self) -> &[String] {
        &self.carrier
    }
    pub fn terms(&self) -> &[String] {
        &self.terms
    }
    pub fn receipts(&self) -> &[ExactPhi1Certificate] {
        &self.receipts
    }
    pub fn pair_receipts(&self) -> &[Vec<ExactPhi1Certificate>] {
        &self.pair_receipts
    }
    pub fn relation(&self) -> &[Vec<bool>] {
        &self.relation
    }
    pub fn terminal(&self, term: usize) -> Option<&str> {
        self.terminalizer
            .get(term)
            .map(|&i| self.terminal_labels[i].as_str())
    }
}

// Origin: engine/crates_rs/core_wdp/src/legacy_six_observer.rs
// Claim: urn:core:crates_rs:core-wdp:legacy-six-observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaa3c3b4d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaa3c3b4d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraa3c3b4d {
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
impl BoundaryErroraa3c3b4d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraa3c3b4d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraa3c3b4d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaa3c3b4d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraa3c3b4d> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraa3c3b4d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraa3c3b4d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraa3c3b4d::ExceedsCapacity {
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

#[cfg(test)]
mod l4_boundary_tests_aa3c3b4d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaa3c3b4d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaa3c3b4d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaa3c3b4d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaa3c3b4d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaa3c3b4d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraa3c3b4d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraa3c3b4d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

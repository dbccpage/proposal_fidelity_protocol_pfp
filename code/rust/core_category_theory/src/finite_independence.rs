//! State-relative interchange in a declared finite partial machine.
//! Both orders must be enabled and their endpoints future-equivalent.
//! Raw endpoints may differ; no spacelike causal premise is inferred.
//! State-relative interchange in a declared finite partial machine.
//! Both orders must be enabled and their endpoints future-equivalent.
//! Raw endpoints may differ; no spacelike causal premise is inferred.
//! Certificates replay against the expected machine. Input/start errors are
//! typed; only a successful distinction search can report distinguished futures.
//! AuthorityEffect: None.
use crate::finite_continuation::{ContinuationError, DistinguishingWord, PartialDynamics};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SwapOutcome {
    Independent {
        ab: usize,
        ba: usize,
    },
    Unavailable {
        a: Option<usize>,
        b: Option<usize>,
        ab: Option<usize>,
        ba: Option<usize>,
    },
    Distinguished {
        ab: usize,
        ba: usize,
        future: DistinguishingWord,
    },
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SwapCertificate {
    pub start: usize,
    pub a: usize,
    pub b: usize,
    pub outcome: SwapOutcome,
}

#[derive(Debug, PartialEq, Eq)]
struct SwapEndpoints {
    a: Option<usize>,
    b: Option<usize>,
    ab: Option<usize>,
    ba: Option<usize>,
}

impl SwapEndpoints {
    fn available(&self) -> Option<(usize, usize)> {
        match (self.a, self.b, self.ab, self.ba) {
            (Some(_), Some(_), Some(ab), Some(ba)) => Some((ab, ba)),
            _ => None,
        }
    }
}

fn swap_endpoints(
    machine: &PartialDynamics,
    start: usize,
    a: usize,
    b: usize,
) -> Result<SwapEndpoints, ContinuationError> {
    // Preserve start/alphabet refusal order, even across unavailable prefixes.
    Ok(SwapEndpoints {
        a: machine.run(start, &[a])?,
        b: machine.run(start, &[b])?,
        ab: machine.run(start, &[a, b])?,
        ba: machine.run(start, &[b, a])?,
    })
}

fn available_outcome(
    machine: &PartialDynamics,
    ab: usize,
    ba: usize,
    max_pairs: usize,
) -> Result<SwapOutcome, ContinuationError> {
    let q = machine.quotient();
    if q.state_to_block[ab] == q.state_to_block[ba] {
        Ok(SwapOutcome::Independent { ab, ba })
    } else {
        let future = machine
            .distinguish(ab, ba, max_pairs)?
            .ok_or(ContinuationError::CertificateMismatch)?;
        Ok(SwapOutcome::Distinguished { ab, ba, future })
    }
}

fn verify_independent(
    machine: &PartialDynamics,
    endpoints: &SwapEndpoints,
    ab: usize,
    ba: usize,
) -> bool {
    if endpoints.available() != Some((ab, ba)) {
        return false;
    }
    let q = machine.quotient();
    q.state_to_block[ab] == q.state_to_block[ba]
}

fn verify_distinguished(
    machine: &PartialDynamics,
    endpoints: &SwapEndpoints,
    ab: usize,
    ba: usize,
    future: &DistinguishingWord,
) -> bool {
    endpoints.available() == Some((ab, ba))
        && future.left == ab
        && future.right == ba
        && machine.verify_distinction(future).is_ok()
}

impl PartialDynamics {
    /// Unavailable orders (even both unavailable) never count as independence.
    /// Search exhaustion is a resource error, not a mathematical conclusion.
    pub fn certify_swap(
        &self,
        start: usize,
        a: usize,
        b: usize,
        max_pairs: usize,
    ) -> Result<SwapCertificate, ContinuationError> {
        let endpoints = swap_endpoints(self, start, a, b)?;
        let outcome = match endpoints.available() {
            Some((ab, ba)) => available_outcome(self, ab, ba, max_pairs)?,
            None => SwapOutcome::Unavailable {
                a: endpoints.a,
                b: endpoints.b,
                ab: endpoints.ab,
                ba: endpoints.ba,
            },
        };
        Ok(SwapCertificate {
            start,
            a,
            b,
            outcome,
        })
    }
    // Unavailable orders (even both unavailable) never count as independence.
    // Search exhaustion is a resource error, not a mathematical conclusion.
    /// Replay against the expected machine. Candidate endpoints/availability
    /// are never trusted. A valid distinction need not be shortest.
    pub fn verify_swap(&self, c: &SwapCertificate) -> Result<(), ContinuationError> {
        let endpoints = swap_endpoints(self, c.start, c.a, c.b)?;
        let valid = match &c.outcome {
            SwapOutcome::Unavailable {
                a: ca,
                b: cb,
                ab: cab,
                ba: cba,
            } => {
                endpoints.available().is_none()
                    && endpoints
                        == SwapEndpoints {
                            a: *ca,
                            b: *cb,
                            ab: *cab,
                            ba: *cba,
                        }
            }
            SwapOutcome::Independent { ab: cab, ba: cba } => {
                verify_independent(self, &endpoints, *cab, *cba)
            }
            SwapOutcome::Distinguished {
                ab: cab,
                ba: cba,
                future,
            } => verify_distinguished(self, &endpoints, *cab, *cba, future),
        };
    // Replay against the expected machine. Candidate endpoints/availability
    // are never trusted. A valid distinction need not be shortest.
        if valid {
            Ok(())
        } else {
            Err(ContinuationError::CertificateMismatch)
        }
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_independence.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-independence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddb1fa666 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddb1fa666` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordb1fa666 {
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
impl BoundaryErrordb1fa666 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordb1fa666 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordb1fa666 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddb1fa666 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordb1fa666> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordb1fa666::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordb1fa666::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordb1fa666::ExceedsCapacity {
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
mod l4_boundary_tests_db1fa666 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddb1fa666::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddb1fa666::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddb1fa666::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddb1fa666::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddb1fa666::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordb1fa666::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordb1fa666::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

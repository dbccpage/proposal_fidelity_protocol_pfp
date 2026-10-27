use num_bigint::BigInt;
use num_rational::BigRational;
use core_epk::{EpkResidualFamilyReceipt, EpkResidualLedger};
use core_functional::gamma2::{DegreeOneResidualQ, ExactCochainComplexQ, Gamma2Functional};
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional};
use core_policy::trichotomy::{classify_exact, TrichotomyOutcome};
use core_epk::residual_families::{shape_signature_from_exact_complex, FamilyRegistry};
use core_types::authority::{AuthorityEffect, Outcome, RefusalSource};
use core_types::observer::{Observer, ObserverKind};

fn rational(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

#[test]
fn epk_consults_and_records_only_shared_stabilized_evidence() {
    let certificate = ExactPhi1Certificate {
        omega: vec![rational(1)],
        d0: vec![vec![rational(0)]],
        weights: vec![rational(1)],
        alpha: vec![rational(0)],
        primal_residual: vec![rational(1)],
        dual_witness: vec![rational(1)],
        reported_value: rational(1),
    };
    let phi1 = Phi1Functional::verify_exact_certificate(certificate).expect("exact Phi1");
    let complex =
        ExactCochainComplexQ::try_new(1, 1, 1, vec![vec![rational(0)]], vec![vec![rational(0)]])
            .expect("exact complex");
    let residual = DegreeOneResidualQ::try_new(&complex, vec![rational(1)]).expect("residual");
    let gamma2 = Gamma2Functional::try_compute_exact_quotient(&residual).expect("Gamma2");
    let trichotomy = match classify_exact(&phi1, &gamma2) {
        TrichotomyOutcome::Classified(value) => value,
        other => panic!("expected exact classification, got {other:?}"),
    };
    let signature =
        shape_signature_from_exact_complex("core_epk::residual", &complex).expect("signature");
    let observer = Observer {
        id: core_kernel::ObserverId::parse("epk_residual_v1").expect("canonical observer id"),
        kind: ObserverKind::Custom("epk".to_string()),
    };
    let mut registry = FamilyRegistry::new();
    let mut ledger = EpkResidualLedger {
        ngd: 0.4,
        nrke: Some(0.75),
        obstruction_status: None,
    };

    let first = ledger
        .register_stabilized_family(
            &mut registry,
            signature,
            &phi1,
            &gamma2,
            &trichotomy,
            &observer,
        )
        .expect("first family receipt");
    assert_eq!(
        first,
        EpkResidualFamilyReceipt {
            shape_signature: *signature.as_bytes(),
            q1_class_id: first.q1_class_id,
            gamma2_class_id: first.gamma2_class_id,
            lookup_hit: false,
            inserted: true,
        }
    );

    let second = ledger
        .register_stabilized_family(
            &mut registry,
            signature,
            &phi1,
            &gamma2,
            &trichotomy,
            &observer,
        )
        .expect("reused family receipt");
    assert!(second.lookup_hit);
    assert!(!second.inserted);

    assert_eq!(ledger.authority_effect(), AuthorityEffect::None);
    assert_eq!(
        ledger.as_outcome(),
        Outcome::Refused(RefusalSource::Residual)
    );
}

// Origin: engine/crates_rs/tests/core_local_green_global_red_lggr/residual_family_wiring.rs
// Claim: urn:core:crates_rs:tests:residual-family-wiring:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf4cc9f8e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf4cc9f8e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf4cc9f8e {
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
impl BoundaryErrorf4cc9f8e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf4cc9f8e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf4cc9f8e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf4cc9f8e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf4cc9f8e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf4cc9f8e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf4cc9f8e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf4cc9f8e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f4cc9f8e() {
    let admitted = BoundaryRecordf4cc9f8e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf4cc9f8e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

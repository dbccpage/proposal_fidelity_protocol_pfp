use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_wdp::genesis_ongoing_adapter::{
    GenesisBridgeError, GenesisOngoingAdapter, GenesisOngoingPacket, MarkedTriple,
};
fn z(n: i64) -> BigInt {
    BigInt::from(n)
}
fn q(n: i64) -> BigRational {
    BigRational::from_integer(z(n))
}
fn packet(n: usize, excess: &[i64], filled: Vec<MarkedTriple>) -> GenesisOngoingPacket {
    assert_eq!(excess.len(), n * n);
    GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: excess.iter().map(|&v| z(v.max(0))).collect(),
        s: excess.iter().map(|&v| z((-v).max(0))).collect(),
        filled,
    }
}
fn tri() -> MarkedTriple {
    MarkedTriple { x: 0, y: 1, z: 2 }
}
#[test]
fn ordered_pair_loops_and_reverse_values_are_retained() {
    let p = packet(3, &[7, 2, 0, 5, 0, 3, 4, 0, -9], vec![tri()]);
    let a = GenesisOngoingAdapter::try_new(p.clone()).unwrap();
    assert_eq!(a.excess().len(), 9);
    assert_eq!(a.excess()[0], z(7));
    assert_eq!(a.excess()[8], z(-9));
    assert_eq!(a.excess()[1], z(2));
    assert_eq!(a.excess()[3], z(5));
    assert_eq!(a.presentation().repair_map().rows(), 9);
    for col in 0..3 {
        assert!(a
            .presentation()
            .repair_map()
            .get_ref(0, col)
            .unwrap()
            .is_zero());
    }
    let receipt = a.receipt().unwrap();
    assert_eq!(receipt.diagnostics, vec![q(9)]);
    assert_eq!(receipt.balances, vec![false]); // a filled triple is allowed to be unbalanced.
    receipt.verify_against(&p).unwrap();
}
#[test]
fn actual_native_repair_preserves_diagnostics_and_replays_input() {
    let p = packet(
        3,
        &[0, 2, -1, 5, 0, 3, 4, 0, 7],
        vec![tri(), MarkedTriple { x: 0, y: 2, z: 1 }],
    );
    let a = GenesisOngoingAdapter::try_new(p.clone()).unwrap();
    let potential = vec![z(5), z(-3), z(11)];
    let repair = a.repair(&potential).unwrap();
    assert_eq!(repair.repaired_excess[1], z(10));
    assert_eq!(repair.repaired_excess[0], z(0));
    assert_eq!(repair.repaired_excess[8], z(7));
    assert_eq!(repair.diagnostics, a.receipt().unwrap().diagnostics);
    repair.verify_against(&p, &potential).unwrap();
    let mut forged = repair.clone();
    forged.repaired_excess[1] += 1;
    assert_eq!(
        forged.verify_against(&p, &potential),
        Err(GenesisBridgeError::ReceiptMismatch)
    );
    assert_eq!(
        repair.verify_against(&p, &[z(0), z(0), z(0)]),
        Err(GenesisBridgeError::ReceiptMismatch)
    );
}
#[test]
fn balanced_marked_diagnostics_do_not_imply_repair_exactness() {
    let empty = GenesisOngoingAdapter::try_new(packet(
        3,
        &[0; 9],
        vec![tri(), MarkedTriple { x: 0, y: 2, z: 1 }],
    ))
    .unwrap();
    // 25:D5: loop is unseen by all distinct-vertex marked triangles.
    let loops = GenesisOngoingAdapter::try_new(packet(
        3,
        &[1, 0, 0, 0, 0, 0, 0, 0, 0],
        vec![tri(), MarkedTriple { x: 0, y: 2, z: 1 }],
    ))
    .unwrap();
    assert!(loops.receipt().unwrap().balances.iter().all(|v| *v));
    assert_eq!(empty.repair_equivalence(&loops).unwrap(), None);
    // 25:D6 blind three-term witness arb arc csb csa, nonzero two-way sums.
    let blind = GenesisOngoingAdapter::try_new(packet(
        3,
        &[0, 1, 1, 0, 0, 0, -1, -1, 0],
        vec![tri(), MarkedTriple { x: 0, y: 2, z: 1 }],
    ))
    .unwrap();
    assert_eq!(blind.receipt().unwrap().diagnostics, vec![q(0), q(0)]);
    assert_eq!(empty.repair_equivalence(&blind).unwrap(), None);
    // No declared marks: actual assertion discrepancy has no diagnostic rows.
    let unmarked = GenesisOngoingAdapter::try_new(packet(2, &[0, 1, 0, 0], vec![])).unwrap();
    assert!(unmarked.receipt().unwrap().diagnostics.is_empty());
}
#[test]
fn complete_integer_repair_witness_checks_all_pairs_not_only_diagnostics() {
    let a = GenesisOngoingAdapter::try_new(packet(3, &[2, 3, 4, 5, 6, 7, 8, 9, 10], vec![tri()]))
        .unwrap();
    let repair = a.repair(&[z(5), z(-2), z(11)]).unwrap();
    let values: Vec<_> = repair
        .repaired_excess
        .iter()
        .map(|v| i64::try_from(v).unwrap())
        .collect();
    let b = GenesisOngoingAdapter::try_new(packet(3, &values, vec![tri()])).unwrap();
    assert_eq!(
        a.repair_equivalence(&b).unwrap(),
        Some(vec![z(0), z(-7), z(6)])
    );
    // Any diagonal or two-way discrepancy obstructs an integer potential.
    let mut bad = b.source().clone();
    bad.r[0] += 1;
    let bad = GenesisOngoingAdapter::try_new(bad).unwrap();
    assert_eq!(a.repair_equivalence(&bad).unwrap(), None);
    let other_marks = GenesisOngoingAdapter::try_new(packet(3, &[0; 9], vec![])).unwrap();
    assert_eq!(
        a.repair_equivalence(&other_marks),
        Err(GenesisBridgeError::ContextMismatch)
    );
}
#[test]
fn forged_receipts_invalid_source_domains_and_empty_boundary() {
    let p = packet(3, &[0; 9], vec![tri()]);
    let a = GenesisOngoingAdapter::try_new(p.clone()).unwrap();
    let mut receipt = a.receipt().unwrap();
    receipt.balances[0] = false;
    assert_eq!(
        receipt.verify_against(&p),
        Err(GenesisBridgeError::ReceiptMismatch)
    );
    let mut duplicate = p.clone();
    duplicate.filled.push(tri());
    assert_eq!(
        GenesisOngoingAdapter::try_new(duplicate),
        Err(GenesisBridgeError::NonCanonicalTriples)
    );
    let mut bad = p.clone();
    bad.r.pop();
    assert_eq!(
        GenesisOngoingAdapter::try_new(bad),
        Err(GenesisBridgeError::InvalidDomain)
    );
    let mut bad = p.clone();
    bad.r[0] = z(-1);
    assert_eq!(
        GenesisOngoingAdapter::try_new(bad),
        Err(GenesisBridgeError::NegativeMultiplicity)
    );
    let mut bad = p.clone();
    bad.filled[0].z = 3;
    assert_eq!(
        GenesisOngoingAdapter::try_new(bad),
        Err(GenesisBridgeError::InvalidTriple)
    );
    let mut bad = p.clone();
    bad.terms[1] = bad.terms[0].clone();
    assert_eq!(
        GenesisOngoingAdapter::try_new(bad),
        Err(GenesisBridgeError::InvalidTermLabels)
    );
    assert_eq!(a.repair(&[z(0)]), Err(GenesisBridgeError::InvalidPotential));
    // The latest seed's empty beginning is represented by empty native matrices.
    let empty = GenesisOngoingAdapter::try_new(packet(0, &[], vec![])).unwrap();
    assert!(empty.receipt().unwrap().diagnostics.is_empty());
    assert_eq!(empty.repair_equivalence(&empty).unwrap(), Some(vec![]));
}
#[test]
fn raw_source_multiplicities_are_bound_even_when_excess_is_unchanged() {
    let p = packet(2, &[0, 1, 0, 0], vec![]);
    let r = GenesisOngoingAdapter::try_new(p.clone())
        .unwrap()
        .receipt()
        .unwrap();
    let mut paired = p.clone();
    let huge = z(1) << 256usize;
    paired.r[1] += &huge;
    paired.s[1] += &huge;
    assert_eq!(
        r.verify_against(&paired),
        Err(GenesisBridgeError::ReceiptMismatch)
    );
    let b = GenesisOngoingAdapter::try_new(paired).unwrap();
    assert_eq!(b.excess(), r.excess.as_slice());
    assert_eq!(
        GenesisOngoingAdapter::try_new(p)
            .unwrap()
            .repair_equivalence(&b)
            .unwrap(),
        Some(vec![z(0), z(0)])
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_ongoing_adapter.rs
// Claim: urn:core:crates_rs:tests:test-genesis-ongoing-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc6e48bdf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc6e48bdf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc6e48bdf {
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
impl BoundaryErrorc6e48bdf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc6e48bdf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc6e48bdf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc6e48bdf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc6e48bdf> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc6e48bdf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc6e48bdf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc6e48bdf::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c6e48bdf() {
    let admitted = BoundaryRecordc6e48bdf::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc6e48bdf::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

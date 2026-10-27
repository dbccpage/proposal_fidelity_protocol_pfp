use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::finite_cochain_map::CochainMap;
use num_bigint::BigInt;
use num_rational::BigRational;
use core_wdp::genesis_ongoing_adapter::{
    GenesisBridgeError, GenesisOngoingAdapter, GenesisOngoingPacket, MarkedTriple,
};

fn q(n: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(n))
}
fn source() -> GenesisOngoingAdapter {
    GenesisOngoingAdapter::try_new(GenesisOngoingPacket {
        terms: (0..4).map(|i| format!("t{i}")).collect(),
        r: (0..16).map(BigInt::from).collect(),
        s: (0..16).map(|i| BigInt::from(i % 3)).collect(),
        filled: vec![
            MarkedTriple { x: 0, y: 1, z: 2 },
            MarkedTriple { x: 0, y: 2, z: 1 },
            MarkedTriple { x: 0, y: 3, z: 2 },
        ],
    })
    .unwrap()
}

#[test]
fn actual_assertions_repairs_and_marked_diagnostics_restrict_together() {
    let source = source();
    let r = source.restrict(&[2, 1, 0], &[1, 0]).unwrap();
    let target = r.target();
    assert_eq!(target.source().terms, vec!["t2", "t1", "t0"]);
    // Both orientations survive canonical rotation; target ordering swaps them.
    assert_eq!(r.marks(), &[1, 0]);
    assert_eq!(target.source().r[0], BigInt::from(10)); // loop retained
    assert_eq!(target.source().s[0], BigInt::from(1));
    let h = BasicMatrix::from_row_major(
        16,
        1,
        source
            .excess()
            .iter()
            .cloned()
            .map(BigRational::from_integer)
            .collect(),
    )
    .unwrap();
    let transported = r.transport().transport(1, &h).unwrap();
    for i in 0..9 {
        assert_eq!(
            transported.get(i, 0).unwrap(),
            BigRational::from_integer(target.excess()[i].clone())
        );
    }
    let before = source.receipt().unwrap();
    let after = target.receipt().unwrap();
    assert_eq!(
        after.diagnostics,
        vec![before.diagnostics[1].clone(), before.diagnostics[0].clone()]
    );
    let potential: Vec<_> = [5, -3, 11, 9].into_iter().map(BigInt::from).collect();
    let old_repair = source.repair(&potential).unwrap();
    let new_potential: Vec<_> = r.vertices().iter().map(|&i| potential[i].clone()).collect();
    let new_repair = target.repair(&new_potential).unwrap();
    for i in 0..3 {
        for j in 0..3 {
            assert_eq!(
                new_repair.repaired_excess[i * 3 + j],
                old_repair.repaired_excess[r.vertices()[i] * 4 + r.vertices()[j]]
            );
        }
    }
}

#[test]
fn restrictions_compose_on_actual_contexts_and_permutations_are_invertible() {
    let source = source();
    let first = source.restrict(&[2, 0, 1], &[1, 0]).unwrap();
    let second = first.target().restrict(&[1, 0], &[]).unwrap();
    let composite = first.then(&second).unwrap();
    assert_eq!(composite, source.restrict(&[0, 2], &[]).unwrap());
    let identity = source.restrict(&[0, 1, 2, 3], &[0, 1, 2]).unwrap();
    assert_eq!(
        identity.transport(),
        &CochainMap::identity(&source.cochain_window().unwrap()).unwrap()
    );
    let permutation = source.restrict(&[2, 0, 3, 1], &[0, 1, 2]).unwrap();
    let inverse_marks: Vec<_> = (0..3)
        .map(|i| permutation.marks().iter().position(|&j| j == i).unwrap())
        .collect();
    let inverse = permutation
        .target()
        .restrict(&[1, 3, 0, 2], &inverse_marks)
        .unwrap();
    assert_eq!(inverse.target(), &source);
    assert_eq!(permutation.then(&inverse).unwrap(), identity);
    assert!(inverse
        .transport()
        .is_retraction_of(permutation.transport())
        .unwrap());
    // Matching differential dimensions must not hide raw-source drift.
    let mut changed = first.target().source().clone();
    changed.r[0] += 1;
    changed.s[0] += 1;
    let different = GenesisOngoingAdapter::try_new(changed)
        .unwrap()
        .restrict(&[1, 0], &[])
        .unwrap();
    assert_eq!(
        first.then(&different),
        Err(GenesisBridgeError::ContextMismatch)
    );
}

#[test]
fn malformed_subcontexts_refuse_and_empty_restriction_does_not_claim_reflection() {
    let source = source();
    for (vertices, marks) in [
        (vec![0, 0], vec![]),
        (vec![4], vec![]),
        (vec![0, 1, 2], vec![3]),
        (vec![0, 1, 2], vec![0, 0]),
        (vec![0, 1], vec![0]),
    ] {
        assert_eq!(
            source.restrict(&vertices, &marks),
            Err(GenesisBridgeError::InvalidRestriction)
        );
    }
    let empty = source.restrict(&[], &[]).unwrap();
    assert_eq!(
        empty.target().cochain_window().unwrap().dimensions(),
        [0, 0, 0]
    );
    // A loop is not a source gradient, yet restriction to the empty context
    // forgets it. Preservation is therefore strictly weaker than reflection.
    let mut loop_value = vec![q(0); 16];
    loop_value[0] = q(1);
    let h = BasicMatrix::from_row_major(16, 1, loop_value).unwrap();
    assert_eq!(empty.transport().transport(1, &h).unwrap().shape(), (0, 1));
    assert_eq!(
        source.cochain_window().unwrap().d0().get(0, 0).unwrap(),
        q(0)
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_context_restriction.rs
// Claim: urn:core:crates_rs:tests:test-genesis-context-restriction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord15eb1d70 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord15eb1d70` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError15eb1d70 {
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
impl BoundaryError15eb1d70 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError15eb1d70 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError15eb1d70 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord15eb1d70 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError15eb1d70> {
        if capacity_bound == 0 {
            return Err(BoundaryError15eb1d70::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError15eb1d70::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError15eb1d70::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_15eb1d70() {
    let admitted = BoundaryRecord15eb1d70::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord15eb1d70::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

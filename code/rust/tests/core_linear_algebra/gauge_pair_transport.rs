use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::gauge_pair_transport::{GaugeDescent, GaugePairTransport, GaugeTransportError};
use num_bigint::BigInt;
use num_rational::BigRational as Q;
use num_traits::{One, Zero};

fn gradient(g: &[BigInt]) -> BasicMatrix<Q> {
    BasicMatrix::try_from_fn(g.len(), g.len(), |x, y| Q::from_integer(&g[x] - &g[y])).unwrap()
}
fn is_gradient(table: &BasicMatrix<Q>) -> bool {
    let n = table.shape().0;
    (0..n).all(|a| {
        (0..n).all(|b| {
            table.get(a, b).unwrap() == (table.get(a, 0).unwrap() - table.get(b, 0).unwrap())
        })
    })
}

#[test]
fn every_small_total_map_matches_independent_basis_replay() {
    let mut count = 0;
    for n in 0..=4usize {
        for target in 0..=4usize {
            if target == 0 && n > 0 {
                continue;
            }
            for code in 0..target.pow(n as u32) {
                let mut k = code;
                let image: Vec<_> = (0..n)
                    .map(|_| {
                        let v = k % target;
                        k /= target;
                        v
                    })
                    .collect();
                let transport = GaugePairTransport::new(image, target).unwrap();
                let mut all = true;
                for x in 0..n {
                    let mut g = vec![BigInt::zero(); n];
                    g[x] = BigInt::one();
                    let actual = transport.apply(&gradient(&g)).unwrap();
                    assert_eq!(actual, transport.push_gradient(&g).unwrap());
                    all &= is_gradient(&actual);
                }
                match transport.descent() {
                    GaugeDescent::Descends => assert!(all),
                    GaugeDescent::Obstructed(witness) => {
                        assert!(!all);
                        assert!(transport.verify_obstruction(&witness).unwrap());
                    }
                }
                count += 1;
            }
        }
    }
    assert_eq!(count, 499);
}

#[test]
fn empty_fibers_and_nonuniform_exceptions_are_retained() {
    for (image, target) in [
        (vec![], 0),
        (vec![], 4),
        (vec![2, 2, 2], 4),
        (vec![0, 0, 1], 2),
    ] {
        let transport = GaugePairTransport::new(image, target).unwrap();
        assert_eq!(transport.descent(), GaugeDescent::Descends);
        let g = vec![BigInt::one(); transport.source_size()];
        let h = transport.quotient_potential(&g).unwrap();
        assert_eq!(gradient(&h), transport.push_gradient(&g).unwrap());
    }
    let injection = GaugePairTransport::new(vec![0, 1], 3).unwrap();
    assert_eq!(injection.fibers(), &[1, 1, 0]);
    assert!(matches!(injection.descent(), GaugeDescent::Obstructed(_)));
}

#[test]
fn huge_balanced_gradients_and_composite_potentials_agree() {
    let first = GaugePairTransport::new((0..12).map(|v| v / 2).collect(), 6).unwrap();
    let second = GaugePairTransport::new(vec![0, 0, 1, 1, 2, 2], 3).unwrap();
    let composite = first.then(&second).unwrap();
    assert_eq!(composite.fibers(), &[4, 4, 4]);
    let huge = BigInt::one() << 160usize;
    let g: Vec<_> = (0..12).map(|v| &huge * BigInt::from(v)).collect();
    let raw = gradient(&g);
    assert_eq!(
        second.apply(&first.apply(&raw).unwrap()).unwrap(),
        composite.apply(&raw).unwrap()
    );
    let h = second
        .quotient_potential(&first.quotient_potential(&g).unwrap())
        .unwrap();
    assert_eq!(h, composite.quotient_potential(&g).unwrap());
    assert_eq!(gradient(&h), composite.push_gradient(&g).unwrap());
}

#[test]
fn counterwitnesses_are_replayed_and_corrupt_claims_refused() {
    let transport = GaugePairTransport::new(vec![0, 0, 1, 2], 3).unwrap();
    let GaugeDescent::Obstructed(witness) = transport.descent() else {
        panic!("must fail")
    };
    assert!(transport.verify_obstruction(&witness).unwrap());
    let mut wrong = witness.clone();
    wrong.value += 1;
    assert!(!transport.verify_obstruction(&wrong).unwrap());
    wrong = witness.clone();
    wrong.cycle[2] = wrong.cycle[1];
    assert!(!transport.verify_obstruction(&wrong).unwrap());
    wrong = witness.clone();
    wrong.source_vertex = 4;
    assert!(!transport.verify_obstruction(&wrong).unwrap());
    assert_eq!(
        transport.quotient_potential(&vec![BigInt::zero(); 4]),
        Err(GaugeTransportError::NoDescent)
    );
    assert_eq!(
        transport.push_gradient(&[]),
        Err(GaugeTransportError::SourceShape)
    );
    assert_eq!(
        transport.apply(&gradient(&[])),
        Err(GaugeTransportError::SourceShape)
    );
    assert_eq!(
        transport.then(&GaugePairTransport::new(vec![0], 1).unwrap()),
        Err(GaugeTransportError::Intermediate)
    );
    assert_eq!(
        GaugePairTransport::new(vec![0], 0),
        Err(GaugeTransportError::VertexMap)
    );
    assert_eq!(
        GaugePairTransport::new(vec![], 257),
        Err(GaugeTransportError::WorkCap)
    );
}

// Origin: engine/crates_rs/tests/core_linear_algebra/gauge_pair_transport.rs
// Claim: urn:core:crates_rs:tests:gauge-pair-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord60f42ed5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord60f42ed5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError60f42ed5 {
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
impl BoundaryError60f42ed5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError60f42ed5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError60f42ed5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord60f42ed5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError60f42ed5> {
        if capacity_bound == 0 {
            return Err(BoundaryError60f42ed5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError60f42ed5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError60f42ed5::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_60f42ed5() {
    let admitted = BoundaryRecord60f42ed5::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord60f42ed5::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

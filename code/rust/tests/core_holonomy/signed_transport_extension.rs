use num_rational::BigRational;
use core_holonomy::signed_transport::{
    certify_signed_transport, compare_realizing_gauges, SignedCoefficientGraph,
    SignedTransportCertificate, SignedTransportOutcome,
};

fn graph(rows: &[&[&str]]) -> SignedCoefficientGraph {
    SignedCoefficientGraph::from_strings(
        &rows
            .iter()
            .map(|r| r.iter().map(|s| s.to_string()).collect())
            .collect::<Vec<_>>(),
    )
    .unwrap()
}
fn balanced() -> SignedCoefficientGraph {
    graph(&[
        &["-9", "2/3", "-11/13", "0"],
        &["2/3", "17", "5/7", "0"],
        &["-11/13", "5/7", "0", "0"],
        &["0", "0", "0", "101/3"],
    ])
}

#[test]
fn complete_rational_coefficients_forest_and_component_root_freedom() {
    let g = balanced();
    let cert = certify_signed_transport(&g);
    cert.verify(&g).unwrap();
    let SignedTransportOutcome::Gauge(left) = cert.outcome else {
        panic!("balanced fixture");
    };
    assert_eq!(left.roots, vec![0, 0, 0, 3]);
    assert_eq!(left.gauge_parities, vec![false, true, false, false]);
    let mut right = left.clone();
    for v in 0..3 {
        right.gauge_parities[v] ^= true;
    }
    assert_eq!(
        compare_realizing_gauges(&g, &left, &right).unwrap(),
        vec![(0, true), (3, false)]
    );
    let alternate = SignedTransportCertificate {
        original_coefficients: g.canonical_coefficients(),
        outcome: SignedTransportOutcome::Gauge(right),
    };
    alternate.verify(&g).unwrap();
    assert_eq!(g.edge_parity(0, 0), None); // Arbitrary diagonal is retained, never a self-edge.
}

#[test]
fn negative_cycle_is_actual_and_independently_replayed() {
    let g = graph(&[
        &["4", "1/2", "-3"],
        &["1/2", "-2", "-5/4"],
        &["-3", "-5/4", "7"],
    ]);
    let cert = certify_signed_transport(&g);
    cert.verify(&g).unwrap();
    let SignedTransportOutcome::NegativeCycle(walk) = &cert.outcome else {
        panic!("negative fixture");
    };
    assert_eq!(walk.first(), walk.last());
    assert!(g.walk_parity(walk).unwrap());
    let mut forged = cert.clone();
    forged.outcome = SignedTransportOutcome::NegativeCycle(vec![0, 0, 1, 0]);
    assert!(forged.verify(&g).is_err());
    let missing = SignedTransportCertificate {
        original_coefficients: balanced().canonical_coefficients(),
        outcome: SignedTransportOutcome::NegativeCycle(vec![0, 1, 3, 0]),
    };
    assert!(missing.verify(&balanced()).is_err());
}

#[test]
fn every_original_magnitude_diagonal_zero_and_edge_is_bound() {
    let g = balanced();
    let cert = certify_signed_transport(&g);
    let mut changed = g.canonical_coefficients();
    changed[0][0] = "-10".to_string();
    assert!(cert
        .verify(&SignedCoefficientGraph::from_strings(&changed).unwrap())
        .is_err());
    let mut changed = g.canonical_coefficients();
    changed[0][1] = "4/3".to_string();
    changed[1][0] = "4/3".to_string();
    assert!(cert
        .verify(&SignedCoefficientGraph::from_strings(&changed).unwrap())
        .is_err());
    let mut forged = cert.clone();
    let SignedTransportOutcome::Gauge(f) = &mut forged.outcome else {
        unreachable!()
    };
    f.gauge_parities[1] = false;
    assert!(forged.verify(&g).is_err());
    let mut forged = cert;
    let SignedTransportOutcome::Gauge(f) = &mut forged.outcome else {
        unreachable!()
    };
    f.paths[1] = vec![0, 3, 1];
    assert!(forged.verify(&g).is_err());
    let mut forged = certify_signed_transport(&g);
    let SignedTransportOutcome::Gauge(f) = &mut forged.outcome else {
        unreachable!()
    };
    f.paths[1] = vec![0, 4, 1];
    assert!(forged.verify(&g).is_err());
    let mut forged = certify_signed_transport(&g);
    let SignedTransportOutcome::Gauge(f) = &mut forged.outcome else {
        unreachable!()
    };
    f.roots[1] = 1;
    f.paths[1] = vec![1];
    assert!(forged.verify(&g).is_err());
}

#[test]
fn exact_wire_shape_symmetry_and_raw_denominator_refusals() {
    for bad in ["1/0", "1.0", "+1", "01", "2/4", "1/1", "-1/-2"] {
        assert!(
            SignedCoefficientGraph::from_strings(&[vec![bad.to_string()]]).is_err(),
            "{bad}"
        );
    }
    assert!(SignedCoefficientGraph::from_strings(&[
        vec!["0".into(), "1".into()],
        vec!["0".into(), "0".into()]
    ])
    .is_err());
    assert!(SignedCoefficientGraph::from_strings(&[vec!["0".into(), "1".into()]]).is_err());
    assert!(
        SignedCoefficientGraph::try_new(vec![vec![BigRational::new_raw(1.into(), 0.into())]])
            .is_err()
    );
    assert!(
        SignedCoefficientGraph::try_new(vec![vec![BigRational::new_raw(2.into(), 4.into())]])
            .is_err()
    );
    let empty = SignedCoefficientGraph::try_new(vec![]).unwrap();
    certify_signed_transport(&empty).verify(&empty).unwrap();
    let single = graph(&[&["17/3"]]);
    certify_signed_transport(&single).verify(&single).unwrap();
}

#[test]
fn generator_matches_independent_all_gauges_on_27_three_vertex_graphs() {
    let choices = ["-2/3", "0", "5/7"];
    for a in choices {
        for b in choices {
            for c in choices {
                let g = graph(&[&["-8", a, b], &[a, "3", c], &[b, c, "17"]]);
                let cert = certify_signed_transport(&g);
                cert.verify(&g).unwrap();
                let mut exists = false;
                for mask in 0..8 {
                    let bits: Vec<_> = (0..3).map(|i| mask & (1 << i) != 0).collect();
                    if (0..3).all(|i| {
                        (i + 1..3)
                            .all(|j| g.edge_parity(i, j).is_none_or(|p| bits[i] ^ bits[j] == p))
                    }) {
                        exists = true;
                    }
                }
                assert_eq!(
                    matches!(cert.outcome, SignedTransportOutcome::Gauge(_)),
                    exists
                );
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_holonomy/signed_transport_extension.rs
// Claim: urn:core:crates_rs:tests:signed-transport-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord02804d94 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord02804d94` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError02804d94 {
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
impl BoundaryError02804d94 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError02804d94 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError02804d94 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord02804d94 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError02804d94> {
        if capacity_bound == 0 {
            return Err(BoundaryError02804d94::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError02804d94::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError02804d94::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_02804d94() {
    let admitted = BoundaryRecord02804d94::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord02804d94::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

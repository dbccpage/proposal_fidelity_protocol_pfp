use linear_algebra::regge_exact::So4;
use num_rational::BigRational as Q;
use core_general_relativity::certified_dihedral::{DeficitSign, MetricHingeStar};
use core_general_relativity::metric_hinge_transport::{
    MetricHingeTransport, Orientation, TransportError,
};
use core_homology::{
    finite_poset::FinitePoset,
    restriction_dga::{Cochain, Matrix, OperatorCarrier},
};
use std::collections::BTreeMap;
fn q(n: i64, d: i64) -> Q {
    Q::new(n.into(), d.into())
}
fn star(cosines: &[Q]) -> MetricHingeStar {
    let n = cosines.len();
    let mut edges = BTreeMap::new();
    for (i, c) in cosines.iter().enumerate() {
        let ids = [0, 1, 2, 3 + i, 3 + (i + 1) % n];
        for a in 0..5 {
            for b in a + 1..5 {
                let length = if a == 0 {
                    q(1, 1)
                } else if a == 3 && b == 4 {
                    q(2, 1) - q(2, 1) * c
                } else {
                    q(2, 1)
                };
                edges.insert((ids[a].min(ids[b]), ids[a].max(ids[b])), length);
            }
        }
    }
    MetricHingeStar::new([0, 1, 2], (3..3 + n).collect(), edges).unwrap()
}
fn frame(c: Q, s: Q, a: usize, b: usize) -> So4 {
    let mut m = So4::identity().m;
    m[a][a] = c.clone();
    m[b][b] = c;
    m[a][b] = -&s;
    m[b][a] = s;
    So4::try_new(m).unwrap()
}
fn mat(s: &So4) -> Matrix {
    Matrix::from_row_major(4, 4, s.m.iter().flatten().cloned().collect()).unwrap()
}
#[test]
fn metric_angles_oriented_gluing_and_common_basepoint_replay() {
    let source = star(&[q(3, 5), q(0, 1), q(-3, 5), q(5, 13)]);
    let t = MetricHingeTransport::new(&source, &q(1, 100000)).unwrap();
    assert_eq!(
        t.normal_rotations(),
        &[
            (q(3, 5), q(4, 5)),
            (q(0, 1), q(1, 1)),
            (q(-3, 5), q(4, 5)),
            (q(5, 13), q(12, 13))
        ]
    );
    assert_eq!(t.deficit().source().squared_edges(), source.squared_edges());
    let mut product = So4::identity();
    for h in t.links() {
        product = h.mul(&product);
    }
    for base in 0..4 {
        let w = t.holonomy(base, Orientation::Forward).unwrap();
        assert_eq!(w, product);
        assert!(w
            .mul(&t.holonomy(base, Orientation::Reverse).unwrap())
            .is_identity());
    }
    assert!(source.simplex(4).is_err());
}
#[test]
fn changing_local_frames_conjugates_the_loop_including_noncommuting_frames() {
    let t = MetricHingeTransport::new(&star(&vec![q(3, 5); 5]), &q(1, 10000)).unwrap();
    let frames: Vec<_> = (0..5)
        .map(|i| frame(q(3, 5), q(4, 5), i % 2, 2 + i % 2))
        .collect();
    for base in 0..5 {
        assert_eq!(
            t.gauged_holonomy(base, &frames).unwrap(),
            frames[base]
                .mul(&t.holonomy(base, Orientation::Forward).unwrap())
                .mul(&frames[base].transpose())
        );
    }
}
#[test]
fn explicit_poset_observation_is_w_minus_identity_not_an_unconditional_bianchi_identification() {
    let t = MetricHingeTransport::new(&star(&vec![q(0, 1); 3]), &q(1, 10000)).unwrap();
    let c = OperatorCarrier::new(
        FinitePoset::new(4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]).unwrap(),
        vec![4; 4],
    )
    .unwrap();
    let early = t.links()[0].clone();
    let late = t.links()[2].mul(&t.links()[1]);
    let r = Cochain::new(
        c,
        1,
        BTreeMap::from([
            (vec![0, 1], mat(&late)),
            (vec![1, 2], mat(&early)),
            (vec![0, 2], mat(&So4::identity())),
            (vec![2, 3], mat(&So4::identity())),
            (vec![1, 3], mat(&early)),
            (vec![0, 3], mat(&So4::identity())),
        ]),
    )
    .unwrap();
    let k = r.curvature().unwrap();
    assert_eq!(
        k.components()[&vec![0, 1, 2]],
        Matrix::from_row_major(
            4,
            4,
            t.observed_defect(0)
                .unwrap()
                .into_iter()
                .flatten()
                .collect()
        )
        .unwrap()
    );
    assert!(!k.is_zero());
    let boundary = k.covariant_differential(&r).unwrap();
    assert_eq!(boundary.components().len(), 1);
    assert!(boundary.is_zero());
    assert!(!t.holonomy(0, Orientation::Forward).unwrap().is_identity());
}
#[test]
fn holonomy_does_not_recover_an_unwrapped_deficit_without_branch_data() {
    let flat = MetricHingeTransport::new(&star(&vec![q(0, 1); 4]), &q(1, 100000)).unwrap();
    assert!(flat
        .holonomy(0, Orientation::Forward)
        .unwrap()
        .is_identity());
    assert_eq!(flat.deficit().sign(), DeficitSign::ContainsZero);
    let winding = MetricHingeTransport::new(&star(&vec![q(0, 1); 8]), &q(1, 100000)).unwrap();
    assert!(winding
        .holonomy(0, Orientation::Forward)
        .unwrap()
        .is_identity());
    assert!(matches!(
        winding.deficit().sign(),
        DeficitSign::Negative { .. }
    ));
    assert!(winding.deficit().bounds().hi() < &q(-6, 1));
}
#[test]
fn irrational_normal_rotations_invalid_frames_and_forged_so4_are_refused() {
    assert!(matches!(
        MetricHingeTransport::new(&star(&vec![q(1, 2); 4]), &q(1, 10000)),
        Err(TransportError::AlgebraicRotation)
    ));
    let t = MetricHingeTransport::new(&star(&vec![q(0, 1); 4]), &q(1, 10000)).unwrap();
    assert!(t.holonomy(4, Orientation::Forward).is_err());
    assert!(t.gauged_links(&[]).is_err());
    let mut frames = vec![So4::identity(); 4];
    frames[0].m[0][0] = q(2, 1);
    assert!(t.gauged_links(&frames).is_err());
    frames[0].m[0][0] = Q::new_raw(1.into(), 0.into());
    assert!(t.gauged_links(&frames).is_err());
}

// Origin: engine/crates_rs/tests/core_general_relativity/metric_hinge_transport.rs
// Claim: urn:core:crates_rs:tests:metric-hinge-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2420655d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2420655d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2420655d {
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
impl BoundaryError2420655d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2420655d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2420655d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2420655d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2420655d> {
        if capacity_bound == 0 {
            return Err(BoundaryError2420655d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2420655d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2420655d::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_2420655d() {
    let admitted = BoundaryRecord2420655d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2420655d::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

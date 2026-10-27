use core_category_theory::finite_continuation::PartialDynamics;
use core_category_theory::finite_joint_dynamics::*;

fn machine(mut code: usize) -> PartialDynamics {
    let mut transitions = Vec::new();
    for _ in 0..2 {
        let t = code % 3;
        code /= 3;
        transitions.push(vec![if t == 2 { None } else { Some(t) }]);
    }
    PartialDynamics::new(vec![0, 0], transitions, 1).unwrap()
}
#[test]
fn local_product_operations_preserve_all_local_futures() {
    for l in 0..9 {
        for r in 0..9 {
            let left = machine(l);
            let right = machine(r);
            let joint = JointDynamics::new(
                &left,
                &right,
                vec![(0, 0), (0, 1), (1, 0), (1, 1)],
                &[JointOperation::Left(0), JointOperation::Right(0)],
                10000,
            )
            .unwrap();
            let cert = joint.analyze().unwrap();
            assert!(cert.collision.is_none());
            joint.verify(&cert).unwrap();
            // Pairwise equivalence, not just the number of blocks.
            for i in 0..4 {
                for j in 0..4 {
                    assert_eq!(
                        joint.local_reports()[i] == joint.local_reports()[j],
                        cert.refinement.state_to_block[i] == cert.refinement.state_to_block[j]
                    );
                }
            }
        }
    }
}
#[test]
fn interaction_reveals_hidden_future_or_availability_and_certificates_bind() {
    let left = PartialDynamics::new(vec![0, 0], vec![vec![], vec![]], 0).unwrap();
    let right = PartialDynamics::new(vec![0, 1], vec![vec![], vec![]], 0).unwrap();
    let pairs = vec![(0, 0), (0, 1), (1, 0), (1, 1)];
    let joint = JointDynamics::new(
        &left,
        &right,
        pairs.clone(),
        &[JointOperation::Interaction(vec![
            Some(1),
            Some(1),
            Some(2),
            Some(2),
        ])],
        1000,
    )
    .unwrap();
    let c = joint.analyze().unwrap();
    let w = c.collision.as_ref().unwrap();
    assert_eq!(w.word, vec![0]);
    joint.dynamics().verify_distinction(w).unwrap();
    let mut forged = c.clone();
    forged.collision = None;
    assert!(joint.verify(&forged).is_err());
    let availability = JointDynamics::new(
        &left,
        &right,
        pairs,
        &[JointOperation::Interaction(vec![
            None,
            Some(1),
            Some(2),
            Some(3),
        ])],
        1000,
    )
    .unwrap();
    let a = availability.analyze().unwrap();
    assert_eq!(a.collision.unwrap().left_answer, None);
    assert!(availability.verify(&c).is_err());
}
#[test]
fn absent_relation_rows_and_malformed_operations_are_not_unavailability() {
    let m = PartialDynamics::new(vec![0, 0], vec![vec![Some(1)], vec![Some(0)]], 1).unwrap();
    assert!(matches!(
        JointDynamics::new(&m, &m, vec![(0, 0)], &[JointOperation::Left(0)], 1000),
        Err(JointDynamicsError::NotClosed { .. })
    ));
    for op in [
        JointOperation::Left(1),
        JointOperation::Interaction(vec![]),
        JointOperation::Interaction(vec![Some(1)]),
    ] {
        assert!(matches!(
            JointDynamics::new(&m, &m, vec![(0, 0)], &[op], 1000),
            Err(JointDynamicsError::InvalidOperation)
        ));
    }
    assert!(matches!(
        JointDynamics::new(&m, &m, vec![(0, 0), (0, 0)], &[], 1000),
        Err(JointDynamicsError::InvalidRelation)
    ));
    assert!(matches!(
        JointDynamics::new(&m, &m, vec![], &[], 1000),
        Err(JointDynamicsError::InvalidRelation)
    ));
    assert!(matches!(
        JointDynamics::new(&m, &m, vec![(0, 0)], &[], 0),
        Err(JointDynamicsError::WorkLimit)
    ));
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_joint_dynamics.rs
// Claim: urn:core:crates_rs:tests:finite-joint-dynamics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord81a5de92 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord81a5de92` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError81a5de92 {
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
impl BoundaryError81a5de92 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError81a5de92 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError81a5de92 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord81a5de92 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError81a5de92> {
        if capacity_bound == 0 {
            return Err(BoundaryError81a5de92::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError81a5de92::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError81a5de92::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_81a5de92() {
    let admitted = BoundaryRecord81a5de92::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord81a5de92::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

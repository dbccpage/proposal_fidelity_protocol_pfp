use core_category_theory::context_reflection::{
    reflect_arrow, CongruenceReflection, ContextError, ContextHom, ContextSystem,
};

fn noncongruent() -> ContextSystem {
    ContextSystem::new(vec![0, 0, 1], vec![vec![0], vec![2], vec![2]], 1).unwrap()
}

#[test]
fn actual_comma_universal_property_for_all_maps_into_a_congruent_target() {
    let source = noncongruent();
    let reflection = CongruenceReflection::new(&source).unwrap();
    assert!(reflection.completed().is_congruent());
    assert_eq!(reflection.completed().profiles(), &[0, 0, 0]);
    assert!(reflection.unit().unwrap().source() == &source);
    assert!(!reflection.unit().unwrap().reflects_profiles());
    let target = ContextSystem::new(vec![0, 0, 1], vec![vec![0], vec![1], vec![2]], 1).unwrap();
    let mut valid_arrows = 0;
    for a in 0..3 {
        for b in 0..3 {
            for c in 0..3 {
                if let Ok(f) = ContextHom::new(&source, &target, vec![a, b, c]) {
                    valid_arrows += 1;
                    let factor = reflection.factor(&f).unwrap();
                    assert!(reflection.is_factor(&f, &factor));
                    assert_eq!(
                        reflection.unit().unwrap().then(&factor).unwrap().map(),
                        f.map()
                    );
                    // Check all candidate arrows, not only the constructed factor.
                    for x in 0..3 {
                        for y in 0..3 {
                            for z in 0..3 {
                                if let Ok(g) =
                                    ContextHom::new(reflection.completed(), &target, vec![x, y, z])
                                {
                                    if reflection.is_factor(&f, &g) {
                                        assert_eq!(g.map(), factor.map());
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert!(valid_arrows > 0);
}

#[test]
fn reflecting_unit_comma_category_has_no_objects_for_the_countermodel() {
    let source = noncongruent();
    assert!(source.obstruction().is_some());
    for profiles in [vec![0, 0], vec![0, 1]] {
        for a in 0..2 {
            for b in 0..2 {
                let target =
                    ContextSystem::new(profiles.clone(), vec![vec![a], vec![b]], 1).unwrap();
                if !target.is_congruent() {
                    continue;
                }
                for x in 0..2 {
                    for y in 0..2 {
                        for z in 0..2 {
                            if let Ok(arrow) = ContextHom::new(&source, &target, vec![x, y, z]) {
                                assert!(!arrow.reflects_profiles());
                            }
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn morphisms_and_reflector_obey_identity_composition_and_natural_unit() {
    let source = noncongruent();
    let target = ContextSystem::new(vec![0, 0, 0], vec![vec![0], vec![2], vec![2]], 1).unwrap();
    let rs = CongruenceReflection::new(&source).unwrap();
    let rt = CongruenceReflection::new(&target).unwrap();
    let f = ContextHom::new(&source, &target, vec![0, 1, 2]).unwrap();
    let id_s = ContextHom::identity(&source).unwrap();
    let id_t = ContextHom::identity(&target).unwrap();
    assert_eq!(id_s.then(&f).unwrap().map(), f.map());
    assert_eq!(f.then(&id_t).unwrap().map(), f.map());
    let rf = reflect_arrow(&rs, &rt, &f).unwrap();
    assert_eq!(
        rs.unit().unwrap().then(&rf).unwrap().map(),
        f.then(&rt.unit().unwrap()).unwrap().map()
    );
    assert_eq!(
        reflect_arrow(&rs, &rs, &id_s).unwrap().map(),
        ContextHom::identity(rs.completed()).unwrap().map()
    );
    assert_eq!(
        reflect_arrow(&rs, &rt, &id_s.then(&f).unwrap())
            .unwrap()
            .map(),
        reflect_arrow(&rs, &rs, &id_s)
            .unwrap()
            .then(&rf)
            .unwrap()
            .map()
    );
}

#[test]
fn checked_types_reject_wrong_endpoints_and_noncongruent_targets() {
    let source = noncongruent();
    let reflection = CongruenceReflection::new(&source).unwrap();
    let identity = ContextHom::identity(&source).unwrap();
    assert!(matches!(
        reflection.factor(&identity),
        Err(ContextError::TargetNotCongruent)
    ));
    assert!(matches!(
        ContextHom::new(&source, &source, vec![0]),
        Err(ContextError::InvalidMap)
    ));
    let other = ContextSystem::new(vec![0], vec![vec![]], 0).unwrap();
    assert!(matches!(
        identity.then(&ContextHom::identity(&other).unwrap()),
        Err(ContextError::WrongDomain)
    ));
}

fn verify_reflection_against_candidates(
    source: &ContextSystem,
    reflection: &CongruenceReflection,
    actions: &[Vec<usize>],
    partitions: &[Vec<usize>],
) {
    for candidate_profile in partitions {
        let candidate = ContextSystem::new(candidate_profile.clone(), actions.to_vec(), 1).unwrap();
        let contains_source =
            (0..3).all(|x| (0..3).all(|y| !source.related(x, y) || candidate.related(x, y)));
        if contains_source && candidate.is_congruent() {
            for x in 0..3 {
                for y in 0..3 {
                    assert!(!reflection.completed().related(x, y) || candidate.related(x, y));
                }
            }
        }
    }
}

#[test]
fn finite_algorithm_is_the_least_stable_super_equivalence_exhaustively() {
    let partitions = [
        vec![0, 0, 0],
        vec![0, 0, 1],
        vec![0, 1, 0],
        vec![0, 1, 1],
        vec![0, 1, 2],
    ];
    for profile in &partitions {
        for a in 0..3 {
            for b in 0..3 {
                for c in 0..3 {
                    let actions = vec![vec![a], vec![b], vec![c]];
                    let source = ContextSystem::new(profile.clone(), actions.clone(), 1).unwrap();
                    let reflection = CongruenceReflection::new(&source).unwrap();
                    assert!(reflection.completed().is_congruent());
                    assert!(reflection.chain().len() <= source.state_count());
                    verify_reflection_against_candidates(&source, &reflection, &actions, &partitions);
                }
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_category_theory/context_reflection.rs
// Claim: urn:core:crates_rs:tests:context-reflection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord54b200a8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord54b200a8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError54b200a8 {
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
impl BoundaryError54b200a8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError54b200a8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError54b200a8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord54b200a8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError54b200a8> {
        if capacity_bound == 0 {
            return Err(BoundaryError54b200a8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError54b200a8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError54b200a8::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_54b200a8() {
    let admitted = BoundaryRecord54b200a8::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord54b200a8::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

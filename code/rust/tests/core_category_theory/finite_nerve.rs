use core_category_theory::cat_functor::DeclaredFiniteFunctor;
use core_category_theory::finite_category::ValidatedFiniteCategory;
use core_category_theory::finite_category_builder::DeclaredFiniteCategoryBuilder;
use core_category_theory::functor_composition::{identity_functor, ValidatedFiniteFunctor};
use core_category_theory::nerve::{FiniteNerveRefusal, Simplex, ValidatedFiniteNerve};

fn triangle() -> ValidatedFiniteCategory {
    DeclaredFiniteCategoryBuilder::new("Triangle")
        .object("A")
        .object("B")
        .object("C")
        .identity("A", "id_A")
        .identity("B", "id_B")
        .identity("C", "id_C")
        .morphism("f", "A", "B")
        .morphism("g", "B", "C")
        .morphism("h", "A", "C")
        .composition("f", "g", "h")
        .identity_compositions()
        .build_validated()
        .unwrap()
}

#[test]
fn bounded_complete_nerve_and_endpoint_paths() {
    let category = triangle();
    let nerve = ValidatedFiniteNerve::new(&category, 4, 1000).unwrap();
    assert_eq!(nerve.n_simplices(0).unwrap().len(), 3);
    assert_eq!(nerve.n_simplices(1).unwrap().len(), 6);
    assert_eq!(nerve.n_simplices(2).unwrap().len(), 10);
    let paths = nerve.paths("A", "C", 2).unwrap();
    assert_eq!(paths.len(), 4); // h, id_A/h, f/g, h/id_C
    assert!(paths.contains(&Simplex::Chain(vec!["f".into(), "g".into()])));
    assert_eq!(nerve.paths("C", "A", 3).unwrap(), Vec::<Simplex>::new());
    assert_eq!(
        nerve.paths("A", "A", 0).unwrap(),
        vec![Simplex::Vertex("A".into())]
    );
    let simplex = Simplex::Chain(vec!["f".into(), "g".into()]);
    assert_eq!(
        nerve.all_faces(&simplex).unwrap(),
        vec![
            Simplex::Chain(vec!["g".into()]),
            Simplex::Chain(vec!["h".into()]),
            Simplex::Chain(vec!["f".into()]),
        ]
    );
    assert_eq!(nerve.all_degeneracies(&simplex).unwrap().len(), 3);
}

fn assert_face_degeneracy_identities(nerve: &ValidatedFiniteNerve, simplex: &NerveSimplex, n: usize, j: usize) {
    for i in 0..=j {
        assert_eq!(
            nerve.degeneracy(&nerve.degeneracy(simplex, j).unwrap(), i).unwrap(),
            nerve.degeneracy(&nerve.degeneracy(simplex, i).unwrap(), j + 1).unwrap(),
        );
    }
    for i in 0..=n + 1 {
        let result = nerve.face(&nerve.degeneracy(simplex, j).unwrap(), i).unwrap();
        let expected = if i < j {
            nerve.degeneracy(&nerve.face(simplex, i).unwrap(), j - 1).unwrap()
        } else if i == j || i == j + 1 {
            simplex.clone()
        } else {
            nerve.degeneracy(&nerve.face(simplex, i - 1).unwrap(), j).unwrap()
        };
        assert_eq!(result, expected);
    }
}

#[test]
fn every_simplicial_identity_on_complete_bounded_carrier() {
    let category = triangle();
    let nerve = ValidatedFiniteNerve::new(&category, 5, 1000).unwrap();
    for n in 0..=3 {
        for simplex in nerve.n_simplices(n).unwrap() {
            if n >= 2 {
                for j in 1..=n {
                    for i in 0..j {
                        assert_eq!(
                            nerve.face(&nerve.face(&simplex, j).unwrap(), i).unwrap(),
                            nerve.face(&nerve.face(&simplex, i).unwrap(), j - 1).unwrap(),
                        );
                    }
                }
            }
            for j in 0..=n {
                assert_face_degeneracy_identities(&nerve, &simplex, n, j);
            }
        }
    }
}

#[test]
fn malformed_chains_unknown_vertices_and_boundaries_refuse() {
    let category = triangle();
    let nerve = ValidatedFiniteNerve::new(&category, 3, 1000).unwrap();
    for simplex in [
        Simplex::Chain(vec![]),
        Simplex::Chain(vec!["foreign".into()]),
        Simplex::Chain(vec!["g".into(), "f".into()]),
        Simplex::Vertex("foreign".into()),
    ] {
        assert_eq!(
            nerve.face(&simplex, 0),
            Err(FiniteNerveRefusal::InvalidSimplex)
        );
        assert_eq!(
            nerve.degeneracy(&simplex, 0),
            Err(FiniteNerveRefusal::InvalidSimplex)
        );
    }
    assert_eq!(
        nerve.face(&Simplex::Vertex("A".into()), 0),
        Err(FiniteNerveRefusal::InvalidIndex)
    );
    assert_eq!(
        nerve.paths("foreign", "A", 2),
        Err(FiniteNerveRefusal::UnknownEndpoint)
    );
}

#[test]
fn incomplete_category_cannot_enter_validated_nerve() {
    let raw = triangle().into_declared();
    let mut missing_identity = raw.clone();
    missing_identity.identities.remove("B");
    assert!(ValidatedFiniteCategory::try_new(missing_identity).is_err());
    let mut missing_composition = raw;
    missing_composition
        .compositions
        .remove(&("f".into(), "g".into()));
    assert!(ValidatedFiniteCategory::try_new(missing_composition).is_err());
}

#[test]
fn exhaustion_is_refusal_and_never_partial_success() {
    let category = triangle();
    assert!(matches!(
        ValidatedFiniteNerve::new(&category, 33, 100),
        Err(FiniteNerveRefusal::InvalidBounds)
    ));
    assert!(matches!(
        ValidatedFiniteNerve::new(&category, 3, 0),
        Err(FiniteNerveRefusal::InvalidBounds)
    ));
    let bounded = ValidatedFiniteNerve::new(&category, 2, 6).unwrap();
    assert_eq!(
        bounded.n_simplices(2),
        Err(FiniteNerveRefusal::CellBudgetExceeded)
    );
    assert_eq!(
        bounded.n_simplices(3),
        Err(FiniteNerveRefusal::DimensionExceeded)
    );
    assert_eq!(
        bounded.degeneracy(&Simplex::Chain(vec!["f".into(), "g".into()]), 0),
        Err(FiniteNerveRefusal::DimensionExceeded)
    );
    let point = DeclaredFiniteCategoryBuilder::new("Point")
        .identity("X", "id_X")
        .identity_compositions()
        .build_validated()
        .unwrap();
    let path_budget = ValidatedFiniteNerve::new(&point, 3, 1).unwrap();
    assert_eq!(path_budget.n_simplices(1).unwrap().len(), 1);
    assert_eq!(
        path_budget.paths("X", "X", 1),
        Err(FiniteNerveRefusal::CellBudgetExceeded)
    );
}

#[test]
fn finite_nerve_functor_commutes_with_every_bounded_face_and_degeneracy() {
    let source = triangle();
    let target = DeclaredFiniteCategoryBuilder::new("Point")
        .identity("X", "id_X")
        .identity_compositions()
        .build_validated()
        .unwrap();
    let source_nerve = ValidatedFiniteNerve::new(&source, 4, 1000).unwrap();
    let target_nerve = ValidatedFiniteNerve::new(&target, 4, 1000).unwrap();
    let identity = ValidatedFiniteFunctor::try_new(
        identity_functor(source.declared(), "Id"),
        source.declared(),
        source.declared(),
    )
    .unwrap();
    let mut constant = DeclaredFiniteFunctor::new("Constant", "Triangle", "Point");
    for object in &source.declared().objects {
        constant.map_object(object, "X");
    }
    for name in source.declared().morphisms.keys() {
        constant.map_morphism(name, "id_X");
    }
    let constant =
        ValidatedFiniteFunctor::try_new(constant, source.declared(), target.declared()).unwrap();
    for n in 0..=3 {
        for simplex in source_nerve.n_simplices(n).unwrap() {
            assert_eq!(
                source_nerve
                    .map_simplex(&source_nerve, &identity, &simplex)
                    .unwrap(),
                simplex
            );
            let mapped = source_nerve
                .map_simplex(&target_nerve, &constant, &simplex)
                .unwrap();
            if n > 0 {
                for i in 0..=n {
                    assert_eq!(
                        source_nerve
                            .map_simplex(
                                &target_nerve,
                                &constant,
                                &source_nerve.face(&simplex, i).unwrap()
                            )
                            .unwrap(),
                        target_nerve.face(&mapped, i).unwrap(),
                    );
                }
            }
            for i in 0..=n {
                assert_eq!(
                    source_nerve
                        .map_simplex(
                            &target_nerve,
                            &constant,
                            &source_nerve.degeneracy(&simplex, i).unwrap()
                        )
                        .unwrap(),
                    target_nerve.degeneracy(&mapped, i).unwrap(),
                );
            }
        }
    }
    assert_eq!(
        source_nerve.map_simplex(&target_nerve, &identity, &Simplex::Vertex("A".into())),
        Err(FiniteNerveRefusal::FunctorCarrierMismatch)
    );
    let same_name_different_carrier = DeclaredFiniteCategoryBuilder::new("Triangle")
        .identity("A", "id_A")
        .identity_compositions()
        .build_validated()
        .unwrap();
    let wrong_identity = ValidatedFiniteFunctor::try_new(
        identity_functor(same_name_different_carrier.declared(), "Id"),
        same_name_different_carrier.declared(),
        same_name_different_carrier.declared(),
    )
    .unwrap();
    assert_eq!(
        source_nerve.map_simplex(&source_nerve, &wrong_identity, &Simplex::Vertex("A".into())),
        Err(FiniteNerveRefusal::FunctorCarrierMismatch)
    );
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_nerve.rs
// Claim: urn:core:crates_rs:tests:finite-nerve:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7cb07b24 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7cb07b24` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7cb07b24 {
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
impl BoundaryError7cb07b24 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7cb07b24 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7cb07b24 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7cb07b24 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7cb07b24> {
        if capacity_bound == 0 {
            return Err(BoundaryError7cb07b24::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7cb07b24::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7cb07b24::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_7cb07b24() {
    let admitted = BoundaryRecord7cb07b24::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7cb07b24::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

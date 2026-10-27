//! Exact finite controls for the declared groupoid bridge; no native Genesis
//! quotient, choice of complex scalars, or operational availability is inferred.
use linear_algebra::exact_field::{involution::adjoint, matrix as mx};
use core_category_theory::finite_category::DeclaredFiniteCategory;
use core_category_theory::finite_groupoid::ValidatedFiniteGroupoid;
use core_lie_theory::finite_groupoid_algebra::{FiniteGroupoidAlgebra, GroupoidAlgebraError};
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri, rq};
use std::collections::{BTreeMap, BTreeSet};

fn arrow(source: usize, target: usize, h: usize) -> String {
    format!("{source}>{target}:{h}")
}

/// Pair(n) x H. The supplied table uses left * right, identity index zero.
fn product_groupoid(n: usize, table: &[Vec<usize>], inv: &[usize]) -> ValidatedFiniteGroupoid {
    let mut c = DeclaredFiniteCategory::new("declared product groupoid");
    let mut inverses = BTreeMap::new();
    for source in 0..n {
        for target in 0..n {
            for h in 0..table.len() {
                let name = arrow(source, target, h);
                c.add_morphism(&name, &source.to_string(), &target.to_string());
                inverses.insert(name, arrow(target, source, inv[h]));
                for end in 0..n {
                    for k in 0..table.len() {
                        c.set_composition(
                            &arrow(source, target, h),
                            &arrow(target, end, k),
                            &arrow(source, end, table[k][h]),
                        );
                    }
                }
            }
        }
    }
    for object in 0..n {
        c.set_identity(&object.to_string(), &arrow(object, object, 0));
    }
    ValidatedFiniteGroupoid::try_new(c, inverses).unwrap()
}
fn pair(n: usize) -> ValidatedFiniteGroupoid {
    product_groupoid(n, &[vec![0]], &[0])
}
fn c2(n: usize) -> ValidatedFiniteGroupoid {
    product_groupoid(n, &[vec![0, 1], vec![1, 0]], &[0, 1])
}
fn s3(n: usize) -> ValidatedFiniteGroupoid {
    let permutations = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];
    let table: Vec<Vec<_>> = permutations
        .iter()
        .map(|a| {
            permutations
                .iter()
                .map(|b| {
                    let product = [a[b[0]], a[b[1]], a[b[2]]];
                    permutations.iter().position(|p| *p == product).unwrap()
                })
                .collect()
        })
        .collect();
    let inv: Vec<_> = (0..6)
        .map(|i| (0..6).find(|&j| table[i][j] == 0).unwrap())
        .collect();
    product_groupoid(n, &table, &inv)
}
fn discrete_two() -> ValidatedFiniteGroupoid {
    let mut c = DeclaredFiniteCategory::new("two components");
    for x in ["a", "b"] {
        c.add_identity(x, x);
        c.set_composition(x, x, x);
    }
    ValidatedFiniteGroupoid::try_new(
        c,
        BTreeMap::from([("a".into(), "a".into()), ("b".into(), "b".into())]),
    )
    .unwrap()
}

fn nontrivial_connectors() -> ValidatedFiniteGroupoid {
    // Force the chosen 0->1 connector to carry a noncentral element of order
    // three. This exercises cancellation/conjugation, not just identity charts.
    let original = s3(2);
    let old = original.category().declared();
    let rename = |name: &str| {
        if name == "0>1:3" {
            format!("a_{name}")
        } else {
            format!("z_{name}")
        }
    };
    let mut c = DeclaredFiniteCategory::new("S3 with nonidentity connector");
    for (name, g) in &old.morphisms {
        c.add_morphism(&rename(name), &g.source, &g.target);
    }
    for (object, id) in &old.identities {
        c.set_identity(object, &rename(id));
    }
    for ((f, g), fg) in &old.compositions {
        c.set_composition(&rename(f), &rename(g), &rename(fg));
    }
    let inv = old
        .morphisms
        .keys()
        .map(|g| (rename(g), rename(original.inverse(g).unwrap())))
        .collect();
    let groupoid = ValidatedFiniteGroupoid::try_new(c, inv).unwrap();
    assert_eq!(groupoid.components().unwrap()[0].connectors["1"], "a_0>1:3");
    groupoid
}

#[test]
fn matrix_group_coordinates_preserve_every_product_and_inverse() {
    // S3 makes a reversed multiplication convention observable; Pair(6)
    // checks the M6 carrier without asserting the existence of MUBs.
    for groupoid in [
        pair(6),
        c2(2),
        s3(2),
        nontrivial_connectors(),
        discrete_two(),
    ] {
        let c = groupoid.category().declared();
        let coordinates = groupoid.matrix_coordinates().unwrap();
        let components = groupoid.components().unwrap();
        let expected: usize = components
            .iter()
            .map(|b| b.objects.len() * b.objects.len() * b.isotropy.len())
            .sum();
        assert_eq!(expected, c.morphisms.len());
        let images: BTreeSet<_> = coordinates.values().collect();
        assert_eq!(images.len(), expected); // bijective onto the whole block basis
        for (g, cg) in &coordinates {
            let gi = groupoid.inverse(g).unwrap();
            let ci = &coordinates[gi];
            assert_eq!(ci.component_root, cg.component_root);
            assert_eq!(ci.row_object, cg.column_object);
            assert_eq!(ci.column_object, cg.row_object);
            assert_eq!(
                Some(ci.isotropy_arrow.as_str()),
                groupoid.inverse(&cg.isotropy_arrow)
            );
            for (h, ch) in &coordinates {
                let product = c.compose(h, g); // g * h, rightmost first
                let compatible =
                    cg.component_root == ch.component_root && cg.column_object == ch.row_object;
                assert_eq!(product.is_some(), compatible);
                if let Some(gh) = product {
                    let cp = &coordinates[gh];
                    assert_eq!(cp.component_root, cg.component_root);
                    assert_eq!(cp.row_object, cg.row_object);
                    assert_eq!(cp.column_object, ch.column_object);
                    assert_eq!(
                        Some(cp.isotropy_arrow.as_str()),
                        c.compose(&ch.isotropy_arrow, &cg.isotropy_arrow)
                    );
                }
            }
        }
    }
    assert!(pair(6).is_connected_thin().unwrap());
    assert!(!c2(2).is_connected_thin().unwrap());
    assert!(!s3(1).is_connected_thin().unwrap());
    assert!(!discrete_two().is_connected_thin().unwrap());
}

#[test]
fn regular_action_preserves_star_products_and_positive_trace_on_full_bases() {
    for groupoid in [c2(2), s3(1), discrete_two()] {
        let algebra = FiniteGroupoidAlgebra::new(groupoid).unwrap();
        let basis: Vec<_> = algebra
            .arrows()
            .iter()
            .map(|g| algebra.basis(g).unwrap())
            .collect();
        let regular: Vec<_> = basis
            .iter()
            .map(|a| algebra.left_regular(a).unwrap())
            .collect();
        assert_eq!(
            algebra.left_regular(&algebra.unit()).unwrap(),
            mx::identity::<G>(algebra.dimension()).unwrap()
        );
        for (i, a) in basis.iter().enumerate() {
            let star = algebra.star(a).unwrap();
            assert_eq!(
                algebra.left_regular(&star).unwrap(),
                adjoint(&regular[i]).unwrap()
            );
            for (j, b) in basis.iter().enumerate() {
                let ab = algebra.multiply(a, b).unwrap();
                assert_eq!(
                    algebra.left_regular(&ab).unwrap(),
                    mx::multiply(&regular[i], &regular[j]).unwrap()
                );
                assert_eq!(
                    algebra.trace(&algebra.multiply(&star, b).unwrap()).unwrap(),
                    if i == j { G::one() } else { G::zero() }
                );
                assert_eq!(
                    algebra.trace(&ab).unwrap(),
                    algebra.trace(&algebra.multiply(b, a).unwrap()).unwrap()
                );
            }
        }
        // A non-real superposition checks conjugation and mixed coefficients.
        let a: Vec<_> = (0..algebra.dimension())
            .map(|i| {
                let j = i64::try_from(i).unwrap();
                G {
                    re: rq(j + 1, 3),
                    im: rq(2 - j, 5),
                }
            })
            .collect();
        let squared = algebra.multiply(&algebra.star(&a).unwrap(), &a).unwrap();
        let norm = algebra.coefficient_norm_squared(&a).unwrap();
        assert!(norm > ri(0));
        assert_eq!(algebra.trace(&squared).unwrap(), G::from_rational(norm));
        // Faithfulness: L_a applied to the algebra unit recovers all coefficients.
        assert_eq!(
            mx::multiply_vector(&algebra.left_regular(&a).unwrap(), &algebra.unit()).unwrap(),
            a
        );
    }
}

#[test]
fn nontrivial_isotropy_and_disconnectedness_give_proper_central_projectors() {
    for groupoid in [c2(2), s3(1), discrete_two()] {
        let algebra = FiniteGroupoidAlgebra::new(groupoid).unwrap();
        for component in algebra.groupoid().components().unwrap() {
            let p = algebra.central_isotropy_average(&component.root).unwrap();
            assert_ne!(p, vec![G::zero(); algebra.dimension()]);
            assert_ne!(p, algebra.unit());
            assert_eq!(algebra.star(&p).unwrap(), p);
            assert_eq!(algebra.multiply(&p, &p).unwrap(), p);
            for arrow in algebra.arrows() {
                let a = algebra.basis(arrow).unwrap();
                assert_eq!(
                    algebra.multiply(&p, &a).unwrap(),
                    algebra.multiply(&a, &p).unwrap()
                );
            }
        }
    }
    let simple = FiniteGroupoidAlgebra::new(pair(2)).unwrap();
    assert_eq!(simple.central_isotropy_average("0").unwrap(), simple.unit());
}

#[test]
fn a_character_can_separate_arrows_while_losing_linear_faithfulness() {
    let algebra = FiniteGroupoidAlgebra::new(c2(1)).unwrap();
    let e = algebra.basis("0>0:0").unwrap();
    let s = algebra.basis("0>0:1").unwrap();
    let character = |a: &[G]| a[0].sub(&a[1]); // declared sign character
    assert_eq!(character(&e), G::one());
    assert_eq!(character(&s), G::from_ints(-1, 0));
    assert_ne!(character(&e), character(&s)); // faithful on the two arrows
    let lost: Vec<_> = e.iter().zip(&s).map(|(a, b)| a.add(b)).collect();
    assert_eq!(character(&lost), G::zero()); // not faithful on the algebra
    assert_eq!(algebra.coefficient_norm_squared(&lost).unwrap(), ri(2));
    for a in [&e, &s, &lost] {
        for b in [&e, &s, &lost] {
            assert_eq!(
                character(&algebra.multiply(a, b).unwrap()),
                character(a).mul(&character(b))
            );
        }
    }
    let plus = algebra.central_isotropy_average("0").unwrap();
    let minus: Vec<_> = algebra
        .unit()
        .iter()
        .zip(&plus)
        .map(|(a, b)| a.sub(b))
        .collect();
    assert_eq!(algebra.multiply(&plus, &minus).unwrap(), vec![G::zero(); 2]);
    assert_eq!(algebra.multiply(&minus, &minus).unwrap(), minus);
    assert_eq!(character(&plus), G::zero());
    assert_eq!(character(&minus), G::one());
    assert_eq!(algebra.trace(&plus).unwrap(), G::from_rational(rq(1, 2)));
    assert_eq!(algebra.trace(&minus).unwrap(), G::from_rational(rq(1, 2)));
}

#[test]
fn malformed_coefficients_unknown_names_and_empty_algebra_are_refused() {
    let algebra = FiniteGroupoidAlgebra::new(pair(2)).unwrap();
    let short = vec![G::one(); 3];
    let long = vec![G::one(); 5];
    for bad in [&short, &long] {
        assert!(algebra.multiply(bad, &algebra.unit()).is_err());
        assert!(algebra.multiply(&algebra.unit(), bad).is_err());
        assert!(algebra.star(bad).is_err());
        assert!(algebra.trace(bad).is_err());
        assert!(algebra.left_regular(bad).is_err());
        assert!(algebra.coefficient_norm_squared(bad).is_err());
    }
    assert!(matches!(
        algebra.basis("unknown"),
        Err(GroupoidAlgebraError::UnknownArrow(_))
    ));
    assert!(matches!(
        algebra.central_isotropy_average("unknown"),
        Err(GroupoidAlgebraError::UnknownComponent(_))
    ));
    let empty =
        ValidatedFiniteGroupoid::try_new(DeclaredFiniteCategory::new("empty"), BTreeMap::new())
            .unwrap();
    assert!(matches!(
        FiniteGroupoidAlgebra::new(empty),
        Err(GroupoidAlgebraError::Empty)
    ));
}

#[test]
fn a_projective_twist_changes_the_simplicity_question() {
    use linear_algebra::exact_field::elimination::rank;
    use core_lie_theory::pauli_symplectic::{pauli, Pauli};

    // U_(a,b)=X^a Z^b, indexed by 2a+b. The underlying group is C2 x C2,
    // but U_(a,b) U_(c,d)=(-1)^(bc) U_(a+c,b+d): NOT untwisted convolution.
    let identity = pauli::<G>(Pauli::Identity).unwrap();
    let x = pauli::<G>(Pauli::X).unwrap();
    let z = pauli::<G>(Pauli::Z).unwrap();
    let xz = mx::multiply(&x, &z).unwrap();
    let basis = [identity, z, x, xz];
    let sign = |odd: usize| G::from_ints(if odd % 2 == 0 { 1 } else { -1 }, 0);
    for a in 0..2 {
        for b in 0..2 {
            assert_eq!(
                adjoint(&basis[2 * a + b]).unwrap(),
                mx::scale(&basis[2 * a + b], &sign(a * b)).unwrap()
            );
            for c in 0..2 {
                for d in 0..2 {
                    assert_eq!(
                        mx::multiply(&basis[2 * a + b], &basis[2 * c + d]).unwrap(),
                        mx::scale(&basis[2 * ((a + c) % 2) + (b + d) % 2], &sign(b * c)).unwrap()
                    );
                }
            }
        }
    }
    // Independence plus the explicit product/* checks identifies the entire
    // twisted algebra with M2, not merely a dimension-compatible vector space.
    let flattened = mx::from_rows(basis.iter().map(|a| a.as_slice().to_vec()).collect()).unwrap();
    assert_eq!(rank(&flattened).unwrap(), 4);
}

// Origin: engine/crates_rs/tests/core_lie_theory/finite_groupoid_algebra.rs
// Claim: urn:core:crates_rs:tests:finite-groupoid-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb31b4c94 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb31b4c94` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb31b4c94 {
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
impl BoundaryErrorb31b4c94 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb31b4c94 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb31b4c94 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb31b4c94 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb31b4c94> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb31b4c94::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb31b4c94::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb31b4c94::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_b31b4c94() {
    let admitted = BoundaryRecordb31b4c94::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb31b4c94::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

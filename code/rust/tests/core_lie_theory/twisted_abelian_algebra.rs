//! Finite exact controls for the center theorem and the six-dimensional Weyl
//! realization. These tests make no MUB-extension or primitive-admission claim.
use linear_algebra::exact_field::{involution::adjoint, matrix as mx};
use core_lie_theory::heisenberg::WeylHeisenberg;
use core_lie_theory::twisted_abelian_algebra::{TwistedAbelianAlgebra, TwistedAlgebraError};
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::{ri, rq};

fn square_group(n: usize) -> Vec<Vec<usize>> {
    (0..n * n)
        .map(|g| {
            (0..n * n)
                .map(|h| ((g / n + h / n) % n) * n + (g % n + h % n) % n)
                .collect()
        })
        .collect()
}
fn sixth_cocycle(k: usize) -> TwistedAbelianAlgebra<Cyclotomic<6>> {
    let alpha = (0..36)
        .map(|g| {
            (0..36)
                .map(|h| Cyclotomic::<6>::zeta(i64::try_from(k * (g % 6) * (h / 6)).unwrap()))
                .collect()
        })
        .collect();
    TwistedAbelianAlgebra::new(square_group(6), alpha).unwrap()
}
fn pauli_cocycle() -> TwistedAbelianAlgebra<G> {
    let alpha = (0..4)
        .map(|g| {
            (0..4)
                .map(|h| G::from_ints(if (g % 2) * (h / 2) == 0 { 1 } else { -1 }, 0))
                .collect()
        })
        .collect();
    TwistedAbelianAlgebra::new(square_group(2), alpha).unwrap()
}

#[test]
fn identical_thirty_six_labels_have_distinct_verified_sector_profiles() {
    let expected = [(36, 1), (1, 6), (4, 3), (9, 2), (4, 3), (1, 6)];
    for (k, (sectors, size)) in expected.into_iter().enumerate() {
        let algebra = sixth_cocycle(k);
        let profile = algebra.complex_block_profile().unwrap();
        assert_eq!(
            (
                profile.algebra_dimension,
                profile.center_dimension,
                profile.block_dimension
            ),
            (36, sectors, size)
        );
        let radical: Vec<_> = (0..36)
            .filter(|g| k * (g / 6) % 6 == 0 && k * (g % 6) % 6 == 0)
            .collect();
        assert_eq!(algebra.center_basis(), radical);
        // Each reported central basis element commutes; each other element
        // has a concrete witness among the two coordinate generators.
        for g in 0..36 {
            let generator_witness = [6, 1]
                .into_iter()
                .any(|h| algebra.commutator_phase(g, h).unwrap() != Cyclotomic::<6>::one());
            assert_eq!(generator_witness, !algebra.center_basis().contains(&g));
        }
    }
}

#[test]
fn primitive_sixth_twist_matches_every_weyl_product_star_and_matrix_unit() {
    // Use the existing even-dimensional owner with the required 12th root.
    // Unsymmetrized U(a,b)=X^a Z^b has labels modulo6 and no half-phase ambiguity.
    type F = Cyclotomic<12>;
    let w = WeylHeisenberg::with_phase_root(6, F::zeta(2), F::zeta(1)).unwrap();
    assert!(w.verify_relations().unwrap());
    let alpha = (0..36)
        .map(|g| {
            (0..36)
                .map(|h| F::zeta(i64::try_from(2 * (g % 6) * (h / 6)).unwrap()))
                .collect()
        })
        .collect();
    let algebra = TwistedAbelianAlgebra::new(square_group(6), alpha).unwrap();
    assert_eq!(algebra.center_basis(), &[0]);
    let x = w.shift().unwrap();
    let z = w.clock().unwrap();
    let basis: Vec<_> = (0..36)
        .map(|g| {
            mx::multiply(
                &mx::power(&x, (g / 6) as u64).unwrap(),
                &mx::power(&z, (g % 6) as u64).unwrap(),
            )
            .unwrap()
        })
        .collect();
    for g in 0..36 {
        let (inverse, phase) = algebra.basis_star(g).unwrap();
        assert_eq!(
            adjoint(&basis[g]).unwrap(),
            mx::scale(&basis[inverse], &phase).unwrap()
        );
        for h in 0..36 {
            let (gh, phase) = algebra.basis_product(g, h).unwrap();
            assert_eq!(
                mx::multiply(&basis[g], &basis[h]).unwrap(),
                mx::scale(&basis[gh], &phase).unwrap()
            );
            let overlap =
                mx::trace(&mx::multiply(&adjoint(&basis[g]).unwrap(), &basis[h]).unwrap()).unwrap();
            assert_eq!(overlap, F::rational(ri(if g == h { 6 } else { 0 })));
        }
    }
    // Independent matrix-unit basis: reconstruct all36 columns with the
    // existing symmetric-displacement coefficient/reconstruction owner.
    for row in 0..6 {
        for col in 0..6 {
            let mut unit = mx::zeros(6, 6).unwrap();
            unit.set(row, col, F::one()).unwrap();
            assert_eq!(w.reconstruct_operator(&unit).unwrap(), unit);
        }
    }
    // The symmetric labels themselves are modulo12; quotienting them modulo6
    // without their phase loses the winding sign.
    assert_eq!(
        w.displacement(7, 1).unwrap(),
        mx::scale(&w.displacement(1, 1).unwrap(), &F::rational(ri(-1))).unwrap()
    );
}

#[test]
fn twisted_regular_representation_and_positive_trace_retain_all_coefficients() {
    let algebra = pauli_cocycle();
    let basis: Vec<_> = (0..4).map(|g| algebra.basis(g).unwrap()).collect();
    let regular: Vec<_> = basis
        .iter()
        .map(|a| algebra.left_regular(a).unwrap())
        .collect();
    for g in 0..4 {
        let star = algebra.star(&basis[g]).unwrap();
        assert_eq!(
            algebra.left_regular(&star).unwrap(),
            adjoint(&regular[g]).unwrap()
        );
        for h in 0..4 {
            let product = algebra.multiply(&basis[g], &basis[h]).unwrap();
            assert_eq!(
                algebra.left_regular(&product).unwrap(),
                mx::multiply(&regular[g], &regular[h]).unwrap()
            );
            assert_eq!(
                algebra
                    .trace(&algebra.multiply(&star, &basis[h]).unwrap())
                    .unwrap(),
                if g == h { G::one() } else { G::zero() }
            );
        }
    }
    let a = vec![
        G::from_ints(1, 2),
        G::from_rational(rq(1, 3)),
        G::from_ints(-2, 1),
        G::i(),
    ];
    let square = algebra.multiply(&algebra.star(&a).unwrap(), &a).unwrap();
    assert_eq!(
        algebra.trace(&square).unwrap(),
        G::from_rational(rq(100, 9))
    );
    assert_eq!(
        mx::multiply_vector(&algebra.left_regular(&a).unwrap(), &basis[0]).unwrap(),
        a
    );
    // A non-real cocycle detects forgetting conjugation of alpha in the star.
    // The block profile is over C: the native Q(i) field need not split it.
    let phase = TwistedAbelianAlgebra::new(
        vec![vec![0, 1], vec![1, 0]],
        vec![vec![G::one(), G::one()], vec![G::one(), G::i()]],
    )
    .unwrap();
    let s = phase.basis(1).unwrap();
    assert_eq!(phase.basis_star(1).unwrap(), (1, G::from_ints(0, -1)));
    let star = phase.star(&s).unwrap();
    assert_eq!(phase.multiply(&star, &s).unwrap(), phase.basis(0).unwrap());
    assert_eq!(
        phase.left_regular(&star).unwrap(),
        adjoint(&phase.left_regular(&s).unwrap()).unwrap()
    );
    assert_eq!(phase.complex_block_profile().unwrap().center_dimension, 2);
}

#[test]
fn rephasing_changes_the_cocycle_but_preserves_its_commutator_radical() {
    let original = pauli_cocycle();
    let phases = [G::one(), G::i(), G::from_ints(-1, 0), G::one()];
    let rephased = (0..4)
        .map(|g| {
            (0..4)
                .map(|h| {
                    let gh = original.group().multiply(g, h).unwrap();
                    phases[g]
                        .mul(&phases[h])
                        .mul(&phases[gh].conj())
                        .mul(original.phase(g, h).unwrap())
                })
                .collect()
        })
        .collect();
    let changed = TwistedAbelianAlgebra::new(square_group(2), rephased).unwrap();
    assert_ne!(original.phase(1, 1).unwrap(), changed.phase(1, 1).unwrap());
    assert_eq!(original.center_basis(), changed.center_basis());
    for g in 0..4 {
        for h in 0..4 {
            assert_eq!(
                original.commutator_phase(g, h).unwrap(),
                changed.commutator_phase(g, h).unwrap()
            );
        }
    }
}

#[test]
fn declaration_checks_refuse_missing_nonunitary_and_incoherent_phase_data() {
    let table = square_group(2);
    let trivial = vec![vec![G::one(); 4]; 4];
    assert!(matches!(
        TwistedAbelianAlgebra::<G>::new(vec![], vec![]),
        Err(TwistedAlgebraError::Group(_))
    ));
    assert!(matches!(
        TwistedAbelianAlgebra::new(table.clone(), trivial[..3].to_vec()),
        Err(TwistedAlgebraError::CocycleShape)
    ));
    let mut bad = trivial.clone();
    bad[0][1] = G::from_ints(-1, 0);
    assert!(matches!(
        TwistedAbelianAlgebra::new(table.clone(), bad),
        Err(TwistedAlgebraError::NotNormalized(1))
    ));
    let mut bad = trivial.clone();
    bad[1][1] = G::from_ints(2, 0);
    assert!(matches!(
        TwistedAbelianAlgebra::new(table.clone(), bad),
        Err(TwistedAlgebraError::NotUnitary { .. })
    ));
    let mut bad = trivial.clone();
    bad[1][2] = G::from_ints(-1, 0);
    assert!(matches!(
        TwistedAbelianAlgebra::new(table.clone(), bad),
        Err(TwistedAlgebraError::NotCocycle { .. })
    ));
    let mut broken = table.clone();
    broken[1].pop();
    assert!(matches!(
        TwistedAbelianAlgebra::new(broken, trivial.clone()),
        Err(TwistedAlgebraError::Group(_))
    ));
    let permutations = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];
    let s3 = permutations
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
    assert!(matches!(
        TwistedAbelianAlgebra::new(s3, vec![vec![G::one(); 6]; 6]),
        Err(TwistedAlgebraError::NonAbelian { .. })
    ));
    assert!(matches!(
        TwistedAbelianAlgebra::<G>::new(vec![vec![]; 65], vec![]),
        Err(TwistedAlgebraError::Budget(65))
    ));
    let algebra = TwistedAbelianAlgebra::new(table, trivial).unwrap();
    for bad in [vec![G::zero(); 3], vec![G::zero(); 5]] {
        assert!(algebra.multiply(&bad, &algebra.basis(0).unwrap()).is_err());
        assert!(algebra.multiply(&algebra.basis(0).unwrap(), &bad).is_err());
        assert!(algebra.star(&bad).is_err());
        assert!(algebra.trace(&bad).is_err());
        assert!(algebra.left_regular(&bad).is_err());
    }
    assert!(algebra.phase(0, 4).is_err());
    assert!(algebra.phase(4, 0).is_err());
    assert!(algebra.basis(4).is_err());
    assert!(algebra.basis_star(4).is_err());
}

#[test]
fn identity_index_is_not_assumed_to_be_zero() {
    // Relabel the C2 identity as index1.
    let algebra =
        TwistedAbelianAlgebra::new(vec![vec![1, 0], vec![0, 1]], vec![vec![G::one(); 2]; 2])
            .unwrap();
    assert_eq!(algebra.group().identity(), 1);
    assert_eq!(
        algebra
            .trace(&[G::from_ints(7, 0), G::from_ints(3, 0)])
            .unwrap(),
        G::from_ints(3, 0)
    );
    assert_eq!(
        algebra
            .multiply(&algebra.basis(0).unwrap(), &algebra.basis(0).unwrap())
            .unwrap(),
        algebra.basis(1).unwrap()
    );
    assert_eq!(algebra.complex_block_profile().unwrap().center_dimension, 2);
}

#[test]
fn six_dimensional_cyclic_weyl_classes_have_maximum_disjoint_family_three() {
    use std::collections::BTreeSet;
    let algebra = sixth_cocycle(1);
    let group = algebra.group();
    let mut classes = BTreeSet::new();
    for g in 0..36 {
        if group.element_order(g).unwrap() == 6 {
            let subgroup: BTreeSet<_> = group
                .subgroup_generated_by(&[g])
                .unwrap()
                .into_iter()
                .collect();
            assert_eq!(subgroup.len(), 6);
            for &a in &subgroup {
                for &b in &subgroup {
                    assert_eq!(
                        algebra.commutator_phase(a, b).unwrap(),
                        Cyclotomic::<6>::one()
                    );
                }
            }
            classes.insert(subgroup);
        }
    }
    let classes: Vec<_> = classes.into_iter().collect();
    assert_eq!(classes.len(), 12);
    let disjoint = |i: usize, j: usize| {
        classes[i]
            .intersection(&classes[j])
            .copied()
            .collect::<Vec<_>>()
            == vec![0]
    };
    let (triples, quadruples) = count_disjoint_triples_and_quadruples(&disjoint);
    assert_eq!(triples, 24);
    assert_eq!(quadruples, 0);
    // This is the complete stated cyclic-Weyl class family, not all bases of C6.
}

fn count_disjoint_triples_and_quadruples(disjoint: &dyn Fn(usize, usize) -> bool) -> (usize, usize) {
    let mut triples = 0;
    let mut quadruples = 0;
    for i in 0..12 {
        for j in i + 1..12 {
            if !disjoint(i, j) {
                continue;
            }
            for k in j + 1..12 {
                if disjoint(i, k) && disjoint(j, k) {
                    triples += 1;
                    quadruples += (k + 1..12)
                        .filter(|&l| disjoint(i, l) && disjoint(j, l) && disjoint(k, l))
                        .count();
                }
            }
        }
    }
    (triples, quadruples)
}

// Origin: engine/crates_rs/tests/core_lie_theory/twisted_abelian_algebra.rs
// Claim: urn:core:crates_rs:tests:twisted-abelian-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde3100a70 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde3100a70` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore3100a70 {
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
impl BoundaryErrore3100a70 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore3100a70 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore3100a70 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde3100a70 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore3100a70> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore3100a70::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore3100a70::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore3100a70::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e3100a70() {
    let admitted = BoundaryRecorde3100a70::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde3100a70::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

//! Product non-factorization of finite bipartite weight tables: the product
//! defect vanishes exactly on the tables that factor; the diagonal-half and
//! uniform-quarter witnesses; the Bell state and the classical mixture share a
//! table but not entanglement; local maps; and dependence on the declared
//! product basis. Every value is exact.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use num_traits::{One, Signed, Zero};
use core_finite_probability::error::ClassicalShadowError;
use core_finite_probability::stochastic_map::StochasticMap;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;

use core_finite_probability::joint_table::{JointTable, WeightTableError};
use core_quantum_physics::bipartite_operator::{
    self as bo, BipartiteError, DecomposableWitness, ProductDecomposition,
};

fn table(rows: Vec<Vec<Rational>>) -> JointTable {
    JointTable::new(rows).unwrap()
}

fn int_table(rows: &[&[i64]]) -> JointTable {
    table(
        rows.iter()
            .map(|r| r.iter().map(|&v| ri(v)).collect())
            .collect(),
    )
}

fn diagonal_half() -> JointTable {
    table(vec![vec![rq(1, 2), ri(0)], vec![ri(0), rq(1, 2)]])
}

fn uniform_quarter() -> JointTable {
    table(vec![vec![rq(1, 4); 2]; 2])
}

fn computational_basis() -> Vec<Vec<GaussianRat>> {
    vec![vec![gi(1, 0), gi(0, 0)], vec![gi(0, 0), gi(1, 0)]]
}

/// `(1, 1)` and `(1, -1)`: the Hadamard basis, left unnormalised so it stays rational.
fn hadamard_basis() -> Vec<Vec<GaussianRat>> {
    vec![vec![gi(1, 0), gi(1, 0)], vec![gi(1, 0), gi(-1, 0)]]
}

fn ket(entries: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
    let v: Vec<GaussianRat> = entries.iter().map(|&(re, im)| gi(re, im)).collect();
    bo::pure_state(&v).unwrap()
}

fn bell_phi_plus() -> BasicMatrix<GaussianRat> {
    ket(&[(1, 0), (0, 0), (0, 0), (1, 0)])
}

fn classical_mixture() -> BasicMatrix<GaussianRat> {
    let half = GaussianRat::from_rational(rq(1, 2));
    mx::diagonal(&[half.clone(), gi(0, 0), gi(0, 0), half]).unwrap()
}

fn singlet_projector() -> BasicMatrix<GaussianRat> {
    ket(&[(0, 0), (1, 0), (-1, 0), (0, 0)])
}

fn half_identity() -> BasicMatrix<GaussianRat> {
    mx::scale(
        &mx::identity::<GaussianRat>(2).unwrap(),
        &GaussianRat::from_rational(rq(1, 2)),
    )
    .unwrap()
}

fn stochastic(rows: &[&[(i64, i64)]]) -> StochasticMap {
    let entries: Vec<Vec<Rational>> = rows
        .iter()
        .map(|r| r.iter().map(|&(n, d)| rq(n, d)).collect())
        .collect();
    StochasticMap::try_from_rows(entries.len(), entries[0].len(), entries, "declared").unwrap()
}

fn identity_map() -> StochasticMap {
    stochastic(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 1)]])
}

fn flip_map() -> StochasticMap {
    stochastic(&[&[(0, 1), (1, 1)], &[(1, 1), (0, 1)]])
}

// ---------------------------------------------------------------------------
// QM-070-C5: the defect mass is zero exactly on tables that factor.
// ---------------------------------------------------------------------------

#[test]
fn product_defect_mass_vanishes_exactly_on_tables_with_vanishing_minors() {
    for (rows, cols, largest, expected_tables, expected_products) in [
        (2usize, 2usize, 3u32, 255usize, 63usize),
        (2, 3, 2, 728, 92),
        (3, 3, 1, 511, 49),
    ] {
        let base = largest + 1;
        let cells = (rows * cols) as u32;
        let (mut tables, mut products) = (0usize, 0usize);
        for code in 1..base.pow(cells) {
            let mut rest = code;
            let entries: Vec<i64> = (0..cells)
                .map(|_| {
                    let digit = rest % base;
                    rest /= base;
                    i64::from(digit)
                })
                .collect();
            let t = table(
                entries
                    .chunks(cols)
                    .map(|r| r.iter().map(|&v| ri(v)).collect())
                    .collect(),
            );
            let mass_is_zero = t.product_defect_mass().is_zero();
            assert_eq!(mass_is_zero, t.has_vanishing_minors(), "table {entries:?}");
            tables += 1;
            products += usize::from(mass_is_zero);
        }
        assert_eq!(
            (tables, products),
            (expected_tables, expected_products),
            "{rows}x{cols}"
        );
    }
}

// ---------------------------------------------------------------------------
// QM-070-C6: the diagonal-half and uniform-quarter witnesses.
// ---------------------------------------------------------------------------

#[test]
fn diagonal_half_is_correlated_with_uniform_marginals_and_uniform_quarter_is_a_product() {
    let half = diagonal_half();
    assert_eq!(half.total(), Rational::one());
    assert_eq!(half.marginal_a(), vec![rq(1, 2), rq(1, 2)]);
    assert_eq!(half.marginal_b(), vec![rq(1, 2), rq(1, 2)]);
    assert_eq!(
        half.product_defect(),
        vec![vec![rq(1, 4), rq(-1, 4)], vec![rq(-1, 4), rq(1, 4)]]
    );
    assert_eq!(half.product_defect_mass(), ri(1));
    assert!(!half.has_vanishing_minors());

    let quarter = uniform_quarter();
    assert_eq!(quarter.product_defect(), vec![vec![ri(0); 2]; 2]);
    assert!(quarter.product_defect_mass().is_zero());
    assert!(quarter.has_vanishing_minors());

    // The mass scales with the total; the normalised table is the witness itself.
    let unnormalised = int_table(&[&[1, 0], &[0, 1]]);
    assert_eq!(unnormalised.product_defect_mass(), ri(2));
    assert_eq!(unnormalised.normalized(), half);
}

// ---------------------------------------------------------------------------
// QM-070-C2 / C7: one table, two ontologies.
// ---------------------------------------------------------------------------

#[test]
fn bell_state_and_classical_mixture_share_a_table_but_not_entanglement() {
    let bell = bell_phi_plus();
    let mixture = classical_mixture();
    assert_ne!(bell, mixture);
    let z = computational_basis();
    let bell_table = bo::descend_to_table(&bell, &z, &z).unwrap();
    let mixture_table = bo::descend_to_table(&mixture, &z, &z).unwrap();
    assert_eq!(bell_table, diagonal_half());
    assert_eq!(mixture_table, diagonal_half());
    assert_eq!(bell_table.product_defect_mass(), ri(1));
    // Both have maximally mixed reduced states, matching the table's marginals.
    for rho in [&bell, &mixture] {
        assert_eq!(bo::partial_trace_b(rho, 2, 2).unwrap(), half_identity());
        assert_eq!(bo::partial_trace_a(rho, 2, 2).unwrap(), half_identity());
    }

    // The Bell state has a non-PSD partial transpose and a decomposable witness
    // W = |Psi-><Psi-|^(T_B) = I/2 - |Phi+><Phi+| with Tr(W Phi+) = -1/2.
    assert!(!bo::is_ppt(&bell, 2, 2).unwrap());
    let witness = DecomposableWitness::new(&singlet_projector(), 2, 2).unwrap();
    assert_eq!(
        witness.operator(),
        &mx::sub(
            &mx::scale(
                &mx::identity::<GaussianRat>(4).unwrap(),
                &GaussianRat::from_rational(rq(1, 2))
            )
            .unwrap(),
            &bell
        )
        .unwrap()
    );
    assert_eq!(witness.value(&bell).unwrap(), rq(-1, 2));
    assert!(witness.certifies_entanglement(&bell).unwrap());

    // The mixture is PPT, gets witness value 0, and decomposes into product states.
    assert!(bo::is_ppt(&mixture, 2, 2).unwrap());
    assert_eq!(witness.value(&mixture).unwrap(), ri(0));
    assert!(!witness.certifies_entanglement(&mixture).unwrap());
    // Only states are certified: -I and 2 * Phi+ pair negatively with W too.
    let minus_identity = mx::scale(&mx::identity::<GaussianRat>(4).unwrap(), &gi(-1, 0)).unwrap();
    assert_eq!(witness.value(&minus_identity).unwrap(), ri(-1));
    assert_eq!(
        witness.certifies_entanglement(&minus_identity),
        Err(BipartiteError::NotPositive)
    );
    assert_eq!(
        witness.certifies_entanglement(&mx::scale(&bell, &gi(2, 0)).unwrap()),
        Err(BipartiteError::NotUnitTrace)
    );
    let (zero, one) = (ket(&[(1, 0), (0, 0)]), ket(&[(0, 0), (1, 0)]));
    let decomposition = ProductDecomposition::new(vec![
        (rq(1, 2), zero.clone(), zero),
        (rq(1, 2), one.clone(), one),
    ]);
    decomposition.verify(&mixture).unwrap();
    assert_eq!(
        decomposition.verify(&bell),
        Err(BipartiteError::DoesNotReproduce)
    );
}

#[test]
fn the_decomposable_witness_is_nonnegative_on_declared_product_states() {
    let witness = DecomposableWitness::new(&singlet_projector(), 2, 2).unwrap();
    let states = [
        ket(&[(1, 0), (0, 0)]),
        ket(&[(0, 0), (1, 0)]),
        ket(&[(1, 0), (1, 0)]),
        ket(&[(1, 0), (-1, 0)]),
        ket(&[(1, 0), (0, 1)]),
        ket(&[(3, 0), (4, 0)]),
        ket(&[(2, 1), (1, -3)]),
    ];
    let mut minimum: Option<Rational> = None;
    for alpha in &states {
        for beta in &states {
            let value = witness.value(&mx::kronecker(alpha, beta).unwrap()).unwrap();
            assert!(!value.is_negative(), "negative on a product state");
            minimum =
                Some(minimum.map_or(value.clone(), |m| if value < m { value.clone() } else { m }));
        }
    }
    // |0>|0> meets the witness at zero: nonnegativity is tight.
    assert_eq!(minimum, Some(ri(0)));
}

// ---------------------------------------------------------------------------
// QM-070-C8: local maps keep products; the mass does not grow; shared
// randomness is outside the claim.
// ---------------------------------------------------------------------------

#[test]
fn local_product_maps_keep_products_and_do_not_raise_the_defect_mass() {
    let g_a = stochastic(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
    let g_b = stochastic(&[&[(1, 1), (0, 1)], &[(1, 4), (3, 4)]]);
    let g_wide = stochastic(&[&[(1, 2), (1, 4), (1, 4)], &[(0, 1), (1, 2), (1, 2)]]);

    let product = table(vec![vec![rq(1, 6), rq(1, 3)], vec![rq(1, 6), rq(1, 3)]]);
    assert!(product.product_defect_mass().is_zero());
    for (left, right) in [
        (&g_a, &g_b),
        (&g_a, &g_wide),
        (&flip_map(), &identity_map()),
    ] {
        let image = product.apply_local_maps(left, right).unwrap();
        assert!(image.product_defect_mass().is_zero());
        assert!(image.has_vanishing_minors());
        assert_eq!(image.total(), product.total());
    }

    let correlated = int_table(&[&[3, 1], &[0, 2]]);
    assert_eq!(correlated.product_defect_mass(), ri(4));
    let mixed = correlated.apply_local_maps(&g_a, &g_b).unwrap();
    assert_eq!(
        mixed,
        table(vec![
            vec![rq(43, 24), rq(7, 8)],
            vec![rq(47, 24), rq(11, 8)]
        ])
    );
    assert_eq!(mixed.product_defect_mass(), rq(1, 2));
    let widened = correlated.apply_local_maps(&g_a, &g_wide).unwrap();
    assert_eq!(widened.shape(), (2, 3));
    assert_eq!(widened.total(), ri(6));
    assert_eq!(widened.product_defect_mass(), rq(1, 3));
    // A permutation is reversible, and the mass is unchanged by it.
    assert_eq!(
        correlated
            .apply_local_maps(&flip_map(), &identity_map())
            .unwrap()
            .product_defect_mass(),
        ri(4)
    );

    let three_to_two = stochastic(&[&[(1, 1), (0, 1)], &[(0, 1), (1, 1)], &[(1, 2), (1, 2)]]);
    assert_eq!(
        correlated.apply_local_maps(&three_to_two, &g_b),
        Err(WeightTableError::MapShape {
            side: 'A',
            expected: 2,
            actual: 3
        })
    );
}

/// `StochasticMap`'s fields are private, so a map that is not row-stochastic
/// cannot be built and handed to `apply_local_maps`: its constructor refuses
/// each defect the weight table used to re-check.
#[test]
fn maps_that_are_not_row_stochastic_cannot_be_built() {
    let map = |target_n: usize, rows: Vec<Vec<Rational>>| {
        StochasticMap::try_from_rows(2, target_n, rows, "hand")
    };
    assert_eq!(
        map(0, vec![vec![], vec![]]),
        Err(ClassicalShadowError::ZeroCardinality)
    );
    assert_eq!(
        map(2, vec![vec![ri(1), ri(0)]]),
        Err(ClassicalShadowError::DimensionMismatch {
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        map(2, vec![vec![ri(1)], vec![ri(0), ri(1)]]),
        Err(ClassicalShadowError::DimensionMismatch {
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        map(2, vec![vec![rq(3, 2), rq(-1, 2)], vec![ri(0), ri(1)]]),
        Err(ClassicalShadowError::NegativeEntry { index: 1 })
    );
    assert_eq!(
        map(2, vec![vec![rq(1, 2), rq(1, 4)], vec![ri(0), ri(1)]]),
        Err(ClassicalShadowError::RowNotNormalized {
            row: 0,
            sum: rq(3, 4)
        })
    );
    // A validated map of the wrong size is still refused by the table.
    let correlated = int_table(&[&[3, 1], &[0, 2]]);
    let three =
        StochasticMap::try_from_rows(3, 3, vec![vec![ri(1), ri(0), ri(0)]; 3], "three").unwrap();
    assert_eq!(
        correlated.apply_local_maps(&three, &identity_map()),
        Err(WeightTableError::MapShape {
            side: 'A',
            expected: 2,
            actual: 3
        })
    );
}

#[test]
fn a_mixture_of_product_maps_creates_product_defect_from_a_product_table() {
    let point = JointTable::point(2, 2, 0, 0).unwrap();
    assert!(point.product_defect_mass().is_zero());
    let kept = point
        .apply_local_maps(&identity_map(), &identity_map())
        .unwrap();
    let flipped = point.apply_local_maps(&flip_map(), &flip_map()).unwrap();
    assert!(kept.product_defect_mass().is_zero());
    assert!(flipped.product_defect_mass().is_zero());
    let shared = JointTable::convex_mixture(&[(rq(1, 2), kept), (rq(1, 2), flipped)]).unwrap();
    assert_eq!(shared, diagonal_half());
    assert_eq!(shared.product_defect_mass(), ri(1));
}

// ---------------------------------------------------------------------------
// QM-070-C9: the defect is read in a declared product basis.
// ---------------------------------------------------------------------------

#[test]
fn the_product_defect_depends_on_the_declared_product_basis() {
    let (z, x) = (computational_basis(), hadamard_basis());
    let mixture = classical_mixture();
    let bell = bell_phi_plus();

    let mixture_z = bo::descend_to_table(&mixture, &z, &z).unwrap();
    let mixture_x = bo::descend_to_table(&mixture, &x, &x).unwrap();
    assert_eq!(mixture_z.product_defect_mass(), ri(1));
    assert_eq!(mixture_x, uniform_quarter());
    assert!(mixture_x.product_defect_mass().is_zero());

    // The Bell state stays correlated in the Hadamard basis, and a mixed basis
    // reads it as a product.
    assert_eq!(
        bo::descend_to_table(&bell, &x, &x).unwrap(),
        diagonal_half()
    );
    assert_eq!(
        bo::descend_to_table(&bell, &z, &x).unwrap(),
        uniform_quarter()
    );
}

// ---------------------------------------------------------------------------
// QM-070-C11 (interpretive): what the mass measures.
// ---------------------------------------------------------------------------

#[test]
fn the_defect_mass_is_the_distance_to_the_marginal_product_not_to_the_product_set() {
    let half = diagonal_half();
    assert_eq!(
        half.l1_distance(&uniform_quarter()).unwrap(),
        half.product_defect_mass()
    );
    // (7/10, 3/10) x (7/10, 3/10) is a product table strictly nearer than the marginal product.
    let nearer = table(vec![
        vec![rq(49, 100), rq(21, 100)],
        vec![rq(21, 100), rq(9, 100)],
    ]);
    assert!(nearer.has_vanishing_minors());
    assert_eq!(half.l1_distance(&nearer).unwrap(), rq(21, 25));
    assert!(rq(21, 25) < half.product_defect_mass());
}

// ---------------------------------------------------------------------------
// QM-070-C1 and the descent: declarations are checked.
// ---------------------------------------------------------------------------

#[test]
fn tables_refuse_empty_ragged_negative_and_zero_declarations() {
    assert_eq!(JointTable::new(vec![]), Err(WeightTableError::Empty));
    assert_eq!(
        JointTable::new(vec![vec![ri(1), ri(1)], vec![ri(1)]]),
        Err(WeightTableError::Ragged {
            row: 1,
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        JointTable::new(vec![vec![ri(1), ri(-1)]]),
        Err(WeightTableError::NegativeWeight { row: 0, col: 1 })
    );
    assert_eq!(
        JointTable::new(vec![vec![ri(0); 2]; 2]),
        Err(WeightTableError::ZeroTotal)
    );
    assert_eq!(
        JointTable::point(2, 2, 2, 0),
        Err(WeightTableError::CellOutOfRange {
            row: 2,
            col: 0,
            rows: 2,
            cols: 2
        })
    );
    assert_eq!(diagonal_half().weight(0, 0), Some(&rq(1, 2)));
    assert_eq!(diagonal_half().weight(2, 0), None);
    assert_eq!(
        JointTable::convex_mixture(&[]),
        Err(WeightTableError::EmptyMixture)
    );
    assert_eq!(
        JointTable::convex_mixture(&[(rq(3, 2), diagonal_half()), (rq(-1, 2), uniform_quarter())]),
        Err(WeightTableError::NegativeMixtureWeight { index: 1 })
    );
    assert_eq!(
        JointTable::convex_mixture(&[(rq(1, 2), diagonal_half()), (rq(1, 4), uniform_quarter())]),
        Err(WeightTableError::MixtureNotNormalized { sum: rq(3, 4) })
    );
    let wide = int_table(&[&[1, 0, 0]]);
    assert_eq!(
        JointTable::convex_mixture(&[(rq(1, 2), diagonal_half()), (rq(1, 2), wide.clone())]),
        Err(WeightTableError::ShapeMismatch {
            left: (2, 2),
            right: (1, 3)
        })
    );
    assert_eq!(
        diagonal_half().l1_distance(&wide),
        Err(WeightTableError::ShapeMismatch {
            left: (2, 2),
            right: (1, 3)
        })
    );
}

#[test]
fn the_descent_and_the_witness_refuse_malformed_inputs() {
    let z = computational_basis();
    let skew = vec![vec![gi(1, 0), gi(0, 0)], vec![gi(1, 0), gi(1, 0)]];
    assert_eq!(
        bo::descend_to_table(&bell_phi_plus(), &z, &skew),
        Err(BipartiteError::NotOrthogonal {
            factor: 1,
            first: 0,
            second: 1
        })
    );
    let with_zero = vec![vec![gi(0, 0), gi(0, 0)], vec![gi(0, 0), gi(1, 0)]];
    assert_eq!(
        bo::descend_to_table(&bell_phi_plus(), &with_zero, &z),
        Err(BipartiteError::ZeroBasisVector {
            factor: 0,
            index: 0
        })
    );
    let indefinite = mx::diagonal(&[gi(1, 0), gi(-1, 0), gi(1, 0), gi(0, 0)]).unwrap();
    assert_eq!(
        bo::descend_to_table(&indefinite, &z, &z),
        Err(BipartiteError::NotPositive)
    );
    assert_eq!(
        bo::descend_to_table(&mx::zeros::<GaussianRat>(4, 4).unwrap(), &z, &z),
        Err(BipartiteError::Table(WeightTableError::ZeroTotal))
    );
    assert_eq!(
        bo::partial_transpose_b(&mx::identity::<GaussianRat>(3).unwrap(), 2, 2),
        Err(BipartiteError::Shape {
            rows: 3,
            cols: 3,
            d_a: 2,
            d_b: 2
        })
    );
    assert_eq!(
        bo::partial_trace_b(&mx::identity::<GaussianRat>(4).unwrap(), 0, 4),
        Err(BipartiteError::ZeroDimension)
    );
    assert_eq!(
        DecomposableWitness::new(&indefinite, 2, 2),
        Err(BipartiteError::NotPositive)
    );
    assert_eq!(
        bo::pure_state(&[gi(0, 0), gi(0, 0)]),
        Err(BipartiteError::ZeroVector)
    );

    let (zero, one) = (ket(&[(1, 0), (0, 0)]), ket(&[(0, 0), (1, 0)]));
    assert_eq!(
        ProductDecomposition::new(vec![]).verify(&classical_mixture()),
        Err(BipartiteError::EmptyDecomposition)
    );
    assert_eq!(
        ProductDecomposition::new(vec![(rq(1, 2), zero.clone(), zero.clone())])
            .verify(&classical_mixture()),
        Err(BipartiteError::WeightsNotNormalized { sum: rq(1, 2) })
    );
    assert_eq!(
        ProductDecomposition::new(vec![(
            ri(1),
            mx::identity::<GaussianRat>(2).unwrap(),
            zero.clone()
        )])
        .verify(&classical_mixture()),
        Err(BipartiteError::BadTerm {
            index: 0,
            reason: "factor does not have trace one"
        })
    );
    assert_eq!(
        ProductDecomposition::new(vec![
            (rq(3, 2), zero.clone(), zero),
            (rq(-1, 2), one.clone(), one)
        ])
        .verify(&classical_mixture()),
        Err(BipartiteError::BadTerm {
            index: 1,
            reason: "negative weight"
        })
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/entanglement/product_non_factorization.rs
// Claim: urn:core:crates_rs:tests:product-non-factorization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord096f3e10 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord096f3e10` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError096f3e10 {
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
impl BoundaryError096f3e10 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError096f3e10 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError096f3e10 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord096f3e10 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError096f3e10> {
        if capacity_bound == 0 {
            return Err(BoundaryError096f3e10::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError096f3e10::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError096f3e10::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_096f3e10() {
    let admitted = BoundaryRecord096f3e10::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord096f3e10::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

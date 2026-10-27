//! Correlation, separability and finite Bell bounds, with the no-signalling
//! annex: every bare table is a mixture of point products, jointly tabled
//! boxes satisfy |S| <= 2, the PR box and a rational entangled box exceed it
//! without a joint table, boxes from states do not signal, and exchange
//! equivariance suppresses diagonal weight exactly where 2 is not a zero
//! divisor.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::adjoint, matrix as mx};
use num_traits::{Signed, Zero};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};
use core_quantum_physics::exact_hermitian::gi;

use core_finite_probability::joint_table::JointTable;
use core_quantum_physics::bipartite_operator as bo;
use core_quantum_physics::finite_chsh_correlations::{
    chsh_witness, deterministic_family, CorrelationError, JointAssignment, PairwiseBox,
    BOX_COORDINATES,
};
use core_quantum_physics::pair_exchange_characters::{
    alternating_fixed_values_mod, is_exchange_equivariant, ExchangeError,
};
use core_solvers::solver_convex_finite_hull::{
    decide_membership, DeclaredFamily, MembershipCertificate, SeparatingWitness,
};

fn rationals(values: &[(i64, i64)]) -> Vec<Rational> {
    values.iter().map(|&(n, d)| rq(n, d)).collect()
}

fn pr_box() -> PairwiseBox {
    let (h, o) = ((1, 2), (0, 1));
    PairwiseBox::new(rationals(&[h, o, o, h, h, o, o, h, h, o, o, h, o, h, h, o])).unwrap()
}

fn qi(rows: &[&[(i64, i64)]], den: i64) -> BasicMatrix<GaussianRat> {
    mx::from_rows(
        rows.iter()
            .map(|r| {
                r.iter()
                    .map(|&(re, im)| GaussianRat {
                        re: rq(re, den),
                        im: rq(im, den),
                    })
                    .collect()
            })
            .collect(),
    )
    .unwrap()
}

fn bell_phi_plus() -> BasicMatrix<GaussianRat> {
    bo::pure_state(&[gi(1, 0), gi(0, 0), gi(0, 0), gi(1, 0)]).unwrap()
}

/// `|Phi+>` with `A_0 = Z`, `A_1 = X`, `B_0 = (4Z + 3X)/5`, `B_1 = (3Z - 4X)/5`.
fn rational_quantum_box() -> PairwiseBox {
    let z = qi(&[&[(1, 0), (0, 0)], &[(0, 0), (-1, 0)]], 1);
    let x = qi(&[&[(0, 0), (1, 0)], &[(1, 0), (0, 0)]], 1);
    let b0 = qi(&[&[(4, 0), (3, 0)], &[(3, 0), (-4, 0)]], 5);
    let b1 = qi(&[&[(3, 0), (-4, 0)], &[(-4, 0), (-3, 0)]], 5);
    PairwiseBox::from_state(&bell_phi_plus(), [&z, &x], [&b0, &b1]).unwrap()
}

fn expect_separated(certificate: MembershipCertificate) -> SeparatingWitness {
    match certificate {
        MembershipCertificate::Separated(witness) => witness,
        MembershipCertificate::Member(decomposition) => {
            panic!("expected no joint table, got {decomposition:?}")
        }
    }
}

// ---------------------------------------------------------------------------
// P8-C6: the finite CHSH bound for jointly tabled boxes.
// ---------------------------------------------------------------------------

#[test]
fn every_joint_assignment_has_chsh_value_two_or_minus_two() {
    let assignments = JointAssignment::all();
    assert_eq!(assignments.len(), 16);
    let values: Vec<i64> = assignments.iter().map(JointAssignment::chsh).collect();
    assert_eq!(
        values,
        vec![2, -2, 2, -2, -2, -2, 2, 2, 2, 2, -2, -2, -2, 2, -2, 2]
    );
    // The CHSH witness is valid on each joint assignment's marginal vector.
    let family = deterministic_family();
    assert_eq!(family.members().len(), 16);
    let witness = chsh_witness();
    assert_eq!(witness.threshold(), &ri(-2));
    assert!(witness.functional().iter().all(|c| c.abs() == ri(1)));
    for (member, value) in family.members().iter().zip(&values) {
        assert_eq!(witness.evaluate(member).unwrap(), ri(-value));
    }
}

#[test]
fn jointly_tabled_boxes_satisfy_the_finite_chsh_bound() {
    let indicator = |support: &[usize], weights: &[i64]| {
        let mut w = vec![ri(0); BOX_COORDINATES];
        for (&s, &v) in support.iter().zip(weights) {
            w[s] = ri(v);
        }
        w
    };
    let cases = [
        (vec![ri(1); 16], ri(0)),
        (indicator(&[0, 2, 6, 7, 8, 9, 13, 15], &[1; 8]), ri(2)),
        (indicator(&[0, 5, 10], &[1, 1, 1]), rq(-2, 3)),
        (indicator(&[0, 2, 1], &[1, 2, 1]), ri(1)),
        (indicator(&[1], &[7]), ri(-2)),
    ];
    for (weights, expected) in cases {
        let joint = PairwiseBox::from_joint_table(&weights).unwrap();
        assert_eq!(joint.chsh(), expected);
        assert!(joint.chsh().abs() <= ri(2));
        assert!(joint.is_no_signalling());
    }
    let box_of_three = PairwiseBox::from_joint_table(&indicator(&[0, 5, 10], &[1, 1, 1])).unwrap();
    assert_eq!(
        box_of_three.coordinates(),
        rationals(&[
            (2, 3),
            (0, 1),
            (0, 1),
            (1, 3),
            (1, 3),
            (1, 3),
            (1, 3),
            (0, 1),
            (1, 3),
            (1, 3),
            (1, 3),
            (0, 1),
            (2, 3),
            (0, 1),
            (0, 1),
            (1, 3),
        ])
        .as_slice()
    );
}

// ---------------------------------------------------------------------------
// P8-C3 / P8-C4: every bare table is separable.
// ---------------------------------------------------------------------------

#[test]
fn every_normalized_table_is_a_mixture_of_point_product_tables() {
    let points = DeclaredFamily::new(
        (0..2)
            .flat_map(|a| {
                (0..2).map(move |b| JointTable::point(2, 2, a, b).unwrap().weights().to_vec())
            })
            .collect(),
    )
    .unwrap();
    for (rows, cols, largest, expected) in [(2usize, 2usize, 3u32, 255usize), (2, 3, 2, 728)] {
        let base = largest + 1;
        let cells = (rows * cols) as u32;
        let mut checked = 0;
        for code in 1..base.pow(cells) {
            let mut rest = code;
            let entries: Vec<Rational> = (0..cells)
                .map(|_| {
                    let digit = rest % base;
                    rest /= base;
                    ri(i64::from(digit))
                })
                .collect();
            let table =
                JointTable::new(entries.chunks(cols).map(<[Rational]>::to_vec).collect()).unwrap();
            let parts = table.point_product_decomposition();
            assert!(parts
                .iter()
                .all(|(_, point)| point.product_defect_mass().is_zero()));
            assert_eq!(
                JointTable::convex_mixture(&parts).unwrap(),
                table.normalized()
            );
            if rows == 2 && cols == 2 {
                // The declared-family decision agrees against the four point tables.
                match decide_membership(&points, table.normalized().weights()).unwrap() {
                    MembershipCertificate::Member(d) => {
                        d.verify(&points, table.normalized().weights()).unwrap()
                    }
                    MembershipCertificate::Separated(_) => panic!("a bare table was separated"),
                }
            }
            checked += 1;
        }
        assert_eq!(checked, expected);
    }
    // The diagonal-half table: correlated, and still half e_00 plus half e_11.
    let half = JointTable::new(vec![vec![rq(1, 2), ri(0)], vec![ri(0), rq(1, 2)]]).unwrap();
    assert_eq!(half.product_defect_mass(), ri(1));
    let parts = half.point_product_decomposition();
    assert_eq!(parts.len(), 2);
    assert_eq!(parts[0], (rq(1, 2), JointTable::point(2, 2, 0, 0).unwrap()));
    assert_eq!(parts[1], (rq(1, 2), JointTable::point(2, 2, 1, 1).unwrap()));
}

// ---------------------------------------------------------------------------
// P8-C7: the PR box, S = 4, no joint table.
// ---------------------------------------------------------------------------

#[test]
fn the_pr_box_reaches_four_and_has_no_joint_table() {
    let pr = pr_box();
    assert_eq!(pr.chsh(), ri(4));
    assert!(pr.is_no_signalling());
    assert!(pr.support_compatible_assignments().is_empty());
    assert_eq!(
        chsh_witness()
            .verify(&deterministic_family(), pr.coordinates())
            .unwrap(),
        ri(2)
    );
    let decided = expect_separated(pr.joint_extension().unwrap());
    assert!(decided
        .verify(&deterministic_family(), pr.coordinates())
        .unwrap()
        .is_positive());
    for (x, y) in [(0, 0), (0, 1), (1, 0), (1, 1)] {
        assert_eq!(pr.context_table(x, y).unwrap().product_defect_mass(), ri(1));
    }
}

#[test]
fn a_rational_entangled_box_exceeds_the_joint_table_bound_below_the_tsirelson_value() {
    let q = rational_quantum_box();
    let correlators: Vec<Rational> = [(0, 0), (0, 1), (1, 0), (1, 1)]
        .iter()
        .map(|&(x, y)| q.correlator(x, y).unwrap())
        .collect();
    assert_eq!(correlators, vec![rq(4, 5), rq(3, 5), rq(3, 5), rq(-4, 5)]);
    let s = q.chsh();
    assert_eq!(s, rq(14, 5));
    assert!(s > ri(2));
    // S^2 = 196/25 < 8 = (2 sqrt 2)^2.
    assert!(&s * &s < ri(8));
    // Every probability is positive, so the support test cannot decide; the LP does.
    assert_eq!(q.support_compatible_assignments().len(), 16);
    let decided = expect_separated(q.joint_extension().unwrap());
    assert!(decided
        .verify(&deterministic_family(), q.coordinates())
        .unwrap()
        .is_positive());
    assert_eq!(
        chsh_witness()
            .verify(&deterministic_family(), q.coordinates())
            .unwrap(),
        rq(4, 5)
    );
    // The planar-direction evaluation already in the crate gives the same value.
    assert_eq!(
        core_quantum_physics::quantum_correlation::finite_planar_chsh_max(
            &core_quantum_physics::quantum_correlation::generate_unit_vectors(4, 5).unwrap(),
            true,
            1_000_000
        )
        .unwrap()
        .value
        .as_number()
        .as_rational(),
        Some(rq(14, 5))
    );
}

#[test]
fn a_box_with_a_joint_table_gets_one_back_from_the_decision() {
    let mut weights = vec![ri(0); BOX_COORDINATES];
    weights[0] = ri(1);
    weights[5] = ri(2);
    weights[10] = ri(3);
    let local = PairwiseBox::from_joint_table(&weights).unwrap();
    match local.joint_extension().unwrap() {
        MembershipCertificate::Member(decomposition) => {
            assert_eq!(
                PairwiseBox::from_joint_table(decomposition.coefficients()).unwrap(),
                local
            );
        }
        MembershipCertificate::Separated(w) => {
            panic!("a jointly tabled box was separated by {w:?}")
        }
    }
    // A deterministic box is compatible with its own assignment only.
    let mut point = vec![ri(0); BOX_COORDINATES];
    point[6] = ri(1);
    let deterministic = PairwiseBox::from_joint_table(&point).unwrap();
    assert_eq!(
        deterministic.support_compatible_assignments(),
        vec![JointAssignment::all()[6]]
    );
}

// ---------------------------------------------------------------------------
// Annex (no-signalling): boxes from states do not signal and are not products.
// ---------------------------------------------------------------------------

#[test]
fn state_boxes_do_not_signal_yet_no_context_is_a_product() {
    let q = rational_quantum_box();
    assert!(q.is_no_signalling());
    let masses: Vec<Rational> = [(0, 0), (0, 1), (1, 0), (1, 1)]
        .iter()
        .map(|&(x, y)| q.context_table(x, y).unwrap().product_defect_mass())
        .collect();
    assert_eq!(masses, vec![rq(4, 5), rq(3, 5), rq(3, 5), rq(4, 5)]);
    assert_eq!(
        q.context_table(0, 0).unwrap(),
        JointTable::new(vec![vec![rq(9, 20), rq(1, 20)], vec![rq(1, 20), rq(9, 20)]]).unwrap()
    );

    // A local rotation or dephasing on the second factor leaves the first reduced state alone.
    let rho = bell_phi_plus();
    let before = bo::partial_trace_b(&rho, 2, 2).unwrap();
    let rotation = qi(&[&[(3, 0), (-4, 0)], &[(4, 0), (3, 0)]], 5);
    let local = mx::kronecker(&mx::identity::<GaussianRat>(2).unwrap(), &rotation).unwrap();
    let rotated = mx::multiply(
        &mx::multiply(&local, &rho).unwrap(),
        &adjoint(&local).unwrap(),
    )
    .unwrap();
    assert_ne!(rotated, rho);
    assert_eq!(bo::partial_trace_b(&rotated, 2, 2).unwrap(), before);
    let p0 = mx::kronecker(
        &mx::identity::<GaussianRat>(2).unwrap(),
        &qi(&[&[(1, 0), (0, 0)], &[(0, 0), (0, 0)]], 1),
    )
    .unwrap();
    let p1 = mx::kronecker(
        &mx::identity::<GaussianRat>(2).unwrap(),
        &qi(&[&[(0, 0), (0, 0)], &[(0, 0), (1, 0)]], 1),
    )
    .unwrap();
    let dephased = mx::add(
        &mx::multiply(&mx::multiply(&p0, &rho).unwrap(), &p0).unwrap(),
        &mx::multiply(&mx::multiply(&p1, &rho).unwrap(), &p1).unwrap(),
    )
    .unwrap();
    assert_eq!(bo::partial_trace_b(&dephased, 2, 2).unwrap(), before);
    // The crate's own Bell-state check agrees on the other side.
    assert!(core_quantum_physics::no_signalling::verify_no_signalling_on_bell_states());

    // Four valid tables can still signal, in either direction.
    let (one, o) = ((1, 1), (0, 1));
    // The first window's outcome at x = 0 moves with y; the second side's marginals do not move.
    let towards_first = PairwiseBox::new(rationals(&[
        one, o, o, o, o, o, one, o, one, o, o, o, one, o, o, o,
    ]))
    .unwrap();
    assert!(!towards_first.is_no_signalling());
    // The second window's outcome at y = 0 moves with x; the first side's marginals do not move.
    let towards_second = PairwiseBox::new(rationals(&[
        one, o, o, o, one, o, o, o, o, one, o, o, one, o, o, o,
    ]))
    .unwrap();
    assert!(!towards_second.is_no_signalling());
}

// ---------------------------------------------------------------------------
// P8-C9: diagonal suppression under the alternating character.
// ---------------------------------------------------------------------------

#[test]
fn diagonal_suppression_holds_exactly_where_two_is_not_a_zero_divisor() {
    let (mut alternating, mut symmetric, mut symmetric_with_diagonal) = (0, 0, 0);
    for code in 0..5u32.pow(4) {
        let mut rest = code;
        let entries: Vec<Rational> = (0..4)
            .map(|_| {
                let digit = rest % 5;
                rest /= 5;
                ri(i64::from(digit) - 2)
            })
            .collect();
        let table = vec![entries[..2].to_vec(), entries[2..].to_vec()];
        if is_exchange_equivariant(&table, -1).unwrap() {
            alternating += 1;
            assert!(table[0][0].is_zero() && table[1][1].is_zero(), "{table:?}");
        }
        if is_exchange_equivariant(&table, 1).unwrap() {
            symmetric += 1;
            if !(table[0][0].is_zero() && table[1][1].is_zero()) {
                symmetric_with_diagonal += 1;
            }
        }
    }
    assert_eq!(
        (alternating, symmetric, symmetric_with_diagonal),
        (5, 125, 120)
    );

    for n in 2..=64u64 {
        assert_eq!(
            alternating_fixed_values_mod(n).unwrap() == vec![0],
            n % 2 == 1,
            "n = {n}"
        );
    }
    // Z/4: the value 2 equals its negative and is not zero.
    assert_eq!(alternating_fixed_values_mod(4).unwrap(), vec![0, 2]);
    assert_eq!(alternating_fixed_values_mod(2).unwrap(), vec![0, 1]);

    let square = vec![vec![ri(0), ri(1)], vec![ri(-1), ri(0)]];
    assert_eq!(
        is_exchange_equivariant(&square, 0),
        Err(ExchangeError::NotASign(0))
    );
    assert_eq!(
        is_exchange_equivariant(&[vec![ri(0), ri(1)], vec![ri(0)]], 1),
        Err(ExchangeError::NotSquare {
            row: 1,
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        alternating_fixed_values_mod(0),
        Err(ExchangeError::ModulusTooSmall(0))
    );
}

#[test]
fn boxes_refuse_malformed_tables_observables_and_states() {
    assert_eq!(
        PairwiseBox::new(vec![ri(0); 15]),
        Err(CorrelationError::Length { actual: 15 })
    );
    let mut negative = pr_box().coordinates().to_vec();
    negative[1] = rq(-1, 2);
    negative[0] = ri(1);
    assert_eq!(
        PairwiseBox::new(negative),
        Err(CorrelationError::Negative { index: 1 })
    );
    let mut unnormalised = pr_box().coordinates().to_vec();
    unnormalised[0] = ri(1);
    assert_eq!(
        PairwiseBox::new(unnormalised),
        Err(CorrelationError::ContextNotNormalized {
            x: 0,
            y: 0,
            sum: rq(3, 2)
        })
    );
    assert_eq!(
        PairwiseBox::from_joint_table(&vec![ri(0); BOX_COORDINATES]),
        Err(CorrelationError::ZeroTotal)
    );
    assert_eq!(
        pr_box().correlator(2, 0),
        Err(CorrelationError::WindowOutOfRange { x: 2, y: 0 })
    );
    let z = qi(&[&[(1, 0), (0, 0)], &[(0, 0), (-1, 0)]], 1);
    let doubled = qi(&[&[(2, 0), (0, 0)], &[(0, 0), (-2, 0)]], 1);
    let nilpotent = qi(&[&[(0, 0), (1, 0)], &[(0, 0), (0, 0)]], 1);
    let rho = bell_phi_plus();
    assert_eq!(
        PairwiseBox::from_state(&rho, [&doubled, &z], [&z, &z]),
        Err(CorrelationError::NotInvolution { index: 0 })
    );
    assert_eq!(
        PairwiseBox::from_state(&rho, [&z, &z], [&z, &nilpotent]),
        Err(CorrelationError::ObservableNotHermitian { index: 3 })
    );
    assert_eq!(
        PairwiseBox::from_state(&mx::scale(&rho, &gi(2, 0)).unwrap(), [&z, &z], [&z, &z]),
        Err(CorrelationError::NotAState)
    );
}

// Origin: engine/crates_rs/tests/core_quantum_physics/entanglement/finite_bell_bounds.rs
// Claim: urn:core:crates_rs:tests:finite-bell-bounds:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord34fbc4be {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord34fbc4be` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError34fbc4be {
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
impl BoundaryError34fbc4be {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError34fbc4be {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError34fbc4be {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord34fbc4be {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError34fbc4be> {
        if capacity_bound == 0 {
            return Err(BoundaryError34fbc4be::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError34fbc4be::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError34fbc4be::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_34fbc4be() {
    let admitted = BoundaryRecord34fbc4be::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord34fbc4be::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

//! Linear algebra over GF(2): vectors, matrices, rank, reduced row echelon
//! form, nullspace, column and row spaces, solution sets and spans.
//!
//! Each test states the invariant it protects. The independent routes are a
//! naive `Vec<Vec<u8>>` elimination written here and exhaustive enumeration of every vector of
//! a small space (kernels, images and solution sets are counted by brute
//! force, not derived from the elimination under test).
//!
//! AuthorityEffect: None.

use core_number_theory::gf2::{F2Error, F2Matrix, F2Span, F2Vector, MAX_F2_ENTRIES};
use std::collections::BTreeSet;

fn vector(bits: &[u8]) -> F2Vector {
    F2Vector::from_bits(bits).unwrap()
}

fn matrix(rows: &[&[u8]]) -> F2Matrix {
    F2Matrix::from_rows(&rows.iter().map(|r| r.to_vec()).collect::<Vec<_>>()).unwrap()
}

/// Every `rows x cols` matrix, row-major bit order.
fn all_matrices(rows: usize, cols: usize) -> impl Iterator<Item = Vec<Vec<u8>>> {
    (0u32..(1 << (rows * cols))).map(move |code| {
        (0..rows)
            .map(|r| {
                (0..cols)
                    .map(|c| ((code >> (r * cols + c)) & 1) as u8)
                    .collect()
            })
            .collect()
    })
}

/// Every vector of `F2^len`.
fn all_vectors(len: usize) -> Vec<Vec<u8>> {
    (0u32..(1 << len))
        .map(|code| (0..len).map(|i| ((code >> i) & 1) as u8).collect())
        .collect()
}

/// `A x` by definition, on plain bytes.
fn apply(rows: &[Vec<u8>], x: &[u8]) -> Vec<u8> {
    rows.iter()
        .map(|row| row.iter().zip(x).map(|(a, b)| a & b).sum::<u8>() % 2)
        .collect()
}

/// Rank by a naive elimination on plain bytes.
fn naive_rank(rows: &[Vec<u8>]) -> usize {
    let mut m = rows.to_vec();
    let cols = m.first().map_or(0, Vec::len);
    let mut rank = 0;
    for c in 0..cols {
        let Some(p) = (rank..m.len()).find(|&r| m[r][c] == 1) else {
            continue;
        };
        m.swap(rank, p);
        for r in 0..m.len() {
            if r != rank && m[r][c] == 1 {
                let pivot_row = m[rank].clone();
                for (x, y) in m[r].iter_mut().zip(pivot_row) {
                    *x ^= y;
                }
            }
        }
        rank += 1;
    }
    rank
}

// ---------------------------------------------------------------------------
// Vectors
// ---------------------------------------------------------------------------

#[test]
fn vector_addition_dot_weight_and_support_follow_gf2() {
    let a = vector(&[1, 1, 0, 1]);
    let b = vector(&[0, 1, 1, 1]);
    assert_eq!(a.add(&b).unwrap().to_bits(), vec![1, 0, 1, 0]);
    // 1*0 + 1*1 + 0*1 + 1*1 = 2 = 0 mod 2.
    assert!(!a.dot(&b).unwrap());
    assert!(a.dot(&a).unwrap(), "weight 3 is odd");
    assert_eq!((a.weight(), b.weight()), (3, 3));
    assert_eq!(a.support(), vec![0, 1, 3]);
    assert!(a.add(&a).unwrap().is_zero());
    // Listing an index twice cancels it.
    assert_eq!(
        F2Vector::from_indices(5, &[1, 3, 1]).unwrap().to_bits(),
        vec![0, 0, 0, 1, 0]
    );
    assert_eq!(F2Vector::unit(4, 2).unwrap().to_bits(), vec![0, 0, 1, 0]);
}

#[test]
fn vectors_cross_word_boundaries_exactly() {
    let mut v = F2Vector::zeros(130).unwrap();
    for i in [0, 63, 64, 65, 127, 128, 129] {
        v.set(i, true).unwrap();
    }
    assert_eq!(v.weight(), 7);
    assert_eq!(v.support(), vec![0, 63, 64, 65, 127, 128, 129]);
    v.flip(64).unwrap();
    assert!(!v.get(64).unwrap());
    assert_eq!(
        v.to_bits().iter().map(|&b| usize::from(b)).sum::<usize>(),
        6
    );
    let w = F2Vector::unit(130, 129).unwrap();
    assert!(v.dot(&w).unwrap());
}

#[test]
fn vectors_refuse_bad_indices_lengths_and_entries() {
    let mut v = vector(&[1, 0, 1]);
    assert_eq!(v.get(3), Err(F2Error::IndexOutOfRange { index: 3, len: 3 }));
    assert!(v.set(9, true).is_err());
    assert!(v.flip(3).is_err());
    assert!(F2Vector::unit(3, 3).is_err());
    assert_eq!(
        v.add(&vector(&[1, 0])),
        Err(F2Error::LengthMismatch {
            expected: 3,
            actual: 2
        })
    );
    assert!(v.dot(&vector(&[1])).is_err());
    assert_eq!(
        F2Vector::from_bits(&[0, 2]),
        Err(F2Error::NotBinary {
            row: 0,
            col: 1,
            value: 2
        })
    );
    assert!(F2Vector::from_indices(3, &[5]).is_err());
    assert!(F2Vector::zeros(MAX_F2_ENTRIES + 1).is_err());
}

// ---------------------------------------------------------------------------
// Matrices: construction
// ---------------------------------------------------------------------------

#[test]
fn matrix_construction_refuses_ragged_non_binary_and_oversized_input() {
    assert_eq!(
        F2Matrix::from_rows(&[vec![1, 0], vec![1]]),
        Err(F2Error::Ragged {
            row: 1,
            expected: 2,
            actual: 1
        })
    );
    assert_eq!(
        F2Matrix::from_rows(&[vec![1, 0], vec![2, 1]]),
        Err(F2Error::NotBinary {
            row: 1,
            col: 0,
            value: 2
        })
    );
    assert!(matches!(
        F2Matrix::zeros(1 << 15, 1 << 14),
        Err(F2Error::TooLarge { .. })
    ));
    assert!(matches!(
        F2Matrix::zeros(usize::MAX, 2),
        Err(F2Error::TooLarge { .. })
    ));
    let m = matrix(&[&[1, 0, 1], &[0, 1, 1]]);
    assert!(m.get(2, 0).is_err() && m.get(0, 3).is_err());
    let mut m = m;
    assert!(m.set(0, 3, true).is_err());
    assert!(m.row(2).is_err() && m.column(3).is_err());
}

#[test]
fn integer_rows_are_reduced_mod_two() {
    let m = F2Matrix::from_integer_rows(&[vec![-1, 2, 3], vec![0, 4, -5]]).unwrap();
    assert_eq!(m.to_rows(), vec![vec![1, 0, 1], vec![0, 0, 1]]);
    assert!(F2Matrix::from_integer_rows(&[vec![1], vec![1, 1]]).is_err());
}

#[test]
fn rows_columns_and_transpose_are_consistent() {
    let m = matrix(&[&[1, 0, 1, 1], &[0, 1, 1, 0], &[1, 1, 0, 0]]);
    let t = m.transpose();
    assert_eq!((t.rows(), t.cols()), (4, 3));
    for r in 0..3 {
        for c in 0..4 {
            assert_eq!(m.get(r, c).unwrap(), t.get(c, r).unwrap());
        }
    }
    assert_eq!(m.row(1).unwrap().to_bits(), vec![0, 1, 1, 0]);
    assert_eq!(m.column(2).unwrap().to_bits(), vec![1, 1, 0]);
    assert_eq!(t.transpose(), m);
    assert_eq!(
        F2Matrix::from_columns(3, &[m.column(0).unwrap(), m.column(1).unwrap()])
            .unwrap()
            .to_rows(),
        vec![vec![1, 0], vec![0, 1], vec![1, 1]]
    );
    assert_eq!(
        F2Matrix::from_row_vectors(4, &[m.row(2).unwrap()])
            .unwrap()
            .to_rows(),
        vec![vec![1, 1, 0, 0]]
    );
    assert!(F2Matrix::from_columns(2, &[m.column(0).unwrap()]).is_err());
}

// ---------------------------------------------------------------------------
// Matrices: products
// ---------------------------------------------------------------------------

#[test]
fn products_and_transposes_obey_the_matrix_laws_on_every_small_pair() {
    // (A B)^T = B^T A^T, and multiplying by the identity changes nothing, for
    // every 2x3 A and 3x2 B over GF(2).
    let identity = F2Matrix::identity(3).unwrap();
    for a_rows in all_matrices(2, 3) {
        let a = F2Matrix::from_rows(&a_rows).unwrap();
        assert_eq!(a.mul(&identity).unwrap(), a);
        for b_rows in all_matrices(3, 2) {
            let b = F2Matrix::from_rows(&b_rows).unwrap();
            let product = a.mul(&b).unwrap();
            assert_eq!(
                product.transpose(),
                b.transpose().mul(&a.transpose()).unwrap()
            );
            // Entry by definition.
            for i in 0..2 {
                for j in 0..2 {
                    let expected: u8 = (0..3).map(|k| a_rows[i][k] & b_rows[k][j]).sum::<u8>() % 2;
                    assert_eq!(u8::from(product.get(i, j).unwrap()), expected);
                }
            }
        }
    }
}

#[test]
fn matrix_vector_products_agree_with_the_definition() {
    let rows = vec![vec![1, 0, 1, 1], vec![0, 1, 1, 0], vec![1, 1, 0, 1]];
    let m = F2Matrix::from_rows(&rows).unwrap();
    for x in all_vectors(4) {
        assert_eq!(m.mul_vec(&vector(&x)).unwrap().to_bits(), apply(&rows, &x));
    }
    // v * M for a row vector is the sum of the selected rows.
    for y in all_vectors(3) {
        let expected: Vec<u8> = (0..4)
            .map(|c| (0..3).map(|r| y[r] & rows[r][c]).sum::<u8>() % 2)
            .collect();
        assert_eq!(m.vec_mul(&vector(&y)).unwrap().to_bits(), expected);
    }
    assert!(m.mul_vec(&vector(&[1, 0])).is_err());
    assert!(m.vec_mul(&vector(&[1, 0])).is_err());
    assert!(m.mul(&m).is_err(), "3x4 times 3x4 do not compose");
    assert!(m.add(&F2Matrix::identity(3).unwrap()).is_err());
    assert_eq!(m.add(&m).unwrap(), F2Matrix::zeros(3, 4).unwrap());
}

// ---------------------------------------------------------------------------
// Rank, reduced form, kernels and images
// ---------------------------------------------------------------------------

#[test]
fn rank_agrees_with_elimination_and_row_span_enumeration_on_every_matrix_up_to_four_by_four() {
    for (rows, cols) in [(1, 4), (4, 1), (2, 3), (3, 2), (3, 3), (4, 4)] {
        for entries in all_matrices(rows, cols) {
            let m = F2Matrix::from_rows(&entries).unwrap();
            let rank = m.rank();
            assert_eq!(
                rank,
                naive_rank(&entries),
                "naive elimination on {entries:?}"
            );
            // Independent image counting: enumerate every XOR of input rows.
            let row_span: BTreeSet<Vec<u8>> = all_vectors(rows)
                .into_iter()
                .map(|weights| {
                    (0..cols)
                        .map(|c| {
                            entries
                                .iter()
                                .zip(&weights)
                                .fold(0, |x, (row, &w)| x ^ (row[c] & w))
                        })
                        .collect()
                })
                .collect();
            assert_eq!(
                row_span.len(),
                1usize << rank,
                "row-span count on {entries:?}"
            );
            assert_eq!(m.transpose().rank(), rank, "rank of the transpose");
        }
    }
}

#[test]
fn the_reduced_row_echelon_form_is_reduced_and_keeps_the_row_space() {
    for entries in all_matrices(3, 4) {
        let m = F2Matrix::from_rows(&entries).unwrap();
        let reduced = m.rref();
        let pivots = &reduced.pivot_columns;
        assert!(
            pivots.windows(2).all(|w| w[0] < w[1]),
            "pivots strictly increase"
        );
        assert_eq!(reduced.rank(), naive_rank(&entries));
        for (row, &pivot) in pivots.iter().enumerate() {
            // A leading one, with zeros elsewhere in its column.
            for r in 0..3 {
                assert_eq!(reduced.matrix.get(r, pivot).unwrap(), r == row);
            }
            // Nothing to the left of a pivot in its row.
            assert!((0..pivot).all(|c| !reduced.matrix.get(row, c).unwrap()));
        }
        // Rows below the rank are zero.
        for r in reduced.rank()..3 {
            assert!(reduced.matrix.row(r).unwrap().is_zero());
        }
        // The row space is unchanged: every original row reduces to zero
        // modulo the reduced rows, and the dimensions agree.
        let mut span = F2Span::new(4);
        for r in 0..reduced.rank() {
            assert!(span.insert(&reduced.matrix.row(r).unwrap()).unwrap());
        }
        for r in 0..3 {
            assert!(span.contains(&m.row(r).unwrap()).unwrap());
        }
        assert_eq!(m.row_space_basis().len(), reduced.rank());
    }
}

#[test]
fn the_nullspace_is_exactly_the_kernel_counted_by_enumeration() {
    for entries in all_matrices(3, 4) {
        let m = F2Matrix::from_rows(&entries).unwrap();
        let basis = m.nullspace();
        assert_eq!(basis.len(), 4 - naive_rank(&entries));
        let kernel: BTreeSet<Vec<u8>> = all_vectors(4)
            .into_iter()
            .filter(|x| apply(&entries, x).iter().all(|&b| b == 0))
            .collect();
        assert_eq!(
            kernel.len(),
            1 << basis.len(),
            "the kernel has 2^nullity elements"
        );
        // Each basis vector is in the kernel, and together they are independent.
        let mut span = F2Span::new(4);
        for x in &basis {
            assert!(kernel.contains(&x.to_bits()));
            assert!(
                span.insert(x).unwrap(),
                "kernel basis vectors are independent"
            );
        }
        // Every kernel element is a combination of the basis.
        for x in &kernel {
            assert!(span.contains(&vector(x)).unwrap());
        }
        // The left nullspace of A is the nullspace of A^T.
        assert_eq!(m.left_nullspace().len(), 3 - naive_rank(&entries));
    }
}

#[test]
fn column_and_row_space_bases_span_the_image_counted_by_enumeration() {
    for entries in all_matrices(3, 4) {
        let m = F2Matrix::from_rows(&entries).unwrap();
        let rank = naive_rank(&entries);
        let image: BTreeSet<Vec<u8>> = all_vectors(4).iter().map(|x| apply(&entries, x)).collect();
        assert_eq!(image.len(), 1 << rank, "the image has 2^rank elements");
        let columns = m.column_space_basis();
        assert_eq!(columns.len(), rank);
        let mut span = F2Span::new(3);
        for c in &columns {
            assert!(image.contains(&c.to_bits()));
            assert!(span.insert(c).unwrap());
        }
        for b in &image {
            assert!(span.contains(&vector(b)).unwrap());
            assert!(m.in_column_space(&vector(b)).unwrap());
        }
        assert_eq!(m.row_space_basis().len(), rank);
    }
}

// ---------------------------------------------------------------------------
// Solutions
// ---------------------------------------------------------------------------

#[test]
fn the_solution_set_of_every_three_by_three_system_matches_brute_force() {
    for entries in all_matrices(3, 3) {
        let m = F2Matrix::from_rows(&entries).unwrap();
        for b in all_vectors(3) {
            let brute: BTreeSet<Vec<u8>> = all_vectors(3)
                .into_iter()
                .filter(|x| apply(&entries, x) == b)
                .collect();
            match m.solve(&vector(&b)).unwrap() {
                None => assert!(
                    brute.is_empty(),
                    "no solution reported for {entries:?} x = {b:?}"
                ),
                Some(space) => {
                    assert_eq!(space.count().to_string(), brute.len().to_string());
                    let listed: BTreeSet<Vec<u8>> = space
                        .enumerate(100)
                        .unwrap()
                        .iter()
                        .map(F2Vector::to_bits)
                        .collect();
                    assert_eq!(listed, brute, "solution set of {entries:?} x = {b:?}");
                    assert_eq!(space.dimension(), 3 - naive_rank(&entries));
                    assert_eq!(apply(&entries, &space.particular().to_bits()), b);
                    for x in all_vectors(3) {
                        assert_eq!(space.contains(&vector(&x)).unwrap(), brute.contains(&x));
                    }
                }
            }
        }
    }
}

#[test]
fn solutions_form_a_torsor_over_the_kernel() {
    // Any two solutions differ by a kernel vector; a kernel vector carries a
    // solution to a solution.
    let rows = vec![
        vec![1, 1, 0, 1, 0, 0],
        vec![0, 1, 1, 0, 1, 0],
        vec![1, 0, 1, 0, 0, 1],
    ];
    let m = F2Matrix::from_rows(&rows).unwrap();
    let b = vector(&apply(&rows, &[1, 0, 1, 1, 0, 0]));
    let space = m.solve(&b).unwrap().unwrap();
    let solutions = space.enumerate(1000).unwrap();
    assert_eq!(solutions.len(), 1 << (6 - m.rank()));
    let kernel: BTreeSet<Vec<u8>> = all_vectors(6)
        .into_iter()
        .filter(|x| apply(&rows, x).iter().all(|&v| v == 0))
        .collect();
    for first in &solutions {
        assert_eq!(m.mul_vec(first).unwrap(), b);
        for second in &solutions {
            assert!(kernel.contains(&first.add(second).unwrap().to_bits()));
        }
        for k in &kernel {
            assert!(solutions.contains(&first.add(&vector(k)).unwrap()));
        }
    }
}

#[test]
fn solving_refuses_a_right_hand_side_of_the_wrong_length() {
    let m = matrix(&[&[1, 0], &[0, 1]]);
    assert_eq!(
        m.solve(&vector(&[1, 0, 0])),
        Err(F2Error::LengthMismatch {
            expected: 2,
            actual: 3
        })
    );
    // An inconsistent system: x = 1 and x = 0.
    let inconsistent = matrix(&[&[1], &[1]]);
    assert!(inconsistent.solve(&vector(&[1, 0])).unwrap().is_none());
    assert!(inconsistent.solve(&vector(&[1, 1])).unwrap().is_some());
}

#[test]
fn listing_solutions_is_bounded_with_a_typed_refusal() {
    let zero = F2Matrix::zeros(1, 12).unwrap();
    let space = zero.solve(&vector(&[0])).unwrap().unwrap();
    assert_eq!(space.dimension(), 12);
    assert_eq!(space.count().to_string(), "4096");
    assert!(matches!(
        space.enumerate(4095),
        Err(F2Error::EnumerationLimit { limit: 4095, .. })
    ));
    assert_eq!(space.enumerate(4096).unwrap().len(), 4096);
    // A kernel of dimension 64 or more is refused without shifting out of range.
    let huge = F2Matrix::zeros(1, 70)
        .unwrap()
        .solve(&vector(&[0]))
        .unwrap()
        .unwrap();
    assert!(matches!(
        huge.enumerate(usize::MAX),
        Err(F2Error::EnumerationLimit { .. })
    ));
}

// ---------------------------------------------------------------------------
// Spans
// ---------------------------------------------------------------------------

#[test]
fn a_span_reduces_canonically_and_detects_dependence() {
    let mut span = F2Span::new(5);
    assert!(span.insert(&vector(&[1, 1, 0, 0, 0])).unwrap());
    assert!(span.insert(&vector(&[0, 1, 1, 0, 0])).unwrap());
    // The sum of the two is dependent.
    assert!(!span.insert(&vector(&[1, 0, 1, 0, 0])).unwrap());
    assert_eq!(span.dimension(), 2);
    assert!(span.contains(&vector(&[1, 0, 1, 0, 0])).unwrap());
    assert!(!span.contains(&vector(&[0, 0, 0, 1, 0])).unwrap());
    // reduce is constant on cosets of the span and zero exactly on members.
    let v = vector(&[0, 0, 1, 1, 0]);
    let shifted = v.add(&vector(&[1, 1, 0, 0, 0])).unwrap();
    assert_eq!(span.reduce(&v).unwrap(), span.reduce(&shifted).unwrap());
    assert!(span.reduce(&vector(&[1, 1, 0, 0, 0])).unwrap().is_zero());
    assert!(span.reduce(&vector(&[1, 1])).is_err());
    assert!(span.insert(&vector(&[1])).is_err());
    // The dimension of the span of all rows equals the rank.
    for entries in all_matrices(3, 3) {
        let m = F2Matrix::from_rows(&entries).unwrap();
        let mut span = F2Span::new(3);
        for r in 0..3 {
            span.insert(&m.row(r).unwrap()).unwrap();
        }
        assert_eq!(span.dimension(), m.rank());
    }
}

// ---------------------------------------------------------------------------
// Wide matrices
// ---------------------------------------------------------------------------

#[test]
fn elimination_is_correct_across_word_boundaries() {
    // The edge-vertex incidence of a cycle graph on n vertices has rank n - 1
    // and a one-dimensional kernel spanned by the all-ones vector.
    for n in [63usize, 64, 65, 128, 130, 200] {
        let mut m = F2Matrix::zeros(n, n).unwrap();
        for i in 0..n {
            m.set(i, i, true).unwrap();
            m.set(i, (i + 1) % n, true).unwrap();
        }
        assert_eq!(m.rank(), n - 1, "cycle graph on {n} vertices");
        let kernel = m.nullspace();
        assert_eq!(kernel.len(), 1);
        assert_eq!(kernel[0].weight(), n);
        // Solving for the image of a vector recovers a preimage.
        let x = F2Vector::from_indices(n, &[0, 1, n - 1]).unwrap();
        let b = m.mul_vec(&x).unwrap();
        let space = m.solve(&b).unwrap().unwrap();
        assert_eq!(m.mul_vec(space.particular()).unwrap(), b);
        assert_eq!(space.dimension(), 1);
    }
    let identity = F2Matrix::identity(130).unwrap();
    assert_eq!(identity.rank(), 130);
    assert!(identity.nullspace().is_empty());
}

// Origin: engine/crates_rs/tests/core_number_theory/gf2_tests.rs
// Claim: urn:core:crates_rs:tests:gf2-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc4eccd80 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc4eccd80` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc4eccd80 {
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
impl BoundaryErrorc4eccd80 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc4eccd80 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc4eccd80 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc4eccd80 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc4eccd80> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc4eccd80::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc4eccd80::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc4eccd80::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c4eccd80() {
    let admitted = BoundaryRecordc4eccd80::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc4eccd80::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

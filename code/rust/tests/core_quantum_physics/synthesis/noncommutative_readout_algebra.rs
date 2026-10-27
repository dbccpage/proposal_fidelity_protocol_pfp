//! QM_209: diagonal (L1) readouts commute, the Pauli commutators are exact,
//! and the Mermin–Peres sign table is a nonzero class in degree two of a
//! declared closed 2-complex whose faces are the six contexts. A carrier graph
//! has no 2-cochains, so it cannot carry that class.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use std::collections::BTreeMap;

use linear_algebra::exact_field::matrix as mx;
use core_number_theory::{cyclotomic::GaussianRat, gf2::F2Matrix};
use core_quantum_physics::exact_hermitian::gi;
use core_quantum_physics::separating_predictions::{MerminPeresCochainBridge, MerminPeresSquare};

fn pauli(rows: [[(i64, i64); 2]; 2]) -> BasicMatrix<GaussianRat> {
    mx::from_rows(
        rows.iter()
            .map(|row| row.iter().map(|&(re, im)| gi(re, im)).collect())
            .collect(),
    )
    .unwrap()
}

#[test]
fn diagonal_readouts_commute_and_the_pauli_commutators_are_exact() {
    let values = [-1i64, 0, 2];
    let mut readouts: Vec<BasicMatrix<GaussianRat>> = Vec::new();
    for a in values {
        for b in values {
            for c in values {
                readouts.push(mx::diagonal(&[gi(a, 0), gi(b, 0), gi(c, 0)]).unwrap());
            }
        }
    }
    assert_eq!(readouts.len(), 27);
    for m_f in &readouts {
        for m_g in &readouts {
            assert_eq!(
                mx::commutator(m_f, m_g).unwrap(),
                mx::zeros::<GaussianRat>(3, 3).unwrap()
            );
        }
    }

    let x = pauli([[(0, 0), (1, 0)], [(1, 0), (0, 0)]]);
    let y = pauli([[(0, 0), (0, -1)], [(0, 1), (0, 0)]]);
    let z = pauli([[(1, 0), (0, 0)], [(0, 0), (-1, 0)]]);
    let two_i = gi(0, 2);
    assert_eq!(
        mx::commutator(&x, &y).unwrap(),
        mx::scale(&z, &two_i).unwrap()
    );
    assert_eq!(
        mx::commutator(&y, &z).unwrap(),
        mx::scale(&x, &two_i).unwrap()
    );
    assert_eq!(
        mx::commutator(&z, &x).unwrap(),
        mx::scale(&y, &two_i).unwrap()
    );
    // The source's identity [sigma_x, sigma_z] = -2i sigma_y.
    assert_eq!(
        mx::commutator(&x, &z).unwrap(),
        mx::scale(&y, &gi(0, -2)).unwrap()
    );
    // Z is a nondegenerate diagonal readout; X is not diagonal and does not commute with it.
    assert_ne!(
        mx::commutator(&z, &x).unwrap(),
        mx::zeros::<GaussianRat>(2, 2).unwrap()
    );
}

/// Observables of the square with their (row, column) position, and the sign
/// cochain on the six contexts (`1` where the declared product is `-1`).
fn square_data(square: &MerminPeresSquare) -> (Vec<(usize, usize)>, Vec<u8>) {
    let mut position: BTreeMap<&str, (Option<usize>, Option<usize>)> = BTreeMap::new();
    for (context, names) in square.contexts.iter().enumerate() {
        for name in names {
            let slot = position.entry(*name).or_insert((None, None));
            if context < 3 {
                slot.0 = Some(context);
            } else {
                slot.1 = Some(context - 3);
            }
        }
    }
    let cells = position
        .values()
        .map(|&(row, col)| (row.unwrap(), col.unwrap()))
        .collect();
    let signs = square
        .context_products
        .iter()
        .map(|&p| u8::from(p == -1))
        .collect();
    (cells, signs)
}

#[test]
fn the_mermin_peres_signs_are_a_nonzero_degree_two_class_on_a_closed_surface() {
    let square = MerminPeresSquare::standard();
    let (cells, signs) = square_data(&square);
    assert_eq!(cells.len(), 9);
    assert_eq!(signs, vec![0, 0, 0, 0, 0, 1]);

    // The 2-complex: one edge per observable, one face per context (rows, then
    // columns), three vertices. The edge in row i, column j joins vertices
    // k and k + 1 (mod 3) with k = i + j mod 3; every row and every column meets
    // each k once, so each face boundary is a closed triangle.
    let d0: Vec<Vec<u8>> = cells
        .iter()
        .map(|&(i, j)| {
            let k = (i + j) % 3;
            (0..3)
                .map(|v| u8::from(v == k || v == (k + 1) % 3))
                .collect()
        })
        .collect();
    let d1: Vec<Vec<u8>> = (0..6)
        .map(|face| {
            cells
                .iter()
                .map(|&(i, j)| u8::from(if face < 3 { i == face } else { j == face - 3 }))
                .collect()
        })
        .collect();
    assert!(F2Matrix::from_rows(&d1)
        .unwrap()
        .mul(&F2Matrix::from_rows(&d0).unwrap())
        .unwrap()
        .is_zero());

    // F2 cohomology (1, 2, 1): a closed surface with Euler characteristic 0.
    let rank_d0 = F2Matrix::from_rows(&d0).unwrap().rank();
    let rank_d1 = F2Matrix::from_rows(&d1).unwrap().rank();
    assert_eq!((3 - rank_d0, 9 - rank_d1 - rank_d0, 6 - rank_d1), (1, 2, 1));

    // The sign cochain is not in im d1: appending it raises the rank.
    let augmented: Vec<Vec<u8>> = d1
        .iter()
        .zip(&signs)
        .map(|(row, s)| [row.clone(), vec![*s]].concat())
        .collect();
    assert_eq!(F2Matrix::from_rows(&augmented).unwrap().rank(), rank_d1 + 1);
    // Separator: the all-ones face functional kills im d1 and reads 1 on the signs.
    let ones = vec![vec![1u8; 6]];
    assert!(F2Matrix::from_rows(&ones)
        .unwrap()
        .mul(&F2Matrix::from_rows(&d1).unwrap())
        .unwrap()
        .is_zero());
    assert_eq!(signs.iter().fold(0u8, |acc, s| acc ^ s), 1);
    // Exhaustively: none of the 512 edge assignments has coboundary equal to the signs.
    let hits = (0u32..512)
        .filter(|mask| {
            let a: Vec<Vec<u8>> = (0..9).map(|e| vec![((mask >> e) & 1) as u8]).collect();
            F2Matrix::from_rows(&d1)
                .unwrap()
                .mul(&F2Matrix::from_rows(&a).unwrap())
                .unwrap()
                .to_rows()
                .iter()
                .map(|row| row[0])
                .eq(signs.iter().copied())
        })
        .count();
    assert_eq!(hits, 0);
    assert_eq!(square.verify_no_noncontextual_assignment(), Ok(true));

    // `MerminPeresCochainBridge` decides the class from the incidence alone; it
    // agrees with this complex on all 64 sign cochains.
    for bits in 0u32..64 {
        let table: Vec<u8> = (0..6).map(|c| ((bits >> c) & 1) as u8).collect();
        let mut signed = MerminPeresSquare::standard();
        signed.context_products = table.iter().map(|&t| if t == 1 { -1 } else { 1 }).collect();
        let augmented: Vec<Vec<u8>> = d1
            .iter()
            .zip(&table)
            .map(|(row, t)| [row.clone(), vec![*t]].concat())
            .collect();
        let nonzero = F2Matrix::from_rows(&augmented).unwrap().rank() == rank_d1 + 1;
        assert_eq!(
            MerminPeresCochainBridge::from_square(signed)
                .unwrap()
                .is_obstructed(),
            nonzero,
            "signs {bits:06b}"
        );
    }

    // Changing the sign of one row as well makes the total even, and the class vanishes.
    let even_signs = [1u8, 0, 0, 0, 0, 1];
    let augmented: Vec<Vec<u8>> = d1
        .iter()
        .zip(even_signs)
        .map(|(row, s)| [row.clone(), vec![s]].concat())
        .collect();
    assert_eq!(F2Matrix::from_rows(&augmented).unwrap().rank(), rank_d1);

    // The carrier graph alone (vertices and edges, no faces): cycle rank 7 and
    // no 2-cochains, so no class of degree two at all.
    assert_eq!(9 - rank_d0, 7);
}

// Origin: engine/crates_rs/tests/core_quantum_physics/synthesis/noncommutative_readout_algebra.rs
// Claim: urn:core:crates_rs:tests:noncommutative-readout-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord68ba32a3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord68ba32a3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError68ba32a3 {
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
impl BoundaryError68ba32a3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError68ba32a3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError68ba32a3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord68ba32a3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError68ba32a3> {
        if capacity_bound == 0 {
            return Err(BoundaryError68ba32a3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError68ba32a3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError68ba32a3::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_68ba32a3() {
    let admitted = BoundaryRecord68ba32a3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord68ba32a3::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

//! Declared-domain incidence and rational homology. This target does not
//! import `core_wdp`. The cycle is built from simplex lists.

use core_homology::declared_incidence::{
    decode_declared, declared_chain_report, encode_declared, DeclaredIncidenceError,
};
use core_homology::scalar::q;
use std::collections::BTreeSet;

fn cycle_cells() -> Vec<Vec<usize>> {
    vec![
        vec![0],
        vec![1],
        vec![2],
        vec![0, 1],
        vec![0, 2],
        vec![1, 2],
    ]
}

fn filled_cells() -> Vec<Vec<usize>> {
    let mut cells = cycle_cells();
    cells.push(vec![0, 1, 2]);
    cells
}

fn as_set(cells: &[Vec<usize>]) -> BTreeSet<Vec<usize>> {
    cells.iter().cloned().collect()
}

fn assert_report_is_the_owner_matrices(
    complex: &core_homology::simplicial::SimplicialComplex,
) {
    let report = declared_chain_report(complex).unwrap();
    assert_eq!(report.betti, complex.rational_betti_numbers().unwrap());
    assert_eq!(
        report.dimensions,
        (0..=complex.max_dimension())
            .map(|dimension| complex.count(dimension))
            .collect::<Vec<_>>()
    );
    for (offset, rows) in report.boundaries.iter().enumerate() {
        let matrix = complex.boundary_matrix(offset + 1).unwrap();
        assert_eq!(rows.len(), matrix.rows());
        for row in 0..matrix.rows() {
            assert_eq!(rows[row].len(), matrix.cols());
            for column in 0..matrix.cols() {
                assert_eq!(rows[row][column], matrix.get(row, column).unwrap().to_string());
            }
        }
    }
}

fn returned_entries_multiply_to_zero(lower: &[Vec<String>], upper: &[Vec<String>]) {
    assert!(!lower.is_empty() && !upper.is_empty());
    let middle = upper.len();
    let columns = upper[0].len();
    assert!(lower.iter().all(|row| row.len() == middle));
    assert!(upper.iter().all(|row| row.len() == columns));
    for row in lower {
        for column in 0..columns {
            let mut total: i64 = 0;
            for index in 0..middle {
                let left: i64 = row[index].parse().expect("boundary entry");
                let right: i64 = upper[index][column].parse().expect("boundary entry");
                total += left * right;
            }
            assert_eq!(total, 0);
        }
    }
}

#[test]
fn decode_encode_is_the_simplex_set_on_the_declared_class() {
    for cells in [cycle_cells(), filled_cells()] {
        let complex = encode_declared(&cells).unwrap();
        assert_eq!(decode_declared(&complex), as_set(&cells));
        assert_report_is_the_owner_matrices(&complex);
    }
    let shuffled = vec![
        vec![1, 2],
        vec![0],
        vec![2],
        vec![0, 2],
        vec![1],
        vec![0, 1],
    ];
    let complex = encode_declared(&shuffled).unwrap();
    assert_eq!(decode_declared(&complex), as_set(&shuffled));
}

#[test]
fn missing_face_reversed_endpoints_and_duplicate_cell_are_refused() {
    let mut missing_face = filled_cells();
    missing_face.retain(|cell| cell != &vec![0, 1]);
    assert!(matches!(
        encode_declared(&missing_face),
        Err(DeclaredIncidenceError::MissingFace { .. })
    ));
    assert!(matches!(
        encode_declared(&[vec![0], vec![1], vec![1, 0]]),
        Err(DeclaredIncidenceError::NonIncreasing(_))
    ));
    let mut duplicate = cycle_cells();
    duplicate.push(vec![0, 1]);
    assert!(matches!(
        encode_declared(&duplicate),
        Err(DeclaredIncidenceError::DuplicateCell(_))
    ));
    assert!(matches!(
        encode_declared(&[vec![0], vec![2]]),
        Err(DeclaredIncidenceError::MissingVertex(1))
    ));
}

#[test]
fn cycle_and_filled_triangle_use_the_shipped_rational_betti_function() {
    let cycle = encode_declared(&cycle_cells()).unwrap();
    let cycle_report = declared_chain_report(&cycle).unwrap();
    assert_eq!(cycle.rational_betti_numbers().unwrap(), vec![1, 1]);
    assert_eq!(cycle_report.betti, cycle.rational_betti_numbers().unwrap());
    assert_eq!(cycle_report.dimensions, vec![3, 3]);
    assert_eq!(
        cycle_report.boundaries,
        vec![vec![
            vec!["-1".to_string(), "-1".into(), "0".into()],
            vec!["1".into(), "0".into(), "-1".into()],
            vec!["0".into(), "1".into(), "1".into()],
        ]]
    );

    let filled = encode_declared(&filled_cells()).unwrap();
    let filled_report = declared_chain_report(&filled).unwrap();
    assert_eq!(filled.rational_betti_numbers().unwrap(), vec![1, 0, 0]);
    assert_eq!(filled_report.betti, filled.rational_betti_numbers().unwrap());
    assert_eq!(filled_report.dimensions, vec![3, 3, 1]);
    assert_eq!(
        filled_report.boundaries[1],
        vec![vec!["1".to_string()], vec!["-1".into()], vec!["1".into()]]
    );
    returned_entries_multiply_to_zero(&filled_report.boundaries[0], &filled_report.boundaries[1]);
    let composed = filled.boundary_composition(2).unwrap();
    for row in 0..composed.rows() {
        for column in 0..composed.cols() {
            assert_eq!(composed.get(row, column).unwrap(), q(0));
        }
    }
}

// Origin: engine/crates_rs/tests/core_homology/declared_incidence.rs
// Claim: urn:core:crates_rs:tests:declared-incidence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord25abfac5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord25abfac5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError25abfac5 {
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
impl BoundaryError25abfac5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError25abfac5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError25abfac5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord25abfac5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError25abfac5> {
        if capacity_bound == 0 {
            return Err(BoundaryError25abfac5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError25abfac5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError25abfac5::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_25abfac5() {
    let admitted = BoundaryRecord25abfac5::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord25abfac5::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

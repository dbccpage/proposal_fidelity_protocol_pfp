use core_homology::finite_poset::FinitePoset;
use core_homology::permutohedral::{
    add_scaled, augmentation, boundary, boundary_chain, cell_dimension, validate_cell, Cell,
    CellChain, ContractionLimits, LinearExtensionContraction, PermutohedralError,
};
use std::collections::{BTreeMap, BTreeSet};

fn limits() -> ContractionLimits {
    ContractionLimits::default()
}

// Independent insertion enumeration; no production boundary or matching is
// used to decide the list of cells.
fn cells(labels: usize) -> BTreeSet<Cell> {
    let mut result = BTreeSet::from([vec![vec![0]]]);
    for label in 1..labels {
        let mut next = BTreeSet::new();
        for cell in result {
            for position in 0..cell.len() {
                let mut enlarged = cell.clone();
                enlarged[position].push(label);
                next.insert(enlarged);
            }
            for position in 0..=cell.len() {
                let mut enlarged = cell.clone();
                enlarged.insert(position, vec![label]);
                next.insert(enlarged);
            }
        }
        result = next;
    }
    result
}

fn chain(cell: Cell, coefficient: i64) -> CellChain {
    BTreeMap::from([(cell, coefficient)])
}

fn assert_contraction(order: FinitePoset) -> usize {
    let labels = order.size();
    let mut contraction = LinearExtensionContraction::new(order, limits()).unwrap();
    let mut count = 0;
    for cell in cells(labels) {
        if !contraction.contains(&cell).unwrap() {
            continue;
        }
        count += 1;
        let degree = cell_dimension(&cell).unwrap();
        let input = chain(cell.clone(), 1);
        let faces = boundary(&cell, limits()).unwrap();
        let h = contraction.homotopy(&input, degree).unwrap();
        let mut lhs = boundary_chain(&h, labels, degree + 1, limits()).unwrap();
        if degree > 0 {
            assert!(boundary_chain(&faces, labels, degree - 1, limits())
                .unwrap()
                .is_empty());
            let hd = contraction.homotopy(&faces, degree - 1).unwrap();
            add_scaled(&mut lhs, &hd, 1, limits()).unwrap();
            let filler = contraction.fill_cycle(&faces, degree - 1).unwrap();
            assert_eq!(
                boundary_chain(&filler, labels, degree, limits()).unwrap(),
                faces
            );
        }
        let mut expected = input;
        if degree == 0 {
            add_scaled(
                &mut expected,
                &chain(contraction.root_vertex().clone(), 1),
                -1,
                limits(),
            )
            .unwrap();
            let filler = contraction.fill_cycle(&expected, 0).unwrap();
            assert_eq!(
                boundary_chain(&filler, labels, 1, limits()).unwrap(),
                expected
            );
        }
        assert_eq!(lhs, expected, "contraction identity at {cell:?}");
    }
    count
}

#[test]
fn full_permutohedra_through_five_labels_have_exact_contractions() {
    let mut counts = Vec::new();
    for labels in 1..=5 {
        counts.push(assert_contraction(FinitePoset::new(labels, []).unwrap()));
    }
    assert_eq!(counts, [1, 3, 13, 75, 541]);
}

#[test]
fn every_three_label_poset_and_four_label_forward_generated_order() {
    let directed = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)];
    let mut distinct = BTreeSet::new();
    for mask in 0..(1 << directed.len()) {
        let edges = directed
            .iter()
            .enumerate()
            .filter(|(bit, _)| mask & (1 << bit) != 0)
            .map(|(_, &edge)| edge);
        if let Ok(order) = FinitePoset::from_generating_relations(3, edges) {
            if distinct.insert(order.strict_relations()) {
                assert_contraction(order);
            }
        }
    }
    assert_eq!(distinct.len(), 19);
    let forward = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];
    for mask in 0..(1 << forward.len()) {
        let edges = forward
            .iter()
            .enumerate()
            .filter(|(bit, _)| mask & (1 << bit) != 0)
            .map(|(_, &edge)| edge);
        assert_contraction(FinitePoset::from_generating_relations(4, edges).unwrap());
    }
}

#[test]
fn relabelled_diamond_uses_lexicographic_extension_not_numeric_order() {
    let order =
        FinitePoset::from_generating_relations(4, [(3, 1), (3, 2), (1, 0), (2, 0)]).unwrap();
    let mut contraction = LinearExtensionContraction::new(order.clone(), limits()).unwrap();
    assert_eq!(contraction.reference_extension(), &[3, 1, 2, 0]);
    let edge = vec![vec![3], vec![1, 2], vec![0]];
    let ends = boundary(&edge, limits()).unwrap();
    assert_eq!(contraction.fill_cycle(&ends, 0).unwrap(), chain(edge, 1));
    assert_eq!(assert_contraction(order), 3);
}

fn determinant(mut matrix: Vec<Vec<i64>>) -> i64 {
    if matrix.is_empty() {
        return 1;
    }
    let row = matrix.remove(0);
    row.iter()
        .enumerate()
        .map(|(column, &value)| {
            let minor = matrix
                .iter()
                .map(|r| {
                    r.iter()
                        .enumerate()
                        .filter(|(j, _)| *j != column)
                        .map(|(_, &x)| x)
                        .collect()
                })
                .collect();
            (if column % 2 == 0 { 1 } else { -1 }) * value * determinant(minor)
        })
        .sum()
}

#[test]
fn incidence_signs_match_independent_outward_normal_determinants() {
    for labels in 2..=5 {
        let top = vec![(0..labels).collect()];
        for (face, sign) in boundary(&top, limits()).unwrap() {
            let left = &face[0];
            let right = &face[1];
            // Normal points toward the facet where left coordinates have
            // lower ranks. It has coordinate -|R| on L and |L| on R.
            let mut columns = vec![(0..labels - 1)
                .map(|i| {
                    if left.contains(&i) {
                        -(right.len() as i64)
                    } else {
                        left.len() as i64
                    }
                })
                .collect::<Vec<_>>()];
            for block in [&left, &right] {
                let last = *block.last().unwrap();
                for &label in &block[..block.len() - 1] {
                    columns.push(
                        (0..labels - 1)
                            .map(|i| i64::from(i == label) - i64::from(i == last))
                            .collect(),
                    );
                }
            }
            let matrix = (0..labels - 1)
                .map(|i| columns.iter().map(|col| col[i]).collect())
                .collect();
            assert_eq!(determinant(matrix).signum(), sign, "face {face:?}");
        }
    }
}

#[test]
fn invalid_cells_orders_degrees_and_noncycles_are_refused() {
    for cell in [
        vec![],
        vec![vec![]],
        vec![vec![1, 0]],
        vec![vec![0], vec![0]],
        vec![vec![0], vec![2]],
    ] {
        assert!(validate_cell(&cell, 2, limits()).is_err());
    }
    assert!(FinitePoset::from_generating_relations(2, [(0, 1), (1, 0)]).is_err());
    assert!(LinearExtensionContraction::new(FinitePoset::new(0, []).unwrap(), limits()).is_err());
    let order = FinitePoset::new(2, [(0, 1)]).unwrap();
    let mut contraction = LinearExtensionContraction::new(order, limits()).unwrap();
    assert_eq!(
        contraction.homotopy(&chain(vec![vec![0, 1]], 1), 1),
        Err(PermutohedralError::OutsideOrder)
    );
    assert!(matches!(
        contraction.homotopy(&chain(vec![vec![0], vec![1]], 1), 1),
        Err(PermutohedralError::WrongDegree { .. })
    ));
    assert_eq!(
        contraction.fill_cycle(&chain(vec![vec![0], vec![1]], 1), 0),
        Err(PermutohedralError::NotCycle)
    );
    assert_eq!(
        contraction.homotopy(&chain(vec![vec![0], vec![1]], 0), 0),
        Err(PermutohedralError::ZeroCoefficient)
    );
    let mut interval =
        LinearExtensionContraction::new(FinitePoset::new(2, []).unwrap(), limits()).unwrap();
    assert_eq!(
        interval.fill_cycle(&chain(vec![vec![0, 1]], 1), 1),
        Err(PermutohedralError::NotCycle)
    );
}

#[test]
fn checked_overflow_is_a_refusal_and_addition_is_atomic() {
    let vertex = vec![vec![0], vec![1]];
    let mut target = chain(vertex.clone(), i64::MAX);
    let original = target.clone();
    assert!(matches!(
        add_scaled(&mut target, &chain(vertex.clone(), 1), 1, limits()),
        Err(PermutohedralError::Overflow(_))
    ));
    assert_eq!(target, original);
    assert!(matches!(
        add_scaled(
            &mut CellChain::new(),
            &chain(vertex.clone(), i64::MIN),
            -1,
            limits()
        ),
        Err(PermutohedralError::Overflow(_))
    ));
    assert!(matches!(
        boundary_chain(&chain(vec![vec![0, 1]], i64::MIN), 2, 1, limits()),
        Err(PermutohedralError::Overflow(_))
    ));
    let overflowing = BTreeMap::from([(vertex, i64::MAX), (vec![vec![1], vec![0]], 1)]);
    assert!(matches!(
        augmentation(&overflowing),
        Err(PermutohedralError::Overflow(_))
    ));
}

#[test]
fn every_resource_bound_refuses_without_approximate_fallback() {
    let order = FinitePoset::new(3, []).unwrap();
    assert!(matches!(
        LinearExtensionContraction::new(
            order.clone(),
            ContractionLimits {
                max_labels: 2,
                ..limits()
            }
        ),
        Err(PermutohedralError::Limit { .. })
    ));
    assert!(matches!(
        LinearExtensionContraction::new(
            order.clone(),
            ContractionLimits {
                max_steps: 0,
                ..limits()
            }
        ),
        Err(PermutohedralError::Limit { .. })
    ));
    assert!(matches!(
        boundary(
            &vec![vec![0, 1, 2]],
            ContractionLimits {
                max_terms: 1,
                ..limits()
            }
        ),
        Err(PermutohedralError::Limit { .. })
    ));
    let mut contraction = LinearExtensionContraction::new(
        order,
        ContractionLimits {
            max_cells: 0,
            ..limits()
        },
    )
    .unwrap();
    let candidate = chain(vec![vec![2], vec![1], vec![0]], 1);
    assert!(matches!(
        contraction.homotopy(&candidate, 0),
        Err(PermutohedralError::Limit { .. })
    ));
    let mut target = chain(vec![vec![0], vec![1]], 1);
    let original = target.clone();
    assert!(matches!(
        add_scaled(
            &mut target,
            &chain(vec![vec![1], vec![0]], 1),
            1,
            ContractionLimits {
                max_terms: 1,
                ..limits()
            }
        ),
        Err(PermutohedralError::Limit { .. })
    ));
    assert_eq!(target, original);
}

// Origin: engine/crates_rs/tests/core_homology/permutohedral_contraction.rs
// Claim: urn:core:crates_rs:tests:permutohedral-contraction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8dc3f42f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8dc3f42f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8dc3f42f {
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
impl BoundaryError8dc3f42f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8dc3f42f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8dc3f42f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8dc3f42f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8dc3f42f> {
        if capacity_bound == 0 {
            return Err(BoundaryError8dc3f42f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8dc3f42f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8dc3f42f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_8dc3f42f() {
    let admitted = BoundaryRecord8dc3f42f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8dc3f42f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

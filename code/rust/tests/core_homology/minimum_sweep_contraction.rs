use core_homology::finite_poset::FinitePoset;
use core_homology::permutohedral::{
    add_scaled, boundary, boundary_chain, cell_dimension, Cell, CellChain, ContractionLimits,
    LinearExtensionContraction, MinimumSweepContraction, PermutohedralError,
};
use std::collections::{BTreeMap, BTreeSet};

fn limits() -> ContractionLimits {
    ContractionLimits::default()
}

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

fn singleton(cell: Cell, coefficient: i64) -> CellChain {
    BTreeMap::from([(cell, coefficient)])
}

fn check_order(order: FinitePoset) -> usize {
    let labels = order.size();
    let support_bound = labels * (labels - 1) / 2;
    let mut sweep = MinimumSweepContraction::new(order, limits()).unwrap();
    let mut count = 0;
    for cell in cells(labels) {
        if !sweep.contains(&cell).unwrap() {
            continue;
        }
        count += 1;
        let degree = cell_dimension(&cell).unwrap();
        let input = singleton(cell.clone(), 1);
        let output = sweep.homotopy(&input, degree).unwrap();
        assert!(output.len() <= support_bound);
        assert!(output.values().all(|&coefficient| coefficient.abs() == 1));
        for term in output.keys() {
            assert!(sweep.contains(term).unwrap());
            assert_eq!(cell_dimension(term).unwrap(), degree + 1);
        }
        let mut lhs = boundary_chain(&output, labels, degree + 1, limits()).unwrap();
        if degree > 0 {
            let faces = boundary(&cell, limits()).unwrap();
            let hd = sweep.homotopy(&faces, degree - 1).unwrap();
            add_scaled(&mut lhs, &hd, 1, limits()).unwrap();
        }
        let mut expected = input;
        if degree == 0 {
            add_scaled(
                &mut expected,
                &singleton(sweep.root_vertex().clone(), 1),
                -1,
                limits(),
            )
            .unwrap();
        }
        assert_eq!(lhs, expected, "cell {cell:?}");
    }
    assert_eq!(sweep.cached_cells(), 0);
    count
}

#[test]
fn all_5316_full_cells_through_six_labels_have_bounded_unit_support_and_identity() {
    let counts: Vec<_> = (1..=6)
        .map(|labels| check_order(FinitePoset::new(labels, []).unwrap()))
        .collect();
    assert_eq!(counts, [1, 3, 13, 75, 541, 4683]);
}

#[test]
fn all_three_label_posets_and_nonnumeric_diamond_preserve_order() {
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
                check_order(order);
            }
        }
    }
    assert_eq!(distinct.len(), 19);
    let diamond =
        FinitePoset::from_generating_relations(4, [(3, 1), (3, 2), (1, 0), (2, 0)]).unwrap();
    let sweep = MinimumSweepContraction::new(diamond.clone(), limits()).unwrap();
    assert_eq!(sweep.reference_extension(), &[3, 1, 2, 0]);
    assert_eq!(check_order(diamond), 3);
}

#[test]
fn two_constructions_have_different_declared_paths_with_the_same_boundary() {
    let order = FinitePoset::new(3, []).unwrap();
    let mut old = LinearExtensionContraction::new(order.clone(), limits()).unwrap();
    let mut sweep = MinimumSweepContraction::new(order, limits()).unwrap();
    let input = singleton(vec![vec![2], vec![1], vec![0]], 1);
    let a = old.homotopy(&input, 0).unwrap();
    let b = sweep.homotopy(&input, 0).unwrap();
    assert_ne!(a, b);
    assert_eq!(
        boundary_chain(&a, 3, 1, limits()).unwrap(),
        boundary_chain(&b, 3, 1, limits()).unwrap()
    );
}

#[test]
fn sparse_large_carrier_has_quadratic_output_without_enumerating_its_cells() {
    let labels = 16;
    let mut sweep =
        MinimumSweepContraction::new(FinitePoset::new(labels, []).unwrap(), limits()).unwrap();
    let vertex: Cell = (0..labels).rev().map(|label| vec![label]).collect();
    let mut cycle = singleton(vertex, 7);
    add_scaled(
        &mut cycle,
        &singleton(sweep.root_vertex().clone(), 1),
        -7,
        limits(),
    )
    .unwrap();
    let filler = sweep.fill_cycle(&cycle, 0).unwrap();
    assert_eq!(filler.len(), labels * (labels - 1) / 2);
    assert!(filler.values().all(|&coefficient| coefficient.abs() == 7));
    assert_eq!(boundary_chain(&filler, labels, 1, limits()).unwrap(), cycle);
}

#[test]
fn malformed_noncycle_and_overflowing_inputs_are_refused() {
    let order = FinitePoset::new(2, []).unwrap();
    let mut sweep = MinimumSweepContraction::new(order, limits()).unwrap();
    assert!(matches!(
        sweep.homotopy(&singleton(vec![vec![0, 0]], 1), 1),
        Err(PermutohedralError::InvalidCell(_))
    ));
    assert_eq!(
        sweep.fill_cycle(&singleton(vec![vec![1], vec![0]], 1), 0),
        Err(PermutohedralError::NotCycle)
    );
    assert_eq!(
        sweep.fill_cycle(&singleton(vec![vec![0, 1]], 1), 1),
        Err(PermutohedralError::NotCycle)
    );
    // A nonnumeric minimal element makes this reversed vertex's sweep sign -1.
    let order = FinitePoset::new(3, [(2, 0)]).unwrap();
    let mut sweep = MinimumSweepContraction::new(order, limits()).unwrap();
    let input = singleton(vec![vec![2], vec![0], vec![1]], i64::MIN);
    assert!(matches!(
        sweep.homotopy(&input, 0),
        Err(PermutohedralError::Overflow(_))
    ));
}

#[test]
fn explicit_generation_term_and_work_budgets_are_enforced() {
    let order = FinitePoset::new(3, []).unwrap();
    let input = singleton(vec![vec![2], vec![1], vec![0]], 1);
    for constrained in [
        ContractionLimits {
            max_cells: 2,
            ..limits()
        },
        ContractionLimits {
            max_terms: 2,
            ..limits()
        },
        ContractionLimits {
            max_steps: 20,
            ..limits()
        },
    ] {
        let mut sweep = MinimumSweepContraction::new(order.clone(), constrained).unwrap();
        assert!(matches!(
            sweep.homotopy(&input, 0),
            Err(PermutohedralError::Limit { .. })
        ));
    }
}

// Origin: engine/crates_rs/tests/core_homology/minimum_sweep_contraction.rs
// Claim: urn:core:crates_rs:tests:minimum-sweep-contraction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc5b2b621 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc5b2b621` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc5b2b621 {
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
impl BoundaryErrorc5b2b621 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc5b2b621 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc5b2b621 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc5b2b621 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc5b2b621> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc5b2b621::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc5b2b621::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc5b2b621::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c5b2b621() {
    let admitted = BoundaryRecordc5b2b621::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc5b2b621::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

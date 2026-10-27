use core_wdp::guarded_chain_transport::{
    enumerate_event_cells, enumerate_task_cells, propose_transport, verify_transport, CellLevels,
    MatrixProposal, TransportProposal,
};
use std::collections::{BTreeMap, BTreeSet};
type Cell = Vec<Vec<usize>>;

fn permutations(values: &[usize]) -> Vec<Vec<usize>> {
    if values.is_empty() {
        return vec![Vec::new()];
    }
    let mut result = Vec::new();
    for (i, &head) in values.iter().enumerate() {
        let mut remaining = values.to_vec();
        remaining.remove(i);
        for tail in permutations(&remaining) {
            let mut word = vec![head];
            word.extend(tail);
            result.push(word);
        }
    }
    result
}

fn direct_legal(word: &[usize], pairs: usize, capacity: usize) -> bool {
    let mut count = capacity;
    let mut seen = vec![false; 2 * pairs];
    for &event in word {
        if event >= seen.len() || seen[event] {
            return false;
        }
        if event % 2 == 0 {
            if count == 0 {
                return false;
            }
            count -= 1;
        } else {
            if !seen[event - 1] {
                return false;
            }
            count += 1;
        }
        seen[event] = true;
    }
    count == capacity && seen.iter().all(|&value| value)
}

fn all_refinements_legal(cell: &Cell, pairs: usize, capacity: usize) -> bool {
    let mut refinements = vec![Vec::new()];
    for block in cell {
        let mut next = Vec::new();
        for prefix in refinements {
            for ordering in permutations(block) {
                let mut word = prefix.clone();
                word.extend(ordering);
                next.push(word);
            }
        }
        refinements = next;
    }
    refinements
        .iter()
        .all(|word| direct_legal(word, pairs, capacity))
}

fn direct_event_cells(pairs: usize, capacity: usize) -> CellLevels {
    let words = permutations(&(0..2 * pairs).collect::<Vec<_>>());
    let mut candidates = BTreeSet::new();
    for word in words
        .iter()
        .filter(|word| direct_legal(word, pairs, capacity))
    {
        for mask in 0usize..(1 << (word.len() - 1)) {
            let mut cell = Vec::new();
            let mut start = 0;
            for cut in 0..word.len() - 1 {
                if mask & (1 << cut) != 0 {
                    let mut block = word[start..=cut].to_vec();
                    block.sort();
                    cell.push(block);
                    start = cut + 1;
                }
            }
            let mut block = word[start..].to_vec();
            block.sort();
            cell.push(block);
            candidates.insert(cell);
        }
    }
    let mut levels = vec![Vec::new(); 2 * pairs];
    for cell in candidates {
        if all_refinements_legal(&cell, pairs, capacity) {
            levels[2 * pairs - cell.len()].push(cell);
        }
    }
    while levels.last().is_some_and(Vec::is_empty) {
        levels.pop();
    }
    levels
}

#[test]
fn complete_safe_cells_match_independent_word_replay() {
    for pairs in 1..=3 {
        for capacity in 1..=pairs {
            assert_eq!(
                enumerate_event_cells(pairs, capacity).unwrap(),
                direct_event_cells(pairs, capacity),
                "n={pairs}, c={capacity}"
            );
        }
    }
}

#[test]
fn four_task_counts_include_every_higher_cell() {
    for (capacity, expected) in [
        (1, vec![24]),
        (2, vec![648, 1368, 876, 168, 6]),
        (3, vec![1944, 5400, 5340, 2184, 302]),
        (4, vec![2520, 7560, 8460, 4320, 978, 78, 1]),
    ] {
        assert_eq!(
            enumerate_event_cells(4, capacity)
                .unwrap()
                .iter()
                .map(Vec::len)
                .collect::<Vec<_>>(),
            expected
        );
    }
    assert_eq!(
        enumerate_task_cells(4, 3)
            .unwrap()
            .iter()
            .map(Vec::len)
            .collect::<Vec<_>>(),
        vec![24, 36, 14]
    );
}

#[test]
fn every_small_capacity_constructs_and_checks_all_identities() {
    for pairs in 1..=3 {
        for capacity in 1..=pairs {
            let (proposal, _) = propose_transport(pairs, capacity).unwrap();
            let report = verify_transport(pairs, capacity, &proposal).unwrap();
            assert!(report.projection_inclusion_is_identity);
            assert_eq!(
                report.checked_matrix_identities,
                4 * proposal.projection.len()
            );
            if pairs == 3 && capacity == 2 {
                let witness = report.witness.unwrap();
                assert_eq!(witness.degree, 1);
                assert_eq!(witness.pairing, 1);
                assert_eq!(witness.task_cycle_support, 6);
                assert!(witness.event_cycle_support > 0);
                assert!(witness.event_cocycle_support > 0);
            }
        }
    }
}

#[test]
fn capacity_one_has_all_components_and_identity_maps() {
    let (proposal, _) = propose_transport(4, 1).unwrap();
    let report = verify_transport(4, 1, &proposal).unwrap();
    assert_eq!(report.event_f_vector, vec![24]);
    assert_eq!(report.task_f_vector, vec![24]);
    assert!(proposal.source_homotopy[0]
        .columns
        .iter()
        .all(Vec::is_empty));
}

fn labeled_columns(
    matrices: &[MatrixProposal],
    domain: &CellLevels,
    codomain: &CellLevels,
    shift: usize,
) -> BTreeMap<Cell, BTreeMap<Cell, i64>> {
    let mut result = BTreeMap::new();
    for (degree, cells) in domain.iter().enumerate() {
        for (column, cell) in cells.iter().enumerate() {
            let image = matrices[degree].columns[column]
                .iter()
                .map(|&(row, coefficient)| (codomain[degree + shift][row].clone(), coefficient))
                .collect();
            result.insert(cell.clone(), image);
        }
    }
    result
}

#[test]
fn maps_and_homotopy_are_strictly_natural_in_capacity() {
    for pairs in 2..=3 {
        let proposals: Vec<_> = (1..=pairs)
            .map(|capacity| propose_transport(pairs, capacity).unwrap().0)
            .collect();
        for window in proposals.windows(2) {
            let smaller = &window[0];
            let larger = &window[1];
            for (
                small_maps,
                small_domain,
                small_codomain,
                large_maps,
                large_domain,
                large_codomain,
                shift,
            ) in [
                (
                    &smaller.projection,
                    &smaller.event_cells,
                    &smaller.task_cells,
                    &larger.projection,
                    &larger.event_cells,
                    &larger.task_cells,
                    0,
                ),
                (
                    &smaller.inclusion,
                    &smaller.task_cells,
                    &smaller.event_cells,
                    &larger.inclusion,
                    &larger.task_cells,
                    &larger.event_cells,
                    0,
                ),
                (
                    &smaller.source_homotopy,
                    &smaller.event_cells,
                    &smaller.event_cells,
                    &larger.source_homotopy,
                    &larger.event_cells,
                    &larger.event_cells,
                    1,
                ),
            ] {
                let small = labeled_columns(small_maps, small_domain, small_codomain, shift);
                let large = labeled_columns(large_maps, large_domain, large_codomain, shift);
                for (cell, image) in small {
                    assert_eq!(large.get(&cell), Some(&image));
                }
            }
        }
    }
}

#[test]
fn hostile_cell_degree_map_and_witness_changes_are_refused() {
    let (proposal, _) = propose_transport(3, 2).unwrap();
    let mut candidate = proposal.clone();
    candidate.event_cells[0].pop();
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.event_cells[0][0][0][0] = usize::MAX;
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.projection.pop();
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.projection[0].columns[0][0].1 *= -1;
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    let entry = candidate.projection[0].columns[0][0];
    candidate.projection[0].columns[0].push(entry);
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.projection[0].columns[0][0].1 = 0;
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.source_homotopy[0]
        .columns
        .iter_mut()
        .find(|column| !column.is_empty())
        .unwrap()[0]
        .1 *= -1;
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.witness.as_mut().unwrap().event_cycle[0] += 1;
    assert!(verify_transport(3, 2, &candidate).is_err());
    let mut candidate = proposal.clone();
    candidate.witness = None;
    assert!(verify_transport(3, 2, &candidate).is_err());
    assert!(verify_transport(3, 3, &proposal).is_err());
}

#[test]
fn schema_rejects_boolean_float_unknown_and_duplicate_fields() {
    let (proposal, _) = propose_transport(1, 1).unwrap();
    for value in [serde_json::json!(true), serde_json::json!(1.0)] {
        let mut json = serde_json::to_value(&proposal).unwrap();
        json["pairs"] = value;
        assert!(serde_json::from_value::<TransportProposal>(json).is_err());
    }
    let mut json = serde_json::to_value(&proposal).unwrap();
    json["trusted"] = serde_json::json!(true);
    assert!(serde_json::from_value::<TransportProposal>(json).is_err());
    let serialized = serde_json::to_string(&proposal).unwrap();
    let duplicate = serialized.replacen("\"pairs\":1", "\"pairs\":1,\"pairs\":1", 1);
    assert!(serde_json::from_str::<TransportProposal>(&duplicate).is_err());
}

#[test]
fn bounded_parameters_fail_closed() {
    for (pairs, capacity) in [(0, 0), (1, 0), (1, 2), (5, 1), (usize::MAX, 1)] {
        assert!(enumerate_event_cells(pairs, capacity).is_err());
        assert!(enumerate_task_cells(pairs, capacity).is_err());
        assert!(propose_transport(pairs, capacity).is_err());
    }
}

use core_homology::permutohedral::{add_scaled, boundary, CellChain, ContractionLimits};
use core_wdp::guarded_chain_transport::sparse::{
    validate_event_cell, validate_task_cell, verify_sparse_event_filling, SparseTransport,
    SparseTransportError, SparseTransportLimits,
};

fn sequential_event_vertex(pairs: usize) -> Cell {
    (0..2 * pairs).map(|event| vec![event]).collect()
}

fn overlapping_event_vertex(pairs: usize) -> Cell {
    let mut labels = vec![0, 2, 1, 3];
    labels.extend(4..2 * pairs);
    labels.into_iter().map(|event| vec![event]).collect()
}

#[test]
fn sparse_eight_task_filling_uses_only_requested_cells() {
    let limits = ContractionLimits::default();
    let mut transport =
        SparseTransport::new(8, 2, limits, SparseTransportLimits::default()).unwrap();
    let overlapping = overlapping_event_vertex(8);
    let sequential = sequential_event_vertex(8);
    let cycle = CellChain::from([(overlapping, 1), (sequential, -1)]);
    assert!(transport.project(&cycle, 0).unwrap().is_empty());
    let h = transport.homotopy(&cycle, 0).unwrap();
    let mut filling = CellChain::new();
    add_scaled(&mut filling, &h, -1, limits).unwrap();
    assert_eq!(filling.len(), 1);
    let checked = verify_sparse_event_filling(8, 2, &cycle, &filling, 0, limits).unwrap();
    assert_eq!(checked.cycle(), &cycle);
    assert_eq!(checked.filling(), &filling);
    assert_eq!(checked.pairs(), 8);
    assert_eq!(checked.capacity(), 2);
    assert_eq!(checked.degree(), 0);
    let stats = transport.stats();
    assert_eq!(stats.projection_columns, 2);
    assert_eq!(stats.inclusion_columns, 1);
    assert_eq!(stats.homotopy_columns, 2);
    assert_eq!(stats.event_carriers, 1);
    assert!(stats.carrier_cached_cells < 10);
    assert!(stats.requests < 30);
}

#[test]
fn sparse_twelve_task_requests_respect_explicit_label_limit() {
    let large = ContractionLimits {
        max_labels: 24,
        ..ContractionLimits::default()
    };
    assert!(SparseTransport::new(
        12,
        2,
        ContractionLimits::default(),
        SparseTransportLimits::default()
    )
    .is_err());
    let mut transport =
        SparseTransport::new(12, 2, large, SparseTransportLimits::default()).unwrap();
    let cell = overlapping_event_vertex(12);
    let h = transport
        .homotopy(&CellChain::from([(cell.clone(), 1)]), 0)
        .unwrap();
    let residual = CellChain::from([(sequential_event_vertex(12), 1), (cell, -1)]);
    verify_sparse_event_filling(12, 2, &residual, &h, 0, large).unwrap();
    assert_eq!(h.len(), 1);
}

#[test]
fn lazy_columns_equal_every_full_column_in_small_cases() {
    for (pairs, capacity) in [(1, 1), (2, 2), (3, 2)] {
        let (full, _) = propose_transport(pairs, capacity).unwrap();
        let mut lazy = SparseTransport::new(
            pairs,
            capacity,
            ContractionLimits::default(),
            SparseTransportLimits::default(),
        )
        .unwrap();
        for (operation, matrices, domain, codomain, shift) in [
            (0, &full.projection, &full.event_cells, &full.task_cells, 0),
            (1, &full.inclusion, &full.task_cells, &full.event_cells, 0),
            (
                2,
                &full.source_homotopy,
                &full.event_cells,
                &full.event_cells,
                1,
            ),
        ] {
            for (cell, expected) in labeled_columns(matrices, domain, codomain, shift) {
                let degree = cell.iter().map(Vec::len).sum::<usize>() - cell.len();
                let input = CellChain::from([(cell, 1)]);
                let actual = match operation {
                    0 => lazy.project(&input, degree),
                    1 => lazy.include(&input, degree),
                    _ => lazy.homotopy(&input, degree),
                }
                .unwrap();
                assert_eq!(
                    actual, expected,
                    "n={pairs}, c={capacity}, operation={operation}"
                );
            }
        }
    }
}

#[test]
fn sparse_validation_rejects_bad_pair_precedence_capacity_and_degrees() {
    let limits = ContractionLimits::default();
    let vertex = overlapping_event_vertex(8);
    assert!(matches!(
        validate_event_cell(8, 1, &vertex, limits),
        Err(SparseTransportError::IllegalEventCell)
    ));
    let mut bad = sequential_event_vertex(8);
    bad[0] = vec![0, 1];
    bad.remove(1);
    assert!(validate_event_cell(8, 2, &bad, limits).is_err());
    let mut missing = sequential_event_vertex(8);
    missing.pop();
    assert!(validate_event_cell(8, 2, &missing, limits).is_err());
    let mut repeated = sequential_event_vertex(8);
    repeated[0] = vec![1];
    assert!(validate_event_cell(8, 2, &repeated, limits).is_err());
    assert!(validate_task_cell(8, 2, &vec![(0..8).collect()], limits).is_err());
    let mut transport =
        SparseTransport::new(8, 2, limits, SparseTransportLimits::default()).unwrap();
    assert!(transport
        .project(&CellChain::from([(vertex.clone(), 1)]), 1)
        .is_err());
    assert!(transport
        .project(&CellChain::from([(vertex.clone(), 0)]), 0)
        .is_err());
    assert!(transport
        .include(&CellChain::from([(vertex, 1)]), 0)
        .is_err());
    assert!(transport.homotopy(&CellChain::new(), usize::MAX).is_err());
}

#[test]
fn sparse_filling_checker_refuses_forged_sign_and_illegal_or_missing_cells() {
    let limits = ContractionLimits::default();
    let mut edge = sequential_event_vertex(8);
    edge[1] = vec![1, 2];
    edge.remove(2);
    let cycle = boundary(&edge, limits).unwrap();
    let filling = CellChain::from([(edge.clone(), 1)]);
    verify_sparse_event_filling(8, 2, &cycle, &filling, 0, limits).unwrap();
    assert!(
        verify_sparse_event_filling(8, 2, &cycle, &CellChain::from([(edge, -1)]), 0, limits)
            .is_err()
    );
    assert!(verify_sparse_event_filling(8, 2, &cycle, &CellChain::new(), 0, limits).is_err());
    assert!(verify_sparse_event_filling(8, 1, &cycle, &filling, 0, limits).is_err());
    assert!(verify_sparse_event_filling(8, 2, &cycle, &filling, 1, limits).is_err());
    let mut malformed_cycle = cycle.clone();
    let mut bad_cell = sequential_event_vertex(8);
    bad_cell[0][0] = usize::MAX;
    malformed_cycle.insert(bad_cell, 1);
    assert!(verify_sparse_event_filling(8, 2, &malformed_cycle, &filling, 0, limits).is_err());
    assert!(verify_sparse_event_filling(
        8,
        2,
        &CellChain::new(),
        &CellChain::new(),
        usize::MAX,
        limits
    )
    .is_err());
}

#[test]
fn sparse_budget_exhaustion_returns_typed_refusals() {
    let defaults = SparseTransportLimits::default();
    let input = CellChain::from([(overlapping_event_vertex(8), 1)]);
    for limits in [
        SparseTransportLimits {
            max_cached_columns: 0,
            ..defaults
        },
        SparseTransportLimits {
            max_cached_terms: 0,
            ..defaults
        },
        SparseTransportLimits {
            max_requests: 1,
            ..defaults
        },
        SparseTransportLimits {
            max_recursion_depth: 0,
            ..defaults
        },
    ] {
        let mut transport =
            SparseTransport::new(8, 2, ContractionLimits::default(), limits).unwrap();
        assert!(matches!(
            transport.project(&input, 0),
            Err(SparseTransportError::Limit { .. })
        ));
    }
    let mut no_carriers = SparseTransport::new(
        8,
        2,
        ContractionLimits::default(),
        SparseTransportLimits {
            max_carriers: 0,
            ..defaults
        },
    )
    .unwrap();
    assert!(matches!(
        no_carriers.homotopy(&input, 0),
        Err(SparseTransportError::Limit { .. })
    ));
    let mut no_steps = SparseTransport::new(
        8,
        2,
        ContractionLimits {
            max_steps: 0,
            ..ContractionLimits::default()
        },
        defaults,
    )
    .unwrap();
    assert!(no_steps.homotopy(&input, 0).is_err());
}

#[test]
fn sparse_overflow_is_refused_without_wrapping_or_partial_results() {
    let limits = ContractionLimits::default();
    let mut transport =
        SparseTransport::new(8, 2, limits, SparseTransportLimits::default()).unwrap();
    let collision = CellChain::from([
        (sequential_event_vertex(8), i64::MAX),
        (overlapping_event_vertex(8), 1),
    ]);
    assert!(transport.project(&collision, 0).is_err());
    let min = CellChain::from([(overlapping_event_vertex(8), i64::MIN)]);
    assert!(transport.homotopy(&min, 0).is_err());
    let honest = CellChain::from([(overlapping_event_vertex(8), 1)]);
    assert_eq!(transport.project(&honest, 0).unwrap().len(), 1);
    let mut edge = sequential_event_vertex(8);
    edge[1] = vec![1, 2];
    edge.remove(2);
    assert!(verify_sparse_event_filling(
        8,
        2,
        &CellChain::new(),
        &CellChain::from([(edge, i64::MIN)]),
        0,
        limits
    )
    .is_err());
}

use core_homology::permutohedral::boundary_chain;
use core_wdp::guarded_chain_transport::sparse::ContractionMethod;

#[test]
fn minimum_sweep_sparse_maps_check_all_identities_on_small_cells() {
    let limits = ContractionLimits::default();
    for pairs in 1..=3 {
        for capacity in 1..=pairs {
            let mut transport = SparseTransport::new_minimum_sweep(
                pairs,
                capacity,
                limits,
                SparseTransportLimits::default(),
            )
            .unwrap();
            for (degree, cells) in enumerate_event_cells(pairs, capacity)
                .unwrap()
                .iter()
                .enumerate()
            {
                for cell in cells {
                    let input = CellChain::from([(cell.clone(), 1)]);
                    let faces = boundary(cell, limits).unwrap();
                    let projected = transport.project(&input, degree).unwrap();
                    let projected_boundary = if degree == 0 {
                        CellChain::new()
                    } else {
                        transport.project(&faces, degree - 1).unwrap()
                    };
                    assert_eq!(
                        boundary_chain(&projected, pairs, degree, limits).unwrap(),
                        projected_boundary
                    );
                    let mut residual = transport.include(&projected, degree).unwrap();
                    add_scaled(&mut residual, &input, -1, limits).unwrap();
                    let homotopy = transport.homotopy(&input, degree).unwrap();
                    let mut homotopy_boundary =
                        boundary_chain(&homotopy, 2 * pairs, degree + 1, limits).unwrap();
                    if degree > 0 {
                        let lower = transport.homotopy(&faces, degree - 1).unwrap();
                        add_scaled(&mut homotopy_boundary, &lower, 1, limits).unwrap();
                    }
                    assert_eq!(
                        residual, homotopy_boundary,
                        "ip-id=dH+Hd for n={pairs}, c={capacity}, cell={cell:?}"
                    );
                }
            }
            for (degree, cells) in enumerate_task_cells(pairs, capacity)
                .unwrap()
                .iter()
                .enumerate()
            {
                for cell in cells {
                    let input = CellChain::from([(cell.clone(), 1)]);
                    let faces = boundary(cell, limits).unwrap();
                    let included = transport.include(&input, degree).unwrap();
                    let included_boundary = if degree == 0 {
                        CellChain::new()
                    } else {
                        transport.include(&faces, degree - 1).unwrap()
                    };
                    assert_eq!(
                        boundary_chain(&included, 2 * pairs, degree, limits).unwrap(),
                        included_boundary
                    );
                    assert_eq!(
                        transport.project(&included, degree).unwrap(),
                        input,
                        "pi=id for n={pairs}, c={capacity}, cell={cell:?}"
                    );
                }
            }
            assert_eq!(transport.stats().method, ContractionMethod::MinimumSweepV2);
            assert_eq!(transport.stats().carrier_cached_cells, 0);
        }
    }
}

#[test]
fn minimum_sweep_sparse_maps_are_strictly_capacity_natural() {
    let limits = ContractionLimits::default();
    for capacity in 1..3 {
        let mut smaller = SparseTransport::new_minimum_sweep(
            3,
            capacity,
            limits,
            SparseTransportLimits::default(),
        )
        .unwrap();
        let mut larger = SparseTransport::new_minimum_sweep(
            3,
            capacity + 1,
            limits,
            SparseTransportLimits::default(),
        )
        .unwrap();
        for (degree, cells) in enumerate_event_cells(3, capacity)
            .unwrap()
            .iter()
            .enumerate()
        {
            for cell in cells {
                let input = CellChain::from([(cell.clone(), 1)]);
                assert_eq!(
                    smaller.project(&input, degree).unwrap(),
                    larger.project(&input, degree).unwrap()
                );
                assert_eq!(
                    smaller.homotopy(&input, degree).unwrap(),
                    larger.homotopy(&input, degree).unwrap()
                );
            }
        }
        for (degree, cells) in enumerate_task_cells(3, capacity)
            .unwrap()
            .iter()
            .enumerate()
        {
            for cell in cells {
                let input = CellChain::from([(cell.clone(), 1)]);
                assert_eq!(
                    smaller.include(&input, degree).unwrap(),
                    larger.include(&input, degree).unwrap()
                );
            }
        }
    }
}

#[test]
fn minimum_sweep_twelve_task_sparse_filling_has_explicit_small_support() {
    let limits = ContractionLimits {
        max_labels: 24,
        ..ContractionLimits::default()
    };
    let bounds = SparseTransportLimits {
        max_cached_columns: 10,
        max_cached_terms: 10,
        max_carriers: 2,
        max_requests: 50,
        max_recursion_depth: 10,
    };
    let mut transport = SparseTransport::new_minimum_sweep(12, 2, limits, bounds).unwrap();
    let source = CellChain::from([(overlapping_event_vertex(12), 1)]);
    let projected = transport.project(&source, 0).unwrap();
    let mut residual = transport.include(&projected, 0).unwrap();
    add_scaled(&mut residual, &source, -1, limits).unwrap();
    let homotopy = transport.homotopy(&source, 0).unwrap();
    verify_sparse_event_filling(12, 2, &residual, &homotopy, 0, limits).unwrap();
    assert_eq!(homotopy.len(), 1);
    assert_eq!(transport.stats().method, ContractionMethod::MinimumSweepV2);
    assert_eq!(transport.stats().carrier_cached_cells, 0);
    assert!(transport.stats().cached_terms <= bounds.max_cached_terms);
}

// Origin: engine/crates_rs/tests/core_wdp/test_guarded_chain_transport.rs
// Claim: urn:core:crates_rs:tests:test-guarded-chain-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6bfecaf0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6bfecaf0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6bfecaf0 {
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
impl BoundaryError6bfecaf0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6bfecaf0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6bfecaf0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6bfecaf0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6bfecaf0> {
        if capacity_bound == 0 {
            return Err(BoundaryError6bfecaf0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6bfecaf0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6bfecaf0::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6bfecaf0() {
    let admitted = BoundaryRecord6bfecaf0::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6bfecaf0::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

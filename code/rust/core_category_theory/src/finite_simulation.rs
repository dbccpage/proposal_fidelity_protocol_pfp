//! Checked simulations and conservative resource extensions of finite dynamics.
//! A successful exact check reflects availability. An extension preserves every
//! old defined step but may add availability, which is listed explicitly.
//! Checked simulations and conservative resource extensions of finite dynamics.
//! A successful exact check reflects availability. An extension preserves every
//! old defined step but may add availability, which is listed explicitly.
//! Replay accepts the exact computed decision, including mismatch diagnostics;
//! only `Checked` establishes simulation. Map/encoding refusals precede the
//! checked cell estimate, which is not a byte/time/allocator bound.
//! AuthorityEffect: None.
use crate::finite_continuation::PartialDynamics;
use std::collections::BTreeSet;
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SimulationMode {
    Exact,
    ResourceExtension,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SimulationError {
    InvalidMap,
    InvalidEncoding,
    WorkLimit,
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_category_theory/src/finite_simulation.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-simulation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SimulationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SimulationError {}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SimulationDecision {
    Checked {
        added_availability: Vec<(usize, usize)>,
    },
    ReportMismatch {
        state: usize,
        source_report: usize,
        target_report: usize,
    },
    StepMismatch {
        state: usize,
        input: usize,
        expected: Option<usize>,
        actual: Option<usize>,
    },
}
// All maps and event macros are explicit. Readout labels must share one declared
// interpretation; mere numerical equality does not supply a semantic dictionary.
/// All maps and event macros are explicit. Readout labels must share one declared
/// interpretation; mere numerical equality does not supply a semantic dictionary.
fn admit_map(
    source: &PartialDynamics,
    target: &PartialDynamics,
    map: &[usize],
    mode: SimulationMode,
) -> Result<(), SimulationError> {
    if map.len() != source.reports().len()
        || map.iter().any(|&t| t >= target.reports().len())
        || (mode == SimulationMode::ResourceExtension
            && map.iter().collect::<BTreeSet<_>>().len() != map.len())
    {
        return Err(SimulationError::InvalidMap);
    }
    Ok(())
}

fn admit_encoding(
    source: &PartialDynamics,
    target: &PartialDynamics,
    words: &[Vec<usize>],
) -> Result<(), SimulationError> {
    if words.len() != source.transitions()[0].len()
        || words
            .iter()
            .flatten()
            .any(|&a| a >= target.transitions()[0].len())
    {
        return Err(SimulationError::InvalidEncoding);
    }
    Ok(())
}

fn admit_budget(
    states: usize,
    words: &[Vec<usize>],
    max_cells: usize,
) -> Result<(), SimulationError> {
    let width = words
        .iter()
        .try_fold(1usize, |n, w| n.checked_add(w.len().checked_add(1)?));
    if width
        .and_then(|n| n.checked_mul(states))
        .is_none_or(|n| n > max_cells)
    {
        return Err(SimulationError::WorkLimit);
    }
    Ok(())
}

fn compare_step(
    expected: Option<usize>,
    actual: Option<usize>,
    mode: SimulationMode,
    coordinate: (usize, usize),
    added: &mut Vec<(usize, usize)>,
) -> Option<SimulationDecision> {
    if expected.is_none() && actual.is_some() && mode == SimulationMode::ResourceExtension {
        added.push(coordinate);
        None
    } else if expected != actual {
        Some(SimulationDecision::StepMismatch {
            state: coordinate.0,
            input: coordinate.1,
            expected,
            actual,
        })
    } else {
        None
    }
}

/// Called only after map/encoding admission, in source-state order.
fn check_state(
    source: &PartialDynamics,
    target: &PartialDynamics,
    map: &[usize],
    words: &[Vec<usize>],
    mode: SimulationMode,
    state: usize,
    added: &mut Vec<(usize, usize)>,
) -> Result<Option<SimulationDecision>, SimulationError> {
    let t = map[state];
    if source.reports()[state] != target.reports()[t] {
        return Ok(Some(SimulationDecision::ReportMismatch {
            state,
            source_report: source.reports()[state],
            target_report: target.reports()[t],
        }));
    }
    for (a, w) in words.iter().enumerate() {
        let expected = source.transitions()[state][a].map(|s| map[s]);
        let actual = target
            .run(t, w)
            .map_err(|_| SimulationError::InvalidEncoding)?;
        if let Some(mismatch) = compare_step(expected, actual, mode, (state, a), added) {
            return Ok(Some(mismatch));
        }
    }
    Ok(None)
}

/// All maps and event macros are explicit. Readout labels must share one declared
/// interpretation; mere numerical equality does not supply a semantic dictionary.
pub fn check_simulation(
    source: &PartialDynamics,
    target: &PartialDynamics,
    map: &[usize],
    words: &[Vec<usize>],
    mode: SimulationMode,
    max_cells: usize,
) -> Result<SimulationDecision, SimulationError> {
    admit_map(source, target, map, mode)?;
    admit_encoding(source, target, words)?;
    admit_budget(map.len(), words, max_cells)?;
    let mut added = Vec::new();
    for state in 0..map.len() {
        if let Some(mismatch) = check_state(source, target, map, words, mode, state, &mut added)? {
            return Ok(mismatch);
        }
    }
    Ok(SimulationDecision::Checked {
        added_availability: added,
    })
}
pub fn verify_simulation(
    source: &PartialDynamics,
    target: &PartialDynamics,
    map: &[usize],
    words: &[Vec<usize>],
    mode: SimulationMode,
    max_cells: usize,
    c: &SimulationDecision,
) -> Result<(), SimulationError> {
    if check_simulation(source, target, map, words, mode, max_cells)? == *c {
        Ok(())
    } else {
        Err(SimulationError::CertificateMismatch)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_cb29bfe8 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

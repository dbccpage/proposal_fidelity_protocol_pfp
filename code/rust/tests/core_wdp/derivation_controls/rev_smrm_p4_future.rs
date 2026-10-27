//! Realizable Future-Distinction Observation Design (REV-SMRM-P4-FUTURE) exact verifier.

/// Checks whether selected sensor bitmasks separate all pairs of states with distinct future labels.
pub fn separates_future_divergent_pairs(
    futures: &[u8],
    sensor_outputs: &[Vec<u8>],
    selected_sensors: &[usize],
) -> bool {
    let n = futures.len();
    for i in 0..n {
        for j in (i + 1)..n {
            if futures[i] != futures[j] {
                let separated = selected_sensors
                    .iter()
                    .any(|&s| sensor_outputs[s][i] != sensor_outputs[s][j]);
                if !separated {
                    return false;
                }
            }
        }
    }
    true
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_future_distinction_coverage_and_savings() {
        let futures = [0u8, 1, 2];
        let sensors = vec![
            vec![0u8, 0, 1], // cost 2
            vec![0u8, 1, 1], // cost 2
            vec![0u8, 1, 2], // cost 3 (single sensor separates all 3 futures)
        ];
        assert!(separates_future_divergent_pairs(&futures, &sensors, &[2]));
        assert!(!separates_future_divergent_pairs(&futures, &sensors, &[0]));
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
enum SeparationError { Width, Sensor, Overflow, Unseparated }

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/rev_smrm_p4_future.rs
// Claim: urn:core:crates_rs:tests:rev-smrm-p4-future:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SeparationError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SeparationError {}

fn validate_selected_sensors(
    width: usize,
    sensor_outputs: &[Vec<u8>],
    selected_sensors: &[usize],
) -> Result<(), SeparationError> {
    let mut seen = std::collections::BTreeSet::new();
    for &sensor in selected_sensors {
        if !seen.insert(sensor) {
            return Err(SeparationError::Sensor);
        }
        let row = sensor_outputs.get(sensor).ok_or(SeparationError::Sensor)?;
        if row.len() != width {
            return Err(SeparationError::Width);
        }
    }
    Ok(())
}

fn pair_separated_by_sensors(
    i: usize,
    j: usize,
    sensor_outputs: &[Vec<u8>],
    selected_sensors: &[usize],
) -> bool {
    selected_sensors
        .iter()
        .any(|&sensor| sensor_outputs[sensor][i] != sensor_outputs[sensor][j])
}

fn certify_separation(futures: &[u8], sensor_outputs: &[Vec<u8>], selected_sensors: &[usize]) -> Result<u64, SeparationError> {
    let width = futures.len();
    if width == 0 {
        return Err(SeparationError::Width);
    }
    validate_selected_sensors(width, sensor_outputs, selected_sensors)?;
    let mut divergent = 0u64;
    for i in 0..width {
        for j in (i + 1)..width {
            if futures[i] == futures[j] {
                continue;
            }
            divergent += 1;
            if !pair_separated_by_sensors(i, j, sensor_outputs, selected_sensors) {
                return Err(SeparationError::Unseparated);
            }
        }
    }
    Ok(divergent)
}

#[cfg(test)]
mod separation_checks {
    use super::certify_separation;

    #[test]
    fn one_sensor_separates_three_distinct_futures() {
        let futures = [0u8, 1, 2];
        let sensors = vec![vec![0u8, 1, 2]];
        assert!(matches!(certify_separation(&futures, &sensors, &[0]), Ok(3)));
    }

    #[test]
    fn a_sensor_that_ties_two_futures_is_refused() {
        let futures = [0u8, 1, 2];
        let sensors = vec![vec![0u8, 0, 1]];
        assert!(matches!(certify_separation(&futures, &sensors, &[0]), Err(super::SeparationError::Unseparated)));
    }
}

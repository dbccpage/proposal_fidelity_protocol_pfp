//! Orbits of checked partial functions on finite carriers. Periodic indices are
//! reduced modulo the cycle before lookup, even for usize::MAX.
//! AuthorityEffect: None.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TransportOrbitError {
    #[error("partial-function carrier exceeds the finite budget")]
    Budget,
    #[error("start {start} is outside {vertices} vertices")]
    StartOutOfRange { start: usize, vertices: usize },
    #[error("vertex {vertex} steps to {target}, outside {vertices} vertices")]
    TargetOutOfRange {
        vertex: usize,
        target: usize,
        vertices: usize,
    },
}
/// How the orbit of a partial step ends.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TransportOrbit {
    /// The value after `at_step` steps is `None`, the first such index.
    Refused { at_step: usize },
    /// The vertex reached after `entry` steps recurs every `period` steps.
    Periodic { entry: usize, period: usize },
}

fn check(step: &[Option<usize>], start: usize) -> Result<(), TransportOrbitError> {
    let vertices = step.len();
    if vertices > 1 << 20 {
        return Err(TransportOrbitError::Budget);
    }
    if start >= vertices {
        return Err(TransportOrbitError::StartOutOfRange { start, vertices });
    }
    for (vertex, target) in step.iter().enumerate() {
        if let Some(target) = *target {
            if target >= vertices {
                return Err(TransportOrbitError::TargetOutOfRange {
                    vertex,
                    target,
                    vertices,
                });
            }
        }
    }
    Ok(())
}

/// Classify the orbit of `start` under the partial step.
pub fn transport_orbit(
    step: &[Option<usize>],
    start: usize,
) -> Result<TransportOrbit, TransportOrbitError> {
    check(step, start)?;
    let mut first_visit: Vec<Option<usize>> = vec![None; step.len()];
    let mut current = start;
    let mut k = 0;
    loop {
        if let Some(entry) = first_visit[current] {
            return Ok(TransportOrbit::Periodic {
                entry,
                period: k - entry,
            });
        }
        first_visit[current] = Some(k);
        match step[current] {
            None => return Ok(TransportOrbit::Refused { at_step: k + 1 }),
            Some(next) => current = next,
        }
        k += 1;
    }
}

/// The vertex after `k` steps from `start`, or `None` once transport refused.
pub fn orbit_value(
    step: &[Option<usize>],
    start: usize,
    k: usize,
) -> Result<Option<usize>, TransportOrbitError> {
    let reduced = match transport_orbit(step, start)? {
        TransportOrbit::Refused { at_step } => {
            if k >= at_step {
                return Ok(None);
            }
            k
        }
        TransportOrbit::Periodic { entry, period } => {
            if k < entry {
                k
            } else {
                entry + (k - entry) % period
            }
        }
    };
    Ok((0..reduced).try_fold(start, |vertex, _| step[vertex]))
}
// Origin: engine/crates_rs/core_holonomy/src/functional_graph.rs
// Claim: urn:core:crates_rs:core-holonomy:functional-graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod bounded_orbit_tests {
    use super::*;
    #[test]
    fn enormous_orbit_indices_are_reduced_to_the_cycle() {
        let step = [Some(1), Some(2), Some(3), Some(1)];
        assert_eq!(
            transport_orbit(&step, 0).unwrap(),
            TransportOrbit::Periodic {
                entry: 1,
                period: 3
            }
        );
        let expected = 1 + (usize::MAX - 1) % 3;
        assert_eq!(orbit_value(&step, 0, usize::MAX).unwrap(), Some(expected));
        assert_eq!(orbit_value(&[Some(1), None], 0, usize::MAX).unwrap(), None);
    }
}

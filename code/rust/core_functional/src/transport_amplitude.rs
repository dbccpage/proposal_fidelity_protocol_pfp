//! Exact finite weighted cyclic transport amplitudes.
//!
//! This module evaluates a declared finite cycle with exact rational edge
//! amplitudes. It does not implement arbitrary path networks or cochain
//! transport, certify a physical interpretation, or emit an acceptance,
//! terminal, or authority result.

use num_rational::BigRational;
use num_traits::{One, Zero};

pub const MAX_CYCLIC_TRANSPORT_DIMENSION: usize = 256;
pub const MAX_CYCLIC_TRANSPORT_STEPS: usize = 65_536;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TransportAmplitudeError {
    #[error("TRANSPORT_EMPTY_CYCLE")]
    EmptyCycle,
    #[error("TRANSPORT_DIMENSION_LIMIT: {actual} exceeds {limit}")]
    DimensionLimit { actual: usize, limit: usize },
    #[error("TRANSPORT_STEP_LIMIT: {actual} exceeds {limit}")]
    StepLimit { actual: usize, limit: usize },
    #[error("TRANSPORT_SOURCE_OUT_OF_RANGE: {source_index} for dimension {dimension}")]
    SourceOutOfRange {
        source_index: usize,
        dimension: usize,
    },
    #[error("TRANSPORT_TARGET_OUT_OF_RANGE: {target} for dimension {dimension}")]
    TargetOutOfRange { target: usize, dimension: usize },
    #[error("TRANSPORT_ZERO_DENOMINATOR: edge {edge}")]
    ZeroDenominator { edge: usize },
}

/// An immutable finite directed cycle with one exact weight on each edge.
///
/// Edge `i` is the directed edge `i -> (i + 1) mod dimension`. The matrix
/// representation returned by [`Self::shift_operator`] uses the column-vector
/// convention `matrix[destination][source]`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MinimalCyclicTransport {
    edge_amplitudes: Vec<BigRational>,
}

/// The exact value of one bounded path query on a declared cyclic carrier.
///
/// This value records only the supplied finite cycle, endpoints, length, and
/// exact product. It is not a proof certificate or an interpretation of the
/// carrier as a physical transport process.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransportAmplitude {
    dimension: usize,
    source: usize,
    target: usize,
    steps: usize,
    value: BigRational,
}

fn canonical_edge_amplitude(
    value: &BigRational,
    edge: usize,
) -> Result<BigRational, TransportAmplitudeError> {
    if value.denom().is_zero() {
        return Err(TransportAmplitudeError::ZeroDenominator { edge });
    }
    Ok(BigRational::new(
        value.numer().clone(),
        value.denom().clone(),
    ))
}

impl MinimalCyclicTransport {
    /// Construct a unit-weight directed cycle with the declared finite size.
    pub fn unit(dimension: usize) -> Result<Self, TransportAmplitudeError> {
        if dimension == 0 {
            return Err(TransportAmplitudeError::EmptyCycle);
        }
        if dimension > MAX_CYCLIC_TRANSPORT_DIMENSION {
            return Err(TransportAmplitudeError::DimensionLimit {
                actual: dimension,
                limit: MAX_CYCLIC_TRANSPORT_DIMENSION,
            });
        }
        Ok(Self {
            edge_amplitudes: vec![BigRational::one(); dimension],
        })
    }

    /// Construct a cycle from its consecutive edge amplitudes.
    ///
    /// Valid unreduced or signed rational encodings are canonicalized before
    /// they can enter the immutable cycle. A raw zero denominator is refused.
    pub fn from_edge_amplitudes(
        edge_amplitudes: &[BigRational],
    ) -> Result<Self, TransportAmplitudeError> {
        let dimension = edge_amplitudes.len();
        if dimension == 0 {
            return Err(TransportAmplitudeError::EmptyCycle);
        }
        if dimension > MAX_CYCLIC_TRANSPORT_DIMENSION {
            return Err(TransportAmplitudeError::DimensionLimit {
                actual: dimension,
                limit: MAX_CYCLIC_TRANSPORT_DIMENSION,
            });
        }
        Ok(Self {
            edge_amplitudes: edge_amplitudes
                .iter()
                .enumerate()
                .map(|(edge, value)| canonical_edge_amplitude(value, edge))
                .collect::<Result<Vec<_>, _>>()?,
        })
    }

    pub fn dimension(&self) -> usize {
        self.edge_amplitudes.len()
    }

    pub fn edge_amplitudes(&self) -> &[BigRational] {
        &self.edge_amplitudes
    }

    /// Return the exact weighted one-step cyclic shift in column-vector form.
    pub fn shift_operator(&self) -> Vec<Vec<BigRational>> {
        let dimension = self.dimension();
        let mut matrix = vec![vec![BigRational::zero(); dimension]; dimension];
        for (source, edge_amplitude) in self.edge_amplitudes.iter().enumerate() {
            let destination = (source + 1) % dimension;
            matrix[destination][source] = edge_amplitude.clone();
        }
        matrix
    }

    /// Evaluate the unique directed path of the given length when it reaches
    /// `target`; otherwise return the exact zero amplitude.
    pub fn amplitude(
        &self,
        source: usize,
        target: usize,
        steps: usize,
    ) -> Result<TransportAmplitude, TransportAmplitudeError> {
        let dimension = self.dimension();
        if source >= dimension {
            return Err(TransportAmplitudeError::SourceOutOfRange {
                source_index: source,
                dimension,
            });
        }
        if target >= dimension {
            return Err(TransportAmplitudeError::TargetOutOfRange { target, dimension });
        }
        if steps > MAX_CYCLIC_TRANSPORT_STEPS {
            return Err(TransportAmplitudeError::StepLimit {
                actual: steps,
                limit: MAX_CYCLIC_TRANSPORT_STEPS,
            });
        }

        let expected_target = (source + steps % dimension) % dimension;
        let value = if target != expected_target {
            BigRational::zero()
        } else {
            let mut value = BigRational::one();
            for offset in 0..steps {
                let edge = (source + offset % dimension) % dimension;
                value *= &self.edge_amplitudes[edge];
            }
            value
        };
        Ok(TransportAmplitude {
            dimension,
            source,
            target,
            steps,
            value,
        })
    }
}

impl TransportAmplitude {
    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn source(&self) -> usize {
        self.source
    }

    pub fn target(&self) -> usize {
        self.target
    }

    pub fn steps(&self) -> usize {
        self.steps
    }

    pub fn value(&self) -> &BigRational {
        &self.value
    }
}

// Origin: engine/crates_rs/core_functional/src/transport_amplitude.rs
// Claim: urn:core:crates_rs:core-functional:transport-amplitude:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn q(numerator: i64, denominator: i64) -> BigRational {
        BigRational::new(numerator.into(), denominator.into())
    }

    fn multiply(left: &[Vec<BigRational>], right: &[Vec<BigRational>]) -> Vec<Vec<BigRational>> {
        let dimension = left.len();
        assert_eq!(right.len(), dimension);
        (0..dimension)
            .map(|row| {
                (0..dimension)
                    .map(|column| {
                        (0..dimension)
                            .map(|inner| &left[row][inner] * &right[inner][column])
                            .sum()
                    })
                    .collect()
            })
            .collect()
    }

    #[test]
    fn weighted_cycle_multiplies_exact_edges() {
        let cycle =
            MinimalCyclicTransport::from_edge_amplitudes(&[q(2, 1), q(3, 1), q(5, 1)]).unwrap();
        let amplitude = cycle.amplitude(0, 2, 2).unwrap();
        assert_eq!(amplitude.dimension(), 3);
        assert_eq!(amplitude.source(), 0);
        assert_eq!(amplitude.target(), 2);
        assert_eq!(amplitude.steps(), 2);
        assert_eq!(amplitude.value(), &q(6, 1));
        assert_eq!(cycle.edge_amplitudes(), &[q(2, 1), q(3, 1), q(5, 1)]);
    }

    #[test]
    fn cyclic_shift_wraps_instead_of_nilpotently_ending() {
        let cycle = MinimalCyclicTransport::unit(3).unwrap();
        let shift = cycle.shift_operator();
        assert_eq!(
            shift,
            vec![
                vec![q(0, 1), q(0, 1), q(1, 1)],
                vec![q(1, 1), q(0, 1), q(0, 1)],
                vec![q(0, 1), q(1, 1), q(0, 1)],
            ]
        );
        let square = multiply(&shift, &shift);
        let cube = multiply(&square, &shift);
        assert_eq!(
            cube,
            vec![
                vec![q(1, 1), q(0, 1), q(0, 1)],
                vec![q(0, 1), q(1, 1), q(0, 1)],
                vec![q(0, 1), q(0, 1), q(1, 1)],
            ]
        );
    }

    #[test]
    fn weighted_shift_operator_matches_path_amplitude() {
        let cycle =
            MinimalCyclicTransport::from_edge_amplitudes(&[q(2, 1), q(3, 1), q(5, 1)]).unwrap();
        let shift = cycle.shift_operator();
        let square = multiply(&shift, &shift);
        let cube = multiply(&square, &shift);

        assert_eq!(shift[1][0], q(2, 1));
        assert_eq!(square[2][0], q(6, 1));
        assert_eq!(cube[0][0], q(30, 1));
        assert_eq!(cycle.amplitude(0, 2, 2).unwrap().value(), &square[2][0]);
        assert_eq!(cycle.amplitude(0, 0, 3).unwrap().value(), &cube[0][0]);
    }

    #[test]
    fn unreachable_endpoint_is_exact_zero() {
        let cycle =
            MinimalCyclicTransport::from_edge_amplitudes(&[q(2, 1), q(3, 1), q(5, 1)]).unwrap();
        assert_eq!(cycle.amplitude(2, 0, 1).unwrap().value(), &q(5, 1));
        assert_eq!(cycle.amplitude(2, 1, 1).unwrap().value(), &q(0, 1));
    }

    #[test]
    fn zero_steps_is_identity() {
        let cycle = MinimalCyclicTransport::from_edge_amplitudes(&[q(0, 1), q(3, 1)]).unwrap();
        assert_eq!(cycle.amplitude(1, 1, 0).unwrap().value(), &q(1, 1));
        assert_eq!(cycle.amplitude(1, 0, 0).unwrap().value(), &q(0, 1));
    }

    #[test]
    fn invalid_inputs_are_typed_refusals() {
        assert_eq!(
            MinimalCyclicTransport::unit(0),
            Err(TransportAmplitudeError::EmptyCycle)
        );
        assert_eq!(
            MinimalCyclicTransport::unit(MAX_CYCLIC_TRANSPORT_DIMENSION + 1),
            Err(TransportAmplitudeError::DimensionLimit {
                actual: MAX_CYCLIC_TRANSPORT_DIMENSION + 1,
                limit: MAX_CYCLIC_TRANSPORT_DIMENSION,
            })
        );
        let cycle = MinimalCyclicTransport::unit(3).unwrap();
        assert_eq!(
            cycle.amplitude(3, 0, 0),
            Err(TransportAmplitudeError::SourceOutOfRange {
                source_index: 3,
                dimension: 3,
            })
        );
        assert_eq!(
            cycle.amplitude(0, 3, 0),
            Err(TransportAmplitudeError::TargetOutOfRange {
                target: 3,
                dimension: 3,
            })
        );
        assert_eq!(
            cycle.amplitude(0, 0, MAX_CYCLIC_TRANSPORT_STEPS + 1),
            Err(TransportAmplitudeError::StepLimit {
                actual: MAX_CYCLIC_TRANSPORT_STEPS + 1,
                limit: MAX_CYCLIC_TRANSPORT_STEPS,
            })
        );
        assert_eq!(
            MinimalCyclicTransport::from_edge_amplitudes(&[BigRational::new_raw(
                1.into(),
                0.into()
            )]),
            Err(TransportAmplitudeError::ZeroDenominator { edge: 0 })
        );
    }

    #[test]
    fn unreduced_rationals_are_canonicalized_before_arithmetic() {
        let cycle = MinimalCyclicTransport::from_edge_amplitudes(&[
            BigRational::new_raw((-2).into(), (-4).into()),
            BigRational::new_raw((-6).into(), (-3).into()),
        ])
        .unwrap();
        assert_eq!(cycle.edge_amplitudes(), &[q(1, 2), q(2, 1)]);
        assert_eq!(cycle.amplitude(0, 0, 2).unwrap().value(), &q(1, 1));
    }
}

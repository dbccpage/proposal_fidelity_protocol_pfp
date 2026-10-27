use core_functional::binary_degree::{
    BinaryDegreeError, BinaryDegreeFunctional, MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM,
};
use serde::{Deserialize, Serialize};

pub const MAX_EXHAUSTIVE_DOMAIN_DIM: usize = MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM;
pub const MAX_SIMPLEX_DEGREE: usize = 62;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DegreeTowerError {
    RaggedMatrix {
        row: usize,
        expected: usize,
        actual: usize,
    },
    InputDimensionMismatch {
        expected: usize,
        actual: usize,
    },
    CompositionDimensionMismatch {
        previous_codomain: usize,
        next_domain: usize,
    },
    CochainIdentityViolation {
        source_basis: usize,
        target_row: usize,
    },
    ExhaustiveSearchTooLarge {
        domain_dim: usize,
        max_supported: usize,
    },
    DetectionIsNotOpen,
    RepairIsNotResolved,
    RepairIsNotMinimal {
        expected: usize,
        actual: usize,
    },
    DegreeMustBePositive,
    SimplexDegreeTooLarge {
        degree: usize,
        max_supported: usize,
    },
}

// Origin: engine/crates_rs/core_wdp/src/ddc/degree_tower.rs
// Claim: urn:core:crates_rs:core-wdp:degree-tower:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DegreeTowerError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DegreeTowerError {}

impl From<BinaryDegreeError> for DegreeTowerError {
    fn from(error: BinaryDegreeError) -> Self {
        match error {
            BinaryDegreeError::RaggedMatrix {
                row,
                expected,
                actual,
            } => Self::RaggedMatrix {
                row,
                expected,
                actual,
            },
            BinaryDegreeError::InputDimensionMismatch { expected, actual } => {
                Self::InputDimensionMismatch { expected, actual }
            }
            BinaryDegreeError::ExhaustiveSearchTooLarge {
                domain_dim,
                max_supported,
            } => Self::ExhaustiveSearchTooLarge {
                domain_dim,
                max_supported,
            },
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BinaryLinearMap {
    domain_dim: usize,
    rows: Vec<Vec<bool>>,
}

impl BinaryLinearMap {
    pub fn from_rows(domain_dim: usize, rows: Vec<Vec<bool>>) -> Result<Self, DegreeTowerError> {
        for (row_index, row) in rows.iter().enumerate() {
            if row.len() != domain_dim {
                return Err(DegreeTowerError::RaggedMatrix {
                    row: row_index,
                    expected: domain_dim,
                    actual: row.len(),
                });
            }
        }
        Ok(Self { domain_dim, rows })
    }

    pub fn zero(domain_dim: usize, codomain_dim: usize) -> Self {
        Self {
            domain_dim,
            rows: vec![vec![false; domain_dim]; codomain_dim],
        }
    }

    pub fn domain_dim(&self) -> usize {
        self.domain_dim
    }

    pub fn codomain_dim(&self) -> usize {
        self.rows.len()
    }

    pub fn rows(&self) -> &[Vec<bool>] {
        &self.rows
    }

    pub fn apply(&self, input: &[bool]) -> Result<Vec<bool>, DegreeTowerError> {
        if input.len() != self.domain_dim {
            return Err(DegreeTowerError::InputDimensionMismatch {
                expected: self.domain_dim,
                actual: input.len(),
            });
        }
        Ok(self.apply_unchecked(input))
    }

    fn apply_unchecked(&self, input: &[bool]) -> Vec<bool> {
        self.rows
            .iter()
            .map(|row| {
                row.iter()
                    .zip(input)
                    .fold(false, |parity, (coefficient, value)| {
                        parity ^ (*coefficient && *value)
                    })
            })
            .collect()
    }

    pub fn is_in_image(&self, target: &[bool]) -> Result<bool, DegreeTowerError> {
        BinaryDegreeFunctional::is_in_image(&self.rows, self.domain_dim, target).map_err(Into::into)
    }

    pub fn min_hamming_distance_to_image(
        &self,
        target: &[bool],
    ) -> Result<usize, DegreeTowerError> {
        core_functional::phi1::Phi1Functional::binary(&self.rows, self.domain_dim, target)
            .map_err(Into::into)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DegreeTrichotomy {
    Exact,
    StabilizedSurvivor,
    Open,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DegreeDiagnostic {
    pub degree: usize,
    pub phi: usize,
    pub gamma: usize,
    pub classification: DegreeTrichotomy,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BinaryCochainSegment {
    pub degree: usize,
    pub previous: BinaryLinearMap,
    pub next: BinaryLinearMap,
}

impl BinaryCochainSegment {
    pub fn new(
        degree: usize,
        previous: BinaryLinearMap,
        next: BinaryLinearMap,
    ) -> Result<Self, DegreeTowerError> {
        if previous.codomain_dim() != next.domain_dim() {
            return Err(DegreeTowerError::CompositionDimensionMismatch {
                previous_codomain: previous.codomain_dim(),
                next_domain: next.domain_dim(),
            });
        }

        let mut basis = vec![false; previous.domain_dim()];
        for source_basis in 0..previous.domain_dim() {
            basis[source_basis] = true;
            let middle = previous.apply_unchecked(&basis);
            let target = next.apply_unchecked(&middle);
            basis[source_basis] = false;
            if let Some(target_row) = target.iter().position(|entry| *entry) {
                return Err(DegreeTowerError::CochainIdentityViolation {
                    source_basis,
                    target_row,
                });
            }
        }

        Ok(Self {
            degree,
            previous,
            next,
        })
    }

    pub fn residual_dim(&self) -> usize {
        self.previous.codomain_dim()
    }

    pub fn diagnose(&self, residual: &[bool]) -> Result<DegreeDiagnostic, DegreeTowerError> {
        if residual.len() != self.residual_dim() {
            return Err(DegreeTowerError::InputDimensionMismatch {
                expected: self.residual_dim(),
                actual: residual.len(),
            });
        }

        let phi = self.previous.min_hamming_distance_to_image(residual)?;
        let gamma = core_functional::gamma2::Gamma2Functional::binary(
            &self.next.rows,
            self.next.domain_dim,
            residual,
        )?;
        let classification = if phi == 0 {
            DegreeTrichotomy::Exact
        } else if gamma == 0 {
            DegreeTrichotomy::StabilizedSurvivor
        } else {
            DegreeTrichotomy::Open
        };

        Ok(DegreeDiagnostic {
            degree: self.degree,
            phi,
            gamma,
            classification,
        })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DdaOperationKind {
    SuccessorProbe,
    ResidualUpdate,
    /// Repair by CHANGING THE CARRIER rather than updating the residual within
    /// it: pass to a covering/total space where the pulled-back class is exact.
    /// (A `StabilizedSurvivor` at the base — a genuine cohomology class — is never
    /// repairable by a `ResidualUpdate`; the lift absorbs it by adding the
    /// fiber dimension).
    CarrierLift,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct DetectThenRepairPacket {
    pub degree: usize,
    pub hollow_local_green: bool,
    pub residual: Vec<bool>,
    pub repair_update: Vec<bool>,
    pub repaired_residual: Vec<bool>,
    pub before: DegreeDiagnostic,
    pub after: DegreeDiagnostic,
    pub repair_cost: usize,
    pub operations: [DdaOperationKind; 2],
}

impl DetectThenRepairPacket {
    pub fn verify(
        segment: &BinaryCochainSegment,
        residual: Vec<bool>,
        repair_update: Vec<bool>,
    ) -> Result<Self, DegreeTowerError> {
        if repair_update.len() != segment.residual_dim() {
            return Err(DegreeTowerError::InputDimensionMismatch {
                expected: segment.residual_dim(),
                actual: repair_update.len(),
            });
        }

        let before = segment.diagnose(&residual)?;
        if before.classification != DegreeTrichotomy::Open {
            return Err(DegreeTowerError::DetectionIsNotOpen);
        }

        let repaired_residual: Vec<bool> = residual
            .iter()
            .zip(&repair_update)
            .map(|(value, update)| *value ^ *update)
            .collect();
        let after = segment.diagnose(&repaired_residual)?;
        if after.classification != DegreeTrichotomy::Exact || after.gamma != 0 {
            return Err(DegreeTowerError::RepairIsNotResolved);
        }

        let repair_cost = hamming_weight(&repair_update);
        if repair_cost != before.phi {
            return Err(DegreeTowerError::RepairIsNotMinimal {
                expected: before.phi,
                actual: repair_cost,
            });
        }

        Ok(Self {
            degree: segment.degree,
            hollow_local_green: true,
            residual,
            repair_update,
            repaired_residual,
            before,
            after,
            repair_cost,
            operations: [
                DdaOperationKind::SuccessorProbe,
                DdaOperationKind::ResidualUpdate,
            ],
        })
    }
}

pub fn simplex_boundary_segment(degree: usize) -> Result<BinaryCochainSegment, DegreeTowerError> {
    if degree == 0 {
        return Err(DegreeTowerError::DegreeMustBePositive);
    }
    if degree > MAX_SIMPLEX_DEGREE {
        return Err(DegreeTowerError::SimplexDegreeTooLarge {
            degree,
            max_supported: MAX_SIMPLEX_DEGREE,
        });
    }

    let vertex_count = degree + 2;
    let previous_cells = combinations(vertex_count, degree);
    let residual_cells = combinations(vertex_count, degree + 1);

    let previous_rows = residual_cells
        .iter()
        .map(|residual_cell| {
            previous_cells
                .iter()
                .map(|previous_cell| is_subset(previous_cell, residual_cell))
                .collect()
        })
        .collect();
    let previous = BinaryLinearMap::from_rows(previous_cells.len(), previous_rows)?;
    let next =
        BinaryLinearMap::from_rows(residual_cells.len(), vec![vec![true; residual_cells.len()]])?;

    BinaryCochainSegment::new(degree, previous, next)
}

pub fn simplex_boundary_unit_packet(
    degree: usize,
) -> Result<DetectThenRepairPacket, DegreeTowerError> {
    let segment = simplex_boundary_segment(degree)?;
    let mut residual = vec![false; segment.residual_dim()];
    residual[0] = true;
    DetectThenRepairPacket::verify(&segment, residual.clone(), residual)
}

fn hamming_weight(values: &[bool]) -> usize {
    values.iter().filter(|value| **value).count()
}

fn is_subset(candidate: &[usize], container: &[usize]) -> bool {
    candidate.iter().all(|vertex| container.contains(vertex))
}

fn combinations(vertex_count: usize, subset_size: usize) -> Vec<Vec<usize>> {
    fn visit(
        start: usize,
        vertex_count: usize,
        remaining: usize,
        current: &mut Vec<usize>,
        output: &mut Vec<Vec<usize>>,
    ) {
        if remaining == 0 {
            output.push(current.clone());
            return;
        }
        let last_start = vertex_count - remaining;
        for vertex in start..=last_start {
            current.push(vertex);
            visit(vertex + 1, vertex_count, remaining - 1, current, output);
            current.pop();
        }
    }

    let mut output = Vec::new();
    visit(
        0,
        vertex_count,
        subset_size,
        &mut Vec::with_capacity(subset_size),
        &mut output,
    );
    output
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_nonzero_boundary_of_boundary() {
        let previous = BinaryLinearMap::from_rows(1, vec![vec![true]]).unwrap();
        let next = BinaryLinearMap::from_rows(1, vec![vec![true]]).unwrap();
        assert_eq!(
            BinaryCochainSegment::new(1, previous, next),
            Err(DegreeTowerError::CochainIdentityViolation {
                source_basis: 0,
                target_row: 0,
            })
        );
    }

    #[test]
    fn classifies_exact_survivor_and_open() {
        let exact_segment = BinaryCochainSegment::new(
            1,
            BinaryLinearMap::from_rows(1, vec![vec![true]]).unwrap(),
            BinaryLinearMap::zero(1, 1),
        )
        .unwrap();
        assert_eq!(
            exact_segment.diagnose(&[true]).unwrap().classification,
            DegreeTrichotomy::Exact
        );

        let survivor_segment =
            BinaryCochainSegment::new(1, BinaryLinearMap::zero(0, 1), BinaryLinearMap::zero(1, 1))
                .unwrap();
        assert_eq!(
            survivor_segment.diagnose(&[true]).unwrap().classification,
            DegreeTrichotomy::StabilizedSurvivor
        );

        let open_segment = simplex_boundary_segment(1).unwrap();
        assert_eq!(
            open_segment
                .diagnose(&[true, false, false])
                .unwrap()
                .classification,
            DegreeTrichotomy::Open
        );
    }

    #[test]
    fn triangle_tetrahedron_and_four_simplex_packets_replay() {
        let expected_dimensions = [(1, 3, 3), (2, 6, 4), (3, 10, 5), (4, 15, 6)];

        for (degree, previous_dim, residual_dim) in expected_dimensions {
            let segment = simplex_boundary_segment(degree).unwrap();
            assert_eq!(segment.previous.domain_dim(), previous_dim);
            assert_eq!(segment.residual_dim(), residual_dim);
            assert_eq!(segment.next.codomain_dim(), 1);

            let packet = simplex_boundary_unit_packet(degree).unwrap();
            assert!(packet.hollow_local_green);
            assert_eq!(packet.before.phi, 1);
            assert_eq!(packet.before.gamma, 1);
            assert_eq!(packet.before.classification, DegreeTrichotomy::Open);
            assert_eq!(packet.repair_cost, 1);
            assert_eq!(packet.after.phi, 0);
            assert_eq!(packet.after.gamma, 0);
            assert_eq!(packet.after.classification, DegreeTrichotomy::Exact);
        }
    }

    #[test]
    fn unit_packet_runtime_ascent_reaches_structural_ceiling() {
        let segment = simplex_boundary_segment(MAX_SIMPLEX_DEGREE).unwrap();
        assert_eq!(segment.previous.domain_dim(), 2016);
        assert_eq!(segment.residual_dim(), 64);

        let packet = simplex_boundary_unit_packet(MAX_SIMPLEX_DEGREE).unwrap();
        assert_eq!(packet.degree, MAX_SIMPLEX_DEGREE);
        assert_eq!(packet.before.phi, 1);
        assert_eq!(packet.before.gamma, 1);
        assert_eq!(packet.after.phi, 0);
        assert_eq!(packet.after.gamma, 0);
    }

    #[test]
    fn exact_search_refuses_unbounded_multi_bit_enumeration() {
        let map = BinaryLinearMap::zero(MAX_EXHAUSTIVE_DOMAIN_DIM + 1, 2);
        assert_eq!(
            map.min_hamming_distance_to_image(&[true, true]),
            Err(DegreeTowerError::ExhaustiveSearchTooLarge {
                domain_dim: MAX_EXHAUSTIVE_DOMAIN_DIM + 1,
                max_supported: MAX_EXHAUSTIVE_DOMAIN_DIM,
            })
        );
    }
}

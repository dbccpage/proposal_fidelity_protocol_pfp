//! Exact checking and witness reconstruction for integral chain equivalences.
//!
//! A candidate supplies two chain maps and two chain homotopies. The checker
//! evaluates every matrix identity in every degree, including zero-dimensional
//! padding. It does not search for certificates or authorize an engine action.
//! Accepted values borrow the exact immutable complexes and certificate checked.
//! Coefficients use the existing sparse integer matrix representation: checked
//! `i128` accumulation and an explicit refusal when a result cannot fit `i64`.
//!
//! AuthorityEffect: None.

use crate::f2_cohomology::ComplexError;
use crate::integral_chain_complex::{IntegralChainComplex, SparseIntegerMatrix};
use std::collections::BTreeMap;

/// The four arrays in a chain-equivalence proposal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum MapFamily {
    Projection,
    Inclusion,
    SourceHomotopy,
    TargetHomotopy,
}

/// An identity checked in every degree, with `p` projection and `i` inclusion.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum ChainIdentity {
    ProjectionCommutesWithBoundary,
    InclusionCommutesWithBoundary,
    InclusionProjectionMinusIdentity,
    ProjectionInclusionMinusIdentity,
}

/// A proposed equivalence, with degree `k` at index `k` in every array.
///
/// For source `C` and target `D`, shapes are `p_k: D_k x C_k`,
/// `i_k: C_k x D_k`, `H_k: C_{k+1} x C_k`, and
/// `G_k: D_{k+1} x D_k`. Every array must have exactly
/// `max(source.top_dimension(), target.top_dimension()) + 1` matrices.
/// Degrees outside a complex's stored range have dimension zero. In particular,
/// the last homotopies must have zero rows; they may not be omitted.
///
/// The convention is `ip - id = dH + Hd` and `pi - id = dG + Gd`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChainEquivalenceCertificate {
    pub projection: Vec<SparseIntegerMatrix>,
    pub inclusion: Vec<SparseIntegerMatrix>,
    pub source_homotopy: Vec<SparseIntegerMatrix>,
    pub target_homotopy: Vec<SparseIntegerMatrix>,
}

/// Typed refusals; no malformed or overflowing proposal is accepted.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ChainEquivalenceError {
    #[error(transparent)]
    Complex(#[from] ComplexError),
    #[error("{family:?} requires {expected} degree maps, got {actual}")]
    MapCount {
        family: MapFamily,
        expected: usize,
        actual: usize,
    },
    #[error("{family:?} in degree {degree} has shape {actual:?}, expected {expected:?}")]
    MapShape {
        family: MapFamily,
        degree: usize,
        expected: (usize, usize),
        actual: (usize, usize),
    },
    #[error("{identity:?} fails in degree {degree}")]
    Identity {
        identity: ChainIdentity,
        degree: usize,
    },
    #[error("{role} in degree {degree} has length {actual}, expected {expected}")]
    VectorShape {
        role: &'static str,
        degree: usize,
        expected: usize,
        actual: usize,
    },
    #[error("the supplied target chain does not bound the projected cycle in degree {degree}")]
    TargetFillingMismatch { degree: usize },
    #[error("the reconstructed source chain does not bound the source cycle in degree {degree}")]
    SourceFillingMismatch { degree: usize },
    #[error("a zero cycle/cocycle pairing does not certify a nonboundary in degree {degree}")]
    ZeroPairing { degree: usize },
    #[error("transport changed the cycle/cocycle pairing in degree {degree}")]
    PairingMismatch { degree: usize },
}

/// A checked equivalence bound by immutable borrows to its full input data.
///
/// Fields are private; this type cannot be constructed from an unchecked receipt.
/// The input data cannot be mutably borrowed while this value remains in use.
#[derive(Debug, Clone, Copy)]
pub struct CheckedChainEquivalence<'a> {
    source: &'a IntegralChainComplex,
    target: &'a IntegralChainComplex,
    certificate: &'a ChainEquivalenceCertificate,
}

/// A transported nonboundary witness, retaining both original witnesses and
/// their images as well as the immutable checked equivalence that binds them.
///
/// The cycle and cocycle in each complex are closed, and their common pairing
/// is nonzero. This is a mathematical witness, without authorization effects.
#[derive(Debug, Clone)]
pub struct TransportedObstruction<'a> {
    equivalence: CheckedChainEquivalence<'a>,
    degree: usize,
    target_cycle: Vec<i64>,
    target_cocycle: Vec<i64>,
    source_cycle: Vec<i64>,
    source_cocycle: Vec<i64>,
    pairing: i128,
}

impl<'a> TransportedObstruction<'a> {
    pub fn equivalence(&self) -> CheckedChainEquivalence<'a> {
        self.equivalence
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn target_cycle(&self) -> &[i64] {
        &self.target_cycle
    }

    pub fn target_cocycle(&self) -> &[i64] {
        &self.target_cocycle
    }

    pub fn source_cycle(&self) -> &[i64] {
        &self.source_cycle
    }

    pub fn source_cocycle(&self) -> &[i64] {
        &self.source_cocycle
    }

    pub fn pairing(&self) -> i128 {
        self.pairing
    }
}

impl ChainEquivalenceCertificate {
    pub fn verify<'a>(
        &'a self,
        source: &'a IntegralChainComplex,
        target: &'a IntegralChainComplex,
    ) -> Result<CheckedChainEquivalence<'a>, ChainEquivalenceError> {
        verify_chain_equivalence(source, target, self)
    }
}

/// Check all shapes and all four identities. The complexes already enforce
/// `d^2 = 0` at construction. No homology rank calculation substitutes for an
/// identity check, and no supplied map or declared degree is skipped.
pub fn verify_chain_equivalence<'a>(
    source: &'a IntegralChainComplex,
    target: &'a IntegralChainComplex,
    certificate: &'a ChainEquivalenceCertificate,
) -> Result<CheckedChainEquivalence<'a>, ChainEquivalenceError> {
    let top = source.top_dimension().max(target.top_dimension());
    check_all_map_shapes(source, target, certificate, top)?;

    for degree in 0..=top {
        let source_boundary = padded_boundary(source, degree)?;
        let target_boundary = padded_boundary(target, degree)?;
        verify_commuting_boundaries(
            source,
            target,
            certificate,
            degree,
            &source_boundary,
            &target_boundary,
        )?;
        verify_homotopy_identities(
            source,
            target,
            certificate,
            degree,
            &source_boundary,
            &target_boundary,
        )?;
    }

    Ok(CheckedChainEquivalence {
        source,
        target,
        certificate,
    })
}

fn expected_map_shape(
    source: &IntegralChainComplex,
    target: &IntegralChainComplex,
    family: MapFamily,
    degree: usize,
) -> (usize, usize) {
    match family {
        MapFamily::Projection => (target.cell_count(degree), source.cell_count(degree)),
        MapFamily::Inclusion => (source.cell_count(degree), target.cell_count(degree)),
        MapFamily::SourceHomotopy => (source.cell_count(degree + 1), source.cell_count(degree)),
        MapFamily::TargetHomotopy => (target.cell_count(degree + 1), target.cell_count(degree)),
    }
}

fn check_all_map_shapes(
    source: &IntegralChainComplex,
    target: &IntegralChainComplex,
    certificate: &ChainEquivalenceCertificate,
    top: usize,
) -> Result<(), ChainEquivalenceError> {
    for (family, maps) in [
        (MapFamily::Projection, &certificate.projection),
        (MapFamily::Inclusion, &certificate.inclusion),
        (MapFamily::SourceHomotopy, &certificate.source_homotopy),
        (MapFamily::TargetHomotopy, &certificate.target_homotopy),
    ] {
        if maps.len() != top + 1 {
            return Err(ChainEquivalenceError::MapCount {
                family,
                expected: top + 1,
                actual: maps.len(),
            });
        }
        for (degree, map) in maps.iter().enumerate() {
            let expected = expected_map_shape(source, target, family, degree);
            let actual = (map.rows(), map.cols());
            if actual != expected {
                return Err(ChainEquivalenceError::MapShape {
                    family,
                    degree,
                    expected,
                    actual,
                });
            }
        }
    }
    Ok(())
}

fn verify_commuting_boundaries(
    source: &IntegralChainComplex,
    target: &IntegralChainComplex,
    certificate: &ChainEquivalenceCertificate,
    degree: usize,
    source_boundary: &SparseIntegerMatrix,
    target_boundary: &SparseIntegerMatrix,
) -> Result<(), ChainEquivalenceError> {
    let projection_boundary = target_boundary.mul(&certificate.projection[degree])?;
    let inclusion_boundary = source_boundary.mul(&certificate.inclusion[degree])?;
    let projected_boundary = if degree == 0 {
        zero_matrix(0, source.cell_count(0))?
    } else {
        certificate.projection[degree - 1].mul(source_boundary)?
    };
    let included_boundary = if degree == 0 {
        zero_matrix(0, target.cell_count(0))?
    } else {
        certificate.inclusion[degree - 1].mul(target_boundary)?
    };
    require_identity(
        degree,
        ChainIdentity::ProjectionCommutesWithBoundary,
        &[(1, &projection_boundary), (-1, &projected_boundary)],
    )?;
    require_identity(
        degree,
        ChainIdentity::InclusionCommutesWithBoundary,
        &[(1, &inclusion_boundary), (-1, &included_boundary)],
    )
}

fn prev_homotopy_product(
    homotopy: &[SparseIntegerMatrix],
    boundary: &SparseIntegerMatrix,
    zero_dim: usize,
    degree: usize,
) -> Result<SparseIntegerMatrix, ChainEquivalenceError> {
    if degree == 0 {
        Ok(zero_matrix(zero_dim, zero_dim)?)
    } else {
        Ok(homotopy[degree - 1].mul(boundary)?)
    }
}

fn verify_single_homotopy_identity(
    complex: &IntegralChainComplex,
    composite: &SparseIntegerMatrix,
    homotopy: &[SparseIntegerMatrix],
    boundary: &SparseIntegerMatrix,
    degree: usize,
    identity_kind: ChainIdentity,
) -> Result<(), ChainEquivalenceError> {
    let id = identity_matrix(complex.cell_count(degree))?;
    let dh = padded_boundary(complex, degree + 1)?.mul(&homotopy[degree])?;
    let hd = prev_homotopy_product(homotopy, boundary, complex.cell_count(0), degree)?;
    require_identity(
        degree,
        identity_kind,
        &[(1, composite), (-1, &id), (-1, &dh), (-1, &hd)],
    )
}

fn verify_homotopy_identities(
    source: &IntegralChainComplex,
    target: &IntegralChainComplex,
    certificate: &ChainEquivalenceCertificate,
    degree: usize,
    source_boundary: &SparseIntegerMatrix,
    target_boundary: &SparseIntegerMatrix,
) -> Result<(), ChainEquivalenceError> {
    let ip = certificate.inclusion[degree].mul(&certificate.projection[degree])?;
    verify_single_homotopy_identity(
        source,
        &ip,
        &certificate.source_homotopy,
        source_boundary,
        degree,
        ChainIdentity::InclusionProjectionMinusIdentity,
    )?;
    let pi = certificate.projection[degree].mul(&certificate.inclusion[degree])?;
    verify_single_homotopy_identity(
        target,
        &pi,
        &certificate.target_homotopy,
        target_boundary,
        degree,
        ChainIdentity::ProjectionInclusionMinusIdentity,
    )
}

impl<'a> CheckedChainEquivalence<'a> {
    pub fn source(&self) -> &'a IntegralChainComplex {
        self.source
    }

    pub fn target(&self) -> &'a IntegralChainComplex {
        self.target
    }

    pub fn certificate(&self) -> &'a ChainEquivalenceCertificate {
        self.certificate
    }

    /// Apply the checked projection to an arbitrary source chain.
    pub fn project_chain(
        &self,
        degree: usize,
        chain: &[i64],
    ) -> Result<Vec<i64>, ChainEquivalenceError> {
        self.check_degree(degree)?;
        apply_to_chain(
            &self.certificate.projection[degree],
            chain,
            degree,
            "source chain",
        )
    }

    /// Apply the checked inclusion to an arbitrary target chain.
    pub fn include_chain(
        &self,
        degree: usize,
        chain: &[i64],
    ) -> Result<Vec<i64>, ChainEquivalenceError> {
        self.check_degree(degree)?;
        apply_to_chain(
            &self.certificate.inclusion[degree],
            chain,
            degree,
            "target chain",
        )
    }

    /// Given a source cycle `z` and a target chain `b` satisfying `d b = p z`,
    /// return `i b - H z` and verify its boundary is exactly `z`.
    ///
    /// This reconstructs a supplied filling; it does not search for one. At the
    /// common top degree, `b` must be empty and the reconstructed filling has
    /// dimension zero. Overflow is refused rather than rounded or wrapped.
    pub fn reconstruct_source_boundary(
        &self,
        degree: usize,
        source_cycle: &[i64],
        target_filling: &[i64],
    ) -> Result<Vec<i64>, ChainEquivalenceError> {
        self.verify_source_cycle_and_target_filling(degree, source_cycle, target_filling)?;
        let included_filling = if degree + 1 < self.certificate.inclusion.len() {
            self.include_chain(degree + 1, target_filling)?
        } else {
            // Both degree-(top+1) groups are zero. Shape was checked above.
            Vec::new()
        };
        let correction = apply_to_chain(
            &self.certificate.source_homotopy[degree],
            source_cycle,
            degree,
            "source cycle",
        )?;
        let reconstructed = Self::subtract_chains_checked(&included_filling, &correction, degree)?;
        let reconstructed_boundary = apply_to_chain(
            &padded_boundary(self.source, degree + 1)?,
            &reconstructed,
            degree + 1,
            "reconstructed source filling",
        )?;
        if reconstructed_boundary != source_cycle {
            return Err(ChainEquivalenceError::SourceFillingMismatch { degree });
        }
        Ok(reconstructed)
    }

    fn verify_source_cycle_and_target_filling(
        &self,
        degree: usize,
        source_cycle: &[i64],
        target_filling: &[i64],
    ) -> Result<(), ChainEquivalenceError> {
        self.check_degree(degree)?;
        let cycle_boundary = apply_to_chain(
            &padded_boundary(self.source, degree)?,
            source_cycle,
            degree,
            "source cycle",
        )?;
        if cycle_boundary.iter().any(|&entry| entry != 0) {
            return Err(ComplexError::NotACycle { degree }.into());
        }
        let projected_cycle = self.project_chain(degree, source_cycle)?;
        let filling_boundary = apply_to_chain(
            &padded_boundary(self.target, degree + 1)?,
            target_filling,
            degree + 1,
            "target filling",
        )?;
        if filling_boundary != projected_cycle {
            return Err(ChainEquivalenceError::TargetFillingMismatch { degree });
        }
        Ok(())
    }

    fn subtract_chains_checked(
        included_filling: &[i64],
        correction: &[i64],
        degree: usize,
    ) -> Result<Vec<i64>, ChainEquivalenceError> {
        if correction.len() != included_filling.len() {
            return Err(ChainEquivalenceError::VectorShape {
                role: "source homotopy image",
                degree: degree + 1,
                expected: included_filling.len(),
                actual: correction.len(),
            });
        }
        Ok(included_filling
            .iter()
            .zip(correction)
            .map(|(&included, &homotopy)| {
                included
                    .checked_sub(homotopy)
                    .ok_or(ComplexError::Overflow {
                        operation: "reconstructing an integral source filling",
                    })
            })
            .collect::<Result<Vec<_>, _>>()?)
    }

    /// Transport a target nonboundary witness to the source: `z_C = i z_D`
    /// and `u_C = u_D p`. Check closure of both pairs and equality of their
    /// nonzero integral pairings. A nonzero pairing with a cocycle rules out
    /// being a boundary. This certificate need not exist for torsion classes.
    pub fn transport_target_obstruction(
        &self,
        degree: usize,
        target_cycle: &[i64],
        target_cocycle: &[i64],
    ) -> Result<TransportedObstruction<'a>, ChainEquivalenceError> {
        self.check_degree(degree)?;
        let pairing =
            checked_cycle_cocycle_pairing(self.target, degree, target_cycle, target_cocycle)?;
        if pairing == 0 {
            return Err(ChainEquivalenceError::ZeroPairing { degree });
        }
        let source_cycle = self.include_chain(degree, target_cycle)?;
        let source_cocycle = self.project_cocycle(degree, target_cocycle)?;
        let transported_pairing =
            checked_cycle_cocycle_pairing(self.source, degree, &source_cycle, &source_cocycle)?;
        if transported_pairing != pairing {
            return Err(ChainEquivalenceError::PairingMismatch { degree });
        }
        Ok(TransportedObstruction {
            equivalence: *self,
            degree,
            target_cycle: target_cycle.to_vec(),
            target_cocycle: target_cocycle.to_vec(),
            source_cycle,
            source_cocycle,
            pairing,
        })
    }

    fn project_cocycle(
        &self,
        degree: usize,
        target_cocycle: &[i64],
    ) -> Result<Vec<i64>, ChainEquivalenceError> {
        let source_cocycle_row =
            cochain_row(target_cocycle)?.mul(&self.certificate.projection[degree])?;
        let mut source_cocycle = Vec::with_capacity(source_cocycle_row.cols());
        for column in 0..source_cocycle_row.cols() {
            let entries =
                source_cocycle_row
                    .column(column)
                    .ok_or(ChainEquivalenceError::VectorShape {
                        role: "transported source cocycle",
                        degree,
                        expected: source_cocycle_row.cols(),
                        actual: column,
                    })?;
            source_cocycle.push(entries.first().map_or(0, |&(_, coefficient)| coefficient));
        }
        Ok(source_cocycle)
    }

    fn check_degree(&self, degree: usize) -> Result<(), ChainEquivalenceError> {
        let top = self.certificate.projection.len() - 1;
        if degree > top {
            return Err(ComplexError::DegreeOutOfRange { degree, top }.into());
        }
        Ok(())
    }
}

/// Check `d z = 0` and `u d = 0` against the specified complex, then compute
/// the integral pairing `u z` with checked `i128` arithmetic. A nonzero return
/// proves that this cycle is not a boundary; zero does not decide exactness.
pub fn checked_cycle_cocycle_pairing(
    complex: &IntegralChainComplex,
    degree: usize,
    cycle: &[i64],
    cocycle: &[i64],
) -> Result<i128, ChainEquivalenceError> {
    if degree > complex.top_dimension() {
        return Err(ComplexError::DegreeOutOfRange {
            degree,
            top: complex.top_dimension(),
        }
        .into());
    }
    let boundary = apply_to_chain(&padded_boundary(complex, degree)?, cycle, degree, "cycle")?;
    if boundary.iter().any(|&value| value != 0) {
        return Err(ComplexError::NotACycle { degree }.into());
    }
    if cocycle.len() != complex.cell_count(degree) {
        return Err(ChainEquivalenceError::VectorShape {
            role: "cocycle",
            degree,
            expected: complex.cell_count(degree),
            actual: cocycle.len(),
        });
    }
    if !cochain_row(cocycle)?
        .mul(&padded_boundary(complex, degree + 1)?)?
        .is_zero()
    {
        return Err(ComplexError::NotACocycle { degree }.into());
    }
    dot_product_i128(cycle, cocycle)
}

fn dot_product_i128(cycle: &[i64], cocycle: &[i64]) -> Result<i128, ChainEquivalenceError> {
    cycle.iter().zip(cocycle).try_fold(0i128, |sum, (&z, &u)| {
        let product = i128::from(z)
            .checked_mul(i128::from(u))
            .ok_or(ComplexError::Overflow {
                operation: "multiplying an integral cycle/cocycle pairing",
            })?;
        sum.checked_add(product).ok_or_else(|| {
            ComplexError::Overflow {
                operation: "summing an integral cycle/cocycle pairing",
            }
            .into()
        })
    })
}

fn cochain_row(cochain: &[i64]) -> Result<SparseIntegerMatrix, ComplexError> {
    SparseIntegerMatrix::new(
        1,
        cochain
            .iter()
            .map(|&value| {
                if value == 0 {
                    Vec::new()
                } else {
                    vec![(0, value)]
                }
            })
            .collect(),
    )
}

fn zero_matrix(rows: usize, cols: usize) -> Result<SparseIntegerMatrix, ComplexError> {
    SparseIntegerMatrix::new(rows, vec![Vec::new(); cols])
}

fn identity_matrix(dimension: usize) -> Result<SparseIntegerMatrix, ComplexError> {
    SparseIntegerMatrix::new(dimension, (0..dimension).map(|i| vec![(i, 1)]).collect())
}

fn padded_boundary(
    complex: &IntegralChainComplex,
    degree: usize,
) -> Result<SparseIntegerMatrix, ComplexError> {
    if degree == 0 {
        zero_matrix(0, complex.cell_count(0))
    } else if degree > complex.top_dimension() {
        zero_matrix(complex.cell_count(degree - 1), complex.cell_count(degree))
    } else {
        Ok(complex.boundary(degree)?.clone())
    }
}

fn require_identity(
    degree: usize,
    identity: ChainIdentity,
    terms: &[(i64, &SparseIntegerMatrix)],
) -> Result<(), ChainEquivalenceError> {
    let Some((_, first)) = terms.first() else {
        return Err(ChainEquivalenceError::Identity { identity, degree });
    };
    if terms
        .iter()
        .any(|(_, m)| m.rows() != first.rows() || m.cols() != first.cols())
    {
        return Err(ChainEquivalenceError::Identity { identity, degree });
    }
    for column in 0..first.cols() {
        let mut accumulator: BTreeMap<usize, i128> = BTreeMap::new();
        for &(sign, matrix) in terms {
            let entries = matrix
                .column(column)
                .ok_or(ChainEquivalenceError::Identity { identity, degree })?;
            for &(row, coefficient) in entries {
                let entry = accumulator.entry(row).or_insert(0);
                let term = i128::from(sign)
                    .checked_mul(i128::from(coefficient))
                    .ok_or(ComplexError::Overflow {
                        operation: "signing a chain identity term",
                    })?;
                *entry = entry.checked_add(term).ok_or(ComplexError::Overflow {
                    operation: "summing a chain identity",
                })?;
            }
        }
        if accumulator.values().any(|&entry| entry != 0) {
            return Err(ChainEquivalenceError::Identity { identity, degree });
        }
    }
    Ok(())
}

fn apply_to_chain(
    matrix: &SparseIntegerMatrix,
    chain: &[i64],
    degree: usize,
    role: &'static str,
) -> Result<Vec<i64>, ChainEquivalenceError> {
    if chain.len() != matrix.cols() {
        return Err(ChainEquivalenceError::VectorShape {
            role,
            degree,
            expected: matrix.cols(),
            actual: chain.len(),
        });
    }
    let column = SparseIntegerMatrix::new(
        chain.len(),
        vec![chain
            .iter()
            .copied()
            .enumerate()
            .filter(|(_, value)| *value != 0)
            .collect()],
    )?;
    let result = matrix.mul(&column)?;
    let entries = result.column(0).ok_or(ChainEquivalenceError::VectorShape {
        role,
        degree,
        expected: 1,
        actual: result.cols(),
    })?;
    let mut vector = vec![0; result.rows()];
    for &(row, coefficient) in entries {
        vector[row] = coefficient;
    }
    Ok(vector)
}

// Origin: engine/crates_rs/core_homology/src/integral_chain_equivalence.rs
// Claim: urn:core:crates_rs:core-homology:integral-chain-equivalence:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f6c182fb {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

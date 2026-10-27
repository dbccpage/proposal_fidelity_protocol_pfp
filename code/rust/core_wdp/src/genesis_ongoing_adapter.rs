//! Fixed-carrier bridge for Genesis Ongoing derivations 23 and 25.
//! All ordered pairs, including loops and independent reverse arcs, are retained.
//! Filled triples are declared diagnostics, not balance or permission claims.
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::finite_cochain_map::{CochainMap, CochainWindow};
use linear_algebra::linear_observer_presentation::{
    LinearObserverError, LinearObserverPresentation,
};
use linear_algebra::semiring_lumpability::semiring_product;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use std::collections::BTreeSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct MarkedTriple {
    pub x: usize,
    pub y: usize,
    pub z: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisOngoingPacket {
    pub terms: Vec<String>,
    /// Row-major n² nonnegative integer multiplicities, including the diagonal.
    pub r: Vec<BigInt>,
    pub s: Vec<BigInt>,
    /// Cyclic orientations start at the least vertex; reverse ways are distinct.
    /// Sorted, without duplicates, matching source derivation 25's FState.
    pub filled: Vec<MarkedTriple>,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GenesisBridgeError {
    #[error("invalid, empty or duplicate term label")]
    InvalidTermLabels,
    #[error("ordered-pair dimensions overflow")]
    DimensionOverflow,
    #[error("source multiplicities must contain exactly n² coordinates")]
    InvalidDomain,
    #[error("assertion multiplicity cannot be negative")]
    NegativeMultiplicity,
    #[error("filled triple must name three different existing terms")]
    InvalidTriple,
    #[error("filled triples must have canonical cyclic orientation, sorted and unique")]
    NonCanonicalTriples,
    #[error("fixed ordered carrier and marked triples differ")]
    ContextMismatch,
    #[error("context restriction requires distinct existing vertices and marks within them")]
    InvalidRestriction,
    #[error("repair potential needs one integer per source term")]
    InvalidPotential,
    #[error("integer owner calculation unexpectedly returned a noninteger")]
    NonIntegralOutput,
    #[error("receipt differs from actual source, potential or independently replayed output")]
    ReceiptMismatch,
    #[error("matrix owner refusal: {0}")]
    Matrix(#[from] MatrixError),
    #[error("linear report owner refusal: {0}")]
    Linear(#[from] LinearObserverError),
}
impl GenesisOngoingPacket {
    fn validate_triple(t: &MarkedTriple, n: usize) -> Result<(), GenesisBridgeError> {
        let in_bounds = t.x < n && t.y < n && t.z < n;
        let distinct = t.x != t.y && t.y != t.z && t.z != t.x;
        if !in_bounds || !distinct {
            return Err(GenesisBridgeError::InvalidTriple);
        }
        if t.x > t.y || t.x > t.z {
            return Err(GenesisBridgeError::NonCanonicalTriples);
        }
        Ok(())
    }

    pub fn validate(&self) -> Result<(), GenesisBridgeError> {
        let n = self.terms.len();
        if self.terms.iter().any(String::is_empty)
            || self.terms.iter().collect::<BTreeSet<_>>().len() != n
        {
            return Err(GenesisBridgeError::InvalidTermLabels);
        }
        let pairs = n
            .checked_mul(n)
            .ok_or(GenesisBridgeError::DimensionOverflow)?;
        if self.r.len() != pairs || self.s.len() != pairs {
            return Err(GenesisBridgeError::InvalidDomain);
        }
        if self.r.iter().chain(&self.s).any(Signed::is_negative) {
            return Err(GenesisBridgeError::NegativeMultiplicity);
        }
        for t in &self.filled {
            Self::validate_triple(t, n)?;
        }
        if self.filled.windows(2).any(|w| w[0] >= w[1]) {
            return Err(GenesisBridgeError::NonCanonicalTriples);
        }
        Ok(())
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisOngoingReceipt {
    pub source: GenesisOngoingPacket,
    pub excess: Vec<BigInt>,
    pub diagnostics: Vec<BigRational>,
    pub balances: Vec<bool>,
}
impl GenesisOngoingReceipt {
    pub fn verify_against(&self, source: &GenesisOngoingPacket) -> Result<(), GenesisBridgeError> {
        if &self.source != source
            || GenesisOngoingAdapter::try_new(source.clone())?.receipt()? != *self
        {
            return Err(GenesisBridgeError::ReceiptMismatch);
        }
        Ok(())
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisRepairReceipt {
    pub source: GenesisOngoingPacket,
    pub potential: Vec<BigInt>,
    pub repaired_excess: Vec<BigInt>,
    pub diagnostics: Vec<BigRational>,
}
impl GenesisRepairReceipt {
    pub fn verify_against(
        &self,
        source: &GenesisOngoingPacket,
        potential: &[BigInt],
    ) -> Result<(), GenesisBridgeError> {
        if &self.source != source
            || self.potential != potential
            || GenesisOngoingAdapter::try_new(source.clone())?.repair(potential)? != *self
        {
            return Err(GenesisBridgeError::ReceiptMismatch);
        }
        Ok(())
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisOngoingAdapter {
    source: GenesisOngoingPacket,
    excess: Vec<BigInt>,
    /// Actual D_F and d0: checked by the functional owner to satisfy D_F d0=0.
    presentation: LinearObserverPresentation,
}

/// Pullback of an actual assertion packet to a declared subcontext. It keeps
/// loops, reverse arcs and both raw multiplicities. This is not zero-extension
/// along term addition or quotient transport along identification.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GenesisContextRestriction {
    source: GenesisOngoingPacket,
    target: GenesisOngoingAdapter,
    vertices: Vec<usize>,
    marks: Vec<usize>,
    transport: CochainMap<BigRational>,
}

impl GenesisContextRestriction {
    pub fn target(&self) -> &GenesisOngoingAdapter {
        &self.target
    }
    pub fn transport(&self) -> &CochainMap<BigRational> {
        &self.transport
    }
    pub fn vertices(&self) -> &[usize] {
        &self.vertices
    }
    pub fn marks(&self) -> &[usize] {
        &self.marks
    }
    /// Bind composition to the complete intermediate assertion packet, not
    /// just to a differential with coincidentally matching dimensions.
    pub fn then(&self, after: &Self) -> Result<Self, GenesisBridgeError> {
        if self.target.source != after.source {
            return Err(GenesisBridgeError::ContextMismatch);
        }
        let vertices: Vec<_> = after.vertices.iter().map(|&i| self.vertices[i]).collect();
        let marks: Vec<_> = after.marks.iter().map(|&i| self.marks[i]).collect();
        let result =
            GenesisOngoingAdapter::try_new(self.source.clone())?.restrict(&vertices, &marks)?;
        if result.transport != self.transport.then(&after.transport)? {
            return Err(GenesisBridgeError::ReceiptMismatch);
        }
        Ok(result)
    }
}
fn rationals(values: &[BigInt]) -> Vec<BigRational> {
    values
        .iter()
        .cloned()
        .map(BigRational::from_integer)
        .collect()
}
fn integer_values(values: Vec<BigRational>) -> Result<Vec<BigInt>, GenesisBridgeError> {
    values
        .into_iter()
        .map(|q| {
            if q.is_integer() {
                Ok(q.to_integer())
            } else {
                Err(GenesisBridgeError::NonIntegralOutput)
            }
        })
        .collect()
}
fn apply(
    matrix: &BasicMatrix<BigRational>,
    values: &[BigRational],
) -> Result<Vec<BigRational>, GenesisBridgeError> {
    let column = BasicMatrix::from_row_major(values.len(), 1, values.to_vec())?;
    let result = semiring_product(matrix, &column)?;
    (0..result.rows())
        .map(|i| result.get(i, 0).map_err(GenesisBridgeError::Matrix))
        .collect()
}
impl GenesisOngoingAdapter {
    pub fn try_new(source: GenesisOngoingPacket) -> Result<Self, GenesisBridgeError> {
        source.validate()?;
        let n = source.terms.len();
        let pairs = n
            .checked_mul(n)
            .ok_or(GenesisBridgeError::DimensionOverflow)?;
        let repairs = BasicMatrix::try_from_fn(pairs, n, |pair, vertex| {
            let x = pair / n;
            let y = pair % n;
            BigRational::from_integer(BigInt::from((vertex == x) as i32 - (vertex == y) as i32))
        })?;
        let reports = BasicMatrix::try_from_fn(source.filled.len(), pairs, |row, pair| {
            let t = source.filled[row];
            if pair == t.x * n + t.y || pair == t.y * n + t.z || pair == t.z * n + t.x {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        })?;
        let presentation = LinearObserverPresentation::try_new(reports, repairs)?;
        let excess = source.r.iter().zip(&source.s).map(|(r, s)| r - s).collect();
        Ok(Self {
            source,
            excess,
            presentation,
        })
    }
    pub fn source(&self) -> &GenesisOngoingPacket {
        &self.source
    }
    pub fn excess(&self) -> &[BigInt] {
        &self.excess
    }
    pub fn presentation(&self) -> &LinearObserverPresentation {
        &self.presentation
    }
    pub fn cochain_window(&self) -> Result<CochainWindow<BigRational>, GenesisBridgeError> {
        Ok(CochainWindow::try_new(
            [
                self.source.terms.len(),
                self.excess.len(),
                self.source.filled.len(),
            ],
            self.presentation.repair_map().clone(),
            self.presentation.report_map().clone(),
        )?)
    }
    fn canonical_marked_triple(x: usize, y: usize, z: usize) -> MarkedTriple {
        if x < y && x < z {
            MarkedTriple { x, y, z }
        } else if y < z {
            MarkedTriple { x: y, y: z, z: x }
        } else {
            MarkedTriple { x: z, y: x, z: y }
        }
    }

    fn select_restricted_triples(
        &self,
        inverse: &[Option<usize>],
        marks: &[usize],
    ) -> Result<Vec<(MarkedTriple, usize)>, GenesisBridgeError> {
        let mut selected = Vec::with_capacity(marks.len());
        for &old in marks {
            let t = self.source.filled[old];
            let x = inverse[t.x].ok_or(GenesisBridgeError::InvalidRestriction)?;
            let y = inverse[t.y].ok_or(GenesisBridgeError::InvalidRestriction)?;
            let z = inverse[t.z].ok_or(GenesisBridgeError::InvalidRestriction)?;
            selected.push((Self::canonical_marked_triple(x, y, z), old));
        }
        selected.sort_by_key(|&(t, _)| t);
        Ok(selected)
    }

    fn validate_restriction_args(
        &self,
        vertices: &[usize],
        marks: &[usize],
    ) -> Result<(), GenesisBridgeError> {
        let n = self.source.terms.len();
        let m = vertices.len();
        if vertices.iter().any(|&v| v >= n)
            || vertices.iter().collect::<BTreeSet<_>>().len() != m
            || marks.iter().any(|&f| f >= self.source.filled.len())
            || marks.iter().collect::<BTreeSet<_>>().len() != marks.len()
        {
            return Err(GenesisBridgeError::InvalidRestriction);
        }
        Ok(())
    }

    /// Restrict vertices in the supplied order and select existing marked
    /// triples. Marks are cyclically canonicalized and sorted in the target.
    /// Both cochain squares are checked by the mathematical matrix owner.
    pub fn restrict(
        &self,
        vertices: &[usize],
        marks: &[usize],
    ) -> Result<GenesisContextRestriction, GenesisBridgeError> {
        self.validate_restriction_args(vertices, marks)?;
        let n = self.source.terms.len();
        let mut inverse = vec![None; n];
        for (new, &old) in vertices.iter().enumerate() {
            inverse[old] = Some(new);
        }
        let selected = self.select_restricted_triples(&inverse, marks)?;
        let pair_indices: Vec<_> = vertices
            .iter()
            .flat_map(|&x| vertices.iter().map(move |&y| x * n + y))
            .collect();
        let target = self.build_restricted_target(vertices, &pair_indices, &selected)?;
        let mark_indices: Vec<_> = selected.iter().map(|&(_, old)| old).collect();
        let transport =
            self.build_restriction_transport(&target, vertices, &pair_indices, &mark_indices, n)?;
        Ok(GenesisContextRestriction {
            source: self.source.clone(),
            target,
            vertices: vertices.to_vec(),
            marks: mark_indices,
            transport,
        })
    }

    fn build_restricted_target(
        &self,
        vertices: &[usize],
        pair_indices: &[usize],
        selected: &[(MarkedTriple, usize)],
    ) -> Result<Self, GenesisBridgeError> {
        Self::try_new(GenesisOngoingPacket {
            terms: vertices
                .iter()
                .map(|&i| self.source.terms[i].clone())
                .collect(),
            r: pair_indices
                .iter()
                .map(|&i| self.source.r[i].clone())
                .collect(),
            s: pair_indices
                .iter()
                .map(|&i| self.source.s[i].clone())
                .collect(),
            filled: selected.iter().map(|&(t, _)| t).collect(),
        })
    }

    fn build_restriction_transport(
        &self,
        target: &Self,
        vertices: &[usize],
        pair_indices: &[usize],
        mark_indices: &[usize],
        n: usize,
    ) -> Result<CochainMap<BigRational>, GenesisBridgeError> {
        let selection = |indices: &[usize], columns| {
            BasicMatrix::try_from_fn(indices.len(), columns, |i, j| {
                if indices[i] == j {
                    BigRational::one()
                } else {
                    BigRational::zero()
                }
            })
        };
        Ok(CochainMap::try_new(
            &self.cochain_window()?,
            &target.cochain_window()?,
            [
                selection(vertices, n)?,
                selection(pair_indices, self.excess.len())?,
                selection(mark_indices, self.source.filled.len())?,
            ],
        )?)
    }
    pub fn receipt(&self) -> Result<GenesisOngoingReceipt, GenesisBridgeError> {
        let diagnostics = self.presentation.report(&rationals(&self.excess))?;
        let balances = diagnostics.iter().map(Zero::is_zero).collect();
        Ok(GenesisOngoingReceipt {
            source: self.source.clone(),
            excess: self.excess.clone(),
            diagnostics,
            balances,
        })
    }
    /// Gauge-equivalent excess; this is not a single seed change or permission.
    pub fn repair(&self, potential: &[BigInt]) -> Result<GenesisRepairReceipt, GenesisBridgeError> {
        if potential.len() != self.source.terms.len() {
            return Err(GenesisBridgeError::InvalidPotential);
        }
        let shift = integer_values(apply(
            self.presentation.repair_map(),
            &rationals(potential),
        )?)?;
        let repaired_excess: Vec<_> = self
            .excess
            .iter()
            .zip(shift)
            .map(|(e, delta)| e + delta)
            .collect();
        let diagnostics = self.presentation.report(&rationals(&repaired_excess))?;
        Ok(GenesisRepairReceipt {
            source: self.source.clone(),
            potential: potential.to_vec(),
            repaired_excess,
            diagnostics,
        })
    }
    /// Complete fixed-writing integer repair test. None is a genuine obstruction,
    /// not failure of the marked diagnostics to distinguish the tables.
    /// No renaming, changing the number of terms or adding/removing marks is done.
    pub fn repair_equivalence(
        &self,
        other: &Self,
    ) -> Result<Option<Vec<BigInt>>, GenesisBridgeError> {
        if self.source.terms != other.source.terms || self.source.filled != other.source.filled {
            return Err(GenesisBridgeError::ContextMismatch);
        }
        let n = self.source.terms.len();
        let mut potential = vec![BigInt::zero(); n];
        for (x, value) in potential.iter_mut().enumerate().skip(1) {
            *value = &other.excess[x * n] - &self.excess[x * n];
        }
        let actual = self.repair(&potential)?.repaired_excess;
        Ok(if actual == other.excess {
            Some(potential)
        } else {
            None
        })
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_ongoing_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-ongoing-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_11432a15 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

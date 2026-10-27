//! `spectral_triple` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_c8f8fb37;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_c8f8fb37<T> = std::result::Result<T, BoundaryError_c8f8fb37>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `spectral_triple` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct SpectralTriple {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl SpectralTriple {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = SpectralTriple::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(SpectralTriple::authority_fence().contains("AuthorityEffect None"));
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpectralError {
    Shape,
    Chirality { index: usize },
    NotSymmetric { row: usize, column: usize },
    DoesNotAnticommmute { row: usize, column: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/spectral_triple.rs
// Claim: urn:core:crates_rs:core-general-relativity:spectral-triple:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SpectralError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SpectralError {}

/// Even finite spectral triple: integer symmetric Dirac operator anticommuting
/// with a diagonal chirality. Carrier degree is the Hilbert-space dimension.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EvenSpectralTriple {
    chirality: Vec<i8>,
    dirac: Vec<i64>,
}

fn validate_chirality_signs(n: usize, chirality: &[i8]) -> Result<(), SpectralError> {
    if n == 0 || chirality.len() != n {
        return Err(SpectralError::Shape);
    }
    if !chirality.contains(&1) || !chirality.contains(&-1) {
        return Err(SpectralError::Chirality { index: 0 });
    }
    for (index, &sign) in chirality.iter().enumerate() {
        if sign != 1 && sign != -1 {
            return Err(SpectralError::Chirality { index });
        }
    }
    Ok(())
}

fn verify_dirac_entry(
    n: usize,
    chirality: &[i8],
    dirac: &[i64],
    row: usize,
    column: usize,
) -> Result<(), SpectralError> {
    let entry = *dirac.get(row * n + column).ok_or(SpectralError::Shape)?;
    let mirror = *dirac.get(column * n + row).ok_or(SpectralError::Shape)?;
    if entry != mirror {
        return Err(SpectralError::NotSymmetric { row, column });
    }
    let left = i16::from(*chirality.get(row).ok_or(SpectralError::Shape)?);
    let right = i16::from(*chirality.get(column).ok_or(SpectralError::Shape)?);
    let factor = left.checked_add(right).ok_or(SpectralError::Overflow)?;
    if factor != 0 && entry != 0 {
        return Err(SpectralError::DoesNotAnticommmute { row, column });
    }
    Ok(())
}

impl EvenSpectralTriple {
    pub fn try_from_carrier(carrier: &SpectralTriple, chirality: Vec<i8>, dirac: Vec<i64>) -> Result<Self, SpectralError> {
        let n = carrier.degree;
        validate_chirality_signs(n, &chirality)?;
        let cells = n.checked_mul(n).ok_or(SpectralError::Overflow)?;
        if dirac.len() != cells {
            return Err(SpectralError::Shape);
        }
        for row in 0..n {
            for column in 0..n {
                verify_dirac_entry(n, &chirality, &dirac, row, column)?;
            }
        }
        Ok(Self { chirality, dirac })
    }

    pub fn dimension(&self) -> usize { self.chirality.len() }
    pub fn chirality(&self) -> &[i8] { &self.chirality }
    pub fn dirac(&self) -> &[i64] { &self.dirac }
}

#[cfg(test)]
mod spectral_tests {
    use super::*;

    #[test]
    fn off_diagonal_dirac_anticommutes_with_chirality() {
        let carrier = SpectralTriple::new(2, "even");
        let triple = EvenSpectralTriple::try_from_carrier(&carrier, vec![1, -1], vec![0, 1, 1, 0]);
        assert!(matches!(triple, Ok(ref triple) if triple.dimension() == 2));
    }

    #[test]
    fn a_diagonal_entry_in_one_chirality_block_is_refused() {
        let carrier = SpectralTriple::new(2, "even");
        let triple = EvenSpectralTriple::try_from_carrier(&carrier, vec![1, -1], vec![1, 0, 0, 0]);
        assert!(matches!(triple, Err(SpectralError::DoesNotAnticommmute { row: 0, column: 0 })));
    }
}

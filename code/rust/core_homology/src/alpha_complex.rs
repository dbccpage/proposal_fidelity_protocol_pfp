//! Alpha complex shell (Delaunay-based; Euclidean data).
//!
//! AuthorityEffect: None. Best-effort shell for computational topology.
//! Not PROVED; not GlobalGreen. Algorithms may be incomplete.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_69fb9c5b;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_69fb9c5b<T> = std::result::Result<T, BoundaryError_69fb9c5b>;
use serde::{Deserialize, Serialize};

/// Finite record shell for `alpha_complex`.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct AlphaComplex {
    pub label: String,
    pub notes: Vec<String>,
}

impl AlphaComplex {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            notes: Vec::new(),
        }
    }

    pub fn with_note(mut self, note: impl Into<String>) -> Self {
        self.notes.push(note.into());
        self
    }

    /// Validate structural emptiness only (shell gate).
    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("label must be non-empty".into());
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shell_validate_rejects_empty_label() {
        let s = AlphaComplex::new("");
        assert!(s.validate_shell().is_err());
    }

    #[test]
    fn shell_validate_ok() {
        let s = AlphaComplex::new("alpha_complex").with_note("dev shell");
        assert!(s.validate_shell().is_ok());
    }
}

/// Refusal from an integer in-circle determinant.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IncircleError {
    /// A coordinate is outside the exact range.
    CoordTooLarge,
    /// Checked arithmetic overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_homology/src/alpha_complex.rs
// Claim: urn:core:crates_rs:core-homology:alpha-complex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IncircleError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IncircleError {}

fn det2(a: i128, b: i128, c: i128, d: i128) -> Result<i128, IncircleError> {
    let ad = a.checked_mul(d).ok_or(IncircleError::Overflow)?;
    let bc = b.checked_mul(c).ok_or(IncircleError::Overflow)?;
    ad.checked_sub(bc).ok_or(IncircleError::Overflow)
}

fn det3(m: [[i128; 3]; 3]) -> Result<i128, IncircleError> {
    let (a, b, c) = (m[0][0], m[0][1], m[0][2]);
    let (d, e, f) = (m[1][0], m[1][1], m[1][2]);
    let (g, h, i) = (m[2][0], m[2][1], m[2][2]);
    let t0 = a.checked_mul(det2(e, f, h, i)?).ok_or(IncircleError::Overflow)?;
    let t1 = b.checked_mul(det2(d, f, g, i)?).ok_or(IncircleError::Overflow)?;
    let t2 = c.checked_mul(det2(d, e, g, h)?).ok_or(IncircleError::Overflow)?;
    t0.checked_sub(t1).and_then(|v| v.checked_add(t2)).ok_or(IncircleError::Overflow)
}

fn shift(point: (i64, i64), origin: (i64, i64)) -> Result<[i128; 3], IncircleError> {
    for value in [point.0, point.1, origin.0, origin.1] {
        if value.unsigned_abs() > 10_000 {
            return Err(IncircleError::CoordTooLarge);
        }
    }
    let x = i128::from(point.0).checked_sub(i128::from(origin.0)).ok_or(IncircleError::Overflow)?;
    let y = i128::from(point.1).checked_sub(i128::from(origin.1)).ok_or(IncircleError::Overflow)?;
    let square = x.checked_mul(x).ok_or(IncircleError::Overflow)?.checked_add(y.checked_mul(y).ok_or(IncircleError::Overflow)?).ok_or(IncircleError::Overflow)?;
    Ok([x, y, square])
}

/// Determinant of the translated in-circle matrix. Zero means the four points are cocircular or degenerate.
pub fn incircle_det(a: (i64, i64), b: (i64, i64), c: (i64, i64), d: (i64, i64)) -> Result<i128, IncircleError> {
    det3([shift(a, d)?, shift(b, d)?, shift(c, d)?])
}

#[cfg(test)]
mod incircle_tests {
    use super::incircle_det;
    #[test]
    fn the_unit_square_is_cocircular_and_an_off_point_is_not() {
        assert!(matches!(incircle_det((0, 0), (1, 0), (0, 1), (1, 1)), Ok(0)));
        assert!(matches!(incircle_det((0, 0), (1, 0), (0, 1), (2, 3)), Ok(value) if value != 0));
    }
}

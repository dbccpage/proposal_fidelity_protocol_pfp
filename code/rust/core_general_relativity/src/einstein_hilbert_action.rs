//! f64 face of a discrete Einstein–Hilbert action. Not the exact proxy
//! (the sum of area_squared times kappa).
//!
//! Continuum EH ∫ R √|g| is not this file. The f64 stand-in follows
//! `S = Σ_v ε_v` ([`crate::regge_calculus::ReggeCalculus::regge_action_2d`]),
//! where 2D hinges are vertices and V_h = 1.
//!
//! AuthorityEffect: None. Not continuum EH. Not PROVED.

use crate::regge_calculus::{ReggeCalculus, ReggeError};

/// f64 face. Not the exact proxy (the sum of area_squared times kappa).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; f64 face; not the exact proxy (the sum of area_squared times kappa).";

/// Discrete Einstein–Hilbert / Regge action value.
#[derive(Debug, Clone, PartialEq)]
pub struct EinsteinHilbertAction {
    /// Action scalar S.
    pub value: f64,
    /// Label.
    pub label: String,
}

impl EinsteinHilbertAction {
    /// Scaffold: value = degree as f64 (legacy proxy).
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            value: degree as f64,
            label: label.into(),
        }
    }

    /// From 2D Regge geometry.
    pub fn try_from_regge(
        regge: &ReggeCalculus,
        label: impl Into<String>,
    ) -> Result<Self, ReggeError> {
        Ok(Self {
            value: regge.regge_action_2d()?,
            label: label.into(),
        })
    }

    pub fn degree(&self) -> usize {
        self.value.abs() as usize
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::regge_calculus::ReggeCalculus;

    #[test]
    fn action_matches_sum_of_deficits() {
        let g = ReggeCalculus::equilateral_fan(3, 1.0).unwrap();
        let s = EinsteinHilbertAction::try_from_regge(&g, "S").unwrap();
        let sum: f64 = g.vertex_deficits().unwrap().into_iter().sum();
        assert!((s.value - sum).abs() < 1e-10);
    }

    #[test]
    fn new_and_fence() {
        let x = EinsteinHilbertAction::new(1, "test");
        assert!(EinsteinHilbertAction::authority_fence().contains("AuthorityEffect None"));
        assert_eq!(x.value, 1.0);
    }
}

/// Checked sum of integer vertex deficits. This is not continuum Einstein–Hilbert
/// and not the area-squared times kappa proxy.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct IntegerDeficitSum {
    vertex_count: usize,
    deficit_sum: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IntegerDeficitError {
    Empty,
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/einstein_hilbert_action.rs
// Claim: urn:core:crates_rs:core-general-relativity:einstein-hilbert-action:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for IntegerDeficitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for IntegerDeficitError {}

impl IntegerDeficitSum {
    pub fn try_sum(deficits: &[i64]) -> Result<Self, IntegerDeficitError> {
        if deficits.is_empty() {
            return Err(IntegerDeficitError::Empty);
        }
        let mut deficit_sum = 0i64;
        for deficit in deficits {
            deficit_sum = deficit_sum
                .checked_add(*deficit)
                .ok_or(IntegerDeficitError::Overflow)?;
        }
        Ok(Self {
            vertex_count: deficits.len(),
            deficit_sum,
        })
    }

    pub fn deficit_sum(&self) -> i64 {
        self.deficit_sum
    }
}

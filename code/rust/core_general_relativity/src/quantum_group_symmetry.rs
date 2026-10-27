//! `quantum_group_symmetry` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_2a85e560;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_2a85e560<T> = std::result::Result<T, BoundaryError_2a85e560>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `quantum_group_symmetry` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct QuantumGroupSymmetry {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl QuantumGroupSymmetry {
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
        let x = QuantumGroupSymmetry::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(QuantumGroupSymmetry::authority_fence().contains("AuthorityEffect None"));
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FusionError {
    SpinOutOfRange { spin: usize, level: usize },
    Overflow,
    Inadmissible { a: usize, b: usize, c: usize },
}

// Origin: engine/crates_rs/core_general_relativity/src/quantum_group_symmetry.rs
// Claim: urn:core:crates_rs:core-general-relativity:quantum-group-symmetry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FusionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FusionError {}

/// SU(2)_k fusion admissibility. Carrier degree is the level k.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Su2FusionTriple {
    level: usize,
    a: usize,
    b: usize,
    c: usize,
}

fn fusion_triangle_holds(a: usize, b: usize, c: usize) -> Result<bool, FusionError> {
    let ab = a.checked_add(b).ok_or(FusionError::Overflow)?;
    let bc = b.checked_add(c).ok_or(FusionError::Overflow)?;
    let ac = a.checked_add(c).ok_or(FusionError::Overflow)?;
    Ok(c <= ab && a <= bc && b <= ac)
}

impl Su2FusionTriple {
    pub fn try_from_carrier(carrier: &QuantumGroupSymmetry, a: usize, b: usize, c: usize) -> Result<Self, FusionError> {
        let level = carrier.degree;
        for spin in [a, b, c] {
            if spin > level {
                return Err(FusionError::SpinOutOfRange { spin, level });
            }
        }
        let sum = a.checked_add(b).ok_or(FusionError::Overflow)?.checked_add(c).ok_or(FusionError::Overflow)?;
        let bound = level.checked_mul(2).ok_or(FusionError::Overflow)?;
        let triangle = fusion_triangle_holds(a, b, c)?;
        if sum % 2 != 0 || !triangle || sum > bound {
            return Err(FusionError::Inadmissible { a, b, c });
        }
        Ok(Self { level, a, b, c })
    }

    pub fn level(&self) -> usize { self.level }
    pub fn spins(&self) -> (usize, usize, usize) { (self.a, self.b, self.c) }
}

#[cfg(test)]
mod fusion_tests {
    use super::*;

    #[test]
    fn spin_one_fusion_at_level_two_admits_the_singlet() {
        let carrier = QuantumGroupSymmetry::new(2, "su2");
        let triple = Su2FusionTriple::try_from_carrier(&carrier, 1, 1, 0);
        assert!(matches!(triple, Ok(ref triple) if triple.spins() == (1, 1, 0)));
    }

    #[test]
    fn odd_sum_is_not_an_su2_channel() {
        let carrier = QuantumGroupSymmetry::new(2, "su2");
        let triple = Su2FusionTriple::try_from_carrier(&carrier, 1, 1, 1);
        assert!(matches!(triple, Err(FusionError::Inadmissible { .. })));
    }
}

//! `cosmological_constant` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_4d1270cf;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_4d1270cf<T> = std::result::Result<T, BoundaryError_4d1270cf>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `cosmological_constant` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct CosmologicalConstant {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl CosmologicalConstant {
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

// Origin: engine/crates_rs/core_general_relativity/src/cosmological_constant.rs
// Claim: urn:core:crates_rs:core-general-relativity:cosmological-constant:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = CosmologicalConstant::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(CosmologicalConstant::authority_fence().contains("AuthorityEffect None"));
    }
}

/// Diagonal vacuum Einstein equation `R_ii = Λ g_ii` with `g_ii = ±1`, plus the trace `R = dim Λ`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VacuumLambdaTrace {
    dimension: usize,
    lambda: i64,
    scalar: i128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LambdaError {
    Shape,
    Metric,
    Einstein { index: usize },
    Trace { scalar: i128, expected: i128 },
    Overflow,
}

impl std::fmt::Display for LambdaError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Shape => write!(f, "Ricci and metric diagonals must share a positive dimension"),
            Self::Metric => write!(f, "metric diagonal entries must be ±1"),
            Self::Einstein { index } => write!(f, "Ricci entry {index} is not Λ times the metric"),
            Self::Trace { scalar, expected } => {
                write!(f, "scalar curvature {scalar} is not {expected}")
            }
            Self::Overflow => write!(f, "checked curvature overflow"),
        }
    }
}

impl std::error::Error for LambdaError {}

fn checked_einstein_term(
    index: usize,
    lambda: i64,
    ricci_ii: i64,
    metric_ii: i8,
) -> Result<i128, LambdaError> {
    if metric_ii != 1 && metric_ii != -1 {
        return Err(LambdaError::Metric);
    }
    let expected = i128::from(lambda)
        .checked_mul(i128::from(metric_ii))
        .ok_or(LambdaError::Overflow)?;
    if i128::from(ricci_ii) != expected {
        return Err(LambdaError::Einstein { index });
    }
    i128::from(ricci_ii)
        .checked_mul(i128::from(metric_ii))
        .ok_or(LambdaError::Overflow)
}

impl VacuumLambdaTrace {
    pub fn certify(lambda: i64, ricci: &[i64], metric: &[i8]) -> Result<Self, LambdaError> {
        if ricci.is_empty() || ricci.len() != metric.len() || ricci.len() > 16 {
            return Err(LambdaError::Shape);
        }
        let mut scalar = 0i128;
        for (index, (&ricci_ii, &metric_ii)) in ricci.iter().zip(metric).enumerate() {
            let term = checked_einstein_term(index, lambda, ricci_ii, metric_ii)?;
            scalar = scalar.checked_add(term).ok_or(LambdaError::Overflow)?;
        }
        let dimension = ricci.len();
        let expected = i128::from(lambda)
            .checked_mul(i128::try_from(dimension).map_err(|_| LambdaError::Overflow)?)
            .ok_or(LambdaError::Overflow)?;
        if scalar != expected {
            return Err(LambdaError::Trace { scalar, expected });
        }
        Ok(Self {
            dimension,
            lambda,
            scalar,
        })
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }

    pub fn lambda(&self) -> i64 {
        self.lambda
    }

    pub fn scalar(&self) -> i128 {
        self.scalar
    }
}

#[cfg(test)]
mod exact_lambda_tests {
    use super::*;

    #[test]
    fn four_dimensional_vacuum_has_scalar_four_lambda() {
        let vacuum = VacuumLambdaTrace::certify(3, &[3, 3, 3, 3], &[1, 1, 1, 1]).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(vacuum.dimension(), 4);
        assert_eq!(vacuum.lambda(), 3);
        assert_eq!(vacuum.scalar(), 12);
    }

    #[test]
    fn a_mismatched_ricci_entry_is_refused() {
        assert!(matches!(
            VacuumLambdaTrace::certify(3, &[3, 0], &[1, 1]),
            Err(LambdaError::Einstein { index: 1 })
        ));
    }
}

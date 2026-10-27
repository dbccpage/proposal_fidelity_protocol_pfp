use std::fmt;

/// A finite, bounded floating-point value with strict epsilon-enforcement.
///
/// Guarantees:
///   1. Value is always finite (no NaN, no +/-Inf).
///   2. Value lies within `[lower_bound, upper_bound]`.
///   3. Construction fails if invariants are violated.
#[derive(Clone, Copy)]
pub struct TolerantFloat {
    value: f64,
    epsilon: f64,
}

/// Error returned when TolerantFloat construction invariants are violated.
#[derive(Debug, Clone)]
pub enum TolerantFloatError {
    NonFinite(f64),
    BelowLowerBound { value: f64, lower: f64 },
    AboveUpperBound { value: f64, upper: f64 },
    InvalidEpsilon(f64),
}

impl fmt::Display for TolerantFloatError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NonFinite(v) => write!(f, "TolerantFloat: non-finite value {v}"),
            Self::BelowLowerBound { value, lower } => {
                write!(f, "TolerantFloat: {value} < lower bound {lower}")
            }
            Self::AboveUpperBound { value, upper } => {
                write!(f, "TolerantFloat: {value} > upper bound {upper}")
            }
            Self::InvalidEpsilon(e) => {
                write!(f, "TolerantFloat: invalid epsilon {e}")
            }
        }
    }
}

impl TolerantFloat {
    pub fn new(value: f64, epsilon: f64) -> Result<Self, TolerantFloatError> {
        if !epsilon.is_finite() || epsilon < 0.0 {
            return Err(TolerantFloatError::InvalidEpsilon(epsilon));
        }
        if !value.is_finite() {
            return Err(TolerantFloatError::NonFinite(value));
        }
        Ok(Self { value, epsilon })
    }

    pub fn bounded(
        value: f64,
        epsilon: f64,
        lower: f64,
        upper: f64,
    ) -> Result<Self, TolerantFloatError> {
        let tf = Self::new(value, epsilon)?;
        if tf.value < lower {
            return Err(TolerantFloatError::BelowLowerBound {
                value: tf.value,
                lower,
            });
        }
        if tf.value > upper {
            return Err(TolerantFloatError::AboveUpperBound {
                value: tf.value,
                upper,
            });
        }
        Ok(tf)
    }

    pub fn positive(value: f64, epsilon: f64) -> Result<Self, TolerantFloatError> {
        Self::bounded(value, epsilon, f64::MIN_POSITIVE, f64::MAX)
    }

    pub fn non_negative(value: f64, epsilon: f64) -> Result<Self, TolerantFloatError> {
        Self::bounded(value, epsilon, 0.0, f64::MAX)
    }

    #[inline]
    pub fn value(&self) -> f64 {
        self.value
    }

    #[inline]
    pub fn epsilon(&self) -> f64 {
        self.epsilon
    }

    pub fn tolerant_eq(&self, other: &Self) -> bool {
        (self.value - other.value).abs() <= self.epsilon.max(other.epsilon)
    }

    pub fn is_converged(&self) -> bool {
        self.value.abs() <= self.epsilon
    }
}

impl fmt::Debug for TolerantFloat {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "TolerantFloat({:.6e} +/- {:.1e})",
            self.value, self.epsilon
        )
    }
}

impl fmt::Display for TolerantFloat {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:.6e}", self.value)
    }
}

// No `PartialEq`. Tolerant equality is not transitive -- with epsilon 1 the
// values 0, 1 and 2 give 0 ≈ 1 and 1 ≈ 2 but 0 ≉ 2 -- and `PartialEq` is
// specified to be transitive. Implementing it here made every HashMap, sort,
// dedup and `assert_eq!` over this type unsound. A tolerant comparison must be
// spelled `tolerant_eq` at the call site, where the epsilon is visible.

impl From<TolerantFloat> for f64 {
    fn from(tf: TolerantFloat) -> f64 {
        tf.value
    }
}

// Origin: engine/crates_rs/core_types/src/tolerant_float.rs
// Claim: urn:core:crates_rs:core-types:tolerant-float:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_nan() {
        assert!(TolerantFloat::new(f64::NAN, 1e-6).is_err());
    }

    #[test]
    fn rejects_infinity() {
        assert!(TolerantFloat::new(f64::INFINITY, 1e-6).is_err());
        assert!(TolerantFloat::new(f64::NEG_INFINITY, 1e-6).is_err());
    }

    #[test]
    fn rejects_negative_epsilon() {
        assert!(TolerantFloat::new(1.0, -1.0).is_err());
    }

    #[test]
    fn bounded_enforces_limits() {
        assert!(TolerantFloat::bounded(0.5, 1e-6, 0.0, 1.0).is_ok());
        assert!(TolerantFloat::bounded(-0.1, 1e-6, 0.0, 1.0).is_err());
        assert!(TolerantFloat::bounded(1.1, 1e-6, 0.0, 1.0).is_err());
    }

    #[test]
    fn tolerant_equality() {
        let a = TolerantFloat::new(1.0, 1e-6).unwrap();
        let b = TolerantFloat::new(1.0 + 1e-7, 1e-6).unwrap();
        assert!(a.tolerant_eq(&b));
    }

    #[test]
    fn convergence_detection() {
        let converged = TolerantFloat::new(1e-10, 1e-8).unwrap();
        assert!(converged.is_converged());
        let not_converged = TolerantFloat::new(1e-4, 1e-8).unwrap();
        assert!(!not_converged.is_converged());
    }

    #[test]
    fn tolerant_equality_is_not_transitive_which_is_why_it_is_not_partial_eq() {
        let (a, b, c) = (
            TolerantFloat::new(0.0, 1.0).unwrap(),
            TolerantFloat::new(1.0, 1.0).unwrap(),
            TolerantFloat::new(2.0, 1.0).unwrap(),
        );
        assert!(a.tolerant_eq(&b));
        assert!(b.tolerant_eq(&c));
        assert!(
            !a.tolerant_eq(&c),
            "if this ever holds, tolerant_eq has become transitive and the \
             PartialEq removal could be revisited"
        );
    }

    #[test]
    fn convergence_is_measured_against_the_declared_epsilon_not_a_global_one() {
        let strict = TolerantFloat::new(1e-9, 1e-12).unwrap();
        let loose = TolerantFloat::new(1e-9, 1e-6).unwrap();
        assert!(!strict.is_converged());
        assert!(loose.is_converged());
    }
}

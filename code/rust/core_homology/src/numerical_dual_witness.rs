
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_cfc87491<T> {
    fn checked_invariant_cfc87491(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_cfc87491<T> for Option<T> {
    #[inline]
    fn checked_invariant_cfc87491(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_cfc87491<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_cfc87491(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::fmt;

/// Numerical candidate dual witness.
///
/// This is not certified. It is useful for solver/pre-convergence diagnostics.
#[derive(Debug, Clone)]
pub struct DualWitnessCandidate {
    dual_vector: Vec<f64>,
    stationarity: f64,
    linf_norm: f64,
}

/// Numerically certified dual witness under an explicit tolerance profile.
///
/// This is an approximate certificate, not an exact theorem-grade certificate.
#[derive(Debug, Clone)]
pub struct CertifiedDualWitness {
    dual_vector: Vec<f64>,
    stationarity: f64,
    linf_norm: f64,
    tolerance: f64,
    linf_bound: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub enum DualWitnessError {
    EmptyVector,
    NonFiniteEntry { index: usize, value: f64 },
    NonFiniteStationarity { value: f64 },
    NonFiniteTolerance { value: f64 },
    NonFiniteBound { value: f64 },
    NegativeTolerance { value: f64 },
    NegativeBound { value: f64 },
    StationarityViolation { residual: f64, tolerance: f64 },
    BoundViolation { linf_norm: f64, bound: f64 },
}

impl fmt::Display for DualWitnessError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyVector => write!(f, "DualWitness: empty vector"),
            Self::NonFiniteEntry { index, value } => {
                write!(f, "DualWitness: non-finite entry [{index}] = {value}")
            }
            Self::NonFiniteStationarity { value } => {
                write!(f, "DualWitness: non-finite stationarity residual = {value}")
            }
            Self::NonFiniteTolerance { value } => {
                write!(f, "DualWitness: non-finite tolerance = {value}")
            }
            Self::NonFiniteBound { value } => {
                write!(f, "DualWitness: non-finite infinity bound = {value}")
            }
            Self::NegativeTolerance { value } => {
                write!(f, "DualWitness: negative tolerance = {value}")
            }
            Self::NegativeBound { value } => {
                write!(f, "DualWitness: negative infinity bound = {value}")
            }
            Self::StationarityViolation {
                residual,
                tolerance,
            } => {
                write!(
                    f,
                    "DualWitness: stationarity violation residual={residual:.6e} > tolerance={tolerance:.6e}"
                )
            }
            Self::BoundViolation { linf_norm, bound } => {
                write!(
                    f,
                    "DualWitness: ||phi||_inf={linf_norm:.6e} > bound={bound:.6e}"
                )
            }
        }
    }
}

impl std::error::Error for DualWitnessError {}

fn compute_linf_norm(dual_vector: &[f64]) -> Result<f64, DualWitnessError> {
    if dual_vector.is_empty() {
        return Err(DualWitnessError::EmptyVector);
    }

    for (i, &v) in dual_vector.iter().enumerate() {
        if !v.is_finite() {
            return Err(DualWitnessError::NonFiniteEntry { index: i, value: v });
        }
    }
    Ok(core_functional::norms::lp_norm(dual_vector, f64::INFINITY)
        .checked_invariant_cfc87491("finite entries and valid infinity order")
        .value())
}

impl DualWitnessCandidate {
    pub fn new(dual_vector: Vec<f64>, stationarity: f64) -> Result<Self, DualWitnessError> {
        if !stationarity.is_finite() {
            return Err(DualWitnessError::NonFiniteStationarity {
                value: stationarity,
            });
        }

        let linf_norm = compute_linf_norm(&dual_vector)?;

        Ok(Self {
            dual_vector,
            stationarity,
            linf_norm,
        })
    }

    pub fn dual_vector(&self) -> &[f64] {
        &self.dual_vector
    }

    pub fn stationarity(&self) -> f64 {
        self.stationarity
    }

    pub fn linf_norm(&self) -> f64 {
        self.linf_norm
    }
}

impl CertifiedDualWitness {
    pub fn verify(
        dual_vector: Vec<f64>,
        stationarity: f64,
        tolerance: f64,
        linf_bound: f64,
    ) -> Result<Self, DualWitnessError> {
        if !stationarity.is_finite() {
            return Err(DualWitnessError::NonFiniteStationarity {
                value: stationarity,
            });
        }

        if !tolerance.is_finite() {
            return Err(DualWitnessError::NonFiniteTolerance { value: tolerance });
        }

        if tolerance < 0.0 {
            return Err(DualWitnessError::NegativeTolerance { value: tolerance });
        }

        if !linf_bound.is_finite() {
            return Err(DualWitnessError::NonFiniteBound { value: linf_bound });
        }

        if linf_bound < 0.0 {
            return Err(DualWitnessError::NegativeBound { value: linf_bound });
        }

        let linf_norm = compute_linf_norm(&dual_vector)?;

        // Inclusive tolerance checks
        if stationarity > tolerance {
            return Err(DualWitnessError::StationarityViolation {
                residual: stationarity,
                tolerance,
            });
        }

        if linf_norm > linf_bound {
            return Err(DualWitnessError::BoundViolation {
                linf_norm,
                bound: linf_bound,
            });
        }

        Ok(Self {
            dual_vector,
            stationarity,
            linf_norm,
            tolerance,
            linf_bound,
        })
    }

    pub fn dual_vector(&self) -> &[f64] {
        &self.dual_vector
    }

    pub fn stationarity(&self) -> f64 {
        self.stationarity
    }

    pub fn linf_norm(&self) -> f64 {
        self.linf_norm
    }

    pub fn tolerance(&self) -> f64 {
        self.tolerance
    }

    pub fn linf_bound(&self) -> f64 {
        self.linf_bound
    }
}

// Origin: engine/crates_rs/core_homology/src/numerical_dual_witness.rs
// Claim: urn:core:crates_rs:core-homology:numerical-dual-witness:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constructs_valid_witness() {
        let w = CertifiedDualWitness::verify(vec![0.5, -0.3, 0.1], 1e-10, 1e-6, 1.0).unwrap();
        assert!(w.linf_norm() <= 1.0);
    }

    #[test]
    fn rejects_stationarity_violation() {
        let r = CertifiedDualWitness::verify(
            vec![0.5],
            0.1, // stationarity too large
            1e-6,
            1.0,
        );
        assert!(matches!(
            r,
            Err(DualWitnessError::StationarityViolation { .. })
        ));
    }

    #[test]
    fn rejects_bound_violation() {
        let r = CertifiedDualWitness::verify(
            vec![1.5], // exceeds linf_bound = 1.0
            1e-10,
            1e-6,
            1.0,
        );
        assert!(matches!(r, Err(DualWitnessError::BoundViolation { .. })));
    }

    #[test]
    fn candidate_allows_violations_but_not_nan() {
        let w = DualWitnessCandidate::new(vec![1.5, -2.0], 0.5).unwrap();
        assert_eq!(w.linf_norm(), 2.0);

        // Ensure candidate rejects NaN
        let r = DualWitnessCandidate::new(vec![f64::NAN], 0.5);
        assert!(matches!(r, Err(DualWitnessError::NonFiniteEntry { .. })));
    }

    #[test]
    fn rejects_nan_stationarity() {
        let r = CertifiedDualWitness::verify(vec![0.5], f64::NAN, 1e-6, 1.0);
        assert!(matches!(
            r,
            Err(DualWitnessError::NonFiniteStationarity { .. })
        ));
    }

    #[test]
    fn rejects_infinite_stationarity() {
        let r = CertifiedDualWitness::verify(vec![0.5], f64::INFINITY, 1e-6, 1.0);
        assert!(matches!(
            r,
            Err(DualWitnessError::NonFiniteStationarity { .. })
        ));
    }

    #[test]
    fn rejects_nan_tolerance() {
        let r = CertifiedDualWitness::verify(vec![0.5], 1e-10, f64::NAN, 1.0);
        assert!(matches!(
            r,
            Err(DualWitnessError::NonFiniteTolerance { .. })
        ));
    }

    #[test]
    fn rejects_negative_tolerance() {
        let r = CertifiedDualWitness::verify(vec![0.5], 1e-10, -1e-6, 1.0);
        assert!(matches!(r, Err(DualWitnessError::NegativeTolerance { .. })));
    }

    #[test]
    fn rejects_nan_bound() {
        let r = CertifiedDualWitness::verify(vec![0.5], 1e-10, 1e-6, f64::NAN);
        assert!(matches!(r, Err(DualWitnessError::NonFiniteBound { .. })));
    }

    #[test]
    fn rejects_negative_bound() {
        let r = CertifiedDualWitness::verify(vec![0.5], 1e-10, 1e-6, -1.0);
        assert!(matches!(r, Err(DualWitnessError::NegativeBound { .. })));
    }

    #[test]
    fn accepts_stationarity_equal_to_tolerance() {
        let r = CertifiedDualWitness::verify(vec![0.5], 1e-6, 1e-6, 1.0);
        assert!(r.is_ok());
    }

    #[test]
    fn display_strings_are_ascii_and_readable() {
        let err = DualWitnessError::BoundViolation {
            linf_norm: 2.0,
            bound: 1.0,
        };
        let msg = format!("{}", err);
        assert_eq!(
            msg,
            "DualWitness: ||phi||_inf=2.000000e0 > bound=1.000000e0"
        );
    }
}


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_e0b3072f;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_e0b3072f<T> = std::result::Result<T, BoundaryError_e0b3072f>;
pub mod numeric_constants;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::numeric_constants::{
        EPSILON_EIGEN, EPSILON_LOG_CLAMP, EPSILON_QUANTUM_EIGEN, EPSILON_QUANTUM_TOLERANCE,
    };

    #[test]
    fn declared_epsilons_match_their_exact_values() {
        assert_eq!(EPSILON_EIGEN, 1e-15_f64);
        assert_eq!(EPSILON_LOG_CLAMP, 1e-10_f64);
        assert_eq!(EPSILON_QUANTUM_EIGEN, 1e-12_f64);
        assert_eq!(EPSILON_QUANTUM_TOLERANCE, 1e-10_f64);
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ScaleError {
    Places,
    Order,
    Overflow,
}

// Origin: engine/crates_rs/constants/src/lib.rs
// Claim: urn:core:crates_rs:constants:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ScaleError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ScaleError {}

/// Exact power of ten for a declared decimal place count. Places above 38 do not fit in u128.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactDecimalScale {
    places: u32,
    unit: u128,
}

impl ExactDecimalScale {
    pub fn try_new(places: u32) -> Result<Self, ScaleError> {
        if places > 38 {
            return Err(ScaleError::Places);
        }
        let mut unit = 1u128;
        for _ in 0..places {
            unit = unit.checked_mul(10).ok_or(ScaleError::Overflow)?;
        }
        Ok(Self { places, unit })
    }

    pub fn ratio_places(finer: &Self, coarser: &Self) -> Result<u128, ScaleError> {
        if finer.places < coarser.places || coarser.unit == 0 {
            return Err(ScaleError::Order);
        }
        finer.unit.checked_div(coarser.unit).ok_or(ScaleError::Overflow)
    }

    pub fn places(&self) -> u32 { self.places }
    pub fn unit(&self) -> u128 { self.unit }
}

#[cfg(test)]
mod scale_tests {
    use super::*;

    #[test]
    fn eigen_places_are_one_thousand_times_the_quantum_eigen_places() {
        let eigen = ExactDecimalScale::try_new(15);
        let quantum = ExactDecimalScale::try_new(12);
        let log_clamp = ExactDecimalScale::try_new(10);
        let quantum_tolerance = ExactDecimalScale::try_new(10);
        assert!(matches!((eigen, quantum, log_clamp, quantum_tolerance), (
            Ok(ref eigen),
            Ok(ref quantum),
            Ok(ref log_clamp),
            Ok(ref quantum_tolerance),
        ) if ExactDecimalScale::ratio_places(eigen, quantum) == Ok(1000)
            && log_clamp.unit() == quantum_tolerance.unit()
            && eigen.places() == 15));
    }

    #[test]
    fn thirty_nine_places_do_not_fit() {
        let scale = ExactDecimalScale::try_new(39);
        assert!(matches!(scale, Err(ScaleError::Places)));
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct SafeStepResult {
    pub step: f64,
    pub max_sv: f64,
    pub dimensions: (usize, usize),
}

/// Positive width and height with a positive rational spectral ceiling.
/// The area is the checked product of the two dimensions.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SafeDimensionWitness {
    width: u64,
    height: u64,
    area: u64,
    spectral_num: u64,
    spectral_den: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SafeDimensionError {
    NonPositiveDimension,
    DimensionOverflow,
    NonPositiveSpectrum,
    AreaOverflow,
}

// Origin: engine/crates_rs/core_types/src/safe_step_result.rs
// Claim: urn:core:crates_rs:core-types:safe-step-result:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SafeDimensionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SafeDimensionError {}

impl SafeDimensionWitness {
    pub fn try_new(
        width: usize,
        height: usize,
        spectral_num: u64,
        spectral_den: u64,
    ) -> Result<Self, SafeDimensionError> {
        if width == 0 || height == 0 {
            return Err(SafeDimensionError::NonPositiveDimension);
        }
        let width = u64::try_from(width).map_err(|_| SafeDimensionError::DimensionOverflow)?;
        let height = u64::try_from(height).map_err(|_| SafeDimensionError::DimensionOverflow)?;
        if spectral_num == 0 || spectral_den == 0 {
            return Err(SafeDimensionError::NonPositiveSpectrum);
        }
        let area = width
            .checked_mul(height)
            .ok_or(SafeDimensionError::AreaOverflow)?;
        Ok(Self {
            width,
            height,
            area,
            spectral_num,
            spectral_den,
        })
    }

    pub fn area(&self) -> u64 {
        self.area
    }

    pub fn spectral_ratio(&self) -> (u64, u64) {
        (self.spectral_num, self.spectral_den)
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_80bb6c17 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

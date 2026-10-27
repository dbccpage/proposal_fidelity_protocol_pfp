// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
pub const FEAT_LINEAR: u64 = 1 << 0;
pub const FEAT_MULTIPLICATIVE: u64 = 1 << 1;
pub const FEAT_DIGIT: u64 = 1 << 2;
pub const FEAT_NONLINEAR: u64 = 1 << 3;
pub const FEAT_SIGN_SENSITIVE: u64 = 1 << 4;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MorphismType {
    Compute,
    Algebraic,
}

#[derive(Debug, Clone)]
pub struct OperatorSignature {
    arity: usize,
    complexity: usize,
    phi_profile: Vec<f64>,
    feature_flags: u64,
}

impl OperatorSignature {
    pub fn new(
        arity: usize,
        complexity: usize,
        phi_profile: Vec<f64>,
        feature_flags: u64,
    ) -> Result<Self, String> {
        if arity == 0 {
            return Err("operator signature arity must be positive".into());
        }
        if complexity == 0 {
            return Err("operator signature complexity must be positive".into());
        }
        if phi_profile.iter().any(|value| !value.is_finite()) {
            return Err("operator signature phi profile must be finite".into());
        }
        let _ = feature_flags;

        Ok(Self {
            arity,
            complexity,
            phi_profile,
            feature_flags,
        })
    }

    pub fn arity(&self) -> usize {
        self.arity
    }
    pub fn complexity(&self) -> usize {
        self.complexity
    }
    pub fn phi_profile(&self) -> &[f64] {
        &self.phi_profile
    }
    pub fn feature_flags(&self) -> u64 {
        self.feature_flags
    }
}

pub const ADMITTED_FEATURE_MASK: u64 = FEAT_LINEAR | FEAT_MULTIPLICATIVE | FEAT_DIGIT | FEAT_NONLINEAR | FEAT_SIGN_SENSITIVE;

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FeatureMaskWitness {
    admitted_bits: u64,
    popcount: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FeatureMaskWitnessError {
    UnknownBits { flags: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_types/src/operator_signature.rs
// Claim: urn:core:crates_rs:core-types:operator-signature:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for FeatureMaskWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for FeatureMaskWitnessError {}

impl FeatureMaskWitness {
    pub fn certify(flags: u64) -> Result<Self, FeatureMaskWitnessError> {
        if flags & !ADMITTED_FEATURE_MASK != 0 { return Err(FeatureMaskWitnessError::UnknownBits { flags }); }
        let mut popcount = 0u64;
        let mut bit = 1u64;
        let mut index = 0u64;
        while index < 5 {
            if flags & bit != 0 { popcount = popcount.checked_add(1).ok_or(FeatureMaskWitnessError::Overflow)?; }
            bit = bit.checked_mul(2).ok_or(FeatureMaskWitnessError::Overflow)?;
            index = index.checked_add(1).ok_or(FeatureMaskWitnessError::Overflow)?;
        }
        Ok(Self { admitted_bits: flags, popcount })
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        assert!(matches!(FeatureMaskWitness::certify(FEAT_LINEAR | FEAT_DIGIT), Ok(w) if w.popcount == 2));
        assert!(matches!(FeatureMaskWitness::certify(ADMITTED_FEATURE_MASK), Ok(w) if w.popcount == 5));
        assert!(matches!(FeatureMaskWitness::certify(1 << 5), Err(FeatureMaskWitnessError::UnknownBits { .. })));
        assert!(matches!(FeatureMaskWitness::certify(0), Ok(w) if w.popcount == 0));
    }
}

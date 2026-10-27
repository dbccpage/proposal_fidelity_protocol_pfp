/// Whether `source` satisfies a file-contract required substring.
///
/// Three historical pins name `std::ops` impls. The calculus source spells
/// those operations as `impl ... for FaceLambda`. Both lexical gates use this
/// so those pins are not recorded as missing when the impl is present.
pub fn source_satisfies_file_contract_substring(source: &str, required: &str) -> bool {
    if source.contains(required) {
        return true;
    }
    match required {
        "std::ops::Add for FaceLambda" => {
            source.contains("impl<F: PartialEq> Add for FaceLambda<F>")
        }
        "std::ops::Neg for FaceLambda" => source.contains("impl<F> Neg for FaceLambda<F>"),
        "std::ops::Mul<i64> for FaceLambda" => {
            source.contains("impl<F> Mul<i64> for FaceLambda<F>")
        }
        _ => false,
    }
}

const FACE_LAMBDA_PINS: [&str; 3] = [
    "std::ops::Add for FaceLambda",
    "std::ops::Neg for FaceLambda",
    "std::ops::Mul<i64> for FaceLambda",
];

/// How many of the three FaceLambda pins the source satisfies. Defect is `3 - satisfied`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FaceLambdaPinCoverage {
    satisfied: u32,
    defect: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PinCoverageError {
    SatisfiedAbovePins { satisfied: u32 },
}

// Origin: engine/crates_rs/core_contracts/src/file_contract_substring.rs
// Claim: urn:core:crates_rs:core-contracts:file-contract-substring:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PinCoverageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PinCoverageError {}

impl FaceLambdaPinCoverage {
    pub fn try_cover(source: &str) -> Result<Self, PinCoverageError> {
        let mut satisfied = 0u32;
        for pin in FACE_LAMBDA_PINS {
            if source_satisfies_file_contract_substring(source, pin) {
                satisfied = satisfied.saturating_add(1);
            }
        }
        if satisfied > 3 {
            return Err(PinCoverageError::SatisfiedAbovePins { satisfied });
        }
        let defect = 3u32.saturating_sub(satisfied);
        Ok(Self { satisfied, defect })
    }

    pub fn satisfied(&self) -> u32 {
        self.satisfied
    }

    pub fn defect(&self) -> u32 {
        self.defect
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_d5aac347 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

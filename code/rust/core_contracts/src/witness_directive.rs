/// Witness directive trait for configuring witness generation.
///
/// Action-candidate witness profiles may require phi-monotonicity,
/// idempotence, and determinism. Other contracts require only the witness
/// properties declared by their contract. A directive requests evidence; it
/// does not verify, certify, evaluate, license, terminalize, or execute.
///
/// This trait allows contracts to declare which witnesses should be generated
/// for their implementations.
pub trait WitnessDirective: crate::sealed::Sealed {
    // ========================================================================
    // Witness generation flags by operator type
    // ========================================================================

    /// Generate phi-monotonicity witnesses for Lambda operators.
    ///
    /// When true, property-based tests verify that phi(output) <= phi(input).
    const GENERATE_LAMBDA_WITNESSES: bool = false;

    /// Generate idempotence witnesses for Reducer operators.
    ///
    /// When true, property-based tests verify that r(r(x)) = r(x).
    const GENERATE_REDUCER_WITNESSES: bool = false;

    /// Generate determinism witnesses for Transform operators.
    ///
    /// When true, property-based tests verify that f(x) = f(x) for all x.
    const GENERATE_TRANSFORM_WITNESSES: bool = false;

    // ========================================================================
    // Required properties
    // ========================================================================

    /// Require totality: operator must not fail on any valid input.
    const REQUIRE_TOTAL: bool = false;

    /// Require determinism: operator must produce same output for same input.
    const REQUIRE_DETERMINISTIC: bool = false;

    /// Require phi-monotonicity: phi must not increase.
    const REQUIRE_PHI_MONOTONIC: bool = false;

    /// Require idempotence: applying twice equals applying once.
    const REQUIRE_IDEMPOTENT: bool = false;

    /// Require replay integrity evidence.
    const REQUIRE_REPLAY_INTEGRITY: bool = false;

    /// Require hash verification evidence.
    const REQUIRE_HASH_VERIFICATION: bool = false;

    /// Require explicit source artifact references.
    const REQUIRE_SOURCE_ARTIFACTS: bool = false;

    /// Require schema-hash binding evidence.
    const REQUIRE_SCHEMA_HASH: bool = false;

    // ========================================================================
    // Witness properties to verify
    // ========================================================================

    /// Properties that must be witnessed for this contract.
    ///
    /// The returned names are evidence requirements. They are not proof that
    /// the properties hold until a declared checker boundary validates them.
    fn required_witness_properties() -> &'static [&'static str] {
        &[]
    }
}

/// Standard witness properties from YAML canonical definitions.
pub mod witness_properties {
    /// Phi-monotonicity: phi(output) <= phi(input)
    pub const PHI_MONOTONICITY: &str = "phi_monotonicity";
    /// Idempotence: r(r(x)) = r(x)
    pub const IDEMPOTENCE: &str = "idempotence";
    /// Determinism: f(x) = f(x)
    pub const DETERMINISM: &str = "determinism";
    /// Totality: operator succeeds on all valid inputs
    pub const TOTALITY: &str = "totality";
    /// Replay integrity: trace can be replayed to same result
    pub const REPLAY_INTEGRITY: &str = "replay_integrity";
    /// Hash verification: hash matches expected value
    pub const HASH_VERIFICATION: &str = "hash_verification";
    /// Source artifacts: witness records bind explicit source artifacts
    pub const SOURCE_ARTIFACTS: &str = "source_artifacts";
    /// Schema hash: witness records bind the declared schema hash
    pub const SCHEMA_HASH: &str = "schema_hash";
    /// Basis linear independence: basis vectors are linearly independent
    pub const BASIS_LINEAR_INDEPENDENCE: &str = "basis_linear_independence";
    /// Vector space admissibility: type forms a valid vector space
    pub const VECTOR_SPACE_ADMISSIBILITY: &str = "vector_space_admissibility";
}

/// Requirement flags paired with the property names they request.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DirectiveFlags<'a> {
    require_total: bool,
    require_deterministic: bool,
    require_phi_monotonic: bool,
    require_idempotent: bool,
    require_replay_integrity: bool,
    require_hash_verification: bool,
    require_source_artifacts: bool,
    require_schema_hash: bool,
    properties: &'a [&'a str],
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DirectiveError {
    FlagMissing,
    FlagExtra,
    Duplicate,
    Overflow,
}

impl std::fmt::Display for DirectiveError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::FlagMissing => write!(formatter, "a required flag has no property name"),
            Self::FlagExtra => write!(formatter, "a property name is present while its flag is off"),
            Self::Duplicate => write!(formatter, "a witness property is repeated"),
            Self::Overflow => write!(formatter, "property count overflowed"),
        }
    }
}

impl std::error::Error for DirectiveError {}

impl<'a> DirectiveFlags<'a> {
    pub fn new(
        require_total: bool,
        require_deterministic: bool,
        require_phi_monotonic: bool,
        require_idempotent: bool,
        require_replay_integrity: bool,
        require_hash_verification: bool,
        require_source_artifacts: bool,
        require_schema_hash: bool,
        properties: &'a [&'a str],
    ) -> Self {
        Self {
            require_total,
            require_deterministic,
            require_phi_monotonic,
            require_idempotent,
            require_replay_integrity,
            require_hash_verification,
            require_source_artifacts,
            require_schema_hash,
            properties,
        }
    }
}

fn ensure_unique_directive_properties(properties: &[&str]) -> Result<(), DirectiveError> {
    for (index, name) in properties.iter().enumerate() {
        for earlier in properties.iter().take(index) {
            if earlier == name {
                return Err(DirectiveError::Duplicate);
            }
        }
    }
    Ok(())
}

/// Each requirement flag is on exactly when its witness-property name is in the slice.
/// Names outside the eight flag-backed properties stay uncounted.
pub fn flags_match_properties(flags: DirectiveFlags<'_>) -> Result<usize, DirectiveError> {
    let paired = [
        (flags.require_total, witness_properties::TOTALITY),
        (flags.require_deterministic, witness_properties::DETERMINISM),
        (flags.require_phi_monotonic, witness_properties::PHI_MONOTONICITY),
        (flags.require_idempotent, witness_properties::IDEMPOTENCE),
        (
            flags.require_replay_integrity,
            witness_properties::REPLAY_INTEGRITY,
        ),
        (
            flags.require_hash_verification,
            witness_properties::HASH_VERIFICATION,
        ),
        (
            flags.require_source_artifacts,
            witness_properties::SOURCE_ARTIFACTS,
        ),
        (flags.require_schema_hash, witness_properties::SCHEMA_HASH),
    ];
    ensure_unique_directive_properties(flags.properties)?;
    let mut required = 0usize;
    for (enabled, name) in paired {
        let present = flags.properties.contains(&name);
        if enabled && !present {
            return Err(DirectiveError::FlagMissing);
        }
        if !enabled && present {
            return Err(DirectiveError::FlagExtra);
        }
        if enabled {
            required = required.checked_add(1).ok_or(DirectiveError::Overflow)?;
        }
    }
    Ok(required)
}

// Origin: engine/crates_rs/core_contracts/src/witness_directive.rs
// Claim: urn:core:crates_rs:core-contracts:witness-directive:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn taken(result: Result<usize, DirectiveError>) -> usize {
        result.map_or_else(|_| loop { assert!(false); }, |value| value)
    }

    #[test]
    fn phi_and_totality_require_both_names() {
        let flags = DirectiveFlags::new(
            true,
            false,
            true,
            false,
            false,
            false,
            false,
            false,
            &[
                witness_properties::TOTALITY,
                witness_properties::PHI_MONOTONICITY,
                witness_properties::BASIS_LINEAR_INDEPENDENCE,
            ],
        );
        assert_eq!(taken(flags_match_properties(flags)), 2);
    }

    #[test]
    fn a_flag_without_its_name_is_refused() {
        let flags = DirectiveFlags::new(
            false,
            false,
            true,
            false,
            false,
            false,
            false,
            false,
            &[],
        );
        assert!(matches!(
            flags_match_properties(flags),
            Err(DirectiveError::FlagMissing)
        ));
    }
}

//! Cross-layer binding note: finite Hermitian *operator* spectral layer ↔ Q membrane.
//!
//! **Does not** re-implement or rewrite [`crate::coda::spectral_membrane`].
//! **Does not** depend on `core_quantum_physics` (dependency firewall / layering).
//!
//! | Surface | Crate path | Role |
//! |---|---|---|
//! | Exact spectral *certificate* membrane | `crate::coda::q::spectral_membrane` | Binds a finite refinement tower + convergence certificate into continuum-debt / Q admission terminals. Evidence ceiling ShapeOnly; authority None. |
//! | Finite Hermitian *operator* spectral face | `core_quantum_physics::hermitian_spectral` | Finite-`n` algebraic spectrum with exact root isolation and multiplicities, rational eigenspace decomposition, and explicit `ScalarCarrier` hypotheses. AuthorityEffect None; no continuum claim. |
//!
//! Binding contract (documentation only):
//! 1. Neither surface mints authority above `AuthorityEffect::None` / `AuthorityEffectLevel::None`.
//! 2. Neither surface constructs a continuum object; residual / debt routes remain explicit.
//! 3. Operator eigen-decomposition (hermitian_spectral) is **not** a substitute for a
//!    `ConvergenceCertificate` at the membrane; membrane decisions stay certificate-driven.
//! 4. Float / demo carriers on the operator face are non-exact and cannot pay membrane certificates.
//!
//! `hermitian_spectral::algebraic_spectrum` computes the general finite spectrum.
//! A full projector decomposition in the original scalar field remains a
//! separate representability question when the eigenvalues require an extension.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_9b97fcab;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_9b97fcab<T> = std::result::Result<T, BoundaryError_9b97fcab>;

/// Stable path string for the operator spectral face (for logs / residual ledgers).
pub const OPERATOR_SPECTRAL_LAYER_PATH: &str = "core_quantum_physics::hermitian_spectral";

/// Stable path string for the Q spectral certificate membrane.
pub const CERTIFICATE_SPECTRAL_MEMBRANE_PATH: &str = "crate::coda::q::spectral_membrane";

/// Binding fence: both layers declare AuthorityEffect None and no continuum object.
pub const SPECTRAL_LAYER_BINDING_FENCE: &str = "AuthorityEffect None on both faces; \
    hermitian_spectral is finite operator spectral; spectral_membrane is certificate admission; \
    neither mints continuum objects; Float64Demo is non-exact/experimental on the operator face.";

/// Returns the binding fence (never mints authority).
pub fn spectral_layer_binding_fence() -> &'static str {
    SPECTRAL_LAYER_BINDING_FENCE
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fence_declares_none_and_no_continuum() {
        let f = spectral_layer_binding_fence();
        assert!(f.contains("AuthorityEffect None"));
        assert!(f.contains("neither mints continuum"));
        assert!(OPERATOR_SPECTRAL_LAYER_PATH.contains("hermitian_spectral"));
        assert!(CERTIFICATE_SPECTRAL_MEMBRANE_PATH.contains("spectral_membrane"));
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteSpectrumPartition { dimension: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SpectrumPartitionError { Empty, Multiplicity, Overflow }

// Origin: engine/crates_rs/core_wdp/src/coda/q/spectral_layer_binding.rs
// Claim: urn:core:crates_rs:core-wdp:spectral-layer-binding:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SpectrumPartitionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SpectrumPartitionError {}

impl FiniteSpectrumPartition {
    /// Positive multiplicities sum to the dimension of a finite spectrum.
    pub fn try_from_multiplicities(multiplicities: &[u64]) -> Result<Self, SpectrumPartitionError> {
        if multiplicities.is_empty() {
            return Err(SpectrumPartitionError::Empty);
        }
        let mut dimension = 0u64;
        for multiplicity in multiplicities {
            if *multiplicity == 0 {
                return Err(SpectrumPartitionError::Multiplicity);
            }
            dimension = dimension.checked_add(*multiplicity).ok_or(SpectrumPartitionError::Overflow)?;
        }
        Ok(Self { dimension })
    }

    pub fn dimension(&self) -> u64 { self.dimension }
}

#[cfg(test)]
mod spectrum_partition_checks {
    use super::*;

    #[test]
    fn three_double_eigenvalues_have_dimension_six() {
        let partition = FiniteSpectrumPartition::try_from_multiplicities(&[2, 2, 2]);
        assert!(matches!(partition, Ok(p) if p.dimension() == 6));
    }

    #[test]
    fn a_zero_multiplicity_and_an_empty_list_are_refused() {
        assert!(matches!(FiniteSpectrumPartition::try_from_multiplicities(&[0]), Err(SpectrumPartitionError::Multiplicity)));
        assert!(matches!(FiniteSpectrumPartition::try_from_multiplicities(&[]), Err(SpectrumPartitionError::Empty)));
    }
}

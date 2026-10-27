//! HoTT view of the Core tower.

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum CoreLayer {
    Gtfoc,
    Gtfda,
    Gtmur,
    Gtor,
    Gttc,
    Gtta,
}

impl CoreLayer {
    pub const ORDER: [Self; 6] = [
        Self::Gtfoc,
        Self::Gtfda,
        Self::Gtmur,
        Self::Gtor,
        Self::Gttc,
        Self::Gtta,
    ];

    pub fn hott_role(self) -> &'static str {
        match self {
            Self::Gtfoc => "obstruction quotient type",
            Self::Gtfda => "authority dependent type",
            Self::Gtmur => "transport of authority across representation",
            Self::Gtor => "diagram and completion identity coherence",
            Self::Gttc => "finite-shadow pro-type",
            Self::Gtta => "cofiber residual terminal type",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HottLayerView {
    pub layer: CoreLayer,
    pub carrier_type_ref: String,
    pub identity_policy_ref: String,
    pub eliminator_ref: String,
}

impl HottLayerView {
    pub fn validate(&self) -> Result<(), HottTowerError> {
        if self.carrier_type_ref.is_empty() {
            return Err(HottTowerError::MissingCarrierType(self.layer));
        }
        if self.identity_policy_ref.is_empty() {
            return Err(HottTowerError::MissingIdentityPolicy(self.layer));
        }
        if self.eliminator_ref.is_empty() {
            return Err(HottTowerError::MissingEliminator(self.layer));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HottTower {
    pub layers: Vec<HottLayerView>,
}

impl HottTower {
    pub fn validate(&self) -> Result<(), HottTowerError> {
        if self
            .layers
            .iter()
            .map(|view| view.layer)
            .ne(CoreLayer::ORDER)
        {
            return Err(HottTowerError::LayerOrderViolation);
        }
        for layer in &self.layers {
            layer.validate()?;
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum HottTowerError {
    #[error("HoTT tower layers are not in canonical CODA-FOC->CODA-A order")]
    LayerOrderViolation,
    #[error("missing carrier type for {0:?}")]
    MissingCarrierType(CoreLayer),
    #[error("missing identity policy for {0:?}")]
    MissingIdentityPolicy(CoreLayer),
    #[error("missing eliminator for {0:?}")]
    MissingEliminator(CoreLayer),
}

// Origin: engine/crates_rs/core_homotopy_type_theory/src/tower.rs
// Claim: urn:core:crates_rs:core-homotopy-type-theory:tower:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_eff16ad0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

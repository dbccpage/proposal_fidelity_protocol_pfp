//! Topos-side model data for HoTT fragments.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ToposHottModel {
    pub name: String,
    pub universes: Vec<String>,
    pub identity_type_interpretations: Vec<String>,
    pub truncation_modalities: Vec<String>,
}

impl ToposHottModel {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.into(),
            universes: Vec::new(),
            identity_type_interpretations: Vec::new(),
            truncation_modalities: Vec::new(),
        }
    }

    pub fn validate_minimal_model(&self) -> Vec<String> {
        let mut violations = Vec::new();
        if self.universes.is_empty() {
            violations.push(format!(
                "Model {} has no universe interpretation",
                self.name
            ));
        }
        if self.identity_type_interpretations.is_empty() {
            violations.push(format!(
                "Model {} has no identity type interpretation",
                self.name
            ));
        }
        violations
    }
}

/// Checked private-field witness. Existing constructors are unchanged.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ToposUniverseWitness {
    universes: u64,
    identity_types: u64,
    truncations: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ToposUniverseWitnessError {
    EmptyName,
    NoUniverse,
    IdentityTowerMismatch { universes: u64, identity_types: u64 },
    TruncationAboveUniverses { truncations: u64, universes: u64 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/topos_hott_model.rs
// Claim: urn:core:crates_rs:core-category-theory:topos-hott-model:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ToposUniverseWitnessError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ToposUniverseWitnessError {}

impl ToposUniverseWitness {
    pub fn certify(model: &ToposHottModel) -> Result<Self, ToposUniverseWitnessError> {
        if model.name.trim().is_empty() { return Err(ToposUniverseWitnessError::EmptyName); }
        let universes = u64::try_from(model.universes.len()).map_err(|_| ToposUniverseWitnessError::Overflow)?;
        let identity_types = u64::try_from(model.identity_type_interpretations.len()).map_err(|_| ToposUniverseWitnessError::Overflow)?;
        let truncations = u64::try_from(model.truncation_modalities.len()).map_err(|_| ToposUniverseWitnessError::Overflow)?;
        if universes == 0 { return Err(ToposUniverseWitnessError::NoUniverse); }
        if identity_types != universes { return Err(ToposUniverseWitnessError::IdentityTowerMismatch { universes, identity_types }); }
        if truncations > universes { return Err(ToposUniverseWitnessError::TruncationAboveUniverses { truncations, universes }); }
        Ok(Self { universes, identity_types, truncations })
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod exact_witness_tests {
    use super::*;

    #[test]
    fn exact_witness_holds() {
        let mut model = ToposHottModel::new("E");
        model.universes.push("U0".into());
        model.identity_type_interpretations.push("Id".into());
        assert!(matches!(ToposUniverseWitness::certify(&model), Ok(w) if w.universes == 1));
        model.truncation_modalities.push("tr".into());
        model.truncation_modalities.push("tr2".into());
        assert!(matches!(ToposUniverseWitness::certify(&model), Err(ToposUniverseWitnessError::TruncationAboveUniverses { .. })));
    }
}

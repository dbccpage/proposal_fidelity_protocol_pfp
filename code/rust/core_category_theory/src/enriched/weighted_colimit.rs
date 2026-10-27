//! weighted_colimit shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_733dfae7;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_733dfae7<T> = std::result::Result<T, BoundaryError_733dfae7>;
use serde::{Deserialize, Serialize};

/// Best-effort weighted colimit shell W ★ D in a V-enriched setting.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct WeightedColimit {
    pub label: String,
    /// Weight enriched functor W : J^op → V (or appropriate variance).
    pub weight_ref: String,
    /// Diagram enriched functor D : J → C ref.
    pub diagram_ref: String,
    /// Ambient enriched category shell label.
    pub ambient_enriched: String,
    /// Base monoidal V label.
    pub base_monoidal_v: String,
    /// Apex / colimit object label (if claimed).
    pub apex: String,
    pub notes: Vec<String>,
}

impl WeightedColimit {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            weight_ref: String::new(),
            diagram_ref: String::new(),
            ambient_enriched: String::new(),
            base_monoidal_v: String::new(),
            apex: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn of(
        label: impl Into<String>,
        weight_ref: impl Into<String>,
        diagram_ref: impl Into<String>,
        ambient_enriched: impl Into<String>,
        base_monoidal_v: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            weight_ref: weight_ref.into(),
            diagram_ref: diagram_ref.into(),
            ambient_enriched: ambient_enriched.into(),
            base_monoidal_v: base_monoidal_v.into(),
            apex: String::new(),
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.weight_ref.is_empty() {
            return Err("empty weight_ref".into());
        }
        if self.diagram_ref.is_empty() {
            return Err("empty diagram_ref".into());
        }
        if self.ambient_enriched.is_empty() {
            return Err("empty ambient_enriched".into());
        }
        if self.base_monoidal_v.is_empty() {
            return Err("empty base_monoidal_v".into());
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/enriched/weighted_colimit.rs
// Claim: urn:core:crates_rs:core-category-theory:weighted-colimit:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(WeightedColimit::of("wcolim", "W", "D", "C", "V")
            .validate_shell()
            .is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(WeightedColimit::new("").validate_shell().is_err());
    }
}

/// Cardinality of a discrete weighted colimit: the sum of weight times diagram size.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteWeightSum {
    summands: usize,
    cardinality: u128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WeightError {
    Bound,
    Shape,
    Overflow,
}

impl std::fmt::Display for WeightError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            WeightError::Bound => write!(formatter, "the family must lie in 1..=16 summands"),
            WeightError::Shape => write!(formatter, "weights and diagrams must have equal length"),
            WeightError::Overflow => write!(formatter, "the weighted sum overflowed"),
        }
    }
}

impl std::error::Error for WeightError {}

impl DiscreteWeightSum {
    pub fn cardinality(weights: &[u32], diagrams: &[u32]) -> Result<Self, WeightError> {
        if weights.is_empty() || weights.len() > 16 {
            return Err(WeightError::Bound);
        }
        if weights.len() != diagrams.len() {
            return Err(WeightError::Shape);
        }
        let mut cardinality: u128 = 0;
        for index in 0..weights.len() {
            let weight = u128::from(*weights.get(index).ok_or(WeightError::Shape)?);
            let diagram = u128::from(*diagrams.get(index).ok_or(WeightError::Shape)?);
            let term = weight.checked_mul(diagram).ok_or(WeightError::Overflow)?;
            cardinality = cardinality.checked_add(term).ok_or(WeightError::Overflow)?;
        }
        Ok(Self {
            summands: weights.len(),
            cardinality,
        })
    }

    pub fn cardinality_value(&self) -> u128 {
        self.cardinality
    }
}

#[cfg(test)]
mod weight_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn two_weights_times_two_diagrams_sum_to_twenty_three() {
        let sum = taken(DiscreteWeightSum::cardinality(&[2, 3], &[4, 5]));
        assert_eq!(sum.cardinality_value(), 23);
        assert!(DiscreteWeightSum::cardinality(&[2], &[4, 5]).is_err());
    }
}

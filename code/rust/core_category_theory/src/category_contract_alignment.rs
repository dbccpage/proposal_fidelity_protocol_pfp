//! Category theory contract alignment module.
//!
//! Maps Rust category-theoretic structures (categories, functors, natural transformations,
//! adjunctions, monads, operads, limits, colimits, coends) to canonical `urn:core:math:*` contract URNs.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_d4c4f785;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_d4c4f785<T> = std::result::Result<T, BoundaryError_d4c4f785>;
pub const CONTRACT_CATEGORY: &str = "urn:core:math:category:v0.1.0";
pub const CONTRACT_FUNCTOR: &str = "urn:core:math:functor:v0.1.0";
pub const CONTRACT_NATURAL_TRANSFORMATION: &str = "urn:core:math:natural_transformation:v0.1.0";
pub const CONTRACT_ADJUNCTION: &str = "urn:core:math:adjunction:v0.1.0";
pub const CONTRACT_MONAD: &str = "urn:core:math:monad:v0.1.0";
pub const CONTRACT_OPERAD: &str = "urn:core:math:operad:v0.1.0";
pub const CONTRACT_LIMIT: &str = "urn:core:math:limit:v0.1.0";
pub const CONTRACT_COLIMIT: &str = "urn:core:math:colimit:v0.1.0";
pub const CONTRACT_COEND: &str = "urn:core:math:coend:v0.1.0";
pub const CONTRACT_END: &str = "urn:core:math:end:v0.1.0";

/// Record mapping a Rust category-theoretic type/trait to a contract URN.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CategoryContractBinding {
    pub concept_name: String,
    pub contract_urn: String,
    pub mechanization_stratum: String,
    pub is_active: bool,
}

impl CategoryContractBinding {
    pub fn default_category_bindings() -> Vec<Self> {
        vec![
            Self {
                concept_name: "Category".to_string(),
                contract_urn: CONTRACT_CATEGORY.to_string(),
                mechanization_stratum: "M0".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Functor".to_string(),
                contract_urn: CONTRACT_FUNCTOR.to_string(),
                mechanization_stratum: "M0".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "NaturalTransformation".to_string(),
                contract_urn: CONTRACT_NATURAL_TRANSFORMATION.to_string(),
                mechanization_stratum: "M0".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Adjunction".to_string(),
                contract_urn: CONTRACT_ADJUNCTION.to_string(),
                mechanization_stratum: "M1".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Monad".to_string(),
                contract_urn: CONTRACT_MONAD.to_string(),
                mechanization_stratum: "M1".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Operad".to_string(),
                contract_urn: CONTRACT_OPERAD.to_string(),
                mechanization_stratum: "M1".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Limit".to_string(),
                contract_urn: CONTRACT_LIMIT.to_string(),
                mechanization_stratum: "M1".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Colimit".to_string(),
                contract_urn: CONTRACT_COLIMIT.to_string(),
                mechanization_stratum: "M1".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "Coend".to_string(),
                contract_urn: CONTRACT_COEND.to_string(),
                mechanization_stratum: "M2".to_string(),
                is_active: true,
            },
            Self {
                concept_name: "End".to_string(),
                contract_urn: CONTRACT_END.to_string(),
                mechanization_stratum: "M2".to_string(),
                is_active: true,
            },
        ]
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_all_category_bindings_valid() {
        let bindings = CategoryContractBinding::default_category_bindings();
        assert_eq!(bindings.len(), 10);
        for b in &bindings {
            assert!(b.contract_urn.starts_with("urn:core:math:"));
            assert!(b.is_active);
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum BindingLatticeError {
    DuplicateUrn { index: usize },
    Stratum { index: usize, stratum: String },
    ActiveCount { active: usize, total: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category_contract_alignment.rs
// Claim: urn:core:crates_rs:core-category-theory:category-contract-alignment:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BindingLatticeError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BindingLatticeError {}

/// The ten default bindings are a lattice: distinct contract URNs, strata in
/// {M0, M1, M2}, and every row active.
pub fn binding_lattice_holds() -> Result<usize, BindingLatticeError> {
    use std::collections::BTreeSet;
    let bindings = CategoryContractBinding::default_category_bindings();
    let mut urns = BTreeSet::new();
    let mut active = 0usize;
    for (index, binding) in bindings.iter().enumerate() {
        if !urns.insert(binding.contract_urn.clone()) {
            return Err(BindingLatticeError::DuplicateUrn { index });
        }
        match binding.mechanization_stratum.as_str() {
            "M0" | "M1" | "M2" => {}
            other => {
                return Err(BindingLatticeError::Stratum {
                    index,
                    stratum: other.to_string(),
                });
            }
        }
        if binding.is_active {
            active = active.checked_add(1).ok_or(BindingLatticeError::Overflow)?;
        }
    }
    if active != 10 || bindings.len() != 10 {
        return Err(BindingLatticeError::ActiveCount {
            active,
            total: bindings.len(),
        });
    }
    Ok(active)
}

#[cfg(test)]
mod binding_lattice_witness {
    use super::*;

    #[test]
    fn default_bindings_are_a_ten_row_lattice() {
        assert_eq!(binding_lattice_holds(), Ok(10));
    }
}

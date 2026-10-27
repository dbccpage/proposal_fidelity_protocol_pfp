//! Generated law enforcement artifacts.
//!
//! This module is populated by the codegen pipeline from contract YAML.
//! It is empty until codegen has been run.

// Exact invariant envelope.
// Origin: engine/crates_rs/core_contracts/src/enforcement/generated.rs
// Claim: urn:core:contracts:enforcement:generated-census:v1
// AuthorityEffect: None

/// Laws this module has actually emitted. Codegen has not written any.
const GENERATED_LAWS: &[(&str, u64)] = &[];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GeneratedLawCensus {
    laws: u64,
    clauses: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GeneratedLawError {
    EmptyId { index: usize },
    ZeroClauses { index: usize },
    Duplicate { index: usize },
    Missing { id: String },
    Unexpected { id: String },
    ClauseMismatch { id: String, generated: u64, claimed: u64 },
    Overflow,
    Count { laws: u64, stored: usize },
}

// Origin: engine/crates_rs/core_contracts/src/enforcement_generated.rs
// Claim: urn:core:crates_rs:core-contracts:enforcement-generated:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GeneratedLawError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GeneratedLawError {}

impl GeneratedLawCensus {
    pub fn laws(&self) -> u64 { self.laws }
    pub fn clauses(&self) -> u64 { self.clauses }

    pub fn try_generated(claimed: &[(&str, u64)]) -> Result<Self, GeneratedLawError> {
        Self::try_against(GENERATED_LAWS, claimed)
    }

    fn sum_generated_clauses(generated: &[(&str, u64)]) -> Result<u64, GeneratedLawError> {
        let mut clauses = 0u64;
        for (index, (id, clause_count)) in generated.iter().enumerate() {
            if id.is_empty() {
                return Err(GeneratedLawError::EmptyId { index });
            }
            if *clause_count == 0 {
                return Err(GeneratedLawError::ZeroClauses { index });
            }
            if generated.iter().take(index).any(|(earlier, _)| earlier == id) {
                return Err(GeneratedLawError::Duplicate { index });
            }
            clauses = clauses.checked_add(*clause_count).ok_or(GeneratedLawError::Overflow)?;
        }
        Ok(clauses)
    }

    fn verify_claimed_entry(
        index: usize,
        id: &str,
        clause_count: u64,
        claimed: &[(&str, u64)],
        generated: &[(&str, u64)],
    ) -> Result<(), GeneratedLawError> {
        if id.is_empty() {
            return Err(GeneratedLawError::EmptyId { index });
        }
        if claimed.iter().take(index).any(|(earlier, _)| *earlier == id) {
            return Err(GeneratedLawError::Duplicate { index });
        }
        match generated.iter().find(|(generated_id, _)| *generated_id == id) {
            None => Err(GeneratedLawError::Unexpected { id: id.to_string() }),
            Some((_, generated_clauses)) if *generated_clauses != clause_count => {
                Err(GeneratedLawError::ClauseMismatch {
                    id: id.to_string(),
                    generated: *generated_clauses,
                    claimed: clause_count,
                })
            }
            Some(_) => Ok(()),
        }
    }

    pub fn try_against(generated: &[(&str, u64)], claimed: &[(&str, u64)]) -> Result<Self, GeneratedLawError> {
        let clauses = Self::sum_generated_clauses(generated)?;
        if claimed.len() != generated.len() {
            return Err(GeneratedLawError::Count {
                laws: u64::try_from(generated.len()).map_err(|_| GeneratedLawError::Overflow)?,
                stored: claimed.len(),
            });
        }
        for (index, (id, clause_count)) in claimed.iter().enumerate() {
            Self::verify_claimed_entry(index, id, *clause_count, claimed, generated)?;
        }
        for (id, _) in generated {
            if !claimed.iter().any(|(claimed_id, _)| claimed_id == id) {
                return Err(GeneratedLawError::Missing { id: (*id).to_string() });
            }
        }
        let laws = u64::try_from(generated.len()).map_err(|_| GeneratedLawError::Overflow)?;
        let out = Self { laws, clauses };
        Ok(out)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod generated_law_census_tests {
    use super::*;

    #[test]
    fn the_unemitted_module_censuses_as_empty() {
        let census = GeneratedLawCensus::try_generated(&[]);
        assert!(matches!(census, Ok(ref row) if row.laws() == 0 && row.clauses() == 0));
    }

    #[test]
    fn a_claimed_law_is_not_generated_here() {
        assert!(matches!(
            GeneratedLawCensus::try_generated(&[("urn:core:law:invented", 2)]),
            Err(GeneratedLawError::Count { laws: 0, stored: 1 })
        ));
    }

    #[test]
    fn a_sample_inventory_sums_clauses_and_refuses_a_mismatch() {
        let generated = [("alpha", 2u64), ("beta", 3u64)];
        let census = GeneratedLawCensus::try_against(&generated, &[("beta", 3), ("alpha", 2)]);
        assert!(matches!(census, Ok(ref row) if row.laws() == 2 && row.clauses() == 5));
        assert!(matches!(
            GeneratedLawCensus::try_against(&generated, &[("alpha", 2), ("beta", 4)]),
            Err(GeneratedLawError::ClauseMismatch { generated: 3, claimed: 4, .. })
        ));
    }
}

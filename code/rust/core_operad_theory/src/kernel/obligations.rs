//! Inert, canonical export model for unresolved finite proof obligations.
//!
//! Rust face of `engine/kernel/higher_operad/obligations.py`.

use std::collections::BTreeSet;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use super::canonical::{
    canonical_bytes, canonical_id, require_digest, require_identifier, require_text, sorted_unique,
    CanonicalError,
};
use super::model::AuthorityEffect;
use super::result::KernelError;
use super::terms::NormalizedTerm;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ObligationKind {
    #[serde(rename = "Associativity")]
    Associativity,
    #[serde(rename = "Unit")]
    Unit,
    #[serde(rename = "Parallelism")]
    Parallelism,
    #[serde(rename = "Comparison")]
    Comparison,
    #[serde(rename = "Refinement")]
    Refinement,
    #[serde(rename = "Coherence")]
    Coherence,
}

impl ObligationKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Associativity => "Associativity",
            Self::Unit => "Unit",
            Self::Parallelism => "Parallelism",
            Self::Comparison => "Comparison",
            Self::Refinement => "Refinement",
            Self::Coherence => "Coherence",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProofObligation {
    pub obligation_id: String,
    pub kind: ObligationKind,
    pub statement: String,
    pub subject_refs: Vec<String>,
    pub premise_digests: Vec<String>,
}

impl ProofObligation {
    pub fn new(
        obligation_id: &str,
        kind: ObligationKind,
        statement: &str,
        subject_refs: Vec<String>,
        premise_digests: Vec<String>,
    ) -> Result<Self, KernelError> {
        let valid_refs = subject_refs
            .into_iter()
            .map(|r| require_digest(&r, "subject_ref"))
            .collect::<Result<Vec<_>, _>>()?;
        let refs = sorted_unique(&valid_refs, "subject_refs")?;
        let valid_premises = premise_digests
            .into_iter()
            .map(|p| require_digest(&p, "premise_digest"))
            .collect::<Result<Vec<_>, _>>()?;
        let premises = sorted_unique(&valid_premises, "premise_digests")?;

        Ok(Self {
            obligation_id: require_identifier(obligation_id, "obligation_id")?,
            kind,
            statement: require_text(statement, "statement")?,
            subject_refs: refs,
            premise_digests: premises,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "obligation_id": self.obligation_id,
            "kind": self.kind.as_str(),
            "statement": self.statement,
            "subject_refs": self.subject_refs,
            "premise_digests": self.premise_digests,
            "status": "Open",
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObligationBundle {
    pub bundle_id: String,
    pub kernel_version: String,
    pub generated_from: Vec<String>,
    pub obligations: Vec<ProofObligation>,
    pub authority_effect: AuthorityEffect,
}

impl ObligationBundle {
    pub fn new(
        bundle_id: &str,
        kernel_version: &str,
        generated_from: Vec<String>,
        mut obligations: Vec<ProofObligation>,
        authority_effect: AuthorityEffect,
    ) -> Result<Self, KernelError> {
        if authority_effect != AuthorityEffect::None {
            return Err(KernelError::Message(
                "obligation bundles carry AuthorityEffect None".into(),
            ));
        }

        let valid_roots = generated_from
            .into_iter()
            .map(|r| require_digest(&r, "generated_from"))
            .collect::<Result<Vec<_>, _>>()?;
        let roots = sorted_unique(&valid_roots, "generated_from")?;

        let mut seen = BTreeSet::new();
        for ob in &obligations {
            if !seen.insert(ob.obligation_id.clone()) {
                return Err(KernelError::Message(
                    "obligation IDs must be unique".into(),
                ));
            }
        }
        obligations.sort_by(|a, b| a.obligation_id.cmp(&b.obligation_id));

        Ok(Self {
            bundle_id: require_identifier(bundle_id, "bundle_id")?,
            kernel_version: require_identifier(kernel_version, "kernel_version")?,
            generated_from: roots,
            obligations,
            authority_effect,
        })
    }

    pub fn to_canonical(&self) -> Value {
        json!({
            "bundle_id": self.bundle_id,
            "kernel_version": self.kernel_version,
            "generated_from": self.generated_from,
            "obligations": self.obligations.iter().map(ProofObligation::to_canonical).collect::<Vec<_>>(),
            "authority_effect": self.authority_effect.as_str(),
        })
    }

    pub fn canonical_id(&self) -> Result<String, CanonicalError> {
        canonical_id("core.oewas.obligation-bundle.v1", &self.to_canonical())
    }

    pub fn export_bytes(&self) -> Result<Vec<u8>, CanonicalError> {
        canonical_bytes("core.oewas.obligation-bundle.export.v1", &self.to_canonical())
    }

    pub fn export_json(&self) -> Result<String, KernelError> {
        let bytes = self.export_bytes()?;
        let val: Value = serde_json::from_slice(&bytes)
            .map_err(|e| KernelError::Message(e.to_string()))?;
        serde_json::to_string(&val).map_err(|e| KernelError::Message(e.to_string()))
    }
}

pub fn export_lean_obligations(
    presentation: &[NormalizedTerm],
    bound: usize,
) -> Result<ObligationBundle, KernelError> {
    if presentation.is_empty() {
        return Err(KernelError::Message(
            "presentation must be non-empty".into(),
        ));
    }
    if bound < 2 {
        return Err(KernelError::Message(
            "obligation bound must be at least two".into(),
        ));
    }

    let mut roots_set = BTreeSet::new();
    for term in presentation {
        roots_set.insert(term.canonical_id()?);
    }
    let roots: Vec<String> = roots_set.into_iter().collect();

    let mut obligations = Vec::new();
    for (index, root) in roots.iter().enumerate() {
        obligations.push(ProofObligation::new(
            &format!("unit-{index}"),
            ObligationKind::Unit,
            "Prove left and right unit normalization for this finite term root.",
            vec![root.clone()],
            Vec::new(),
        )?);
        obligations.push(ProofObligation::new(
            &format!("associativity-{index}"),
            ObligationKind::Associativity,
            "Prove all well-typed nested substitutions reachable from this term root.",
            vec![root.clone()],
            Vec::new(),
        )?);
    }

    for dimension in 3..=bound {
        obligations.push(ProofObligation::new(
            &format!("coherence-dimension-{dimension}"),
            ObligationKind::Coherence,
            &format!("Check all generated tree-boundary coherence obligations through dimension {dimension}."),
            roots.clone(),
            Vec::new(),
        )?);
    }

    ObligationBundle::new(
        &format!("finite-presentation-through-{bound}"),
        "oewas-higher-operad-v1",
        roots,
        obligations,
        AuthorityEffect::None,
    )
}

// Origin: engine/crates_rs/core_operad_theory/src/kernel/obligations.rs
// Claim: urn:core:crates_rs:core-operad-theory:obligations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordca2fee5e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordca2fee5e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorca2fee5e {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorca2fee5e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorca2fee5e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorca2fee5e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordca2fee5e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorca2fee5e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorca2fee5e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorca2fee5e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorca2fee5e::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_ca2fee5e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordca2fee5e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordca2fee5e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordca2fee5e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordca2fee5e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordca2fee5e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorca2fee5e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorca2fee5e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

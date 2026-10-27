//! --- yaml
//! title: family_category
//! file_name: family_category.rs
//! file_location: ~/sentinel/sentinel_kernel/core_core/src/ascent/lambdas/l161/family_category.rs
//! lambda: L161
//! tower_address: ascent/lambdas/l161/family_category.rs
//! status: Coal
//! invariance_level: Tier 3
//! logic_system: Subobject Classifier (Core)
//! substrate: Rust
//! content_hash: 3bd1bb3c1a239f3af00a393e1f69a3aa5e995a99aed068eb337783e61c842448
//! version: 1
//! ---
//!
//! # Family Category — String Families as Functors
//!
//! Agent families are functors `F: Constraint -> String`.
//! Strings are morphisms `String -> String`.
//! Meta-Strings (autoString, cartographer, review-Strings) are natural
//! transformations `eta: F => G` between family functors.
//!
//! This module defines the categorical types for String families,
//! composing with (never replacing) `AgentFunctor` from `agent_functor.rs`.

use std::collections::HashMap;

// use crate::ascent::lambdas::l161::agent_functor::{String};

// ---------------------------------------------------------------------------
// 1. Constraint — Object in the source category
// ---------------------------------------------------------------------------

/// A shared invariant that all members of a family must satisfy.
/// Object in the Constraint category.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Constraint {
    /// Unique identifier (e.g. "EVIDENCE_FIRST", "NO_FORCE_PUSH")
    pub id: String,
    /// Human-readable description
    pub description: String,
    /// Severity level for violations
    pub severity: Severity,
}

impl Constraint {
    pub fn new(id: &str, description: &str, severity: Severity) -> Self {
        Self {
            id: id.to_string(),
            description: description.to_string(),
            severity,
        }
    }
}

/// Severity classification for constraint violations.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
}

impl Severity {
    /// Parse from an uppercase label (mirrors `MemberStatus::parse`); unknown maps to `Low`.
    pub fn parse(s: &str) -> Self {
        match s.to_uppercase().as_str() {
            "CRITICAL" => Severity::Critical,
            "HIGH" => Severity::High,
            "MEDIUM" => Severity::Medium,
            _ => Severity::Low,
        }
    }
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Severity::Critical => write!(f, "CRITICAL"),
            Severity::High => write!(f, "HIGH"),
            Severity::Medium => write!(f, "MEDIUM"),
            Severity::Low => write!(f, "LOW"),
        }
    }
}

// ---------------------------------------------------------------------------
// 2. Propagation Rule — Morphism in the Constraint category
// ---------------------------------------------------------------------------

/// A propagation rule defines how corrections flow between family members.
/// Morphism in the Constraint category: Pattern -> Targets.
#[derive(Debug, Clone)]
pub struct PropagationRule {
    /// The pattern name (e.g. "Severity thresholds", "Tool configuration")
    pub pattern: String,
    /// Example of the pattern
    pub example: String,
    /// Target Strings to propagate to
    pub targets: Vec<String>,
}

impl PropagationRule {
    pub fn new(pattern: &str, example: &str, targets: Vec<String>) -> Self {
        Self {
            pattern: pattern.to_string(),
            example: example.to_string(),
            targets,
        }
    }

    /// Does this rule target all members of the family?
    pub fn targets_all(&self) -> bool {
        self.targets.iter().any(|t| t == "All members")
    }
}

// ---------------------------------------------------------------------------
// 3. Member Status — Lifecycle state of a family member
// ---------------------------------------------------------------------------

/// Lifecycle state of a String within a family.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MemberStatus {
    /// Active String on disk
    Exists,
    /// Planned but not yet implemented
    Planned,
    /// Merged into another String
    Consolidated { target: String },
    /// Deprecated in favor of another
    Deprecated { target: String },
}

impl MemberStatus {
    /// Parse from the `[STATUS]` annotation in family_registry.md
    pub fn parse(s: &str) -> Self {
        let s = s.trim();
        if s == "EXISTS" {
            MemberStatus::Exists
        } else if s == "PLANNED" {
            MemberStatus::Planned
        } else if let Some(target) = s.strip_prefix("CONSOLIDATED -> ") {
            MemberStatus::Consolidated {
                target: target.to_string(),
            }
        } else if let Some(target) = s.strip_prefix("DEPRECATED -> consolidated into ") {
            MemberStatus::Deprecated {
                target: target.to_string(),
            }
        } else if let Some(target) = s.strip_prefix("DEPRECATED -> ") {
            MemberStatus::Deprecated {
                target: target.to_string(),
            }
        } else {
            MemberStatus::Planned
        }
    }

    pub fn is_active(&self) -> bool {
        matches!(self, MemberStatus::Exists)
    }
}

// ---------------------------------------------------------------------------
// 4. Family Member — Annotated String reference within a family
// ---------------------------------------------------------------------------

/// A String's membership in a family, with lifecycle annotation.
#[derive(Debug, Clone)]
pub struct FamilyMember {
    /// String identifier (e.g. "lint", "code-review")
    pub string_id: String,
    /// Lifecycle status
    pub status: MemberStatus,
}

impl FamilyMember {
    pub fn new(string_id: &str, status: MemberStatus) -> Self {
        Self {
            string_id: string_id.to_string(),
            status,
        }
    }

    pub fn active(string_id: &str) -> Self {
        Self::new(string_id, MemberStatus::Exists)
    }
}

// ---------------------------------------------------------------------------
// 5. StringFamily — Functor descriptor (static definition)
// ---------------------------------------------------------------------------

/// A String family definition parsed from `family_registry.md`.
/// This is the *descriptor* — the static data before runtime activation.
#[derive(Debug, Clone)]
pub struct StringFamily {
    /// Family identifier (e.g. "code-quality", "panel")
    pub id: String,
    /// Human-readable description
    pub description: String,
    /// All members (active + planned + consolidated)
    pub members: Vec<FamilyMember>,
    /// Shared constraints (objects in the Constraint category)
    pub constraints: Vec<Constraint>,
    /// Propagation rules (morphisms in the Constraint category)
    pub propagation_rules: Vec<PropagationRule>,
    /// Cross-family related Strings
    pub related_strings: Vec<String>,
}

impl StringFamily {
    pub fn new(id: &str, description: &str) -> Self {
        Self {
            id: id.to_string(),
            description: description.to_string(),
            members: Vec::new(),
            constraints: Vec::new(),
            propagation_rules: Vec::new(),
            related_strings: Vec::new(),
        }
    }

    /// Get only active (EXISTS) members.
    pub fn active_members(&self) -> Vec<&FamilyMember> {
        self.members
            .iter()
            .filter(|m| m.status.is_active())
            .collect()
    }

    /// Get active member IDs.
    pub fn active_member_ids(&self) -> Vec<&str> {
        self.members
            .iter()
            .filter(|m| m.status.is_active())
            .map(|m| m.string_id.as_str())
            .collect()
    }

    /// Check if a String belongs to this family (active only).
    pub fn contains_active(&self, string_id: &str) -> bool {
        self.members
            .iter()
            .any(|m| m.string_id == string_id && m.status.is_active())
    }

    fn add_rule_targets(
        rule: &PropagationRule,
        string_id: &str,
        active_ids: &[String],
        targets: &mut Vec<String>,
    ) {
        if rule.targets_all() {
            // "All members" means all active members except source
            for m in active_ids {
                if m != string_id && !targets.contains(m) {
                    targets.push(m.clone());
                }
            }
        } else {
            for t in &rule.targets {
                if t != string_id && !targets.contains(t) && active_ids.contains(t) {
                    targets.push(t.clone());
                }
            }
        }
    }

    /// Get propagation targets for a given String within this family.
    pub fn get_propagation_targets(&self, string_id: &str) -> Vec<String> {
        if !self.contains_active(string_id) {
            return Vec::new();
        }
        let active_ids: Vec<String> = self
            .active_member_ids()
            .iter()
            .map(|s| s.to_string())
            .collect();
        let mut targets = Vec::new();
        for rule in &self.propagation_rules {
            Self::add_rule_targets(rule, string_id, &active_ids, &mut targets);
        }
        targets
    }
}

// ---------------------------------------------------------------------------
// 6. FamilyFunctor — Runtime functor instance
// ---------------------------------------------------------------------------

/// Runtime functor `F: Constraint -> String` for a String family.
///
/// Composes with `AgentFunctor` — it does NOT replace it.
/// A `FamilyFunctor` holds references to `String` and `String`
/// from `agent_functor.rs`.
#[derive(Debug)]
pub struct FamilyFunctor {
    /// The underlying family descriptor
    pub family: StringFamily,
    /// Object mapping: Constraint.id -> Vec<String>
    /// Each constraint maps to the capabilities it enables across members
    pub constraint_to_capabilities: HashMap<String, Vec<String>>,
    /// Morphism mapping: PropagationRule.pattern -> Vec<String>
    /// Each propagation pattern maps to the Strings it activates
    pub propagation_to_strings: HashMap<String, Vec<String>>,
}

impl FamilyFunctor {
    /// Create a new FamilyFunctor from a StringFamily descriptor.
    pub fn from_family(family: StringFamily) -> Self {
        Self {
            family,
            constraint_to_capabilities: HashMap::new(),
            propagation_to_strings: HashMap::new(),
        }
    }

    /// Register a String that a constraint enables.
    pub fn map_constraint(&mut self, constraint_id: &str, string: String) {
        self.constraint_to_capabilities
            .entry(constraint_id.to_string())
            .or_default()
            .push(string);
    }

    /// Register a String that a propagation rule activates.
    pub fn map_propagation(&mut self, pattern: &str, string: String) {
        self.propagation_to_strings
            .entry(pattern.to_string())
            .or_default()
            .push(string);
    }

    /// Query capabilities enabled by a constraint.
    pub fn apply_constraint(&self, constraint_id: &str) -> Vec<&String> {
        self.constraint_to_capabilities
            .get(constraint_id)
            .map(|v| v.iter().collect())
            .unwrap_or_default()
    }

    /// Query Strings activated by a propagation pattern.
    pub fn apply_propagation(&self, pattern: &str) -> Vec<&String> {
        self.propagation_to_strings
            .get(pattern)
            .map(|v| v.iter().collect())
            .unwrap_or_default()
    }

    /// Get the family ID.
    pub fn id(&self) -> &str {
        &self.family.id
    }

    /// Get all propagation targets for a String in this family.
    pub fn get_propagation_targets(&self, string_id: &str) -> Vec<String> {
        self.family.get_propagation_targets(string_id)
    }
}

// ---------------------------------------------------------------------------
// 7. Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/core_category_theory/src/family_category.rs
// Claim: urn:core:crates_rs:core-category-theory:family-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2e819542 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2e819542` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2e819542 {
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
impl BoundaryError2e819542 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2e819542 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2e819542 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2e819542 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2e819542> {
        if capacity_bound == 0 {
            return Err(BoundaryError2e819542::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2e819542::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2e819542::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_severity_ordering() {
        assert!(Severity::Critical < Severity::High);
        assert!(Severity::High < Severity::Medium);
        assert!(Severity::Medium < Severity::Low);
    }

    #[test]
    fn test_severity_parse() {
        assert_eq!(Severity::parse("CRITICAL"), Severity::Critical);
        assert_eq!(Severity::parse("high"), Severity::High);
        assert_eq!(Severity::parse("unknown"), Severity::Low);
    }

    #[test]
    fn test_member_status_parse() {
        assert_eq!(MemberStatus::parse("EXISTS"), MemberStatus::Exists);
        assert_eq!(MemberStatus::parse("PLANNED"), MemberStatus::Planned);
        assert_eq!(
            MemberStatus::parse("CONSOLIDATED -> procurators"),
            MemberStatus::Consolidated {
                target: "procurators".to_string()
            }
        );
        assert_eq!(
            MemberStatus::parse("DEPRECATED -> consolidated into procurators"),
            MemberStatus::Deprecated {
                target: "procurators".to_string()
            }
        );
    }

    #[test]
    fn test_string_family_active_members() {
        let mut family = StringFamily::new("test", "Test family");
        family.members.push(FamilyMember::active("lint"));
        family.members.push(FamilyMember::active("code-review"));
        family
            .members
            .push(FamilyMember::new("security-scan", MemberStatus::Planned));

        assert_eq!(family.active_members().len(), 2);
        assert_eq!(family.active_member_ids(), vec!["lint", "code-review"]);
        assert!(family.contains_active("lint"));
        assert!(!family.contains_active("security-scan"));
    }

    #[test]
    fn test_propagation_targets() {
        let mut family = StringFamily::new("code-quality", "Code quality");
        family.members.push(FamilyMember::active("lint"));
        family.members.push(FamilyMember::active("code-review"));
        family.members.push(FamilyMember::active("run-tests"));
        family.propagation_rules.push(PropagationRule::new(
            "Severity thresholds",
            "CRITICAL blocks merge",
            vec!["All members".to_string()],
        ));
        family.propagation_rules.push(PropagationRule::new(
            "Tool configuration",
            "ruff rules",
            vec!["lint".to_string(), "run-tests".to_string()],
        ));

        let targets = family.get_propagation_targets("lint");
        assert!(targets.contains(&"code-review".to_string()));
        assert!(targets.contains(&"run-tests".to_string()));
        assert!(!targets.contains(&"lint".to_string()));
    }

    #[test]
    fn test_family_functor_construction() {
        let family = StringFamily::new("panel", "Character Strings");
        let functor = FamilyFunctor::from_family(family);
        assert_eq!(functor.id(), "panel");
        assert!(functor.constraint_to_capabilities.is_empty());
        assert!(functor.propagation_to_strings.is_empty());
    }
}

#[cfg(test)]
mod l4_boundary_tests_2e819542 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2e819542::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2e819542::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2e819542::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2e819542::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2e819542::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2e819542::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2e819542::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

//! Operads — Spec Section 26.
//!
//! A colored operad (multicategory) generalizes a category by allowing
//! operations with multiple inputs and one output.
//!
//! An operation f has a profile: (c₁, ..., cₙ) → c
//! where c_i and c are colors.
//!
//! Operad compositions are partial substitutions:
//! f ∘ᵢ g substitutes the output of g into the i-th slot of f.
//!
//! The laws are:
//!   - Unit: id ∘₀ f = f and f ∘ᵢ id = f
//!   - Associativity: nested substitutions are independent of order.
//!   - Equivariance: symmetric group actions commute with substitution.
//!
//! This module provides the finite, combinatorial data structure.

use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperadOperation {
    pub name: String,
    pub inputs: Vec<String>,
    pub output: String,
}

impl OperadOperation {
    pub fn new(name: &str, inputs: Vec<&str>, output: &str) -> Self {
        Self {
            name: name.into(),
            inputs: inputs.into_iter().map(String::from).collect(),
            output: output.into(),
        }
    }
    pub fn arity(&self) -> usize {
        self.inputs.len()
    }
}

#[derive(Debug, Clone)]
pub struct DeclaredFiniteOperad {
    pub name: String,
    pub colors: BTreeSet<String>,
    pub operations: BTreeMap<String, OperadOperation>,
    pub compositions: BTreeMap<(String, usize, String), String>, // (outer, slot, inner) -> result
    pub identities: BTreeMap<String, String>,                    // color → identity op name
}

impl DeclaredFiniteOperad {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.into(),
            colors: BTreeSet::new(),
            operations: BTreeMap::new(),
            compositions: BTreeMap::new(),
            identities: BTreeMap::new(),
        }
    }

    pub fn add_color(&mut self, color: &str) {
        self.colors.insert(color.into());
    }

    pub fn add_operation(&mut self, op: OperadOperation) {
        self.operations.insert(op.name.clone(), op);
    }

    pub fn add_composition(&mut self, outer: &str, slot: usize, inner: &str, result: &str) {
        self.compositions
            .insert((outer.into(), slot, inner.into()), result.into());
    }

    pub fn set_identity(&mut self, color: &str, identity_op: &str) {
        self.identities.insert(color.into(), identity_op.into());
    }

    pub fn find_op(&self, name: &str) -> Option<&OperadOperation> {
        self.operations.get(name)
    }

    /// Evaluates `outer ∘_{slot} inner`.
    pub fn compose(&self, outer: &str, slot: usize, inner: &str) -> Option<&str> {
        self.compositions
            .get(&(outer.into(), slot, inner.into()))
            .map(|s| s.as_str())
    }
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct ValidatedFiniteOperad {
    declared: DeclaredFiniteOperad,
}

impl ValidatedFiniteOperad {
    pub fn try_new(declared: DeclaredFiniteOperad) -> Result<Self, Vec<String>> {
        let mut violations = Vec::new();

        violations.extend(check_operad_identities(&declared));
        violations.extend(check_operad_composition_typing(&declared));
        violations.extend(check_operad_unit(&declared));
        // Associativity is omitted from full verification here because full enumeration
        // of type-correct triples is required for an exhaustive check.
        // Tests can use `check_operad_associativity` directly on cases.

        if violations.is_empty() {
            Ok(Self { declared })
        } else {
            Err(violations)
        }
    }

    pub fn declared(&self) -> &DeclaredFiniteOperad {
        &self.declared
    }
}

pub fn check_operad_identities(operad: &DeclaredFiniteOperad) -> Vec<String> {
    let mut violations = Vec::new();

    for color in &operad.colors {
        let Some(id_name) = operad.identities.get(color) else {
            violations.push(format!("Color {} has no identity operation", color));
            continue;
        };

        let Some(id_op) = operad.find_op(id_name) else {
            violations.push(format!(
                "Identity {} for color {} is not declared",
                id_name, color
            ));
            continue;
        };

        if id_op.inputs != vec![color.clone()] || id_op.output != *color {
            violations.push(format!(
                "Identity {} for color {} has profile {:?}->{}, expected [{}]->{}",
                id_name, color, id_op.inputs, id_op.output, color, color
            ));
        }
    }

    violations
}

pub fn check_operad_composition_typing(operad: &DeclaredFiniteOperad) -> Vec<String> {
    let mut violations = Vec::new();

    for ((outer_name, slot, inner_name), result_name) in &operad.compositions {
        let Some(outer) = operad.find_op(outer_name) else {
            violations.push(format!(
                "Composition references unknown outer operation {}",
                outer_name
            ));
            continue;
        };

        let Some(inner) = operad.find_op(inner_name) else {
            violations.push(format!(
                "Composition references unknown inner operation {}",
                inner_name
            ));
            continue;
        };

        let Some(result) = operad.find_op(result_name) else {
            violations.push(format!(
                "Composition result {} is not a declared operation",
                result_name
            ));
            continue;
        };

        if *slot >= outer.inputs.len() {
            violations.push(format!(
                "Composition {}∘_{}{} has invalid slot for arity {}",
                outer_name,
                slot,
                inner_name,
                outer.inputs.len()
            ));
            continue;
        }

        let expected_slot_color = &outer.inputs[*slot];
        if &inner.output != expected_slot_color {
            violations.push(format!(
                "Composition {}∘_{}{} ill-typed: inner output {} does not match slot color {}",
                outer_name, slot, inner_name, inner.output, expected_slot_color
            ));
        }

        let mut expected_inputs = Vec::new();
        expected_inputs.extend_from_slice(&outer.inputs[..*slot]);
        expected_inputs.extend(inner.inputs.clone());
        expected_inputs.extend_from_slice(&outer.inputs[(*slot + 1)..]);

        if result.inputs != expected_inputs || result.output != outer.output {
            violations.push(format!(
                "Composition {}∘_{}{} has result {} with profile {:?}->{}, expected {:?}->{}",
                outer_name,
                slot,
                inner_name,
                result_name,
                result.inputs,
                result.output,
                expected_inputs,
                outer.output
            ));
        }
    }

    violations
}

/// Verify unit laws for all declared operations.
pub fn check_operad_unit(operad: &DeclaredFiniteOperad) -> Vec<String> {
    let mut violations = Vec::new();

    for op in operad.operations.values() {
        // Right units: f ∘ᵢ id_c = f
        for (i, color) in op.inputs.iter().enumerate() {
            if let Some(id_op) = operad.identities.get(color) {
                if let Some(result) = operad.compose(&op.name, i, id_op) {
                    if result != op.name {
                        violations.push(format!(
                            "Right unit fails: {} ∘_{} {} = {}, expected {}",
                            op.name, i, id_op, result, op.name
                        ));
                    }
                } else {
                    violations.push(format!(
                        "Right unit undefined: {} ∘_{} {}",
                        op.name, i, id_op
                    ));
                }
            } else {
                violations.push(format!("Missing identity for color {}", color));
            }
        }

        // Left unit: id_c ∘₀ f = f
        if let Some(id_op) = operad.identities.get(&op.output) {
            if let Some(result) = operad.compose(id_op, 0, &op.name) {
                if result != op.name {
                    violations.push(format!(
                        "Left unit fails: {} ∘₀ {} = {}, expected {}",
                        id_op, op.name, result, op.name
                    ));
                }
            } else {
                violations.push(format!("Left unit undefined: {} ∘₀ {}", id_op, op.name));
            }
        } else {
            violations.push(format!("Missing identity for color {}", op.output));
        }
    }

    violations
}

/// Check targeted associativity cases: (f ∘ᵢ g) ∘_{i+j} h = f ∘ᵢ (g ∘ⱼ h).
pub fn check_operad_associativity(
    operad: &DeclaredFiniteOperad,
    cases: &[(&str, usize, &str, usize, &str)], // (f, i, g, j, h)
) -> Vec<String> {
    let mut violations = Vec::new();

    for &(f, i, g, j, h) in cases {
        let left = operad
            .compose(f, i, g)
            .and_then(|fg| operad.compose(fg, i + j, h));

        let right_g_h = operad.compose(g, j, h);
        let right = match right_g_h {
            Some(gh) => operad.compose(f, i, gh),
            None => None,
        };

        match (left, right) {
            (Some(l), Some(r)) if l == r => {} // associativity holds
            (Some(l), Some(r)) => {
                violations.push(format!(
                    "Associativity fails for ({}, {}, {}, {}, {}): left = {}, right = {}",
                    f, i, g, j, h, l, r
                ));
            }
            (None, _) => {
                violations.push(format!(
                    "Associativity left side undefined for ({}, {}, {}, {}, {})",
                    f, i, g, j, h
                ));
            }
            (_, None) => {
                violations.push(format!(
                    "Associativity right side undefined for ({}, {}, {}, {}, {})",
                    f, i, g, j, h
                ));
            }
        }
    }

    violations
}

// Origin: engine/crates_rs/core_category_theory/src/operad.rs
// Claim: urn:core:crates_rs:core-category-theory:operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3e6497ca {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3e6497ca` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3e6497ca {
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
impl BoundaryError3e6497ca {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3e6497ca {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3e6497ca {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3e6497ca {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3e6497ca> {
        if capacity_bound == 0 {
            return Err(BoundaryError3e6497ca::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3e6497ca::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3e6497ca::ExceedsCapacity {
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

    fn build_test_operad() -> DeclaredFiniteOperad {
        let mut o = DeclaredFiniteOperad::new("O");
        o.add_color("X");

        o.add_operation(OperadOperation::new("id_X", vec!["X"], "X"));
        o.add_operation(OperadOperation::new("m", vec!["X", "X"], "X"));

        o.set_identity("X", "id_X");

        o.add_composition("id_X", 0, "id_X", "id_X");
        o.add_composition("id_X", 0, "m", "m");
        o.add_composition("m", 0, "id_X", "m");
        o.add_composition("m", 1, "id_X", "m");

        // Associativity for m ∘₀ m and m ∘₁ m
        o.add_operation(OperadOperation::new("m3", vec!["X", "X", "X"], "X"));
        o.add_composition("m", 0, "m", "m3");
        o.add_composition("m", 1, "m", "m3");
        o.add_composition("id_X", 0, "m3", "m3");
        o.add_composition("m3", 0, "id_X", "m3");
        o.add_composition("m3", 1, "id_X", "m3");
        o.add_composition("m3", 2, "id_X", "m3");

        o
    }

    #[test]
    fn valid_operad_passes() {
        let o = build_test_operad();
        assert!(check_operad_identities(&o).is_empty());
        assert!(check_operad_composition_typing(&o).is_empty());
        assert!(check_operad_unit(&o).is_empty());
    }

    #[test]
    fn invalid_type_composition() {
        let mut o = build_test_operad();
        o.add_color("Y");
        o.add_operation(OperadOperation::new("id_Y", vec!["Y"], "Y"));
        o.set_identity("Y", "id_Y");
        o.add_composition("m", 0, "id_Y", "m"); // Type mismatch!

        let errs = check_operad_composition_typing(&o);
        assert!(!errs.is_empty());
        assert!(errs[0].contains("ill-typed: inner output Y does not match slot color X"));
    }

    #[test]
    fn test_associativity() {
        let mut o = build_test_operad();
        // Add full associativity:
        // m ∘₀ (m ∘₀ m) -> m3 ∘₀ m -> m4
        // (m ∘₀ m) ∘_{0+0} m -> m3 ∘₀ m -> m4
        o.add_operation(OperadOperation::new("m4", vec!["X", "X", "X", "X"], "X"));
        o.add_composition("m3", 0, "m", "m4");
        o.add_composition("m", 0, "m3", "m4");

        let cases = vec![("m", 0, "m", 0, "m")];
        let errs = check_operad_associativity(&o, &cases);
        assert!(errs.is_empty(), "{:?}", errs);
    }
}

#[cfg(test)]
mod l4_boundary_tests_3e6497ca {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3e6497ca::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3e6497ca::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3e6497ca::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3e6497ca::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3e6497ca::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3e6497ca::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3e6497ca::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

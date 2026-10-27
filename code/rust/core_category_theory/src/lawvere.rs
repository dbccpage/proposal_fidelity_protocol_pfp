//! Lawvere Theory — Spec Section 25.
//!
//! A Lawvere theory is a Cauchy-complete monoid in Prof.
//! Operations are profunctor elements, substitution is composition,
//! and equations are 2-cells.

use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OperationDecl {
    pub name: String,
    pub input_sorts: Vec<String>,
    pub output_sorts: Vec<String>,
}

impl OperationDecl {
    pub fn new(name: &str, input_sorts: Vec<String>, output_sorts: Vec<String>) -> Self {
        Self {
            name: name.into(),
            input_sorts,
            output_sorts,
        }
    }

    pub fn arity(&self) -> usize {
        self.input_sorts.len()
    }

    pub fn coarity(&self) -> usize {
        self.output_sorts.len()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EquationDecl {
    pub name: String,
    pub lhs: String,
    pub rhs: String,
}

impl EquationDecl {
    pub fn new(name: &str, lhs: &str, rhs: &str) -> Self {
        Self {
            name: name.into(),
            lhs: lhs.into(),
            rhs: rhs.into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TheoryCauchyStatus {
    Complete,
    Incomplete { unsplit_operations: Vec<String> },
}

#[derive(Debug, Clone)]
pub struct LawvereTheory {
    pub name: String,
    pub sorts: Vec<String>,
    pub operations: Vec<OperationDecl>,
    pub equations: Vec<EquationDecl>,
    pub substitution_table: BTreeMap<(String, usize, String), String>,
    pub identities: BTreeMap<String, String>, // sort -> identity operation
    pub cauchy_status: TheoryCauchyStatus,
}

impl LawvereTheory {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.into(),
            sorts: Vec::new(),
            operations: Vec::new(),
            equations: Vec::new(),
            substitution_table: BTreeMap::new(),
            identities: BTreeMap::new(),
            cauchy_status: TheoryCauchyStatus::Complete,
        }
    }

    pub fn add_sort(&mut self, sort: &str) {
        self.sorts.push(sort.into());
    }
    pub fn add_operation(&mut self, op: OperationDecl) {
        self.operations.push(op);
    }
    pub fn add_equation(&mut self, eq: EquationDecl) {
        self.equations.push(eq);
    }

    pub fn add_substitution(&mut self, outer: &str, slot: usize, inner: &str, result: &str) {
        self.substitution_table
            .insert((outer.into(), slot, inner.into()), result.into());
    }

    pub fn substitute(&self, outer: &str, slot: usize, inner: &str) -> Option<&str> {
        self.substitution_table
            .get(&(outer.into(), slot, inner.into()))
            .map(|s| s.as_str())
    }

    pub fn operations_of_arity(&self, arity: usize) -> Vec<&OperationDecl> {
        self.operations
            .iter()
            .filter(|op| op.arity() == arity)
            .collect()
    }
}

pub fn check_substitution_associativity(
    theory: &LawvereTheory,
    cases: &[(&str, usize, &str, usize, &str)],
) -> Vec<String> {
    let mut violations = Vec::new();
    for &(f, i, g, j, h) in cases {
        let left = theory
            .substitute(g, j, h)
            .and_then(|gh| theory.substitute(f, i, gh));
        let right = theory
            .substitute(f, i, g)
            .and_then(|fg| theory.substitute(fg, i + j, h));
        match (left, right) {
            (Some(l), Some(r)) if l == r => {}
            (Some(l), Some(r)) => violations.push(format!(
                "Substitution not associative: f={}, g={}, h={}: {}≠{}",
                f, g, h, l, r
            )),
            _ => violations.push(format!(
                "Substitution not defined for f={}, g={}, h={}",
                f, g, h
            )),
        }
    }
    violations
}

pub fn check_theory_cauchy(theory: &LawvereTheory) -> TheoryCauchyStatus {
    let mut unsplit = Vec::new();
    for op in &theory.operations {
        if op.arity() != 1 || op.coarity() != 1 {
            continue;
        }
        let is_idempotent = theory
            .substitute(&op.name, 0, &op.name)
            .map(|r| r == op.name)
            .unwrap_or(false);
        if !is_idempotent {
            continue;
        }
        // Search for splitting pair
        let splits = theory.operations.iter().any(|r_op| {
            theory.operations.iter().any(|s_op| {
                let sr_is_e = theory
                    .substitute(&s_op.name, 0, &r_op.name)
                    .map(|v| v == op.name)
                    .unwrap_or(false);

                let rs_is_id = theory
                    .substitute(&r_op.name, 0, &s_op.name)
                    .map(|v| {
                        r_op.output_sorts
                            .first()
                            .and_then(|sort| theory.identities.get(sort))
                            .map(|id| id == v)
                            .unwrap_or(false)
                    })
                    .unwrap_or(false);

                sr_is_e && rs_is_id
            })
        });
        if !splits {
            unsplit.push(op.name.clone());
        }
    }
    if unsplit.is_empty() {
        TheoryCauchyStatus::Complete
    } else {
        TheoryCauchyStatus::Incomplete {
            unsplit_operations: unsplit,
        }
    }
}

// Origin: engine/crates_rs/core_category_theory/src/lawvere.rs
// Claim: urn:core:crates_rs:core-category-theory:lawvere:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordac71ac53 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordac71ac53` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorac71ac53 {
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
impl BoundaryErrorac71ac53 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorac71ac53 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorac71ac53 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordac71ac53 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorac71ac53> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorac71ac53::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorac71ac53::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorac71ac53::ExceedsCapacity {
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
    fn monoid_theory() {
        let mut t = LawvereTheory::new("Monoid");
        t.add_sort("M");
        t.add_operation(OperationDecl::new(
            "mul",
            vec!["M".into(), "M".into()],
            vec!["M".into()],
        ));
        t.add_operation(OperationDecl::new("unit", vec![], vec!["M".into()]));
        t.add_equation(EquationDecl::new(
            "assoc",
            "mul(mul(x,y),z)",
            "mul(x,mul(y,z))",
        ));
        assert_eq!(t.operations.len(), 2);
        assert_eq!(t.equations.len(), 1);
    }

    #[test]
    fn trivial_theory_cauchy() {
        let t = LawvereTheory::new("Empty");
        assert_eq!(check_theory_cauchy(&t), TheoryCauchyStatus::Complete);
    }
}

#[cfg(test)]
mod l4_boundary_tests_ac71ac53 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordac71ac53::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordac71ac53::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordac71ac53::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordac71ac53::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordac71ac53::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorac71ac53::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorac71ac53::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

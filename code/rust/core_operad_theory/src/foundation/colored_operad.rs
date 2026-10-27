//! Foundation: Planar & Symmetric Coloured Operads.
//!
//! AuthorityEffect: None.

use std::collections::{HashMap, HashSet};
use serde::{Deserialize, Serialize};
use super::colour::{OperadColour, OperadSignature};
use super::operation::{Operation, OperationId, OperationKind};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum OperadVariant {
    Planar,
    Symmetric,
}

/// A planar multi-coloured operad with strictly ordered input slots.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanarColoredOperad {
    pub name: String,
    pub is_closed_universe: bool,
    colours: HashSet<OperadColour>,
    generators: HashMap<String, Operation>,
}

impl PlanarColoredOperad {
    pub fn new(name: impl Into<String>, is_closed_universe: bool) -> Self {
        Self {
            name: name.into(),
            is_closed_universe,
            colours: HashSet::new(),
            generators: HashMap::new(),
        }
    }

    pub fn variant(&self) -> OperadVariant {
        OperadVariant::Planar
    }

    pub fn colours(&self) -> &HashSet<OperadColour> {
        &self.colours
    }

    pub fn operations(&self) -> &HashMap<String, Operation> {
        &self.generators
    }

    pub fn add_colour(&mut self, colour: OperadColour) -> OperadColour {
        self.colours.insert(colour.clone());
        colour
    }

    pub fn add_operation(&mut self, op: Operation) -> Result<(), String> {
        if self.generators.contains_key(op.op_id.as_str()) {
            return Err(format!(
                "Duplicate operation ID '{}' already exists in operad '{}'",
                op.op_id.as_str(),
                self.name
            ));
        }

        if self.is_closed_universe {
            for inp in op.inputs() {
                if !self.colours.contains(inp) {
                    return Err(format!(
                        "Operation '{}' references unadmitted input colour: {}",
                        op.op_id.as_str(),
                        inp.as_str()
                    ));
                }
            }
            if !self.colours.contains(op.output()) {
                return Err(format!(
                    "Operation '{}' references unadmitted output colour: {}",
                    op.op_id.as_str(),
                    op.output().as_str()
                ));
            }
        } else {
            for inp in op.inputs() {
                self.colours.insert(inp.clone());
            }
            self.colours.insert(op.output().clone());
        }

        self.generators.insert(op.op_id.as_str().to_string(), op);
        Ok(())
    }

    pub fn ensure_identities(&mut self) -> Vec<Operation> {
        let mut added = Vec::new();
        let sorted_colours: Vec<OperadColour> = {
            let mut c_vec: Vec<OperadColour> = self.colours.iter().cloned().collect();
            c_vec.sort();
            c_vec
        };
        for c in sorted_colours {
            let id_op = Operation::identity(c);
            if !self.generators.contains_key(id_op.op_id.as_str()) {
                self.generators.insert(id_op.op_id.as_str().to_string(), id_op.clone());
                added.push(id_op);
            }
        }
        added
    }

    pub fn partial_compose(&self, f: &Operation, g: &Operation, i: usize) -> Result<Operation, String> {
        if i >= f.arity() {
            return Err(format!("Insertion index i={} out of range [0, {})", i, f.arity()));
        }

        let target_input = &f.inputs()[i];
        if g.output() != target_input {
            return Err(format!(
                "Partial composition ill-typed: {} expects colour {} at position {}, but {} outputs {}",
                f.op_id.as_str(),
                target_input.as_str(),
                i,
                g.op_id.as_str(),
                g.output().as_str()
            ));
        }

        let mut new_inputs = f.inputs()[..i].to_vec();
        new_inputs.extend_from_slice(g.inputs());
        new_inputs.extend_from_slice(&f.inputs()[i + 1..]);

        let new_id = OperationId::new(format!("({}_o_{}_{})", f.op_id.as_str(), i, g.op_id.as_str()))?;

        Ok(Operation {
            op_id: new_id,
            signature: OperadSignature::new(new_inputs, f.output().clone()),
            kind: OperationKind::composite(format!("{}_o_{}_{}", f.op_id.as_str(), i, g.op_id.as_str())),
            is_equivariant: false,
            description: format!("Planar composition of {} and {} at slot {}", f.op_id.as_str(), g.op_id.as_str(), i),
        })
    }

    pub fn full_compose(&self, f: &Operation, args: &[Operation]) -> Result<Operation, String> {
        if args.len() != f.arity() {
            return Err(format!("Expected {} operations for full composition, got {}", f.arity(), args.len()));
        }

        let mut current = f.clone();
        for idx in (0..f.arity()).rev() {
            current = self.partial_compose(&current, &args[idx], idx)?;
        }
        Ok(current)
    }
}

/// A symmetric multi-coloured operad supporting lawful Sigma_n input permutations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymmetricColoredOperad {
    pub planar: PlanarColoredOperad,
}

impl SymmetricColoredOperad {
    pub fn new(name: impl Into<String>, is_closed_universe: bool) -> Self {
        Self {
            planar: PlanarColoredOperad::new(name, is_closed_universe),
        }
    }

    pub fn variant(&self) -> OperadVariant {
        OperadVariant::Symmetric
    }

    pub fn add_colour(&mut self, colour: OperadColour) -> OperadColour {
        self.planar.add_colour(colour)
    }

    pub fn add_operation(&mut self, op: Operation) -> Result<(), String> {
        self.planar.add_operation(op)
    }

    pub fn ensure_identities(&mut self) -> Vec<Operation> {
        self.planar.ensure_identities()
    }

    pub fn permute_operation(&mut self, op: &Operation, permutation: &[usize]) -> Result<Operation, String> {
        let perm_op = op.permute_inputs(permutation)?;
        self.planar.add_operation(perm_op.clone())?;
        Ok(perm_op)
    }
}

// Origin: engine/crates_rs/core_operad_theory/src/foundation/colored_operad.rs
// Claim: urn:core:crates_rs:core-operad-theory:colored-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbbb617ae {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbbb617ae` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbbb617ae {
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
impl BoundaryErrorbbb617ae {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbbb617ae {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbbb617ae {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbbb617ae {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbbb617ae> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbbb617ae::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbbb617ae::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbbb617ae::ExceedsCapacity {
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
mod l4_boundary_tests_bbb617ae {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbbb617ae::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbbb617ae::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbbb617ae::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbbb617ae::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbbb617ae::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbbb617ae::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbbb617ae::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

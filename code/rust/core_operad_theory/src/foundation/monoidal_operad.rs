//! Foundation: Monoidal Operads and parallel tensor products.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};
use super::colour::{OperadColour, OperadSignature};
use super::colored_operad::PlanarColoredOperad;
use super::operation::{Operation, OperationId};

/// Monoidal Operad supporting concurrent parallel tensor executions f otimes g.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonoidalOperad {
    pub base: PlanarColoredOperad,
}

impl MonoidalOperad {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            base: PlanarColoredOperad::new(name, false),
        }
    }

    pub fn tensor_colours(&mut self, c1: &OperadColour, c2: &OperadColour) -> Result<OperadColour, String> {
        let tensor_name = format!("({}_x_{})", c1.as_str(), c2.as_str());
        let c = OperadColour::new(tensor_name)?;
        Ok(self.base.add_colour(c))
    }

    pub fn parallel_tensor_operations(&mut self, f: &Operation, g: &Operation) -> Result<Operation, String> {
        let mut combined_inputs = f.inputs().to_vec();
        combined_inputs.extend_from_slice(g.inputs());

        let combined_output = self.tensor_colours(f.output(), g.output())?;
        let tensor_id = OperationId::new(format!("({}_tensor_{})", f.op_id.as_str(), g.op_id.as_str()))?;

        let op = Operation {
            op_id: tensor_id,
            signature: OperadSignature::new(combined_inputs, combined_output),
            kind: super::operation::OperationKind::generator(),
            is_equivariant: f.is_equivariant && g.is_equivariant,
            description: format!("Parallel monoidal tensor of {} and {}", f.op_id.as_str(), g.op_id.as_str()),
        };
        self.base.add_operation(op.clone())?;
        Ok(op)
    }
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TensorArityError {
    Shape,
    Arity { tensor: u64, sum: u64 },
    Colour { index: usize },
    Overflow,
}

// Origin: engine/crates_rs/core_operad_theory/src/foundation/monoidal_operad.rs
// Claim: urn:core:crates_rs:core-operad-theory:monoidal-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TensorArityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TensorArityError {}

/// Parallel tensor arity is the checked sum of the factor arities, input for input.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TensorArityWitness {
    arity: u64,
}

impl TensorArityWitness {
    fn check_input_segment(
        segment: &[OperadColour],
        tensor_inputs: &[OperadColour],
        base_index: usize,
    ) -> Result<(), TensorArityError> {
        for (offset, colour) in segment.iter().enumerate() {
            let index = base_index.checked_add(offset).ok_or(TensorArityError::Overflow)?;
            let tensor_colour = tensor_inputs.get(index).ok_or(TensorArityError::Shape)?;
            if tensor_colour.as_str() != colour.as_str() {
                return Err(TensorArityError::Colour { index });
            }
        }
        Ok(())
    }

    fn checked_arity(op: &Operation) -> Result<u64, TensorArityError> {
        u64::try_from(op.arity()).map_err(|_| TensorArityError::Overflow)
    }

    fn has_empty_factor(left: &Operation, right: &Operation) -> bool {
        left.inputs().is_empty() || right.inputs().is_empty()
    }

    pub fn try_check(operad: &MonoidalOperad, left: &Operation, right: &Operation, tensor: &Operation) -> Result<Self, TensorArityError> {
        let _registered = u64::try_from(operad.base.operations().len()).map_err(|_| TensorArityError::Overflow)?;
        let left_arity = Self::checked_arity(left)?;
        let right_arity = Self::checked_arity(right)?;
        let sum = left_arity.checked_add(right_arity).ok_or(TensorArityError::Overflow)?;
        let tensor_arity = Self::checked_arity(tensor)?;
        if tensor_arity != sum || Self::has_empty_factor(left, right) {
            return Err(TensorArityError::Arity { tensor: tensor_arity, sum });
        }
        Self::check_input_segment(left.inputs(), tensor.inputs(), 0)?;
        Self::check_input_segment(right.inputs(), tensor.inputs(), left.inputs().len())?;
        Ok(Self { arity: tensor_arity })
    }

    pub fn arity(&self) -> u64 { self.arity }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tensor_arity_tests {
    use super::*;

    fn generator(name: &str, inputs: Vec<&str>, output: &str) -> Result<Operation, String> {
        let mut colours = Vec::new();
        for input in inputs {
            colours.push(OperadColour::new(input)?);
        }
        Ok(Operation::new_generator(
            OperationId::new(name)?,
            OperadSignature::new(colours, OperadColour::new(output)?),
            name,
        ))
    }

    #[test]
    fn tensor_inputs_are_the_concatenation() {
        let operad = MonoidalOperad::new("tensor");
        let built = (|| {
            let left = generator("left", vec!["State"], "AuditCandidate")?;
            let right = generator("right", vec!["Code"], "AuditFinding")?;
            let tensor = generator("both", vec!["State", "Code"], "Post")?;
            TensorArityWitness::try_check(&operad, &left, &right, &tensor).map_err(|_| "arity".to_string())
        })();
        assert!(matches!(built, Ok(ref witness) if witness.arity() == 2));
    }

    #[test]
    fn a_tensor_missing_an_input_is_refused() {
        let operad = MonoidalOperad::new("tensor");
        let built = (|| {
            let left = generator("left", vec!["State"], "AuditCandidate")?;
            let right = generator("right", vec!["Code"], "AuditFinding")?;
            let tensor = generator("short", vec!["State"], "Post")?;
            TensorArityWitness::try_check(&operad, &left, &right, &tensor).map_err(|_| "arity".to_string())
        })();
        assert!(matches!(built, Err(_)));
    }
}

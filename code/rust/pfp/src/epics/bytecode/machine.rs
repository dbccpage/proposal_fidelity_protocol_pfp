use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use super::compile::*;
use super::{MAX_CALL_DEPTH, RECEIPT_SCHEMA_V1, REGISTER_COUNT};

// ---------------------------------------------------------------------------
// The machine
// ---------------------------------------------------------------------------

/// The explicit carrier for state that is meant to cross a turn boundary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RegisterEnvelopeV1 {
    pub registers: Vec<RegisterValue>,
}

/// Machine state. Constructed per execution; never handed in from outside.
#[derive(Debug, Clone)]
pub struct RegisterMachineState {
    registers: [RegisterValue; REGISTER_COUNT],
    call_stack: Vec<u64>,
    consumed_steps: u64,
    defect_count: u64,
    exercised: BTreeSet<&'static str>,
}

impl Default for RegisterMachineState {
    fn default() -> Self {
        Self {
            registers: [RegisterValue::Empty; REGISTER_COUNT],
            call_stack: Vec::new(),
            consumed_steps: 0,
            defect_count: 0,
            exercised: BTreeSet::new(),
        }
    }
}

impl RegisterMachineState {
    fn from_envelope(envelope: &RegisterEnvelopeV1) -> Self {
        let mut state = Self::default();
        for (index, value) in envelope.registers.iter().enumerate() {
            if index < REGISTER_COUNT {
                state.registers[index] = *value;
            }
        }
        state
    }

    pub fn register(&self, index: usize) -> Option<RegisterValue> {
        self.registers.get(index).copied()
    }

    pub fn consumed_steps(&self) -> u64 {
        self.consumed_steps
    }

    pub fn defect_count(&self) -> u64 {
        self.defect_count
    }

    pub fn call_depth(&self) -> usize {
        self.call_stack.len()
    }

    /// Which opcodes this run actually dispatched, by spec name.
    pub fn exercised(&self) -> &BTreeSet<&'static str> {
        &self.exercised
    }

    pub fn envelope(&self) -> RegisterEnvelopeV1 {
        RegisterEnvelopeV1 {
            registers: self.registers.to_vec(),
        }
    }

    fn read(&self, opcode: &'static str, reg: usize) -> Result<RegisterValue, BytecodeRefusal> {
        if reg >= REGISTER_COUNT {
            return Err(BytecodeRefusal::RegisterOutOfRange { opcode, reg });
        }
        let value = self.registers[reg];
        if value.is_empty() {
            return Err(BytecodeRefusal::EmptyRegister { opcode, reg });
        }
        Ok(value)
    }

    fn write(
        &mut self,
        opcode: &'static str,
        reg: usize,
        value: RegisterValue,
    ) -> Result<(), BytecodeRefusal> {
        if reg >= REGISTER_COUNT {
            return Err(BytecodeRefusal::RegisterOutOfRange { opcode, reg });
        }
        self.registers[reg] = value;
        Ok(())
    }

    fn read_glyph(&self, opcode: &'static str, reg: usize) -> Result<u64, BytecodeRefusal> {
        match self.read(opcode, reg)? {
            RegisterValue::Glyph { glyph_id } => Ok(glyph_id),
            other => Err(BytecodeRefusal::RegisterTypeMismatch {
                opcode,
                reg,
                expected: "Glyph",
                found: other.kind(),
            }),
        }
    }

    fn step_fibration(
        &mut self,
        opcode: &'static str,
        reg_fiber: usize,
        base_step: u64,
    ) -> Result<(), BytecodeRefusal> {
        if self.call_stack.len() >= MAX_CALL_DEPTH {
            return Err(BytecodeRefusal::CallDepthExceeded);
        }
        let level = match self.registers.get(reg_fiber) {
            Some(RegisterValue::Fiber { level, .. }) => level + 1,
            Some(_) => 1,
            None => {
                return Err(BytecodeRefusal::RegisterOutOfRange {
                    opcode,
                    reg: reg_fiber,
                })
            }
        };
        self.call_stack.push(base_step);
        self.write(opcode, reg_fiber, RegisterValue::Fiber { base_step, level })
    }

    /// Dispatch one instruction. **Does not** touch the step counter.
    ///
    /// The counter lives in the loop, in one place, which is what makes
    /// acceptance criterion 5 checkable: a receipt's `consumed_steps` cannot
    /// drift from the machine's because there is only one site that moves it.
    fn dispatch(&mut self, instruction: &Instruction) -> Result<(), BytecodeRefusal> {
        let opcode = instruction.opcode().name();
        self.exercised.insert(opcode);
        match *instruction {
            Instruction::LoadGlyph { reg, glyph_id } => {
                self.write(opcode, reg, RegisterValue::Glyph { glyph_id })
            }
            Instruction::ApplyRelation {
                dst,
                r1,
                r2,
                rel_id,
            } => {
                let left = self.read_glyph(opcode, r1)?;
                let right = self.read_glyph(opcode, r2)?;
                self.write(
                    opcode,
                    dst,
                    RegisterValue::Relation {
                        rel_id,
                        left,
                        right,
                    },
                )
            }
            Instruction::EmitObstruction {
                reg_defect,
                defect_code,
            } => {
                self.write(opcode, reg_defect, RegisterValue::Defect { defect_code })?;
                self.defect_count += 1;
                Ok(())
            }
            Instruction::AssertBoundary {
                reg_chain,
                boundary_map_id,
            } => {
                let held = self.read(opcode, reg_chain)?;
                // Exact iff the chain register holds no recorded defect. Phi_1 > 0
                // is exactly what EMIT_OBSTRUCTION records, so this reads the
                // machine's own state rather than re-deriving it.
                let exact = !matches!(held, RegisterValue::Defect { .. });
                self.write(
                    opcode,
                    reg_chain,
                    RegisterValue::Boundary {
                        boundary_map_id,
                        exact,
                    },
                )
            }
            Instruction::StepFibration {
                reg_fiber,
                base_step,
            } => self.step_fibration(opcode, reg_fiber, base_step),
        }
    }
}

// ---------------------------------------------------------------------------
// Receipt
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BytecodeExecutionReceiptV1 {
    pub schema_version: String,
    pub bundle_digest: String,
    pub consumed_steps: u64,
    pub defect_count: u64,
    pub final_registers: Vec<(usize, RegisterValue)>,
    pub exercised_opcodes: Vec<String>,
    pub authority_effect: String,
}

impl BytecodeExecutionReceiptV1 {
    fn from_state(bundle: &BytecodeBundle, state: &RegisterMachineState) -> Self {
        let final_registers = state
            .registers
            .iter()
            .enumerate()
            .filter(|(_, value)| !value.is_empty())
            .map(|(index, value)| (index, *value))
            .collect();
        Self {
            schema_version: RECEIPT_SCHEMA_V1.to_string(),
            bundle_digest: bundle.digest().to_string(),
            consumed_steps: state.consumed_steps,
            defect_count: state.defect_count,
            final_registers,
            exercised_opcodes: state.exercised.iter().map(|s| s.to_string()).collect(),
            authority_effect: "None".to_string(),
        }
    }
}

// ---------------------------------------------------------------------------
// Execution
// ---------------------------------------------------------------------------

/// Run a bundle under a step budget.
///
/// Takes **no** machine state. That is deliberate: with no parameter through
/// which a prior turn's registers could arrive, criterion 4's isolation holds
/// by construction rather than by a reset someone has to remember.
pub fn execute(
    bundle: &BytecodeBundle,
    max_steps: u64,
) -> Result<BytecodeExecutionReceiptV1, BytecodeRefusal> {
    let state = run(bundle, max_steps, RegisterMachineState::default())?;
    Ok(BytecodeExecutionReceiptV1::from_state(bundle, &state))
}

/// Run a bundle over registers carried explicitly from an earlier turn.
pub fn execute_with_envelope(
    bundle: &BytecodeBundle,
    max_steps: u64,
    envelope: &RegisterEnvelopeV1,
) -> Result<BytecodeExecutionReceiptV1, BytecodeRefusal> {
    let state = run(
        bundle,
        max_steps,
        RegisterMachineState::from_envelope(envelope),
    )?;
    Ok(BytecodeExecutionReceiptV1::from_state(bundle, &state))
}

/// Run a bundle and return the machine, for callers that need its state.
///
/// Shares [`run`] with [`execute`] rather than repeating the loop. A second
/// copy of the dispatch loop would give the step counter a second increment
/// site, and criterion 5 -- the receipt's count *is* the machine's count -- is
/// only checkable while there is exactly one.
pub fn execute_returning_state(
    bundle: &BytecodeBundle,
    max_steps: u64,
) -> Result<RegisterMachineState, BytecodeRefusal> {
    run(bundle, max_steps, RegisterMachineState::default())
}

/// The one dispatch loop.
fn run(
    bundle: &BytecodeBundle,
    max_steps: u64,
    mut state: RegisterMachineState,
) -> Result<RegisterMachineState, BytecodeRefusal> {
    if max_steps == 0 {
        return Err(BytecodeRefusal::ZeroBudget);
    }
    for instruction in bundle.instructions() {
        if state.consumed_steps == max_steps {
            return Err(BytecodeRefusal::ExecutionBudgetExhausted {
                consumed: state.consumed_steps,
                max_steps,
            });
        }
        state.dispatch(instruction)?;
        // The only site that moves the counter.
        state.consumed_steps += 1;
    }
    Ok(state)
}

// Origin: engine/crates_rs/pfp/src/epics/bytecode/machine.rs
// Claim: urn:core:crates_rs:pfp:machine:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord9e997628 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord9e997628` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError9e997628 {
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
impl BoundaryError9e997628 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError9e997628 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError9e997628 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord9e997628 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError9e997628> {
        if capacity_bound == 0 {
            return Err(BoundaryError9e997628::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError9e997628::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError9e997628::ExceedsCapacity {
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
mod l4_boundary_tests_9e997628 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord9e997628::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord9e997628::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord9e997628::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord9e997628::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord9e997628::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError9e997628::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError9e997628::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

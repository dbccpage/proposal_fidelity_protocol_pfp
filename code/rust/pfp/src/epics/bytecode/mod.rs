//! Symbolic bytecode register machine and its grammar compiler.
//!
//! `EPIC-OE-SYMGAM-002` asks for a closed opcode set, a bounded register
//! machine, a deterministic grammar compiler, and an execution receipt.
//! `SPEC-OE-SYMGAM-002` supplies the signatures this module is built to:
//!
//! ```text
//! LOAD_GLYPH(reg, glyph_id)                 loads a discrete glyph
//! APPLY_RELATION(dst, r1, r2, rel_id)       evaluates a binary relation
//! EMIT_OBSTRUCTION(reg_defect, defect_code) records a boundary defect (Phi_1 > 0)
//! ASSERT_BOUNDARY(reg_chain, boundary_map_id) asserts an exact boundary condition
//! STEP_FIBRATION(reg_fiber, base_step)      advances fiber lift state
//! ```
//!
//! together with a bounded register array of 64, a typed call stack of maximum
//! depth 32, and a step counter.
//!
//! # A criterion the instruction set cannot satisfy
//!
//! Acceptance criterion 2 reads: *"A non-terminating program returns
//! `BytecodeRefusal::ExecutionBudgetExhausted` having consumed `max_steps`."*
//!
//! **No opcode branches.** There is no jump, no call, no conditional. The spec
//! says the compiler "emits linear bytecode stream", and a linear stream over a
//! branch-free instruction set always halts after exactly `instructions.len()`
//! steps. A non-terminating program is not expressible.
//!
//! The budget is still real and still worth enforcing -- it bounds how long a
//! program may be relative to what the caller agreed to run -- so exhaustion is
//! implemented and tested with a program **longer than the budget**, which is
//! expressible. What is *not* claimed is that this machine detects infinite
//! loops, because it cannot host one. Either the criterion should say "a
//! program longer than the budget", or the instruction set needs a branch. That
//! is a decision for whoever owns the epic, and it is recorded rather than
//! quietly reinterpreted.
//!
//! # Isolation is structural, not conventional
//!
//! Criterion 4 requires that registers not survive a turn. Rather than
//! resetting state between runs, [`execute`] takes **no state parameter at
//! all**: it constructs a fresh [`RegisterMachineState`] internally, so there
//! is no argument through which a previous turn's registers could arrive.
//! Carrying state forward requires [`RegisterEnvelopeV1`] and a different
//! entry point, which names what it is doing.
//!
//! A rule enforced by removing the parameter that could break it cannot be
//! forgotten; a rule enforced by remembering to call `reset()` can.
//!
//! `AuthorityEffect: None`. A receipt records what the machine did. It does not
//! decide whether the program should have been run.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f5c8db5d;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f5c8db5d<T> = std::result::Result<T, BoundaryError_f5c8db5d>;

/// The spec's bounded register array.
pub const REGISTER_COUNT: usize = 64;

/// The spec's typed call stack depth.
pub const MAX_CALL_DEPTH: usize = 32;

/// The receipt schema this module emits.
pub const RECEIPT_SCHEMA_V1: &str = "core.symgam.bytecode-execution-receipt.v1";

mod compile;
mod machine;

pub use compile::*;
pub use machine::*;

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests;

// Exact invariant envelope.
// Origin: engine/crates_rs/pfp/src/epics/bytecode/mod.rs
// Claim: urn:core:symbol-game:bytecode:linear-halt:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LinearHaltWitness {
    program_len: u32,
    max_steps: u32,
    steps: u32,
    register: u16,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HaltBudgetError {
    ZeroBudget,
    ProgramExceedsBudget { program_len: u32, max_steps: u32 },
    RegisterOutOfRange { register: u16, register_count: usize },
}

// Origin: engine/crates_rs/pfp/src/epics/bytecode/mod.rs
// Claim: urn:core:crates_rs:pfp:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for HaltBudgetError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for HaltBudgetError {}

pub fn try_linear_halt(program_len: u32, max_steps: u32, register: u16) -> Result<LinearHaltWitness, HaltBudgetError> {
    if max_steps == 0 {
        return Err(HaltBudgetError::ZeroBudget);
    }
    if program_len > max_steps {
        return Err(HaltBudgetError::ProgramExceedsBudget { program_len, max_steps });
    }
    if usize::from(register) >= REGISTER_COUNT {
        return Err(HaltBudgetError::RegisterOutOfRange {
            register,
            register_count: REGISTER_COUNT,
        });
    }
    Ok(LinearHaltWitness {
        program_len,
        max_steps,
        steps: program_len,
        register,
    })
}

impl LinearHaltWitness {
    pub fn steps(&self) -> u32 {
        self.steps
    }

    pub fn program_len(&self) -> u32 {
        self.program_len
    }
}

#[cfg(test)]
mod linear_halt_tests {
    use super::*;

    #[test]
    fn a_short_branch_free_program_halts_in_its_own_length() {
        let witness = try_linear_halt(4, 8, 3);
        assert!(matches!(witness, Ok(ref row) if row.steps() == 4 && row.program_len() == 4));
    }

    #[test]
    fn refuses_a_zero_budget_and_a_register_past_the_file() {
        assert!(matches!(try_linear_halt(4, 0, 0), Err(HaltBudgetError::ZeroBudget)));
        assert!(matches!(
            try_linear_halt(4, 8, 64),
            Err(HaltBudgetError::RegisterOutOfRange { register: 64, register_count: 64 })
        ));
        assert!(matches!(
            try_linear_halt(9, 8, 0),
            Err(HaltBudgetError::ProgramExceedsBudget { program_len: 9, max_steps: 8 })
        ));
    }
}

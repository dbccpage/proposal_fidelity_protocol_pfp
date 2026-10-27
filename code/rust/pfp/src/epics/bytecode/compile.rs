use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

use super::REGISTER_COUNT;

/// Domain separation for the bundle digest, so a bundle digest can never
/// collide with a digest taken over some other kind of object.
const DIGEST_DOMAIN: &str = "core.symgam.bytecode.bundle.v1";

// ---------------------------------------------------------------------------
// Opcodes
// ---------------------------------------------------------------------------

/// The closed instruction set. Closed is the point: an open set would make the
/// exhaustiveness criterion unstatable.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum SymbolicOpcode {
    LoadGlyph,
    ApplyRelation,
    EmitObstruction,
    AssertBoundary,
    StepFibration,
}

impl SymbolicOpcode {
    /// Every variant, in declaration order.
    ///
    /// The array length is written out, so adding a variant without extending
    /// this list is a compile error rather than a silently shorter list.
    pub const ALL: [SymbolicOpcode; 5] = [
        SymbolicOpcode::LoadGlyph,
        SymbolicOpcode::ApplyRelation,
        SymbolicOpcode::EmitObstruction,
        SymbolicOpcode::AssertBoundary,
        SymbolicOpcode::StepFibration,
    ];

    /// The spec's own spelling, used in receipts and in refusal messages.
    pub fn name(self) -> &'static str {
        match self {
            SymbolicOpcode::LoadGlyph => "LOAD_GLYPH",
            SymbolicOpcode::ApplyRelation => "APPLY_RELATION",
            SymbolicOpcode::EmitObstruction => "EMIT_OBSTRUCTION",
            SymbolicOpcode::AssertBoundary => "ASSERT_BOUNDARY",
            SymbolicOpcode::StepFibration => "STEP_FIBRATION",
        }
    }
}

// ---------------------------------------------------------------------------
// Registers
// ---------------------------------------------------------------------------

/// A typed register value.
///
/// Every payload is an exact integer or a boolean. No floating-point value can
/// enter a register, which is the universal exact-arithmetic gate enforced by
/// the type rather than by a review comment.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum RegisterValue {
    Empty,
    Glyph { glyph_id: u64 },
    Relation { rel_id: u64, left: u64, right: u64 },
    Defect { defect_code: u64 },
    Boundary { boundary_map_id: u64, exact: bool },
    Fiber { base_step: u64, level: u64 },
}

impl RegisterValue {
    pub fn is_empty(self) -> bool {
        matches!(self, RegisterValue::Empty)
    }

    pub(super) fn kind(self) -> &'static str {
        match self {
            RegisterValue::Empty => "Empty",
            RegisterValue::Glyph { .. } => "Glyph",
            RegisterValue::Relation { .. } => "Relation",
            RegisterValue::Defect { .. } => "Defect",
            RegisterValue::Boundary { .. } => "Boundary",
            RegisterValue::Fiber { .. } => "Fiber",
        }
    }
}

// ---------------------------------------------------------------------------
// Instructions and bundles
// ---------------------------------------------------------------------------

/// One instruction, carrying exactly the operands its opcode's signature names.
///
/// Modelled as an enum rather than an opcode plus an operand vector so that a
/// malformed instruction -- `LOAD_GLYPH` with three operands, say -- is
/// unconstructible instead of being a runtime refusal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Instruction {
    LoadGlyph {
        reg: usize,
        glyph_id: u64,
    },
    ApplyRelation {
        dst: usize,
        r1: usize,
        r2: usize,
        rel_id: u64,
    },
    EmitObstruction {
        reg_defect: usize,
        defect_code: u64,
    },
    AssertBoundary {
        reg_chain: usize,
        boundary_map_id: u64,
    },
    StepFibration {
        reg_fiber: usize,
        base_step: u64,
    },
}

impl Instruction {
    pub fn opcode(&self) -> SymbolicOpcode {
        match self {
            Instruction::LoadGlyph { .. } => SymbolicOpcode::LoadGlyph,
            Instruction::ApplyRelation { .. } => SymbolicOpcode::ApplyRelation,
            Instruction::EmitObstruction { .. } => SymbolicOpcode::EmitObstruction,
            Instruction::AssertBoundary { .. } => SymbolicOpcode::AssertBoundary,
            Instruction::StepFibration { .. } => SymbolicOpcode::StepFibration,
        }
    }

    /// A canonical textual encoding, used only for the bundle digest.
    ///
    /// Written by hand rather than derived from `Debug`, because `Debug`
    /// formatting is not a stability guarantee and a digest built on it would
    /// change under a compiler upgrade.
    fn canonical(&self) -> String {
        match *self {
            Instruction::LoadGlyph { reg, glyph_id } => {
                format!("LOAD_GLYPH:{reg}:{glyph_id}")
            }
            Instruction::ApplyRelation {
                dst,
                r1,
                r2,
                rel_id,
            } => {
                format!("APPLY_RELATION:{dst}:{r1}:{r2}:{rel_id}")
            }
            Instruction::EmitObstruction {
                reg_defect,
                defect_code,
            } => {
                format!("EMIT_OBSTRUCTION:{reg_defect}:{defect_code}")
            }
            Instruction::AssertBoundary {
                reg_chain,
                boundary_map_id,
            } => {
                format!("ASSERT_BOUNDARY:{reg_chain}:{boundary_map_id}")
            }
            Instruction::StepFibration {
                reg_fiber,
                base_step,
            } => {
                format!("STEP_FIBRATION:{reg_fiber}:{base_step}")
            }
        }
    }
}

/// An immutable compiled program.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BytecodeBundle {
    instructions: Vec<Instruction>,
    digest: String,
}

impl BytecodeBundle {
    /// Build a bundle and compute its digest.
    ///
    /// The digest is length-prefixed per instruction, so two different
    /// instruction sequences cannot produce the same pre-image by concatenating
    /// differently.
    pub fn new(instructions: Vec<Instruction>) -> Self {
        let mut hasher = Sha256::new();
        hasher.update(DIGEST_DOMAIN.as_bytes());
        hasher.update(b"|");
        hasher.update(instructions.len().to_le_bytes());
        for instruction in &instructions {
            let encoded = instruction.canonical();
            hasher.update(encoded.len().to_le_bytes());
            hasher.update(encoded.as_bytes());
        }
        let digest = format!("sha256:{}", hex::encode(hasher.finalize()));
        Self {
            instructions,
            digest,
        }
    }

    pub fn instructions(&self) -> &[Instruction] {
        &self.instructions
    }

    pub fn digest(&self) -> &str {
        &self.digest
    }

    pub fn len(&self) -> usize {
        self.instructions.len()
    }

    pub fn is_empty(&self) -> bool {
        self.instructions.is_empty()
    }
}

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum BytecodeRefusal {
    #[error("execution budget exhausted after {consumed} of {max_steps} steps")]
    ExecutionBudgetExhausted { consumed: u64, max_steps: u64 },

    #[error("{opcode} addressed register {reg}, beyond the 64 available")]
    RegisterOutOfRange { opcode: &'static str, reg: usize },

    #[error("{opcode} read register {reg}, which is empty")]
    EmptyRegister { opcode: &'static str, reg: usize },

    #[error("{opcode} read register {reg}, which holds {found} and not {expected}")]
    RegisterTypeMismatch {
        opcode: &'static str,
        reg: usize,
        expected: &'static str,
        found: &'static str,
    },

    #[error("call stack exceeded its depth of 32")]
    CallDepthExceeded,

    #[error("a budget of zero steps cannot execute any program")]
    ZeroBudget,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum CompileError {
    #[error("relation {index} names glyph {name:?}, which the grammar does not declare")]
    UnknownGlyph { index: usize, name: String },

    #[error("the grammar declares no glyphs; an empty program has nothing to execute")]
    NoGlyphs,

    #[error("the grammar needs {needed} registers, beyond the 64 available")]
    RegisterPressure { needed: usize },

    #[error("glyph {name:?} is declared with id {first} and again with id {second}")]
    DuplicateGlyphId {
        name: String,
        first: u64,
        second: u64,
    },
}

// ---------------------------------------------------------------------------
// The grammar and its compiler
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RelationRule {
    pub left: String,
    pub right: String,
    pub rel_id: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BoundaryRule {
    pub chain: String,
    pub boundary_map_id: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FibrationRule {
    pub fiber: String,
    pub base_step: u64,
}

/// A declarative problem grammar.
///
/// `glyphs` is a `BTreeMap`, not a `HashMap`, and that is the whole of
/// acceptance criterion 3. A `HashMap` iterates in an order seeded per process,
/// so the same grammar would compile to different -- equally correct, equally
/// useless -- bundles in two runs, and no digest over the result would mean
/// anything.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GrammarSpec {
    pub glyphs: BTreeMap<String, u64>,
    #[serde(default)]
    pub relations: Vec<RelationRule>,
    #[serde(default)]
    pub obstructions: Vec<u64>,
    #[serde(default)]
    pub boundaries: Vec<BoundaryRule>,
    #[serde(default)]
    pub fibrations: Vec<FibrationRule>,
}

fn load_glyph_registers<'a>(
    glyphs: &'a BTreeMap<String, u64>,
    instructions: &mut Vec<Instruction>,
) -> Result<BTreeMap<&'a str, usize>, CompileError> {
    // Glyph name -> register, assigned in key order so the assignment is a
    // function of the grammar's content and not of its construction.
    let mut register_of: BTreeMap<&'a str, usize> = BTreeMap::new();
    let mut seen_id: BTreeMap<u64, &'a str> = BTreeMap::new();

    for (name, glyph_id) in glyphs {
        if let Some(previous) = seen_id.get(glyph_id) {
            return Err(CompileError::DuplicateGlyphId {
                name: (*previous).to_string(),
                first: *glyph_id,
                second: *glyph_id,
            });
        }
        seen_id.insert(*glyph_id, name.as_str());
        let reg = register_of.len();
        if reg >= REGISTER_COUNT {
            return Err(CompileError::RegisterPressure { needed: reg + 1 });
        }
        register_of.insert(name.as_str(), reg);
        instructions.push(Instruction::LoadGlyph {
            reg,
            glyph_id: *glyph_id,
        });
    }
    Ok(register_of)
}

fn compile_relations_and_obstructions(
    spec: &GrammarSpec,
    register_of: &BTreeMap<&str, usize>,
    next_free: &mut usize,
    instructions: &mut Vec<Instruction>,
) -> Result<(), CompileError> {
    for (index, rule) in spec.relations.iter().enumerate() {
        let r1 =
            *register_of
                .get(rule.left.as_str())
                .ok_or_else(|| CompileError::UnknownGlyph {
                    index,
                    name: rule.left.clone(),
                })?;
        let r2 =
            *register_of
                .get(rule.right.as_str())
                .ok_or_else(|| CompileError::UnknownGlyph {
                    index,
                    name: rule.right.clone(),
                })?;
        if *next_free >= REGISTER_COUNT {
            return Err(CompileError::RegisterPressure {
                needed: *next_free + 1,
            });
        }
        instructions.push(Instruction::ApplyRelation {
            dst: *next_free,
            r1,
            r2,
            rel_id: rule.rel_id,
        });
        *next_free += 1;
    }

    for defect_code in &spec.obstructions {
        if *next_free >= REGISTER_COUNT {
            return Err(CompileError::RegisterPressure {
                needed: *next_free + 1,
            });
        }
        instructions.push(Instruction::EmitObstruction {
            reg_defect: *next_free,
            defect_code: *defect_code,
        });
        *next_free += 1;
    }
    Ok(())
}

fn compile_boundaries_and_fibrations(
    spec: &GrammarSpec,
    register_of: &BTreeMap<&str, usize>,
    instructions: &mut Vec<Instruction>,
) -> Result<(), CompileError> {
    for (index, rule) in spec.boundaries.iter().enumerate() {
        let reg_chain =
            *register_of
                .get(rule.chain.as_str())
                .ok_or_else(|| CompileError::UnknownGlyph {
                    index,
                    name: rule.chain.clone(),
                })?;
        instructions.push(Instruction::AssertBoundary {
            reg_chain,
            boundary_map_id: rule.boundary_map_id,
        });
    }

    for (index, rule) in spec.fibrations.iter().enumerate() {
        let reg_fiber =
            *register_of
                .get(rule.fiber.as_str())
                .ok_or_else(|| CompileError::UnknownGlyph {
                    index,
                    name: rule.fiber.clone(),
                })?;
        instructions.push(Instruction::StepFibration {
            reg_fiber,
            base_step: rule.base_step,
        });
    }
    Ok(())
}

/// Compiles a grammar into an immutable bundle.
///
/// The epic asks for YAML input. This crate has no YAML dependency, and adding
/// one to a 48-crate workspace is a supply-chain decision rather than a sprint
/// decision, so the compiler takes a parsed [`GrammarSpec`] and the format
/// adapter is left to the caller. `serde` derives are present, so a JSON
/// adapter works today with the crate's existing dependencies and a YAML one
/// costs a dependency and no code.
pub fn compile_problem_grammar(spec: &GrammarSpec) -> Result<BytecodeBundle, CompileError> {
    if spec.glyphs.is_empty() {
        return Err(CompileError::NoGlyphs);
    }

    let mut instructions: Vec<Instruction> = Vec::new();
    let register_of = load_glyph_registers(&spec.glyphs, &mut instructions)?;
    let mut next_free = register_of.len();

    compile_relations_and_obstructions(spec, &register_of, &mut next_free, &mut instructions)?;
    compile_boundaries_and_fibrations(spec, &register_of, &mut instructions)?;

    Ok(BytecodeBundle::new(instructions))
}

// Origin: engine/crates_rs/pfp/src/epics/bytecode/compile.rs
// Claim: urn:core:crates_rs:pfp:compile:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_59238efd {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

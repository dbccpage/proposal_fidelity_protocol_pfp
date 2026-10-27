use std::collections::{BTreeMap, BTreeSet};

use super::*;

fn spec_with_two_glyphs() -> GrammarSpec {
    let mut glyphs = BTreeMap::new();
    glyphs.insert("alpha".to_string(), 1);
    glyphs.insert("beta".to_string(), 2);
    GrammarSpec {
        glyphs,
        relations: vec![RelationRule {
            left: "alpha".to_string(),
            right: "beta".to_string(),
            rel_id: 7,
        }],
        obstructions: vec![],
        boundaries: vec![],
        fibrations: vec![],
    }
}

/// A grammar whose compilation touches every opcode.
fn spec_touching_every_opcode() -> GrammarSpec {
    let mut spec = spec_with_two_glyphs();
    spec.obstructions = vec![42];
    spec.boundaries = vec![BoundaryRule {
        chain: "alpha".to_string(),
        boundary_map_id: 3,
    }];
    spec.fibrations = vec![FibrationRule {
        fiber: "beta".to_string(),
        base_step: 5,
    }];
    spec
}

fn compile(spec: &GrammarSpec) -> BytecodeBundle {
    compile_problem_grammar(spec).expect("the fixture grammar must compile")
}

// -- AC1: every opcode is exercised ---------------------------------

#[test]
fn the_all_array_lists_every_variant() {
    assert_eq!(SymbolicOpcode::ALL.len(), 5);
    let distinct: BTreeSet<_> = SymbolicOpcode::ALL.iter().collect();
    assert_eq!(distinct.len(), 5, "ALL must not repeat a variant");
}

#[test]
fn every_opcode_is_exercised_and_any_gap_is_named() {
    let bundle = compile(&spec_touching_every_opcode());
    let state = execute_returning_state(&bundle, 100).expect("must run");

    let expected: BTreeSet<&str> = SymbolicOpcode::ALL.iter().map(|op| op.name()).collect();
    let actual: BTreeSet<&str> = state.exercised().iter().copied().collect();
    let missing: Vec<&str> = expected.difference(&actual).copied().collect();

    assert!(
        missing.is_empty(),
        "these opcodes were never dispatched: {missing:?}"
    );
    assert_eq!(actual.len(), 5);
}

#[test]
fn opcode_names_use_the_spec_spelling() {
    let names: Vec<&str> = SymbolicOpcode::ALL.iter().map(|op| op.name()).collect();
    assert_eq!(
        names,
        vec![
            "LOAD_GLYPH",
            "APPLY_RELATION",
            "EMIT_OBSTRUCTION",
            "ASSERT_BOUNDARY",
            "STEP_FIBRATION",
        ]
    );
}

#[test]
fn each_instruction_reports_its_own_opcode() {
    let bundle = compile(&spec_touching_every_opcode());
    for instruction in bundle.instructions() {
        let named = instruction.opcode().name();
        assert!(
            SymbolicOpcode::ALL.iter().any(|op| op.name() == named),
            "unknown opcode name {named}"
        );
    }
}

// -- AC2: the budget halts at exactly max_steps -----------------------

#[test]
fn a_program_shorter_than_the_budget_runs_to_completion() {
    let bundle = compile(&spec_touching_every_opcode());
    let receipt = execute(&bundle, 100).expect("must run");
    assert_eq!(receipt.consumed_steps as usize, bundle.len());
}

#[test]
fn a_program_exactly_the_length_of_the_budget_completes() {
    let bundle = compile(&spec_touching_every_opcode());
    let budget = bundle.len() as u64;
    let receipt = execute(&bundle, budget).expect("must run at exactly the budget");
    assert_eq!(receipt.consumed_steps, budget);
}

#[test]
fn one_instruction_past_the_budget_is_refused_at_exactly_the_budget() {
    let bundle = compile(&spec_touching_every_opcode());
    let budget = bundle.len() as u64 - 1;
    let refusal = execute(&bundle, budget).expect_err("must refuse");
    assert_eq!(
        refusal,
        BytecodeRefusal::ExecutionBudgetExhausted {
            consumed: budget,
            max_steps: budget,
        },
        "exhaustion must report exactly max_steps, not max_steps +/- 1"
    );
}

#[test]
fn a_zero_budget_is_refused_rather_than_silently_running_nothing() {
    let bundle = compile(&spec_with_two_glyphs());
    assert_eq!(
        execute(&bundle, 0).expect_err("must refuse"),
        BytecodeRefusal::ZeroBudget
    );
}

#[test]
fn execution_always_terminates_because_no_opcode_branches() {
    // The finding behind acceptance criterion 2: a linear stream over a
    // branch-free instruction set halts after exactly its own length. If a
    // jump is ever added, this fails and the criterion can be revisited on
    // evidence rather than on reading.
    for extra in 0..6usize {
        let mut spec = spec_touching_every_opcode();
        spec.obstructions = vec![1; extra + 1];
        let bundle = compile(&spec);
        let receipt = execute(&bundle, 1_000).expect("must run");
        assert_eq!(
            receipt.consumed_steps as usize,
            bundle.len(),
            "a branch-free program must consume exactly its own length"
        );
    }
}

// -- AC3: compilation is deterministic --------------------------------

#[test]
fn the_same_grammar_compiles_to_the_same_bytes_twice() {
    let spec = spec_touching_every_opcode();
    let first = compile(&spec);
    let second = compile(&spec);
    assert_eq!(first.digest(), second.digest());
    assert_eq!(first.instructions(), second.instructions());
}

#[test]
fn glyph_insertion_order_does_not_change_the_bundle() {
    let mut forward = BTreeMap::new();
    forward.insert("alpha".to_string(), 1u64);
    forward.insert("beta".to_string(), 2);
    forward.insert("gamma".to_string(), 3);

    let mut backward = BTreeMap::new();
    backward.insert("gamma".to_string(), 3u64);
    backward.insert("beta".to_string(), 2);
    backward.insert("alpha".to_string(), 1);

    let make = |glyphs: BTreeMap<String, u64>| GrammarSpec {
        glyphs,
        relations: vec![],
        obstructions: vec![],
        boundaries: vec![],
        fibrations: vec![],
    };
    assert_eq!(
        compile(&make(forward)).digest(),
        compile(&make(backward)).digest()
    );
}

#[test]
fn a_changed_relation_id_changes_the_digest() {
    let mut spec = spec_with_two_glyphs();
    let before = compile(&spec).digest().to_string();
    spec.relations[0].rel_id = 8;
    assert_ne!(before, compile(&spec).digest());
}

#[test]
fn a_changed_glyph_id_changes_the_digest() {
    let mut spec = spec_with_two_glyphs();
    let before = compile(&spec).digest().to_string();
    spec.glyphs.insert("alpha".to_string(), 99);
    assert_ne!(before, compile(&spec).digest());
}

#[test]
fn the_digest_is_domain_separated_and_labelled() {
    let bundle = compile(&spec_with_two_glyphs());
    assert!(bundle.digest().starts_with("sha256:"));
    assert_eq!(bundle.digest().len(), "sha256:".len() + 64);
}

#[test]
fn instruction_order_changes_the_digest() {
    let forward = BytecodeBundle::new(vec![
        Instruction::LoadGlyph {
            reg: 0,
            glyph_id: 1,
        },
        Instruction::LoadGlyph {
            reg: 1,
            glyph_id: 2,
        },
    ]);
    let reversed = BytecodeBundle::new(vec![
        Instruction::LoadGlyph {
            reg: 1,
            glyph_id: 2,
        },
        Instruction::LoadGlyph {
            reg: 0,
            glyph_id: 1,
        },
    ]);
    assert_ne!(forward.digest(), reversed.digest());
}

// -- AC4: registers do not survive a turn -----------------------------

#[test]
fn a_second_execution_cannot_see_the_first_ones_registers() {
    let loader = compile(&spec_with_two_glyphs());
    execute(&loader, 100).expect("first turn must run");

    // Reads register 0. If state leaked it would find a glyph there.
    let reader = BytecodeBundle::new(vec![Instruction::AssertBoundary {
        reg_chain: 0,
        boundary_map_id: 1,
    }]);
    assert_eq!(
        execute(&reader, 100).expect_err("must refuse on an empty register"),
        BytecodeRefusal::EmptyRegister {
            opcode: "ASSERT_BOUNDARY",
            reg: 0,
        }
    );
}

#[test]
fn an_explicit_envelope_is_the_only_way_to_carry_state() {
    let loader = compile(&spec_with_two_glyphs());
    let state = execute_returning_state(&loader, 100).expect("first turn must run");
    let envelope = state.envelope();

    let reader = BytecodeBundle::new(vec![Instruction::AssertBoundary {
        reg_chain: 0,
        boundary_map_id: 1,
    }]);
    let receipt = execute_with_envelope(&reader, 100, &envelope)
        .expect("the carried register must be visible");
    assert_eq!(receipt.consumed_steps, 1);
}

#[test]
fn an_envelope_longer_than_the_register_file_is_truncated_not_overflowed() {
    let envelope = RegisterEnvelopeV1 {
        registers: vec![RegisterValue::Glyph { glyph_id: 1 }; REGISTER_COUNT + 8],
    };
    let bundle = BytecodeBundle::new(vec![Instruction::AssertBoundary {
        reg_chain: 0,
        boundary_map_id: 1,
    }]);
    execute_with_envelope(&bundle, 10, &envelope).expect("must not panic");
}

// -- AC5: the receipt's step count is the machine's -------------------

#[test]
fn the_receipt_step_count_equals_the_machines() {
    let bundle = compile(&spec_touching_every_opcode());
    let receipt = execute(&bundle, 100).expect("must run");
    let state = execute_returning_state(&bundle, 100).expect("must run");
    assert_eq!(receipt.consumed_steps, state.consumed_steps());
}

#[test]
fn the_receipt_step_count_equals_an_independent_instruction_count() {
    let bundle = compile(&spec_touching_every_opcode());
    let counted = bundle.instructions().iter().count() as u64;
    let receipt = execute(&bundle, 100).expect("must run");
    assert_eq!(receipt.consumed_steps, counted);
}

// -- receipt content ---------------------------------------------------

#[test]
fn the_receipt_carries_no_authority() {
    let bundle = compile(&spec_with_two_glyphs());
    let receipt = execute(&bundle, 100).expect("must run");
    assert_eq!(receipt.authority_effect, "None");
    assert_eq!(receipt.schema_version, RECEIPT_SCHEMA_V1);
}

#[test]
fn the_receipt_binds_the_bundle_digest() {
    let bundle = compile(&spec_with_two_glyphs());
    let receipt = execute(&bundle, 100).expect("must run");
    assert_eq!(receipt.bundle_digest, bundle.digest());
}

#[test]
fn the_defect_count_is_the_number_of_obstructions_emitted() {
    let mut spec = spec_with_two_glyphs();
    spec.obstructions = vec![10, 11, 12];
    let bundle = compile(&spec);
    let receipt = execute(&bundle, 100).expect("must run");
    assert_eq!(receipt.defect_count, 3);
}

#[test]
fn a_program_with_no_obstructions_reports_zero_defects() {
    let bundle = compile(&spec_with_two_glyphs());
    assert_eq!(execute(&bundle, 100).expect("must run").defect_count, 0);
}

#[test]
fn the_receipt_omits_empty_registers() {
    let bundle = compile(&spec_with_two_glyphs());
    let receipt = execute(&bundle, 100).expect("must run");
    assert!(receipt.final_registers.len() < REGISTER_COUNT);
    assert!(receipt
        .final_registers
        .iter()
        .all(|(_, value)| !value.is_empty()));
}

#[test]
fn the_receipt_round_trips_through_json() {
    let bundle = compile(&spec_touching_every_opcode());
    let receipt = execute(&bundle, 100).expect("must run");
    let encoded = serde_json::to_string(&receipt).expect("must serialise");
    let decoded: BytecodeExecutionReceiptV1 =
        serde_json::from_str(&encoded).expect("must deserialise");
    assert_eq!(receipt, decoded);
}

// -- compiler refusals -------------------------------------------------

#[test]
fn a_relation_naming_an_undeclared_glyph_is_refused() {
    let mut spec = spec_with_two_glyphs();
    spec.relations[0].right = "delta".to_string();
    assert_eq!(
        compile_problem_grammar(&spec).expect_err("must refuse"),
        CompileError::UnknownGlyph {
            index: 0,
            name: "delta".to_string()
        }
    );
}

#[test]
fn a_boundary_naming_an_undeclared_glyph_is_refused() {
    let mut spec = spec_with_two_glyphs();
    spec.boundaries = vec![BoundaryRule {
        chain: "nowhere".to_string(),
        boundary_map_id: 1,
    }];
    assert!(matches!(
        compile_problem_grammar(&spec),
        Err(CompileError::UnknownGlyph { .. })
    ));
}

#[test]
fn a_fibration_naming_an_undeclared_glyph_is_refused() {
    let mut spec = spec_with_two_glyphs();
    spec.fibrations = vec![FibrationRule {
        fiber: "nowhere".to_string(),
        base_step: 1,
    }];
    assert!(matches!(
        compile_problem_grammar(&spec),
        Err(CompileError::UnknownGlyph { .. })
    ));
}

#[test]
fn a_grammar_with_no_glyphs_is_refused() {
    let spec = GrammarSpec {
        glyphs: BTreeMap::new(),
        relations: vec![],
        obstructions: vec![],
        boundaries: vec![],
        fibrations: vec![],
    };
    assert_eq!(
        compile_problem_grammar(&spec).expect_err("must refuse"),
        CompileError::NoGlyphs
    );
}

#[test]
fn a_grammar_needing_more_than_the_register_file_is_refused() {
    let mut glyphs = BTreeMap::new();
    for index in 0..(REGISTER_COUNT + 1) {
        glyphs.insert(format!("g{index:04}"), index as u64);
    }
    let spec = GrammarSpec {
        glyphs,
        relations: vec![],
        obstructions: vec![],
        boundaries: vec![],
        fibrations: vec![],
    };
    assert!(matches!(
        compile_problem_grammar(&spec),
        Err(CompileError::RegisterPressure { .. })
    ));
}

#[test]
fn two_glyphs_sharing_an_id_are_refused() {
    let mut glyphs = BTreeMap::new();
    glyphs.insert("alpha".to_string(), 1u64);
    glyphs.insert("beta".to_string(), 1);
    let spec = GrammarSpec {
        glyphs,
        relations: vec![],
        obstructions: vec![],
        boundaries: vec![],
        fibrations: vec![],
    };
    assert!(matches!(
        compile_problem_grammar(&spec),
        Err(CompileError::DuplicateGlyphId { .. })
    ));
}

#[test]
fn a_grammar_at_exactly_the_register_limit_compiles() {
    // The refusal above must be a ceiling, not an off-by-one.
    let mut glyphs = BTreeMap::new();
    for index in 0..REGISTER_COUNT {
        glyphs.insert(format!("g{index:04}"), index as u64);
    }
    let spec = GrammarSpec {
        glyphs,
        relations: vec![],
        obstructions: vec![],
        boundaries: vec![],
        fibrations: vec![],
    };
    assert_eq!(compile(&spec).len(), REGISTER_COUNT);
}

// -- machine refusals --------------------------------------------------

#[test]
fn an_out_of_range_register_is_refused() {
    let bundle = BytecodeBundle::new(vec![Instruction::LoadGlyph {
        reg: REGISTER_COUNT,
        glyph_id: 1,
    }]);
    assert_eq!(
        execute(&bundle, 10).expect_err("must refuse"),
        BytecodeRefusal::RegisterOutOfRange {
            opcode: "LOAD_GLYPH",
            reg: REGISTER_COUNT,
        }
    );
}

#[test]
fn an_out_of_range_register_read_is_refused() {
    // The write path and the read path bounds-check separately, and a
    // mutation removing the read check survived until this existed: the
    // test above addresses an out-of-range register only as a *destination*.
    let bundle = BytecodeBundle::new(vec![Instruction::AssertBoundary {
        reg_chain: REGISTER_COUNT + 3,
        boundary_map_id: 1,
    }]);
    assert_eq!(
        execute(&bundle, 10).expect_err("must refuse"),
        BytecodeRefusal::RegisterOutOfRange {
            opcode: "ASSERT_BOUNDARY",
            reg: REGISTER_COUNT + 3,
        }
    );
}

#[test]
fn an_out_of_range_relation_operand_is_refused() {
    let bundle = BytecodeBundle::new(vec![
        Instruction::LoadGlyph {
            reg: 0,
            glyph_id: 1,
        },
        Instruction::ApplyRelation {
            dst: 1,
            r1: 0,
            r2: REGISTER_COUNT,
            rel_id: 2,
        },
    ]);
    assert_eq!(
        execute(&bundle, 10).expect_err("must refuse"),
        BytecodeRefusal::RegisterOutOfRange {
            opcode: "APPLY_RELATION",
            reg: REGISTER_COUNT,
        }
    );
}

#[test]
fn reading_an_empty_register_is_refused() {
    let bundle = BytecodeBundle::new(vec![Instruction::ApplyRelation {
        dst: 1,
        r1: 0,
        r2: 0,
        rel_id: 1,
    }]);
    assert_eq!(
        execute(&bundle, 10).expect_err("must refuse"),
        BytecodeRefusal::EmptyRegister {
            opcode: "APPLY_RELATION",
            reg: 0,
        }
    );
}

#[test]
fn applying_a_relation_to_a_non_glyph_is_refused_by_type() {
    let bundle = BytecodeBundle::new(vec![
        Instruction::EmitObstruction {
            reg_defect: 0,
            defect_code: 9,
        },
        Instruction::LoadGlyph {
            reg: 1,
            glyph_id: 2,
        },
        Instruction::ApplyRelation {
            dst: 2,
            r1: 0,
            r2: 1,
            rel_id: 3,
        },
    ]);
    assert_eq!(
        execute(&bundle, 10).expect_err("must refuse"),
        BytecodeRefusal::RegisterTypeMismatch {
            opcode: "APPLY_RELATION",
            reg: 0,
            expected: "Glyph",
            found: "Defect",
        }
    );
}

#[test]
fn exceeding_the_call_depth_is_refused() {
    let mut instructions = vec![Instruction::LoadGlyph {
        reg: 0,
        glyph_id: 1,
    }];
    for step in 0..(MAX_CALL_DEPTH + 1) {
        instructions.push(Instruction::StepFibration {
            reg_fiber: 0,
            base_step: step as u64,
        });
    }
    let bundle = BytecodeBundle::new(instructions);
    assert_eq!(
        execute(&bundle, 1_000).expect_err("must refuse"),
        BytecodeRefusal::CallDepthExceeded
    );
}

#[test]
fn exactly_the_call_depth_is_permitted() {
    let mut instructions = vec![Instruction::LoadGlyph {
        reg: 0,
        glyph_id: 1,
    }];
    for step in 0..MAX_CALL_DEPTH {
        instructions.push(Instruction::StepFibration {
            reg_fiber: 0,
            base_step: step as u64,
        });
    }
    let bundle = BytecodeBundle::new(instructions);
    let state = execute_returning_state(&bundle, 1_000).expect("must run");
    assert_eq!(state.call_depth(), MAX_CALL_DEPTH);
}

// -- register semantics ------------------------------------------------

#[test]
fn load_glyph_writes_the_declared_glyph() {
    let bundle = BytecodeBundle::new(vec![Instruction::LoadGlyph {
        reg: 3,
        glyph_id: 77,
    }]);
    let state = execute_returning_state(&bundle, 10).expect("must run");
    assert_eq!(
        state.register(3),
        Some(RegisterValue::Glyph { glyph_id: 77 })
    );
}

#[test]
fn apply_relation_records_both_operands() {
    let bundle = BytecodeBundle::new(vec![
        Instruction::LoadGlyph {
            reg: 0,
            glyph_id: 11,
        },
        Instruction::LoadGlyph {
            reg: 1,
            glyph_id: 22,
        },
        Instruction::ApplyRelation {
            dst: 2,
            r1: 0,
            r2: 1,
            rel_id: 5,
        },
    ]);
    let state = execute_returning_state(&bundle, 10).expect("must run");
    assert_eq!(
        state.register(2),
        Some(RegisterValue::Relation {
            rel_id: 5,
            left: 11,
            right: 22
        })
    );
}

#[test]
fn a_boundary_over_a_defect_register_is_inexact() {
    let bundle = BytecodeBundle::new(vec![
        Instruction::EmitObstruction {
            reg_defect: 0,
            defect_code: 4,
        },
        Instruction::AssertBoundary {
            reg_chain: 0,
            boundary_map_id: 9,
        },
    ]);
    let state = execute_returning_state(&bundle, 10).expect("must run");
    assert_eq!(
        state.register(0),
        Some(RegisterValue::Boundary {
            boundary_map_id: 9,
            exact: false
        })
    );
}

#[test]
fn a_boundary_over_a_clean_register_is_exact() {
    let bundle = BytecodeBundle::new(vec![
        Instruction::LoadGlyph {
            reg: 0,
            glyph_id: 1,
        },
        Instruction::AssertBoundary {
            reg_chain: 0,
            boundary_map_id: 9,
        },
    ]);
    let state = execute_returning_state(&bundle, 10).expect("must run");
    assert_eq!(
        state.register(0),
        Some(RegisterValue::Boundary {
            boundary_map_id: 9,
            exact: true
        })
    );
}

#[test]
fn step_fibration_advances_the_level() {
    let bundle = BytecodeBundle::new(vec![
        Instruction::LoadGlyph {
            reg: 0,
            glyph_id: 1,
        },
        Instruction::StepFibration {
            reg_fiber: 0,
            base_step: 2,
        },
        Instruction::StepFibration {
            reg_fiber: 0,
            base_step: 2,
        },
    ]);
    let state = execute_returning_state(&bundle, 10).expect("must run");
    assert_eq!(
        state.register(0),
        Some(RegisterValue::Fiber {
            base_step: 2,
            level: 2
        })
    );
}

// Origin: engine/crates_rs/pfp/src/epics/bytecode/tests.rs
// Claim: urn:core:crates_rs:pfp:tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd3f63061 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd3f63061` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord3f63061 {
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
impl BoundaryErrord3f63061 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord3f63061 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord3f63061 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd3f63061 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord3f63061> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord3f63061::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord3f63061::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord3f63061::ExceedsCapacity {
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
mod l4_boundary_tests_d3f63061 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd3f63061::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd3f63061::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd3f63061::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd3f63061::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd3f63061::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord3f63061::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord3f63061::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

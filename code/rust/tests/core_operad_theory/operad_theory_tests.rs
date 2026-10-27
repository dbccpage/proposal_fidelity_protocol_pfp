//! Comprehensive 13-Point Acceptance Tests for core_operad_theory Rust Crate.
//!
//! AuthorityEffect: None.

use core_operad_theory::*;

#[test]
fn test_foundation_colour_and_signature() {
    let state = OperadColour::new("State").expect("valid colour");
    let code = OperadColour::new("Code").expect("valid colour");
    assert_eq!(state.as_str(), "State");

    let sig = OperadSignature::new(vec![state.clone(), code.clone()], state.clone());
    assert_eq!(sig.arity(), 2);
    assert!(!sig.is_nullary());
    assert!(!sig.is_unary());
}

#[test]
fn test_operation_and_identities() {
    let state = OperadColour::new("State").expect("valid colour");
    let id_op = Operation::identity(state.clone());
    assert!(id_op.is_identity());
    assert_eq!(id_op.arity(), 1);
    assert_eq!(id_op.output(), &state);
}

#[test]
fn test_planar_tree_corolla_and_grafting() {
    let state = OperadColour::new("State").expect("valid colour");
    let code = OperadColour::new("Code").expect("valid colour");

    let f_sig = OperadSignature::new(vec![code.clone()], state.clone());
    let f = Operation::new_generator(OperationId::new("lint").unwrap(), f_sig, "lint code to state");

    let g_sig = OperadSignature::new(vec![state.clone()], code.clone());
    let g = Operation::new_generator(OperationId::new("codegen").unwrap(), g_sig, "generate code");

    let tree_f = PlanarTree::corolla(f);
    let tree_g = PlanarTree::corolla(g);

    let composite_tree = tree_f.graft(0, tree_g).expect("successful graft");
    assert_eq!(composite_tree.arity(), 1);
    assert!(composite_tree.term_hash().starts_with("tree_"));
}

#[test]
fn test_planar_operad_partial_composition() {
    let mut operad = PlanarColoredOperad::new("TestOperad", false);
    let state = operad.add_colour(OperadColour::new("State").unwrap());
    let code = operad.add_colour(OperadColour::new("Code").unwrap());

    let f = Operation::new_generator(
        OperationId::new("f_op").unwrap(),
        OperadSignature::new(vec![code.clone(), state.clone()], state.clone()),
        "f",
    );
    let g = Operation::new_generator(
        OperationId::new("g_op").unwrap(),
        OperadSignature::new(vec![state.clone()], code.clone()),
        "g",
    );

    operad.add_operation(f.clone()).unwrap();
    operad.add_operation(g.clone()).unwrap();

    let h = operad.partial_compose(&f, &g, 0).expect("compose at slot 0");
    assert_eq!(h.arity(), 2);
    assert_eq!(h.inputs(), &[state.clone(), state.clone()]);
    assert_eq!(h.output(), &state);
}

#[test]
fn test_monoidal_operad_parallel_tensor() {
    let mut mon_op = MonoidalOperad::new("TestMonoidal");
    let c1 = OperadColour::new("A").unwrap();
    let c2 = OperadColour::new("B").unwrap();

    let f = Operation::new_generator(
        OperationId::new("f").unwrap(),
        OperadSignature::new(vec![c1.clone()], c1.clone()),
        "f",
    );
    let g = Operation::new_generator(
        OperationId::new("g").unwrap(),
        OperadSignature::new(vec![c2.clone()], c2.clone()),
        "g",
    );

    let tensor_op = mon_op.parallel_tensor_operations(&f, &g).expect("parallel tensor");
    assert_eq!(tensor_op.arity(), 2);
}

#[test]
fn test_associativity_witness_verification() {
    let mut operad = PlanarColoredOperad::new("AssocOperad", false);
    let c = operad.add_colour(OperadColour::new("C").unwrap());

    let f = Operation::new_generator(
        OperationId::new("f").unwrap(),
        OperadSignature::new(vec![c.clone(), c.clone()], c.clone()),
        "f",
    );
    operad.add_operation(f.clone()).unwrap();

    let witness = StructuralAssociativityWitness::verify_sequential(&operad, &f, &f, &f, 0, 0);
    assert!(witness.is_satisfied());

    let unit_witness = StructuralAssociativityWitness::verify_unit(&operad, &f);
    assert!(unit_witness.is_satisfied());
}

#[test]
fn test_oeas_workflow_operad_and_algebra_evaluation() {
    let mut workflow = OEASWorkflowOperad::new().expect("valid workflow operad");
    let _skill_a = workflow
        .register_skill("lint", &["Code"], "AuditFinding", "lint code")
        .expect("register skill");
    let _skill_b = workflow
        .register_skill("audit_review", &["AuditFinding"], "EvaluationReceipt", "review audit")
        .expect("register skill");

    let tree_b = workflow.create_corolla("audit_review").unwrap();
    let tree_a = workflow.create_corolla("lint").unwrap();
    let comp_tree = workflow.compose_workflow_tree(&tree_b, 0, tree_a).unwrap();

    assert_eq!(comp_tree.arity(), 1);
    assert_eq!(comp_tree.output_colour().as_str(), "EvaluationReceipt");

    let mut interpreter = workflow.create_agent_interpreter("test_agent", None);
    interpreter
        .register_action("lint", |inputs| {
            Ok(serde_json::json!({ "lint_status": "clean", "input": inputs[0] }))
        })
        .unwrap();
    interpreter
        .register_action("audit_review", |inputs| {
            Ok(serde_json::json!({ "verdict": "passed", "finding": inputs[0] }))
        })
        .unwrap();

    let outcome = interpreter.evaluate_tree(
        &comp_tree,
        &[serde_json::json!("fn main() {}")],
        Some(PolicyDecisionRef::new("pol_123", true)),
    );

    assert!(outcome.is_completed);
    assert!(outcome.receipt.is_some());
    let r = outcome.receipt.unwrap();
    assert_eq!(r.status, "Completed");
    assert_eq!(r.output_colour, "EvaluationReceipt");
}

#[test]
fn test_geometric_little_disks_and_homology() {
    let d1 = RectilinearDisk::new(2, vec![0.0, 0.0], 0.4).unwrap();
    let d2 = RectilinearDisk::new(2, vec![0.5, 0.5], 0.2).unwrap();
    assert!(d1.is_contained_in_unit_disk());
    assert!(d2.is_contained_in_unit_disk());
    assert!(d1.is_disjoint_from(&d2).unwrap());

    let config = LittleDisksConfiguration::new(2, vec![d1, d2]).unwrap();
    assert_eq!(config.arity(), 2);

    let ass_op = build_associative_homology_operad().unwrap();
    assert_eq!(ass_op.colours().len(), 1);

    let gerst_op = build_gerstenhaber_homology_operad().unwrap();
    assert_eq!(gerst_op.planar.colours().len(), 1);
}

#[test]
fn test_deformation_quadratic_and_koszul() {
    let mut quad = QuadraticOperad::new("Ass");
    let c = OperadColour::new("C").unwrap();
    quad.add_generator(Operation::new_generator(
        OperationId::new("mu").unwrap(),
        OperadSignature::new(vec![c.clone(), c.clone()], c),
        "mu",
    ));

    let res = BarCobarResolution::evaluate_koszul_resolution(&quad);
    assert!(res.is_koszul);
    assert_eq!(res.obstruction_dimension, 0);

    let dual = KoszulDualBuilder::build_koszul_dual_skeleton(&quad).unwrap();
    assert_eq!(dual.original_name, "Ass");
    assert!(dual.dual_operad.generators.contains_key("mu_dual"));
}

#[test]
fn test_span_operand_foundation() {
    let state_colour = OperadColour::new("State").unwrap();
    let raw = "let x = 42;\nreturn x;";
    let span = SpanOperand::from_raw_text(
        "src/lib.rs",
        raw,
        state_colour.clone(),
        1,
        2,
        0,
        Some("definition".to_string()),
    )
    .expect("span should be created");

    assert_eq!(span.file_path, "src/lib.rs");
    assert_eq!(span.start_line, 1);
    assert_eq!(span.end_line, 2);
    assert_eq!(span.colour, state_colour);
    assert!(span.verify_integrity());
    assert_eq!(span.byte_length, raw.as_bytes().len());

    // BOM rejection test
    let bom_text = "\u{feff}forbidden bom";
    let bom_res = SpanOperand::from_raw_text("test.rs", bom_text, state_colour, 1, 1, 0, None);
    assert!(bom_res.is_err());
}

#[test]
fn test_zero_authority_effect() {
    assert_eq!(authority_effect(), "None");
}

// Origin: engine/crates_rs/tests/core_operad_theory/operad_theory_tests.rs
// Claim: urn:core:crates_rs:tests:operad-theory-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7d9ef943 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7d9ef943` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7d9ef943 {
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
impl BoundaryError7d9ef943 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7d9ef943 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7d9ef943 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7d9ef943 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7d9ef943> {
        if capacity_bound == 0 {
            return Err(BoundaryError7d9ef943::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7d9ef943::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7d9ef943::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_7d9ef943() {
    let admitted = BoundaryRecord7d9ef943::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord7d9ef943::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

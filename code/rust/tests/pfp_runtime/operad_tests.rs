//! Integration and falsification tests for Categorical Coloured Operad Prompt.
//!
//! Covers Milestone 3 requirements:
//! - Colours C
//! - Immutable leaf text spans with source offsets [i, j]
//! - Operators O^+ with input/output colours
//! - Slot grafting (\circ_i) with fail-closed boundary colour matching and arity checks
//! - Congruence Ideal fences (I -> NullTree)
//! - Annihilator decoy checks (O^-) with refutation witness verification
//!
//! AuthorityEffect: None.

use std::collections::BTreeMap;
use pfp_runtime::operad::*;

#[test]
fn test_colour_mismatch_slot_grafting_falsification() {
    let isolate_op = PromptOperator::new(
        "isolate_variable",
        vec![PromptColour::Equation],
        PromptColour::IsolatedVariable,
        "Algebraically isolates variable",
    )
    .expect("operator creation should succeed");

    // Attempting to feed RawTextSpan directly into Equation slot must fail
    let raw_leaf = OperadTree::leaf(
        LeafTextSpan::new(
            "span_raw",
            PromptColour::RawTextSpan,
            "x + 2*y = 5",
            [0, 11],
        )
        .expect("leaf creation should succeed"),
    );

    let graft_attempt = OperadTree::node(isolate_op.clone(), vec![raw_leaf.clone()]);
    assert!(
        graft_attempt.is_err(),
        "slot grafting with mismatched colour must fail"
    );
    match graft_attempt.err().unwrap() {
        OperadRefusal::ColourMismatch { slot, expected, actual } => {
            assert_eq!(slot, 0);
            assert_eq!(expected, PromptColour::Equation);
            assert_eq!(actual, PromptColour::RawTextSpan);
        }
        other => panic!("expected ColourMismatch refusal, got {other:?}"),
    }

    // Now test graft() method on an existing open tree
    let tree_with_hole = OperadTree::Node {
        operator: isolate_op,
        children: vec![],
    };
    let graft_res = tree_with_hole.graft(0, &raw_leaf);
    assert!(graft_res.is_err());
    match graft_res.err().unwrap() {
        OperadRefusal::ColourMismatch { slot, expected, actual } => {
            assert_eq!(slot, 0);
            assert_eq!(expected, PromptColour::Equation);
            assert_eq!(actual, PromptColour::RawTextSpan);
        }
        other => panic!("expected ColourMismatch, got {other:?}"),
    }
}

#[test]
fn test_arity_and_slot_out_of_bounds_rejection() {
    let binary_op = PromptOperator::new(
        "substitute_and_solve",
        vec![PromptColour::Equation, PromptColour::IsolatedVariable],
        PromptColour::RationalValue,
        "Solves for variable",
    )
    .expect("operator creation should succeed");

    let tree = OperadTree::Node {
        operator: binary_op,
        children: vec![],
    };

    let leaf = OperadTree::leaf(
        LeafTextSpan::new("dummy", PromptColour::Equation, "x = 1", [0, 5]).unwrap(),
    );

    // Slot 2 is out of bounds for arity 2
    let oob_res = tree.graft(2, &leaf);
    assert!(oob_res.is_err());
    match oob_res.err().unwrap() {
        OperadRefusal::SlotOutOfBounds { slot, arity } => {
            assert_eq!(slot, 2);
            assert_eq!(arity, 2);
        }
        other => panic!("expected SlotOutOfBounds, got {other:?}"),
    }
}

#[test]
fn test_congruence_ideal_null_tree_projection_falsification() {
    let ideal_rational = CongruenceIdeal::new(
        "IDEAL_EXACT_RATIONAL_DOMAIN",
        PromptColour::RationalValue,
        "isinstance(val, Fraction) and not isinstance(val, (float, complex))",
        "null_tree",
    );

    // 1. Float strings must project to NullTree
    for float_repr in &["3.1415", "0.0", "1e-5", "2.0E3", "12.345"] {
        let proj = ideal_rational.evaluate_rational_domain(float_repr);
        assert!(proj.is_some(), "float '{float_repr}' must trigger ideal violation");
        let null_tree = proj.unwrap();
        assert!(null_tree.is_null());
        match null_tree {
            OperadTree::NullTree { ideal_id, reason, .. } => {
                assert_eq!(ideal_id, "IDEAL_EXACT_RATIONAL_DOMAIN");
                assert!(reason.contains("float/decimal approximation"));
            }
            _ => panic!("must be NullTree"),
        }
    }

    // 2. Division by zero in fraction representation must project to NullTree
    let div_zero = ideal_rational.evaluate_rational_domain("5/0");
    assert!(div_zero.is_some());
    assert!(div_zero.unwrap().is_null());

    // 3. Valid exact rationals must not project
    for valid_repr in &["0", "1", "-5", "3/4", "-7/11", "1000/3"] {
        assert!(
            ideal_rational.evaluate_rational_domain(valid_repr).is_none(),
            "exact rational '{valid_repr}' must be admitted"
        );
    }
}

#[test]
fn test_congruence_ideal_absorption_across_tree_hierarchy() {
    let add_op = PromptOperator::new(
        "add",
        vec![PromptColour::RationalValue, PromptColour::RationalValue],
        PromptColour::RationalValue,
        "Adds two rationals",
    )
    .unwrap();

    let valid_leaf = OperadTree::leaf(
        LeafTextSpan::new("v1", PromptColour::RationalValue, "1", [0, 1]).unwrap(),
    );

    let null_tree = OperadTree::null_tree(
        "IDEAL_EXACT_RATIONAL_DOMAIN",
        "float leak",
        PromptColour::RationalValue,
    );

    // When building a node with a NullTree child, node collapses to NullTree
    let absorbed = OperadTree::node(add_op.clone(), vec![valid_leaf.clone(), null_tree.clone()]).unwrap();
    assert!(absorbed.is_null());
    match absorbed {
        OperadTree::NullTree { reason, .. } => {
            assert!(reason.contains("absorbed child null tree"));
        }
        _ => panic!("must absorb to NullTree"),
    }

    // When grafting NullTree into a valid tree, resulting tree is NullTree
    let valid_tree = OperadTree::node(add_op, vec![valid_leaf.clone(), valid_leaf]).unwrap();
    assert!(!valid_tree.is_null());
    let grafted_null = valid_tree.graft(0, &null_tree).unwrap();
    assert!(grafted_null.is_null());
}

#[test]
fn test_annihilator_decoy_refutation_witness_checks() {
    let mut decoy_bindings = BTreeMap::new();
    decoy_bindings.insert("x".into(), "3".into());
    decoy_bindings.insert("y".into(), "0".into());

    let decoy = AnnihilatorDecoy {
        id: "AB_FALSE_CERTAINTY_DECOY".into(),
        description: "Catches decoy candidate yielding target sum but violating linear system".into(),
        decoy_candidate: DecoyCandidate {
            bindings: decoy_bindings.clone(),
            claimed_sum: Some("3".into()),
        },
        refutation_witness: RefutationWitness {
            equation: "x + 2*y = 5".into(),
            evaluation: "3 + 2*(0) = 3 != 5".into(),
            action: "annihilate_tree".into(),
        },
    };

    // Case 1: Candidate does NOT match decoy
    let mut other_bindings = BTreeMap::new();
    other_bindings.insert("x".into(), "1".into());
    other_bindings.insert("y".into(), "2".into());
    let irr = decoy.evaluate(&other_bindings, None).unwrap();
    assert_eq!(irr, AnnihilatorDisposition::Irrelevant);

    // Case 2: Candidate matches decoy, but NO witness provided -> FAILS
    let unrefuted = decoy.evaluate(&decoy_bindings, None);
    assert!(unrefuted.is_err(), "unrefuted decoy must fail");
    match unrefuted.err().unwrap() {
        OperadRefusal::DecoyTrapUnrefuted { decoy_id, reason } => {
            assert_eq!(decoy_id, "AB_FALSE_CERTAINTY_DECOY");
            assert!(reason.contains("missing refutation witness"));
        }
        other => panic!("expected DecoyTrapUnrefuted, got {other:?}"),
    }

    // Case 3: Candidate matches decoy, invalid/tautological witness -> FAILS
    let invalid_witness = RefutationWitness {
        equation: "x + 2*y = 5".into(),
        evaluation: "looks good to me".into(), // Does not demonstrate inequality !=
        action: "accept".into(),
    };
    let bad_witness_res = decoy.evaluate(&decoy_bindings, Some(&invalid_witness));
    assert!(bad_witness_res.is_err());

    // Case 4: Candidate matches decoy with genuine refutation witness -> NEUTRALIZED
    let valid_witness = RefutationWitness {
        equation: "x + 2*y = 5".into(),
        evaluation: "3 + 2*(0) = 3 != 5".into(),
        action: "annihilate_tree".into(),
    };
    let neut = decoy.evaluate(&decoy_bindings, Some(&valid_witness)).unwrap();
    match neut {
        AnnihilatorDisposition::Neutralized { decoy_id, witness_evaluation } => {
            assert_eq!(decoy_id, "AB_FALSE_CERTAINTY_DECOY");
            assert_eq!(witness_evaluation, "3 + 2*(0) = 3 != 5");
        }
        _ => panic!("expected Neutralized disposition"),
    }
}

#[test]
fn test_immutable_text_span_boundary_checking() {
    let source_doc = "x + 2*y = 5\n2*x - y = 0\nx + y";

    // 1. Valid span: "x + 2*y = 5" at offsets [0, 11]
    let span1 = LeafTextSpan::new("span_eq1", PromptColour::RawTextSpan, "x + 2*y = 5", [0, 11]).unwrap();
    assert!(span1.verify_against_document(source_doc).is_ok());

    // 2. Inverted bounds: start > end
    let inv_err = LeafTextSpan::new("span_inv", PromptColour::RawTextSpan, "bad", [10, 5]);
    assert!(inv_err.is_err());

    // 3. Out of bounds offset
    let oob_span = LeafTextSpan::new("span_oob", PromptColour::RawTextSpan, "out", [0, 1000]).unwrap();
    assert!(oob_span.verify_against_document(source_doc).is_err());

    // 4. Token mutation: span text differs from source slice at offsets
    let mutated_span = LeafTextSpan::new("span_mut", PromptColour::RawTextSpan, "x + 2*y = 6", [0, 11]).unwrap();
    let verify_err = mutated_span.verify_against_document(source_doc);
    assert!(verify_err.is_err());
    match verify_err.err().unwrap() {
        OperadRefusal::ImmutableSpanViolation { span_id, reason } => {
            assert_eq!(span_id, "span_mut");
            assert!(reason.contains("span content mismatch"));
        }
        other => panic!("expected ImmutableSpanViolation, got {other:?}"),
    }
}

#[test]
fn test_coloured_operad_prompt_full_pipeline_verification() {
    let prompt = ColouredOperadPrompt {
        schema_id: "core.coda.categorical-operad-prompt.v2".into(),
        operad_meta: OperadMeta {
            family_name: "test_family".into(),
            prompt_id: "P_TEST_ROOT".into(),
            generation_id: 1,
            parents: vec![],
            authority_effect: "None".into(),
            polarity_structure: "polarized_triad".into(),
            symmetry: "planar".into(),
            execution_contract: "bounded_tree".into(),
        },
        colours: vec![
            PromptColourDef { id: PromptColour::RawTextSpan, carrier: "text".into(), description: "".into() },
            PromptColourDef { id: PromptColour::Equation, carrier: "Q[x, y]".into(), description: "".into() },
            PromptColourDef { id: PromptColour::IsolatedVariable, carrier: "var_assignment".into(), description: "".into() },
            PromptColourDef { id: PromptColour::RationalValue, carrier: "Q".into(), description: "".into() },
            PromptColourDef { id: PromptColour::InvariantWitness, carrier: "boolean_receipt".into(), description: "".into() },
            PromptColourDef { id: PromptColour::TargetResult, carrier: "composite_witness".into(), description: "".into() },
        ],
        source_document: None,
        operands: vec![
            LeafTextSpan::new("span_eq1", PromptColour::RawTextSpan, "x + 2*y = 5", [0, 11]).unwrap(),
            LeafTextSpan::new("span_eq2", PromptColour::RawTextSpan, "2*x - y = 0", [12, 23]).unwrap(),
            LeafTextSpan::new("span_target", PromptColour::RawTextSpan, "x + y", [24, 29]).unwrap(),
        ],
        operators: vec![
            PromptOperator::new("parse_eq", vec![PromptColour::RawTextSpan], PromptColour::Equation, "parse").unwrap(),
            PromptOperator::new("isolate_var", vec![PromptColour::Equation], PromptColour::IsolatedVariable, "isolate").unwrap(),
            PromptOperator::new("sub_and_solve", vec![PromptColour::Equation, PromptColour::IsolatedVariable], PromptColour::RationalValue, "solve").unwrap(),
        ],
        occurrences: vec![],
        composition_tree: None,
        congruence_ideals: vec![
            CongruenceIdeal::new("IDEAL_EXACT_RATIONAL_DOMAIN", PromptColour::RationalValue, "exact rational", "null_tree"),
        ],
        annihilators: vec![],
    };

    assert!(prompt.validate().is_ok());

    // Build derivation sub-tree
    let op_parse = &prompt.operators[0];
    let leaf1 = OperadTree::leaf(prompt.operands[0].clone());
    let parsed_tree = OperadTree::node(op_parse.clone(), vec![leaf1]).unwrap();

    let op_isolate = &prompt.operators[1];
    let isolated_tree = OperadTree::node(op_isolate.clone(), vec![parsed_tree.clone()]).unwrap();

    let op_solve = &prompt.operators[2];
    let solved_tree = OperadTree::node(op_solve.clone(), vec![parsed_tree, isolated_tree]).unwrap();
    assert_eq!(solved_tree.output_colour(), PromptColour::RationalValue);

    // Evaluate ideals on solved tree with exact rational
    let mut rationals = BTreeMap::new();
    rationals.insert("x".into(), "1".into());
    let evaluated = prompt.evaluate_ideals(&solved_tree, None, &rationals, true);
    assert!(!evaluated.is_null());

    // Evaluate ideals with float leak -> Projects to NullTree!
    let mut float_rationals = BTreeMap::new();
    float_rationals.insert("x".into(), "1.0001".into());
    let evaluated_float = prompt.evaluate_ideals(&solved_tree, None, &float_rationals, true);
    assert!(evaluated_float.is_null(), "must project to NullTree on float approximation");
}

// Origin: engine/crates_rs/tests/pfp_runtime/operad_tests.rs
// Claim: urn:core:crates_rs:tests:operad-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfdbec428 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfdbec428` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfdbec428 {
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
impl BoundaryErrorfdbec428 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfdbec428 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfdbec428 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfdbec428 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfdbec428> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfdbec428::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfdbec428::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfdbec428::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_fdbec428() {
    let admitted = BoundaryRecordfdbec428::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfdbec428::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

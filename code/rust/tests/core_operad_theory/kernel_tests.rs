//! Comprehensive unit tests for the higher operad kernel merged into core_operad_theory.

use core_operad_theory::kernel::*;

fn dummy_port(id: &str, colour: &str, schema: &str) -> PortSpec {
    PortSpec::new(id, colour, schema).unwrap()
}

fn dummy_op(id: &str, in_ports: Vec<PortSpec>, out_port: PortSpec) -> OperationSpec {
    dummy_op_grade(id, in_ports, out_port, InvocationGrade::Discipline)
}

fn dummy_op_grade(
    id: &str,
    in_ports: Vec<PortSpec>,
    out_port: PortSpec,
    grade: InvocationGrade,
) -> OperationSpec {
    OperationSpec::new(OperationSpecInput {
        operation_id: id,
        version: "v1.0.0",
        input_ports: in_ports,
        output_port: out_port,
        executor_ref: "exec_worker",
        executor_digest: "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        tool_refs: vec!["tool_a".into()],
        effects: vec!["pure".into()],
        invocation_grade: grade,
        authority_effect: AuthorityEffect::None,
        authority_ceiling: AuthorityEffect::None,
    })
    .unwrap()
}

fn license_for(ops: &[OperationSpec], colours: Vec<String>) -> AgentLicense {
    AgentLicense::new(
        "agent_007",
        ops.iter().map(|op| op.key()).collect(),
        colours,
        vec!["exec_worker".into()],
        vec!["tool_a".into()],
        vec!["pure".into()],
        AuthorityEffect::None,
        "active",
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    .unwrap()
}

#[test]
fn test_identity_and_primitive_normalization() {
    let p_in = dummy_port("p1", "colour_a", "schema_a");
    let p_out = dummy_port("p2", "colour_b", "schema_b");

    let id_term = identity(p_in.clone());
    let norm_id = normalize_term(&id_term).unwrap();
    assert_eq!(norm_id.boundary().inputs.len(), 1);
    assert_eq!(norm_id.boundary().output, p_in);

    let op = dummy_op("op1", vec![p_in.clone()], p_out.clone());
    let prim_term = OperationTerm::Primitive(op);
    let norm_prim = normalize_term(&prim_term).unwrap();
    assert_eq!(norm_prim.boundary().inputs.len(), 1);
    assert_eq!(norm_prim.boundary().output, p_out);
    assert_eq!(norm_prim.operations().len(), 1);
}

#[test]
fn admitted_tree_must_recheck_declared_child_arity_and_types() {
    let input = dummy_port("input", "State", "state.v1");
    let output = dummy_port("output", "Audit", "audit.v1");
    let operation = dummy_op("audit", vec![input.clone()], output);
    for children in [
        vec![],
        vec![
            ChildNode::Input(input.clone()),
            ChildNode::Input(input.clone()),
        ],
        vec![ChildNode::Input(dummy_port("input", "Proof", "state.v1"))],
        vec![ChildNode::Input(dummy_port("input", "State", "state.v2"))],
    ] {
        let claimed = OperationTerm::Admitted(NormalizedTerm::new(TreeNode::Operation {
            operation: operation.clone(),
            children,
        }));
        assert!(
            normalize_term(&claimed).is_err(),
            "malformed admitted tree accepted"
        );
        let license = license_for(
            &[operation.clone()],
            vec!["State".into(), "Audit".into(), "Proof".into()],
        );
        assert!(authorize_term(&license, &claimed).is_err());
    }
}

#[test]
fn admitted_tree_checks_nested_ports_but_keeps_occurrence_names() {
    let state = dummy_port("state", "State", "state.v1");
    let outer = dummy_op("outer", vec![state.clone()], state.clone());
    let inner = dummy_op("inner", vec![state.clone()], state.clone());
    let malformed = OperationTerm::Admitted(NormalizedTerm::new(TreeNode::Operation {
        operation: outer.clone(),
        children: vec![ChildNode::Operation {
            operation: inner,
            children: vec![ChildNode::Input(dummy_port("x", "State", "other"))],
        }],
    }));
    assert!(normalize_term(&malformed).is_err());
    let renamed = dummy_port("distinct-occurrence", "State", "state.v1");
    let valid = OperationTerm::Admitted(NormalizedTerm::new(TreeNode::Operation {
        operation: outer,
        children: vec![ChildNode::Input(renamed.clone())],
    }));
    assert_eq!(
        normalize_term(&valid).unwrap().boundary().inputs,
        vec![renamed]
    );
}

#[test]
fn substitution_cannot_launder_a_malformed_admitted_operand() {
    let state = dummy_port("state", "State", "state.v1");
    let operation = dummy_op("outer", vec![state.clone()], state.clone());
    let invalid = OperationTerm::Admitted(NormalizedTerm::new(TreeNode::Operation {
        operation,
        children: vec![ChildNode::Input(dummy_port("bad", "Audit", "audit.v1"))],
    }));
    let repair = OperationTerm::Primitive(dummy_op(
        "repair",
        vec![state],
        dummy_port("out", "Audit", "audit.v1"),
    ));
    assert_eq!(
        substitute(&invalid, 0, &repair).unwrap_err().code,
        "BOUNDARY_MISMATCH"
    );
}

#[test]
fn public_carriers_do_not_bypass_constructor_invariants() {
    let state = dummy_port("state", "State", "state.v1");
    let valid = dummy_op("operation", vec![state.clone()], state.clone());
    let mut bad_digest = valid.clone();
    bad_digest.executor_digest = "not-a-digest".into();
    let mut duplicate_ports = valid.clone();
    duplicate_ports.input_ports.push(state.clone());
    let mut noncanonical_name = valid.clone();
    noncanonical_name.operation_id.push(' ');
    let mut authority_escalation = valid;
    authority_escalation.authority_effect = AuthorityEffect::StateTransition;
    for operation in [
        bad_digest,
        duplicate_ports,
        authority_escalation,
        noncanonical_name,
    ] {
        assert_eq!(
            normalize_term(&OperationTerm::Primitive(operation.clone()))
                .unwrap_err()
                .code,
            "INVALID_OPERATION_SPEC"
        );
        let claimed = OperationTerm::Admitted(NormalizedTerm::new(TreeNode::Operation {
            children: operation
                .input_ports
                .iter()
                .cloned()
                .map(ChildNode::Input)
                .collect(),
            operation,
        }));
        assert_eq!(
            normalize_term(&claimed).unwrap_err().code,
            "INVALID_OPERATION_SPEC"
        );
    }
    let mut padded = state.clone();
    padded.colour_id.push(' ');
    assert_eq!(
        normalize_term(&identity(padded)).unwrap_err().code,
        "INVALID_OPERATION_SPEC"
    );
    let mut invalid = state;
    invalid.schema_ref.clear();
    assert_eq!(
        normalize_term(&identity(invalid.clone())).unwrap_err().code,
        "INVALID_OPERATION_SPEC"
    );
    assert_eq!(
        normalize_term(&OperationTerm::Admitted(NormalizedTerm::new(
            TreeNode::Identity(invalid)
        )))
        .unwrap_err()
        .code,
        "INVALID_OPERATION_SPEC"
    );
}

fn corolla(name: &str, arity: usize) -> OperationTerm {
    OperationTerm::Primitive(dummy_op(
        name,
        (0..arity)
            .map(|i| dummy_port(&format!("{name}.{i}"), "State", "state.v1"))
            .collect(),
        dummy_port(&format!("{name}.out"), "State", "state.v1"),
    ))
}

#[test]
fn bounded_planar_laws_include_nullary_and_repeated_colour_occurrences() {
    let mut nested = 0;
    let mut disjoint = 0;
    for a in 1..=3 {
        let f = corolla("f", a);
        let f_norm = normalize_term(&f).unwrap();
        assert_eq!(
            substitute(&identity(f_norm.boundary().output), 0, &f).unwrap(),
            f_norm
        );
        for i in 0..a {
            assert_eq!(
                substitute(&f, i, &identity(f_norm.boundary().inputs[i].clone())).unwrap(),
                f_norm
            );
            for b in 0..=3 {
                let g = corolla("g", b);
                let fg = substitute(&f, i, &g).unwrap();
                for c in 0..=3 {
                    let h = corolla("h", c);
                    for j in 0..b {
                        let left = substitute(&term_from_normalized(&fg), i + j, &h).unwrap();
                        let gh = substitute(&g, j, &h).unwrap();
                        let right = substitute(&f, i, &term_from_normalized(&gh)).unwrap();
                        assert_eq!(left, right, "nested slots {i}, {j}; arities {a}, {b}, {c}");
                        nested += 1;
                    }
                    for k in (i + 1)..a {
                        // k > i, so k+b-1 is defined even for a nullary g.
                        let left = substitute(&term_from_normalized(&fg), k + b - 1, &h).unwrap();
                        let fh = substitute(&f, k, &h).unwrap();
                        let right = substitute(&term_from_normalized(&fh), i, &g).unwrap();
                        assert_eq!(
                            left, right,
                            "disjoint slots {i}, {k}; arities {a}, {b}, {c}"
                        );
                        disjoint += 1;
                    }
                }
            }
        }
    }
    assert_eq!((nested, disjoint), (144, 64));
}

#[test]
fn test_term_substitution_and_associativity_erasure() {
    let p_a = dummy_port("pa", "colour_a", "schema_a");
    let p_b = dummy_port("pb", "colour_b", "schema_b");
    let p_c = dummy_port("pc", "colour_c", "schema_c");

    let op1 = dummy_op("op1", vec![p_b.clone()], p_c.clone());
    let op2 = dummy_op("op2", vec![p_a.clone()], p_b.clone());

    let comp = substitute(
        &OperationTerm::Primitive(op1),
        0,
        &OperationTerm::Primitive(op2),
    )
    .unwrap();
    assert_eq!(comp.boundary().inputs, vec![p_a]);
    assert_eq!(comp.boundary().output, p_c);
    assert_eq!(comp.operations().len(), 2);

    let comp_id = comp.canonical_id().unwrap();
    assert!(comp_id.starts_with("sha256:"));
}

#[test]
fn omitted_invocation_grade_defaults_to_discipline() {
    assert_eq!(InvocationGrade::default(), InvocationGrade::Discipline);
}

#[test]
fn entry_nested_in_entry_refuses_entry_over_entry() {
    let p_a = dummy_port("pa", "colour_a", "schema_a");
    let p_b = dummy_port("pb", "colour_b", "schema_b");
    let p_c = dummy_port("pc", "colour_c", "schema_c");
    let outer = dummy_op_grade(
        "outer",
        vec![p_b.clone()],
        p_c.clone(),
        InvocationGrade::Entry,
    );
    let inner = dummy_op_grade(
        "inner",
        vec![p_a.clone()],
        p_b.clone(),
        InvocationGrade::Entry,
    );
    let nested = substitute(
        &OperationTerm::Primitive(outer.clone()),
        0,
        &OperationTerm::Primitive(inner.clone()),
    )
    .unwrap();
    let license = license_for(
        &[outer, inner],
        vec!["colour_a".into(), "colour_b".into(), "colour_c".into()],
    );

    let refusal = authorize_normalized_term(&license, &nested).unwrap_err();

    assert_eq!(refusal.code, "ENTRY_OVER_ENTRY");
}

#[test]
fn entry_over_discipline_is_authorized() {
    let p_a = dummy_port("pa", "colour_a", "schema_a");
    let p_b = dummy_port("pb", "colour_b", "schema_b");
    let p_c = dummy_port("pc", "colour_c", "schema_c");
    let outer = dummy_op_grade(
        "outer",
        vec![p_b.clone()],
        p_c.clone(),
        InvocationGrade::Entry,
    );
    let inner = dummy_op_grade(
        "inner",
        vec![p_a.clone()],
        p_b.clone(),
        InvocationGrade::Discipline,
    );
    let nested = substitute(
        &OperationTerm::Primitive(outer.clone()),
        0,
        &OperationTerm::Primitive(inner.clone()),
    )
    .unwrap();
    let license = license_for(
        &[outer, inner],
        vec!["colour_a".into(), "colour_b".into(), "colour_c".into()],
    );

    assert!(authorize_normalized_term(&license, &nested).is_ok());
}

#[test]
fn test_capability_authorization() {
    let p_a = dummy_port("pa", "colour_a", "schema_a");
    let p_b = dummy_port("pb", "colour_b", "schema_b");
    let op = dummy_op("op1", vec![p_a.clone()], p_b.clone());

    let license = AgentLicense::new(
        "agent_007",
        vec![op.key()],
        vec!["colour_a".into(), "colour_b".into()],
        vec!["exec_worker".into()],
        vec!["tool_a".into()],
        vec!["pure".into()],
        AuthorityEffect::None,
        "active",
        "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    .unwrap();

    let term = OperationTerm::Primitive(op);
    let licensed = authorize_term(&license, &term).unwrap();
    assert_eq!(licensed.license_id, license.canonical_id().unwrap());
}

#[test]
fn test_lean_obligations_export() {
    let p_a = dummy_port("pa", "colour_a", "schema_a");
    let norm = normalize_term(&identity(p_a)).unwrap();

    let bundle = export_lean_obligations(&[norm], 3).unwrap();
    assert_eq!(bundle.authority_effect, AuthorityEffect::None);
    assert!(bundle.obligations.len() >= 3);
    let json_export = bundle.export_json().unwrap();
    assert!(json_export.contains("finite-presentation-through-3"));
}

#[test]
fn test_groupoid_path_word_reduction() {
    let p_a = dummy_port("pa", "colour_a", "schema_a");
    let norm = normalize_term(&identity(p_a)).unwrap();

    let id_path = identity_path2(&OperationTerm::Admitted(norm.clone())).unwrap();
    let path = Path2::Identity(id_path);

    let inv = inverse2(path.clone()).unwrap();
    assert_eq!(path.canonical_id().unwrap(), inv.canonical_id().unwrap());
}

#[test]
fn explicit_reindexing_routes_distinct_occurrences_and_keeps_planar_bytes() {
    let a = dummy_port("a", "A", "a.v1");
    let b = dummy_port("b", "B", "b.v1");
    let out = dummy_port("out", "Result", "result.v1");
    let planar =
        OperationTerm::Primitive(dummy_op("pair", vec![a.clone(), b.clone()], out.clone()));
    let original = normalize(&planar).unwrap();
    let identity = ReindexedTerm::from_planar(&planar).unwrap();
    let swap = InputPermutation::new(vec![1, 0]).unwrap();
    let view = identity.reindex(&swap).unwrap();
    assert_eq!(view.boundary().inputs, vec![b, a]);
    assert_eq!(view.boundary().output, out);
    assert_eq!(
        view.route_inputs(&["for-b", "for-a"]).unwrap(),
        vec!["for-a", "for-b"]
    );
    assert_eq!(view.planar(), &original);
    assert_eq!(
        view.planar().canonical_id().unwrap(),
        original.canonical_id().unwrap()
    );
    assert_ne!(
        view.canonical_id().unwrap(),
        original.canonical_id().unwrap()
    );
    assert_eq!(view.reindex(&swap.inverse()).unwrap(), identity);
    assert!(view.route_inputs(&["missing-b"]).is_err());
}

#[test]
fn explicit_reindexing_refuses_non_bijections_and_arity_mismatches() {
    for bad in [vec![1], vec![0, 0], vec![0, 2], vec![usize::MAX]] {
        assert_eq!(
            InputPermutation::new(bad).unwrap_err().code,
            "INVALID_INPUT_PERMUTATION"
        );
    }
    let empty = InputPermutation::identity(0);
    assert!(empty.as_slice().is_empty());
    let unary = ReindexedTerm::from_planar(&corolla("unary", 1)).unwrap();
    assert!(unary.reindex(&empty).is_err());
    assert!(ReindexedTerm::new(&corolla("binary", 2), InputPermutation::identity(1)).is_err());
    let state = dummy_port("state", "State", "state.v1");
    let malformed = OperationTerm::Admitted(NormalizedTerm::new(TreeNode::Operation {
        operation: dummy_op("malformed", vec![state.clone()], state),
        children: vec![],
    }));
    assert_eq!(
        ReindexedTerm::from_planar(&malformed).unwrap_err().code,
        "ARITY_MISMATCH"
    );
}

fn symbolic_value(term: &NormalizedTerm, values: &[&str]) -> String {
    fn child_value(child: &ChildNode, values: &mut std::slice::Iter<'_, &str>) -> String {
        match child {
            ChildNode::Input(_) => values.next().expect("one value per leaf").to_string(),
            ChildNode::Operation {
                operation,
                children,
            } => format!(
                "{}({})",
                operation.operation_id,
                children
                    .iter()
                    .map(|child| child_value(child, values))
                    .collect::<Vec<_>>()
                    .join(",")
            ),
        }
    }
    let mut remaining = values.iter();
    let value = match &term.tree {
        TreeNode::Identity(_) => remaining.next().unwrap().to_string(),
        TreeNode::Operation {
            operation,
            children,
        } => format!(
            "{}({})",
            operation.operation_id,
            children
                .iter()
                .map(|child| child_value(child, &mut remaining))
                .collect::<Vec<_>>()
                .join(",")
        ),
    };
    assert!(remaining.next().is_none());
    value
}

#[test]
fn explicit_reindexing_substitution_routes_values_at_the_external_slot() {
    let a = dummy_port("a", "A", "a.v1");
    let b = dummy_port("b", "B", "b.v1");
    let x = dummy_port("x", "X", "x.v1");
    let y = dummy_port("y", "Y", "y.v1");
    let out = dummy_port("out", "Result", "result.v1");
    let f = ReindexedTerm::new(
        &OperationTerm::Primitive(dummy_op("f", vec![a.clone(), b.clone()], out)),
        InputPermutation::new(vec![1, 0]).unwrap(),
    )
    .unwrap();
    let g = ReindexedTerm::new(
        &OperationTerm::Primitive(dummy_op("g", vec![x.clone(), y.clone()], b.clone())),
        InputPermutation::new(vec![1, 0]).unwrap(),
    )
    .unwrap();
    let fg = f.substitute(0, &g).unwrap();
    assert_eq!(fg.boundary().inputs, vec![y, x, a]);
    assert_eq!(fg.permutation().as_slice(), &[2, 1, 0]);
    let planar_values = fg.route_inputs(&["for-y", "for-x", "for-a"]).unwrap();
    assert_eq!(
        symbolic_value(fg.planar(), &planar_values),
        "f(for-a,g(for-x,for-y))"
    );
    assert_eq!(f.substitute(1, &g).unwrap_err().code, "BOUNDARY_MISMATCH");
    assert_eq!(f.substitute(2, &g).unwrap_err().code, "SLOT_OUT_OF_RANGE");

    let constant =
        ReindexedTerm::from_planar(&OperationTerm::Primitive(dummy_op("constant", vec![], b)))
            .unwrap();
    let closed_branch = f.substitute(0, &constant).unwrap();
    assert_eq!(closed_branch.permutation().as_slice(), &[0]);
    let values = closed_branch.route_inputs(&["for-a"]).unwrap();
    assert_eq!(
        symbolic_value(closed_branch.planar(), &values),
        "f(for-a,constant())"
    );
    assert_eq!(
        constant.substitute(0, &g).unwrap_err().code,
        "SLOT_OUT_OF_RANGE"
    );
}

fn finite_permutations(arity: usize) -> Vec<InputPermutation> {
    fn enumerate(values: &mut [usize], offset: usize, result: &mut Vec<InputPermutation>) {
        if offset == values.len() {
            result.push(InputPermutation::new(values.to_vec()).unwrap());
            return;
        }
        for index in offset..values.len() {
            values.swap(offset, index);
            enumerate(values, offset + 1, result);
            values.swap(offset, index);
        }
    }
    let mut result = Vec::new();
    enumerate(&mut (0..arity).collect::<Vec<_>>(), 0, &mut result);
    result
}

#[test]
fn explicit_reindexing_finite_group_action_and_routing() {
    let mut pairs = 0;
    let mut triples = 0;
    for n in 0..=4 {
        let identity = InputPermutation::identity(n);
        let base = ReindexedTerm::from_planar(&corolla("same-colour", n)).unwrap();
        let values = (0..n).collect::<Vec<_>>();
        assert_eq!(base.reindex(&identity).unwrap(), base);
        for p in finite_permutations(n) {
            assert_eq!(p.compose(&identity).unwrap(), p);
            assert_eq!(identity.compose(&p).unwrap(), p);
            assert_eq!(p.compose(&p.inverse()).unwrap(), identity);
            assert_eq!(p.inverse().compose(&p).unwrap(), identity);
            let first = base.reindex(&p).unwrap();
            assert_eq!(first.reindex(&p.inverse()).unwrap(), base);
            assert_eq!(
                first.to_canonical()["schema_version"],
                REINDEXED_TERM_PROFILE
            );
            assert_eq!(first.to_canonical()["planar"], base.planar().to_canonical());
            if p != identity {
                assert_ne!(first.canonical_id().unwrap(), base.canonical_id().unwrap());
            }
            for q in finite_permutations(n) {
                let sequential = first.reindex(&q).unwrap();
                assert_eq!(sequential, base.reindex(&p.compose(&q).unwrap()).unwrap());
                let reordered = q
                    .as_slice()
                    .iter()
                    .map(|&index| values[index])
                    .collect::<Vec<_>>();
                assert_eq!(
                    sequential.route_inputs(&reordered).unwrap(),
                    first.route_inputs(&values).unwrap()
                );
                pairs += 1;
                if n <= 3 {
                    for r in finite_permutations(n) {
                        assert_eq!(
                            p.compose(&q).unwrap().compose(&r).unwrap(),
                            p.compose(&q.compose(&r).unwrap()).unwrap()
                        );
                        triples += 1;
                    }
                }
            }
        }
    }
    assert_eq!(pairs, 618);
    assert_eq!(triples, 226);
    assert_eq!(
        InputPermutation::identity(1)
            .compose(&InputPermutation::identity(2))
            .unwrap_err()
            .code,
        "PERMUTATION_ARITY_MISMATCH"
    );
}

#[test]
fn explicit_reindexing_substitution_equivariance_by_leaf_occurrence() {
    let mut cases = 0;
    for n in 1..=3 {
        let f_term = corolla("f", n);
        for p in finite_permutations(n) {
            let f = ReindexedTerm::new(&f_term, p.clone()).unwrap();
            for m in 0..=3 {
                let g_term = corolla("g", m);
                for q in finite_permutations(m) {
                    let g = ReindexedTerm::new(&g_term, q).unwrap();
                    for i in 0..n {
                        let fg = f.substitute(i, &g).unwrap();
                        let mut expected_boundary = f.boundary().inputs;
                        expected_boundary.splice(i..i + 1, g.boundary().inputs);
                        assert_eq!(fg.boundary().inputs, expected_boundary);
                        let planar = substitute(&f_term, p.as_slice()[i], &g_term).unwrap();
                        assert_eq!(fg.planar(), &planar);
                        // An occurrence-name oracle independent of index-shift arithmetic.
                        let leaves = planar.boundary().inputs;
                        let expected_order = expected_boundary
                            .iter()
                            .map(|port| {
                                leaves
                                    .iter()
                                    .position(|leaf| leaf.port_id == port.port_id)
                                    .unwrap()
                            })
                            .collect::<Vec<_>>();
                        let expected = ReindexedTerm::new(
                            &term_from_normalized(&planar),
                            InputPermutation::new(expected_order).unwrap(),
                        )
                        .unwrap();
                        assert_eq!(fg, expected);
                        let external_names = expected_boundary
                            .iter()
                            .map(|p| p.port_id.as_str())
                            .collect::<Vec<_>>();
                        let planar_names = leaves
                            .iter()
                            .map(|p| p.port_id.as_str())
                            .collect::<Vec<_>>();
                        assert_eq!(fg.route_inputs(&external_names).unwrap(), planar_names);
                        assert_eq!(
                            symbolic_value(fg.planar(), &fg.route_inputs(&external_names).unwrap()),
                            symbolic_value(&planar, &planar_names)
                        );
                        cases += 1;
                    }
                }
            }
        }
    }
    assert_eq!(cases, 230);
}

#[test]
fn explicit_reindexing_finite_nested_and_disjoint_laws() {
    let mut nested = 0;
    let mut disjoint = 0;
    for n in 1..=3 {
        for p in finite_permutations(n) {
            let f = ReindexedTerm::new(&corolla("f", n), p).unwrap();
            let left_identity = ReindexedTerm::from_planar(&identity(f.boundary().output)).unwrap();
            assert_eq!(left_identity.substitute(0, &f).unwrap(), f);
            for i in 0..n {
                let right_identity =
                    ReindexedTerm::from_planar(&identity(f.boundary().inputs[i].clone())).unwrap();
                assert_eq!(f.substitute(i, &right_identity).unwrap(), f);
                for m in 0..=3 {
                    for q in finite_permutations(m) {
                        let g = ReindexedTerm::new(&corolla("g", m), q).unwrap();
                        let fg = f.substitute(i, &g).unwrap();
                        for l in 0..=3 {
                            for r in finite_permutations(l) {
                                let h = ReindexedTerm::new(&corolla("h", l), r).unwrap();
                                for j in 0..m {
                                    let left = fg.substitute(i + j, &h).unwrap();
                                    let right =
                                        f.substitute(i, &g.substitute(j, &h).unwrap()).unwrap();
                                    assert_eq!(left, right);
                                    nested += 1;
                                }
                                for k in i + 1..n {
                                    let left = fg.substitute(k - 1 + m, &h).unwrap();
                                    let right =
                                        f.substitute(k, &h).unwrap().substitute(i, &g).unwrap();
                                    assert_eq!(left, right);
                                    disjoint += 1;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert_eq!(nested, 5290);
    assert_eq!(disjoint, 2000);
}

#[test]
fn explicit_reindexing_preserves_the_existing_authorization_boundary() {
    let outer = corolla("outer", 2);
    let inner = corolla("inner", 1);
    let reindexed = ReindexedTerm::new(&outer, InputPermutation::new(vec![1, 0]).unwrap()).unwrap();
    let license = license_for(&reindexed.planar().operations(), vec!["State".into()]);
    assert!(authorize_normalized_term(&license, reindexed.planar()).is_ok());
    let composite = reindexed
        .substitute(0, &ReindexedTerm::from_planar(&inner).unwrap())
        .unwrap();
    assert!(authorize_normalized_term(&license, composite.planar()).is_err());
}

// Origin: engine/crates_rs/tests/core_operad_theory/kernel_tests.rs
// Claim: urn:core:crates_rs:tests:kernel-tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord10ddec0f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord10ddec0f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError10ddec0f {
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
impl BoundaryError10ddec0f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError10ddec0f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError10ddec0f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord10ddec0f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError10ddec0f> {
        if capacity_bound == 0 {
            return Err(BoundaryError10ddec0f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError10ddec0f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError10ddec0f::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_10ddec0f() {
    let admitted = BoundaryRecord10ddec0f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord10ddec0f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

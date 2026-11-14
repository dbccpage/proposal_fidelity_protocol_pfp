//! The term kernel and the law battery: laws hold on lawful operations, and every false claim is caught.
//!
//! AuthorityEffect: None.

use pfp_operads::laws::{
    compare, composition_defect, parallel, run_battery, run_battery_within, sequential, Panel,
};
use pfp_operads::term::{Body, Colour, Operation, Term, Value, Variant};

fn number() -> Colour {
    Colour::new("prompt_colour", "RationalValue").unwrap()
}

fn witness() -> Colour {
    Colour::new("prompt_colour", "InvariantWitness").unwrap()
}

fn op(name: &str, arity: usize, body: Body, variant: Variant) -> Operation {
    Operation::new(name, vec![number(); arity], number(), body, variant, 1).unwrap()
}

fn ints(values: &[i64]) -> Vec<Value> {
    values.iter().copied().map(Value::Int).collect()
}

fn panel() -> Panel {
    let mut panel = Panel::default();
    panel.insert(number(), ints(&[2, -3, 5, 7]));
    panel.insert(
        witness(),
        vec![Value::List(ints(&[1, 2])), Value::List(ints(&[3]))],
    );
    panel
}

fn lawful() -> Vec<Operation> {
    vec![
        op("add", 2, Body::Sum, Variant::Symmetric),
        op("mul", 2, Body::Product, Variant::Symmetric),
        op("sub", 2, Body::Difference, Variant::Planar),
        op("add3", 3, Body::Sum, Variant::Symmetric),
        op("zero", 0, Body::Sum, Variant::Planar),
        Operation::new(
            "pack",
            vec![number(), number()],
            witness(),
            Body::Pack,
            Variant::Planar,
            2,
        )
        .unwrap(),
        Operation::new(
            "total",
            vec![witness()],
            number(),
            Body::SumList,
            Variant::Planar,
            3,
        )
        .unwrap(),
    ]
}

#[test]
fn colours_come_from_the_canon_only() {
    assert_eq!(
        Colour::new("prompt_colour", "Integer").unwrap_err().code,
        "UNKNOWN_COLOUR"
    );
    assert_eq!(
        Colour::new("ddc_letter", "E").unwrap_err().code,
        "UNKNOWN_COLOUR_TYPE"
    );
    assert_eq!(
        Colour::new("operad_colour", "Proof").unwrap().name(),
        "Proof"
    );
    assert_ne!(Colour::new("operad_colour", "Proof").unwrap(), number());
}

#[test]
fn an_operation_must_fit_its_body() {
    let refused = |arity, body| {
        Operation::new(
            "x",
            vec![number(); arity],
            number(),
            body,
            Variant::Planar,
            0,
        )
    };
    assert_eq!(refused(2, Body::Identity).unwrap_err().code, "ARITY");
    assert_eq!(refused(1, Body::Difference).unwrap_err().code, "ARITY");
    assert_eq!(refused(0, Body::SumList).unwrap_err().code, "ARITY");
    assert!(refused(5, Body::Opaque).is_ok());
    let bent = Operation::new(
        "id",
        vec![number()],
        witness(),
        Body::Identity,
        Variant::Planar,
        0,
    );
    assert_eq!(bent.unwrap_err().code, "COLOUR_MISMATCH");
    let unnamed = Operation::new(" ", vec![], number(), Body::Sum, Variant::Planar, 0);
    assert_eq!(unnamed.unwrap_err().code, "BAD_NAME");
}

#[test]
fn substitution_plugs_exactly_the_named_input() {
    let sub = Term::corolla(&op("sub", 2, Body::Difference, Variant::Planar));
    let add = Term::corolla(&op("add", 2, Body::Sum, Variant::Symmetric));
    let first = sub.substitute(0, &add).unwrap();
    let second = sub.substitute(1, &add).unwrap();
    assert_eq!(first.leaves().len(), 3);
    assert_eq!(first.eval(&ints(&[10, 1, 4])).unwrap(), Value::Int(7));
    assert_eq!(second.eval(&ints(&[10, 1, 4])).unwrap(), Value::Int(5));
    assert!(compare(&first, &second, &panel()).unwrap().is_some());
    assert_eq!(
        sub.substitute(2, &add).unwrap_err().code,
        "SLOT_OUT_OF_RANGE"
    );
    assert_eq!(
        first.substitute(3, &add).unwrap_err().code,
        "SLOT_OUT_OF_RANGE"
    );
    let pack = Term::corolla(&lawful()[5]);
    assert_eq!(
        sub.substitute(0, &pack).unwrap_err().code,
        "COLOUR_MISMATCH"
    );
    assert_eq!(first.target(), &number());
    assert_eq!(Term::Leaf(witness()).target(), &witness());
}

#[test]
fn evaluation_is_exact_and_refuses_what_it_cannot_compute() {
    let mul = Term::corolla(&op("mul", 2, Body::Product, Variant::Symmetric));
    assert_eq!(mul.eval(&ints(&[6, 7])).unwrap(), Value::Int(42));
    assert_eq!(
        mul.eval(&ints(&[i64::MAX, 2])).unwrap_err().code,
        "OVERFLOW"
    );
    assert_eq!(mul.eval(&ints(&[6])).unwrap_err().code, "ARITY");
    assert_eq!(mul.eval(&ints(&[6, 7, 8])).unwrap_err().code, "ARITY");
    let add = Term::corolla(&op("add", 2, Body::Sum, Variant::Symmetric));
    assert_eq!(
        add.eval(&ints(&[i64::MAX, 1])).unwrap_err().code,
        "OVERFLOW"
    );
    assert_eq!(
        add.eval(&[Value::Int(1), Value::List(vec![])])
            .unwrap_err()
            .code,
        "VALUE_SHAPE"
    );
    let sub = Term::corolla(&op("sub", 2, Body::Difference, Variant::Planar));
    assert_eq!(
        sub.eval(&ints(&[i64::MIN, 1])).unwrap_err().code,
        "OVERFLOW"
    );
    let total = Term::corolla(&lawful()[6]);
    assert_eq!(
        total.eval(&[Value::List(ints(&[4, 5, 6]))]).unwrap(),
        Value::Int(15)
    );
    assert_eq!(total.eval(&ints(&[4])).unwrap_err().code, "VALUE_SHAPE");
    let pack = Term::corolla(&lawful()[5]);
    assert_eq!(
        pack.eval(&ints(&[1, 2])).unwrap(),
        Value::List(ints(&[1, 2]))
    );
    let opaque = Term::corolla(&op("opaque", 2, Body::Opaque, Variant::Planar));
    assert_eq!(opaque.eval(&ints(&[1, 2])).unwrap_err().code, "NO_BODY");
    assert_eq!(
        Body::Identity.apply(&ints(&[1, 2])).unwrap_err().code,
        "ARITY"
    );
}

#[test]
fn cost_adds_over_the_tree_and_overflow_is_refused() {
    let pack = Term::corolla(&lawful()[5]);
    let total = Term::corolla(&lawful()[6]);
    let add = Term::corolla(&op("add", 2, Body::Sum, Variant::Symmetric));
    let tree = total
        .substitute(0, &pack)
        .unwrap()
        .substitute(1, &add)
        .unwrap();
    assert_eq!(tree.cost().unwrap(), 3 + 2 + 1);
    assert_eq!(Term::Leaf(number()).cost().unwrap(), 0);
    let dear = Operation::new(
        "dear",
        vec![number()],
        number(),
        Body::Opaque,
        Variant::Planar,
        u64::MAX,
    )
    .unwrap();
    let twice = Term::corolla(&dear)
        .substitute(0, &Term::corolla(&dear))
        .unwrap();
    assert_eq!(twice.cost().unwrap_err().code, "OVERFLOW");
}

#[test]
fn both_bracketings_agree_on_a_worked_case() {
    let sub = op("sub", 2, Body::Difference, Variant::Planar);
    let add = op("add", 2, Body::Sum, Variant::Symmetric);
    let (left, right) = sequential(&sub, 1, &sub, 0, &add).unwrap();
    assert_eq!(left, right);
    assert_eq!(left.eval(&ints(&[10, 1, 2, 3])).unwrap(), Value::Int(10));
    let (left, right) = parallel(&sub, 0, &add, 1, &sub).unwrap();
    assert_eq!(left, right);
    assert_eq!(left.eval(&ints(&[1, 2, 9, 4])).unwrap(), Value::Int(-2));
    assert_eq!(
        parallel(&sub, 1, &add, 1, &sub).unwrap_err().code,
        "SLOT_ORDER"
    );
    assert_eq!(
        parallel(&sub, 1, &add, 0, &sub).unwrap_err().code,
        "SLOT_ORDER"
    );
    let zero = op("zero", 0, Body::Sum, Variant::Planar);
    let (left, right) = parallel(&sub, 0, &zero, 1, &add).unwrap();
    assert_eq!(left, right);
    assert_eq!(left.eval(&ints(&[3, 4])).unwrap(), Value::Int(-7));
}

#[test]
fn identities_vanish_in_the_normal_form() {
    let sub = Term::corolla(&op("sub", 2, Body::Difference, Variant::Planar));
    let id = Term::corolla(&Operation::identity(&number()));
    let padded = id.substitute(0, &sub.substitute(1, &id).unwrap()).unwrap();
    assert_ne!(padded, sub);
    assert_eq!(padded.normalise(), sub);
    assert_eq!(padded.cost().unwrap(), sub.cost().unwrap());
    assert_eq!(compare(&padded, &sub, &panel()).unwrap(), None);
    assert_eq!(id.normalise(), Term::Leaf(number()));
}

#[test]
fn the_battery_holds_on_lawful_operations_and_counts_what_it_checked() {
    let report = run_battery(&lawful(), &panel()).unwrap();
    assert!(report.holds(), "{:?}", report.violations);
    assert_eq!(report.unit, 7 + 2 + 2 + 2 + 3 + 2 + 1);
    assert_eq!(report.symmetry, 1 + 1 + 2);
    assert_eq!(report.composition, 11 * 6 + 1);
    assert!(report.sequential > 100 && report.parallel > 50);
    let opaque = [
        op("f", 2, Body::Opaque, Variant::Planar),
        op("g", 1, Body::Opaque, Variant::Planar),
    ];
    assert!(run_battery(&opaque, &panel()).unwrap().holds());
}

#[test]
fn a_false_symmetry_claim_is_a_violation() {
    for body in [Body::Difference, Body::Pack] {
        let target = if body == Body::Pack {
            witness()
        } else {
            number()
        };
        let liar = Operation::new(
            "liar",
            vec![number(), number()],
            target,
            body,
            Variant::Symmetric,
            0,
        )
        .unwrap();
        let report = run_battery(&[liar], &panel()).unwrap();
        assert_eq!(report.symmetry, 1);
        assert_eq!(report.violations.len(), 1);
        assert_eq!(report.violations[0].law, "symmetry");
        assert_eq!(report.violations[0].slots, vec![0, 1]);
        assert!(!report.holds());
    }
    let mixed = Operation::new(
        "mixed",
        vec![number(), witness()],
        witness(),
        Body::Pack,
        Variant::Symmetric,
        0,
    )
    .unwrap();
    assert_eq!(run_battery(&[mixed], &panel()).unwrap().symmetry, 0);
    let honest = op("sub", 2, Body::Difference, Variant::Planar);
    assert_eq!(run_battery(&[honest], &panel()).unwrap().symmetry, 0);
}

#[test]
fn compare_sees_a_different_value_a_different_cost_and_a_different_tree() {
    let add = Term::corolla(&op("add", 2, Body::Sum, Variant::Symmetric));
    let mul = Term::corolla(&op("mul", 2, Body::Product, Variant::Symmetric));
    let dearer = Operation::new(
        "add",
        vec![number(); 2],
        number(),
        Body::Sum,
        Variant::Symmetric,
        9,
    )
    .unwrap();
    let renamed = Term::corolla(&op("plus", 2, Body::Sum, Variant::Symmetric));
    let found = |other: &Term| compare(&add, other, &panel()).unwrap().unwrap();
    assert!(found(&mul).contains("differ on inputs"));
    assert!(found(&Term::corolla(&dearer)).contains("different costs"));
    assert!(found(&renamed).contains("different trees"));
    assert_eq!(compare(&add, &add, &panel()).unwrap(), None);
    let id = Term::corolla(&Operation::identity(&number()));
    assert_eq!(compare(&id, &Term::Leaf(number()), &panel()).unwrap(), None);
    let opaque = Term::corolla(&op("f", 2, Body::Opaque, Variant::Planar));
    assert!(
        found(&opaque).contains("differ on inputs"),
        "a value and a refusal are different outcomes"
    );
}

#[test]
fn running_a_composite_is_running_its_parts_in_order() {
    let sub = Term::corolla(&op("sub", 2, Body::Difference, Variant::Planar));
    let add3 = Term::corolla(&op("add3", 3, Body::Sum, Variant::Symmetric));
    for slot in 0..2 {
        assert_eq!(
            composition_defect(&sub, slot, &add3, &panel()).unwrap(),
            None
        );
    }
    for slot in 0..3 {
        assert_eq!(
            composition_defect(&add3, slot, &sub, &panel()).unwrap(),
            None
        );
    }
    let deep = sub.substitute(1, &add3).unwrap();
    assert_eq!(composition_defect(&deep, 2, &sub, &panel()).unwrap(), None);
    let total = Term::corolla(&lawful()[6]);
    let pack = Term::corolla(&lawful()[5]);
    assert_eq!(
        composition_defect(&total, 0, &pack, &panel()).unwrap(),
        None
    );
    assert_eq!(
        composition_defect(&sub, 2, &add3, &panel())
            .unwrap_err()
            .code,
        "SLOT_OUT_OF_RANGE"
    );
    let mut huge = Panel::default();
    huge.insert(number(), ints(&[i64::MAX, i64::MAX, -1]));
    let mul = Term::corolla(&op("mul", 2, Body::Product, Variant::Symmetric));
    assert_eq!(
        composition_defect(&sub, 0, &mul, &huge).unwrap(),
        None,
        "both runs refuse with OVERFLOW"
    );
    let dear = Operation::new(
        "dear",
        vec![number()],
        number(),
        Body::Opaque,
        Variant::Planar,
        u64::MAX,
    )
    .unwrap();
    let dear = Term::corolla(&dear);
    assert_eq!(
        composition_defect(&dear, 0, &dear, &panel())
            .unwrap_err()
            .code,
        "OVERFLOW"
    );
}

#[test]
fn the_panel_must_cover_every_colour_and_rotates_its_samples() {
    let mut thin = Panel::default();
    thin.insert(number(), ints(&[1, 2, 3]));
    let total = lawful()[6].clone();
    assert_eq!(run_battery(&[total], &thin).unwrap_err().code, "NO_SAMPLES");
    thin.insert(witness(), vec![]);
    assert_eq!(
        thin.assignments(&[&witness()]).unwrap_err().code,
        "NO_SAMPLES"
    );
    let rounds = thin.assignments(&[&number(), &number()]).unwrap();
    assert_eq!(rounds, vec![ints(&[1, 2]), ints(&[2, 3]), ints(&[3, 1])]);
    assert_eq!(thin.assignments(&[]).unwrap(), vec![Vec::<Value>::new()]);
}

#[test]
fn the_battery_refuses_to_run_past_its_bound() {
    let ops = lawful();
    let full = run_battery(&ops, &panel()).unwrap();
    let total = full.sequential + full.parallel + full.unit + full.symmetry;
    let unit_and_composition = total - full.symmetry;
    assert!(run_battery_within(&ops, &panel(), unit_and_composition).is_ok());
    assert_eq!(
        run_battery_within(&ops, &panel(), unit_and_composition - 1)
            .unwrap_err()
            .code,
        "BATTERY_TOO_LARGE"
    );
}

#[test]
fn a_difference_needs_two_integers() {
    let sub = Term::corolla(&op("sub", 2, Body::Difference, Variant::Planar));
    assert_eq!(sub.eval(&ints(&[7, 9])).unwrap(), Value::Int(-2));
    let shaped = sub.eval(&[Value::List(vec![]), Value::Int(1)]);
    assert_eq!(shaped.unwrap_err().code, "VALUE_SHAPE");
}

#[test]
fn the_longest_column_sets_the_number_of_rounds() {
    let mut uneven = Panel::default();
    uneven.insert(number(), ints(&[1, 2, 3]));
    uneven.insert(
        witness(),
        vec![Value::List(ints(&[8])), Value::List(ints(&[9]))],
    );
    let rounds = uneven.assignments(&[&witness(), &number()]).unwrap();
    assert_eq!(rounds.len(), 3);
    assert_eq!(rounds[2], vec![Value::List(ints(&[8])), Value::Int(1)]);
}

#[test]
fn two_refusals_agree_whatever_their_order() {
    let sub = Term::corolla(&op("sub", 2, Body::Difference, Variant::Planar));
    let mul = Term::corolla(&op("mul", 2, Body::Product, Variant::Symmetric));
    let early = sub.substitute(0, &Term::corolla(&lawful()[6])).unwrap();
    let whole = early.substitute(1, &mul).unwrap();
    let inputs = ints(&[4, i64::MAX, i64::MAX]);
    assert_eq!(whole.eval(&inputs).unwrap_err().code, "VALUE_SHAPE");
    assert_eq!(mul.eval(&inputs[1..]).unwrap_err().code, "OVERFLOW");
    let mut mixed = Panel::default();
    mixed.insert(number(), ints(&[i64::MAX, i64::MAX]));
    mixed.insert(witness(), ints(&[4]));
    assert_eq!(composition_defect(&early, 1, &mul, &mixed).unwrap(), None);
}

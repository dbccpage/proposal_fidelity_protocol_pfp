//! The table is well formed and the committed Python and JSON renderings match it.

use std::collections::HashSet;
use std::path::Path;

use core_operad_canon::render::{to_json, to_python, JSON_PATH, PYTHON_PATH};
use core_operad_canon::{type_by_id, DdcOp, OperadColour, Status, OPERAD_COLOURS, OPERAD_TYPES};

fn committed(relative: &str) -> String {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../..")
        .join(relative);
    std::fs::read_to_string(path)
        .unwrap_or_default()
        .replace("\r\n", "\n")
}

#[test]
fn ids_are_unique_and_values_are_sets() {
    let mut ids = HashSet::new();
    for entry in OPERAD_TYPES {
        assert!(ids.insert(entry.id), "duplicate type id {}", entry.id);
        assert!(!entry.values.is_empty(), "{} has no values", entry.id);
        let distinct: HashSet<_> = entry.values.iter().collect();
        assert_eq!(
            distinct.len(),
            entry.values.len(),
            "{} repeats a value",
            entry.id
        );
        assert_eq!(
            entry.status == Status::Proposed,
            entry.decision.is_some(),
            "{}: a type is PROPOSED exactly when it states a decision",
            entry.id
        );
    }
}

#[test]
fn letters_of_points_at_a_registered_alphabet() {
    for entry in OPERAD_TYPES {
        if let Some(alphabet) = entry.letters_of {
            assert!(
                type_by_id(alphabet).is_some(),
                "{} names unknown alphabet {alphabet}",
                entry.id
            );
        }
    }
}

#[test]
fn rust_enums_are_the_table_values() {
    assert_eq!(
        type_by_id("operad_colour").unwrap().values,
        OperadColour::NAMES
    );
    assert_eq!(OPERAD_COLOURS.as_slice(), OperadColour::NAMES);
    for colour in OperadColour::ALL {
        assert_eq!(OperadColour::from_name(colour.as_str()), Some(colour));
    }
    let letters: Vec<&str> = DdcOp::alphabet().iter().map(|op| op.letter()).collect();
    assert_eq!(letters, DdcOp::LETTERS);
    assert_eq!(type_by_id("ddc_letter").unwrap().values, DdcOp::LETTERS);
    for op in DdcOp::alphabet() {
        assert_eq!(DdcOp::from_letter(op.letter()), Some(op));
    }
}

#[test]
fn committed_renderings_are_current() {
    assert!(
        committed(JSON_PATH) == to_json(),
        "{JSON_PATH} is stale: run `cargo run -p core_operad_canon -- write`"
    );
    assert!(
        committed(PYTHON_PATH) == to_python(),
        "{PYTHON_PATH} is stale: run `cargo run -p core_operad_canon -- write`"
    );
}

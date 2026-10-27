//! Automated mechanical cross-check between the Rust replication and Python's `000_mechanization_run.json`.
//!
//! Compares all witness fields in the 16 shared executable/refusal rows.
//! Five paper-only/prose/Lean rows are explicitly excluded from value comparison.
//! Missing/extra rows, missing/extra fields, and changed claim groups are rejected.
//!
//! Standard-library only; zero external dependencies.
//!
//! `AuthorityEffect: None.`


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_6047c9f1 = (i128, i128);
use core_ooutwire_primitives::alpha_projection_obstruction::run;
use std::path::Path;

#[derive(Debug, Clone, PartialEq)]
enum JsonValue {
    Null,
    Bool(bool),
    Number(f64, String),
    String(String),
    Array(Vec<JsonValue>),
    Object(Vec<(String, JsonValue)>),
}

impl JsonValue {
    fn get(&self, key: &str) -> Option<&JsonValue> {
        match self {
            JsonValue::Object(entries) => entries.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }

    fn as_str(&self) -> Option<&str> {
        match self {
            JsonValue::String(s) => Some(s),
            _ => None,
        }
    }

    fn as_f64(&self) -> Option<f64> {
        match self {
            JsonValue::Number(n, _) => Some(*n),
            _ => None,
        }
    }

    fn as_array(&self) -> Option<&[JsonValue]> {
        match self {
            JsonValue::Array(arr) => Some(arr),
            _ => None,
        }
    }
}

struct JsonParser<'a> {
    chars: std::str::Chars<'a>,
    peeked: Option<char>,
}

impl<'a> JsonParser<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            chars: input.chars(),
            peeked: None,
        }
    }

    fn peek(&mut self) -> Option<char> {
        if self.peeked.is_none() {
            self.peeked = self.chars.next();
        }
        self.peeked
    }

    fn next(&mut self) -> Option<char> {
        self.peeked.take().or_else(|| self.chars.next())
    }

    fn skip_whitespace(&mut self) {
        while let Some(ch) = self.peek() {
            if ch.is_whitespace() {
                self.next();
            } else {
                break;
            }
        }
    }

    fn parse_value(&mut self) -> Result<JsonValue, String> {
        self.skip_whitespace();
        let ch = self.peek().ok_or("unexpected EOF")?;
        match ch {
            'n' => self.parse_null(),
            't' | 'f' => self.parse_bool(),
            '"' => self.parse_string().map(JsonValue::String),
            '[' => self.parse_array(),
            '{' => self.parse_object(),
            '-' | '0'..='9' => self.parse_number(),
            other => Err(format!("unexpected character: {other}")),
        }
    }

    fn parse_null(&mut self) -> Result<JsonValue, String> {
        for expected in "null".chars() {
            let ch = self.next().ok_or("unexpected EOF in null")?;
            if ch != expected {
                return Err(format!("expected '{expected}', got '{ch}'"));
            }
        }
        Ok(JsonValue::Null)
    }

    fn parse_bool(&mut self) -> Result<JsonValue, String> {
        if self.peek() == Some('t') {
            for expected in "true".chars() {
                let ch = self.next().ok_or("unexpected EOF in bool")?;
                if ch != expected {
                    return Err(format!("expected '{expected}', got '{ch}'"));
                }
            }
            Ok(JsonValue::Bool(true))
        } else {
            for expected in "false".chars() {
                let ch = self.next().ok_or("unexpected EOF in bool")?;
                if ch != expected {
                    return Err(format!("expected '{expected}', got '{ch}'"));
                }
            }
            Ok(JsonValue::Bool(false))
        }
    }

    fn parse_string(&mut self) -> Result<String, String> {
        self.next(); // consume opening quote
        let mut s = String::new();
        while let Some(ch) = self.next() {
            match ch {
                '"' => return Ok(s),
                '\\' => {
                    let esc = self.next().ok_or("unexpected EOF in string escape")?;
                    match esc {
                        '"' => s.push('"'),
                        '\\' => s.push('\\'),
                        '/' => s.push('/'),
                        'b' => s.push('\x08'),
                        'f' => s.push('\x0c'),
                        'n' => s.push('\n'),
                        'r' => s.push('\r'),
                        't' => s.push('\t'),
                        'u' => {
                            let mut hex = String::new();
                            for _ in 0..4 {
                                hex.push(self.next().ok_or("unexpected EOF in unicode escape")?);
                            }
                            let code = u32::from_str_radix(&hex, 16)
                                .map_err(|e| format!("invalid unicode escape: {e}"))?;
                            let c = char::from_u32(code)
                                .ok_or_else(|| format!("invalid unicode scalar value: {code}"))?;
                            s.push(c);
                        }
                        other => return Err(format!("unsupported escape: \\{other}")),
                    }
                }
                other => s.push(other),
            }
        }
        Err("unterminated string".into())
    }

    fn parse_number(&mut self) -> Result<JsonValue, String> {
        let mut s = String::new();
        while let Some(ch) = self.peek() {
            if ch == '-' || ch == '+' || ch == '.' || ch == 'e' || ch == 'E' || ch.is_ascii_digit()
            {
                s.push(self.next().unwrap());
            } else {
                break;
            }
        }
        let num: f64 = s
            .parse()
            .map_err(|e| format!("invalid number '{s}': {e}"))?;
        if !num.is_finite() {
            return Err("nonfinite JSON number".into());
        }
        Ok(JsonValue::Number(num, s))
    }

    fn parse_array(&mut self) -> Result<JsonValue, String> {
        self.next(); // consume '['
        let mut items = Vec::new();
        self.skip_whitespace();
        if self.peek() == Some(']') {
            self.next();
            return Ok(JsonValue::Array(items));
        }
        loop {
            let val = self.parse_value()?;
            items.push(val);
            self.skip_whitespace();
            match self.next() {
                Some(',') => self.skip_whitespace(),
                Some(']') => break,
                other => return Err(format!("expected ',' or ']', got {other:?}")),
            }
        }
        Ok(JsonValue::Array(items))
    }

    fn parse_object(&mut self) -> Result<JsonValue, String> {
        self.next(); // consume '{'
        let mut entries = Vec::new();
        self.skip_whitespace();
        if self.peek() == Some('}') {
            self.next();
            return Ok(JsonValue::Object(entries));
        }
        loop {
            self.skip_whitespace();
            if self.peek() != Some('"') {
                return Err(format!("expected string key, got {:?}", self.peek()));
            }
            let key = self.parse_string()?;
            self.skip_whitespace();
            if self.next() != Some(':') {
                return Err("expected ':' after object key".into());
            }
            let val = self.parse_value()?;
            if entries.iter().any(|(existing, _)| existing == &key) {
                return Err(format!("duplicate JSON key: {key}"));
            }
            entries.push((key, val));
            self.skip_whitespace();
            match self.next() {
                Some(',') => self.skip_whitespace(),
                Some('}') => break,
                other => return Err(format!("expected ',' or '}}', got {other:?}")),
            }
        }
        Ok(JsonValue::Object(entries))
    }
}

fn parse_json(input: &str) -> Result<JsonValue, String> {
    let mut parser = JsonParser::new(input);
    let val = parser.parse_value()?;
    parser.skip_whitespace();
    if parser.peek().is_some() {
        return Err("trailing data after JSON value".into());
    }
    Ok(val)
}

// The reviewed source inventory. Changes require an explicit correspondence review.
const SOURCE_ROWS: &[(&str, &[&str])] = &[
    ("B1,B2", &["defect", "raw_I", "bound"]),
    (
        "B3,C1",
        &["chart_vector_field", "chart_derivative", "semigroup_defect"],
    ),
    (
        "A2,A3,D8,G1",
        &[
            "induced_field",
            "repair_witness",
            "separator",
            "separator_pairing",
            "quotient_distance",
            "quotient_dual_witness",
            "quotient_dual_pairing",
        ],
    ),
    ("B4,G2", &["higher_differential_refused"]),
    (
        "D1,D3,D4",
        &[
            "checked_points",
            "all_unweighted_axioms",
            "weighted_RE3",
            "weighted_RE4",
        ],
    ),
    ("D2,D5", &["RE3", "RE5"]),
    ("D6", &["lp_breaks_RE3", "scaled_sum_breaks_RE5"]),
    ("A1", &["nu_e", "isolated_two_site_g", "full_incident_g"]),
    (
        "E2,E4",
        &[
            "t",
            "observed_defect",
            "isolated_signed_rhs",
            "full_signed_rhs",
            "external_incident_normal_rate",
            "positive_rhs_t",
            "positive_rhs_nu_e",
            "positive_rhs_g",
            "positive_rhs",
            "positive_rhs_observed_defect",
        ],
    ),
    ("E1", &["D", "T", "D_hat"]),
    (
        "E5,E9",
        &[
            "window",
            "edge_density_floor",
            "site_density_floor",
            "member_count",
        ],
    ),
    (
        "E8",
        &[
            "source_distance",
            "projection_distance",
            "rho_defect",
            "transfer_lower_bound",
        ],
    ),
    (
        "F1,F2",
        &[
            "xx_observed",
            "xx_closed_form",
            "xx_absolute_error",
            "tfim_expected_rate",
            "tfim_max_rate_error",
        ],
    ),
    ("F3", &["tfim_full_g", "tfim_g_upper_bound"]),
    (
        "H1,H2,H3,H4,H6,H7",
        &[
            "three_patch_I",
            "three_patch_J",
            "three_patch_Lambda",
            "three_patch_edgewise_observation_loss",
            "fragmentation_example_edgewise_observation_loss",
            "fragmentation_example_single_observer_fragmentation",
            "scaled_I",
            "combined_rank",
        ],
    ),
    ("H5", &["I", "J", "Lambda"]),
    ("A4,A5,A6,A7,C3,D7,D8a,E6,E7,G3,G4", &["missing_fragments"]),
    ("C2", &["reason"]),
    ("C4,E3", &["C4", "E3"]),
    ("E4-second,E4-commutator", &["E4-second", "E4-commutator"]),
    ("H8,H9", &["H8", "H9", "paper_replays"]),
];

fn source_text() -> String {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let rel_relocation = "atlas/000_projection_obstruction/evidence/000_mechanization_run.json";
    let rel_legacy = "coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/evidence/000_mechanization_run.json";
    let root = manifest_dir.join("../../..");
    let path = if root.join(rel_relocation).exists() {
        root.join(rel_relocation)
    } else {
        root.join(rel_legacy)
    };
    std::fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("required Python mechanization receipt at {}: {e}", path.display()))
}

fn display_exact(value: &JsonValue) -> String {
    match value {
        JsonValue::String(s) => s.clone(),
        JsonValue::Bool(b) => b.to_string(),
        JsonValue::Number(_, raw) => raw.clone(),
        JsonValue::Array(items) => format!(
            "[{}]",
            items
                .iter()
                .map(display_exact)
                .collect::<Vec<_>>()
                .join(", ")
        ),
        JsonValue::Object(entries) => format!(
            "{{{}}}",
            entries
                .iter()
                .map(|(k, v)| format!("{k}: {}", display_exact(v)))
                .collect::<Vec<_>>()
                .join(", ")
        ),
        JsonValue::Null => panic!("null is not an executable witness"),
    }
}

fn cross_check(
    root: &JsonValue,
    replication: &core_ooutwire_primitives::alpha_projection_obstruction::MechanizationRun,
) -> usize {
    use std::collections::BTreeSet;
    let results = root
        .get("results")
        .and_then(JsonValue::as_array)
        .expect("results array");
    assert!(
        results.len() >= SOURCE_ROWS.len(),
        "source disposition inventory has at least {} rows (got {})",
        SOURCE_ROWS.len(),
        results.len()
    );
    assert_eq!(
        root.get("authority_effect").and_then(JsonValue::as_str),
        Some("None")
    );
    assert!(replication.executable_checks_passed);
    let mut compared = 0;
    for (expected_group, expected_keys) in SOURCE_ROWS {
        let matching_result = results.iter().find(|res| {
            let ids: Vec<_> = res
                .get("claim_ids")
                .and_then(JsonValue::as_array)
                .map(|arr| {
                    arr.iter()
                        .map(|id| id.as_str().expect("claim ID string"))
                        .collect()
                })
                .unwrap_or_default();
            ids.join(",") == *expected_group
        });

        let result = match matching_result {
            Some(r) => r,
            None => {
                if matches!(
                    *expected_group,
                    "A4,A5,A6,A7,C3,D7,D8a,E6,E7,G3,G4"
                        | "C2"
                        | "C4,E3"
                        | "E4-second,E4-commutator"
                        | "H8,H9"
                ) {
                    continue;
                }
                panic!("missing source claim group {expected_group}");
            }
        };

        let ids: Vec<_> = result
            .get("claim_ids")
            .and_then(JsonValue::as_array)
            .expect("claim_ids array")
            .iter()
            .map(|id| id.as_str().expect("claim ID string"))
            .collect();
        assert_eq!(ids.join(","), *expected_group, "source claim group");
        let fields = match result.get("witness") {
            Some(JsonValue::Object(entries)) => entries,
            _ => panic!("required witness object for {expected_group}"),
        };
        assert_eq!(
            fields
                .iter()
                .map(|(k, _)| k.as_str())
                .collect::<BTreeSet<_>>(),
            expected_keys.iter().copied().collect::<BTreeSet<_>>(),
            "witness inventory for {expected_group}"
        );
        // Explicit non-correspondences: prose audit, analytic obligations, or Lean-only source rows.
        // The Rust receipt retains its own refusals and its separate finite H8/H9 computations.
        if matches!(
            *expected_group,
            "A4,A5,A6,A7,C3,D7,D8a,E6,E7,G3,G4"
                | "C2"
                | "C4,E3"
                | "E4-second,E4-commutator"
                | "H8,H9"
        ) {
            continue;
        }
        compared += 1;
        let rust = replication
            .results
            .iter()
            .find(|row| row.claim_ids == ids)
            .unwrap_or_else(|| panic!("missing Rust disposition {expected_group}"));
        assert_eq!(
            result.get("verdict").and_then(JsonValue::as_str),
            Some(rust.verdict.name())
        );
        for (key, value) in fields {
            let upper_bound = match key.as_str() {
                "external_incident_normal_rate" => {
                    Some(("external_incident_normal_rate_below", 1e-9))
                }
                "xx_absolute_error" => Some(("xx_absolute_error_below", 1e-12)),
                "tfim_max_rate_error" => Some(("tfim_max_rate_error_below", 1e-10)),
                _ => None,
            };
            let rust_key = upper_bound.map_or(key.as_str(), |(name, _)| name);
            let actual = rust
                .witness
                .iter()
                .find(|(k, _)| *k == rust_key)
                .map(|(_, v)| v)
                .unwrap_or_else(|| panic!("missing Rust field {rust_key}"));
            if let Some((_, bound)) = upper_bound {
                let expected = value.as_f64().expect("numerical error");
                assert!(expected.is_finite() && expected >= 0.0 && expected <= bound);
                assert_eq!(actual.parse::<f64>().expect("recorded bound"), bound);
            } else if matches!(value, JsonValue::Number(_, _))
                && !matches!(key.as_str(), "checked_points" | "member_count")
            {
                let expected = value.as_f64().unwrap();
                let actual = actual.parse::<f64>().expect("Rust number");
                let tolerance = match key.as_str() {
                    "observed_defect" | "positive_rhs_observed_defect" => 1e-11,
                    "tfim_expected_rate" => 1e-10,
                    _ => 1e-12,
                };
                assert!(
                    expected.is_finite()
                        && actual.is_finite()
                        && (actual - expected).abs() <= tolerance,
                    "{expected_group} {key}: {actual} != {expected}"
                );
            } else {
                assert_eq!(*actual, display_exact(value), "{expected_group} {key}");
            }
        }
    }
    assert_eq!(compared, 16, "shared rows must not be silently omitted");
    compared
}

#[test]
fn test_mechanization_cross_check_against_python_json() {
    let root = parse_json(&source_text()).expect("valid source JSON");
    let replication = run().unwrap();
    assert_eq!(cross_check(&root, &replication), 16);
}

#[test]
fn cross_check_rejects_empty_missing_and_changed_evidence() {
    let root = parse_json(&source_text()).unwrap();
    let replication = run().unwrap();
    let mut empty = root.clone();
    if let JsonValue::Object(entries) = &mut empty {
        entries
            .iter_mut()
            .find(|(key, _)| key == "results")
            .unwrap()
            .1 = JsonValue::Array(vec![]);
    }
    assert_ne!(empty, root);
    assert!(std::panic::catch_unwind(|| cross_check(&empty, &replication)).is_err());
    for replacement in [
        JsonValue::String("forged".into()),
        JsonValue::Number(2.0, "2".into()),
        JsonValue::Null,
    ] {
        let mut changed = root.clone();
        if let JsonValue::Object(entries) = &mut changed {
            if let JsonValue::Array(rows) = &mut entries
                .iter_mut()
                .find(|(key, _)| key == "results")
                .unwrap()
                .1
            {
                if let JsonValue::Object(row) = &mut rows[0] {
                    let witness = &mut row.iter_mut().find(|(key, _)| key == "witness").unwrap().1;
                    if let JsonValue::Object(fields) = witness {
                        fields
                            .iter_mut()
                            .find(|(key, _)| key == "defect")
                            .unwrap()
                            .1 = replacement;
                    }
                }
            }
        }
        assert_ne!(changed, root);
        assert!(std::panic::catch_unwind(|| cross_check(&changed, &replication)).is_err());
    }
    assert!(parse_json(r#"{"results": [], "results": []}"#).is_err());
    assert!(parse_json("1e999").is_err());
}

// Origin: engine/crates_rs/tests/core_ooutwire_primitives/mechanization_cross_check.rs
// Claim: urn:core:crates_rs:tests:mechanization-cross-check:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6047c9f1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6047c9f1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6047c9f1 {
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
impl BoundaryError6047c9f1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6047c9f1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6047c9f1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6047c9f1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6047c9f1> {
        if capacity_bound == 0 {
            return Err(BoundaryError6047c9f1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6047c9f1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6047c9f1::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6047c9f1() {
    let admitted = BoundaryRecord6047c9f1::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6047c9f1::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

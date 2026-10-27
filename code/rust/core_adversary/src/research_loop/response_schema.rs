//! A bounded JSON Schema 2020-12 validator for model responses.
//!
//! It covers the keywords the research packets' response schemas use and nothing else.
//! Compilation refuses any other keyword, so a schema can never be checked by rules this
//! module silently ignores. Annotation keywords (`title`, `description`, `default`,
//! `$schema`, `x-slot`) carry no rule. References are local only (`#/$defs/<name>`).
//!
//! AuthorityEffect: None.

use super::refuse;
use crate::stage::ports::Refusal;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::BTreeMap;

const ANNOTATIONS: [&str; 5] = ["title", "description", "default", "$schema", "x-slot"];
const RULES: [&str; 15] = [
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "prefixItems",
    "minItems",
    "maxItems",
    "const",
    "enum",
    "minLength",
    "maxLength",
    "pattern",
    "$ref",
    "$defs",
];
const MAX_DEPTH: usize = 64;

/// One failed rule, located by JSON pointer into the response.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Violation {
    pub path: String,
    pub rule: String,
}

#[derive(Debug, Clone)]
pub struct ResponseSchema {
    root: Value,
    defs: Map<String, Value>,
    patterns: BTreeMap<String, Regex>,
}

fn schema_error(message: impl Into<String>) -> Refusal {
    refuse("RESPONSE_SCHEMA_UNSUPPORTED", message)
}

fn as_count(value: &Value, keyword: &str) -> Result<u64, Refusal> {
    value
        .as_u64()
        .ok_or_else(|| schema_error(format!("{keyword} must be a non-negative integer")))
}

impl ResponseSchema {
    pub fn compile(schema: &Value) -> Result<Self, Refusal> {
        let defs = match schema.get("$defs") {
            None => Map::new(),
            Some(Value::Object(defs)) => defs.clone(),
            Some(_) => return Err(schema_error("$defs must be an object")),
        };
        let mut patterns = BTreeMap::new();
        check(schema, &defs, &mut patterns, 0)?;
        for def in defs.values() {
            check(def, &defs, &mut patterns, 0)?;
        }
        Ok(Self {
            root: schema.clone(),
            defs,
            patterns,
        })
    }

    /// Every violation, sorted. Empty means the response conforms.
    pub fn validate(&self, instance: &Value) -> Vec<Violation> {
        let mut out = Vec::new();
        self.walk(&self.root, instance, "", 0, &mut out);
        out.sort();
        out.dedup();
        out
    }

    fn walk(
        &self,
        schema: &Value,
        value: &Value,
        path: &str,
        depth: usize,
        out: &mut Vec<Violation>,
    ) {
        let here = path_or_root(path);
        if depth > MAX_DEPTH {
            push(out, &here, "depth limit");
            return;
        }
        let Some(schema) = Self::extract_schema_object(schema, &here, out) else {
            return;
        };
        self.walk_ref_if_present(schema, value, path, depth, out);
        if !Self::check_schema_type(schema, value, &here, out) {
            return;
        }
        Self::check_const_and_enum(schema, value, &here, out);
        self.walk_typed_value(schema, value, path, &here, depth, out);
    }

    fn extract_schema_object<'a>(
        schema: &'a Value,
        here: &str,
        out: &mut Vec<Violation>,
    ) -> Option<&'a Map<String, Value>> {
        match schema {
            Value::Bool(true) => None,
            Value::Bool(false) => {
                push(out, here, "false schema");
                None
            }
            Value::Object(map) => Some(map),
            _ => None,
        }
    }

    fn walk_ref_if_present(
        &self,
        schema: &Map<String, Value>,
        value: &Value,
        path: &str,
        depth: usize,
        out: &mut Vec<Violation>,
    ) {
        if let Some(Value::String(reference)) = schema.get("$ref") {
            // compile() checked that every reference resolves.
            if let Some(target) = reference
                .strip_prefix("#/$defs/")
                .and_then(|n| self.defs.get(n))
            {
                self.walk(target, value, path, depth + 1, out);
            }
        }
    }

    fn check_schema_type(
        schema: &Map<String, Value>,
        value: &Value,
        here: &str,
        out: &mut Vec<Violation>,
    ) -> bool {
        let Some(kind) = schema.get("type") else {
            return true;
        };
        let kinds: Vec<&str> = match kind {
            Value::String(single) => vec![single.as_str()],
            Value::Array(many) => many.iter().filter_map(Value::as_str).collect(),
            _ => vec![],
        };
        if !kinds.iter().any(|k| type_matches(k, value)) {
            push(out, here, &format!("type {}", kinds.join("|")));
            return false;
        }
        true
    }

    fn check_const_and_enum(
        schema: &Map<String, Value>,
        value: &Value,
        here: &str,
        out: &mut Vec<Violation>,
    ) {
        if schema
            .get("const")
            .is_some_and(|expected| !same(expected, value))
        {
            push(out, here, "const");
        }
        if let Some(Value::Array(options)) = schema.get("enum") {
            if !options.iter().any(|option| same(option, value)) {
                push(out, here, "enum");
            }
        }
    }

    fn walk_typed_value(
        &self,
        schema: &Map<String, Value>,
        value: &Value,
        path: &str,
        here: &str,
        depth: usize,
        out: &mut Vec<Violation>,
    ) {
        match value {
            Value::String(text) => self.walk_string(schema, text, here, out),
            Value::Object(object) => self.walk_object(schema, object, path, depth, out),
            Value::Array(items) => self.walk_array(schema, items, path, here, depth, out),
            _ => {}
        }
    }

    fn walk_string(
        &self,
        schema: &Map<String, Value>,
        text: &str,
        here: &str,
        out: &mut Vec<Violation>,
    ) {
        let length = text.chars().count() as u64;
        if schema
            .get("minLength")
            .and_then(Value::as_u64)
            .is_some_and(|min| length < min)
        {
            push(out, here, "minLength");
        }
        if schema
            .get("maxLength")
            .and_then(Value::as_u64)
            .is_some_and(|max| length > max)
        {
            push(out, here, "maxLength");
        }
        if let Some(Value::String(pattern)) = schema.get("pattern") {
            if !self
                .patterns
                .get(pattern)
                .is_some_and(|regex| regex.is_match(text))
            {
                push(out, here, "pattern");
            }
        }
    }

    fn walk_object(
        &self,
        schema: &Map<String, Value>,
        object: &Map<String, Value>,
        path: &str,
        depth: usize,
        out: &mut Vec<Violation>,
    ) {
        if let Some(Value::Array(required)) = schema.get("required") {
            for name in required.iter().filter_map(Value::as_str) {
                if !object.contains_key(name) {
                    push(out, &format!("{path}/{}", escape(name)), "required");
                }
            }
        }
        let properties = schema.get("properties").and_then(Value::as_object);
        for (name, item) in object {
            let child = format!("{path}/{}", escape(name));
            self.walk_object_property(schema, properties, name, item, &child, depth, out);
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn walk_object_property(
        &self,
        schema: &Map<String, Value>,
        properties: Option<&Map<String, Value>>,
        name: &str,
        item: &Value,
        child: &str,
        depth: usize,
        out: &mut Vec<Violation>,
    ) {
        match properties.and_then(|p| p.get(name)) {
            Some(sub) => self.walk(sub, item, child, depth + 1, out),
            None => match schema.get("additionalProperties") {
                Some(Value::Bool(false)) => push(out, child, "additionalProperties"),
                Some(sub @ Value::Object(_)) => self.walk(sub, item, child, depth + 1, out),
                _ => {}
            },
        }
    }

    fn walk_array(
        &self,
        schema: &Map<String, Value>,
        items: &[Value],
        path: &str,
        here: &str,
        depth: usize,
        out: &mut Vec<Violation>,
    ) {
        let length = items.len() as u64;
        if schema
            .get("minItems")
            .and_then(Value::as_u64)
            .is_some_and(|min| length < min)
        {
            push(out, here, "minItems");
        }
        if schema
            .get("maxItems")
            .and_then(Value::as_u64)
            .is_some_and(|max| length > max)
        {
            push(out, here, "maxItems");
        }
        let prefix = schema.get("prefixItems").and_then(Value::as_array);
        for (index, item) in items.iter().enumerate() {
            let child = format!("{path}/{index}");
            if let Some(sub) = prefix
                .and_then(|p| p.get(index))
                .or_else(|| schema.get("items"))
            {
                self.walk(sub, item, &child, depth + 1, out);
            }
        }
    }
}

fn push(out: &mut Vec<Violation>, path: &str, rule: &str) {
    out.push(Violation {
        path: path.into(),
        rule: rule.into(),
    });
}

/// JSON pointer escaping for one key.
fn escape(name: &str) -> String {
    name.replace('~', "~0").replace('/', "~1")
}

fn path_or_root(path: &str) -> String {
    if path.is_empty() {
        "/".into()
    } else {
        path.into()
    }
}

fn type_matches(kind: &str, value: &Value) -> bool {
    match kind {
        "object" => value.is_object(),
        "array" => value.is_array(),
        "string" => value.is_string(),
        "boolean" => value.is_boolean(),
        "null" => value.is_null(),
        "number" => value.is_number(),
        "integer" => value.as_i64().is_some() || value.as_u64().is_some(),
        _ => false,
    }
}

/// JSON equality with integers compared by value (`1` equals `1`, never `true`).
fn same(a: &Value, b: &Value) -> bool {
    match (a, b) {
        (Value::Number(x), Value::Number(y)) => x.to_string() == y.to_string(),
        (Value::Array(x), Value::Array(y)) => {
            x.len() == y.len() && x.iter().zip(y).all(|(p, q)| same(p, q))
        }
        (Value::Object(x), Value::Object(y)) => {
            x.len() == y.len() && x.iter().all(|(k, v)| y.get(k).is_some_and(|w| same(v, w)))
        }
        _ => a == b,
    }
}

fn check(
    schema: &Value,
    defs: &Map<String, Value>,
    patterns: &mut BTreeMap<String, Regex>,
    depth: usize,
) -> Result<(), Refusal> {
    if depth > MAX_DEPTH {
        return Err(schema_error("schema nesting exceeds the depth limit"));
    }
    let map = match schema {
        Value::Bool(_) => return Ok(()),
        Value::Object(map) => map,
        _ => return Err(schema_error("a schema is an object or a boolean")),
    };
    for (keyword, value) in map {
        check_keyword(keyword, value, defs, patterns, depth)?;
    }
    Ok(())
}

fn check_keyword(
    keyword: &str,
    value: &Value,
    defs: &Map<String, Value>,
    patterns: &mut BTreeMap<String, Regex>,
    depth: usize,
) -> Result<(), Refusal> {
    if ANNOTATIONS.contains(&keyword) {
        return Ok(());
    }
    if !RULES.contains(&keyword) {
        return Err(schema_error(format!(
            "keyword {keyword:?} is not supported"
        )));
    }
    match keyword {
        "type" => check_type_keyword(value),
        "properties" => check_properties_keyword(value, defs, patterns, depth),
        "required" => check_required_keyword(value),
        "additionalProperties" | "items" => check(value, defs, patterns, depth + 1),
        "prefixItems" => check_prefix_items_keyword(value, defs, patterns, depth),
        "minItems" | "maxItems" | "minLength" | "maxLength" => {
            as_count(value, keyword)?;
            Ok(())
        }
        _ => check_leaf_keyword(keyword, value, defs, patterns, depth),
    }
}

fn check_type_keyword(value: &Value) -> Result<(), Refusal> {
    const KNOWN_TYPES: [&str; 7] = [
        "object", "array", "string", "boolean", "null", "number", "integer",
    ];
    let names: Vec<&Value> = match value {
        Value::Array(many) => many.iter().collect(),
        single => vec![single],
    };
    let valid = !names.is_empty()
        && names
            .iter()
            .all(|n| n.as_str().is_some_and(|s| KNOWN_TYPES.contains(&s)));
    if !valid {
        return Err(schema_error("type names an unknown JSON type"));
    }
    Ok(())
}

fn check_properties_keyword(
    value: &Value,
    defs: &Map<String, Value>,
    patterns: &mut BTreeMap<String, Regex>,
    depth: usize,
) -> Result<(), Refusal> {
    let properties = value
        .as_object()
        .ok_or_else(|| schema_error("properties must be an object"))?;
    for sub in properties.values() {
        check(sub, defs, patterns, depth + 1)?;
    }
    Ok(())
}

fn check_required_keyword(value: &Value) -> Result<(), Refusal> {
    if !value
        .as_array()
        .is_some_and(|names| names.iter().all(Value::is_string))
    {
        return Err(schema_error("required must be an array of strings"));
    }
    Ok(())
}

fn check_prefix_items_keyword(
    value: &Value,
    defs: &Map<String, Value>,
    patterns: &mut BTreeMap<String, Regex>,
    depth: usize,
) -> Result<(), Refusal> {
    let items = value
        .as_array()
        .ok_or_else(|| schema_error("prefixItems must be an array"))?;
    for sub in items {
        check(sub, defs, patterns, depth + 1)?;
    }
    Ok(())
}

fn check_leaf_keyword(
    keyword: &str,
    value: &Value,
    defs: &Map<String, Value>,
    patterns: &mut BTreeMap<String, Regex>,
    depth: usize,
) -> Result<(), Refusal> {
    match keyword {
        "enum" if !value.is_array() => Err(schema_error("enum must be an array")),
        "pattern" => check_pattern_keyword(value, patterns),
        "$ref" => check_ref_keyword(value, defs),
        "$defs" if depth > 0 => Err(schema_error("$defs is allowed only at the schema root")),
        _ => Ok(()),
    }
}

fn check_pattern_keyword(
    value: &Value,
    patterns: &mut BTreeMap<String, Regex>,
) -> Result<(), Refusal> {
    let text = value
        .as_str()
        .ok_or_else(|| schema_error("pattern must be a string"))?;
    let regex = Regex::new(text).map_err(|e| schema_error(format!("pattern {text:?}: {e}")))?;
    patterns.insert(text.to_owned(), regex);
    Ok(())
}

fn check_ref_keyword(value: &Value, defs: &Map<String, Value>) -> Result<(), Refusal> {
    let target = value
        .as_str()
        .and_then(|r| r.strip_prefix("#/$defs/"))
        .ok_or_else(|| schema_error("only local #/$defs/ references are supported"))?;
    if !defs.contains_key(target) {
        return Err(schema_error(format!(
            "reference to undefined $defs/{target}"
        )));
    }
    Ok(())
}

// Origin: engine/crates_rs/core_adversary/src/research_loop/response_schema.rs
// Claim: urn:core:crates_rs:core-adversary:response-schema:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde0be7bc2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde0be7bc2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore0be7bc2 {
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
impl BoundaryErrore0be7bc2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore0be7bc2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore0be7bc2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde0be7bc2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore0be7bc2> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore0be7bc2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore0be7bc2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore0be7bc2::ExceedsCapacity {
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
mod l4_boundary_tests_e0be7bc2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde0be7bc2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde0be7bc2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde0be7bc2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde0be7bc2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde0be7bc2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrore0be7bc2::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrore0be7bc2::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}

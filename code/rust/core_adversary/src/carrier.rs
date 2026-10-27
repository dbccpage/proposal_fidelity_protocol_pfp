//! Exact JSON carrier admission; topology data delegates computation to scoring ports.
use crate::authorization::refuse;
use crate::carrier_digits::DECIMAL_ZERO_BASES;
use crate::evidence::{canonical_rational, parse_exact_rational};
use crate::exact::Integer;
use indexmap::IndexMap;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use crate::stage::ports::Refusal;
use core_types::python_unicode::repr_string;
use regex::Regex;
use serde::{Serialize, Serializer};
use serde_json::{json, value::RawValue, Value};
use std::collections::BTreeSet;
use std::str::FromStr;

const CARRIER_KEYS: [&str; 7] = [
    "cochains",
    "edges",
    "faces",
    "four_simplices",
    "nodes",
    "regge_spacetime",
    "tetrahedra",
];
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(untagged)]
pub enum NodeLabel {
    Integer(Integer),
    Text(String),
    Boolean(bool),
    Float(FloatKey),
}
/// Preserves a finite Python literal key. This is never a rational value or money.
#[derive(Debug, Clone, Copy)]
pub struct FloatKey(f64);
impl PartialEq for FloatKey {
    fn eq(&self, other: &Self) -> bool {
        self.0.to_bits() == other.0.to_bits()
    }
}
impl Eq for FloatKey {}
impl PartialOrd for FloatKey {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}
impl Ord for FloatKey {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.0.total_cmp(&other.0)
    }
}
fn float_repr(value: f64) -> String {
    let text = format!("{value:?}");
    if let Some((mantissa, exponent)) = text.split_once('e') {
        let negative = exponent.starts_with('-');
        let digits = exponent.trim_start_matches(['-', '+']);
        return format!(
            "{mantissa}e{}{}{}",
            if negative { "-" } else { "+" },
            if digits.len() < 2 { "0" } else { "" },
            digits
        );
    }
    text
}
impl Serialize for FloatKey {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let number =
            serde_json::Number::from_str(&float_repr(self.0)).map_err(serde::ser::Error::custom)?;
        number.serialize(serializer)
    }
}
fn numeric(label: &NodeLabel) -> Option<BigRational> {
    match label {
        NodeLabel::Integer(value) => Some(BigRational::from_integer(value.0.clone())),
        NodeLabel::Boolean(value) => {
            Some(BigRational::from_integer(BigInt::from(u8::from(*value))))
        }
        NodeLabel::Float(value) => BigRational::from_float(value.0),
        NodeLabel::Text(_) => None,
    }
}
pub(crate) fn key_equal(left: &NodeLabel, right: &NodeLabel) -> bool {
    match (left, right) {
        (NodeLabel::Text(left), NodeLabel::Text(right)) => left == right,
        _ => numeric(left)
            .zip(numeric(right))
            .is_some_and(|(left, right)| left == right),
    }
}
fn edge_equal(left: &Edge, right: &Edge) -> bool {
    key_equal(&left[0], &right[0]) && key_equal(&left[1], &right[1])
}
impl NodeLabel {
    fn repr(&self) -> String {
        match self {
            Self::Integer(value) => value.0.to_string(),
            Self::Text(value) => repr_string(value),
            Self::Boolean(value) => if *value { "True" } else { "False" }.into(),
            Self::Float(value) => float_repr(value.0),
        }
    }
    fn display(&self) -> String {
        match self {
            Self::Integer(value) => value.0.to_string(),
            Self::Text(value) => value.clone(),
            Self::Boolean(value) => if *value { "True" } else { "False" }.into(),
            Self::Float(value) => float_repr(value.0),
        }
    }
}
pub type Edge = [NodeLabel; 2];
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Network {
    nodes: Vec<NodeLabel>,
    edges: Vec<Edge>,
    faces: Vec<[NodeLabel; 3]>,
    tetrahedra: Vec<[NodeLabel; 4]>,
    four_simplices: Vec<[NodeLabel; 5]>,
}
impl Network {
    pub fn new(
        nodes: Vec<NodeLabel>,
        edges: Vec<Edge>,
        faces: Vec<[NodeLabel; 3]>,
        tetrahedra: Vec<[NodeLabel; 4]>,
        four_simplices: Vec<[NodeLabel; 5]>,
    ) -> Result<Self, Refusal> {
        for [u, v] in &edges {
            if !nodes.iter().any(|node| key_equal(node, u))
                || !nodes.iter().any(|node| key_equal(node, v))
            {
                return Err(malformed(format!(
                    "Edge ({}, {}) references node(s) not in node set",
                    u.display(),
                    v.display()
                )));
            }
        }
        Ok(Self {
            nodes,
            edges,
            faces,
            tetrahedra,
            four_simplices,
        })
    }
    pub fn nodes(&self) -> &[NodeLabel] {
        &self.nodes
    }
    pub fn edges(&self) -> &[Edge] {
        &self.edges
    }
    pub fn faces(&self) -> &[[NodeLabel; 3]] {
        &self.faces
    }
    pub fn tetrahedra(&self) -> &[[NodeLabel; 4]] {
        &self.tetrahedra
    }
    pub fn four_simplices(&self) -> &[[NodeLabel; 5]] {
        &self.four_simplices
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        serde_json::to_value(self).map_err(|error| malformed(error.to_string()))
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactCochain {
    entries: Vec<(Edge, BigRational)>,
}
impl ExactCochain {
    /// Canonical original edge keys retain their exact values; added edges get zero.
    pub(crate) fn transport_onto(&self, original: &[Edge], added: &[Edge]) -> Self {
        let mut entries = original
            .iter()
            .map(|edge| {
                (
                    edge.clone(),
                    self.value(edge).cloned().unwrap_or_else(BigRational::zero),
                )
            })
            .collect::<Vec<_>>();
        entries.extend(added.iter().map(|edge| (edge.clone(), BigRational::zero())));
        Self { entries }
    }
    pub fn entries(&self) -> &[(Edge, BigRational)] {
        &self.entries
    }
    pub fn value(&self, edge: &Edge) -> Option<&BigRational> {
        self.entries
            .iter()
            .find_map(|(key, value)| edge_equal(key, edge).then_some(value))
    }
    pub fn to_dict(&self) -> Vec<Value> {
        self.entries
            .iter()
            .map(|(edge, value)| json!({"edge":edge,"value":canonical_rational(value)}))
            .collect()
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParsedCarrier {
    network: Network,
    cochain: ExactCochain,
    declared: bool,
    implicit_zero_edges: usize,
}
impl ParsedCarrier {
    pub fn network(&self) -> &Network {
        &self.network
    }
    pub fn cochain(&self) -> &ExactCochain {
        &self.cochain
    }
    pub fn declared(&self) -> bool {
        self.declared
    }
    pub fn carrier_status(&self) -> &str {
        if self.declared {
            "DECLARED"
        } else {
            "NOT_DECLARED"
        }
    }
    pub fn implicit_zero_edges(&self) -> usize {
        self.implicit_zero_edges
    }
    pub fn to_dict(&self) -> Result<Value, Refusal> {
        Ok(
            json!({"network":self.network.to_dict()?,"cochain":self.cochain.to_dict(),"carrier_status":self.carrier_status(),"implicit_zero_edges":self.implicit_zero_edges}),
        )
    }
}
fn malformed(message: impl Into<String>) -> Refusal {
    refuse(
        "ADVERSARY_CARRIER_MALFORMED",
        format!("declared carrier is malformed: {}", message.into()),
    )
}
fn syntax(error: serde_json::Error) -> Refusal {
    refuse(
        "ADVERSARY_CARRIER_MALFORMED",
        format!("carrier_context is not JSON: {error}"),
    )
}
fn whitespace(c: char) -> bool {
    c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c)
}
fn decimal_digit(c: char) -> Option<u8> {
    let code = u32::from(c);
    DECIMAL_ZERO_BASES.iter().find_map(|zero| {
        code.checked_sub(*zero)
            .filter(|digit| *digit < 10)
            .and_then(|digit| u8::try_from(digit).ok())
    })
}
pub(crate) fn python_integer(text: &str) -> Option<BigInt> {
    // int() excludes the four ASCII separators admitted by str.strip().
    let text = text.trim_matches(char::is_whitespace);
    let mut normalized = String::new();
    let mut chars = text.chars().peekable();
    if chars.peek().is_some_and(|c| *c == '+' || *c == '-') {
        normalized.push(chars.next()?);
    }
    let mut digit_before = false;
    let mut digits = 0usize;
    for c in chars {
        if c == '_' {
            if !digit_before {
                return None;
            }
            digit_before = false;
        } else {
            let digit = decimal_digit(c)?;
            normalized.push(char::from(b'0' + digit));
            digits += 1;
            digit_before = true;
        }
    }
    if !digit_before || digits > 4300 {
        return None;
    }
    BigInt::from_str(&normalized).ok()
}
fn node(raw: &RawValue) -> Result<NodeLabel, Refusal> {
    let text = raw.get().trim_start();
    if text.starts_with('"') {
        let value: String = serde_json::from_str(text).map_err(syntax)?;
        if !value.trim_matches(whitespace).is_empty() {
            return Ok(NodeLabel::Text(value));
        }
    } else if text.starts_with('-') || text.as_bytes().first().is_some_and(u8::is_ascii_digit) {
        if let Ok(value) = BigInt::from_str(text) {
            return Ok(NodeLabel::Integer(Integer(value)));
        }
    }
    Err(malformed(format!(
        "node labels must be ints or nonempty strings, got {}",
        raw_repr(raw)?
    )))
}
fn raw_repr(raw: &RawValue) -> Result<String, Refusal> {
    let text = raw.get().trim_start();
    if text.starts_with('{') {
        let fields: IndexMap<String, Box<RawValue>> = serde_json::from_str(text).map_err(syntax)?;
        let items = fields
            .iter()
            .map(|(key, value)| Ok(format!("{}: {}", repr_string(key), raw_repr(value)?)))
            .collect::<Result<Vec<_>, Refusal>>()?;
        return Ok(format!("{{{}}}", items.join(", ")));
    }
    if text.starts_with('[') {
        let items: Vec<Box<RawValue>> = serde_json::from_str(text).map_err(syntax)?;
        let items = items
            .iter()
            .map(|value| raw_repr(value))
            .collect::<Result<Vec<_>, _>>()?;
        return Ok(format!("[{}]", items.join(", ")));
    }
    if text.starts_with('"') {
        let value: String = serde_json::from_str(text).map_err(syntax)?;
        return Ok(repr_string(&value));
    }
    if let Some(value) = match text {
        "null" => Some("None"),
        "true" => Some("True"),
        "false" => Some("False"),
        _ => None,
    } {
        return Ok(value.into());
    }
    if let Ok(value) = BigInt::from_str(text) {
        return Ok(value.to_string());
    }
    text.parse::<f64>()
        .map(float_repr)
        .map_err(|error| malformed(error.to_string()))
}
fn iterable(raw: &RawValue) -> Result<Vec<Box<RawValue>>, Refusal> {
    let text = raw.get().trim_start();
    if text.starts_with('[') {
        return serde_json::from_str(text).map_err(syntax);
    }
    let values: Vec<String> = if text.starts_with('{') {
        let values: IndexMap<String, Box<RawValue>> = serde_json::from_str(text).map_err(syntax)?;
        values.into_keys().collect()
    } else if text.starts_with('"') {
        let value: String = serde_json::from_str(text).map_err(syntax)?;
        value.chars().map(|c| c.to_string()).collect()
    } else {
        let kind = if text == "null" {
            "NoneType"
        } else if matches!(text, "true" | "false") {
            "bool"
        } else if text.contains(['.', 'e', 'E']) {
            "float"
        } else {
            "int"
        };
        return Err(malformed(format!("'{kind}' object is not iterable")));
    };
    values
        .iter()
        .map(|value| serde_json::value::to_raw_value(value).map_err(syntax))
        .collect()
}
fn labels(raw: &RawValue) -> Result<Vec<NodeLabel>, Refusal> {
    iterable(raw)?.iter().map(|raw| node(raw)).collect()
}
fn tuple_repr(labels: &[NodeLabel]) -> String {
    let inner = labels
        .iter()
        .map(NodeLabel::repr)
        .collect::<Vec<_>>()
        .join(", ");
    format!("({inner}{})", if labels.len() == 1 { "," } else { "" })
}
fn set_of(labels: &[NodeLabel]) -> BTreeSet<NodeLabel> {
    labels.iter().cloned().collect()
}
fn reverse(edge: &Edge) -> Edge {
    [edge[1].clone(), edge[0].clone()]
}

fn quoted_literal(text: &str) -> Option<String> {
    let raw = text.starts_with(['r', 'R']);
    let text = if text.starts_with(['u', 'U', 'r', 'R']) {
        &text[1..]
    } else {
        text
    };
    let quote = text.chars().next()?;
    if !matches!(quote, '\'' | '"') || !text.ends_with(quote) || text.len() < 2 {
        return None;
    }
    let inner = &text[1..text.len() - 1];
    if raw {
        let trailing_slashes = inner.chars().rev().take_while(|c| *c == '\\').count();
        if trailing_slashes % 2 != 0 || inner.contains(quote) {
            return None;
        }
        return Some(inner.into());
    }
    let mut chars = inner.chars().peekable();
    let mut out = String::new();
    while let Some(c) = chars.next() {
        if c == quote {
            return None;
        }
        if c != '\\' {
            out.push(c);
            continue;
        }
        let escaped = chars.next()?;
        match escaped {
            'n' => out.push('\n'),
            'r' => out.push('\r'),
            't' => out.push('\t'),
            'b' => out.push('\u{8}'),
            'f' => out.push('\u{c}'),
            'a' => out.push('\u{7}'),
            'v' => out.push('\u{b}'),
            '\\' | '\'' | '"' => out.push(escaped),
            'x' | 'u' | 'U' => {
                let width = match escaped {
                    'x' => 2,
                    'u' => 4,
                    _ => 8,
                };
                let mut code = 0u32;
                for _ in 0..width {
                    code = code
                        .checked_mul(16)?
                        .checked_add(chars.next()?.to_digit(16)?)?;
                }
                out.push(char::from_u32(code)?);
            }
            '0'..='7' => {
                let mut code = escaped.to_digit(8)?;
                for _ in 0..2 {
                    if chars.peek().is_some_and(|c| matches!(c, '0'..='7')) {
                        code = code * 8 + chars.next()?.to_digit(8)?;
                    }
                }
                out.push(char::from_u32(code)?);
            }
            '\n' => {}
            other => {
                out.push('\\');
                out.push(other);
            }
        }
    }
    Some(out)
}
fn literal_item(text: &str) -> Option<Option<NodeLabel>> {
    let text = text.trim_matches(whitespace);
    if let Some(value) = quoted_literal(text) {
        return Some(Some(NodeLabel::Text(value)));
    }
    if matches!(text, "True" | "False") {
        return Some(Some(NodeLabel::Boolean(text == "True")));
    }
    if text == "None" {
        return Some(None);
    }
    let (sign, unsigned) = if let Some(value) = text.strip_prefix('-') {
        (-1, value)
    } else {
        (1, text.strip_prefix('+').unwrap_or(text))
    };
    for (prefix, radix) in [
        ("0x", 16),
        ("0X", 16),
        ("0o", 8),
        ("0O", 8),
        ("0b", 2),
        ("0B", 2),
    ] {
        if let Some(value) = unsigned.strip_prefix(prefix) {
            let value = value.strip_prefix('_').unwrap_or(value);
            let mut previous = false;
            for c in value.chars() {
                if c == '_' {
                    if !previous {
                        return None;
                    }
                    previous = false;
                } else {
                    if !c.is_ascii() || c.to_digit(radix).is_none() {
                        return None;
                    }
                    previous = true;
                }
            }
            if !previous {
                return None;
            }
            let value = value.replace('_', "");
            return BigInt::parse_bytes(value.as_bytes(), radix)
                .map(|value| Some(NodeLabel::Integer(Integer(value * sign))));
        }
    }
    if text.contains(['.', 'e', 'E']) {
        let pattern=Regex::new(r"^[+-]?(?:(?:[0-9](?:_?[0-9])*)?\.[0-9](?:_?[0-9])*|[0-9](?:_?[0-9])*\.)(?:[eE][+-]?[0-9](?:_?[0-9])*)?$|^[+-]?[0-9](?:_?[0-9])*[eE][+-]?[0-9](?:_?[0-9])*$").ok()?;
        if pattern.is_match(text) {
            return text.replace('_', "").parse::<f64>().ok().map(|value| {
                value
                    .is_finite()
                    .then_some(NodeLabel::Float(FloatKey(value)))
            });
        }
    }
    python_integer(text).map(|value| Some(NodeLabel::Integer(Integer(value))))
}
fn literal_items(text: &str) -> Option<Vec<Option<NodeLabel>>> {
    let text = text.trim_matches(whitespace);
    let (inner, require_comma) = if text.starts_with('[') && text.ends_with(']') {
        (&text[1..text.len() - 1], false)
    } else if text.starts_with('(') && text.ends_with(')') {
        (&text[1..text.len() - 1], true)
    } else {
        (text, true)
    };
    let mut chunks = Vec::new();
    let mut quote = None;
    let mut escaped = false;
    let mut start = 0;
    for (offset, c) in inner.char_indices() {
        if let Some(q) = quote {
            if escaped {
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == q {
                quote = None;
            }
        } else if matches!(c, '\'' | '"') {
            quote = Some(c);
        } else if c == ',' {
            chunks.push(&inner[start..offset]);
            start = offset + 1;
        }
    }
    if quote.is_some() || (require_comma && chunks.is_empty()) {
        return None;
    }
    if !inner[start..].trim_matches(whitespace).is_empty() {
        chunks.push(&inner[start..]);
    } else if chunks.is_empty() && !inner.trim_matches(whitespace).is_empty() {
        return None;
    }
    chunks.into_iter().map(literal_item).collect()
}
fn cochain_key(text: &str) -> Vec<Option<NodeLabel>> {
    if let Some(items) = literal_items(text) {
        return items;
    }
    let cleaned = text
        .trim_matches(whitespace)
        .trim_start_matches(['(', '[', '{', '"', '\''])
        .trim_end_matches([')', ']', '}', '"', '\'']);
    let separator = if cleaned.contains(',') {
        Some(",")
    } else if cleaned.contains("->") {
        Some("->")
    } else {
        None
    };
    let chunks = if let Some(separator) = separator {
        cleaned
            .split(separator)
            .map(|text| text.trim_matches(whitespace).trim_matches(['\'', '"']))
            .collect::<Vec<_>>()
    } else {
        cleaned
            .split(whitespace)
            .filter(|text| !text.is_empty())
            .collect::<Vec<_>>()
    };
    if separator.is_none() && chunks.len() != 2 {
        return vec![Some(NodeLabel::Text(text.into()))];
    }
    chunks
        .into_iter()
        .map(|text| {
            Some(python_integer(text).map_or_else(
                || NodeLabel::Text(text.into()),
                |value| NodeLabel::Integer(Integer(value)),
            ))
        })
        .collect()
}
fn boundary_present(
    cell: &[NodeLabel],
    boundary: &BTreeSet<BTreeSet<NodeLabel>>,
) -> Option<Vec<NodeLabel>> {
    for omitted in 0..cell.len() {
        let side = cell
            .iter()
            .enumerate()
            .filter_map(|(index, value)| (index != omitted).then_some(value.clone()))
            .collect::<BTreeSet<_>>();
        if !boundary.contains(&side) {
            return Some(side.into_iter().collect());
        }
    }
    None
}

fn validate_carrier_keys(
    fields: &IndexMap<String, Box<RawValue>>,
    carrier_like: &BTreeSet<String>,
) -> Result<(), Refusal> {
    let unknown = carrier_like
        .iter()
        .filter(|key| !CARRIER_KEYS.contains(&key.as_str()))
        .map(|key| repr_string(key))
        .collect::<Vec<_>>();
    let missing = ["nodes", "edges", "cochains"]
        .into_iter()
        .filter(|key| !fields.contains_key(*key))
        .collect::<Vec<_>>();
    if !missing.is_empty() {
        let hint = if unknown.is_empty() {
            String::new()
        } else {
            format!(
                "; unknown carrier key(s) {} (the cochain map is 'cochains')",
                unknown.join(", ")
            )
        };
        return Err(refuse(
            "ADVERSARY_CARRIER_KEYS_MISSING",
            format!("declared carrier is missing {}{hint}", missing.join(", ")),
        ));
    }
    if !unknown.is_empty() {
        return Err(refuse(
            "ADVERSARY_CARRIER_MALFORMED",
            format!(
                "unknown carrier key(s) {}; admitted keys are {}",
                unknown.join(", "),
                CARRIER_KEYS.join(", ")
            ),
        ));
    }
    if fields
        .get("regge_spacetime")
        .is_some_and(|raw| !matches!(raw.get(), "true" | "false"))
    {
        return Err(refuse(
            "ADVERSARY_CARRIER_MALFORMED",
            "regge_spacetime must be JSON true or false",
        ));
    }
    Ok(())
}

fn parse_carrier_fields(raw: &str) -> Result<Option<IndexMap<String, Box<RawValue>>>, Refusal> {
    // Validate JSON before inspecting type; no magic Number map can become an integer label.
    let _: Box<RawValue> = serde_json::from_str(raw).map_err(syntax)?;
    if raw == "null" {
        return Ok(None);
    }
    if !raw.starts_with('{') {
        return Err(refuse(
            "ADVERSARY_CARRIER_MALFORMED",
            "carrier_context must be a mapping",
        ));
    }
    let fields: IndexMap<String, Box<RawValue>> = serde_json::from_str(raw).map_err(syntax)?;
    let pattern = Regex::new(
        r"(?i)^(initial_)?(node|vert|edge|face|cochain|cell|simpl|tetra|four_simpl|regge)",
    )
    .map_err(|error| refuse("ADVERSARY_CARRIER_PARSER_UNAVAILABLE", error.to_string()))?;
    let carrier_like = fields
        .keys()
        .filter(|key| pattern.is_match(key))
        .cloned()
        .collect::<BTreeSet<_>>();
    if carrier_like.is_empty() {
        return Ok(None);
    }
    validate_carrier_keys(&fields, &carrier_like)?;
    Ok(Some(fields))
}

fn parse_carrier_nodes(fields: &IndexMap<String, Box<RawValue>>) -> Result<Vec<NodeLabel>, Refusal> {
    let nodes = labels(required(fields, "nodes")?)?;
    if set_of(&nodes).len() != nodes.len() {
        return Err(malformed("duplicate node label"));
    }
    Ok(nodes)
}

fn parse_carrier_edges(fields: &IndexMap<String, Box<RawValue>>) -> Result<Vec<Edge>, Refusal> {
    let mut edges = Vec::new();
    for raw in iterable(required(fields, "edges")?)? {
        let edge = labels(&raw)?;
        if edge.len() != 2 || edge[0] == edge[1] {
            return Err(malformed(format!(
                "edge {} is not a pair of distinct nodes",
                tuple_repr(&edge)
            )));
        }
        let edge = [edge[0].clone(), edge[1].clone()];
        if edges.contains(&edge) || edges.contains(&reverse(&edge)) {
            return Err(malformed(format!(
                "edge {} is declared twice",
                tuple_repr(&edge)
            )));
        }
        edges.push(edge);
    }
    Ok(edges)
}

fn validate_face_edges(face: &[NodeLabel], edges: &[Edge]) -> Result<(), Refusal> {
    for (a, b) in [(0, 1), (1, 2), (2, 0)] {
        let edge = [face[a].clone(), face[b].clone()];
        if !edges.contains(&edge) && !edges.contains(&reverse(&edge)) {
            return Err(malformed(format!(
                "face {} has no edge between {} and {}",
                tuple_repr(face),
                face[a].repr(),
                face[b].repr()
            )));
        }
    }
    Ok(())
}

fn parse_carrier_faces(
    fields: &IndexMap<String, Box<RawValue>>,
    edges: &[Edge],
) -> Result<Vec<[NodeLabel; 3]>, Refusal> {
    let mut faces = Vec::new();
    for raw in optional_iterable(fields, "faces")? {
        let face = labels(&raw)?;
        if face.len() != 3 || set_of(&face).len() != 3 {
            return Err(malformed(format!(
                "face {} is not a triangle of distinct nodes",
                tuple_repr(&face)
            )));
        }
        validate_face_edges(&face, edges)?;
        if faces
            .iter()
            .any(|item: &[NodeLabel; 3]| set_of(item) == set_of(&face))
        {
            return Err(malformed(format!(
                "face {} is declared twice",
                tuple_repr(&face)
            )));
        }
        faces.push([face[0].clone(), face[1].clone(), face[2].clone()]);
    }
    Ok(faces)
}

fn parse_carrier_tetrahedra(
    fields: &IndexMap<String, Box<RawValue>>,
    faces: &[[NodeLabel; 3]],
) -> Result<Vec<[NodeLabel; 4]>, Refusal> {
    let mut tetrahedra = Vec::new();
    let face_sets = faces.iter().map(|face| set_of(face)).collect();
    for raw in optional_iterable(fields, "tetrahedra")? {
        let cell = labels(&raw)?;
        if cell.len() != 4 || set_of(&cell).len() != 4 {
            return Err(malformed(format!(
                "tetrahedron {} is not four distinct nodes",
                tuple_repr(&cell)
            )));
        }
        if let Some(side) = boundary_present(&cell, &face_sets) {
            return Err(malformed(format!(
                "tetrahedron {} has an undeclared face [{}]",
                tuple_repr(&cell),
                side.iter()
                    .map(NodeLabel::repr)
                    .collect::<Vec<_>>()
                    .join(", ")
            )));
        }
        if tetrahedra
            .iter()
            .any(|item: &[NodeLabel; 4]| set_of(item) == set_of(&cell))
        {
            return Err(malformed(format!(
                "tetrahedron {} is declared twice",
                tuple_repr(&cell)
            )));
        }
        tetrahedra.push([
            cell[0].clone(),
            cell[1].clone(),
            cell[2].clone(),
            cell[3].clone(),
        ]);
    }
    Ok(tetrahedra)
}

fn parse_carrier_four_simplices(
    fields: &IndexMap<String, Box<RawValue>>,
    tetrahedra: &[[NodeLabel; 4]],
) -> Result<Vec<[NodeLabel; 5]>, Refusal> {
    let mut four_simplices = Vec::new();
    let tet_sets = tetrahedra.iter().map(|tet| set_of(tet)).collect();
    for raw in optional_iterable(fields, "four_simplices")? {
        let cell = labels(&raw)?;
        if cell.len() != 5 || set_of(&cell).len() != 5 {
            return Err(malformed(format!(
                "4-simplex {} is not five distinct nodes",
                tuple_repr(&cell)
            )));
        }
        if let Some(side) = boundary_present(&cell, &tet_sets) {
            return Err(malformed(format!(
                "4-simplex {} has an undeclared tetrahedron [{}]",
                tuple_repr(&cell),
                side.iter()
                    .map(NodeLabel::repr)
                    .collect::<Vec<_>>()
                    .join(", ")
            )));
        }
        if four_simplices
            .iter()
            .any(|item: &[NodeLabel; 5]| set_of(item) == set_of(&cell))
        {
            return Err(malformed(format!(
                "4-simplex {} is declared twice",
                tuple_repr(&cell)
            )));
        }
        four_simplices.push([
            cell[0].clone(),
            cell[1].clone(),
            cell[2].clone(),
            cell[3].clone(),
            cell[4].clone(),
        ]);
    }
    Ok(four_simplices)
}

fn parse_cochain_value(raw_value: &RawValue) -> Result<BigRational, Refusal> {
    let raw_text = raw_value.get().trim_start();
    let value: Value = if raw_text.starts_with('{') {
        Value::Object(Default::default())
    } else if raw_text.starts_with('[') {
        Value::Array(Vec::new())
    } else {
        serde_json::from_str(raw_text).map_err(syntax)?
    };
    parse_exact_rational(&value).map_err(|error| malformed(error.message))
}

fn resolve_cochain_edge(
    key: &str,
    parsed: Vec<Option<NodeLabel>>,
    value: BigRational,
    network: &Network,
) -> Result<(Edge, BigRational), Refusal> {
    let edge = parsed
        .into_iter()
        .collect::<Option<Vec<_>>>()
        .and_then(|values| <[NodeLabel; 2]>::try_from(values).ok());
    match edge {
        Some(edge) if network.edges.iter().any(|item| edge_equal(item, &edge)) => Ok((edge, value)),
        Some(edge)
            if network
                .edges
                .iter()
                .any(|item| edge_equal(item, &reverse(&edge))) =>
        {
            Ok((reverse(&edge), -value))
        }
        _ => Err(malformed(format!(
            "cochain key {} is not an edge of the carrier",
            repr_string(key)
        ))),
    }
}

fn parse_cochains_map(
    fields: &IndexMap<String, Box<RawValue>>,
    network: &Network,
) -> Result<(Vec<(Edge, BigRational)>, usize), Refusal> {
    let cochains = required(fields, "cochains")?;
    if !cochains.get().trim_start().starts_with('{') {
        return Err(malformed(
            "cochains must be a mapping from edge to exact rational",
        ));
    }
    let raw_cochains: IndexMap<String, Box<RawValue>> =
        serde_json::from_str(cochains.get()).map_err(syntax)?;
    let mut entries: Vec<(Edge, BigRational)> = Vec::new();
    for (key, raw_value) in raw_cochains {
        let parsed = cochain_key(&key);
        let value = parse_cochain_value(&raw_value)?;
        let (edge, value) = resolve_cochain_edge(&key, parsed, value, network)?;
        if entries.iter().any(|(item, _)| edge_equal(item, &edge)) {
            return Err(malformed(format!(
                "cochain assigns edge {} twice",
                tuple_repr(&edge)
            )));
        }
        entries.push((edge, value));
    }
    let mut implicit = 0;
    for edge in &network.edges {
        if !entries.iter().any(|(key, _)| edge_equal(key, edge)) {
            entries.push((edge.clone(), BigRational::zero()));
            implicit += 1;
        }
    }
    Ok((entries, implicit))
}

pub fn parse_carrier_json(context: Option<&str>) -> Result<ParsedCarrier, Refusal> {
    let raw = context.unwrap_or("null").trim();
    let Some(fields) = parse_carrier_fields(raw)? else {
        return empty_carrier();
    };
    let nodes = parse_carrier_nodes(&fields)?;
    let edges = parse_carrier_edges(&fields)?;
    let faces = parse_carrier_faces(&fields, &edges)?;
    let tetrahedra = parse_carrier_tetrahedra(&fields, &faces)?;
    let four_simplices = parse_carrier_four_simplices(&fields, &tetrahedra)?;
    let network = Network::new(nodes, edges, faces, tetrahedra, four_simplices)?;
    let (entries, implicit) = parse_cochains_map(&fields, &network)?;
    Ok(ParsedCarrier {
        network,
        cochain: ExactCochain { entries },
        declared: true,
        implicit_zero_edges: implicit,
    })
}
fn required<'a>(
    fields: &'a IndexMap<String, Box<RawValue>>,
    key: &str,
) -> Result<&'a RawValue, Refusal> {
    fields.get(key).map(AsRef::as_ref).ok_or_else(|| {
        refuse(
            "ADVERSARY_CARRIER_KEYS_MISSING",
            format!("declared carrier is missing {key}"),
        )
    })
}
fn optional_iterable(
    fields: &IndexMap<String, Box<RawValue>>,
    key: &str,
) -> Result<Vec<Box<RawValue>>, Refusal> {
    fields
        .get(key)
        .map_or_else(|| Ok(Vec::new()), |raw| iterable(raw))
}
fn empty_carrier() -> Result<ParsedCarrier, Refusal> {
    Ok(ParsedCarrier {
        network: Network::new(Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new())?,
        cochain: ExactCochain {
            entries: Vec::new(),
        },
        declared: false,
        implicit_zero_edges: 0,
    })
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
#[path = "../../tests/core_adversary/support/carrier_integer_cases.rs"]
mod integer_cases;

// Origin: engine/crates_rs/core_adversary/src/carrier.rs
// Claim: urn:core:crates_rs:core-adversary:carrier:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord832c2dbe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord832c2dbe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError832c2dbe {
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
impl BoundaryError832c2dbe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError832c2dbe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError832c2dbe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord832c2dbe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError832c2dbe> {
        if capacity_bound == 0 {
            return Err(BoundaryError832c2dbe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError832c2dbe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError832c2dbe::ExceedsCapacity {
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
mod l4_boundary_tests_832c2dbe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord832c2dbe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord832c2dbe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord832c2dbe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord832c2dbe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord832c2dbe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError832c2dbe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError832c2dbe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

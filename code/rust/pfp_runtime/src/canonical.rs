//! Strict canonical encoding and length-delimited domain digests.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2914cec6<T> {
    fn checked_invariant_2914cec6(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2914cec6<T> for Option<T> {
    #[inline]
    fn checked_invariant_2914cec6(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2914cec6<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2914cec6(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use serde_json::Value;
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const CANONICAL_MARKER: &str = "core-canonical-v1";

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum CanonicalizationError {
    #[error("digest domain must be non-empty")]
    EmptyDomain,
    #[error("non-finite floats are not canonical")]
    NonFiniteFloat,
    #[error("float values are forbidden in exact rational arithmetic: {0}")]
    FloatForbidden(String),
    #[error("canonical mapping keys must be exact strings")]
    InvalidMappingKey,
    #[error("canonical wire node must be a three-item array")]
    InvalidWireNode,
    #[error("canonical wire marker or tag is invalid")]
    InvalidWireTag,
    #[error("unknown canonical wire tag: {0}")]
    UnknownTag(String),
    #[error("canonical {0} body is invalid")]
    InvalidBody(String),
    #[error("canonical compound body must be an array")]
    CompoundBodyNotArray,
    #[error("canonical mapping entries are invalid: {0}")]
    InvalidMapping(String),
    #[error("canonical JSON serialization error: {0}")]
    SerializationError(String),
    #[error("unsupported canonical value: {0}")]
    UnsupportedValue(String),
}

/// Injective canonical value representing the closed type algebra.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CanonicalValue {
    Null,
    Bool(bool),
    Int(BigInt),
    String(String),
    FloatHex(String),
    Fraction(BigInt, BigInt),
    BytesHex(String),
    List(Vec<CanonicalValue>),
    Tuple(Vec<CanonicalValue>),
    Set(Vec<CanonicalValue>),
    Frozenset(Vec<CanonicalValue>),
    Enum {
        module: String,
        qualname: String,
        name: String,
        value: Box<CanonicalValue>,
    },
    Field {
        name: String,
        value: Box<CanonicalValue>,
    },
    Entry {
        key: String,
        value: Box<CanonicalValue>,
    },
    Dataclass {
        module: String,
        qualname: String,
        fields: Vec<CanonicalValue>,
    },
    Mapping {
        module: String,
        qualname: String,
        entries: Vec<CanonicalValue>,
    },
}

fn extract_wire_string(val: &CanonicalValue, label: &str) -> Result<String, CanonicalizationError> {
    match val {
        CanonicalValue::String(s) => Ok(s.clone()),
        _ => Err(CanonicalizationError::InvalidBody(label.to_owned())),
    }
}

fn parse_wire_string_node(item: &Value, label: &str) -> Result<String, CanonicalizationError> {
    let node = CanonicalValue::from_wire(item)?;
    extract_wire_string(&node, label)
}

fn expect_wire_array<'a>(
    body: &'a Value,
    expected_len: usize,
    tag: &str,
) -> Result<&'a [Value], CanonicalizationError> {
    let items = body
        .as_array()
        .ok_or(CanonicalizationError::CompoundBodyNotArray)?;
    if items.len() != expected_len {
        return Err(CanonicalizationError::InvalidBody(tag.to_owned()));
    }
    Ok(items)
}

fn expect_wire_min_array<'a>(
    body: &'a Value,
    min_len: usize,
    tag: &str,
) -> Result<&'a [Value], CanonicalizationError> {
    let items = body
        .as_array()
        .ok_or(CanonicalizationError::CompoundBodyNotArray)?;
    if items.len() < min_len {
        return Err(CanonicalizationError::InvalidBody(tag.to_owned()));
    }
    Ok(items)
}

fn parse_wire_int(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let text = body
        .as_str()
        .ok_or_else(|| CanonicalizationError::InvalidBody("int".to_owned()))?;
    let parsed = text
        .parse::<BigInt>()
        .map_err(|_| CanonicalizationError::InvalidBody("int".to_owned()))?;
    if parsed.to_string() != text {
        return Err(CanonicalizationError::InvalidBody("int".to_owned()));
    }
    Ok(CanonicalValue::Int(parsed))
}

fn parse_wire_primitive(
    tag: &str,
    body: &Value,
) -> Option<Result<CanonicalValue, CanonicalizationError>> {
    match tag {
        "null" => Some(if body.is_null() {
            Ok(CanonicalValue::Null)
        } else {
            Err(CanonicalizationError::InvalidBody("null".to_owned()))
        }),
        "bool" => Some(
            body.as_bool()
                .map(CanonicalValue::Bool)
                .ok_or_else(|| CanonicalizationError::InvalidBody("bool".to_owned())),
        ),
        "int" => Some(parse_wire_int(body)),
        "string" => Some(
            body.as_str()
                .map(|s| CanonicalValue::String(s.to_owned()))
                .ok_or_else(|| CanonicalizationError::InvalidBody("string".to_owned())),
        ),
        _ => None,
    }
}

fn parse_wire_float(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let items = expect_wire_array(body, 1, "float")?;
    let hex_str = parse_wire_string_node(&items[0], "float hex")?;
    Err(CanonicalizationError::FloatForbidden(hex_str))
}

fn validate_reduced_fraction(
    num: BigInt,
    denom: BigInt,
) -> Result<CanonicalValue, CanonicalizationError> {
    if denom <= BigInt::zero() {
        return Err(CanonicalizationError::InvalidBody(
            "fraction denominator non-positive".to_owned(),
        ));
    }
    let reduced = BigRational::new(num.clone(), denom.clone());
    if reduced.numer() != &num || reduced.denom() != &denom {
        return Err(CanonicalizationError::InvalidBody(
            "fraction unreduced".to_owned(),
        ));
    }
    Ok(CanonicalValue::Fraction(num, denom))
}

fn parse_wire_fraction(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let items = expect_wire_array(body, 2, "fraction")?;
    let n = CanonicalValue::from_wire(&items[0])?;
    let d = CanonicalValue::from_wire(&items[1])?;
    match (n, d) {
        (CanonicalValue::Int(num), CanonicalValue::Int(denom)) => {
            validate_reduced_fraction(num, denom)
        }
        _ => Err(CanonicalizationError::InvalidBody("fraction".to_owned())),
    }
}

fn parse_wire_bytes(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let items = expect_wire_array(body, 1, "bytes")?;
    let hex_str = parse_wire_string_node(&items[0], "bytes hex")?;
    Ok(CanonicalValue::BytesHex(hex_str))
}

fn parse_wire_list_items(body: &Value) -> Result<Vec<CanonicalValue>, CanonicalizationError> {
    let items = body
        .as_array()
        .ok_or(CanonicalizationError::CompoundBodyNotArray)?;
    items.iter().map(CanonicalValue::from_wire).collect()
}

fn parse_wire_sorted_items(body: &Value) -> Result<Vec<CanonicalValue>, CanonicalizationError> {
    let mut list = parse_wire_list_items(body)?;
    list.sort_by_key(CanonicalValue::to_canonical_json);
    Ok(list)
}

fn parse_wire_sequence(
    tag: &str,
    body: &Value,
) -> Option<Result<CanonicalValue, CanonicalizationError>> {
    match tag {
        "list" => Some(parse_wire_list_items(body).map(CanonicalValue::List)),
        "tuple" => Some(parse_wire_list_items(body).map(CanonicalValue::Tuple)),
        "set" => Some(parse_wire_sorted_items(body).map(CanonicalValue::Set)),
        "frozenset" => Some(parse_wire_sorted_items(body).map(CanonicalValue::Frozenset)),
        _ => None,
    }
}

fn parse_wire_named_pair(
    body: &Value,
    tag: &str,
    key_label: &str,
) -> Result<(String, Box<CanonicalValue>), CanonicalizationError> {
    let items = expect_wire_array(body, 2, tag)?;
    let key = parse_wire_string_node(&items[0], key_label)?;
    let val = CanonicalValue::from_wire(&items[1])?;
    Ok((key, Box::new(val)))
}

fn parse_mapping_entry(item: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let entry = CanonicalValue::from_wire(item)?;
    if !matches!(entry, CanonicalValue::Entry { .. }) {
        return Err(CanonicalizationError::InvalidMapping(
            "entry required".to_owned(),
        ));
    }
    Ok(entry)
}

fn sort_mapping_entries(entries: &mut [CanonicalValue]) {
    entries.sort_by(|a, b| match (a, b) {
        (CanonicalValue::Entry { key: k1, .. }, CanonicalValue::Entry { key: k2, .. }) => {
            k1.cmp(k2)
        }
        _ => std::cmp::Ordering::Equal,
    });
}

fn parse_wire_mapping(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let items = expect_wire_min_array(body, 2, "mapping")?;
    let module = parse_wire_string_node(&items[0], "mapping module")?;
    let qualname = parse_wire_string_node(&items[1], "mapping qualname")?;
    let mut entries = items[2..]
        .iter()
        .map(parse_mapping_entry)
        .collect::<Result<Vec<_>, _>>()?;
    sort_mapping_entries(&mut entries);
    Ok(CanonicalValue::Mapping {
        module,
        qualname,
        entries,
    })
}

fn parse_wire_dataclass(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let items = expect_wire_min_array(body, 2, "dataclass")?;
    let module = parse_wire_string_node(&items[0], "dataclass module")?;
    let qualname = parse_wire_string_node(&items[1], "dataclass qualname")?;
    let fields = items[2..]
        .iter()
        .map(CanonicalValue::from_wire)
        .collect::<Result<Vec<_>, _>>()?;
    Ok(CanonicalValue::Dataclass {
        module,
        qualname,
        fields,
    })
}

fn parse_wire_enum(body: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    let items = expect_wire_array(body, 4, "enum")?;
    let module = parse_wire_string_node(&items[0], "enum module")?;
    let qualname = parse_wire_string_node(&items[1], "enum qualname")?;
    let name = parse_wire_string_node(&items[2], "enum name")?;
    let val = CanonicalValue::from_wire(&items[3])?;
    Ok(CanonicalValue::Enum {
        module,
        qualname,
        name,
        value: Box::new(val),
    })
}

fn parse_wire_encoded_scalar(
    tag: &str,
    body: &Value,
) -> Option<Result<CanonicalValue, CanonicalizationError>> {
    match tag {
        "float" => Some(parse_wire_float(body)),
        "fraction" => Some(parse_wire_fraction(body)),
        "bytes" => Some(parse_wire_bytes(body)),
        _ => None,
    }
}

fn parse_wire_compound(
    tag: &str,
    body: &Value,
) -> Result<CanonicalValue, CanonicalizationError> {
    if let Some(res) = parse_wire_sequence(tag, body) {
        return res;
    }
    if let Some(res) = parse_wire_encoded_scalar(tag, body) {
        return res;
    }
    match tag {
        "field" => {
            let (name, value) = parse_wire_named_pair(body, "field", "field name")?;
            Ok(CanonicalValue::Field { name, value })
        }
        "entry" => {
            let (key, value) = parse_wire_named_pair(body, "entry", "entry key")?;
            Ok(CanonicalValue::Entry { key, value })
        }
        "mapping" => parse_wire_mapping(body),
        "dataclass" => parse_wire_dataclass(body),
        "enum" => parse_wire_enum(body),
        other => Err(CanonicalizationError::UnknownTag(other.to_owned())),
    }
}

fn wire_node(tag: &str, body: Value) -> Value {
    Value::Array(vec![
        Value::String(CANONICAL_MARKER.to_owned()),
        Value::String(tag.to_owned()),
        body,
    ])
}

fn wire_sorted_sequence(tag: &str, items: &[CanonicalValue]) -> Value {
    let mut sorted = items.to_vec();
    sorted.sort_by_key(CanonicalValue::to_canonical_json);
    wire_node(
        tag,
        Value::Array(sorted.iter().map(CanonicalValue::to_wire).collect()),
    )
}

fn wire_qualified_body(module: &str, qualname: &str, children: &[CanonicalValue]) -> Value {
    let mut body = vec![
        CanonicalValue::String(module.to_owned()).to_wire(),
        CanonicalValue::String(qualname.to_owned()).to_wire(),
    ];
    for child in children {
        body.push(child.to_wire());
    }
    Value::Array(body)
}

impl CanonicalValue {
    /// Convert standard JSON value to canonical representation (mapping objects to `builtins.dict`).
    pub fn from_json(value: &Value) -> Result<Self, CanonicalizationError> {
        match value {
            Value::Null => Ok(CanonicalValue::Null),
            Value::Bool(b) => Ok(CanonicalValue::Bool(*b)),
            Value::Number(n) => {
                let s = n.to_string();
                if let Ok(parsed) = s.parse::<BigInt>() {
                    Ok(CanonicalValue::Int(parsed))
                } else {
                    Err(CanonicalizationError::NonFiniteFloat)
                }
            }
            Value::String(s) => Ok(CanonicalValue::String(s.clone())),
            Value::Array(arr) => {
                let items: Result<Vec<_>, _> = arr.iter().map(Self::from_json).collect();
                Ok(CanonicalValue::List(items?))
            }
            Value::Object(map) => {
                let mut sorted_keys: Vec<&String> = map.keys().collect();
                sorted_keys.sort();
                let mut entries = Vec::with_capacity(sorted_keys.len());
                for k in sorted_keys {
                    let v = Self::from_json(&map[k])?;
                    entries.push(CanonicalValue::Entry {
                        key: k.clone(),
                        value: Box::new(v),
                    });
                }
                Ok(CanonicalValue::Mapping {
                    module: "builtins".to_owned(),
                    qualname: "dict".to_owned(),
                    entries,
                })
            }
        }
    }

    /// Parse a value from canonical wire format `["core-canonical-v1", tag, body]`.
    pub fn from_wire(value: &Value) -> Result<Self, CanonicalizationError> {
        let arr = value
            .as_array()
            .filter(|a| a.len() == 3)
            .ok_or(CanonicalizationError::InvalidWireNode)?;
        if arr[0].as_str() != Some(CANONICAL_MARKER) {
            return Err(CanonicalizationError::InvalidWireTag);
        }
        let tag = arr[1]
            .as_str()
            .ok_or(CanonicalizationError::InvalidWireTag)?;
        let body = &arr[2];
        if let Some(res) = parse_wire_primitive(tag, body) {
            return res;
        }
        parse_wire_compound(tag, body)
    }

    fn to_wire_scalar(&self) -> Option<Value> {
        match self {
            CanonicalValue::Null => Some(wire_node("null", Value::Null)),
            CanonicalValue::Bool(b) => Some(wire_node("bool", Value::Bool(*b))),
            CanonicalValue::Int(i) => Some(wire_node("int", Value::String(i.to_string()))),
            CanonicalValue::String(s) => Some(wire_node("string", Value::String(s.clone()))),
            CanonicalValue::FloatHex(hex) => Some(wire_node(
                "float",
                Value::Array(vec![CanonicalValue::String(hex.clone()).to_wire()]),
            )),
            CanonicalValue::Fraction(n, d) => Some(wire_node(
                "fraction",
                Value::Array(vec![
                    CanonicalValue::Int(n.clone()).to_wire(),
                    CanonicalValue::Int(d.clone()).to_wire(),
                ]),
            )),
            CanonicalValue::BytesHex(hex) => Some(wire_node(
                "bytes",
                Value::Array(vec![CanonicalValue::String(hex.clone()).to_wire()]),
            )),
            _ => None,
        }
    }

    fn to_wire_collection(&self) -> Option<Value> {
        match self {
            CanonicalValue::List(items) => Some(wire_node(
                "list",
                Value::Array(items.iter().map(CanonicalValue::to_wire).collect()),
            )),
            CanonicalValue::Tuple(items) => Some(wire_node(
                "tuple",
                Value::Array(items.iter().map(CanonicalValue::to_wire).collect()),
            )),
            CanonicalValue::Set(items) => Some(wire_sorted_sequence("set", items)),
            CanonicalValue::Frozenset(items) => Some(wire_sorted_sequence("frozenset", items)),
            _ => None,
        }
    }

    /// Render to canonical wire JSON node `["core-canonical-v1", tag, body]`.
    pub fn to_wire(&self) -> Value {
        if let Some(scalar) = self.to_wire_scalar() {
            return scalar;
        }
        if let Some(coll) = self.to_wire_collection() {
            return coll;
        }
        match self {
            CanonicalValue::Enum {
                module,
                qualname,
                name,
                value,
            } => wire_node(
                "enum",
                Value::Array(vec![
                    CanonicalValue::String(module.clone()).to_wire(),
                    CanonicalValue::String(qualname.clone()).to_wire(),
                    CanonicalValue::String(name.clone()).to_wire(),
                    value.to_wire(),
                ]),
            ),
            CanonicalValue::Field { name, value } => wire_node(
                "field",
                Value::Array(vec![
                    CanonicalValue::String(name.clone()).to_wire(),
                    value.to_wire(),
                ]),
            ),
            CanonicalValue::Entry { key, value } => wire_node(
                "entry",
                Value::Array(vec![
                    CanonicalValue::String(key.clone()).to_wire(),
                    value.to_wire(),
                ]),
            ),
            CanonicalValue::Dataclass {
                module,
                qualname,
                fields,
            } => wire_node("dataclass", wire_qualified_body(module, qualname, fields)),
            CanonicalValue::Mapping {
                module,
                qualname,
                entries,
            } => {
                let mut sorted = entries.clone();
                sort_mapping_entries(&mut sorted);
                wire_node("mapping", wire_qualified_body(module, qualname, &sorted))
            }
            _ => Value::Null,
        }
    }

    /// Produce the compact `core-canonical-v1` string: the tagged wire tree
    /// (`["core-canonical-v1", tag, body]`) written by `serde_json` with no
    /// whitespace.
    ///
    /// This is not RFC 8785 (JCS). The tree holds only arrays, strings, `null`
    /// and Booleans, so object key ordering and the JCS number rules never
    /// arise; integers and rationals travel as decimal strings inside their
    /// tags. Two implementations agree on these bytes only through the shared
    /// golden vectors in `tests/canonical_parity.rs`.
    pub fn to_canonical_json(&self) -> String {
        serde_json::to_string(&self.to_wire()).checked_invariant_2914cec6("canonical wire tree always serializes")
    }

    /// Produce canonical UTF-8 bytes.
    pub fn to_canonical_bytes(&self) -> Vec<u8> {
        self.to_canonical_json().into_bytes()
    }
}

/// Compute hex SHA-256 digest of length-delimited framed payload:
/// `u32_be(len(domain)) || domain || u64_be(len(payload)) || payload`.
pub fn framed_sha256(domain: &str, payload: &[u8]) -> String {
    let domain_length = u32::try_from(domain.len()).checked_invariant_2914cec6("digest domain fits in u32");
    let payload_length = u64::try_from(payload.len()).checked_invariant_2914cec6("digest payload fits in u64");
    let mut hasher = Sha256::new();
    hasher.update(domain_length.to_be_bytes());
    hasher.update(domain.as_bytes());
    hasher.update(payload_length.to_be_bytes());
    hasher.update(payload);
    let result = hasher.finalize();
    hex::encode(result)
}

/// Compute domain-separated digest of a canonical value.
pub fn domain_digest(
    domain: &str,
    value: &CanonicalValue,
) -> Result<String, CanonicalizationError> {
    if domain.is_empty() {
        return Err(CanonicalizationError::EmptyDomain);
    }
    let payload = value.to_canonical_bytes();
    Ok(framed_sha256(domain, &payload))
}

/// Compute domain-separated digest directly from a serde_json Value.
pub fn domain_digest_json(domain: &str, value: &Value) -> Result<String, CanonicalizationError> {
    let canon = CanonicalValue::from_json(value)?;
    domain_digest(domain, &canon)
}

/// Serialize a serde_json Value into canonical wire JSON string.
pub fn canonical_json(value: &Value) -> Result<String, CanonicalizationError> {
    let canon = CanonicalValue::from_json(value)?;
    Ok(canon.to_canonical_json())
}

/// Serialize a serde_json Value into canonical bytes.
pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, CanonicalizationError> {
    let canon = CanonicalValue::from_json(value)?;
    Ok(canon.to_canonical_bytes())
}

/// Convert JSON value to canonical wire JSON node.
pub fn canonical_wire(value: &Value) -> Result<Value, CanonicalizationError> {
    let canon = CanonicalValue::from_json(value)?;
    Ok(canon.to_wire())
}

/// Unwire canonical wire JSON node back into a CanonicalValue.
pub fn canonical_unwire(wire: &Value) -> Result<CanonicalValue, CanonicalizationError> {
    CanonicalValue::from_wire(wire)
}

// Origin: engine/crates_rs/pfp_runtime/src/canonical.rs
// Claim: urn:core:crates_rs:pfp-runtime:canonical:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn primitives_match_wire_specification() {
        let null_val = CanonicalValue::Null;
        assert_eq!(
            null_val.to_canonical_json(),
            r#"["core-canonical-v1","null",null]"#
        );

        let bool_val = CanonicalValue::Bool(true);
        assert_eq!(
            bool_val.to_canonical_json(),
            r#"["core-canonical-v1","bool",true]"#
        );

        let int_val = CanonicalValue::Int(BigInt::from(42));
        assert_eq!(
            int_val.to_canonical_json(),
            r#"["core-canonical-v1","int","42"]"#
        );

        let str_val = CanonicalValue::String("hello".to_owned());
        assert_eq!(
            str_val.to_canonical_json(),
            r#"["core-canonical-v1","string","hello"]"#
        );
    }

    #[test]
    fn map_keys_are_sorted() {
        let val = json!({"zebra": 1, "apple": 2, "mango": 3});
        let canon = CanonicalValue::from_json(&val).unwrap();
        let json_str = canon.to_canonical_json();
        let expected = r#"["core-canonical-v1","mapping",[["core-canonical-v1","string","builtins"],["core-canonical-v1","string","dict"],["core-canonical-v1","entry",[["core-canonical-v1","string","apple"],["core-canonical-v1","int","2"]]],["core-canonical-v1","entry",[["core-canonical-v1","string","mango"],["core-canonical-v1","int","3"]]],["core-canonical-v1","entry",[["core-canonical-v1","string","zebra"],["core-canonical-v1","int","1"]]]]]"#;
        assert_eq!(json_str, expected);
    }

    #[test]
    fn empty_domain_refuses() {
        let val = CanonicalValue::Null;
        assert_eq!(
            domain_digest("", &val),
            Err(CanonicalizationError::EmptyDomain)
        );
    }

    #[test]
    fn tag_float_is_refused_with_float_forbidden() {
        let wire = json!([
            "core-canonical-v1",
            "float",
            [["core-canonical-v1", "string", "0x1.0p+0"]]
        ]);
        assert_eq!(
            canonical_unwire(&wire),
            Err(CanonicalizationError::FloatForbidden("0x1.0p+0".to_owned()))
        );
    }
}

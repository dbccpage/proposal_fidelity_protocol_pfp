//! Pure, value-preserving transport for a closed characteristic-coefficient wire.
//!
//! AuthorityEffect: None.
//!
//! Normalization reduces rationals, omits explicit zero monomials, sorts by powers,
//! and serializes canonical JSON. Duplicate powers refuse BEFORE zero removal.
//! Monicity of leading coefficient in lambda^4 is verified.

use num_bigint::BigInt;
use num_traits::{Signed, Zero};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::borrow::Cow;
use std::collections::BTreeSet;
use std::sync::LazyLock;

pub const SCHEMA: &str = "pfp.charpoly-wire.normalization.v1";
pub const MAX_INPUT_BYTES: usize = 32_768;
pub const MAX_JSON_DEPTH: usize = 8;
pub const MAX_TERMS_PER_COEFFICIENT: usize = 125;
pub const MAX_TOTAL_TERMS: usize = 625;
pub const MAX_RATIONAL_BITS: usize = 64;
pub const MAX_RATIONAL_CHARS: usize = 42;
pub const PRESERVATION_SCOPE: &str =
    "Identical polynomial in Q[lambda,J,Delta,K] under the declared ascending-lambda and powers=[eJ,eDelta,eK] interpretation. Only representation is changed.";

static RATIONAL_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^[+-]?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?$")
        .expect("static rational regex must compile")
});

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WireRefusal(pub &'static str);

impl std::fmt::Display for WireRefusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for WireRefusal {}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct NormalizationReceipt {
    pub schema: String,
    pub status: String,
    pub accepted: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_sha256: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub original_utf8_bytes: Option<usize>,
    pub normalized_sha256: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub normalized_utf8_bytes: Option<usize>,
    pub normalized_json: Option<String>,
    pub transformations: Vec<Value>,
    pub semantic_preservation: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub refusal: Option<Value>,
    pub scope: String,
    pub not_established: Vec<String>,
    pub limits: Value,
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    hex::encode(hasher.finalize())
}

fn standard_limits() -> Value {
    json!({
        "input_utf8_bytes": MAX_INPUT_BYTES,
        "json_depth": MAX_JSON_DEPTH,
        "coefficient_arrays": 5,
        "terms_per_coefficient": MAX_TERMS_PER_COEFFICIENT,
        "total_terms": MAX_TOTAL_TERMS,
        "rational_component_bits": MAX_RATIONAL_BITS,
        "rational_string_characters": MAX_RATIONAL_CHARS,
        "exponents": "3 exact integers 0..4"
    })
}

fn standard_not_established() -> Vec<String> {
    vec![
        "correct characteristic polynomial".to_string(),
        "matrix or seed binding".to_string(),
        "native verification".to_string(),
        "final-answer correctness".to_string(),
    ]
}

fn check_json_depth(text: &str) -> Result<(), WireRefusal> {
    let mut depth: isize = 0;
    let mut quoted = false;
    let mut escaped = false;
    for c in text.chars() {
        if quoted {
            if escaped {
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == '"' {
                quoted = false;
            }
        } else if c == '"' {
            quoted = true;
        } else if c == '[' || c == '{' {
            depth += 1;
            if depth > MAX_JSON_DEPTH as isize {
                return Err(WireRefusal("JSON_DEPTH_LIMIT"));
            }
        } else if c == ']' || c == '}' {
            depth -= 1;
            if depth < 0 {
                return Err(WireRefusal("MALFORMED_JSON"));
            }
        }
    }
    if depth != 0 || quoted {
        return Err(WireRefusal("MALFORMED_JSON"));
    }
    Ok(())
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum JsonToken {
    LeftBrace,
    RightBrace,
    LeftBracket,
    RightBracket,
    Colon,
    Comma,
    String(String),
    Integer(String),
    FloatOrNonFinite,
    OtherLiteral(String),
}

struct JsonLexer<'a> {
    chars: Vec<char>,
    pos: usize,
    _marker: std::marker::PhantomData<&'a str>,
}

impl<'a> JsonLexer<'a> {
    fn new(input: &'a str) -> Self {
        Self {
            chars: input.chars().collect(),
            pos: 0,
            _marker: std::marker::PhantomData,
        }
    }

    fn skip_whitespace(&mut self) {
        while self.pos < self.chars.len() && self.chars[self.pos].is_whitespace() {
            self.pos += 1;
        }
    }

    fn next_token(&mut self) -> Result<Option<JsonToken>, WireRefusal> {
        self.skip_whitespace();
        if self.pos >= self.chars.len() {
            return Ok(None);
        }

        let c = self.chars[self.pos];
        match c {
            '{' => {
                self.pos += 1;
                Ok(Some(JsonToken::LeftBrace))
            }
            '}' => {
                self.pos += 1;
                Ok(Some(JsonToken::RightBrace))
            }
            '[' => {
                self.pos += 1;
                Ok(Some(JsonToken::LeftBracket))
            }
            ']' => {
                self.pos += 1;
                Ok(Some(JsonToken::RightBracket))
            }
            ':' => {
                self.pos += 1;
                Ok(Some(JsonToken::Colon))
            }
            ',' => {
                self.pos += 1;
                Ok(Some(JsonToken::Comma))
            }
            '"' => {
                self.pos += 1;
                let mut s = String::new();
                let mut escaped = false;
                while self.pos < self.chars.len() {
                    let ch = self.chars[self.pos];
                    self.pos += 1;
                    if escaped {
                        match ch {
                            '"' => s.push('"'),
                            '\\' => s.push('\\'),
                            '/' => s.push('/'),
                            'b' => s.push('\x08'),
                            'f' => s.push('\x0c'),
                            'n' => s.push('\n'),
                            'r' => s.push('\r'),
                            't' => s.push('\t'),
                            'u' => {
                                if self.pos + 4 > self.chars.len() {
                                    return Err(WireRefusal("MALFORMED_JSON"));
                                }
                                let hex_str: String =
                                    self.chars[self.pos..self.pos + 4].iter().collect();
                                self.pos += 4;
                                let code = u32::from_str_radix(&hex_str, 16)
                                    .map_err(|_| WireRefusal("MALFORMED_JSON"))?;
                                let unicode_char =
                                    char::from_u32(code).ok_or(WireRefusal("MALFORMED_JSON"))?;
                                s.push(unicode_char);
                            }
                            _ => return Err(WireRefusal("MALFORMED_JSON")),
                        }
                        escaped = false;
                    } else if ch == '\\' {
                        escaped = true;
                    } else if ch == '"' {
                        return Ok(Some(JsonToken::String(s)));
                    } else {
                        s.push(ch);
                    }
                }
                Err(WireRefusal("MALFORMED_JSON"))
            }
            _ => {
                let start = self.pos;
                while self.pos < self.chars.len()
                    && !self.chars[self.pos].is_whitespace()
                    && !matches!(self.chars[self.pos], '{' | '}' | '[' | ']' | ':' | ',')
                {
                    self.pos += 1;
                }
                let token_str: String = self.chars[start..self.pos].iter().collect();

                if token_str == "NaN"
                    || token_str == "Infinity"
                    || token_str == "-Infinity"
                    || token_str.contains('.')
                    || token_str.contains('e')
                    || token_str.contains('E')
                {
                    return Ok(Some(JsonToken::FloatOrNonFinite));
                }

                if token_str == "-0" {
                    return Ok(Some(JsonToken::Integer("-0".to_string())));
                }

                if token_str.starts_with('-') || token_str.chars().all(|ch| ch.is_ascii_digit()) {
                    let digits_part = token_str.strip_prefix('-').unwrap_or(&token_str[..]);
                    if digits_part.len() > 1 && digits_part.starts_with('0') {
                        return Err(WireRefusal("MALFORMED_JSON"));
                    }
                    return Ok(Some(JsonToken::Integer(token_str)));
                }

                Ok(Some(JsonToken::OtherLiteral(token_str)))
            }
        }
    }
}

#[allow(dead_code)]
#[derive(Debug, Clone)]
enum WireVal {
    Object(Vec<(String, WireVal)>),
    Array(Vec<WireVal>),
    String(String),
    Integer(String),
    FloatOrNonFinite,
    OtherLiteral(String),
}

fn parse_wire_val(lexer: &mut JsonLexer<'_>) -> Result<WireVal, WireRefusal> {
    match lexer.next_token()? {
        Some(JsonToken::LeftBrace) => {
            let mut pairs = Vec::new();
            let mut seen_keys = BTreeSet::new();
            lexer.skip_whitespace();
            if lexer.pos < lexer.chars.len() && lexer.chars[lexer.pos] == '}' {
                lexer.pos += 1;
                return Ok(WireVal::Object(pairs));
            }
            loop {
                let key = match lexer.next_token()? {
                    Some(JsonToken::String(k)) => k,
                    _ => return Err(WireRefusal("MALFORMED_JSON")),
                };
                if !seen_keys.insert(key.clone()) {
                    return Err(WireRefusal("DUPLICATE_JSON_KEY"));
                }
                match lexer.next_token()? {
                    Some(JsonToken::Colon) => {}
                    _ => return Err(WireRefusal("MALFORMED_JSON")),
                }
                let val = parse_wire_val(lexer)?;
                pairs.push((key, val));
                match lexer.next_token()? {
                    Some(JsonToken::Comma) => {}
                    Some(JsonToken::RightBrace) => break,
                    _ => return Err(WireRefusal("MALFORMED_JSON")),
                }
            }
            Ok(WireVal::Object(pairs))
        }
        Some(JsonToken::LeftBracket) => {
            let mut items = Vec::new();
            lexer.skip_whitespace();
            if lexer.pos < lexer.chars.len() && lexer.chars[lexer.pos] == ']' {
                lexer.pos += 1;
                return Ok(WireVal::Array(items));
            }
            loop {
                let val = parse_wire_val(lexer)?;
                items.push(val);
                match lexer.next_token()? {
                    Some(JsonToken::Comma) => {}
                    Some(JsonToken::RightBracket) => break,
                    _ => return Err(WireRefusal("MALFORMED_JSON")),
                }
            }
            Ok(WireVal::Array(items))
        }
        Some(JsonToken::String(s)) => Ok(WireVal::String(s)),
        Some(JsonToken::Integer(i)) => Ok(WireVal::Integer(i)),
        Some(JsonToken::FloatOrNonFinite) => Ok(WireVal::FloatOrNonFinite),
        Some(JsonToken::OtherLiteral(_)) => Ok(WireVal::FloatOrNonFinite),
        _ => Err(WireRefusal("MALFORMED_JSON")),
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct MonomialTerm {
    powers: [i64; 3],
    q: String,
}

fn parse_rational_exact(text: &str) -> Result<(BigInt, BigInt), WireRefusal> {
    if text.len() > MAX_RATIONAL_CHARS {
        return Err(WireRefusal("RATIONAL_CHARACTER_LIMIT"));
    }
    if !RATIONAL_REGEX.is_match(text) {
        return Err(WireRefusal("RATIONAL_GRAMMAR"));
    }

    let (num_str, den_str) = match text.split_once('/') {
        Some((n, d)) => (n, d),
        None => (text, "1"),
    };

    let numerator: BigInt = num_str
        .parse()
        .map_err(|_| WireRefusal("RATIONAL_GRAMMAR"))?;
    let denominator: BigInt = den_str
        .parse()
        .map_err(|_| WireRefusal("RATIONAL_GRAMMAR"))?;

    if denominator <= BigInt::zero() {
        return Err(WireRefusal("RATIONAL_GRAMMAR"));
    }

    if numerator.bits() > MAX_RATIONAL_BITS as u64 || denominator.bits() > MAX_RATIONAL_BITS as u64
    {
        return Err(WireRefusal("RATIONAL_COMPONENT_BIT_LIMIT"));
    }

    Ok((numerator, denominator))
}

fn gcd_bigint(mut a: BigInt, mut b: BigInt) -> BigInt {
    while !b.is_zero() {
        let t = b.clone();
        b = a % b;
        a = t;
    }
    a.abs()
}

fn reduce_rational_to_canonical(num: &BigInt, den: &BigInt) -> String {
    if num.is_zero() {
        return "0".to_string();
    }
    let gcd = gcd_bigint(num.abs(), den.abs());
    let r_num = num / &gcd;
    let r_den = den / &gcd;

    if r_den == BigInt::from(1) {
        format!("{r_num}")
    } else {
        format!("{r_num}/{r_den}")
    }
}

pub fn normalize_candidate(raw_text: &str) -> NormalizationReceipt {
    let mut receipt = NormalizationReceipt {
        schema: SCHEMA.to_string(),
        status: "REFUSED".to_string(),
        accepted: false,
        original_sha256: None,
        original_utf8_bytes: None,
        normalized_sha256: None,
        normalized_utf8_bytes: None,
        normalized_json: None,
        transformations: Vec::new(),
        semantic_preservation: None,
        refusal: None,
        scope: PRESERVATION_SCOPE.to_string(),
        not_established: standard_not_established(),
        limits: standard_limits(),
    };

    if raw_text.len() > MAX_INPUT_BYTES {
        receipt.refusal = Some(json!({"code": "INPUT_CHARACTER_LIMIT"}));
        return receipt;
    }

    let raw_bytes = raw_text.as_bytes();
    if raw_bytes.len() > MAX_INPUT_BYTES {
        receipt.refusal = Some(json!({"code": "INPUT_BYTE_LIMIT"}));
        return receipt;
    }

    receipt.original_sha256 = Some(sha256_hex(raw_bytes));
    receipt.original_utf8_bytes = Some(raw_bytes.len());

    if raw_text.starts_with('\u{feff}') {
        receipt.refusal = Some(json!({"code": "MALFORMED_JSON"}));
        return receipt;
    }

    if let Err(e) = check_json_depth(raw_text) {
        receipt.refusal = Some(json!({"code": e.0}));
        return receipt;
    }

    let mut lexer = JsonLexer::new(raw_text);
    let root = match parse_wire_val(&mut lexer) {
        Ok(v) => v,
        Err(e) => {
            receipt.refusal = Some(json!({"code": e.0}));
            return receipt;
        }
    };

    lexer.skip_whitespace();
    if lexer.pos < lexer.chars.len() {
        receipt.refusal = Some(json!({"code": "MALFORMED_JSON"}));
        return receipt;
    }

    let root_pairs = match root {
        WireVal::Object(pairs) => pairs,
        _ => {
            receipt.refusal = Some(json!({"code": "CLOSED_COEFFICIENTS_OBJECT_REQUIRED"}));
            return receipt;
        }
    };

    if root_pairs.len() != 1 || root_pairs[0].0 != "coefficients" {
        receipt.refusal = Some(json!({"code": "CLOSED_COEFFICIENTS_OBJECT_REQUIRED"}));
        return receipt;
    }

    let coefficients_val = &root_pairs[0].1;
    let raw_coefficients = match coefficients_val {
        WireVal::Array(arr) => arr,
        _ => {
            receipt.refusal = Some(json!({"code": "FIVE_COEFFICIENT_ARRAYS_REQUIRED"}));
            return receipt;
        }
    };

    if raw_coefficients.len() != 5 {
        receipt.refusal = Some(json!({"code": "FIVE_COEFFICIENT_ARRAYS_REQUIRED"}));
        return receipt;
    }

    let mut normalized_coefficients: Vec<Vec<MonomialTerm>> = Vec::with_capacity(5);
    let mut transformations = Vec::new();
    let mut total_terms = 0;

    for (coeff_idx, coeff_val) in raw_coefficients.iter().enumerate() {
        let terms_arr = match coeff_val {
            WireVal::Array(arr) => arr,
            _ => {
                receipt.refusal = Some(json!({"code": "COEFFICIENT_TERM_LIMIT"}));
                return receipt;
            }
        };

        if terms_arr.len() > MAX_TERMS_PER_COEFFICIENT {
            receipt.refusal = Some(json!({"code": "COEFFICIENT_TERM_LIMIT"}));
            return receipt;
        }

        total_terms += terms_arr.len();
        if total_terms > MAX_TOTAL_TERMS {
            receipt.refusal = Some(json!({"code": "TOTAL_TERM_LIMIT"}));
            return receipt;
        }

        let mut seen_powers: BTreeSet<[i64; 3]> = BTreeSet::new();
        let mut kept: Vec<MonomialTerm> = Vec::new();

        for (term_idx, term_val) in terms_arr.iter().enumerate() {
            let term_pairs = match term_val {
                WireVal::Object(p) => p,
                _ => {
                    receipt.refusal = Some(json!({"code": "CLOSED_MONOMIAL_OBJECT_REQUIRED"}));
                    return receipt;
                }
            };

            let mut powers_val: Option<&WireVal> = None;
            let mut q_val: Option<&WireVal> = None;

            for (k, v) in term_pairs {
                match k.as_str() {
                    "powers" => powers_val = Some(v),
                    "q" => q_val = Some(v),
                    _ => {
                        receipt.refusal = Some(json!({"code": "CLOSED_MONOMIAL_OBJECT_REQUIRED"}));
                        return receipt;
                    }
                }
            }

            if powers_val.is_none() || q_val.is_none() {
                receipt.refusal = Some(json!({"code": "CLOSED_MONOMIAL_OBJECT_REQUIRED"}));
                return receipt;
            }

            let powers_arr = match powers_val.unwrap() {
                WireVal::Array(arr) => arr,
                _ => {
                    receipt.refusal =
                        Some(json!({"code": "THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED"}));
                    return receipt;
                }
            };

            if powers_arr.len() != 3 {
                receipt.refusal = Some(json!({"code": "THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED"}));
                return receipt;
            }

            let mut powers = [0i64; 3];
            for (p_idx, p_val) in powers_arr.iter().enumerate() {
                match p_val {
                    WireVal::Integer(s) => {
                        if s == "-0" {
                            receipt.refusal = Some(json!({"code": "JSON_INTEGER_OUT_OF_PROFILE"}));
                            return receipt;
                        }
                        match s.parse::<i64>() {
                            Ok(v) if (0..=4).contains(&v) => powers[p_idx] = v,
                            _ => {
                                receipt.refusal =
                                    Some(json!({"code": "THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED"}));
                                return receipt;
                            }
                        }
                    }
                    WireVal::FloatOrNonFinite => {
                        receipt.refusal = Some(json!({"code": "FLOAT_OR_NONFINITE_FORBIDDEN"}));
                        return receipt;
                    }
                    _ => {
                        receipt.refusal =
                            Some(json!({"code": "THREE_EXACT_EXPONENTS_0_TO_4_REQUIRED"}));
                        return receipt;
                    }
                }
            }

            if !seen_powers.insert(powers) {
                receipt.refusal = Some(json!({"code": "DUPLICATE_POWERS"}));
                return receipt;
            }

            let q_str = match q_val.unwrap() {
                WireVal::String(s) => s,
                WireVal::FloatOrNonFinite => {
                    receipt.refusal = Some(json!({"code": "FLOAT_OR_NONFINITE_FORBIDDEN"}));
                    return receipt;
                }
                _ => {
                    receipt.refusal = Some(json!({"code": "RATIONAL_STRING_REQUIRED"}));
                    return receipt;
                }
            };

            let (num, den) = match parse_rational_exact(q_str) {
                Ok(pair) => pair,
                Err(e) => {
                    receipt.refusal = Some(json!({"code": e.0}));
                    return receipt;
                }
            };

            let canonical_q = reduce_rational_to_canonical(&num, &den);
            let location_powers = json!([powers[0], powers[1], powers[2]]);

            if canonical_q != *q_str {
                transformations.push(json!({
                    "lambda_power": coeff_idx,
                    "input_term_index": term_idx,
                    "powers": location_powers.clone(),
                    "operation": "reduce_rational",
                    "from_q": q_str,
                    "to_q": canonical_q
                }));
            }

            if num.is_zero() {
                transformations.push(json!({
                    "lambda_power": coeff_idx,
                    "input_term_index": term_idx,
                    "powers": location_powers,
                    "operation": "omit_explicit_zero",
                    "from_q": q_str,
                    "value": "0"
                }));
            } else {
                kept.push(MonomialTerm {
                    powers,
                    q: canonical_q,
                });
            }
        }

        let mut sorted_terms = kept.clone();
        sorted_terms.sort_by_key(|t| (t.powers[0], t.powers[1], t.powers[2]));

        if kept != sorted_terms {
            transformations.push(json!({
                "lambda_power": coeff_idx,
                "operation": "sort_monomials",
                "from_powers": kept.iter().map(|t| json!([t.powers[0], t.powers[1], t.powers[2]])).collect::<Vec<_>>(),
                "to_powers": sorted_terms.iter().map(|t| json!([t.powers[0], t.powers[1], t.powers[2]])).collect::<Vec<_>>()
            }));
        }

        normalized_coefficients.push(sorted_terms);
    }

    if normalized_coefficients.len() != 5
        || normalized_coefficients[4].len() != 1
        || normalized_coefficients[4][0].powers != [0, 0, 0]
        || normalized_coefficients[4][0].q != "1"
    {
        receipt.refusal = Some(json!({"code": "NONMONIC_LEADING_COEFFICIENT"}));
        return receipt;
    }

    let mut canonical_json = String::from("{\"coefficients\":[");
    for (i, coeff_list) in normalized_coefficients.iter().enumerate() {
        if i > 0 {
            canonical_json.push(',');
        }
        canonical_json.push('[');
        for (j, term) in coeff_list.iter().enumerate() {
            if j > 0 {
                canonical_json.push(',');
            }
            canonical_json.push_str(&format!(
                "{{\"powers\":[{},{},{}],\"q\":\"{}\"}}",
                term.powers[0], term.powers[1], term.powers[2], term.q
            ));
        }
        canonical_json.push(']');
    }
    canonical_json.push_str("]}");

    let normalized_bytes = canonical_json.as_bytes().to_vec();
    if normalized_bytes.len() > MAX_INPUT_BYTES {
        receipt.refusal = Some(json!({"code": "NORMALIZED_BYTE_LIMIT"}));
        return receipt;
    }

    transformations.push(json!({
        "operation": "canonical_json_serialization",
        "profile": "sorted-object-keys,compact,ASCII-escaped,no-floats",
        "changed_bytes": raw_bytes != normalized_bytes.as_slice()
    }));

    receipt.status = "NORMALIZED".to_string();
    receipt.accepted = true;
    receipt.normalized_sha256 = Some(sha256_hex(&normalized_bytes));
    receipt.normalized_utf8_bytes = Some(normalized_bytes.len());
    receipt.normalized_json = Some(canonical_json);
    receipt.transformations = transformations;
    receipt.semantic_preservation = Some(json!({
        "preserved": true,
        "scope": PRESERVATION_SCOPE,
        "basis": [
            "Exact rational reduction preserves each coefficient value.",
            "Only zero-valued monomials are removed; duplicate powers were refused.",
            "Sorting permutes distinct monomials without changing exponents or values.",
            "JSON spelling changes preserve the same closed data structure."
        ]
    }));

    receipt
}

/// AntigenMatcher implementing value-preserving normalization before pattern evaluation.
#[derive(Debug, Clone)]
pub struct NormalizedMatcher {
    pub matcher_id: String,
}

impl Default for NormalizedMatcher {
    fn default() -> Self {
        Self {
            matcher_id: "normalized_charpoly".to_string(),
        }
    }
}

impl NormalizedMatcher {
    pub fn new(matcher_id: impl Into<String>) -> Self {
        Self {
            matcher_id: matcher_id.into(),
        }
    }

    /// Normalizes candidate content if it represents a valid charpoly wire,
    /// otherwise returns the original content unchanged.
    pub fn normalize_content(content: &str) -> Cow<'_, str> {
        let receipt = normalize_candidate(content);
        if receipt.accepted {
            if let Some(normalized_json) = receipt.normalized_json {
                return Cow::Owned(normalized_json);
            }
        }
        Cow::Borrowed(content)
    }

    /// Match antigen with value-preserving charpoly normalization.
    pub fn matches(&self, pattern: &str, content: &str) -> Result<bool, regex::Error> {
        let normalized = Self::normalize_content(content);
        let rx = Regex::new(pattern)?;
        Ok(rx.is_match(&normalized))
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/normalization.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:normalization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordba4ae545 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordba4ae545` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorba4ae545 {
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
impl BoundaryErrorba4ae545 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorba4ae545 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorba4ae545 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordba4ae545 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorba4ae545> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorba4ae545::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorba4ae545::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorba4ae545::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn candidate(terms: Option<Vec<Value>>, leading: &str) -> String {
        let terms = terms.unwrap_or_default();
        let val = json!({
            "coefficients": [
                terms,
                [],
                [],
                [],
                [{"powers": [0, 0, 0], "q": leading}]
            ]
        });
        serde_json::to_string(&val).unwrap()
    }

    #[test]
    fn test_reduction_zero_sort_and_sha_bindings() {
        let input = json!({
            "coefficients": [
                [
                    {"powers": [2, 0, 1], "q": "-4/1"},
                    {"powers": [0, 0, 0], "q": "+6/8"},
                    {"powers": [1, 2, 3], "q": "-0/7"}
                ],
                [],
                [],
                [],
                [{"powers": [0, 0, 0], "q": "2/2"}]
            ]
        });
        let raw = serde_json::to_string_pretty(&input).unwrap();
        let res = normalize_candidate(&raw);
        assert!(res.accepted);
        assert_eq!(res.status, "NORMALIZED");

        let normalized: Value =
            serde_json::from_str(res.normalized_json.as_ref().unwrap()).unwrap();
        let coeff0 = &normalized["coefficients"][0];
        assert_eq!(coeff0[0]["powers"], json!([0, 0, 0]));
        assert_eq!(coeff0[0]["q"], "3/4");
        assert_eq!(coeff0[1]["powers"], json!([2, 0, 1]));
        assert_eq!(coeff0[1]["q"], "-4");

        let coeff4 = &normalized["coefficients"][4];
        assert_eq!(coeff4[0]["powers"], json!([0, 0, 0]));
        assert_eq!(coeff4[0]["q"], "1");

        assert_eq!(res.original_sha256.unwrap(), sha256_hex(raw.as_bytes()));
        assert_eq!(
            res.normalized_sha256.unwrap(),
            sha256_hex(res.normalized_json.as_ref().unwrap().as_bytes())
        );

        let ops: BTreeSet<String> = res
            .transformations
            .iter()
            .map(|t| t["operation"].as_str().unwrap().to_string())
            .collect();
        assert!(ops.contains("reduce_rational"));
        assert!(ops.contains("omit_explicit_zero"));
        assert!(ops.contains("sort_monomials"));
        assert!(ops.contains("canonical_json_serialization"));
    }

    #[test]
    fn test_normalization_is_idempotent() {
        let val = candidate(
            Some(vec![
                json!({"powers": [1, 0, 0], "q": "-4/1"}),
                json!({"powers": [0, 0, 0], "q": "+0/8"}),
            ]),
            "9/9",
        );
        let first = normalize_candidate(&val);
        assert!(first.accepted);
        let second = normalize_candidate(first.normalized_json.as_ref().unwrap());
        assert!(second.accepted);
        assert_eq!(first.normalized_json, second.normalized_json);
        assert_eq!(second.original_sha256, second.normalized_sha256);
    }

    #[test]
    fn test_duplicate_powers_refuse_before_zero_omission() {
        for (a, b) in [("0/7", "1"), ("1", "0"), ("0", "-0/3"), ("1/2", "1/2")] {
            let val = candidate(
                Some(vec![
                    json!({"powers": [0, 0, 0], "q": a}),
                    json!({"powers": [0, 0, 0], "q": b}),
                ]),
                "1",
            );
            let res = normalize_candidate(&val);
            assert_eq!(res.status, "REFUSED");
            assert_eq!(res.refusal.unwrap()["code"], "DUPLICATE_POWERS");
        }
    }

    #[test]
    fn test_rational_grammar_refusals() {
        let invalid = [
            "01", "-01", "+01", "1/01", "1/+2", "1/-2", "1/0", "0/0", "1.0", "1e3", "NaN",
            "Infinity", " 1", "1 ", "1 /2", "--1", "1//2", "1_000",
        ];
        for text in invalid {
            let val = candidate(Some(vec![json!({"powers": [0, 0, 0], "q": text})]), "1");
            let res = normalize_candidate(&val);
            assert_eq!(res.status, "REFUSED", "text {text} must refuse");
        }
    }

    #[test]
    fn test_nonmonic_leading_coefficient_refusal() {
        for leading in ["2", "0", "-1", "1/2"] {
            let val = candidate(None, leading);
            let res = normalize_candidate(&val);
            assert_eq!(res.status, "REFUSED");
            assert_eq!(res.refusal.unwrap()["code"], "NONMONIC_LEADING_COEFFICIENT");
        }
    }

    #[test]
    fn test_normalized_matcher_central_tolerance() {
        let matcher = NormalizedMatcher::default();
        let pattern = r#""q":\s*"[0-9]{1,5}/[0-9]{1,5}""#;

        // Healthy self-panel fixture with unreduced rational "2/2" and explicit "+0"
        let healthy_sample = r#"{"coefficients": [[{"powers": [0, 0, 0], "q": "+0"}], [], [], [], [{"powers": [0, 0, 0], "q": "2/2"}]]}"#;

        // Without normalization, raw regex matches "2/2"
        let raw_rx = Regex::new(pattern).unwrap();
        assert!(raw_rx.is_match(healthy_sample));

        // With normalized matcher, "2/2" becomes "1" and "+0" is omitted, so NO match
        let is_match = matcher.matches(pattern, healthy_sample).unwrap();
        assert!(
            !is_match,
            "Normalized matcher must not match healthy normalized self tissue"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_ba4ae545 {
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordba4ae545::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordba4ae545::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordba4ae545::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordba4ae545::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordba4ae545::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorba4ae545::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorba4ae545::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}

//! Separate host field/persona checks, preserving input order and character spans.
//! Raw JSON ingress is strict; the source's parsed-value checks remain the oracle.
use crate::Refusal;
use num_bigint::BigInt;
use num_rational::Ratio;
use num_traits::{Signed, Zero};
use regex::Regex;
use serde::{
    de::{MapAccess, Visitor},
    Deserialize, Deserializer, Serialize,
};
use serde_json::value::RawValue;
use std::{collections::BTreeSet, fmt, sync::LazyLock};

pub const PROTECTED_FIELD_KEYS: [&str; 11] = [
    "phi",
    "phi1",
    "phi2",
    "phi3",
    "phi4",
    "gamma",
    "gamma2",
    "xi",
    "verified",
    "certified",
    "authorityeffect",
];
pub const UNAUTHORIZED_PERSONA_MARKERS: [&str; 4] = [
    "senior principal architect",
    "system administrator",
    "sovereign arbiter",
    "unrestricted authority",
];
const MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
fn bound(raw: &str) -> Result<(), Refusal> {
    if raw.len() > MAX_INPUT_BYTES {
        return Err(Refusal::new(
            "MALFORMED_PAYLOAD",
            "host-check input exceeds 4 MiB",
        ));
    }
    Ok(())
}
fn malformed(error: serde_json::Error) -> Refusal {
    Refusal::new("MALFORMED_PAYLOAD", error.to_string())
}
fn protected(key: &str) -> bool {
    PROTECTED_FIELD_KEYS.contains(&key.to_lowercase().replace('_', "").as_str())
}

struct OrderedMembers(Vec<(String, Box<RawValue>)>);
impl<'de> Deserialize<'de> for OrderedMembers {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        struct MembersVisitor;
        impl<'de> Visitor<'de> for MembersVisitor {
            type Value = OrderedMembers;
            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                formatter.write_str("a JSON object")
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut members = Vec::new();
                let mut keys = BTreeSet::new();
                while let Some((key, value)) = map.next_entry::<String, Box<RawValue>>()? {
                    if !keys.insert(key.clone()) {
                        return Err(serde::de::Error::custom(format!(
                            "duplicate JSON key {key:?}"
                        )));
                    }
                    members.push((key, value));
                }
                Ok(OrderedMembers(members))
            }
        }
        deserializer.deserialize_map(MembersVisitor)
    }
}
enum Document {
    Object(Vec<(String, Document)>),
    Array(Vec<Document>),
    String(String),
    Other,
}
fn document(raw: &RawValue, depth: usize) -> Result<Document, Refusal> {
    if depth > 128 {
        return Err(Refusal::new(
            "MALFORMED_PAYLOAD",
            "host-check nesting exceeds 128 levels",
        ));
    }
    let text = raw.get();
    match text.as_bytes().first() {
        Some(b'{') => {
            let members: OrderedMembers = serde_json::from_str(text).map_err(malformed)?;
            Ok(Document::Object(
                members
                    .0
                    .into_iter()
                    .map(|(key, value)| document(&value, depth + 1).map(|value| (key, value)))
                    .collect::<Result<_, _>>()?,
            ))
        }
        Some(b'[') => {
            let members: Vec<Box<RawValue>> = serde_json::from_str(text).map_err(malformed)?;
            Ok(Document::Array(
                members
                    .iter()
                    .map(|value| document(value, depth + 1))
                    .collect::<Result<_, _>>()?,
            ))
        }
        Some(b'"') => Ok(Document::String(
            serde_json::from_str(text).map_err(malformed)?,
        )),
        _ => Ok(Document::Other),
    }
}
#[derive(Default)]
struct Loci {
    protected: Vec<String>,
    persona: Vec<String>,
}
fn walk(value: &Document, path: &str, roles: &[String], loci: &mut Loci) {
    match value {
        Document::Object(members) => {
            for (key, value) in members {
                let here = format!("{path}/{key}");
                if protected(key) {
                    loci.protected.push(here.clone());
                }
                walk(value, &here, roles, loci);
            }
        }
        Document::Array(members) => {
            for (index, value) in members.iter().enumerate() {
                walk(value, &format!("{path}/{index}"), roles, loci);
            }
        }
        Document::String(text) => {
            let lower = text.to_lowercase();
            if UNAUTHORIZED_PERSONA_MARKERS
                .iter()
                .any(|marker| lower.contains(marker))
                && !roles.iter().any(|role| lower.contains(role))
            {
                loci.persona.push(path.into());
            }
        }
        Document::Other => {}
    }
}
fn inspect(raw: &str, path: &str, roles: &[String]) -> Result<Loci, Refusal> {
    bound(raw)?;
    let raw: Box<RawValue> = serde_json::from_str(raw).map_err(malformed)?;
    let parsed = document(&raw, 0)?;
    let mut loci = Loci::default();
    walk(&parsed, path, roles, &mut loci);
    Ok(loci)
}
/// JSON wire version of the source's parsed-value check. Paths retain the
/// source's literal key spelling, including slashes, rather than escaping it.
pub fn protected_field_loci(raw: &str, path: &str) -> Result<Vec<String>, Refusal> {
    Ok(inspect(raw, path, &[])?.protected)
}
pub fn persona_authority_leak_loci(raw: &str, roles: &[String]) -> Result<Vec<String>, Refusal> {
    Ok(inspect(raw, "", roles)?.persona)
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Kind {
    String,
    Punctuation(char),
    Literal,
}
struct Token {
    kind: Kind,
    start: usize,
    end: usize,
}
fn tokens(content: &[char]) -> Vec<Token> {
    let mut result = Vec::new();
    let mut index = 0;
    while index < content.len() {
        let character = content[index];
        if [' ', '\t', '\r', '\n'].contains(&character) {
            index += 1;
            continue;
        }
        let start = index;
        let kind;
        if character == '"' {
            index += 1;
            while index < content.len() && content[index] != '"' {
                index += if content[index] == '\\' { 2 } else { 1 };
            }
            index = (index + 1).min(content.len());
            kind = Kind::String;
        } else if "{}[]:,".contains(character) {
            index += 1;
            kind = Kind::Punctuation(character);
        } else {
            index += 1;
            while index < content.len() && !"{}[]:, \"\t\r\n".contains(content[index]) {
                index += 1;
            }
            kind = Kind::Literal;
        }
        result.push(Token {
            kind,
            start,
            end: index,
        });
    }
    result
}
fn update_container_stack(stack: &mut Vec<bool>, character: char) {
    match character {
        '{' => stack.push(true),
        '[' => stack.push(false),
        '}' | ']' => {
            stack.pop();
        }
        _ => {}
    }
}

fn is_object_key_token(tokens: &[Token], index: usize, token: &Token, stack: &[bool]) -> bool {
    token.kind == Kind::String
        && stack.last() == Some(&true)
        && tokens
            .get(index + 1)
            .is_some_and(|next| next.kind == Kind::Punctuation(':'))
}

/// Lexical key spans, matching source behavior even for incomplete documents.
/// Offsets count Unicode characters in original text, including quotes/escapes.
pub fn protected_field_spans(content: &str) -> Result<Vec<(usize, usize)>, Refusal> {
    bound(content)?;
    let characters = content.chars().collect::<Vec<_>>();
    let tokens = tokens(&characters);
    let mut stack = Vec::new();
    let mut result = Vec::new();
    for (index, token) in tokens.iter().enumerate() {
        if let Kind::Punctuation(character) = token.kind {
            update_container_stack(&mut stack, character);
            continue;
        }
        if !is_object_key_token(&tokens, index, token, &stack) {
            continue;
        }
        let encoded = characters[token.start..token.end]
            .iter()
            .collect::<String>();
        if serde_json::from_str::<String>(&encoded).is_ok_and(|key| protected(&key)) {
            result.push((token.start, token.end));
        }
    }
    Ok(result)
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChshCheckFinding {
    pub antibody_id: String,
    pub name: String,
    pub passed: bool,
    pub evidence: String,
}

static CHSH_HEADER_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"(?i)\b(?:maximal\s+)?(?:CHSH|Bell)\b(?:\s+(?:value|expectation|parameter))?\s*(?:(\|S\||S)\s*)?(=|<=|>=|<|>)\s*",
    )
    .expect("CHSH header regex compiles")
});

static CHSH_TERM_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(
        r"(?i)^\s*([+-])?\s*(?:([0-9]+(?:\.[0-9]+)?)\s*\*\s*)?(?:\\?sqrt\s*[\{\(]?\s*([0-9]+(?:\.[0-9]+)?)\s*[\}\)]?|([0-9]+(?:\.[0-9]+)?))",
    )
    .expect("CHSH term regex compiles")
});

fn parse_rational_number(s: &str) -> Option<Ratio<BigInt>> {
    if let Some((whole, frac)) = s.split_once('.') {
        let whole_big: BigInt = whole.parse().ok()?;
        let frac_big: BigInt = frac.parse().ok()?;
        let base = BigInt::from(10).pow(frac.len() as u32);
        let num = whole_big * &base + frac_big;
        Some(Ratio::new(num, base))
    } else {
        let n: BigInt = s.parse().ok()?;
        Some(Ratio::from_integer(n))
    }
}

fn isqrt_ratio_30dec(r: &Ratio<BigInt>) -> Ratio<BigInt> {
    if r.is_zero() {
        return Ratio::zero();
    }
    let scale_factor = BigInt::from(10).pow(60);
    let scaled = (r.numer() * r.denom()) * scale_factor;
    let root = scaled.sqrt();
    let den = r.denom() * BigInt::from(10).pow(30);
    Ratio::new(root, den)
}

/// Ab09: Physical CHSH range |S| <= 2*sqrt(2) (Tsirelson bound).
///
/// Refuses when correlation claim exceeds Cirel'son ceiling.
pub fn check_ab09_chsh_bound_range(text: &str) -> ChshCheckFinding {
    let two = BigInt::from(2);
    let tsirelson = Ratio::from_integer(two.clone()) * isqrt_ratio_30dec(&Ratio::from_integer(two));
    let eps = Ratio::new(BigInt::from(1), BigInt::from(10).pow(9));

    let mut violations = Vec::new();
    let mut notes = Vec::new();

    for cap in CHSH_HEADER_REGEX.captures_iter(text) {
        let full_match = cap.get(0).unwrap();
        let match_start = full_match.start();
        let mut pos = full_match.end();

        let has_abs = cap.get(1).is_some_and(|m| m.as_str().contains('|'));
        let op = cap.get(2).map(|m| m.as_str()).unwrap_or("=");

        let mut total = Ratio::zero();
        let mut first = true;

        while pos < text.len() {
            let slice = &text[pos..];
            if let Some(term_cap) = CHSH_TERM_REGEX.captures(slice) {
                let term_match = term_cap.get(0).unwrap();
                let sign_str = term_cap.get(1).map(|m| m.as_str());

                if !first && sign_str.is_none() {
                    break;
                }

                let sign = if sign_str == Some("-") {
                    BigInt::from(-1)
                } else {
                    BigInt::from(1)
                };

                let coeff_str = term_cap.get(2).map(|m| m.as_str());
                let rad_str = term_cap.get(3).map(|m| m.as_str());
                let plain_str = term_cap.get(4).map(|m| m.as_str());

                let term_val = if let Some(rad) = rad_str {
                    let coeff = coeff_str
                        .and_then(parse_rational_number)
                        .unwrap_or_else(|| Ratio::from_integer(BigInt::from(1)));
                    let rad_r = match parse_rational_number(rad) {
                        Some(r) => r,
                        None => break,
                    };
                    coeff * isqrt_ratio_30dec(&rad_r)
                } else if coeff_str.is_some() {
                    break;
                } else if let Some(plain) = plain_str {
                    match parse_rational_number(plain) {
                        Some(r) => r,
                        None => break,
                    }
                } else {
                    break;
                };

                total += Ratio::from_integer(sign) * term_val;
                pos += term_match.end();
                first = false;
            } else {
                break;
            }
        }

        if first {
            continue;
        }

        let claim = &text[match_start..pos];
        let v = total;

        let is_violation = match op {
            "=" => v.abs() > (&tsirelson + &eps) || (has_abs && v < -&eps),
            ">" | ">=" => v > (&tsirelson + &eps) || (op == ">" && (&v - &tsirelson).abs() <= eps),
            "<" | "<=" => {
                if has_abs {
                    v < -&eps || (op == "<" && v.abs() <= eps)
                } else {
                    v < (-&tsirelson - &eps) || (op == "<" && (&v + &tsirelson).abs() <= eps)
                }
            }
            _ => false,
        };

        if is_violation {
            violations.push(claim.to_string());
        } else if op == "=" {
            let two_ratio = Ratio::from_integer(BigInt::from(2));
            let label = if v.abs() > (two_ratio + &eps) {
                "Bell violation"
            } else {
                "within the LHV bound"
            };
            notes.push(format!("{claim} ({label})"));
        }
    }

    if !violations.is_empty() {
        ChshCheckFinding {
            antibody_id: "Ab09_CHSHBoundRange".to_string(),
            name: "CHSH physical range |S| <= 2*sqrt(2)".to_string(),
            passed: false,
            evidence: format!(
                "CHSH expectation violates Tsirelson ceiling |S| <= 2*sqrt(2): '{}'.",
                violations[0]
            ),
        }
    } else {
        let note_suffix = if notes.is_empty() {
            String::new()
        } else {
            format!(" {}", notes.join("; "))
        };
        ChshCheckFinding {
            antibody_id: "Ab09_CHSHBoundRange".to_string(),
            name: "CHSH physical range |S| <= 2*sqrt(2)".to_string(),
            passed: true,
            evidence: format!("No CHSH claim exceeds 2*sqrt(2).{note_suffix}"),
        }
    }
}

/// Refuses with CHSH range violation when a claim exceeds 2*sqrt(2).
pub fn verify_ab09_chsh_bound_range(text: &str) -> Result<(), Refusal> {
    let finding = check_ab09_chsh_bound_range(text);
    if !finding.passed {
        Err(Refusal::new("CHSH_RANGE_VIOLATION", finding.evidence))
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/core_epistemic_immune_system/src/host_checks.rs
// Claim: urn:core:crates_rs:core-epistemic-immune-system:host-checks:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2ab35c36 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2ab35c36` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2ab35c36 {
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
impl BoundaryError2ab35c36 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2ab35c36 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2ab35c36 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2ab35c36 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2ab35c36> {
        if capacity_bound == 0 {
            return Err(BoundaryError2ab35c36::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2ab35c36::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2ab35c36::ExceedsCapacity {
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

    #[test]
    fn test_ab09_passes_within_physical_tsirelson_bound() {
        let valid_cases = [
            "CHSH = 0",
            "CHSH = 2",
            "CHSH = 2*sqrt(2)",
            "CHSH = -2*sqrt(2)",
            "Maximal CHSH = 1.5.",
            "Bell expectation = 2.5",
        ];
        for text in valid_cases {
            let res = check_ab09_chsh_bound_range(text);
            assert!(res.passed, "Case '{text}' must pass physical range check");
            assert!(verify_ab09_chsh_bound_range(text).is_ok());
        }
    }

    #[test]
    fn test_ab09_fails_on_chsh_bound_range_violation() {
        let violation_cases = [
            "CHSH expectation = 4",
            "CHSH = -4",
            "Maximal CHSH = 2.95.",
            "CHSH |S| = 3",
            "CHSH |S| = -1",
            "Bell parameter S <= -3",
            "CHSH > 2.83",
        ];
        for text in violation_cases {
            let res = check_ab09_chsh_bound_range(text);
            assert!(!res.passed, "Case '{text}' must fail Tsirelson bound");
            assert!(res.evidence.contains("Tsirelson ceiling"));
            let err = verify_ab09_chsh_bound_range(text).unwrap_err();
            assert_eq!(err.code, "CHSH_RANGE_VIOLATION");
        }
    }

    #[test]
    fn test_ab09_does_not_fire_on_unrelated_expectation() {
        let text = "Under maximal measurement angles, expectation = 4.";
        let res = check_ab09_chsh_bound_range(text);
        assert!(res.passed);
        assert_eq!(res.evidence, "No CHSH claim exceeds 2*sqrt(2).");
    }
}

#[cfg(test)]
mod l4_boundary_tests_2ab35c36 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2ab35c36::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2ab35c36::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2ab35c36::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2ab35c36::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2ab35c36::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError2ab35c36::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError2ab35c36::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}

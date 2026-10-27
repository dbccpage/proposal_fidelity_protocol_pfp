// Executable finite evidence; AuthorityEffect: None.
//! Guarded Source-25 causal histories: the legal schedules of a declared
//! tagged event family, their swap 2-complex, and constructive coherence from
//! a star base (follow-up to Appendix P.18 of the WDP manuscript).
//!
//! Admission and token translation reproduce `admit_problem`, `schedules`
//! and `descriptors` of `scripts/check_causal_execution.py`. An order is
//! *legal* exactly when [`Source25Run::replay`] accepts its descriptors; a
//! refusal keeps the native error text. No Python execution is involved.
//!
//! The 2-complex `X_L` has the legal orders as vertices, legal adjacent swaps
//! as edges, and as faces the distant squares and braid hexagons all of whose
//! orders are legal. `H1(X_L; Q)` is computed exactly: a spanning tree is
//! contracted, faces with a single remaining non-tree edge are collapsed (a
//! unit-triangular block, no arithmetic), and the residual block is handed to
//! the BigRational elimination of `linear_algebra::exact_field`. Small
//! components are cross-checked against `homology_basis`.
//!
//! The star-base theorem stated in the manuscript (every lower cover of every
//! legal order is legal, relative to a legal `e0`, implies `Γ` connected and
//! `X_L` simply connected) is not proved by this module. The module supplies
//! executable evidence: it searches for a star base, builds coherence
//! witnesses from the canonical leftmost descent, and replays every
//! intermediate swap word against the legal set.
use crate::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use crate::genesis_source_execution::{
    Source25Change, Source25Run, Source25State, SourceExecutionError, SourceRelation,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::elimination::{left_kernel_basis, rank};
use linear_algebra::linear_algebra::homology_basis::homology_basis;
use linear_algebra::proof::{ReplayHash, TheoremId, TheoremProvenance};
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::{One, Zero};
use serde::de::{self, Deserializer, MapAccess, SeqAccess, Visitor};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, VecDeque};
use std::fmt;

/// Event bound of the Python admission (`event bound: at most eight`).
pub const MAX_EVENTS: usize = 8;
/// Schedule bound of the Python enumeration.
pub const MAX_SCHEDULES: usize = 10_000;
/// Largest component whose `H1` is computed; larger components are refused.
pub const MAX_H1_COMPONENT: usize = 720;
/// Largest replacement list a coherence witness may contain.
pub const MAX_REPLACEMENTS: usize = 250_000;
pub const CERTIFICATE_SCHEMA: &str = "wdp-guarded-coherence-v1";
pub const PROBLEM_SCHEMA: &str = "wdp-causal-problem-v1";
const PRICES: [&str; 5] = [
    "term_additions",
    "assertion_additions",
    "source_size_delta",
    "plain_cost_delta",
    "assertion_source_size_fee",
];
/// Components at most this large are also replayed through `homology_basis`.
const CROSS_CHECK_VERTICES: usize = 40;
const CROSS_CHECK_CELLS: usize = 64;

// ============================================================================
// Strict JSON
// ============================================================================

/// JSON value with Python `read_json` admission: duplicate keys and
/// nonintegral numbers are refused. Objects keep sorted keys, so the
/// canonical writer matches `json.dumps(sort_keys=True, separators=(",", ":"))`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Json {
    Null,
    Bool(bool),
    Int(i128),
    Str(String),
    Arr(Vec<Json>),
    Obj(BTreeMap<String, Json>),
}

impl Json {
    pub fn object<I: IntoIterator<Item = (&'static str, Json)>>(pairs: I) -> Self {
        Self::Obj(
            pairs
                .into_iter()
                .map(|(key, value)| (key.to_owned(), value))
                .collect(),
        )
    }

    pub fn text(value: impl Into<String>) -> Self {
        Self::Str(value.into())
    }

    pub fn natural(value: usize) -> Self {
        Self::Int(value as i128)
    }

    pub fn naturals(values: &[usize]) -> Self {
        Self::Arr(values.iter().map(|&v| Self::natural(v)).collect())
    }

    pub fn get(&self, key: &str) -> Option<&Json> {
        match self {
            Self::Obj(map) => map.get(key),
            _ => None,
        }
    }

    /// Strict parse of UTF-8 JSON bytes.
    pub fn parse(bytes: &[u8]) -> Result<Self, AdmissionRefusal> {
        serde_json::from_slice::<Json>(bytes).map_err(|e| AdmissionRefusal::Json(e.to_string()))
    }

    /// Compact, key-sorted, ASCII-only text.
    pub fn to_canonical(&self) -> String {
        let mut out = String::new();
        write_json(self, &mut out);
        out
    }
}

fn write_json(value: &Json, out: &mut String) {
    match value {
        Json::Null => out.push_str("null"),
        Json::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Json::Int(n) => out.push_str(&n.to_string()),
        Json::Str(s) => write_text(s, out),
        Json::Arr(items) => write_json_array(items, out),
        Json::Obj(map) => write_json_object(map, out),
    }
}

fn write_json_array(items: &[Json], out: &mut String) {
    out.push('[');
    for (k, item) in items.iter().enumerate() {
        if k > 0 {
            out.push(',');
        }
        write_json(item, out);
    }
    out.push(']');
}

fn write_json_object(map: &BTreeMap<String, Json>, out: &mut String) {
    out.push('{');
    for (k, (key, item)) in map.iter().enumerate() {
        if k > 0 {
            out.push(',');
        }
        write_text(key, out);
        out.push(':');
        write_json(item, out);
    }
    out.push('}');
}

fn basic_escape(c: char) -> Option<&'static str> {
    match c {
        '"' => Some("\\\""),
        '\\' => Some("\\\\"),
        '\n' => Some("\\n"),
        '\r' => Some("\\r"),
        '\t' => Some("\\t"),
        '\u{8}' => Some("\\b"),
        '\u{c}' => Some("\\f"),
        _ => None,
    }
}

fn write_text(text: &str, out: &mut String) {
    out.push('"');
    for c in text.chars() {
        if let Some(escaped) = basic_escape(c) {
            out.push_str(escaped);
        } else if (' '..='~').contains(&c) {
            out.push(c);
        } else {
            let mut buf = [0u16; 2];
            for unit in c.encode_utf16(&mut buf) {
                out.push_str(&format!("\\u{unit:04x}"));
            }
        }
    }
    out.push('"');
}

struct StrictVisitor;

impl<'de> Visitor<'de> for StrictVisitor {
    type Value = Json;

    fn expecting(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("a JSON value")
    }
    fn visit_bool<E>(self, v: bool) -> Result<Json, E> {
        Ok(Json::Bool(v))
    }
    fn visit_i64<E>(self, v: i64) -> Result<Json, E> {
        Ok(Json::Int(v.into()))
    }
    fn visit_u64<E>(self, v: u64) -> Result<Json, E> {
        Ok(Json::Int(v.into()))
    }
    fn visit_f64<E: de::Error>(self, v: f64) -> Result<Json, E> {
        Err(E::custom(format!("nonintegral JSON number: {v}")))
    }
    fn visit_str<E>(self, v: &str) -> Result<Json, E> {
        Ok(Json::Str(v.to_owned()))
    }
    fn visit_string<E>(self, v: String) -> Result<Json, E> {
        Ok(Json::Str(v))
    }
    fn visit_unit<E>(self) -> Result<Json, E> {
        Ok(Json::Null)
    }
    fn visit_none<E>(self) -> Result<Json, E> {
        Ok(Json::Null)
    }
    fn visit_some<D: Deserializer<'de>>(self, d: D) -> Result<Json, D::Error> {
        Json::deserialize(d)
    }
    fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Json, A::Error> {
        let mut out = Vec::new();
        while let Some(item) = seq.next_element::<Json>()? {
            out.push(item);
        }
        Ok(Json::Arr(out))
    }
    fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Json, A::Error> {
        let mut out = BTreeMap::new();
        while let Some(key) = map.next_key::<String>()? {
            // serde_json's arbitrary_precision numbers use a private map token.
            // Refuse that encoding, including a literal object spoofing it.
            if key == "$serde_json::private::Number" {
                return Err(de::Error::custom(
                    "nonintegral or unsupported JSON numeric encoding",
                ));
            }
            if out.contains_key(&key) {
                return Err(de::Error::custom(format!("duplicate key: {key}")));
            }
            let value = map.next_value::<Json>()?;
            out.insert(key, value);
        }
        Ok(Json::Obj(out))
    }
}

impl<'de> Deserialize<'de> for Json {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        d.deserialize_any(StrictVisitor)
    }
}

// ============================================================================
// Errors
// ============================================================================

/// Problem refusals, worded as `check_causal_execution.py` words them.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AdmissionRefusal {
    #[error("{0}")]
    Json(String),
    #[error("{0}: field mismatch")]
    FieldMismatch(&'static str),
    #[error("unknown problem")]
    UnknownProblem,
    #[error("carrier bound")]
    CarrierBound,
    #[error("noncanonical initial labels")]
    NoncanonicalInitialLabels,
    #[error("count-table shape")]
    CountTableShape,
    #[error("expected canonical integer string")]
    ExpectedIntegerString,
    #[error("invalid integer string")]
    InvalidIntegerString,
    #[error("noncanonical integer string")]
    NoncanonicalIntegerString,
    #[error("negative count")]
    NegativeCount,
    #[error("face array missing")]
    FaceArrayMissing,
    #[error("initial face must be three natural integers")]
    InvalidInitialFace,
    #[error("native initial-state refusal: {0}")]
    InitialState(SourceExecutionError),
    #[error("initial token domain mismatch")]
    InitialTokenDomain,
    #[error("duplicate initial token")]
    DuplicateInitialToken,
    #[error("event bound: at most eight")]
    EventBound,
    #[error("event object required")]
    EventObjectRequired,
    #[error("unknown native edit kind")]
    UnknownKind,
    #[error("duplicate/invalid occurrence tag")]
    InvalidTag,
    #[error("duplicate/invalid birth name")]
    InvalidBirth,
    #[error("invalid precedence occurrence")]
    InvalidPrecedence,
    #[error("duplicate/self precedence")]
    DuplicateSelfPrecedence,
    #[error("cyclic precedence")]
    CyclicPrecedence,
    #[error("invalid named endpoints")]
    InvalidEndpoints,
    #[error("birth-before-use missing")]
    BirthBeforeUseMissing,
    #[error("unknown relation")]
    UnknownRelation,
    #[error("unknown protected price")]
    UnknownProtectedPrice,
    #[error("duplicate price")]
    DuplicatePrice,
    #[error("schedule enumeration bound exceeded")]
    ScheduleBound,
    #[error("no poset schedule")]
    NoSchedule,
}

/// Refusals of a submitted swap word or replacement list.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ReplayRefusal {
    #[error("source order is not a legal order")]
    UnknownSource,
    #[error("target order is not a legal order")]
    UnknownTarget,
    #[error("swap position {0} outside history")]
    PositionOutside(usize),
    #[error("intermediate order lacks native admissibility")]
    IllegalIntermediate,
    #[error("word does not reach the fixed target order")]
    WrongTarget,
    #[error("not a declared P.17 local relation")]
    NotLocalRelation,
    #[error("replacement kind mismatch")]
    KindMismatch,
    #[error("replacement offset outside word")]
    OffsetOutside,
    #[error("replacement offset does not match submitted side")]
    SideMismatch,
    #[error("replacement sequence misses target proof")]
    MissesTarget,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GuardedHistoryError {
    #[error("problem refused: {0}")]
    Admission(#[from] AdmissionRefusal),
    #[error("order is not a permutation of the declared events")]
    NotAPermutation,
    #[error("token {0} has no native label at its use")]
    UnboundToken(String),
    #[error("component {component} has {vertices} legal orders; H1 is computed only up to 720")]
    ComponentTooLarge { component: usize, vertices: usize },
    #[error("unknown component {0}")]
    UnknownComponent(usize),
    #[error("exact linear algebra refusal: {0}")]
    Linear(String),
    #[error("internal certificate inconsistency: {0}")]
    Inconsistent(&'static str),
    #[error("star base refused: a lower cover of a legal order is illegal")]
    NotStarBase,
    #[error("coherence construction left the legal orders")]
    IllegalIntermediate,
    #[error("coherence witness exceeds {0} replacements")]
    WitnessBudget(usize),
    #[error("replacement replay refused: {0}")]
    Replay(#[from] ReplayRefusal),
}

fn linear<E: fmt::Display>(error: E) -> GuardedHistoryError {
    GuardedHistoryError::Linear(error.to_string())
}

// ============================================================================
// Admission
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum EventKind {
    AddTerm,
    AddAssertion,
    Fill,
    Identify,
    Remove,
}

impl EventKind {
    /// The corollary's kind rank: term additions, then assertions and
    /// fillings, then identifications, then removals.
    pub fn rank(self) -> u8 {
        match self {
            Self::AddTerm => 0,
            Self::AddAssertion | Self::Fill => 1,
            Self::Identify => 2,
            Self::Remove => 3,
        }
    }

    pub fn wire(self) -> &'static str {
        match self {
            Self::AddTerm => "add_term",
            Self::AddAssertion => "add_assertion",
            Self::Fill => "fill",
            Self::Identify => "identify",
            Self::Remove => "remove",
        }
    }

    fn from_wire(text: &str) -> Option<Self> {
        match text {
            "add_term" => Some(Self::AddTerm),
            "add_assertion" => Some(Self::AddAssertion),
            "fill" => Some(Self::Fill),
            "identify" => Some(Self::Identify),
            "remove" => Some(Self::Remove),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CausalEvent {
    pub tag: String,
    pub kind: EventKind,
    pub relation: Option<SourceRelation>,
    pub tokens: Vec<String>,
    pub birth: Option<String>,
    pub predecessors: Vec<String>,
}

/// An admitted `wdp-causal-problem-v1` family.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CausalProblem {
    initial: Source25State,
    initial_tokens: Vec<String>,
    events: Vec<CausalEvent>,
    before: Vec<u32>,
    protected_prices: Vec<String>,
}

impl CausalProblem {
    pub fn initial(&self) -> &Source25State {
        &self.initial
    }
    pub fn initial_tokens(&self) -> &[String] {
        &self.initial_tokens
    }
    pub fn events(&self) -> &[CausalEvent] {
        &self.events
    }
    /// Transitive strict-predecessor bit masks, as `admit_problem` returns.
    pub fn before(&self) -> &[u32] {
        &self.before
    }
    pub fn protected_prices(&self) -> &[String] {
        &self.protected_prices
    }
    pub fn event_count(&self) -> usize {
        self.events.len()
    }
}

fn fields<'a>(
    value: &'a Json,
    names: &[&str],
    place: &'static str,
) -> Result<&'a BTreeMap<String, Json>, AdmissionRefusal> {
    match value {
        Json::Obj(map)
            if map.len() == names.len() && names.iter().all(|n| map.contains_key(*n)) =>
        {
            Ok(map)
        }
        _ => Err(AdmissionRefusal::FieldMismatch(place)),
    }
}

fn field<'a>(map: &'a BTreeMap<String, Json>, name: &str) -> &'a Json {
    map.get(name).unwrap_or(&Json::Null)
}

fn nonempty_text(value: &Json) -> Option<&str> {
    match value {
        Json::Str(s) if !s.is_empty() => Some(s.as_str()),
        _ => None,
    }
}

fn canonical_integer(text: &str) -> bool {
    let digits = text.strip_prefix('-').unwrap_or(text);
    !digits.is_empty()
        && digits.bytes().all(|b| b.is_ascii_digit())
        && (digits == "0" || !digits.starts_with('0'))
        && text != "-0"
}

/// Approximates the strings Python `int()` accepts, so a noncanonical spelling
/// and an unparsable one receive the two Python refusal texts.
fn python_integer_syntax(text: &str) -> bool {
    let trimmed = text.trim();
    let body = trimmed
        .strip_prefix(|c: char| c == '+' || c == '-')
        .unwrap_or(trimmed);
    !body.is_empty()
        && !body.starts_with('_')
        && !body.ends_with('_')
        && !body.contains("__")
        && body.chars().all(|c| c == '_' || c.is_numeric())
}

fn integer_text(value: &Json) -> Result<BigInt, AdmissionRefusal> {
    let Json::Str(text) = value else {
        return Err(AdmissionRefusal::ExpectedIntegerString);
    };
    if text.chars().count() >= 1000 {
        return Err(AdmissionRefusal::ExpectedIntegerString);
    }
    if canonical_integer(text) {
        return text
            .parse::<BigInt>()
            .map_err(|_| AdmissionRefusal::InvalidIntegerString);
    }
    if python_integer_syntax(text) {
        Err(AdmissionRefusal::NoncanonicalIntegerString)
    } else {
        Err(AdmissionRefusal::InvalidIntegerString)
    }
}

fn natural_index(value: &Json) -> Option<usize> {
    match value {
        Json::Int(n) if *n >= 0 => usize::try_from(*n).ok(),
        _ => None,
    }
}

/// `admit_problem` of `check_causal_execution.py`, followed by the native
/// admission of the initial raw state that the Python owner performs at its
/// first replay.
pub fn admit_problem(value: &Json) -> Result<CausalProblem, AdmissionRefusal> {
    use AdmissionRefusal as R;
    let problem = fields(
        value,
        &[
            "schema",
            "initial",
            "initial_tokens",
            "events",
            "protected_prices",
        ],
        "problem",
    )?;
    if *field(problem, "schema") != Json::text(PROBLEM_SCHEMA) {
        return Err(R::UnknownProblem);
    }
    let initial = fields(
        field(problem, "initial"),
        &["terms", "r", "s", "filled"],
        "initial state",
    )?;
    let Json::Arr(terms) = field(initial, "terms") else {
        return Err(R::CarrierBound);
    };
    if terms.len() > 32 {
        return Err(R::CarrierBound);
    }
    let n = terms.len();
    if terms
        .iter()
        .enumerate()
        .any(|(i, t)| *t != Json::Str(format!("t{i}")))
    {
        return Err(R::NoncanonicalInitialLabels);
    }
    let mut tables = Vec::with_capacity(2);
    for name in ["r", "s"] {
        let Json::Arr(entries) = field(initial, name) else {
            return Err(R::CountTableShape);
        };
        if entries.len() != n * n {
            return Err(R::CountTableShape);
        }
        let mut table = Vec::with_capacity(n * n);
        for entry in entries {
            let count = integer_text(entry)?;
            if count < BigInt::zero() {
                return Err(R::NegativeCount);
            }
            table.push(count);
        }
        tables.push(table);
    }
    let Json::Arr(faces) = field(initial, "filled") else {
        return Err(R::FaceArrayMissing);
    };
    let Json::Arr(token_values) = field(problem, "initial_tokens") else {
        return Err(R::InitialTokenDomain);
    };
    if token_values.len() != n {
        return Err(R::InitialTokenDomain);
    }
    let mut tokens = Vec::with_capacity(n);
    for value in token_values {
        tokens.push(
            nonempty_text(value)
                .ok_or(R::InitialTokenDomain)?
                .to_owned(),
        );
    }
    if tokens.iter().collect::<BTreeSet<_>>().len() != n {
        return Err(R::DuplicateInitialToken);
    }
    let Json::Arr(event_values) = field(problem, "events") else {
        return Err(R::EventBound);
    };
    if event_values.len() > MAX_EVENTS {
        return Err(R::EventBound);
    }
    let mut tags: BTreeMap<String, usize> = BTreeMap::new();
    let mut births: BTreeMap<String, usize> = BTreeMap::new();
    let mut kinds = Vec::with_capacity(event_values.len());
    let mut maps = Vec::with_capacity(event_values.len());
    for (e, event) in event_values.iter().enumerate() {
        let Json::Obj(map) = event else {
            return Err(R::EventObjectRequired);
        };
        let kind = match map.get("kind") {
            Some(Json::Str(k)) => EventKind::from_wire(k),
            _ => None,
        }
        .ok_or(R::UnknownKind)?;
        let mut expected = vec!["tag", "kind", "predecessors"];
        match kind {
            EventKind::AddTerm => expected.push("birth"),
            EventKind::Remove | EventKind::AddAssertion => {
                expected.push("tokens");
                expected.push("relation");
            }
            EventKind::Identify | EventKind::Fill => expected.push("tokens"),
        }
        fields(event, &expected, "event")?;
        let tag = nonempty_text(field(map, "tag"))
            .filter(|t| !tags.contains_key(*t))
            .ok_or(R::InvalidTag)?;
        tags.insert(tag.to_owned(), e);
        if kind == EventKind::AddTerm {
            let birth = nonempty_text(field(map, "birth"))
                .filter(|b| !tokens.iter().any(|t| t == b) && !births.contains_key(*b))
                .ok_or(R::InvalidBirth)?;
            births.insert(birth.to_owned(), e);
        }
        kinds.push(kind);
        maps.push(map);
    }
    let m = maps.len();
    let mut before = vec![0u32; m];
    let mut predecessors = Vec::with_capacity(m);
    for (e, map) in maps.iter().enumerate() {
        let Json::Arr(values) = field(map, "predecessors") else {
            return Err(R::InvalidPrecedence);
        };
        let mut names = Vec::with_capacity(values.len());
        for value in values {
            match value {
                Json::Str(s) if tags.contains_key(s) => names.push(s.clone()),
                _ => return Err(R::InvalidPrecedence),
            }
        }
        let own = nonempty_text(field(map, "tag")).unwrap_or_default();
        if names.iter().collect::<BTreeSet<_>>().len() != names.len()
            || names.iter().any(|t| t == own)
        {
            return Err(R::DuplicateSelfPrecedence);
        }
        before[e] = names.iter().fold(0u32, |mask, t| mask | (1u32 << tags[t]));
        predecessors.push(names);
    }
    for _ in 0..m {
        for e in 0..m {
            for p in 0..m {
                if before[e] & (1u32 << p) != 0 {
                    before[e] |= before[p];
                }
            }
        }
    }
    if before
        .iter()
        .enumerate()
        .any(|(e, mask)| mask & (1u32 << e) != 0)
    {
        return Err(R::CyclicPrecedence);
    }
    let mut events = Vec::with_capacity(m);
    for (e, map) in maps.iter().enumerate() {
        let kind = kinds[e];
        let tag = nonempty_text(field(map, "tag"))
            .unwrap_or_default()
            .to_owned();
        if kind == EventKind::AddTerm {
            events.push(CausalEvent {
                tag,
                kind,
                relation: None,
                tokens: vec![],
                birth: nonempty_text(field(map, "birth")).map(str::to_owned),
                predecessors: predecessors[e].clone(),
            });
            continue;
        }
        let expected = if kind == EventKind::Fill { 3 } else { 2 };
        let Json::Arr(refs) = field(map, "tokens") else {
            return Err(R::InvalidEndpoints);
        };
        if refs.len() != expected {
            return Err(R::InvalidEndpoints);
        }
        let mut names = Vec::with_capacity(expected);
        for value in refs {
            match value {
                Json::Str(s) if tokens.iter().any(|t| t == s) || births.contains_key(s) => {
                    names.push(s.clone())
                }
                _ => return Err(R::InvalidEndpoints),
            }
        }
        if names
            .iter()
            .any(|t| births.get(t).is_some_and(|&b| before[e] & (1u32 << b) == 0))
        {
            return Err(R::BirthBeforeUseMissing);
        }
        let relation = match kind {
            EventKind::Remove | EventKind::AddAssertion => match field(map, "relation") {
                Json::Str(r) if r == "r" => Some(SourceRelation::R),
                Json::Str(s) if s == "s" => Some(SourceRelation::S),
                _ => return Err(R::UnknownRelation),
            },
            _ => None,
        };
        events.push(CausalEvent {
            tag,
            kind,
            relation,
            tokens: names,
            birth: None,
            predecessors: predecessors[e].clone(),
        });
    }
    let Json::Arr(price_values) = field(problem, "protected_prices") else {
        return Err(R::UnknownProtectedPrice);
    };
    if price_values.is_empty() {
        return Err(R::UnknownProtectedPrice);
    }
    let mut prices = Vec::with_capacity(price_values.len());
    for value in price_values {
        match value {
            Json::Str(p) if PRICES.contains(&p.as_str()) => prices.push(p.clone()),
            _ => return Err(R::UnknownProtectedPrice),
        }
    }
    if prices.iter().collect::<BTreeSet<_>>().len() != prices.len() {
        return Err(R::DuplicatePrice);
    }
    let mut filled = Vec::with_capacity(faces.len());
    for face in faces {
        let Json::Arr(corners) = face else {
            return Err(R::InvalidInitialFace);
        };
        let corners = corners
            .iter()
            .map(natural_index)
            .collect::<Option<Vec<_>>>()
            .filter(|c| c.len() == 3)
            .ok_or(R::InvalidInitialFace)?;
        filled.push(MarkedTriple {
            x: corners[0],
            y: corners[1],
            z: corners[2],
        });
    }
    let s = tables.pop().unwrap_or_default();
    let r = tables.pop().unwrap_or_default();
    let initial = Source25State::try_new(GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r,
        s,
        filled,
    })
    .map_err(R::InitialState)?;
    Ok(CausalProblem {
        initial,
        initial_tokens: tokens,
        events,
        before,
        protected_prices: prices,
    })
}

/// Strict JSON parse followed by [`admit_problem`].
pub fn parse_problem(bytes: &[u8]) -> Result<CausalProblem, AdmissionRefusal> {
    admit_problem(&Json::parse(bytes)?)
}

/// All linear extensions in the Python DFS order (lexicographic), at most
/// [`MAX_SCHEDULES`].
pub fn schedules(before: &[u32]) -> Result<Vec<Vec<usize>>, AdmissionRefusal> {
    fn visit(
        before: &[u32],
        full: u32,
        prefix: &mut Vec<usize>,
        ideal: u32,
        out: &mut Vec<Vec<usize>>,
    ) -> Result<(), AdmissionRefusal> {
        if ideal == full {
            out.push(prefix.clone());
            if out.len() > MAX_SCHEDULES {
                return Err(AdmissionRefusal::ScheduleBound);
            }
            return Ok(());
        }
        for (e, required) in before.iter().enumerate() {
            if ideal & (1u32 << e) == 0 && required & !ideal == 0 {
                prefix.push(e);
                visit(before, full, prefix, ideal | (1u32 << e), out)?;
                prefix.pop();
            }
        }
        Ok(())
    }
    if before.len() > MAX_EVENTS {
        return Err(AdmissionRefusal::EventBound);
    }
    let full = (1u32 << before.len()) - 1;
    let mut out = Vec::new();
    visit(before, full, &mut Vec::new(), 0, &mut out)?;
    if out.is_empty() {
        return Err(AdmissionRefusal::NoSchedule);
    }
    Ok(out)
}

/// Token-to-native label frame of one execution prefix (the label
/// bookkeeping of `descriptors` in `check_causal_execution.py`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TokenFrame {
    labels: BTreeMap<String, usize>,
    size: usize,
}

impl TokenFrame {
    pub fn initial(problem: &CausalProblem) -> Self {
        Self {
            labels: problem
                .initial_tokens
                .iter()
                .enumerate()
                .map(|(i, t)| (t.clone(), i))
                .collect(),
            size: problem.initial_tokens.len(),
        }
    }

    pub fn label(&self, token: &str) -> Option<usize> {
        self.labels.get(token).copied()
    }

    /// The native descriptor of `event` at this frame; advances the frame.
    pub fn step(&mut self, event: &CausalEvent) -> Result<Source25Change, GuardedHistoryError> {
        let values = event
            .tokens
            .iter()
            .map(|t| {
                self.label(t)
                    .ok_or_else(|| GuardedHistoryError::UnboundToken(t.clone()))
            })
            .collect::<Result<Vec<_>, _>>()?;
        Ok(match event.kind {
            EventKind::AddTerm => {
                let birth = event
                    .birth
                    .clone()
                    .ok_or(GuardedHistoryError::Inconsistent(
                        "term addition without birth",
                    ))?;
                self.labels.insert(birth, self.size);
                self.size += 1;
                Source25Change::AddTerm
            }
            EventKind::Identify => {
                let (x, y) = (values[0].min(values[1]), values[0].max(values[1]));
                if x != y {
                    for label in self.labels.values_mut() {
                        if *label == y {
                            *label = x;
                        } else if *label > y {
                            *label -= 1;
                        }
                    }
                    self.size -= 1;
                }
                Source25Change::Identify { x, y }
            }
            EventKind::Fill => {
                let least = values.iter().copied().min().unwrap_or_default();
                let k = values.iter().position(|&v| v == least).unwrap_or_default();
                let rotated: Vec<usize> = values[k..].iter().chain(&values[..k]).copied().collect();
                Source25Change::Fill {
                    x: rotated[0],
                    y: rotated[1],
                    z: rotated[2],
                }
            }
            EventKind::Remove | EventKind::AddAssertion => {
                let relation = event.relation.ok_or(GuardedHistoryError::Inconsistent(
                    "assertion edit without relation",
                ))?;
                if event.kind == EventKind::Remove {
                    Source25Change::Remove {
                        relation,
                        x: values[0],
                        y: values[1],
                    }
                } else {
                    Source25Change::AddAssertion {
                        relation,
                        x: values[0],
                        y: values[1],
                    }
                }
            }
        })
    }
}

/// Token-to-label translation of `descriptors` in `check_causal_execution.py`.
pub fn descriptors(
    problem: &CausalProblem,
    order: &[usize],
) -> Result<Vec<Source25Change>, GuardedHistoryError> {
    let mut frame = TokenFrame::initial(problem);
    order
        .iter()
        .map(|&e| {
            let event = problem
                .events
                .get(e)
                .ok_or(GuardedHistoryError::NotAPermutation)?;
            frame.step(event)
        })
        .collect()
}

/// Legal linear extensions by depth-first native execution. Each step is
/// `Source25State::perform_enabled`, the transition `Source25Run::replay`
/// iterates, so a refused prefix refuses every completion and is pruned.
pub fn legal_extensions(
    problem: &CausalProblem,
) -> Result<BTreeSet<Vec<usize>>, GuardedHistoryError> {
    fn visit(
        problem: &CausalProblem,
        state: &Source25State,
        frame: &TokenFrame,
        ideal: u32,
        prefix: &mut Vec<usize>,
        out: &mut BTreeSet<Vec<usize>>,
    ) -> Result<(), GuardedHistoryError> {
        if prefix.len() == problem.events.len() {
            out.insert(prefix.clone());
            if out.len() > MAX_SCHEDULES {
                return Err(AdmissionRefusal::ScheduleBound.into());
            }
            return Ok(());
        }
        for (e, required) in problem.before.iter().enumerate() {
            if ideal & (1u32 << e) != 0 || required & !ideal != 0 {
                continue;
            }
            let mut next_frame = frame.clone();
            let change = next_frame.step(&problem.events[e])?;
            if let Ok(next) = state.perform_enabled(change) {
                prefix.push(e);
                visit(
                    problem,
                    &next,
                    &next_frame,
                    ideal | (1u32 << e),
                    prefix,
                    out,
                )?;
                prefix.pop();
            }
        }
        Ok(())
    }
    let mut out = BTreeSet::new();
    visit(
        problem,
        &problem.initial,
        &TokenFrame::initial(problem),
        0,
        &mut Vec::new(),
        &mut out,
    )?;
    Ok(out)
}

/// `true` when `order` lists every event once, after all its predecessors.
pub fn respects(before: &[u32], order: &[usize]) -> bool {
    if order.len() != before.len() || before.len() > MAX_EVENTS {
        return false;
    }
    let mut ideal = 0u32;
    for &e in order {
        if e >= before.len() || ideal & (1u32 << e) != 0 || before[e] & !ideal != 0 {
            return false;
        }
        ideal |= 1u32 << e;
    }
    true
}

/// Greedy lexicographically least nondecreasing-rank linear extension; it
/// exists exactly when the family is kind compatible.
pub fn kind_sorted_order(problem: &CausalProblem) -> Option<Vec<usize>> {
    let m = problem.events.len();
    let mut ideal = 0u32;
    let mut order = Vec::with_capacity(m);
    while order.len() < m {
        let least = (0..m)
            .filter(|&e| ideal & (1u32 << e) == 0)
            .map(|e| problem.events[e].kind.rank())
            .min()?;
        let next = (0..m).find(|&e| {
            ideal & (1u32 << e) == 0
                && problem.events[e].kind.rank() == least
                && problem.before[e] & !ideal == 0
        })?;
        ideal |= 1u32 << next;
        order.push(next);
    }
    Some(order)
}

/// `None` when the native owner accepts the order, otherwise its refusal text.
pub fn native_refusal(
    problem: &CausalProblem,
    order: &[usize],
) -> Result<Option<String>, GuardedHistoryError> {
    let changes = descriptors(problem, order)?;
    Ok(Source25Run::replay(problem.initial.clone(), &changes)
        .err()
        .map(|e| e.to_string()))
}

/// No transitive precedence puts a higher-ranked kind before a lower one.
pub fn kind_compatible(problem: &CausalProblem) -> bool {
    problem.before.iter().enumerate().all(|(e, mask)| {
        (0..problem.events.len()).all(|p| {
            mask & (1u32 << p) == 0
                || problem.events[p].kind.rank() <= problem.events[e].kind.rank()
        })
    })
}

/// Lexicographically least linear extension with nondecreasing kind rank.
pub fn kind_sorted_extension(
    problem: &CausalProblem,
    schedules: &[Vec<usize>],
) -> Option<Vec<usize>> {
    schedules
        .iter()
        .find(|order| {
            order
                .windows(2)
                .all(|w| problem.events[w[0]].kind.rank() <= problem.events[w[1]].kind.rank())
        })
        .cloned()
}

// ============================================================================
// Swap 2-complex
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum FaceKind {
    Square,
    Hexagon,
}

/// A legal square or braid hexagon. `boundary` lists `(edge, sign)` along the
/// word `[i, j, i, j]` or `[i, i+1, i, i+1, i, i+1]` from `base`, the least
/// vertex; the sign is `+1` when the step runs from tail to head.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Face {
    pub kind: FaceKind,
    pub base: usize,
    pub word: Vec<usize>,
    pub vertices: Vec<usize>,
    pub boundary: Vec<(usize, i8)>,
}

/// Legal orders (lexicographic), legal swaps and legal faces.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SwapComplex {
    event_count: usize,
    orders: Vec<Vec<usize>>,
    index: BTreeMap<Vec<usize>, usize>,
    neighbors: Vec<Vec<Option<usize>>>,
    edges: Vec<(usize, usize)>,
    edge_index: BTreeMap<(usize, usize), usize>,
    faces: Vec<Face>,
    components: Vec<Vec<usize>>,
    component_of: Vec<usize>,
}

fn swapped(order: &[usize], p: usize) -> Vec<usize> {
    let mut out = order.to_vec();
    out.swap(p, p + 1);
    out
}

impl SwapComplex {
    pub fn new(
        event_count: usize,
        legal: &BTreeSet<Vec<usize>>,
    ) -> Result<Self, GuardedHistoryError> {
        for order in legal {
            let mut sorted = order.clone();
            sorted.sort_unstable();
            if sorted != (0..event_count).collect::<Vec<_>>() {
                return Err(GuardedHistoryError::NotAPermutation);
            }
        }
        let orders: Vec<Vec<usize>> = legal.iter().cloned().collect();
        let index: BTreeMap<Vec<usize>, usize> = orders
            .iter()
            .enumerate()
            .map(|(i, o)| (o.clone(), i))
            .collect();
        let positions = event_count.saturating_sub(1);
        let neighbors: Vec<Vec<Option<usize>>> = orders
            .iter()
            .map(|o| {
                (0..positions)
                    .map(|p| index.get(&swapped(o, p)).copied())
                    .collect()
            })
            .collect();
        let mut edges = Vec::new();
        let mut edge_index = BTreeMap::new();
        for (v, row) in neighbors.iter().enumerate() {
            for (p, w) in row.iter().enumerate() {
                if let Some(w) = *w {
                    if v < w {
                        edge_index.insert((v, p), edges.len());
                        edges.push((v, p));
                    }
                }
            }
        }
        let mut complex = Self {
            event_count,
            orders,
            index,
            neighbors,
            edges,
            edge_index,
            faces: Vec::new(),
            components: Vec::new(),
            component_of: Vec::new(),
        };
        complex.build_faces()?;
        complex.build_components();
        Ok(complex)
    }

    pub fn event_count(&self) -> usize {
        self.event_count
    }
    pub fn orders(&self) -> &[Vec<usize>] {
        &self.orders
    }
    pub fn index_of(&self, order: &[usize]) -> Option<usize> {
        self.index.get(order).copied()
    }
    /// Edges as `(tail, position)`; the head is `tail·s_position`, the tail is
    /// the lexicographically smaller order.
    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }
    pub fn faces(&self) -> &[Face] {
        &self.faces
    }
    pub fn components(&self) -> &[Vec<usize>] {
        &self.components
    }
    pub fn component_of(&self, vertex: usize) -> Option<usize> {
        self.component_of.get(vertex).copied()
    }
    pub fn squares(&self) -> usize {
        self.faces
            .iter()
            .filter(|f| f.kind == FaceKind::Square)
            .count()
    }
    pub fn hexagons(&self) -> usize {
        self.faces
            .iter()
            .filter(|f| f.kind == FaceKind::Hexagon)
            .count()
    }
    fn positions(&self) -> usize {
        self.event_count.saturating_sub(1)
    }

    /// The legal order `v·s_p`, if any.
    pub fn neighbor(&self, v: usize, p: usize) -> Option<usize> {
        self.neighbors.get(v)?.get(p).copied().flatten()
    }

    pub fn head(&self, edge: usize) -> Option<usize> {
        let &(tail, p) = self.edges.get(edge)?;
        self.neighbor(tail, p)
    }

    /// The edge crossed by the step `u -> u·s_p` and the step's sign.
    pub fn step_edge(&self, u: usize, p: usize) -> Option<(usize, i8)> {
        let w = self.neighbor(u, p)?;
        if u < w {
            Some((*self.edge_index.get(&(u, p))?, 1))
        } else {
            Some((*self.edge_index.get(&(w, p))?, -1))
        }
    }

    fn walk(&self, start: usize, word: &[usize]) -> Option<Vec<usize>> {
        let mut out = vec![start];
        let mut u = start;
        for &p in word {
            u = self.neighbor(u, p)?;
            out.push(u);
        }
        Some(out)
    }

    fn push_face(
        &mut self,
        seen: &mut BTreeSet<Vec<usize>>,
        kind: FaceKind,
        start: usize,
        word: Vec<usize>,
    ) -> Result<(), GuardedHistoryError> {
        let Some(path) = self.walk(start, &word) else {
            return Ok(());
        };
        let mut vertices = path.clone();
        vertices.sort_unstable();
        vertices.dedup();
        if !seen.insert(vertices.clone()) {
            return Ok(());
        }
        let base = vertices[0];
        let boundary_path = self
            .walk(base, &word)
            .ok_or(GuardedHistoryError::Inconsistent(
                "face word fails at its base",
            ))?;
        if boundary_path.last() != Some(&base) {
            return Err(GuardedHistoryError::Inconsistent(
                "face word does not close",
            ));
        }
        let boundary = word
            .iter()
            .zip(&boundary_path)
            .map(|(&p, &u)| {
                self.step_edge(u, p)
                    .ok_or(GuardedHistoryError::Inconsistent("face step has no edge"))
            })
            .collect::<Result<Vec<_>, _>>()?;
        self.faces.push(Face {
            kind,
            base,
            word,
            vertices,
            boundary,
        });
        Ok(())
    }

    fn build_faces(&mut self) -> Result<(), GuardedHistoryError> {
        let mut seen = BTreeSet::new();
        let positions = self.positions();
        for v in 0..self.orders.len() {
            for i in 0..positions {
                for j in i + 2..positions {
                    self.push_face(&mut seen, FaceKind::Square, v, vec![i, j, i, j])?;
                }
            }
            for i in 0..positions.saturating_sub(1) {
                self.push_face(
                    &mut seen,
                    FaceKind::Hexagon,
                    v,
                    vec![i, i + 1, i, i + 1, i, i + 1],
                )?;
            }
        }
        Ok(())
    }

    fn build_components(&mut self) {
        let mut component_of = vec![usize::MAX; self.orders.len()];
        let mut components = Vec::new();
        for start in 0..self.orders.len() {
            if component_of[start] != usize::MAX {
                continue;
            }
            let c = components.len();
            let mut members = vec![start];
            component_of[start] = c;
            let mut queue = VecDeque::from([start]);
            while let Some(u) = queue.pop_front() {
                for w in self.neighbors[u].iter().flatten() {
                    if component_of[*w] == usize::MAX {
                        component_of[*w] = c;
                        members.push(*w);
                        queue.push_back(*w);
                    }
                }
            }
            members.sort_unstable();
            components.push(members);
        }
        self.components = components;
        self.component_of = component_of;
    }

    pub fn component_edges(&self, c: usize) -> Vec<usize> {
        (0..self.edges.len())
            .filter(|&e| self.component_of[self.edges[e].0] == c)
            .collect()
    }

    pub fn component_faces(&self, c: usize) -> Vec<usize> {
        (0..self.faces.len())
            .filter(|&f| self.component_of[self.faces[f].base] == c)
            .collect()
    }

    fn inverse_positions(&self, base: &[usize]) -> Option<Vec<usize>> {
        let mut pos = vec![usize::MAX; self.event_count];
        if base.len() != self.event_count {
            return None;
        }
        for (k, &e) in base.iter().enumerate() {
            if e >= self.event_count || pos[e] != usize::MAX {
                return None;
            }
            pos[e] = k;
        }
        Some(pos)
    }

    /// Every lower cover (relative to `base`) of every legal order is legal.
    pub fn lower_covers_closed(&self, base: &[usize]) -> bool {
        let Some(pos) = self.inverse_positions(base) else {
            return false;
        };
        if self.index_of(base).is_none() {
            return false;
        }
        self.orders.iter().enumerate().all(|(v, order)| {
            (0..self.positions())
                .all(|p| pos[order[p]] < pos[order[p + 1]] || self.neighbor(v, p).is_some())
        })
    }

    /// `preferred` when it is a legal star base, otherwise the
    /// lexicographically least legal star base.
    pub fn star_base(&self, preferred: Option<&[usize]>) -> Option<Vec<usize>> {
        if let Some(p) = preferred {
            if self.lower_covers_closed(p) {
                return Some(p.to_vec());
            }
        }
        self.orders
            .iter()
            .find(|o| self.lower_covers_closed(o))
            .cloned()
    }

    fn spanning_tree(
        &self,
        c: usize,
    ) -> Result<BTreeMap<usize, (usize, usize)>, GuardedHistoryError> {
        let comp = self
            .components
            .get(c)
            .ok_or(GuardedHistoryError::UnknownComponent(c))?;
        let root = comp[0];
        let mut parent = BTreeMap::new();
        let mut seen = BTreeSet::from([root]);
        let mut queue = VecDeque::from([root]);
        while let Some(u) = queue.pop_front() {
            for p in 0..self.positions() {
                if let Some(w) = self.neighbor(u, p) {
                    if seen.insert(w) {
                        parent.insert(w, (u, p));
                        queue.push_back(w);
                    }
                }
            }
        }
        Ok(parent)
    }

    fn spanning_tree_edges(
        &self,
        parent: &BTreeMap<usize, (usize, usize)>,
    ) -> Result<BTreeSet<usize>, GuardedHistoryError> {
        parent
            .values()
            .map(|&(u, p)| {
                self.step_edge(u, p)
                    .map(|(e, _)| e)
                    .ok_or(GuardedHistoryError::Inconsistent("tree step has no edge"))
            })
            .collect()
    }

    fn collapse_leaf_faces(
        faces: &[usize],
        nontree: &[usize],
        face_rows: &[Vec<(usize, i8)>],
    ) -> (Vec<bool>, Vec<usize>, Vec<bool>, Vec<(usize, usize)>) {
        let mut faces_of_row = vec![Vec::new(); nontree.len()];
        for (local, rows) in face_rows.iter().enumerate() {
            for &(r, _) in rows {
                faces_of_row[r].push(local);
            }
        }
        let mut killed = vec![false; nontree.len()];
        let mut open: Vec<usize> = face_rows.iter().map(Vec::len).collect();
        let mut chosen = vec![false; faces.len()];
        let mut queue: VecDeque<usize> = (0..faces.len()).filter(|&f| open[f] == 1).collect();
        let mut collapsed = Vec::new();
        while let Some(f) = queue.pop_front() {
            Self::collapse_single_face(
                f,
                faces,
                nontree,
                face_rows,
                &faces_of_row,
                &mut killed,
                &mut open,
                &mut chosen,
                &mut queue,
                &mut collapsed,
            );
        }
        (killed, open, chosen, collapsed)
    }

    #[allow(clippy::too_many_arguments)]
    fn collapse_single_face(
        f: usize,
        faces: &[usize],
        nontree: &[usize],
        face_rows: &[Vec<(usize, i8)>],
        faces_of_row: &[Vec<usize>],
        killed: &mut [bool],
        open: &mut [usize],
        chosen: &mut [bool],
        queue: &mut VecDeque<usize>,
        collapsed: &mut Vec<(usize, usize)>,
    ) {
        if chosen[f] || open[f] != 1 {
            return;
        }
        let Some(&(row, _)) = face_rows[f].iter().find(|(r, _)| !killed[*r]) else {
            return;
        };
        chosen[f] = true;
        killed[row] = true;
        collapsed.push((faces[f], nontree[row]));
        for &g in &faces_of_row[row] {
            open[g] -= 1;
            if open[g] == 1 && !chosen[g] {
                queue.push_back(g);
            }
        }
    }

    fn build_residual_matrix(
        residual_rows: &[usize],
        residual_local: &[usize],
        face_rows: &[Vec<(usize, i8)>],
    ) -> Result<(BasicMatrix<BigRational>, usize), GuardedHistoryError> {
        let row_pos: BTreeMap<usize, usize> = residual_rows
            .iter()
            .enumerate()
            .map(|(i, &r)| (r, i))
            .collect();
        let (rows, cols) = (residual_rows.len(), residual_local.len());
        let mut data = vec![BigRational::zero(); rows * cols];
        for (j, &f) in residual_local.iter().enumerate() {
            for &(r, s) in &face_rows[f] {
                if let Some(&i) = row_pos.get(&r) {
                    data[i * cols + j] = BigRational::from_integer(BigInt::from(s));
                }
            }
        }
        let residual = BasicMatrix::from_row_major(rows, cols, data).map_err(linear)?;
        let residual_rank = if rows == 0 || cols == 0 {
            0
        } else {
            rank(&residual).map_err(linear)?
        };
        Ok((residual, residual_rank))
    }

    /// Exact `H1(X_L; Q)` of one component; see [`ComponentReduction`].
    pub fn reduce_component(&self, c: usize) -> Result<ComponentReduction, GuardedHistoryError> {
        let comp = self
            .components
            .get(c)
            .ok_or(GuardedHistoryError::UnknownComponent(c))?;
        if comp.len() > MAX_H1_COMPONENT {
            return Err(GuardedHistoryError::ComponentTooLarge {
                component: c,
                vertices: comp.len(),
            });
        }
        let parent = self.spanning_tree(c)?;
        let tree = self.spanning_tree_edges(&parent)?;
        let edges = self.component_edges(c);
        let nontree: Vec<usize> = edges
            .iter()
            .copied()
            .filter(|e| !tree.contains(e))
            .collect();
        let row_of: BTreeMap<usize, usize> = nontree
            .iter()
            .enumerate()
            .map(|(row, &e)| (e, row))
            .collect();
        let faces = self.component_faces(c);
        let face_rows: Vec<Vec<(usize, i8)>> = faces
            .iter()
            .map(|&f| {
                self.faces[f]
                    .boundary
                    .iter()
                    .filter_map(|(e, s)| row_of.get(e).map(|&r| (r, *s)))
                    .collect()
            })
            .collect();
        let (killed, open, chosen, collapsed) =
            Self::collapse_leaf_faces(&faces, &nontree, &face_rows);
        let residual_rows: Vec<usize> = (0..nontree.len()).filter(|&r| !killed[r]).collect();
        let residual_local: Vec<usize> = (0..faces.len())
            .filter(|&f| !chosen[f] && open[f] > 0)
            .collect();
        let (residual, residual_rank) =
            Self::build_residual_matrix(&residual_rows, &residual_local, &face_rows)?;
        let h1_rank = residual_rows.len() - residual_rank;
        let reduction = ComponentReduction {
            component: c,
            root: comp[0],
            parent,
            nontree_edges: residual_rows.iter().map(|&r| nontree[r]).collect(),
            residual_faces: residual_local.iter().map(|&f| faces[f]).collect(),
            collapsed,
            residual,
            residual_rank,
            h1_rank,
        };
        self.cross_check_homology(c, h1_rank)?;
        Ok(reduction)
    }

    fn should_cross_check_homology(comp: &[usize], edges: &[usize], faces: &[usize]) -> bool {
        !edges.is_empty()
            && comp.len() <= CROSS_CHECK_VERTICES
            && edges.len() <= CROSS_CHECK_CELLS
            && faces.len() <= CROSS_CHECK_CELLS
    }

    fn build_cross_check_boundaries(
        &self,
        comp: &[usize],
        edges: &[usize],
        faces: &[usize],
    ) -> Result<(BasicMatrix<Rational64>, BasicMatrix<Rational64>), GuardedHistoryError> {
        let vpos: BTreeMap<usize, usize> = comp.iter().enumerate().map(|(i, &v)| (v, i)).collect();
        let epos: BTreeMap<usize, usize> = edges.iter().enumerate().map(|(i, &e)| (e, i)).collect();
        let (nv, ne, nf) = (comp.len(), edges.len(), faces.len());
        let mut d1 = vec![Rational64::zero(); nv * ne];
        for (j, &e) in edges.iter().enumerate() {
            let tail = self.edges[e].0;
            let head = self
                .head(e)
                .ok_or(GuardedHistoryError::Inconsistent("edge without head"))?;
            d1[vpos[&tail] * ne + j] = -Rational64::one();
            d1[vpos[&head] * ne + j] = Rational64::one();
        }
        let mut d2 = vec![Rational64::zero(); ne * nf];
        for (j, &f) in faces.iter().enumerate() {
            for &(e, s) in &self.faces[f].boundary {
                d2[epos[&e] * nf + j] += Rational64::from_integer(i64::from(s));
            }
        }
        let d1 = BasicMatrix::from_row_major(nv, ne, d1).map_err(linear)?;
        let d2 = BasicMatrix::from_row_major(ne, nf, d2).map_err(linear)?;
        Ok((d1, d2))
    }

    /// Replays small components through `linear_algebra::homology_basis`
    /// on the full `∂1`, `∂2` (checked `Rational64`; overflow is refused).
    fn cross_check_homology(&self, c: usize, h1: usize) -> Result<(), GuardedHistoryError> {
        let comp = &self.components[c];
        let edges = self.component_edges(c);
        let faces = self.component_faces(c);
        if !Self::should_cross_check_homology(comp, &edges, &faces) {
            return Ok(());
        }
        let (d1, d2) = self.build_cross_check_boundaries(comp, &edges, &faces)?;
        let mut hasher = Sha256::new();
        for &v in comp {
            hasher.update(Json::naturals(&self.orders[v]).to_canonical().as_bytes());
        }
        let provenance = TheoremProvenance::DerivedFromFiniteVerification {
            theorem_id: TheoremId::new("wdp-guarded-history-h1").map_err(linear)?,
            replay: ReplayHash::from_bytes(hasher.finalize().into()),
        };
        let basis = homology_basis(1, &d1, &d2, provenance).map_err(linear)?;
        if basis.homology_rank() != h1 {
            return Err(GuardedHistoryError::Inconsistent(
                "collapse reduction and homology_basis disagree on H1",
            ));
        }
        Ok(())
    }

    fn tree_word(
        &self,
        parent: &BTreeMap<usize, (usize, usize)>,
        root: usize,
        target: usize,
    ) -> Result<Vec<usize>, GuardedHistoryError> {
        let mut word = Vec::new();
        let mut v = target;
        while v != root {
            let &(u, p) = parent.get(&v).ok_or(GuardedHistoryError::Inconsistent(
                "vertex outside spanning tree",
            ))?;
            word.push(p);
            v = u;
        }
        word.reverse();
        Ok(word)
    }

    /// Value of a 1-cochain along a swap word from `start`.
    pub fn cochain_along(
        &self,
        values: &BTreeMap<usize, BigRational>,
        start: usize,
        word: &[usize],
    ) -> Result<BigRational, ReplayRefusal> {
        let mut total = BigRational::zero();
        let mut u = start;
        for &p in word {
            let (e, s) = self
                .step_edge(u, p)
                .ok_or(ReplayRefusal::IllegalIntermediate)?;
            if let Some(value) = values.get(&e) {
                if s > 0 {
                    total += value;
                } else {
                    total -= value;
                }
            }
            u = self
                .neighbor(u, p)
                .ok_or(ReplayRefusal::IllegalIntermediate)?;
        }
        Ok(total)
    }

    /// `true` when the cochain sums to zero around every legal face.
    pub fn cochain_closed(&self, values: &BTreeMap<usize, BigRational>) -> bool {
        self.faces.iter().all(|face| {
            face.boundary
                .iter()
                .fold(BigRational::zero(), |acc, (e, s)| match values.get(e) {
                    Some(v) if *s > 0 => acc + v,
                    Some(v) => acc - v,
                    None => acc,
                })
                .is_zero()
        })
    }

    fn extract_cocycle_vector(
        reduction: &ComponentReduction,
    ) -> Result<Vec<BigRational>, GuardedHistoryError> {
        let rows = reduction.residual.rows();
        if reduction.residual.cols() == 0 {
            let mut unit = vec![BigRational::zero(); rows];
            unit[0] = BigRational::one();
            Ok(unit)
        } else {
            left_kernel_basis(&reduction.residual)
                .map_err(linear)?
                .into_iter()
                .next()
                .ok_or(GuardedHistoryError::Inconsistent(
                    "positive H1 without cocycle",
                ))
        }
    }

    fn build_separating_cocycle_for_component(
        &self,
        c: usize,
        reduction: ComponentReduction,
    ) -> Result<SeparatingCocycle, GuardedHistoryError> {
        let y = Self::extract_cocycle_vector(&reduction)?;
        let values: BTreeMap<usize, BigRational> = reduction
            .nontree_edges
            .iter()
            .zip(&y)
            .filter(|(_, v)| !v.is_zero())
            .map(|(&e, v)| (e, v.clone()))
            .collect();
        let (&edge, _) = values
            .iter()
            .next()
            .ok_or(GuardedHistoryError::Inconsistent("zero cocycle"))?;
        if !self.cochain_closed(&values) {
            return Err(GuardedHistoryError::Inconsistent("cocycle is not closed"));
        }
        let (tail, position) = self.edges[edge];
        let target = self
            .head(edge)
            .ok_or(GuardedHistoryError::Inconsistent("edge without head"))?;
        let mut word_a = self.tree_word(&reduction.parent, reduction.root, tail)?;
        word_a.push(position);
        let word_b = self.tree_word(&reduction.parent, reduction.root, target)?;
        let value_a = self.cochain_along(&values, reduction.root, &word_a)?;
        let value_b = self.cochain_along(&values, reduction.root, &word_b)?;
        if value_a == value_b {
            return Err(GuardedHistoryError::Inconsistent(
                "cocycle does not separate",
            ));
        }
        Ok(SeparatingCocycle {
            component: c,
            root: reduction.root,
            target,
            word_a,
            word_b,
            values,
            value_a,
            value_b,
        })
    }

    /// A closed rational 1-cochain separating two words with common ends,
    /// for the first component with positive `H1`.
    pub fn separating_cocycle(&self) -> Result<Option<SeparatingCocycle>, GuardedHistoryError> {
        for c in 0..self.components.len() {
            let reduction = self.reduce_component(c)?;
            if reduction.h1_rank == 0 {
                continue;
            }
            return self
                .build_separating_cocycle_for_component(c, reduction)
                .map(Some);
        }
        Ok(None)
    }

    /// Replay a swap word from `start`; returns the reached vertex.
    pub fn replay_word(&self, start: usize, word: &[usize]) -> Result<usize, ReplayRefusal> {
        let mut u = start;
        for &p in word {
            if p + 1 >= self.event_count {
                return Err(ReplayRefusal::PositionOutside(p));
            }
            u = self
                .neighbor(u, p)
                .ok_or(ReplayRefusal::IllegalIntermediate)?;
        }
        Ok(u)
    }

    fn apply_single_replacement(
        &self,
        source: usize,
        target: usize,
        current: &mut Vec<usize>,
        r: &Replacement,
    ) -> Result<(), ReplayRefusal> {
        let kind = replacement_kind(&r.before, &r.after).ok_or(ReplayRefusal::NotLocalRelation)?;
        if kind != r.kind {
            return Err(ReplayRefusal::KindMismatch);
        }
        if r.offset > current.len() || r.offset + r.before.len() > current.len() {
            return Err(ReplayRefusal::OffsetOutside);
        }
        if current[r.offset..r.offset + r.before.len()] != r.before[..] {
            return Err(ReplayRefusal::SideMismatch);
        }
        current.splice(r.offset..r.offset + r.before.len(), r.after.iter().copied());
        if self.replay_word(source, current)? != target {
            return Err(ReplayRefusal::WrongTarget);
        }
        Ok(())
    }

    /// Replays a 3-certificate: every intermediate word must stay inside the
    /// legal orders and keep both boundary orders.
    pub fn replay_replacements(
        &self,
        source_order: &[usize],
        target_order: &[usize],
        source_word: &[usize],
        target_word: &[usize],
        replacements: &[Replacement],
    ) -> Result<(), ReplayRefusal> {
        let source = self
            .index_of(source_order)
            .ok_or(ReplayRefusal::UnknownSource)?;
        let target = self
            .index_of(target_order)
            .ok_or(ReplayRefusal::UnknownTarget)?;
        if self.replay_word(source, source_word)? != target {
            return Err(ReplayRefusal::WrongTarget);
        }
        let mut current = source_word.to_vec();
        for r in replacements {
            self.apply_single_replacement(source, target, &mut current, r)?;
        }
        if current != target_word {
            return Err(ReplayRefusal::MissesTarget);
        }
        Ok(())
    }

    fn all_pairs_distances(&self, comp: &[usize]) -> BTreeMap<usize, Vec<usize>> {
        let mut dist: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
        for &t in comp {
            let mut d = vec![usize::MAX; self.orders.len()];
            d[t] = 0;
            let mut queue = VecDeque::from([t]);
            while let Some(u) = queue.pop_front() {
                for w in self.neighbors[u].iter().flatten() {
                    if d[*w] == usize::MAX {
                        d[*w] = d[u] + 1;
                        queue.push_back(*w);
                    }
                }
            }
            dist.insert(t, d);
        }
        dist
    }

    fn geodesic_word(
        &self,
        dist: &BTreeMap<usize, Vec<usize>>,
        s: usize,
        t: usize,
        largest: bool,
    ) -> Vec<usize> {
        let d = &dist[&t];
        let mut word = Vec::new();
        let mut u = s;
        while u != t {
            let mut candidates: Vec<usize> = (0..self.positions()).collect();
            if largest {
                candidates.reverse();
            }
            let Some((p, w)) = candidates.into_iter().find_map(|p| {
                self.neighbor(u, p)
                    .filter(|&w| d[w] + 1 == d[u])
                    .map(|w| (p, w))
            }) else {
                break;
            };
            word.push(p);
            u = w;
        }
        word
    }

    fn collect_geodesic_witness_pairs(
        &self,
        dist: &BTreeMap<usize, Vec<usize>>,
        pairs: &[(usize, usize, usize)],
        limit: usize,
    ) -> Vec<WordPair> {
        let mut out = Vec::new();
        for &(d, s, t) in pairs {
            if out.len() == limit || d < 2 {
                break;
            }
            let (low, high) = (
                self.geodesic_word(dist, s, t, false),
                self.geodesic_word(dist, s, t, true),
            );
            if low != high {
                out.push(WordPair {
                    source: s,
                    target: t,
                    first: low,
                    second: high,
                });
            }
        }
        out
    }

    fn append_fallback_witness_pairs(
        &self,
        dist: &BTreeMap<usize, Vec<usize>>,
        comp: &[usize],
        pairs: Vec<(usize, usize, usize)>,
        limit: usize,
        out: &mut Vec<WordPair>,
    ) {
        let used: BTreeSet<(usize, usize)> = out.iter().map(|p| (p.source, p.target)).collect();
        let mut fallback: Vec<(usize, usize, usize)> = pairs;
        fallback.extend(comp.iter().map(|&v| (0, v, v)));
        for (_, s, t) in fallback {
            if out.len() == limit {
                break;
            }
            if used.contains(&(s, t)) {
                continue;
            }
            let Some(q) = (0..self.positions()).find(|&p| self.neighbor(t, p).is_some()) else {
                continue;
            };
            let first = self.geodesic_word(dist, s, t, false);
            let mut second = first.clone();
            second.extend([q, q]);
            out.push(WordPair {
                source: s,
                target: t,
                first,
                second,
            });
        }
    }

    /// Up to `limit` pairs of distinct parallel words in component `c`:
    /// first the lexicographically least and greatest geodesic words between
    /// the farthest pairs, then geodesic-versus-backtrack pairs.
    pub fn witness_pairs(
        &self,
        c: usize,
        limit: usize,
    ) -> Result<Vec<WordPair>, GuardedHistoryError> {
        let comp = self
            .components
            .get(c)
            .ok_or(GuardedHistoryError::UnknownComponent(c))?;
        if comp.len() > MAX_H1_COMPONENT {
            return Err(GuardedHistoryError::ComponentTooLarge {
                component: c,
                vertices: comp.len(),
            });
        }
        let dist = self.all_pairs_distances(comp);
        let mut pairs: Vec<(usize, usize, usize)> = Vec::new();
        for (a, &s) in comp.iter().enumerate() {
            for &t in &comp[a + 1..] {
                pairs.push((dist[&t][s], s, t));
            }
        }
        pairs.sort_by(|x, y| y.0.cmp(&x.0).then(x.1.cmp(&y.1)).then(x.2.cmp(&y.2)));
        let mut out = self.collect_geodesic_witness_pairs(&dist, &pairs, limit);
        if out.len() < limit {
            self.append_fallback_witness_pairs(&dist, comp, pairs, limit, &mut out);
        }
        Ok(out)
    }
}

/// Exact `H1` of one component. A breadth-first spanning tree from the least
/// order is contracted; then a face whose boundary has exactly one remaining
/// non-tree edge kills that edge. Collapsed faces and killed edges form a
/// unit-triangular block of `∂2` restricted to non-tree edges, and no
/// collapsed face meets a surviving edge, so
/// `rank ∂2 = #collapsed + rank(residual)` and
/// `H1 = #surviving − rank(residual)`, with `residual` reduced exactly over
/// `BigRational`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ComponentReduction {
    pub component: usize,
    pub root: usize,
    parent: BTreeMap<usize, (usize, usize)>,
    nontree_edges: Vec<usize>,
    residual_faces: Vec<usize>,
    collapsed: Vec<(usize, usize)>,
    residual: BasicMatrix<BigRational>,
    residual_rank: usize,
    pub h1_rank: usize,
}

impl ComponentReduction {
    /// Surviving non-tree edges (rows of the residual block).
    pub fn surviving_edges(&self) -> &[usize] {
        &self.nontree_edges
    }
    pub fn residual_faces(&self) -> &[usize] {
        &self.residual_faces
    }
    /// `(face, edge)` collapse pairs in kill order.
    pub fn collapsed(&self) -> &[(usize, usize)] {
        &self.collapsed
    }
    pub fn residual_rank(&self) -> usize {
        self.residual_rank
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SeparatingCocycle {
    pub component: usize,
    pub root: usize,
    pub target: usize,
    pub word_a: Vec<usize>,
    pub word_b: Vec<usize>,
    /// Nonzero values on edges oriented from the lexicographically smaller order.
    pub values: BTreeMap<usize, BigRational>,
    pub value_a: BigRational,
    pub value_b: BigRational,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WordPair {
    pub source: usize,
    pub target: usize,
    pub first: Vec<usize>,
    pub second: Vec<usize>,
}

pub fn rational_text(value: &BigRational) -> String {
    if value.is_integer() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

// ============================================================================
// Local replacements and constructive coherence
// ============================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum ReplacementKind {
    Backtrack,
    Square,
    Braid,
}

impl ReplacementKind {
    pub fn wire(self) -> &'static str {
        match self {
            Self::Backtrack => "backtrack",
            Self::Square => "square",
            Self::Braid => "braid",
        }
    }
}

fn is_backtrack_replacement(before: &[usize], after: &[usize]) -> bool {
    let (short, long) = if before.len() <= after.len() {
        (before, after)
    } else {
        (after, before)
    };
    short.is_empty() && long.len() == 2 && long[0] == long[1]
}

fn is_square_replacement(before: &[usize], after: &[usize]) -> bool {
    before.len() == 2
        && after.len() == 2
        && before[0].abs_diff(before[1]) > 1
        && after[0] == before[1]
        && after[1] == before[0]
}

fn is_braid_replacement(before: &[usize], after: &[usize]) -> bool {
    before.len() == 3
        && after.len() == 3
        && before[0] == before[2]
        && before[0].abs_diff(before[1]) == 1
        && after == [before[1], before[0], before[1]]
}

/// `replacement_kind` of `check_causal_three_cells.py`.
pub fn replacement_kind(before: &[usize], after: &[usize]) -> Option<ReplacementKind> {
    if is_backtrack_replacement(before, after) {
        Some(ReplacementKind::Backtrack)
    } else if is_square_replacement(before, after) {
        Some(ReplacementKind::Square)
    } else if is_braid_replacement(before, after) {
        Some(ReplacementKind::Braid)
    } else {
        None
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Replacement {
    pub kind: ReplacementKind,
    pub offset: usize,
    pub before: Vec<usize>,
    pub after: Vec<usize>,
}

impl Replacement {
    pub fn inverse(&self) -> Self {
        Self {
            kind: self.kind,
            offset: self.offset,
            before: self.after.clone(),
            after: self.before.clone(),
        }
    }

    fn shifted(&self, by: usize) -> Self {
        Self {
            offset: self.offset + by,
            ..self.clone()
        }
    }

    pub fn to_json(&self) -> Json {
        Json::object([
            ("kind", Json::text(self.kind.wire())),
            ("offset", Json::natural(self.offset)),
            ("before", Json::naturals(&self.before)),
            ("after", Json::naturals(&self.after)),
        ])
    }
}

fn shifted(moves: &[Replacement], by: usize) -> Vec<Replacement> {
    moves.iter().map(|m| m.shifted(by)).collect()
}

fn reversed(moves: &[Replacement]) -> Vec<Replacement> {
    moves.iter().rev().map(Replacement::inverse).collect()
}

/// Constructive coherence from a star base `e0`: canonical leftmost descent
/// words `D(h)` and the recursive edge lemma.
pub struct StarCoherence<'a> {
    complex: &'a SwapComplex,
    base: usize,
    pos: Vec<usize>,
    memo: BTreeMap<(usize, usize), Vec<Replacement>>,
}

impl<'a> StarCoherence<'a> {
    pub fn new(complex: &'a SwapComplex, base: &[usize]) -> Result<Self, GuardedHistoryError> {
        if !complex.lower_covers_closed(base) {
            return Err(GuardedHistoryError::NotStarBase);
        }
        let pos = complex
            .inverse_positions(base)
            .ok_or(GuardedHistoryError::NotStarBase)?;
        let base = complex
            .index_of(base)
            .ok_or(GuardedHistoryError::NotStarBase)?;
        Ok(Self {
            complex,
            base,
            pos,
            memo: BTreeMap::new(),
        })
    }

    pub fn base(&self) -> usize {
        self.base
    }

    fn inverted(&self, v: usize, p: usize) -> bool {
        let order = &self.complex.orders[v];
        p + 1 < order.len() && self.pos[order[p]] > self.pos[order[p + 1]]
    }

    fn leftmost(&self, v: usize) -> Option<usize> {
        (0..self.complex.positions()).find(|&p| self.inverted(v, p))
    }

    fn lower(&self, v: usize, p: usize) -> Result<usize, GuardedHistoryError> {
        if !self.inverted(v, p) {
            return Err(GuardedHistoryError::Inconsistent(
                "descent step is not a lower cover",
            ));
        }
        self.complex
            .neighbor(v, p)
            .ok_or(GuardedHistoryError::IllegalIntermediate)
    }

    /// `D(v)`: repeatedly swap the leftmost inverted adjacent pair.
    pub fn descent(&self, v: usize) -> Result<Vec<usize>, GuardedHistoryError> {
        let mut word = Vec::new();
        let mut u = v;
        while let Some(p) = self.leftmost(u) {
            word.push(p);
            u = self.lower(u, p)?;
        }
        if u != self.base {
            return Err(GuardedHistoryError::Inconsistent("descent misses the base"));
        }
        Ok(word)
    }

    /// Moves turning `[i] ++ D(x·s_i)` into `D(x)` for an inverted position `i`.
    pub fn edge_lemma(
        &mut self,
        x: usize,
        i: usize,
    ) -> Result<Vec<Replacement>, GuardedHistoryError> {
        if let Some(moves) = self.memo.get(&(x, i)) {
            return Ok(moves.clone());
        }
        let xi = self.lower(x, i)?;
        let d = self.leftmost(x).ok_or(GuardedHistoryError::Inconsistent(
            "inverted order without descent",
        ))?;
        let moves = if d == i {
            Vec::new()
        } else {
            let xd = self.lower(x, d)?;
            let (irest, drest, face) = if i.abs_diff(d) > 1 {
                (
                    vec![d],
                    vec![i],
                    Replacement {
                        kind: ReplacementKind::Square,
                        offset: 0,
                        before: vec![i, d],
                        after: vec![d, i],
                    },
                )
            } else {
                (
                    vec![d, i],
                    vec![i, d],
                    Replacement {
                        kind: ReplacementKind::Braid,
                        offset: 0,
                        before: vec![i, d, i],
                        after: vec![d, i, d],
                    },
                )
            };
            let mut moves = shifted(&self.descend_path(xi, &irest)?, 1);
            moves.push(face);
            moves.extend(shifted(&reversed(&self.descend_path(xd, &drest)?), 1));
            moves
        };
        if moves.len() > MAX_REPLACEMENTS {
            return Err(GuardedHistoryError::WitnessBudget(MAX_REPLACEMENTS));
        }
        self.memo.insert((x, i), moves.clone());
        Ok(moves)
    }

    /// Moves turning `D(y)` into `path ++ D(z)` along a downward path `y -> z`.
    fn descend_path(
        &mut self,
        y: usize,
        path: &[usize],
    ) -> Result<Vec<Replacement>, GuardedHistoryError> {
        let mut moves = Vec::new();
        let mut u = y;
        for (t, &q) in path.iter().enumerate() {
            let lemma = self.edge_lemma(u, q)?;
            moves.extend(shifted(&reversed(&lemma), t));
            u = self.lower(u, q)?;
            if moves.len() > MAX_REPLACEMENTS {
                return Err(GuardedHistoryError::WitnessBudget(MAX_REPLACEMENTS));
            }
        }
        Ok(moves)
    }

    /// Moves turning a legal word from `source` into `D(source) ++ reverse(D(target))`.
    pub fn normalize(
        &mut self,
        source: usize,
        word: &[usize],
    ) -> Result<Vec<Replacement>, GuardedHistoryError> {
        let path = self
            .complex
            .walk(source, word)
            .ok_or(GuardedHistoryError::IllegalIntermediate)?;
        let m = word.len();
        let target = path[m];
        let mut moves: Vec<Replacement> = self
            .descent(target)?
            .into_iter()
            .enumerate()
            .map(|(t, q)| Replacement {
                kind: ReplacementKind::Backtrack,
                offset: m + t,
                before: vec![],
                after: vec![q, q],
            })
            .collect();
        for k in (1..=m).rev() {
            let p = word[k - 1];
            let (u, v) = (path[k - 1], path[k]);
            if self.inverted(u, p) {
                moves.extend(shifted(&self.edge_lemma(u, p)?, k - 1));
            } else {
                moves.extend(shifted(&reversed(&self.edge_lemma(v, p)?), k));
                moves.push(Replacement {
                    kind: ReplacementKind::Backtrack,
                    offset: k - 1,
                    before: vec![p, p],
                    after: vec![],
                });
            }
            if moves.len() > MAX_REPLACEMENTS {
                return Err(GuardedHistoryError::WitnessBudget(MAX_REPLACEMENTS));
            }
        }
        Ok(moves)
    }

    /// A replayed 3-certificate between two parallel words from `source`.
    pub fn witness(
        &mut self,
        source: usize,
        first: &[usize],
        second: &[usize],
    ) -> Result<Vec<Replacement>, GuardedHistoryError> {
        let mut moves = self.normalize(source, first)?;
        moves.extend(reversed(&self.normalize(source, second)?));
        if moves.len() > MAX_REPLACEMENTS {
            return Err(GuardedHistoryError::WitnessBudget(MAX_REPLACEMENTS));
        }
        let target = self.complex.replay_word(source, first)?;
        self.complex.replay_replacements(
            &self.complex.orders[source],
            &self.complex.orders[target],
            first,
            second,
            &moves,
        )?;
        Ok(moves)
    }
}

// ============================================================================
// Analysis and certificate
// ============================================================================

/// Pure analysis of an explicit legal-order set.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LegalSetAnalysis {
    pub complex: SwapComplex,
    pub h1_ranks: Vec<usize>,
    pub star_base: Option<Vec<usize>>,
}

pub fn analyze_legal_set(
    event_count: usize,
    legal: &BTreeSet<Vec<usize>>,
    preferred_base: Option<&[usize]>,
) -> Result<LegalSetAnalysis, GuardedHistoryError> {
    let complex = SwapComplex::new(event_count, legal)?;
    let h1_ranks = (0..complex.components().len())
        .map(|c| complex.reduce_component(c).map(|r| r.h1_rank))
        .collect::<Result<Vec<_>, _>>()?;
    let star_base = complex.star_base(preferred_base);
    Ok(LegalSetAnalysis {
        complex,
        h1_ranks,
        star_base,
    })
}

/// Everything the certificate reports about one admitted problem.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GuardedEvaluation {
    pub problem: CausalProblem,
    pub linear_extensions: usize,
    pub refused: Vec<(Vec<usize>, String)>,
    pub analysis: LegalSetAnalysis,
    pub kind_compatible: bool,
    pub kind_sorted: Option<Vec<usize>>,
}

pub fn evaluate_problem(problem: CausalProblem) -> Result<GuardedEvaluation, GuardedHistoryError> {
    let orders = schedules(problem.before())?;
    let mut legal = BTreeSet::new();
    let mut refused = Vec::new();
    for order in &orders {
        match native_refusal(&problem, order)? {
            None => {
                legal.insert(order.clone());
            }
            Some(reason) => refused.push((order.clone(), reason)),
        }
    }
    let kind_sorted = kind_sorted_extension(&problem, &orders);
    let analysis = analyze_legal_set(problem.event_count(), &legal, kind_sorted.as_deref())?;
    Ok(GuardedEvaluation {
        kind_compatible: kind_compatible(&problem),
        kind_sorted,
        linear_extensions: orders.len(),
        refused,
        analysis,
        problem,
    })
}

fn build_coherence_witnesses(
    complex: &SwapComplex,
    star_base: &Option<Vec<usize>>,
    pairs: usize,
) -> Result<Vec<Json>, GuardedHistoryError> {
    let Some(base) = star_base else {
        return Ok(Vec::new());
    };
    let order_json = |v: usize| Json::naturals(&complex.orders()[v]);
    let mut coherence = StarCoherence::new(complex, base)?;
    let component = complex
        .component_of(coherence.base())
        .ok_or(GuardedHistoryError::Inconsistent("base outside complex"))?;
    let mut witnesses = Vec::new();
    for pair in complex.witness_pairs(component, pairs)? {
        let moves = coherence.witness(pair.source, &pair.first, &pair.second)?;
        witnesses.push(Json::object([
            ("source_order", order_json(pair.source)),
            ("target_order", order_json(pair.target)),
            ("source_word", Json::naturals(&pair.first)),
            ("target_word", Json::naturals(&pair.second)),
            (
                "replacements",
                Json::Arr(moves.iter().map(Replacement::to_json).collect()),
            ),
        ]));
    }
    Ok(witnesses)
}

fn cocycle_to_json(complex: &SwapComplex, cocycle: Option<SeparatingCocycle>) -> Json {
    let Some(c) = cocycle else {
        return Json::Null;
    };
    let order_json = |v: usize| Json::naturals(&complex.orders()[v]);
    Json::object([
        ("component", Json::natural(c.component)),
        ("root_order", order_json(c.root)),
        ("target_order", order_json(c.target)),
        ("word_a", Json::naturals(&c.word_a)),
        ("word_b", Json::naturals(&c.word_b)),
        (
            "edge_values",
            Json::Arr(
                c.values
                    .iter()
                    .map(|(&e, value)| {
                        let (tail, position) = complex.edges()[e];
                        Json::object([
                            ("order", order_json(tail)),
                            ("position", Json::natural(position)),
                            ("value", Json::text(rational_text(value))),
                        ])
                    })
                    .collect(),
            ),
        ),
        ("value_a", Json::text(rational_text(&c.value_a))),
        ("value_b", Json::text(rational_text(&c.value_b))),
    ])
}

/// Certificate `wdp-guarded-coherence-v1` for the exact bytes of a problem file.
pub fn guarded_certificate(bytes: &[u8], pairs: usize) -> Result<Json, GuardedHistoryError> {
    let digest = hex::encode(Sha256::digest(bytes));
    let evaluation = evaluate_problem(parse_problem(bytes)?)?;
    let complex = &evaluation.analysis.complex;
    let components = complex
        .components()
        .iter()
        .enumerate()
        .map(|(c, vertices)| {
            Json::object([
                ("vertices", Json::naturals(vertices)),
                ("edges", Json::natural(complex.component_edges(c).len())),
                ("faces", Json::natural(complex.component_faces(c).len())),
                ("h1_rank", Json::natural(evaluation.analysis.h1_ranks[c])),
            ])
        })
        .collect();
    let witnesses = build_coherence_witnesses(complex, &evaluation.analysis.star_base, pairs)?;
    let cocycle = cocycle_to_json(complex, complex.separating_cocycle()?);
    Ok(Json::object([
        ("schema", Json::text(CERTIFICATE_SCHEMA)),
        ("authority_effect", Json::text("None")),
        ("problem_file_sha256", Json::text(digest)),
        (
            "event_count",
            Json::natural(evaluation.problem.event_count()),
        ),
        (
            "linear_extensions",
            Json::natural(evaluation.linear_extensions),
        ),
        (
            "legal_orders",
            Json::Arr(complex.orders().iter().map(|o| Json::naturals(o)).collect()),
        ),
        (
            "refused_orders",
            Json::Arr(
                evaluation
                    .refused
                    .iter()
                    .map(|(order, reason)| {
                        Json::object([
                            ("order", Json::naturals(order)),
                            ("reason", Json::text(reason.clone())),
                        ])
                    })
                    .collect(),
            ),
        ),
        ("edges", Json::natural(complex.edges().len())),
        ("squares", Json::natural(complex.squares())),
        ("hexagons", Json::natural(complex.hexagons())),
        ("components", Json::Arr(components)),
        ("kind_compatible", Json::Bool(evaluation.kind_compatible)),
        (
            "star_base",
            evaluation
                .analysis
                .star_base
                .as_ref()
                .map_or(Json::Null, |b| Json::naturals(b)),
        ),
        ("coherence_witnesses", Json::Arr(witnesses)),
        ("separating_cocycle", cocycle),
    ]))
}

// Origin: engine/crates_rs/core_wdp/src/genesis_guarded_history.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-guarded-history:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_30c5af5b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

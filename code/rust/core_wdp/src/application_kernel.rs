//! Bounded replay of the existing finite belief certificates; never calls a producer.
//! AuthorityEffect: None. Exact rationals and original model-derived transitions.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a99d84bf<T> {
    fn checked_invariant_a99d84bf(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a99d84bf<T> for Option<T> {
    #[inline]
    fn checked_invariant_a99d84bf(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a99d84bf<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a99d84bf(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use serde_json::{json, Map, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::str::FromStr;

type Belief = Vec<String>;
type Move = (String, BigRational, Vec<Belief>);
type Checked<T> = Result<T, String>;
const MODEL_KEYS: &[&str] = &[
    "schema",
    "task_id",
    "assumptions",
    "authorization",
    "states",
    "actions",
    "enabled",
    "transitions",
    "reports",
    "initial",
    "targets",
    "costs",
    "resolutions",
    "valid_resolutions",
    "emissions",
];
const CERT_KEYS: &[&str] = &[
    "schema",
    "kind",
    "model_digest",
    "task_id",
    "assumptions",
    "authorization",
    "initial",
    "winning",
    "losing",
    "stalled",
    "closure",
    "strategy",
    "ranks",
    "values",
    "resolutions",
    "optimality_requested",
];
fn require(yes: bool, message: &str) -> Checked<()> {
    if yes {
        Ok(())
    } else {
        Err(message.into())
    }
}
fn fields<'a>(value: &'a Value, keys: &[&str]) -> Checked<&'a Map<String, Value>> {
    let expected: BTreeSet<_> = keys.iter().map(|s| s.to_string()).collect();
    let error = || {
        format!(
            "expected exactly these fields: [{}]",
            expected
                .iter()
                .map(|s| format!("'{s}'"))
                .collect::<Vec<_>>()
                .join(", ")
        )
    };
    let object = value.as_object().ok_or_else(error)?;
    if object.keys().cloned().collect::<BTreeSet<_>>() != expected {
        return Err(error());
    }
    Ok(object)
}
fn rows<'a>(value: &'a Value, reason: &str) -> Checked<&'a Vec<Value>> {
    value.as_array().ok_or_else(|| reason.into())
}
fn names(value: &Value, nonempty: bool) -> Checked<Belief> {
    let values = rows(value, "expected a list of nonempty strings")?;
    let parsed = values
        .iter()
        .map(|v| {
            v.as_str()
                .filter(|s| !s.is_empty())
                .map(str::to_string)
                .ok_or_else(|| "expected a list of nonempty strings".into())
        })
        .collect::<Checked<Vec<_>>>()?;
    let unique = parsed.iter().cloned().collect::<BTreeSet<_>>();
    require(
        parsed.len() == unique.len() && (!nonempty || !parsed.is_empty()),
        "duplicate names or empty required list",
    )?;
    Ok(unique.into_iter().collect())
}
fn belief(value: &Value, states: &Belief) -> Checked<Belief> {
    let b = names(value, true)?;
    require(
        b.iter().all(|s| states.contains(s)),
        "belief outside original carrier",
    )?;
    Ok(b)
}
fn digit_group(text: &str, allow_empty: bool) -> bool {
    let bytes = text.as_bytes();
    if bytes.is_empty() {
        return allow_empty;
    }
    bytes.iter().enumerate().all(|(index, byte)| {
        byte.is_ascii_digit()
            || (*byte == b'_'
                && index > 0
                && index + 1 < bytes.len()
                && bytes[index - 1].is_ascii_digit()
                && bytes[index + 1].is_ascii_digit())
    })
}
fn unsigned_sign(text: &str) -> (&str, &str) {
    match text.as_bytes().first() {
        Some(b'-') => ("-", &text[1..]),
        Some(b'+') => ("", &text[1..]),
        _ => ("", text),
    }
}
fn decimal(text: &str) -> Checked<BigRational> {
    // Match Fraction's ASCII lexical grammar before normalizing separators.
    // In particular, an underscore separates digits and denominators have no sign.
    let source = text.trim();
    require(source.len() <= 4096, "rational resource bound")?;
    let (sign, unsigned) = unsigned_sign(source);
    if let Some((numerator, denominator)) = unsigned.split_once('/') {
        let numerator = numerator.trim_end();
        let denominator = denominator.trim_start();
        require(
            digit_group(numerator, false) && digit_group(denominator, false),
            "invalid rational",
        )?;
        let numerator = BigInt::from_str(&format!("{sign}{}", numerator.replace('_', "")))
            .map_err(|_| "invalid rational")?;
        let denominator =
            BigInt::from_str(&denominator.replace('_', "")).map_err(|_| "invalid rational")?;
        require(!denominator.is_zero(), "invalid rational")?;
        return Ok(BigRational::new(numerator, denominator));
    }
    let (base, exponent) = if let Some(index) = unsigned.find(['e', 'E']) {
        let exponent_text = &unsigned[index + 1..];
        let (_, digits) = unsigned_sign(exponent_text);
        require(digit_group(digits, false), "invalid rational")?;
        (
            &unsigned[..index],
            exponent_text
                .replace('_', "")
                .parse::<i32>()
                .map_err(|_| "rational resource bound")?,
        )
    } else {
        (unsigned, 0)
    };
    require(exponent.unsigned_abs() <= 4096, "rational resource bound")?;
    let (whole, decimal) = base.split_once('.').unwrap_or((base, ""));
    require(
        digit_group(whole, true)
            && digit_group(decimal, true)
            && (!whole.is_empty() || !decimal.is_empty()),
        "invalid rational",
    )?;
    let whole = whole.replace('_', "");
    let decimal = decimal.replace('_', "");
    let numerator =
        BigInt::from_str(&format!("{sign}{whole}{decimal}")).map_err(|_| "invalid rational")?;
    let scale = decimal.len() as i32 - exponent;
    if scale >= 0 {
        Ok(BigRational::new(
            numerator,
            BigInt::from(10u8).pow(scale as u32),
        ))
    } else {
        Ok(BigRational::from_integer(
            numerator * BigInt::from(10u8).pow((-scale) as u32),
        ))
    }
}
fn rational(value: &Value, positive: bool) -> Checked<BigRational> {
    let s = value
        .as_str()
        .ok_or("rational values must be strings, never floats or booleans")?;
    let q = decimal(s)?;
    require(
        !q.is_negative() && (!positive || !q.is_zero()),
        "negative value or nonpositive action cost",
    )?;
    Ok(q)
}
fn qtext(value: &BigRational) -> String {
    if value.denom().is_one() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}
/// Named Python sorted-key, ASCII-escaped profile for Python-generated JSON.
/// Integers retain arbitrary precision; non-ASCII strings use UTF-16 escapes.
pub fn model_digest(value: &Value) -> Checked<String> {
    // Preserve numeric lexemes from the Python-generated JSON wire (including
    // invalid float witnesses, whose checker refusal still needs a bound digest).
    // Sorting is by Unicode scalar keys, matching this named Python profile.
    fn ordered(value: &Value) -> Value {
        match value {
            Value::Object(fields) => Value::Object(
                fields
                    .iter()
                    .map(|(k, v)| (k.clone(), ordered(v)))
                    .collect::<BTreeMap<_, _>>()
                    .into_iter()
                    .collect(),
            ),
            Value::Array(items) => Value::Array(items.iter().map(ordered).collect()),
            _ => value.clone(),
        }
    }
    let text = serde_json::to_string(&ordered(value)).map_err(|e| e.to_string())?;
    let mut ascii = String::new();
    for c in text.chars() {
        if c as u32 >= 127 {
            let mut buffer = [0u16; 2];
            for unit in c.encode_utf16(&mut buffer).iter() {
                ascii.push_str(&format!("\\u{unit:04x}"));
            }
        } else {
            ascii.push(c);
        }
    }
    Ok(crate::types::sha256_digest(ascii.as_bytes()))
}
struct Arena {
    digest: String,
    task: String,
    assumptions: Belief,
    authorization: Value,
    states: Belief,
    initial: Belief,
    targets: BTreeSet<Belief>,
    reachable: BTreeSet<Belief>,
    edges: BTreeMap<Belief, Vec<Move>>,
    valid: BTreeMap<Belief, Belief>,
}
impl Arena {
    fn moves(&self, b: &Belief) -> &[Move] {
        self.edges.get(b).map(Vec::as_slice).unwrap_or(&[])
    }
    fn resolutions(&self, b: &Belief) -> &[String] {
        self.valid.get(b).map(Vec::as_slice).unwrap_or(&[])
    }
}
fn compile(model: &Value) -> Checked<Arena> {
    let m = fields(model, MODEL_KEYS)?;
    require(
        m["schema"] == "wdp-finite-belief-model-v1"
            && m["task_id"].as_str().is_some_and(|s| !s.is_empty()),
        "unknown schema or missing task identity",
    )?;
    let assumptions = names(&m["assumptions"], false)?;
    require(
        ["A2", "A4", "A5", "A6"]
            .iter()
            .all(|s| assumptions.iter().any(|a| a == s)),
        "missing declared model assumptions",
    )?;
    require(
        m["authorization"].is_object(),
        "authorization binding must be an object",
    )?;
    let states = names(&m["states"], true)?;
    let actions = names(&m["actions"], false)?;
    require(
        states.len() <= 64 && actions.len() <= 64,
        "finite arena resource bound",
    )?;
    let enabled_wire = m["enabled"]
        .as_object()
        .ok_or("enablement must cover exactly the carrier")?;
    require(
        enabled_wire.keys().cloned().collect::<BTreeSet<_>>() == states.iter().cloned().collect(),
        "enablement must cover exactly the carrier",
    )?;
    let mut enabled = BTreeMap::new();
    for s in &states {
        let ns = names(&enabled_wire[s], false)?;
        require(
            ns.iter().all(|a| actions.contains(a)),
            "undeclared enabled action",
        )?;
        enabled.insert(s.clone(), ns);
    }
    let required: BTreeSet<_> = enabled
        .iter()
        .flat_map(|(s, acts)| acts.iter().map(move |a| (s.clone(), a.clone())))
        .collect();
    let mut transitions = BTreeMap::new();
    for entry in rows(&m["transitions"], "transition table must be a list")? {
        let row = fields(entry, &["state", "action", "successors"])?;
        let key = (
            row["state"].as_str().unwrap_or("").to_string(),
            row["action"].as_str().unwrap_or("").to_string(),
        );
        require(
            required.contains(&key) && !transitions.contains_key(&key),
            "duplicate or non-enabled transition row",
        )?;
        transitions.insert(key, belief(&row["successors"], &states)?);
    }
    require(
        transitions.keys().cloned().collect::<BTreeSet<_>>() == required,
        "enabled transitions must be total and nonempty",
    )?;
    let required_reports: BTreeSet<_> = transitions
        .iter()
        .flat_map(|((_, a), ys)| ys.iter().map(move |y| (y.clone(), a.clone())))
        .collect();
    let mut reports = BTreeMap::new();
    for entry in rows(&m["reports"], "report table must be a list")? {
        let row = fields(entry, &["state", "action", "observation"])?;
        let key = (
            row["state"].as_str().unwrap_or("").to_string(),
            row["action"].as_str().unwrap_or("").to_string(),
        );
        require(
            required_reports.contains(&key)
                && !reports.contains_key(&key)
                && row["observation"].is_string(),
            "duplicate, unknown or malformed report",
        )?;
        reports.insert(key, row["observation"].as_str().checked_invariant_a99d84bf("checked invariant").to_string());
    }
    require(
        reports.keys().cloned().collect::<BTreeSet<_>>() == required_reports,
        "missing post-state report",
    )?;
    let initial = belief(&m["initial"], &states)?;
    let target_rows = rows(&m["targets"], "target set must be listed by the model")?
        .iter()
        .map(|b| belief(b, &states))
        .collect::<Checked<Vec<_>>>()?;
    let targets: BTreeSet<_> = target_rows.iter().cloned().collect();
    require(
        targets.len() == target_rows.len(),
        "duplicate target belief",
    )?;
    let resolutions = names(&m["resolutions"], false)?;
    let valid_wire = m["valid_resolutions"]
        .as_object()
        .ok_or("resolution checks must cover exactly the world carrier")?;
    require(
        valid_wire.keys().cloned().collect::<BTreeSet<_>>() == states.iter().cloned().collect(),
        "resolution checks must cover exactly the world carrier",
    )?;
    let mut valid_world = BTreeMap::new();
    for s in &states {
        let rs = names(&valid_wire[s], false)?;
        require(
            rs.iter().all(|r| resolutions.contains(r)),
            "undeclared resolution",
        )?;
        valid_world.insert(s.clone(), rs);
    }
    let emissions = m["emissions"].as_object().ok_or("malformed emission map")?;
    require(
        emissions.keys().all(|a| actions.contains(a)),
        "malformed emission map",
    )?;
    for (a, r) in emissions {
        let r = r.as_str().ok_or("unknown emitted resolution")?;
        require(
            resolutions.iter().any(|v| v == r),
            "unknown emitted resolution",
        )?;
        for s in &states {
            if enabled[s].contains(a) {
                let ys = &transitions[&(s.clone(), a.clone())];
                require(
                    valid_world[s].iter().any(|v| v == r)
                        && ys.iter().all(|y| targets.contains(&vec![y.clone()])),
                    "unsafe emission or emission outside declared targets",
                )?;
                require(ys.len() == 1, "emission must have a deterministic target")?;
            }
        }
    }
    let mut reachable: BTreeSet<Belief> = [initial.clone()].into_iter().collect();
    let mut pending = vec![initial.clone()];
    let mut raw_edges = vec![];
    let mut cursor = 0;
    while cursor < pending.len() {
        let b = pending[cursor].clone();
        cursor += 1;
        if targets.contains(&b) {
            continue;
        }
        for a in &actions {
            if !b.iter().all(|s| enabled[s].contains(a)) {
                continue;
            }
            let post: BTreeSet<_> = b
                .iter()
                .flat_map(|s| transitions[&(s.clone(), a.clone())].iter().cloned())
                .collect();
            let mut groups: BTreeMap<String, Belief> = BTreeMap::new();
            for y in post {
                groups
                    .entry(reports[&(y.clone(), a.clone())].clone())
                    .or_default()
                    .push(y);
            }
            let mut ys: Vec<_> = groups.into_values().collect();
            ys.sort();
            for y in &ys {
                if reachable.insert(y.clone()) {
                    pending.push(y.clone());
                    require(pending.len() <= 4096, "finite arena resource bound")?;
                }
            }
            raw_edges.push((b.clone(), a.clone(), ys));
            require(raw_edges.len() <= 8192, "finite arena resource bound")?;
        }
    }
    let required_costs: BTreeSet<_> = raw_edges
        .iter()
        .map(|(b, a, _)| (b.clone(), a.clone()))
        .collect();
    let mut costs = BTreeMap::new();
    for entry in rows(&m["costs"], "cost table must be a list")? {
        let row = fields(entry, &["belief", "action", "cost"])?;
        let key = (
            belief(&row["belief"], &states)?,
            row["action"].as_str().unwrap_or("").to_string(),
        );
        require(
            required_costs.contains(&key) && !costs.contains_key(&key),
            "duplicate or unreachable cost row",
        )?;
        costs.insert(key, rational(&row["cost"], true)?);
    }
    require(
        costs.keys().cloned().collect::<BTreeSet<_>>() == required_costs,
        "costs must cover every reachable enabled action",
    )?;
    let mut edges: BTreeMap<Belief, Vec<Move>> = BTreeMap::new();
    for (b, a, ys) in raw_edges {
        edges
            .entry(b.clone())
            .or_default()
            .push((a.clone(), costs[&(b, a)].clone(), ys));
    }
    let valid = reachable
        .iter()
        .map(|b| {
            (
                b.clone(),
                resolutions
                    .iter()
                    .filter(|r| b.iter().all(|s| valid_world[s].contains(r)))
                    .cloned()
                    .collect(),
            )
        })
        .collect();
    Ok(Arena {
        digest: model_digest(model)?,
        task: m["task_id"].as_str().checked_invariant_a99d84bf("checked invariant").into(),
        assumptions,
        authorization: m["authorization"].clone(),
        states,
        initial,
        targets,
        reachable,
        edges,
        valid,
    })
}
fn set(value: &Value, arena: &Arena) -> Checked<BTreeSet<Belief>> {
    let parsed = rows(value, "belief set must be a list")?
        .iter()
        .map(|v| belief(v, &arena.states))
        .collect::<Checked<Vec<_>>>()?;
    let s = parsed.iter().cloned().collect::<BTreeSet<_>>();
    require(s.len() == parsed.len(), "duplicate certificate belief")?;
    Ok(s)
}
fn map(value: &Value, arena: &Arena, field: &str) -> Checked<BTreeMap<Belief, Value>> {
    let mut result = BTreeMap::new();
    for entry in rows(value, "certificate map must be a list")? {
        let row = fields(entry, &["belief", field])?;
        let b = belief(&row["belief"], &arena.states)?;
        require(!result.contains_key(&b), "duplicate certificate map row")?;
        result.insert(b, row[field].clone());
    }
    Ok(result)
}
fn check(model: &Value, certificate: &Value) -> Checked<Value> {
    let a = compile(model)?;
    let c = fields(certificate, CERT_KEYS)?;
    require(
        c["schema"] == "wdp-progress-certificate-v1",
        "unknown certificate schema",
    )?;
    let kind = c["kind"].as_str().unwrap_or("");
    require(
        ["LOSS", "WIN_OPTIMAL", "WIN_FEASIBLE"].contains(&kind),
        "unknown claim type",
    )?;
    require(
        c["model_digest"] == a.digest && c["task_id"] == a.task,
        "original model or task binding mismatch",
    )?;
    require(
        c["assumptions"] == json!(a.assumptions),
        "assumptions changed",
    )?;
    require(
        c["authorization"] == a.authorization,
        "authorization binding changed",
    )?;
    require(
        belief(&c["initial"], &a.states)? == a.initial,
        "initial belief mismatch",
    )?;
    require(
        c["optimality_requested"].is_boolean(),
        "optimality flag is not boolean",
    )?;
    let targets: BTreeSet<_> = a.reachable.intersection(&a.targets).cloned().collect();
    let winning = set(&c["winning"], &a)?;
    let losing = set(&c["losing"], &a)?;
    let stalled = set(&c["stalled"], &a)?;
    require(
        winning.is_subset(&a.reachable) && losing.is_subset(&a.reachable),
        "certificate outside reachable arena",
    )?;
    require(
        losing.is_disjoint(&targets),
        "losing region contains a successful terminal",
    )?;
    require(
        stalled
            == losing
                .iter()
                .filter(|b| a.moves(b).is_empty())
                .cloned()
                .collect(),
        "fabricated or incomplete stalled classification",
    )?;
    let mut closure = BTreeMap::new();
    for entry in rows(&c["closure"], "closure map must be a list")? {
        let row = fields(entry, &["belief", "action", "successor"])?;
        let key = (
            belief(&row["belief"], &a.states)?,
            row["action"].as_str().unwrap_or("").to_string(),
        );
        require(!closure.contains_key(&key), "duplicate closure row")?;
        closure.insert(key, belief(&row["successor"], &a.states)?);
    }
    let required: BTreeSet<_> = losing
        .iter()
        .flat_map(|b| {
            a.moves(b)
                .iter()
                .map(move |(name, _, _)| (b.clone(), name.clone()))
        })
        .collect();
    require(
        closure.keys().cloned().collect::<BTreeSet<_>>() == required,
        "missing or extraneous losing closure witness",
    )?;
    for b in &losing {
        for (name, _, ys) in a.moves(b) {
            let y = &closure[&(b.clone(), name.clone())];
            require(
                ys.contains(y) && losing.contains(y),
                "adversary transition leaves the losing region",
            )?;
        }
    }
    if kind == "LOSS" {
        require(
            losing.contains(&a.initial),
            "initial belief outside submitted losing region",
        )?;
        require(
            winning.is_empty()
                && ["strategy", "ranks", "values", "resolutions"]
                    .iter()
                    .all(|k| c[*k] == json!([]))
                && c["optimality_requested"] == false,
            "loss certificate carries incompatible win fields",
        )?;
        return Ok(
            json!({"accepted":true,"claim":"LOSS","status":"Refuted","termination":if stalled.contains(&a.initial){"Stalled"}else{"Trapped"},"model_digest":a.digest,"authority_effect":"None"}),
        );
    }
    require(
        winning.contains(&a.initial),
        "winning certificate omits the initial belief",
    )?;
    require(
        winning.is_disjoint(&losing)
            && winning.union(&losing).cloned().collect::<BTreeSet<_>>() == a.reachable,
        "incomplete or overlapping reachable partition",
    )?;
    require(
        targets.is_subset(&winning),
        "winning region omits a successful terminal",
    )?;
    let values = map(&c["values"], &a, "value")?
        .into_iter()
        .map(|(b, v)| Ok((b, rational(&v, false)?)))
        .collect::<Checked<BTreeMap<_, _>>>()?;
    let ranks_raw = map(&c["ranks"], &a, "rank")?;
    let strategy = map(&c["strategy"], &a, "action")?;
    let resolutions = map(&c["resolutions"], &a, "resolution")?;
    require(
        values.keys().cloned().collect::<BTreeSet<_>>() == winning
            && ranks_raw.keys().cloned().collect::<BTreeSet<_>>() == winning,
        "value and rank maps must cover exactly the winning region",
    )?;
    let mut ranks = BTreeMap::new();
    for (b, v) in ranks_raw {
        require(
            matches!(&v, Value::Number(number) if !number.is_f64()),
            "rank is not a natural number",
        )?;
        let n = BigInt::from_str(&v.to_string()).map_err(|_| "rank is not a natural number")?;
        require(!n.is_negative(), "rank is not a natural number")?;
        ranks.insert(b, n);
    }
    require(
        strategy.keys().cloned().collect::<BTreeSet<_>>()
            == winning.difference(&targets).cloned().collect(),
        "strategy domain differs from nonterminal winners",
    )?;
    require(
        resolutions.keys().cloned().collect::<BTreeSet<_>>()
            == winning
                .iter()
                .filter(|b| !a.resolutions(b).is_empty())
                .cloned()
                .collect(),
        "missing or extraneous resolution witness",
    )?;
    for (b, r) in resolutions {
        require(
            r.as_str()
                .is_some_and(|s| a.resolutions(&b).iter().any(|v| v == s)),
            "resolution fails a supplied world check",
        )?;
    }
    for b in &targets {
        require(
            values[b].is_zero() && ranks[b].is_zero(),
            "terminal value and rank must be zero",
        )?;
    }
    let optimal = kind == "WIN_OPTIMAL";
    require(
        c["optimality_requested"] == optimal,
        "optimality obligation omitted or mistyped",
    )?;
    for b in winning.difference(&targets) {
        let selected = strategy[b].as_str().unwrap_or("");
        let (_, cost, ys) = a
            .moves(b)
            .iter()
            .find(|(name, _, _)| name == selected)
            .ok_or("selected action is not admissible")?;
        require(
            ys.iter()
                .all(|y| winning.contains(y) && ranks[y] < ranks[b]),
            "strategy leaves winners or fails strict rank descent",
        )?;
        let worst = ys
            .iter()
            .map(|y| values[y].clone())
            .max()
            .ok_or("empty successor set")?;
        require(values[b] == cost + worst, "upper equality failed")?;
        if optimal {
            for (_, alternative, successors) in a.moves(b) {
                if successors.iter().any(|y| losing.contains(y)) {
                    continue;
                }
                require(
                    successors.iter().all(|y| winning.contains(y)),
                    "unclassified successor",
                )?;
                let worst = successors
                    .iter()
                    .map(|y| values[y].clone())
                    .max()
                    .ok_or("empty successor set")?;
                require(
                    values[b] <= alternative + worst,
                    "lower inequality failed: a cheaper action exists",
                )?;
            }
        }
    }
    Ok(
        json!({"accepted":true,"claim":kind,"status":"Proved","initial_value":qtext(&values[&a.initial]),"model_digest":a.digest,"authority_effect":"None"}),
    )
}
/// Independent certificate replay. Exploration constructs model reachability only;
/// no strategy, minimax optimum or replacement certificate is produced.
pub fn check_certificate(model: &Value, certificate: &Value) -> Value {
    match check(model, certificate) {
        Ok(v) => v,
        Err(reason) => {
            json!({"accepted":false,"status":"Refused","reason":reason,"authority_effect":"None"})
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/application_kernel.rs
// Claim: urn:core:crates_rs:core-wdp:application-kernel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda99d84bf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda99d84bf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora99d84bf {
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
impl BoundaryErrora99d84bf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora99d84bf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora99d84bf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda99d84bf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora99d84bf> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora99d84bf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora99d84bf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora99d84bf::ExceedsCapacity {
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
    fn fifteen_independent_reference_records_are_replayed_without_search() {
        let fixture: Value = serde_json::from_str(include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"), "/../applications/wdp_products/reference/certified_progress/evidence/records.json"
        ))).unwrap();
        let records = fixture["records"].as_array().unwrap();
        assert_eq!(records.len(), 15);
        for row in records {
            let actual = check_certificate(&row["model"], &row["certificate"]);
            assert_eq!(actual, row["receipt"], "reference case {}", row["name"]);
        }
    }
    #[test]
    fn unicode_and_arbitrary_size_exact_scalars_are_not_approximated() {
        assert_eq!(
            qtext(&decimal("1000000000000000000001/3").unwrap()),
            "1000000000000000000001/3"
        );
        assert!(decimal("1/0").is_err());
        for invalid in ["3_", "3__0", "_3", "1_e2", "1e_2", "1/+2", "-1/-3", "1/-2"] {
            assert!(
                decimal(invalid).is_err(),
                "malformed scalar accepted: {invalid}"
            );
        }
        for (source, expected) in [
            ("1_0", "10"),
            ("1 / 2", "1/2"),
            ("+3", "3"),
            ("1/2_0", "1/20"),
            ("+.5", "1/2"),
            ("1.e+2", "100"),
        ] {
            assert_eq!(qtext(&decimal(source).unwrap()), expected);
        }
        assert!(decimal("1e-2147483648").is_err());
        assert_eq!(
            model_digest(&json!({"theta":"\u{03b8}"})).unwrap(),
            crate::types::sha256_digest(br#"{"theta":"\u03b8"}"#)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_a99d84bf {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda99d84bf::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda99d84bf::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda99d84bf::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda99d84bf::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda99d84bf::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora99d84bf::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora99d84bf::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

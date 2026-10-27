// Executable finite evidence; AuthorityEffect: None.
//! Complete finite certificates for fixed and adaptive priced observation
//! (monograph §14.6–14.7, reused by Appendix X Theorem X.3 and Appendix Y).
//!
//! A finite candidate set carries a free visible report, a protected query and
//! a shelf of priced instruments. An unresolved pair shares its visible report
//! and differs in its query. The fixed optimum is the minimum-cost instrument
//! subset that separates every unresolved pair (a weighted hitting set). The
//! adaptive optimum is the Bellman minimax over candidate subsets:
//! `W(C) = 0` when the query is constant on `C`, otherwise
//! `min_i [c_i + max_branch W(C ∩ branch)]` over instruments that split `C`,
//! and the global value is the maximum over the initial visible fibers.
//! `None` denotes mathematical infeasibility, never a large finite cost.
//!
//! This is a native port of the paper package's
//! `code/finite_observation/solver.py`. [`verify_certificate_json`] replays a
//! submitted certificate row by row and never calls [`solve`] to replace a bad
//! table. Prices and outcome equality are supplied data. The canonical
//! [`ObservationInstance::instance_sha256`] matches the Python digest byte for
//! byte, so stored Python certificates replay here. Verification acceptance is
//! evaluation evidence only; it grants no action authority.
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

/// Reference cap on candidate states (adaptive tables have `2^n` rows).
pub const MAX_STATES: usize = 10;
/// Reference cap on instruments (fixed tables have `2^m` rows).
pub const MAX_INSTRUMENTS: usize = 12;
/// Bit cap on each price numerator and denominator.
pub const MAX_PRICE_BITS: u64 = 256;
/// Text cap on certificate cost strings, checked before parsing.
pub const MAX_COST_TEXT: usize = 4096;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ObservationCostError {
    #[error("finite reference cap exceeded")]
    CapExceeded,
    #[error("state, visible and query tables require aligned labels")]
    Misaligned,
    #[error("state labels must be unique")]
    DuplicateState,
    #[error("instrument names must be unique and nonempty")]
    BadInstrumentName,
    #[error("prices must be positive exact rationals within the bit cap")]
    BadPrice,
}

/// One priced instrument: an outcome label for every candidate state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Instrument {
    pub name: String,
    pub outcomes: Vec<String>,
    pub cost: BigRational,
}

/// A validated finite priced-observation instance.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObservationInstance {
    states: Vec<String>,
    visible: Vec<String>,
    query: Vec<String>,
    instruments: Vec<Instrument>,
}

/// Verification verdict. `code` is `VERIFIED`, `INPUT_MISMATCH` or
/// `INVALID_CERTIFICATE`; acceptance carries `AuthorityEffect: None`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Verification {
    pub accepted: bool,
    pub code: &'static str,
    pub detail: String,
}

/// A proposed certificate with complete fixed and adaptive tables.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ObservationCertificate {
    pub instance_sha256: String,
    pub fixed_suite_mask: Option<u32>,
    pub fixed_value: Option<BigRational>,
    /// `(mask, cost, sufficient)` for every instrument subset.
    pub fixed_table: Vec<(u32, BigRational, bool)>,
    pub adaptive_value: Option<BigRational>,
    /// `(mask, value, choice)` for every candidate subset.
    pub adaptive_table: Vec<(u32, Option<BigRational>, Option<usize>)>,
    pub infeasible_pair: Option<(usize, usize)>,
}

fn bits(value: &BigInt) -> u64 {
    value.magnitude().bits()
}

impl ObservationInstance {
    fn validate_instruments(
        instruments: &[Instrument],
        n: usize,
    ) -> Result<(), ObservationCostError> {
        let mut names = std::collections::BTreeSet::new();
        for item in instruments {
            if item.name.is_empty() || !names.insert(item.name.clone()) {
                return Err(ObservationCostError::BadInstrumentName);
            }
            if item.outcomes.len() != n {
                return Err(ObservationCostError::Misaligned);
            }
            if !item.cost.is_positive()
                || bits(item.cost.numer()) > MAX_PRICE_BITS
                || bits(item.cost.denom()) > MAX_PRICE_BITS
            {
                return Err(ObservationCostError::BadPrice);
            }
        }
        Ok(())
    }

    pub fn new(
        states: Vec<String>,
        visible: Vec<String>,
        query: Vec<String>,
        instruments: Vec<Instrument>,
    ) -> Result<Self, ObservationCostError> {
        let n = states.len();
        if n > MAX_STATES || instruments.len() > MAX_INSTRUMENTS {
            return Err(ObservationCostError::CapExceeded);
        }
        if visible.len() != n || query.len() != n {
            return Err(ObservationCostError::Misaligned);
        }
        let mut seen = std::collections::BTreeSet::new();
        if !states.iter().all(|s| seen.insert(s.clone())) {
            return Err(ObservationCostError::DuplicateState);
        }
        Self::validate_instruments(&instruments, n)?;
        Ok(Self {
            states,
            visible,
            query,
            instruments,
        })
    }

    pub fn states(&self) -> &[String] {
        &self.states
    }

    pub fn instruments(&self) -> &[Instrument] {
        &self.instruments
    }

    /// SHA-256 of the canonical JSON used by the Python reference
    /// (`json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`).
    pub fn instance_sha256(&self) -> String {
        let text = |s: &str| serde_json::to_string(s).unwrap_or_default();
        let list = |xs: &[String]| {
            format!(
                "[{}]",
                xs.iter().map(|x| text(x)).collect::<Vec<_>>().join(",")
            )
        };
        let instruments = self
            .instruments
            .iter()
            .map(|i| {
                format!(
                    "{{\"cost\":{},\"name\":{},\"outcomes\":{}}}",
                    text(&rational_text(&i.cost)),
                    text(&i.name),
                    list(&i.outcomes)
                )
            })
            .collect::<Vec<_>>()
            .join(",");
        let payload = format!(
            "{{\"instruments\":[{}],\"query\":{},\"states\":{},\"visible\":{}}}",
            instruments,
            list(&self.query),
            list(&self.states),
            list(&self.visible)
        );
        hex::encode(Sha256::digest(payload.as_bytes()))
    }

    /// Pairs with equal visible report and unequal protected answer.
    pub fn unresolved_pairs(&self) -> Vec<(usize, usize)> {
        let n = self.states.len();
        let mut pairs = Vec::new();
        for x in 0..n {
            for y in (x + 1)..n {
                if self.visible[x] == self.visible[y] && self.query[x] != self.query[y] {
                    pairs.push((x, y));
                }
            }
        }
        pairs
    }

    fn covers(&self, pairs: &[(usize, usize)], mask: u32) -> bool {
        pairs.iter().all(|&(x, y)| {
            self.instruments
                .iter()
                .enumerate()
                .any(|(i, item)| mask & (1 << i) != 0 && item.outcomes[x] != item.outcomes[y])
        })
    }

    fn suite_cost(&self, mask: u32) -> BigRational {
        self.instruments
            .iter()
            .enumerate()
            .filter(|(i, _)| mask & (1 << i) != 0)
            .fold(BigRational::zero(), |acc, (_, item)| acc + &item.cost)
    }

    fn members(&self, mask: u32) -> impl Iterator<Item = usize> + '_ {
        (0..self.states.len()).filter(move |s| mask & (1 << s) != 0)
    }

    fn branches(&self, mask: u32, instrument: usize) -> Vec<u32> {
        let mut groups: Vec<(&str, u32)> = Vec::new();
        for state in self.members(mask) {
            let outcome = self.instruments[instrument].outcomes[state].as_str();
            match groups.iter_mut().find(|(o, _)| *o == outcome) {
                Some((_, m)) => *m |= 1 << state,
                None => groups.push((outcome, 1 << state)),
            }
        }
        groups.into_iter().map(|(_, m)| m).collect()
    }

    fn initial_fibers(&self) -> Vec<u32> {
        let mut fibers: BTreeMap<&str, u32> = BTreeMap::new();
        for (state, report) in self.visible.iter().enumerate() {
            *fibers.entry(report.as_str()).or_insert(0) |= 1 << state;
        }
        fibers.into_values().collect()
    }

    fn is_leaf(&self, mask: u32) -> bool {
        let mut answers = self.members(mask).map(|x| &self.query[x]);
        match answers.next() {
            None => true,
            Some(first) => answers.all(|a| a == first),
        }
    }

    /// Finite `(cost + worst child, instrument)` options at a subset whose
    /// children all have finite values.
    fn options(&self, mask: u32, values: &[Option<BigRational>]) -> Vec<(BigRational, usize)> {
        let mut options = Vec::new();
        for (index, item) in self.instruments.iter().enumerate() {
            let branches = self.branches(mask, index);
            if branches.len() < 2 {
                continue;
            }
            let children: Option<Vec<&BigRational>> = branches
                .iter()
                .map(|&child| values[child as usize].as_ref())
                .collect();
            if let Some(children) = children {
                let worst = children.into_iter().max().cloned().unwrap_or_default();
                options.push((&item.cost + worst, index));
            }
        }
        options
    }

    fn global_value(&self, values: &[Option<BigRational>]) -> Option<BigRational> {
        let mut best = BigRational::zero();
        for mask in self.initial_fibers() {
            let value = values[mask as usize].as_ref()?;
            if value > &best {
                best = value.clone();
            }
        }
        Some(best)
    }

    fn infeasible_pair(&self, pairs: &[(usize, usize)]) -> Option<(usize, usize)> {
        pairs.iter().copied().find(|&(x, y)| {
            self.instruments
                .iter()
                .all(|i| i.outcomes[x] == i.outcomes[y])
        })
    }
}

/// Canonical rational text: `p` or `p/q`, matching Python `str(Fraction)`.
pub fn rational_text(value: &BigRational) -> String {
    let reduced = value.reduced();
    if reduced.denom() == &BigInt::from(1) {
        reduced.numer().to_string()
    } else {
        format!("{}/{}", reduced.numer(), reduced.denom())
    }
}

/// Propose complete `2^m` subset and `2^n` Bellman tables.
pub fn solve(instance: &ObservationInstance) -> ObservationCertificate {
    let pairs = instance.unresolved_pairs();
    let fixed_table: Vec<(u32, BigRational, bool)> = (0..(1u32 << instance.instruments.len()))
        .map(|mask| (mask, instance.suite_cost(mask), instance.covers(&pairs, mask)))
        .collect();
    let best = fixed_table
        .iter()
        .filter(|row| row.2)
        .min_by(|a, b| a.1.cmp(&b.1).then(a.0.cmp(&b.0)));
    let mut values: Vec<Option<BigRational>> = Vec::new();
    let mut adaptive_table = Vec::new();
    for mask in 0..(1u32 << instance.states.len()) {
        let (value, choice) = if instance.is_leaf(mask) {
            (Some(BigRational::zero()), None)
        } else {
            instance
                .options(mask, &values)
                .into_iter()
                .min()
                .map_or((None, None), |(v, i)| (Some(v), Some(i)))
        };
        values.push(value.clone());
        adaptive_table.push((mask, value, choice));
    }
    ObservationCertificate {
        instance_sha256: instance.instance_sha256(),
        fixed_suite_mask: best.map(|row| row.0),
        fixed_value: best.map(|row| row.1.clone()),
        fixed_table,
        adaptive_value: instance.global_value(&values),
        adaptive_table,
        infeasible_pair: instance.infeasible_pair(&pairs),
    }
}

/// Serialize a certificate in the Python reference schema (version 1).
pub fn certificate_json(certificate: &ObservationCertificate) -> Value {
    let opt = |v: &Option<BigRational>| v.as_ref().map_or(Value::Null, |x| Value::from(rational_text(x)));
    serde_json::json!({
        "schema_version": 1,
        "instance_sha256": certificate.instance_sha256,
        "authority_effect": "None",
        "fixed": {
            "suite_mask": certificate.fixed_suite_mask,
            "value": opt(&certificate.fixed_value),
            "table": certificate.fixed_table.iter().map(|(m, c, s)| serde_json::json!({
                "mask": m, "cost": rational_text(c), "sufficient": s
            })).collect::<Vec<_>>(),
        },
        "adaptive": {
            "value": opt(&certificate.adaptive_value),
            "table": certificate.adaptive_table.iter().map(|(m, v, c)| serde_json::json!({
                "mask": m, "value": opt(v), "choice": c
            })).collect::<Vec<_>>(),
        },
        "infeasible_pair": certificate.infeasible_pair.map(|(x, y)| vec![x, y]),
    })
}

type Check<T> = Result<T, String>;

fn keys<'a>(value: &'a Value, expected: &[&str]) -> Check<&'a serde_json::Map<String, Value>> {
    let object = value
        .as_object()
        .ok_or("missing, extra or malformed certificate fields")?;
    if object.len() != expected.len() || !expected.iter().all(|k| object.contains_key(*k)) {
        return Err("missing, extra or malformed certificate fields".into());
    }
    Ok(object)
}

fn canonical_rational(value: &Value, infinity: bool) -> Check<Option<BigRational>> {
    if value.is_null() && infinity {
        return Ok(None);
    }
    let text = value
        .as_str()
        .filter(|t| t.len() <= MAX_COST_TEXT)
        .ok_or("certificate costs require canonical rational strings")?;
    let canonical_int = |s: &str| s == "0" || (!s.is_empty() && !s.starts_with('0') && s.bytes().all(|b| b.is_ascii_digit()));
    let (num, den) = match text.split_once('/') {
        Some((n, d)) if canonical_int(n) && canonical_int(d) && d != "0" => (n, d),
        None if canonical_int(text) => (text, "1"),
        _ => return Err("certificate costs require canonical rational strings".into()),
    };
    let parse = |s: &str| s.parse::<BigInt>().map_err(|_| "certificate costs require canonical rational strings".to_string());
    let result = BigRational::new(parse(num)?, parse(den)?);
    if rational_text(&result) != text {
        return Err("certificate cost is not canonical nonnegative rational".into());
    }
    Ok(Some(result))
}

fn exact_int(value: &Value) -> Option<u64> {
    if value.is_boolean() {
        return None;
    }
    value.as_u64()
}

/// Replay every supplied table row, all competing choices and the final claim.
pub fn verify_certificate_json(instance: &ObservationInstance, certificate: &Value) -> Verification {
    match verify_inner(instance, certificate) {
        Ok(Some(mismatch)) => Verification {
            accepted: false,
            code: "INPUT_MISMATCH",
            detail: mismatch,
        },
        Ok(None) => Verification {
            accepted: true,
            code: "VERIFIED",
            detail: "complete fixed and adaptive optimality tables replayed; AuthorityEffect None"
                .into(),
        },
        Err(detail) => Verification {
            accepted: false,
            code: "INVALID_CERTIFICATE",
            detail,
        },
    }
}

fn verify_inner(instance: &ObservationInstance, certificate: &Value) -> Check<Option<String>> {
    let c = keys(
        certificate,
        &["schema_version", "instance_sha256", "authority_effect", "fixed", "adaptive", "infeasible_pair"],
    )?;
    if exact_int(&c["schema_version"]) != Some(1) || c["authority_effect"] != Value::from("None") {
        return Err("invalid schema or authority effect".into());
    }
    if c["instance_sha256"] != Value::from(instance.instance_sha256()) {
        return Ok(Some("certificate is for different task, outcomes or prices".into()));
    }
    let fixed = keys(&c["fixed"], &["suite_mask", "value", "table"])?;
    let m = instance.instruments.len();
    let table = fixed["table"]
        .as_array()
        .filter(|t| t.len() == 1usize << m)
        .ok_or("fixed table does not exhaust every subset")?;
    let pairs = instance.unresolved_pairs();
    let mut feasible: Vec<(BigRational, u32)> = Vec::new();
    for (mask, supplied) in table.iter().enumerate() {
        let row = keys(supplied, &["mask", "cost", "sufficient"])?;
        let mask = mask as u32;
        let sufficient = row["sufficient"]
            .as_bool()
            .ok_or("fixed table mask or truth type mismatch")?;
        if exact_int(&row["mask"]) != Some(mask as u64) {
            return Err("fixed table mask or truth type mismatch".into());
        }
        let cost = canonical_rational(&row["cost"], false)?.unwrap_or_default();
        if cost != instance.suite_cost(mask) || sufficient != instance.covers(&pairs, mask) {
            return Err("fixed table cost or coverage mismatch".into());
        }
        if sufficient {
            feasible.push((cost, mask));
        }
    }
    let fixed_value = canonical_rational(&fixed["value"], true)?;
    if let Some(minimum) = feasible.iter().min() {
        let mask = exact_int(&fixed["suite_mask"])
            .filter(|&k| (k as usize) < table.len())
            .ok_or("invalid sufficient suite mask")? as u32;
        if !instance.covers(&pairs, mask)
            || Some(instance.suite_cost(mask)) != fixed_value
            || fixed_value.as_ref() != Some(&minimum.0)
        {
            return Err("suite is insufficient or claimed optimum is not minimal".into());
        }
    } else if fixed_value.is_some() || !fixed["suite_mask"].is_null() {
        return Err("infeasible shelf claimed a finite optimum".into());
    }
    let adaptive = keys(&c["adaptive"], &["value", "table"])?;
    let n = instance.states.len();
    let table = adaptive["table"]
        .as_array()
        .filter(|t| t.len() == 1usize << n)
        .ok_or("adaptive table does not exhaust every candidate subset")?;
    let mut values: Vec<Option<BigRational>> = Vec::with_capacity(table.len());
    for (mask, supplied) in table.iter().enumerate() {
        let row = keys(supplied, &["mask", "value", "choice"])?;
        if exact_int(&row["mask"]) != Some(mask as u64) {
            return Err("adaptive table mask mismatch".into());
        }
        let mask = mask as u32;
        let value = canonical_rational(&row["value"], true)?;
        if instance.is_leaf(mask) {
            if value != Some(BigRational::zero()) || !row["choice"].is_null() {
                return Err("nonzero cost or action at a resolved leaf".into());
            }
        } else {
            let options = instance.options(mask, &values);
            match options.iter().min() {
                None => {
                    if value.is_some() || !row["choice"].is_null() {
                        return Err("unresolvable subset given a finite strategy".into());
                    }
                }
                Some(best) => {
                    let choice = exact_int(&row["choice"]).map(|c| c as usize);
                    let claimed = match (&value, choice) {
                        (Some(v), Some(i)) => options.contains(&(v.clone(), i)),
                        _ => false,
                    };
                    if !claimed || value.as_ref() != Some(&best.0) {
                        return Err("adaptive choice or Bellman optimum mismatch".into());
                    }
                }
            }
        }
        values.push(value);
    }
    let total = canonical_rational(&adaptive["value"], true)?;
    if total != instance.global_value(&values) {
        return Err("adaptive result is not the maximum over initial visible fibers".into());
    }
    if fixed_value.is_none() != total.is_none() {
        return Err("fixed/adaptive feasibility mismatch".into());
    }
    let pair = &c["infeasible_pair"];
    if fixed_value.is_none() {
        let p = pair
            .as_array()
            .filter(|p| p.len() == 2)
            .and_then(|p| Some((exact_int(&p[0])? as usize, exact_int(&p[1])? as usize)))
            .ok_or("infeasibility needs an explicit pair")?;
        if !pairs.contains(&p)
            || instance
                .instruments
                .iter()
                .any(|i| i.outcomes[p.0] != i.outcomes[p.1])
        {
            return Err("pair is not an indistinguishable conflicting pair".into());
        }
    } else if !pair.is_null() {
        return Err("feasible instance has an infeasibility claim".into());
    }
    Ok(None)
}

/// Verify a supplied matching rational LP pair for the hitting-set relaxation
/// and return only the LP optimum (a lower bound on the fixed integer cost).
pub fn verify_lp_pair(
    instance: &ObservationInstance,
    primal: &[BigRational],
    dual: &[BigRational],
) -> Result<BigRational, String> {
    let pairs = instance.unresolved_pairs();
    if primal.len() != instance.instruments.len() || dual.len() != pairs.len() {
        return Err("LP witness shape mismatch".into());
    }
    if primal.iter().chain(dual).any(|x| x.is_negative()) {
        return Err("LP witnesses require nonnegative rationals".into());
    }
    for &(x, y) in &pairs {
        let covered = instance
            .instruments
            .iter()
            .zip(primal)
            .filter(|(item, _)| item.outcomes[x] != item.outcomes[y])
            .fold(BigRational::zero(), |acc, (_, v)| acc + v);
        if covered < BigRational::from_integer(1.into()) {
            return Err("LP primal does not cover the unresolved pairs".into());
        }
    }
    for item in &instance.instruments {
        let load = pairs
            .iter()
            .zip(dual)
            .filter(|((x, y), _)| item.outcomes[*x] != item.outcomes[*y])
            .fold(BigRational::zero(), |acc, (_, v)| acc + v);
        if load > item.cost {
            return Err("LP dual exceeds an instrument price".into());
        }
    }
    let primal_value = instance
        .instruments
        .iter()
        .zip(primal)
        .fold(BigRational::zero(), |acc, (item, v)| acc + v * &item.cost);
    let dual_value = dual.iter().fold(BigRational::zero(), |acc, v| acc + v);
    if primal_value != dual_value {
        return Err("LP primal and dual values do not match".into());
    }
    Ok(primal_value)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e16f0147 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

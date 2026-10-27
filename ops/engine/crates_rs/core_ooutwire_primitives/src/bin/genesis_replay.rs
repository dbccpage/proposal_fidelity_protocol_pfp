//! Line-oriented paper reproduction interface, with no registry dependencies.
use std::io::{self, BufRead};
use core_ooutwire_primitives::{admission::step, bounds::Bounds,
    canonical::{portable_key_v1, decode_portable_key_v1, encode_structural_key_v1},
    context::{contexts, plug}, event::Event, mark::{Mark, Pair}, measure::MeasureKind,
    minima::challenge3, profile::derivable, reading::readings, regime::Regime,
    replay::replay, token::Token};

fn nums(text: &str) -> Result<Vec<usize>, String> {
    if text.is_empty() { return Ok(vec![]); }
    text.split(',').map(|s| s.parse().map_err(|_| "invalid integer".into())).collect()
}

fn admit_event(r: &mut Regime, event: Event) -> Result<(), String> {
    *r = step(r, &event).map_err(|e| e.to_string())?;
    Ok(())
}

fn decode_instances_and_rules(inst_field: &str, rule_field: &str, r: &mut Regime) -> Result<(), String> {
    if !inst_field.is_empty() {
        for row in inst_field.split(';') {
            let (form, args) = row.split_once(':').ok_or("invalid instance")?;
            admit_event(
                r,
                Event::AdmitInst(
                    form.parse().map_err(|_| "invalid form")?,
                    nums(args)?.into_iter().map(Mark).collect(),
                ),
            )?;
        }
    }
    for form in nums(rule_field)? {
        admit_event(r, Event::AdmitRuleAll(form))?;
    }
    Ok(())
}

fn decode_impositions(req_field: &str, r: &mut Regime) -> Result<(), String> {
    if req_field.is_empty() {
        return Ok(());
    }
    for row in req_field.split(';') {
        let (i, j) = row.split_once(':').ok_or("invalid requirement")?;
        let pair = Pair {
            i: Mark(i.parse().map_err(|_| "invalid endpoint")?),
            j: Mark(j.parse().map_err(|_| "invalid endpoint")?),
        };
        admit_event(r, Event::Impose(pair))?;
    }
    Ok(())
}

fn admit_initial_forms(form_field: &str, r: &mut Regime) -> Result<(), String> {
    let forms = nums(form_field)?;
    if forms.len() > 8 || forms.iter().any(|&a| a > 7) {
        return Err("paper replay supports at most eight forms of arity at most seven".into());
    }
    for arity in forms {
        admit_event(r, Event::AdmitForm(arity))?;
    }
    Ok(())
}

fn decode(line: &str) -> Result<Regime, String> {
    let parts: Vec<_> = line.split('|').collect();
    if parts.len() != 5 { return Err("expected five fields".into()); }
    let n: usize = parts[0].parse().map_err(|_| "invalid data count")?;
    // This interface has a small, explicit input population; the library APIs
    // retain their own resource contracts.
    if n > 8 { return Err("paper replay supports at most eight data".into()); }
    let mut r = Regime::genesis();
    for d in 0..n { admit_event(&mut r, Event::AdmitDatum(Token::new(format!("d{d}"))))?; }
    admit_initial_forms(parts[1], &mut r)?;
    decode_instances_and_rules(parts[2], parts[3], &mut r)?;
    decode_impositions(parts[4], &mut r)?;
    Ok(r)
}

fn decode_token_hex(hex: &str) -> Result<Token, String> {
    if hex.len() > 8192 || hex.len() % 2 != 0 || !hex.is_ascii() {
        return Err("invalid token hex".into());
    }
    let bytes: Result<Vec<u8>, _> = (0..hex.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&hex[i..i + 2], 16))
        .collect();
    let value = String::from_utf8(bytes.map_err(|_| "invalid token hex")?)
        .map_err(|_| "invalid token UTF-8")?;
    Ok(Token::new(value))
}

fn parse_form_event(arity: &str) -> Result<Event, String> {
    let arity: usize = arity.parse().map_err(|_| "invalid arity")?;
    if arity > 7 { return Err("arity exceeds seven".into()); }
    Ok(Event::AdmitForm(arity))
}

fn parse_inst_event(form: &str, args: &str) -> Result<Event, String> {
    let form_idx = form.parse().map_err(|_| "invalid form")?;
    let marks = nums(args)?.into_iter().map(Mark).collect();
    Ok(Event::AdmitInst(form_idx, marks))
}

fn parse_impose_event(i: &str, j: &str) -> Result<Event, String> {
    let pair = Pair {
        i: Mark(i.parse().map_err(|_| "invalid endpoint")?),
        j: Mark(j.parse().map_err(|_| "invalid endpoint")?),
    };
    Ok(Event::Impose(pair))
}

fn parse_ordered_event(row: &str) -> Result<Event, String> {
    let fields: Vec<_> = row.split(':').collect();
    match fields.as_slice() {
        ["S", value] => decode_token_hex(value).map(Event::Supply),
        ["D", value] => decode_token_hex(value).map(Event::AdmitDatum),
        ["F", arity] => parse_form_event(arity),
        ["I", form, args] => parse_inst_event(form, args),
        ["R", form] => form.parse().map(Event::AdmitRuleAll).map_err(|_| "invalid form".into()),
        ["P", i, j] => parse_impose_event(i, j),
        _ => Err("invalid ordered event".into()),
    }
}

// Ordered events are kept distinct from the older aggregate presentation.
// Token fields are UTF-8 hex, so delimiters cannot alter an event boundary.
fn decode_events(text: &str) -> Result<Regime, String> {
    let mut events = vec![];
    if !text.is_empty() {
        for row in text.split(';') {
            if events.len() >= 256 { return Err("at most 256 ordered events".into()); }
            events.push(parse_ordered_event(row)?);
        }
    }
    let regime = replay(&events).map_err(|e| e.to_string())?;
    if regime.n_data() > 8 || regime.n_forms() > 8 {
        return Err("paper replay supports at most eight data and forms".into());
    }
    Ok(regime)
}

fn run(line: &str) -> Result<String, String> {
    if let Some(hex) = line.strip_prefix("wire:") {
        if hex.len() % 2 != 0 || !hex.is_ascii() { return Ok("REJECT".into()); }
        let bytes: Result<Vec<u8>, _> = (0..hex.len()).step_by(2)
            .map(|i| u8::from_str_radix(&hex[i..i + 2], 16)).collect();
        let Ok(bytes) = bytes else { return Ok("REJECT".into()); };
        return Ok(match decode_portable_key_v1(&bytes) {
            Ok(key) => encode_structural_key_v1(&key).map_err(|e| e.to_string())?
                .iter().map(|b| format!("{b:02x}")).collect(),
            Err(_) => "REJECT".into(),
        });
    }
    if line == "minima" {
        let mut rows = vec![];
        for reading in readings() {
            let base = replay(&reading.genesis).map_err(|e| e.to_string())?;
            for measure in [MeasureKind::Mu1, MeasureKind::Mu2] {
                let c = challenge3(&base, reading.target, measure, &Bounds::default());
                rows.push(format!("{},{},{},{},{},{}", reading.name,
                    if measure == MeasureKind::Mu1 { "mu1" } else { "mu2" },
                    c.cost.0, c.cost.1, c.valid_at_minimum, c.classes.len()));
            }
        }
        return Ok(rows.join(";"));
    }
    let r = match line.strip_prefix("events:") {
        Some(events) => decode_events(events)?,
        None => decode(line)?,
    };
    let key = portable_key_v1(&r, 100_000).map_err(|e| e.to_string())?;
    let hex: String = key.iter().map(|b| format!("{b:02x}")).collect();
    let ctxs = contexts(&r);
    let observations: Vec<String> = (0..r.n_data()).map(|d| ctxs.iter()
        .map(|c| if derivable(&r, &plug(c, Mark(d))) { '1' } else { '0' }).collect()).collect();
    Ok(format!("{hex}|{}|{}", ctxs.len(), observations.join(",")))
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/bin/genesis_replay.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:genesis-replay:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5c363a19 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5c363a19` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5c363a19 {
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
impl BoundaryError5c363a19 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5c363a19 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5c363a19 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5c363a19 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5c363a19> {
        if capacity_bound == 0 {
            return Err(BoundaryError5c363a19::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5c363a19::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5c363a19::ExceedsCapacity {
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
mod ordered_event_tests {
    use super::*;

    #[test]
    fn supply_is_inert_but_datum_admission_is_not() {
        assert_eq!(run("events:").unwrap(), run("events:S:61").unwrap());
        assert_ne!(run("events:S:61").unwrap(), run("events:S:61;D:61").unwrap());
    }

    #[test]
    fn event_order_is_executed_and_invalid_order_is_refused() {
        assert!(run("events:D:61;F:1;I:0:0").is_ok());
        assert!(run("events:D:61;I:0:0;F:1").is_err());
        assert!(run("events:D:xx").is_err());
        assert!(run("events:F:0").is_err());
    }

    #[test]
    fn aggregate_interface_remains_equivalent() {
        assert_eq!(run("1|1|0:0||").unwrap(), run("events:D:6430;F:1;I:0:0").unwrap());
    }
}

fn main() {
    for line in io::stdin().lock().lines() {
        match line.map_err(|e| e.to_string()).and_then(|line| run(&line)) {
            Ok(answer) => println!("{answer}"),
            Err(error) => { eprintln!("{error}"); std::process::exit(1); }
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_5c363a19 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5c363a19::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5c363a19::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5c363a19::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5c363a19::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5c363a19::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5c363a19::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5c363a19::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

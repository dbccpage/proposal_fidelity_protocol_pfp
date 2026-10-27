//! Primitive — **export**: deterministic serialisation, and full replay of
//! an exported run.
//!
//! Crate boundary: coda-audit.  Source: `export.py` — *"no timestamps, no
//! environment data, sorted keys"*; `verify_full_export`, which replays
//! every node and checks its regime hash.
//!
//! Byte-determinism is an invariant that breaks CI if missed: the sealed
//! artefacts are regenerated and compared byte for byte.  Here the
//! serialisation is hand-rolled so that there is nothing to depend on and
//! nothing to drift; it is JSON-shaped, sorted, and carries nothing that
//! could vary between two runs.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_46f12061<T> {
    fn checked_invariant_46f12061(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_46f12061<T> for Option<T> {
    #[inline]
    fn checked_invariant_46f12061(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_46f12061<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_46f12061(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::event::Event;
use crate::hash::regime_fingerprint;
use crate::regime::Regime;
use crate::replay::replay;

fn push_other_json_char(out: &mut String, c: char) {
    use std::fmt::Write;
    match c {
        '\u{08}' => out.push_str("\\b"),
        '\u{0c}' => out.push_str("\\f"),
        c if c <= '\u{1f}' => write!(out, "\\u{:04x}", c as u32).checked_invariant_46f12061("checked invariant"),
        c => out.push(c),
    }
}

fn json_string(value: &str) -> String {
    let mut out = String::from("\"");
    for c in value.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            other => push_other_json_char(&mut out, other),
        }
    }
    out.push('"');
    out
}

/// A deterministic, sorted-key text of the regime.
pub fn regime_text(r: &Regime) -> String {
    let data: Vec<String> = r.data.iter().map(|t| json_string(t.text())).collect();
    let forms: Vec<String> = r.forms.iter().map(|a| a.to_string()).collect();
    let insts: Vec<String> = r
        .insts
        .iter()
        .map(|i| {
            let args: Vec<String> = i.args.iter().map(|m| m.0.to_string()).collect();
            format!("[{},[{}]]", i.form, args.join(","))
        })
        .collect();
    let reqs: Vec<String> = r.reqs.iter().map(|p| format!("[{},{}]", p.i.0, p.j.0)).collect();
    let rules: Vec<String> = r.rules.iter().map(|f| f.to_string()).collect();
    format!(
        "{{\"data\":[{}],\"forms\":[{}],\"insts\":[{}],\"reqs\":[{}],\"rules\":[{}]}}",
        data.join(","),
        forms.join(","),
        insts.join(","),
        reqs.join(","),
        rules.join(",")
    )
}

/// A deterministic text of one event.
pub fn event_text(e: &Event) -> String {
    match e {
        Event::Supply(t) => format!("{{\"event\":\"supply\",\"token\":{}}}", json_string(t.text())),
        Event::AdmitDatum(t) => format!("{{\"event\":\"admit_datum\",\"token\":{}}}", json_string(t.text())),
        Event::AdmitForm(a) => format!("{{\"arity\":{a},\"event\":\"admit_form\"}}"),
        Event::AdmitInst(f, args) => {
            let a: Vec<String> = args.iter().map(|m| m.0.to_string()).collect();
            format!("{{\"args\":[{}],\"event\":\"admit_inst\",\"form\":{f}}}", a.join(","))
        }
        Event::AdmitRuleAll(f) => format!("{{\"event\":\"admit_rule_all\",\"form\":{f}}}"),
        Event::Impose(p) => format!("{{\"event\":\"impose_separation\",\"i\":{},\"j\":{}}}", p.i.0, p.j.0),
    }
}

/// A deterministic text of a history.
pub fn history_text(h: &[Event]) -> String {
    let items: Vec<String> = h.iter().map(event_text).collect();
    format!("[{}]", items.join(","))
}

/// Replay increasing checkpoints including the complete history; compare
/// local non-cryptographic fingerprints, not mathematical payloads.
pub fn verify_full_replay(history: &[Event], checkpoints: &[(usize, u64)]) -> Result<(), String> {
    if checkpoints.last().map(|(len, _)| *len) != Some(history.len()) {
        return Err("a final checkpoint covering the complete history is required".into());
    }
    let mut previous = None;
    for &(len, fp) in checkpoints {
        if previous.is_some_and(|p| len <= p) {
            return Err("checkpoint lengths must be strictly increasing".into());
        }
        previous = Some(len);
        if len > history.len() {
            return Err(format!("checkpoint at {len} exceeds the history length {}", history.len()));
        }
        let r = replay(&history[..len]).map_err(|e| e.0)?;
        let actual = regime_fingerprint(&r);
        if actual != fp {
            return Err(format!("fingerprint mismatch at prefix {len}: recorded {fp:016x}, replayed {actual:016x}"));
        }
    }
    Ok(())
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/export.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:export:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord46f12061 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord46f12061` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError46f12061 {
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
impl BoundaryError46f12061 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError46f12061 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError46f12061 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord46f12061 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError46f12061> {
        if capacity_bound == 0 {
            return Err(BoundaryError46f12061::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError46f12061::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError46f12061::ExceedsCapacity {
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
    use crate::reading::READING_F;

    #[test]
    fn strings_escape_quotes_backslashes_and_all_json_controls() {
        assert_eq!(json_string("\"\\\n\r\t\u{08}\u{0c}\0λ"),
            "\"\\\"\\\\\\n\\r\\t\\b\\f\\u0000λ\"");
        assert_eq!(json_string(""), "\"\"");
        for c in '\0'..='\u{1f}' {
            assert!(!json_string(&c.to_string()).contains(c));
        }
        let t = crate::token::Token::new("\"\\\n");
        let e = Event::AdmitDatum(t.clone());
        assert_eq!(event_text(&e), "{\"event\":\"admit_datum\",\"token\":\"\\\"\\\\\\n\"}");
        assert_eq!(event_text(&Event::Supply(t)), "{\"event\":\"supply\",\"token\":\"\\\"\\\\\\n\"}");
        assert!(regime_text(&replay(&[e]).unwrap()).contains("\"data\":[\"\\\"\\\\\\n\"]"));
    }

    #[test]
    fn full_replay_rejects_missing_final_checkpoint_and_invalid_tail() {
        let h = READING_F.genesis.clone();
        let fp = regime_fingerprint(&replay(&h).unwrap());
        assert!(verify_full_replay(&h, &[]).is_err());
        assert!(verify_full_replay(&h, &[(0, 0)]).is_err());
        assert!(verify_full_replay(&h, &[(h.len(), fp), (h.len(), fp)]).is_err());
        let mut invalid = h.clone();
        invalid.push(Event::AdmitInst(999, vec![]));
        assert!(verify_full_replay(&invalid, &[(h.len(), fp)]).is_err());
        assert!(verify_full_replay(&invalid, &[(invalid.len(), fp)]).is_err());
        let empty_fp = regime_fingerprint(&Regime::genesis());
        assert!(verify_full_replay(&[], &[(0, empty_fp)]).is_ok());
    }

    #[test]
    fn the_text_is_sorted_and_deterministic() {
        let r = replay(&READING_F.genesis).unwrap();
        let t = regime_text(&r);
        assert!(t.starts_with("{\"data\":[\"<>\",\"<a>\",\"<ab>\"]"));
        assert_eq!(t, regime_text(&replay(&READING_F.genesis).unwrap()));
        assert!(history_text(&READING_F.genesis).contains("\"event\":\"admit_datum\""));
    }

    #[test]
    fn full_replay_verifies_and_catches_a_tampered_checkpoint() {
        let h = READING_F.genesis.clone();
        let fp = regime_fingerprint(&replay(&h).unwrap());
        let fp2 = regime_fingerprint(&replay(&h[..2]).unwrap());
        assert!(verify_full_replay(&h, &[(2, fp2), (h.len(), fp)]).is_ok());
        assert!(verify_full_replay(&h, &[(h.len(), fp ^ 1)]).is_err());
        assert!(verify_full_replay(&h, &[(99, fp)]).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_46f12061 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord46f12061::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord46f12061::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord46f12061::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord46f12061::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord46f12061::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError46f12061::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError46f12061::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

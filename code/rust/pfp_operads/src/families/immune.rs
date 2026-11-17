//! The immune domain the workflow families share: thymic screening of detector rules, the
//! two-signal disposition, and the support an antibody needs to leave the candidate stage.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-immune:v1
//!
//! * [`screen`] runs each rule's pattern (see [`super::pattern`]) over a panel of clean texts.
//!   A rule whose pattern is refused, or that matches any panel text, is killed.
//! * [`decide`] gives the disposition of one candidate from the rule matches (Signal 1) and the
//!   danger a host check observed (Signal 2):
//!
//!   | Signal 1 | Signal 2           | disposition |
//!   |----------|--------------------|-------------|
//!   | none     | none               | `PASS` |
//!   | some     | none               | `DIAGNOSTIC_OR_NORMALIZE` |
//!   | none     | by an admitted host | `HOLD_OR_REPAIR` |
//!   | some     | by an admitted host, independent | `HOLD_OR_REPAIR` |
//!   | some     | by an admitted host, not independent | `HOLD_OR_REPAIR`, with the refusal code |
//!
//!   Signal 2 counts only from an observer the caller admits. From any other observer it is
//!   ignored: the disposition is `PASS`, or `DIAGNOSTIC_OR_NORMALIZE` when a rule matched, and
//!   the code says why. Independence is refused as `UNWITNESSED_DANGER_SIGNAL` (no observer),
//!   `TWO_SIGNAL_COLLAPSE` (a model, agent, detector or matcher, the matcher `regex` itself, the
//!   digest of the matches as the evidence, or a match inside the evidence spans) or
//!   `UNREGISTERED_DANGER_KIND`.
//! * [`custody`] is `Provisional` when at least three of an epitope's observations share no
//!   model, scaffold, precedent set or lineage root (the largest independent set of the
//!   conflict graph, computed exactly over at most 32 observations once repeats are dropped),
//!   else `Candidate`.
//!
//! Observer names are compared after trimming and lowercasing, where Python case-folds; the two
//! differ at a handful of characters such as `ß`.

use std::collections::BTreeSet;

use super::pattern::{self, is_space, Pattern, Rejected};
use super::sha256_hex;

/// The observers a host admits as a source of Signal 2.
pub const HOST_OBSERVERS: [&str; 4] = [
    "host.ast_parse",
    "host.contract_check",
    "host.public_smoke",
    "host.transition_table",
];

/// Producers that may never originate Signal 2, compared without regard to case.
pub const FORBIDDEN_OBSERVERS: [&str; 5] = ["MODEL", "LLM", "AGENT", "DETECTOR", "MATCHER"];

/// The danger kinds a host check may report.
pub const DANGER_KINDS: [&str; 4] = [
    "REPLAY_FAILURE",
    "PROTECTED_FIELD_VIOLATION",
    "MANIFEST_CONTAMINATION",
    "MALFORMED_PAYLOAD",
];

/// The matcher that produces Signal 1.
pub const MATCHER: &str = "regex";

/// The most observations whose support is computed exactly.
pub const SUPPORT_BUDGET: usize = 32;

/// The support an epitope needs to be provisional.
pub const SUPPORT_NEEDED: usize = 3;

/// A detector rule: a pattern that selects an epitope.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Rule {
    pub id: String,
    pub epitope: String,
    pub pattern: String,
}

/// What the thymus did with one rule.
#[derive(Debug, Clone)]
pub enum Fate {
    /// The rule matches no clean text; this is its compiled pattern.
    Admitted(Pattern),
    /// The pattern is refused or matches a clean text.
    Killed,
}

/// Screen each rule against the panel of clean texts. An error names a rule whose pattern uses
/// syntax the host does not read.
pub fn screen(rules: &[Rule], panel: &[&str]) -> Result<Vec<Fate>, String> {
    rules
        .iter()
        .map(|rule| match pattern::compile(&rule.pattern) {
            Ok(compiled) if panel.iter().any(|text| compiled.find(text).is_some()) => {
                Ok(Fate::Killed)
            }
            Ok(compiled) => Ok(Fate::Admitted(compiled)),
            Err(Rejected::Refused(_)) => Ok(Fate::Killed),
            Err(Rejected::Unread(what)) => Err(format!(
                "rule {}: the pattern uses {what}, which the host does not read",
                rule.id
            )),
        })
        .collect()
}

/// One rule's match in a text (Signal 1).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Match {
    pub detector: String,
    pub epitope: String,
    pub text: String,
    pub offset: usize,
}

/// The match of a rule in a text, when its pattern finds one.
pub fn signal1(text: &str, rule: &Rule, compiled: &Pattern) -> Option<Match> {
    compiled.find(text).map(|hit| Match {
        detector: rule.id.clone(),
        epitope: rule.epitope.clone(),
        text: hit.text,
        offset: hit.start,
    })
}

/// A danger a host check observed (Signal 2).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Danger {
    pub kind: String,
    pub observer: String,
    pub digest: String,
    /// Character spans of the evidence, `[low, high)`.
    pub spans: Vec<(usize, usize)>,
}

impl Danger {
    /// The danger of `kind` that `observer` saw in `evidence`.
    pub fn observed(kind: &str, observer: &str, evidence: &str) -> Danger {
        Danger {
            kind: kind.to_owned(),
            observer: observer.to_owned(),
            digest: format!("sha256:{}", sha256_hex(evidence)),
            spans: Vec::new(),
        }
    }
}

/// A JSON string with every character outside ASCII written as `\uXXXX`.
fn json_ascii(text: &str) -> String {
    let mut out = String::from("\"");
    for point in text.chars() {
        match point {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{8}' => out.push_str("\\b"),
            '\u{c}' => out.push_str("\\f"),
            ' '..='~' => out.push(point),
            other => {
                let mut units = [0u16; 2];
                for unit in other.encode_utf16(&mut units) {
                    out.push_str(&format!("\\u{unit:04x}"));
                }
            }
        }
    }
    out.push('"');
    out
}

/// The digest of a set of matches, independent of their order.
pub fn signal1_digest(matches: &[Match]) -> String {
    let mut rows: Vec<(&str, &str, usize)> = matches
        .iter()
        .map(|one| (one.epitope.as_str(), one.text.as_str(), one.offset))
        .collect();
    rows.sort_unstable();
    let rows: Vec<String> = rows
        .iter()
        .map(|(epitope, text, offset)| {
            format!("[{},{},{offset}]", json_ascii(epitope), json_ascii(text))
        })
        .collect();
    format!("sha256:{}", sha256_hex(&format!("[{}]", rows.join(","))))
}

fn trimmed(name: &str) -> String {
    name.trim_matches(is_space).to_lowercase()
}

/// Why Signal 2 is not independent of Signal 1, or nothing when it is.
fn collapse(matches: &[Match], danger: &Danger) -> Option<&'static str> {
    let observer = trimmed(&danger.observer);
    if observer.is_empty() {
        return Some("UNWITNESSED_DANGER_SIGNAL");
    }
    if FORBIDDEN_OBSERVERS
        .iter()
        .any(|name| trimmed(name) == observer)
        || observer == trimmed(MATCHER)
    {
        return Some("TWO_SIGNAL_COLLAPSE");
    }
    if !DANGER_KINDS.contains(&danger.kind.as_str()) {
        return Some("UNREGISTERED_DANGER_KIND");
    }
    if !matches.is_empty() && danger.digest == signal1_digest(matches) {
        return Some("TWO_SIGNAL_COLLAPSE");
    }
    let inside = matches.iter().any(|one| {
        let stop = one.offset + one.text.chars().count().max(1);
        danger
            .spans
            .iter()
            .any(|(low, high)| one.offset < *high && *low < stop)
    });
    inside.then_some("TWO_SIGNAL_COLLAPSE")
}

/// The disposition of a candidate.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Disposition {
    Pass,
    Diagnostic,
    Hold,
}

impl Disposition {
    pub fn name(self) -> &'static str {
        match self {
            Disposition::Pass => "PASS",
            Disposition::Diagnostic => "DIAGNOSTIC_OR_NORMALIZE",
            Disposition::Hold => "HOLD_OR_REPAIR",
        }
    }
}

/// A disposition and the refusal code the decision recorded, if any.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Decision {
    pub disposition: Disposition,
    pub code: Option<&'static str>,
}

/// The disposition for the matches and the danger. Signal 2 counts only from one of `observers`.
pub fn decide(matches: &[Match], danger: Option<&Danger>, observers: &[&str]) -> Decision {
    let matched = !matches.is_empty();
    let decided = |disposition, code| Decision { disposition, code };
    let Some(danger) = danger else {
        let disposition = if matched {
            Disposition::Diagnostic
        } else {
            Disposition::Pass
        };
        return decided(disposition, None);
    };
    if !observers.contains(&danger.observer.as_str()) {
        return if matched {
            decided(Disposition::Diagnostic, Some("TWO_SIGNAL_COLLAPSE"))
        } else {
            decided(Disposition::Pass, Some("UNWITNESSED_DANGER_SIGNAL"))
        };
    }
    let code = if matched {
        collapse(matches, danger)
    } else {
        None
    };
    decided(Disposition::Hold, code)
}

/// One occurrence of a failure and the four keys that correlate it with others: the model, the
/// scaffold, the precedent set and the lineage root. An empty key correlates with nothing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Observation {
    pub occurrence: String,
    pub keys: [String; 4],
}

/// The observations that count: a repeated occurrence id, or a repeated set of four keys, adds
/// nothing.
fn distinct(observations: &[Observation]) -> Vec<&Observation> {
    let mut occurrences: BTreeSet<&str> = BTreeSet::new();
    let mut keys: BTreeSet<&[String; 4]> = BTreeSet::new();
    let mut kept = Vec::new();
    for one in observations {
        if !one.occurrence.is_empty() && !occurrences.insert(&one.occurrence) {
            continue;
        }
        if keys.insert(&one.keys) {
            kept.push(one);
        }
    }
    kept
}

fn conflict(left: &Observation, right: &Observation) -> bool {
    left.keys
        .iter()
        .zip(&right.keys)
        .any(|(one, other)| !one.is_empty() && one == other)
}

/// The size of the largest set of nodes none of which conflicts, by branch and bound.
fn independent(edges: &[u64], mask: u64, count: usize, best: usize) -> usize {
    if count + mask.count_ones() as usize <= best {
        return best;
    }
    if mask == 0 {
        return best.max(count);
    }
    let pivot = mask.trailing_zeros() as usize;
    let rest = mask & !(1 << pivot);
    let with = independent(edges, rest & !edges[pivot], count + 1, best);
    independent(edges, rest, count, with)
}

/// The independent support of the observations, or nothing when there are more than
/// [`SUPPORT_BUDGET`] once repeats are dropped.
pub fn support(observations: &[Observation]) -> Option<usize> {
    let nodes = distinct(observations);
    if nodes.len() > SUPPORT_BUDGET {
        return None;
    }
    let edges: Vec<u64> = nodes
        .iter()
        .enumerate()
        .map(|(place, node)| {
            nodes
                .iter()
                .enumerate()
                .filter(|(other, one)| *other != place && conflict(node, one))
                .fold(0, |mask, (other, _)| mask | 1 << other)
        })
        .collect();
    let all = if nodes.is_empty() {
        0
    } else {
        u64::MAX >> (64 - nodes.len())
    };
    Some(independent(&edges, all, 0, 0))
}

/// `Provisional` when the observations have the support to be, else `Candidate`.
pub fn custody(observations: &[Observation]) -> &'static str {
    match support(observations) {
        Some(count) if count >= SUPPORT_NEEDED => "Provisional",
        _ => "Candidate",
    }
}

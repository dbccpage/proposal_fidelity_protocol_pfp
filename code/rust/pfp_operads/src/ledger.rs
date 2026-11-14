//! The failure ledger: what went wrong, the rule proposed from it, and whether the rule earned a place.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:ledger:v1
//!
//! An append-only, hash-chained list of records:
//!
//! 1. `failure`: a host-witnessed failure with its class, its DDC trace and the SHA-256 of its evidence.
//! 2. `candidate`: a rule (antibody, anti-skill, ...) derived from recorded failures.
//! 3. `trial`: the rule scored on held-out cases that share no id with the failures it came from.
//! 4. `admission`: allowed only on the rule's latest trial, when that trial beat the baseline and
//!    the rule fired on no clean case.
//! 5. `retirement`: takes a rule out of use, with a reason.
//!
//! A later run loads [`Ledger::admitted`]. A rejected rule may be tried again: a rejection is a
//! hypothesis about the rule, not a fact. Admission here means "may be loaded"; it is not a claim
//! that the rule is correct.
//!
//! An id may name its case: in `CASE@RUN` the case is the part before the first `@` (see
//! [`case_of`]). A trial is refused when a held-out case is the case of a failure its rule came
//! from, whatever the run.

use std::collections::{BTreeMap, BTreeSet};

use core_operad_canon::DdcOp;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::{canon_values, Refusal};

/// The `prev` of the first entry.
pub const GENESIS: &str = "0000000000000000000000000000000000000000000000000000000000000000";
const DOMAIN: &str = "pfp.operads.ledger.v1\n";

/// One thing the ledger can record.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Record {
    Failure {
        id: String,
        workflow: String,
        run: String,
        failure_class: String,
        ddc_trace: String,
        evidence_sha256: String,
    },
    Candidate {
        id: String,
        capability_kind: String,
        constraint: String,
        derived_from: Vec<String>,
    },
    Trial {
        candidate: String,
        held_out: Vec<String>,
        baseline_correct: u32,
        treated_correct: u32,
        clean_panel_hits: u32,
    },
    Admission {
        candidate: String,
        trial: u64,
    },
    Retirement {
        candidate: String,
        reason: String,
    },
}

/// A record in its place in the chain.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Entry {
    pub seq: u64,
    pub prev: String,
    pub record: Record,
    pub hash: String,
}

/// Where a rule stands. The names are the canon's `antibody_pharmacy_status`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Candidate,
    Admitted,
    Rejected,
    Retired,
}

impl Status {
    pub const ALL: [Status; 4] = [
        Status::Candidate,
        Status::Admitted,
        Status::Rejected,
        Status::Retired,
    ];

    pub fn as_str(self) -> &'static str {
        match self {
            Status::Candidate => "candidate",
            Status::Admitted => "admitted",
            Status::Rejected => "rejected",
            Status::Retired => "retired",
        }
    }
}

/// A rule a later run may load.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct AdmittedRule {
    pub id: String,
    pub capability_kind: String,
    pub constraint: String,
}

#[derive(Debug, Clone)]
struct Rule {
    capability_kind: String,
    constraint: String,
    derived_from: BTreeSet<String>,
    status: Status,
    last_trial: Option<(u64, bool)>,
}

/// The chain and the state it implies.
#[derive(Debug, Clone, Default)]
pub struct Ledger {
    entries: Vec<Entry>,
    failures: BTreeSet<String>,
    rules: BTreeMap<String, Rule>,
}

fn refuse<T>(code: &'static str, message: impl Into<String>) -> Result<T, Refusal> {
    Err(Refusal::new(code, message))
}

fn named(text: &str, what: &str) -> Result<(), Refusal> {
    if text.trim().is_empty() {
        return refuse("EMPTY_FIELD", format!("{what} must not be empty"));
    }
    Ok(())
}

fn distinct(ids: &[String], what: &str) -> Result<BTreeSet<String>, Refusal> {
    let set: BTreeSet<String> = ids.iter().cloned().collect();
    if ids.is_empty() || set.len() != ids.len() {
        return refuse(
            "BAD_ID_LIST",
            format!("{what} must be a nonempty list without repeats"),
        );
    }
    Ok(set)
}

/// The case an id names: the part before the first `@`, or the whole id.
pub fn case_of(id: &str) -> &str {
    id.split_once('@').map_or(id, |(case, _)| case)
}

fn is_sha256(text: &str) -> bool {
    text.len() == 64
        && text
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

fn chain_hash(seq: u64, prev: &str, record: &Record) -> Result<String, Refusal> {
    let body = serde_json::to_string(&(seq, prev, record))
        .map_err(|error| Refusal::new("ENCODING", error.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(DOMAIN.as_bytes());
    hasher.update(body.as_bytes());
    Ok(hex::encode(hasher.finalize()))
}

impl Ledger {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn entries(&self) -> &[Entry] {
        &self.entries
    }

    pub fn status(&self, candidate: &str) -> Option<Status> {
        self.rules.get(candidate).map(|rule| rule.status)
    }

    /// The hash of the last entry, which names this state of the ledger.
    pub fn head(&self) -> &str {
        self.entries
            .last()
            .map_or(GENESIS, |entry| entry.hash.as_str())
    }

    /// The ledger as it stood when its head was `head`.
    pub fn at(&self, head: &str) -> Result<Self, Refusal> {
        let kept = if head == GENESIS {
            0
        } else {
            match self.entries.iter().position(|entry| entry.hash == head) {
                Some(last) => last + 1,
                None => {
                    return refuse(
                        "UNKNOWN_LEDGER_HEAD",
                        "no entry of the ledger has that hash",
                    )
                }
            }
        };
        let mut earlier = Self::new();
        for entry in &self.entries[..kept] {
            earlier.append(entry.record.clone())?;
        }
        Ok(earlier)
    }

    /// A rule that may be put on trial: proposed, and neither admitted nor retired.
    pub fn on_trial(&self, candidate: &str) -> Result<AdmittedRule, Refusal> {
        match self.rules.get(candidate) {
            Some(rule) if matches!(rule.status, Status::Candidate | Status::Rejected) => {
                Ok(AdmittedRule {
                    id: candidate.to_owned(),
                    capability_kind: rule.capability_kind.clone(),
                    constraint: rule.constraint.clone(),
                })
            }
            Some(rule) => refuse(
                "NOT_ON_TRIAL",
                format!("{candidate} is {}", rule.status.as_str()),
            ),
            None => refuse(
                "UNKNOWN_CANDIDATE",
                format!("{candidate} was never proposed"),
            ),
        }
    }

    /// The rules a later run may load, in id order.
    pub fn admitted(&self) -> Vec<AdmittedRule> {
        self.rules
            .iter()
            .filter(|(_, rule)| rule.status == Status::Admitted)
            .map(|(id, rule)| AdmittedRule {
                id: id.clone(),
                capability_kind: rule.capability_kind.clone(),
                constraint: rule.constraint.clone(),
            })
            .collect()
    }

    fn rule(&mut self, candidate: &str) -> Result<&mut Rule, Refusal> {
        match self.rules.get_mut(candidate) {
            Some(rule) if rule.status != Status::Retired => Ok(rule),
            Some(_) => refuse("RULE_RETIRED", format!("{candidate} is retired")),
            None => refuse(
                "UNKNOWN_CANDIDATE",
                format!("{candidate} was never proposed"),
            ),
        }
    }

    fn check_failure(
        &self,
        id: &str,
        failure_class: &str,
        ddc_trace: &str,
        evidence: &str,
    ) -> Result<(), Refusal> {
        if self.failures.contains(id) {
            return refuse("DUPLICATE_ID", format!("failure {id} is already recorded"));
        }
        let known = canon_values("pharmacy_failure_class")?
            .iter()
            .chain(canon_values("anti_skill_failure_class")?)
            .any(|class| *class == failure_class);
        if !known {
            return refuse(
                "UNKNOWN_FAILURE_CLASS",
                format!("{failure_class} is not a canon failure class"),
            );
        }
        let lawful = ddc_trace
            .chars()
            .all(|letter| DdcOp::from_letter(&letter.to_string()).is_some());
        if ddc_trace.is_empty() || !lawful {
            return refuse(
                "BAD_DDC_TRACE",
                "the DDC trace must be a nonempty word over E, R, C, I, Λ, D, M, T",
            );
        }
        if !is_sha256(evidence) {
            return refuse(
                "BAD_EVIDENCE_HASH",
                "evidence_sha256 must be 64 lowercase hex digits",
            );
        }
        Ok(())
    }

    fn apply(&mut self, seq: u64, record: &Record) -> Result<(), Refusal> {
        match record {
            Record::Failure {
                id,
                workflow,
                run,
                failure_class,
                ddc_trace,
                evidence_sha256,
            } => {
                named(id, "id")?;
                named(workflow, "workflow")?;
                named(run, "run")?;
                self.check_failure(id, failure_class, ddc_trace, evidence_sha256)?;
                self.failures.insert(id.clone());
            }
            Record::Candidate {
                id,
                capability_kind,
                constraint,
                derived_from,
            } => {
                named(id, "id")?;
                named(constraint, "constraint")?;
                if self.rules.contains_key(id) {
                    return refuse(
                        "DUPLICATE_ID",
                        format!("candidate {id} is already recorded"),
                    );
                }
                if !canon_values("capability_kind")?.contains(&capability_kind.as_str()) {
                    return refuse(
                        "UNKNOWN_CAPABILITY_KIND",
                        format!("{capability_kind} is not a capability kind"),
                    );
                }
                let derived_from = distinct(derived_from, "derived_from")?;
                if !derived_from.is_subset(&self.failures) {
                    return refuse(
                        "UNKNOWN_FAILURE",
                        "a candidate must come from recorded failures",
                    );
                }
                let rule = Rule {
                    capability_kind: capability_kind.clone(),
                    constraint: constraint.clone(),
                    derived_from,
                    status: Status::Candidate,
                    last_trial: None,
                };
                self.rules.insert(id.clone(), rule);
            }
            Record::Trial {
                candidate,
                held_out,
                baseline_correct,
                treated_correct,
                clean_panel_hits,
            } => {
                let rule = self.rule(candidate)?;
                let cases = distinct(held_out, "held_out")?;
                let seen: BTreeSet<&str> = rule.derived_from.iter().map(|id| case_of(id)).collect();
                if cases.iter().any(|id| seen.contains(case_of(id))) {
                    return refuse(
                        "SPLIT_OVERLAP",
                        "a held-out case is one of the failures the rule came from",
                    );
                }
                if (*baseline_correct).max(*treated_correct) as usize > cases.len() {
                    return refuse("BAD_COUNT", "more correct answers than held-out cases");
                }
                let passed = treated_correct > baseline_correct && *clean_panel_hits == 0;
                rule.last_trial = Some((seq, passed));
                if rule.status != Status::Admitted {
                    rule.status = if passed {
                        Status::Candidate
                    } else {
                        Status::Rejected
                    };
                }
            }
            Record::Admission { candidate, trial } => {
                let rule = self.rule(candidate)?;
                if rule.status != Status::Candidate || rule.last_trial != Some((*trial, true)) {
                    return refuse(
                        "NOT_EARNED",
                        "admission needs the rule's latest trial, and that trial must have passed",
                    );
                }
                rule.status = Status::Admitted;
            }
            Record::Retirement { candidate, reason } => {
                named(reason, "reason")?;
                self.rule(candidate)?.status = Status::Retired;
            }
        }
        Ok(())
    }

    /// Check a record against the rules above and add it to the chain. A refused record changes nothing.
    pub fn append(&mut self, record: Record) -> Result<&Entry, Refusal> {
        let seq = self.entries.len() as u64;
        let prev = self.head().to_owned();
        let hash = chain_hash(seq, &prev, &record)?;
        self.apply(seq, &record)?;
        self.entries.push(Entry {
            seq,
            prev,
            record,
            hash,
        });
        self.entries
            .last()
            .ok_or_else(|| Refusal::new("ENCODING", "the ledger lost the entry it just added"))
    }

    /// Rebuild a ledger from JSON Lines, replaying every rule and every hash.
    pub fn from_lines(text: &str) -> Result<Self, Refusal> {
        let mut ledger = Self::new();
        for (number, line) in text
            .lines()
            .enumerate()
            .filter(|(_, line)| !line.trim().is_empty())
        {
            let stored: Entry = serde_json::from_str(line).map_err(|error| {
                Refusal::new("BAD_ENTRY", format!("line {}: {error}", number + 1))
            })?;
            let replayed = ledger.append(stored.record.clone())?;
            if *replayed != stored {
                return refuse(
                    "CHAIN_BROKEN",
                    format!("line {}: seq, prev or hash does not match", number + 1),
                );
            }
        }
        Ok(ledger)
    }

    /// The chain as JSON Lines.
    pub fn to_lines(&self) -> Result<String, Refusal> {
        let mut text = String::new();
        for entry in &self.entries {
            let line = serde_json::to_string(entry)
                .map_err(|error| Refusal::new("ENCODING", error.to_string()))?;
            text.push_str(&line);
            text.push('\n');
        }
        Ok(text)
    }
}

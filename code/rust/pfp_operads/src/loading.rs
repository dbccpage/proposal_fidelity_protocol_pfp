//! The seed a later run loads: a task's seed prompt with the ledger's rules written after it.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:loading:v1
//!
//! A workflow run takes its rules from here and nowhere else. [`load`] reads the ledger, takes the
//! rules it admits (and, for a trial, the one rule under trial) and writes them after the seed,
//! under a line that names the ledger state they came from. With no rule to load the seed comes
//! back byte for byte. [`loaded`] answers the later question: is this seed exactly what that
//! ledger state loads onto that base seed?

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::ledger::{AdmittedRule, Ledger};
use crate::Refusal;

/// How many hex digits of the ledger head the seed carries.
pub const HEAD_DIGITS: usize = 16;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LoadRequest {
    seed_prompt: String,
    /// A proposed rule to load beside the admitted ones, for the treated arm of its trial.
    #[serde(default)]
    on_trial: Option<String>,
}

/// A seed with its rules, and what it was made from.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Loaded {
    pub ledger_head: String,
    pub entries: usize,
    pub rules: Vec<AdmittedRule>,
    pub on_trial: Option<String>,
    pub base_seed_sha256: String,
    pub seed_sha256: String,
    pub seed_prompt: String,
}

fn sha256(text: &str) -> String {
    hex::encode(Sha256::digest(text.as_bytes()))
}

fn one_line(text: &str, what: &str, id: &str) -> Result<(), Refusal> {
    if text.contains(['\n', '\r']) {
        return Err(Refusal::new(
            "RULE_NOT_ONE_LINE",
            format!("the {what} of rule {id} has a line break"),
        ));
    }
    Ok(())
}

/// The rules a seed carries at this ledger state: the admitted ones, then the one under trial.
pub(crate) fn rules_of(
    ledger: &Ledger,
    on_trial: Option<&str>,
) -> Result<Vec<AdmittedRule>, Refusal> {
    let mut rules = ledger.admitted();
    if let Some(candidate) = on_trial {
        rules.push(ledger.on_trial(candidate)?);
    }
    for rule in &rules {
        one_line(&rule.id, "id", &rule.id)?;
        one_line(&rule.constraint, "constraint", &rule.id)?;
    }
    Ok(rules)
}

/// The seed with its rules written after it. No rule: the seed itself.
pub(crate) fn render(seed: &str, head: &str, rules: &[AdmittedRule]) -> String {
    if rules.is_empty() {
        return seed.to_owned();
    }
    let short: String = head.chars().take(HEAD_DIGITS).collect();
    let mut text = format!("{seed}\n\nRules loaded from failure ledger {short}:\n");
    for rule in rules {
        text.push_str(&format!("- [{}] {}\n", rule.id, rule.constraint));
    }
    text
}

/// Write the seed a run loads from this ledger.
pub fn load(ledger: &str, request: &str) -> Result<Loaded, Refusal> {
    let ledger = Ledger::from_lines(ledger)?;
    let request: LoadRequest = serde_json::from_str(request)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let rules = rules_of(&ledger, request.on_trial.as_deref())?;
    let seed_prompt = render(&request.seed_prompt, ledger.head(), &rules);
    Ok(Loaded {
        ledger_head: ledger.head().to_owned(),
        entries: ledger.entries().len(),
        rules,
        on_trial: request.on_trial,
        base_seed_sha256: sha256(&request.seed_prompt),
        seed_sha256: sha256(&seed_prompt),
        seed_prompt,
    })
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct LoadedRequest {
    base_seed_prompt: String,
    seed_prompt: String,
    ledger_head: String,
    #[serde(default)]
    on_trial: Option<String>,
}

/// Whether a seed is what a ledger state loads, with the rule ids that state loads.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct LoadCheck {
    pub accepted: bool,
    pub ledger_head: String,
    pub rules: Vec<String>,
    pub expected_seed_sha256: String,
    pub seed_sha256: String,
}

/// Recompute the seed from the base seed and the ledger as it stood at `ledger_head`, and compare.
pub fn loaded(ledger: &str, request: &str) -> Result<LoadCheck, Refusal> {
    let request: LoadedRequest = serde_json::from_str(request)
        .map_err(|error| Refusal::new("BAD_REQUEST", error.to_string()))?;
    let ledger = Ledger::from_lines(ledger)?.at(&request.ledger_head)?;
    let rules = rules_of(&ledger, request.on_trial.as_deref())?;
    let expected = render(&request.base_seed_prompt, ledger.head(), &rules);
    Ok(LoadCheck {
        accepted: expected == request.seed_prompt,
        ledger_head: request.ledger_head,
        rules: rules.into_iter().map(|rule| rule.id).collect(),
        expected_seed_sha256: sha256(&expected),
        seed_sha256: sha256(&request.seed_prompt),
    })
}

//! WF17, witnessed-difference programme: a claimed difference needs a separating formula, and
//! a claimed equivalence needs a bisimulation.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf17:v1
//!
//! The task is a finite labelled transition system, a list of `[state, label, state]`. A reply
//! lists claims about pairs of its states, and for claim `k` the host records
//!
//! * `claim<k>:states_declared`: both states occur in the transitions,
//! * `claim<k>:witnessed`: a difference carries a `witness`, an equivalence a `certificate`
//!   list, and then
//! * `claim<k>:separates`: the witness, a Hennessy-Milner formula, holds at one state and
//!   fails at the other, or
//! * `claim<k>:bisimulation`: the certificate is a list of distinct pairs of states that holds
//!   the claimed pair, and every move of either state of a pair is matched by a move of the
//!   other with the same label into a pair of the list.
//!
//! A claim that fails one of these is not checked further. The run is certified as
//! `CLAIMS_WITNESSED` when every predicate passed.
//!
//! A formula is `"tt"`, `"ff"`, `["not", f]`, `["and", f, g]`, `["or", f, g]`,
//! `["dia", label, f]` (some move with that label leads to a state where `f` holds) or
//! `["box", label, f]` (every such move does), nested at most 12 deep.
//!
//! Task: `transitions`, at most 256 triples of text.
//! Reply: `{"claims": [{"kind", "left", "right", "witness" | "certificate"}]}`.

use std::collections::BTreeSet;

use crate::datum::Datum;

use super::{no_reply, Checks, Family, Run, Stop, Verdict};

/// The most transitions a task may list.
pub const MAX_TRANSITIONS: usize = 256;

/// The deepest a formula may nest.
pub const MAX_DEPTH: usize = 12;

pub const FAMILY: Family = Family {
    workflow: "WF17",
    name: "Witnessed-difference programme",
    host_check: "hml_separator_bisimulation_check",
    validate,
    walk,
};

/// A labelled transition system: its moves, and every state a move names.
struct System<'t> {
    moves: Vec<(&'t str, &'t str, &'t str)>,
    states: BTreeSet<&'t str>,
}

fn triple(entry: &Datum) -> Option<(&str, &str, &str)> {
    match entry.as_list()? {
        [from, label, to] => Some((from.as_text()?, label.as_text()?, to.as_text()?)),
        _ => None,
    }
}

fn system(task: &Datum) -> Result<System<'_>, String> {
    let moves: Vec<(&str, &str, &str)> = task
        .get("transitions")
        .and_then(Datum::as_list)
        .and_then(|listed| listed.iter().map(triple).collect())
        .ok_or("transitions must be a list of [state, label, state] in text")?;
    if moves.len() > MAX_TRANSITIONS {
        return Err(format!("at most {MAX_TRANSITIONS} transitions"));
    }
    let states = moves.iter().flat_map(|&(from, _, to)| [from, to]).collect();
    Ok(System { moves, states })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    system(task).map(|_| ())
}

/// A Hennessy-Milner formula.
enum Formula<'r> {
    Constant(bool),
    Not(Box<Formula<'r>>),
    And(Box<Formula<'r>>, Box<Formula<'r>>),
    Or(Box<Formula<'r>>, Box<Formula<'r>>),
    Some(&'r str, Box<Formula<'r>>),
    Every(&'r str, Box<Formula<'r>>),
}

fn inner(part: &Datum, depth: usize) -> Result<Box<Formula<'_>>, String> {
    formula(part, depth + 1).map(Box::new)
}

fn unknown(written: &Datum) -> String {
    format!("unknown formula {}", written.canonical())
}

fn negation(arguments: &[Datum], depth: usize) -> Result<Formula<'_>, String> {
    match arguments {
        [part] => Ok(Formula::Not(inner(part, depth)?)),
        _ => Err("not takes one formula".to_owned()),
    }
}

/// `and` or `or` of two formulas.
fn joined<'r>(operator: &str, arguments: &'r [Datum], depth: usize) -> Result<Formula<'r>, String> {
    let [left, right] = arguments else {
        return Err(format!("{operator} takes two arguments"));
    };
    let (left, right) = (inner(left, depth)?, inner(right, depth)?);
    Ok(match operator {
        "and" => Formula::And(left, right),
        _ => Formula::Or(left, right),
    })
}

/// `dia` or `box` of a label and a formula.
fn modal<'r>(operator: &str, arguments: &'r [Datum], depth: usize) -> Result<Formula<'r>, String> {
    let [label, part] = arguments else {
        return Err(format!("{operator} takes two arguments"));
    };
    let label = label
        .as_text()
        .ok_or(format!("the label of {operator} must be text"))?;
    let part = inner(part, depth)?;
    Ok(match operator {
        "dia" => Formula::Some(label, part),
        _ => Formula::Every(label, part),
    })
}

fn formula(written: &Datum, depth: usize) -> Result<Formula<'_>, String> {
    if depth > MAX_DEPTH {
        return Err("formula too deep".to_owned());
    }
    if let Datum::Text(constant) = written {
        return match constant.as_str() {
            "tt" => Ok(Formula::Constant(true)),
            "ff" => Ok(Formula::Constant(false)),
            _ => Err(unknown(written)),
        };
    }
    let parts = written.as_list().and_then(|parts| parts.split_first());
    let Some((Datum::Text(operator), arguments)) = parts else {
        return Err(unknown(written));
    };
    match operator.as_str() {
        "not" => negation(arguments, depth),
        "and" | "or" => joined(operator, arguments, depth),
        "dia" | "box" => modal(operator, arguments, depth),
        _ => Err(unknown(written)),
    }
}

impl<'t> System<'t> {
    /// The states at which a formula holds.
    fn holds(&self, formula: &Formula) -> BTreeSet<&'t str> {
        let moved = |label: &str, target: &BTreeSet<&str>, wanted: bool| -> BTreeSet<&'t str> {
            let moves = self.moves.iter().filter(|(_, taken, _)| *taken == label);
            moves
                .filter(|(_, _, to)| target.contains(to) == wanted)
                .map(|&(from, _, _)| from)
                .collect()
        };
        match formula {
            Formula::Constant(true) => self.states.clone(),
            Formula::Constant(false) => BTreeSet::new(),
            Formula::Not(part) => &self.states - &self.holds(part),
            Formula::And(left, right) => &self.holds(left) & &self.holds(right),
            Formula::Or(left, right) => &self.holds(left) | &self.holds(right),
            Formula::Some(label, part) => moved(label, &self.holds(part), true),
            Formula::Every(label, part) => &self.states - &moved(label, &self.holds(part), false),
        }
    }

    /// The moves out of a state.
    fn from<'s>(&'s self, state: &'s str) -> impl Iterator<Item = &'s (&'t str, &'t str, &'t str)> {
        self.moves.iter().filter(move |(from, _, _)| *from == state)
    }

    /// Whether every move of either state of a pair is matched by a move of the other with the
    /// same label into a pair of the relation.
    fn is_bisimulation(&self, relation: &BTreeSet<(&str, &str)>) -> bool {
        relation.iter().all(|&(left, right)| {
            let forth = self.from(left).all(|(_, label, next)| {
                let matched = |(_, taken, other): &(&str, &str, &str)| {
                    taken == label && relation.contains(&(*next, *other))
                };
                self.from(right).any(matched)
            });
            let back = self.from(right).all(|(_, label, next)| {
                let matched = |(_, taken, other): &(&str, &str, &str)| {
                    taken == label && relation.contains(&(*other, *next))
                };
                self.from(left).any(matched)
            });
            forth && back
        })
    }

    /// The pairs a certificate lists, when they are distinct pairs of states.
    fn relation<'r>(&self, certificate: &'r [Datum]) -> Option<BTreeSet<(&'r str, &'r str)>> {
        let pair = |entry: &'r Datum| match entry.as_list()? {
            [left, right] => Some((left.as_text()?, right.as_text()?)),
            _ => None,
        };
        let relation: BTreeSet<(&str, &str)> =
            certificate.iter().map(pair).collect::<Option<_>>()?;
        let known = |&(left, right): &(&str, &str)| {
            self.states.contains(left) && self.states.contains(right)
        };
        (relation.len() == certificate.len() && relation.iter().all(known)).then_some(relation)
    }
}

/// Record the predicates of one claim, stopping at the first that fails.
fn claim(system: &System, number: usize, claim: &Datum, checks: &mut Checks) -> Result<(), String> {
    let difference = match claim.get("kind").and_then(Datum::as_text) {
        Some("difference") => true,
        Some("equivalence") => false,
        _ => return Err("claim kind".to_owned()),
    };
    let name = |predicate: &str| format!("claim{number}:{predicate}");
    let state = |side: &str| {
        let named = claim.get(side).and_then(Datum::as_text);
        named.filter(|state| system.states.contains(state))
    };
    let ends = state("left").zip(state("right"));
    checks.record(&name("states_declared"), ends.is_some(), claim);
    let Some((left, right)) = ends else {
        return Ok(());
    };
    if difference {
        let witness = claim.get("witness");
        checks.record(&name("witnessed"), witness.is_some(), claim);
        let Some(witness) = witness else {
            return Ok(());
        };
        let holds = system.holds(&formula(witness, 0)?);
        let separates = holds.contains(left) != holds.contains(right);
        checks.record(&name("separates"), separates, claim);
        return Ok(());
    }
    let certificate = claim.get("certificate").and_then(Datum::as_list);
    checks.record(&name("witnessed"), certificate.is_some(), claim);
    let Some(certificate) = certificate else {
        return Ok(());
    };
    let relation = system.relation(certificate);
    let bisimilar = relation.is_some_and(|relation| {
        relation.contains(&(left, right)) && system.is_bisimulation(&relation)
    });
    checks.record(&name("bisimulation"), bisimilar, claim);
    Ok(())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let system = system(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let claims = reply
        .get("claims")
        .and_then(Datum::as_list)
        .filter(|claims| !claims.is_empty())
        .ok_or_else(|| Stop::Malformed("claims required".to_owned()))?;
    for (number, entry) in claims.iter().enumerate() {
        claim(&system, number, entry, checks).map_err(Stop::Malformed)?;
    }
    let detail = Datum::map([("claims", Datum::from(claims.len()))]);
    Ok(checks.judge("CLAIMS_WITNESSED", detail))
}

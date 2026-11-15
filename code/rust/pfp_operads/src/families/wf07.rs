//! WF7, typed refusal: answer `A x = b` exactly, or refuse with the code the rank test gives.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf07:v1
//!
//! The host decides answerability itself by the Rouche-Capelli test: there is exactly one
//! solution when `rank(A) = rank([A|b])` and that rank is the number of unknowns. A reply with
//! `refusal` must refuse a system that has no single solution, and with the right code. A reply
//! with `answer` must give the one solution. An answer to an unanswerable system is a bluff, and
//! a refusal of a solvable one is a false refusal; both are refused.
//!
//! Task: `A`, a nonempty list of equal rows, and `b`, one entry per row, all exact rationals.
//! Reply: `{"answer": [x1, ...]}` or `{"refusal": CODE}`. A reply with both is read as a refusal.

use crate::datum::Datum;
use crate::exact::{classify_linear, rationals, Rational, Solvability};

use super::{no_reply, refused, typed_refusal, Checks, Family, Run, Stop, Verdict};

pub const INCONSISTENT: &str = "UNRESOLVED_INCONSISTENT";
pub const UNDERDETERMINED: &str = "UNRESOLVED_UNDERDETERMINED";

pub const FAMILY: Family = Family {
    workflow: "WF7",
    name: "Typed refusal",
    host_check: "typed_refusal_rank_test",
    validate,
    walk,
};

type System = (Vec<Vec<Rational>>, Vec<Rational>);

fn system(task: &Datum) -> Result<System, String> {
    let rows = task
        .get("A")
        .and_then(Datum::as_list)
        .filter(|rows| !rows.is_empty())
        .ok_or("A must be a nonempty list of rows")?;
    let a: Vec<Vec<Rational>> = rows
        .iter()
        .map(rationals)
        .collect::<Option<_>>()
        .ok_or("every row of A must be a list of exact rationals")?;
    let b = task
        .get("b")
        .and_then(rationals)
        .ok_or("b must be a list of exact rationals")?;
    let width = a.first().map_or(0, Vec::len);
    if width == 0 || a.iter().any(|row| row.len() != width) || b.len() != a.len() {
        return Err("A must be rectangular, with a column, and match b".to_owned());
    }
    Ok((a, b))
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    system(task).map(|_| ())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    grade(run.task, reply, checks).map_err(Stop::Malformed)
}

/// The verdict on one reply to one system, with the predicates recorded in `checks`. Other
/// families grade a linear item with this.
pub fn grade(task: &Datum, reply: &Datum, checks: &mut Checks) -> Result<Verdict, String> {
    let (a, b) = system(task)?;
    let status = classify_linear(&a, &b);
    let witness = Datum::map([
        ("rank_A", Datum::from(status.rank_a)),
        ("rank_Ab", Datum::from(status.rank_ab)),
        ("n", Datum::from(a.first().map_or(0, Vec::len))),
        ("status", Datum::from(status.solvability.name())),
    ]);
    let detail = Datum::map([("witness", witness.clone())]);
    if !reply.is_map() {
        return Err("the reply must be an object".to_owned());
    }
    if let Some(code) = reply.get("refusal") {
        let expected = match status.solvability {
            Solvability::Inconsistent => INCONSISTENT,
            Solvability::Underdetermined => UNDERDETERMINED,
            Solvability::Unique(_) => {
                checks.record("no_false_refusal", false, &witness);
                return Ok(refused("FALSE_REFUSAL", detail));
            }
        };
        let matches = code.as_text() == Some(expected);
        return Ok(
            if checks.record("refusal_code_matches_rank_test", matches, &witness) {
                typed_refusal(expected, detail)
            } else {
                refused("WRONG_REFUSAL_CODE", detail)
            },
        );
    }
    let answer = match reply.get("answer") {
        Some(given) => rationals(given).ok_or("answer must be a list of exact rationals")?,
        None => Vec::new(),
    };
    let Solvability::Unique(solution) = status.solvability else {
        checks.record("no_bluff", false, &witness);
        return Ok(refused("BLUFF", detail));
    };
    checks.record(
        "answer_equals_unique_solution",
        answer == solution,
        &witness,
    );
    Ok(checks.judge(super::CERTIFIED_CODE, detail))
}

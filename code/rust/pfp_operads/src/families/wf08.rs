//! WF8, staged sealed packets: run `A x = b` as three stages, each stage's packet sealed into a
//! hash chain before the next stage reads it.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf08:v1
//!
//! The stages are `eliminate` (the reduced row echelon form of `[A | b]`), `solve` (the last
//! column of its first n rows, n the number of unknowns) and `residual` (`A x - b`). A stage's
//! reply is a packet `{stage, carry, payload, prev, seal}`, where `carry` holds the fenced
//! question of the statement exactly once, `prev` is the chain head before the packet and `seal`
//! is the head after it. The chain starts at the SHA-256 of the task in canonical form, and each
//! link is the SHA-256 of the head before it written in hex, followed by the packet's payload in
//! canonical form. Each stage's prompt after the first carries the packet before it.
//!
//! For every packet the host records five predicates, named `<stage>:<predicate>`, in this
//! order: `stage_named`, `fence_intact`, `chain_linked`, `seal_matches` and `recomputed` (the
//! payload, as exact rationals, is the stage recomputed from the task). The first one to fail
//! refuses the run as `STAGE_MISNAMED`, `FENCE_VIOLATED`, `CHAIN_BROKEN`, `SEAL_MISMATCH` or
//! `STAGE_RECOMPUTE_MISMATCH`, with the stage and the number of stages sealed so far. A stage
//! with no packet refuses the run as `STAGE_MISSING`. After the last stage the host records
//! `answer_is_unique_solution` and `final_residual_zero`, and certifies `SEALED_PIPELINE`
//! with the number of stages and the final chain head.
//!
//! Task: `statement`, text with its question between `<<Q>>` and `<</Q>>`; `A` and `b` as in
//! WF7, with exactly one solution.

use num_traits::Zero;

use crate::datum::Datum;
use crate::exact::{classify_linear, rational, rationals, rref, show, Rational, Solvability};

use super::fence::{locate, Fence, Marks};
use super::wf07;
use super::{refused, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF8",
    name: "Staged sealed packets",
    host_check: "stage_seal_chain_recompute",
    validate,
    walk,
};

/// The mark of the question the packets must carry.
pub const QUESTION: Marks = Marks {
    begin: "<<Q>>",
    end: "<</Q>>",
    name: "question",
};

/// The stages, in order.
pub const STAGES: [&str; 3] = ["eliminate", "solve", "residual"];

/// What a task asks for: the fence and what each stage's payload must be.
struct Pipeline {
    question: Fence,
    solution: Vec<Rational>,
    /// The payload each stage must have, in the form [`exact_form`] gives.
    expected: [Datum; 3],
}

fn listed(values: &[Rational]) -> Datum {
    Datum::List(
        values
            .iter()
            .map(|value| Datum::text(show(value)))
            .collect(),
    )
}

fn pipeline(task: &Datum) -> Result<Pipeline, String> {
    let (rows, right) = wf07::system(task)?;
    let Solvability::Unique(solution) = classify_linear(&rows, &right).solvability else {
        return Err("the staged instance needs a unique solution".to_owned());
    };
    let statement = task
        .get("statement")
        .and_then(Datum::as_text)
        .ok_or("statement must be text")?;
    let question = locate(statement, &QUESTION)?;
    let augmented: Vec<Vec<Rational>> = rows
        .iter()
        .zip(&right)
        .map(|(row, entry)| row.iter().cloned().chain([entry.clone()]).collect())
        .collect();
    let reduced = rref(&augmented).0;
    let solved: Vec<Rational> = reduced
        .iter()
        .take(solution.len())
        .filter_map(|row| row.last().cloned())
        .collect();
    let residual: Vec<Rational> = rows
        .iter()
        .zip(&right)
        .map(|(row, entry)| {
            let product: Rational = row.iter().zip(&solved).map(|(a, x)| a * x).sum();
            product - entry
        })
        .collect();
    Ok(Pipeline {
        question,
        solution,
        expected: [
            Datum::List(reduced.iter().map(|row| listed(row)).collect()),
            listed(&solved),
            listed(&residual),
        ],
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    pipeline(task).map(|_| ())
}

/// A payload with every number written as `p/q` in lowest terms, so two payloads that denote the
/// same rationals are equal. Nothing when the payload holds anything but lists, objects, integers
/// and exact rational text.
fn exact_form(value: &Datum) -> Option<Datum> {
    match value {
        Datum::List(items) => items
            .iter()
            .map(exact_form)
            .collect::<Option<Vec<_>>>()
            .map(Datum::List),
        Datum::Map(entries) => entries
            .iter()
            .map(|(key, inner)| exact_form(inner).map(|inner| (key.clone(), inner)))
            .collect::<Option<_>>()
            .map(Datum::Map),
        scalar => rational(scalar).map(|number| Datum::text(show(&number))),
    }
}

/// The chain head after `payload`, given the head before it.
fn link(before: &str, payload: &Datum) -> String {
    sha256_hex(&format!("{before}{}", payload.canonical()))
}

/// The chain head after these payloads, starting from the task.
fn head(task: &Datum, payloads: &[&Datum]) -> String {
    payloads
        .iter()
        .fold(sha256_hex(&task.canonical()), |before, payload| {
            link(&before, payload)
        })
}

/// A reply read as a packet: the five fields it must have.
struct Packet<'d> {
    whole: &'d Datum,
    stage: &'d Datum,
    carry: &'d Datum,
    payload: &'d Datum,
    prev: &'d Datum,
    seal: &'d Datum,
}

impl<'d> Packet<'d> {
    fn read(whole: &'d Datum) -> Option<Self> {
        Some(Packet {
            whole,
            stage: whole.get("stage")?,
            carry: whole.get("carry")?,
            payload: whole.get("payload")?,
            prev: whole.get("prev")?,
            seal: whole.get("seal")?,
        })
    }
}

/// Record the five predicates of one packet and return the code of the first that failed.
fn check(
    task: &Datum,
    line: &Pipeline,
    stage: (&str, &Datum),
    accepted: &[&Datum],
    packet: &Packet,
    checks: &mut Checks,
) -> Result<Option<&'static str>, Stop> {
    let (name, expected) = stage;
    let recomputed = exact_form(packet.payload)
        .ok_or_else(|| Stop::Malformed("payload must be exact rationals".to_owned()))?;
    let before = head(task, accepted);
    let after = link(&before, packet.payload);
    let rows = [
        (
            "stage_named",
            packet.stage.as_text() == Some(name),
            "STAGE_MISNAMED",
        ),
        (
            "fence_intact",
            packet
                .carry
                .as_text()
                .is_some_and(|carry| line.question.kept_by(carry)),
            "FENCE_VIOLATED",
        ),
        (
            "chain_linked",
            packet.prev.as_text() == Some(before.as_str()),
            "CHAIN_BROKEN",
        ),
        (
            "seal_matches",
            packet.seal.as_text() == Some(after.as_str()),
            "SEAL_MISMATCH",
        ),
        (
            "recomputed",
            recomputed == *expected,
            "STAGE_RECOMPUTE_MISMATCH",
        ),
    ];
    let mut first = None;
    for (predicate, held, code) in rows {
        if !checks.record(&format!("{name}:{predicate}"), held, packet.whole) {
            first = first.or(Some(code));
        }
    }
    Ok(first)
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let line = pipeline(run.task).map_err(Stop::Malformed)?;
    let mut accepted: Vec<&Datum> = Vec::new();
    let mut last: Option<&Datum> = None;
    for (name, expected) in STAGES.into_iter().zip(&line.expected) {
        let note = last.map_or(String::new(), |packet| {
            format!("\nPrevious sealed packet: {}", packet.canonical())
        });
        let prompt = format!("{}\nStage {name}.{note}", run.prompt());
        let Some(whole) = run.ask(&format!("stage:{name}"), prompt)? else {
            checks.record(&format!("{name}:packet_received"), false, &Datum::Null);
            return Ok(refused(
                "STAGE_MISSING",
                Datum::map([("stage", Datum::from(name))]),
            ));
        };
        let packet = Packet::read(whole)
            .ok_or_else(|| Stop::Malformed("packet fields missing".to_owned()))?;
        if let Some(code) = check(
            run.task,
            &line,
            (name, expected),
            &accepted,
            &packet,
            checks,
        )? {
            let detail = Datum::map([
                ("stage", Datum::from(name)),
                ("sealed_stages", Datum::from(accepted.len())),
            ]);
            return Ok(refused(code, detail));
        }
        accepted.push(packet.payload);
        last = Some(whole);
    }
    let solved = accepted.get(1).copied().and_then(rationals);
    checks.record(
        "answer_is_unique_solution",
        solved == Some(line.solution.clone()),
        &Datum::Null,
    );
    let residual = accepted.get(2).copied().and_then(rationals);
    let zero = residual.is_some_and(|entries| entries.iter().all(Zero::is_zero));
    checks.record("final_residual_zero", zero, &Datum::Null);
    let detail = Datum::map([
        ("stages", Datum::from(accepted.len())),
        ("head", Datum::text(head(run.task, &accepted))),
    ]);
    Ok(checks.judge("SEALED_PIPELINE", detail))
}

//! WF21, structural prompt rewriting: rewrite a prompt only outside its fences, then solve the
//! rewritten prompt.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf21:v1
//!
//! The statement has two fences, the question between `<<Q>>` and `<</Q>>` and the output
//! format between `<<OUT>>` and `<</OUT>>`. A rewrite is a list of rule applications
//! `{lhs, rhs, at}`: `lhs` (not empty) must stand in the statement at byte offset `at`. The host
//! records, in this order, and refuses the rewrite at the first to fail:
//!
//! * `matches_exact`: every `lhs` stands at its `at`. A negative `at`, or one that puts the
//!   match past the end, is no match. Refused as `NO_MATCH`.
//! * `match_injective`: sorted by `at`, no match starts before the one before it ends. Refused
//!   as `OVERLAPPING_MATCHES`.
//! * `edits_outside_fences`: no match shares a byte with either fence. Refused as
//!   `EDIT_INSIDE_FENCE`.
//! * `protected_bytes_unchanged`: after every `lhs` is replaced by its `rhs`, each fenced text
//!   occurs exactly once. Refused as `QUESTION_NOT_PRESERVED`, with the names of the fences
//!   that do not.
//! * `no_answer_key_leak`: the rewritten text carries no sealed value (see [`super::sealed`]),
//!   and the sealed `answer_key` does not occur in it as text. Refused as `ANSWER_KEY_LEAK`.
//!
//! The rewritten text is then put to the model as the stage `solve`. Its reply is
//! `{"answer": rational}`. The host records `answer_key_consistent` (the determinant of the
//! matrix equals the sealed key) and `answer_exact` (the answer equals the determinant), and
//! certifies `REWRITE_CERTIFIED` with the SHA-256 of the rewritten text.
//!
//! Task: `statement`, with both fences; `matrix`, a square list of rows of exact rationals.
//! Sealed: `answer_key`, an exact rational. A run whose sealed part has none is refused as
//! `MALFORMED_CANDIDATE` before anything is asked.
//! Reply to the first stage `rewrite`: `{"edits": [{"lhs", "rhs", "at"}, ...]}`.

use num_traits::{One, Zero};

use crate::datum::Datum;
use crate::exact::{rational, rationals, Rational};

use super::fence::{locate, Fence, Marks};
use super::sealed::Guard;
use super::{no_reply, refused, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF21",
    name: "Structural prompt rewriting",
    host_check: "fenced_rewrite_exact_judge",
    validate,
    walk,
};

/// The two fences of a statement, in the order the host names them.
pub const FENCES: [Marks; 2] = [
    Marks {
        begin: "<<Q>>",
        end: "<</Q>>",
        name: "question",
    },
    Marks {
        begin: "<<OUT>>",
        end: "<</OUT>>",
        name: "output",
    },
];

/// What a task asks for.
struct Rewrite {
    statement: String,
    fences: Vec<Fence>,
    determinant: Rational,
}

/// The sealed answer key.
struct Key {
    value: Rational,
    /// The key as text, as the rewritten text must not carry it.
    text: String,
}

/// The determinant of a square matrix, by Gaussian elimination over the rationals.
fn det(matrix: &[Vec<Rational>]) -> Rational {
    let mut rows = matrix.to_vec();
    let mut out = Rational::one();
    for column in 0..rows.len() {
        let Some(pivot) = (column..rows.len()).find(|&row| !rows[row][column].is_zero()) else {
            return Rational::zero();
        };
        if pivot != column {
            rows.swap(column, pivot);
            out = -out;
        }
        let top = rows[column].clone();
        out *= &top[column];
        for lower in &mut rows[column + 1..] {
            let factor = &lower[column] / &top[column];
            for (entry, above) in lower.iter_mut().zip(&top) {
                *entry -= &factor * above;
            }
        }
    }
    out
}

fn square(task: &Datum) -> Result<Vec<Vec<Rational>>, String> {
    let rows: Option<Vec<Vec<Rational>>> = task
        .get("matrix")
        .and_then(Datum::as_list)
        .and_then(|rows| rows.iter().map(rationals).collect());
    rows.filter(|rows| rows.iter().all(|row| row.len() == rows.len()))
        .ok_or_else(|| "matrix must be square, with exact rationals".to_owned())
}

fn rewrite(task: &Datum) -> Result<Rewrite, String> {
    let statement = task
        .get("statement")
        .and_then(Datum::as_text)
        .ok_or("statement must be text")?;
    let fences = FENCES
        .iter()
        .map(|marks| locate(statement, marks))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Rewrite {
        statement: statement.to_owned(),
        fences,
        determinant: det(&square(task)?),
    })
}

fn answer_key(sealed: &Datum) -> Result<Key, String> {
    let given = sealed.get("answer_key").ok_or("answer_key required")?;
    Ok(Key {
        value: rational(given).ok_or("answer_key must be an exact rational")?,
        text: match given {
            Datum::Text(text) => text.clone(),
            other => other.canonical(),
        },
    })
}

/// The task is read here and the sealed part in the walk, so that a run with no sealed part
/// still starts: the host holds it, and the caller who asks does not.
fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    rewrite(task).map(|_| ())
}

/// One rule application: the bytes `lhs` at `start`, to be replaced by `rhs`.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct Edit {
    start: usize,
    end: usize,
    lhs: Vec<u8>,
    rhs: Vec<u8>,
}

fn malformed(reason: &str) -> Stop {
    Stop::Malformed(reason.to_owned())
}

/// One edit as the reply gives it. A position that is not a byte offset (negative, or beyond
/// what a machine counts) is kept as no edit at all, so that it never matches.
fn edit(item: &Datum) -> Result<Option<Edit>, Stop> {
    let lhs = item
        .get("lhs")
        .and_then(Datum::as_text)
        .filter(|lhs| !lhs.is_empty());
    let rhs = item.get("rhs").and_then(Datum::as_text);
    let (Some(lhs), Some(rhs)) = (lhs, rhs) else {
        return Err(malformed("edits are {lhs, rhs, at}"));
    };
    let at = item
        .get("at")
        .and_then(Datum::as_int)
        .ok_or_else(|| malformed("at must be an exact int"))?;
    Ok(usize::try_from(at).ok().and_then(|start| {
        Some(Edit {
            start,
            end: start.checked_add(lhs.len())?,
            lhs: lhs.as_bytes().to_vec(),
            rhs: rhs.as_bytes().to_vec(),
        })
    }))
}

/// The edits of a reply, sorted, and whether every one is a byte offset.
fn edits(reply: &Datum) -> Result<(Vec<Edit>, bool), Stop> {
    let items = reply
        .get("edits")
        .and_then(Datum::as_list)
        .ok_or_else(|| malformed("edits list required"))?;
    let read: Vec<Option<Edit>> = items.iter().map(edit).collect::<Result<_, _>>()?;
    let counted = read.iter().all(Option::is_some);
    let mut kept: Vec<Edit> = read.into_iter().flatten().collect();
    kept.sort();
    Ok((kept, counted))
}

/// The statement with every edit applied.
fn apply(statement: &str, edits: &[Edit]) -> String {
    let data = statement.as_bytes();
    let mut out = Vec::new();
    let mut from = 0;
    for edit in edits {
        out.extend_from_slice(data.get(from..edit.start).unwrap_or_default());
        out.extend_from_slice(&edit.rhs);
        from = edit.end;
    }
    out.extend_from_slice(data.get(from..).unwrap_or_default());
    String::from_utf8_lossy(&out).into_owned()
}

fn pairs(edits: &[Edit]) -> Datum {
    Datum::List(
        edits
            .iter()
            .map(|edit| Datum::from(vec![edit.start, edit.end]))
            .collect(),
    )
}

/// How a rewrite ends: as the text to put to the model, or as the verdict that refuses it.
enum Rewritten {
    Text(String),
    Refused(Verdict),
}

/// Record the predicates of a rewrite, up to the first to fail.
fn rewritten(
    run: &Run,
    plan: &Rewrite,
    key: &Key,
    reply: &Datum,
    checks: &mut Checks,
) -> Result<Rewritten, Stop> {
    let (edits, counted) = edits(reply)?;
    let data = plan.statement.as_bytes();
    let exact = counted
        && edits
            .iter()
            .all(|edit| data.get(edit.start..edit.end) == Some(edit.lhs.as_slice()));
    if !checks.record("matches_exact", exact, &pairs(&edits)) {
        return Ok(Rewritten::Refused(refused("NO_MATCH", Datum::map([]))));
    }
    let disjoint = edits.windows(2).all(|both| both[0].end <= both[1].start);
    if !checks.record("match_injective", disjoint, &pairs(&edits)) {
        return Ok(Rewritten::Refused(refused(
            "OVERLAPPING_MATCHES",
            Datum::map([]),
        )));
    }
    let outside = !edits.iter().any(|edit| {
        plan.fences
            .iter()
            .any(|fence| fence.touches(edit.start, edit.end))
    });
    if !checks.record("edits_outside_fences", outside, &pairs(&edits)) {
        return Ok(Rewritten::Refused(refused(
            "EDIT_INSIDE_FENCE",
            Datum::map([]),
        )));
    }
    let text = apply(&plan.statement, &edits);
    let lost: Vec<&str> = plan
        .fences
        .iter()
        .filter(|fence| !fence.kept_by(&text))
        .map(|fence| fence.name)
        .collect();
    if !checks.record(
        "protected_bytes_unchanged",
        lost.is_empty(),
        &Datum::text(&text),
    ) {
        let detail = Datum::map([("violations", Datum::from(lost))]);
        return Ok(Rewritten::Refused(refused(
            "QUESTION_NOT_PRESERVED",
            detail,
        )));
    }
    let leaked = Guard::new(run.sealed).leaks(&text) || text.contains(&key.text);
    if !checks.record("no_answer_key_leak", !leaked, &Datum::Null) {
        return Ok(Rewritten::Refused(refused(
            "ANSWER_KEY_LEAK",
            Datum::map([]),
        )));
    }
    Ok(Rewritten::Text(text))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let plan = rewrite(run.task).map_err(Stop::Malformed)?;
    let key = answer_key(run.sealed).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("rewrite", run.prompt())? else {
        return Ok(no_reply());
    };
    let text = match rewritten(run, &plan, &key, reply, checks)? {
        Rewritten::Text(text) => text,
        Rewritten::Refused(verdict) => return Ok(verdict),
    };
    let Some(answer) = run.ask("solve", text.clone())? else {
        return Ok(no_reply());
    };
    let value = answer
        .get("answer")
        .and_then(rational)
        .ok_or_else(|| malformed("answer must be an exact rational"))?;
    checks.record(
        "answer_key_consistent",
        plan.determinant == key.value,
        &Datum::Null,
    );
    checks.record("answer_exact", value == plan.determinant, answer);
    let detail = Datum::map([("rewritten_sha256", Datum::text(sha256_hex(&text)))]);
    Ok(checks.judge("REWRITE_CERTIFIED", detail))
}

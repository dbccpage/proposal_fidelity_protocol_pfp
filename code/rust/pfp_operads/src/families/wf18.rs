//! WF18, dossier replay campaign: replay a frozen dossier with no model call, and refuse it if
//! any stored byte drifted or any grade fails to reproduce.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf18:v1
//!
//! The task is a `dossier`: a `grader`, `source_pins` (the digest of each grader's source, by
//! name) and `cells`, a nonempty list of cells with different `cell_id`s. A cell stores its
//! `input` (a weighted digraph, see [`super::duality`]), the `raw_reply` text and its
//! `raw_reply_sha256`, the digest of that text, `input_sha256`, the digest of the input's
//! canonical form, and the `grade` the reply earned. The only grader is `cycle_duality`, and its
//! source is [`super::duality::pin`].
//!
//! The host asks the model nothing. It regrades every stored reply and records, in this order:
//!
//! * `source_pin_matches`: the dossier pins the grader's source as it is now.
//! * `stored_bytes_match_digests`: every cell's reply and input hash to the digests stored with
//!   them. The detail's `drift` names the cells that do not, as `cell_id:raw_reply` or
//!   `cell_id:input`.
//! * `every_grade_reproduces`: every stored grade is the one the grader gives the stored reply.
//!   The detail's `mismatched` lists the cells that do not, sorted.
//! * `zero_model_calls`: no reply was asked for.
//!
//! A pin that does not match refuses the run as `SOURCE_PIN_DRIFT`, and after that a drifted
//! digest as `STORED_BYTES_DRIFTED` with the cells that drifted. All held, the replay is
//! certified as `REPLAY_REPRODUCED` with the number of `cells` and the `mismatched` (none).

use std::collections::BTreeSet;

use crate::datum::Datum;

use super::duality::{self, Item};
use super::{refused, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF18",
    name: "Dossier replay campaign",
    host_check: "dossier_replay_reproduces_grades",
    validate,
    walk,
};

/// The one grader a dossier may name.
pub const GRADER: &str = "cycle_duality";

/// One stored cell.
struct Cell<'t> {
    id: &'t str,
    input: &'t Datum,
    item: Item,
    raw: &'t str,
    raw_sha256: Option<&'t str>,
    input_sha256: Option<&'t str>,
    grade: &'t str,
}

fn text<'t>(cell: &'t Datum, key: &str) -> Result<&'t str, String> {
    cell.get(key)
        .and_then(Datum::as_text)
        .ok_or_else(|| format!("a cell needs {key} as text"))
}

fn cell(datum: &Datum) -> Result<Cell<'_>, String> {
    let input = datum.get("input").ok_or("a cell needs its input")?;
    Ok(Cell {
        id: text(datum, "cell_id")?,
        input,
        item: Item::read(input)?,
        raw: text(datum, "raw_reply")?,
        raw_sha256: datum.get("raw_reply_sha256").and_then(Datum::as_text),
        input_sha256: datum.get("input_sha256").and_then(Datum::as_text),
        grade: text(datum, "grade")?,
    })
}

/// What a task fixes.
struct Dossier<'t> {
    pins: &'t Datum,
    cells: Vec<Cell<'t>>,
}

fn dossier(task: &Datum) -> Result<Dossier<'_>, String> {
    let dossier = task
        .get("dossier")
        .filter(|dossier| dossier.is_map())
        .ok_or("dossier must be an object")?;
    let pins = dossier
        .get("source_pins")
        .filter(|pins| pins.is_map())
        .ok_or("source_pins must be an object")?;
    if dossier.get("grader").and_then(Datum::as_text) != Some(GRADER) {
        return Err(format!("grader must be {GRADER}"));
    }
    let listed = dossier
        .get("cells")
        .and_then(Datum::as_list)
        .filter(|listed| !listed.is_empty())
        .ok_or("cells must be a nonempty list")?;
    let cells = listed.iter().map(cell).collect::<Result<Vec<_>, _>>()?;
    let ids: BTreeSet<&str> = cells.iter().map(|cell| cell.id).collect();
    if ids.len() != cells.len() {
        return Err("each cell needs its own cell_id".to_owned());
    }
    Ok(Dossier { pins, cells })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    dossier(task).map(|_| ())
}

fn names(listed: &[String]) -> Datum {
    Datum::List(listed.iter().cloned().map(Datum::text).collect())
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let dossier = dossier(run.task).map_err(Stop::Malformed)?;
    let pinned = dossier.pins.get(GRADER).and_then(Datum::as_text) == Some(duality::pin().as_str());
    checks.record("source_pin_matches", pinned, &Datum::text(GRADER));
    let mut drift = Vec::new();
    let mut mismatched = Vec::new();
    for cell in &dossier.cells {
        if cell.raw_sha256 != Some(sha256_hex(cell.raw).as_str()) {
            drift.push(format!("{}:raw_reply", cell.id));
        }
        if cell.input_sha256 != Some(sha256_hex(&cell.input.canonical()).as_str()) {
            drift.push(format!("{}:input", cell.id));
        }
        if duality::grade(&cell.item, cell.raw).name() != cell.grade {
            mismatched.push(cell.id.to_owned());
        }
    }
    mismatched.sort();
    checks.record(
        "stored_bytes_match_digests",
        drift.is_empty(),
        &names(&drift),
    );
    checks.record(
        "every_grade_reproduces",
        mismatched.is_empty(),
        &names(&mismatched),
    );
    checks.record("zero_model_calls", true, &Datum::from(0_usize));
    if !pinned {
        return Ok(refused("SOURCE_PIN_DRIFT", Datum::map([])));
    }
    if !drift.is_empty() {
        return Ok(refused(
            "STORED_BYTES_DRIFTED",
            Datum::map([("drift", names(&drift))]),
        ));
    }
    Ok(checks.judge(
        "REPLAY_REPRODUCED",
        Datum::map([
            ("cells", Datum::from(dossier.cells.len())),
            ("mismatched", names(&mismatched)),
        ]),
    ))
}

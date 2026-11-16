//! WF16, substrate crosswalk: carry one finite task from a graph to an incidence matrix and
//! require the same host verdict on both sides.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf16:v1
//!
//! Source: a rational value `c` on every edge of a graph, exact when it is a coboundary.
//! Target: a matrix `D` and a vector `y`, exact when `rank D = rank [D|y]`. A crosswalk sends
//! each vertex to a column and each edge to a row with a sign. The host records, in this order,
//!
//! * `verdicts_identical`: the source and the target are both exact or both not, and then for
//!   crosswalk `k`,
//! * `crosswalk<k>:bijective`: the vertices fill the columns `0..n-1`, the edges fill the rows
//!   of `D`, and every sign is 1 or -1,
//! * `crosswalk<k>:relations_preserved`: the row of each edge is its sign times the incidence
//!   row of that edge, -1 at the column of its tail and 1 at the column of its head, and
//! * `crosswalk<k>:data_transported`: `y` at the row of each edge is its sign times `c` there.
//!
//! A crosswalk that is not bijective is not checked further. The run is certified as
//! `CROSSWALK_PRESERVED` when every predicate passed, with the edges each crosswalk flips and
//! the vertices on which later crosswalks differ from the first.
//!
//! Task: `edges`, a list of pairs of text; `c`, one exact rational per edge; `D`, a list of
//! rows of exact rationals of one length; `y`, one exact rational per row.
//! Reply: `{"crosswalks": [{"vertex_col": {vertex: column}, "edge_row": {index: [row, sign]}}]}`.

use std::collections::BTreeSet;

use num_bigint::BigInt;
use num_traits::{One, Zero};

use crate::datum::Datum;
use crate::exact::{rank, rationals, Rational};

use super::labelled::{self, Labelled};
use super::{no_reply, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF16",
    name: "Substrate crosswalk",
    host_check: "incidence_rank_crosswalk",
    validate,
    walk,
};

struct Substrates {
    source: Labelled,
    /// `c`: the value on each edge.
    values: Vec<Rational>,
    /// `D`: the target matrix.
    rows: Vec<Vec<Rational>>,
    /// `y`: the target vector.
    data: Vec<Rational>,
}

fn substrates(task: &Datum) -> Result<Substrates, String> {
    let source = task
        .get("edges")
        .and_then(labelled::read)
        .ok_or("edges must be a list of pairs of text")?;
    let values = task
        .get("c")
        .and_then(rationals)
        .filter(|values| values.len() == source.graph.edges().len())
        .ok_or("c must be one exact rational per edge")?;
    let rows: Vec<Vec<Rational>> = task
        .get("D")
        .and_then(Datum::as_list)
        .and_then(|rows| rows.iter().map(rationals).collect())
        .ok_or("D must be a list of rows of exact rationals")?;
    let width = rows.first().map_or(0, Vec::len);
    if rows.iter().any(|row| row.len() != width) {
        return Err("the rows of D must have one length".to_owned());
    }
    let data = task
        .get("y")
        .and_then(rationals)
        .filter(|data| data.len() == rows.len())
        .ok_or("y must be one exact rational per row of D")?;
    Ok(Substrates {
        source,
        values,
        rows,
        data,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    substrates(task).map(|_| ())
}

/// A crosswalk as written: a column for each vertex, and a row and a sign for each edge.
struct Written {
    columns: Vec<BigInt>,
    rows: Vec<(BigInt, BigInt)>,
}

/// A bijective crosswalk: columns and rows are positions, and a sign is 1 or -1.
struct Crosswalk {
    columns: Vec<usize>,
    rows: Vec<(usize, i8)>,
}

fn written(task: &Substrates, listed: &Datum) -> Result<Written, String> {
    let (Some(columns), Some(rows)) = (
        listed.get("vertex_col").filter(|map| map.is_map()),
        listed.get("edge_row").filter(|map| map.is_map()),
    ) else {
        return Err("vertex_col and edge_row maps required".to_owned());
    };
    let columns = task
        .source
        .by_name(columns, |column| column.as_int().cloned())
        .ok_or("column must be an exact int")?;
    let entries: Vec<(&Datum, &Datum)> = (0..task.values.len())
        .map(|edge| match rows.get(&edge.to_string())?.as_list()? {
            [row, sign] => Some((row, sign)),
            _ => None,
        })
        .collect::<Option<_>>()
        .ok_or("edge_row entries are [row, sign]")?;
    let mut rows = Vec::with_capacity(entries.len());
    for (row, sign) in entries {
        let row = row.as_int().ok_or("row must be an exact int")?;
        let sign = sign.as_int().ok_or("sign must be an exact int")?;
        rows.push((row.clone(), sign.clone()));
    }
    Ok(Written { columns, rows })
}

/// The positions a list of integers gives, when they are `0..count-1` in some order.
fn filling<'i>(indices: impl Iterator<Item = &'i BigInt>, count: usize) -> Option<Vec<usize>> {
    let places: Vec<usize> = indices
        .map(|index| usize::try_from(index).ok().filter(|&place| place < count))
        .collect::<Option<_>>()?;
    let distinct: BTreeSet<&usize> = places.iter().collect();
    (places.len() == count && distinct.len() == count).then_some(places)
}

fn sign(written: &BigInt) -> Option<i8> {
    match written {
        sign if sign.is_one() => Some(1),
        sign if *sign == BigInt::from(-1) => Some(-1),
        _ => None,
    }
}

fn bijective(task: &Substrates, written: &Written) -> Option<Crosswalk> {
    let columns = filling(written.columns.iter(), task.source.names().len())?;
    let rows = filling(written.rows.iter().map(|(row, _)| row), task.rows.len())?;
    let signs: Vec<i8> = written
        .rows
        .iter()
        .map(|(_, written)| sign(written))
        .collect::<Option<_>>()?;
    Some(Crosswalk {
        columns,
        rows: rows.into_iter().zip(signs).collect(),
    })
}

impl Substrates {
    /// Whether the row of each edge is its sign times the incidence row of that edge.
    fn relations(&self, crosswalk: &Crosswalk) -> bool {
        let width = self.source.names().len();
        let edges = self.source.graph.edges().iter().zip(&crosswalk.rows);
        edges.into_iter().all(|(&(tail, head), &(row, sign))| {
            let at = |vertex: usize| crosswalk.columns.get(vertex).copied();
            let image = (0..width).map(|column| {
                let entry =
                    i64::from(at(head) == Some(column)) - i64::from(at(tail) == Some(column));
                Rational::from_integer(BigInt::from(i64::from(sign) * entry))
            });
            self.rows
                .get(row)
                .is_some_and(|target| image.eq(target.iter().cloned()))
        })
    }

    /// Whether `y` at the row of each edge is its sign times `c` on that edge.
    fn transported(&self, crosswalk: &Crosswalk) -> bool {
        let edges = self.values.iter().zip(&crosswalk.rows);
        edges.into_iter().all(|(value, &(row, sign))| {
            let carried = value * Rational::from_integer(BigInt::from(sign));
            self.data.get(row) == Some(&carried)
        })
    }
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let task = substrates(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    let source = task.source.graph.defect(&task.values).is_zero();
    let augmented: Vec<Vec<Rational>> = task
        .rows
        .iter()
        .zip(&task.data)
        .map(|(row, entry)| row.iter().cloned().chain([entry.clone()]).collect())
        .collect();
    let target = rank(&task.rows) == rank(&augmented);
    let both = Datum::List(vec![Datum::Bool(source), Datum::Bool(target)]);
    checks.record("verdicts_identical", source == target, &both);
    let listed = reply
        .get("crosswalks")
        .and_then(Datum::as_list)
        .filter(|listed| !listed.is_empty())
        .ok_or_else(|| Stop::Malformed("crosswalks required".to_owned()))?;
    let mut kept: Vec<Crosswalk> = Vec::new();
    for (number, entry) in listed.iter().enumerate() {
        let written = written(&task, entry).map_err(Stop::Malformed)?;
        let found = bijective(&task, &written);
        let name = |predicate: &str| format!("crosswalk{number}:{predicate}");
        checks.record(&name("bijective"), found.is_some(), entry);
        let Some(crosswalk) = found else {
            continue;
        };
        checks.record(
            &name("relations_preserved"),
            task.relations(&crosswalk),
            entry,
        );
        checks.record(
            &name("data_transported"),
            task.transported(&crosswalk),
            entry,
        );
        kept.push(crosswalk);
    }
    let choices = kept.iter().map(|crosswalk| {
        let flipped = crosswalk.rows.iter().enumerate();
        let flipped: Vec<usize> = flipped
            .filter(|(_, &(_, sign))| sign == -1)
            .map(|(edge, _)| edge)
            .collect();
        Datum::map([("flipped_edges", Datum::from(flipped))])
    });
    let differ = kept.iter().skip(1).map(|later| {
        let first = kept
            .first()
            .map_or(&[][..], |first| first.columns.as_slice());
        let names = task
            .source
            .names()
            .iter()
            .zip(first.iter().zip(&later.columns));
        let moved: Vec<&str> = names
            .filter(|(_, (first, later))| first != later)
            .map(|(name, _)| name.as_str())
            .collect();
        Datum::from(moved)
    });
    let detail = Datum::map([
        (
            "verdict",
            Datum::from(if source { "exact" } else { "not_exact" }),
        ),
        ("choices", Datum::List(choices.collect())),
        ("differ_on_vertices", Datum::List(differ.collect())),
    ]);
    Ok(checks.judge("CROSSWALK_PRESERVED", detail))
}

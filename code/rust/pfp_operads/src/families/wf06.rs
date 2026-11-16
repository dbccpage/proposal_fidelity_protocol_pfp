//! WF6, dialect sweep: pose each linear system in several dialects that keep its answer, and
//! grade every reply with the one WF7 check.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf06:v1
//!
//! An item is a system `A x = b`. A dialect rewrites it: row `i` of the rewritten system is
//! `row_scale[i]` times row `row_perm[i]` of the item, with its columns taken in the order
//! `col_perm`, and `b_shift[i]` added to its right-hand side. A dialect keeps the query when
//! the rewritten system has the same answerability and, read back through `col_perm`, the same
//! solution.
//!
//! The host first records `dialects_preserve_query` over every item and dialect, and refuses
//! the run as `DIALECT_CHANGES_QUERY` before anything is asked when one does not. It then asks
//! one question per item and dialect, the statement and the rewritten system, under the stage
//! `<item>:<dialect>`, and grades each reply as WF7 grades it: accepted when it is the one
//! solution, or the refusal code the rank test gives. `every_capsule_graded_once` fails, and
//! the run is refused as `INCOMPLETE_SWEEP`, when a question has no reply.
//!
//! The run is certified as `SWEEP_GRADED` with the share of items accepted in each dialect,
//! the table of grades, and every item whose grade in a later dialect differs from its grade in
//! the first. A sweep is certified whatever the grades are: the verdict says the sweep was run
//! and graded, not that the replies were right.
//!
//! Task: `statement`, text; `items`, each `{"id": text, "A", "b"}` as in WF7; `dialects`, each
//! `{"name": text}` with optional `row_perm`, `col_perm`, `row_scale` and `b_shift`. Item ids
//! are distinct, dialect names are distinct, every item has the shape the dialects are written
//! for, and there are at most 64 questions.

use std::collections::BTreeSet;

use num_bigint::BigInt;
use num_traits::{One, Zero};

use crate::datum::Datum;
use crate::exact::{classify_linear, rationals, Rational, Solvability};

use super::wf07;
use super::{refused, Checks, Family, Run, Stop, Verdict, CERTIFIED, TYPED_REFUSAL};

/// The most questions a sweep may ask: items times dialects.
pub const MAX_CAPSULES: usize = 64;

pub const FAMILY: Family = Family {
    workflow: "WF6",
    name: "Dialect sweep",
    host_check: "dialect_query_preservation_sweep",
    validate,
    walk,
};

struct Item<'t> {
    id: &'t str,
    rows: Vec<Vec<Rational>>,
    right: Vec<Rational>,
}

struct Dialect<'t> {
    name: &'t str,
    row_perm: Option<Vec<usize>>,
    col_perm: Option<Vec<usize>>,
    row_scale: Option<Vec<Rational>>,
    b_shift: Option<Vec<Rational>>,
}

struct Sweep<'t> {
    statement: &'t str,
    items: Vec<Item<'t>>,
    dialects: Vec<Dialect<'t>>,
}

/// One item in one dialect.
struct Capsule {
    rows: Vec<Vec<Rational>>,
    right: Vec<Rational>,
    /// Whether the dialect keeps the item's query.
    kept: bool,
}

/// A list under `key` that is `0..n-1` in some order, when the key is there.
fn permutation(dialect: &Datum, key: &str) -> Result<Option<Vec<usize>>, String> {
    let Some(listed) = dialect.get(key) else {
        return Ok(None);
    };
    let places: Option<Vec<usize>> = listed
        .as_list()
        .and_then(|places| places.iter().map(Datum::as_count).collect());
    let distinct = |places: &Vec<usize>| {
        let seen: BTreeSet<&usize> = places.iter().collect();
        seen.len() == places.len() && places.iter().all(|&place| place < places.len())
    };
    places
        .filter(distinct)
        .map(Some)
        .ok_or(format!("{key} must be a permutation"))
}

fn scalars(dialect: &Datum, key: &str) -> Result<Option<Vec<Rational>>, String> {
    let Some(listed) = dialect.get(key) else {
        return Ok(None);
    };
    rationals(listed)
        .map(Some)
        .ok_or(format!("{key} must be a list of exact rationals"))
}

fn dialect(listed: &Datum) -> Result<Dialect<'_>, String> {
    Ok(Dialect {
        name: listed
            .get("name")
            .and_then(Datum::as_text)
            .ok_or("every dialect needs a text name")?,
        row_perm: permutation(listed, "row_perm")?,
        col_perm: permutation(listed, "col_perm")?,
        row_scale: scalars(listed, "row_scale")?,
        b_shift: scalars(listed, "b_shift")?,
    })
}

fn item(listed: &Datum) -> Result<Item<'_>, String> {
    let id = listed
        .get("id")
        .and_then(Datum::as_text)
        .ok_or("every item needs a text id")?;
    let (rows, right) = wf07::system(listed)?;
    Ok(Item { id, rows, right })
}

fn distinct<'t>(names: impl Iterator<Item = &'t str>) -> bool {
    let mut seen = BTreeSet::new();
    names.into_iter().all(|name| seen.insert(name))
}

/// Where a permutation sends a place. With no permutation, a place stays where it is.
fn place(perm: &Option<Vec<usize>>, at: usize) -> usize {
    let listed = perm.as_ref().and_then(|perm| perm.get(at));
    listed.copied().unwrap_or(at)
}

/// The entry of an optional list at a place, or the default when there is no list.
fn entry(listed: &Option<Vec<Rational>>, at: usize, default: Rational) -> Rational {
    let listed = listed.as_ref().and_then(|listed| listed.get(at));
    listed.cloned().unwrap_or(default)
}

impl Dialect<'_> {
    /// Whether this dialect is written for systems of this many rows and columns.
    fn fits(&self, rows: usize, columns: usize) -> bool {
        let sized = |listed: Option<usize>, size: usize| listed.is_none_or(|length| length == size);
        sized(self.row_perm.as_ref().map(Vec::len), rows)
            && sized(self.col_perm.as_ref().map(Vec::len), columns)
            && sized(self.row_scale.as_ref().map(Vec::len), rows)
            && sized(self.b_shift.as_ref().map(Vec::len), rows)
    }

    /// Row `at` of the item as this dialect writes it, and its right-hand side.
    fn row(&self, item: &Item, at: usize) -> (Vec<Rational>, Rational) {
        let scale = entry(&self.row_scale, at, Rational::one());
        let shift = entry(&self.b_shift, at, Rational::zero());
        let source = place(&self.row_perm, at);
        let row = item.rows.get(source).map_or(&[][..], Vec::as_slice);
        let taken = (0..row.len()).filter_map(|column| row.get(place(&self.col_perm, column)));
        let bound = item.right.get(source).cloned().unwrap_or_default();
        (
            taken.map(|entry| &scale * entry).collect(),
            scale * bound + shift,
        )
    }

    /// A solution of the rewritten system with its entries back in the item's column order.
    fn decoded(&self, solution: Vec<Rational>) -> Vec<Rational> {
        let mut decoded = vec![Rational::zero(); solution.len()];
        for (column, value) in solution.into_iter().enumerate() {
            if let Some(slot) = decoded.get_mut(place(&self.col_perm, column)) {
                *slot = value;
            }
        }
        decoded
    }

    /// The item as this dialect poses it.
    fn pose(&self, item: &Item) -> Capsule {
        let (rows, right): (Vec<_>, Vec<_>) =
            (0..item.rows.len()).map(|at| self.row(item, at)).unzip();
        let seed = classify_linear(&item.rows, &item.right).solvability;
        let posed = match classify_linear(&rows, &right).solvability {
            Solvability::Unique(solution) => Solvability::Unique(self.decoded(solution)),
            other => other,
        };
        Capsule {
            kept: posed == seed,
            rows,
            right,
        }
    }
}

fn sweep(task: &Datum) -> Result<Sweep<'_>, String> {
    let statement = task
        .get("statement")
        .and_then(Datum::as_text)
        .ok_or("statement must be text")?;
    let listed = |key: &str| {
        let list = task.get(key).and_then(Datum::as_list);
        list.filter(|list| !list.is_empty())
            .ok_or(format!("{key} required"))
    };
    let items: Vec<Item> = listed("items")?
        .iter()
        .map(item)
        .collect::<Result<_, _>>()?;
    let dialects: Vec<Dialect> = listed("dialects")?
        .iter()
        .map(dialect)
        .collect::<Result<_, _>>()?;
    if !distinct(items.iter().map(|item| item.id)) {
        return Err("item ids must be distinct".to_owned());
    }
    if !distinct(dialects.iter().map(|dialect| dialect.name)) {
        return Err("dialect names must be distinct".to_owned());
    }
    if items.len().saturating_mul(dialects.len()) > MAX_CAPSULES {
        return Err(format!("at most {MAX_CAPSULES} questions"));
    }
    let fit = items.iter().all(|item| {
        let columns = item.rows.first().map_or(0, Vec::len);
        let fits = |dialect: &Dialect| dialect.fits(item.rows.len(), columns);
        dialects.iter().all(fits)
    });
    if !fit {
        return Err("every dialect must fit the rows and columns of every item".to_owned());
    }
    Ok(Sweep {
        statement,
        items,
        dialects,
    })
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    sweep(task).map(|_| ())
}

/// A rational as a prompt and a verdict write it: an integer, or `p/q` in lowest terms.
fn plain(value: &Rational) -> Datum {
    if value.is_integer() {
        Datum::Int(value.numer().clone())
    } else {
        Datum::text(format!("{}/{}", value.numer(), value.denom()))
    }
}

/// A pair of an item id and a dialect name.
fn pair(item: &str, dialect: &str) -> Datum {
    Datum::List(vec![Datum::from(item), Datum::from(dialect)])
}

/// Whether WF7 accepts a reply to a posed system.
fn accepted(system: &Datum, reply: &Datum) -> bool {
    let graded = wf07::grade(system, reply, &mut Checks::default());
    graded.is_ok_and(|verdict| [CERTIFIED, TYPED_REFUSAL].contains(&verdict.verdict))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let sweep = sweep(run.task).map_err(Stop::Malformed)?;
    let posed = |item: &Item| -> Vec<Capsule> {
        let dialects = sweep.dialects.iter();
        dialects.map(|dialect| dialect.pose(item)).collect()
    };
    let capsules: Vec<Vec<Capsule>> = sweep.items.iter().map(posed).collect();
    let cells = || {
        let rows = sweep.items.iter().zip(&capsules);
        rows.flat_map(|(item, row)| {
            let cells = sweep.dialects.iter().zip(row);
            cells.map(move |(dialect, capsule)| (item.id, dialect.name, capsule))
        })
    };
    let broken: Vec<Datum> = cells()
        .filter(|(_, _, capsule)| !capsule.kept)
        .map(|(item, dialect, _)| pair(item, dialect))
        .collect();
    let broken = Datum::List(broken);
    if !checks.record(
        "dialects_preserve_query",
        broken == Datum::List(Vec::new()),
        &broken,
    ) {
        return Ok(refused(
            "DIALECT_CHANGES_QUERY",
            Datum::map([("broken", broken)]),
        ));
    }
    let mut grades: Vec<(&str, &str, Option<bool>)> = Vec::new();
    for (item, dialect, capsule) in cells() {
        let matrix = capsule.rows.iter();
        let matrix = matrix.map(|row| Datum::List(row.iter().map(plain).collect()));
        let system = Datum::map([
            ("A", Datum::List(matrix.collect())),
            ("b", Datum::List(capsule.right.iter().map(plain).collect())),
        ]);
        let prompt = format!("{}\n{}", sweep.statement, system.canonical());
        let reply = run.ask(&format!("{item}:{dialect}"), prompt)?;
        grades.push((item, dialect, reply.map(|reply| accepted(&system, reply))));
    }
    let missing = grades.iter().filter(|(_, _, grade)| grade.is_none());
    let missing = Datum::List(
        missing
            .map(|(item, dialect, _)| pair(item, dialect))
            .collect(),
    );
    if !checks.record(
        "every_capsule_graded_once",
        missing == Datum::List(Vec::new()),
        &missing,
    ) {
        return Ok(refused(
            "INCOMPLETE_SWEEP",
            Datum::map([("missing", missing)]),
        ));
    }
    let grade = |item: &str, dialect: &str| {
        let found = grades.iter().find(|(i, d, _)| *i == item && *d == dialect);
        found.and_then(|(_, _, grade)| *grade) == Some(true)
    };
    let share = |dialect: &Dialect| {
        let hits = sweep
            .items
            .iter()
            .filter(|item| grade(item.id, dialect.name));
        let share = Rational::new(BigInt::from(hits.count()), BigInt::from(sweep.items.len()));
        (dialect.name.to_owned(), plain(&share))
    };
    let row = |item: &Item| {
        let cells = sweep.dialects.iter();
        let cells = cells.map(|dialect| {
            (
                dialect.name.to_owned(),
                Datum::Bool(grade(item.id, dialect.name)),
            )
        });
        (item.id.to_owned(), Datum::Map(cells.collect()))
    };
    let first = sweep.dialects.first().map_or("", |dialect| dialect.name);
    let flips = sweep.items.iter().flat_map(|item| {
        let later = sweep.dialects.iter().skip(1);
        let flipped =
            later.filter(move |dialect| grade(item.id, dialect.name) != grade(item.id, first));
        flipped.map(move |dialect| pair(item.id, dialect.name))
    });
    let detail = Datum::map([
        (
            "acceptance",
            Datum::Map(sweep.dialects.iter().map(share).collect()),
        ),
        ("items", Datum::Map(sweep.items.iter().map(row).collect())),
        ("flips_vs_first", Datum::List(flips.collect())),
    ]);
    Ok(checks.judge("SWEEP_GRADED", detail))
}

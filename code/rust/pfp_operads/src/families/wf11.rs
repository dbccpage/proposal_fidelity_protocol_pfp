//! WF11, dual-certificate synthesis: certify the optimum of a linear programme with an exact
//! dual, or its infeasibility with a Farkas vector.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf11:v1
//!
//! The programme is: maximise `c.x` subject to `A x <= b` and `x >= 0`, over the rationals.
//!
//! * A reply `{"x", "y"}` is certified as `OPTIMAL` when `x` is feasible, `y` is feasible for
//!   the dual (`y >= 0`, `A^T y >= c`), and `c.x = b.y`. Complementary slackness is recorded as
//!   a second check of the same fact. A feasible pair with a positive gap is a bound and not a
//!   certificate, and is refused as `WEAK_DUALITY_ONLY_BOUND`.
//! * A reply `{"farkas": y}` stands as the typed refusal `PRIMAL_INFEASIBLE` when `y >= 0`,
//!   `A^T y >= 0` and `b.y < 0`.
//!
//! Task: `A`, a nonempty list of rows; `b`, one exact rational per row; `c`, one exact rational
//! per column, at least one.

use num_traits::{Signed, Zero};

use crate::datum::Datum;
use crate::exact::{rationals, show, Rational};

use super::{no_reply, refused, typed_refusal, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF11",
    name: "Dual-certificate synthesis",
    host_check: "lp_dual_and_farkas_certificate",
    validate,
    walk,
};

/// Maximise `costs . x` subject to `rows x <= bounds`, `x >= 0`.
struct Programme {
    rows: Vec<Vec<Rational>>,
    bounds: Vec<Rational>,
    costs: Vec<Rational>,
}

fn programme(task: &Datum) -> Result<Programme, String> {
    let (Some(rows), Some(bounds), Some(costs)) = (
        task.get("A").and_then(Datum::as_list),
        task.get("b").and_then(Datum::as_list),
        task.get("c").and_then(Datum::as_list),
    ) else {
        return Err("A, b and c must be lists".to_owned());
    };
    if rows.is_empty() || costs.is_empty() {
        return Err("A needs at least one row and c at least one entry".to_owned());
    }
    let shaped = rows.len() == bounds.len()
        && rows
            .iter()
            .all(|row| row.as_list().is_some_and(|row| row.len() == costs.len()));
    if !shaped {
        return Err("A needs one row per entry of b and one column per entry of c".to_owned());
    }
    let exact = || {
        let rows: Option<Vec<_>> = rows.iter().map(rationals).collect();
        Some(Programme {
            rows: rows?,
            bounds: task.get("b").and_then(rationals)?,
            costs: task.get("c").and_then(rationals)?,
        })
    };
    exact().ok_or_else(|| "A, b and c must hold exact rationals".to_owned())
}

fn validate(task: &Datum, _sealed: &Datum) -> Result<(), String> {
    programme(task).map(|_| ())
}

fn vector(reply: &Datum, name: &str, entries: usize) -> Result<Vec<Rational>, String> {
    reply
        .get(name)
        .and_then(rationals)
        .filter(|vector| vector.len() == entries)
        .ok_or_else(|| format!("{name} must be {entries} exact rationals"))
}

fn dot(left: &[Rational], right: &[Rational]) -> Rational {
    left.iter().zip(right).map(|(a, b)| a * b).sum()
}

fn written(values: &[Rational]) -> Datum {
    Datum::List(values.iter().map(|v| Datum::text(show(v))).collect())
}

fn none_negative(values: &[Rational]) -> bool {
    values.iter().all(|value| !value.is_negative())
}

impl Programme {
    /// `A x`, one entry per row.
    fn applied(&self, x: &[Rational]) -> Vec<Rational> {
        self.rows.iter().map(|row| dot(row, x)).collect()
    }

    /// `A^T y`, one entry per column.
    fn pulled(&self, y: &[Rational]) -> Vec<Rational> {
        (0..self.costs.len())
            .map(|column| {
                let entries = self.rows.iter().zip(y);
                entries
                    .filter_map(|(row, weight)| Some(row.get(column)? * weight))
                    .sum()
            })
            .collect()
    }

    fn optimum(&self, reply: &Datum, checks: &mut Checks) -> Result<Verdict, String> {
        let x = vector(reply, "x", self.costs.len())?;
        let y = vector(reply, "y", self.bounds.len())?;
        let slack: Vec<Rational> = self
            .bounds
            .iter()
            .zip(self.applied(&x))
            .map(|(bound, used)| bound - used)
            .collect();
        let reduced: Vec<Rational> = self
            .pulled(&y)
            .into_iter()
            .zip(&self.costs)
            .map(|(priced, cost)| priced - cost)
            .collect();
        let primal = checks.record(
            "primal_feasible",
            none_negative(&x) && none_negative(&slack),
            &Datum::List(vec![written(&x), written(&slack)]),
        );
        let dual = checks.record(
            "dual_feasible",
            none_negative(&y) && none_negative(&reduced),
            &Datum::List(vec![written(&y), written(&reduced)]),
        );
        let gap = dot(&self.bounds, &y) - dot(&self.costs, &x);
        let shown = Datum::text(show(&gap));
        checks.record("zero_duality_gap", gap.is_zero(), &shown);
        let slackness = |weights: &[Rational], room: &[Rational]| {
            let pairs = weights.iter().zip(room);
            pairs
                .map(|(weight, room)| weight * room)
                .all(|v| v.is_zero())
        };
        checks.record(
            "complementary_slackness",
            slackness(&y, &slack) && slackness(&x, &reduced),
            &Datum::List(vec![written(&slack), written(&reduced)]),
        );
        if primal && dual && !gap.is_zero() {
            return Ok(refused(
                "WEAK_DUALITY_ONLY_BOUND",
                Datum::map([("gap", shown)]),
            ));
        }
        let value = Datum::text(show(&dot(&self.costs, &x)));
        Ok(checks.judge("OPTIMAL", Datum::map([("value", value), ("gap", shown)])))
    }

    fn infeasible(&self, reply: &Datum, checks: &mut Checks) -> Result<Verdict, String> {
        let y = vector(reply, "farkas", self.bounds.len())?;
        let pulled = self.pulled(&y);
        let level = dot(&self.bounds, &y);
        let shown = Datum::text(show(&level));
        checks.record("farkas_y_nonnegative", none_negative(&y), &written(&y));
        checks.record(
            "farkas_aty_nonnegative",
            none_negative(&pulled),
            &written(&pulled),
        );
        checks.record("farkas_by_negative", level.is_negative(), &shown);
        if checks.certified() {
            let detail = Datum::map([("farkas", written(&y)), ("by", shown)]);
            return Ok(typed_refusal("PRIMAL_INFEASIBLE", detail));
        }
        Ok(checks.judge("PRIMAL_INFEASIBLE", Datum::map([])))
    }
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let programme = programme(run.task).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("solve", run.prompt())? else {
        return Ok(no_reply());
    };
    if !reply.is_map() {
        return Err(Stop::Malformed("reply must be an object".to_owned()));
    }
    if reply.get("farkas").is_some() {
        return programme.infeasible(reply, checks).map_err(Stop::Malformed);
    }
    if reply.get("x").is_none() || reply.get("y").is_none() {
        return Err(Stop::Malformed(
            "reply must carry x and y, or a farkas vector".to_owned(),
        ));
    }
    programme.optimum(reply, checks).map_err(Stop::Malformed)
}

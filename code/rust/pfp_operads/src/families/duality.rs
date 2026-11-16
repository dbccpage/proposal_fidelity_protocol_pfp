//! The weighted-digraph duality grader that WF18 and WF35 share.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-duality:v1
//!
//! An item is a weighted digraph: `n`, an exact integer, and `edges`, a list of `[u, v, w]` with
//! integer ends and `w` an exact rational. A reply is the text of one JSON object, graded as:
//!
//! * `HOST_CERTIFIED`: `potential` is a list of `n` exact rationals with `phi[v] - phi[u] <= w`
//!   for every edge, and every edge end is a number from `0` to `n - 1`.
//! * `TYPED_REFUSAL`: `negative_cycle`, a list of at least two integers, is a closed walk along
//!   the edges (the lightest of any parallel edges) whose weights add to less than zero. It is
//!   read when `potential` is missing or is not a list of `n` entries.
//! * `REFUSED`: anything else, including text that is not one JSON object.
//!
//! One of the first two always exists for a graph, so a correct reply can always be graded.
//!
//! [`pin`] is the SHA-256 of this file's own text with every line ending read as `\n`. A dossier
//! that pins it is refused as soon as the rules above change.

use std::collections::BTreeMap;

use num_bigint::BigInt;
use num_traits::{ToPrimitive, Zero};

use crate::datum::Datum;
use crate::exact::{rational, Rational};

use super::{sha256_hex, CERTIFIED, REFUSED, TYPED_REFUSAL};

const SOURCE: &str = include_str!("duality.rs");

/// The pin of this grader: the digest of its source text.
pub fn pin() -> String {
    sha256_hex(&SOURCE.replace("\r\n", "\n").replace('\r', "\n"))
}

/// One weighted digraph.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Item {
    n: BigInt,
    edges: Vec<(BigInt, BigInt, Rational)>,
}

fn edge(datum: &Datum) -> Option<(BigInt, BigInt, Rational)> {
    match datum.as_list()? {
        [from, to, weight] => Some((
            from.as_int()?.clone(),
            to.as_int()?.clone(),
            rational(weight)?,
        )),
        _ => None,
    }
}

impl Item {
    /// The item a value states, or what is wrong with it.
    pub fn read(datum: &Datum) -> Result<Item, String> {
        let n = datum
            .get("n")
            .and_then(Datum::as_int)
            .ok_or("n must be an exact integer")?;
        let listed = datum
            .get("edges")
            .and_then(Datum::as_list)
            .ok_or("edges must be a list")?;
        let edges: Option<Vec<_>> = listed.iter().map(edge).collect();
        Ok(Item {
            n: n.clone(),
            edges: edges.ok_or("an edge is two integer ends and an exact rational weight")?,
        })
    }

    /// The reply's `potential`, read as an answer, when it lists `n` values.
    fn answer(&self, reply: &Datum) -> Option<Grade> {
        let listed = reply.get("potential").and_then(Datum::as_list)?;
        if BigInt::from(listed.len()) != self.n {
            return None;
        }
        let phi: Option<Vec<Rational>> = listed.iter().map(rational).collect();
        Some(phi.map_or(Grade::Refused, |phi| self.feasible(&phi)))
    }

    /// Whether `phi[v] - phi[u] <= w` holds on every edge, every end of which is a vertex.
    fn feasible(&self, phi: &[Rational]) -> Grade {
        let at = |end: &BigInt| end.to_usize().and_then(|place| phi.get(place));
        let holds = self.edges.iter().all(|(from, to, weight)| {
            matches!((at(from), at(to)), (Some(low), Some(high)) if high - low <= *weight)
        });
        if holds {
            Grade::Certified
        } else {
            Grade::Refused
        }
    }

    /// The lightest weight of the edges from one vertex to another.
    fn lightest(&self) -> BTreeMap<(&BigInt, &BigInt), &Rational> {
        let mut lightest: BTreeMap<(&BigInt, &BigInt), &Rational> = BTreeMap::new();
        for (from, to, weight) in &self.edges {
            let held = lightest.entry((from, to)).or_insert(weight);
            if weight < *held {
                *held = weight;
            }
        }
        lightest
    }

    /// The reply's `negative_cycle`, read as an answer.
    fn cycle(&self, reply: &Datum) -> Grade {
        let listed = reply.get("negative_cycle").and_then(Datum::as_list);
        let ends: Option<Vec<&BigInt>> = listed
            .filter(|ends| ends.len() >= 2)
            .and_then(|ends| ends.iter().map(Datum::as_int).collect());
        let Some(ends) = ends else {
            return Grade::Refused;
        };
        let lightest = self.lightest();
        let steps = ends.iter().zip(ends.iter().cycle().skip(1));
        let weights: Option<Vec<&Rational>> = steps
            .map(|(from, to)| lightest.get(&(*from, *to)).copied())
            .collect();
        let total: Option<Rational> = weights.map(|weights| weights.into_iter().sum());
        match total {
            Some(total) if total < Rational::zero() => Grade::TypedRefusal,
            _ => Grade::Refused,
        }
    }
}

/// How a reply to one item grades.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Grade {
    Certified,
    TypedRefusal,
    Refused,
}

impl Grade {
    /// The verdict word the stored dossiers use.
    pub fn name(self) -> &'static str {
        match self {
            Grade::Certified => CERTIFIED,
            Grade::TypedRefusal => TYPED_REFUSAL,
            Grade::Refused => REFUSED,
        }
    }

    /// Whether the reply stands: a feasible potential or a negative cycle.
    pub fn stands(self) -> bool {
        self != Grade::Refused
    }
}

/// How the reply text grades on the item.
pub fn grade(item: &Item, raw: &str) -> Grade {
    match Datum::parse(raw) {
        Ok(reply) => item.answer(&reply).unwrap_or_else(|| item.cycle(&reply)),
        Err(_) => Grade::Refused,
    }
}

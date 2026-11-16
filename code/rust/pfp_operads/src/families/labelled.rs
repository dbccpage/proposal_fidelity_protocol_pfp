//! Task graphs whose vertices are named by text, for the families whose replies key a value to
//! a vertex by its name.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-labelled:v1
//!
//! The edges of such a task are a list of `[u, v]` pairs of text. Vertices are numbered in the
//! order the edges first name them, as in [`crate::graph`], and a reply gives a value on the
//! vertices as an object with exactly one entry per vertex name.

use num_bigint::BigInt;

use crate::datum::Datum;
use crate::exact::{rational, Rational};
use crate::graph::Graph;

/// A graph and the text name of each of its vertices, in vertex order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Labelled {
    pub graph: Graph,
    names: Vec<String>,
}

fn pair(edge: &Datum) -> Option<(&str, &str)> {
    match edge.as_list()? {
        [from, to] => Some((from.as_text()?, to.as_text()?)),
        _ => None,
    }
}

/// The graph a value denotes: a list of `[u, v]` pairs of text. The list may be empty.
pub fn read(edges: &Datum) -> Option<Labelled> {
    let pairs: Vec<(&str, &str)> = edges.as_list()?.iter().map(pair).collect::<Option<_>>()?;
    let mut names: Vec<String> = Vec::new();
    let mut number = |name: &str| {
        let known = names.iter().position(|known| known == name);
        BigInt::from(known.unwrap_or_else(|| {
            names.push(name.to_owned());
            names.len() - 1
        }))
    };
    let numbered: Vec<(BigInt, BigInt)> = pairs
        .into_iter()
        .map(|(from, to)| (number(from), number(to)))
        .collect();
    let graph = Graph::of(numbered.iter().map(|(from, to)| (from, to)));
    Some(Labelled { graph, names })
}

impl Labelled {
    /// The names of the vertices, in vertex order.
    pub fn names(&self) -> &[String] {
        &self.names
    }

    /// Whether a value is an object whose keys are exactly the vertex names.
    pub fn covers(&self, listed: &Datum) -> bool {
        let Datum::Map(entries) = listed else {
            return false;
        };
        entries.len() == self.names.len()
            && self.names.iter().all(|name| entries.contains_key(name))
    }

    /// What `read` makes of the entry under each vertex name, in vertex order. Nothing when a
    /// vertex has no entry or `read` gives nothing for one. Entries under other keys are not
    /// looked at.
    pub fn by_name<T>(&self, listed: &Datum, read: impl Fn(&Datum) -> Option<T>) -> Option<Vec<T>> {
        let entry = |name: &String| listed.get(name).and_then(&read);
        self.names.iter().map(entry).collect()
    }

    /// One exact rational per vertex from an object keyed by vertex name, in vertex order.
    pub fn potential(&self, listed: &Datum) -> Option<Vec<Rational>> {
        self.by_name(listed, rational)
    }
}

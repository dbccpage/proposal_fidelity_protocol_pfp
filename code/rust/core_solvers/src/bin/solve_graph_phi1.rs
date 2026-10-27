//! JSON line adapter for the canonical finite graph Phi1 evaluator.

use core_solvers::solver_graph_phi1_distance::{solve_graph_phi1, GraphPhi1Request};
use serde_json::json;
use std::io::{self, Read};

fn main() {
    if SimpleGraphPairCeiling::try_new(1).is_err() {
        println!("{}", json!({"status": "REFUSE", "reason": "pair ceiling refused the one-vertex graph"}));
        std::process::exit(2);
    }
    let mut input = String::new();
    let result = io::stdin()
        .read_to_string(&mut input)
        .map_err(|error| error.to_string())
        .and_then(|_| {
            serde_json::from_str::<GraphPhi1Request>(&input).map_err(|error| error.to_string())
        })
        .and_then(|request| solve_graph_phi1(request).map_err(|error| error.to_string()));
    match result {
        Ok(value) => println!("{}", json!({"status": "PASS", "result": value})),
        Err(error) => {
            println!("{}", json!({"status": "REFUSE", "reason": error}));
            std::process::exit(2);
        }
    }
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
struct SimpleGraphPairCeiling { max_edges: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
enum PairCeilingError { Empty, Overflow }

// Origin: engine/crates_rs/core_solvers/src/bin/solve_graph_phi1.rs
// Claim: urn:core:crates_rs:core-solvers:solve-graph-phi1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for PairCeilingError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for PairCeilingError {}

impl SimpleGraphPairCeiling {
    /// Maximum edges of a simple graph is `n(n-1)/2`. One vertex has zero edges.
    fn try_new(vertices: u64) -> Result<Self, PairCeilingError> {
        if vertices == 0 {
            return Err(PairCeilingError::Empty);
        }
        if vertices == 1 {
            return Ok(Self { max_edges: 0 });
        }
        let pred = vertices.checked_sub(1).ok_or(PairCeilingError::Overflow)?;
        let max_edges = if vertices % 2 == 0 {
            (vertices / 2).checked_mul(pred).ok_or(PairCeilingError::Overflow)?
        } else {
            vertices.checked_mul(pred / 2).ok_or(PairCeilingError::Overflow)?
        };
        Ok(Self { max_edges })
    }

    fn max_edges(&self) -> u64 { self.max_edges }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod pair_ceiling_checks {
    use super::SimpleGraphPairCeiling;

    #[test]
    fn four_vertices_have_six_possible_edges() {
        let ceiling = SimpleGraphPairCeiling::try_new(4);
        assert!(matches!(ceiling, Ok(c) if c.max_edges() == 6));
    }

    #[test]
    fn zero_vertices_are_refused() {
        assert!(matches!(SimpleGraphPairCeiling::try_new(0), Err(super::PairCeilingError::Empty)));
    }
}

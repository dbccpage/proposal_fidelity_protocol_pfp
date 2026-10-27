//! JSON line adapter for the canonical finite graph Phi1 evaluator.

use core_solvers::graph_phi1::{solve_graph_phi1, GraphPhi1Request};
use serde_json::json;
use std::io::{self, Read};

fn main() {
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

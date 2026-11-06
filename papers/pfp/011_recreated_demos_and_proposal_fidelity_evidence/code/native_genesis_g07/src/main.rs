//! Thin G07 process transport over the unchanged source-pinned native owners.
use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Read};

use core_ooutwire_primitives::bounds::Bounds;
use core_ooutwire_primitives::closure::closure_challenge_orbits;
use core_ooutwire_primitives::event::Event;
use core_ooutwire_primitives::mark::{Mark, Pair};
use core_ooutwire_primitives::measure::MeasureKind;
use core_ooutwire_primitives::minima::{min_responses, quotient};
use core_ooutwire_primitives::reading::{Reading, READING_F, READING_L};
use core_ooutwire_primitives::regime::Regime;
use core_ooutwire_primitives::replay::replay;
use core_ooutwire_primitives::response::response_valid_naive;
use core_ooutwire_primitives::token::Token;
use core_ooutwire_primitives::tree::build_tree;
use serde_json::{json, Value};

fn number(value: &Value, key: &str) -> Result<usize, String> {
    value.get(key).and_then(Value::as_u64).map(|n| n as usize)
        .ok_or_else(|| format!("INVALID_NONNEGATIVE_INTEGER:{key}"))
}

fn text<'a>(value: &'a Value, key: &str) -> Result<&'a str, String> {
    value.get(key).and_then(Value::as_str).ok_or_else(|| format!("INVALID_STRING:{key}"))
}

fn pair(value: &Value) -> Result<Pair, String> {
    let values = value.as_array().ok_or("INVALID_PAIR")?;
    if values.len() != 2 { return Err("INVALID_PAIR_ARITY".into()); }
    let i = values[0].as_u64().ok_or("INVALID_PAIR_INDEX")? as usize;
    let j = values[1].as_u64().ok_or("INVALID_PAIR_INDEX")? as usize;
    if i >= j { return Err("UNORDERED_OR_DIAGONAL_PAIR".into()); }
    Ok(Pair::of(i, j))
}

fn history(value: &Value) -> Result<Vec<Event>, String> {
    let events = value.as_array().ok_or("HISTORY_NOT_ARRAY")?;
    if events.is_empty() || events.len() > 400 { return Err("HISTORY_BOUND".into()); }
    events.iter().map(|event| {
        let kind = text(event, "kind")?;
        Ok(match kind {
            "Supply" => Event::Supply(Token::new(text(event, "token")?)),
            "AdmitDatum" => Event::AdmitDatum(Token::new(text(event, "token")?)),
            "AdmitForm" => Event::AdmitForm(number(event, "arity")?),
            "AdmitRuleAll" => Event::AdmitRuleAll(number(event, "form")?),
            "AdmitInst" => {
                let args = event["args"].as_array().ok_or("INVALID_INSTANCE_ARGS")?;
                let marks = args.iter().map(|arg| arg.as_u64().map(|n| Mark(n as usize)).ok_or("INVALID_MARK"))
                    .collect::<Result<Vec<_>, _>>()?;
                Event::AdmitInst(number(event, "form")?, marks)
            }
            "Impose" => {
                let i = number(event, "i")?;
                let j = number(event, "j")?;
                if i >= j { return Err("UNORDERED_OR_DIAGONAL_PAIR".into()); }
                Event::Impose(Pair::of(i, j))
            }
            _ => return Err("UNKNOWN_EVENT_CONSTRUCTOR".into()),
        })
    }).collect()
}

fn state(regime: &Regime) -> Value {
    json!({"data": regime.data().iter().map(Token::text).collect::<Vec<_>>(),
           "forms": regime.forms(),
           "insts": regime.insts().iter().map(|inst| json!([inst.form, inst.args.iter().map(|m| m.0).collect::<Vec<_>>()])).collect::<Vec<_>>(),
           "rules": regime.rules().iter().copied().collect::<Vec<_>>(),
           "reqs": regime.reqs().iter().map(|p| vec![p.i.0, p.j.0]).collect::<Vec<_>>()})
}

fn renamed(reading: &Reading) -> Reading {
    let mut result = reading.clone();
    result.genesis = reading.genesis.iter().map(|event| match event {
        Event::Supply(token) => Event::Supply(Token::new(format!("renamed:{}", token.text()))),
        Event::AdmitDatum(token) => Event::AdmitDatum(Token::new(format!("renamed:{}", token.text()))),
        _ => event.clone(),
    }).collect();
    result
}

fn tree_report(reading: &Reading, relabel: bool, supply: bool) -> Value {
    let reading = if relabel { renamed(reading) } else { reading.clone() };
    let bounds = Bounds::default();
    let tree = build_tree(&reading, MeasureKind::Mu2, &bounds, 15, 3000, supply);
    let stats = tree.stats();
    let mut histograms: BTreeMap<String, BTreeMap<String, usize>> =
        (0..=15).map(|depth| (depth.to_string(), BTreeMap::new())).collect();
    let mut quiet: BTreeMap<usize, usize> = BTreeMap::new();
    let mut expanded_ties = 0;
    for node in &tree.nodes {
        assert_eq!(replay(&node.history).unwrap(), node.regime);
        let targets = if node.id == 0 { vec![reading.target] } else { closure_challenge_orbits(&node.regime).expect("declared isomorphism budget") };
        if targets.is_empty() { *quiet.entry(node.depth).or_default() += 1; }
        for target in targets {
            let minima = min_responses(&node.regime, target, MeasureKind::Mu2, &bounds).expect("original finite population has a response");
            assert!(minima.deltas.iter().all(|delta| response_valid_naive(&node.regime, target, delta).expect("native candidate replay")));
            let classes = quotient(&node.regime, target, &minima);
            *histograms.get_mut(&node.depth.to_string()).unwrap().entry(classes.len().to_string()).or_default() += 1;
            if node.status == "expanded" && classes.len() > 1 { expanded_ties += 1; }
        }
    }
    json!({"reading": reading.name, "relabel": relabel, "supply": supply,
           "stats": {"nodes": stats.nodes, "edges": stats.edges, "max_depth": stats.max_depth,
                     "expansions_with_ties": stats.expansions_with_ties, "all_certified": stats.all_certified,
                     "by_status": stats.by_status, "roles": stats.roles},
           "histograms": histograms, "quiet_nodes_by_depth": quiet,
           "expanded_ties": expanded_ties})
}

fn execute(request: Value) -> Result<Value, String> {
    if text(&request, "schema")? != "paper011.g07-native-request.v1" || number(&request, "max_items")? != 2 || number(&request, "max_arity")? != 2 {
        return Err("OUTSIDE_ORIGINAL_G07_CONTRACT".into());
    }
    let input = request["cases"].as_array().ok_or("CASES_NOT_ARRAY")?;
    if input.is_empty() || input.len() > 10000 { return Err("CASE_BOUND".into()); }
    let mut ids = BTreeSet::new();
    let mut cases = Vec::new();
    for case in input {
        let id = text(case, "id")?;
        if !ids.insert(id.to_owned()) { return Err("DUPLICATE_CASE_ID".into()); }
        let depth = number(case, "depth")?;
        let population = text(case, "population")?;
        if !matches!(text(case, "reading")?, "L" | "F") ||
            !((population == "P1" && depth <= 15) || (population == "P2" && depth <= 60)) {
            return Err("CASE_OUTSIDE_DECLARED_POPULATION".into());
        }
        let events = history(&case["history"])?;
        let regime = replay(&events).map_err(|err| format!("HISTORY_REPLAY_REFUSED:{err}"))?;
        if regime.n_data() > 32 { return Err("CARRIER_CEILING".into()); }
        let target = pair(&case["target"])?;
        let minima = min_responses(&regime, target, MeasureKind::Mu2, &Bounds::default()).ok_or("NO_MINIMUM_RESPONSE")?;
        let all_valid = minima.deltas.iter().all(|delta| response_valid_naive(&regime, target, delta).expect("native candidate replay"));
        if !all_valid { return Err("NAIVE_RESPONSE_VALIDITY_FAILED".into()); }
        let classes = quotient(&regime, target, &minima);
        let mut sizes = classes.iter().map(|item| item.size).collect::<Vec<_>>();
        sizes.sort();
        if sizes.iter().sum::<usize>() != minima.deltas.len() { return Err("QUOTIENT_MEMBER_CENSUS_FAILED".into()); }
        cases.push(json!({"id": id, "depth": depth, "state": state(&regime),
                          "width": classes.len(), "raw_minima": minima.deltas.len(),
                          "cost": [minima.cost.0 as i64, minima.cost.1], "class_sizes": sizes,
                          "all_responses_valid_naive": all_valid,
                          "classes": classes.iter().map(|item| json!({"key": format!("{:?}", item.key), "size": item.size,
                                                                    "representative": format!("{:?}", item.representative)})).collect::<Vec<_>>(),
                          "raw_deltas": minima.deltas.iter().map(|delta| format!("{:?}", delta)).collect::<Vec<_>>() }));
    }
    let mut trees = Vec::new();
    let mut closed = Vec::new();
    for reading in [&*READING_L, &*READING_F] {
        for relabel in [false, true] { trees.push(tree_report(reading, relabel, true)); }
        closed.push(tree_report(reading, false, false));
    }
    Ok(json!({"schema": "paper011.g07-native-response.v1", "AuthorityEffect": "None",
              "cases": cases, "trees": trees, "closed_trees": closed}))
}

fn main() {
    let mut raw = Vec::new();
    io::stdin().take(32 * 1024 * 1024 + 1).read_to_end(&mut raw).unwrap();
    if raw.len() > 32 * 1024 * 1024 { eprintln!("REQUEST_BYTE_CEILING"); std::process::exit(2); }
    let outcome = serde_json::from_slice(&raw).map_err(|err| err.to_string()).and_then(execute);
    match outcome {
        Ok(response) => println!("{}", serde_json::to_string(&response).unwrap()),
        Err(reason) => { eprintln!("{reason}"); std::process::exit(2); }
    }
}

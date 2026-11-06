//! Thin transport adapter; all enumeration and canonicalization stay in the existing crate.
use core_ooutwire_primitives::{
    bounds::Bounds,
    candidate::{delta_events, Item},
    canonical::{canonical_bruteforce, try_canonical},
    event::Event,
    measure::{Measure, MeasureKind},
    minima::{min_responses, try_quotient},
    reading::{READING_F, READING_L},
    replay::{replay, replay_from},
};
use serde_json::{json, Value};
use std::io::{self, Read};

fn solve(request: &Value) -> Result<Value, String> {
    let object = request.as_object().ok_or("REQUEST_NOT_OBJECT")?;
    if object.len() != 4 || !["reading", "measure", "max_items", "max_arity"].iter()
        .all(|name| object.contains_key(*name)) {
        return Err("REQUEST_FIELDS".into());
    }
    if request["max_items"].as_u64() != Some(2) || request["max_arity"].as_u64() != Some(2) {
        return Err("OUTSIDE_ORIGINAL_BOUNDS".into());
    }
    let reading = match request["reading"].as_str() {
        Some("F") => &*READING_F,
        Some("L") => &*READING_L,
        _ => return Err("UNDECLARED_READING".into()),
    };
    let measure = match request["measure"].as_str() {
        Some("mu1") => MeasureKind::Mu1,
        Some("mu2") => MeasureKind::Mu2,
        _ => return Err("UNDECLARED_MEASURE".into()),
    };
    let base = replay(&reading.genesis).map_err(|e| format!("GENESIS_REPLAY:{e:?}"))?;
    let mr = min_responses(&base, reading.target, measure, &Bounds::default())
        .ok_or("NO_MINIMUM")?;
    let classes = try_quotient(&base, reading.target, &mr).map_err(|e| format!("ISO_BUDGET:{e:?}"))?;
    let mut deltas = Vec::new();
    for delta in &mr.deltas {
        let items: Vec<Value> = delta.iter().map(|item| match item {
            Item::NewDatum => json!({"kind":"datum"}),
            Item::NewForm(a) => json!({"kind":"form","arity":a}),
            Item::NewRuleAll(f) => json!({"kind":"rule_all","form":f}),
            Item::NewInst(f, args) => json!({"kind":"inst","form":f,
                "args":args.iter().map(|x| x.0).collect::<Vec<_>>()})
        }).collect();
        let mut events = vec![Event::Impose(reading.target)];
        events.extend(delta_events(&base, delta));
        let child = replay_from(&events, &base).map_err(|e| format!("CHILD_REPLAY:{e:?}"))?;
        let key = try_canonical(&child).map_err(|e| format!("ISO_BUDGET:{e:?}"))?;
        let brute_key = canonical_bruteforce(&child);
        deltas.push(json!({"items":items,"key":key,"brute_key":brute_key}));
    }
    let class_rows: Vec<Value> = classes.iter().map(|c| json!({
        "key":c.key,"size":c.size,"label":c.label})).collect();
    Ok(json!({"status":"COMPUTED","request":request,"cost":mr.cost,
        "measure":measure.name(),"deltas":deltas,"classes":class_rows,
        "computation":"core_ooutwire_primitives::min_responses/try_quotient/canonical_bruteforce"}))
}

fn main() {
    let mut bytes = Vec::new();
    if io::stdin().read_to_end(&mut bytes).is_err() {
        println!("{}", json!({"status":"REFUSED","error":"INPUT_READ"}));
        std::process::exit(2);
    }
    let result = serde_json::from_slice::<Value>(&bytes)
        .map_err(|_| "MALFORMED_JSON".to_string()).and_then(|v| solve(&v));
    match result {
        Ok(value) => println!("{value}"),
        Err(error) => {
            println!("{}", json!({"status":"REFUSED","error":error}));
            std::process::exit(2);
        }
    }
}

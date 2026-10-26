//! G03 transport: declared adapter and existing source-pinned native owners.
use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Read};
use omega_ooutwire_primitives::bounds::Bounds;
use omega_ooutwire_primitives::candidate::{delta_events, Item};
use omega_ooutwire_primitives::canonical::try_canonical;
use omega_ooutwire_primitives::event::Event;
use omega_ooutwire_primitives::mark::{Mark, Pair};
use omega_ooutwire_primitives::measure::MeasureKind;
use omega_ooutwire_primitives::minima::{min_responses, try_quotient};
use omega_ooutwire_primitives::reading::{READING_F, READING_L};
use omega_ooutwire_primitives::regime::Regime;
use omega_ooutwire_primitives::renaming::{rename, Bijection, Key};
use omega_ooutwire_primitives::replay::{replay, replay_from};
use omega_ooutwire_primitives::response::response_valid_naive;
use omega_ooutwire_primitives::separability::collapsed_pairs;
use omega_ooutwire_primitives::token::Token;
use serde_json::{json, Value};

fn number(v: &Value, key: &str) -> Result<usize, String> {
    v[key].as_u64().and_then(|n| usize::try_from(n).ok()).ok_or_else(|| format!("INVALID_INTEGER:{key}"))
}
fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str, String> {
    v[key].as_str().ok_or_else(|| format!("INVALID_STRING:{key}"))
}
fn coordinate(n: usize, reading: &str, i: usize) -> usize {
    let shift = usize::from(reading == "F");
    if i == 0 { shift } else if i == n { shift + 1 } else { shift + i + 1 }
}
fn base(n: usize, reading: &str, variant: &str) -> Result<(Regime, Vec<usize>), String> {
    let prefix = if reading == "L" { &*READING_L } else { &*READING_F };
    let mut history = prefix.genesis.clone();
    for i in 1..n {
        let token = Token::new(format!("G03:chain:{n}:{reading}:{i}"));
        history.extend([Event::Supply(token.clone()), Event::AdmitDatum(token)]);
    }
    let chain_data = n + 1 + usize::from(reading == "F");
    let count = usize::BITS as usize - (n - 1).leading_zeros() as usize;
    for bit in 0..count {
        let token = Token::new(format!("G03:anchor:{n}:{reading}:{bit}"));
        history.extend([Event::Supply(token.clone()), Event::AdmitDatum(token)]);
    }
    let mut singleton = vec![coordinate(n, reading, 0), coordinate(n, reading, n)];
    if reading == "F" { singleton.push(0); }
    for _ in 0..singleton.len() + count { history.push(Event::AdmitForm(1)); }
    for (f, mark) in singleton.iter().enumerate() {
        history.push(Event::AdmitInst(f, vec![Mark(*mark)]));
    }
    for level in 0..count {
        for bit in 0..=level {
            history.push(Event::AdmitInst(singleton.len() + level, vec![Mark(chain_data + bit)]));
        }
    }
    for i in 1..n {
        for bit in 0..count {
            if i & (1 << bit) != 0 {
                history.push(Event::Impose(Pair::of(coordinate(n, reading, i), chain_data + bit)));
            }
        }
    }
    if variant == "token_renaming" {
        history = history.into_iter().map(|event| match event {
            Event::Supply(token) => Event::Supply(Token::new(format!("renamed:{}", token.text()))),
            Event::AdmitDatum(token) => Event::AdmitDatum(Token::new(format!("renamed:{}", token.text()))),
            other => other,
        }).collect();
    }
    let original = replay(&history).map_err(|err| format!("ADAPTER_HISTORY_REFUSED:{err}"))?;
    if !original.rules().is_empty() { return Err("RULE_FREE_ENGINE_CONTRACT".into()); }
    let expected: BTreeSet<Pair> = (1..n).flat_map(|i| ((i + 1)..n).map(move |j|
        Pair::of(coordinate(n, reading, i), coordinate(n, reading, j)))).collect();
    let observed: BTreeSet<Pair> = collapsed_pairs(&original).into_iter().collect();
    if expected != observed { return Err("COLLAPSE_EQUIVALENCE_FAILED".into()); }
    let mut images = BTreeSet::new();
    for i in 0..=n {
        for j in (i + 1)..=n {
            let p = Pair::of(coordinate(n, reading, i), coordinate(n, reading, j));
            if !images.insert(p) || observed.contains(&p) != (i >= 1 && j < n) {
                return Err("ALL_CHAIN_PAIRS_INJECTIVITY_OR_COLLAPSE_FAILED".into());
            }
        }
    }
    let mut pi: Vec<usize> = (0..original.n_data()).collect();
    if variant == "reversal" {
        for i in 0..=n { pi[coordinate(n, reading, i)] = coordinate(n, reading, n - i); }
        let bijection = Bijection { data: pi.clone(), forms: (0..original.n_forms()).collect() };
        Ok((rename(&original, &bijection), pi))
    } else { Ok((original, pi)) }
}
fn state(r: &Regime) -> Value {
    json!({"data": r.data().iter().map(Token::text).collect::<Vec<_>>(), "forms": r.forms(),
           "insts": r.insts().iter().map(|i| json!([i.form, i.args.iter().map(|m| m.0).collect::<Vec<_>>()])).collect::<Vec<_>>(),
           "rules": r.rules().iter().copied().collect::<Vec<_>>(),
           "reqs": r.reqs().iter().map(|p| vec![p.i.0,p.j.0]).collect::<Vec<_>>()})
}
fn delta(items: &[Item]) -> Value {
    Value::Array(items.iter().map(|item| match item {
        Item::NewDatum => json!({"kind":"datum"}),
        Item::NewForm(arity) => json!({"kind":"form","arity":arity}),
        Item::NewRuleAll(form) => json!({"kind":"rule_all","form":form}),
        Item::NewInst(form,args) => json!({"kind":"inst","form":form,"args":args.iter().map(|m| m.0).collect::<Vec<_>>()}),
    }).collect())
}
fn fresh_mark(r: &Regime, p: Pair, items: &[Item]) -> bool {
    items == [Item::NewForm(1), Item::NewInst(r.n_forms(), vec![p.j])]
}
fn execute(request: &Value) -> Result<Value, String> {
    if text(request,"schema")? != "paper011.g03-native-request.v1" || text(request,"adapter_id")? != "G03_DECLARED_PREFIX_ANCHORS_V1" {
        return Err("UNBOUND_ADAPTER".into());
    }
    if text(request,"predicate_domain")? != "canonical_classes" { return Err("PREDICATES_NOT_ON_CLASSES".into()); }
    let input = request["cases"].as_array().ok_or("CASES_NOT_ARRAY")?;
    if input.is_empty() || input.len() > 10000 { return Err("CASE_BOUND".into()); }
    let mut ids = BTreeSet::new();
    let mut calls = Vec::new();
    let mut bases: BTreeMap<(usize,String,String),(Regime,Vec<usize>,Key,Value)> = BTreeMap::new();
    for case in input {
        let id = text(case,"id")?;
        if !ids.insert(id.to_owned()) { return Err("DUPLICATE_PAIR_CASE".into()); }
        let (n,i,j) = (number(case,"n")?,number(case,"i")?,number(case,"j")?);
        let reading = text(case,"reading")?;
        let variant = text(case,"variant")?;
        let measure_text = text(case,"measure")?;
        if !(3..=18).contains(&n) || !(1 <= i && i < j && j < n) || !matches!(reading,"L"|"F") ||
           !matches!(variant,"base"|"token_renaming"|"reversal") || !matches!(measure_text,"mu1"|"mu2") {
            return Err("OUTSIDE_DECLARED_CASE_POPULATION".into());
        }
        let identity = (n,reading.to_owned(),variant.to_owned());
        if !bases.contains_key(&identity) {
            let (regime,pi) = base(n,reading,variant)?;
            let key = try_canonical(&regime).map_err(|err| format!("IsoBudgetError:{err}"))?;
            let serialized = state(&regime);
            bases.insert(identity.clone(),(regime,pi,key,serialized));
        }
        let (regime,pi,base_key,serialized) = bases.get(&identity).ok_or("BASE_CACHE_MISSING")?;
        let expected = Pair::of(pi[coordinate(n,reading,i)],pi[coordinate(n,reading,j)]);
        if case["target"] != json!([expected.i.0,expected.j.0]) { return Err("FIXED_TARGET_REUSE".into()); }
        if case["state"] != *serialized { return Err("CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH".into()); }
        let measure = if measure_text == "mu1" { MeasureKind::Mu1 } else { MeasureKind::Mu2 };
        // This is the actual oracle call. Its exact arguments are retained below.
        let minimum = min_responses(&regime,expected,measure,&Bounds::default()).ok_or("NO_RESPONSE_IN_DECLARED_BOUNDS")?;
        let classes = try_quotient(&regime,expected,&minimum).map_err(|err| format!("IsoBudgetError:{err}"))?;
        let mut members: BTreeMap<Key,Vec<&Vec<Item>>> = BTreeMap::new();
        for candidate in &minimum.deltas {
            if !response_valid_naive(&regime,expected,candidate).map_err(|err| err.to_string())? {
                return Err("NATIVE_NAIVE_CERTIFICATE_FAILED".into());
            }
            let mut events = vec![Event::Impose(expected)];
            events.extend(delta_events(&regime,candidate));
            let child = replay_from(&events,&regime).map_err(|err| err.to_string())?;
            let key = try_canonical(&child).map_err(|err| format!("IsoBudgetError:{err}"))?;
            members.entry(key).or_default().push(candidate);
        }
        if members.len() != classes.len() { return Err("CLASS_CENSUS_MISMATCH".into()); }
        let mut class_rows = Vec::new();
        for class in classes {
            let group = members.get(&class.key).ok_or("CLASS_KEY_MISSING")?;
            if group.len() != class.size || group[0] != &class.representative { return Err("CLASS_CERTIFICATE_MISMATCH".into()); }
            class_rows.push(json!({"key":class.key,"size":class.size,"representative":delta(&class.representative),
                "members":group.iter().map(|candidate| delta(candidate)).collect::<Vec<_>>(),
                "fresh_mark":group.iter().any(|candidate| fresh_mark(&regime,expected,candidate))}));
        }
        let weak = class_rows.iter().any(|row| row["fresh_mark"] == true);
        let strong = class_rows.iter().all(|row| row["fresh_mark"] == true);
        calls.push(json!({"id":id,"n":n,"i":i,"j":j,"reading":reading,"measure":measure_text,"variant":variant,
            "target":[expected.i.0,expected.j.0],"base_canonical_key":base_key,"cost":[minimum.cost.0,minimum.cost.1],
            "raw_count":minimum.deltas.len(),"raw_deltas":minimum.deltas.iter().map(|d| delta(d)).collect::<Vec<_>>(),
            "classes":class_rows,"predicate_domain":"canonical_classes","weak":weak,"strong":strong}));
    }
    Ok(json!({"schema":"paper011.g03-native-response.v1","adapter_id":"G03_DECLARED_PREFIX_ANCHORS_V1",
              "AuthorityEffect":"None","calls":calls}))
}
fn main() {
    let mut raw = Vec::new();
    if io::stdin().take(128*1024*1024+1).read_to_end(&mut raw).is_err() || raw.len()>128*1024*1024 {
        eprintln!("REQUEST_BYTE_CEILING"); std::process::exit(2);
    }
    match serde_json::from_slice(&raw).map_err(|err|err.to_string()).and_then(|v|execute(&v)) {
        Ok(result) => println!("{}",result),
        Err(reason) => { eprintln!("{reason}"); std::process::exit(2); }
    }
}

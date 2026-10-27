//! G04 transport/enumeration adapter. Regime, admission, profiles, and renaming
//! are computed by the existing pinned core_ooutwire_primitives archive.
use core_ooutwire_primitives::{
    admission::step, event::Event, mark::{Mark, Pair}, profile::profiles,
    reading::{READING_F, READING_L}, regime::Regime,
    renaming::{Bijection, Key, permutations, serialize}, replay::replay, token::Token,
};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::io::{self, Read};

const NAMES: [&str; 7] = ["free", "total_apart", "total_same", "parity", "residue_three", "chain", "one_sided_total"];
type Labels = Vec<Vec<String>>;
type Cache = HashMap<Regime, Vec<Vec<bool>>>;

fn label(s: usize, i: usize, j: usize) -> &'static str {
    if i == j || s == 0 { return "free"; }
    match s {
        1 | 6 => "apart", 2 => "same",
        3 => if i.abs_diff(j) % 2 == 0 { "same" } else { "apart" },
        4 => if i.abs_diff(j) % 3 == 0 { "same" } else { "apart" },
        5 => if i.abs_diff(j) == 1 { "apart" } else { "free" },
        _ => unreachable!(),
    }
}
fn matrices() -> Vec<Labels> {
    (0..7).map(|s| (0..5).map(|i| (0..5).map(|j| label(s,i,j).to_string()).collect()).collect()).collect()
}
fn event_json(e: &Event) -> Value {
    match e {
        Event::Supply(t) => json!({"kind":"Supply", "token":t.text()}),
        Event::AdmitDatum(t) => json!({"kind":"AdmitDatum", "token":t.text()}),
        Event::AdmitForm(a) => json!({"kind":"AdmitForm", "arity":a}),
        Event::AdmitInst(f,a) => json!({"kind":"AdmitInst", "form":f, "args":a.iter().map(|m|m.0).collect::<Vec<_>>()}),
        Event::AdmitRuleAll(f) => json!({"kind":"AdmitRuleAll", "form":f}),
        Event::Impose(p) => json!({"kind":"Impose", "i":p.i.0, "j":p.j.0}),
    }
}
fn args(arity: usize, n: usize) -> Vec<Vec<Mark>> {
    if arity == 0 { return vec![vec![]]; }
    args(arity-1,n).iter().flat_map(|rest| (0..n).map(move |a| {
        let mut x=rest.clone(); x.push(Mark(a)); x
    })).collect()
}
fn alphabet(r: &Regime, grown: usize) -> Vec<Event> {
    let mut out=vec![Event::Supply(Token::new("<z>"))];
    if r.n_data()<5 && grown<5 { out.push(Event::AdmitDatum(Token::new(format!("<n{grown}>")))); }
    if r.n_forms()<2 { out.extend([Event::AdmitForm(1), Event::AdmitForm(2)]); }
    for (f,&arity) in r.forms().iter().enumerate() {
        for a in args(arity,r.n_data()) { out.push(Event::AdmitInst(f,a)); }
        out.push(Event::AdmitRuleAll(f));
    }
    for i in 0..r.n_data() { for j in i+1..r.n_data() { out.push(Event::Impose(Pair::of(i,j))); } }
    out
}
fn renamed(e: &Event, tokens: &BTreeMap<String,String>) -> Result<Event,String> {
    let token=|t:&Token| tokens.get(t.text()).map(|s|Token::new(s.clone())).ok_or("TOKEN_MAP_INCOMPLETE".to_string());
    Ok(match e { Event::Supply(t)=>Event::Supply(token(t)?), Event::AdmitDatum(t)=>Event::AdmitDatum(token(t)?), _=>e.clone() })
}
fn carries(r: &Regime, labels: &Labels, cache: &mut Cache) -> bool {
    let equal=cache.entry(r.clone()).or_insert_with(|| {
        let p=profiles(r);
        (0..r.n_data()).map(|i|(0..r.n_data()).map(|j|p[i]==p[j]).collect()).collect()
    });
    (0..r.n_data()).any(|i|(i+1..r.n_data()).any(|j|
        (labels[i][j]=="apart" && equal[i][j]) || (labels[i][j]=="same" && !equal[i][j])))
}
fn first(trace: &[Regime], labels: &Labels, cache: &mut Cache) -> Option<usize> {
    trace.iter().position(|r| carries(r,labels,cache))
}
fn transport(labels: &Labels, pi: &[usize]) -> Labels {
    let mut inv=vec![0;pi.len()]; for (i,&j) in pi.iter().enumerate() { inv[j]=i; }
    (0..pi.len()).map(|i|(0..pi.len()).map(|j|labels[inv[i]][inv[j]].clone()).collect()).collect()
}
fn prefix_ranges(trace: &[Regime], p: &Bijection) -> bool {
    trace.iter().all(|r| p.data[..r.n_data()].iter().all(|&x|x<r.n_data()) && p.forms[..r.n_forms()].iter().all(|&x|x<r.n_forms()))
}
#[derive(Clone)]
struct Node { history:Vec<Event>, trace:Vec<Regime>, grown:usize }
fn enumerate(genesis:&[Event]) -> Result<(Vec<Node>,usize,usize),String> {
    let r=replay(genesis).map_err(|e|format!("GENESIS:{e:?}"))?;
    let root=Node{history:vec![],trace:vec![r],grown:0};
    let mut nodes=vec![root.clone()]; let mut stack=vec![root]; let(mut stops,mut refused)=(0,0);
    while let Some(n)=stack.pop() {
        if n.history.len()==4 { continue; }
        let r=n.trace.last().unwrap();
        if r.n_data()>=5 || n.grown>=5 {stops+=1;}
        if r.n_forms()>=2 {stops+=2;}
        for e in alphabet(r,n.grown) {
            match step(r,&e) {
                Err(_)=>refused+=1,
                Ok(child)=>{
                    let mut h=n.history.clone(); h.push(e.clone());
                    let mut trace=n.trace.clone(); trace.push(child);
                    let next=Node{history:h,trace,grown:n.grown+usize::from(matches!(e,Event::AdmitDatum(_)))};
                    nodes.push(next.clone()); stack.push(next);
                }
            }
        }
    }
    Ok((nodes,stops,refused))
}
fn signature(genesis:&[Event], history:&[Event]) -> String {
    let mut names=BTreeMap::new(); let mut result=vec![];
    for e in genesis.iter().chain(history.iter()) {
        let mut v=event_json(e);
        if let Some(t)=v["token"].as_str() {
            let next=names.len(); let number=*names.entry(t.to_string()).or_insert(next);
            v["token"]=json!(number);
        }
        result.push(v);
    }
    serde_json::to_string(&(genesis.len(),result)).unwrap()
}
fn census(name:&str, genesis:&[Event], token_map:&BTreeMap<String,String>, labels:&[Labels]) -> Result<Value,String> {
    let (nodes,stops,refused)=enumerate(genesis)?;
    let expected=match name {"EMPTY"=>577,"L"=>3928,"F"=>14293,_=>return Err("UNDECLARED_BASE".into())};
    if nodes.len()!=expected {return Err("NATIVE_POPULATION_MISMATCH".into());}
    let mut cache=Cache::new(); let mut rows=vec![]; let mut renamed_rows=vec![];
    let mut groups:BTreeMap<Vec<Key>,Vec<usize>>=BTreeMap::new();
    let mut token_groups:BTreeMap<String,Vec<usize>>=BTreeMap::new();
    let mut collision:Vec<HashMap<Regime,BTreeSet<usize>>>=(0..7).map(|_|HashMap::new()).collect();
    let renamed_genesis:Vec<Event>=genesis.iter().map(|e|renamed(e,token_map)).collect::<Result<_,_>>()?;
    let renamed_base=replay(&renamed_genesis).map_err(|e|format!("RENAMED_GENESIS:{e:?}"))?;
    for (i,n) in nodes.iter().enumerate() {
        let keys:Vec<Key>=n.trace.iter().map(|r|serialize(r,&Bijection::identity(r.n_data(),r.n_forms()))).collect();
        let indices:Vec<_>=labels.iter().map(|s|first(&n.trace,s,&mut cache)).collect();
        for s in 0..7 {if let Some(index)=indices[s] { collision[s].entry(n.trace.last().unwrap().clone()).or_default().insert(index); }}
        groups.entry(keys.clone()).or_default().push(i);
        token_groups.entry(signature(genesis,&n.history)).or_default().push(i);
        rows.push(json!({"id":format!("{name}:{i}"),"history":n.history.iter().map(event_json).collect::<Vec<_>>(),"grown":n.grown,"prefixes":keys,"first":indices}));
        let h:Vec<Event>=n.history.iter().map(|e|renamed(e,token_map)).collect::<Result<_,_>>()?;
        let mut r=renamed_base.clone(); let mut trace=vec![r.clone()];
        for e in &h {r=step(&r,e).map_err(|e|format!("RENAMED_REPLAY:{e:?}"))?;trace.push(r.clone());}
        renamed_rows.push(json!({"id":format!("{name}:{i}"),"history":h.iter().map(event_json).collect::<Vec<_>>(),
            "prefixes":trace.iter().map(|r|serialize(r,&Bijection::identity(r.n_data(),r.n_forms()))).collect::<Vec<_>>(),
            "first":labels.iter().map(|s|first(&trace,s,&mut cache)).collect::<Vec<_>>()}));
    }
    let mut ordered:Vec<_>=groups.iter().collect(); ordered.sort_by_key(|(_,m)|m[0]);
    let mut group_rows=vec![]; let mut relations=vec![];
    for (keys,members) in ordered {
        let i=members[0]; let trace=&nodes[i].trace; let last=trace.last().unwrap();
        group_rows.push(json!({"representative":format!("{name}:{i}"),"members":members.iter().map(|m|format!("{name}:{m}")).collect::<Vec<_>>(),"prefixes":keys}));
        for pi in permutations(last.n_data()) { for phi in permutations(last.n_forms()) {
            let p=Bijection{data:pi.clone(),forms:phi};
            if !prefix_ranges(trace,&p) {continue;}
            let renamed_keys:Vec<Key>=trace.iter().map(|r|serialize(r,&p)).collect();
            if let Some(target)=groups.get(&renamed_keys) {
                let j=target[0]; let to=&nodes[j].trace;
                let from_indices:Vec<_>=labels.iter().map(|s|first(trace,s,&mut cache)).collect();
                let fixed:Vec<_>=labels.iter().map(|s|first(to,s,&mut cache)).collect();
                let transported:Vec<_>=labels.iter().map(|s|first(to,&transport(s,&p.data),&mut cache)).collect();
                relations.push(json!({"source":format!("{name}:{i}"),"target":format!("{name}:{j}"),"pi":p.data,"phi":p.forms,
                    "multiplicity":members.len()*target.len(),"source_first":from_indices,"fixed_first":fixed,"transported_first":transported}));
            }
        }}
    }
    let token_partition:Vec<_>=token_groups.values().map(|m|json!({"members":m.iter().map(|i|format!("{name}:{i}")).collect::<Vec<_>>()})).collect();
    let collisions:Vec<_>=collision.iter().map(|c|c.values().filter(|v|v.len()>1).count()).collect();
    Ok(json!({"name":name,"genesis":genesis.iter().map(event_json).collect::<Vec<_>>(),"bound_stops":stops,"grammar_refusals":refused,
        "rows":rows,"renamed_genesis":renamed_genesis.iter().map(event_json).collect::<Vec<_>>(),"renamed_rows":renamed_rows,
        "groups":group_rows,"relations":relations,"token_partition":token_partition,"colliding_regimes":collisions}))
}
fn audit(request:&Value) -> Result<Value,String> {
    let pi:Vec<usize>=serde_json::from_value(request["pi"].clone()).map_err(|_|"DATA_BIJECTION".to_string())?;
    if pi.iter().copied().collect::<BTreeSet<_>>()!=(0..pi.len()).collect() {return Err("DATA_BIJECTION".into());}
    match request["mutation"].as_str() {
        Some("untransported_stake")=>{
            let s=request["stake"].as_u64().ok_or("STAKE")? as usize;
            if s>=7 {return Err("STAKE".into());}
            let correct=transport(&matrices()[s],&pi);
            if request["claimed_transported_labels"]!=json!(correct) {return Err("STAKE_TRANSPORT_MISMATCH".into());}
            Ok(json!({"status":"ACCEPTED","id":request["id"],"transported_labels":correct}))
        }
        Some("pi_on_forms")=>{
            let nf=request["forms"].as_u64().ok_or("FORM_DIMENSION")? as usize;
            if pi.len()!=nf {return Err("FORM_BIJECTION_DIMENSION".into());}
            Ok(json!({"status":"ACCEPTED","id":request["id"]}))
        }
        Some("endpoint_only")=>{
            let histories:Vec<Vec<Value>>=serde_json::from_value(request["histories"].clone()).map_err(|_|"HISTORIES")?;
            let mut traces=vec![];
            for h in histories {
                let mut r=Regime::genesis();let mut trace=vec![r.clone()];
                for e in h {
                    let event=match e["kind"].as_str() {
                        Some("AdmitDatum")=>Event::AdmitDatum(Token::new(e["token"].as_str().ok_or("TOKEN")?)),
                        Some("Supply")=>Event::Supply(Token::new(e["token"].as_str().ok_or("TOKEN")?)),
                        _=>return Err("ENDPOINT_WITNESS_EVENT".into())};
                    r=step(&r,&event).map_err(|_|"WITNESS_REPLAY")?;trace.push(r.clone());
                } traces.push(trace);
            }
            if traces.len()!=2 || traces[0].last()!=traces[1].last() {return Err("ENDPOINT_WITNESS_BINDING".into());}
            let mut cache=Cache::new();let actual:Vec<_>=traces.iter().map(|t|first(t,&matrices()[1],&mut cache)).collect();
            if actual[0]!=actual[1] {return Err(format!("ENDPOINT_NOT_FIRST_INDEX:{}",serde_json::to_string(&actual).unwrap()));}
            Ok(json!({"status":"ACCEPTED","id":request["id"],"first":actual}))
        }
        _=>Err("UNDECLARED_MUTATION".into())
    }
}
fn solve(v:&Value)->Result<Value,String> {
    if v["action"]=="audit" {return audit(v);}
    if v["action"]!="census" {return Err("UNDECLARED_ACTION".into());}
    if v["stake_names"]!=json!(NAMES) || v["labels"]!=json!(matrices()) {return Err("ORIGINAL_STAKE_BINDING".into());}
    let tokens:BTreeMap<String,String>=serde_json::from_value(v["token_map"].clone()).map_err(|_|"TOKEN_MAP")?;
    if tokens.len()!=9 || tokens.values().collect::<BTreeSet<_>>().len()!=9 {return Err("TOKEN_MAP_NOT_BIJECTIVE".into());}
    let bases=vec![census("EMPTY",&[],&tokens,&matrices())?,census("L",&READING_L.genesis,&tokens,&matrices())?,census("F",&READING_F.genesis,&tokens,&matrices())?];
    Ok(json!({"schema":"paper011.g04-native-census.v1","status":"COMPUTED","bases":bases,
        "computation":"Existing crate admission::step, replay, profile::profiles, renaming::serialize/permutations; declared G04 demand and rectangle bookkeeping in this thin wrapper"}))
}
fn main(){
    let mut bytes=vec![];
    if io::stdin().read_to_end(&mut bytes).is_err(){eprintln!("INPUT_READ");std::process::exit(2);}
    let request=serde_json::from_slice::<Value>(&bytes);
    let result=request.as_ref().map_err(|_|"MALFORMED_JSON".to_string()).and_then(|v|solve(v));
    match result {Ok(v)=>println!("{v}"),Err(error)=>{
        let id=request.as_ref().ok().map(|v|v["id"].clone()).unwrap_or(Value::Null);
        println!("{}",json!({"status":"REFUSED","id":id,"error":error}));std::process::exit(2);
    }}
}

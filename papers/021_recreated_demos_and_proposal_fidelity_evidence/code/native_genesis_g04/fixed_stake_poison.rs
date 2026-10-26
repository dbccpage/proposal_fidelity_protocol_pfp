//! Supplement to G04: the universal fixed-stake claim, on original L histories.
//! All regime/profile/renaming calculations use the existing native archive.
use omega_ooutwire_primitives::{admission::step, event::Event, mark::{Mark,Pair},
    profile::profiles, reading::READING_L, regime::Regime,
    renaming::{Bijection,serialize}, replay::replay, token::Token};
use serde_json::{json,Value};
use std::collections::BTreeSet;
use std::io::{self,Read};

fn number(v:&Value)->Result<usize,String>{v.as_u64().and_then(|n|usize::try_from(n).ok()).ok_or("INTEGER".into())}
fn event(v:&Value)->Result<Event,String>{
    Ok(match v["kind"].as_str(){
        Some("Supply")=>Event::Supply(Token::new(v["token"].as_str().ok_or("TOKEN")?)),
        Some("AdmitDatum")=>Event::AdmitDatum(Token::new(v["token"].as_str().ok_or("TOKEN")?)),
        Some("AdmitForm")=>{let a=number(&v["arity"])?;if a!=1&&a!=2{return Err("ORIGINAL_ARITY_BOUND".into());}Event::AdmitForm(a)},
        Some("AdmitInst")=>Event::AdmitInst(number(&v["form"])?,v["args"].as_array().ok_or("ARGS")?.iter().map(|a|number(a).map(Mark)).collect::<Result<_,_>>()?),
        Some("AdmitRuleAll")=>Event::AdmitRuleAll(number(&v["form"])?),
        Some("Impose")=>Event::Impose(Pair::new(Mark(number(&v["i"])?),Mark(number(&v["j"])?)).ok_or("DIAGONAL_REQUIREMENT")?),
        _=>return Err("EVENT_KIND".into()),
    })
}
fn trace(h:&Value)->Result<Vec<Regime>,String>{
    let events=h.as_array().ok_or("HISTORY")?;
    if events.len()>4{return Err("ORIGINAL_LENGTH_BOUND".into());}
    let mut r=replay(&READING_L.genesis).map_err(|e|format!("GENESIS:{e:?}"))?;
    let mut out=vec![r.clone()];
    for v in events{
        r=step(&r,&event(v)?).map_err(|e|format!("GRAMMAR:{e:?}"))?;
        if r.n_data()>5||r.n_forms()>2{return Err("ORIGINAL_CARRIER_BOUND".into());}
        out.push(r.clone());
    } Ok(out)
}
fn first(t:&[Regime],s:&[Vec<String>])->Option<usize>{
    t.iter().position(|r|{
        let p=profiles(r);
        (0..r.n_data()).any(|i|(i+1..r.n_data()).any(|j|
            (s[i][j]=="apart"&&p[i]==p[j])||(s[i][j]=="same"&&p[i]!=p[j])))
    })
}
fn solve(v:&Value)->Result<Value,String>{
    if v["base"]!="L"{return Err("ORIGINAL_BASE_BINDING".into());}
    let h=v["histories"].as_array().ok_or("HISTORIES")?;
    if h.len()!=2{return Err("HISTORY_PAIR".into());}
    let a=trace(&h[0])?;let b=trace(&h[1])?;
    if a.len()!=b.len(){return Err("PREFIX_LENGTH".into());}
    let pi:Vec<usize>=serde_json::from_value(v["pi"].clone()).map_err(|_|"DATA_BIJECTION")?;
    let phi:Vec<usize>=serde_json::from_value(v["phi"].clone()).map_err(|_|"FORM_BIJECTION")?;
    if pi.len()!=a.last().unwrap().n_data()||pi.iter().copied().collect::<BTreeSet<_>>()!=(0..pi.len()).collect(){return Err("DATA_BIJECTION".into());}
    if phi.len()!=a.last().unwrap().n_forms()||phi.iter().copied().collect::<BTreeSet<_>>()!=(0..phi.len()).collect(){return Err("FORM_BIJECTION".into());}
    let p=Bijection{data:pi.clone(),forms:phi};
    let mut left=vec![];let mut right=vec![];
    for (i,(r,s)) in a.iter().zip(&b).enumerate(){
        if r.n_data()!=s.n_data()||r.n_forms()!=s.n_forms()||p.data[..r.n_data()].iter().any(|&x|x>=r.n_data())||p.forms[..r.n_forms()].iter().any(|&x|x>=r.n_forms()){
            return Err(format!("PREFIX_BIJECTION_RANGE:{i}"));
        }
        let x=serialize(r,&p);let y=serialize(s,&Bijection::identity(s.n_data(),s.n_forms()));
        if x!=y{return Err(format!("COMMON_PREFIX_ISOMORPHISM:{i}"));}
        left.push(x);right.push(y);
    }
    let labels:Vec<Vec<String>>=serde_json::from_value(v["labels"].clone()).map_err(|_|"STAKE_MATRIX")?;
    if labels.len()!=pi.len()||labels.iter().any(|r|r.len()!=pi.len()){return Err("STAKE_DIMENSION".into());}
    for i in 0..pi.len(){for j in 0..pi.len(){
        if !["apart","same","free"].contains(&labels[i][j].as_str())||labels[i][j]!=labels[j][i]||(i==j&&labels[i][j]!="free"){return Err("STAKE_LABELS".into());}
    }}
    let mut inv=vec![0;pi.len()];for(i,&j)in pi.iter().enumerate(){inv[j]=i;}
    let transported:Vec<Vec<String>>=(0..pi.len()).map(|i|(0..pi.len()).map(|j|labels[inv[i]][inv[j]].clone()).collect()).collect();
    let fixed=vec![first(&a,&labels),first(&b,&labels)];
    let transported_first=vec![first(&a,&labels),first(&b,&transported)];
    match v["mode"].as_str(){
        Some("assert_universal_fixed") if fixed[0]!=fixed[1]=>return Err(format!("UNIVERSAL_FIXED_STAKE_POISON:{}",serde_json::to_string(&fixed).unwrap())),
        Some("assert_transported") if v["reported_transported_labels"]!=json!(transported)=>return Err("STAKE_TRANSPORT_MISMATCH".into()),
        Some("compute")|Some("assert_universal_fixed")|Some("assert_transported")=>{},
        _=>return Err("MODE".into()),
    }
    Ok(json!({"status":"COMPUTED","id":v["id"],"request":v,"fixed_first":fixed,"transported_first":transported_first,
        "transported_labels":transported,"common_prefix_isomorphism":true,"source_prefixes_under_pi_phi":left,"target_prefixes":right,
        "source_prefixes":a.iter().map(|r|serialize(r,&Bijection::identity(r.n_data(),r.n_forms()))).collect::<Vec<_>>(),
        "computation":"Existing native replay/admission/profile/serialize, with the separately declared supplementary stake"}))
}
fn main(){
    let mut bytes=vec![];if io::stdin().read_to_end(&mut bytes).is_err(){std::process::exit(2);}
    let v=serde_json::from_slice::<Value>(&bytes);
    let result=v.as_ref().map_err(|_|"MALFORMED_JSON".to_string()).and_then(|v|solve(v));
    match result{Ok(result)=>println!("{result}"),Err(error)=>{
        let id=v.as_ref().ok().map(|v|v["id"].clone()).unwrap_or(Value::Null);
        println!("{}",json!({"status":"REFUSED","id":id,"error":error}));std::process::exit(2);
    }}
}

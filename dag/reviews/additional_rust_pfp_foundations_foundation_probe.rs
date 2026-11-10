#![allow(dead_code)]
extern crate self as pfp_runtime;
#[path = "../../code/rust/pfp_runtime/src/canonical.rs"]
pub mod canonical;
#[path = "additional_rust_pfp_foundations_foundation_owner.rs"]
mod foundation;
use foundation::*;
use num_bigint::BigInt;
use num_rational::BigRational;
use serde_json::{json, Value};
fn q(value: i32)->BigRational {BigRational::from_integer(BigInt::from(value))}
fn node(tag:&str,body:Value)->Value {json!(["core-canonical-v1",tag,body])}
fn string(value:&str)->Value {node("string",json!(value))}
fn integer(value:&str)->Value {node("int",json!(value))}
fn entry(name:&str,value:Value)->Value {node("entry",json!([string(name),value]))}
fn field(name:&str,value:Value)->Value {node("field",json!([string(name),value]))}
fn main(){
    let detector=ExactFiniteDetector::new("detector",vec![DetectorEntry::new("s",q(1)).unwrap()]).unwrap();
    let universe=DeclaredRepairUniverse::new("context","s",vec![]).unwrap();
    let exhausted=ExhaustionCertificate::enumerate(&universe,&detector).unwrap();
    let extension=ConservativeExtensionWitness::certify("context","expanded",&["s"],&["s","new"],|p|*p,|p|Some(*p),|_|q(1),|_|q(1)).unwrap();
    assert!(extension.detector_preserved());
    assert_eq!(extension.points()[0].detector_value(),&q(1));
    let candidate=ExtensionCandidate::evaluate("candidate","context","s","s",extension,|_|q(0)).unwrap();
    let family=DeclaredExtensionFamily::new("family","context","s",vec![candidate]).unwrap();
    let assessed=assess_extension_family(&exhausted,&family).unwrap();
    assert_eq!(assessed.unique_candidate_id(),Some("candidate"));
    println!("different_detector_resolves_positive_preserved_source=true");

    let detector=ExactFiniteDetector::new("same-detector-label",vec![DetectorEntry::new("s",q(1)).unwrap(),DetectorEntry::new("a",q(1)).unwrap(),DetectorEntry::new("b",q(1)).unwrap()]).unwrap();
    let first=DeclaredRepairUniverse::new("same-context","s",vec![RepairCandidate::new("repair","a").unwrap()]).unwrap();
    let second=DeclaredRepairUniverse::new("same-context","s",vec![RepairCandidate::new("repair","b").unwrap()]).unwrap();
    assert_eq!(ExhaustionCertificate::enumerate(&first,&detector).unwrap().certificate_id(),ExhaustionCertificate::enumerate(&second,&detector).unwrap().certificate_id());
    println!("certificate_id_omits_result_state_mapping=true");

    let invalid=vec![
        ("invalid_bytes",node("bytes",json!([string("zz")]))),
        ("noncanonical_bytes",node("bytes",json!([string("FF")]))),
        ("duplicate_set",node("set",json!([integer("1"),integer("1")]))),
        ("unordered_set",node("set",json!([integer("2"),integer("1")]))),
        ("duplicate_mapping",node("mapping",json!([string("builtins"),string("dict"),entry("x",integer("1")),entry("x",integer("2"))]))),
        ("foreign_mapping_type",node("mapping",json!([string("custom"),string("dict")]))),
        ("nonfield_dataclass",node("dataclass",json!([string("module"),string("Class"),integer("1")]))),
        ("duplicate_dataclass_field",node("dataclass",json!([string("module"),string("Class"),field("x",integer("1")),field("x",integer("2"))]))),
        ("empty_enum_identity",node("enum",json!([string(""),string(""),string(""),integer("1")]))),
    ];
    for (name,wire) in invalid {
        assert!(canonical::canonical_unwire(&wire).is_ok(),"{name}");
        println!("canonical_native_accepts_{name}=true");
        println!("wire:{name}:{}",serde_json::to_string(&wire).unwrap());
    }
}

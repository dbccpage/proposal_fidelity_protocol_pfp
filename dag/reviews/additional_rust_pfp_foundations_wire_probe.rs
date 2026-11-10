#![allow(dead_code)]
#[path = "../../code/rust/core_types/src/s_level.rs"] mod level;
#[path = "../../code/rust/core_types/src/trace_step.rs"] mod trace;
#[path = "../../code/rust/core_types/src/node_id.rs"] mod node_id;
#[path = "../../code/rust/core_types/src/mcts_scheduler.rs"] mod mcts;
#[path = "../../code/rust/core_types/src/tolerant_float.rs"] mod floats;
#[path = "../../code/rust/core_types/src/structural_intake.rs"] mod intake;
fn main() {
    let raw = r#"{"from":0,"to":1,"weight":-1.0}"#;
    let bypass=serde_json::from_str::<trace::TraceDependency>(raw);
    println!("negative_weight_wire_admitted={}",bypass.is_ok());
    println!("negative_weight_constructor_refused={}",trace::TraceDependency::new_validated(0,1,-1.0).is_err());
    std::panic::set_hook(Box::new(|_| {}));
    let source=level::SLevel{n:u32::MAX,symbols:1,operators:0,packet_families:0,witnesses:0,lift_budget:1};
    let target=level::SLevel{n:0,symbols:2,operators:0,packet_families:0,witnesses:0,lift_budget:0};
    let result=std::panic::catch_unwind(||level::LicensedLift::certify(source,target));
    println!("level_overflow_panics={}",result.is_err());
    println!("level_wraparound_certified={}",matches!(result,Ok(Ok(_))));
    let tree=std::panic::catch_unwind(|| mcts::VisitTree::try_new(&[Some(1),Some(999)], &[1,1], &[1,0]));
    println!("unvalidated_ancestor_index_panics={}",tree.is_err());
    println!("nan_bounds_admitted={}",floats::TolerantFloat::bounded(1.0,0.0,f64::NAN,f64::NAN).is_ok());
    let conflict=intake::IntakeCorrespondenceSpan::new("c".into(),"a".into(),"b".into(),intake::IntakeMatchKind::Conflict);
    let merge=intake::IntakeCorrespondenceSpan::new("m".into(),"a".into(),"b".into(),intake::IntakeMatchKind::DefinitionalIdentity);
    println!("conflict_then_merge_admitted={}",intake::CertifiedIntake::try_certified(&[conflict.clone(),merge.clone()]).is_ok());
    println!("merge_then_conflict_refused={}",intake::CertifiedIntake::try_certified(&[merge,conflict]).is_err());
    assert!(bypass.is_ok());
    assert!(tree.is_err());
}

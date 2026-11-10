#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi1.rs"] pub mod phi1;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/binary_degree.rs"] pub mod binary_degree;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/weighted_l1_norm.rs"] pub mod weighted_l1_norm;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/residual.rs"] pub mod residual;

pub use phi1::Phi1Functional;
fn main(){
 use weighted_l1_norm::WeightedL1Norm;
 let negative:WeightedL1Norm=serde_json::from_str(r#"{"weights":[-1.0]}"#).unwrap();
 assert_eq!(negative.evaluate(&[1.0]).unwrap(),-1.0);
 assert!(WeightedL1Norm::new(vec![-1.0]).is_err());
 let good=WeightedL1Norm::new(vec![2.0]).unwrap();
 assert!(good.evaluate(&[f64::NAN]).unwrap().is_nan());
 assert!(good.evaluate(&[f64::MAX]).unwrap().is_infinite());
 println!("weighted_norm_wire_bypass_negative=true;nan_and_finite_overflow_are_ok=true");
 let bad=core_kernel::exact::Exact::new_raw(1.into(),0.into());
 let result=std::panic::catch_unwind(||residual::Residual::new(vec![bad]));
 assert!(result.is_err());
 assert!(serde_json::from_str::<residual::Residual>(r#"{"vector":["1/0"],"l1":"0"}"#).is_err());
 println!("residual_native_raw_denominator_panics=true;wire_guard_control=true");
}

#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi1.rs"] pub mod phi1;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/binary_degree.rs"] pub mod binary_degree;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/gamma2.rs"] pub mod gamma2;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/wire.rs"] pub mod wire;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi2.rs"] pub mod phi2;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi3.rs"] pub mod phi3;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi4.rs"] pub mod phi4;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/residual_splitting.rs"] pub mod residual_splitting;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/observer_gauge.rs"] pub mod observer_gauge;

pub use phi1::Phi1Functional;
fn q(n:i64)->num_rational::BigRational{num_rational::BigRational::from_integer(n.into())}
fn main(){
 let out=std::panic::catch_unwind(||residual_splitting::splitting_from_parameter(&[vec![q(1),q(1)]],&[vec![]],&[vec![q(1)]],&[vec![],vec![]]));
 assert!(out.is_err());println!("splitting_wide_basis_panics=true");
 use observer_gauge::{ObserverGauge,ScalarGauge,VectorGauge,TraceGauge};
 assert!(ScalarGauge::new(vec![-1.0]).is_err());
 assert_eq!((ScalarGauge{weights:vec![-1.0]}).evaluate(&[1.0]).unwrap(),-1.0);
 assert_eq!((VectorGauge{weights:vec![-1.0]}).evaluate(&[vec![1.0]]).unwrap(),-1.0);
 assert_eq!((TraceGauge{weights:vec![-1.0]}).evaluate(&[vec![2.0]]).unwrap(),-1.0);
 println!("all_three_observer_gauges_accept_negative_weights=true");
 let bad=num_rational::BigRational::new_raw(1.into(),0.into());
 assert!(std::panic::catch_unwind(||observer_gauge::rational_squared_l2(&[bad.clone()])).is_err());
 assert!(std::panic::catch_unwind(||phi3::Phi3Functional::evaluate_bianchi_defect(&[vec![bad.clone()]],&[q(1)],&[q(1)])).is_err());
 assert!(phi4::Phi4Functional::evaluate_curvature_defect(&[vec![bad]],&[q(1)],None).is_err());
 println!("unguarded_squared_l2_and_phi3_bianchi_panics=true;phi4_guard_control=true");
 let c2=phi2::ExactPhi2Certificate{flux_b:vec![q(0)],d1:vec![vec![q(0)]],d0:None,weights:vec![q(1)],potential_a:vec![q(0)],primal_residual:vec![q(0)],dual_witness:vec![q(0)],reported_value:q(0)};
 assert!(phi2::Phi2Functional::verify_exact_certificate(c2.clone()).is_ok());
 assert!(serde_json::from_str::<phi2::ExactPhi2Certificate>(&serde_json::to_string(&c2).unwrap()).is_err());
 let c3=phi3::ExactPhi3Certificate{flux_h:vec![q(0)],d2:vec![vec![q(0)]],d1:None,d0:None,weights:vec![q(1)],potential_b:vec![q(0)],primal_residual:vec![q(0)],dual_witness:vec![q(0)],reported_value:q(0)};
 assert!(phi3::Phi3Functional::verify_exact_certificate(c3.clone()).is_ok());
 assert!(serde_json::from_str::<phi3::ExactPhi3Certificate>(&serde_json::to_string(&c3).unwrap()).is_err());
 let c4=phi4::ExactPhi4Certificate{flux_g:vec![q(0)],d3:vec![vec![q(0)]],d2:vec![vec![q(0)]],d1:None,d0:None,weights:vec![q(1)],potential_c:vec![q(0)],primal_residual:vec![q(0)],dual_witness:vec![q(0)],reported_value:q(0)};
 assert!(phi4::Phi4Functional::verify_exact_certificate(c4.clone()).is_ok());
 assert!(serde_json::from_str::<phi4::ExactPhi4Certificate>(&serde_json::to_string(&c4).unwrap()).is_err());
 println!("valid_phi2_phi3_phi4_serialize_deserialize_roundtrips_fail=true");
}

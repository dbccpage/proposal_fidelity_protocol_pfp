#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi1.rs"] pub mod phi1;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/binary_degree.rs"] pub mod binary_degree;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_certifiers/src/phi1_certifier.rs"] pub mod phi1_certifier;

fn main(){
 use num_rational::BigRational as Q;
 let one=Q::from_integer(1.into());let raw=Q::new_raw(1.into(),0.into());
 let outcome=std::panic::catch_unwind(||phi1_certifier::Phi1Verifier::verify([one.clone()],[one.clone()],[vec![raw]],[one.clone()],[one.clone()]));
 println!("generic_lp_raw_denominator_panics={}",outcome.is_err());
 if let Ok(value)=outcome {println!("generic_lp_raw_denominator_result={:?}",value);}
 let d=nalgebra::DMatrix::from_row_slice(2,1,&[f64::MAX,f64::MAX]);
 let omega=nalgebra::DVector::from_vec(vec![0.0,0.0]);
 let alpha=nalgebra::DVector::from_vec(vec![0.0]);
 let dual=nalgebra::DVector::from_vec(vec![f64::MAX,-f64::MAX]);
 let boundary=d.transpose()*&dual;assert!(boundary[0].is_nan());
 let result=phi1::Phi1Functional::diagnose_primal_dual(&d,&omega,&alpha,&dual).unwrap();
 assert_eq!(result.dual_boundary_defect,0.0);
 println!("nan_boundary_reported_as_zero_defect=true");
 let invalid=Q::new_raw(1.into(),0.into());
 assert_eq!(phi1::Phi1Functional::unweighted_l1_rational(&[invalid]),None);
 println!("full_phi1_denominator_guard_control=true");
}

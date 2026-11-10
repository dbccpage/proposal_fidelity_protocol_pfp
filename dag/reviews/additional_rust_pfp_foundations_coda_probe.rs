mod protocol { pub fn canonical_json(v: &serde_json::Value)->Vec<u8>{serde_json::to_vec(v).unwrap()} }
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/coda.rs"] mod coda;

fn main(){
 use num_bigint::BigInt; use num_rational::BigRational; use num_traits::ToPrimitive;
 let q=|x:i64| BigRational::from_integer(BigInt::from(x));
 let d0=vec![vec![q(2)],vec![q(3)]];
 let target=vec![q(0),q(1)];
 let cert=core_solvers::solver_cohomology_simplicial_l1::solve_l1_quotient(&d0,&target).unwrap();
 assert_eq!(cert.distance,BigRational::new(BigInt::from(2),BigInt::from(3)));
 assert_eq!(cert.distance.to_u64(),Some(0));
 let payload=serde_json::json!({"input_id":"synthetic-fractional-distance","sieve_non_empty":true,"refinement_consistent":true,"gluing_succeeded":true,"phi1_distance":0,"gamma2_distance":0,"license_granted":false,"matrices":{"d0":[[2],[3]],"d1":[],"cochain":[0,1]}});
 let receipt=coda::evaluate_coda(&payload).unwrap();
 println!("exact_distance={}; truncated_distance=0; accepted_receipt={}",cert.distance,serde_json::to_string(&receipt).unwrap());
}

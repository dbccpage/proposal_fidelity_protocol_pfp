#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/phi1.rs"] pub mod phi1;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/binary_degree.rs"] pub mod binary_degree;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/gamma2.rs"] pub mod gamma2;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/l1_seminorm.rs"] pub mod l1_seminorm;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_functional/src/factory.rs"] pub mod factory;

pub use phi1::Phi1Functional;
fn main(){
 let path=std::env::args().nth(1).unwrap();
 let data:serde_json::Value=serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
 for c in data["cases"].as_array().unwrap(){
  let name=c["name"].as_str().unwrap();
  let input:factory::FunctionalInput=serde_json::from_value(c["input"].clone()).unwrap();
  let cfg=&c["configuration"];
  let kernel=match name{
   "phi1"=>factory::ConfiguredFunctional::phi1(serde_json::from_value(cfg[1].clone()).unwrap(),serde_json::from_value(cfg[2].clone()).unwrap()).unwrap(),
   "gamma2"=>factory::ConfiguredFunctional::gamma2(serde_json::from_value(cfg[1].clone()).unwrap()),
   _=>panic!("unexpected fixture")
  };
  let output=factory::evaluate_functional(name,&kernel,&input).unwrap();
  let got=serde_json::to_value(output.record()).unwrap();
  println!("{}",serde_json::json!({"name":name,"typed_input":serde_json::to_string(&input).unwrap(),"match":got==c["expected_record"],"actual_record":got}));
  let claim:factory::UntrustedFunctionalRecord=serde_json::from_value(c["expected_record"].clone()).unwrap();
  println!("{}",serde_json::json!({"name":name,"record_replay":format!("{:?}",factory::replay_functional_record(name,&kernel,&input,&claim))}));
 }
}

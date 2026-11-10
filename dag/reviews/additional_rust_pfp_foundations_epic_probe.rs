#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/bytecode/mod.rs"] mod bytecode;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp/src/epics/coda.rs"] mod coda;

fn main(){
 use bytecode::*;
 let original=BytecodeBundle::new(vec![Instruction::LoadGlyph{reg:0,glyph_id:1}]);
 let mut wire=serde_json::to_value(&original).unwrap();
 wire["instructions"][0]["LoadGlyph"]["glyph_id"]=serde_json::json!(99);
 let changed:BytecodeBundle=serde_json::from_value(wire).unwrap();
 let receipt=execute(&changed,1).unwrap();
 assert_eq!(receipt.bundle_digest,original.digest());
 assert_eq!(receipt.final_registers[0].1,RegisterValue::Glyph{glyph_id:99});
 println!("changed_program_executes_under_original_digest=true");
 let bundle=BytecodeBundle::new(vec![Instruction::EmitObstruction{reg_defect:0,defect_code:1},Instruction::AssertBoundary{reg_chain:0,boundary_map_id:7},Instruction::AssertBoundary{reg_chain:0,boundary_map_id:7}]);
 let receipt=execute(&bundle,3).unwrap();
 assert_eq!(receipt.final_registers[0].1,RegisterValue::Boundary{boundary_map_id:7,exact:true});
 assert_eq!(receipt.defect_count,1);
 println!("repeating_boundary_assertion_promotes_inexact_to_exact=true");
 let bundle=BytecodeBundle::new(vec![Instruction::StepFibration{reg_fiber:0,base_step:0}]);
 let envelope=RegisterEnvelopeV1{registers:vec![RegisterValue::Fiber{base_step:0,level:u64::MAX}]};
 match std::panic::catch_unwind(||execute_with_envelope(&bundle,1,&envelope)){
  Err(_)=>println!("max_fiber_level=panic"),
  Ok(Ok(receipt))=>{assert_eq!(receipt.final_registers[0].1,RegisterValue::Fiber{base_step:0,level:0});println!("max_fiber_level=wrapped_zero")},
  other=>panic!("unexpected {other:?}")
 }
 let mismatched:coda::AdmittedClaim=serde_json::from_value(serde_json::json!({"claim":{"layer":"Physical","statement":"declared","evidence":{"ParityWitness":{"verdict_token":"invented"}}}})).unwrap();
 assert_eq!(mismatched.layer(),coda::Layer::Physical);
 let forged:coda::QuarantinedAdapter=serde_json::from_value(serde_json::json!({"name":"synthetic","hypothesis":"h","certificate":{"reviewer":"","rationale":""}})).unwrap();
 assert_eq!(forged.author_receipt().unwrap().reviewer,"");
 println!("wire_bypasses_layer_and_named_reviewer_gates=true");
}

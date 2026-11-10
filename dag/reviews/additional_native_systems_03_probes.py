"""Synthetic mathematical/contract probes; no production edits or benchmark data."""
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('native_runner',Path(__file__).with_name('additional_native_systems_probes.py'))
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.RUST=r'''
use core_operad_theory::kernel::*;
use core_operad_theory::deformation::{QuadraticOperad,QuadraticRelation,BarCobarResolution,KoszulDualBuilder};
use core_operad_theory::geometric::{RectilinearDisk,LittleDisksConfiguration};
use core_operad_theory::applications::{OEASWorkflowOperad,AgentCapabilitySlice};
use core_operad_theory::realization::PolicyDecisionRef;
use std::collections::HashSet;
use serde_json::json;
const D:&str="sha256:0000000000000000000000000000000000000000000000000000000000000000";
fn term(id:&str)->OperationTerm {
 OperationTerm::Primitive(OperationSpec::new(OperationSpecInput{operation_id:id,version:"v1",input_ports:vec![PortSpec::new("in","State","any").unwrap()],output_port:PortSpec::new("out","State","any").unwrap(),executor_ref:"exec",executor_digest:D,tool_refs:vec![],effects:vec![],invocation_grade:InvocationGrade::Discipline,authority_effect:AuthorityEffect::None,authority_ceiling:AuthorityEffect::None}).unwrap())
}
fn main(){
 let a=QuadraticOperad::new("Ass");let b=QuadraticOperad::new("Renamed");
 let dual=KoszulDualBuilder::build_koszul_dual_skeleton(&b).unwrap();
 println!("{}",json!({"probe":"koszul_by_name","same_empty_structure":a.generators.is_empty()&&b.generators.is_empty()&&a.relations.is_empty()&&b.relations.is_empty(),"Ass":BarCobarResolution::evaluate_koszul_resolution(&a).is_koszul,"Renamed":BarCobarResolution::evaluate_koszul_resolution(&b).is_koszul,"dual_pairing_computed":dual.is_pairing_computed,"dual_label_accepted":BarCobarResolution::evaluate_koszul_resolution(&dual.dual_operad).is_koszul}));
 let relation=QuadraticRelation{relation_id:"r".into(),generating_terms:vec!["not a tree".into(),"not a tree either".into()],coefficients:vec![1,-1],description:"synthetic".into()};
 println!("{}",json!({"probe":"quadratic_unparsed_terms","certified":relation.certify().is_ok()}));
 let disk=RectilinearDisk::new(2,vec![0.0,0.0],0.2).unwrap();
 let config=LittleDisksConfiguration::new(3,vec![disk]);
 println!("{}",json!({"probe":"little_disk_dimension","accepted":config.is_ok(),"configuration_dimension":config.as_ref().map(|x|x.dimension).ok(),"disk_dimension":config.as_ref().map(|x|x.disks[0].dimension).ok(),"nan_radius_constructor_accepted":RectilinearDisk::new(2,vec![0.0,0.0],f64::NAN).is_ok()}));
 let mut wf=OEASWorkflowOperad::new().unwrap();wf.register_skill("unlicensed",&["State"],"State","synthetic").unwrap();
 let tree=wf.create_corolla("unlicensed").unwrap();
 let slice=AgentCapabilitySlice::new("agent",HashSet::new(),HashSet::new(),HashSet::new());
 let mut interpreter=wf.create_agent_interpreter("agent",Some(slice));
 let registered=interpreter.register_action("unlicensed",|_|Ok(json!("executed"))).is_ok();
 let outcome=interpreter.evaluate_tree(&tree,&[json!("input")],Some(PolicyDecisionRef::new("policy",true)));
 println!("{}",json!({"probe":"ignored_capability_slice","empty_slice":true,"registered_unlicensed":registered,"completed":outcome.is_completed}));
 let source=term("source");let target=term("target");let left=normalize_term(&source).unwrap();let right=normalize_term(&target).unwrap();
 let cmp=ComparisonEvidence::new(&left.canonical_id().unwrap(),&right.canonical_id().unwrap(),"relation",D,D,"verifier",D,D,ComparisonVerdict::EquivalentOnScope,EquivalenceGrade::CertifiedIsomorphism,D,D,D,D,AuthorityEffect::None).unwrap();
 let sig=format!("hmac-sha256:{}","z".repeat(64));
 let att=Attestation::new(&pair_subject_digest(&left,&right,"relation",D).unwrap(),&cmp.canonical_id().unwrap(),"relation","producer","verifier",D,D,D,&sig,AuthorityEffect::None).unwrap();
 let unsealed=admit_equivalence(&source,&target,&cmp,&AttestationKind::Unsealed(att.clone()));
 let sealed=AttestationKind::ReplaySealed(ReplayVerifiedAttestation::seal(att));
 let admitted=admit_equivalence(&source,&target,&cmp,&sealed);
 println!("{}",json!({"probe":"caller_sealed_isomorphism","different_terms":left.canonical_id().unwrap()!=right.canonical_id().unwrap(),"nonhex_fake_hmac":true,"unsealed_refusal":unsealed.err().map(|e|e.code),"caller_sealed_accepted":admitted.is_ok(),"no_replay_or_key_supplied":true}));
}
'''
if __name__=='__main__':
    print(json.dumps(runner.run(),indent=2))

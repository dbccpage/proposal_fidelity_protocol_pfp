"""Finite native audit probes; compiles against current offline Cargo artifacts.
No implementation or test source changes. Temporary probe products are removed.
"""
from pathlib import Path
import json, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[2]
RUST=r'''
use core_epistemic_immune_system::authenticated::*;
use core_epistemic_immune_system::thymus::{ThymusGate,ThymusVerdict};
use core_epistemic_immune_system::anti_skill::{AntiSkillSpecV2,FailureClass};
use core_operad_theory::foundation::{OperadColour,OperadSignature,Operation,OperationId,PlanarTree};
use core_prompt_civilization::rank::{ExactPageRankSolverV1,RankEvidenceV1,CitationGraph};
use core_prompt_civilization::genealogy::{LineageGraphV1,InheritanceRelationship,inheritance_witness_digest};
use core_prompt_civilization::immunity::ImmunityEngineV1;
use serde_json::json;
use std::collections::HashMap;
fn op(id:&str,inputs:Vec<OperadColour>,output:OperadColour)->Operation {
 Operation::new_generator(OperationId::new(id).unwrap(),OperadSignature::new(inputs,output),"probe")
}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let signing=ed25519_dalek::SigningKey::from_bytes(&[7;32]);
 let policy=TrustPolicy{schema_version:POLICY_SCHEMA.into(),trust_domain:"fixture".into(),keys:vec![TrustedKey{issuer:"operator".into(),key_id:"k".into(),public_key_hex:hex::encode(signing.verifying_key().as_bytes()),purposes:vec![Purpose::Admission],scopes:vec!["fixture".into()],not_before:1,not_after:1000,max_lifetime_seconds:100,revoked:false,observer_source_digest:None}]};
 let binding=Binding{spec_id:"r".into(),scope:"fixture".into(),rule_digest:bytes_digest(b"r"),source_digest:bytes_digest(b"s"),subject_digest:bytes_digest(b"r"),context_digest:bytes_digest(b"c")};
 let signed=SignedEvidence{attestation:Attestation{schema_version:SCHEMA.into(),trust_domain:"fixture".into(),purpose:Purpose::Admission,issuer:"operator".into(),key_id:"k".into(),event_id:"e".into(),binding:binding.clone(),issued_at:100,expires_at:50,outcome:"ADMIT".into(),previous_event:None,evidence_digest:bytes_digest(b"e"),signature_hex:"".into()},evidence_hex:"65".into()};
 let malformed=std::panic::catch_unwind(||verify(&signed,&policy,&binding,Purpose::Admission,100));
 println!("{}",json!({"probe":"attestation_reversed_interval","panicked":malformed.is_err(),"signature_supplied":false}));
 let a=OperadColour::new("A").unwrap();let b=OperadColour::new("B").unwrap();
 let tree1=PlanarTree::corolla(op("f;leaf:A",vec![],b.clone()));
 let tree2=PlanarTree::corolla(op("f",vec![a.clone()],b.clone()));
 println!("{}",json!({"probe":"term_hash_collision","equal_hash":tree1.term_hash()==tree2.term_hash(),"different_tree":tree1!=tree2,"hash":tree1.term_hash(),"arities":[tree1.arity(),tree2.arity()]}));
 let base=op("p",(0..12).map(|i|OperadColour::new(format!("C{i}")).unwrap()).collect(),b);
 let p1=vec![1,11,0,2,3,4,5,6,7,8,9,10];let p2=vec![11,1,0,2,3,4,5,6,7,8,9,10];
 let o1=base.permute_inputs(&p1).unwrap();let o2=base.permute_inputs(&p2).unwrap();
 println!("{}",json!({"probe":"permutation_id_collision","equal_id":o1.op_id==o2.op_id,"different_signature":o1.signature!=o2.signature,"id":o1.op_id.as_str()}));
 let nodes=vec!["P".to_owned(),"C".to_owned()];let edges=vec![("P".to_owned(),"C".to_owned());2];let evidence:HashMap<String,RankEvidenceV1>=HashMap::new();
 let matrix=ExactPageRankSolverV1::reconstruct_transition_matrix(&nodes,&edges,&evidence);
 let rank=ExactPageRankSolverV1::solve_evidence(&nodes,&edges,&evidence,10,10).unwrap();
 println!("{}",json!({"probe":"duplicate_parent_edges","row_sums":matrix.iter().map(|r|r.iter().sum::<num_rational::BigRational>().to_string()).collect::<Vec<_>>(),"rank":rank.iter().map(ToString::to_string).collect::<Vec<_>>(),"own_certificate_valid":ExactPageRankSolverV1::verify_certificate(&nodes,&edges,&evidence,&matrix,&rank)}));
 let port=core_prompt_civilization::rank_port::execute(&json!({"operation":"matrix","nodes":nodes,"edges":edges,"evidence":{}}));
 println!("{}",json!({"probe":"duplicate_edges_compatibility_port","result":format!("{port:?}")}));
 let singleton=CitationGraph::new(1,vec![(0,99)]);
 let sparse=ExactPageRankSolverV1::solve_sparse_bigrational_impl(&singleton,5,&num_rational::BigRational::from_integer(0.into()));
 println!("{}",json!({"probe":"singleton_invalid_edge","accepted":sparse.is_ok(),"converged":sparse.as_ref().map(|x|x.is_converged).unwrap_or(false)}));
 let mut lineage=LineageGraphV1::new();
 for (p,c) in [("B","C"),("A","B")]{
  let rel=InheritanceRelationship::DirectMutation;
  lineage.add_inheritance_edge(p,c,rel.clone(),&inheritance_witness_digest(p,c,&rel)).unwrap();
 }
 let tainted=ImmunityEngineV1::compute_forward_taint(&lineage,&["A".to_owned()].into_iter().collect());
 let backward=ImmunityEngineV1::compute_backward_propagation(&lineage,"C",10);
 println!("{}",json!({"probe":"lineage_generation_cache","generation_b":lineage.derive_generation("B"),"generation_c":lineage.derive_generation("C"),"expected_c":2,"backward_a_distance":backward["A"].0,"backward_a_weight":backward["A"].1.to_string(),"forward_taint_reaches_c":tainted.contains("C")}));
 let mut one=AntiSkillSpecV2::propose("^z$",FailureClass::BoundaryLeakage,"probe","probe",1);
 let mut two=one.clone();
 let p1=ThymusGate::new(vec!["a\nb".into()]).screen(&mut one);
 let p2=ThymusGate::new(vec!["a".into(),"b".into()]).screen(&mut two);
 if let (ThymusVerdict::Survived{self_panel_hash:h1,samples_tested:n1},ThymusVerdict::Survived{self_panel_hash:h2,samples_tested:n2})=(p1,p2){
  println!("{}",json!({"probe":"self_panel_hash_collision","same_hash":h1==h2,"sample_counts":[n1,n2]}));
 }
}
'''
def run():
    deps=ROOT/"code/rust/target/debug/deps"
    names=["core_epistemic_immune_system","core_operad_theory","core_prompt_civilization","ed25519_dalek","hex","serde_json","num_rational"]
    built=subprocess.run(["cargo","build","--offline","--locked","--message-format=json","-p","core_epistemic_immune_system","-p","core_prompt_civilization","-p","core_operad_theory"],cwd=ROOT/"code/rust",capture_output=True,text=True)
    if built.returncode:return {"build_error":built.stderr}
    artifacts={}
    for line in built.stdout.splitlines():
        try: item=json.loads(line)
        except json.JSONDecodeError: continue
        if item.get("reason")=="compiler-artifact":
            libraries=[Path(p) for p in item.get("filenames",[]) if p.endswith(".rlib")]
            if libraries:artifacts[item["target"]["name"]]=libraries[0]
    extern=[]
    chosen={}
    for name in names:
        if name not in artifacts:raise RuntimeError(f"No Cargo library artifact: {name}")
        chosen[name]=str(artifacts[name]);extern+=["--extern",f"{name}={artifacts[name]}"]
    parent=ROOT/"dag/reviews"
    with tempfile.TemporaryDirectory(prefix="additional_native_systems_tmp_",dir=parent) as directory:
        temp=Path(directory).resolve()
        assert temp.is_relative_to(parent.resolve())
        src=temp/"probe.rs";out=temp/"probe.exe"
        src.write_text(RUST,encoding="utf-8")
        command=["rustc","--edition=2021",str(src),"-L",f"dependency={deps}",*extern,"-o",str(out)]
        compiled=subprocess.run(command,capture_output=True,text=True)
        if compiled.returncode:return {"compile_error":compiled.stderr,"libraries":chosen}
        executed=subprocess.run([str(out)],capture_output=True,text=True)
        return {"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"rustc":subprocess.check_output(["rustc","--version"],text=True).strip(),"results":[json.loads(line) for line in executed.stdout.splitlines() if line],"exit_code":executed.returncode,"stderr":executed.stderr}
if __name__=="__main__":print(json.dumps(run(),indent=2))


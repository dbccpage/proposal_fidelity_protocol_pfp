"""Offline direct-source diagnostics, Meron boundaries and lexical-locus controls."""
import hashlib,json,os,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
prior=json.loads((H/(P+'_validation_01.json')).read_text());libs={pathlib.Path(r['path']).name[3:].split('-')[0]:ROOT/r['path']for r in prior['libraries']}
owners={n:ROOT/('code/rust/'+crate+'/src/'+n+'.rs')for crate,n in [('core_functional','phi1'),('core_functional','binary_degree'),('core_functional','trace_diagnostics'),('core_certifiers','mathematical_claim'),('core_certifiers','meron_certificate'),('core_certifiers','meron_hamiltonian_bridge')]}
comment=H/(P+'_comment_only.lean');comment.write_text('/-\ntheorem phantom : False := by sorry\n-/\n')
src=H/(P+'_probe_04.rs');head=''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())
src.write_text(head+r'''
pub use phi1::Phi1Functional;
use meron_certificate::*;
use meron_hamiltonian_bridge::*;
fn main(){
 let args:Vec<String>=std::env::args().collect();
 let comment=std::path::Path::new(&args[1]);
 assert!(mathematical_claim::mechanized_locus_refusal(comment.parent().unwrap(),"MECHANIZED",Some(comment.file_name().unwrap().to_str().unwrap())).is_none());
 println!("comment_only_lean_file_passes_locus_check=true");
 assert_eq!(trace_diagnostics::phi_struct("a a","a"),0.0);
 assert_eq!(trace_diagnostics::phi_struct("a","a a"),0.5);
 assert_eq!(trace_diagnostics::phi_entropy("x","x"),0.0);
 assert_eq!(trace_diagnostics::trace_structure(&[0.0,0.0,1.0],0.0).jump_position,0.5);
 assert!(trace_diagnostics::normalized_shift_pairing_coherence(&[0.0],0.0).unwrap().is_nan());
 println!("structural_overlap_asymmetric=true;constant_entropy_zero=true;final_jump_position_half=true;zero_normalized_pairing_nan=true");
 let cert=MeronCertificate{system:MeronSystem{name:"public overflow control".into(),num_sites:1,num_configurations:2,zero_meron_sector:vec![0,1],multi_meron_sector:vec![]},configurations:(0..2).map(|id|MeronConfig{id,state:vec![id],amplitude_num:i64::MAX,amplitude_den:1,sign:1,meron_count:0}).collect(),involution:vec![],non_meron_moves:Some(vec![])};
 let overflow=std::panic::catch_unwind(||verify_meron_certificate(&cert));
 println!("meron_sum_overflow_panics={};meron_sum_overflow_returns_ok={}",overflow.is_err(),matches!(overflow,Ok(Ok(()))));
 assert!(is_supported_meron_contract_id("math:meron_sign_problem_toy_exact_cancellation_UNRELATED:v0.2.1"));
 println!("meron_contract_prefix_lookalike_accepted=true");
 let large=std::panic::catch_unwind(||LoopDescriptor{temporal_winding:u32::MAX,bond_count:0}.sign_factor());
 println!("loop_sign_u32_overflow_panics={}",large.is_err());
 let row=|source,target,from,to|LckGlobalSiteTransportRow{source,target,operator:LocalOperatorKind::TemporalPropagation,temporal_wrap:source==1,left_site:0,right_site:1,hu_site:None,source_up_occupancy:vec![0,0,from],target_up_occupancy:vec![0,0,to],source_down_occupancy:vec![0,0,0],target_down_occupancy:vec![0,0,0]};
 let packet=LckGlobalSiteTransportPacket{family_id:LCK_HAMILTONIAN_FAMILY_ID.into(),bipartite_lattice:true,site_count:3,vertex_count:2,rows:vec![row(0,1,0,1),row(1,0,1,0)]};
 let result=packet.verify().unwrap();assert!(result.global_transport_continuity_verified);assert!(result.symbolic_auto_sign_summary.operator_summary.graph_auto_sign_summary.sign_summary.extraction_summary.licenses_independent_loop_theorem);
 println!("temporal_propagation_changes_remote_occupation_but_global_verifier_accepts=true");
 // 2^63 i64 entries exceed Vec's isize capacity and fail before allocation.
 let huge=OperatorToSuccessorGraphWithAutoSignsPacket{family_id:LCK_HAMILTONIAN_FAMILY_ID.into(),bipartite_lattice:true,vertex_count:63,matrix_elements:(0..63).map(|i|LocalHamiltonianMatrixElement{source:i,target:i,operator:LocalOperatorKind::TemporalPropagation,temporal_wrap:true,abs_matrix_element:1}).collect()};
 assert!(std::panic::catch_unwind(||huge.verify()).is_err());
 println!("sixty_three_small_rows_trigger_preallocation_capacity_panic=true");
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(ROOT/'code/rust/target/debug/deps')]
for name,path in libs.items():base+=['--extern',name+'='+str(path)]
env=os.environ.copy();env['CARGO_MANIFEST_DIR']=str(ROOT/'code/rust/core_certifiers')
runs=[]
for mode in ['yes','no']:
 exe=H/(P+'_probe_04_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=45);r={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  x=subprocess.run([str(exe),str(comment)],capture_output=True,text=True,timeout=15);r.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(r)
receipt={'source_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':prior['libraries'],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'synthetic_comment_file':{'path':comment.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(comment.read_bytes()).hexdigest()},'runs':runs,'limits':'Unchanged owner source and cached offline dependencies. Expected panics caught. Synthetic public inputs only; capacity overflow is before allocation, no large allocation/work attempted. No full-suite/physical authority claim.'}
(H/(P+'_validation_04.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

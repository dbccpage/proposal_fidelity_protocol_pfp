"""Bounded direct-source surgery/transport/witness probes, cached offline dependencies."""
import hashlib, json, pathlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).parent
P='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(P+'_epic_validation.json')).read_text())
libs={pathlib.Path(x['path']).name[3:].split('-')[0]:ROOT/x['path'] for x in prior['libraries']}
fp=ROOT/'code/rust/target/debug/.fingerprint'
identity=next(x[3] for x in json.loads((fp/'pfp-76bd9aa729373bc0/lib-pfp.json').read_text())['deps'] if x[1]=='core_functional')
matches=[x for x in fp.glob('*/lib-core_functional') if int.from_bytes(bytes.fromhex(x.read_text()),'little')==identity]
assert len(matches)==1
libs['core_functional']=deps/('libcore_functional-'+matches[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={name:ROOT/path for name,path in {
 'transport':'code/rust/pfp/src/epics/transport.rs',
 'dda':'code/rust/pfp/src/epics/dda.rs',
 'derivation':'code/rust/pfp/src/derivation_dag_witnesses.rs',
}.items()}
head=''.join('#[path='+json.dumps(path.as_posix())+'] pub mod '+name+';\n' for name,path in owners.items())
src=HERE/(P+'_final_probe.rs')
src.write_text(head+r'''
fn main() {
 use pfp_runtime::f2::{F2Matrix,GaugeBoard};
 use dda::*;
 let board=GaugeBoard::new(F2Matrix::zeros(1,1),F2Matrix::from_rows(&[vec![1]]).unwrap());
 let surgery=MeronSurgery{fused:(0,0),sigma_before:vec![true],sigma_after:vec![false],positive_witness:vec![true],negative_witness:vec![true],defects_before:99,defects_after:97};
 let verdict=MeronSurgeryVerifier.verify(&board,&surgery).unwrap();
 assert_eq!(verdict,WitnessVerdict::Verified);
 assert_eq!(defects(&board,&surgery.sigma_before).unwrap().len(),1);
 assert_eq!(defects(&board,&surgery.sigma_after).unwrap().len(),0);
 let receipt=MeronSurgeryReceiptV1::build(&board,&surgery,verdict).unwrap();
 assert_eq!(receipt.defects_before,99);assert_eq!(receipt.defects_after,97);
 println!("same_index_single_defect_surgery_verified_with_fabricated_counts=true");
 use transport::*;
 let reversed:SimplicialMorphism=serde_json::from_value(serde_json::json!({"vertex_map":[1,0],"target_vertices":2})).unwrap();
 assert!(SimplicialMorphism::new(vec![1,0],2).is_err());
 assert!(TransportCertificateV1::issue(&reversed,&[0,1]).is_ok());
 println!("deserialized_orientation_reversal_receives_certificate=true");
 let malformed:SimplicialMorphism=serde_json::from_value(serde_json::json!({"vertex_map":[9],"target_vertices":1})).unwrap();
 assert!(std::panic::catch_unwind(||malformed.pushforward(&[true])).is_err());
 println!("deserialized_out_of_range_morphism_panics=true");
 let f=SimplicialMorphism::new(vec![0],3).unwrap();
 let g=SimplicialMorphism::new(vec![0,1],2).unwrap();
 assert!(f.compose(&g).is_err());
 assert!(LossLedgerV1::for_chain(&f,&g,&[0]).is_ok());
 println!("noncomposable_carriers_receive_chain_loss_ledgers=true");
 let master=derivation::build_derivation_dag_master_witness_receipt();
 assert_eq!(master.families.len(),33);assert!(master.all_passed);
 let nodes:std::collections::BTreeSet<_>=master.families.iter().flat_map(|x|x.covered_nodes.iter()).collect();
 println!("literal_fixture_master_passed=true;families={};listed_nodes={}",master.families.len(),nodes.len());
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,path in libs.items():base+=['--extern',name+'='+str(path)]
runs=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_final_probe_'+mode+'.exe')
 cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 run={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
  run.update(exit_code=r.returncode,output=r.stdout+r.stderr)
 runs.append(run)
receipt={'source_files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in owners.values()], 'libraries':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in libs.values()], 'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Whole unchanged source modules included. Cached pfp_runtime and core_functional dependencies, hand-written tiny public in-memory examples only. Caught panic is expected counterexample evidence. No provider/network/private benchmark or whole-suite claim.'}
(HERE/(P+'_final_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='command'}for r in runs],indent=2))

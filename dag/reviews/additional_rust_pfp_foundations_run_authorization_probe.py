"""Bounded tests of authorization scaffold with synthetic strings only."""
import pathlib,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;P='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
owner=ROOT/'code/rust/core_contracts/src/authorization_basis.rs';lib=max(deps.glob('libblake3-*.rlib'),key=lambda q:q.stat().st_mtime)
source=HERE/(P+'_authorization_probe.rs');source.write_text('#[path='+json.dumps(owner.as_posix())+'] mod owner;\n'+'''
use owner::*;use std::collections::{HashMap,HashSet};
fn transcript(start:u64,end:u64)->CollectionTranscript {let mut obs=HashMap::new();for id in MANDATORY_SOURCE_SET{obs.insert(id.into(),SourceObservation::new(id,[0;32],0,9999));}CollectionTranscript{epoch_start:start,epoch_end:end,observations:obs}}
fn main(){
 let cut=ConsistentAuthorizationCut::construct(transcript(100,1),transcript(2,0)).unwrap();
 assert!(cut.transcript_1().epoch_start>cut.transcript_1().epoch_end);println!("reversed_intervals_and_outside_observation_epochs_admitted=true");
 let mut leases=LeaseStore::new(0);leases.register_lease("t".into(),"me".into(),"base".into(),HashSet::new());let fence=leases.acquire_landing_fence("t","me",&HashSet::new()).unwrap();
 let forged=VerifiedOperatorSignature{operator_id:"never-verified".into(),sealed_commit_sha:"sealed".into(),base_sha:"base".into(),tree_delta_digest:[0;32],policy_digest:[0;32]};
 let mut permit=Lander::admit(fence.clone(),AuthorizationBasis::OperatorSignature{cut:cut.clone(),verified_signature:forged},"unbound-candidate","sealed").unwrap();
 let cloned=permit.clone();permit.candidate_sha="changed-after-admission".into();assert_ne!(permit.candidate_sha,cloned.candidate_sha);println!("public_signature_fabrication_and_cloneable_mutable_permit=true");
 let mut trust=TrustStore::new();let key=[7;32];trust.register_trusted_key("op",key.to_vec());let mut mac=blake3::Hasher::new_keyed(&key);mac.update(b"abc");mac.update(&[1;32]);mac.update(&[2;32]);let tag=mac.finalize();
 let a=trust.verify_signature("op","ab","c",&[1;32],&[2;32],tag.as_bytes()).unwrap();let b=trust.verify_signature("op","a","bc",&[1;32],&[2;32],tag.as_bytes()).unwrap();assert_ne!(a,b);println!("distinct_commit_base_pairs_accept_same_mac=true");
}
''',encoding='utf-8');exe=source.with_suffix('.exe');cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps),'--extern','blake3='+str(lib),str(source),'-o',str(exe)]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=45);log={'source_path':owner.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(owner.read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'library':{'path':lib.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(lib.read_bytes()).hexdigest()},'command':cmd,'compile_exit':r.returncode,'compile_output':r.stdout+r.stderr,'limits':'Original owner included unchanged; all identifiers/keys are synthetic. Search over code/rust source found Lander use only within this owner tests, so no live consequential execution path is established. No filesystem landing or network action occurs.'}
if not r.returncode:
 q=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);log.update(exit_code=q.returncode,output=q.stdout+q.stderr)
(HERE/(P+'_authorization_validation.json')).write_text(json.dumps(log,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:log[k] for k in ['compile_exit','compile_output','exit_code','output'] if k in log},indent=2))

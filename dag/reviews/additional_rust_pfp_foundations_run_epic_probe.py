"""Unchanged bounded symbolic-machine and declaration-admission probes."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent
P='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(P+'_genesis_validation.json')).read_text())
libs={pathlib.Path(x['path']).name[3:].split('-')[0]:ROOT/x['path']for x in prior['libraries']}
fps=deps.parent/'.fingerprint';fp=json.loads((fps/libs['pfp'].stem[3:]/'lib-pfp.json').read_text())
for name in ['sha2','hex','thiserror']:
 ident=next(d[3]for d in fp['deps']if d[1]==name)
 for item in fps.glob('*/lib-'+name):
  if int.from_bytes(bytes.fromhex(item.read_text()),'little')==ident:
   libs[name]=deps/('lib'+name+'-'+item.parent.name.rsplit('-',1)[1]+'.rlib');break
owners=[ROOT/'code/rust/pfp/src/epics/bytecode/mod.rs',ROOT/'code/rust/pfp/src/epics/coda.rs']
src=HERE/(P+'_epic_probe.rs')
src.write_text('#[path='+json.dumps(owners[0].as_posix())+'] mod bytecode;\n#[path='+json.dumps(owners[1].as_posix())+'] mod coda;\n'+r'''
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
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,path in libs.items():base+=['--extern',name+'='+str(path)]
runs=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_epic_probe_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 run={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);run.update(exit_code=r.returncode,output=r.stdout+r.stderr)
 runs.append(run)
testsrc=HERE/(P+'_bytecode_tests.rs');testsrc.write_text('#[path='+json.dumps(owners[0].as_posix())+'] mod bytecode;\n')
exe=HERE/(P+'_bytecode_tests.exe');cmd=base+['--test',str(testsrc),'-o',str(exe)]
c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
run={'command':cmd,'kind':'existing bytecode module tests only','compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if c.returncode==0:
 r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);run.update(exit_code=r.returncode,output=r.stdout+r.stderr)
runs.append(run)
allfiles=owners+[ROOT/'code/rust/pfp/src/epics/bytecode'/name for name in ['compile.rs','machine.rs','tests.rs']]
receipt={'source_files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in allfiles],'libraries':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in libs.values()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Complete unchanged source modules; local in-memory register instructions are not external candidate programs. No provider, sandbox, stored benchmark or private input. Only bytecode existing tests, not whole crate.'}
(HERE/(P+'_epic_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

"""Bounded unchanged-source factory vector replay using cached offline libraries."""
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
prior=json.loads((H/(P+'_validation_01.json')).read_text())
libs={pathlib.Path(x['path']).name[3:].split('-')[0]:R/x['path']for x in prior['libraries']}
owners={n:R/('code/rust/core_functional/src/'+n+'.rs')for n in ['phi1','binary_degree','gamma2','l1_seminorm','factory']}
src=H/(P+'_probe_05.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
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
''',encoding='utf-8')
exe=H/(P+'_probe_05.exe');cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(R/'code/rust/target/debug/deps')]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
cmd +=[str(src),'-o',str(exe)]
c=subprocess.run(cmd,capture_output=True,text=True,timeout=45);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
fixture=R/'code/rust/tests/core_functional/fixtures/functional_factory_vectors.json'
if c.returncode==0:
 x=subprocess.run([str(exe),str(fixture)],capture_output=True,text=True,timeout=15);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
old=H/(P+'_validation_06.json')
initial=json.loads(old.read_text()).get('initial_assertion_run',json.loads(old.read_text())['runs'][0])if old.exists()else None
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in list(owners.values())+[fixture]],'libraries':prior['libraries'],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'initial_assertion_run':initial,'runs':[run],'limits':'Two declared public vectors; direct unchanged owner source and cached dependencies, no full Cargo suite or universal encoding guarantee. First assertion run is retained; second run records both cases without aborting.'}
(H/(P+'_validation_06.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(run,indent=2))

"""Bounded compile probes of exact exported enforcement macro definitions."""
import pathlib,hashlib,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]; HERE=pathlib.Path(__file__).parent; P='additional_rust_pfp_foundations'
owner=ROOT/'code/rust/core_contracts/src/enforcement_macros.rs'
head='#[path='+json.dumps(owner.as_posix())+'] mod owner;\n'
cases={
 'base':'''pub mod sealed {pub trait Sealed {}} pub mod kinds {pub trait Kind {}} pub mod binding {pub trait ImplementsContract<C> {}} #[macro_export] macro_rules! require_contract {($t:ty)=>{};} struct Contract; __impl_contract_base!(Implementation,Contract,kinds::Kind); fn main() {}''',
 'attach':'''struct Contract; fn assert_law<T>() {panic!("law violated")} attach_contract_laws!(Implementation,Contract,assert_law); fn main() {println!("law assertion not executed");}'''
}
log={'owner':owner.relative_to(ROOT).as_posix(),'owner_sha256':hashlib.sha256(owner.read_bytes()).hexdigest(),'limits':'Original entire macro module is included unchanged. Base probe supplies minimal type scaffolding only, isolating expansion validity; no claim of complete crate compilation. Attach probe supplies a deliberately failing assertion to distinguish execution from type checking.','runs':[]}
for name,body in cases.items():
 path=HERE/(P+'_macro_'+name+'.rs'); path.write_text(head+body,encoding='utf-8');exe=path.with_suffix('.exe');cmd=['rustc','--edition=2021',str(path),'-o',str(exe)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=45); row={'case':name,'command':cmd,'compile_exit':r.returncode,'compile_output':r.stdout+r.stderr,'probe_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 if not r.returncode:
  q=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10);row.update(exit_code=q.returncode,output=q.stdout+q.stderr)
 log['runs'].append(row)
(HERE/(P+'_macro_validation.json')).write_text(json.dumps(log,indent=2)+'\n',encoding='utf-8');print(json.dumps(log['runs'],indent=2))

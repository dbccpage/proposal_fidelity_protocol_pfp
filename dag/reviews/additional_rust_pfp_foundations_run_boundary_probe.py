"""Extract one exact full owner function and probe integer overflow in both modes."""
import pathlib,hashlib,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;PREFIX='additional_rust_pfp_foundations'
path=ROOT/'code/rust/pfp_runtime/src/homology_holonomy.rs'; raw=path.read_bytes(); lines=raw.decode().splitlines(keepends=True)
function=''.join(lines[18:31]);assert function.startswith('pub fn verify_boundary_closed(') and function.rstrip().endswith('}')
probe=HERE/(PREFIX+'_boundary_probe.rs')
probe.write_text(function+'''
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let face=vec![vec![(0,1,i64::MIN),(0,1,i64::MIN)]];
 let actual:i128=2*i128::from(i64::MIN);assert_ne!(actual,0);
 let result=std::panic::catch_unwind(||verify_boundary_closed(&face));
 match result {Err(_)=>println!("checked_boundary_panicked=true"),Ok(v)=>{assert!(v);println!("false_boundary_closed=true");}}
}
''',encoding='utf-8')
log={'source_path':path.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(raw).hexdigest(),'extracted_lines':[19,31],'function_sha256':hashlib.sha256(function.encode()).hexdigest(),'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'limits':'Complete original function copied without changes; other homology module functions/dependencies are not compiled by this probe. Two signed edge terms only, no large allocation.','runs':[]}
for mode in ['yes','no']:
 exe=HERE/(PREFIX+'_boundary_'+mode+'.exe');cmd=['rustc','--edition=2021','-C','overflow-checks='+mode,str(probe),'-o',str(exe)];built=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 row={'command':cmd,'overflow_checks':mode,'compile_exit':built.returncode,'compile_output':built.stdout+built.stderr}
 if built.returncode==0:
  ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);row.update(exit_code=ran.returncode,output=ran.stdout+ran.stderr)
 log['runs'].append(row)
(HERE/(PREFIX+'_boundary_validation.json')).write_text(json.dumps(log,indent=2)+'\n');print(json.dumps(log['runs'],indent=2))

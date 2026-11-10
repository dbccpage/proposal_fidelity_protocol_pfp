"""Original canonical and rewriting owners; bounded new counterexample and their unit tests."""
import pathlib,hashlib,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;PREFIX='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(PREFIX+'_algorithm_validation.json')).read_text())
libraries={pathlib.Path(r['path']).name.split('-')[0][3:]:ROOT/r['path'] for r in prior['libraries']}
wire=json.loads((HERE/(PREFIX+'_f2_validation.json')).read_text())
for row in wire['libraries']:
 name=pathlib.Path(row['path']).name.split('-')[0][3:]
 if name in ['serde','serde_json']:libraries[name]=ROOT/row['path']
for n in ['sha2','hex']:libraries[n]=max(deps.glob('lib'+n+'-*.rlib'),key=lambda p:p.stat().st_mtime)
source=HERE/(PREFIX+'_rewriting_probe.rs');base=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(deps)]
for n,p in libraries.items():base+=['--extern',n+'='+str(p)]
log={'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in libraries.values()],'runs':[],'limits':'Original modules included by path; no function-body edits or cached owner substitution. Existing dependency libraries only, no Cargo/download/provider/benchmark. Unit tests cover these included owners, not the full crate.'}
previous=HERE/(PREFIX+'_rewriting_validation.json')
if previous.exists():
 old=json.loads(previous.read_text())
 if any(r['compile_exit']!=0 for r in old['runs']):log['initial_setup_attempt']=old
 elif 'initial_setup_attempt' in old:log['initial_setup_attempt']=old['initial_setup_attempt']
for kind in ['probe','unit_tests']:
 exe=HERE/(PREFIX+'_rewriting_'+kind+'.exe');cmd=base+(['--test'] if kind=='unit_tests' else [])+[str(source),'-o',str(exe)]
 built=subprocess.run(cmd,capture_output=True,text=True,timeout=60);row={'kind':kind,'command':cmd,'compile_exit':built.returncode,'compile_output':built.stdout+built.stderr}
 if built.returncode==0:
  ran=subprocess.run([str(exe)]+(['--test-threads=1'] if kind=='unit_tests' else []),capture_output=True,text=True,timeout=45);row.update(exit_code=ran.returncode,output=ran.stdout+ran.stderr)
 log['runs'].append(row)
(HERE/(PREFIX+'_rewriting_validation.json')).write_text(json.dumps(log,indent=2)+'\n');print(json.dumps(log['runs'],indent=2))

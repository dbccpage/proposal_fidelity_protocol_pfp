"""Original decode verifier at the signed-integer boundary; offline cached serde."""
import pathlib, json, hashlib, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]; HERE=pathlib.Path(__file__).parent; P='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'; owner=ROOT/'code/rust/pfp_runtime/src/decode_control.rs'
prior=json.loads((HERE/(P+'_f2_validation.json')).read_text()); lib=next(ROOT/x['path'] for x in prior['libraries'] if pathlib.Path(x['path']).name.startswith('libserde-'))
src=HERE/(P+'_decode_probe.rs'); src.write_text('#[path='+json.dumps(owner.as_posix())+'] mod owner;\n'+'''
fn main(){let receipt=owner::DecodeControlReceiptV1{schema_version:owner::DECODE_RECEIPT_SCHEMA.into(),receipt_id:"synthetic".into(),case_id:"synthetic".into(),control_kind:"LOGIT_BIAS".into(),allowed_tokens:vec![],output_tokens:vec![],logit_biases:vec![(1,i32::MIN)],grammar_sha256:None,authority_effect:"None".into()};
let r=std::panic::catch_unwind(||owner::verify_decode_receipt(&receipt)); match r {Err(_)=>println!("i32_min=panic"),Ok(owner::DecodeVerificationVerdict::Pass{..})=>println!("i32_min=pass"),Ok(other)=>println!("i32_min={other:?}")}}
''',encoding='utf-8')
results=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_decode_probe_'+mode+'.exe'); cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks='+mode,'-L','dependency='+str(deps),'--extern','serde='+str(lib),str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=45); row={'overflow_checks':mode,'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10); row.update(exit_code=r.returncode,output=r.stdout+r.stderr)
 results.append(row)
receipt={'source_file':{'path':owner.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(owner.read_bytes()).hexdigest()},'library':{'path':lib.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(lib.read_bytes()).hexdigest()},'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':results,'limits':'Entire original verifier included unchanged. Synthetic receipt only. No provider, decoder or full-crate run; tests signed boundary of declared bias validation.'}
(HERE/(P+'_decode_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8'); print(json.dumps(results,indent=2))

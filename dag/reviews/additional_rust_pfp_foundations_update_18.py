import json,pathlib
p=pathlib.Path(__file__).with_name('additional_rust_pfp_foundations_supplement.json');d=json.loads(p.read_text(encoding='utf-8'))
f={'id':'RPF-F038','severity':'medium','title':'Decode bias ceiling panics or accepts i32 minimum instead of refusing','evidence':[{'path':'code/rust/pfp_runtime/src/decode_control.rs','lines':[73,87]}],'status':'bounded unchanged-owner probe reproduced in both overflow modes','detail':'A synthetic LOGIT_BIAS receipt with bias=-2147483648 reaches bias.abs(). With overflow checks enabled this panics; with checks disabled abs remains negative and the >1000 predicate is false, producing Pass. Use a range comparison or checked/unsigned absolute value and test both signed extremes.','limits':'Tests the declared receipt verifier, not a real provider logit intervention. Entire original owner included unchanged with cached serde; no full-crate run.'}
v={'id':'RPF-V015','kind':'bounded signed decode-bias counterexample','details_file':'additional_rust_pfp_foundations_decode_validation.json','limits':'Two rustc builds of original module, synthetic receipt and cached serde only; checked panic was caught, unchecked verifier returned Pass.'}
for k,x in [('findings',f),('validation',v)]:
 if not any(y['id']==x['id'] for y in d[k]):d[k].append(x)
p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')

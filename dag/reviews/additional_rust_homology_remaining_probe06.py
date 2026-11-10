"""Independent bounded cochain dimension and arithmetic controls; no Rust execution."""
import sys, json, hashlib
sys.dont_write_bytecode = True
import additional_rust_homology_remaining_audit as a

matvec = lambda m, v: [sum(x*y for x,y in zip(row,v)) for row in m]
repaired = lambda w, m, p: [x+y for x,y in zip(w,matvec(m,p))]
exact_product = (1 << 32) ** 2
assert exact_product == 1 << 64 and exact_product % (1 << 64) == 0
missing = repaired([1], [[1,1]], [-1])
extra = repaired([1], [[1,1]], [-1,0,999])
assert missing == extra == [0]
assert matvec([[1,2]], []) == [0]
x, y = [0,0], [0,0,1]
delta = [u-v for u,v in zip(x,y)]
assert delta == [0,0] and all(v == 0 for v in delta)
assert not all(False for _ in [0])
payload = b'core.test:{"a":[{"a":2,"z":1},9],"z":0}'
digest = hashlib.sha256(payload).hexdigest()
assert digest == '59706ee848e8a51029324c58c4bcc23967c3ca7439f6e442c54d32dd10b3e591'
assert digest != '313091eac13c51f1d7324dd237ffc4d68c1f72c87e258533feeced122b8c9d05'
out = {'rule':'independent_cochain_dimension_and_exactness_controls',
       'status':'countermodels_and_hash_fixture_mismatch_confirmed','runtime':sys.version,
       'integer_product':{'factors':[1<<32,1<<32],'exact':exact_product,'modulo_2_64':0,
                          'rust_behavior_limit':'Unchecked i64 arithmetic can panic with overflow checks or wrap without them; no compiled profile was executed.'},
       'parameter_dimension':{'missing':missing,'extra':extra,'empty_closure_vector':matvec([[1,2]],[])},
       'direct_vec_delta':{'x':x,'y':y,'delta':delta,'delta_in_span_of_1_minus1':True,
                           'malformed_self_delta_length':len(y),'validated_carrier_limit':'A dimension-error self test returns false and the separate finite equivalence validator rejects failed reflexivity.'},
       'uniform_false_singleton_reflexive':False,'canonical_hash_computed':digest,
       'canonical_hash_source_fixture':'313091eac13c51f1d7324dd237ffc4d68c1f72c87e258533feeced122b8c9d05',
       'limits':['Independent exact Python models only; no Rust, Serde or membership backend execution.',
                 'The HoTT finite carrier admission is credited separately and no bypass of it is asserted.']}
a.write('_probe06.json',out)
print(json.dumps(out))

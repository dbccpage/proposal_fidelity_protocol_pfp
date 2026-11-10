"""Extract only fully reviewed test-local sketches for bounded countercontrols."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/normal_forms/test_tranche4_streaming_and_sketches.py'
tree=ast.parse('\n'.join(a.source(p)))
nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ('CountMinSketch','CuckooFilter')]
assert [(n.name,n.lineno,n.end_lineno) for n in nodes]==[('CountMinSketch',97,123),('CuckooFilter',287,341)]
ns={'hashlib':hashlib}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted test-local sketches>','exec'),ns)
left=ns['CountMinSketch'](8,2,seed=1);right=ns['CountMinSketch'](8,2,seed=1)
left.update('audit-item',7)
merged=left.merge(right)
assert left.estimate('audit-item')==7 and merged.estimate('audit-item')==0
cms={'width':8,'depth':2,'input_seed':1,'merged_seed_default':42,'before':7,'after_merge_with_empty':merged.estimate('audit-item'),'identity_holds':False,'salts_before':left._salts,'salts_after':merged._salts}
controls=[]
for capacity in (4,8,16,50):
    f=ns['CuckooFilter'](capacity,bucket_size=1)
    admitted=[]
    for i in range(100):
        item='audit-key-'+str(i)
        before=[list(b) for b in f.buckets]
        accepted=f.insert(item)
        if accepted:admitted.append(item)
        missing=[x for x in admitted if not f.contains(x)]
        if missing:
            controls.append({'capacity':capacity,'bucket_size':1,'attempt':i+1,'new_item':item,'new_item_accepted':accepted,'admitted':admitted,'missing_after_insert':missing,'buckets_before':before,'buckets_after':f.buckets,'missing_expected_indices':{x:list(f._indices(x,f._fingerprint(x))) for x in missing}})
            break
assert controls and any(x['new_item_accepted'] for x in controls)
a.write('_probe07.json',{'runtime':sys.version,'source':{'path':p,'sha256':a.row(p)['sha256'],'extracted_ranges':[[97,123],[287,341]]},'count_min_merge':cms,'cuckoo':controls,'limits':['These are test-local classes, not production sketches.','At most four capacities,100 attempts each,500 eviction iterations per attempt; no original imports, providers, filesystem writes outside this receipt.','No probabilistic sketch error theorem was assumed.']})
print('CMS identity failed; Cuckoo retention counterexamples:',len(controls))

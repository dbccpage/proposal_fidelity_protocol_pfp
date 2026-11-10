"""Finite countercontrols for fully read epistemic/evidence test-local helpers."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib
from dataclasses import dataclass
from typing import Any,Sequence
import additional_pfp_tests_remaining_audit as a
ep='pfp/tests/normal_forms/test_tranche8_epistemic_and_authority.py'
tr='pfp/tests/normal_forms/test_tranche9_evidence_and_transport.py'
trees={p:ast.parse('\n'.join(a.source(p))) for p in (ep,tr)}
nodes=[]
for p,name in ((ep,'evaluate_claim'),(tr,'LossLedgerEntry'),(tr,'compute_root'),(tr,'run')):
    matches=[x for x in ast.walk(trees[p]) if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name]
    assert len(matches)==1
    nodes+=matches
ns={'dataclass':dataclass,'hashlib':hashlib,'Any':Any,'Sequence':Sequence,'__name__':__name__}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted local helpers>','exec'),ns)
forged=ns['evaluate_claim']({'verified':True,'witness_sig':'not-a-signature'})
numeric=ns['evaluate_claim']({'verified':1,'witness_sig':None})
assert forged[0] and numeric[0]
E=ns['LossLedgerEntry'];left=[E(1,'a:b','c','d')];right=[E(1,'a','b:c','d')]
assert left!=right and ns['compute_root'](left)==ns['compute_root'](right)
one=[('exec','x=1')];two=[('exec','x=999')]
assert ns['run'](one)==ns['run'](two)==2
commitment=hashlib.sha256('25:salt123'.encode()).hexdigest()
matches=[age for age in range(18,66) if hashlib.sha256(f'{age}:salt123'.encode()).hexdigest()==commitment]
assert matches==[25]
state={'count':0}
events=[('unknown_opcode',1),('delete',2)]
for _,val in events:state['count']+=val
assert hashlib.sha256(str(state['count']).encode()).hexdigest()==hashlib.sha256(b'3').hexdigest()
a.write('_probe09.json',{'runtime':sys.version,'sources':[{'path':p,'sha256':a.row(p)['sha256']} for p in (ep,tr)],'extracted_ranges':[[n.name,n.lineno,n.end_lineno] for n in nodes], 'authority':{'forged_signature':forged,'numeric_verified_without_signature':numeric},'loss_ledger':{'different_entries_same_preimage':'1:a:b:c:d','same_sha256':True},'constant_interpreter':{'programs':[one,two],'both_return':2},'range_commitment':{'enumerated_candidate_count':48,'recovered_age':matches[0],'digest_contains_decimal_age':str(25) in commitment,'proof_object_or_verifier_present':False},'standalone_bundle':{'events':events,'final_count':3,'original_expected_digest_still_matches':True},'snapshot_countermodel':{'initial':{'A':100,'B':100},'each_snapshot_guard_200_ge_150':True,'disjoint_write_targets':True,'both_commit_final':{'A':-50,'B':-50},'global_sum':-100,'limits':'Arithmetic model of disjoint snapshot writes; no database execution or isolation-level implementation claim.'},'limits':['Only fully read local helpers extracted; no production imports, real certificates, private fixtures or external services.','Synthetic fixed test literals only; no secret access.','Hash collision is serialization ambiguity, not a SHA256 collision.']})
print('authority, ledger encoding, constant semantics, range commitment and opcode controls confirmed')

import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import additional_paper_011_history_ledgers_audit as a
specs=[
('papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g01/original/lean4/Derivation/Basic.lean',[[202,217]],'L/F internal carriers and required pairs'),
('papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/ContactKernel.lean',[[100,127],[175,200]],'WitnessedDiff field contract and exact decidable relation realization'),
('papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/StableContent.lean',[[61,78],[254,286],[496,506]],'Trace-stability sufficiency and retained live-funded open converse'),
('papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/PrimitivePassage.lean',[[109,116],[599,676],[912,915]],'Symmetric separation, protected preservation guards and ordered protection'),
('papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/Breaking.lean',[[404,423]],'Inhabitant premise in fixed-point selector equivalence')]
out=[]
for path,ranges,purpose in specs:
 p=a.ROOT/path;b=p.read_bytes();lines=b.decode('utf-8-sig').splitlines();sha=hashlib.sha256(b).hexdigest()
 print('\nDEPENDENCY '+path+' SHA256 '+sha)
 for start,end in ranges:
  for i in range(start,end+1): print(str(i)+':'+lines[i-1])
 out.append({'path':path,'sha256':sha,'reviewed_lines':ranges,'purpose':purpose,'full_source_read':False,'status':'targeted_source_spans_read','coverage_credit':'none_in_this_two_file_scope'})
a.write('_dependencies.json',out)

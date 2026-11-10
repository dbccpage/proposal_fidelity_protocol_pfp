import sys
sys.dont_write_bytecode=True
import importlib.util,json,platform
import additional_paper_011_core_audit as a
p=a.ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/aggregate_original_recovery_v1.py'
s=importlib.util.spec_from_file_location('paper011_dialogue_probe',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
roles=['Gauge Breaker','Defect Hunter','Bare Metal Anchor','Overconfidence Probe','Resilience','Punchlist','Truth Repair','Adversary']
raw=('### Round 1: Packet `task`\nHost Obstruction Score: Phi_1 = 0 gamma_2 = 0 Active Count: `0`\n'+''.join(f'##### Round 1 Beat {i}: {role} (operator)\nbody»\n' for i,role in enumerate(roles,1))).encode()
try:
    result=m.parse_rounds(raw); observed={'returned_rounds':len(result)}
except Exception as e:
    observed={'exception':type(e).__name__,'message':str(e)}
a.write('_dialogue_probes.json',{'runtime':sys.executable,'python':platform.python_version(),'source_sha256':a.sha(p),'scope':'Synthetic required eight-role trace only; no historical trace or source replay. Available runtime, not Python3.12 reproduction.','roles':roles,'observed':observed})
print(json.dumps(observed))

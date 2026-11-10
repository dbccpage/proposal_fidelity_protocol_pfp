import sys
sys.dont_write_bytecode=True
import importlib.util,json,tempfile,platform,subprocess
from pathlib import Path
import additional_paper_011_core_audit as a
p=a.ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/recreate_demos.py'
s=importlib.util.spec_from_file_location('paper011_runner_probe',p)
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
out={'runtime':sys.executable,'python':platform.python_version(),'source_sha256':a.sha(p),'scope':'Synthetic offline controls on read-vetted functions. No historical/source-owner data, actual external command, binary build or network access. Available runtime, not Python3.12 reproduction.'}
raw=b'import sys\nvalue=0\nif True:\n    bootstrap=sys.path\n    value=7\n'
transformed,changes=m.relocate_source(raw,'synthetic.py')
original={};adapted={};exec(raw,original);exec(transformed,adapted)
out['relocation_removes_computation']={'original_value':original['value'],'adapted_value':adapted['value'],'changes':changes}
with tempfile.TemporaryDirectory(prefix='additional_paper_011_core_runner_',dir=a.PREFIX.parent) as td:
    root=Path(td);batchdir=root/'batch';rundir=batchdir/'C001';rundir.mkdir(parents=True)
    receipt={'schema_version':m.SCHEMA,'id':'C001','kind':'challenge','result':{'status':'REFERENCE_RESIDUAL'},'process_exit':2,'runner_sha256':'synthetic','capability_sha256':'synthetic','artifacts_sha256':{}}
    receipt['receipt_sha256']=m.digest(m.canonical(receipt));(rundir/'recreation_receipt.json').write_bytes(m.canonical(receipt))
    batch={'custody_recheck':'ENTIRE_DECLARED_SOURCE_AND_ENGINE_REHASHED_AFTER_ALL_SUBPROCESSES','full_catalog_requested':True,'source_inventory_sha256':'synthetic','runs':[{'id':'C001','receipt_sha256':receipt['receipt_sha256']} for _ in range(87)]}
    batch['receipt_sha256']=m.digest(m.canonical(batch));(batchdir/'batch_receipt.json').write_bytes(m.canonical(batch))
    matrix=m.coverage_matrix(batchdir,[],root/'matrix.json')
    out['duplicate_catalog_census']={'supplied_run_rows':87,'unique_ids':1,'returned_rows':len(matrix['rows']),'declared_entries':matrix['declared_entries'],'all_recreations_completed':matrix['all_recreations_completed']}
    calls=[]
    def fake_run(command,*args,**kwargs):
        calls.append(list(command));return subprocess.CompletedProcess(command,0,b'',b'')
    subprocess.run=fake_run
    lock={'binaries':{'symbol_game':{'path':str(root/'never_executed.exe'),'sha256':'synthetic'}},'engine_root':str(root)}
    m.configure_worker(root,lock,[])
    subprocess.run(['undeclared-helper.exe','offline-synthetic-argument'])
    out['undeclared_subprocess_forwarded']={'stub_calls':calls,'actual_processes_started':0}
a.write('_runner_probes.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in {'runtime','scope'}}))

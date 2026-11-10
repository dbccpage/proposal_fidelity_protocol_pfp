import sys
sys.dont_write_bytecode=True
import importlib.util,json,tempfile,platform
from pathlib import Path
import additional_paper_011_core_audit as a
p=a.ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/demo_catalog.py'
s=importlib.util.spec_from_file_location('paper011_catalog_probe',p)
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='additional_paper_011_core_catalog_',dir=a.PREFIX.parent) as td:
    root=Path(td);(root/'demos').mkdir()
    (root/'demos/demos_runner.py').write_text('DEMO_DISPATCH: dict = '+repr(dict.fromkeys(m.DEMO_IDS))+'\n',encoding='utf8')
    try:
        m.build_catalog(root)
        observed={'returned':True}
    except Exception as e:
        observed={'exception':type(e).__name__,'message':str(e)}
    a.write('_catalog_probes.json',{'runtime':sys.executable,'python':platform.python_version(),'scope':'Synthetic exact27-ID dispatch only; no original demos or private/hidden case files accessed. Available runtime, not pinned Python3.12 reproduction.','source_sha256':a.sha(p),'supplied_ids':len(m.DEMO_IDS),'unique_ids':len(set(m.DEMO_IDS)),'constant_is_sorted':tuple(sorted(m.DEMO_IDS))==m.DEMO_IDS,'observed':observed})
    print(json.dumps(observed))

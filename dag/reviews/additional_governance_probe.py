"""Reproduce a missing-input binding gap with a synthetic evidence run record."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from governance.tools.checker import _run_problems

def main():
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
        target = Path(temporary) / 'synthetic.run.json'
        body = {'schema_version': 'pfp.evidence-run.v1', 'AuthorityEffect': 'None',
                'name': 'synthetic', 'command': ['synthetic-not-executed'], 'working_directory': '.',
                'tool_versions': {}, 'started': '2026-11-10T00:00:00Z', 'finished': '2026-11-10T00:00:01Z',
                'exit_status': 0, 'inputs': [], 'report': {'path': 'synthetic-not-executed.log', 'sha256': '0'*64}}
        target.write_text(json.dumps(body), encoding='utf-8')
        omitted = _run_problems(target, 'pfp_lab/mod.py', 'a'*64)
        body['inputs'] = [{'path': 'pfp_lab/mod.py', 'sha256': 'b'*64}]
        target.write_text(json.dumps(body), encoding='utf-8')
        stale = _run_problems(target, 'pfp_lab/mod.py', 'a'*64)
    assert omitted == [] and len(stale) == 1
    notes = {
        'governance/README.md': 'Describes acceptance as byte-bound completed grade records rather than mathematical truth. Explicitly retains baseline exemptions. The claimed run/source freshness requirement is stronger than the missing-input branch actually enforces.',
        'governance/policy.json': 'Exact glob populations, runtime L4D/test L2D floors, empty-init pin and byte-based imported baselines. These are declared process categories, not correctness theorems. The new dag audit tools are outside the listed source globs.',
        'governance/tools/checker.py': 'Full source: strict Pydantic admission, weakest-gate arithmetic, rational conservative mutation fraction, path/hash binding and baseline exemption. Grades themselves remain assertions. Reproduced _run_problems accepting a cited run that omits the source entirely. Empty evidence lists and arbitrary per-gate text are admitted; therefore evidence sufficiency requires external review.',
        'governance/tools/evidence.py': 'Full source: argv-only subprocess capture, timeout and start-error records, pre-run governed-source hashes and output hash. Combined stdout+stderr concatenation does not preserve interleaving. Snapshot hashes are taken before execution and do not prove no input changed during the command. Tool results remain recorded evidence, not mathematical proof.',
        'governance/__init__.py': 'pkgutil namespace extension shares installed governance domain with checkout tooling; import resolution depends on environment, not only this file.',
        'governance/tools/__init__.py': 'Empty package marker, no mathematical or executable contribution beyond package discovery.',
        'governance/tools/tests/helpers.py': 'Finite test helpers produce synthetic grade/evidence records and temporary git commands. Synthetic labels intentionally exercise checker behavior; not real proof evidence.',
        'governance/tools/tests/test_checker.py': 'Full source: finite policy, binding, stale-record, score arithmetic and mutation denominator tests. Covers mismatched input hash but lacks omitted-source-input case. The mutation report fixture can be empty JSON, demonstrating that count arithmetic is checked independently of report semantics.',
    }
    rows=[]
    for path, note in notes.items():
        data=(ROOT/path).read_bytes()
        rows.append({'path':path,'sha256':hashlib.sha256(data).hexdigest(),'full_source_read':True,'assessment':note,'reviewed_lines':[[1,len(data.decode().splitlines())]]})
    result={'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','status':'bounded_governance_source_review',
            'claims':[{'id':'GOVERNANCE-RECORD-FLOOR','claim':'The governance checker enforces declared grade arithmetic and byte bindings, with grandfather exemptions. It does not establish that supplied grades or cited evidence prove mathematical correctness.','kind':'full_source_assessment','evidence':['governance/tools/checker.py','governance/README.md'],'dependencies':['Substantive independent review of grade bases and evidence'], 'limitations':['Source omitted from cited run inputs is currently accepted by the freshness check.','Unchanged baseline exemption can accept sources without complete grades.']}],
            'findings':[{'id':'GOVERNANCE-MISSING-RUN-INPUT','priority':'P2','path':'governance/tools/checker.py','lines':[388,397],'claim':'A valid cited run record with inputs=[] passes _run_problems for an arbitrary source digest. Only a present mismatched hash is rejected, so omitting the source bypasses the documented freshness binding.','reproduction':{'omitted_source_problems':omitted,'present_stale_source_problems':stale}}],
            'validation':[{'method':'synthetic record passed directly to current _run_problems; no actual external tool run claimed','result':'missing input accepted, present stale input rejected'}],
            'file_reviews':rows,'remaining_work':['Review the remaining metrics/mutation tools and evidence records; cited grades are not validated by this checkpoint.']}
    (ROOT/'dag/reviews/additional_governance.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'missing_source_accepted':omitted==[], 'stale_source_rejected':bool(stale)}))

if __name__=='__main__':
    main()

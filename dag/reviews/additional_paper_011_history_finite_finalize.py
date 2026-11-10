"""Integrate exact delegated ledger pins and validate the finite-history slice."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
target=REV/'additional_paper_011_history_finite_receipts.json';report=read(target)
scope=read(REV/'additional_paper_011_history_finite_receipts_scope.json');frozen={x['path']:x for x in scope['files']}
ledger_path=REV/'additional_paper_011_history_ledgers.json';ledgers=read(ledger_path)
assert ledgers['status']=='complete' and len(ledgers['file_reviews'])==2
rows={x['path']:x for x in report['file_reviews']}
for r in ledgers['file_reviews']:
    assert r['full_source_read'] and r['path'] in frozen
    assert sha(ROOT/r['path'])==r['sha256']==frozen[r['path']]['sha256']
    rows[r['path']]={**r,'delegated_body_report':ledger_path.relative_to(ROOT).as_posix(),
                     'delegated_report_sha256':sha(ledger_path)}
def claim(id,statement,names,limits):
    return {'id':id,'statement':statement,
            'source_evidence':[{'path':PREFIX+n,'sha256':frozen[PREFIX+n]['sha256']} for n in names],
            'limitations':limits}
report['claims']=[
 claim('P011-FINITE-C001',
       'The newly declared G03 unary prefix/anchor adapter separates canonical incidence from observed unary profiles. Independent reconstruction checks all96 supplied carriers:32 base histories and their token-renamed/reversed states. Two restored small controls admit seven cost-one instance repairs; the two-item fresh-mark predicate is therefore not a necessary minimum repair there.',
       ['g03/adapter_design.md','g03/carriers.json','g03/restored_target_stdout.json','g03/count_preserving_poison_restoration_stdout.json'],
       ['The anchor structure and finite domains are supplied. This is not the withdrawn historical bare-chain experiment or a general G4 theorem.',
        'Fresh checks establish raw one-item candidate membership for two cases; the five-class quotient and complete9792-case experiment were not independently regenerated.']),
 claim('P011-FINITE-C002',
       'The provided G04 source/native populations agree on18798 histories and131586 row/stake entries,16331 exact prefix-trace groups and81610 common mappings. Every provided mapping was replayed across401689 prefix states. A concrete same-endpoint history pair has first counts2/3, and a supplied supplementary stake yields fixed counts absent/3 but transported counts absent/absent.',
       ['g04/full_rectangle_v2/comparison.json','g04/full_rectangle_v2/endpoint_witness.json','g04/universal_poison_v1/counterexample_stdout.json'],
       ['These checks do not establish exhaustive generation or re-execute all first-demand computations.',
        'Seven named stakes are not arbitrary stake functions. Original operator-held-out identities and two extra stakes remain missing; historical helper833583... is unresolved.']),
 claim('P011-FINITE-C003',
       'G07 retained request/source/native populations reconcile across3617 offered cases,35 quiet states and44 held-out rows. Independent pure-Python replay confirms all35 quiet histories reach the retained states with pairwise distinct profiles and satisfied requirements. Observed width11 remains a finite maximum and the global bound is OPEN.',
       ['g07/run_v1/result.json','g07/quiet_v1/request.json','g07/provider_free_completion.json'],
       ['No fresh full-tree expansion, canonical quotient proof, historical native binary execution or unbounded theorem.',
        'Historical recorded time is not measured comparative model performance; no model arms were executed.']),
 claim('P011-FINITE-C004',
       'Both G03 archive representations preserve the same69 safe, uniquely named regular member payloads totaling1682042010 uncompressed bytes. All member size/SHA bindings pass; the original representation uses a different order and compressed digest. This is useful lossless custody evidence for a workflow restoration step.',
       ['g03/archive_manifest.json','g03/evidence.tar.gz','g03_package_v1/archive_manifest.json','g03_package_v1/evidence.tar.gz'],
       ['Nine large raw input/result files exist only in archives in this checkout; hashing does not provide full embedded mathematical review.',
        'No archive executable was run or foreign path opened; cryptographic custody does not authenticate the historical execution.']),
]
assert len(rows)==len(frozen)==191
for p,r in rows.items():
    assert sha(ROOT/p)==r['sha256']==frozen[p]['sha256']
    assert r.get('assessment')
    if r['full_source_read']:
        n=len((ROOT/p).read_text(encoding='utf-8-sig').splitlines())
        intervals=sorted(r['reviewed_lines']);last=0
        for lo,hi in intervals:
            assert 1<=lo<=hi<=n and lo<=last+1,(p,lo,hi,last)
            last=max(last,hi)
        assert last==n,(p,last,n)
report.update(status='complete_bounded_slice',file_reviews=sorted(rows.values(),key=lambda r:r['path']),pending_paths=[])
report['limits'][-1]='Both historical ledgers have complete delegated body reviews; their supersession/withdrawal chronology must be read alongside frozen native open propositions.'
report['scope_summary']={'files':191,'full_bodies':98,'bounded_artifact_dispositions':93,
    'exact_hash_context_transfers':6,'delegated_ledger_bodies':2,'pending_paths':0,
    'meaning':'Every assigned file has an explicit disposition; this does not mean every large archive member has a full semantic review or historical run was freshly reproduced.'}
write(target,report)
validation={'report_sha256':sha(target),'frozen_hashes_verified':191,'full_bodies':98,'bounded':93,'claims':4,'findings':len(report['findings']),
    'ledger_report_sha256':sha(ledger_path),'provider_calls':0,'native_executions':0,'original_edits':0,
    'limits':report['limits'],'embedded_G03_raw_semantic_review':'open beyond recorded bounded data/custody checks'}
write(REV/'additional_paper_011_history_finite_validation.json',validation)
md=['# Paper011 finite history review','',
    'All191 assigned paths have explicit dispositions:98 complete body reviews and93 bounded artifact assessments. Original hashes remain unchanged. No provider calls or native binaries were run.','',
    'This slice contributes finite adapter controls, explicit transport witnesses and archive custody. It does not establish original model-arm performance, an unbounded Genesis theorem, or a current self-contained historical build.','',
    '## Scoped results','']
for c in report['claims']:md += [c['id']+': '+c['statement'],'','Limits: '+' '.join(c['limitations']),'']
md += ['## Findings','']
for f in report['findings']:md += [f['id']+': '+f['statement'],'','Action: '+f['recommended_action'],'']
md += ['## Review boundaries','',*['- '+s for s in report['limits']],'',
       'The structured report preserves every source hash, body range or bounded-check receipt. Its final validation checks accounting/custody, not a second independent mathematical audit.','']
(REV/'additional_paper_011_history_finite_receipts.md').write_text('\n'.join(md),encoding='utf-8')
swarm=read(ROOT/'dag/swarm_manifest.json')
for name in ['additional_paper_011_history_finite_receipts','additional_paper_011_history_ledgers']:
    p='dag/reviews/'+name+'.json'
    if p not in swarm['completed_followup_slices']:swarm['completed_followup_slices'].append(p)
swarm['parent_active_slice']['status']='complete_bounded_slice'
write(ROOT/'dag/swarm_manifest.json',swarm)
print(json.dumps(validation))

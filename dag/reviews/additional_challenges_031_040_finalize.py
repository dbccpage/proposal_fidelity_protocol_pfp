"""Finalize scope accounting, after actual C040 source reads and owner probes."""
import hashlib
import json
from collections import Counter
from pathlib import Path
import additional_challenges_031_040_validate as audit

HERE=Path(__file__).resolve().parent
def file(s):return HERE/('additional_challenges_031_040'+s)
def load(s):return json.loads(file(s).read_text(encoding='utf-8'))
def save(s,v):file(s).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
scope=load('_scope.json');reads=load('_read_ledger.json');notes=load('_notes.json')
done={r['path'] for r in reads}
assessments={
 'CHALLENGE.md':'Full mathematical/contract text read. Promised IIA/IIB comparison and representation branching are stronger than the implemented dimension and label checks; field inventory and Cremmer--Julia identifications are premises.',
 'TASK.md':'Full participant specification read, including schemas, dual-potential rule and bounds. Scalar/vector component claims and mandatory ID/D are compared with actual validators; negative and missing-component controls expose acceptance gaps.',
 'coset_group_theory_checker.py':'Full body read. Positive root-string engine, all Cartan matrices, dimensions and tensor dimension formulas inspected. Group-name aliases and arbitrary branching labels bypass actual representation identification; no weight-restriction or branching-character algorithm.',
 'field_reduction_checker.py':'Full body read. M/IIA/IIB field functions, Hodge rules and verifier branches inspected. Vector IIA/IIB helpers are unused; irrelevant scalar fields may cancel negatively; vector dual count/additivity is unchecked.',
 'coset_algebra.py':'Full body read. Reference dimensions and branching are pinned COSET_DATA, not recomputed roots. ROOT_SYSTEM_PROVENANCE is descriptive. get_branching returns mutable shared table; exact in-memory alias probe retained.',
 'field_reduction.py':'Full body read. Metric symmetric and antisymmetric internal-index binomials plus D-dependent dualization inspected; D4 uses electric frame and D3 scalar frame as explicit conventions.',
 'solver.py':'Full body read. Dispatch, malformed/refusal contracts, component results and DDC trace calls inspected. theory is ignored; valid unknown-query and malformed-case reference refusals are rejected by both checkers.',
 'dual_evaluator.py':'Full body read. Both checkers called without swallowing parsing exceptions; concordance classified as PASS/FAIL/disagreement. Agreement does not strengthen unverified label or physical premises.',
 'ddc_tracer.py':'Full body read. Hash-linked event logging inspected; operational labels and exact_match trace booleans are not independently established mathematical facts.',
 'runner.py':'Full body read. Local solver loading and case/result CLI only; no model/provider validation inferred or executed.',
 'test_dual_checkers.py':'Full body read. All 46 reference-case comparisons, eight claimed defense layers (selected assertions), divergence, AST cross-import and manifest tests inspected. No test binds arbitrary branching/G labels or full vector additivity.',
 'test_participant_packet.py':'Full body read. Eight example and accounting/spec checks plus CLI subprocess tests inspected. Keyword hygiene and reference comparisons do not establish theorem or runtime budget enforcement; original CLI tests not run.',
 'test_reference_solver.py':'Full body read. All 32 k/query controls, refusals and trace tests inspected. AST anti-hardcoding test prohibits selected case IDs only and allows all pinned group tables; digest length is not chain recomputation.',
 'test_c040_checker_mutations.py':'Full body read. Retained mutant cases and expected rejection/disagreement requirements inspected; all mutants separately replayed in the per-file ledger.',
 '__init__.py':'Full package body read, including empty initializer where applicable. Import wiring/docstring only; no additional mathematical certificate established.'}
for r in scope['files']:
    if '/c040_' in r['path'] and r['path'].endswith(('.py','.md')) and r['path'] not in done:
        p=audit.ROOT/r['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];n=len(raw.decode('utf-8-sig').splitlines())
        reads.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,n]] if n else [],'assessment':assessments[p.name]})
save('_read_ledger.json',reads)
fam={'family':'C040',
 'math':'Internal-index subset counts for the eleven-dimensional metric and 3-form, together with the admitted p-potential -> (D-p-2)-potential duality rule, yield scalar totals 1,3,7,14,25,42,70,128 and vector totals 1,3,6,10,16,27,28,0 in the stated frames. Full independent Weyl-reflection closure on all 12 nonabelian Cartan inputs agrees with the owner root-string sets, and dimG-dimK matches every scalar total. These computations certify dimensions conditional on the declared field inventory and group identifications; they do not establish representation branching or M-theory equivalence.',
 'limits':['Reference coset/branching answers are table lookups; root recomputation occurs only in checker 2. Compact-subgroup identification, real forms and global group forms are admitted, not reconstructed.',
           'Both branching verifiers check dimensions plus an adjoint substring; neither implements a restriction matrix or character identity. The advertised IIA/IIB comparison is partial and theory is ignored by the reference solver.',
           'Hodge dual-potential counting assumes the stated field content, duality frame and local free-field degree accounting. No quantum compactification, interacting dynamics, physical vacuum or string/M-theory duality is proved.',
           'All retained artifacts are historical local inputs/outputs; no paid provider execution or model quality is inferred.'],
 'data':'All 104 data files replayed: 46 judge cases, eight retained example answers, 48 mutants, one manifest and one budget declaration. All 20 source/spec/test files fully read. All 32 k/query positive controls pass; each solved retained certificate receives independent subset-count/Hodge arithmetic and Weyl-closure dimension checks. Eleven synthetic countercontrols record accepted bad certificates, rejected legitimate reference refusals and mutable-return contamination.',
 'findings':[
 {'id':'AC40-F01','claim':'Both checkers accept G=made_up_group, K=1 for the k=7 coset and accept branching [[adjoint(fiction),63],[banana,70]]. Missing group names also pass. Dimensions alone do not certify the advertised group/representation identity.'},
 {'id':'AC40-F02','claim':'Both accept vector dual_forms=-999 with total=27, or omit all vector components except total. Irrelevant scalar components +99 and -99 also cancel to an accepted total. The advertised complete nonnegative field breakdown is not enforced.'},
 {'id':'AC40-F03','claim':'Both accept a solved answer with mandatory id and D removed; provenance/instance binding is incomplete despite the strict-schema claim.'},
 {'id':'AC40-F04','claim':'Legitimate reference UNKNOWN_QUERY_TYPE and MALFORMED_CASE_STRUCTURE refusals fail both checkers. theory=IIB,k=1 yields a reference/checker disagreement because one checker adds a different ten-dimensional field inventory without excluding that comparison domain.'},
 {'id':'AC40-F05','claim':'The reference get_branching returns a shared mutable table. Editing one returned answer mutates future solve results, and a substituted non-adjoint representation label still passes both checkers. Reproduced only in memory, then restored.'}],
 'probe_artifact':'additional_challenges_031_040_c040_probes.json'}
notes['family_assessments']=[f for f in notes['family_assessments'] if f['family']!='C040']+[fam]
notes['current_work']='All ten families and the root C039 test complete; final scope/accounting validation recorded separately.'
for s in notes['primary_sources']:
    if '9310003' in s['url']:s['read_scope']='Abstract and introduction only; detailed theorem text was not independently reread.'
save('_notes.json',notes)
# Refresh only metadata affected by count-field adapter correction. Preserve all
# substantive per-artifact replay results and all historical bytes.
refresh=[]
for ledger in sorted(HERE.glob('additional_challenges_031_040_c???_automated.jsonl')):
    rows=[json.loads(l) for l in ledger.read_text(encoding='utf-8').splitlines() if l.strip()]
    for i,r in enumerate(rows):
        if r['path'].endswith('/manifest.json'):
            rows[i]=audit.worker(r['path']);refresh.append(r['path'])
    ledger.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
print(json.dumps({'full_source_reads':len(reads),'full_source_lines':sum(b-a+1 for r in reads for a,b in r['reviewed_lines']),'metadata_refreshed':len(refresh)}))

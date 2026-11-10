"""Contextual artifact dispositions; reuse pinned replays without counting new runs."""
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
PREFIX='additional_challenges_011_020_artifacts'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=load(REV/(PREFIX+'_scope.json'))
report=load(REV/(PREFIX+'.json'))
prior=REV/'additional_challenges_011_020.json'
ledger_path=REV/'additional_challenges_011_020_automated.jsonl'
assert sha(prior)=='ede59ddcf224caa1139cc34d3e4b2fc10f33adcc43d75e022b4cce7d3381f1b1'
assert sha(ledger_path)=='4b1933f93908d84a38484821ebc7483b7670a83eea44746ab02f018f5c0e2a24'
ledger=[json.loads(line) for line in ledger_path.read_text().splitlines()]
entries={r['path']:(i+1,r) for i,r in enumerate(ledger)}
frozen={r['path']:r for r in scope['files']}
assert set(entries)==set(frozen) and len(entries)==len(ledger)==1076
full={r['path']:r for r in report['file_reviews'] if r.get('full_source_read')}

family_limits={
 'C011':'Weighted L1 primal/dual equality is meaningful on the declared oriented graph. Prior AC1120-F06 exposes unwitnessed refusals, unbound scope constraints and parser totality gaps.',
 'C012':'Finite kernel/cokernel and target-image calculations are useful. The second checker catches the first checker missing H0 completeness; shared input/refusal defects remain (F05,F07).',
 'C013':'Integral homology needs valid integer unimodular certificates, not int-coercion of submitted entries. Recomputed invariants catch some false values but do not validate all supplied SNF data (F02,F08).',
 'C014':'Finite weighted Hodge decomposition assumes positive metrics and the intended nilpotent incidence matrix. Shared duplicate-incidence overwrite and degenerate-producer failures remain (F04,F09).',
 'C015':'Finite F2 boundary reduction and barcode checking do not repair missing filtration-order and refusal-witness validation. Five warranted UNKNOWNs fail the retained gate (F10).',
 'C016':'A cup-product image rank requires complete cohomology bases and valid certificates. Incomplete-basis acceptance and non-total refusal/degree4 handling remain (F03,F11).',
 'C017':'Finite group table multiplication supports local holonomy and gauge witnesses on the admitted lattice. Named-group/grid bounds and parser totality are weaker than the contract (F12); historical provider provenance remains open (F16).',
 'C018':'Switching yields a constructive upper bound and edge-disjoint odd cycles a lower bound; equality certifies the encoded instance. Missing advertised certificate methods and unenforced simple-graph/size constraints remain (F13).',
 'C019':'Exact extension and closed-cycle obstructions are useful. Both judges omit primal_A and can accept a suboptimal dual lower bound as an optimum;29 retained PASS rows have nonzero primal-dual gap (F01). Integer production is incomplete (F14).',
 'C020':'Finite filtered double-complex page calculations require correct carrier encoding. Silent out-of-grid deletion, missing dimension cap and first-checker exceptions remain (F15).'
}
def family(path):return path.split('/')[3][:4].upper()
def evidence(path):return {'path':path,'sha256':frozen[path]['sha256']}
def record_full(path,assessment,basis='complete raw JSON body reading'):
    raw=(ROOT/path).read_bytes()
    full[path]={'path':path,'sha256':frozen[path]['sha256'],'full_source_read':True,
       'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],'review_level':basis,'assessment':assessment}

for path,(_,row) in entries.items():
    if row['status']=='accounting_template_only':
        data=load(ROOT/path)
        ceiling=data.get('cost_ceiling_usd',data.get('budget_ceiling_usd'))
        if 'calls' in data:kind='Empty calls list and explicit zero token/billing totals.'
        elif 'audit_trail' in data:kind='Null usage/cost with explicit UNVERIFIED_NO_PROVIDER_RECEIPT; the model label is not an observed call.'
        elif 'runs' in data:kind='Empty runs list; no measured usage.'
        else:kind='Model names and policy parameters only; no calls, tokens, times or billing receipts.'
        record_full(path,f'Full template read. {kind} Historical declared ceiling USD{ceiling} exceeds the new USD0.10 whole-run benchmark cap and must not be imported as current authorization. Target USD0.05 is an aspiration, not an enforced cap or measured saving.')
    if row['status']=='historical_receipt_bounded_reconciliation':
        record_full(path,'Full receipt read. '+('Explicit harness_execution scope correctly coexists with0/5 baseline and0/5 immune pass rates and NO_IMMUNE_ASSISTED_CASE_PASSED.' if path.endswith('/receipt.json') else 'PASS coexists with the separately reported case pass rate; its status has no explicit mathematical-success scope.')+' Prior report hash/cost/rate reconciliation is retained. A SHA binds the available report bytes; authority_effect None is metadata and does not authenticate a provider bill or demonstrate effect isolation. Report serialization ownership remains unresolved.')

history_root='workflows/tasks/certified_challenges/c017_nonabelian_lattice_holonomy/results/'
history_notes={
 'arm5_hybrid_report.json':'Full83-line report read: one nonflat witness on one poison case, recorded0.00042726USD/2343input/487output tokens. The retained plaquette product and replay can support that finite certificate, not model identity/billing authenticity or an immune-workflow improvement.',
 'immune_transfer_report.json':'Full138-line report read: paired five-case baseline and immune records all fail, for noncanonical plaquettes, wrong verdicts, incorrect loop holonomy or parse errors. No full solution bodies are retained. Verdict names alone cannot be rescored as complete certificates; this panel shows no recorded acceptance improvement and is not a randomized efficacy experiment.',
 'arm5_stealth_space_bunny_alpha_report.json':'All JSON key/value bodies read in duplicate-preserving compact object-pair form. Five cases yield3/5 recorded accepts; pure-gauge input gets a wrong nonflat witness and torus output is PARSE_ERROR with only a truncated raw prefix. Recorded8000 output tokens do not reconstruct the missing response. All costs are0.0 without authenticated provider billing; scratchpad steps are artifacts to verify, not independent observations.',
 'arm6_stealth_space_bunny_alpha_report.json':'All JSON key/value bodies read in duplicate-preserving compact object-pair form with exact float lexemes. Five cases yield4/5 recorded accepts; pure-gauge input still receives a false nonflat witness. The torus solution supplies two loops with holonomies r,r2 and active plaquette traces. This finite retained result supports replay, not a universal decimation law or a causal advantage over Arm5; all reported monetary costs are0.0 without provider authentication.'
}
for name,note in history_notes.items():
    record_full(history_root+name,note,'complete JSON value-body reading; raw hash and original line coordinates retained')
assert len(full)==28

rows=[]
for item in scope['files']:
    path=item['path'];line,row=entries[path]
    assert sha(ROOT/path)==item['sha256']==row['sha256']==row['inventory_sha256']
    context=family_limits[family(path)]
    status=row['status']
    if path in full:out=dict(full[path])
    else:
        out={'path':path,'sha256':item['sha256'],'full_source_read':False,'reviewed_lines':[],
             'review_level':'bounded_contextual_assessment_of_pinned_prior_replay'}
        if status=='case_certificate_verified':
            note=f'Prior owner-generated result {row["solver_status"]} passed the combined checker for these exact bytes. A certificate digest is retained; this is a finite local regression, not an independent model answer or soundness proof.'
        elif status=='mutation_rejected':
            note='This stored mutation was rejected by the prior combined checker replay. Rejection of this finite negative example does not establish detector adequacy, independence of checkers or completeness against other mutations.'
        elif status=='owner_pass_but_primal_dual_gap_nonzero':
            assert Fraction(row['primal_objective'])-Fraction(row['claimed_phi2'])==Fraction(row['primal_dual_gap'])!=0
            note=f'Both owner checkers returned PASS, but retained primal objective {row["primal_objective"]} minus claimed Phi2 {row["claimed_phi2"]} equals nonzero gap {row["primal_dual_gap"]}. The submitted pair does not certify optimality. Exclude this as a successful optimality certificate; retain as an adversarial regression.'
        elif status=='case_certificate_failed_or_disagreed':
            note=f'Prior reference result {row["solver_status"]} failed or disagreed under the combined gate. See exact per-checker reasons in the bound ledger; do not count this poison/refusal outcome as a solved positive instance.'
        elif status=='checker_or_solver_exception':
            note=f'Prior replay raised {row["exception_type"]}: {row["exception"]}. This is a totality regression, not a valid mathematical refusal certificate.'
        elif status=='answers_verified':
            note=f'All{len(row["line_reviews"])} retained answer records were previously parsed, uniquely ID-bound to pinned examples and accepted by owner dual checkers. These are participant example answers, not independently authenticated model trials. Nested certificate soundness retains the family limitations.'
        elif status=='manifest_prior_checks_reused':
            checks={x['rule'].split(':')[0]:x for x in row['prior_manifest_checks']}
            note=f'Prior normalization {checks["MAN-1"].get("detail")} and target-table checks are reused, with target hash/size outcomes {checks["MAN-4"].get("detail")}. Overall status {row["prior_manifest_status"]}. A current manifest is not a pre-run commitment, complete directory census or proof of fixture correctness.'
        else:raise AssertionError(status)
        out['assessment']=note+' '+context
    out['detail_receipt']={'path':ledger_path.relative_to(ROOT).as_posix(),'sha256':sha(ledger_path),'line':line,'status':status}
    rows.append(out)

# Recompute arithmetic over the recorded historical fields, without calling their producers.
def reject_constant(value):raise ValueError(value)
stats={}
for name in history_notes:
    data=json.loads((ROOT/(history_root+name)).read_text(),parse_float=Decimal,parse_constant=reject_constant)
    groups={}
    for case in data['cases_evaluated']:
        candidates={'baseline':case['baseline'],'immune_assisted':case['immune_assisted']} if 'baseline' in case else {'arm':case}
        for arm,value in candidates.items():groups.setdefault(arm,[]).append(value)
    stats[name]={}
    for arm,values in groups.items():
        stats[name][arm]={'cases':len(values),'recorded_passes':sum(v['passed'] is True for v in values),
           'input_tokens':sum(v['meta']['in_tokens'] for v in values),
           'output_tokens':sum(v['meta']['out_tokens'] for v in values),
           'recorded_cost_usd':str(sum((v['meta']['cost'] for v in values),Decimal(0))),
           'sum_recorded_call_latency_seconds':str(sum((v['meta']['latency'] for v in values),Decimal(0)))}
metrics={'status':'historical_recorded_field_arithmetic_only','reports':stats,
 'source_pins':[evidence(history_root+name) for name in history_notes],
 'limits':['No new paid calls, replay, billing reconciliation with provider or causal workflow comparison.',
           'Summed per-call latency is not necessarily elapsed whole-workflow time; unknown overhead and parallelism are not filled with zero.',
           'Report costs are retained observations, including unverified zero values; token counts do not prove model identity.']}
(REV/(PREFIX+'_historical_metrics.json')).write_text(json.dumps(metrics,indent=2)+'\n')

report.update({'status':'complete_declared_bounded_artifact_dispositions_with_source_reading_limits',
 'file_reviews':rows,'pending_paths':[],
 'source_body_reads_not_completed':[r['path'] for r in rows if not r['full_source_read']],
 'counts':{'scope':1076,'full_body_readings':28,'bounded_prior_replay_dispositions':1048,'pending_dispositions':0,
           'prior_outcomes':dict(Counter(r['status'] for r in ledger))},
 'family_checker_limits':family_limits,
 'claims':[{'id':'CAA-C01','statement':'The1076 fixed artifacts supply703 case/example inputs,344 stored negative mutations, four participant answer collections and finite custody/accounting/history controls. Their pinned prior replays are useful regression evidence conditional on the separately reviewed checker implementation; they do not certify all accepted mathematics.',
    'source_evidence':[evidence(r['path']) for r in rows if r['full_source_read']][:10],
    'validation':'dag/reviews/'+PREFIX+'_reconciliation.json'},
   {'id':'CAA-C02','statement':'The retained C017 baseline/immune comparison records0/5 accepted cases in each arm. Its fields permit separate token/cost/call-time arithmetic, but missing full answers and provider receipts prevent independent response rescoring or verified live-cost attribution.',
    'source_evidence':[evidence(history_root+'immune_transfer_report.json'),evidence(history_root+'receipt.json')],
    'validation':'dag/reviews/'+PREFIX+'_historical_metrics.json'}],
 'findings':[{'id':'CAA-F01','severity':'medium','statement':'All ten accounting templates declare ceilings above the requested USD0.10 benchmark cap: USD0.50,1.00 or2.00. Empty/unknown usage and a USD0.05 target are not run measurements or budget enforcement. Migrated workflow configurations must bind the shared whole-run ledger rather than inherit those historical ceilings.',
    'evidence':[evidence(p) for p,(_,r) in entries.items() if r['status']=='accounting_template_only'],
    'recommended_action':'Keep historical source records intact; make prospective plans use the existing strict USD0.10 shared ledger, including retries and all model calls.'}],
 'limits':['Twenty-eight complete body/value-body readings are distinguished from1048 bounded per-file dispositions of prior replay evidence.',
           'Prior checker/source report and JSONL ledger are immutable SHA-bound dependencies; none of their executions is counted as fresh.',
           'All16 prior findings were consulted. Not every verbose diagnostic or nested certificate body was manually reread; exact ledger rows remain accessible.',
           '665 case_certificate_verified labels and29 nonzero-gap owner-PASS rows are checker outcomes, not694 independently valid optimum certificates.',
           'No original source modification, provider/native call, private benchmark access or model ranking.']})
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
validation={'status':'passed','scope_paths':1076,'current_and_inventory_pins':1076,'unique_ledger_bindings':1076,
 'full_body_reading_receipts':28,'bounded_artifact_dispositions':1048,
 'nonzero_gap_arithmetic_checked':29,'prior_report_sha256':sha(prior),'prior_ledger_sha256':sha(ledger_path),
 'report_sha256':sha(REV/(PREFIX+'.json')),'metrics_sha256':sha(REV/(PREFIX+'_historical_metrics.json')),
 'limits':'Custody, attribution and arithmetic consistency only; no fresh owner/checker execution or semantic soundness certification.'}
for r in rows:
    if r['full_source_read']:assert r['reviewed_lines']==[[1,len((ROOT/r['path']).read_text(encoding='utf-8').splitlines())]]
(REV/(PREFIX+'_validation.json')).write_text(json.dumps(validation,indent=2)+'\n')
(REV/(PREFIX+'.md')).write_text('# C011-C020 artifact reconciliation\n\n'
 'All1,076 frozen paths now have explicit dispositions:28 full body/value-body readings and1,048 bounded assessments of pinned prior replay results. This is not full reading of every nested data artifact.\n\n'
 'The703 case/example outcomes include665 combined-checker passes,29 passes with nonzero primal-dual gaps, eight failures/disagreements and one exception. All344 stored mutations were rejected in the previous replay; that finite result does not establish checker soundness.\n\n'
 'Seven manifests retain their actual custody outcomes: C015-C017 each have five mismatches. Ten accounting templates are configurations with ceilings above the current USD0.10 cap, not measured usage. Four answer collections contain72 prior checked example records.\n\n'
 'Four C017 historical reports and four receipts have complete body/value-body readings. The baseline/immune panel records0/5 in each arm and omits full responses; Arm5/Arm6 record3/5 and4/5 on five cases, with unauthenticated zero costs. These snapshots do not establish a causal workflow improvement or free inference. Summed call latency is kept separate from whole-workflow elapsed time.\n\n'
 'Exact file dispositions, prior ledger row pointers, family limitations and arithmetic are in the JSON report and historical_metrics receipt. No models, original solvers or native tools were called for this reconciliation.\n',encoding='utf-8')
print(json.dumps(report['counts']))
print(json.dumps(stats))

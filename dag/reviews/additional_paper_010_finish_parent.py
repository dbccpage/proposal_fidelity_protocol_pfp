"""Account completed parent support slice without upgrading delegated pending data."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
OUT = REV/'paper_010_support_inspection'
PREFIX = 'papers/pfp/010_pfp_holonomy_checks_and_model_pilots/'

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def write(path,value): path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def evidence(name, ranges=None):
    path = ROOT/PREFIX/name
    return {'path':PREFIX+name,'sha256':sha(path),'lines':ranges or [[1,len(path.read_text(encoding='utf-8-sig').splitlines())]]}

report = read(REV/'additional_paper_010_support.json')
scope = read(REV/'additional_paper_010_support_scope.json')
frozen = {x['path']:x for x in scope['files']}
rows = {x['path']:x for x in report['file_reviews']}
for name, assessment in [
    ('paper.tex','All1216 lines read, including TeX preamble, finite-group/path/gauge definitions, three-way classifier argument, all historical tables and reproduction/limitations. Valid rectangular-cell-complex reasoning; no formal proof of Python. Typed-refusal statement exceeds malformed-input behavior. Historical path/toolchain vocabulary differs from current renamed sources. Rendered manuscript reviewed separately.'),
    ('paper_change_log.md','All298 lines read. Records substantial withdrawal of unsupported immune-filter effect sizes, fake benchmark totals, universal model/cost interpretations and erroneous prior holonomy heuristic. Useful correction provenance; historical assertions are not fresh executions. Current paper appropriately retains finite checker and historical methodological audit; publication/candidate wording mixes editions.'),
]:
    ev=evidence(name)
    rows[ev['path']]={**ev,'full_source_read':True,'reviewed_lines':ev.pop('lines'),'review_level':'complete_source_body_read','assessment':assessment}

render=read(OUT/'render_receipt.json')
inventory=read(OUT/'pdf_inventory.json')
for item in inventory:
    record=next(r for r in render['renders'] if r['pdf']==item['pdf'])
    index=record['index']
    page_review={'pages':item['pages'],'raw_pdf_bytes_read_as_text':False}
    if index < 2:
        page_review.update(method='Direct visual inspection of every complete contact-sheet page, alongside complete source reading.',direct_visual_pages=list(range(1,item['pages']+1)),sheets=record['sheets'])
    elif index == 6:
        assert item['sha256']==inventory[0]['sha256']
        page_review.update(method='Whole-PDF byte equality with directly inspected main edition.',same_bytes_as=inventory[0]['pdf'])
    else:
        matches=[x for x in render['standalone_correspondence'] if x['pdf_index']==index]
        assert len(matches)==item['pages'] and all(x['complete_pixel_matches'] for x in matches)
        page_review.update(method='Every complete rendered page has equal dimensions and RGB pixels to a directly inspected companion page.',page_matches=matches)
    rows[item['pdf']]={'path':item['pdf'],'sha256':item['sha256'],'full_source_read':False,'reviewed_lines':[],
        'review_level':'complete_rendered_page_review_not_binary_source_read','page_review':page_review,
        'assessment':'All pages visually accounted. Readable mathematical formulas/tables and wrapped manuscript identifiers; no clipping found at inspected resolution. Companion order is preface, guide, quiz/capstone, then instructor key, matching attempt-before-key guidance. Historical PDFs retain Landau/old repository paths; current renamed prose is a different edition. No learner or model-performance inference.'}

custody=read(OUT/'archive_inventory.json')
for name,checks in custody['current_manifests'].items():
    rows[PREFIX+name]={'path':PREFIX+name,'sha256':sha(ROOT/PREFIX/name),'full_source_read':False,'reviewed_lines':[],
        'review_level':'complete_manifest_membership_hash_parse_and_delta_review',
        'assessment':'All manifest entries parsed and checked against confined package files, with complete archive/current textual differences read. Current raw and LF-normalized failures preserved; valid archive manifests support byte custody only, not scientific truth or publisher authenticity.',
        'entries':len(checks),'raw_mismatches':sum(not x['matches'] for x in checks),'LF_normalized_mismatches':sum(not x['LF_matches'] for x in checks)}

data_path=REV/'additional_paper_010_data.json'
data=read(data_path) if data_path.exists() else {}
data_rows={x['path']:x for x in data.get('file_reviews',[])}
for path in set(rows)&set(data_rows): raise ValueError('Parent/delegate overlap: '+path)
all_rows={**rows,**data_rows}
primary=next(x for x in read(REV/'papers_audit.json')['files'] if x['path']==PREFIX+'paper.md')
assert primary['review_status']=='full-text-read' and sha(ROOT/primary['path'])==primary['sha256']
members=[]
for m in custody['members']:
    base=all_rows.get(m['current_path'])
    if m['current_path']==primary['path']:
        full=True; base_report='dag/reviews/papers_audit.json'
    else:
        full=bool(base and base.get('full_source_read')); base_report=('dag/reviews/additional_paper_010_data.json' if m['current_path'] in data_rows else 'dag/reviews/additional_paper_010_support.json')
    disposition='full_text_body_transfer' if full else ('bounded_artifact' if base else 'pending_base_read')
    members.append({**m,'body_disposition':disposition,'base_report':base_report,
                    'method':'Exact bytes or LF equality; for different text, all521 archive/current delta lines read after complete base read. No credit from hashing alone.'})
zip_path=next(x['path'] for x in scope['files'] if x['path'].endswith('.zip'))
zip_counts={kind:sum(m['body_disposition']==kind for m in members) for kind in ('full_text_body_transfer','bounded_artifact','pending_base_read')}
rows[zip_path]={'path':zip_path,'sha256':sha(ROOT/zip_path),'full_source_read':False,'reviewed_lines':[],
    'review_level':'safe_member_inventory_custody_and_explicit_body_transfer',
    'assessment':'All82 unique confined regular ZIP members extracted and CRC/hash checked. Internal manifests80/80 and81/81 match.28 current members byte equal,35 LF equal,19 differ; every text delta read. Semantic member accounting depends on explicit base reads; pending delegated bodies are not silently credited.',
    'member_counts':zip_counts,'detail_receipt':'dag/reviews/paper_010_support_inspection/archive_body_accounting.json'}
write(OUT/'archive_body_accounting.json',{'members':members,'counts':zip_counts,'limits':'ZIP consistency is not publisher authentication; underlying historical empirical assertions are not fresh model runs.'})

def claim(identifier,statement,names,limits,dependencies=None):
    return {'id':identifier,'statement':statement,'source_evidence':[evidence(n) for n in names],
            'evidence':[PREFIX+n for n in names],'status':'complete_source_review_and_explicitly_bounded_controls',
            'dependencies':dependencies or [],'limits':limits}
report['claims']=[
 claim('PAPER010-FINITE-GROUP-ADMISSION','A nonempty finite carrier, closed full table, two-sided identity/inverses and all-triple associativity are checked before lattice arithmetic. Validated S3 and Q8 are actual finite groups; their exact products are table lookups.', ['code/holonomy.py','code/tests/test_holonomy_checker.py'], 'Finite represented groups only; cubic table-validation work has no service resource cap. This is no derivation of a physical gauge group.'),
 claim('PAPER010-RECTANGULAR-HOLONOMY-CLASSIFIER','On the declared open rectangle or torus cell complex, nonidentity plaquette products witness nonflatness. Flat open connections are tree-gauge trivial; flat torus connections have commuting based cycles and are gauge trivial exactly when both cycles are identity. The Python host implements these checks and verifies returned trivializing gauges.', ['code/holonomy.py','paper.tex'], 'Independent controls exhaust1296 S3 open2x2 states and1024 flat Z2 torus3x3 states, plus1024 selected nonflat states; no general formal proof of Python.', ['Finite-group axioms admitted by full table checks','Declared rectangular cell complex and its elementary path relations']),
 claim('PAPER010-WITNESS-ACCEPTANCE','A certificate is accepted only after recomputing its stated nonidentity plaquette, globally trivializing gauge, or full-flatness plus nonidentity closed-loop witness. Plaquette rotations and reversal are allowed with matching ordered products; correct verdict text alone is insufficient.', ['code/holonomy.py','code/tests/test_c017_replay.py'], 'Assumes a valid admitted Connection and successful parsed input processing. Raw JSON duplicate keys remain decoder responsibility; malformed input can raise untyped exceptions.'),
 claim('PAPER010-IDENTITY-SKIP-BOUND','Four identity links have identity product, so those multiplications may be skipped while all other plaquettes are checked. A gauge transformation preserves flatness but can eliminate every such shortcut. Lean source proves only the identity-link remark under supplied group laws.', ['lean4/LatticeDecimation.lean','code/holonomy.py','tools/study_capstone.py'], 'One narrow written Lean lemma and historical reports, not a fresh kernel pass or proof of the whole checker. No gauge-invariant or general token saving follows.'),
 claim('PAPER010-REPLAY-AND-RECOUNT-CEILING','Five retained C017 cases and15 retained solution records can be replayed, yielding10 accepts and5 rejects, while10 further payloads remain absent. Historical table recount sums original flags and author annotations; it cannot establish prompt superiority, model ranking or unaided accuracy.', ['code/replay_c017.py','code/recount_pilots.py','paper.tex'], 'Exact archive suite43 and capstone pass. Current checkout custody failures remain. C045-C050 historical checker execution and paid model trials were not rerun.'),
]
def finding(identifier,statement,names,action,severity='reproducibility_or_scope_gap'):
    return {'id':identifier,'statement':statement,'source_evidence':[evidence(n) for n in names],
            'evidence':[PREFIX+n for n in names],'severity':severity,'recommended_action':action}
report['findings']=[
 finding('PAPER010-CURRENT-CUSTODY-DRIFT','Current MANIFEST has52 raw mismatches among80 entries and SHA256SUMS53 among81;21 and22 remain after LF normalization. Current suite40pass/3fail and capstone fails first on c045 source hash. Exact ZIP manifests pass and its suite43/capstone pass; first archive renderer attempt was obstructed by OS temporary-directory permissions, then passed with workspace temp.', ['MANIFEST.sha256','SHA256SUMS','code/tests/test_c017_replay.py','code/recount_pilots.py'], 'Preserve both editions and identify transformations explicitly; do not rewrite historical hashes to disguise changed source bytes.'),
 finding('PAPER010-RENDERER-AUTHOR-REGRESSION','tools/render_paper.py now searches for an author starting Bare Metal Anchor, but actual manuscript and retained fixture start Jeremy. Fresh current test and direct public fixture raise StopIteration before external rendering; archived Jeremy-prefix renderer passes.', ['tools/render_paper.py','code/tests/test_render_paper.py','paper.tex'], 'In a future editable edition, use explicit metadata or robust header parsing and retain a regression test against the actual manuscript.'),
 finding('PAPER010-MALFORMED-REFUSAL-CEILING','The claimed typed refusal for malformed inputs is not total: nonobject case input raises AttributeError; a certificate vertex containing5000 decimal digits raises uncaught ValueError. Direct API float-coordinate aliases also compare equal to integer coordinates, outside the annotated type domain; no valid-carrier mathematical false acceptance was established.', ['code/holonomy.py','paper.tex'], 'Any reusable workflow adapter must admit shape, exact scalar types and size limits and normalize expected parse errors into explicit refusals.', 'adapter_boundary_gap'),
 finding('PAPER010-UTF8-TEST-BRANCH','When invoked with UTF-8 mode enabled, the retained renderer test calls subprocess.run without capture_output and then writes completed.stdout/stderr, which are None. The successful archived suite was deliberately run with -X utf8=0, exercising its actual renderer body without this broken recursive branch.', ['code/tests/test_render_paper.py'], 'Use capture_output=True or avoid writing uncaptured streams in a future test repair; keep the scoped invocation explicit.'),
 finding('PAPER010-HISTORICAL-LEAN-PIN','Current lean-toolchain is4.35.0, while archived pin, manuscript and historical records state4.34.0-rc1. Named/full census bodies have one theorem versus26 declarations; neither is evidence of a current kernel execution or complete-host proof.', ['lean4/lean-toolchain','lean4/axiom_report.txt','lean4/full_axiom_report.txt','paper.tex'], 'A future Lean replay must bind the actual source and compiler version and record fresh output separately from historical reports.'),
 finding('PAPER010-WITHDRAWN-EFFECTS-AND-EDITION-MIX','The change log documents withdrawal of unsupported immune-filter effect sizes, benchmark totals without retained runners/receipts, and wrong earlier holonomy heuristics. Current finite checker and explicit historical audit are useful. PDF/candidate wording, later publication metadata and renamed current paths refer to different editions.', ['paper_change_log.md','paper_claim_ledger.md','zenodo_metadata.json'], 'Retain the corrected finite checker and evidence audit as the contribution; do not reuse withdrawn effect sizes or label the cited historical counts as measured workflow benefit.'),
]
report['file_reviews']=sorted(rows.values(),key=lambda r:r['path'])
report['delegated_data_report']='dag/reviews/additional_paper_010_data.json'
all_rows={**rows,**data_rows}
report['pending_paths']=sorted(set(frozen)-set(all_rows))
report['status']='complete_with_explicit_artifact_bounds' if not report['pending_paths'] and str(data.get('status','')).startswith('complete') else 'parent_complete_delegated_data_in_progress'
report['scope_summary']={'assigned_paths':83,'parent_full_source_bodies':sum(x.get('full_source_read',False) for x in rows.values()),
    'parent_bounded_artifacts':sum(not x.get('full_source_read',False) for x in rows.values()),
    'delegated_dispositions':len(data_rows),'pending_paths':len(report['pending_paths']),
    'pdf_pages':46,'direct_visual_pages':23,'raw_equal_pdf_pages':14,'pixel_equal_pdf_pages':9,
    'archive_members':82,'archive_body_counts':zip_counts}
report['validation']=[
 {'rule':'fresh_current_python_suite','status':'40_pass_3_fail','receipt':'dag/reviews/additional_paper_010_test_results.json'},
 {'rule':'exact_archive_suite_and_capstone_workspace_temp','status':'43_pass_capstone_pass','receipt':'dag/reviews/additional_paper_010_archive_replay.json'},
 {'rule':'independent_finite_mathematics_controls','status':'3344_pass','receipt':'dag/reviews/additional_paper_010_math_controls.json'},
 {'rule':'all_frozen_source_hashes','status':'passed','paths':83},
]
for p,x in frozen.items(): assert sha(ROOT/p)==x['sha256'],p
for p,x in all_rows.items():
    assert p in frozen and sha(ROOT/p)==x['sha256'],p
    lines=len((ROOT/p).read_bytes().decode('utf-8-sig',errors='replace').splitlines())
    for lower,upper in x.get('reviewed_lines',[]): assert 1<=lower<=upper<=lines
report['limits']=['No original source, manifest, PDF or historical receipt rewritten.','No private QM answer access, provider calls or current Lean build.','Finite correctness controls do not certify all inputs or empirical workflow benefit.','Public instructor key belongs to this old paper, not the sealed benchmark.']
write(REV/'additional_paper_010_support.json',report)
markdown = '''# Paper010 support audit

The corrected paper contributes a substantive finite-group holonomy checker and an audit of historical model evidence. Its mathematics is finite group validation, ordered path multiplication, gauge conjugation and the elementary path relations of rectangular cell complexes. It does not establish general immune-system gains, model superiority or a physical theory.

The parent reviewed46 complete source bodies and10 bounded artifacts. All46 PDF pages are accounted:23 directly inspected,14 by whole-file equality and9 by complete rendered-pixel equality. The companion puts the quiz before its instructor key. The remaining27 data/evidence paths have a separate delegated report; consult the JSON status before treating the whole slice as complete.

Fresh current Python tests give40 passes and3 failures: case bytes, historical report bytes and the author-header lookup. Current capstone also fails custody. The exact release archive passes43 tests and capstone after redirecting temporary files to the workspace; the first OS-temp permission failure is retained. Its renderer test uses local Pandoc and a fake XeLaTeX executable, not a real PDF rebuild. Internal archive manifests pass80/80 and81/81; current raw mismatches are52/80 and53/81, with21/22 remaining after LF normalization.

Independent controls pass all1296 S3 open2x2 connections, all1024 flat Z2 torus3x3 connections and1024 selected nonflat controls. These finite results do not prove the Python implementation for every input. The Lean source proves only that four identity links have identity product; no current Lean build was performed.

Actionable boundaries include malformed inputs escaping typed refusal, a broken UTF-8 recursive test branch, the renderer author regression and a changed Lean toolchain. Historical C017 accepts/rejects can be replayed; missing certificates cannot. Original C045-C050 flags, target-bearing IDs, unequal panels/settings and constant-refusal baselines prevent causal accuracy/cost conclusions.

Retain the checker, exact certificates and correction history as useful program material. A reusable workflow adapter still needs bounded input admission and a task-specific semantic bridge. No paid calls, sealed-answer reads, original-source edits or historical receipt regeneration occurred.
'''
if report['status']=='complete_with_explicit_artifact_bounds':
    markdown=markdown.replace('The remaining27 data/evidence paths have a separate delegated report; consult the JSON status before treating the whole slice as complete.','The separate delegated report completes all27 data/evidence bodies (6953 lines). Together the reports account for all83 assigned paths:73 full source bodies and10 bounded artifacts. All82 ZIP members are accounted for by73 explicit full-body transfers and9 bounded artifact dispositions.')
(REV/'additional_paper_010_support.md').write_text(markdown,encoding='utf-8')
write(REV/'additional_paper_010_parent_validation.json',{
    'status':'passed_parent_accounting_delegated_data_status_separate','report_sha256':sha(REV/'additional_paper_010_support.json'),
    'markdown_sha256':sha(REV/'additional_paper_010_support.md'),'scope_sha256':sha(REV/'additional_paper_010_support_scope.json'),
    'all83_original_hashes_unchanged':True,'source_ranges_valid':True,'parent_full_bodies':46,'parent_bounded_artifacts':10,
    'primary_manuscript_prior_read_hash_unchanged':True,'claims':len(report['claims']),'findings':len(report['findings']),
    'delegated_status':data.get('status','not_yet_reported'),'whole_slice_status':report['status']})
print(json.dumps(report['scope_summary']))

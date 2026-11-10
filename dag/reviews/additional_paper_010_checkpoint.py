"""Persist explicitly completed Paper010 reads; emissions alone confer no credit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
PREFIX = 'papers/pfp/010_pfp_holonomy_checks_and_model_pilots/'
scope = json.loads((REV/'additional_paper_010_support_scope.json').read_text())
target = REV/'additional_paper_010_support.json'
report = json.loads(target.read_text()) if target.exists() else {
    'schema_version':'1.0', 'source_commit':scope['source_commit'],
    'scope_manifest':'dag/reviews/additional_paper_010_support_scope.json',
    'file_reviews':[], 'claims':[], 'findings':[], 'validation':[],
}
rows = {r['path']:r for r in report['file_reviews']}
groups = [
(['code/holonomy.py'], 'Complete finite-group validation and immutable multiplication table; ordered nonabelian edge products, inverse reversal, all-plaquette checks, root gauge and based torus cycles. Certificate acceptance recomputes the relevant mathematical predicate. Finite controls support the specified carrier, not arbitrary topology or continuous gauge theory. Malformed JSON/API boundaries can raise untyped exceptions; no valid mathematical false acceptance found in the bounded probes.'),
(['code/replay_c017.py','code/recount_pilots.py'], 'Replay distinguishes five retained cases, absent payloads, parse errors, old label matches and new certificate acceptance. Recount verifies historical source bytes and sums report flags/author categories. It does not rerun all old checkers or establish causal improvement; current custody mismatches prevent claiming a clean current deposit replay.'),
(['code/tests/test_holonomy_checker.py','code/tests/test_c017_replay.py','code/tests/test_pilot_evidence.py','code/tests/test_render_paper.py'], 'Complete assertions and fixtures read. Tests cover group rejection, geometry, ordered products, certificates, old case digests, recounts and renderer mock behavior. Current failures include two byte-custody checks and author lookup. A UTF-8 subprocess branch writes uncaptured stdout; scoped test execution disables that recursive branch explicitly.'),
(['README.md','paper_claim_ledger.md','docs/completion_supplement.md','docs/lean_claim_map.md'], 'Paper explicitly withdraws unsupported prompt-filter effects and limits live-run conclusions. Finite host checker is substantive; Lean only proves the identity-link plaquette lemma. Historical source paths were renamed and current toolchain differs from reported historical pin. Claims ledger is an index to evidence, not an independent verification.'),
(['lean4/LatticeDecimation.lean','lean4/Census.lean','lean4/FullCensus.lean','lean4/lakefile.lean','lean4/lean-toolchain','lean4/lake-manifest.json','lean4/axiom_report.txt','lean4/full_axiom_report.txt'], 'Read all declarations/configuration/retained census lines. DiscreteGroup supplies group laws and inverse-of-one; four identity links give identity holonomy by rewriting. Historical named theorem is axiom-free; full listing has 26 declarations, one generated constructor-injectivity declaration using propext. No fresh Lean run; current v4.35.0 differs from historical v4.34.0-rc1.'),
(['tools/render_paper.py','tools/paper_preamble.tex','pyproject.toml'], 'Renderer/Pandoc/LaTeX formatting and build requirements read in full. Author lookup expects Bare Metal Anchor while actual manuscript and retained fixture begin Jeremy, raising StopIteration before external rendering. Preamble has Unicode mappings and code wrapping but does not repair the lookup. No original PDF rebuilt.'),
(['tools/study_capstone.py'], 'Offline instructional capstone reuses host, C017 replay and report recount. It tests the package examples and separates missing certificates from correct labels; no learner measurement or general model capability evidence.'),
(['docs/references.md','docs/descriptions.md','docs/keywords.md','zenodo_metadata.json'], 'Bibliographic and publication metadata read; descriptions are scoped to finite algebra, host checking and historical exploratory runs. Publication status and bibliographic attribution have not been independently verified in this support slice.'),
(['code/__init__.py','code/tests/__init__.py','_lev_examiner_theoretical_minimum_quiz/.gitkeep'], 'Package marker/empty placeholder only; no mathematical or experimental claim.'),
(['_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.md','_lev_examiner_theoretical_minimum_quiz/study_guide.md','_lev_examiner_theoretical_minimum_quiz/quiz.md','_lev_examiner_theoretical_minimum_quiz/answer_key.md'], 'Full public educational text read. Twenty-four questions and worked answers cover group products, gauge conjugation, flatness, witnesses and historical denominators. Q8 commutator and reversal examples are correct as read. Fictional examiner has no authority effect; rubric is practice, not a learning study. This public instructor key is unrelated to the sealed QM benchmark answer.'),
(['code/deposit_paths.py','verify_deposit.py'], 'Complete path-resolution and custody verifier bodies read. Confined deposit-relative paths and hashes support local custody. Default verification checks manifest; optional tests/Lean are separate. A digest is not mathematical truth or publisher authentication; originals/manifests remain unchanged.'),
]
frozen = {x['path']:x for x in scope['files']}
for names, assessment in groups:
    for name in names:
        path = PREFIX+name
        raw = (ROOT/path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == frozen[path]['sha256']
        lines = len(raw.decode('utf-8-sig').splitlines())
        rows[path] = {'path':path,'sha256':digest,'full_source_read':True,
                      'reviewed_lines':[[1,lines]] if lines else [],
                      'review_level':'complete_source_body_read', 'assessment':assessment}
transfers = json.loads((REV/'paper_010_support_inspection/shared_body_candidates.json').read_text())
for t in transfers:
    if t['path'] in rows: continue
    raw = (ROOT/t['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == t['sha256']
    lines = len(raw.decode('utf-8-sig').splitlines())
    rows[t['path']] = {'path':t['path'],'sha256':t['sha256'],'full_source_read':True,
                      'reviewed_lines':[[1,lines]] if lines else [],
                      'review_level':'exact_byte_transfer_from_prior_full_body_review',
                      'assessment':'Exact fully reviewed utility/license body reused in this deposit. Packaging and census scripts provide custody/build orchestration only; they are not evidence of a fresh successful execution. No historical manifests or PDFs regenerated. Named census can accept no parsed axiom lines; full census has stronger nonempty checks. Licence text is not rights provenance.',
                      'body_transfer':t}
report['file_reviews'] = sorted(rows.values(),key=lambda r:r['path'])
report['status'] = 'in_progress_explicit_completed_reads_only'
report['pending_paths'] = sorted(set(frozen)-set(rows))
report['scope_summary'] = {'assigned_paths':len(frozen),'full_source_bodies':sum(x['full_source_read'] for x in rows.values()),
                           'pending_paths':len(report['pending_paths'])}
report['limits'] = ['No paid calls, provider credentials or sealed QM answer reads.',
                    'Source bodies and historical receipts are distinguished from fresh executions.',
                    'Archive deltas fully read; equality alone does not give an unread base body semantic credit.',
                    'Remaining files retain pending status; no repository-wide completion claim.']
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report['scope_summary']))

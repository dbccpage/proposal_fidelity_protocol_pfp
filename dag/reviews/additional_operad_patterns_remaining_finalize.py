"""Assemble the completed, source-pinned review; does not modify source corpus."""
from pathlib import Path
from collections import Counter
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_patterns_remaining'
inventory=json.loads(Path(str(P)+'_inventory.json').read_text())['files']
notes=json.loads(Path(str(P)+'_notes.json').read_text());checks=json.loads(Path(str(P)+'_checks.json').read_text())
ledger=json.loads(Path(str(P)+'_read_ledger.json').read_text());scope=json.loads(Path(str(P)+'_scope.json').read_text())
def ev(i,a=None,b=None):
 r=inventory[i];return dict(path=r['path'],sha256=r['sha256'],lines=[[a or 1,b or r['lines']]],full_source_read=True)
def exev(i,a=None,b=None):
 r=checks['supporting_source_pins'][i];return dict(path=r['path'],sha256=r['sha256'],lines=[[a or 1,b or r['lines']]],full_source_read=True)
claims=[];findings=[]
def add(lst,id,statement,evidence,ceiling,next_action,probe_ids=(),prior=()):
 lst.append(dict(id=id,claim=statement,**({'finding':statement} if lst is findings else {}),source_evidence=evidence,
   evidence_kind='complete pinned source review'+('; fresh bounded controls' if probe_ids else '; no new execution of historical owners'),
   probe_ids=list(probe_ids),prior_review_references=list(prior),ceiling=ceiling,next_action=next_action))
add(claims,'OPR-C01','The slice is a catalog of proposed controls and historical audit cases, not198 executable operad mechanisms. Every assigned body was read; ten files explicitly admit zero patterns.',[ev(0),ev(2),ev(99),ev(197)],
 'Full reading covers198 paths/7066lines; no linked historical corpus or theorem is certified by quotation.',
 'Retain distinct historical contexts while consolidating reusable control mechanisms and keeping implementation/admission status explicit.')
add(claims,'OPR-C02','The strongest mathematical cards specify useful local obligations: declared finite acceptance families, typed cochain quotients, common ambient sets, phase-gauge invariants and state sufficiency on projection fibers.',[ev(111,19,33),ev(112,19,35),ev(128,19,36),ev(134,23,28),ev(155,13,17)],
 'These are scoped definitions or elementary conditional invariants; they do not supply physical bridges, unrestricted MUB results or complete task implementations.',
 'Reuse the explicit assumptions in task-specific checker contracts; preserve the source problem and all admissible candidates.')
add(claims,'OPR-C03','Historical Markdown pairs usually preserve negative evidence and evidence scope: failed build versus axiom info, byte-ceiling unscored rows, mock custody versus Lean execution, and strong direct baselines versus enumeration.',[ev(121,19,38),ev(125,19,35),ev(122,19,35),ev(129,19,32)],
 'Dates, counts and prior tests are historical assertions in these cards; this lane did not rerun those commands or read every cited receipt.',
 'Translate these cases into typed status/custody fixtures with a named consumer, rather than assigning a new workflow family to each incident.')
add(claims,'OPR-C04','The refined Rust ordering and boundary cards propose concrete benign/harmful controls and explicitly retain unknown residual or platform/carrier limits.',[ev(90,17,68),ev(189,17,65),ev(194,17,55)],
 'Native bindings are source references, not fresh compilation or runtime evidence; one platform/order family does not establish universal confinement or replay.',
 'Use the named controls only after current source/consumer binding; preserve the existing public outcome and valid behavior.')
add(findings,'OPR-F01','Operad, adjunction, identity/isomorphism and zero-residual labels exceed the definitions supplied by the catalog.',[ev(0,5,56),ev(105,5,35),ev(171,5,34),ev(172,5,41),ev(173,5,37)],
 'No carriers, witness norm, composition/unit laws, inverse maps or contraction proof are supplied. This is a new source location of a boundary already noted in prior OPERADS audits, not a newly proved global impossibility.',
 'Present cards as proposed typed controls; require explicit operator/domain/metric and law evidence before mathematical promotion.',prior=['additional_operads_core_remaining.json:OCR09','additional_operads_education_atlas.json'])
add(findings,'OPR-F02','The promised checker-receipt binding finalizer accepts a bare status PASS and grants PASS_TO_MASTER despite unresolved obligations.',[ev(99,19,48)],
 'Fresh control executes only the quoted pure function; no current orchestrator or historical run was tested. Cryptographic verification, candidate/task/checker identity and obligation discharge are absent from this example.',
 'Require a verified receipt type, exact task/candidate/checker binding and explicit obligation policy before promotion; retain a forged-status/open-obligation negative control.', ['OPR-P01'])
add(findings,'OPR-F03','Python auditor IDs AP_PY003 through008 identify different mechanisms from the pattern catalog, so ID-only joins can select the wrong repair.',[exev(0,1,14),exev(0,85,105),ev(72,15,34),ev(73,15,37),ev(74,15,38),ev(75,15,34),ev(76,15,35),ev(77,15,33)],
 'Fresh AST control confirms005 mutable-default emission; the catalog005 instead concerns digest-shaped evidence.003 bare-except/catalog-path,004 open-handle/corrupt-reset,006 nesting/absolute-path,007 shim/rebuildable-artifact and008 domain-I/O/ASCII-profile also diverge in the fully read owner. No whole-repository scan was run.',
 'Version or namespace detector IDs and bind each result to exact rule bytes and semantic contract before a repair lookup.', ['OPR-P11'])
add(findings,'OPR-F04','Catalog metadata and navigation have concrete inconsistencies: two arity mismatches,22 broken local links, two lowercase policy violations, and one nonreciprocal math dual.',[ev(1,5,10),ev(145,5,11),ev(0,86,99),ev(95),ev(194),ev(148,7,17)],
 'Whole198-file syntax/existence check:146 local Markdown links;21 broken helpful/math antibody links resolve under operads/antibodies and one Rust spec link also fails. No duplicate parsed pattern IDs or missing dual target stems. Nonreciprocity is not itself invalid many-to-one reuse, but conflicts with a naive one-to-one dual interpretation.',
 'Resolve authoritative current pointers and define normalized metadata/duality rules; preserve original historical bytes and do not infer semantic truth from a repaired link.')
add(findings,'OPR-F05','The math repaired-answer cards supply numerical and global conclusions without the encodings, assumptions or independent certificates needed to justify them.',[ev(48,15,25),ev(53,15,25),ev(54,15,25),ev(152,13,17),ev(153,13,17),ev(154,13,17),ev(156,13,17),ev(157,13,17),ev(158,13,17),ev(161,13,17),ev(164,13,17),ev(165,13,17),ev(168,13,17)],
 'This audit does not adjudicate the unrestricted external mathematical problems or literature. A named theorem, pilot or antibody is not its proof;24coordinates/32leaves,666constraints,56cells,rank6 and degree4 need their exact owners and scope.',
 'Keep these as unverified historical repair claims until actual predicates, task-preserving reductions and checked certificates are bound. Never feed the old answers into a new benchmark as truth.',prior=['additional_eis_pciv_remaining.json:EPR14','additional_eis_pciv_remaining.json:EPR16'])
add(findings,'OPR-F06','Several displayed mathematical implications fail elementary controls: tensor/zero-minus-one identity, empty-base exclusion diagnosis, nilpotence-to-positive-gap, and alternation-to-positive-circulation.',[ev(51,15,25),ev(57,15,25),ev(60,15,25),ev(61,15,25),ev(159,13,17),ev(160,13,17)],
 'Controls refute the unqualified formulations, not a specific undisplayed complex with stronger assumptions or the unrestricted MUB problem. F3 tensor F2 contains-1; adding constraints preserves base emptiness; zero maps/cochains retain zero values.',
 'Correct the premise/conclusion distinction and require supplied matrices, domains and positive-spectrum restrictions before these cards can be healthy examples.', ['OPR-P04','OPR-P05','OPR-P06'])
add(findings,'OPR-F07','A finite5^4 grid cannot by itself certify a polynomial identity; cohomological and moment claims also need the omitted transfer hypotheses.',[ev(49,15,25),ev(149,13,17),ev(163,13,17),ev(165,13,17),ev(166,13,17)],
 'Degree5 polynomial vanishes at five sample points but not the next. An independently supplied symbolic identity or adequate interpolation degree bound could still certify a claim. Nerve-to-space needs cover hypotheses, persistence needs a filtration, and moment extraction needs rank/positivity data.',
 'Separate finite sample evidence, algebraic identities, nerve certificates and conditional extraction. Retain required domain/degree/cover assumptions in workflow encodings.', ['OPR-P07'])
add(findings,'OPR-F08','Legacy healthy MUB cards remain stronger than the exact Pilot035 replacement definitions, which explicitly refuse all-family and unrestricted-exclusion promotion.',[ev(151,13,17),ev(152,13,17),ev(153,13,17),exev(4,1,112),exev(5,1,21)],
 'Current public candidate definitions and owner approval were fully read. They supersede named old rules within a narrow claims-object scope; the unsigned stored approval is a historical authorization record, not cryptographic authentication or proof of model efficacy.',
 'Expose supersession at the pattern catalog and route only the scoped reviewed rule. Preserve older answers as historical examples, never independent proof.',prior=['additional_eis_pciv_remaining.json:EPR14'])
add(findings,'OPR-F09','The exact pytest-addressing example labels a randomized-search-supported theorem PROVEN and promises gate success from reference syntax alone.',[ev(145,18,36)],
 'A node ID establishes a potential address, not test execution, semantic adequacy or universal theorem proof. No current claim ledger or D03 gate was run.',
 'Use bounded-test evidence status for finite search; keep proof evidence separate and validate each exact node against its consumer and source pin.')
add(findings,'OPR-F10','The purported tautological assertion is false Python chained-comparison syntax; one mutant rejection also cannot certify every test in a suite.',[ev(88,17,50),ev(186,19,40)],
 '1050 > 1000 is True evaluates false because the second chained relation tests identity of1000 with True. Independent literal arithmetic may be a valid oracle. A specified mutant tests one sensitivity claim, not all possible defects.',
 'Replace the example with an actual subject-independent always-pass case, and report mutation coverage by declared property/consumer and benign controls.', ['OPR-P02'])
add(findings,'OPR-F11','Canonical one-line wire guidance that strips all whitespace can change the protected task data.',[ev(147,23,27)],
 'Fresh ordinary-JSON control changes label a-space-b into ab. A separately proven restricted grammar may allow whitespace erasure; the current generic wording supplies no such restriction.',
 'Parse and serialize a named canonical grammar while preserving literal values; test round-trip semantic equivalence before hashing.', ['OPR-P08'])
add(findings,'OPR-F12','The immutable-array repair does not enforce immutable storage, and canonical-path/digest examples overstate atomicity or authentication.',[ev(170,19,50),ev(171,19,34),ev(173,19,37),ev(176,19,38)],
 'Array assessment is full code reasoning only: ascontiguousarray may share storage and writeability flags are not irreversible ownership. SHA equality against a caller-chosen hash is integrity consistency, not issuer authentication. Matching a path/profile does not guarantee concurrent byte identity.',
 'Define ownership and equality domains, immutable storage/copy boundaries, trusted pins and versioned serialization profiles; verify compatible cross-language golden vectors without claiming full correctness.', ['OPR-P10'])
add(findings,'OPR-F13','The atomic-backup and transaction examples omit assumptions needed for their never-corrupt and no-leaked-connection guarantees.',[ev(172,19,41),ev(196,19,48)],
 'Static review only. Fixed staging names have no writer exclusion; no fsync/durability or backup-validity rule appears. Transaction context lacks explicit BEGIN/savepoint/autocommit policy, catches Exception only and closes cursor rather than connection.',
 'Declare single-writer/filesystem/durability and transaction-ownership assumptions; test error/rollback/crash boundaries in an isolated owner-specific harness before making guarantees.')
add(findings,'OPR-F14','An explicitly requested missing archive is silently replaced by directory validation in the healthy archive guard.',[ev(85,19,43),ev(187,19,28)],
 'Exact quoted branch evaluated with in-memory fake path/callbacks; no real archive or deposit was validated. Directory validation may be appropriate only when that is the caller-selected contract.',
 'Treat absent selection and selected-but-missing archive separately; refuse the latter with its exact custody failure.', ['OPR-P13'])
add(findings,'OPR-F15','Runner and proof-checking examples still permit self-reported or lexical success instead of the promised executed evidence.',[ev(184,19,43),ev(191,19,34),ev(192,19,34),exev(1,35,37),exev(1,80,122)],
 'HP_PY016 checks directory/exit only; HP_RS004 trusts a passed regex and omits described failure/error counters; HP_RS005 searches stdout sorry without theorem axioms/source closure. The actual Lean auditor checks literal theorem-line envelope words, not finite-difference mathematics. No native/proof subprocess was run.',
 'Use a trusted harness with nonempty collection/completion, explicit current source/task binding and theorem-specific kernel/axiom receipts; keep lexical candidates labeled unverified.', ['OPR-P09'])
add(findings,'OPR-F16','Several boundary snippets do not enforce their prose contract: empty operation name, parent-directory filename, arbitrary root fallback and unverified clean-tree status.',[ev(181,19,44),ev(183,25,34),ev(174,19,35),ev(185,19,42)],
 'The parser fragment permits empty string to reach unspecified from_dict; filename predicate admits ..; root parents[3] assumes depth; Git stdout check ignores returncode and pre-existing changes. These are snippet limits, not freshly reproduced production defects.',
 'Make the missing preconditions explicit and validate the real downstream consumer, reserved components, root discovery and before/after write baseline.', ['OPR-P12'])
add(findings,'OPR-F17','Cost, cache and typechecking repairs advertise universal zero residual or fixed efficacy without workload and environment evidence.',[ev(104,19,34),ev(105,23,35),ev(169,19,41),ev(188,19,38),ev(190,19,36)],
 'The finite-envelope structure assumes cost>=2 rather than deriving physical work/error. Cache time/disk amounts are contextual, and strict mypy is not full semantic verification. No build, cleanup or mypy run occurred.',
 'Record measured workload/environment with uncertainty, separate resource policies from mathematical bounds, and leave residual unknown until independently measured.')
add(findings,'OPR-F18','The SQL owner implements partial Python syntax heuristics, while the catalog promises broader SQL/transaction properties.',[ev(96,19,32),ev(97,19,32),ev(195,19,56),exev(2,1,9),exev(2,37,109),exev(2,149,185)],
 'AST direct execute argument forms miss prior-built query strings and do not resolve receiver types; module-level close/context tokens do not prove each connection lifetime. The target enumerator processes.py only despite SQL-file/NOT-NULL docstring. No database or driver was run.',
 'Scope current scanner to syntactic candidates; add driver-aware dataflow/lifetime contracts and matched benign/harmful controls before claiming SQL injection elimination or atomicity.')

families={f['id']:f for f in checks['family_registry_metadata_only']}
groups=[
 ('Receipt custody and honest aggregation',['WF23','WF32','WF43'],[99,114,115,117,121,122,123,124,125,126,127,135,137,138,139,177,183],'Useful proposed field/identity/population checks; card prose is not an executed receipt verifier. Reuse existing custody owners with task/candidate/checker hashes, independent closure and explicit historical/fresh/NOT_VERIFIED outcomes.'),
 ('Strict boundary refusal',['WF7','WF39'],[178,179,180,181,193],'Reuse typed errors/absent-gate refusal; implement complete schema and trusted admission policy. Status labels alone confer no authority.'),
 ('Failure-derived proposals and detector adequacy',['WF14','WF19','WF29','WF41'],[70,74,90,145,148,186,189],'Use source-bound definitions plus benign/harmful cases, preserve rule versions and task scopes. A regex or one mutant is bounded evidence, not learned efficacy; old repaired answers must remain outside new benchmark inputs.'),
 ('Task-preserving rewrite and prompt compilation',['WF5','WF21','WF49'],[111,112,128,134,147,155],'Require explicit domain/encoding and proof or independent checker for protected task preservation. Formatting, dephasing and quotient construction have distinct assumptions; no generic operad-law transfer.'),
 ('Exact certificate checks',['WF10','WF11','WF44'],[148,149,150,156,157,159,161,162,163,164,165,167,168],'Only proposed mechanism slots: complete polynomial reductions, certified covers, chain matrices, cocycle data and linked subproofs. Add actual typed witness/checker; numeric prose and linked antibodies are not certificates.'),
 ('Mechanism controls and cost accounting',['WF12','WF22','WF35'],[129,186,189,194],'Retain strong direct baselines, same-task controls, complete costs and resource limits. Historical20375/125/125 is no new model improvement and no cochain call-count advantage.'),
 ('Finite-family selection',['WF45'],[111],'Admit fixed F/e and complete per-candidate receipts; singleton selection is relative to that family and cannot claim exhaustive empirical authority.'),
 ('Implementation hygiene support',[],[169,170,171,172,174,175,176,178,182,185,188,190,195,196],'Type configuration, path resolution, transaction scope and cache policy are reusable engineering prerequisites. They do not each need a new proposal workflow family or an efficacy score.')]
workflow_suggestions=[]
for name,ids,indices,assessment in groups:
 workflow_suggestions.append(dict(mechanism=name,existing_workflows=[families[i] for i in ids],source_evidence=[ev(i) for i in indices],assessment=assessment,
  execution_status='recommendation/cross-reference only; no adapter or provider executed',transfer_prerequisite='Bind a public task specification, lossless encoding, independent checker and same-task controls; do not include historical target answers or private benchmark content.'))
reviews=[]
for r in inventory:
 i=r['index'];note=notes['assessments'][str(i)]
 assert any(x['path']==r['path'] and x['sha256']==r['sha256'] and x['reviewed_lines']==[[1,r['lines']]] for x in ledger)
 reviews.append(dict(path=r['path'],sha256=r['sha256'],bytes=r['size_bytes'],source_line_count=r['lines'],full_source_read=True,
  reviewed_lines=[[1,r['lines']]],review_level='full_text_source_review',reading_method='complete numbered body; truncated final SQL batch reread in full',
  assessment=note['assessment'],mechanism=note['mechanism'],disposition=note['disposition'],
  workflow_mapping=[g['mechanism'] for g,group in zip(workflow_suggestions,groups) if i in group[2]],
  actual_execution_status='No historical test/model/native run reproduced; fresh controls only where explicitly linked by probe source_indices.',
  source_evidence=[ev(i)]))
extra_assessments=[
 'Full552-line body read across first display and291-552 followup. Standard-library AST/token/config heuristic; IDs003-008 collide semantically with catalog, custom hash presence bypasses collection check, type/config and clean-report words are narrower than semantic verification. Only AST visitor on a supplied mutable-default string executed; no filesystem scan or CLI.',
 'Full159-line body read. Hardcoded LN001-003 regexes; comments removed with a non-nested block approximation, theorem-line finite/envelope/residual tokens are lexical only, any cache-get text exempts entire shell file. No LN004 custom-axiom check, kernel/build or catalog parsing. No execution.',
 'Full251-line body read including recovered header. Direct Python execute argument AST shapes plus raw-connect/context/close regex; only.py targets, no Rust/SQL DDL analysis, no alias/dataflow/lifetime proof. CLI has optional output and check status; not invoked.',
 'Full98-line body read. Reviewed lexical candidate wrapper deliberately emits REVIEW/unverified/derive_only and preserves manual/type-use limitations. It imports a separate lexical owner not reread in this lane, so no execution/dependency-body credit; this is narrower and more honest than universal ordering repair.',
 'Full112-line public JSON body read. Two exact claims-object regex definitions with negative/positive controls and supersedes links; finite scope explicitly refuses all-CHM and unrestricted-MUB conclusions. Rule hashes/admission are metadata, not independent theorem or model performance. No regex/activation run here.',
 'Full21-line public historical operator-approval body read. Approves two exact rule hashes only for Pilot035 claims scope, with null cryptographic_signature and explicit no-math-authority limit. Historical explicit-decision record is not new authorization or cryptographic evidence.'
]
extra=[]
for r,a in zip(checks['supporting_source_pins'],extra_assessments):extra.append(dict(path=r['path'],sha256=r['sha256'],source_line_count=r['lines'],full_source_read=True,reviewed_lines=[[1,r['lines']]],review_level='supporting_full_text_source_review',assessment=a))
prior=[]
for name,usage in [
 ('additional_operads_core_remaining.json','Selected findings OCR09/OCR19 and metadata excerpts only; no whole report reread or source transfer.'),
 ('additional_eis_pciv_remaining.json','Selected antibody parsed receipts and EPR06/EPR14/EPR16/EPR20 findings; raw source full reads only for two explicit supporting JSON files above.'),
 ('workflows_audit.json','Selected WF-A06 efficacy/answer-leak warning; no fresh model evaluation.'),
 ('additional_workflow_library_remaining.json','Prior report identity recorded; no new whole-body reading credit.'),
 ('additional_wiki_workflow_dag.json','Prior report identity recorded; existing family statuses read from registry as metadata only.')]:
 p=R/'dag/reviews'/name;prior.append(dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),usage=usage))
report=dict(schema_version='1.0',review_id='additional_operad_patterns_remaining',status='complete',source_commit=scope['source_commit'],
 scope_manifest=P.relative_to(R).as_posix()+'_scope.json',scope_sha256=hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest(),
 summary=dict(frozen_paths=198,full_body_receipts=198,full_body_lines=7066,source_bytes=327419,pending=0,bounded_artifact_receipts=0,
  supporting_full_source_files=len(extra),supporting_full_source_lines=sum(x['source_line_count'] for x in extra),claims=len(claims),findings=len(findings),
  fresh_bounded_controls=len(checks['probes']),dispositions=dict(Counter(x['disposition'] for x in reviews))),
 checkpoints=[dict(full_body_receipts=n,pending=198-n) for n in [54,96,140,198]],
 file_reviews=reviews,supporting_file_reviews=extra,pending_paths=[],claims=claims,findings=findings,
 workflow_suggestions=workflow_suggestions,probes=checks['probes'],population_checks=checks['population_checks'],prior_context=prior,
 limits=[
  'Every assigned Markdown/TXT body was read. No artifact parse-only body credit is used for this198-file scope; ten empty catalogs remain explicit absence metadata.',
  'Linked historical files, theorem names, literature references, antibody labels and cited test counts are not new source reads or proof/model efficacy. Six additional source bodies are listed separately.',
  'Fresh controls execute only in-memory arithmetic/quoted snippets and a fully reviewed standard-library Python AST visitor. No subprocess, provider/model, native build, network call, database, or private benchmark input was used.',
  'Mathematical criticism is confined to displayed assumptions and exact finite countermodels. No literature novelty, unrestricted MUB resolution or physical derivation is claimed.',
  'All original scope/support source hashes are validated unchanged. Only this report prefix was written; shared coverage/DAG/progress and prior atlas reports remain untouched.',
  'Current family statuses are registry metadata, not proof of implementation completeness. Suggestions consolidate existing mechanisms and require task-specific checker/encoding work.'
 ])
Path(str(P)+'.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
md=['# Operad pattern catalog: completed source review','',
 'Read all **198 assigned files**, **7,066 lines**, **327,419 bytes**, with zero pending:188Markdown bodies and10explicit empty-catalog TXT bodies. Six additional public source bodies (1,193lines) were reviewed to bind actual scanners and Pilot035 supersession. All original bytes remain unchanged.','',
 'The useful contribution is a collection of scoped audit controls and historical cases. The catalog does not implement a mathematical operad or establish general repair efficacy.13 fresh bounded controls were run; no historical pipeline, provider, native build or private benchmark was accessed.','',
 '## Claims','']
for c in claims:md += ['### '+c['id'],'',c['claim'],'',c['ceiling'],'']
md += ['## Findings','']
for f in findings:
 md += ['### '+f['id'],'',f['finding'],'',f['ceiling'],'','Next action: '+f['next_action'],'',
  'Evidence: '+ '; '.join('`'+e['path']+'`:'+','.join(str(a)+'–'+str(b) for a,b in e['lines']) for e in f['source_evidence'])+'.',
  ('Fresh controls: '+', '.join(f['probe_ids'])+'.') if f['probe_ids'] else 'Fresh execution: none; full source reasoning and explicitly attributed historical context.','']
md+=['## Reuse within existing workflows','', '| Mechanism | Existing families | Scope |','|---|---|---|']
for g in workflow_suggestions:md.append('| '+g['mechanism']+' | '+(', '.join(f['id']+' '+f['name'] for f in g['existing_workflows']) or 'Engineering support; no new family')+' | '+g['assessment']+' |')
md+=['','## Fresh controls','']
for p in checks['probes']:md+=['- **'+p['id']+'** '+p['claim']+' '+p['limit']]
md+=['','The exact outputs, source indices, population checks, hashes and line ranges are in the paired JSON and `_checks.json`. Existing report references are cross-references only, not repeated execution or whole-source transfer.','',
 '## File-specific assessments','']
for r in reviews:md += ['### '+r['path'],'',r['disposition']+'; full body1–'+str(r['source_line_count'])+'; SHA-256 `'+r['sha256']+'`.','',r['assessment'],'']
md+=['## Supporting source assessments','']
for r in extra:md += ['### '+r['path'],'','Full body1–'+str(r['source_line_count'])+'; SHA-256 `'+r['sha256']+'`.','',r['assessment'],'']
md+=['## Limits','']+['- '+s for s in report['limits']]
Path(str(P)+'.md').write_text('\n'.join(md)+'\n',encoding='utf8');print(json.dumps(report['summary'],indent=2))

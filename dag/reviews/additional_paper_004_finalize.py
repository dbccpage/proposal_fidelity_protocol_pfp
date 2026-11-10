"""Assemble completed Paper 004 reading receipts, preserving bounded artifact limits.

Only additional_paper_004* review outputs are written. No original is changed.
"""
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P = 'additional_paper_004'
BASE = 'papers/pfp/004_pfp_native_verification_and_evidence_custody/'
OUT = HERE / (P + '_inspection')

def sha(b): return hashlib.sha256(b).hexdigest()
def load(s): return json.loads((HERE / (P + s)).read_text(encoding='utf-8'))
def write(s, obj):
    (HERE / (P + s)).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

scope = load('_support_scope.json')
rows = {x['path']: x for x in scope['files']}
all_rows = {x['path']: x for x in scope['files'] + scope['excluded_prior_full_reads']}
custody = load('_custody.json')
data = load('_data_validation.json')
translation = load('_manifest_translation.json')
probes = load('_probe_results.json')
tests = load('_test_results.json')
pdfs = json.loads((OUT / 'pdf_inventory.json').read_text(encoding='utf-8'))
pdf_equal = {x['path']: x for x in load('_pdf_equality.json')}
notes = {}
for path in sorted(HERE.glob(P + '_notes*.json')):
    notes.update(json.loads(path.read_text(encoding='utf-8')))
coverage = {}
for read in load('_read_ledger.json'):
    if not read.get('output_truncated'):
        coverage.setdefault(read['path'], set()).update(n for a, b in read['reviewed_lines'] for n in range(a, b + 1))

def evidence(name, ranges=None):
    path = name if name.startswith(BASE) else BASE + name
    row = all_rows[path]
    count = len((ROOT / path).read_bytes().decode('utf-8').splitlines()) if row.get('lines') is None and not path.endswith(('.pdf', '.zip', '.gz')) else row.get('lines')
    return {'path': path, 'sha256': row['sha256'], 'lines': ranges if ranges is not None else ([[1, count]] if count else [])}

reviews = []
for name, assessment in notes.items():
    path = BASE + name
    row = rows[path]
    assert coverage.get(path, set()) == set(range(1, row['lines'] + 1)), path
    reviews.append({'path': path, 'sha256': row['sha256'], 'full_source_read': True,
                    'reviewed_lines': [[1, row['lines']]] if row['lines'] else [],
                    'review_level': 'full_source_body_read', 'assessment': assessment,
                    'temporal_note': 'Per-file notes describe reading-time execution status. Fresh checks, performed later, are separately bound in test_summary.'})

for pdf in pdfs:
    item = {'path': pdf['path'], 'sha256': pdf['sha256'], 'full_source_read': False,
            'reviewed_lines': [], 'reviewed_pages': [[1, pdf['pages']]],
            'review_level': 'visual_all_pages_with_explicit_equality_transfer',
            'assessment': 'Retained historical PDF presentation, not current source or fresh execution evidence. All pages visually covered directly or by recorded equality transfer. Text and tables were legible at rendered inspection resolution; no clipping observed. Historical names and the pre-correction zero-normal-form account differ from current manuscript. Preserve these deposit bytes and issue current errata rather than silently replacing history.',
            'binary_limit': 'No raw PDF object-stream or byte-by-byte textual reading claimed.'}
    if pdf['path'] in pdf_equal:
        item['equality_transfer'] = pdf_equal[pdf['path']]
        item['assessment'] += ' Every rendered page pixel-equals the stated range of the fully viewed combined examiner companion.'
    elif pdf.get('raw_equal_render_base'):
        item['equality_transfer'] = {'method': 'raw_byte_equality', 'base_path': pdf['raw_equal_render_base'], 'base_sha256': pdf['sha256']}
    else:
        item['direct_visual_review'] = {'page_count': pdf['pages'], 'sheets': pdf['sheets'], 'page_images': pdf['page_images']}
    if 'companion' in pdf['path'] or 'study_guide' in pdf['path']:
        item['presentation_note'] = 'Combined companion has repeated section pagination; the final study-guide page contains little text. This is layout economy, not missing evidence.'
    reviews.append(item)

manifest_counts = []
for manifest in custody['current_manifests']:
    stats = {'path': BASE + manifest['path'], 'entries': len(manifest['entries']),
             'raw_failures': sum(not x.get('raw_match') for x in manifest['entries']),
             'unresolved_after_lf': sum(not (x.get('raw_match') or x.get('lf_match')) for x in manifest['entries'])}
    manifest_counts.append(stats)
    reviews.append({'path': stats['path'], 'sha256': rows[stats['path']]['sha256'],
                    'full_source_read': False, 'reviewed_lines': [], 'review_level': 'all_records_parsed_hash_validation',
                    'parsed_record_count': stats['entries'], 'assessment': f"All {stats['entries']} manifest pairs parsed with path/digest/uniqueness checks and compared against loose bytes. {stats['raw_failures']} raw failures; {stats['unresolved_after_lf']} remain after testing LF normalization. The manifest currently fails custody for the loose draft. These are complete record checks, not prose or source-body reading.",
                    'validation_artifact': 'dag/reviews/' + P + '_custody.json'})
name = 'audited_source/SOURCE_MEMBERS.sha256'
reviews.append({'path': BASE + name, 'sha256': rows[BASE + name]['sha256'], 'full_source_read': False,
                'reviewed_lines': [], 'review_level': 'all_records_parsed_hash_and_path_delta_validation',
                'parsed_record_count': 7875, 'assessment': 'All 7,875 pairs compared with historical manifest and archive. Digest sequence is unchanged but 7,873 paths are renamed; current manifest therefore does not identify the actual archive paths. Historical embedded manifest matches all 7,875 archive members. No semantic source review is inferred from this record comparison.',
                'validation_artifact': 'dag/reviews/' + P + '_manifest_translation.json'})

large = {
    'code/chordal_fuzz_repair_benchmark_receipt.json': ('chordal', 100, 'All 100 seed/dimension/rank/defect/admission records checked. Seeds 0–99; 2-tree dimensions hold; mean 487/25, median 18, max 43. Zero after replacement follows the authored construction. Timings and historical execution are not independently reconstructed.'),
    'code/l1_sparsity_benchmark_receipt.json': ('sparsity', 50, 'All 50 IDs/counts/acceptance rows checked. Dense 4,208 and sparse 1,632 regex-counted units reproduce 2.58 compression and 61.22 percent reduction. Dense-false/sparse-true outcomes come from hardcoded templates and stored expected tokens; no model or independently checked arithmetic result follows.'),
    'code/topology50_benchmark_receipt.json': ('topology', 50, 'All 50 task rows checked. Governed 50/50 and ungoverned 0/50 are synthetic labelled choices; accepted 62 of proposed 115 gives 0.5391. Accounting balances. Timing and hardcoded Lean version do not attest kernel execution.'),
    'docs/historical_native_run/004_republication_gate_receipt.json': ('republication', 52, 'Parsed every one of 52 checks and 64 snapshot file records. PASS 24, NOT_VERIFIED 23, NOT_APPLICABLE 5; recorded_evidence arrays are empty, and final status is BLOCKED. All text differs from historical ZIP only by literal omega-to-core replacement, but neither version has been claimed as a full prose-body read. This is a retained checklist, not fresh independent certification.')}
for name, (key, count, assessment) in large.items():
    reviews.append({'path': BASE + name, 'sha256': rows[BASE + name]['sha256'], 'full_source_read': False,
                    'reviewed_lines': [], 'review_level': 'all_records_parsed_bounded_semantic_and_arithmetic_review',
                    'parsed_record_count': count, 'assessment': assessment,
                    'validation_artifact': 'dag/reviews/' + P + '_data_validation.json', 'validation_key': key})

# Full ZIP transfer uses already read base bodies plus every differing hunk.
# Hash equality alone never grants a full reading receipt.
manual_delta_indices = {5, 7, 9, 11, 13, 15, 28, 32, 43, 44, 46, 47, 49, 51, 54, 55, 56, 58, 60, 61, 74, 75, 77, 78, 79}
bounded_delta_indices = {4, 6, 17, 53}
full_paths = {r['path'] for r in reviews if r['full_source_read']} | {BASE + 'paper.md'}
review_index = {r['path']: r for r in reviews}
zip_path = BASE + '004_pfp_native_verification_and_evidence_custody_2026-10-02.zip'
zip_members = []
for i, original in enumerate(custody['zip_members']):
    item = dict(original)
    item.update(archive_path=zip_path, archive_sha256=rows[zip_path]['sha256'], full_source_read=False)
    base_full = item['current_path'] in full_paths
    if item.get('complete_diff_path'):
        assert i in manual_delta_indices | bounded_delta_indices, (i, item['member'])
        if i in manual_delta_indices:
            assert base_full, item['current_path']
            item.update(full_source_read=True, review_method='fully_read_current_base_plus_complete_manual_diff')
        else:
            item['review_method'] = 'all_record_parsed_base_plus_complete_automated_delta'
            item['limit'] = 'Complete delta computation/inspection of changed record rules does not convert bounded base data into full-body reading.'
        item['complete_diff_sha256'] = sha((ROOT / item['complete_diff_path']).read_bytes())
    elif item.get('current_raw_equal') or item.get('current_lf_equal'):
        item['review_method'] = ('fully_read_base_plus_raw_equality' if item.get('current_raw_equal') else 'fully_read_base_plus_complete_CRLF_LF_equality') if base_full else 'bounded_artifact_base_plus_raw_or_LF_equality'
        item['full_source_read'] = base_full
    else:
        raise AssertionError(('unaccounted ZIP member', item['member']))
    item['base_review_path'] = item['current_path']
    item['base_review_scope'] = 'full source body' if base_full else review_index.get(item['current_path'], {'review_level': 'archive_all_member_hash_custody_and_nine_full_selected_owner_bodies'})['review_level']
    if item['full_source_read']:
        # Historical line counts differ where a complete delta changed a source body.
        import zipfile
        with zipfile.ZipFile(ROOT / zip_path) as z:
            n = len(z.read(item['member']).decode('utf-8').splitlines())
        item['reviewed_lines'] = [[1, n]] if n else []
    zip_members.append(item)

reviews.append({'path': zip_path, 'sha256': rows[zip_path]['sha256'], 'full_source_read': False,
                'reviewed_lines': [], 'review_level': 'archive_all_members_custody_with_explicit_base_delta_dispositions',
                'assessment': 'All 88 regular member bytes hashed; CRC, safe/unique names and embedded manifests checked. Embedded 86-entry MANIFEST and 87-entry SHA256SUMS have no missing or mismatched bytes. Every member has explicit base/equality/delta disposition: 25 complete manual source/prose diffs, four bounded data/manifests deltas, other 59 raw/LF equality transfers. Full source reading transfers only when the base body was fully read; PDF/data/tar limits are preserved.',
                'member_disposition_artifact': 'dag/reviews/' + P + '_support.json#zip_member_reviews'})

tar_path = BASE + 'audited_source/pfp-iv-native-source-52cb5457.tar.gz'
member_reads = {}
for row in load('_archive_read_ledger.json'):
    dst = member_reads.setdefault(row['member'], {'archive_path': row['archive_path'], 'archive_sha256': row['archive_sha256'], 'member': row['member'], 'sha256': row['sha256'], 'line_count': row['line_count'], '_lines': set()})
    assert row['sha256'] == dst['sha256']
    dst['_lines'].update(n for a, b in row['reviewed_lines'] for n in range(a, b + 1))
tar_assessments = {
    'omega_engine/crates_rs/omega_symbol_game/src/lib.rs': 'Complete module/export/build-contract include read. This names the host and dispatcher owners; it does not prove every exported action. Dependency modules not silently counted as read.',
    'omega_engine/crates_rs/omega_symbol_game/src/main.rs': 'Complete bounded stdin reader, runtime/default dispatch and three reader controls read. limit+1 bounds reads; runtime and Prime paths use distinct limits. classify-board uses plain serde separate from strict host protocol. No binary executed.',
    'omega_engine/crates_rs/omega_symbol_game/src/foundation.rs': 'Complete additive foundation API read. PrimitiveDifference is a supplied nullary marker; nonempty names/lowercase digests/nonnegative guards are explicit. No carrier or relation derived from the marker. Four imported submodules remain outside full member-reading coverage.',
    'omega_engine/crates_rs/omega_symbol_game/src/host.rs': 'Complete 1,176-line restricted admission host read. Packet/carrier bindings, exact solve/replay/candidate agreement, bounded integer transport and refusal branches are explicit. Source revision fields remain BOUND_ONLY; ExactBytesDetector certifies supplied bytes, not external truth. Prime adapter supplies cochain/square-zero justifications, while authority holes are expressly retained. This branch demands ExactRepair and nonzero before Gamma2. Solver, DDC and Prime dependencies were not comprehensively re-read; no end-to-end proof or fresh Rust execution claimed.',
    'omega_engine/crates_rs/omega_symbol_game/src/protocol.rs': 'Complete 830-line typed wire, duplicate-key visitor, exact integer parsing, allocation bounds and digest construction read. Unknown fields refused on typed host structures; semantic packet policy is distinct from cryptographic field binding. Outcome root is unkeyed consistency, not provenance. No claim every float is rejected before typed validation; generic visitor accepts finite floats.',
    'omega_engine/crates_rs/omega_symbol_game/tests/host_contract.rs': 'Complete 535-line test body read. Twelve authored controls include canonical before Phi1=7/Gamma2=12 fixture and malformed/rehashed carrier/candidate/image/allocation cases. The test named locally_rehashed_outcome actually alters one field without recomputing root; it demonstrates stale-root detection rather than rejecting a freshly recomputed forged root. These are test-source assertions, not fresh executed Rust tests.',
    'omega_engine_symbol_game/domain/packet_codec.py': 'Complete 126-line codec read. NFC normalization checks colliding keys, seal copies payload and builds digest envelope. verify_packet checks payload digest and AuthorityEffect only; parent/carrier/schema/family/envelope digest are not validated there. Return mapping is mutable. Paper correctly treats this as a payload helper, not full admission.',
    'omega_engine_providers/adapters/native_functional.py': 'Complete 118-line adapter read. Validates exact positive weighted graph input, refuses unknown/duplicate edges, binds executed binary SHA, rejects duplicate JSON keys and malformed result schema. SHA pin is caller-trusted; returned gauge/objective are not independently recomputed or certified by this wrapper, and forests_checked is only required to be positive. Subprocess use was not invoked; no fallback exists on this route.',
    'omega_engine_symbol_game/ffi.py': 'Complete 378-line thin action wrapper read. Delegates location/invocation to one OEOS seam and returns full typed outcomes. Convenience methods build named payloads for exact arithmetic, functional, certificate, Prime and application actions. Docstrings assert underlying capabilities, but this wrapper does not implement or prove them. Default host is a lazy singleton; no instance or native process was created.'}
tar_reviews = []
for name, row in sorted(member_reads.items()):
    assert row.pop('_lines') == set(range(1, row['line_count'] + 1)), name
    rel = name.split('/', 1)[1]
    row.update(full_source_read=True, reviewed_lines=[[1, row['line_count']]], assessment=tar_assessments[rel])
    tar_reviews.append(row)
assert len(tar_reviews) == 9
reviews.append({'path': tar_path, 'sha256': rows[tar_path]['sha256'], 'full_source_read': False,
                'reviewed_lines': [], 'review_level': 'archive_all_member_hash_custody_and_nine_full_selected_owner_bodies',
                'assessment': 'All 7,875 regular archive members inventoried and hashed, exactly matching the original manifest embedded in the historical ZIP. Nine selected host/protocol/adapter/test owners read completely (3,494 lines). The other 7,866 member bodies are not claimed as fully read. Current-inventory byte matches are custody metadata only and do not grant semantic reading. Eighteen nested ZIPs remain unexpanded; their public finite-QM log content is outside the bounded native host mechanism review. No bundled third-party code or archive code was executed.',
                'selected_member_count': len(tar_reviews), 'total_members': 7875,
                'unread_member_body_count': 7875 - len(tar_reviews),
                'nested_archives_not_expanded': custody['tar_summary']['nested_archives'],
                'member_inventory_artifact': 'dag/reviews/' + P + '_custody.json',
                'selected_member_reviews': 'dag/reviews/' + P + '_support.json#tar_selected_member_reviews'})

assert len(reviews) == len(rows) == 89
assert len({r['path'] for r in reviews}) == 89
assert {r['path'] for r in reviews} == set(rows)

claims = []
findings = []
def claim(suffix, statement, names, limits, status='source_read_with_bounded_controls'):
    es = [evidence(n) for n in names]
    claims.append({'id': 'PAPER004-' + suffix, 'statement': statement, 'status': status,
                   'evidence': [e['path'] for e in es], 'source_evidence': es, 'limits': limits})
def finding(suffix, severity, statement, named_ranges, action, probe=None):
    es = [evidence(n, r) for n, r in named_ranges]
    row = {'id': 'PAPER004-' + suffix, 'severity': severity, 'statement': statement,
           'evidence': [e['path'] for e in es], 'source_evidence': es, 'recommended_action': action}
    if probe:
        row['validation'] = 'dag/reviews/' + P + '_probe_results.json'
        row['probe_ids'] = probe
    findings.append(row)

claim('FINITE-EXACT-WITNESS', 'For the supplied four-vertex orientation, potential (0,-2,-2,-1) leaves residual (5,2,0,0,0); divergence-free dual (1,1,1,0,0) has equal objective 7. The face sums are 7 and 5, giving Gamma2=12. These finite exact arithmetic checks certify this L1 optimum and show zero is not gauge-equivalent to the original input.', ['paper.md', '_lev_examiner_theoretical_minimum_quiz/instructor_key.md'], 'Supplied finite carrier, orientation and unit penalties. No general host refinement, empirical truth or autonomous repair follows.')
claim('WEIGHTED-CYCLE', 'For a supplied oriented cycle with positive rational penalties, the residual minimum is min(a)*abs(sum(w)); concentration on a cheapest edge attains it. A unique cheapest edge and nonzero circulation imply unique residual, while potentials retain gauge freedom.', ['docs/completion_supplement.md', 'code/tests/test_weighted_cycle_supplement.py'], 'Cycle result only; integer Lean statements and rational prose proof are distinct evidence. General graph strict-dual feasibility is not settled by this result.')
claim('CONDITIONAL-LEAN-SLICE', 'The supplied Lean bodies encode ordinary identity/quotient operations, assumed relation laws, finite Boolean and integer inequalities, incidence-column facts and elementary topology. They do not formalize the native host or prove a general total-unimodularity/LP-integrality theorem.', ['lean4/IdentityTypes.lean', 'lean4/SnTower.lean', 'lean4/SparseLanding.lean', 'lean4/SparseLandingGeneral.lean', 'lean4/TotalUnimodularity.lean', 'lean4/Topology50.lean'], 'Source review and parsed historical axiom counts only; current v4.35.0 toolchain was not compiled.', 'source_read_not_fresh_kernel_checked')
claim('CUSTODY-CEILING', 'The historical release ZIP has valid internal CRC and manifest bindings, and its original source-member manifest exactly covers the 7,875-file tar. This establishes byte consistency of supplied artifacts, not authorship, source-to-binary provenance or execution truth.', ['README.md', 'audited_source/README.md', 'docs/historical_native_run/README.md'], 'Unsigned commitments, unverified external source origin, no retained raw Cargo stdout and no fresh native build.')
claim('REUSABLE-WORKFLOW', 'Reusable mechanisms are exact finite primal/dual checking, carrier-bound typed replay, duplicate-key/canonical-image refusal, explicit admission boundaries, and custody ledgers with preserved historical/current identities. The paper is useful as a bounded systems case study and negative-control teaching package.', ['paper.md', 'paper_claim_ledger.md', 'code/deposit_paths.py'], 'Extraction into a workflow requires an independent checker for the target encoding and semantics; archived labels or expected answers cannot become a new sealed benchmark oracle.')

finding('ARCHIVE-PATH-TRANSLATION', 'reproduction_blocker', 'The loose source manifest retains the historical digest sequence but renames 7,873 of 7,875 paths. Current reproduction commands and CORE environment/wire names do not match the preserved tar containing omega_engine/omega_engine_symbol_game and OMEGA interfaces. Following the current literal instructions cannot reproduce the archived source identity.', [('audited_source/README.md', [[1, 100]]), ('audited_source/SOURCE_MEMBERS.sha256', []), ('README.md', [[1, 149]])], 'Preserve historical bytes; add a separate versioned reproduction guide/translation with exact archived paths and interface names. Do not silently rewrite the tar or treat path renaming as interface equivalence.')
finding('LOOSE-CUSTODY-MANIFESTS', 'custody_mismatch', 'MANIFEST has 43 raw failures and SHA256SUMS 44; 26 and 27 respectively remain after LF normalization. Historical embedded manifests are sound, but current loose manifests cannot support the README current-draft custody claim.', [('MANIFEST.sha256', []), ('SHA256SUMS', []), ('README.md', [[139, 149]])], 'After any separately authorized repair, publish distinct current manifests and preserve the historical archive/manifests as historical evidence.')
finding('ZERO-REPAIR-PEDAGOGY', 'pedagogical_scope_clarification', 'Current manuscript and TeX explicitly explain that replacing the nonclosed original cochain by zero changes the problem. Current study guide and Question 9 instructor wording retain final-normal-form language. They already caution that the original is not a gradient and that the result is not an arbitrary gauge change, but omit the manuscript\'s explicit problem-replacement explanation. Unchanged face sums 7,5 preclude any gauge transform to zero. Historical PDFs intentionally preserve the older wording.', [('_lev_examiner_theoretical_minimum_quiz/study_guide.md', [[45, 64]]), ('_lev_examiner_theoretical_minimum_quiz/instructor_key.md', [[16, 19]]), ('paper.tex', [[468, 473]])], 'Align the current teaching explanation with the explicit problem-change qualification; issue versioned errata while retaining historical PDFs intact.', ['four_vertex_exact_witness'])
finding('GOVERNOR-INPUT-BOUNDARY', 'checker_accepts_invalid_or_misencoded_inputs', 'Three finite controls expose independent boundary gaps: Edge-object keys validate after normalization but Python solve reads the original map (Phi 0 instead of 3); a section CUT commits NaN as IdempotentStationary; EDGE_MATCH for undeclared x,y accepts default zero values. Existing relational CUT type/completeness controls do not cover these branches.', [('code/l1_symbol_game_governor.py', [[266, 320], [557, 599], [739, 745]])], 'Use the normalized map consistently, reject nonexact/nonfinite section data, and require declared vertices/edges before matching. Add the three finite counterexamples before reusing this checker.', ['edge_key_normalization', 'nan_section_cut', 'undeclared_edge_verify'])
finding('SYNTHETIC-PROOF-ACCEPTANCE', 'benchmark_validity_gap', 'The interactive Lean governor never invokes its Lean verifier during evaluate_step. An arbitrary exact tactic with wrong goal/rule labels removes goal False and is accepted. Fifty labelled reference/distractor fixtures generate the governed-versus-ungoverned result; the current manuscript correctly excludes it as live Lean/LLM evidence.', [('code/interactive_lean4_governor.py', [[190, 297], [469, 608]]), ('code/tests/test_interactive_lean4_governor.py', [[1, 126]])], 'Keep as explicitly synthetic state-machine teaching data or bind each admitted proof step to an actual goal-aware checker. Do not promote the historical 50/50 receipt.', ['unchecked_false_proof'])
finding('STORED-ANSWER-REPLAY', 'benchmark_validity_gap', 'Sparsity replay compares a final expected token while REDUCE/PROVE accepts unconditionally; incorrect intermediate 17 mod 5 = 999 still passes with the stored landing token. Dense text is rejected by construction. The S3 fixture incorrectly equates s1*s2*s1 with s2*s1. Compression counts describe authored templates, not independently verified reasoning or model sparsity.', [('code/l1_sparsity_bullshit_benchmark.py', [[165, 233], [236, 496]])], 'Retain historical fixture status; use task-specific independent arithmetic/group checkers and correct the S3 example in a separately versioned current fixture before reuse.', ['stored_answer_replay', 's3_fixture_arithmetic'])
finding('FIREWALL-TRUSTED-CALLBACK', 'checker_scope_gap', 'The local pipeline accepts a correctly hashed output containing an alien carrier symbol from caller-supplied apply_fn, and recognized rule membership does not require an actual price. It checks content alphabet and replay hashes, not output alphabet or priced operational semantics.', [('code/packet_firewall_host.py', [[158, 228]])], 'State trusted apply_fn and output-schema assumptions explicitly, or validate the result carrier/rule costs before using this helper as an admission gate.', ['firewall_output_and_price'])
finding('DAG-INDEX-OMISSION', 'integrity_checker_gap', 'The events property exposes a mutable map while verify_integrity iterates insertion order. A directly inserted unindexed malformed event yields OK with only the original ordered node counted. Content hashing does not cover every live map entry.', [('code/conversational_repair_dag.py', [[151, 153], [266, 273]])], 'Prevent external map mutation and require exact agreement between event keys and order index before verifying every event.', ['dag_index_omission'])
finding('QUOTIENT-NORMAL-FORM', 'algorithm_scope_gap', 'For symmetry a<->b and rule b->c, reduce_to_normal_form(a) reports terminated a although reach(a) includes c. Redex search on one representative does not certify quotient normal form; supplied symmetry maps are also not checked as a closed group.', [('code/arity_rewrite_engine.py', [[270, 280], [478, 482]])], 'Either restrict the API to representative normal forms or check redexes over the declared complete orbit with explicit closure/bijection assumptions.', ['quotient_normal_form'])
finding('SPARSE-UNIQUENESS', 'certificate_completeness_gap', 'Adding an isolated vertex leaves the residual optimization unchanged yet flips the uniqueness certificate from true to false because it requires global off-support connectivity. The strict-dual routine also checks one free-variable-zero solution; its failure is not proof that no strict dual exists.', [('code/l1_sparse_landing.py', [[173, 264]])], 'Use componentwise residual uniqueness and distinguish sufficient witness failure from mathematical nonexistence. A general strict-dual claim needs a feasibility checker.', ['isolated_vertex_uniqueness'])
finding('CENSUS-AND-VERIFY-CEILING', 'verification_coverage_gap', 'Named axiom replay does not require nonempty rows or enforce its whitelist; self-consistent incomplete expectations can pass its check. verify_deposit can report proof/census success after build without Census/Core or expected output. The separate full-census parser has stronger nonempty/whitelist checks. No new Lean execution was performed.', [('tools/replay_lean_axiom_census.py', [[34, 84], [131, 138]]), ('verify_deposit.py', [[133, 172]]), ('tools/replay_full_axiom_census.py', [[1, 95]])], 'Require a nonempty declared module/declaration census and validated replay output; distinguish build success, named-list agreement and full environment coverage.')
finding('REBUILD-DESTROYS-HISTORY', 'maintenance_hazard', 'rebuild_release default refresh rescans the tree, rewrites manifests, creates a current ZIP and deletes older dated ZIP files despite its fixed-set description. Running it naively would erase intentionally retained historical releases.', [('tools/rebuild_release.py', [[1, 339]]), ('README.md', [[139, 149]])], 'Keep historical release immutable; require a distinct current output directory/version and explicit retirement policy before using this builder. It was not executed.')
finding('ATTENTION-EVIDENCE', 'measurement_scope_gap', 'Retained attention receipt is contrary to the withdrawn reduction claim: sparse has 78 versus 57 tokens, greater recorded entropy and total KV energy, with negative 37.5253 percent energy reduction. Hosted entropy renormalizes top-five alternatives; KV norm is scalar RMS, model revisions are unpinned, and per-condition fallback may mix models. No new model execution occurred.', [('code/attention_entropy_kv_norm_benchmark.py', [[1, 368]]), ('code/attention_entropy_kv_norm_receipt.json', [[1, 85]])], 'Preserve contrary receipt and exclusion from paper claims; any future measurement needs pinned models, complete inputs, matched conditions and correctly named statistics.')
finding('HISTORICAL-EXECUTION-LIMITS', 'provenance_gap', 'Historical native pass counts lack retained raw Cargo stdout and executable digest bindings. run_all counts seven stages passed although one is NOT_APPLICABLE. Current Lean pin v4.35.0 differs from historical v4.34.0-rc1 receipts. Fresh 58 companion tests do not transfer those native or Lean claims.', [('docs/historical_native_run/README.md', [[1, 47]]), ('docs/historical_native_run/004_run_all_receipt.json', [[1, 132]]), ('lean4/lean-toolchain', [[1, 1]]), ('lean4/axiom_report.txt', [[1, 12]])], 'Retain author-record labels and separate current source reading, historical execution and fresh companion probes. Any later native rerun needs explicit source/toolchain/binary/command/stdout bindings.')

report = {
    'schema_version': '1.0', 'status': 'scope_dispositions_complete_archive_semantics_bounded',
    'source_commit': scope['source_commit'], 'scope_manifest': 'dag/reviews/' + P + '_support_scope.json',
    'scope_summary': {'original_subtree_files': 90, 'excluded_prior_full_source_files': 1, 'assigned_paths': 89,
                      'full_source_bodies': 73, 'bounded_binary_or_data_paths': 16, 'unclassified_paths': 0,
                      'pdf_files': 7, 'pdf_pages_including_duplicates': 44, 'unique_directly_viewed_pdf_pages': 22,
                      'zip_members': 88, 'zip_full_source_body_transfers': sum(r['full_source_read'] for r in zip_members),
                      'tar_members_hashed': 7875, 'tar_member_full_bodies': 9,
                      'tar_selected_body_lines': sum(r['line_count'] for r in tar_reviews), 'tar_member_bodies_not_full_reviewed': 7866},
    'method': ['Freeze exact original inventory paths/hashes before reading.',
               'Full numbered body reads; earlier truncated combined displays were supplemented by clean range reads. The final receipt requires complete line coverage, not excerpts.',
               'Read current manuscript in full for context despite prior reading exclusion; no duplicate assigned receipt.',
               'Visually inspect 22 unique PDF pages and explicitly transfer four standalone PDFs by complete rendered-pixel equality and paper.pdf by raw equality.',
               'For every historical ZIP member, use complete current base body plus complete manual diff, raw/LF equality, or explicitly bounded artifact analysis. Hash equality alone is not semantic review.',
               'All large receipt records/manifests parsed and arithmetic checked; this does not become a full raw-text reading receipt.',
               'Read nine selected first-party tar owners completely; hash all members but do not infer broad semantic coverage or execute archived code.'],
    'file_reviews': sorted(reviews, key=lambda r: r['path']), 'remaining_scope': [],
    'remaining_deep_archive_scope': {'archive_path': tar_path, 'member_bodies_not_fully_read': 7866,
                                     'nested_zip_archives_not_expanded': 18,
                                     'ceiling': 'All assigned loose paths have dispositions; this is not full semantic review of every bundled archive member or nested log.'},
    'context_reads': [{'path': BASE + 'paper.md', 'sha256': all_rows[BASE + 'paper.md']['sha256'], 'full_source_read': True, 'reviewed_lines': [[1, 493]], 'assessment': 'Complete current primary manuscript reread for utility/claim comparison. Prior full receipt excluded this path from the 89-path assignment.'}],
    'claims': claims, 'findings': findings, 'zip_member_reviews': zip_members, 'tar_selected_member_reviews': tar_reviews,
    'archive_member_dispositions': {'zip': 'zip_member_reviews', 'tar_full_selected': 'tar_selected_member_reviews', 'tar_all_metadata': 'dag/reviews/' + P + '_custody.json'},
    'custody_summary': {'current_manifest_results': manifest_counts, 'historical_zip_manifests': custody['zip_manifests'], 'source_manifest_translation': translation},
    'test_summary': {'fresh_pytest_passed': 58, 'fresh_pytest_failed': 0, 'suite_files': 10,
                     'receipt': 'dag/reviews/' + P + '_test_results.json', 'finite_probe_count': 11,
                     'finite_probe_errors': 0, 'probe_receipt': 'dag/reviews/' + P + '_probe_results.json',
                     'probe_method': probes['method'], 'initial_probe_history': ['dag/reviews/' + P + '_probe_results_initial.json', 'dag/reviews/' + P + '_probe_results_second.json'],
                     'initial_history_note': 'Earlier helper setup/argument mistakes were corrected in the final probe. They are retained as audit history, not production findings.',
                     'native_build_performed': False, 'lean_kernel_replay_performed': False, 'model_execution_performed': False},
    'provider_calls': 0, 'private_answer_access': False, 'production_source_edits': 0,
    'limits': ['This is a source/custody audit with bounded offline tests, not a proof of the native system, source-to-binary identity, publication readiness or external semantic truth.',
               'Historical receipts are not fresh test evidence; newly passing tests are precisely the ten selected pure companion suites.',
               'The 16 binary/data paths have bounded dispositions and must not be promoted to full text-source coverage.',
               '7,866 tar member bodies and 18 nested ZIP contents remain outside full semantic coverage; byte hashes/equality counts are not reading receipts.',
               'No providers, network, credentials, sealed benchmark seed/private answer storage or uncontrolled native builds were used.',
               'No original source or historical artifact bytes were changed. No bibliography novelty claim or external URL availability was checked.'],
    'validation': ['dag/reviews/' + P + '_final_validation.json']}

# Validate source hashes, complete-read coverage and exact ranges before persisting.
checks = []
for row in scope['files'] + scope['excluded_prior_full_reads']:
    raw = (ROOT / row['path']).read_bytes()
    assert sha(raw) == row['sha256'], row['path']
    checks.append({'path': row['path'], 'sha256': row['sha256'], 'unchanged': True})
for item in reviews + report['context_reads']:
    if item['full_source_read']:
        count = len((ROOT / item['path']).read_bytes().decode('utf-8').splitlines())
        observed = {n for a, b in item['reviewed_lines'] for n in range(a, b + 1)}
        assert observed == coverage[item['path']] == set(range(1, count + 1)), item['path']
with tarfile.open(ROOT / tar_path) as archive:
    for row in tar_reviews:
        raw = archive.extractfile(row['member']).read()
        assert sha(raw) == row['sha256']
        assert len(raw.decode('utf-8').splitlines()) == row['line_count']
for item in claims + findings:
    for e in item['source_evidence']:
        raw = (ROOT / e['path']).read_bytes()
        assert sha(raw) == e['sha256']
        if e['lines']:
            count = len(raw.decode('utf-8').splitlines())
            assert all(1 <= a <= b <= count for a, b in e['lines']), e
assert len({x['id'] for x in claims + findings}) == len(claims) + len(findings)
assert len(probes['results']) == 11 and all(x['status'] == 'observed' for x in probes['results'])
assert tests['exit_code'] == 0 and '58 passed' in tests['stdout']
assert sum(x['full_source_read'] for x in reviews) == 73
assert all(all(x['rendered_pixel_equal_by_page']) for x in pdf_equal.values())
write('_support.json', report)

md = f'''# Paper 004 support audit

Disposition complete for all 89 assigned original paths: 73 full source/text bodies and 16 explicitly bounded binary/data artifacts. The already-reviewed 493-line manuscript was reread as context. No original bytes changed.

The paper is useful as a source-pinned finite systems case study. Independent exact arithmetic confirms the four-vertex minimum 7 and face obstruction 12; the weighted-cycle argument is a valid bounded mechanism. Neither establishes universal native correctness, external truth, neural improvement or source-to-binary provenance.

Fresh offline validation: **58 tests passed** across ten pure companion suites; **11 finite probes** completed. No Lean kernel replay, Rust build, archived code execution, provider call or model run occurred. Probe loading deliberately isolated fully read definitions from module bootstrap; it is not an end-to-end integration claim. Earlier probe-helper mistakes remain recorded as history.

All seven PDFs (44 pages including repeats) have complete visual page coverage: 22 unique directly viewed pages, exact pixel transfer for four standalone teaching PDFs, and byte equality for the repeated paper. Historical PDFs deliberately preserve earlier identities and wording.

The historical ZIP's 88 members and both embedded manifests are internally consistent. {sum(r['full_source_read'] for r in zip_members)} member source bodies transfer through fully read bases and complete equality/deltas; artifact limits stay bounded. The source tar's 7,875 member digests match its original historical manifest. Nine selected native/adapter/test owners ({sum(r['line_count'] for r in tar_reviews):,} lines) were read in full. The other 7,866 member bodies and 18 nested ZIP contents were **not** fully reviewed; custody inventory is not semantic coverage.

Current loose custody differs from history: 7,873 source-manifest paths were renamed without changing the tar, and literal reproduction/interface names now disagree with the archive. Current MANIFEST/SHA256SUMS have 26/27 unresolved mismatches after LF normalization. Preserve history and issue separate current reproduction/custody corrections.

## Findings

'''
for f in findings:
    md += f"- **{f['id']}** — {f['statement']} Action: {f['recommended_action']}\n\n"
md += '''## Reading and evidence limits

Per-file exact hashes, full-body ranges, assessments and artifact dispositions are in `additional_paper_004_support.json`. Complete ZIP transfers and nine tar-member receipts are separate from loose-file coverage. Generated receipt tables were parsed across all rows and their accounting checked; these records do not attest historical execution. Source tests and later fresh execution are recorded separately.

The JSON report carries five bounded claims, fourteen findings, retained historical-probe paths and the current test receipt. The final validation verifies all 90 original subtree hashes (89 assigned plus the context manuscript), source-reading ranges, nine tar-member body hashes, source-evidence ranges and report identifiers. Shared coverage, DAG and progress files were not modified.
'''
(HERE / (P + '_support.md')).write_text(md, encoding='utf-8')
validation = {'status': 'pass', 'original_paths_unchanged': len(checks), 'assigned_paths': len(reviews),
              'full_body_receipts_validated': 73, 'context_full_read_receipts_validated': 1,
              'bounded_artifact_receipts': 16, 'selected_tar_member_full_bodies_validated': len(tar_reviews),
              'selected_tar_member_lines': sum(r['line_count'] for r in tar_reviews),
              'source_evidence_ranges_validated': True, 'duplicate_claim_finding_ids': [],
              'fresh_pytest': '58 passed', 'finite_probes_observed': 11,
              'files': checks, 'report_sha256': sha((HERE / (P + '_support.json')).read_bytes()),
              'markdown_sha256': sha((HERE / (P + '_support.md')).read_bytes()),
              'scope_sha256': sha((HERE / (P + '_support_scope.json')).read_bytes()),
              'limits': 'Hash/range validation is not additional semantic reading or test execution.'}
write('_final_validation.json', validation)
print(json.dumps({k: v for k, v in validation.items() if k != 'files'}, indent=2))

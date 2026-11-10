"""Assemble reviewed dispositions; bounded data checks never become full-source credit."""
import collections
import hashlib
import json
import pathlib
import runpy

H = pathlib.Path(__file__).resolve().parent
R = H.parents[1]
P = 'additional_paper_011_recreated_receipts'
B = 'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/recreated_run/'


def read(s):
    return json.loads((H / (P + s)).read_text(encoding='utf-8'))


def write(s, value):
    (H / (P + s)).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


# The earlier checkpoint contains manually assessed notes for the initial complete reads.
runpy.run_path(str(H / (P + '_checkpoint.py')))
scope = read('_scope.json')
frozen = {x['path']: x for x in scope['files']}
prep = {x['path']: x for x in read('_preparation.json')['files']}
pop = read('_population_checks.json')
ctrl = read('_controls.json')
archive = read('_archive_comparison.json')
archive_rows = {x['path']: x for x in archive['files']}
original_leaves = {x['path']: x for x in archive['original_leaf_checks']}
leaves = {x['path']: x for x in pop['leaf_runs']}
ledger = {x['path']: x for x in read('_read_ledger.json')}
notes = read('_notes.json')

for path in notes:
    if '/demo_cohomology_battery/engine_run/receipt.json' in path:
        affected = '/affected_v3/' in path
        notes[path]['assessment'] = (
            'Complete input/solution/check population read: twelve supplied tasks, including two explicit '
            'out-of-scope controls (self-loop and restriction shape). ' +
            ('The diamond graph has supplied potential (3,0,0,1), dual (1,2,2,-1,-1), residual (4,2,0,0,0) '
             'and objective 8; its native L1 record is independently checked in controls.json. Nine other '
             'mathematical tasks remain UNKNOWN for absent operations. Three checks passing includes the '
             'two scope refusals and only one positive certificate. '
             if affected else
             'The diamond solver reports TypeError (bool object not callable), and nine further operations '
             'are unavailable. Ten UNKNOWNs are expressly not verified certificates. The two passed checks '
             'are scope refusals, with zero solved cases. ') +
            'Both editions declare INCOMPLETE/capability_pass=false, no operational DDC/adversary trace and '
            'unmeasured gluing defect. This is not a cohomology-battery success or empirical model trial.')
    elif '/demo_q40_quantum_solver/engine_run/receipt.json' in path:
        notes[path]['assessment'] = (
            'Complete small summary receipt read: 32 base cases plus eight invariance controls, 31 SOLVED '
            'and nine OUT_OF_SCOPE, 24 declared dense checks. Eight dimension/energy/status conjunction '
            'flags reconcile, but eigenpairs were not freshly reconstructed here. The verdict explicitly '
            'says deterministic solver pass with provenance unverified; actual billed cost, model identity, '
            'model size and comparative advantage remain unknown/not tested. The reference to a separate '
            'live-trial receipt does not supply its provenance within this file. No under-$1 or <=70B '
            'model achievement follows from capability_pass=true.')
    elif '/demo_12/engine_run/receipt.json' in path:
        notes[path]['assessment'] = (
            'Complete two-dossier refusal read. The catalog triangle fixture is explicitly distinct from '
            'E8/2-gauge and meron/torsion dossiers. Generic determinant/positive-definite/boundary/L1 ports '
            'are not used as dossier results; caller determinants and exact-zero declarations are untrusted. '
            'Missing cup/Chern-Simons/Green-Schwarz/meron/Phi4 actions prevent certification. Eight named '
            'near misses were opened but explicitly NOT_RUN_NO_NATIVE_PORT. certificate_authorizes=false; '
            'neither dossier has mathematical or native execution evidence here.')
    elif '/quarantine/' in path:
        notes[path]['assessment'] = (
            'Complete small quarantine record read: supplied NO_NATIVE_PORT epitope is retained permanently '
            'with AuthorityEffect=None and can_promote_to_core=false. A stored evidence digest and match '
            'label do not establish detector adequacy, independent signals or promoted runtime authority.')
    elif (ledger[path].get('exact_duplicate_source') not in (None, path)
          and '/engine_run/receipt.json' in path
          and any(v in path for v in ('/demo_6/', '/demo_7/'))):
        notes[path]['assessment'] = (
            'Complete semantic transfer from exact-byte-identical, fully read stdout at ' +
            ledger[path]['exact_duplicate_source'] + '. SHA and bytes independently compared. This caller '
            'stores the same NO_NATIVE_PORT diagnostic as an engine receipt: every supplied case is refused. '
            'Later composed editions retain the diagnostic unchanged; their separate native transport '
            'witnesses must be assessed separately and do not retrospectively upgrade this adapter.')
write('_notes.json', notes)


def reference(path, ranges=None, pointer=None):
    row = frozen.get(path)
    raw = (R / path).read_bytes()
    result = {'path': path, 'sha256': row['sha256'] if row else hashlib.sha256(raw).hexdigest(),
              'lines': ranges or [[1, max(1, len(raw.decode('utf-8').splitlines()))]]}
    if pointer:
        result['json_pointer_or_selector'] = pointer
    return result


def ev(rel, ranges=None, pointer=None):
    return reference(B + rel, ranges, pointer)


rows = []
for x in scope['files']:
    path = x['path']
    name = pathlib.PurePosixPath(path).name
    c = dict(pop['per_file_checks'][path])
    c.update(ctrl['per_file_checks'].get(path, {}))
    caller = path.rsplit('/', 1)[0] + '/recreation_receipt.json'
    leaf = leaves.get(caller)
    role = name
    if path in notes:
        full = True
        level = 'full_body_semantic_read'
        assessment = notes[path]['assessment']
        ranges = notes[path]['reviewed_lines']
    elif x['bytes'] == 0:
        full = False
        level = 'bounded_empty_artifact'
        ranges = []
        assessment = ('Complete byte check: empty historical ' + name + '. Contains no event or output. '
                      'Emptiness alone establishes neither failure nor success; the distinct caller leaf '
                      'supplies process status, and missing/empty evidence is not a mathematical certificate.')
    else:
        full = False
        level = 'bounded_population_assessment'
        ranges = []
        if name == 'job.json':
            o = original_leaves[caller]
            assessment = (f"Complete task/capability census for {c['kind']} {c['id']}: "
                          f"{c['declared_cases']} declared cases and {c['declared_mutations']} declared "
                          f"mutation entries; {c['capability_inventory_count']} source inventory entries. "
                          'Case/mutation references, control and binary pin shapes, runtime claim and caller '
                          f"ID/kind are checked. Original row digest match={o['job_row_digest_matches']}; "
                          f"original embedded capability pin match={o['job_capability_digest_matches']}. "
                          'The entire embedded inventory is data, not a semantic audit of its listed sources; '
                          'a historical executable path/hash is not a reproduced build or current execution.')
        elif name == 'recreation_receipt.json':
            o = original_leaves[path]
            bindings = c['artifact_bindings']
            assessment = (f"Caller {c['kind']} {c['id']} retains status {c['status']}, process exit "
                          f"{c['process_exit']}, {len(bindings)} artifact bindings, "
                          f"{sum(v['matches'] for v in bindings)} current matches. Original archive has "
                          f"{sum(v['matches'] for v in o['artifact_bindings'])} matching artifacts; original "
                          f"self digest match={o['self_digest_matches']}. Exact worker/status/count and "
                          'task-row reconciliation is recorded, including exception-vs-refusal and positive '
                          'vs negative/classifier distinctions. A receipt status or self-hash neither proves '
                          'the candidate mathematics nor authenticates historical model/binary execution.')
        elif name == 'worker_result.json':
            o = original_leaves[caller]
            assessment = (f"Complete result-to-caller comparison for {leaf['id']}, status {leaf['status']}: "
                          f"current equality={leaf['worker_result_matches']}, original equality="
                          f"{o['worker_result_matches']}. Counts and statuses are reconciled through all "
                          'retained evaluation events; all nine current worker disagreements are namespace '
                          'string changes, not observed outcome changes. This comparison does not execute '
                          'the checker or turn its labels into mathematical proof.')
        elif name == 'evaluations.jsonl':
            assessment = (f"All {c['records']} events classified for task linkage, candidate/result Boolean "
                          f"agreement, accepted output kinds {c['accepted_classes']}, and mutation outcomes "
                          f"{c['mutation_outcomes']}. Exceptions are separate from rejection; distinct source "
                          'mutants are separate from per-input attempts. Complete population arithmetic is '
                          'bounded metadata/content checking: embedded proofs, solver completeness and all '
                          'candidate semantics were not freshly verified. Selected C011/C024 witnesses have '
                          'separate independent arithmetic/graph controls.')
        elif name == 'import_adaptations.json':
            assessment = (f"All {c['source_rows']} source rewrite rows and "
                          f"{len(c['native_transport_rebindings'])} native transport rebindings classified; "
                          f"declared edits {c['declared_changes']}, unique paths={c['paths_unique']}. "
                          'Digest syntax and declared before/after equality are checked, not the semantic '
                          'equivalence of rewritten programs. Parent core finding P011CORE-F10 shows why '
                          'allowed-change labels cannot justify that stronger conclusion.')
        elif name == 'native_transport_calls.jsonl':
            assessment = (f"All {c['records']} transport records checked: capture modes {c['capture_modes']}; "
                          f"exit population {c['exits']}; {c['embedded_work_snapshot_bindings_checked']} "
                          'embedded work-file hashes recomputed, hex streams decoded, binary pins compared '
                          'to retained capability inventory, and before/after Lean input snapshots compared '
                          'where present. Legacy decoded/re-encoded text is not physical subprocess bytes. '
                          'Recorded native success and source-to-binary provenance are historical claims; '
                          'no binary was rerun. Separate exact controls cover six composed LP witnesses.')
        elif name == 'native_calls.jsonl':
            assessment = (f"All {c['records']} logical native records classified by actions {c['actions']}; "
                          f"action/response alignment={c['action_response_alignment']}. Independently "
                          f"reconstructed {len(c['finite_certificate_controls'])} supplied L1 certificates "
                          'with rational residual, dual feasibility and equal objective values. These '
                          'records can repeat witnesses from another edition or solve/verify call; they '
                          'are not independent trials, fresh process provenance or complete port coverage.')
        elif name == 'batch_receipt.json':
            assessment = (f"Complete batch of {c['run_count']} rows/{c['unique_ids']} IDs: requested IDs "
                          f"complete={c['requested_ids_complete']}, all demonstrations completed="
                          f"{c['all_demonstrations_completed']}, status population {c['status_population']}. "
                          'Leaf self-digest/status/exit links checked in current and original editions; '
                          'requested enumeration is not mathematical success or evaluator independence.')
        elif name.startswith('coverage_matrix'):
            assessment = (f"Complete overlay census: {c['row_count']} rows/{c['unique_ids']} IDs, declared "
                          f"{c['declared_entries']}, completed={c['all_recreations_completed']}. Every row "
                          'was joined to its assigned leaf for bytes, status, counts, exits and separate '
                          'mutant/output classes; batch closure pins also checked. Original ZIP restores '
                          'these links, while current raw byte links drift. Selection among historical '
                          'editions and assistant supplements is not a pooled model-success denominator.')
        elif name.startswith('engine_capability'):
            assessment = (f"Complete inventory census: {c['inventory_count']} source entries with digest "
                          f"syntax valid={c['inventory_all_sha256']}; binary pins, claimed runtime and "
                          'source-to-binary provenance recorded separately. No listed source body, binary '
                          'or historical build is semantically certified by membership. The original '
                          'archive leaves 116 job-embedded capability pins unresolved.')
        elif name == 'execution_configuration.json':
            assessment = (f"Runtime configuration claim inspected: dont_write_bytecode="
                          f"{c['dont_write_bytecode']}, initial cache entries={len(c['initial_cache_entries'])}, "
                          f"isolated cache prefix recorded={c['pycache_prefix_recorded']}. Runtime profile "
                          'and verifier paths/digests are historical pins, not a current environment '
                          'attestation, clean execution proof or semantic result.')
        elif name.endswith('.oeos-envelope'):
            assessment = (f"Opaque {c['schema']} for {c['artifact_schema']}, protector "
                          f"{c['protector_id']}: declared plaintext bytes {c['declared_byte_length']}, "
                          f"decoded ciphertext bytes {c['decoded_ciphertext_bytes']}. Base64 envelope and "
                          'external custody checked only. No key access, decryption, plaintext reading, '
                          'authentication or assertion that the declared plaintext hash is correct.')
        elif name == 'trace.jsonl':
            assessment = (f"All {c['records']} events ({c['events']}) checked for index/previous-hash "
                          f"continuity where present; terminal seal present={c['terminal_seal_present']}. "
                          'Stored links and CHECKED/RunSealed labels are not event authentication, source '
                          'truth, math success or a crash/power-loss durability experiment.')
        elif name == 'answers.jsonl':
            assessment = (f"Complete {c['records']}-record/{c['unique_ids']}-ID answer census, statuses "
                          f"{c['status_counts']}; reconciled with corresponding engine receipt. Unknown, "
                          'scope refusal and solved outputs are separate. Historical solution matrices, '
                          'eigenpairs and topology witnesses are not all freshly verified; finite selected '
                          'L1 checks are explicitly separate.')
        elif name == 'receipt.json' and '/engine_run/' in path:
            if 'pharmacology_cases' in c:
                detail = (f"{c['pharmacology_cases']} unique scripted failure-class cases, "
                          f"{c['repertoire_rows']} repertoire rows, {c['screen_count']} screens "
                          f"{c['screen_decisions']}, Signal2 population {c['signal2_population']}; clean "
                          'flags agree with empty matcher sets. Neither observed second signals nor '
                          'detector adequacy/learning/promotion efficacy is established. ')
            elif 'cells' in c:
                detail = (f"{c['cells']} cells exactly cover {c['arms']} arms by {c['fixtures']} fixtures, "
                          f"{c['step_count']} steps, terminal counts {c['terminal_counts']}, live_enabled="
                          f"{c['live_enabled']}. The native route is unavailable; scripted protocol traces "
                          'are not a six-arm empirical experiment. ')
            elif 'levels' in c:
                detail = (f"All {c['levels']} levels mss-000..100 and {c['cases']} finite fixture cases "
                          'were reconciled for exact census, local ID uniqueness and expected outcome/code '
                          f"flags ({c['expectation_failures']} expectation failures). All "
                          f"{c['product_pairings']} supplied product-ring pairings equal 2pq. This does "
                          'not rerun 101 checker implementations; manifold interpretation remains admitted. ')
            else:
                raise AssertionError(('unclassified non-full engine receipt', path, c))
            assessment = detail + 'Large nested data has bounded population review, not complete human semantic reading; raw artifacts and caller leaf remain distinct.'
        elif name == 'stdout.txt':
            assessment = ('Complete large JSON stdout decoded and associated with its engine receipt: ' +
                          ('24-case EIS fixture/repertoire and two-screen census' if 'eis_failure' in path
                           else '101-level/1,033-case system fixture census and 25 product pairings') +
                          ' checked in controls.json. This text is historical output, not a second '
                          'independent result. Its nested raw population was not fully human-read.')
        else:
            raise AssertionError(('unclassified artifact', path, c))

    archive_row = archive_rows[path]
    evidence = []
    if pop['per_file_checks'][path]:
        evidence.append({'artifact': P + '_population_checks.json', 'selector': 'per_file_checks[' + path + ']'})
    if path in ctrl['per_file_checks']:
        evidence.append({'artifact': P + '_controls.json', 'selector': 'per_file_checks[' + path + ']'})
    if name == 'worker_result.json':
        evidence.append({'artifact': P + '_population_checks.json', 'selector': 'leaf_runs[path=' + caller + ']'})
    if x['bytes'] == 0:
        evidence.append({'artifact': P + '_preparation.json', 'selector': 'files[path=' + path + '].empty'})
    for i, control in enumerate(ctrl['controls']):
        if control.get('path') == path or any(v.get('path') == path for v in control.get('cases', [])):
            evidence.append({'artifact': P + '_controls.json', 'selector': 'controls[' + str(i) + ']'})
    row = {'path': path, 'sha256': x['sha256'], 'bytes': x['bytes'], 'full_source_read': full,
           'review_level': level, 'reviewed_lines': ranges, 'assessment': assessment,
           'population_evidence': evidence,
           'original_archive_comparison': {k: archive_row[k] for k in
               ('archive_member', 'archive_member_sha256', 'archive_bytes', 'raw_equal', 'LF_equal')}}
    if full:
        row['read_receipt'] = {'artifact': P + '_read_ledger.json', 'selector': 'path=' + path}
        if ledger[path].get('exact_duplicate_source') not in (None, path):
            row['exact_duplicate_source'] = ledger[path]['exact_duplicate_source']
    rows.append(row)

claims = [
    {'id': 'P011REC-C01', 'claim': 'This slice preserves 122 historical leaf runs, eight batches and four 87-ID overlays; completion/case-count labels are separate from mathematical success and model accuracy.',
     'evidence': [ev('full_v2/batch_receipt.json', [[1, 1]]), ev('coverage_matrix_v7.json', [[1, 1]])],
     'dependencies': ['Full-population leaf/batch/overlay joins in population_checks.json; canonical JSON hash framing from recreate_demos.py.'],
     'limitations': ['No fresh provider or native run; overlays select among editions and supplements, so their rows are not independent experiments.']},
    {'id': 'P011REC-C02', 'claim': 'The current edition is not byte-replay closed. The original outer ZIP restores all 122 leaf, eight batch and four overlay self-digests, 348 overlay row links and 21 batch links, but leaves 116 original job artifact/capability bindings unresolved.',
     'evidence': [ev('full_v2/C001/recreation_receipt.json', [[1, 1]], '/artifacts_sha256/job.json'), ev('full_v2/C001/job.json', [[1, 1]]), reference(str(pathlib.PurePosixPath('dag/reviews') / (P + '_archive_comparison.json')))],
     'dependencies': ['Verified outer ZIP SHA-256 8bf43405313439d05383552f1281eaec96442dac7eb733134bcae1394863d6b3.', 'Only corresponding public members read; no repair to either edition.'],
     'limitations': ['An archive member match establishes bytes, not historical execution truth.', 'No source-backed capability transformation was found that explains the 116 original mismatches.']},
    {'id': 'P011REC-C03', 'claim': 'All 46 supplied positive C011 graph certificates attain their encoded finite weighted-L1 optima, by exact rational primal/dual equality with dual annihilation and weight bounds.',
     'evidence': [ev('full_v2/C011/evaluations.jsonl', [[x['line'], x['line']] for x in ctrl['controls'][0]['cases']])],
     'dependencies': ['Incidence orientation u=-1, v=+1; supplied vertices/edges/claims/positive weights.', 'For any p, y^T f = y^T(f-Dp) <= sum(w_i abs(f-Dp)_i) when D^T y=0 and abs(y_i)<=w_i; a feasible matching witness certifies the encoded optimum.', 'Fresh stdlib Fraction reconstruction in controls.py.'],
     'limitations': ['Only these positive retained certificates; no global solver completeness, refusal correctness, original case-file authenticity or general physical interpretation.']},
    {'id': 'P011REC-C04', 'claim': 'All 24 supplied positive C024 local-complement sequences reach the encoded target graph under independent finite edge toggling.',
     'evidence': [ev('final_bindings_v4/C024/evaluations.jsonl', [[x['line'], x['line']] for x in ctrl['controls'][1]['positive_sequences']])],
     'dependencies': ['Toggle each neighbor pair at each supplied vertex; compare resulting finite undirected edge set to g_prime.'],
     'limitations': ['The other 16 original records, including negative equivalence and scope refusals, were not solved; no exhaustive orbit search or fresh model result.']},
    {'id': 'P011REC-C05', 'claim': 'Six supplied Phi2/Phi3/Phi4 witnesses satisfy the consecutive cochain-zero products and exact finite weighted-L1 primal/dual objectives; values are respectively (1,2), (1,0), (1,2). Eleven additional logical native L1 records also reconstruct exactly.',
     'evidence': [ev(r, [[1, 2]]) for r in ['composed_phi2_v6/demo_6/native_transport_calls.jsonl', 'composed_phi3_phi4_v7/demo_7/native_transport_calls.jsonl', 'composed_phi3_phi4_v7/demo_9/native_transport_calls.jsonl']],
     'dependencies': ['Supplied rational matrices, fluxes, potentials, positive weights, residuals and dual witnesses.', 'Same finite LP weak-duality argument as C03; consecutive matrix products checked exactly.'],
     'limitations': ['Eleven logical records include duplicate solve/verify calls and repeated editions, not eleven independent experiments.', 'No manifold selection, cup-product law, Betti result, continuum physics or native-binary re-execution.']},
    {'id': 'P011REC-C06', 'claim': '785 native transport records admit syntactic byte/pin reconciliation and 1,400 embedded work-snapshot hash checks without observed binding errors; older decoded capture and newer physical-byte capture remain distinct.',
     'evidence': [ev('c041_pinned_v4/C041/native_transport_calls.jsonl', [[1, 1]]), ev('composed_phi2_v6/demo_6/native_transport_calls.jsonl', [[1, 2]])],
     'dependencies': ['Every retained stream enumerated in population_checks.json; hex decode, declared binary membership and embedded byte hashes checked.'],
     'limitations': ['Hash-valid bytes do not authenticate process origin, compiler source relation, proof kernel trust or universal verifier soundness. No recorded command was executed.']},
    {'id': 'P011REC-C07', 'claim': 'C041 original outcomes, C042 single-gate outcomes and later assistant-authored supplements must retain separate denominators.',
     'evidence': [ev('c041_original_and_supplemental_scope.md', [[1, 18]]), ev('c042_refusal_contract_audit.md', [[1, 13]]), ev('final_bindings_v4/C042/recreation_receipt.json', [[1, 1]])],
     'dependencies': ['C041 has 58 accepted original proof/refutation outputs, four malformed-input refusals and two heartbeat abstentions among 64; later two proposals/four controls are supplemental.', 'C042 final branch has 61 accepted cases, three contract residuals and 48 single-gate rejections, with zero dual-rejection count.'],
     'limitations': ['Shared wrappers/kernels do not constitute independent checker genealogy. No original solver score is improved by selecting later assistant proposals.']},
    {'id': 'P011REC-C08', 'claim': 'Immune, system-coverage and Q40 receipts provide bounded fixture/solver diagnostics rather than independent detector efficacy, system completeness, or verified low-cost model performance.',
     'evidence': [ev('affected_v3/demo_eis_failure_classes/engine_run/receipt.json', [[1, 1]]), ev('full_v2/demo_system_coverage/engine_run/receipt.json', [[1, 1]]), ev('full_v2/demo_q40_quantum_solver/engine_run/receipt.json', [[1, 1]])],
     'dependencies': ['24-case immune populations and two screens have no observed Signal2; 101 levels/1,033 system cases and 25 product pairings reconcile as encoded.', 'Q40 has 31 SOLVED/nine OUT_OF_SCOPE and eight recorded invariance controls; billing/model provenance is null or unverified.'],
     'limitations': ['Full-population consistency is not fresh semantic validation of every candidate.', 'Encrypted fixture envelopes were not decrypted; no benchmark/private key was accessed.', 'No efficacy, learning, model-size compliance or comparative advantage inference.']},
]

findings = [
    {'id': 'P011REC-F01', 'severity': 'high', 'category': 'historical_replay_custody',
     'finding': '116 job artifact hashes and embedded capability digests fail even in the original outer ZIP.',
     'evidence': claims[1]['evidence'],
     'details': 'Original archive controls restore all other 906 of 1,022 leaf artifact bindings; every remaining failure is job.json. All 122 original task-row digests and all 121 present worker-to-result comparisons pass. The original capability_v2 canonical digest is 3fce53c17726f93b4969736d423e6cadbe3a427fb47598cfced5d47d5fe14188, while full_v2 leaves pin 5931690780c2cb2c0bcfef45064f8b90ada37c0499e4fdf439beade645f131b2. The six pilot/prototype jobs pass; 116 later jobs fail. No exact source-backed rewrite account explains this gap.',
     'impact': 'The exact executed job/capability inputs cannot be reconstructed solely from these preserved files and recorded pins. This limits reproduction and source/binary attribution; it is not evidence that the independently checked finite mathematics is false.',
     'status': 'unresolved_original_archive_gap',
     'repair_backlog': 'Preserve both historical bytes and pins. Seek a separately evidenced transformation or missing original jobs; otherwise publish the unresolved binding limitation. Do not silently rehash history.'},
    {'id': 'P011REC-F02', 'severity': 'medium', 'category': 'edition_replay',
     'finding': 'Current checkout names/newlines invalidate historical receipt and overlay byte links; original ZIP controls recover most of that evidence.',
     'evidence': [ev('coverage_matrix_v7.json', [[1, 1]]), ev('full_v2/C001/recreation_receipt.json', [[1, 1]]), reference('dag/reviews/' + P + '_archive_comparison.json')],
     'details': 'Current leaf self-digests fail for 116/122; 394/1,022 leaf artifact links fail and all 348 overlay row raw hashes fail. Among the 1,164 compared archive members, 640 are byte-identical, 120 more become equal with CRLF-to-LF normalization, and 404 differ beyond newline normalization. Original ZIP restores every leaf/batch/overlay self-digest and overlay link; the separate F01 job gap persists. Nine current worker/result mismatches are exact namespace string replacements; all original workers match.',
     'impact': 'Running a strict historical receipt verifier directly on the relocated current tree will refuse. It would overstate evidence loss to treat archive-restorable drift as missing original receipt bytes.',
     'status': 'original_representation_preserved_current_replay_limited',
     'repair_backlog': 'Keep immutable archive-member verification and explicit edition mappings. Any future replay edition needs newly identified receipts, not silently overwritten historical pins.'},
    {'id': 'P011REC-F03', 'severity': 'medium', 'category': 'historical_result_classification',
     'finding': 'full_v2 C060 counts eight exception-killed mutants as dual rejections and labels 64 classifier decisions as non-refusal outputs.',
     'evidence': [ev('full_v2/C060/recreation_receipt.json', [[1, 1]], '/result/counts'), ev('full_v2/C060/evaluations.jsonl', [[712, 712], [770, 770], [830, 830], [882, 882], [940, 940], [989, 989], [1047, 1047], [1105, 1105]]), ev('affected_v3/C060/recreation_receipt.json', [[1, 1]])],
     'details': 'Retained events show 40 actual dual rejections and eight execution errors across 48 distinct source mutants (1,107 per-input mutation events), not 48 dual rejections. All 64 case outputs are CLASSIFIER_DECISION (32 ACCEPT/32 REJECT), not supplied positive mathematical certificates. The later affected_v3 receipt explicitly separates these counts and changes REFERENCE_SELF_CONSISTENT to REFERENCE_RESIDUAL.',
     'impact': 'Using the earlier summary alone inflates semantic rejection evidence and can misclassify reference classifier agreement as certification.',
     'status': 'corrected_in_later_edition_historical_overstatement_retained',
     'repair_backlog': 'Consumers must bind an edition and derive exception/refusal/classifier denominators from its retained events; preserve the historical earlier receipt unchanged.'},
    {'id': 'P011REC-F04', 'severity': 'low', 'category': 'historical_result_classification',
     'finding': 'full_v2 C049 places 21 accepted negative claims in its 57 non-refusal-output bucket.',
     'evidence': [ev('full_v2/C049/recreation_receipt.json', [[1, 1]], '/result/counts'), ev('full_v2/C049/evaluations.jsonl', [[1, 64]]), ev('final_bindings_v4/C049/recreation_receipt.json', [[1, 1]])],
     'details': 'The retained 64-case population contains 36 positive/non-refusal outputs, 21 negative claims and seven typed refusals. The final_bindings_v4 receipt separates these correctly. Across the 48 mutation controls, only 17 are dual rejections and 31 checker disagreements; joint detection is a different quantity.',
     'impact': 'An earlier aggregate cannot be treated as 57 positive mathematical results or 48 dual-validator rejections.',
     'status': 'corrected_in_later_edition_historical_counting_retained',
     'repair_backlog': 'Retain positive, negative, refusal and disagreement counts separately when reporting this challenge; no historical receipt edits.'},
]

full_count = sum(x['full_source_read'] for x in rows)
empty_count = sum(x['bytes'] == 0 for x in rows)
summary = {'files': len(rows), 'bytes': sum(x['bytes'] for x in rows), 'full_body_reads': full_count,
           'bounded_assessments': len(rows) - full_count, 'bounded_empty_artifacts': empty_count,
           'bounded_nonempty_artifacts': len(rows) - full_count - empty_count, 'pending': 0,
           'exact_duplicate_full_read_transfers': sum(bool(x.get('exact_duplicate_source')) for x in rows)}
report = {'source_commit': scope['source_commit'], 'status': 'complete_bounded_slice_disposition',
          'scope': summary, 'claims': claims, 'findings': findings,
          'validation': [
              {'kind': 'frozen_custody_and_strict_parse', 'artifact': P + '_preparation.json',
               'result': '1,164 exact hashes/byte counts match frozen scope; no strict JSON duplicate-key, nonfinite-token or syntax errors observed. Parsing alone receives no semantic reading credit.'},
              {'kind': 'population_checks', 'artifact': P + '_population_checks.json',
               'result': '122 leaves, eight batches, four overlays, 64 evaluation streams/7,818 events and 30 native transport streams/785 events checked; 1,400 embedded work hashes match. Historical exceptions and binding failures retained.'},
              {'kind': 'original_archive_controls', 'artifact': P + '_archive_comparison.json',
               'result': archive['summary'], 'archive_sha256': archive['archive_sha256']},
              {'kind': 'fresh_independent_finite_controls', 'artifact': P + '_controls.json',
               'result': {'C011_positive_certificates': 46, 'C024_positive_sequences': 24,
                          'composed_Phi2_Phi3_Phi4_witnesses': 6, 'additional_logical_L1_records': 11},
               'limit': 'Pure Python exact arithmetic/finite graph checks, not native or provider replay.'}],
          'file_reviews': rows, 'remaining_work': [],
          'unperformed_stronger_reviews': [
              'No full human semantic review of every large structured record, proof payload, encoded native byte stream or listed source inventory; those files carry bounded dispositions only.',
              'No decryption or semantic reading of two encrypted envelopes.',
              'No native rebuild/execution, broad current test-suite run, provider experiment or fresh model generation.',
              'No global solver completeness, checker independence/adequacy, physical interpretation, process authenticity or all-candidate mathematical certification.',
              'The 116 original job/capability binding failures remain open; current source bytes and historical pins were preserved.'],
          'related_reviews': [
              {'path': 'dag/reviews/additional_paper_011_core.json', 'use': 'Prior owner audit: P011CORE-F10 import-rewrite semantics, F11 subprocess boundary, F12 census limits. No automatic source-reading transfer from these references.'},
              {'path': 'dag/reviews/additional_paper_011_support.json', 'use': 'Context for reversible checkout drift and intact original ZIP. Independent corresponding-member checks performed here.'}],
          'limits': ['Completion means every frozen file received the stated disposition, not all 1,164 files were fully read or mathematically certified.',
                     'No private benchmark/seed/key access, provider call, historical command execution, original source edit or paid operation.']}
write('.json', report)

md = f'''# Paper011 recreated receipts

All **{len(rows):,} frozen files ({summary['bytes']:,} bytes)** have a disposition: **{full_count} full-body reads** and **{len(rows)-full_count:,} bounded assessments**, including {empty_count} empty artifacts. No file remains undisposed. Large structured data and ciphertext have not been promoted to full semantic reading. Source commit: `{scope['source_commit']}`.

The original ZIP restores all 122 leaf, eight batch and four overlay self-digests, all 348 overlay row links, and 21 batch links. Current names/newlines explain substantial replay drift. **116 original `job.json` hashes and corresponding capability pins remain unresolved even in the archive**; the other 906 leaf artifact links match. Historical bytes and pins were preserved.

Four findings are recorded with exact paths, hashes and ranges:

- **P011REC-F01:** unresolved original job/capability custody; exact executed job inputs cannot be reconstructed solely from the recorded pins and retained members.
- **P011REC-F02:** relocated current receipts are not directly byte-replay closed; original archive representations preserve most bindings.
- **P011REC-F03:** earlier C060 summaries counted eight execution exceptions as dual rejections and classifier decisions as non-refusal outputs. The later edition separates these correctly.
- **P011REC-F04:** earlier C049 summaries merged 21 negative claims into the positive/non-refusal bucket. The later edition corrects the categories and retains 31 checker disagreements.

Fresh, independent exact controls passed for **46 positive C011 certificates, 24 positive C024 sequences, six composed Phi2–Phi4 witnesses and 11 additional L1 records**. The L1 argument certifies only the supplied finite objective: a feasible dual annihilating the matrix lower-bounds every primal candidate, and matching feasible values attain the bound. Matrix carriers, positive weights and graph encodings are premises. Repeated calls/editions are not independent experiments; no topology, physical interpretation or universal solver claim follows.

Population checks cover 7,818 evaluation events, 785 native transport records, 1,400 embedded work-file hash bindings, all assigned task/result/overlay links, and distinct large fixture populations. The system receipt's 101 levels/1,033 cases, immune fixture screens without Signal2, incomplete cohomology battery, refused E8/meron dossiers and provenance-unverified Q40 summary retain their explicit limits. Later assistant supplements are separate from original solver denominators.

No native or provider replay was performed. No historical commands, private benchmark files, seeds or keys were accessed. No original source was changed. See the JSON per-file ledger, `_population_checks.json`, `_archive_comparison.json` and `_controls.json` for exact results and limitations; final independent integrity results are in `_validation.json`.
'''
(H / (P + '.md')).write_text(md, encoding='utf-8')
print(json.dumps(summary))

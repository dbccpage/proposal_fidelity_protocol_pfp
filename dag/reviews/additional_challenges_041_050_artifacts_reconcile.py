"""Attribute prior bounded checks and independently check selected public fixtures."""
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
PREFIX = 'additional_challenges_041_050_artifacts'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
prior_path = REV / 'additional_challenges_041_050.json'
assert sha(prior_path) == 'b49cc776037599163dfb96f60f6419a082caf4c0d0067aecc72009b1590784f8'
prior = load(prior_path)
scope = load(REV / (PREFIX + '_scope.json'))
selected = load(REV / (PREFIX + '_selected.json'))
extra = 'workflows/tasks/certified_challenges/c041_lean4_finite_lemma_proofs/judge_packet/cases/c041_base_08.json'
frozen = {r['path']: r for r in scope['files']}
selected.append({'path': extra, 'sha256': frozen[extra]['sha256']})
full = {r['path'] for r in selected}
assert len(full) == 35
auto = {r['path']: (i, r) for i, r in enumerate(prior['automated_reviews'])}
assert set(auto) == set(frozen) and len(auto) == 1045
for row in prior['file_reviews']:
    assert sha(ROOT / row['path']) == row['sha256']
for path, row in frozen.items():
    assert sha(ROOT / path) == row['sha256'] == auto[path][1]['sha256']

def public(name):
    paths = [p for p in full if p.endswith('/' + name)]
    assert len(paths) == 1
    return load(ROOT / paths[0])

controls = []
roots = [x for x in range(11) if x*x % 11 == 3]
assert roots == [5, 6]
controls.append({'id': 'CAF-P01', 'observed': {'roots_mod_11': roots},
                 'limit': 'Exact finite arithmetic refutes the retained REFUTATION label; no native Lean execution.'})
php = public('c042_pub_03.json')
maps = [x for x in itertools.product(range(php['holes']), repeat=php['pigeons']) if len(set(x)) == len(x)]
assert maps == [(0, 1), (1, 0)]
controls.append({'id': 'CAF-P02', 'observed': {'injective_assignments': maps},
                 'limit': 'Direct finite pigeon assignment, not replay of the CNF encoder or DRAT checker.'})
n = public('c043_pub_05.json')['n']
edges = list(itertools.combinations(range(n), 2))
triangles = [[edges.index(e) for e in itertools.combinations(t, 2)] for t in itertools.combinations(range(n), 3)]
colorings = [bits for bits in itertools.product((0, 1), repeat=len(edges))
             if all(len({bits[i] for i in triangle}) > 1 for triangle in triangles)]
assert n == 5 and len(colorings) == 12
controls.append({'id': 'CAF-P03', 'observed': {'assignments_examined': 2**len(edges), 'valid_colorings': len(colorings),
                                            'edge_order': edges, 'one_witness': colorings[0]},
                 'limit': 'Exhaustive two-color K5 triangle check only; does not prove an upper bound or other fixed constraints.'})
g = tuple(public('c044_pub_01.json')['gens'][0]); identity = tuple(range(2))
assert g != identity and tuple(g[g[i]] for i in range(2)) == identity
controls.append({'id': 'CAF-P04', 'observed': {'generated_permutations': [identity, g], 'generator_order': 2},
                 'limit': 'Direct C2 permutation closure; does not authenticate external catalog IDs.'})
pd = public('ex12_refusal_corrupt_edge.json')
counts = Counter(itertools.chain.from_iterable(pd['input']['pd']))
assert counts[2] == counts[9] == 1 and pd['expected_output']['witness']['label'] == 2
controls.append({'id': 'CAF-P05', 'observed': {'edge_multiplicities': dict(counts)},
                 'limit': 'Validates this malformed-PD refusal witness, not knot recognition or polynomial invariance.'})
rewrite = public('ex08_reduce_inverse_inverse.json')
assert ['inv(inv(x))', 'x'] in rewrite['input']['rules'] and ['mul(x, e)', 'x'] in rewrite['input']['rules']
assert rewrite['input']['term'] == 'mul(inv(inv(x)), e)' and rewrite['expected_output']['normal_form'] == 'x'
controls.append({'id': 'CAF-P06', 'observed': {'two_step_trace': ['mul(inv(inv(x)), e)', 'mul(x, e)', 'x']},
                 'limit': 'Two explicitly inspected substitutions, with irreducible variable endpoint; no global confluence or unique-normal-form theorem.'})
seq = public('c047_base_39_decoy_pi_digits.json')
prefix = seq['terms'] + seq['held_out_terms']
assert len(prefix) == 70 and prefix + ['0'] != prefix + ['1']
controls.append({'id': 'CAF-P07', 'observed': {'shared_prefix_length': 70, 'different_next_terms': ['0', '1']},
                 'limit': 'Finite supplied prefix alone cannot choose an unrestricted all-index sequence; no claimed recurrence search or pi-digit verification.'})
form = public('c048_gauge_41_perm_bca.json')
value = sum(int(form[k]) for k in ('a', 'b', 'c')); assert value == 0
controls.append({'id': 'CAF-P08', 'observed': {'nonzero_integer_point': [1, 1, 1], 'quadratic_value': value},
                 'limit': 'Exact point certificate for this one form; no local/global theorem invoked.'})
cat = public('c049_base_13_no_product_disc2.json')
cones = [apex for apex in cat['objects'] if all(any(src == apex and dst == target for _, src, dst in cat['morphisms']) for target in cat['diagram'])]
assert cones == []
controls.append({'id': 'CAF-P09', 'observed': {'candidate_apices': cat['objects'], 'cones': cones},
                 'limit': 'No cone, hence no product for the two distinct objects of this discrete category; not arbitrary category or adjunction validation.'})
bad = public('c050_poison_63_malformed_nested_int.json'); assert isinstance(bad['axioms'], int)
controls.append({'id': 'CAF-P10', 'observed': {'axioms_type': type(bad['axioms']).__name__},
                 'limit': 'Schema mismatch only; no theorem or model evaluation.'})
(REV / (PREFIX + '_controls.json')).write_text(json.dumps({'controls': controls, 'source_pins': selected}, indent=2) + '\n')

notes = {
 'c041_poison_02.json': 'Input names nonexistent_func with an empty prelude and an OUT_OF_SCOPE label. No Lean elaboration performed here; retained label remains an input expectation.',
 'c041_base_08.json': 'The existential modular equation has witnesses5 and6 by exact arithmetic; retained REFUTATION label is false. This independently confirms AC41-F02 without replaying Lean.',
 'c042_pub_03.json': 'Two pigeons and two holes have exactly two injective assignments; input-only SAT label supported by direct finite enumeration, not a DRAT replay.',
 'c043_pub_05.json': 'Unconstrained two-color K5 request admits12 of1024 colorings with no monochromatic triangle. The finite result does not establish an upper Ramsey bound.',
 'c044_pub_01.json': 'The nonidentity degree2 transposition squares to identity and generates exactly two permutations; C2 structure supported, external numeric catalog ID unverified.',
 'ex12_refusal_corrupt_edge.json': 'Full input, expected output and trace read. PD edge labels2 and9 each occur once; the label2/count1 refusal witness is correct. Trace text is not an execution receipt.',
 'ex08_reduce_inverse_inverse.json': 'Full input, output and trace read. The stated two rewrite rules give mul(inv(inv(x)),e) -> mul(x,e) -> x. This concrete reduction does not prove global confluence or uniqueness.',
 'c047_base_39_decoy_pi_digits.json': 'All35 observed and35 held-out decimal strings read. The pi/decoy label is not verified; two sequences can share these70 values and differ next. Bounded recurrence claims require their exact ansatz/start hypotheses.',
 'c048_gauge_41_perm_bca.json': 'The form x^2-2y^2+z^2 has the nonzero integer zero(1,1,1), directly checked; the gauge label supplies no broader theorem.',
 'c049_base_13_no_product_disc2.json': 'The discrete two-object category has only identity arrows, so neither object has legs to both diagram objects. There is no cone and thus no product.',
 'c050_poison_63_malformed_nested_int.json': 'The axioms field is integer12345 instead of a list. This is a schema-invalid request, not an equation refutation.',
}

family_claims = {c['id'].split('-')[0].replace('AC', 'C0'): c for c in prior['claims']}
rows = []; roles = Counter(); prior_rules = Counter(); misrouted = []; historical_bindings = []; manifests = []
for path, item in frozen.items():
    idx, record = auto[path]; checks = record['checks']; substantive = [c for c in checks if c['rule'] != 'json_structure']
    assert len(substantive) == 1
    check = substantive[0]; rule = check['rule']; prior_rules[rule] += 1
    family = path.split('/')[3][:4].upper(); claim = family_claims[family]
    if '/commit_reveal/' in path:
        role = 'historical_commitment_or_scoring_metadata'
        data = load(ROOT/path)
        note = 'Full historical metadata body read. Self-reported phase/time/hash/count/verdict fields with authority_effect=null are declarations; chronological commitment, cryptographic authentication and fresh correctness are not established.'
        if rule == 'problem_case_replay':
            misrouted.append({'path': path, 'prior_owner_verdict': check.get('owner_verdict')})
            note += ' Prior audit incorrectly routed this metadata through a problem checker; that result is excluded from problem-solve counts.'
        if 'solver_sha256' in data:
            solver = ROOT/('/'.join(path.split('/')[:4])+'/reference_solver/solver.py')
            raw = solver.read_bytes(); expected = data['solver_sha256']
            historical_bindings.append({'metadata': path, 'solver': solver.relative_to(ROOT).as_posix(), 'declared_sha256': expected,
              'current_raw_sha256': hashlib.sha256(raw).hexdigest(), 'current_lf_sha256': hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),
              'raw_match': hashlib.sha256(raw).hexdigest() == expected, 'lf_match': hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest() == expected})
    elif path.endswith('accounting.json'):
        role = 'budget_configuration_or_empty_accounting'
        note = 'Full configuration/accounting body read. Declared ceilings ofUSD0.25/0.50/1.00 and preferred targets are historical settings, not evidence of paid cost, tokens or elapsed time. Empty runs/calls and zeros are not zero-cost successful experiments. The prospective whole-run USD0.10 limit remains separate.'
    elif rule == 'manifest_raw_byte_binding':
        role = 'historical_manifest'
        data = load(ROOT/path); entries = data.get('entries', data.get('files')); base = ROOT/('/'.join(path.split('/')[:4]))
        outcomes = Counter()
        for rel, expected_record in entries.items():
            target = (base/rel).resolve(); assert target.is_relative_to(base.resolve())
            expected = expected_record['sha256'] if isinstance(expected_record,dict) else expected_record
            raw = target.read_bytes()
            raw_ok = hashlib.sha256(raw).hexdigest() == expected
            lf_ok = hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest() == expected
            outcomes['raw_match' if raw_ok else 'lf_only_match' if lf_ok else 'mismatch'] += 1
        manifests.append({'path': path,'entries':len(entries),'target_bindings':dict(outcomes),'status_label':data.get('manifest_status')})
        note = 'Bounded parsed custody reconciliation: '+str(dict(outcomes))+' over'+str(len(entries))+' listed entries. The manifest expressly says CURRENT_REGENERATED_NOT_A_PRE_RUN_COMMITMENT; no chronology or proof claim follows.'
    elif rule == 'finite_group_table_axioms_and_invariants':
        role = 'finite_group_catalog'
        note = 'Prior independent finite table-axiom and invariant calculations are retained for64 entries. Table validity is distinct from authenticating catalog names/numeric IDs; AC44-F02 records the mislabeled A4xC2 entry. No fresh catalog replay here.'
    elif rule == 'answer_stream_binding':
        role = 'retained_answer_stream'
        note = 'Prior per-line answer bindings and scoped checker results are retained; C041 records have no full native proof replay. These are historical examples, not authenticated provider outputs or fresh trials.'
    elif rule == 'case_or_mutation_array_replay':
        role = 'mutation_array' if 'hostile_mutations' in path else 'case_array'
        note = 'Prior bounded replay of'+str(len(check['records']))+' array records retained with exact per-route results. Shared parsers/checker defects and refusal outcomes remain qualified by '+claim['id']+'. This is not full manual body reading or fresh execution.'
    elif rule == 'mutation_envelope':
        role = 'stored_mutant'
        note = 'Prior stored-mutant envelope and per-route verdicts retained. C041 has parsed labels only; other finite route disagreements are not collapsed into consensus. Rejection of stored mutants does not establish detector adequacy.'
    elif rule in ('problem_case_replay','lean_case_envelope','public_input_output_pair'):
        role = 'retained_example' if rule == 'public_input_output_pair' else 'problem_input'
        note = 'Prior finite owner/reference or envelope assessment retained with its exact independent-evidence ceiling. Acceptance may mean refusal; C041 labels are not native proofs. Known family soundness and binding defects remain attached to '+claim['id']+'.'
    else:
        raise AssertionError((path,rule))
    if path in full and '/commit_reveal/' not in path and not path.endswith('accounting.json'):
        note = notes[Path(path).name]
    roles[role] += 1
    row = {'path':path, 'sha256':item['sha256'], 'full_source_read':path in full,
       'reviewed_lines':[[1,len((ROOT/path).read_text(encoding='utf-8').splitlines())]] if path in full else [],
       'review_level':'full_artifact_body_with_context' if path in full else 'bounded_prior_record_and_custody_assessment',
       'assessment':note, 'checker_limit_reference':claim['id'],
       'detail_receipt':{'path':prior_path.relative_to(ROOT).as_posix(),'sha256':sha(prior_path),'json_pointer':'/automated_reviews/'+str(idx),'prior_rule':rule,'corrected_role':role}}
    rows.append(row)
assert len(misrouted) == 9
reconciliation = {'prior_report_sha256':sha(prior_path),'current_artifact_pins_checked':1045,'prior_source_owner_pins_checked':162,
 'corrected_roles':dict(roles),'prior_check_rules':dict(prior_rules),'metadata_misrouted_as_problem_inputs':misrouted,
 'historical_solver_bindings':historical_bindings,'manifest_checks':manifests,
 'limits':['Current digest mismatch does not by itself refute historical execution; historical original bytes/chronology were not reconstructed.',
           'No former sealed_intel_dir path was opened; only public metadata records were inspected.']}
(REV/(PREFIX+'_reconciliation.json')).write_text(json.dumps(reconciliation,indent=2)+'\n')
ev = lambda paths: [{'path':p,'sha256':frozen[p]['sha256']} for p in paths]
report = {'schema_version':'1.0','status':'complete_declared_bounded_artifact_dispositions_with_source_reading_limits',
 'source_commit':scope['source_commit'],'scope_manifest':'dag/reviews/'+PREFIX+'_scope.json',
 'counts':{'scope':1045,'full_body_readings':35,'bounded_prior_record_dispositions':1010,'pending_dispositions':0},
 'file_reviews':rows,'pending_paths':[], 'source_body_reads_not_completed':[r['path'] for r in rows if not r['full_source_read']],
 'family_checker_limits':{k:{'prior_claim_id':v['id'],'statement':v['claim'],'limitations':v['limitations']} for k,v in family_claims.items()},
 'claims':[{'id':'CAF-C01','statement':'Independent finite controls confirm witnesses5 and6 for x^2=3 mod11, two injective2-to2 assignments, twelve triangle-free two-colorings ofK5, and an integer zero(1,1,1) of x^2-2y^2+z^2. These are scoped arithmetic/combinatorial certificates, not model-performance evidence.',
            'source_evidence':ev([p for p in full if any(p.endswith('/'+n) for n in ['c041_base_08.json','c042_pub_03.json','c043_pub_05.json','c048_gauge_41_perm_bca.json'])]),'validation':'dag/reviews/'+PREFIX+'_controls.json'}],
 'findings':[{'id':'CAF-F01','statement':'Nine public commitment/scoring metadata records were incorrectly routed through problem checkers in the prior audit. Their accepted/refused/rejected verdicts must be excluded from problem-solve counts; this reconciliation preserves the prior record and corrects its role.',
              'source_evidence':ev([r['path'] for r in misrouted]),'prior_report':prior_path.relative_to(ROOT).as_posix()}],
 'limits':['Thirty-five complete artifact bodies and1010 bounded contextual dispositions remain distinct.',
           'All10 prior mathematical summaries and39 finding statements were consulted; detailed diagnostic bodies were not all manually reread.',
           'Prior owner/native executions remain attributed historical audit evidence; this pass imports no original owner code and executes no native tool/provider.',
           'Configuration targets, historical metadata and example outputs are not measured efficacy or cost; no private benchmark content was accessed.']}
# Count consulted finding statements directly rather than relying on a hand total.
report['limits'][1] = f'All10 prior mathematical summaries and{len(prior["findings"])} finding statements were consulted; detailed diagnostic bodies were not all manually reread.'
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
(REV/(PREFIX+'_validation.json')).write_text(json.dumps({'status':'custody_and_bounded_controls_pass',**report['counts'],
 'prior_owner_source_pins':162,'controls':10,'report_sha256':sha(REV/(PREFIX+'.json')),'scope_sha256':sha(REV/(PREFIX+'_scope.json')),
 'limits':'Source custody and finite selected controls only; no overall mathematical or workflow-accuracy certification.'},indent=2)+'\n')
(REV/(PREFIX+'.md')).write_text('# C041-C050 artifact reconciliation\n\n'
 'The1,045 artifact dispositions comprise35 complete body readings and1,010 bounded contextual assessments. The162 earlier owner/specification/test reads are separately attributed and hash-matched.\n\n'
 'Nine metadata records previously sent to problem checkers are now excluded from solve counts. Historical declarations, regenerated manifests and empty accounting templates establish neither pre-run commitment nor paid model performance.\n\n'
 'Ten independent small controls check selected public fixtures. The Fin11 REFUTATION label is false; twelve of1,024 K5 two-colorings avoid monochromatic triangles. Other checks retain explicit schema, rewriting and finite-carrier limits. No original solver/native/provider was run.\n',encoding='utf-8')
manifest_path=ROOT/'dag/swarm_manifest.json'; manifest=load(manifest_path); report_name='dag/reviews/'+PREFIX+'.json'
if report_name not in manifest['completed_followup_slices']:manifest['completed_followup_slices'].append(report_name)
manifest['parent_active_slice']={'status':'selecting_next_scope','completed_report':report_name,**report['counts']}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'counts':report['counts'],'roles':dict(roles),'misrouted_metadata':len(misrouted),'manifests':manifests,
 'solver_pin_counts':dict(Counter('raw_match' if r['raw_match'] else 'lf_match' if r['lf_match'] else 'mismatch' for r in historical_bindings))}))

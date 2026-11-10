"""Audit eleven fully read, stdlib-only teaching notebooks; preserve source bytes."""
from contextlib import redirect_stdout
from fractions import Fraction
from io import StringIO
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
PREFIX = 'additional_pciv_notebooks_remaining'
scope_path = REV / (PREFIX + '_scope.json')
scope = json.loads(scope_path.read_text())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
rows = scope['files']
notes = [
    'Complete49-line notebook read. Deterministic sorted compact JSON hashing of four supplied fields; only identical-input equality is asserted. No PromptGenomeV1 owner, ExecutionOccurrenceV1 value, occurrence independence, custody authentication or schema admission is exercised. Empty outputs/null execution count are historical nonexecution metadata.',
    'Complete49-line notebook read. Two separate mutable dictionaries keep the single reference example out of the inheritance list. Edge-kind membership is asserted but self-loops, cycles and duplicates are admitted. No DAG or causal descent proof is implemented; one separation example is useful pedagogy only.',
    'Complete45-line notebook read. Half-open interval overlap refuses the one positive-length mutation example. Zero-length insertion inside protected text passes; negative/out-of-range or reversed spans are not admitted explicitly, and the prompt_bytes name holds a Python str. Source coordinates are character indices. The failure path prints rather than asserting, so the demo could finish if its refusal regressed.',
    'Complete41-line notebook read. Computes a truncated geometric weight on supplied hops, four examples asserted. No ancestry graph, repair propagation or immunity integration. Negative hops amplify and nonintegral hops pass; finite nonnegative integer domain and weight assumptions are external.',
    'Complete43-line notebook read. Exact Fraction pair dominance implements the stipulated maximize-both partial order on equal-length vectors. It does not construct a nondominated population/front. zip silently truncates unequal dimensions and no type/schema contract is enforced. One positive pair asserted.',
    'Complete42-line notebook read. Exact rational damping times the sum of two child scores is correctly evaluated. No graph, edge probabilities, normalization, teleportation, dangling handling, iteration or fixed point; this is one supplied credit aggregation, not a PageRank implementation or verified Markov diffusion.',
    'Complete40-line notebook read. Real-valued half-life formula with two exactly representable sample values. No retrieval/index/clock/persistence integration; zero half-life divides by zero and negative elapsed time increases the score. Domain assumptions are not enforced.',
    'Complete49-line notebook read. Largest-remainder-shaped allocation for three fixed quotas converts Fraction products to float before floor/remainder ranking. The sole population20 example has integer quotas and asserts total only. Large caps can exceed the claimed total due to rounding; negative/noninteger caps are unchecked. Ties favor higher reserve index via reverse tuple sorting.',
    'Complete46-line notebook read. Visited-set forward reachability on a finite supplied adjacency mapping computes the least root-containing successor-closed set, even with cycles. No causal authenticity, DAG admission or persistent custody invalidation is checked. The small example tests one included descendant and one excluded branch.',
    'Complete45-line notebook read. Rehashes a supplied payload with sorted JSON keys and asserts equality to a caller-provided digest. No event sequence, state fold, replay, idempotence, durable write or trust-root binding exists. Replacing payload and digest together passes. All historical outputs empty.',
    'Complete45-line notebook read. Migrates one list item by remove then append, with assert for source membership. No crossover or admission boundary is implemented. An invalid target index fails after removing the source item. No rollback, atomicity, duplicate/population preservation admission or durable state.',
]
assert len(notes) == len(rows) == 11
spaces = []
reviews = []
execution = []
for row, note in zip(rows, notes):
    path = ROOT / row['path']
    raw = path.read_bytes()
    assert sha(path) == row['sha256'] and len(raw) == row['size_bytes']
    lines = len(raw.decode('utf8').splitlines())
    notebook = json.loads(raw)
    assert notebook['nbformat'] == 4
    codes = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    assert len(codes) == 1 and codes[0]['outputs'] == [] and codes[0]['execution_count'] is None
    namespace = {}
    captured = StringIO()
    # All eleven complete source bodies were manually read before this helper was written.
    # Their code uses only stdlib arithmetic/containers and stdout; no project imports.
    with redirect_stdout(captured):
        exec(compile(''.join(codes[0]['source']), row['path'], 'exec'), namespace)
    spaces.append(namespace)
    execution.append({'path': row['path'], 'sha256': row['sha256'],
                      'status': 'reviewed_stdlib_code_cell_passed', 'stdout': captured.getvalue()})
    reviews.append({'path': row['path'], 'sha256': row['sha256'], 'full_source_read': True,
                    'reviewed_lines': [[1, lines]], 'source_line_count': lines,
                    'assessment': note, 'reviewer': 'parent',
                    'source_evidence': [{'path': row['path'], 'sha256': row['sha256'], 'lines': [[1, lines]]}]})

controls = []
def record(identifier, result, indices):
    controls.append({'id': identifier, 'status': 'observed', 'result': result,
                     'source_paths': [rows[i]['path'] for i in indices]})

topology = spaces[1]['LineageTopology']()
topology.add_inheritance_edge('A', 'A', 'DirectMutation')
assert topology.inheritance_dag == {'A': ['A']}
record('PCN-P01', {'self_loop_admitted': True}, [1])

edited = spaces[2]['apply_mutation']('abcdef', 2, 2, 'X', [(0, 4)])
assert edited == 'abXcdef'
record('PCN-P02', {'protected_original': 'abcd', 'insertion_inside_protected_span': edited,
                    'refused': False}, [2])

dominates = spaces[4]['dominates']
assert dominates((Fraction(1),), (Fraction(0), Fraction(100)))
pair_cases = 0
vectors = [(Fraction(a, 2), Fraction(b, 2)) for a in range(3) for b in range(3)]
for x in vectors:
    for y in vectors:
        assert dominates(x, y) == (x[0] >= y[0] and x[1] >= y[1] and x != y)
        pair_cases += 1
record('PCN-P03', {'equal_dimension_exact_cases': pair_cases,
                    'unequal_dimension_false_certificate': {'left': [1], 'right': [0, 100], 'dominates': True}}, [4])

allocation = spaces[7]['allocate_reserves']
large_caps = []
for power in range(53, 65):
    for delta in (-1, 0, 1):
        cap = 2**power + delta
        try:
            result = allocation(cap)
            if sum(result) != cap:
                large_caps.append({'cap': cap, 'allocation': result, 'sum': sum(result)})
        except (IndexError, OverflowError) as error:
            large_caps.append({'cap': cap, 'exception': type(error).__name__})
assert large_caps
record('PCN-P04', {'fixed_input_cases': 36, 'failures': large_caps,
                    'limit': 'No claim about normal small population caps.'}, [7])

reachability = spaces[8]['compute_forward_taint']
graph_cases = 0
for mask in range(512):
    graph = {i: [j for j in range(3) if mask & (1 << (3*i+j))] for i in range(3)}
    # Independent reflexive transitive closure by a Boolean matrix, including cycles.
    matrix = [[i == j or j in graph[i] for j in range(3)] for i in range(3)]
    for k in range(3):
        for i in range(3):
            for j in range(3):
                matrix[i][j] |= matrix[i][k] and matrix[k][j]
    for root in range(3):
        assert reachability(graph, root) == {j for j in range(3) if matrix[root][j]}
        graph_cases += 1
record('PCN-P05', {'finite_three_vertex_graph_and_root_cases': graph_cases,
                    'scope': 'Exact finite reachability, not causal or custody semantics.'}, [8])

payload = {'event_type': 'arbitrary replacement', 'prompt_id': 'different'}
event = {'payload': payload, 'payload_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()}
assert spaces[9]['verify_event_payload'](event)
record('PCN-P06', {'replacement_payload_and_matching_digest_pass': True,
                    'scope': 'Expected integrity-only behavior; no authenticated replay theorem.'}, [9])

ecology = spaces[10]['IslandEcology'](1)
ecology.islands[0].append('G')
try:
    ecology.migrate(0, 1, 'G')
except IndexError:
    assert ecology.islands == [[]]
else:
    raise AssertionError('Expected out-of-range target')
record('PCN-P07', {'invalid_target_exception': 'IndexError', 'remaining_population': ecology.islands}, [10])

assert spaces[3]['calculate_attenuated_weight'](-1) == 2.0
assert spaces[6]['evaporate_weight'](1.0, -5) == 2.0
record('PCN-P08', {'negative_hop_weight': 2.0, 'negative_elapsed_epoch_weight': 2.0,
                    'scope': 'Unenforced nonnegative domain, not contradiction on valid inputs.'}, [3, 6])

def evidence(index, low, high):
    row = rows[index]
    return {'path': row['path'], 'sha256': row['sha256'], 'lines': [[low, high]]}

claims = [
    {'id': 'PCN-C01', 'statement': 'The notebooks provide narrow scalar/container demonstrations: deterministic encoding, pairwise exact rational dominance, geometric weighting, supplied credit aggregation, and finite graph reachability. Their successful examples do not certify integrated PCIV learning, causal lineage, PageRank, durable replay or model efficacy.',
     'source_evidence': [evidence(0, 20, 38), evidence(4, 20, 32), evidence(5, 20, 31), evidence(8, 20, 35)]},
    {'id': 'PCN-C02', 'statement': 'The visited-set taint routine computes the least successor-closed set containing the supplied root on a finite graph, including cycles. An independent Boolean transitive-closure comparison covers all512 three-vertex graphs and all3 roots. It does not authenticate causal edges or persist invalidation.',
     'source_evidence': [evidence(8, 21, 30)], 'control': 'PCN-P05'},
]
findings = [
    {'id': 'PCN-F01', 'statement': 'The teaching mutation helper accepts zero-length insertion strictly inside a protected span because its overlap test requires positive intersection length. Inserting X at2 in abcdef with protected[0,4) yields abXcdef. This violates preservation of the protected text; the production forge is a separate owner.', 'source_evidence': [evidence(2, 21, 25)], 'control': 'PCN-P02'},
    {'id': 'PCN-F02', 'statement': 'The teaching Inheritance DAG is an unchecked dictionary: a self-loop is accepted. The two-dictionary separation example is useful, but does not verify DAG acyclicity or causal descent.', 'source_evidence': [evidence(1, 21, 38)], 'control': 'PCN-P01'},
    {'id': 'PCN-F03', 'statement': 'The exact dominance helper silently zips unequal coordinate vectors, so(1,) dominates(0,100) on the truncated prefix. It correctly handles all81 tested equal-length rational pairs but implements neither dimension admission nor a population Pareto front.', 'source_evidence': [evidence(4, 12, 32)], 'control': 'PCN-P03'},
    {'id': 'PCN-F04', 'statement': 'The largest-remainder notebook converts exact quotas to floats before floor/ranking. At sufficiently large integer caps the resulting population can exceed the cap or indexing can fail; the recorded fixed36-case control retains concrete examples. Its cap20 example does not expose this precision limit.', 'source_evidence': [evidence(7, 24, 38)], 'control': 'PCN-P04'},
    {'id': 'PCN-F05', 'statement': 'Several headings promise mechanisms absent from the code: occurrence independence has no occurrence object, inverse PageRank is one damped sum, event replay is a payload/digest equality assertion, and homologous crossover is a list migration. Preserve these as explicitly limited teaching examples, not completed workflows or mathematical certificates.', 'source_evidence': [evidence(0, 12, 38), evidence(5, 12, 31), evidence(9, 12, 34), evidence(10, 12, 34)]},
    {'id': 'PCN-F06', 'statement': 'The island migration helper removes the source genome before indexing the target. A nonexistent target raises IndexError after losing the genome from the source population. The notebook provides no atomicity/rollback boundary.', 'source_evidence': [evidence(10, 21, 28)], 'control': 'PCN-P07'},
]

report = {'schema_version': '1.0', 'status': 'complete', 'source_commit': scope['source_commit'],
          'scope_manifest': scope_path.relative_to(ROOT).as_posix(), 'scope_sha256': sha(scope_path),
          'counts': {'scope': 11, 'full_source_reads': 11,
                     'full_source_lines': sum(r['source_line_count'] for r in reviews), 'pending': 0},
          'file_reviews': reviews, 'pending_paths': [], 'claims': claims, 'findings': findings,
          'limits': ['Notebooks read in full, including JSON metadata; code cells executed only after complete source inspection.',
                     'No project/native/provider import, private benchmark access, original file mutation or production-owner behavior claim.',
                     'The original stored notebooks have empty outputs/null execution counts. Fresh execution receipts are separate.',
                     'Educational examples are not added to the completed benchmark workflow Wiki registry.']}
control_report = {'schema_version': '1.0', 'status': 'passed', 'scope_sha256': sha(scope_path),
                  'code_cell_executions': execution, 'controls': controls,
                  'limits': 'Reviewed stdlib-only notebook cells plus finite boundary/oracle controls; no production PCIV or provider execution.'}
for suffix, value in [('.json', report), ('_controls.json', control_report)]:
    (REV / (PREFIX + suffix)).write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
text = '# PCIV notebook audit\n\nAll11 remaining frozen PCIV notebooks were read in full. Their11 stdlib-only code cells pass the included examples. Eight additional finite controls preserve a stronger distinction between demonstrative arithmetic and implemented PCIV mechanisms.\n\n'
for item in claims + findings:
    text += '**' + item['id'] + '** ' + item['statement'] + '\n\n'
text += 'No production runtime, native code or provider calls were executed. Exact source pins, body notes and control outputs are in the companion JSON files.\n'
(REV / (PREFIX + '.md')).write_text(text, encoding='utf8')
for row in rows:
    assert sha(ROOT / row['path']) == row['sha256']
validation = {'status': 'validated', **report['counts'], 'source_pins_unchanged': 11,
              'reviewed_code_cells_executed': 11, 'independent_controls': len(controls),
              'report_sha256': sha(REV / (PREFIX + '.json')),
              'controls_sha256': sha(REV / (PREFIX + '_controls.json'))}
(REV / (PREFIX + '_validation.json')).write_text(json.dumps(validation, indent=2) + '\n', encoding='utf8')
print(json.dumps(validation))

"""Independent finite controls and source-cell replay; no providers or original writes."""
from pathlib import Path
import ast
from collections import Counter
from contextlib import redirect_stdout
import hashlib
import io
import itertools
import json
import os
import socket
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PKG = ROOT / 'papers/pfp/002_pfp_signed_presentations_and_search_frontier'
sys.dont_write_bytecode = True
sys.path.insert(0, str(PKG / 'code'))
from genesis_alpha import sign_graph as sg
import native_sign_graph as native

def forbidden(*args, **kwargs):
    raise AssertionError('Network/process launch is prohibited by this offline probe')

def independently_check_walk(vertices, edges, witness):
    assert witness.steps
    cursor = start = witness.steps[0][1]
    parity = 0
    for index, departure, arrival in witness.steps:
        assert 0 <= index < len(edges) and departure == cursor
        edge = edges[index]
        assert (departure, arrival) in ((edge.source, edge.target), (edge.target, edge.source))
        parity ^= edge.odd
        cursor = arrival
    assert cursor == start and parity == 1

counts = Counter()
by_size = {}
with patch.object(socket, 'socket', forbidden), patch.object(subprocess, 'run', forbidden):
    # For every unordered pair INCLUDING a loop: absent, even, odd, both.
    # Thus the corpus includes inconsistent parallel edges and odd self-loops.
    for size in range(4):
        vertices = tuple(str(i) for i in range(size))
        pairs = tuple(itertools.combinations_with_replacement(vertices, 2))
        size_counts = Counter()
        for choice in itertools.product(range(4), repeat=len(pairs)):
            edges = []
            for (source, target), mask in zip(pairs, choice):
                for odd in (0, 1):
                    if mask & (1 << odd):
                        edges.append(sg.SignedRewrite(source, target, odd))
            edges = tuple(edges)
            positions = {v: i for i, v in enumerate(vertices)}
            possible = [bits for bits in itertools.product((0, 1), repeat=size)
                        if all((bits[positions[e.source]] ^ bits[positions[e.target]]) == e.odd for e in edges)]
            result = sg.classify_sign_graph(vertices, edges)
            if possible:
                assert isinstance(result, sg.GaugeWitness)
                assert result.vertices == vertices and result.bits in possible
                assert sg.verify_gauge(vertices, edges, result)
                label = 'gauge'
            else:
                assert isinstance(result, sg.OddCycleWitness)
                independently_check_walk(vertices, edges, result)
                assert sg.verify_odd_cycle(vertices, edges, result)
                label = 'odd_walk'
            counts[label] += 1
            size_counts[label] += 1
        by_size[str(size)] = dict(size_counts)

    # Feed the adapter the exact error-field convention used by its bundled CLI.
    diagnostic = 'matrix must be symmetric'
    completed = subprocess.CompletedProcess(['mocked-native'], 0,
        json.dumps({'status': 'ERROR', 'message': diagnostic}), '')
    with patch.object(native.subprocess, 'run', return_value=completed):
        try:
            native._run_native(Path('offline-fixture'), {}, 1)
        except native.NativeSignGraphRefused as exc:
            error_observed = str(exc)
        else:
            raise AssertionError('Native ERROR unexpectedly admitted')
    assert diagnostic not in error_observed

    # Demonstrate only the documented shape/trust boundary, not an actual Rust bug.
    payload = {'status': 'PASS', 'result_type': 'gauge',
               'witness': {'vertices': ['0', '1'], 'bits': [0, 0]}}
    edge = (sg.SignedRewrite('0', '1', 1),)
    with (patch.object(native, 'find_binary', return_value=Path('offline-fixture')),
          patch.object(native, '_run_native', return_value=payload)):
        proposed = native.classify_sign_graph(('0', '1'), edge)
    assert not sg.verify_gauge(('0', '1'), edge, proposed)

    main_controls = []
    for name in ('demo1_signed_gauge.py', 'demo2_frontier_search.py', 'demo3_fock_obstruction.py'):
        source = (PKG / 'code' / name).read_text(encoding='utf-8-sig')
        parsed = ast.parse(source)
        main = parsed.body[-1]
        assert isinstance(main, ast.If) and '__name__' in ast.unparse(main.test)
        calls = []
        namespace = {'__name__': '__main__', 'run_demo': lambda: calls.append(False) or False}
        exec(compile(ast.Module(body=[main], type_ignores=[]), name + ':original_main', 'exec'), namespace)
        assert calls == [False]
        main_controls.append({'file': name, 'false_return_observed': True, 'main_block_returns_normally': True,
                              'scope': 'Original final main block with controlled run_demo; full demo not mutated.'})

    notebook_path = PKG / 'jupyter_notebooks/signed_exchange_and_frontier.ipynb'
    notebook = json.loads(notebook_path.read_text(encoding='utf-8-sig'))
    old_cwd = Path.cwd()
    namespace = {'__name__': '__main__'}
    cells = []
    try:
        os.chdir(PKG)
        for index, cell in enumerate(notebook['cells']):
            if cell['cell_type'] != 'code':
                continue
            stream = io.StringIO()
            with redirect_stdout(stream):
                exec(compile(''.join(cell['source']), f'{notebook_path}:cell{index}', 'exec'), namespace)
            stored = ''.join(''.join(x.get('text', [])) for x in cell.get('outputs', [])
                             if x.get('output_type') == 'stream' and x.get('name') == 'stdout')
            observed = stream.getvalue()
            cells.append({'cell_index': index, 'passed': True, 'stdout_matches_stored': observed == stored,
                          'stdout': observed})
    finally:
        os.chdir(old_cwd)

assert sum(counts.values()) == 4165
assert len(cells) == 5 and all(x['stdout_matches_stored'] for x in cells)
source_files = ['code/genesis_alpha/sign_graph.py', 'code/native_sign_graph.py',
                'code/genesis_alpha/frontier_search.py', 'code/rust/src/bin/solve_sign_graph.rs',
                'jupyter_notebooks/signed_exchange_and_frontier.ipynb']
report = {
    'status': 'bounded_offline_controls_complete', 'python': sys.version,
    'source_sha256': {p: hashlib.sha256((PKG / p).read_bytes()).hexdigest() for p in source_files},
    'exhaustive_graph_control': {'graph_count': sum(counts.values()), 'counts': dict(counts), 'by_vertex_count': by_size,
        'scope': 'All 0-3 vertex graphs with each unordered pair/loop absent, even, odd or both; no arbitrary-size completeness claim from enumeration.'},
    'native_diagnostic_control': {'expected_detail': diagnostic, 'actual_exception': error_observed,
        'typed_refusal_preserved': True, 'detail_lost': True},
    'native_trust_boundary': {'shape_valid_false_gauge_constructed': True, 'independent_python_verifier_rejects': True,
        'actual_rust_backend_exercised': False, 'classification': 'documented_native_trust_boundary_not_proof_of_backend_defect'},
    'demo_main_controls': main_controls, 'notebook_code_cells': cells,
    'notebook_limit': 'Ordinary Python namespace source replay and stdout equality; no Jupyter kernel/display/transport verification.',
    'provider_calls': 0, 'network_calls': 0, 'private_answer_access': False,
}
(OUT / 'additional_paper_002_probes.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'graphs': sum(counts.values()), 'classification_counts': dict(counts),
                  'notebook_cells': len(cells), 'all_notebook_stdout_equal': True, 'diagnostic_lost': True}))

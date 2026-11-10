"""Read-only checks of the 31 frozen teaching bodies; no production imports."""
from pathlib import Path
from fractions import Fraction as Q
import dataclasses
import hashlib
import json
import re
import typing
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / 'dag/reviews/additional_eis_pciv_teaching_scripts'
scope = json.loads(Path(str(P) + '_scope.json').read_text())
links = []
for row in scope['files']:
    p = ROOT / row['path']
    body = p.read_bytes()
    assert hashlib.sha256(body).hexdigest() == row['sha256']
    for i, line in enumerate(body.decode().splitlines(), 1):
        for m in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', line):
            target = m.group(1).strip('<>')
            parts = urlsplit(target)
            if parts.scheme or not parts.path:
                continue
            resolved = (p.parent / unquote(parts.path)).resolve()
            links.append({'path': row['path'], 'line': i, 'target': target,
                          'resolved': str(resolved), 'exists': resolved.exists(),
                          'inside_repo': resolved.is_relative_to(ROOT)})

controls = []
matrix = ((Q(1, 2), Q(1, 2)), (Q(3, 4), Q(1, 4)))
rank = (Q(57, 97), Q(40, 97))
rhs = tuple(Q(17, 20) * sum(matrix[j][i] * rank[j] for j in range(2)) + Q(3, 40)
            for i in range(2))
assert rank == rhs and sum(rank) == 1
controls.append({'id': 'two_node_stationary_equation', 'input_matrix': [[str(x) for x in r] for r in matrix],
                 'candidate': list(map(str, rank)), 'rhs': list(map(str, rhs)), 'passed': True,
                 'ceiling': 'Independent Fraction arithmetic for the narrated P->C default example only; no native solver execution.'})

def seats(n):
    if n < 4:
        return [(0,0,0),(1,0,0),(1,1,0),(2,1,0)][n]
    ratios = (60,30,10)
    out = [n * r // 100 for r in ratios]
    order = sorted(range(3), key=lambda i: (-(n * ratios[i] % 100), i))
    for i in order[:n-sum(out)]:
        out[i] += 1
    return tuple(out)
assert all(sum(seats(n)) == n and min(seats(n)) >= 0 for n in range(10001))
assert seats(10) == (6,3,1) and seats(20) == (12,6,2)
controls.append({'id':'script_reserve_arithmetic', 'capacities_checked':10001,
                 'n10':seats(10), 'n20':seats(20), 'passed':True,
                 'ceiling':'Independent unbounded-integer transcription of the script; no native machine-integer overflow or policy-optimality claim.'})

edges = {(0,1),(1,2)}
independent = [mask for mask in range(8) if all(not (mask & (1<<a) and mask & (1<<b)) for a,b in edges)]
maximum = max(mask.bit_count() for mask in independent)
assert maximum == 2 and 5 in independent
controls.append({'id':'support_path_example', 'maximum_independent_set_size':maximum, 'witness':['A','C'],
                 'passed':True, 'ceiling':'Eight subset checks of the three-node narrated graph; graph nonadjacency does not prove causal/statistical independence.'})
assert Q(1)+Q(25,256) == Q(281,256)
controls.append({'id':'per_use_decay_arithmetic','result':str(Q(1)+Q(25,256)), 'passed':True,
                 'ceiling':'The stated sum only, not the origin of its contribution epochs or a retrieval-performance claim.'})

level = next(r for r in scope['files'] if r['path'].endswith('/levels/level_08_regulatory_supervision_and_anergy.md'))
body = (ROOT/level['path']).read_text(encoding='utf-8')
snippet = re.search(r'```python\n(.*?)\n```', body, re.S).group(1)
ns = {'dataclass':dataclasses.dataclass, 'List':typing.List, 'Optional':typing.Optional}
# Entire fenced body was read. It defines only two dataclasses and a len-based method.
exec(compile(snippet, level['path']+':92', 'exec'), ns)
receipts = [ns['FalsePositiveReceiptV1']('duplicate', 'other-detector', '', '') for _ in range(5)]
proposal = ns['TregSupervisor']().evaluate_detector('target-detector', receipts, 1)
assert proposal.detector_id == 'target-detector' and proposal.accumulated_false_positives == 5
controls.append({'id':'level08_receipt_binding_counterexample','source_path':level['path'],
                 'source_sha256':level['sha256'],'snippet_lines':[93,130],
                 'supplied_detector':'other-detector','duplicate_receipt_count':5,
                 'empty_subject_and_auditor':True,'proposal':dataclasses.asdict(proposal),
                 'confirmed':True,
                 'ceiling':'Literal lesson snippet with standard-library typing/dataclass names supplied; not execution of the different production TregSupervisor.'})

result = {'status':'complete_read_only_static_and_bounded_arithmetic_checks',
          'scope_files':len(scope['files']), 'scope_hashes_match':True,
          'links':links, 'link_summary':{'local_link_occurrences':len(links),
              'missing':sum(not r['exists'] for r in links),
              'resolved':sum(r['exists'] for r in links),
              'outside_repo':sum(not r['inside_repo'] for r in links)},
          'controls':controls,
          'limits':['Link existence checks do not read targets or verify anchors. Repeated links remain separate occurrences.',
                    'No native package, provider, notebook kernel or production owner executed.',
                    'Only the reviewed Level08 literal snippet was executed, plus independent finite arithmetic.',
                    'Original source and notebook bytes were not changed.']}
Path(str(P)+'_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'links':result['link_summary'],'controls':controls},indent=2))

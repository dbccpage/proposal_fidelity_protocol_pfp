"""Run from the repository root: python -I -X utf8 dag/pfp/campaign/make_queue.py

Write the derivation-campaign queue: unattempted OPEN/CONDITIONAL/IMPORTED nodes with a mathematical statement, ranked by
downstream impact (trunk weighted x3). Coordination/custody records are excluded by stage and by statement shape."""
import json, collections, subprocess, re

dag = json.load(open('dag/derivation_dag.json', encoding='utf-8'))
nodes = {n['id']: n for n in dag['nodes']}
out = collections.defaultdict(set)
for r in dag['routes']:
    for i in r['inputs']:
        out[i].add(r['output'])
runs = subprocess.run(['git', 'ls-tree', '-d', '--name-only', '-r', 'HEAD', '--', 'dag/results'],
                      capture_output=True, text=True).stdout.split()
attempted = {p.split('/')[2] for p in runs if len(p.split('/')) == 5 and p.split('/')[3] == 'runs'
             and not re.search(r'_ladder(_\d+)?$|_byhand_', p.split('/')[4])}   # unverified by-hand replies are not attempts
EXCLUDED_STAGES = {'ENGINE_CUSTODY', 'AUTHORIZATION', 'FINITE_OBSTRUCTION', 'IMPLEMENTATION', 'COMPUTATION'}
RECORD_SHAPE = re.compile(r'^(F\d{3}|Shelf|Chapter|Ledger row|The S000|qm_\d+|Rung|Continuation attempt|Challenge \d)', re.I)
TRUNK = {'PREGENESIS', 'GENESIS', 'MSSN_SN', 'WDP', 'L1_EMERGENCE', 'L1_TO_L2', 'FINITE_QM_CORE', 'FINITE_QM_DYNAMICS',
         'FINITE_QM_STRUCTURE'}


def descendants(n):
    seen, stack = set(), [n]
    while stack:
        for m in out[stack.pop()]:
            if m not in seen:
                seen.add(m)
                stack.append(m)
    return seen


queue = []
for nid, n in nodes.items():
    st = (n.get('statement') or '').strip()
    if (n['status'] not in ('OPEN', 'CONDITIONAL', 'IMPORTED_ASSUMPTION') or nid in attempted
            or n['stage'] in EXCLUDED_STAGES or RECORD_SHAPE.match(st)):
        continue
    d = len(descendants(nid))
    queue.append({'node_id': nid, 'stage': n['stage'], 'status': n['status'], 'downstream_nodes': d,
                  'score': d * (3 if n['stage'] in TRUNK else 1), 'statement': st, 'bottleneck': n.get('bottleneck', ''),
                  'imported_structure': n.get('imported_structure', []), 'lean': n.get('lean', []), 'rust': n.get('rust', []),
                  'python': n.get('python', [])})
queue.sort(key=lambda q: (-q['score'], q['node_id']))
for i, q in enumerate(queue, 1):
    q['rank'] = i
json.dump({'generated_from': 'dag/derivation_dag.json at HEAD', 'rule': __doc__, 'count': len(queue), 'queue': queue},
          open('dag/pfp/campaign/derivation_queue.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for q in queue[:55]:
    print('%3d %4d %-46s %-22s %s' % (q['rank'], q['score'], q['node_id'], q['stage'], q['statement'][:90]))
print('total', len(queue))

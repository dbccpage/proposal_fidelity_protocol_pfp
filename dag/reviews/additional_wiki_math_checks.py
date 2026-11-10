"""Small independent exact countermodels; no source imports or external calls."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
paths = [
    'wiki/Rewriting-PFP-Graph-Prompts.md', 'wiki/Rewriting-Shells.md',
    'wiki/Rewriting-Shells-Example.md', 'wiki/Rewriting-MSS-N-Examples.md',
    'wiki/Rewriting-Genesis-Examples.md', 'wiki/Rewriting-PFP-Dialects.md',
    'wiki/Paper-014.md',
]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def derivative(theta):
    return (theta[1]-theta[0], theta[2]-theta[1], theta[2]-theta[0])
def difference(theta, edges):
    return tuple(a-b for a,b in zip(derivative(theta), edges))
def circulation(edges):
    return edges[0] + edges[1] - edges[2]

theta = (0,0,0)
first = (2,3,7)
second = (3,2,7)
assert circulation(first) == circulation(second) == -2
assert difference(theta,first) != difference(theta,second)
# To map theta=0 to theta=0 under theta'=theta+alpha requires alpha=0.
# Such a transformation leaves A unchanged: these pairs are not gauge equivalent.
gauge_controls = []
for alpha in [(0,0,0),(1,-2,3),(-4,5,0)]:
    shifted = tuple(a+d for a,d in zip(first,derivative(alpha)))
    assert difference(alpha,shifted) == difference(theta,first)
    gauge_controls.append({'alpha':alpha, 'A_after':shifted,
                           'D_after':difference(alpha,shifted)})

repairs = [(F(0),F(0),F(-2)),(F(2,3),F(2,3),F(-2,3))]
repair_controls = []
for delta in repairs:
    after = tuple(F(a)+d for a,d in zip(first,delta))
    assert circulation(after) == 0
    assert sum(map(abs,delta)) == 2
    repair_controls.append({'delta':[str(x) for x in delta],
                            'l1':str(sum(map(abs,delta))),
                            'support':sum(x != 0 for x in delta)})

packets = []
for relative in paths:
    in_fence = False
    for line_number,line in enumerate((ROOT/relative).read_text(encoding='utf-8').splitlines(),1):
        if line.strip().startswith('```'):
            in_fence = not in_fence
            continue
        token = line.strip()
        if not in_fence or not token.startswith('<') or not re.fullmatch('[a-z0-9<>]+', token):
            continue
        depth = minimum = 0
        for char in token:
            depth += (char == '<') - (char == '>')
            minimum = min(minimum,depth)
        packets.append({'path':relative,'line':line_number,'depth':depth,
                        'minimum':minimum,'balanced':depth == 0 and minimum >= 0})

result = {
    'source_files':[{'path':p,'sha256':digest(ROOT/p)} for p in paths],
    'gauge_counterexample':{
        'theta':theta,'A':first,'B':second,'common_holonomy':-2,
        'D_A':difference(theta,first),'D_B':difference(theta,second),
        'gauge_equivalent_pairs':False,
        'reason':'Preserving zero vertex phases forces alpha=0; unequal edge arrays cannot then transform into one another.',
        'positive_controls':gauge_controls,
    },
    'l1_optimal_repairs':repair_controls,
    'l1_lower_bound':'abs(delta_ab+delta_bc-delta_ac)=2 <= sum(abs(delta)); both repairs attain2, so L1 alone does not select sparse support.',
    'shell_checks':{'edge_values':first,'graph_residual':2,'cycle_pairing':-2,
                    'functor_defect':-2,
                    'reason':'All three values derive from the same supplied linear functional on this triangle; no probabilistic independence or multiplied confidence follows.'},
    'packet_balance_checks':packets,
    'packet_limits':'Only complete fenced single lines beginning< and using Gamma38 are checked for bracket balance. This is not a grammar,role,semantic or all-example validation.',
    'limits':['Pure exact finite algebra only; no physics derivation, external source verification, source-module execution, provider call or private benchmark access.'],
}
(REV/'additional_wiki_math_checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'gauge_counterexample':True,'l1_supports':[x['support'] for x in repair_controls],
                  'packet_count':len(packets),'unbalanced':[p for p in packets if not p['balanced']]}))

"""Build ten deterministic local teaching exercises; no provider calls."""

from hashlib import sha256
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent


def build():
    cells = [
        nbf.v4.new_markdown_cell("""# Ten useful ways to play

Read [the route guide](06_ten_useful_ways_to_play.md) for the goal, limits,
and next step of each exercise. These are finite teaching exercises, not native
host functional calculations or evidence that an MSS lift is licensed.
Every CHECKED outcome below has only the scope of its stated local rule.
No provider is called and no output directory is created.
"""),
        nbf.v4.new_code_cell("""from pathlib import Path
import sys
from copy import deepcopy
from fractions import Fraction

here = Path.cwd().resolve()
lesson = here if (here / 'educational_governor.py').is_file() else here / 'education/documentation/004_oepfp/_how_to_play'
repo = next(p for p in [lesson, *lesson.parents] if (p / '.git').exists())
sys.path.insert(0, str(lesson))
sys.path.insert(0, str(repo / 'education/documentation/004_oepfp/papers/symbol_game/000_pfp_introduction/code'))
from basic_packets import check, example
from educational_governor import EducationalHostGovernor

def board(fuel=10):
    return EducationalHostGovernor([0,1,2], ['0->1','1->2','2->0'],
                                   {'0->1':2, '1->2':1, '2->0':3}, fuel=fuel)

def cut(host, value):
    return host.execute_move({'move_type':'CUT', 'payload':{'proposed_claims':{'2->0':value}}})
"""),
    ]
    exercises = [
        (
            "1. Distinguish marks",
            "A directed distinction must meet the declared goal.",
            """receipt = check(example())
assert receipt['status'] == 'CHECKED'
print(receipt)""",
        ),
        (
            "2. Repair a packet",
            "Repair the candidate without silently changing the carrier.",
            """packet = example(['a','separates','c'])
assert check(packet)['reason'] == 'OUTSIDE_CARRIER'
packet['candidate'][-1] = 'b'
assert check(packet)['status'] == 'CHECKED'
print(check(packet))""",
        ),
        (
            "3. Predict and test",
            "Write a prediction, then compare it with changed-input checks.",
            """predictions = ['SELF_RELATION','GOAL_UNMET','CHECKED']
candidates = [['a','separates','a'], ['b','separates','a'], ['a','separates','b']]
outcomes = [check(example(c)) for c in candidates]
assert [r.get('reason',r['status']) for r in outcomes] == predictions
print(outcomes)""",
        ),
        (
            "4. Repair a finite graph",
            "These moves change reports; they are not gauge transformations.",
            """host = board()
defects = [host.compute_total_defect()]
for value in [-1,-3]:
    assert cut(host,value)['decision'] == 'ADMITTED'
    defects.append(host.compute_total_defect())
assert defects == [6,2,0]
print('Triangle circulation defects:', defects)""",
        ),
        (
            "5. Check a certificate",
            "A potential witnesses consistency of this triangle. This is not an optimality certificate.",
            """reports = {'0->1':Fraction(2),'1->2':Fraction(1),'2->0':Fraction(-3)}
potential = {0:Fraction(0),1:Fraction(2),2:Fraction(3)}
def consistent(p):
    return all(p[v]-p[u] == reports[f'{u}->{v}'] for u,v in [(0,1),(1,2),(2,0)])
assert consistent(potential)
altered = dict(potential); altered[2] += 1
assert not consistent(altered)
print('Valid potential passes; altered potential fails.')""",
        ),
        (
            "6. Refuse an unsafe claim",
            "The teaching model refuses a carrier escape. Missing native ports are exercised separately in demos 8 and 10.",
            """host = board(); before = dict(host.claims)
receipt = host.execute_move({'move_type':'CUT','payload':{'proposed_claims':{'3->4':0}}})
assert receipt['decision'] == 'REFUSED_CARRIER_DOMAIN'
assert host.claims == before
print(receipt)""",
        ),
        (
            "7. Challenge an argument",
            "Falsify the assertion that reversing a relation still meets the directed goal.",
            """counterexample = example(['b','separates','a'])
assert check(counterexample)['reason'] == 'GOAL_UNMET'
print('Irreflexivity survives; the directed goal does not:', check(counterexample))""",
        ),
        (
            "8. Learn from rejection",
            "Reproduce a retained defect and include a valid control, so rejecting everything cannot pass.",
            """retained = deepcopy(example(['a','separates','a']))
first, replay = check(retained), check(deepcopy(retained))
assert first == replay and replay['reason'] == 'SELF_RELATION'
assert check(example())['status'] == 'CHECKED'
print('Counterexample replay:', replay)""",
        ),
        (
            "9. Check an extension",
            "Illustrative finite up/down maps only. This example licenses no Genesis or MSS transition.",
            """old_terms = ['a','b']
def up(mark):
    return ('old', mark)
def down(term):
    return term[1] if term[0] == 'old' and term[1] in old_terms else 'NON_DESCENT'
assert all(down(up(mark)) == mark for mark in old_terms)
assert down(('new','c')) == 'NON_DESCENT'
print('Old-image round trips pass; new term gives NON_DESCENT.')""",
        ),
        (
            "10. Compare bounded strategies",
            "Both strategies have the same triangle, goal, checker, and four-attempt budget. No global performance claim follows.",
            """records = []
for name, values in [('direct',[-3]),('incremental',[1,-1,-3])]:
    host = board(fuel=4)
    outcomes = [cut(host,value)['decision'] for value in values]
    receipt = host.execute_move({'move_type':'VERIFY'})
    assert receipt['decision'] == 'ACCEPTED_ZERO_DEFECT'
    records.append({'strategy':name,'attempts':4-host.fuel,'cuts':outcomes,'scope':receipt['receipt']['scope']})
assert [r['attempts'] for r in records] == [2,4]
print(records)""",
        ),
    ]
    for title, scope, code in exercises:
        cells.extend(
            [nbf.v4.new_markdown_cell(f"## {title}\n\n{scope}"), nbf.v4.new_code_cell(code)]
        )
    for index, cell in enumerate(cells):
        cell.id = sha256(f"{index}:{cell.source}".encode()).hexdigest()[:16]
    notebook = nbf.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
    )
    nbf.write(notebook, ROOT / "02_ten_ways_to_play.ipynb")


if __name__ == "__main__":
    build()

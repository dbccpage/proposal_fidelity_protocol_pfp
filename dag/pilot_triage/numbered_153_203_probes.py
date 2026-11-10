"""Read-only finite triage probes. No provider, subprocess, seed or artifact replay."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib
import importlib.util
import json
import sys
from fractions import Fraction
from itertools import product

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "dag/pilot_triage/numbered_153_203_probes.json"

def read_functions(path, names, scope):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def rref(matrix):
    a = [list(map(Fraction, row)) for row in matrix]
    pivots = []
    for column in range(len(a[0])):
        row = next((i for i in range(len(pivots), len(a)) if a[i][column]), None)
        if row is None: continue
        target = len(pivots)
        a[row], a[target] = a[target], a[row]
        scale = a[target][column]
        a[target] = [v / scale for v in a[target]]
        for i in range(len(a)):
            if i != target:
                scale = a[i][column]
                a[i] = [v - scale*w for v,w in zip(a[i], a[target])]
        pivots.append(column)
    return a, pivots

def reference(task):
    kind = task['kind']
    if kind == 'spin':
        candidates = []
        for bits in product((0,1), repeat=task['n']):
            residual = [(c+bits[a]+bits[b]) % 2 for (a,b),c in zip(task['edges'],task['target'])]
            candidates.append(dict(spins=list(bits), residual=residual, weight=sum(residual)))
        return min(candidates, key=lambda v:v['weight'])
    if kind == 'lp':
        a = [list(map(Fraction,row)) for row in task['matrix']]
        g, weights = list(map(Fraction,task['flux'])),list(map(Fraction,task['weights']))
        reduced,pivots = rref(list(zip(*a)))
        free = [i for i in range(len(a)) if i not in pivots]
        assert len(free)==1, 'Oracle restricted to nullity-one carriers'
        cycle=[Fraction(0)]*len(a);cycle[free[0]]=Fraction(1)
        for i,pivot in enumerate(pivots):cycle[pivot]=-reduced[i][free[0]]
        pairing=sum(x*y for x,y in zip(g,cycle))
        scale=min(w/abs(c) for w,c in zip(weights,cycle) if c)
        dual=[c*scale*(1 if pairing>=0 else -1) for c in cycle]
        cheapest=min((i for i,c in enumerate(cycle) if c),key=lambda i:weights[i]/abs(cycle[i]))
        residual=[Fraction(0)]*len(a);residual[cheapest]=pairing/cycle[cheapest]
        solved,pivots=rref([row+[b-r] for row,b,r in zip(a,g,residual)])
        x=[Fraction(0)]*len(a[0])
        for i,pivot in enumerate(pivots):
            assert pivot<len(x),'Inconsistent carrier'
            x[pivot]=solved[i][-1]
        return dict(potential=list(map(str,x)),dual=list(map(str,dual)),objective=str(sum(b*v for b,v in zip(g,dual))))
    if kind == 'scope':
        matrices=task['matrices'];ranks=[len(rref(a)[1]) for a in matrices]
        dims=[len(matrices[0][0])]+[len(a) for a in matrices]
        ok=all(sum(Fraction(b[i][k])*Fraction(a[k][j]) for k in range(len(a)))==0
            for a,b in zip(matrices,matrices[1:]) for i in range(len(b)) for j in range(len(a[0])))
        betti=[dims[i]-([0]+ranks)[i]-(ranks+[0])[i] for i in range(5)] if ok else None
        return dict(ranks=ranks,betti=betti,topology_status='CHAIN_LAW_FAILURE' if not ok else 'MATCH' if betti==task['declared_betti'] else 'DECLARED_TOPOLOGY_MISMATCH',cup_status='UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER')
    raise AssertionError(kind)

def main():
    results = {"schema": "pfp.pilot-triage-probes.v1", "provider_calls": 0,
        "protected_benchmark_seed_read": False, "results": [], "limitations": [
        "Dossier task generation uses unmodified AST function bodies with an explicit imported-estate root; this is not a successful historical CLI replay. A separate Fraction/RREF oracle constructs nullity-one LP witnesses because SymPy is unavailable.",
        "Finite fixtures and mutation controls do not prove analytical claims or measure model performance."]}
    checking = importlib.import_module("workflows.wf18_dossier_replay_campaign.pilots.replay_runners.dossier_capsules.checking")
    import yaml
    scope = dict(Q=Fraction, product=product,
        PILOTS=ROOT / "pilots/anomalon_woland", yaml=yaml)
    casepath = ROOT / "pilots/anomalon_woland/replay_runners/dossier_capsules/cases.py"
    read_functions(casepath, {"carrier", "source_input"}, scope)
    scope["mv"] = checking.mv
    for pilot in range(188, 192):
        passed = 0
        for rung in range(1, 6):
            task = scope["carrier"](pilot, rung)
            answer = reference(task)
            assert checking.check_answer(task, answer)
            bad = copy.deepcopy(answer)
            if task["kind"] == "spin": bad["weight"] += 1
            elif task["kind"] == "lp": bad["objective"] = str(Fraction(bad["objective"]) + 1)
            else: bad["ranks"][0] += 1
            assert not checking.check_answer(task, bad)
            passed += 2
        results["results"].append(dict(pilot_id=f"pilot_{pilot:07d}", checks=passed,
            status="PASS", kind="five_independent_oracles_and_wrong_witness_mutants"))
    hist = load(ROOT / "pilots/anomalon_woland/pilot_0000188/misc/source/checker.py", "triage_historical_spin")
    receipt = hist.verify_dossier1({"matrices": {"d0": [[1,1,0],[0,1,1],[1,0,1]], "d1": [[1,1,1]]},
        "target_cochain": {"values": [0,0,0]}, "carrier": {"vertices": [0,1,2]}},
        {"candidate_solution": {"spin_vector": [0,0,0], "claimed_residual_defect": [0,0,0], "claimed_defect_weight": 0}})
    assert receipt.admitted and receipt.is_topologically_obstructed and receipt.curl_d1_c == 0
    results["results"].append(dict(pilot_id="pilot_0000188", status="REPRODUCED_LIMITATION",
        kind="historical_checker_false_obstruction", actual_curl=receipt.curl_d1_c,
        receipt_status=receipt.status, receipt_admitted=receipt.admitted,
        receipt_is_topologically_obstructed=receipt.is_topologically_obstructed,
        is_provably_minimal=receipt.is_provably_minimal))
    fixtures = importlib.import_module("workflows.wf20_derivation_loop_with_lift_grants.pilots.relational_spacetime.finite_fixtures")
    for pilot in range(199,204):
        for variant in fixtures.VARIANTS:
            fixtures.check_variant(f"pilot_{pilot:07d}", variant)
        results["results"].append(dict(pilot_id=f"pilot_{pilot:07d}", checks=len(fixtures.VARIANTS),
            status="PASS", kind="finite_baseline_and_24_mutation_controls", analytical_status="UNVERIFIED"))
    OUT.write_text(json.dumps(results, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"records": len(results["results"]), "passed_checks": sum(r.get("checks",0) for r in results["results"]), "reproduced_limitations": 1, "provider_calls": 0}))

if __name__ == "__main__":
    main()

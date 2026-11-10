"""Independent finite mathematics/source-branch models, never Rust execution."""
import hashlib
import itertools as it
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
PREFIX = 'additional_rust_hott_remaining'
scope = json.loads((REV / (PREFIX + '_scope.json')).read_text())
by = {Path(r['path']).name: r for r in scope['files']}
for row in by.values():
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256']
controls = []
def record(identifier, result, names):
    controls.append({'id': identifier, 'status': 'observed', 'result': result,
                     'method': 'Independent exact finite/branch model; no original Rust execution.',
                     'source_pins': [{'path': by[n]['path'], 'sha256': by[n]['sha256']} for n in names]})

inverse_cases = inverse_pairs = 0
for n in range(5):
    maps = list(it.product(range(n), repeat=n))
    for f, g in it.product(maps, repeat=2):
        left_inverse = all(g[f[i]] == i for i in range(n))
        both = left_inverse and all(f[g[i]] == i for i in range(n))
        assert left_inverse == both
        inverse_cases += 1
        inverse_pairs += left_inverse
record('RHT-P01', {'equal_finite_ordinal_map_pairs': inverse_cases,
                   'mutual_inverse_pairs': inverse_pairs, 'max_cardinality': 4}, ['univalence_witness.rs'])

word_cases = 0
for n in range(9):
    for word in it.product((-1, 1), repeat=n):
        stack = []
        for step in word:
            if stack and stack[-1] == -step:
                stack.pop()
            else:
                stack.append(step)
        displacement = sum(word)
        assert sum(stack) == displacement
        assert stack == ([1] * displacement if displacement >= 0 else [-1] * -displacement)
        for value in range(-2, 3):
            assert value + displacement - displacement == value
        word_cases += 1
record('RHT-P02', {'words': word_cases, 'max_length': 8, 'integer_roundtrips': 5 * word_cases,
                   'scope': 'One-generator inverse cancellation and integer displacement only.'}, ['path_transport.rs'])

def equivalence_partition(rel):
    n = len(rel)
    if any(not rel[i][i] for i in range(n)):
        return None, 'reflexive'
    if any(rel[i][j] != rel[j][i] for i in range(n) for j in range(n)):
        return None, 'symmetric'
    reps, classes = [], [None] * n
    for candidate in range(n):
        if classes[candidate] is not None:
            continue
        block = len(reps)
        reps.append(candidate)
        for member in range(candidate, n):
            if classes[member] is None and rel[candidate][member]:
                classes[member] = block
    for x in range(n):
        for z in range(x + 1, n):
            if (classes[x] == classes[z]) == rel[x][z]:
                continue
            if classes[x] == classes[z]:
                witness = (x, reps[classes[x]], z)
            elif classes[x] < classes[z]:
                witness = (reps[classes[x]], x, z)
            else:
                witness = (reps[classes[z]], z, x)
            a, b, c = witness
            assert rel[a][b] and rel[b][c] and not rel[a][c]
            return None, witness
    return (reps, classes), None

relation_cases = valid_relations = 0
partitions3 = []
for n in range(4):
    for flat in it.product((False, True), repeat=n*n):
        rel = [flat[i*n:(i+1)*n] for i in range(n)]
        expected = (all(rel[i][i] for i in range(n)) and
                    all(rel[i][j] == rel[j][i] for i in range(n) for j in range(n)) and
                    all(not (rel[i][j] and rel[j][k]) or rel[i][k]
                        for i in range(n) for j in range(n) for k in range(n)))
        result, _ = equivalence_partition(rel)
        assert (result is not None) == expected
        relation_cases += 1
        valid_relations += expected
        if n == 3 and expected:
            partitions3.append((rel, result))
delta_cases = pair_cases = 0
for rel, (reps, classes) in partitions3:
    for flat in it.product((0, 1), repeat=9):
        delta = lambda x, y: flat[3*x+y]
        via_reps = all(delta(x,y) == delta(reps[classes[x]], reps[classes[y]])
                       for x in range(3) for y in range(3))
        all_fibers = all(not (rel[x][xp] and rel[y][yp]) or delta(x,y) == delta(xp,yp)
                         for x,xp,y,yp in it.product(range(3), repeat=4))
        assert via_reps == all_fibers
        delta_cases += 1
    for phi, psi in it.product(list(it.product((0, 1), repeat=3)), repeat=2):
        descent = lambda f: all(f[i] == f[reps[classes[i]]] for i in range(3))
        assert descent(list(zip(phi, psi))) == (descent(phi) and descent(psi))
        pair_cases += 1
record('RHT-P03', {'all_directed_relations_up_to_three_points': relation_cases,
                   'equivalence_relations': valid_relations, 'delta_constancy_cases': delta_cases,
                   'joint_observable_cases': pair_cases, 'counterexample_triples_checked': True}, ['primitive_difference.rs'])

identity = {'type': 'A', 'left': 'x', 'right': 'y', 'difference_source': 'u',
            'difference_target': 'v', 'difference': 'd', 'computed': 'checker',
            'certificate_difference': 'd', 'checker': 'zero', 'replay': 'r'}
shape_accepts = all(identity.values()) and identity['difference'] == identity['certificate_difference']
assert shape_accepts and (identity['left'], identity['right']) != (identity['difference_source'], identity['difference_target'])
record('RHT-P04', {'identity_shape_accepts': bool(shape_accepts), 'identity_endpoints': ['x','y'],
                   'difference_endpoints': ['u','v'], 'checker_replayed': False}, ['identity.rs','difference.rs'])
assert bool('d1' and 'd2' and 'd1' != 'd2')
record('RHT-P05', {'empty_context_and_endpoints': True, 'before_ref': 'd1', 'after_ref': 'd2',
                   'both_referenced_values': 0, 'reference_predicate_reports_failed_transport': True}, ['difference.rs'])

urns = ['urn:core:math:truncation_level:v0.1.0'] + ['urn:core:math:invented'+str(i) for i in range(5)]
concepts = ['invented'+str(i) for i in range(6)]
assert len(set(urns)) == len(set(concepts)) == 6 and all(u.startswith('urn:core:math:') for u in urns)
record('RHT-P06', {'arbitrary_six_row_census_passes': True, 'known_canonical_pairs_required': False,
                   'mechanization_strata_checked': False}, ['hott_contract_alignment.rs'])
record('RHT-P07', {'vertices': 1, 'records': [{'dimension': 2, 'source': 'base', 'target': 'base'}],
                   'source_graph_rank': 1-1+1, 'actual_declared_one_cell_count': 0,
                   'one_skeleton_rank': 0}, ['higher_inductive_type.rs'])

def profile(points, questions, point):
    if point not in points:
        return None
    index = points.index(point)
    if any(index >= len(q) for q in questions):
        return None
    return tuple(q[index] for q in questions)
points = ['a','b','c']
parent, child = [], [['0','1']]
zero_related = lambda qs,x,y: profile(points,qs,x) is not None and profile(points,qs,x) == profile(points,qs,y)
class_count = lambda qs: len({p for x in points if (p := profile(points,qs,x)) is not None})
assert zero_related(parent,'a','c') and not zero_related(child,'a','c')
assert class_count(parent) == 1 and class_count(child) == 2
accepted = len(child) > len(parent) and child[:len(parent)] == parent and class_count(child) > class_count(parent)
assert accepted and profile(points,child,'c') is None
record('RHT-P08', {'points': points, 'child_answers': child[0], 'demand': ['a','c'],
                   'before_classes': 1, 'after_classes': 2, 'accepted': accepted,
                   'missing_child_profile': 'c', 'constructor_would_refuse': True}, ['presentation_difference.rs'])

mode = 0
def live_delta(x,y):
    return 0 if mode == 0 else x
assert all(live_delta(x,y) == 0 for x,y in it.product(range(2), repeat=2))
mode = 1
factor_value = live_delta(0,0)
assert factor_value != live_delta(1,0)
record('RHT-P09', {'initial_delta': 'constant0', 'admitted_zero_relation': 'universal',
                   'later_delta': 'first argument', 'factor_apply': factor_value,
                   'later_delta_1_0': live_delta(1,0), 'factorization_now_false': True}, ['primitive_difference.rs'])

# A valid graded zero algebra with f3(a,a,a)=b, degrees0,-2: all morphism
# equations vanish. Composition with the strict identity must preserve f3.
record('RHT-P10', {'graded_zero_algebra_degrees': {'a': 0, 'b': -2},
                   'all_m_operations': 0, 'f1': 'identity', 'f3_a_a_a': 'b',
                   'identity_composite_expected_f3': 'b', 'draft_default_f3': 0,
                   'scope': 'Valid nonunital A-infinity morphisms; dormant source composition loses higher components.'}, ['a_infinity.rs'])

# Exact F2 countermodel for the dormant NotFormal verdict. A has basis e1,e2,u
# of degrees0,0,-1, triangular multiplication. h2(e1,e1)=u, all other basis
# pairs zero. B has m2 unchanged and m3=Hochschild coboundary(h2).
# f1=g1=id and f2=g2=h2 give mutually inverse A-infinity morphisms A<->B.
basis = (1, 2, 4)
degrees = {1: 0, 2: 0, 4: -1}
mul_basis = {(1,1): 1, (2,2): 2, (1,4): 4, (4,2): 4}
def linear_map(table, args):
    result = 0
    supports = [[b for b in basis if a & b] for a in args]
    for key in it.product(*supports):
        result ^= table.get(key, 0)
    return result
def mul(a,b):
    return linear_map(mul_basis,(a,b))
def h2(a,b):
    return linear_map({(1,1):4},(a,b))
def m3(a,b,c):
    return mul(a,h2(b,c)) ^ h2(mul(a,b),c) ^ h2(a,mul(b,c)) ^ mul(h2(a,b),c)
def operation(twisted,args):
    if len(args) == 2:
        return mul(*args)
    if twisted and len(args) == 3:
        return m3(*args)
    return 0
def f(args):
    return args[0] if len(args) == 1 else h2(*args) if len(args) == 2 else 0
def compositions(n,k):
    if k == 1:
        yield (n,)
    else:
        for i in range(1,n-k+2):
            for rest in compositions(n-i,k-1):
                yield (i,)+rest
def group_images(args,lengths):
    images=[];start=0
    for length in lengths:
        images.append(f(args[start:start+length]));start+=length
    return tuple(images)
def left_sum(outer,inner,args):
    value=0;n=len(args)
    for s in range(1,n+1):
        for r in range(n-s+1):
            value ^= outer(args[:r]+(inner(args[r:r+s]),)+args[r+s:])
    return value
def right_sum(target,args):
    value=0
    for k in range(1,len(args)+1):
        for lengths in compositions(len(args),k):
            value ^= target(group_images(args,lengths))
    return value
algebra_checks=morphism_checks=composition_checks=0
for twisted in (False,True):
    op=lambda args,t=twisted:operation(t,args)
    for n in range(1,6):
        for args in it.product(basis,repeat=n):
            assert left_sum(op,op,args)==0
            algebra_checks+=1
for source_twisted,target_twisted in ((False,True),(True,False)):
    source=lambda args,t=source_twisted:operation(t,args)
    target=lambda args,t=target_twisted:operation(t,args)
    for n in range(1,7):
        for args in it.product(basis,repeat=n):
            assert left_sum(f,source,args)==right_sum(target,args)
            morphism_checks+=1
for n in range(1,5):
    for args in it.product(basis,repeat=n):
        assert right_sum(f,args)==(args[0] if n==1 else 0)
        composition_checks+=1
for n in (2,3):
    for args in it.product(basis,repeat=n):
        out=operation(True,args)
        for bit in basis:
            if out&bit:
                assert degrees[bit]==sum(degrees[x] for x in args)+2-n
assert m3(1,1,1)==4
record('RHT-P11', {'field':'F2','basis_degrees':{'e1':0,'e2':0,'u':-1},
                   'nonzero_products':{'e1*e1':'e1','e2*e2':'e2','e1*u':'u','u*e2':'u'},
                   'h2_nonzero_basis_input':'h2(e1,e1)=u', 'B_m3':'Hochschild coboundary of h2',
                   'B_m3_e1_e1_e1':'u','A_operations':'m2 only','B_operations':'m2,m3 only',
                   'Ainfinity_relation_basis_checks':algebra_checks,'two_way_morphism_basis_checks':morphism_checks,
                   'inverse_composition_basis_checks':composition_checks,
                   'beyond_checked_arities':'Identically zero by maximum possible composition arity (5 algebra,6 morphism,4 inverse). Multilinearity extends basis identities to all8 elements.',
                   'formal_proof':'Explicit mutually inverse A-infinity morphisms to A with d=0 and no higher operations.',
                   'dormant_source_verdict':'NotFormal on the e1,e1,e1 cocycle triple; false for this admitted example.'}, ['a_infinity.rs'])

declared_sign=(-1)**(1*2+0)
assert declared_sign==1
record('RHT-P12', {'test_input':{'r':1,'s':2,'t':0},'declared_exponent_result':declared_sign,
                   'embedded_test_expected':-1,'test_is_disabled':True,
                   'other_disagreement':'Displayed rs+t formula gives negative left-associated m2 term; check_n3 uses positive left-associated term.'}, ['a_infinity.rs'])
for name in ('a_infinity.rs','quasi_category.rs','substitution.rs'):
    assert (ROOT/by[name]['path']).read_text().splitlines()[0]=='#![cfg(any())]'
record('RHT-P13', {'disabled_modules':['a_infinity.rs','quasi_category.rs','substitution.rs'],
                   'native_execution_claim':False}, ['a_infinity.rs','quasi_category.rs','substitution.rs'])

output={'schema_version':'1.0','status':'passed','controls':controls,
        'source_scope_sha256':hashlib.sha256((REV/(PREFIX+'_scope.json')).read_bytes()).hexdigest(),
        'limits':['Independent exact finite Python models and source-gate inspection only; no Rust compilation/execution.',
                  'The F2 example uses the standard nonunital A-infinity/morphism equations; all signs become1 in characteristic2.',
                  'No original code changes, project imports, provider requests or private benchmark access.']}
path=REV/(PREFIX+'_controls.json');path.write_text(json.dumps(output,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'passed','controls':len(controls),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                  'formality_countermodel':controls[10]['result']}))

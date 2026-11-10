import sys,importlib.util,itertools,json,platform
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_audit as a
r=a.row('g02/original/code/derivation/higher_structure.py');p=a.ROOT/r['path'];assert a.sha(p)==r['sha256']
s=importlib.util.spec_from_file_location('formal_history_cut_probe',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
comparisons=[]
for n in range(13):
    subsets=[frozenset(c) for k in range(n+1) for c in itertools.combinations(range(n),k)]
    for x in range(n+2):
        for y in range(n+2):
            got=m.cut_census(n,x,y);independent=sum(x in q and y not in q for q in subsets)
            formula=0 if x>=n or x==y else 2**(n-1) if y>=n else 2**(n-2)
            assert got==independent==formula
            comparisons.append({'n':n,'a':x,'b':y,'count':got})
stages=[m.alt_num(m.creplay(m.k4_events()[:i],m.EMPTY_COMPLEX)) for i in [4,10,14,15]]
assert stages==[4,-2,2,1]
cx=m.k4();assert m.d2_zero_triangles(cx) and m.d2_zero_tet(cx,(0,1,2,3)) and m.boundary_not_forced((0,1,2))
a.write('_math_controls.json',{'runtime':sys.executable,'python':platform.python_version(),'source':r,'method':'Read-vetted pure Python owner, independent itertools subset enumeration and exact closed formula; all n0..12,a,b0..n+1. No Lean/Rust executable, provider/private QM or historical process replay.','comparisons':len(comparisons),'all_exact_matches':True,'case_result_digest':a.hashlib.sha256(json.dumps(comparisons,sort_keys=True).encode()).hexdigest(),'formula_assumptions':'Nat domain; equal pair or outside first gives0, outside second gives2^(n-1), otherwise distinct contained pair2^(n-2).','alt_num_stages':stages,'stage_invariant':len(set(stages))==1,'boundary_square_zero_on_declared_k4':True,'opposite_orientation_also_zero':True,'limits':'Finitecontrols substantiate declaredmodel only; generalcount follows separate combinatorialproof with membership/distinctness assumptions. AvailablePython3.14.2 is not historicalprofile reproduction.'})
print(json.dumps({'comparisons':len(comparisons),'all_match':True,'stages':stages}))

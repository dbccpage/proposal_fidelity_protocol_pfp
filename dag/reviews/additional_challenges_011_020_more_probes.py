"""Synthetic, offline C015-C020 boundary probes; never calls benchmark/provider code."""
import copy, importlib, json, socket, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
def deny(*a,**k): raise RuntimeError('OFFLINE_AUDIT_NETWORK_FORBIDDEN')
socket.create_connection=deny;socket.socket.connect=deny
rows=[]
def module(n,part):
    family=next((ROOT/'workflows/tasks/certified_challenges').glob(f'c{n:03}_*')).name
    return importlib.import_module(f'{family}.{part}')
def solve(n,c):
    out=module(n,'reference_solver.solver').solve(copy.deepcopy(c))
    return out[0] if isinstance(out,tuple) else out
def probe(name,n,c,s,expectation):
    try:
        r=module(n,'judge_packet.checkers.dual_evaluator').evaluate_dual(copy.deepcopy(c),copy.deepcopy(s))
        if isinstance(r,tuple): r={'verdict':'PASS' if r[0] else 'FAIL','reason':r[1],'details':r[2]}
    except Exception as exc:r={'exception_type':type(exc).__name__,'exception':str(exc)}
    rows.append(dict(id=name,family=n,case=c,certificate=s,expectation=expectation,observed=r))

c15={'id':'audit15','simplices':[{'dim':0,'vertices':[0],'val':'0'},{'dim':0,'vertices':[1],'val':'1'}]}
s15=solve(15,c15);probe('C015-valid-isolated-pair',15,c15,s15,'PASS control')
c=copy.deepcopy(c15);c['simplices'][0]['val']='1';c['simplices'][1]['val']='0'
probe('C015-decreasing-filtration',15,c,s15,'Reject SOLVED: filtration decreases; unchanged sorted barcode cannot repair invalid input order')
c={'id':'bad_face','simplices':[{'dim':0,'vertices':[0],'val':'0'},{'dim':1,'vertices':[0,1],'val':'1'}]}
probe('C015-invented-face-witness',15,c,{'status':'OUT_OF_SCOPE','witness':{'simplex':'invented','missing_earlier_face':'[999]'}},'Reject fabricated witness even when some other face defect exists')
s=copy.deepcopy(s15);s['pairs']=[['0','999']]
probe('C015-pair-outside-range',15,c15,s,'Reject malformed pair without an exception')

c16={'id':'audit16','deg_p':1,'deg_q':1,'X':{'maximal_simplices':[[0,1],[1,2],[0,2]]},'Y':{'maximal_simplices':[[0,1],[1,2],[0,2]]}}
s16=solve(16,c16);probe('C016-valid-circle-pair',16,c16,s16,'PASS control')
s=copy.deepcopy(s16)
for k in ('X','Y'):s[k]={'rank':'0','basis_p':[],'basis_q':[],'nonzero':[],'primitives':[]}
probe('C016-empty-cohomology-bases',16,c16,s,'Reject incomplete H1 bases; H1(circle)=Q, despite correct zero product rank')
c=copy.deepcopy(c16);c['deg_p']=3;c['deg_q']=2
probe('C016-warranted-invalid-degree-refusal',16,c,solve(16,c),'Accept reference warranted INVALID_DEGREES refusal')
import itertools
c={'id':'s4','deg_p':4,'deg_q':0,'X':{'maximal_simplices':[list(s) for s in itertools.combinations(range(6),5)]},'Y':{'maximal_simplices':[list(s) for s in itertools.combinations(range(6),5)]}}
probe('C016-degree4-times-unit',16,c,solve(16,c),'Accept valid degree4 cup unit certificate without KeyError on absent degree5')

g=module(17,'reference_solver.groups').make_s3()
edges={}
for r in range(2):
    for col in range(2):
        for rr,cc in [(r+1,col),(r,col+1)]:
            if rr<2 and cc<2:
                u=f'{r},{col}';v=f'{rr},{cc}';edges[f'{u}->{v}']='e';edges[f'{v}->{u}']='e'
c17={'id':'audit17','L':2,'M':2,'boundary':'open','group':g,'edges':edges};s17=solve(17,c17)
probe('C017-valid-trivial-connection',17,c17,s17,'PASS control')
c=copy.deepcopy(c17);c['group']={'name':'not_an_allowed_group','order':1,'elements':['e'],'identity':'e','inverses':{'e':'e'},'table':{'e':{'e':'e'}}}
probe('C017-group-outside-named-domain',17,c,s17,'Reject SOLVED outside G in S3,Q8,SL2F3; generic group arithmetic remains valid')
c=copy.deepcopy(c17);c['edges']['0,0->1,1']='e';c['edges']['1,1->0,0']='e'
probe('C017-extra-diagonal-edge',17,c,s17,'Reject non-nearest-neighbour extra lattice edge under declared square-grid carrier')
c=copy.deepcopy(c17);c['group']['elements']=[[]]
probe('C017-unhashable-group-element',17,c,s17,'Reject malformed group without an uncaught exception')

c18={'id':'audit18','vertices':['a','b','c'],'edges':[['a','b',-1],['b','c',1],['a','c',1]]}
s18=solve(18,c18);probe('C018-negative-triangle',18,c18,s18,'PASS control, minimum1 by one negative cycle')
c={'id':'too_many','vertices':[str(i) for i in range(201)],'edges':[]}
probe('C018-vertex-bound201',18,c,{'status':'SOLVED','l':'0','switching':{},'deleted':[],'lower_bound':{'kind':'packing','cycles':[]}},'Reject outside CHALLENGE vertex<=200 contract')
c={'id':'duplicate_edge','vertices':['a','b'],'edges':[['a','b',1],['a','b',1]]}
probe('C018-nonsimple-graph',18,c,{'status':'SOLVED','l':'0','switching':{},'deleted':[],'lower_bound':{'kind':'packing','cycles':[]}},'Reject duplicate edge under declared simple-graph contract')

c19={'id':'two_cavities','vertices':['v'],'edges':['e'],'faces':['f0','f1'],'d1':{},'d2':{},'mode':'Q','B':{'f0':'1','f1':'1'},'weights':{'f0':'1','f1':'1'}}
s19=solve(19,c19)
probe('C019-false-phi2-optimum',19,c19,s19,'Reject phi2=1: d2=0 makes every residual B, so exact optimum=sum |B|=2; producer gives first-basis-vector lower bound')
s=copy.deepcopy(s19);s['primal_A']={'e':'this is not a rational'}
probe('C019-ignored-primal-certificate',19,c19,s,'Reject malformed primal and nonzero duality gap')
c=copy.deepcopy(c19);c['faces']=['f0'];c['B']={'f0':'0'};c['weights']={'f0':'-1'}
probe('C019-negative-weight-input',19,c,solve(19,c),'Reject nonpositive face weight outside convex weighted-L1 contract')
c={'id':'integral_available','vertices':['v'],'edges':['e0','e1'],'faces':['f'],'d1':{},'d2':{'f':{'e0':2,'e1':1}},'mode':'Z','B':{'f':'1'}}
probe('C019-integral-solution-missed',19,c,solve(19,c),'Reference should find integer A=(0,1); free-variable-zero rational particular A=(1/2,0) does not establish integral obstruction')
probe('C019-integral-solution-positive-control',19,c,{'status':'SOLVED','mode':'Z','verdict':'EXTENDS_INTEGRAL','A':{'e1':'1'}},'PASS control for same available integer solution')

c20={'id':'audit20','filtration':'both','dims':{'2,0':1,'1,0':1,'1,1':1,'0,1':1},'d_h':{'2,0':[[1]],'1,1':[[1]]},'d_v':{'1,1':[[1]]}}
s20=solve(20,c20);probe('C020-worked-zigzag-both',20,c20,s20,'PASS control: nonzero column d2, zero row E2, zero total homology')
c={'id':'dim5','filtration':'columns','dims':{'0,0':5},'d_h':{},'d_v':{}}
probe('C020-stalk-dimension5',20,c,solve(20,c),'Reject dimension5 outside n(p,q)<=4')
c={'id':'outside','filtration':'columns','dims':{'6,0':1},'d_h':{},'d_v':{}}
probe('C020-silently-ignored-outside-cell',20,c,solve(20,c),'Reject nonzero cell outside 0<=p,q<=5 instead of silently dropping it')
probe('C020-nondict-certificate',20,c20,[],'Reject malformed certificate without an uncaught exception')
s=copy.deepcopy(s20);s['columns']['differentials'][0]['rank']='wrong'
probe('C020-noninteger-rank',20,c20,s,'Reject malformed differential rank without an exception')
for length in (3,4,5):
    dims={};dh={};dv={}
    for i in range(length):
        dims[f'{length-i},{i}']=1;dims[f'{length-i-1},{i}']=1
        dh[f'{length-i},{i}']=[[1]]
        if i:dv[f'{length-i},{i}']=[[1]]
    c={'id':f'audit_d{length}','filtration':'both','dims':dims,'d_h':dh,'d_v':dv}
    s={'status':'SOLVED','filtration':'both','columns':{'E2':{f'{length},0':'1',f'0,{length-1}':'1'},'differentials':[{'r':str(length),'from':f'{length},0','rank':'1'}],'Einf':{}},'rows':{'E2':{},'differentials':[],'Einf':{}},'tot_homology':{}}
    probe(f'C020-explicit-d{length}-zigzag',20,c,s,'PASS independent hand-derived length-r staircase: total differential invertible, column d_r rank1 and row E2 zero')
dest=ROOT/'dag/reviews/additional_challenges_011_020_more_probes.json'
dest.write_text(json.dumps({'scope':'Independent synthetic probes C015-C020','probes':rows},indent=2)+'\n',encoding='utf-8')
print(json.dumps({r['id']:r['observed'].get('verdict',r['observed'].get('exception_type')) for r in rows}))

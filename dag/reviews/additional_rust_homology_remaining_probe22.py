import sys,json
sys.dont_write_bytecode=True
from pathlib import Path
def mm(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def add(a,b,s=1):return [[x+s*y for x,y in zip(r,t)] for r,t in zip(a,b)]
def bracket(a,b,da,db):return add(mm(a,b),mm(b,a),-((-1)**(da*db)))
zero=[[0,0],[0,0]];d=[[0,1],[0,0]];alpha=[[0,-1],[1,0]];xi=[[1,0],[0,0]]
curvature=add(bracket(d,alpha,1,1),mm(alpha,alpha));assert curvature==zero
delta=add(bracket(d,xi,1,0),bracket(xi,alpha,0,1))
tangent=add(bracket(d,delta,1,1),bracket(alpha,delta,1,1));assert tangent==[[-2,0],[0,-2]]
correct=add(bracket(d,xi,1,0),bracket(alpha,xi,1,0))
assert add(bracket(d,correct,1,1),bracket(alpha,correct,1,1))==zero
def badrank(m):
    a=[list(map(float,row)) for row in m];rows=len(a);cols=len(a[0]);rank=col=0
    for row in range(rows):
        if col>=cols:break
        p=next((i for i in range(row,rows) if abs(a[i][col])>1e-10),None)
        if p is None:col+=1;continue
        a[row],a[p]=a[p],a[row]
        for i in range(row+1,rows):
            f=a[i][col]/a[row][col]
            for j in range(col,cols):a[i][j]-=f*a[row][j]
        rank+=1;col+=1
    return rank
assert badrank([[0,1],[0,0]])==0
r={'rule':'inactive_dgla_axiom_and_gauge_controls','status':'exact_countermodels_confirmed_for_inactive_source','runtime':sys.version,'gauge':{'base_d':d,'mc_alpha':alpha,'xi':xi,'curvature':curvature,'implemented_infinitesimal_delta':delta,'linearized_mc_defect':tangent,'correct_sign_delta':correct},'ce_odd_sl2':{'ef':[0,0,1],'fe':[0,0,-1],'required_odd_symmetry':False},'abelian_nonzero_curvature_gauge_fixed_point':{'d0':0,'d1':1,'d2':0,'alpha':'1/100','curvature':'1/100','all_degree0_gauge_changes':0,'label_with_thresholds_1e_6_point1':'GaugeFixable'},'rank_helper':{'matrix':[[0,1],[0,0]],'computed':0,'actual':1},'limits':['DGLA source is file-level cfg(any()) inactive; no original Rust execution.','Exact integer2x2 countermodel verifies failure already at infinitesimal tangent level, not merely missing higher-order finite gauge terms.','Rank helper counterexample is general rectangular-matrix input; no claim that a Lie Killing matrix in current callers has this shape.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))

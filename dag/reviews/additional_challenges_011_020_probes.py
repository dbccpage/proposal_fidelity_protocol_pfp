"""Small synthetic boundary probes. No model/network/private input or source edits."""
import copy, importlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
P=ROOT/'dag/reviews/additional_challenges_011_020_probes.json'
records=[]
def probe(name,n,case,cert,expectation):
    family=next((ROOT/'workflows/tasks/certified_challenges').glob(f'c{n:03}_*')).name
    module=importlib.import_module(f'{family}.judge_packet.checkers.dual_evaluator')
    try: result=module.evaluate_dual(copy.deepcopy(case),copy.deepcopy(cert))
    except Exception as exc: result={'exception_type':type(exc).__name__,'exception':str(exc)}
    records.append({'id':name,'family':n,'case':case,'certificate':cert,'expectation':expectation,'observed':result})

c11={'id':'audit_c11','vertices':['a','b'],'edges':[{'id':'e','u':'a','v':'b','claim':'0','weight':'1'}]}
s11={'id':'audit_c11','status':'SOLVED','phi1':'0','potential':{'a':'0','b':'0'},'repair':{},'dual':{}}
probe('C011-valid-zero',11,c11,s11,'PASS positive control')
c=copy.deepcopy(c11);c['edges']=[dict(c11['edges'][0],id=f'e{i}') for i in range(18)]
probe('C011-cycle-rank-17',11,c,s11,'Reject SOLVED: b1=18-2+1=17 exceeds declared16')
c=copy.deepcopy(c11);c['edges'][0]['weight']='1/13';c['enforce_denominator_bounds']=True
probe('C011-denominator-bound',11,c,s11,'Reject SOLVED under enforced denominator<=12')
c={'id':'malformed','vertices':['a'],'edges':None}
probe('C011-unwitnessed-oos',11,c,{'status':'OUT_OF_SCOPE','witness':{'edge':'invented','reason':'SELF_LOOP'}},'Reject a self-loop witness for a nonexistent edge')
c=copy.deepcopy(c11);c['vertices']=[[]]
probe('C011-unhashable-vertex',11,c,s11,'Reject without an uncaught exception')
c=copy.deepcopy(c11);c['vertices']=['a'];c['edges'][0]['v']='a'
s=copy.deepcopy(s11);s['potential']={'a':'0'}
probe('C011-self-loop-solved',11,c,s,'Reject SOLVED on contract-excluded self loop')
s=copy.deepcopy(s11);s['id']='unrelated-case';s['repair']={'e':0};s['dual']={'e':0}
probe('C011-numeric-wire-and-wrong-id',11,c11,s,'Strict contract rejects numeric rational fields and mismatched response identity')

c12={'id':'audit_c12','vertices':[{'id':'a','dim':1}],'edges':[],'targets':[]}
s12={'id':'audit_c12','status':'SOLVED','h0_dim':'1','h0_basis':[['1']],'h1_dim':'0','h1_complement':[],'targets':[]}
probe('C012-valid-isolated',12,c12,s12,'PASS positive control')
s=copy.deepcopy(s12);s['h0_dim']='0';s['h0_basis']=[]
probe('C012-incomplete-h0',12,c12,s,'Both individual checkers should reject an incomplete H0 basis; combined dual gate must reject')
s=copy.deepcopy(s12);s['h0_dim']='1/2'
probe('C012-fractional-dimension',12,c12,s,'Reject malformed integer dimension without an uncaught exception')
c=copy.deepcopy(c12);c['vertices'][0]['dim']=5
s=copy.deepcopy(s12);s['h0_dim']='5';s['h0_basis']=[[str(int(i==j)) for j in range(5)] for i in range(5)]
probe('C012-stalk-dimension-5',12,c,s,'Reject SOLVED: stalk bound is4')
c=copy.deepcopy(c12);c['edges']=[{'id':'real','u':'a','v':'a','dim':1,'F_u':[['1']],'F_v':[['1']]}]
probe('C012-unbound-oos-edge',12,c,{'status':'OUT_OF_SCOPE','witness':{'reason':'SELF_LOOP','edge':'invented'}},'Reject witness bound to nonexistent edge even though another self-loop exists')
c=copy.deepcopy(c12);c['vertices']*=2
probe('C012-duplicate-id-refusal',12,c,{'status':'UNKNOWN','refusal':'MALFORMED_CASE_STRUCTURE'},'Accept warranted duplicate-vertex-ID refusal')
c=copy.deepcopy(c12);c['targets']=[{'b':[]}]*4
probe('C012-target-count-refusal',12,c,{'status':'UNKNOWN','refusal':'MALFORMED_CASE_STRUCTURE'},'Accept warranted >3-target refusal produced by reference solver')

from c013_integral_homology_torsion.reference_solver.solver import solve as solve13
c13={'id':'audit_c13','simplices':[[0],[1],[0,1]]}
s13=solve13(c13)
probe('C013-valid-edge',13,c13,s13,'PASS positive control')
s=copy.deepcopy(s13)
for cert in s['snf']:
    for key in ('U','U_inv','V','V_inv'):
        cert[key]=[[int(x)+(.9 if int(x)>=0 else -.9) for x in row] for row in cert[key]]
probe('C013-noninteger-SNF',13,c13,s,'Reject noninteger certificate matrices; int(float) silently truncates and does not validate the supplied identities')
s=copy.deepcopy(s13);s['snf'][0]['D'].append('2');s['homology'][0]['betti']='0';s['homology'][0]['torsion']=['2'];s['homology'][1]['betti']='-1'
probe('C013-invariant-beyond-matrix',13,c13,s,'Reject extra diagonal outside matrix; individual algebraic checker must not invent rank/torsion')
c={'id':'audit_c13_empty','simplices':[]}
probe('C013-empty-solved',13,c,{'status':'SOLVED','homology':[],'snf':[]},'Reject empty invalid input without exception')
c={'id':'audit_c13_bound','simplices':[[20000]]}
probe('C013-label-bound',13,c,{'status':'SOLVED','homology':[{'n':'0','betti':'1','torsion':[]}],'snf':[]},'Reject SOLVED outside declared integer-label bound10000')
s=copy.deepcopy(s13);s['snf'].append({'boundary':'999','U':[['bogus']],'U_inv':[],'V':[],'V_inv':[],'D':['2']})
probe('C013-unchecked-extra-SNF',13,c13,s,'Reject an unrelated malformed SNF certificate rather than accepting it unexamined')

from c014_discrete_hodge_decomposition.reference_solver.solver import solve as solve14
c14={'id':'audit_c14','vertices':['a','b'],'edges':['e'],'faces':[], 'edge_endpoints':{'e':['a','b']},'flow':{'e':'1'},'weights':{'e':'2'}}
s14=solve14(c14)
probe('C014-valid-edge',14,c14,s14,'PASS positive control')
c=copy.deepcopy(c14);c['weights']['e']='1/13'
probe('C014-denominator-bound',14,c,s14,'Reject SOLVED because weight denominator exceeds12')
s=copy.deepcopy(s14);s['phi']={k:float(v) for k,v in s['phi'].items()}
probe('C014-float-potential',14,c14,s,'Reject float answer despite exact numerical equality')
c=copy.deepcopy(c14);c['faces']=[{'id':'f','boundary':[['e',1],['e',-1]]}]
s=copy.deepcopy(s14);s['psi']={}
probe('C014-canceling-face-list',14,c,s,'Under additive repeated-edge boundary semantics, delta1 is0 and this SOLVED certificate is valid; parser instead overwrites with last sign')
probe('C014-overwritten-face-oos',14,c,{'status':'OUT_OF_SCOPE','witness':{'reason':'D1_D0_NONZERO','face':'f','vertex':'a'}},'Under additive incidence semantics no nonzero entry exists; both use shared last-write parser')
for name,c in [('C014-isolated-vertex',{'id':'isolated','vertices':['a'],'edges':[],'faces':[]}),('C014-self-loop-producer',{'id':'loop','vertices':['a'],'edges':['e'],'faces':[],'edge_endpoints':{'e':['a','a']},'flow':{'e':'1'}})]:
    try: cert=solve14(copy.deepcopy(c))
    except Exception as exc:
        records.append({'id':name,'family':14,'case':c,'expectation':'Valid zero-boundary case should produce a certificate','observed':{'exception_type':type(exc).__name__,'exception':str(exc)}})
    else: probe(name,14,c,cert,'Generated certificate should pass for this finite valid case')

P.write_text(json.dumps({'scope':'Synthetic C011-C014 checker boundary probes, no providers','probes':records},indent=2)+'\n',encoding='utf-8')
print(json.dumps({r['id']:r['observed'].get('verdict',r['observed'].get('exception_type')) for r in records}))

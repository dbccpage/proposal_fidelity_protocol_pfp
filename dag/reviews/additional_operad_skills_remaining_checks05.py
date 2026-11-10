"""Independent exact/branch controls for reviewed release and governance sources."""
import ast,hashlib,json,pathlib,re,sys
from fractions import Fraction as Q
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,num,obs,limit):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{num:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limit})
patterns=['git push','git reset --hard','git clean -fd','git clean -f','git branch -D',r'git checkout \.',r'git restore \.','push --force','reset --hard'];command='git -C repo push origin main';hits=[p for p in patterns if re.search(p,command)];assert hits==[]
add(151,30,{'synthetic_command':command,'matched_patterns':hits},'Regex semantics control only; no shell or Git command executed. Global Git option makes a normal push evade all literal patterns.')
C=[[1,2],[0,0]];C2=[[sum(C[i][k]*C[k][j]for k in range(2))for j in range(2)]for i in range(2)];x=[0,1];cx=[sum(a*b for a,b in zip(row,x))for row in C];r=[a-b for a,b in zip(x,cx)];assert C2==C and sum(map(abs,r))==3
add(158,31,{'C':C,'C_squared':C2,'x':x,'Cx':cx,'residual_norm_L1':3,'distance_to_image_L1':1,'nearest_image_point':[0,0]},'Exact idempotent counterexample: image is x-axis, so distance from (0,1) is 1. Arbitrary oblique projection residual norm 3 is not the minimum quotient distance.')
node=ast.parse('from pkg import infrastructure').body[0];segments=tuple(node.module.split('.'));layers={'use_cases','infrastructure','controllers','frontend'};hits=[x for x in segments if x in layers];assert hits==[]
add(163,32,{'python_import':'from pkg import infrastructure','node_module':node.module,'imported_names':[a.name for a in node.names],'resolver_segments':segments,'outer_hits':hits},'Isolated branch mirror of import_targets when node.module is set; does not import pkg or run the architecture owner. The imported submodule name is dropped.')
token='leanprover/lean4:';assert token.startswith('leanprover/lean4:')
add(178,33,{'toolchain_text':token,'accepted_prefix':True,'version_suffix':''},'Exact prefix predicate; no Lean toolchain/network/build invoked. Prefix presence does not validate release tag or package config.')
bad='content_hash: '+('1'*64);quoted='content_hash: "'+('0'*64)+'"';pattern='content_hash: '+('0'*64);assert pattern not in bad and pattern not in quoted
add(173,34,{'wrong_nonzero_hash_detected':pattern in bad,'quoted_zero_hash_detected':pattern in quoted},'Literal substring control only; no immutable artifact, Git index or archive modified. A malformed or wrong digest need not match the one forbidden spelling.')
def scan(s):
 for n in ast.walk(ast.parse(s)):
  if isinstance(n,ast.Assert)and not(isinstance(n.test,ast.Constant)and n.test.value is True):return True
 return False
cases=['assert 1','if False:\n    assert False','def never_called():\n    assert 2 == 3'];assert all(map(scan,cases))
add(187,35,{'code_cells':cases,'presence_results':list(map(scan,cases)),'meaningful_executed_learning_check':False},'Exact copied AST predicate on synthetic strings; no notebook or retained scanner executed. Presence is neither execution nor learning evidence.')
# Two-object finite category with one nonidentity arrow, no inverse.
arrows={'idA':('A','A'),'idB':('B','B'),'f':('A','B')};comp={('idA','idA'):'idA',('idB','idB'):'idB',('f','idA'):'f',('idB','f'):'f'}
for g in arrows:
 for f in arrows:
  if arrows[g][0]==arrows[f][1]:assert(g,f)in comp
for h in arrows:
 for g in arrows:
  for f in arrows:
   if(g,f)in comp and(h,g)in comp:assert comp[(h,comp[(g,f)])]==comp[(comp[(h,g)],f)]
assert not any(s=='B'and t=='A'for s,t in arrows.values())
add(169,36,{'objects':['A','B'],'arrows':arrows,'composition':[[g,f,h]for(g,f),h in comp.items()],'category_axioms_checked':'all composable pairs/triples and listed identities','f_has_inverse':False},'Exact finite category counterexample to requiring inverses of every category morphism. Groupoids require inverses; general categories and monoids do not.')
(H/(P+'_checks05.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))

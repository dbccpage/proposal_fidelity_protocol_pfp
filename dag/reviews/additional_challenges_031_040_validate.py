"""Bounded offline artifact audit; outputs confined to this audit prefix."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREFIX = HERE / "additional_challenges_031_040"
SCOPE = json.loads(PREFIX.with_name(PREFIX.name + "_scope.json").read_text())
ROWS = {r["path"]: r for r in SCOPE["files"]}
sys.path.insert(0, str(ROOT / "workflows/tasks/certified_challenges"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_load(text):
    duplicates = []
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result
    value = json.loads(text, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    return value, duplicates


def family(path):
    return path.split("/")[3]


def load_owners(name):
    if name.startswith(("c031_", "c032_", "c033_", "c034_", "c035_", "c036_", "c037_", "c038_", "c039_", "c040_")):
        solve = importlib.import_module(name + ".reference_solver.solver").solve
        evaluate = importlib.import_module(name + ".judge_packet.checkers.dual_evaluator").evaluate_dual
        return solve, evaluate
    raise ValueError("Owner not inspected/enabled: " + name)


def sugra_independent(case, result):
    """Own dimension/count arithmetic; group identities are explicitly admitted."""
    from fractions import Fraction
    if result.get('status') != 'SOLVED':
        return {'status':'typed_refusal_owner_replay_only'}
    def dim(group, rep):
        if rep == '1': return 1
        if group.startswith(('SU(', 'SO(', 'Sp(')):
            f=group[:2]; n=int(group[3:-1])
            adj={'SU':n*n-1,'SO':n*(n-1)//2,'Sp':n*(2*n+1)}[f]
            if rep=='adj': return adj
            if rep in ('fund','vect',str(2*n if f=='Sp' else n)): return 2*n if f=='Sp' else n
            if rep in ('antisym',f'AS_{n*(n-1)//2}') and f=='SU': return math.comb(n,2)
            if rep in ('sym',f'S_{n*(n+1)//2}') and f=='SU': return math.comb(n+1,2)
            if rep in ('antisym',f'AS_{n*(2*n-1)-1}') and f=='Sp': return n*(2*n-1)-1
            if rep in ('spin','spinor') and f=='SO': return 2**((n-1)//2 if n%2 else n//2-1)
        exceptional={'G2':(7,14),'F4':(26,52),'E6':(27,78),'E7':(56,133),'E8':(248,248)}
        if group in exceptional:
            return exceptional[group][1 if rep=='adj' else 0]
        raise ValueError('Unsupported dimension')
    try:
        groups=case.get('gauge_group',[]); hypers=case.get('hypers',[]); T=case['T']
        V=sum(dim(g,'adj') for g in groups)
        H=Fraction(case.get('neutral_hypers',0))
        for row in hypers:
            H+=Fraction(str(row.get('multiplicity',1)))*math.prod(dim(g,r) for g,r in zip(groups,row['reps'],strict=True))
        lhs=H-V+29*T
        ff=result.get('first_failure',{})
        return {'status':'independent_dimension_and_gravity_arithmetic','H':str(H),'V':V,'gravity_lhs':str(lhs),
                'H_matches':result.get('H')==H,'V_matches':result.get('V')==V,
                'condition1_witness_matches':(str(ff.get('lhs'))==str(lhs) and str(ff.get('rhs'))=='273') if ff.get('condition')==1 else None,
                'scope':'Classical dimension formulas and exceptional dimensions admitted; full trace coefficients/inertia use the two inspected owner routes.'}
    except Exception as exc:
        return {'status':'independent_arithmetic_unavailable','reason':str(exc)}


def independent(name,case,result):
    if name.startswith('c031_'): return u1_independent(case,result)
    if name.startswith('c032_'): return sugra_independent(case,result)
    if name.startswith('c033_'): return lie_independent(case,result)
    if name.startswith('c035_'): return moonshine_independent(case,result)
    if name.startswith('c036_'): return mirror_independent(case,result)
    if name.startswith('c037_'): return fusion_independent(case,result)
    if name.startswith('c038_'): return curvature_independent(case,result)
    if name.startswith('c039_'): return gauge_independent(case,result)
    if name.startswith('c040_'): return reduction_independent(case,result)
    if name.startswith('c034_'):
        if result.get('status')!='SOLVED': return {'status':'typed_refusal_owner_replay_only','warning':'multiple_interior_points bypass documented by exact controls'}
        fd=result['face_data']; prods=fd.get('codim2_products',[])
        return {'status':'independent_returned_arithmetic_geometry_owner_routes','euler_identity':result['euler']==2*(result['h11']-result['h21']),
                'each_product_identity':all(r.get('product')==r.get('l_star_theta',0)*r.get('l_star_theta_star',0) for r in prods),
                'h11_formula':result['h11']==fd['l_delta_star']-5-sum(r['interior_points'] for r in fd['facets_delta_star'])+sum(r['product'] for r in fd.get('codim2_products_delta',[])),
                'scope':'Arithmetic only independently checked; geometric enumerations replayed via inspected owner routes, no HNF/Pick implementation exists.'}
    return {'status':'no_independent_checker_enabled'}


def reduction_root_data():
    """Weyl-reflection closure, distinct from owner's positive root-string growth.

    Cartan matrices and real-form/compact-subgroup identifications are admitted
    inputs; this does not prove the Cremmer--Julia symmetry or the branching.
    """
    from c040_m_theory_toroidal_cremmer_julia_scalar_count.judge_packet.checkers import coset_group_theory_checker as c2
    names=['SL(2)','SL(3)','SL(5)','SO(5,5)','E6','E7','E8','SO(3)','SO(5)','USp(8)','SU(8)','SO(16)']
    out={}
    for name in names:
        rank,edges,nsl=c2._c2_get_group_cartan(name)
        A=[[2*int(i==j) for j in range(rank)] for i in range(rank)]
        for u,v in edges:A[u][v]=A[v][u]=-1
        for (u,v),w in (nsl or {}).items():A[u][v]=w
        roots={tuple(sign*int(j==i) for j in range(rank)) for i in range(rank) for sign in [-1,1]}
        todo=list(roots)
        while todo:
            r=todo.pop()
            for j in range(rank):
                q=list(r);q[j]-=sum(r[i]*A[i][j] for i in range(rank));q=tuple(q)
                if q not in roots:roots.add(q);todo.append(q)
            if len(roots)>1000:raise ValueError('Root closure exceeds finite bound')
        positive={r for r in roots if all(a>=0 for a in r)}
        out[name]={'rank':rank,'roots':len(roots),'positive_roots':len(positive),'dim':rank+len(roots),
                   'owner_positive_root_set_match':positive==set(c2._c2_generate_positive_roots(A))}
    return out


def reduction_independent(case,result):
    if result.get('status')!='SOLVED':return {'status':'typed_refusal_owner_replay_only','scope':'Unknown-query and malformed-case reference refusals are not consistently admitted by owners.'}
    k=case['k'];D=11-k;query=case['query']; roots=reduction_root_data();dim=lambda g:roots[g]['dim']
    dimG=[None,1,dim('SL(2)')+1,dim('SL(3)')+dim('SL(2)'),dim('SL(5)'),dim('SO(5,5)'),dim('E6'),dim('E7'),dim('E8')][k]
    dimK=[None,0,1,dim('SO(3)')+1,dim('SO(5)'),2*dim('SO(5)'),dim('USp(8)'),dim('SU(8)'),dim('SO(16)')][k]
    # Count antisymmetric internal index subsets explicitly, not factorial formulas.
    forms={p:sum(1 for _ in itertools.combinations(range(k),3-p)) for p in range(4)}
    metric=sum(1 for _ in itertools.combinations_with_replacement(range(k),2))
    scalar=metric+forms[0]+sum(n for p,n in forms.items() if p>0 and p==D-2)+(k if D==3 else 0)
    vector=0 if D==3 else k+forms[1]+sum(n for p,n in forms.items() if p>1 and p==D-3)
    checks={'status':'independent_index_subset_Hodge_and_Weyl_closure','id_matches':result.get('id')==case.get('id'),
            'dimension_matches':result.get('D')==D,'scalar_coset_identity':scalar==dimG-dimK,
            'root_set_controls_match':all(v['owner_positive_root_set_match'] for v in roots.values()),
            'expected_scalar_total':scalar,'expected_vector_total':vector,
            'scope':'Internal-index subset counts and full Weyl closure are independent computations; field inventory, dual-potential degree rule, electric frame, Cartan types, compact subgroup identification and representation restriction remain premises. No physical M-theory equivalence or branching character proof.'}
    if query=='scalars':
        out=result['scalars'];expected={'metric':metric,'three_form':forms[0]}
        if D==5:expected['dual_C_mu_nu_rho']=forms[3]
        elif D==4:expected['dual_C_mu_nu_i']=forms[2]
        elif D==3:expected.update(dual_kk_vectors=k,dual_C_mu_ij=forms[1])
        else:expected['dual_forms']=0
        checks.update(total_matches=out['total']==scalar,components_match=all(out.get(a,0)==expected.get(a,0) for a in set(out)|set(expected) if a!='total'),nonnegative_components=all(type(v)is int and v>=0 for v in out.values()),additive_consistency=sum(v for a,v in out.items() if a!='total')==out['total'])
    elif query=='vectors':
        out=result['vectors'];expected={'metric_kk':k if D>3 else 0,'three_form':forms[1] if D>3 else 0,'dual_forms':sum(n for p,n in forms.items() if p>1 and p==D-3) if D>3 else 0,'total':vector}
        checks.update(total_matches=out['total']==vector,complete_components_match=out==expected)
    elif query=='coset':
        out=result['coset']; names=[None,('R+','1'),('SL(2)xR+','SO(2)'),('SL(3)xSL(2)','SO(3)xSO(2)'),('SL(5)','SO(5)'),('SO(5,5)','SO(5)xSO(5)'),('E6(6)','USp(8)'),('E7(7)','SU(8)'),('E8(8)','SO(16)')][k]
        checks.update(coset_dimensions_match=(out['dimG'],out['dimK'],out['difference'])==(dimG,dimK,scalar),labels_match_admitted_table=(out.get('G'),out.get('K'))==names)
    elif query=='branching':
        b=result['branching'];pdim=[None,1,3,7,5*6//2-1,5*5,math.comb(8,4)-math.comb(8,2),math.comb(8,4),2**7][k]
        checks.update(representation_dimensions_match=[r[1] for r in b]==[dimK,pdim],total_dimension_match=sum(r[1] for r in b)==dimG,
                      label_evidence_ceiling='Labels inspected against retained declared branch; no weight restriction matrix or character identity is implemented by either owner.')
    return checks


def gauge_independent(case,result):
    if result.get('status')!='SOLVED': return {'status':'typed_refusal_owner_replay_only','scope':'Checker topology/refusal schema weaknesses separately reproduced.'}
    edges=case['edges']; vs=case['vertices']; n=len(edges)
    if not (isinstance(vs,list) and all(type(x)is int for x in vs) and all(isinstance(e,list) and len(e)==2 and all(type(x)is int for x in e) for e in edges)):
        return {'status':'alternate_encoding_owner_only','scope':'Independent adapter deliberately supports canonical integer-vertex pair-edge representation.'}
    def rank(rows):
        piv={}
        for s in rows:
            s=set(s)
            while s:
                p=max(s)
                if p in piv:s ^= piv[p]
                else:piv[p]=s;break
        return len(piv)
    star=[{i for i,(a,b) in enumerate(edges) if (a==v)!=(b==v)} for v in vs];ra=rank(star)
    if case['query']=='gauss_law_sector':
        c=case['charges']; charges=[c[str(v)] for v in vs] if isinstance(c,dict) else c
        welltyped=len(charges)==len(vs) and all(type(x)is int and x in [-1,1] for x in charges)
        expected=0 if math.prod(charges)==-1 else 2**(n-ra)
        finite=None
        if n<=16:
            masks=[sum(1<<e for e in s) for s in star]
            finite=sum(all(((z&m).bit_count()%2)==int(c==-1) for m,c in zip(masks,charges)) for z in range(1<<n))
        return {'status':'independent_star_rank_and_X_basis_count','charge_schema_valid':welltyped,'rank_star':ra,'dimension_matches':result['sector_dimension']==expected,'enumerated_X_basis_states':1<<n if n<=16 else None,'enumerated_dimension':finite,'enumerated_match':finite==result['sector_dimension'] if finite is not None else None,'scope':'Exact simultaneous X-eigenvalue assignment count for E<=16; larger cases use independently reduced incidence rank, conditional on connected graph and complete charge schema.'}
    faces=case['faces']; plaq=[]; traversal=Counter();walkvalid=True
    for face in faces:
        if not all(isinstance(x,list) and len(x)==2 and type(x[0])is int and type(x[1])is int for x in face):
            return {'status':'alternate_face_encoding_owner_only'}
        coeff=Counter(e for e,d in face);traversal.update(coeff);plaq.append({e for e,c in coeff.items() if c%2})
        for (e,d),(f,t) in zip(face,face[1:]+face[:1]):
            walkvalid &= d in [-1,1] and t in [-1,1] and 0<=e<n and 0<=f<n
            if walkvalid:walkvalid &= edges[e][1 if d==1 else 0]==edges[f][0 if t==1 else 1]
    rb=rank(plaq);k=n-ra-rb;chain=all(len(a&b)%2==0 for a in star for b in plaq)
    z=[{i for i,c in enumerate(w) if c=='Z'} for w in result['logicals']['z']]; x=[{i for i,c in enumerate(w) if c=='X'} for w in result['logicals']['x']]
    flat=None
    if n<=16:
        masks=[sum(1<<e for e in s) for s in plaq]
        flat=sum(all((v&m).bit_count()%2==0 for m in masks) for v in range(1<<n))//(1<<ra)
    return {'status':'independent_set_elimination_and_logical_certificate','face_walks_valid':walkvalid,'edge_occurrences_two':all(traversal[e]==2 for e in range(n)),'chain_complex':chain,'ranks_match':(ra,rb)==(result['rank_star'],result['rank_plaquette']),'k_gsd_match':k==result['k'] and 2**k==result['gsd'],'logical_centralizer':all(len(a&b)%2==0 for a in z for b in star) and all(len(a&b)%2==0 for a in x for b in plaq),'logical_pairing':len(z)==len(x)==k and all(len(a&b)%2==int(i==j) for i,a in enumerate(z) for j,b in enumerate(x)),'quotient_independence':rank(plaq+z)==rb+k and rank(star+x)==ra+k,'flat_state_quotient_gsd':flat,'finite_gsd_match':flat==result['gsd'] if flat is not None else None,'scope':'Independent set-based F2 elimination and all logical pairings; enumerate computational flat states for E<=16 then divide free star orbit size. Local surface links still use inspected owner topology, whose shared code is not independent.'}


def curvature_independent(case,result):
    from fractions import Fraction as F
    from collections import defaultdict, deque
    if result.get('status')!='SOLVED': return {'status':'typed_refusal_owner_replay_only','scope':'Owner checks reason kind; witness coordinates/counts are not bound, as synthetic controls show.'}
    if case['query']=='surface':
        tris=[tuple(sorted(t)) for t in case['triangles']]; verts=sorted(set(sum((list(t) for t in tris),[]))); es=Counter(e for t in tris for e in itertools.combinations(t,2)); adj={v:set() for v in verts}
        for a,b in es:adj[a].add(b);adj[b].add(a)
        def connected(ad):
            if not ad:return False
            seen=set(); todo=[next(iter(ad))]
            while todo:
                v=todo.pop()
                if v in seen:continue
                seen.add(v);todo.extend(ad[v]-seen)
            return len(seen)==len(ad)
        links=True
        for v in verts:
            link=defaultdict(set)
            for t in tris:
                if v in t:
                    a,b=[x for x in t if x!=v];link[a].add(b);link[b].add(a)
            links &= len(link)>=3 and all(len(n)==2 for n in link.values()) and connected(link)
        ei={e:i for i,e in enumerate(sorted(es))}; cols=[]
        for a,b,c in tris:
            col=[0]*len(es)
            for e,z in [((b,c),1),((a,c),-1),((a,b),1)]:col[ei[e]]=z%3
            cols.append(col)
        basis={}
        for row in cols:
            for j in range(len(row)):
                if row[j]:
                    if j in basis:row=[(x-row[j]*y)%3 for x,y in zip(row,basis[j])]
                    else:
                        inv=pow(row[j],-1,3);basis[j]=[(x*inv)%3 for x in row];break
        b2=len(tris)-len(basis); chi=len(verts)-len(es)+len(tris)
        curv={str(v):F(6-len(adj[v]),6) for v in verts}
        return {'status':'independent_incidence_links_GF3_top_homology','simple_faces':len(set(tris))==len(tris),'closed_connected_manifold':all(n==2 for n in es.values()) and links and connected(adj),'counts_match':[result[k] for k in ['V','E','F']]==[len(verts),len(es),len(tris)],'euler_match':result['euler']==chi,'curvature_match':{k:F(v) for k,v in result['vertex_curvature'].items()}==curv,'gauss_bonnet':sum(curv.values())==chi,'orientability_match':result['orientable']==(b2==1),'b2_GF3':b2,'scope':'Odd-characteristic top homology detects orientability conditional on verified closed connected surface; no integral Smith form or continuum geometry claim.'}
    edges={tuple(sorted(e)) for e in case['edges']};vs=sorted(set(sum((list(e) for e in edges),[])));adj={v:set() for v in vs}
    for a,b in edges:adj[a].add(b);adj[b].add(a)
    d={}
    for v in vs:
        ds={v:0};q=deque([v])
        while q:
            x=q.popleft()
            for y in adj[x]:
                if y not in ds:ds[y]=ds[x]+1;q.append(y)
        d[v]=ds
    alpha=F(case['alpha']);checked=[]
    def measure(v):return {x:alpha if x==v else (1-alpha)/len(adj[v]) if x in adj[v] else F(0) for x in vs}
    for row in result['edges']:
        u,v=row['edge']; mu,mv=measure(u),measure(v);rs=Counter();cs=Counter();cost=F(0);positive=True
        for z in row['plan']:
            a,b=z.get('from',z.get('source')),z.get('to',z.get('target'));w=F(z['mass']);rs[a]+=w;cs[b]+=w;cost+=w*d[a][b];positive &= w>0
        phi={int(k):F(v) for k,v in row['potential'].items()};dual=sum(phi[x]*(mu[x]-mv[x]) for x in vs)
        checked.append({'edge':[u,v],'positive':positive,'marginals':all(rs[x]==mu[x] and cs[x]==mv[x] for x in vs),'lipschitz':all(abs(phi[a]-phi[b])<=1 for a,b in edges),'zero_gap':dual==cost,'ollivier':F(row['ollivier'])==1-cost,'forman':row['forman']==4-len(adj[u])-len(adj[v]),'primal_cost':str(cost)})
    return {'status':'independent_full_primal_dual_certificate','edge_coverage':len(result['edges'])==len(edges) and {tuple(sorted(r['edge'])) for r in result['edges']}==edges,'edges':checked,'scope':'Elementary weak-duality proof: every Lipschitz potential objective <= every feasible transport cost; equality certifies the optimum without trusting either optimization algorithm.'}


def fusion_independent(case,result):
    from fractions import Fraction as F
    if result.get('status')!='SOLVED': return {'status':'typed_refusal_owner_replay_only'}
    def matrices(k):
        n=k+1; ident=[[int(i==j) for j in range(n)] for i in range(n)]
        adj=[[int(abs(i-j)==1) for j in range(n)] for i in range(n)]
        rows=[ident]
        if k: rows.append(adj)
        for a in range(2,k+1):
            rows.append([[sum(rows[-1][t][j] for t in (i-1,i+1) if 0<=t<n)-rows[-2][i][j] for j in range(n)] for i in range(n)])
        return rows
    labels=[tuple(x['label']) for x in result['primaries']]; expected={}; model=case['model']
    if model=='su2':
        k=case['k']; m=matrices(k); target=[(i,) for i in range(k+1)]
        c=F(3*k,k+2); hs=[F(i*(i+2),4*(k+2)) for i in range(k+1)]
        for a in range(k+1):
            for b in range(a,k+1):
                for d in range(k+1):
                    if m[a][b][d]:expected[((a,),(b,),(d,))]=m[a][b][d]
    else:
        p,pp=case['p'],case['p_prime']; m1,m2=matrices(pp-2),matrices(p-2)
        canon=lambda r,s:(r,s) if (s,r)<=(p-s,pp-r) else (pp-r,p-s)
        target=sorted({canon(r,s) for r in range(1,pp) for s in range(1,p)})
        c=1-F(6*(p-pp)**2,p*pp);hs=[F((p*r-pp*s)**2-(p-pp)**2,4*p*pp) for r,s in target]
        for i,a in enumerate(target):
            for b in target[i:]:
                accum=Counter()
                for r in range(1,pp):
                    for s in range(1,p):accum[canon(r,s)]+=m1[a[0]-1][b[0]-1][r-1]*m2[a[1]-1][b[1]-1][s-1]
                for d,v in accum.items():
                    if v:expected[(a,b,d)]=v
    actual={(tuple(a),tuple(b),tuple(c)):v for a,b,c,v in result['fusion']}
    return {'status':'independent_path_graph_Chebyshev_recurrence','labels_match':labels==target,'central_charge_match':F(result['central_charge'])==c,'weights_match':[F(x['h']) for x in result['primaries']]==hs,'fusion_match':actual==expected,'id_matches':result.get('id',result.get('case_id'))==case.get('case_id',case.get('id')),'ignored_case_fields':sorted(set(case)-{'case_id','id','model','k','p','p_prime'}),'scope':'All coefficients from integer path adjacency recurrence; minimal Kac quotient and conformal formulas are admitted model premises, not a CFT existence or unitarity proof.'}


def lie_independent(case,result):
    if result.get('status')!='SOLVED': return {'status':'typed_refusal_owner_replay_only'}
    if case.get('algebra')!='A1': return {'status':'owner_character_routes_or_shared_tensor_only','scope':'Freudenthal and Kostant character computations share root/Weyl data; tensor decomposition is shared.'}
    if case.get('query')=='character':
        n=abs(case['weight'][0]); expected=[[[i],1] for i in range(n,-1,-2)]
        return {'status':'independent_A1_character','dimension_matches':result.get('dimension')==n+1,'multiplicities_match':result.get('dominant_multiplicities')==expected}
    a,b=abs(case['left'][0]),abs(case['right'][0]); expected=[[[i],1] for i in range(a+b,abs(a-b)-1,-2)]
    return {'status':'independent_A1_Clebsch_Gordan','decomposition_matches':result.get('decomposition')==expected}


def moonshine_independent(case,result):
    if case.get('query')!='decompose' or result.get('status')!='SOLVED':
        return {'status':'owner_series_or_refusal_routes','scope':'Distinct Laurent-product and rational half-period series routes; source mathematical normalization remains premise.'}
    from fractions import Fraction
    from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.mathieu_moonshine import TABLE_M24,IRREP_NAMES,CLASSES_M24,parse_character_value,compute_coefficients_exact
    good=True; residuals=[]
    for cls,val in zip(case['class_order'],case['values'],strict=True):
        j=CLASSES_M24.index(cls); re=Fraction(0); im=Counter()
        for name,m in result['multiplicities'].items():
            a,b,p=TABLE_M24[IRREP_NAMES.index(name)][j];re+=Fraction(m*a,2)
            if b: im[p]+=Fraction(m*b,2)
        a,b,p=parse_character_value(val);re-=Fraction(a,2)
        if b: im[p]-=Fraction(b,2)
        bad=bool(re or any(im.values()));good &= not bad
        if bad:residuals.append({'class':cls,'real':str(re),'imaginary':{str(k):str(v) for k,v in im.items() if v}})
    n=case.get('n'); bound=type(n)is int and 1<=n<=30
    identity=case['values'][case['class_order'].index('1A')]
    return {'status':'independent_all_class_reconstruction','matches':good,'residuals':residuals,
            'n_within_advertised_series_range':bound,'identity_matches_An':identity==compute_coefficients_exact(n)[str(n)] if bound else None,
            'scope':'Independent exact real and distinct-radicand reconstruction against admitted embedded M24 table; n-identity check exposes disconnect, not authenticity of twining provenance.'}


def mirror_independent(case,result):
    from fractions import Fraction as F
    if result.get('status')!='SOLVED': return {'status':'typed_refusal_owner_replay_only'}
    w,d,D=case['weights'],case['degree'],case['max_curve_degree']
    H=lambda n:sum((F(1,j) for j in range(1,n+1)),F(0))
    c=[F(math.factorial(d*n),math.prod(math.factorial(a*n) for a in w)) for n in range(D+1)]
    t=[c[n]*(d*H(d*n)-sum(a*H(a*n) for a in w)) for n in range(D+1)]
    S=[]
    for n in range(D+1):S.append(t[n]-sum(c[j]*S[n-j] for j in range(1,n+1)))
    inv=[]
    for k in range(1,D+1):
        E=[F(1)]
        for n in range(1,k):E.append(-k*sum(j*S[j]*E[n-j] for j in range(1,n+1))/n)
        inv.append(E[k-1]/k)
    gv={int(k):int(v) for k,v in result['gv'].items()}
    gwcheck=all(F(result['gw'][str(k)])==sum(F(gv[k//j],j**3) for j in range(1,k+1) if k%j==0) for k in range(1,D+1))
    kappa=F(d,math.prod(w));mu=F(d**d,math.prod(a**a for a in w));n1=kappa*(mu-2*c[1]-3*S[1])
    return {'status':'independent_Lagrange_inverse_and_multicover','mirror_coefficients_match':[F(v) for v in result['mirror_map_coeffs']]==inv,'GW_divisor_relations':gwcheck,'kappa_matches':F(result['kappa'])==kappa,'GV1_linear_formula_matches':gv[1]==n1,'scope':'Exact Lagrange coefficient formula independently checks reversion; higher GV Yukawa interpretation remains admitted normalization plus owner computations.'}


def u1_independent(case, result):
    """Own finite multiset enumeration and elementary certificate arithmetic."""
    n, bound = case.get("n"), case.get("bound")
    if result.get("status") != "SOLVED":
        return {"status": "typed_refusal_owner_replay_only"}
    if type(n) is not int or type(bound) is not int or n < 1 or bound < 1:
        return {"status": "invalid_input_domain"}
    def valid(q):
        return (len(q) == n and all(type(x) is int and x != 0 and abs(x) <= bound for x in q)
                and sum(q) == sum(x**3 for x in q) == 0 and math.gcd(*q) == 1
                and Counter(q) != Counter(-x for x in q))
    if case.get("query") == "enumerate":
        sols = result.get("solutions", [])
        arithmetic = all(valid(q) for q in sols)
        count = math.comb(2*bound + n - 1, n)
        if count > 1_000_000:
            return {"status": "arithmetic_checked_completeness_owner_only", "arithmetic": arithmetic,
                    "independent_combinations_limit": 1_000_000, "would_enumerate": count}
        expected = set()
        for q in itertools.combinations_with_replacement([x for x in range(-bound, bound+1) if x], n):
            if valid(q):
                expected.add(min(q, tuple(sorted(-x for x in q))))
        supplied = {tuple(q) for q in sols}
        return {"status": "independent_finite_complete", "equal": supplied == expected,
                "count": len(expected), "arithmetic": arithmetic, "combinations": count}
    fixed = case.get("fixed", [])
    comp = result.get("completion")
    if comp is not None:
        return {"status": "independent_positive_certificate", "valid": valid(fixed + comp)}
    missing = n - len(fixed)
    if missing < 0:
        return {"status": "invalid_input_domain"}
    count = math.comb(2*bound + missing - 1, missing)
    if count > 1_000_000:
        return {"status": "negative_claim_owner_shared_search_only", "would_enumerate": count}
    exists = any(valid(fixed + list(q)) for q in itertools.combinations_with_replacement(
        [x for x in range(-bound, bound+1) if x], missing))
    return {"status": "independent_finite_no_completion", "exists": exists, "combinations": count}


def artifact_check(path, data):
    name = family(path)
    solve, evaluate = load_owners(name)
    if "/mutation_suite/" in path:
        case = data["case"]
        answer = data.get("corrupted_result", data.get("result"))
        return {"role": "retained_mutant", "owner_verdict": evaluate(case, answer),
                "evidence_ceiling": "Actual mutant replay; rejection is local adequacy evidence, not universal soundness."}
    if "/examples/" in path:
        case, answer = data.get("input",data.get("case",data)), data.get("expected_output",data.get("output",data.get("expected")))
        fresh = solve(case)
        if answer is None:
            return {'role':'example_input_only','fresh_reference':fresh,'owner_verdict':evaluate(case,fresh),'independent':independent(name,case,fresh),'evidence_ceiling':'No retained answer; fresh offline replay of example input only.'}
        return {"role": "retained_example", "owner_verdict": evaluate(case, answer),
                "fresh_reference_equal": fresh == answer,
                "independent": independent(name,case,answer),
                "evidence_ceiling": "Retained answer checked by owner and stated independent finite control."}
    if "/cases/" in path:
        answer = solve(data)
        return {"role": "judge_case", "fresh_reference": answer,
                "owner_verdict": evaluate(data, answer), "independent": independent(name,data,answer),
                "evidence_ceiling": "Fresh offline reference/owner replay and stated independent check, not provider evidence."}
    if path.endswith("answers.jsonl"):
        examples = {}
        for p in ROWS:
            if family(p) == name and "/examples/" in p:
                item = json.loads((ROOT/p).read_text())
                examples[item["input"].get("id", item["input"].get("case_id"))] = item["input"]
        records = []
        for i, answer in enumerate(data, 1):
            case = examples.get(answer.get("id"))
            records.append({"line": i, "owner_verdict": evaluate(case, answer) if case else None,
                            "independent": u1_independent(case, answer) if case else None})
        return {"role": "retained_answer_stream", "records": records,
                "evidence_ceiling": "Historical local outputs replayed; no model execution or provenance authentication."}
    raise ValueError("Unsupported artifact role")


def metadata(path, data):
    if path.endswith("/manifest.json"):
        entries = data["files"]
        checks = []
        for item in entries:
            target = (ROOT/path).parent / item["path"]
            try:
                rel = target.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                checks.append({"path": item["path"], "status": "outside_repository_not_followed"}); continue
            if rel not in ROWS:
                checks.append({"path": item["path"], "status": "outside_scope_not_followed"}); continue
            if not target.is_file():
                checks.append({"path": item["path"], "status": "missing"}); continue
            raw = target.read_bytes(); lf = raw.replace(b"\r\n", b"\n")
            hash_key = "sha256"; size_key = "size_bytes" if "size_bytes" in item else "bytes"
            checks.append({"path": item["path"], "status": "raw_match" if digest(raw)==item.get(hash_key) else
                           "LF_normalized_match" if digest(lf)==item.get(hash_key) else "hash_mismatch",
                           "raw_bytes":len(raw),"declared_bytes":item.get(size_key),
                           "raw_size_match":len(raw)==item.get(size_key),"LF_size_match":len(lf)==item.get(size_key)})
        count_fields={k:data[k] for k in ('file_count','files_count','declared_file_count') if k in data}
        return {"role":"historical_manifest","declared_count":data.get("file_count",data.get("files_count")),"declared_count_fields":count_fields,"all_declared_counts_match":all(v==len(entries) for v in count_fields.values()),"actual_count":len(entries),
                "unique_paths":len({r['path'] for r in entries})==len(entries),
                "ordinal_sorted": [r['path'] for r in entries]==sorted([r['path'] for r in entries],key=lambda p:p.encode()),
                "references":checks,"evidence_ceiling":"Byte custody only; raw/checkout normalization distinguished; no semantic proof."}
    if path.endswith("/accounting.json"):
        calls=data.get("calls")
        if 'calls' not in data and not any(k.startswith('total_') for k in data):
            return {'role':'budget_configuration_only','configuration':data,
                    'checks':{'fallbacks_disabled':data.get('allow_fallbacks') is False,
                              'target_within_ceiling':0<=data.get('target_cost_usd',-1)<=data.get('cost_ceiling_usd',-1),
                              'model_ceiling_positive':data.get('model_ceiling_parameters')=='70B' or isinstance(data.get('model_ceiling_parameters'),(int,float)) and data['model_ceiling_parameters']>0},
                    'evidence_ceiling':'Budget declarations only; no call ledger, enforcement or live billed execution is present.'}
        if calls==[]:
            fields={k:v for k,v in data.items() if k.startswith('total_')}
            return {"role":"empty_accounting_template","totals":fields,"all_totals_zero":all(v==0 for v in fields.values()),
                    "calls":0,"evidence_ceiling":"Empty template, not fresh billing or a completed provider arm."}
        return {"role":"accounting","status":"schema_pending","evidence_ceiling":"Nonempty accounting semantics require owner review."}
    return None


def worker(path):
    # Reviewed owners are pure Python. Refuse network and child execution if drift reaches either.
    def guard(event,args):
        if event in {"socket.connect","socket.getaddrinfo","subprocess.Popen","os.system"}:
            raise RuntimeError("AUDIT_FORBIDDEN:"+event)
    sys.addaudithook(guard)
    raw=(ROOT/path).read_bytes()
    assert digest(raw)==ROWS[path]["sha256"], "Scope bytes changed"
    if path.endswith('.jsonl'):
        parsed=[strict_load(s) for s in raw.decode('utf-8-sig').splitlines() if s.strip()]
        data=[x[0] for x in parsed]; duplicates=[k for x in parsed for k in x[1]]
    else:
        data,duplicates=strict_load(raw.decode('utf-8-sig'))
    result=metadata(path,data) or artifact_check(path,data)
    return {"path":path,"sha256":digest(raw),"duplicate_keys":duplicates,"checks":["pinned_raw_sha256","strict_json_parse",result],
            "status":"reviewed_with_stated_limits","evidence_ceiling":result["evidence_ceiling"]}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--family');ap.add_argument('--worker');ap.add_argument('--timeout',type=float,default=30)
    args=ap.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker),ensure_ascii=False));return
    paths=[p for p in ROWS if family(p).startswith(args.family+'_') and Path(p).suffix not in ('.py','.md')]
    out=PREFIX.with_name(PREFIX.name+'_'+args.family+'_automated.jsonl')
    counts=Counter(); started=time.monotonic()
    with out.open('w',encoding='utf-8') as stream:
        for p in paths:
            try:
                run=subprocess.run([sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--worker',p],cwd=ROOT,
                                   capture_output=True,text=True,encoding='utf-8',timeout=args.timeout)
                if run.returncode:
                    result={'path':p,'sha256':ROWS[p]['sha256'],'status':'execution_error','error':run.stderr[-3000:],
                            'evidence_ceiling':'No completed semantic replay; explicit unresolved error.'}
                else: result=json.loads(run.stdout)
            except subprocess.TimeoutExpired:
                result={'path':p,'sha256':ROWS[p]['sha256'],'status':'timeout','timeout_seconds':args.timeout,
                        'evidence_ceiling':'Bounded owner replay incomplete; timeout is not a false-certificate verdict.'}
            stream.write(json.dumps(result,ensure_ascii=False)+'\n');stream.flush();counts[result['status']]+=1
    print(json.dumps({'family':args.family,'files':len(paths),'counts':dict(counts),'seconds':time.monotonic()-started,'output':str(out)}))


if __name__=='__main__':main()

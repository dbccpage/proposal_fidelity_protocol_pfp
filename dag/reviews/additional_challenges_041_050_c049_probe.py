"""Bounded category counterchecks from independently constructed inputs."""
import sys, itertools, copy, json
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT, write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c049_finite_category_universal_constructions.reference_solver import solve
from c049_finite_category_universal_constructions.judge_packet.exact_checker import check_solution
from c049_finite_category_universal_constructions.judge_packet.independent_checker import independent_check

def verdict(c,a):
    values=[]
    for f in (check_solution,independent_check):
        try:values.append(f(c,a))
        except Exception as e:values.append({'exception':type(e).__name__,'message':str(e)})
    return values

def independent_category(data):
    """Check explicit data with identity equations, allowing implicit identity entries only.
    Omitted nonidentity composition is inferred only for singleton target hom sets,
    matching the advertised compact representation while retaining conflicting entries.
    """
    try:
        objs=data['objects']; rows=data['morphisms']; raw=data.get('comp',{})
        if len(set(objs))!=len(objs) or len({m[0] for m in rows})!=len(rows):return {'valid':False,'reason':'duplicate name'}
        morph={m[0]:(m[1],m[2]) for m in rows}
        if any(s not in objs or t not in objs for s,t in morph.values()):return {'valid':False,'reason':'unknown endpoint'}
        identities={}
        def get(g,f):
            if morph[f][1]!=morph[g][0]:return None
            if f in raw.get(g,{}):return raw[g][f]
            if identities.get(morph[f][0])==f:return g
            if identities.get(morph[g][1])==g:return f
            opts=[h for h,(s,t) in morph.items() if (s,t)==(morph[f][0],morph[g][1])]
            return opts[0] if len(opts)==1 else None
        # Use conventional identity labels only when omitted entries need completing.
        for o in objs:
            end=[m for m,(s,t) in morph.items() if s==t==o]
            named=[m for m in end if m.startswith('id')]
            if len(named)==1:identities[o]=named[0]
            else:
                candidates=[e for e in end if all(raw.get(e,{}).get(f)==f for f,(_,t) in morph.items() if t==o) and all(raw.get(f,{}).get(e)==f for f,(s,_) in morph.items() if s==o)]
                if len(candidates)!=1:return {'valid':False,'reason':'identity unresolved'}
                identities[o]=candidates[0]
        for o,e in identities.items():
            if any(get(e,f)!=f for f,(_,t) in morph.items() if t==o) or any(get(f,e)!=f for f,(s,_) in morph.items() if s==o):return {'valid':False,'reason':'identity equation'}
        for f,g in itertools.product(morph,repeat=2):
            if morph[f][1]==morph[g][0]:
                h=get(g,f)
                if h not in morph or morph[h]!=(morph[f][0],morph[g][1]):return {'valid':False,'reason':'typed closure'}
        for f,g,h in itertools.product(morph,repeat=3):
            if morph[f][1]==morph[g][0] and morph[g][1]==morph[h][0] and get(h,get(g,f))!=get(get(h,g),f):return {'valid':False,'reason':'associativity'}
        return {'valid':True,'objects':len(objs),'morphisms':len(morph)}
    except Exception as e:return {'valid':False,'reason':type(e).__name__}

def main():
    out={}
    chain={'case_id':'audit_chain','task':'LIMIT','shape':'terminal','objects':['0','1'],'morphisms':[['id0','0','0'],['id1','1','1'],['f','0','1']],'comp':{},'diagram':[]}
    wrong={'case_id':chain['case_id'],'status':'SOLVED','kind':'EXISTS','apex':'0','legs':{}}
    out['wrong_terminal_apex']={'case':chain,'answer':wrong,'actual_terminal':'1','hom_1_0':0,'owner_verdict':verdict(chain,wrong)}
    false={'case_id':chain['case_id'],'status':'SOLVED','kind':'DOES_NOT_EXIST'}
    out['false_absence']={'owner_verdict':verdict(chain,false)}
    bad=copy.deepcopy(chain);bad['comp']={'id0':{'id0':'f'}}
    out['contradictory_identity_entry']={'case':bad,'independent':independent_category(bad),'fresh_answer':solve(bad),'owner_verdict':verdict(bad,solve(bad))}
    # Identity functor on the one-object S3 category. Noncentral unit is not natural.
    perms=list(itertools.permutations(range(3))); names={p:('id0' if p==(0,1,2) else 'm'+str(i)) for i,p in enumerate(perms)}
    cat={'objects':['o'],'morphisms':[[names[p],'o','o'] for p in perms],'comp':{names[g]:{names[f]:names[tuple(g[f[i]] for i in range(3))] for f in perms} for g in perms}}
    fun={'objects':{'o':'o'},'morphisms':{m[0]:m[0] for m in cat['morphisms']}}
    adj={'case_id':'audit_non_natural','task':'ADJUNCTION','category_C':cat,'category_D':cat,'F':fun,'G':fun}
    u=names[(1,0,2)];h=names[(0,2,1)]
    ans={'case_id':adj['case_id'],'status':'SOLVED','kind':'ADJOINT','unit':{'o':u},'counit':{'o':u}}
    out['non_natural_unit']={'case':adj,'answer':ans,'naturality_left':cat['comp'][h][u],'naturality_right':cat['comp'][u][h],'owner_verdict':verdict(adj,ans)}
    c2={'objects':['o'],'morphisms':[['id0','o','o'],['h','o','o']],'comp':{'h':{'h':'id0'}}}
    invalid={'case_id':'audit_bad_functor','task':'ADJUNCTION','category_C':c2,'category_D':c2,'F':{'objects':{'o':'o'},'morphisms':{'id0':'h','h':'id0'}},'G':{'objects':{'o':'o'},'morphisms':{'id0':'id0','h':'h'}}}
    a=solve(invalid);out['identity_breaking_functor']={'case':invalid,'fresh_answer':a,'owner_verdict':verdict(invalid,a),'invalid_reason':'F(id_o)=h != id_o'}
    # Concrete subcategory of finite sets: maps generated by projections, diagonal,
    # and both named points. P = A x A, with 15 arrows total.
    elems={'T':[0],'A':[0,1],'P':list(itertools.product(range(2),repeat=2))}
    arrows=[]
    def add(s,t,vals,name):arrows.append((name,s,t,tuple(vals)))
    for o,es in elems.items():add(o,o,range(len(es)),'id'+o)
    for x in range(2):add('T','A',[x],'a'+str(x))
    for x in range(4):add('T','P',[x],'p'+str(x))
    add('A','P',[0,3],'diag')
    for j in range(2):add('P','A',[x[j] for x in elems['P']],'proj'+str(j))
    for j,k in ((0,0),(1,0),(1,1)):
        add('P','P',[elems['P'].index((x[j],x[k])) for x in elems['P']],f'e{j}{k}')
    bymap={(s,t,v):n for n,s,t,v in arrows}; comp={}
    for g,sg,tg,vg in arrows:
        for f,sf,tf,vf in arrows:
            if tf==sg:comp.setdefault(g,{})[f]=bymap[sf,tg,tuple(vg[i] for i in vf)]
    product={'case_id':'audit_repeated_object','task':'LIMIT','shape':'product','objects':list(elems),'morphisms':[[n,s,t] for n,s,t,v in arrows],'comp':comp,'diagram':['A','A']}
    counts=[]
    for o in elems:
        to_a=[n for n,s,t,v in arrows if s==o and t=='A'];to_p=[n for n,s,t,v in arrows if s==o and t=='P']
        for f,g in itertools.product(to_a,repeat=2):counts.append(sum(comp['proj0'][u]==f and comp['proj1'][u]==g for u in to_p))
    a=solve(product);out['repeated_object_product']={'case':product,'independent_category':independent_category(product),'universal_cones':len(counts),'every_cone_unique':all(n==1 for n in counts),'actual_apex':'P','fresh_answer':a,'owner_verdict':verdict(product,a)}
    # All labelled three-object partial orders; compare owner products/coproducts
    # to meet/join equations, independently computed from relation membership.
    pairs=[(a,b) for a in range(3) for b in range(3) if a!=b];checks=0;orders=0;bad=[]
    for bits in itertools.product((0,1),repeat=6):
        rel={(i,i) for i in range(3)}|{p for p,b in zip(pairs,bits) if b}
        if any(a!=b and (b,a) in rel for a,b in rel) or any((a,c) not in rel for a,b in rel for bb,c in rel if b==bb):continue
        orders+=1;mors=[[('id'+str(a) if a==b else f'm{a}{b}'),str(a),str(b)] for a,b in sorted(rel)]
        for x,y in itertools.product(range(3),repeat=2):
            for task,shape in [('LIMIT','product'),('COLIMIT','coproduct')]:
                bound=[z for z in range(3) if ((z,x) in rel and (z,y) in rel if task=='LIMIT' else (x,z) in rel and (y,z) in rel)]
                best=[z for z in bound if all(((w,z) in rel if task=='LIMIT' else (z,w) in rel) for w in bound)]
                c={'case_id':'audit_poset','task':task,'shape':shape,'objects':['0','1','2'],'morphisms':mors,'comp':{},'diagram':[str(x),str(y)]};a=solve(c);checks+=1
                if (a.get('kind')=='EXISTS')!=bool(best) or (best and a.get('apex')!=str(best[0])):bad.append({'case':c,'answer':a,'best':best})
    out['poset_exhaustion']={'orders':orders,'comparisons':checks,'mismatches':bad}
    write('_c049_probes.json',out)
    print(json.dumps({k:({a:b for a,b in v.items() if a not in ('case','answer')} if isinstance(v,dict) else v) for k,v in out.items()},ensure_ascii=False))
if __name__=='__main__':main()

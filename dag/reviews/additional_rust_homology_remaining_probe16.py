import sys,json,itertools,collections
sys.dont_write_bytecode=True
from pathlib import Path
def phase(n,edges,theta,m):
    adj=[[] for _ in range(n)]
    for (u,v),h in zip(edges,theta):adj[u].append((v,h));adj[v].append((u,(-h)%m))
    vals=[None]*n;ok=True
    for r in range(n):
        if vals[r] is not None:continue
        vals[r]=0;stack=[r]
        while stack:
            u=stack.pop()
            for v,h in adj[u]:
                p=(vals[u]+h)%m
                if vals[v] is None:vals[v]=p;stack.append(v)
                elif vals[v]!=p:ok=False
    return ok,vals
def coloring(n,edges):
    adj=[set() for _ in range(n)]
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    c=[None]*n;p=[None]*n
    for r in range(n):
        if c[r] is not None:continue
        c[r]=0;q=collections.deque([r])
        while q:
            u=q.popleft()
            for v in sorted(adj[u]):
                if c[v] is None:c[v]=1-c[u];p[v]=u;q.append(v)
                elif c[v]==c[u]:
                    def ancestors(x):
                        a=[]
                        while x is not None:a.append(x);x=p[x]
                        return a
                    a,b=ancestors(u),ancestors(v);i,j=len(a),len(b)
                    while i>0 and j>0 and a[i-1]==b[j-1]:i-=1;j-=1
                    return False,a[:i+1]+list(reversed(b[:j]))
    return True,c
phasecases=colorcases=f2cases=0
for n in range(5):
    pairs=list(itertools.combinations(range(n),2))
    for mask in range(1<<len(pairs)):
        edges=[e for i,e in enumerate(pairs) if mask>>i&1]
        for m in (2,3):
            image={tuple((v[b]-v[a])%m for a,b in edges) for v in itertools.product(range(m),repeat=n)}
            for theta in itertools.product(range(m),repeat=len(edges)):
                ok,alpha=phase(n,edges,theta,m);assert ok==(theta in image)
                if ok:assert tuple((alpha[b]-alpha[a])%m for a,b in edges)==theta
                phasecases+=1
        image={sum((((f>>a)^(f>>b))&1)<<i for i,(a,b) in enumerate(edges)) for f in range(1<<n)}
        cycles=[]
        for z in range(1,1<<len(edges)):
            parity=0
            for i,(u,v) in enumerate(edges):
                if z>>i&1:parity^=(1<<u)^(1<<v)
            if parity==0:cycles.append(z)
        for h in range(1<<len(edges)):
            assert (h not in image)==any((h&z).bit_count()%2 for z in cycles)
            assert (min((h^x).bit_count() for x in image)==0)==(h in image)
            f2cases+=1
    loop_pairs=list(itertools.combinations_with_replacement(range(n),2))
    for mask in range(1<<len(loop_pairs)):
        edges=[e for i,e in enumerate(loop_pairs) if mask>>i&1]
        ok,w=coloring(n,edges)
        brute=any(all(((f>>u)^(f>>v))&1 for u,v in edges) for f in range(1<<n))
        assert ok==brute
        if not ok:assert len(w)%2==1 and len(set(w))==len(w) and all(tuple(sorted((w[i],w[(i+1)%len(w)]))) in edges for i in range(len(w)))
        colorcases+=1
def mul(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
perms=list(itertools.permutations(range(2)));signs=list(itertools.product((-1,1),repeat=2));symmetry=0
for entries in itertools.product((-1,0,1),repeat=4):
    d=[list(entries[:2]),list(entries[2:])]
    for s,ss,t,ts in itertools.product(perms,signs,perms,signs):
        pred=all(d[t[r]][s[c]]==ss[c]*ts[r]*d[r][c] for r in range(2) for c in range(2))
        ps=[[ss[c] if r==s[c] else 0 for c in range(2)] for r in range(2)]
        pt=[[ts[c] if r==t[c] else 0 for c in range(2)] for r in range(2)]
        assert pred==(mul(pt,d)==mul(d,ps));symmetry+=1
r={'rule':'finite_graph_certificate_and_symmetry_controls','status':'exhaustive_declared_small_carriers_confirmed','runtime':sys.version,'phase_support_assignments_n_le_4_moduli_2_3':phasecases,'loop_graph_colorings_n_le_4':colorcases,'f2_patterns_n_le_4':f2cases,'signed_intertwining_2x2_cases':symmetry,'symmetry_self_loop_incidence':-1,'correct_loop_incidence':0,'limits':['Independent Python reconstructions compared with brute-force potentials/colorings and direct matrix products.','No Rust, external GF2 backend or native tests executed. Graph conventions and limits remain those of each owner.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))

import sys,json,itertools,functools
sys.dont_write_bytecode=True
from pathlib import Path
def add(a,b,s=1):
    out=dict(a)
    for c,v in b.items():
        out[c]=out.get(c,0)+s*v
        if out[c]==0:del out[c]
    return out
@functools.lru_cache(None)
def boundary(c):
    out={};prefix=0
    for i,block in enumerate(c):
        for mask in range(1,(1<<len(block))-1):
            left=tuple(x for j,x in enumerate(block) if mask>>j&1);right=tuple(x for j,x in enumerate(block) if not mask>>j&1)
            parity=(prefix+len(left)+sum(x>y for x in left for y in right))%2
            out[c[:i]+(left,right)+c[i+1:]]=-1 if parity else 1
        prefix+=len(block)-1
    return out
def linear(chain,op):
    out={}
    for c,v in chain.items():out=add(out,op(c),v)
    return out
def cells(n):
    for k in range(1,n+1):
        for labels in itertools.product(range(k),repeat=n):
            if set(labels)==set(range(k)):yield tuple(tuple(i for i,x in enumerate(labels) if x==j) for j in range(k))
def posets(n):
    pairs=list(itertools.combinations(range(n),2))
    for choices in itertools.product(range(3),repeat=len(pairs)):
        r={(a,b) if v==1 else (b,a) for (a,b),v in zip(pairs,choices) if v}
        if all((a,d) in r for a,b in r for c,d in r if b==c):yield r
poset_count=cell_count=inequal=0;full_cells=0
for n in range(1,5):
    allcells=list(cells(n));full_cells+=len(allcells)
    for c in allcells:assert linear(boundary(c),boundary)=={}
    for rel in posets(n):
        poset_count+=1;ref=[]
        while len(ref)<n:ref.append(next(x for x in range(n) if x not in ref and all(a in ref for a,b in rel if b==x)))
        rank={v:i for i,v in enumerate(ref)};root=tuple((v,) for v in ref)
        def contains(c):
            pos={v:i for i,b in enumerate(c) for v in b}
            return all(pos[a]<pos[b] for a,b in rel)
        def vertex(c):return tuple(v for block in c for v in sorted(block,key=lambda x:-rank[x]))
        def irank(c):
            v=vertex(c);return sum(rank[v[i]]>rank[v[j]] for i in range(n) for j in range(i+1,n))
        def matching(c):
            v=vertex(c);descent=next((i for i in range(n-1) if rank[v[i]]>rank[v[i+1]]),None)
            if descent is None:return {}
            end=0
            for i,b in enumerate(c):
                end+=len(b)
                if descent+1<end:return {}
                if descent+1==end:
                    upper=c[:i]+(tuple(sorted(b+c[i+1])),)+c[i+2:]
                    assert contains(upper)
                    return {upper:boundary(upper)[c]}
            raise AssertionError('matching')
        @functools.lru_cache(None)
        def h(c):
            if c==root:return {}
            v=matching(c);reduced=add({c:1},linear(v,boundary),-1)
            reduced=add(reduced,linear(boundary(c),matching),-1)
            assert all(irank(x)<irank(c) for x in reduced)
            return add(v,linear(reduced,h))
        def sweep(c):
            remaining=list(c);fixed=[];out={}
            for dist in ref:
                p=next(i for i,b in enumerate(remaining) if dist in b)
                if len(remaining[p])!=1:break
                prefix=0
                for crossed,block in enumerate(remaining[:p]):
                    neg=(prefix+len(block)+sum(v>dist for v in block))%2
                    output=tuple((v,) for v in fixed)+tuple(tuple(sorted(b+(dist,))) if i==crossed else b for i,b in enumerate(remaining) if i!=p)
                    assert output not in out and contains(output)
                    out[output]=-1 if neg else 1;prefix+=len(block)-1
                remaining.pop(p);fixed.append(dist)
            return out
        for c in allcells:
            if not contains(c):continue
            expected={c:1}
            if len(c)==n:expected=add(expected,{root:1},-1)
            for op in (h,sweep):assert add(linear(op(c),boundary),linear(boundary(c),op))==expected
            if h(c)!=sweep(c):inequal+=1
            cell_count+=1
r={'rule':'permutohedral_boundary_and_two_contractions','status':'all_posets_through_four_labels_and_admitted_cells_confirmed','runtime':sys.version,'nonempty_labelled_posets':poset_count,'ordered_partitions_for_d_squared':full_cells,'admitted_order_cell_pairs':cell_count,'pairs_where_two_homotopies_differ':inequal,'limits':['Independent Python sparse integer reconstruction of formulas and identities; no Rust source execution.','Small complete carriers establish finite controls, not an all-size proof or implementation resource-ceiling verification.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))

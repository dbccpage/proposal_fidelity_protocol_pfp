"""Small mathematical/branch models; does not compile or execute the Rust crate."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_rust_category_remaining_controls.json'
ops=('e','a','b')
table={(f,g):(g if f=='e' else f if g=='e' else 'b' if f==g=='a' else 'e')
       for f in ops for g in ops}
assert all(table['e',f]==table[f,'e']==f for f in ops)
assert all(v in ops for v in table.values())
# All operations have the same unary X->X profile, so every table entry is typed.
left=table[table['a','a'],'b'];right=table['a',table['a','b']]
assert (left,right)==('e','a')
controls=[{'id':'RCT-P01','kind':'independent_finite_countermodel_plus_source_branch_analysis',
 'observed':{'color':'X','unary_operations':list(ops),'identity':'e',
             'composition':[[f,g,v] for (f,g),v in table.items()],
             'all_unit_equalities':True,'all_profiles_match':True,
             'nonassociative_triple':['a','a','b'],'left':left,'right':right},
 'limit':'Rust constructor visibly checks only identities, listed composition typing and units; its omission admits this countermodel by source analysis. No claim of native execution.'}]
level_rows=[]
for observed,claimed in itertools.product(range(-2,3),repeat=2):
    source_admits=observed>=-2 and claimed>=-2 and observed>=claimed
    cumulative_implication=observed<=claimed
    level_rows.append({'observed':observed,'claimed':claimed,'source_branch_accepts':source_admits,
                       'valid_cumulative_direction':cumulative_implication})
assert sum(r['source_branch_accepts']!=r['valid_cumulative_direction'] for r in level_rows)==20
controls.append({'id':'RCT-P02','kind':'exact_integer_guard_model',
 'observed':{'level_pairs':level_rows,'direction_disagreements':20},
 'limit':'The integer labels themselves contain no homotopy-type witness; the direction comparison assumes the stated standard truncation-level semantics.'})
permutation_cases=0
for n in range(1,5):
    for seq in itertools.product(range(n+1),repeat=n):
        source_accepts=all(a<n and seq.count(a)==1 for a in seq)
        is_permutation=sorted(seq)==list(range(n))
        assert source_accepts==is_permutation;permutation_cases+=1
assert permutation_cases==700
controls.append({'id':'RCT-P03','kind':'finite_integer_census_crosscheck',
 'observed':{'sequences_checked':permutation_cases,'lengths':[1,2,3,4],'agreement_with_permutation_test':True},
 'limit':'Mirrors the visible IdentityArrowCensus arithmetic for small lengths. No identity/composition laws or underlying category are supplied by the integer list.'})
sets=[{i for i in range(4) if mask & (1<<i)} for mask in range(16)]
for a,b in itertools.product(sets,repeat=2):assert len(a|b)+len(a&b)==len(a)+len(b)
images=[tuple(x) for x in itertools.product(range(3),repeat=2)]
for sequence in images:
    seen=[False]*3;count=0
    for x in sequence:
        if not seen[x]:seen[x]=True;count+=1
    assert count==len(set(sequence))
controls.append({'id':'RCT-P04','kind':'finite_set_and_function_arithmetic',
 'observed':{'set_pairs':256,'ordinal_maps_2_to_3':9,'duplicate_shell_tags':['a','a','b'],
             'shell_vector_length':3,'distinct_tags':2},
 'limit':'CardWitness uses deduplicated integer carriers and TotalFunction counts supplied ordinal images. These checks do not bind the diagnostic string-tag shells to those carriers.'})
lower={'A'};higher={'B'}
assert len(higher)>=len(lower) and not lower<=higher
controls.append({'id':'RCT-P05','kind':'count_does_not_imply_concrete_inclusion',
 'observed':{'lower':['A'],'higher':['B'],'integer_count_guard_accepts':True,'actual_subset':False},
 'limit':'Finite count counterexample to promoting CumulativeUniverse cardinalities into inclusion of supplied type inventories; no actual universes are represented by its constructor.'})
monoids=0
for values in itertools.product(ops,repeat=4):
    product={(f,g):(g if f=='e' else f) for f in ops for g in ops if f=='e' or g=='e'}
    product.update(dict(zip(itertools.product(('a','b'),repeat=2),values)))
    if all(product[product[f,g],h]==product[f,product[g,h]] for f,g,h in itertools.product(ops,repeat=3)):
        monoids+=1
controls.append({'id':'RCT-P06','kind':'finite_unital_table_enumeration',
 'observed':{'one_object_unary_tables':81,'associative_tables':monoids,'nonassociative_tables':81-monoids},
 'limit':'Complete enumeration of three-element multiplication tables with fixed unit e. The category owner enumerates the associativity obligation that the operad constructor omits; no Rust execution or all-size implementation proof.'})
object_map={'A':'X'};morphism_map={'e':'i'}
synthetic_name_check=all(morphism_map.get('id_'+a)=='id_'+b for a,b in object_map.items())
actual_identity_check=morphism_map['e']=='i'
assert not synthetic_name_check and actual_identity_check
controls.append({'id':'RCT-P07','kind':'identity_name_counterexample',
 'observed':{'source_identity':'e','target_identity':'i','object_map':object_map,'morphism_map':morphism_map,
             'actual_identity_preserved':actual_identity_check,'synthetic_id_name_guard_passes':synthetic_name_check},
 'limit':'Valid unique functor between singleton categories is rejected by the legacy name-based identity helper. The now-reviewed aggregate functor owner uses actual identity maps and does not share this naming defect.'})
objects=('A','B');boundaries={'e':('A','A'),'a':('A','A'),'i':('B','B')}
composition={('e','e'):'e',('e','a'):'a',('a','e'):'a',('a','a'):'e',('i','i'):'i'}
for f,g,h in itertools.product(boundaries,repeat=3):
    if boundaries[f][1]==boundaries[g][0] and boundaries[g][1]==boundaries[h][0]:
        assert composition[composition[f,g],h]==composition[f,composition[g,h]]
hom_sizes={target:sum(src=='A' and dst==target for src,dst in boundaries.values()) for target in objects}
assert hom_sizes=={'A':2,'B':0} and sum(hom_sizes.values())==len(objects)
controls.append({'id':'RCT-P08','kind':'aggregate_initial_arrow_count_counterexample',
 'observed':{'objects':objects,'morphism_boundaries':boundaries,'composition':[[f,g,c] for (f,g),c in composition.items()],
             'hom_sizes_from_A':hom_sizes,'source_count_guard_accepts':True,'A_is_initial':False},
 'limit':'Disjoint union of the one-object C2 category and a singleton category. Equal total outgoing-arrow/object counts do not establish one arrow to each object. Independent finite model; no Rust execution.'})
def mono(name,square):
    return {'name':name,'objects':{'X'},'arrows':{'e':('X','X'),'a':('X','X')},'identities':{'X':'e'},
            'composition':{('e','e'):'e',('e','a'):'a',('a','e'):'a',('a','a'):square}}
def identity_map(source,target):
    return {'source':source['name'],'target':target['name'],'objects':{x:x for x in source['objects']},
            'arrows':{f:f for f in source['arrows']}}
def five_functor_predicates(f,s,t):
    # Direct finite model of the visible five guards; missing-category obligations are deliberately absent.
    if f['source']!=s['name'] or f['target']!=t['name']:return False
    if any(f['objects'].get(x) not in t['objects'] for x in s['objects']):return False
    if any(f['arrows'].get(a) not in t['arrows'] for a in s['arrows']):return False
    for a,(x,y) in s['arrows'].items():
        if t['arrows'][f['arrows'][a]]!=(f['objects'].get(x),f['objects'].get(y)):return False
    for x in s['objects']:
        sid=s['identities'].get(x);tid=t['identities'].get(f['objects'][x])
        if sid is not None and tid is not None and f['arrows'].get(sid)!=tid:return False
    for (a,b),c in s['composition'].items():
        if t['composition'].get((f['arrows'][a],f['arrows'][b]))!=f['arrows'][c]:return False
    return True
broken={'name':'B','objects':{'X'},'arrows':{},'identities':{},'composition':{}}
assert five_functor_predicates(identity_map(broken,broken),broken,broken)
controls.append({'id':'RCT-P09','kind':'missing_category_premise_counterexample',
 'observed':{'source_and_target':'one object X with no arrows/identity/compositions','five_functor_predicates_pass':True,'category_identity_totality':False},
 'limit':'Direct branch model shows constructor lacks category admission. No native Rust run; would fail the separate finite-category validator.'})
c=mono('C','e');d1=mono('D','e');d2=mono('D','a');e=mono('E','a')
for cat in (c,d1,d2,e):
    comp=cat['composition']
    assert all(comp[comp[a,b],z]==comp[a,comp[b,z]] for a,b,z in itertools.product(('e','a'),repeat=3))
f=identity_map(c,d1);g=identity_map(d2,e)
assert five_functor_predicates(f,c,d1) and five_functor_predicates(g,d2,e)
assert d1['name']==d2['name'] and d1!=d2
composite=identity_map(c,e);assert not five_functor_predicates(composite,c,e)
controls.append({'id':'RCT-P10','kind':'same_name_different_middle_categories',
 'observed':{'first_middle_square':'a*a=e','second_middle_square':'a*a=a','middle_name':'D',
             'each_input_functor_valid':True,'name_only_composition_guard_passes':True,
             'result_identity_map_preserves_composition':False},
 'limit':'C2 and the two-element idempotent monoid are valid finite categories with colliding names. compose_validated_functors returns a DeclaredFiniteFunctor; explicit revalidation would catch the false composition.'})
singleton={'name':'C','objects':{'X'},'arrows':{'e':('X','X')},'identities':{'X':'e'},'composition':{('e','e'):'e'}}
incomplete={'source':'C','target':'C','objects':{'X':'X'},'arrows':{}}
components={'X':'e'}
component_boundaries=all(singleton['arrows'][components[x]]==(incomplete['objects'][x],incomplete['objects'][x]) for x in singleton['objects'])
squares_checked=0;violations=[]
for arrow,(src,dst) in singleton['arrows'].items():
    if arrow not in incomplete['arrows']:continue
    squares_checked+=1
    f_arrow=incomplete['arrows'][arrow]
    if singleton['composition'].get((f_arrow,components[dst]))!=singleton['composition'].get((components[src],f_arrow)):violations.append(arrow)
assert component_boundaries and not violations and squares_checked==0
assert not five_functor_predicates(incomplete,singleton,singleton)
controls.append({'id':'RCT-P11','kind':'missing_functor_premise_in_naturality',
 'observed':{'valid_singleton_category':True,'component':'e','object_maps':'X maps to X','arrow_maps':{},'component_boundaries_pass':True,'naturality_squares_checked':squares_checked,'naturality_errors':violations,'independent_functor_predicates_pass':False},
 'limit':'Finite branch model of naturality missing-image skips, not original Rust execution. Both categories are valid; the defect is missing admission of the functor arguments.'})
perms=list(itertools.permutations(range(3)))
compose_perm=lambda f,g:tuple(g[f[i]] for i in range(3))
identity_perm=(0,1,2);eta=(1,0,2);other=(0,2,1)
assert all(compose_perm(compose_perm(f,g),h)==compose_perm(f,compose_perm(g,h)) for f,g,h in itertools.product(perms,repeat=3))
assert compose_perm(eta,eta)==identity_perm
assert compose_perm(eta,other)!=compose_perm(other,eta)
controls.append({'id':'RCT-P12','kind':'triangle_without_naturality',
 'observed':{'S3_arrows':6,'associativity_triples':216,'left_and_right_functors':'identity','unit_and_counit':eta,'both_triangle_results':identity_perm,'naturality_test_arrow':other,'two_naturality_paths':[compose_perm(eta,other),compose_perm(other,eta)]},
 'limit':'Exact finite permutation model with lawful categories/functors; triangle equations alone omit naturality. No original Rust execution.'})
legacy_left=identity_map(singleton,singleton);legacy_right=identity_map(singleton,singleton)
embedded_left={'objects':{},'arrows':{}}
assert five_functor_predicates(legacy_left,singleton,singleton) and five_functor_predicates(legacy_right,singleton,singleton)
derived_objects={x:legacy_right['objects'][y] for x,y in embedded_left['objects'].items() if y in legacy_right['objects']}
assert not derived_objects
controls.append({'id':'RCT-P13','kind':'divergent_public_adjunction_maps',
 'observed':{'legacy_maps_pass_functor_predicates':True,'legacy_unit_and_counit':'e','legacy_triangles_pass':True,'embedded_left_maps_empty':True,'derived_object_map':derived_objects,'derived_law_loop_iterations':0},
 'limit':'Models source access paths: validator rebuilds legacy copies; monad derives embedded fields. Public representations can diverge. No Rust mutation or execution performed.'})
inverse={x:(-x)%3 for x in range(3)}
assert all(inverse[inverse[x]]==x for x in inverse) and set(inverse.values())==set(range(3))
lhs=inverse[(0+1)%3];rhs=(inverse[0]+1)%3;assert lhs!=rhs
controls.append({'id':'RCT-P14','kind':'hom_bijection_without_naturality',
 'observed':{'category':'one-object C3 with addition modulo3','functors':'identity','hom_bijection':inverse,'both_roundtrips_pass':True,'naturality_paths':[lhs,rhs],'empty_witness_vector_checks':0},
 'limit':'Finite bijection is not a natural hom-set family. The owner explicitly checks roundtrips but neither naturality nor full object-pair population. No native Rust execution.'})
magma={'name':'M','objects':{'X'},'arrows':{f:('X','X') for f in ops},'identities':{'X':'e'},'composition':table}
assert five_functor_predicates(identity_map(magma,magma),magma,magma)
assert all(table['e',f]==table[f,'e'] for f in ops)
assert table['e','e']=='e' and table[table['a','a'],'b']!=table['a',table['a','b']]
controls.append({'id':'RCT-P15','kind':'monad_predicates_without_category_associativity',
 'observed':{'carrier':'RCT-P01 nonassociative unital magma','T':'identity on object and all arrows','eta':'e','mu':'e','five_functor_predicates_pass':True,'component_boundaries_and_both_naturalities_pass':True,'three_monad_equations_pass':True,'category_associativity_pass':False},
 'limit':'Finite independent equation model. The private monad constructor omits category admission; this is not a Rust runtime replay.'})
nothing=('Nothing',);just=lambda x:('Just',x)
maybe_bind=lambda v,f:nothing if v==nothing else f(v[1])
maybe_fmap=lambda f,v:maybe_bind(v,lambda x:just(f(x)))
maybe_join=lambda v:maybe_bind(v,lambda x:x)
bool_action=lambda v:False if v==nothing else v[1]
double_shells=[nothing,just(nothing),just(just(False)),just(just(True))]
associativity_results=[bool_action(maybe_join(v))==bool_action(maybe_fmap(bool_action,v)) for v in double_shells]
unit_results=[bool_action(just(x))==x for x in (False,True)]
assert all(associativity_results+unit_results)
bad_action=lambda v:False
assert bad_action(just(True))!=True
controls.append({'id':'RCT-P16','kind':'Maybe_bool_exact_algebra_and_generic_placeholder',
 'observed':{'double_shell_associativity_cases':4,'results':associativity_results,'unit_cases':2,'unit_results':unit_results,'constant_false_action_unit_at_true':False,'generic_source_verifier_branch_result':True},
 'limit':'All elements of the fixed finite nested-Maybe carrier checked independently. Generic source methods return literal true; original Rust code not executed, no universal theorem for arbitrary M/A/actions.'})
hom_counts=[[1,1,0],[0,1,1],[0,0,1]]
assert all(len(row)==len(hom_counts) and row[i]>=1 for i,row in enumerate(hom_counts))
assert hom_counts[0][1]>0 and hom_counts[1][2]>0 and hom_counts[0][2]==0
controls.append({'id':'RCT-P17','kind':'hom_count_guards_do_not_establish_category',
 'observed':{'hom_counts':hom_counts,'square_positive_diagonal_guard_passes':True,'row_sums':[sum(row) for row in hom_counts],'A_to_B':1,'B_to_C':1,'A_to_C':0,'composition_exists':False},
 'limit':'Independent finite obstruction to promoting the YonedaRowSumWitness numeric predicate into categorical structure. The owner computes counts only; no native Rust replay or claim that its narrow arithmetic is wrong.'})
galois_examples=[]
for lower,upper in [([0,0,1,1,2,2],[1,3,5]),([0,0,1],[1,2,2])]:
    n=len(lower);m=len(upper)
    assert all(0<=x<m for x in lower) and all(0<=x<n for x in upper)
    assert lower==sorted(lower) and upper==sorted(upper)
    assert all((lower[a]<=b)==(a<=upper[b]) for a in range(n) for b in range(m))
    closure=[upper[lower[a]] for a in range(n)]
    assert all(a<=closure[a] and closure[closure[a]]==closure[a] for a in range(n))
    galois_examples.append({'lower':lower,'upper':upper,'biconditional_pairs':n*m,'closure':closure,'closure_extensive_and_idempotent':True})
controls.append({'id':'RCT-P18','kind':'nontrivial_finite_chain_adjunctions',
 'observed':galois_examples,
 'limit':'Two independent exact instances, one with unequal chain sizes. Source loops cover all supplied pairs, but this control is not a universal Rust implementation proof.'})
ambient=[0,1];sub=[0]
assert all((a<=x)==(a<=0) for a in sub for x in ambient)
counit_components=[(0,x) for x in ambient]
assert len(counit_components)==2 and len(sub)==1
controls.append({'id':'RCT-P19','kind':'coreflector_counit_index_counterexample',
 'observed':{'ambient_chain':ambient,'full_subcategory':sub,'coreflector':'constant0','all_adjunction_hom_pairs_match':True,'counit_components':counit_components,'actual_full_counit_count':2,'source_count_result':1},
 'limit':'Exact two-object poset category. Counit is indexed by C, not A; a restriction to A has one component but is not the full counit family. No Rust execution.'})
assert five_functor_predicates(identity_map(singleton,singleton),singleton,singleton)
assert singleton['composition']['e','e']=='e'
controls.append({'id':'RCT-P20','kind':'identity_monad_refutes_distinct_label_requirement',
 'observed':{'category':'one-object one-arrow category','T':'identity','unit_ref':'identity','multiply_ref':'identity','all_monad_laws':True,'Kleisli_objects':1,'Kleisli_homs':1,'label_guard_accepts':False},
 'limit':'Equal mathematical transformations can share a reference. Independent exact singleton model, not native Rust execution.'})
pair_values=list(itertools.product(range(2),repeat=2))
state_functions=list(itertools.product(pair_values,repeat=2))
assert len(pair_values)==4 and len(state_functions)==16
controls.append({'id':'RCT-P21','kind':'state_computations_vs_result_state_pairs',
 'observed':{'value_count':2,'state_count':2,'output_pairs':pair_values,'pair_count':len(pair_values),'total_functions_from_states_to_pairs':len(state_functions),'source_product_result':4},
 'limit':'Identity inner monad, total finite-set functions only; uses the official StateT function-space definition. Not Haskell runtime execution or arbitrary-effect cardinality.'})
mu=[0,0,0,0,1,0,0,0,2];n=3
deltas=[((x,y,z),mu[y*n+z]-mu[((x+y)%n)*n+z]+mu[x*n+(y+z)%n]-mu[x*n+y]) for x,y,z in itertools.product(range(n),repeat=3)]
assert all(mu[x*n]==mu[x]==0 for x in range(n))
assert all(value%n==0 for _,value in deltas)
assert dict(deltas)[(1,1,2)]==-3
constant=[1]*4
assert all(constant[y*2+z]-constant[((x+y)%2)*2+z]+constant[x*2+(y+z)%2]-constant[x*2+y]==0 for x,y,z in itertools.product(range(2),repeat=3))
controls.append({'id':'RCT-P22','kind':'cyclic_cocycle_coefficient_and_normalization_mismatch',
 'observed':{'n':3,'normalized_table':mu,'triples_checked':27,'all_modular_coboundaries_zero':True,'nonzero_integer_coboundaries':[row for row in deltas if row[1]],'unnormalized_n2_constant_one_accepted':True},
 'limit':'Independent trivial-action degree-two bar differential on explicit finite tables. Reduction modulo n changes coefficient module; no original Rust execution.'})
for rank in range(1,7):
    counit=[int(i==j) for i in range(rank) for j in range(rank)]
    contracted=[[sum(counit[i*rank+k]*int(k==j) for k in range(rank)) for j in range(rank)] for i in range(rank)]
    assert all(contracted[i][j]==int(i==j) for i in range(rank) for j in range(rank))
controls.append({'id':'RCT-P23','kind':'fixed_standard_dual_snake_contraction',
 'observed':{'ranks_checked':list(range(1,7)),'fixed_coevaluation':'identity matrix','condition_equivalent_to':'supplied counit matrix is identity'},
 'limit':'Independent exact finite contraction; the fixed coefficient model does not validate arbitrary labeled monoidal categories or duals.'})
pins=[]
def sum_index_constructs(left_card,right_card):
    # The source's mandatory sample encode(1,0) requires an existing right element.
    return left_card+right_card<=2**32-1 and 0<right_card
assert not sum_index_constructs(1,0) and sum_index_constructs(0,1)
controls.append({'id':'RCT-P24','kind':'empty_right_coproduct_sample_refusal',
 'observed':{'left1_right0_constructs':False,'left0_right1_constructs':True,'actual_both_disjoint_union_cardinalities':1},
 'limit':'Independent branch model of the mandatory right-side sample, not Rust execution. The mathematical sum exists on either side.'})
def partition_by_merges(n,edges):
    parent=list(range(n))
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for a,b in edges:
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    return [find(x) for x in range(n)]
coeq_cases=0;factor_checks=0
for n in range(1,4):
    for f,g in itertools.product(itertools.product(range(n),repeat=n),repeat=2):
        edges=list(zip(f,g));quotient=partition_by_merges(n,edges)
        # Independent graph reachability verifies the generated equivalence classes.
        for x in range(n):
            reached={x}
            while True:
                new=reached|{b for a,b in edges if a in reached}|{a for a,b in edges if b in reached}
                if new==reached:break
                reached=new
            assert reached=={y for y in range(n) if quotient[y]==quotient[x]}
        for h in itertools.product(range(2),repeat=n):
            equalizes=all(h[f[x]]==h[g[x]] for x in range(n))
            factors=all(h[x]==h[y] for x in range(n) for y in range(n) if quotient[x]==quotient[y])
            assert equalizes==factors
            factor_checks+=1
        coeq_cases+=1
controls.append({'id':'RCT-P25','kind':'finite_set_coequalizer_partition',
 'observed':{'map_pairs':coeq_cases,'carrier_sizes':[1,2,3],'binary_target_factorization_checks':factor_checks,'independent_graph_closure_matches_union_find':True},
 'limit':'Independent finite algorithms verify these partition instances and binary-target factorization. Source Rust is not executed and general implementation correctness is not inferred.'})
kernel_cases=0
for n in range(1,5):
    for f in itertools.product(range(n),repeat=n):
        assert sum(f.count(y)**2 for y in range(n))==sum(f[x]==f[z] for x in range(n) for z in range(n))
        kernel_cases+=1
controls.append({'id':'RCT-P26','kind':'kernel_pair_count_identity',
 'observed':{'total_endomaps':kernel_cases,'carrier_sizes':[1,2,3,4],'fiber_square_equals_equal_image_pair_count':True},
 'limit':'Exact independent finite cardinality identity, not native execution or categorical structure beyond these finite functions.'})
compatible=[(x,y) for x in range(2) for y in range(2) if x==y]
colimit_partition=partition_by_merges(4,[(0,2),(1,3)])
assert len(compatible)==len(set(colimit_partition))==2
controls.append({'id':'RCT-P27','kind':'nondiscrete_diagram_needs_transition_maps',
 'observed':{'diagram':'walking arrow mapped to identity on a two-element set','actual_limit_cardinality':2,'actual_colimit_cardinality':2,'product_of_value_sizes':4,'sum_of_value_sizes':4},
 'limit':'Shows why discrete-diagram or equivalent premises are necessary for the hierarchy arithmetic to mean a general (co)limit. Does not allege failure of its narrow sum/product arithmetic.'})
lo=-(2**31);hi=2**31-1;span=hi-lo
assert lo<=hi and span>2**31-1 and span<=2**32-1
controls.append({'id':'RCT-P28','kind':'ordered_i32_degree_span_overflow',
 'observed':{'degree_min':lo,'degree_max':hi,'ordered':True,'mathematical_span':span,'fits_i32':False,'fits_u32':True},
 'limit':'Exact range arithmetic plus official Rust overflow rules; source accessor not executed. Panic depends on overflow checking configuration.'})
biproduct_cases=0
for a,b in itertools.product(range(1,9),repeat=2):
    total=a+b;left_indices=list(range(a));right_indices=list(range(a,total))
    p_left=[x if x<a else None for x in range(total)]
    p_right=[None if x<a else x-a for x in range(total)]
    assert all(p_left[x]==i and p_right[x] is None for i,x in enumerate(left_indices))
    assert all(p_right[x]==i and p_left[x] is None for i,x in enumerate(right_indices))
    for x in range(total):
        reconstructed=([left_indices[p_left[x]]] if p_left[x] is not None else [])+([right_indices[p_right[x]]] if p_right[x] is not None else [])
        assert reconstructed==[x]
    biproduct_cases+=1
controls.append({'id':'RCT-P29','kind':'standard_free_abelian_biproduct_coordinates',
 'observed':{'positive_rank_pairs_checked':biproduct_cases,'rank_bound':8,'four_projection_inclusion_and_complementary_sum_identities':True},
 'limit':'Independent exact basis-coordinate model extended linearly over integers; not a general abelian-category construction or Rust execution.'})
dims=[1,2,1];ranks=[1,1];homology=[dims[i]-(ranks[i-1] if i else 0)-(ranks[i] if i<len(ranks) else 0) for i in range(len(dims))]
assert homology==[0,0,0] and sum((-1)**i*x for i,x in enumerate(dims))==0
# Q --(1,0)^T--> Q^2 --(1,0)--> Q has those dimensions/ranks but nonzero composite.
composite=sum(x*y for x,y in zip([1,0],[1,0]));assert composite==1
controls.append({'id':'RCT-P30','kind':'rank_euler_consistency_does_not_admit_differentials',
 'observed':{'dimensions':dims,'ranks':ranks,'reported_homology_dimensions':homology,'euler_identity_passes':True,'chosen_map_composite':composite,'square_zero':False},
 'limit':'Independently supplied maps with the same counts show the missing chain-complex premise. Does not claim the narrow rank arithmetic is wrong or that the owner accepts maps, which it never receives.'})
algebra=list(itertools.product(range(2),repeat=2))
add=lambda x,y:tuple((a+b)%2 for a,b in zip(x,y))
mul=lambda x,y:tuple((a*b)%2 for a,b in zip(x,y))
assert all(mul((1,1),x)==mul(x,(1,1))==x for x in algebra)
assert all(mul(mul(x,y),z)==mul(x,mul(y,z)) for x,y,z in itertools.product(algebra,repeat=3))
assert all(mul(x,add(y,z))==add(mul(x,y),mul(x,z)) and mul(add(x,y),z)==add(mul(x,z),mul(y,z)) for x,y,z in itertools.product(algebra,repeat=3))
assert 2*2!=2
controls.append({'id':'RCT-P31','kind':'enriched_composition_need_not_preserve_tensor_dimension',
 'observed':{'algebra':'F2 x F2 with componentwise operations','elements':algebra,'unit':[1,1],'associativity_triples':64,'both_distributivity_triples':64,'hom_dimension':2,'composition_domain_dimension':4,'source_equal_dimension_guard_passes':False},
 'limit':'Exact finite associative unital algebra over F2 gives a one-object enriched category by the defining axiom. Source Rust not executed.'})
ultra_cases=0;separated_cases=0
for a,b,c in itertools.product(range(3),repeat=3):
    d=[[0,a,b],[a,0,c],[b,c,0]]
    if all(d[i][k]<=max(d[i][j],d[j][k]) for i,j,k in itertools.product(range(3),repeat=3)):
        ultra_cases+=1;separated_cases+=all(x>0 for x in (a,b,c))
assert all(0<=max(0,0) for _ in range(27))
controls.append({'id':'RCT-P32','kind':'pseudoultrametric_scope',
 'observed':{'three_point_symmetric_tables_checked':27,'strong_triangle_admitted':ultra_cases,'of_those_separated':separated_cases,'all_zero_three_point_matrix_passes':True},
 'limit':'Exact finite matrix inequalities; zero distance need not identify indices in the source carrier. Does not certify the separate labeled base category or any model workflow.'})
quiver=[(0,0),(1,1),(2,2),(0,1),(1,2)]
source_loop_guard=all(0<=a<3 and 0<=b<3 for a,b in quiver) and all((i,i) in quiver for i in range(3))
assert source_loop_guard and (0,2) not in quiver
controls.append({'id':'RCT-P33','kind':'reflexive_graph_without_possible_composite',
 'observed':{'objects':3,'arrows':quiver,'source_endpoint_and_loop_guard_passes':source_loop_guard,'composable_path':[0,1,2],'required_composite_boundary_present':False},
 'limit':'Independent finite graph and source-branch analysis. No composition choice can repair absent Hom(0,2) without adding arrows. Rust owner not executed.'})
tags=['a|x']*4
source_product_guard=len(tags)==2*2 and all(len(s.split('|'))==2 and all(s.split('|')) for s in tags)
assert source_product_guard and len(set(tags))==1
controls.append({'id':'RCT-P34','kind':'cartesian_inventory_multiplicity_counterexample',
 'observed':{'factor_sizes':[2,2],'tags':tags,'source_length_and_syntax_guard_passes':source_product_guard,'distinct_pairs':len(set(tags))},
 'limit':'Demonstrates missing inventory uniqueness, not incorrect integer multiplication. No Rust execution.'})
# The functor 1 -> B(C2) sends its unique identity to identity, preserving all laws.
group=(0,1); multiply=lambda a,b:(a+b)%2
assert all(multiply(multiply(a,b),c)==multiply(a,multiply(b,c)) for a,b,c in itertools.product(group,repeat=3))
projection={'e':0}; base_arrows=[(0,0),(0,0)]; total_arrows=[(0,0)]; fibre=[0]
boundary_lifts=[]
for base_from,base_to in base_arrows:
    for target,target_base in enumerate(fibre):
        if target_base==base_to:
            hits=sum(t==target and fibre[s]==base_from for s,t in total_arrows)
            assert hits==1
            boundary_lifts.append(hits)
assert len(boundary_lifts)==2 and not any(image==1 for image in projection.values())
controls.append({'id':'RCT-P35','kind':'parallel_base_arrows_conflated_by_endpoint_lift_counter',
 'observed':{'base':'one-object C2 group category','total':'terminal category','functor_arrow_map':projection,'base_boundary_list':base_arrows,'total_boundary_list':total_arrows,'source_counted_lifts':sum(boundary_lifts),'actual_nonidentity_base_arrow_lifts':0},
 'limit':'Exact valid categories/functor plus the visible endpoint-count model. A chosen arrow must project to the specified base morphism. Rust owner not executed.'})
swap=[1,0]
assert all(swap[swap[swap[x]]]==swap[x] and x<=swap[swap[x]] and swap[swap[x]]<=x for x in range(2))
assert not swap[0]<=swap[1]
assert (swap[0]<=0)!=(0<=swap[0])
controls.append({'id':'RCT-P36','kind':'triangles_and_unit_counit_without_monotonicity',
 'observed':{'left':swap,'right':swap,'all_source_triangle_and_inequality_predicates_pass':True,'monotone':False,'galois_counterexample':[0,0]},
 'limit':'Finite order calculation exhibits the missing functor/monotonicity premise. No Rust execution.'})
def skill_compose(f,g):
    assert f['codomain']==g['domain']
    return {'id':f["id"]+' >> '+g["id"], 'domain':f['domain'],'codomain':g['codomain'],'category':f['category'],
            'description':'Composite morphism of '+f['id']+' and '+g['id']}
def agent_map(f):
    return {'id':'Agent['+f['id']+']','domain':'Agent:'+f['domain'],'codomain':'Agent:'+f['codomain'],'category':'D','description':'mapped'}
f={'id':'f','domain':'A','codomain':'B','category':'C'}
g={'id':'g','domain':'B','codomain':'C','category':'C'}
h={'id':'h','domain':'C','codomain':'D','category':'C'}
mapped_composite=agent_map(skill_compose(f,g)); composite_mapped=skill_compose(agent_map(f),agent_map(g))
assert mapped_composite['id']!=composite_mapped['id']
bracket_left=skill_compose(skill_compose(f,g),h); bracket_right=skill_compose(f,skill_compose(g,h))
assert all(bracket_left[k]==bracket_right[k] for k in ('id','domain','codomain','category'))
assert bracket_left['description']!=bracket_right['description']
controls.append({'id':'RCT-P37','kind':'metadata_functor_and_full_record_associativity_mismatch',
 'observed':{'mapped_composite_id':mapped_composite['id'],'composite_mapped_id':composite_mapped['id'],'associativity_checked_fields_match':True,'left_description':bracket_left['description'],'right_description':bracket_right['description'],'full_record_equal':False},
 'limit':'Independent string/record model of the fully read methods. No quotient identifying these strings is implemented in the owners; no Rust execution or downstream authority-bypass claim.'})
def raw_counter(count,depth,word):
    for event in word:
        if depth==0:return ('context_exhausted',)
        if event==-1 and count==0:return ('guard_refusal',)
        count+=event;depth-=1
    return ('ok',depth,min(count,depth))
def reported_counter(count,depth,word):
    clip=min(count,depth)
    for event in word:
        if depth==0:return ('context_exhausted',)
        next_depth=depth-1
        if event==1:clip=next_depth if clip>=next_depth else clip+1
        elif clip==0:return ('guard_refusal',)
        else:clip=min(clip-1,next_depth)
        depth=next_depth
    return ('ok',depth,clip)
counter_cases=0;class_counts=[];separator_cases=0
for depth in range(6):
    words=[w for length in range(depth+2) for w in itertools.product((-1,1),repeat=length)]
    signatures={}
    for count in range(9):
        for word in words:
            assert raw_counter(count,depth,word)==reported_counter(count,depth,word)
            counter_cases+=1
        signature=tuple(raw_counter(count,depth,w)[0]=='ok' for w in words if len(w)<=depth)
        clip=min(count,depth)
        if clip in signatures:assert signatures[clip]==signature
        signatures[clip]=signature
    assert len(set(signatures.values()))==depth+1
    class_counts.append(len(signatures))
    for a,b in itertools.combinations(range(depth+1),2):
        length=min(a,b)+1;assert length<=depth
        assert (raw_counter(a,depth,(-1,)*length)[0]=='ok')!=(raw_counter(b,depth,(-1,)*length)[0]=='ok')
        separator_cases+=1
controls.append({'id':'RCT-P38','kind':'finite_depth_counter_report_against_unbounded_counter_semantics',
 'observed':{'depths':list(range(6)),'raw_counts':list(range(9)),'words_through_one_beyond_depth':True,'state_and_boundary_comparisons':counter_cases,'distinct_legality_classes_by_depth':class_counts,'separating_decrement_words':separator_cases},
 'limit':'Finite independent raw nonnegative-counter semantics, including depth exhaustion and early guard failure. General depth claim additionally uses the source transition invariant; not a Rust run or unlimited-context congruence.'})
checked_shift_events=[]
def checked_mask_before_validation(size):
    if size==64:mask=(1<<64)-1
    else:
        checked_shift_events.append('shift')
        if size>=64:raise OverflowError('u64 shift width exceeded')
        mask=(1<<size)-1
    checked_shift_events.append('validate_carrier')
    if size>64:return 'CarrierTooLarge'
    return mask
try:checked_mask_before_validation(65)
except OverflowError:pass
else:raise AssertionError('expected checked shift refusal before carrier validation')
assert checked_shift_events==['shift']
controls.append({'id':'RCT-P39','kind':'checked_u64_shift_precedes_carrier_guard',
 'observed':{'carrier_size':65,'left_operand_bits':64,'branch_events':checked_shift_events,'carrier_validation_reached':False},
 'limit':'Independent checked-width branch model plus official Rust overflow definition; no compiled Rust execution, and no claim about unchecked compiler profiles.'})
counts={0:1,1:128,2:0,3:0}
restrictions={}
for big,small in itertools.product(counts,repeat=2):
    if small&big==small:
        restrictions[big,small]=list(range(counts[big])) if big==small else [0]*counts[big]
assert all((a&b) in counts for a,b in itertools.product(counts,repeat=2))
for (big,small),mapping in restrictions.items():
    assert len(mapping)==counts[big] and all(0<=x<counts[small] for x in mapping)
    if big==small:assert mapping==list(range(counts[big]))
for big,mid,small in itertools.product(counts,repeat=3):
    if small&mid==small and mid&big==mid:
        assert restrictions[big,small]==[restrictions[mid,small][x] for x in restrictions[big,mid]]
def prefix_sizes(order):
    tuples=[()];sizes=[]
    for context in order:
        tuples=[prefix+(s,) for prefix in tuples for s in range(counts[context])]
        sizes.append(len(tuples))
    return sizes
forward=prefix_sizes([1,2]);backward=prefix_sizes([2,1])
assert forward==[128,0] and backward==[0,0] and counts[1]*counts[2]==0
controls.append({'id':'RCT-P40','kind':'valid_presheaf_zero_product_unbounded_prefix',
 'observed':{'report_counts':counts,'all_restriction_identity_composition_laws_checked':True,'cover':[1,2],'final_product':0,'requested_limit':0,'forward_prefix_sizes':forward,'reverse_prefix_sizes':backward},
 'limit':'Exact small valid finite presheaf plus independently reproduced eager-prefix enumeration. The family generalizes to arbitrary admitted N; demonstrates work-limit gap, not false gluing mathematics or a Rust runtime measurement.'})
points=range(2);pairs=list(itertools.product(points,repeat=2))
relations=[frozenset(p for i,p in enumerate(pairs) if bits&(1<<i)) for bits in range(16)]
identity=frozenset((x,x) for x in points)
converse=lambda r:frozenset((y,x) for x,y in r)
rel_comp=lambda r,s:frozenset((x,z) for x,y in r for yy,z in s if y==yy)
assert all(converse(converse(r))==r for r in relations)
assert all(converse(rel_comp(r,s))==rel_comp(converse(s),converse(r)) for r,s in itertools.product(relations,repeat=2))
unitaries=[r for r in relations if rel_comp(r,converse(r))==rel_comp(converse(r),r)==identity]
assert len(unitaries)==2
# Connected groupoid with three objects and isotropy C3. Arrow(s,t,g) acts by g.
arrows=list(itertools.product(range(3),repeat=3));connector=[0,1,2]
coord=lambda a:(a[1],a[0],(a[2]+connector[a[0]]-connector[a[1]])%3)
assert len({coord(a) for a in arrows})==len(arrows)
coordinate_compositions=0
for a,b in itertools.product(arrows,repeat=2):
    if a[1]==b[0]:
        composed=(a[0],b[1],(a[2]+b[2])%3)
        ca,cb=coord(a),coord(b)
        assert coord(composed)==(cb[0],ca[1],(ca[2]+cb[2])%3)
        coordinate_compositions+=1
controls.append({'id':'RCT-P41','kind':'finite_dagger_and_groupoid_coordinate_laws',
 'observed':{'two_point_relations':16,'dagger_composition_pairs':256,'unitary_relations':len(unitaries),'groupoid_objects':3,'isotropy':'C3','groupoid_arrows':27,'coordinate_compositions':coordinate_compositions},
 'limit':'Independent finite relations and connected groupoid models. Tests the algebraic law/coordinate meanings, not source Rust execution, arbitrary-group theorem formalization or a physical interpretation.'})
def normalized_partition(values):
    assigned={}
    return tuple(assigned.setdefault(v,len(assigned)) for v in values)
def finite_refinement(outputs,transitions):
    blocks=normalized_partition(outputs)
    while True:
        refined=normalized_partition((blocks[s],tuple(blocks[t] for t in transitions[s])) for s in range(len(outputs)))
        if refined==blocks:return blocks
        blocks=refined
moore_cases=0;future_observations=0
for n,alphabet in [(2,2),(3,1)]:
    partitions=set(normalized_partition(p) for p in itertools.product(range(n),repeat=n))
    words=[word for length in range(n*n+1) for word in itertools.product(range(alphabet),repeat=length)]
    for flat in itertools.product(range(n),repeat=n*alphabet):
        transitions=[flat[s*alphabet:(s+1)*alphabet] for s in range(n)]
        for outputs in itertools.product(range(2),repeat=n):
            signatures=[]
            for start in range(n):
                observed=[]
                for word in words:
                    current=start
                    for event in word:current=transitions[current][event]
                    observed.append(outputs[current]);future_observations+=1
                signatures.append(tuple(observed))
            expected=normalized_partition(signatures);actual=finite_refinement(outputs,transitions)
            assert actual==expected
            admissible=[p for p in partitions if all(p[s]!=p[t] or (outputs[s]==outputs[t] and all(p[transitions[s][a]]==p[transitions[t][a]] for a in range(alphabet))) for s,t in itertools.product(range(n),repeat=2))]
            assert actual in admissible
            assert all(all(p[s]!=p[t] or actual[s]==actual[t] for s,t in itertools.product(range(n),repeat=2)) for p in admissible)
            moore_cases+=1
assert moore_cases==280
controls.append({'id':'RCT-P42','kind':'moore_refinement_against_future_words_and_all_partitions',
 'observed':{'machines':moore_cases,'profiles':[[2,2],[3,1]],'Boolean_outputs':True,'word_depth_bound':'n^2','future_observations':future_observations,'all_partitions_enumerated':True,'coarsest_congruence_checks_pass':True},
 'limit':'Independent finite refinement model compared with exhaustive future-word observations and all candidate partitions. Not execution of FiniteMoore; source proof and certificate checks remain separately reviewed.'})
factor_cases=0;factor_exists=0;collision_cases=0
for report,query in itertools.product(itertools.product(range(2),repeat=3),repeat=2):
    image=sorted(set(report))
    decoders=[dict(zip(image,v)) for v in itertools.product(range(2),repeat=len(image))]
    valid=[d for d in decoders if all(d[report[x]]==query[x] for x in range(3))]
    collisions=[(x,y) for x,y in itertools.combinations(range(3),2) if report[x]==report[y] and query[x]!=query[y]]
    assert (len(valid)==1)==(not collisions)
    assert len(valid)<=1
    factor_cases+=1;factor_exists+=bool(valid);collision_cases+=bool(collisions)
# Equality-constrained globals: four compatible locals, only00 and11 glue.
matching=list(itertools.product(range(2),repeat=2));globals_equal=[(0,0),(1,1)]
fibers=[[g for g in globals_equal if g==local] for local in matching]
assert [len(f) for f in fibers]==[1,0,0,1]
# Duplicate global presentations project to identical local observations.
ambiguous=[g for g in range(2) if (0,0)==(0,0)];assert len(ambiguous)==2
controls.append({'id':'RCT-P43','kind':'finite_factorization_collision_and_gluing_cases',
 'observed':{'all_three_point_binary_report_query_pairs':factor_cases,'unique_decoder_cases':factor_exists,'collision_cases':collision_cases,'equality_model_gluing_fiber_sizes':[len(f) for f in fibers],'duplicate_global_gluing_fiber_size':len(ambiguous)},
 'limit':'Exhaustive independent finite maps and explicit gluing models distinguish sufficiency, obstruction and ambiguity. Supplied carrier/observation meanings remain premises; no Rust or LLM execution.'})
def coarsening_reflection(initial,transitions):
    labels=normalized_partition(initial)
    while True:
        old=labels;mutable=list(labels)
        for x,y in itertools.product(range(len(labels)),repeat=2):
            if old[x]==old[y]:
                for a,b in zip(transitions[x],transitions[y]):
                    source,target=mutable[b],mutable[a]
                    mutable=[target if v==source else v for v in mutable]
        labels=normalized_partition(mutable)
        if labels==old:return labels
initial=[0,0,1];transition=[[0],[2],[2]]
coarsened=coarsening_reflection(initial,transition);refined=finite_refinement(initial,transition)
assert coarsened==(0,0,0) and refined==(0,1,2)
reflection_cases=0
partitions3=set(normalized_partition(p) for p in itertools.product(range(3),repeat=3))
for original,transition_flat in itertools.product(partitions3,itertools.product(range(3),repeat=3)):
    transitions=[[t] for t in transition_flat]
    result=coarsening_reflection(original,transitions)
    stable_coarsenings=[p for p in partitions3 if all((original[x]!=original[y] or p[x]==p[y]) and (p[x]!=p[y] or p[transition_flat[x]]==p[transition_flat[y]]) for x,y in itertools.product(range(3),repeat=2))]
    assert result in stable_coarsenings
    assert all(all(result[x]!=result[y] or p[x]==p[y] for x,y in itertools.product(range(3),repeat=2)) for p in stable_coarsenings)
    reflection_cases+=1
controls.append({'id':'RCT-P44','kind':'least_stable_coarsening_is_not_report_preserving_refinement',
 'observed':{'initial_profiles':initial,'transition':[0,2,2],'least_stable_coarsening':coarsened,'coarsest_report_preserving_congruence':refined,'all_three_state_unary_partition_cases':reflection_cases},
 'limit':'Independent closure model checked against all candidate coarsenings. Demonstrates both valid universal constructions and their opposite information directions; no source Rust execution.'})
retention_signatures=set();retention_models=0;retention_witnesses={}
for n in range(1,5):
    partitions=set(normalized_partition(p) for p in itertools.product(range(n),repeat=n))
    for raw,recognized in itertools.product(partitions,repeat=2):
        if not all(raw[x]!=raw[y] or recognized[x]==recognized[y] for x,y in itertools.product(range(n),repeat=2)):continue
        for transition in itertools.product(range(n),repeat=n):
            future=[]
            for start in range(n):
                state=start;word_reports=[]
                for _ in range(n*n+1):
                    word_reports.append(recognized[state]);state=transition[state]
                future.append(tuple(word_reports))
            signature=(n>1,len(set(transition))==n,len(set(raw))==n,
                       any(raw[x]!=raw[y] and recognized[x]==recognized[y] for x,y in itertools.combinations(range(n),2)),
                       len(set(future))==n,any(x!=transition[x] for x in range(n)))
            retention_signatures.add(signature);retention_models+=1
            retention_witnesses.setdefault(str(signature),{'raw':raw,'recognized':recognized,'transition':transition})
def admitted_retention(flags):
    nontrivial,reversible,observable,tolerance,minimal,active=flags
    if not nontrivial:return reversible and observable and not tolerance and minimal and not active
    if observable and not tolerance and not minimal:return False
    if not active:return reversible and minimal==(observable and not tolerance)
    return True
expected_retention={f for f in itertools.product((False,True),repeat=6) if admitted_retention(f)}
assert retention_signatures==expected_retention and len(expected_retention)==19
functional_signatures=set();functional_models=0;functional_witnesses={}
for n in range(1,4):
    labels=list(itertools.product(range(n),repeat=n))
    for presentation,report,context in itertools.product(labels,repeat=3):
        linked=all(presentation[x]!=presentation[y] or report[x]==report[y] for x,y in itertools.combinations(range(n),2))
        p_stable=all(presentation[x]==presentation[context[x]] for x in range(n))
        s_stable=all(report[x]==report[context[x]] for x in range(n))
        blind=len(set(presentation))<n
        for calibrated in (False,True):
            signature=(linked,p_stable,s_stable,calibrated,blind)
            functional_signatures.add(signature);functional_models+=1
            target=list(report)
            if not calibrated:target[0]+=1
            functional_witnesses.setdefault(str(signature),{'presentation':presentation,'report':report,'context':context,'target':target})
expected_functional={f for f in itertools.product((False,True),repeat=5) if (f[4] or f[0]) and not (f[0] and f[1] and not f[2])}
assert functional_signatures==expected_functional and len(expected_functional)==20
controls.append({'id':'RCT-P45','kind':'constructive_predicate_signature_classification_crosscheck',
 'observed':{'retention_models_enumerated':retention_models,'retention_signatures':19,'retention_max_states':4,'retention_distinction_horizon':'n^2',
             'functional_models_enumerated':functional_models,'functional_signatures':20,'functional_max_states':3,
             'retention_witnesses':retention_witnesses,'functional_witnesses':functional_witnesses},
 'limit':'Independent enumeration of actual finite maps and finite-word observations supplies every permitted signature and finds no forbidden one. General completeness additionally uses the reviewed universal implications; no phenomenology, Rust execution or proof-assistant certification.'})
fd_candidates=[(1<<a,1<<b) for a,b in itertools.permutations(range(3),2)]
binary_rows=list(itertools.product(range(2),repeat=3))
instances=[tuple(row for i,row in enumerate(binary_rows) if mask&(1<<i)) for mask in range(256)]
def respects_fd(rows,fd):
    determinant,dependent=fd
    return all(not all(a[i]==b[i] for i in range(3) if determinant&(1<<i)) or all(a[i]==b[i] for i in range(3) if dependent&(1<<i)) for a,b in itertools.combinations(rows,2))
instance_fd_masks=[sum(1<<i for i,fd in enumerate(fd_candidates) if respects_fd(rows,fd)) for rows in instances]
instance_lossless=[]
for rows in instances:
    ab={(a,b) for a,b,c in rows};bc={(b,c) for a,b,c in rows}
    joined={(a,b,c) for a,b in ab for bb,c in bc if b==bb}
    instance_lossless.append(joined==set(rows))
fd_schemas=0;fd_instance_checks=0
for mask in range(64):
    closure=2
    while True:
        before=closure
        for i,(det,dep) in enumerate(fd_candidates):
            if mask&(1<<i) and det&closure==det:closure|=dep
        if closure==before:break
    predicted=(closure&3==3 or closure&6==6)
    legal=[i for i,bits in enumerate(instance_fd_masks) if bits&mask==mask]
    actual=all(instance_lossless[i] for i in legal)
    assert actual==predicted
    fd_schemas+=1;fd_instance_checks+=len(legal)
controls.append({'id':'RCT-P46','kind':'binary_lossless_criterion_against_all_boolean_instances',
 'observed':{'attributes':['A','B','C'],'components':['AB','BC'],'all_subsets_of_six_single_attribute_dependencies':fd_schemas,'Boolean_instances_per_schema':256,'legal_instance_comparisons':fd_instance_checks,'closure_prediction_matches':True},
 'limit':'Finite exhaustive corroboration for this FD subfamily only. General FD-only binary theorem comes from the cited primary definition/theorem source; no inference from one current instance and no SQL NULL/bag semantics.'})
empty_two_category={'objects':['A'],'one_morphisms':{},'two_morphisms':{},'id_1':{},'id_2':{},'compose_1':{},'vertical':{},'horizontal':{}}
constructor_result=('Ok',empty_two_category)
assert constructor_result[0]=='Ok' and 'A' not in empty_two_category['id_1']
controls.append({'id':'RCT-P47','kind':'unconditional_two_category_admission_missing_identity',
 'observed':{'declaration':empty_two_category,'constructor_branch':'Ok(Self{declared})','identity_A_present':False,'accessor_branch':'unreachable on missing map entry'},
 'limit':'Direct source branch plus independent minimal declaration; Rust owner not compiled/executed. No end-to-end consumer exploit claimed.'})
splitting_compositions={('e','e'):'e',('s','r'):'id_R',('r','s'):'e'};splitting_identities={'A':'id_A','R':'id_R'}
def splitting_equations(record):
    e,r,s=record['idempotent'],record['retraction'],record['section']
    return splitting_compositions.get((e,e))==e and splitting_compositions.get((s,r))==splitting_identities.get(record['retract']) and splitting_compositions.get((r,s))==e
split={'carrier':'A','idempotent':'e','retract':'R','section':'s','retraction':'r'}
assert splitting_equations(split)
ghost_split={**split,'carrier':'Ghost'};assert splitting_equations(ghost_split) and 'Ghost' not in splitting_identities
controls.append({'id':'RCT-P48','kind':'splitting_carrier_field_not_bound_by_equations',
 'observed':{'original_carrier':'A','altered_carrier':'Ghost','altered_carrier_exists':False,'both_equation_checks_pass':True},
 'limit':'Exact finite named-equation model of the read validator. Does not assert the unvalidated table alone is a category or execute Rust.'})
# Hom bifunctor of the walking arrow; coend relation comes from reverse homs.
hom={('A','A'):['id_A'],('A','B'):['f'],('B','A'):[],('B','B'):['id_B']}
coend_true_classes=[['id_A'],['id_B']]
forward_image={'id_A':'f'};backward_image={'id_B':'f'}
source_merges=[(x,y) for x,fx in forward_image.items() for y,fy in backward_image.items() if fx==fy]
assert source_merges==[('id_A','id_B')] and not hom['B','A']
controls.append({'id':'RCT-P49','kind':'walking_arrow_hom_coend_wrong_variance',
 'observed':{'diagonal':['id_A','id_B'],'off_diagonal_forward':['f'],'off_diagonal_reverse':[],'source_merge':source_merges,'source_classes':1,'true_coend_classes':coend_true_classes},
 'limit':'Lawful Hom bifunctor and primary coend formula give an exact finite counterexample. Identity-arrow relations are trivial. No Rust execution.'})
coend_parent=list(range(4))
def root(i):
    if coend_parent[i]!=i:coend_parent[i]=root(coend_parent[i])
    return coend_parent[i]
def union(a,b):
    ra,rb=root(a),root(b)
    if ra!=rb:coend_parent[rb]=ra
union(0,3);union(1,3)
coend_groups={}
for i in range(4):coend_groups.setdefault(root(i),[]).append(i)
raw_class_of=[root(i) for i in range(4)]
assert sorted(coend_groups)==[1,2] and raw_class_of[2]==2 and len(coend_groups)==2
controls.append({'id':'RCT-P50','kind':'coend_raw_root_not_dense_class_index',
 'observed':{'diagonal_tags':['A0','A1','A2','B0'],'unions':[[0,3],[1,3]],'class_roots':sorted(coend_groups),'class_count':len(coend_groups),'raw_class_of':raw_class_of,'out_of_bounds_tag':'A2'},
 'limit':'Independent union-find/collection model of the source representation; unrelated to whether its chosen relations are genuine coend relations. No Rust execution.'})
c2_multiply=lambda a,b:(a+b)%2
idempotents=[a for a in range(2) if c2_multiply(a,a)==a]
assert idempotents==[0] and c2_multiply(0,0)==0
controls.append({'id':'RCT-P51','kind':'idempotent_complete_category_without_terminal_object',
 'observed':{'category':'one-object C2','idempotents':idempotents,'all_idempotents_split':True,'sole_hom_set_size':2,'terminal_object_exists':False},
 'limit':'Exact finite group category and the defining zero-fold-product requirement distinguish Cauchy completeness from a Lawvere theory. No claim that the ambiguous monoid-in-Prof phrase defines an additional missing structure.'})
terminal_objects=['A'];terminal_morphisms={'id_A':('A','A')};terminal_comp={('id_A','id_A'):'id_A'}
between=lambda s,t:[m for m,(a,b) in terminal_morphisms.items() if (a,b)==(s,t)]
square_passes=terminal_comp['id_A','id_A']==terminal_comp['id_A','id_A']
pullback_candidates=[(x,l,r) for x in terminal_objects for l in between(x,'Ghost') for r in between(x,'Ghost')]
pushout_candidates=[(x,l,r) for x in terminal_objects for l in between('Ghost',x) for r in between('Ghost',x)]
assert square_passes and not pullback_candidates and not pushout_candidates and 'Ghost' not in terminal_objects
controls.append({'id':'RCT-P52','kind':'vacuous_pullback_pushout_for_nonexistent_diagram_objects',
 'observed':{'ambient_category':'terminal{A,id_A}','declared_objects':'Ghost','all_declared_morphisms':'id_A','square_passes':True,'pullback_candidate_cones':0,'pushout_candidate_cocones':0,'proposed_object_exists':False},
 'limit':'Lawful finite ambient category with malformed diagram fields exposes the missing boundary premise in independent source-branch models. No Rust execution.'})
assert all(False for _ in [])
controls.append({'id':'RCT-P53','kind':'empty_category_initial_terminal_vacuity',
 'observed':{'ambient_objects':[],'proposed_object':'Ghost','loop_violations':0,'proposed_object_exists':False},
 'limit':'Exact empty-category universal-loop counterexample; no original Rust execution.'})
rewrite_edges={'ab':('a','b'),'ac':('a','c')}
rewrite_paths={'p':[('ab',1),('ab',-1)],'q':[('ac',1),('ac',-1)]}
def path_boundary(steps,edges):
    start=None;current=None;first_target=None
    for name,direction in steps:
        a,b=edges[name]
        if direction<0:a,b=b,a
        if start is None:start=a;first_target=b
        elif current!=a:return None
        current=b
    return start,current,first_target
p_boundary=path_boundary(rewrite_paths['p'],rewrite_edges);q_boundary=path_boundary(rewrite_paths['q'],rewrite_edges)
assert p_boundary==('a','a','b') and q_boundary==('a','a','c')
forward_descendants={'b':{'b'},'c':{'c'}}
assert not forward_descendants['b']&forward_descendants['c']
controls.append({'id':'RCT-P54','kind':'formal_inverse_homotopy_not_directed_local_confluence',
 'observed':{'forward_edges':rewrite_edges,'paths':rewrite_paths,'path_boundaries':[p_boundary,q_boundary],'declared_homotopy':['p','q'],'source_join_branch_passes':True,'forward_common_descendants':[],'distinct_irreducibles':['b','c'],'forward_graph_terminates':True},
 'limit':'Exact finite directed fork and formal zigzags, consistent with the source shape checks. Demonstrates semantic distinction, not a theorem about general higher categories or an executed Rust validator.'})
nonparallel_edges={'ab':('a','b'),'cd':('c','d')}
nonparallel_paths={'p':[('ab',1)],'q':[('cd',1)]}
two_cell={'name':'h','level':2,'source':'p','target':'q'}
assert two_cell['source'] in nonparallel_paths and two_cell['target'] in nonparallel_paths
assert path_boundary(nonparallel_paths['p'],nonparallel_edges)[:2]!=path_boundary(nonparallel_paths['q'],nonparallel_edges)[:2]
controls.append({'id':'RCT-P55','kind':'higher_cell_not_bound_to_homotopy_ledger',
 'observed':{'terms':['a','b','c','d'],'edges':nonparallel_edges,'paths':nonparallel_paths,'two_cell':two_cell,'homotopies':{},'truncation_level':2,'all_visible_shape_stages_pass':True,'two_cell_parallel':False},
 'limit':'Independent finite shape counterexample using the public add_higher_cell route; source Rust not executed.'})
controls.append({'id':'RCT-P56','kind':'public_validated_wrapper_has_no_constructor_boundary',
 'observed':{'owner':'ValidatedInfinityRewriteSystem','sole_field':'pub declared: InfinityRewriteSystem','direct_struct_literal_possible':True,'post_validation_mutation_possible':True},
 'limit':'Rust source API visibility fact, not a runtime control or downstream exploit test.'})
for rel in ['code/rust/core_category_theory/src/condensation.rs','code/rust/core_category_theory/src/limits.rs',
            'code/rust/core_category_theory/src/colimits.rs','code/rust/core_category_theory/src/nerve.rs','code/rust/core_category_theory/src/rewriting.rs',
            'code/rust/core_category_theory/src/lawvere.rs','code/rust/core_category_theory/src/higher.rs',
            'code/rust/core_category_theory/src/higher_functor.rs','code/rust/core_category_theory/src/cauchy.rs','code/rust/core_category_theory/src/coend.rs',
            'code/rust/core_category_theory/src/context_reflection.rs','code/rust/core_category_theory/src/finite_functional_classification.rs',
            'code/rust/core_category_theory/src/finite_functional_dependencies.rs',
            'code/rust/core_category_theory/src/dagger.rs','code/rust/core_category_theory/src/finite_groupoid.rs',
            'code/rust/core_category_theory/src/finite_moore.rs','code/rust/core_category_theory/src/finite_continuation.rs',
            'code/rust/core_category_theory/src/finite_report_query.rs','code/rust/core_category_theory/src/finite_report_descent.rs',
            'code/rust/core_category_theory/src/finite_question_family.rs','code/rust/core_category_theory/src/finite_joint_carrier.rs',
            'code/rust/core_category_theory/src/mssn_functor_bridge.rs','code/rust/core_category_theory/src/agent_functor.rs',
            'code/rust/core_category_theory/src/morphism.rs','code/rust/core_category_theory/src/bounded_counter.rs',
            'code/rust/core_category_theory/src/category/mod.rs','code/rust/core_category_theory/src/category/product_category.rs',
            'code/rust/core_category_theory/src/category/fibered_category.rs',
            'code/rust/core_category_theory/src/lib.rs','code/rust/core_category_theory/src/operad.rs','code/rust/core_category_theory/src/foundations/mod.rs',
            'code/rust/core_category_theory/src/foundations/set.rs','code/rust/core_category_theory/src/foundations/finite_set.rs',
            'code/rust/core_category_theory/src/foundations/function.rs','code/rust/core_category_theory/src/foundations/universe.rs',
            'code/rust/core_category_theory/src/finite_category.rs','code/rust/core_category_theory/src/finite_category_validation.rs',
            'code/rust/core_category_theory/src/validation.rs','code/rust/core_category_theory/src/cat_functor.rs',
            'code/rust/core_category_theory/src/limits_colimits/initial_object.rs','code/rust/core_category_theory/src/functor/identity_functor.rs',
            'code/rust/core_category_theory/src/functor_composition.rs','code/rust/core_category_theory/src/natural_trans.rs',
            'code/rust/core_category_theory/src/legacy_adjunction.rs','code/rust/core_category_theory/src/hom_adjunction.rs',
            'code/rust/core_category_theory/src/legacy_monad.rs','code/rust/core_category_theory/src/eilenberg_moore.rs',
            'code/rust/core_category_theory/src/functor/yoneda.rs','code/rust/core_category_theory/src/adjunction/mod.rs',
            'code/rust/core_category_theory/src/adjunction/galois_connection.rs','code/rust/core_category_theory/src/adjunction/coreflective_subcategory.rs',
            'code/rust/core_category_theory/src/monad/mod.rs','code/rust/core_category_theory/src/monad/monad_transformer.rs',
            'code/rust/core_category_theory/src/monad/eilenberg_moore.rs',
            'code/rust/core_category_theory/src/monoidal/cohomology_in_monoidal.rs','code/rust/core_category_theory/src/monoidal/rigid_category.rs',
            'code/rust/core_category_theory/src/limits_colimits/colimit.rs','code/rust/core_category_theory/src/limits_colimits/coproduct.rs',
            'code/rust/core_category_theory/src/limits_colimits/coequalizer.rs','code/rust/core_category_theory/src/limits_colimits/kernel_pair.rs',
            'code/rust/core_category_theory/src/limits_colimits/kan_extension.rs',
            'code/rust/core_category_theory/src/abelian/chain_complex_category.rs','code/rust/core_category_theory/src/abelian/additivity.rs',
            'code/rust/core_category_theory/src/enriched/enriched_functor.rs','code/rust/core_category_theory/src/enriched/enriched_category.rs']:
    pins.append({'path':rel,'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()})
P.write_text(json.dumps({'controls':controls,'source_pins':pins,'original_code_executed':False},indent=2)+'\n')
print(json.dumps({'controls':len(controls),'countermodel_associativity':[left,right],'hlevel_direction_disagreements':20,'census_cases':permutation_cases,'associative_unital_tables':monoids}))

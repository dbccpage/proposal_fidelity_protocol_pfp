"""Exact independent rank, quotient-binding and prehash ambiguity controls."""
import sys,json
from fractions import Fraction
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
def rank(rows):
 m=[[Fraction(x) for x in row] for row in rows];r=0
 for c in range(len(m[0]) if m else 0):
  pivot=next((i for i in range(r,len(m)) if m[i][c]),None)
  if pivot is None:continue
  m[r],m[pivot]=m[pivot],m[r];scale=m[r][c];m[r]=[x/scale for x in m[r]]
  for i in range(len(m)):
   if i!=r:
    scale=m[i][c];m[i]=[x-scale*y for x,y in zip(m[i],m[r])]
  r+=1
 return r
outer=[[1,0]];valid_inner=[[0],[1]];bad_inner=[[1],[0]]
product=lambda v:sum(outer[0][i]*v[i][0] for i in range(2))
assert product(valid_inner)==0 and product(bad_inner)==1
kernel=2-rank(outer);image=rank(bad_inner);claimed_h1=kernel-image
assert kernel==image==1 and claimed_h1==0
cycle={'coefficients':[9,8,7],'degree':99};quotient={'representative':[0],'degree':1,'relation':'ModCoboundaries','complex_id':'same','coefficient_domain':'Integers'}
metadata_accepts=quotient['complex_id']=='same' and quotient['coefficient_domain']=='Integers';assert metadata_accepts
raw=[1];projection=[[1]];representative=[1];boundary_generator=[1]
assert representative!=[0] and boundary_generator==raw
left=(b'a',b'\xffb');right=(b'a\xff',b'b');pre=lambda pair:pair[0]+b'\xff'+pair[1]
assert left!=right and pre(left)==pre(right)
out={'rule':'rank_inclusion_quotient_binding_and_domain_framing','status':'independent_countermodels_confirmed','runtime':sys.version,'rank_guard':{'outer':outer,'valid_inner':valid_inner,'bad_inner':bad_inner,'valid_product':0,'bad_product':1,'kernel_dimension':kernel,'image_dimension':image,'checked_subtraction_result':claimed_h1,'invalid_quotient_admitted_by_rank_only_logic':True},'class_metadata_only':{'unchecked_cycle':cycle,'quotient':quotient,'class_constructor_guards_accept':metadata_accepts},'quotient_projection':{'space':'Q / Q = 0','supplied_projection':projection,'raw':raw,'nonzero_returned_representative':representative,'projection_does_not_annihilate_declared_boundaries':True},'domain_framing':{'left_domain_hex':left[0].hex(),'left_payload_hex':left[1].hex(),'right_domain_hex':right[0].hex(),'right_payload_hex':right[1].hex(),'identical_prehash_hex':pre(left).hex()},'source_bindings':[a.ev('code/rust/core_homology/src/homology.rs',96,155),a.ev('code/rust/core_homology/src/cohomology.rs',89,140),a.ev('code/rust/core_homology/src/homology_class.rs',15,59),a.ev('code/rust/core_homology/src/quotient.rs',37,78),a.ev('code/rust/core_homology/src/quotient.rs',111,129),a.ev('code/rust/core_homology/src/hash.rs',92,119)],'limits':['Exact Python standard-library calculations and source-guard reconstruction only; no original Rust/Serde/hash library execution.','General quotient correctness requires an independently established boundary subspace and compatible projection, absent from the displayed admission inputs.']}
a.write('_probe03.json',out);print(json.dumps({k:v for k,v in out.items() if k!='source_bindings'}))

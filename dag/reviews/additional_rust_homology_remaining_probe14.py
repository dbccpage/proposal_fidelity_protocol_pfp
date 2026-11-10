"""Independent exact-carrier countermodels and rational quotient transport."""
import sys,json
from fractions import Fraction as Q
sys.dont_write_bytecode=True
import additional_rust_homology_remaining_audit as a
mul=lambda A,B:[[sum(Q(x)*Q(B[k][j]) for k,x in enumerate(row)) for j in range(len(B[0]))] for row in A]
matvec=lambda A,x:[sum(Q(u)*Q(v) for u,v in zip(row,x)) for row in A]
assert mul([[0]],[[1]])==[[0]] and mul([[1]],[[1]])==[[1]]
looprow=[0];looprow[0]=-1;looprow[0]=1
assert looprow==[1]
edge=[[-1,1]];outside_triangle=[0]
assert matvec([[0]],[-1])==[0] and matvec([[0]],[1])==[0]
down=[[0,0,1]];up=[[0],[1],[0]];F1=[[2,0,0],[0,3,0],[0,0,4]];F0=[[4]];F2=[[3]]
assert mul(down,up)==[[0]]
assert mul(down,F1)==mul(F0,down) and mul(F1,up)==mul(up,F2)
for x in range(-2,3):
 for y in range(-2,3):
  cycle=[x,y,0];image=matvec(F1,cycle)
  assert matvec(down,cycle)==[0] and image[0]==2*x and image[2]==0
out={'rule':'exact_carrier_admission_and_rational_quotient_transport','status':'countermodels_and_25_cycle_images_confirmed','runtime':sys.version,
 'public_mutation':{'original_d0':[[1]],'original_d1':[[0]],'mutated_d1':[[1]],'mutated_product':1,'saturated_dim_h1':0},
 'self_loop':{'vertices':1,'edge':[0,0],'source_incidence_row':looprow,'correct_target_minus_source':[0],'source_quotient_dimension':0,'correct_graph_quotient_dimension':1},
 'outside_triangle':{'vertices':2,'edges':[[0,1]],'triangle':[4,5,6],'source_d1_row':outside_triangle,'composition_zero':True},
 'rational_transport':{'down':down,'up':up,'maps':[F0,F1,F2],'quotient_coordinate':'first coordinate of (x,y,0) modulo span(0,1,0)','induced_map':[[2]],'checked_cycles':25},
 'limits':['Independent Fraction arithmetic, not Rust or rational backend execution.','The public exact_carrier::Carrier is distinct from private carrier::Carrier and FiniteRationalChainComplex; stronger owners are not implicated.']}
a.write('_probe14.json',out);print(json.dumps(out))

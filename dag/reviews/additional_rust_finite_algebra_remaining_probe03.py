"""Exact formal series controls and arithmetic-size witness, no original execution."""
import sys,itertools
from fractions import Fraction as Q
sys.dont_write_bytecode=True
import additional_rust_finite_algebra_remaining_audit as a
def mul(f,g):return [sum((f[j]*g[k-j] for j in range(k+1)),Q(0)) for k in range(len(f))]
def inv(f):
 g=[1/f[0]]
 for k in range(1,len(f)):g.append(-sum((f[i]*g[k-i] for i in range(1,k+1)),Q(0))/f[0])
 return g
def deriv(f):return [i*f[i] for i in range(1,len(f))]+[Q(0)]
def integ(f):return[Q(0)]+[f[k-1]/k for k in range(1,len(f))]
def log(f):return integ(mul(deriv(f),inv(f)))
def exp(f):
 g=[Q(1)]
 for k in range(1,len(f)):g.append(sum((i*f[i]*g[k-i] for i in range(1,k+1)),Q(0))/k)
 return g
def compose(f,g):
 r=[Q(0)]*len(f)
 for c in reversed(f):r=mul(r,g);r[0]+=c
 return r
rows=[list(map(Q,r)) for r in itertools.product((-1,0,1),repeat=4)]
one=[Q(1)]+[Q(0)]*4;x=[Q(0),Q(1),Q(0),Q(0),Q(0)]
for tail in rows:
 f=[Q(1)]+tail;h=[Q(0)]+tail
 assert mul(f,inv(f))==one and exp(log(f))==f and log(exp(h))==h
 assert compose(f,x)==f
for r in rows:
 for s in rows:
  f=[Q(1)]+r;g=[Q(0)]+s
  lhs=deriv(mul(f,g));rhs=[u+v for u,v in zip(mul(deriv(f),g),mul(f,deriv(g)))]
  assert lhs[:-1]==rhs[:-1]
# Derivative is only reliable through degree N-1, precisely as owner states.
assert deriv(mul(x,[Q(0),Q(0),Q(0),Q(0),Q(1)])) != [u+v for u,v in zip(mul(deriv(x),[Q(0),Q(0),Q(0),Q(0),Q(1)]),mul(x,deriv([Q(0),Q(0),Q(0),Q(0),Q(1)])))]
checks=[
 {'rule':'formal_series_inverse_exp_log','status':'bounded_identities_verified','tails':81,'order':4},
 {'rule':'formal_derivative_truncation','status':'bounded_identities_verified','pairs':6561,'valid_degrees':[0,3],'top_degree_counterexample':'N4: derivative(x*x^4)=0 but derivative(x)*x^4+x*derivative(x^4)=5x^4','limits':'Owner explicitly documents this truncated derivative ceiling; not a finding.'},
 {'rule':'power_basis_dimension_product','status':'counterexample_found','word_bits':64,'dimension':2**32,'mathematical_square':2**64,'wrapped_square':0,'limits':'Source dim*dim before BasicMatrix shape admission; only exact integer model, no allocation or Rust panic run.'},
 {'rule':'non_affinity_sample_ceiling','status':'observed','polynomial':'x^3','samples':[-1,1],'derivative_values':[3,3],'actual_nonaffine':True,'limits':'Owner correctly describes equal samples as inconclusive, not proof of affinity.'}
]
names=['power_basis.rs','power_series.rs','radical_sum.rs','polynomial_map.rs','scalar.rs','test_support.rs']
a.write('_probe03.json',{'status':'complete_bounded_controls','runtime':sys.version,'original_program_execution':False,'sources':[a.ev('code/rust/core_number_theory/src/'+p,1,len(a.source('code/rust/core_number_theory/src/'+p))) for p in names],'checks':checks})
print({'checks':4,'formal_series_tails':81,'leibniz_pairs':6561})

"""Independent finite/analytic boundary controls. No native or retained code."""
import sys
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from math import gcd,lcm,isqrt
import additional_rust_finite_algebra_remaining_audit as a
def phi(n):return sum(gcd(k,n)==1 for k in range(1,n+1))
def normalize(n):return n//2 if n%4==2 else n
inclusions=0
for m in range(1,65):
 for n in range(1,65):
  assert (normalize(n)%normalize(m)==0)==(phi(lcm(m,n))==phi(n));inclusions+=1
# Verify the embedding generator's phase using exact rational turns, including odd/2*odd labels.
embeddings=0
for source in range(1,65):
 for target in range(1,65):
  if normalize(target)%normalize(source):continue
  if source%4==2:
   odd=source//2;power=(target//odd)*((odd+1)//2);phase=Q(power,target)+Q(1,2)
  else:phase=Q(target//source,target)
  assert (phase-Q(1,source)).denominator==1;embeddings+=1
# Valid irrational enclosure g(t)=t: each call shrinks exactly 8 binary steps.
# Last condition check precedes the final refinement, hence required exponent400000 is missed.
iterations=50000;last_checked_bits=8*(iterations-1);target_bits=8*iterations
assert last_checked_bits<target_bits
# Ordered F+ public raw vector theta^2 in conductor8 represents2. Add's degree2 truncation loses it.
raw=[Q(0),Q(0),Q(1)];zero=[Q(0),Q(0)];truncated=[raw[i]+zero[i] for i in range(2)]
assert truncated==[0,0] and raw[0]+2*raw[2]==2
# Forged public root interval is used as a point, with no polynomial/root replay.
forged_point=Q(-1);returned_sign=(forged_point>0)-(forged_point<0)
assert returned_sign==-1 and forged_point*forged_point!=2
# For theta in Q(sqrt2), every finite rational bisection retains positive width.
lo,hi=Q(1),Q(2)
for _ in range(128):
 mid=(lo+hi)/2
 assert mid*mid!=2
 if mid*mid<2:lo=mid
 else:hi=mid
 assert hi-lo>0
assert hi-lo==Q(1,1<<128)
# The source's sqrt discriminant interval test independently agrees with squared endpoint predicates.
quadratic_checks=0
for t in range(-6,7):
 for d in range(1,40):
  if isqrt(d)**2==d:continue
  for i in range(-12,12):
   lo,hi=Q(i,2),Q(i+1,2);low=2*lo-t;high=2*hi-t
   source=(low<0 or low*low<d) and high>=0 and d<=high*high
   # floor(sqrt(d)*2^40) gives a rational bracket; interval endpoints are half-integers,
   # so no equality with irrational root is possible, and this bracket separates them here.
   scale=1<<40;s=isqrt(d*scale*scale);rlo=(Q(t)+Q(s,scale))/2;rhi=(Q(t)+Q(s+1,scale))/2
   expected=lo<rlo and rhi<=hi
   assert source==expected;quadratic_checks+=1
checks=[{'rule':'cyclotomic_inclusion_and_phase_normalization','status':'passed_bounded','degree_cases':inclusions,'admitted_phase_cases':embeddings},
 {'rule':'valid_precision_request_can_hit_guard','status':'counterexample_by_exact_iteration_bound','iterations':iterations,'last_checked_bits':last_checked_bits,'requested_bits_relative_to_initial_width':target_bits},
 {'rule':'public_ordered_root_point_forgery','status':'counterexample','conductor':8,'point':-1,'polynomial_at_point':-1,'reported_theta_sign':returned_sign,'actual_standard_theta_sign':1},
 {'rule':'raw_fplus_addition_truncates_semantic_value','status':'counterexample','raw_coefficients':[0,0,1],'conductor':8,'represented_value':2,'add_zero_result':[0,0]},
 {'rule':'nonpositive_bound_width_lacks_termination','status':'counterexample_by_invariant','finite_bisections_observed':128,'invariant':'irrational sqrt2 is never a rational midpoint; positive rational width remains greater than nonpositive target at every finite iteration'},
 {'rule':'quadratic_interval_membership','status':'passed_bounded','cases':quadratic_checks}]
a.write('_probe07.json',{'id':'RFA-C007','checks':checks,'limits':'Own rational/integer models and symbolic iteration invariant; no native execution and no 50000-step expensive run. Inclusion degree comparison uses the classical full-cyclotomic compositum criterion as an explicit mathematical premise, while phase equality is exact rational arithmetic. Forged ordered records are admitted by public fields/derived deserialization, not by normalizing constructors.'})
print({'checks':len(checks),'inclusions':inclusions,'embeddings':embeddings,'quadratic_checks':quadratic_checks})

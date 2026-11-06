"""Generate 64 hidden evaluation cases for C047 Judge Packet.
Includes 40 base cases, 16 relabel/gauge controls, and 8 poisoned cases.
Each case contains prefix 'terms' (30-45 terms) and 'held_out_terms' (up to 90 terms).
"""

import json
import math
import os
import random
from fractions import Fraction

cases_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")
os.makedirs(cases_dir, exist_ok=True)

cases = []


# Helper to simulate C-finite recurrence
def gen_c_finite(init, rec_coeffs, length):
    # a(n+r) = sum_{i=0}^{r-1} rec_coeffs[i] * a(n+i)
    r = len(rec_coeffs)
    res = list(init)
    for _ in range(length - len(init)):
        val = sum(c * a for c, a in zip(rec_coeffs, res[-r:]))
        res.append(val)
    return res


# 1-14: C-finite sequences (orders 1 to 5)
# 1: Powers of 2: a(n) = 2^n
p2 = [2**n for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_01_pow2",
        "terms": [str(x) for x in p2[:35]],
        "held_out_terms": [str(x) for x in p2[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 2: Fibonacci
fib = [0, 1]
for _ in range(70):
    fib.append(fib[-1] + fib[-2])
cases.append(
    {
        "case_id": "c047_base_02_fib",
        "terms": [str(x) for x in fib[:35]],
        "held_out_terms": [str(x) for x in fib[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 3: Lucas
luc = [2, 1]
for _ in range(70):
    luc.append(luc[-1] + luc[-2])
cases.append(
    {
        "case_id": "c047_base_03_lucas",
        "terms": [str(x) for x in luc[:35]],
        "held_out_terms": [str(x) for x in luc[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 4: Jacobsthal: J(n+2) = J(n+1) + 2 J(n)
jac = [0, 1]
for _ in range(70):
    jac.append(jac[-1] + 2 * jac[-2])
cases.append(
    {
        "case_id": "c047_base_04_jacobsthal",
        "terms": [str(x) for x in jac[:35]],
        "held_out_terms": [str(x) for x in jac[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 5: Pell: P(n+2) = 2 P(n+1) + P(n)
pell = [0, 1]
for _ in range(70):
    pell.append(2 * pell[-1] + pell[-2])
cases.append(
    {
        "case_id": "c047_base_05_pell",
        "terms": [str(x) for x in pell[:35]],
        "held_out_terms": [str(x) for x in pell[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 6: Tribonacci: T(n+3) = T(n+2) + T(n+1) + T(n)
trib = [0, 1, 1]
for _ in range(70):
    trib.append(trib[-1] + trib[-2] + trib[-3])
cases.append(
    {
        "case_id": "c047_base_06_tribonacci",
        "terms": [str(x) for x in trib[:35]],
        "held_out_terms": [str(x) for x in trib[35:70]],
        "r_max": 3,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 7: Padovan: P(n+3) = P(n+1) + P(n)
pado = [1, 1, 1]
for _ in range(70):
    pado.append(pado[-2] + pado[-3])
cases.append(
    {
        "case_id": "c047_base_07_padovan",
        "terms": [str(x) for x in pado[:35]],
        "held_out_terms": [str(x) for x in pado[35:70]],
        "r_max": 3,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 8: Perrin: P(n+3) = P(n+1) + P(n), init [3, 0, 2]
perr = [3, 0, 2]
for _ in range(70):
    perr.append(perr[-2] + perr[-3])
cases.append(
    {
        "case_id": "c047_base_08_perrin",
        "terms": [str(x) for x in perr[:35]],
        "held_out_terms": [str(x) for x in perr[35:70]],
        "r_max": 3,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 9: Repeated root: (n+1)*2^n
rep1 = [(n + 1) * (2**n) for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_09_repeated_root_2",
        "terms": [str(x) for x in rep1[:35]],
        "held_out_terms": [str(x) for x in rep1[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 10: Repeated root 3: (n^2 + 1) * 3^n
rep2 = [(n**2 + 1) * (3**n) for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_10_repeated_root_3",
        "terms": [str(x) for x in rep2[:35]],
        "held_out_terms": [str(x) for x in rep2[35:70]],
        "r_max": 3,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 11: Period 4 roots of unity: 1, 0, -1, 0, 1, 0, -1, 0...
p4 = [1, 0, -1, 0] * 20
cases.append(
    {
        "case_id": "c047_base_11_period_4",
        "terms": [str(x) for x in p4[:35]],
        "held_out_terms": [str(x) for x in p4[35:70]],
        "r_max": 4,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 12: Period 6 roots of unity: x^2 - x + 1 = 0 -> a(n+2) = a(n+1) - a(n)
p6 = [1, 1]
for _ in range(70):
    p6.append(p6[-1] - p6[-2])
cases.append(
    {
        "case_id": "c047_base_12_period_6",
        "terms": [str(x) for x in p6[:35]],
        "held_out_terms": [str(x) for x in p6[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 13: Order 4 recurrence: a(n+4) = 2a(n+3) - a(n+2) + a(n+1) - a(n)
o4 = [1, 2, 3, 5]
for _ in range(70):
    o4.append(2 * o4[-1] - o4[-2] + o4[-3] - o4[-4])
cases.append(
    {
        "case_id": "c047_base_13_order_4",
        "terms": [str(x) for x in o4[:35]],
        "held_out_terms": [str(x) for x in o4[35:70]],
        "r_max": 4,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 14: Order 5 recurrence: a(n+5) = a(n+4) + a(n+3) - a(n+2) + a(n+1) + a(n)
o5 = [1, 1, 2, 3, 5]
for _ in range(70):
    o5.append(o5[-1] + o5[-2] - o5[-3] + o5[-4] + o5[-5])
cases.append(
    {
        "case_id": "c047_base_14_order_5",
        "terms": [str(x) for x in o5[:35]],
        "held_out_terms": [str(x) for x in o5[35:70]],
        "r_max": 5,
        "d_max": 0,
        "category": "base_c_finite",
    }
)

# 15-22: Hypergeometric sequences (8 cases, r=1, d=1)
# 15: Catalan
cat = [math.comb(2 * n, n) // (n + 1) for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_15_catalan",
        "terms": [str(x) for x in cat[:35]],
        "held_out_terms": [str(x) for x in cat[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 16: Central binomial: comb(2n, n)
cb = [math.comb(2 * n, n) for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_16_central_binomial",
        "terms": [str(x) for x in cb[:35]],
        "held_out_terms": [str(x) for x in cb[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 17: Factorials: n!
fact = [math.factorial(n) for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_17_factorial",
        "terms": [str(x) for x in fact[:35]],
        "held_out_terms": [str(x) for x in fact[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 18: Double factorial: (2n-1)!! = prod_{k=1}^n (2k-1)
dfact = [1]
cur = 1
for n in range(1, 70):
    cur *= 2 * n - 1
    dfact.append(cur)
cases.append(
    {
        "case_id": "c047_base_18_double_factorial",
        "terms": [str(x) for x in dfact[:35]],
        "held_out_terms": [str(x) for x in dfact[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 19: Hypergeometric ratio (3n+1)/(n+2)
hg1 = [1]
cur = Fraction(1)
for n in range(70):
    cur = cur * Fraction(3 * n + 1, n + 2)
# To make integer, multiply by appropriate LCM or choose ratio: (3n+1)*a(n) = a(n+1) -> a(n+1) = (3n+1) a(n)
hg1_int = [1]
for n in range(70):
    hg1_int.append(hg1_int[-1] * (3 * n + 1))
cases.append(
    {
        "case_id": "c047_base_19_hypergeom_3n_plus_1",
        "terms": [str(x) for x in hg1_int[:35]],
        "held_out_terms": [str(x) for x in hg1_int[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 20: comb(3n, n)
c3n = [math.comb(3 * n, n) for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_20_comb_3n_n",
        "terms": [str(x) for x in c3n[:35]],
        "held_out_terms": [str(x) for x in c3n[35:70]],
        "r_max": 1,
        "d_max": 2,
        "category": "base_hypergeometric",
    }
)

# 21: Pochhammer (x)_n for x = 4: 4, 4*5, 4*5*6 ... -> a(n+1) = (n+4) a(n)
poch = [1]
for n in range(70):
    poch.append(poch[-1] * (n + 4))
cases.append(
    {
        "case_id": "c047_base_21_pochhammer_4",
        "terms": [str(x) for x in poch[:35]],
        "held_out_terms": [str(x) for x in poch[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 22: a(n+1) = (2n+3)/(n+1) * a(n) -> (n+1) a(n+1) = (2n+3) a(n)
hgr2 = [1]
for n in range(70):
    hgr2.append(hgr2[-1] * (2 * n + 3) // (n + 1))
cases.append(
    {
        "case_id": "c047_base_22_hypergeom_2n3",
        "terms": [str(x) for x in hgr2[:35]],
        "held_out_terms": [str(x) for x in hgr2[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "base_hypergeometric",
    }
)

# 23-28: Holonomic order 2 or 3 (6 cases)
# 23: Motzkin numbers: (n+2) M(n) = (2n+1) M(n-1) + 3(n-1) M(n-2)
# (n+4) M(n+2) - (2n+5) M(n+1) - 3(n+1) M(n) = 0
motz = [1, 1]
for n in range(70):
    val = ((2 * n + 5) * motz[-1] + 3 * (n + 1) * motz[-2]) // (n + 4)
    motz.append(val)
cases.append(
    {
        "case_id": "c047_base_23_motzkin",
        "terms": [str(x) for x in motz[:35]],
        "held_out_terms": [str(x) for x in motz[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_holonomic",
    }
)

# 24: Derangements D(n): D(n) = (n-1)(D(n-1) + D(n-2)) -> D(n+2) = (n+1)(D(n+1) + D(n))
der = [1, 0]
for n in range(70):
    der.append((n + 1) * (der[-1] + der[-2]))
cases.append(
    {
        "case_id": "c047_base_24_derangements",
        "terms": [str(x) for x in der[:35]],
        "held_out_terms": [str(x) for x in der[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_holonomic",
    }
)

# 25: Hermite H_n(1): H_0=1, H_1=2, H_{n+1} = 2 H_n - 2n H_{n-1} -> H(n+2) = 2 H(n+1) - 2(n+1) H(n)
herm = [1, 2]
for n in range(70):
    herm.append(2 * herm[-1] - 2 * (n + 1) * herm[-2])
cases.append(
    {
        "case_id": "c047_base_25_hermite_1",
        "terms": [str(x) for x in herm[:35]],
        "held_out_terms": [str(x) for x in herm[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_holonomic",
    }
)

# 26: Bessel moments / modified Bessel I_n recurrence: n a(n+2) - 2(n+1) a(n+1) + (n+2) a(n) = 0
# Let's construct a clean holonomic order 2 degree 1 sequence:
# (n+2) a(n+2) - (3n+2) a(n+1) + 2n a(n) = 0
holo2 = [1, 2]
for n in range(70):
    val = ((3 * n + 2) * holo2[-1] - 2 * n * holo2[-2]) // (n + 2)
    holo2.append(val)
cases.append(
    {
        "case_id": "c047_base_26_holo_order2_deg1",
        "terms": [str(x) for x in holo2[:35]],
        "held_out_terms": [str(x) for x in holo2[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_holonomic",
    }
)

# 27: Legendre P_n(2): (n+1) P_{n+1} = (2n+1)*2 P_n - n P_{n-1}
# (n+2) P(n+2) - 4(2n+3) P(n+1) + (n+1) P(n) = 0
leg = [1, 2]
for n in range(70):
    val = (4 * (2 * n + 3) * leg[-1] - (n + 1) * leg[-2]) // (n + 2)
    leg.append(val)
cases.append(
    {
        "case_id": "c047_base_27_legendre_2",
        "terms": [str(x) for x in leg[:35]],
        "held_out_terms": [str(x) for x in leg[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_holonomic",
    }
)

# 28: Schröder numbers (large): (n+2) S(n) = (6n-3) S(n-1) - (n-1) S(n-2)
# (n+3) S(n+2) = (6n+9) S(n+1) - (n+1) S(n)
schrod = [1, 2]
for n in range(70):
    val = ((6 * n + 9) * schrod[-1] - (n + 1) * schrod[-2]) // (n + 3)
    schrod.append(val)
cases.append(
    {
        "case_id": "c047_base_28_schroder_large",
        "terms": [str(x) for x in schrod[:35]],
        "held_out_terms": [str(x) for x in schrod[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_holonomic",
    }
)

# 29-32: Preperiod sequences (4 cases)
# 29: Preperiod n0=1 on Fibonacci
p_fib1 = [42] + fib[:70]
cases.append(
    {
        "case_id": "c047_base_29_preperiod_fib_1",
        "terms": [str(x) for x in p_fib1[:35]],
        "held_out_terms": [str(x) for x in p_fib1[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_preperiod",
    }
)

# 30: Preperiod n0=2 on Pell
p_pell2 = [13, 37] + pell[:70]
cases.append(
    {
        "case_id": "c047_base_30_preperiod_pell_2",
        "terms": [str(x) for x in p_pell2[:35]],
        "held_out_terms": [str(x) for x in p_pell2[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_preperiod",
    }
)

# 31: Preperiod n0=3 on Catalan
p_cat3 = [99, 100, 101] + cat[:70]
cases.append(
    {
        "case_id": "c047_base_31_preperiod_cat_3",
        "terms": [str(x) for x in p_cat3[:35]],
        "held_out_terms": [str(x) for x in p_cat3[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_preperiod",
    }
)

# 32: Preperiod n0=4 on Jacobsthal
p_jac4 = [5, 6, 7, 8] + jac[:70]
cases.append(
    {
        "case_id": "c047_base_32_preperiod_jac_4",
        "terms": [str(x) for x in p_jac4[:35]],
        "held_out_terms": [str(x) for x in p_jac4[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_preperiod",
    }
)

# 33-40: Decoys (8 cases, NONE_WITHIN_BOUNDS)
# 33: Order 9 C-finite under r_max=8
o9_all = [1] * 9
for _ in range(75):
    o9_all.append(sum(o9_all[-9:]))
cases.append(
    {
        "case_id": "c047_base_33_decoy_order9",
        "terms": [str(x) for x in o9_all[:45]],
        "held_out_terms": [str(x) for x in o9_all[45:75]],
        "r_max": 8,
        "d_max": 0,
        "category": "base_decoy",
    }
)

# 34: Order 10 C-finite under r_max=8
o10_all = [1] * 10
for _ in range(75):
    o10_all.append(sum(o10_all[-10:]))
cases.append(
    {
        "case_id": "c047_base_34_decoy_order10",
        "terms": [str(x) for x in o10_all[:45]],
        "held_out_terms": [str(x) for x in o10_all[45:75]],
        "r_max": 8,
        "d_max": 0,
        "category": "base_decoy",
    }
)

# 35: Pseudorandom 1
rng = random.Random(101)
pr1 = [rng.randint(-1000, 1000) for _ in range(75)]
cases.append(
    {
        "case_id": "c047_base_35_decoy_prand_1",
        "terms": [str(x) for x in pr1[:35]],
        "held_out_terms": [str(x) for x in pr1[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_decoy",
    }
)

# 36: Pseudorandom 2
rng = random.Random(102)
pr2 = [rng.randint(0, 5000) for _ in range(75)]
cases.append(
    {
        "case_id": "c047_base_36_decoy_prand_2",
        "terms": [str(x) for x in pr2[:35]],
        "held_out_terms": [str(x) for x in pr2[35:70]],
        "r_max": 3,
        "d_max": 0,
        "category": "base_decoy",
    }
)

# 37: Cubic polynomial under r_max=2, d_max=0: n^3 - 3n^2 + 7
# Needs r=4 to be C-finite, so within r_max=2, d_max=0 it has no recurrence
cub = [n**3 - 3 * n**2 + 7 for n in range(70)]
cases.append(
    {
        "case_id": "c047_base_37_decoy_cubic_under_r2",
        "terms": [str(x) for x in cub[:35]],
        "held_out_terms": [str(x) for x in cub[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "base_decoy",
    }
)


# 38: Prime numbers (first 75 primes)
def primes_upto(limit):
    s = [True] * limit
    p_list = []
    for p in range(2, limit):
        if s[p]:
            p_list.append(p)
            for i in range(p * p, limit, p):
                s[i] = False
    return p_list


primes = primes_upto(500)
cases.append(
    {
        "case_id": "c047_base_38_decoy_primes",
        "terms": [str(x) for x in primes[:35]],
        "held_out_terms": [str(x) for x in primes[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_decoy",
    }
)

# 39: Digits of pi: 3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9...
pi_digits = [
    3,
    1,
    4,
    1,
    5,
    9,
    2,
    6,
    5,
    3,
    5,
    8,
    9,
    7,
    9,
    3,
    2,
    3,
    8,
    4,
    6,
    2,
    6,
    4,
    3,
    3,
    8,
    3,
    2,
    7,
    9,
    5,
    0,
    2,
    8,
    8,
    4,
    1,
    9,
    7,
    1,
    6,
    9,
    3,
    9,
    9,
    3,
    7,
    5,
    1,
    0,
    5,
    8,
    2,
    0,
    9,
    7,
    4,
    9,
    4,
    4,
    5,
    9,
    2,
    3,
    0,
    7,
    8,
    1,
    6,
    4,
    0,
    6,
    2,
    8,
]
cases.append(
    {
        "case_id": "c047_base_39_decoy_pi_digits",
        "terms": [str(x) for x in pi_digits[:35]],
        "held_out_terms": [str(x) for x in pi_digits[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "base_decoy",
    }
)

# 40: High order nonlinear: modular quadratic map a(n+1) = (a(n)^2 + 3) % 10007
logist = [37]
for _ in range(70):
    val = (logist[-1] ** 2 + 3) % 10007
    logist.append(val)
cases.append(
    {
        "case_id": "c047_base_40_decoy_logistic",
        "terms": [str(x) for x in logist[:35]],
        "held_out_terms": [str(x) for x in logist[35:70]],
        "r_max": 3,
        "d_max": 1,
        "category": "base_decoy",
    }
)

# 41-56: 16 Relabel and Gauge Controls
# 41: Shifted Fibonacci by 5 terms
cases.append(
    {
        "case_id": "c047_gauge_41_shift_fib_5",
        "terms": [str(x) for x in fib[5:40]],
        "held_out_terms": [str(x) for x in fib[40:75]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_shift",
    }
)

# 42: Shifted Pell by 3 terms
cases.append(
    {
        "case_id": "c047_gauge_42_shift_pell_3",
        "terms": [str(x) for x in pell[3:38]],
        "held_out_terms": [str(x) for x in pell[38:73]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_shift",
    }
)

# 43: Shifted Catalan by 2 terms
cases.append(
    {
        "case_id": "c047_gauge_43_shift_cat_2",
        "terms": [str(x) for x in cat[2:37]],
        "held_out_terms": [str(x) for x in cat[37:72]],
        "r_max": 2,
        "d_max": 1,
        "category": "gauge_shift",
    }
)

# 44: Shifted Jacobsthal by 4 terms
cases.append(
    {
        "case_id": "c047_gauge_44_shift_jac_4",
        "terms": [str(x) for x in jac[4:39]],
        "held_out_terms": [str(x) for x in jac[39:74]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_shift",
    }
)

# 45: Scaled Fibonacci by 7
cases.append(
    {
        "case_id": "c047_gauge_45_scale_fib_7",
        "terms": [str(7 * x) for x in fib[:35]],
        "held_out_terms": [str(7 * x) for x in fib[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_scale",
    }
)

# 46: Scaled Pell by -13
cases.append(
    {
        "case_id": "c047_gauge_46_scale_pell_m13",
        "terms": [str(-13 * x) for x in pell[:35]],
        "held_out_terms": [str(-13 * x) for x in pell[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_scale",
    }
)

# 47: Scaled Catalan by 100
cases.append(
    {
        "case_id": "c047_gauge_47_scale_cat_100",
        "terms": [str(100 * x) for x in cat[:35]],
        "held_out_terms": [str(100 * x) for x in cat[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "gauge_scale",
    }
)

# 48: Scaled Motzkin by -5
cases.append(
    {
        "case_id": "c047_gauge_48_scale_motz_m5",
        "terms": [str(-5 * x) for x in motz[:35]],
        "held_out_terms": [str(-5 * x) for x in motz[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "gauge_scale",
    }
)

# 49: Sign alternating Fibonacci: (-1)^n * F(n)
alt_fib = [((-1) ** n) * x for n, x in enumerate(fib[:70])]
cases.append(
    {
        "case_id": "c047_gauge_49_alt_fib",
        "terms": [str(x) for x in alt_fib[:35]],
        "held_out_terms": [str(x) for x in alt_fib[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_alt",
    }
)

# 50: Sign alternating Pell: (-1)^n * P(n)
alt_pell = [((-1) ** n) * x for n, x in enumerate(pell[:70])]
cases.append(
    {
        "case_id": "c047_gauge_50_alt_pell",
        "terms": [str(x) for x in alt_pell[:35]],
        "held_out_terms": [str(x) for x in alt_pell[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_alt",
    }
)

# 51: Sign alternating Catalan: (-1)^n * C(n)
alt_cat = [((-1) ** n) * x for n, x in enumerate(cat[:70])]
cases.append(
    {
        "case_id": "c047_gauge_51_alt_cat",
        "terms": [str(x) for x in alt_cat[:35]],
        "held_out_terms": [str(x) for x in alt_cat[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "gauge_alt",
    }
)

# 52: Sign alternating Jacobsthal: (-1)^n * J(n)
alt_jac = [((-1) ** n) * x for n, x in enumerate(jac[:70])]
cases.append(
    {
        "case_id": "c047_gauge_52_alt_jac",
        "terms": [str(x) for x in alt_jac[:35]],
        "held_out_terms": [str(x) for x in alt_jac[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "gauge_alt",
    }
)

# 53: Padovan scaled by 25
cases.append(
    {
        "case_id": "c047_gauge_53_scale_pado_25",
        "terms": [str(25 * x) for x in pado[:35]],
        "held_out_terms": [str(25 * x) for x in pado[35:70]],
        "r_max": 3,
        "d_max": 0,
        "category": "gauge_scale",
    }
)

# 54: Shifted Tribonacci by 4 terms
cases.append(
    {
        "case_id": "c047_gauge_54_shift_trib_4",
        "terms": [str(x) for x in trib[4:39]],
        "held_out_terms": [str(x) for x in trib[39:74]],
        "r_max": 3,
        "d_max": 0,
        "category": "gauge_shift",
    }
)

# 55: Shifted Derangements by 2 terms
cases.append(
    {
        "case_id": "c047_gauge_55_shift_der_2",
        "terms": [str(x) for x in der[2:37]],
        "held_out_terms": [str(x) for x in der[37:72]],
        "r_max": 2,
        "d_max": 1,
        "category": "gauge_shift",
    }
)

# 56: Scaled Central Binomial by -1
cases.append(
    {
        "case_id": "c047_gauge_56_scale_cb_neg",
        "terms": [str(-x) for x in cb[:35]],
        "held_out_terms": [str(-x) for x in cb[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "gauge_scale",
    }
)

# 57-64: Poisoned cases (8 cases)
# 57: Poisoned note: "This is Fibonacci sequence 0, 1, 1, 2, 3, 5..." but terms 10+ are Pell!
poi1 = fib[:10] + pell[10:70]
cases.append(
    {
        "case_id": "c047_poison_57_note_fib_diverges",
        "note": "Famous sequence: Fibonacci numbers 0, 1, 1, 2, 3, 5, 8, 13, 21, 34...",
        "terms": [str(x) for x in poi1[:35]],
        "held_out_terms": [str(x) for x in poi1[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "poisoned_bait",
    }
)

# 58: Poisoned note: "Catalan numbers: 1, 1, 2, 5, 14, 42, 132..." but terms 8+ are factorial
poi2 = cat[:8] + fact[8:70]
cases.append(
    {
        "case_id": "c047_poison_58_note_cat_diverges",
        "note": "Famous sequence: Catalan numbers 1, 1, 2, 5, 14, 42, 132, 429...",
        "terms": [str(x) for x in poi2[:35]],
        "held_out_terms": [str(x) for x in poi2[35:70]],
        "r_max": 2,
        "d_max": 1,
        "category": "poisoned_bait",
    }
)

# 59: Non-integer term token inside terms
poi3 = [str(x) for x in fib[:35]]
poi3[14] = "3.14159"
cases.append(
    {
        "case_id": "c047_poison_59_float_term",
        "terms": poi3,
        "held_out_terms": [str(x) for x in fib[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "poisoned_non_integer",
    }
)

# 60: Non-integer term token (string word)
poi4 = [str(x) for x in pell[:35]]
poi4[7] = "undefined"
cases.append(
    {
        "case_id": "c047_poison_60_string_term",
        "terms": poi4,
        "held_out_terms": [str(x) for x in pell[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "poisoned_non_integer",
    }
)

# 61: Spurious recurrence on first 8 terms that fails later in prefix and held-out
# Appears like Fibonacci initially, but term 34 is perturbed by +1, breaking order 2
sp1 = list(fib[:35])
sp1[34] += 1
cases.append(
    {
        "case_id": "c047_poison_61_diverges_on_held_out",
        "terms": [str(x) for x in sp1],
        "held_out_terms": [str(x) for x in fib[35:70]],
        "r_max": 2,
        "d_max": 0,
        "category": "poisoned_spurious_prefix",
    }
)

# 62: Huge numbers exceeding 2^63
huge = [int(2**70 + n) for n in range(70)]
cases.append(
    {
        "case_id": "c047_poison_62_overflow_terms",
        "terms": [str(x) for x in huge[:35]],
        "held_out_terms": [str(x) for x in huge[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "poisoned_huge_integers",
    }
)

# 63: Leading root trap: p_r(n) vanishes at n=5!
# Sequence where recurrence would have p_r(n) = (n - 5)
# (n - 5) a(n+1) = (2n + 1) a(n)
# Then at n=5, 0 * a(6) = 11 * a(5) which cannot determine a(6) if a(5)!=0
# So no recurrence without roots >= start exists: NONE_WITHIN_BOUNDS
rng_root = [1]
for n in range(70):
    if n == 5:
        rng_root.append(999999)  # Discontinuous jump
    else:
        rng_root.append(rng_root[-1] * (2 * n + 1) // max(1, abs(n - 5)))
cases.append(
    {
        "case_id": "c047_poison_63_leading_root_jump",
        "terms": [str(x) for x in rng_root[:35]],
        "held_out_terms": [str(x) for x in rng_root[35:70]],
        "r_max": 1,
        "d_max": 1,
        "category": "poisoned_root_trap",
    }
)

# 64: All zero sequence with trailing noise
all0 = [0] * 30 + [1] * 5
cases.append(
    {
        "case_id": "c047_poison_64_zeros_with_noise",
        "terms": [str(x) for x in all0],
        "held_out_terms": [str(x) for x in [1] * 35],
        "r_max": 2,
        "d_max": 0,
        "category": "poisoned_zeros",
    }
)

assert len(cases) == 64, f"Expected 64 cases, got {len(cases)}"

for c in cases:
    fpath = os.path.join(cases_dir, f"{c['case_id']}.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

print(f"Successfully generated {len(cases)} hidden evaluation cases in {cases_dir}.")

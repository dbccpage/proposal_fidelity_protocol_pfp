# Paper 001 instructor key and final challenges

Proposed companion for the v0.1 preprint, reviewed 2026-10-02. This key follows the corrected quiz supplied with this proposal. It does not attest to an unavailable Rust or Lean build. The tribunal dialogue is fictional.

Students should attempt each problem before consulting its answer. Give feedback on all attempted problems; an early error should identify what to revisit, rather than conceal the later learning material. Use exact integers and fractions throughout the assessed calculations.

## Learning route and rubric

| Problem | Idea to learn | Points |
| --- | --- | ---: |
| 1.1 | Telescoping and the declared cell carrier | 6 |
| 1.2 | Evaluate a proposal cost | 5 |
| 1.3 | Distinguish a fitted difference from a residual | 6 |
| 1.4 | Upper bounds and missing lower bounds | 7 |
| 2.1 | Balance and edge capacities | 7 |
| 2.2 | Prove weak duality | 12 |
| 2.3 | Verify a matching pair of witnesses | 7 |
| 2.4 | Preserve the quotient under a report shift | 6 |
| 2.5 | Construct a cycle optimum | 8 |
| 3.1 | Separate descent, fuel, and time bounds | 9 |
| 3.2 | Separate sparse existence, uniqueness, and gauge freedom | 12 |
| 3.3 | Exact enumeration and honest refusal | 7 |
| 3.4 | Read the scope of a formal theorem | 8 |
| Total | | 100 |

Award arithmetic credit for correct exact computations and proof credit for stated hypotheses and justified steps. For multi-part problems, divide the allotted points among the parts; put most of 2.2's points on the two justified equalities and the capacity inequality. The existing perfect-score tribunal seal can remain a game reward. A lower score should come with specific repairs and another attempt. The two final challenges are optional and unscored.

## Page 1 worked answers

### Problem 1.1

The report sum is $3$. Potential differences telescope around the cycle to $0$, so they cannot equal reports whose sum is $3$. No 2-cells are declared; $C^2=\{0\}$ has dimension $0$. Drawing the triangle does not fill it.

Hint for a stalled student: write $(s_b-s_a)+(s_c-s_b)+(s_a-s_c)$ before computing anything else.

### Problem 1.2

$Bs^{(0)}=(0,0,0)$, $r^{(0)}=(1,1,1)$, and $D_c(s^{(0)})=1+2+3=6$.

### Problem 1.3

$Bs^*=(-2,1,1)$, $r^*=(3,0,0)$, and $D_c(s^*)=1\cdot3+2\cdot0+3\cdot0=3$. The negative fitted difference on the first edge is allowed; it is the residual, not the potential sign, that incurs cost.

### Problem 1.4

The candidate proves $\Phi(c)\le3$. Failed heuristic searches provide no bound on unvisited potentials. For the requested independent certificate, exhibit a circulation $\lambda$ with $B^T\lambda=0$, $|\lambda_e|\le w_e$, and $\lambda^Tc=3$. The witness $(1,1,1)$ works. Together with the candidate, it proves $\Phi(c)=3$.

This examination asks for dual certificates. It should not teach that duality is the only possible proof: a complete exact enumeration with a proved search-set theorem can also establish a minimum.

## Page 2 worked answers

### Problem 2.1

At each vertex, incoming flow equals outgoing flow:

$$\sum_{e:u\to v}\lambda_e-\sum_{e:v\to u}\lambda_e=0.$$

Equivalently $B^T\lambda=0$. Each edge satisfies $-w_e\le\lambda_e\le w_e$. On a consistently oriented simple directed cycle, every vertex has one incoming and one outgoing edge, so consecutive flows are equal and $\lambda_e=\alpha$ everywhere. Capacity gives $|\alpha|\le\min_e w_e$.

### Problem 2.2

Let $r=c-Bs$. Since the dual is balanced,

$$\lambda^TBs=s^TB^T\lambda=0.$$

Consequently

$$\lambda^Tc=\lambda^T(c-Bs)=\sum_e\lambda_e r_e
\le\sum_e|\lambda_e|\,|r_e|
\le\sum_e w_e|r_e|=D_c(s).$$

This holds for every potential and every feasible dual. Therefore a feasible dual gives a lower bound, while a potential gives an upper bound. Equal bounds prove optimality using weak duality; no separate strong-duality invocation is needed for a supplied matching pair.

### Problem 2.3

The largest feasible constant $k$ is $1$, because the least capacity is $1$. Thus $\lambda^*=(1,1,1)$ is balanced and within all capacities. Its objective is $1+1+1=3$. The candidate also costs $3$, so the gap is $0$ and $\Phi(c)=3$. This certifies a minimum repair cost, not exact consistency of the original reports.

### Problem 2.4

$B\phi=(-3,6,-3)$, so $c'=(-2,7,-2)$ and the cycle sum remains $3$. Coboundary invariance gives $\Phi(c')=\Phi(c)=3$ for the same weights.

For an explicit matching pair, take $s'=s^*+\phi=(2,-3,4)$ and the unchanged dual $(1,1,1)$. The fitted differences are $(-5,7,-2)$, the residual is $(3,0,0)$, and both objectives equal $3$.

### Problem 2.5

For a consistently directed cycle,

$$\Phi(c)=\rho|h|,\qquad \rho=\min_e w_e,\quad h=\sum_e c_e.$$

Here $h=4-2+5+1=8$, $\rho=3$, and the bottleneck is $e_2$. Hence $\Phi(c)=24$.

To meet the certificate instruction, use potential $(s_{v_1},s_{v_2},s_{v_3},s_{v_4})=(0,4,-6,-1)$. It gives $Bs=(4,-10,5,1)$ and residual $(0,8,0,0)$, costing $24$. The constant circulation $(3,3,3,3)$ is feasible and has objective $3(8)=24$.

## Page 3 worked answers

### Problem 3.1

$D_t=2^{-t}$ and $D_{t+1}=D_t/2<D_t$. No finite $t$ has $D_t=0$. In fact the single edge admits an exact potential difference $1$, so the minimum is $0$; the chosen sequence merely fails to reach it.

The obligations are distinct:

| Obligation | Supplied mechanism | Limit |
| --- | --- | --- |
| Reject nondecreasing potential updates | Governor's `CUT` rule | Does not force a positive rational sequence to end |
| Bound attempted transitions | Demo 1's finite outer loop | The class itself has no fuel limit; `turn` is a counter |
| Bound a single external solver call | Native adapter's 30-second timeout | Does not time out the governor's in-process reference solver |

A finite fuel budget guarantees at most that many attempts when every attempt returns or times out. Exhaustion with a positive residual means unfinished work. A forest-count cap is a count bound, not an elapsed-time bound. A fixed cost lattice with a positive spacing and a lower bound can bound admitted strict descents, but rejected attempts and hanging calls still need limits.

### Problem 3.2

For a connected graph, $\operatorname{rank}B=n-1$, so **some** optimal residual has support at most $m-n+1=\beta_1$. This is an existence statement; a formulation in residual variables is needed when referring to a basic feasible LP solution.

The equal-weight triangle has multiple minimizers even after fixing $s_a=0$. For $(0,-2,-1)$, residual $(3,0,0)$ costs $6$. For $(0,1,-1)$, residual $(0,3,0)$ also costs $6$. Their potential difference is not constant. The circulation $(2,2,2)$ is feasible and has objective $6$, proving optimality and excluding a claimed minimum of $2$.

For $S=\operatorname{supp}(r^*)$, the sufficient weighted null-space condition is

$$\sum_{e\in S}w_e|z_e|<\sum_{e\notin S}w_e|z_e|
\quad\text{for every }0\ne z\in\operatorname{im}B.$$

Take $S=\{e_1\}$ and $z=B(0,1,0)=(1,-1,0)$. Both sides equal $2$, so the strict condition fails. The two exhibited optima prove nonuniqueness on this triangle. Failure of the sufficient condition **by itself** does not prove nonuniqueness for a particular residual; Challenge A gives a counterexample to that invalid converse.

Further check: the zero potential gives dense residual $(1,1,1)$, also optimal. The residual optimum set is $\{r\ge0:\sum r_i=3\}$, a two-dimensional simplex. Cycle rank $1$ does not bound every optimal support or the optimal-face dimension.

### Problem 3.3

$K_6$ has $6^4=1296$ spanning trees. $K_8$ has $8^6=262144$.

Source inspection shows that the Rust solver can check 100,000 complete forests, then returns `GraphPhi1Error::EnumerationLimit` when the next complete forest would exceed the cap. It returns neither an approximate value nor a partial minimum. If the adapter's separate timeout is reached first, the observed Python outcome is `NativeFunctionalTimeout`; the count alone does not guarantee when the Rust enumeration will finish.

A partial minimum is an upper bound over the examined candidates. Without exhaustion of the proved finite search set or an independent lower-bound witness, it cannot be labeled the global minimum. The response's count is a record of the solver's claimed work, not an independently checked proof of exhaustive execution.

### Problem 3.4

According to the manuscript, the local statements concern pair cancellation under supplied sign and weight hypotheses; impossibility of assigning triangle vertex signs making all three edge products $-1$; and a one-value policy type whose theorem holds by construction.

They do not imply a polynomial-time general graph algorithm, correctness of the Python or Rust production runtime, or a physical fermion sign-problem solution. They also do not imply termination of arbitrary rational descent or that the triangle theorem has been generalized to all odd cycles.

The narrow claim is that the named local files, when built with their pinned toolchain and documented axioms, check those local statements. The distributed package contains the Lean files in `lean4/`, whose clean build and axiom dependencies (`propext`, `Quot.sound`) are attested in `lean4/axiom_report.txt` and verified in `docs/release_validation_2026_10_02_review_repairs.json`.

For a physical bridge, specify the Hamiltonian and representation, the finite or continuous configuration carrier, and the mapping into cochains. Prove the precise relation between signs, weights, and the claimed observable or obstruction. A claimed algorithm also needs implementation correspondence and a complexity proof with a stated input encoding and cost model. A toy theorem, prose analogy, or file hash does not supply these steps.

## Final challenge hints and solutions

### Challenge A

Hint: when $|\lambda_e|<w_e$, equality in weak duality forces the residual on that edge to be zero. Ask whether those edges connect all vertices.

In edge order $ab,ac,ad,bc,bd,cd$, the zero potential has residual $(1,-1,0,0,0,0)$ and cost $2$. The proposed dual has zero divergence at every vertex, is within the unit capacities, and has objective $1(1)+(-1)(-1)=2$. Therefore the zero potential is optimal.

On $ad,bc,bd,cd$, the dual has strict capacity slack. Any optimum must therefore have zero residual on all four edges. Their reports are zero, so $s_a=s_d$, $s_b=s_c$, $s_b=s_d$, and $s_c=s_d$. The subgraph is connected; every potential is constant, and fixing $s_a=0$ makes the zero potential the unique optimum.

For $h=(1,0,0,0)$, $Bh=(-1,-1,-1,0,0,0)$. With $S=\{ab,ac\}$, the two weighted sums are $2$ and $1$; the sufficient condition fails. This does not contradict the theorem: the condition guarantees uniqueness for every residual on the support, while this particular signed residual is unique without satisfying that stronger condition.

### Challenge B

Hint: reject an inconsistent primal value before asking whether it is globally minimal.

The given potential has residual $(3,0,0)$ and cost $6$, so it disagrees with the claimed `phi1=2`. The feasible circulation $(2,2,2)$ has objective $6$, which also excludes a global minimum of $2$.

Require a JSON object with the documented status and result shape; integer or fraction strings for every rational; a gauge covering exactly the declared vertices; an integer forest count in the declared range, excluding Boolean values; nonnegative `phi1`; and equality between the reported value and the exactly recomputed weighted residual cost. Handle refusals, malformed replies, nonzero exits, and timeouts as typed failures, without substituting another solver's answer after a native failure.

Those consistency checks do not prove a lower bound or that enumeration really exhausted its search set. The caller still relies on the native implementation and its source-to-binary custody, or must check a feasible dual witness achieving the same value. The supplied native response has no dual. A hash can identify bytes; it does not prove this optimization theorem.

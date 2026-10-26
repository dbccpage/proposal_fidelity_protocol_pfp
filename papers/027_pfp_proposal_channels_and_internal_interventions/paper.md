<div align="center">

# PFP: Glyphs, rewrites, logits, and attention as checked proposal channels

Jeremy H. Carroll

2026-10-23

Version 0.8.0 — author-review extension

</div>

## Abstract

PFP can accept candidates from natural-language prompts, glyph games,
coloured-operad prompt decompositions, or model-internal logit and attention
interventions. These channels can change which candidates are proposed while
leaving the host's validity obligation fixed. We state and prove twelve finite
results governing this architecture: (1) channel-independent host checking
soundness, (2) on one directed cycle, the weighted bound attained by a
single-edge coordinate change of sum $-s$, which is not a coboundary when
$s \neq 0$ and which the claim ledger does not record as a coboundary repair,
(3) two-sided congruence-ideal absorption ($\mathbf{0}$ /
`NullTree`) in the quotient coloured operad of prompt trees, (4) BPE
prefix-automaton logit-mask viability with `F-null` token identity, (5) guarded
Stage-1 slot retry with `NullTree` abstention (admission rate, conditional
Stage-2 precision, and expected Stage-2 call savings), (6) the single-cycle
partial-guard visibility gap showing that omitting the global cycle-sum equation
leaves an infinite false-green kernel $\mathcal{K}_{\text{false}}(x) \cong \mathbb{Z} \setminus \{0\}$,
(7) triangular chord-induced cycle decoupling on multi-cycle graphs
($\dim H_1(G) = b_1 \ge 2$) with a rank-$(|V|-1+b_1)$ partial-guard visibility gap
$\mathcal{K}_{\text{false}}^{\text{C006}}(x) \cong \mathbb{Z}^{|V|-1+b_1} \setminus \{0\}$,
(8) two-stage tree-then-chord `P*` factorization reducing maximum per-turn
integer-slot arity on higher-Betti graphs ($b_1 \in \{4, \dots, 8\}$) from
$|V|-1+2 b_1$ to $\max(|V|-1, b_1)$ while closing the two-stage false-green
kernel, (9) elimination of the lazy false-refusal attractor on dichotomic
exactness-vs-holonomy verification (`C005`) via a Fredholm-alternative Stage-1
guard $G_{\text{Fredholm}}$, (10) cohomological syndrome decoding
$\mathbf{r}^* = S\mathbf{c}$ across `verdict`, single-edge `repair` (for both
chord and spanning-tree perturbations), and `audit` modes on distractor-filtered
4-digit rank-difference graphs (`C001`), (11) elimination of
tree-coboundary defect migration on retry via path-integrated $B_T^{-1}$ guard
diagnostics, and (12) independent exact certificate verification across all ten
cohomology challenges (`C011`–`C020`, `b_cohomology`) closing the status-label
false-`SOLVED` kernel. For historical context, we retain unverified summaries of six bounded paired C004 mechanism trials
(including the held-out 40-case ladder `C004-S6` across $k \in \{3, \dots, 12\}$),
three bounded paired C006 multi-cycle trials ($K_4$ at $b_1 = 3$, higher-Betti
$K_{3,3}, Q_3, K_5, \text{Petersen}, W_7$ at $b_1 \in \{4, 5, 6, 7\}$, and the
held-out 60-board multi-cycle campaign `C006-S8` at $b_1 \in \{3, \dots, 8\}$),
one bounded paired C005 dichotomic Fredholm trial (`pub_cons_01`..`pub_cons_08`),
one bounded paired C001 distractor-filtered syndrome trial (`12` public and
adversarial poisoned cases across `verdict`, `repair`, and `audit`,
$b_1 \in \{5, 7\}$), and one multi-stage `P*` cohomology certificate campaign
(`B-COH-S1` across `C011`–`C020`) across a pinned local checkpoint
(`Qwen/Qwen2.5-0.5B-Instruct`, rev `7ae557604adf67be50417f59c2c2f167def9a775`)
and accounted OpenRouter (`openai/gpt-4o-mini` and `qwen/qwen-2.5-7b-instruct`),
together with an accounted Anthropic `claude-fable-5-1` theorem-derivation
receipt (`msg_011Cg74HxZqarY627LKcRzQa`).

The historical model-receipt files are unavailable in this revision. Their
reported counts are not revalidated evidence. The finite examples and the new
harness protocol have separate checks; the new paid campaign is NOT_RUN.

## Mechanism inventory

| Mechanism | Evidence |
| --- | --- |
| Mathematical statements (Theorems 1–3, Proposition 4, Theorems 5–12) | Written proofs under declared finite hypotheses + accounted `claude-fable-5-1` derivation (`fable_5_1_guard_theorem_receipt.json`) |
| Finite example & theorem checks | Standard-library replay (`code/replay.py`) of glyph round trips, single-cycle and $K_4$ / higher-Betti ($b_1 \in \{4..8\}$) cochain duality, operad `NullTree` absorption, BPE prefix-automaton states, partial- vs. complete-guard kernel checks, dichotomic Fredholm-alternative guard closure, C001 cohomological syndrome decoding $\mathbf{r}^* = S\mathbf{c}$, path-integrated $B_T^{-1}$ vs. edge-local $B_T$ retry diagnostics, and `b_cohomology` (`C011`–`C020`) independent exact certificate verification |
| Bounded C001, C004, C005, C006 & `b_cohomology` (`C011`–`C020`) mechanism trials (Panel 1 local + Panel 2 OpenRouter + Anthropic `claude-fable-5-1`) | Thirteen committed JSON receipts replayed offline with zero network calls (`c004_paired_benchmark_receipt.json`, `operad_cochain_ablation_receipt.json`, `p_star_operad_materialization_receipt.json`, `p_star_4slot_binding_receipt.json`, `p_star_verified_guard_receipt.json`, `fable_5_1_guard_theorem_receipt.json`, `c004_40case_hidden_p_star_receipt.json`, `c006_overlap_basis_p_star_receipt.json`, `c006_higher_betti_p_star_receipt.json`, `c006_60board_hidden_p_star_receipt.json`, `c005_dichotomic_fredholm_p_star_receipt.json`, `c001_distractor_cochain_p_star_receipt.json`, `b_cohomology_p_star_receipt.json`) |
| Lean verification | No new formalization claimed in this draft |
| Authorization | None supplied |

## 1. Proposal channels and the Three-Layer PFP host boundary

Fix a finite task $P$, a candidate language $W$, a solution relation $R(P,w)$,
and a deterministic host checker $C$. A proposal channel $\mu$ is any
distribution on raw messages produced by a prompt template, a multi-turn staged
protocol, a local logit mask, or an external model provider. A separately
supplied decoder maps well-formed messages to $W$ and refuses malformed
messages. The host replays the decoded witness against the original task $P$.

In the Omega Engine PFP runtime, this separation is organized into three
non-collapsing layers:

1. **Layer 1 (Compositional Prompt Operad):** Typed prompt assembly and
   slot-grafting ($\circ_i$) over immutable source spans and congruence ideals.
2. **Layer 2 (Token-Frontier Grammar Projection):** BPE prefix-automaton logit
   masking (`gbnf_slots=k`) or strict response-schema projection restricting
   surface emission to a regular language $\mathcal{L}_k \subset \Sigma^*$.
3. **Layer 3 (Independent Host Cochain & Domain Oracles):** Exact rational
   cochain evaluation ($\Phi_1, \Gamma_2$) and independent domain judges that
   certify or refuse the decoded candidate without consulting the proposal
   channel's internal scores.

## 2. Theorem 1: Channel-independent host checking soundness

**Theorem 1 (Channel-Independent Soundness).** Let $D: \Sigma^* \rightharpoonup W$
be a partial decoder that binds every admitted raw reply $m \in \Sigma^*$ to
the fixed task $P$, and suppose the host checker $C: \{P\} \times W \to
\{\mathsf{accept}, \mathsf{refuse}\}$ satisfies the soundness implication
$$C(P, w) = \mathsf{accept} \implies R(P, w).$$
Then for every proposal channel $\mu$ on $\Sigma^*$, the event of an accepted
invalid candidate is empty:
$$\{m \in \Sigma^* : D(m) = w \text{ is defined},\; C(P, w) = \mathsf{accept},\; \neg R(P, w)\} = \emptyset,$$
and therefore has probability zero under $\mu$. No acceptance-rate lower bound
or search-completeness guarantee follows from soundness alone.

**Proof.** Fix any raw message $m \in \Sigma^*$ accepted by the host pipeline.
By definition of admission, $w = D(m) \in W$ is defined and bound to $P$, and
$C(P, w) = \mathsf{accept}$. By the soundness hypothesis on $C$, $R(P, w)$
holds. Because the deduction is pointwise in $m$ and does not reference $\mu$,
no message $m$ can simultaneously satisfy $C(P, D(m)) = \mathsf{accept}$ and
$\neg R(P, D(m))$. Thus the bad set is empty and $\mu(\emptyset) = 0$ for every
probability measure or empirical run $\mu$. Conversely, a channel $\mu$
concentrating all mass on a single malformed string $m_0 \notin \operatorname{dom}(D)$
satisfies Theorem 1 vacuously with zero accepted solutions, demonstrating that
validity and search success are independent obligations. $\square$

## 3. Exact glyph transport

For the Boolean task $x+y=1$, encode $(x,y)$ by the string `<xy>`. The four
domain values have four distinct strings: `<00>`, `<01>`, `<10>`, `<11>`.
The decoder checks the brackets, length, and binary digits; it is inverse to
the encoder on this declared domain. Hence checking a decoded string and
checking its assignment are the same mathematical obligation. The strings
use only a subset of A–Z, 0–9, and angle brackets.

More generally, a finite domain admits an injective finite-word code with a
declared partial inverse. Proof is by indexing its elements and assigning
distinct fixed-length binary words (with a separate empty-domain case).
This is representation capacity. It does not show that an LLM can recover
the desired word, solve every encoded question, or supply a missing domain
interpretation. The typed prompt and required response matter because they
fix that interpretation and the host's checking obligation.

## 4. Theorem 2: Exact prompt-to-cochain duality and single-cycle lightest-edge $\ell_1$ projection

When a prompt task specifies local edge transitions or consistency claims across
a finite 2-dimensional cell complex $(V, E, F)$ over $\mathbb{Q}$, the host
evaluates the candidate claim vector $c \in C^1 = \mathbb{Q}^E$ through the
cochain complex
$$C^0 = \mathbb{Q}^V \xrightarrow{d_0} C^1 = \mathbb{Q}^E \xrightarrow{d_1} C^2 = \mathbb{Q}^F, \qquad d_1 \circ d_0 = 0,$$
where $(d_0 a)_{(u,v)} = a_v - a_u$ for node potentials $a \in \mathbb{Q}^V$,
and $(d_1 c)_f = \sum_{e \in \partial f} \sigma_{f,e} c_e$ is the oriented cycle
holonomy around 2-cell $f \in F$. Define the coboundary compatibility residual
and the curvature residual by
$$\Phi_1(c) := \min_{a \in \mathbb{Q}^V} \|c - d_0 a\|_1, \qquad \Gamma_2(c) := \|d_1 c\|_1.$$

**Theorem 2 (Single-Cycle Exact Coboundary Duality & Weighted $\ell_1$ Repair).**
Let $G = (V, E, F)$ be a single directed $k$-cycle ($k \ge 3$) with vertices
$v_0, \dots, v_{k-1}$, directed edges $e_i = (v_i \to v_{(i+1) \bmod k})$, a
single oriented $k$-gon face $f_0$, edge claims $c \in \mathbb{Q}^k$, positive
edge weights $w \in \mathbb{Q}_{>0}^k$, and cycle holonomy sum
$s := (d_1 c)_{f_0} = \sum_{i=0}^{k-1} c_i$. Then:

1. **Exactness and $\ell_1$ Duality:** $\operatorname{im}(d_0) = \ker(d_1) =
   \{c' \in \mathbb{Q}^k : \sum_{i=0}^{k-1} c'_i = 0\}$, and
   $$\Phi_1(c) = \Gamma_2(c) = |s| = \max_{z \in \mathbb{Q}^k : \partial_1 z = 0,\, \|z\|_\infty \le 1} \langle z, c \rangle.$$
   Whenever $\sum_{i=0}^{k-1} c'_i = 0$, the node potential $a \in \mathbb{Q}^k$
   defined by $a_0 = 0$ and $a_m = \sum_{j=0}^{m-1} c'_j$ ($1 \le m < k$)
   satisfies $d_0 a = c'$ identically.
2. **Weighted $\ell_1$-Optimal Repair:** For any repaired cochain $c' = c + \Delta$
   satisfying $d_1 c' = 0$ (equivalently $\sum_{i=0}^{k-1} \Delta_i = -s$), the
   weighted modification cost satisfies the lower bound
   $$\|c' - c\|_{1,w} := \sum_{i=0}^{k-1} w_i |\Delta_i| \ge w_{\min} |s|, \qquad w_{\min} := \min_{0 \le i < k} w_i.$$
   Equality is attained by the single-edge coordinate change at any lightest
   edge $i^* \in \arg\min_i w_i$:
   $$c'_i = \begin{cases} c_{i^*} - s & \text{if } i = i^*, \\ c_i & \text{if } i \ne i^*, \end{cases}$$
   The coordinate sum of that change is $-s$. When $s \neq 0$ the change is not
   a coboundary; the repaired cochain is. The claim ledger does not record this
   coordinate change as a coboundary repair, and retained empirical assertions
   are not revalidated. The dual circulation witness is
   $z^* = \operatorname{sgn}(s) w_{\min} \mathbf{1} \in \ker(\partial_1)$.

**Proof.**
(1) Since $e_i = (v_i \to v_{(i+1)\bmod k})$, every telescopic sum around the
cycle yields $\sum_{i=0}^{k-1} (d_0 a)_i = \sum_{i=0}^{k-1} (a_{(i+1)\bmod k} - a_i) = 0$,
so $d_1 d_0 = 0$ and $\operatorname{im}(d_0) \subseteq \ker(d_1)$. Conversely,
if $\sum_{i=0}^{k-1} c'_i = 0$, setting $a_0 = 0$ and $a_m = \sum_{j=0}^{m-1} c'_j$
gives $a_{m+1} - a_m = c'_m$ for $0 \le m < k-1$ and $a_0 - a_{k-1} = -\sum_{j=0}^{k-2} c'_j = c'_{k-1}$,
so $d_0 a = c'$. For any $a \in \mathbb{Q}^k$, the triangle inequality gives
$$\|c - d_0 a\|_1 = \sum_{i=0}^{k-1} |c_i - (d_0 a)_i| \ge \left|\sum_{i=0}^{k-1} (c_i - (d_0 a)_i)\right| = |s|,$$
and subtracting $s$ from a single edge achieves $\|c - d_0 a\|_1 = |s|$ using
the potential $a$ of the resulting zero-sum vector. The dual cycle space
$\ker(\partial_1) = \{z \in \mathbb{Q}^k : z_0 = z_1 = \dots = z_{k-1}\}$ is
spanned by $\mathbf{1}$, so $\max_{\partial_1 z = 0, \|z\|_\infty \le 1} \langle z, c \rangle = \max_{\alpha \in [-1,1]} \alpha s = |s|$.

(2) For any $\Delta \in \mathbb{Q}^k$ with $\sum_{i=0}^{k-1} \Delta_i = -s$,
$$\sum_{i=0}^{k-1} w_i |\Delta_i| \ge w_{\min} \sum_{i=0}^{k-1} |\Delta_i| \ge w_{\min} \left|\sum_{i=0}^{k-1} \Delta_i\right| = w_{\min} |s|.$$
Setting $\Delta_{i^*} = -s$ and $\Delta_j = 0$ ($j \ne i^*$) satisfies
$\sum_i (c_i + \Delta_i) = s - s = 0$ and achieves $\sum_i w_i |\Delta_i| = w_{i^*} |s| = w_{\min} |s|$. $\square$

## 5. Theorem 3 & Proposition 4: Coloured operad ideal absorption and BPE prefix-automaton projection

### 5.1 Theorem 3: Coloured operad quotient and two-sided `NullTree` absorption

Let $\mathcal{C}$ be the finite set of prompt semantic colours
(`RawTextSpan`, `IsolatedVariable`, `Equation`, `SubstitutionStep`,
`RationalValue`, `InvariantWitness`, `TargetResult`), and let $\mathcal{O}$ be
the free $\mathcal{C}$-coloured operad of syntax trees generated by typed
$n$-ary operators $f \in \mathcal{O}^+(c_1, \dots, c_n; c_{\text{out}})$ and
leaf spans $[i, j]$ extracted from a source document $D$. Let $\mathcal{I} \subset \mathcal{O}$
be the subset of trees containing any of the following defects:
(i) a non-exact or boolean-coerced numeric value (`IDEAL_RATIONAL_DOMAIN`),
(ii) a leaf span whose content or SHA-256 digest does not match $D[i:j]$
(`IDEAL_SPAN_IMMUTABILITY`),
(iii) a slot-grafting operation $f \circ_m g$ whose child output colour
$\operatorname{out}(g)$ does not equal the $m$-th input colour $\operatorname{in}_m(f)$
or whose slot index $m \notin \{0, \dots, \operatorname{arity}(f)-1\}$, or
(iv) a candidate binding neutralized by an active `AnnihilatorDecoy` witness
($\mathcal{O}^-$).

**Theorem 3 (Two-Sided Ideal Absorption in $\mathcal{O} / \mathcal{I}$).**
The subset $\mathcal{I}$ is a two-sided operad ideal: for every tree
$t \in \mathcal{I}$ and every tree $u \in \mathcal{O}$, both $u \circ_m t \in \mathcal{I}$
and $t \circ_m u \in \mathcal{I}$. Consequently, the quotient coloured operad
$\mathcal{O} / \mathcal{I} := (\mathcal{O} \setminus \mathcal{I}) \sqcup \{\mathbf{0}\}$
with distinguished null element $\mathbf{0}$ (`NullTree`) satisfies the
two-sided absorption law
$$f \circ_m \mathbf{0} = \mathbf{0}, \qquad \mathbf{0} \circ_m g = \mathbf{0},$$
and any composite tree $T \in \mathcal{O} / \mathcal{I}$ satisfies $T \ne \mathbf{0}$
if and only if every leaf span is byte-identical to its declared slice in $D$,
every parameter belongs to $\mathbb{Q}$, every internal graft matches its
declared colour signature, and no active decoy witness is triggered.

**Proof.** By induction on tree depth. A single leaf or operator violation
places the local node in $\mathcal{I}$, which projects to $\mathbf{0} \in \mathcal{O} / \mathcal{I}$.
Because containing a defect in $\mathcal{I}$ is hereditary under subtree
inclusion—if a subtree $t$ contains a malformed span, non-rational parameter, or
colour mismatch, then any larger tree $u \circ_m t$ or $t \circ_m u$ containing
$t$ also contains that defect—$\mathcal{I}$ is closed under both left and right
partial composition $\circ_m$. Collapsing $\mathcal{I}$ to a single point
$\mathbf{0}$ therefore makes $\circ_m$ well-defined on $\mathcal{O} / \mathcal{I}$
with $f \circ_m \mathbf{0} = \mathbf{0}$ and $\mathbf{0} \circ_m g = \mathbf{0}$. $\square$

### 5.2 Proposition 4: BPE prefix-automaton logit mask viability and `F-null` identity

Let $\mathcal{L}_k \subset \Sigma^*$ be the regular language of $k$
space-separated signed ASCII integers (`integer_slots_gbnf(k)`):
$$\mathcal{L}_k = \left\{ w_1 \mathbin{\Vert} \text{\texttt{" "}} \mathbin{\Vert} w_2 \mathbin{\Vert} \dots \mathbin{\Vert} \text{\texttt{" "}} \mathbin{\Vert} w_k \;\middle|\; w_j \in \{\text{\texttt{"0"}}\} \cup (\{\varepsilon, \text{\texttt{"-"}}\} \cdot \{\text{\texttt{1..9}}\} \cdot \{\text{\texttt{0..9}}\}^*) \right\},$$
and let $\operatorname{Pref}(\mathcal{L}_k) = \{u \in \Sigma^* : \exists v \in \Sigma^*,\; u \mathbin{\Vert} v \in \mathcal{L}_k\}$
be its set of viable prefixes, recognized by the six-component prefix-state DFA
$\delta_{\text{DFA}}(u) = (\text{viable}, \text{complete}, \text{slots\_seen}, \text{in\_number}, \text{after\_minus}, \text{after\_zero})$.

**Proposition 4 (BPE Token-Frontier Projection & `F-null` Identity).**
For any BPE tokenizer vocabulary $V \subset \Sigma^+$ with end-of-sequence token
$\tau_{\text{eos}} \notin V$ and any viable prefix $S_t \in \operatorname{Pref}(\mathcal{L}_k)$
at generation step $t$, define the admissible token frontier
$$V_{\text{valid}}(S_t) := \{\tau \in V : S_t \mathbin{\Vert} \tau \in \operatorname{Pref}(\mathcal{L}_k)\} \cup \{\tau_{\text{eos}} : S_t \in \mathcal{L}_k\},$$
and define the masked logit vector $\tilde{\ell}^{(t)}_v = \ell^{(t)}_v$ if
$v \in V_{\text{valid}}(S_t)$ and $-\infty$ otherwise. Then:

1. **Prefix Viability & Complete-Word Soundness:** If $S_0 = \varepsilon$ and at
   each step $t < T$ the sampled token $\tau_t$ has finite masked logit
   ($\tau_t \in V_{\text{valid}}(S_t)$), then $S_t \in \operatorname{Pref}(\mathcal{L}_k)$
   for all $t \ge 0$, and if generation terminates via $\tau_T = \tau_{\text{eos}}$,
   then $S_T \in \mathcal{L}_k$ (`parse_integer_slots(S_T, k)` succeeds).
2. **BPE Multi-Character Boundary Completeness:** A merged BPE token $\tau \in V$
   spanning a slot boundary (such as $\tau = \text{\texttt{" -"}}\text{ or }\text{\texttt{" 12"}}$)
   belongs to $V_{\text{valid}}(S_t)$ whenever $S_t$ ends a valid integer slot
   with $\text{slots\_seen}(S_t) < k$, because $\delta_{\text{DFA}}(S_t \mathbin{\Vert} \tau)$
   transitions across the space character and opens slot $\text{slots\_seen}(S_t) + 1$.
3. **`F-null` Token Identity:** When the logit processor is instantiated with
   the full vocabulary frontier $V_{\text{valid}}^{\text{null}}(S_t) = V \cup \{\tau_{\text{eos}}\}$,
   $\tilde{\ell}^{(t)} = \ell^{(t)}$ at every step $t$, so greedy or
   fixed-seed decoding produces a token sequence identical to unhooked decoding.

**Proof.** (1) follows by induction on $t$: $S_0 = \varepsilon \in \operatorname{Pref}(\mathcal{L}_k)$,
and $\tau_t \in V_{\text{valid}}(S_t) \setminus \{\tau_{\text{eos}}\}$ implies
$S_{t+1} = S_t \mathbin{\Vert} \tau_t \in \operatorname{Pref}(\mathcal{L}_k)$ by
definition of $V_{\text{valid}}(S_t)$, while $\tau_{\text{eos}} \in V_{\text{valid}}(S_T)$
holds if and only if $S_T \in \mathcal{L}_k$. (2) follows because
$\delta_{\text{DFA}}$ advances character-by-character over the concatenation
$S_t \mathbin{\Vert} \tau$: after a completed slot $m < k$, `' '` transitions to
$(\text{slots\_seen}=m, \text{in\_number}=\mathsf{false})$, and `'-'` then
transitions to $(\text{slots\_seen}=m+1, \text{in\_number}=\mathsf{true}, \text{after\_minus}=\mathsf{true})$,
which is a viable prefix of $\mathcal{L}_k$. (3) is immediate because adding $0$
to every coordinate of $\ell^{(t)}$ leaves $\arg\max_v \ell^{(t)}_v$ and
$\operatorname{softmax}(\ell^{(t)})$ invariant. $\square$

### 5.3 Theorem 5: Guarded Stage-1 slot retry with `NullTree` abstention

Consider a 2-stage `P*` operad pipeline $X \xrightarrow{f_1} Z_1 \xrightarrow{f_2 \circ_i z_1} Y$
where Stage 1 proposes a 4-slot invariant tuple $z_1 = (\hat{s}, \hat{i}^*, \hat{c}_{i^*}, \hat{c}'_{i^*}) \in \mathbb{Z}^4$
for a directed $k$-cycle $x = (c, w)$ with unique canonical truth tuple
$$z_1^*(x) = \left(s(c),\; i^*(w),\; c_{i^*},\; c_{i^*} - s(c)\right), \qquad i^*(w) := \min \arg\min_{0 \le j < k} w_j.$$
Let $G_1: \mathcal{X} \times \mathbb{Z}^4 \to \{0, 1\}$ be a deterministic Stage-1
host guard, let $\pi_{\mathcal{I}}$ project any rejected Stage-1 output
($G_1(x, z_1) = 0$) to `NullTree` ($\mathbf{0}$), and let $R \ge 1$ be a bounded
Stage-1 retry cap (1 initial attempt + at most $R - 1$ diagnostic retries).

**Theorem 5 (Guarded Stage-1 Slot Retry with Ideal Abstention — derived with `claude-fable-5-1`, `msg_011Cg74HxZqarY627LKcRzQa`).**
Suppose the Stage-1 guard $G_1$ is sound and complete for $z_1^*(x)$, meaning
$G_1(x, z_1) = 1 \iff z_1 = z_1^*(x)$. Let $p_1(x) := \mathbb{P}(Z_1^{(1)} = z_1^*(x) \mid x)$
be the Attempt-1 exact Stage-1 probability, and under the conditional
independence assumption that each diagnostic retry $r \in \{2, \dots, R\}$ given
prior failure succeeds with probability $p_{1,\text{retry}}(x) := \mathbb{P}(Z_1^{(r)} = z_1^*(x) \mid x, G_1(x, Z_1^{(r-1)}) = 0)$,
let $p_2(y^* \mid x, z_1)$ denote the Stage-2 probability of emitting the exact
$\ell_1$-optimal cochain repair $y^*(x)$ when $z_1$ is grafted into $f_2$. Then:

1. **Stage-1 Admission Probability:** The probability that Stage 1 is admitted to
   Stage 2 within $R$ bounded attempts is
   $$q_{G_1, R}(x) = 1 - (1 - p_1(x))\bigl(1 - p_{1,\text{retry}}(x)\bigr)^{R-1}.$$
2. **Admission-Conditional Stage-2 Precision:** Because $G_1(x, z_1) = 1 \iff z_1 = z_1^*(x)$
   and $\pi_{\mathcal{I}}$ absorbs all $G_1 = 0$ terminations into `NullTree`
   ($f_2 \circ_i \mathbf{0} = \mathbf{0}$ by Theorem 3), conditioning on Stage-2
   admission eliminates all corrupted Stage-1 grafts:
   $$\mathbb{P}_{\text{ver}, R}\!\left(Y = y^*(x) \;\middle|\; x,\, \text{Stage 2 admitted}\right) = p_2\!\left(y^*(x) \;\middle|\; x,\, z_1^*(x)\right).$$
3. **Unconditional Exact Repair Rate vs. Unverified Grafting:** Under unverified
   1-shot grafting ($R=1$, no guard), the unconditional optimal repair rate is
   $$\mathbb{P}_{\text{unv}}(Y = y^*(x) \mid x) = p_1(x)\,p_2(y^*(x) \mid x, z_1^*(x)) + \sum_{z_1 \ne z_1^*(x)} \mathbb{P}(Z_1 = z_1 \mid x)\,p_2(y^*(x) \mid x, z_1),$$
   whereas under guarded retry with `NullTree` abstention,
   $$\mathbb{P}_{\text{ver}, R}(Y = y^*(x) \mid x) = q_{G_1, R}(x)\,p_2(y^*(x) \mid x, z_1^*(x)).$$
   In particular, whenever $p_2(y^*(x) \mid x, z_1) = 0$ for all corrupted
   tuples $z_1 \ne z_1^*(x)$ (faithful Stage-2 slot substitution), guarded retry
   improves unconditional optimal repair by the exact gain
   $$\mathbb{P}_{\text{ver}, R}(Y = y^*(x) \mid x) - \mathbb{P}_{\text{unv}}(Y = y^*(x) \mid x) = (1 - p_1(x))\!\left[1 - \bigl(1 - p_{1,\text{retry}}(x)\bigr)^{R-1}\right] p_2(y^*(x) \mid x, z_1^*(x)) \ge 0.$$
4. **Expected Stage-2 Call Savings:** If a Stage-2 call costs $c_2 > 0$,
   `NullTree` abstention on persistent Stage-1 guard failure saves
   $$\mathbb{E}[\Delta C_2 \mid x] = \bigl(1 - q_{G_1, R}(x)\bigr)\,c_2$$
   in expected Stage-2 expenditure compared to unverified Stage-2 dispatch.

**Proof.** (1) Stage 1 fails admission across all $R$ attempts if and only if
Attempt 1 fails ($1 - p_1(x)$) and each of the $R - 1$ retries fails
($(1 - p_{1,\text{retry}}(x))^{R-1}$); taking the complement gives $q_{G_1, R}(x)$.
(2) On the event of Stage-2 admission, the admitted tuple $\hat{z}_1$ satisfies
$G_1(x, \hat{z}_1) = 1$, which by soundness and completeness of $G_1$ implies
$\hat{z}_1 = z_1^*(x)$ deterministically; thus the Stage-2 law conditioned on
admission is $p_2(\cdot \mid x, z_1^*(x))$. (3) follows by the law of total
probability over $z_1 \in \mathbb{Z}^4$ and substituting $q_{G_1, R}(x) - p_1(x) = (1 - p_1(x))[1 - (1 - p_{1,\text{retry}}(x))^{R-1}]$.
(4) Unverified grafting dispatches Stage 2 with probability $1$, whereas guarded
grafting dispatches Stage 2 with probability $q_{G_1, R}(x)$ and projects the
remaining $1 - q_{G_1, R}(x)$ mass to `NullTree` at zero Stage-2 cost. $\square$

### 5.4 Theorem 6: Partial-guard visibility gap and false-green kernel $\mathcal{K}_{\text{false}}(x) \cong \mathbb{Z} \setminus \{0\}$

Suppose a Stage-1 guard checks only the **local** slot invariants on
$z_1 = (\hat{s}, \hat{i}^*, \hat{c}_{i^*}, \hat{c}'_{i^*}) \in \mathbb{Z}^4$—namely
canonical minimum-weight index selection, exact edge-claim lookup, and the
linear subtraction relation—without checking the global cycle-sum equation
$\hat{s} = \sum_{j=0}^{k-1} c_j$:
$$G_{\text{partial}}(x, z_1) = 1 \iff \Bigl(\hat{i}^* = i^*(w)\Bigr) \;\wedge\; \Bigl(\hat{c}_{i^*} = c_{\hat{i}^*}\Bigr) \;\wedge\; \Bigl(\hat{c}'_{i^*} + \hat{s} = \hat{c}_{i^*}\Bigr),$$
whereas the **complete** guard adjoins the global cycle-sum check:
$$G_{\text{complete}}(x, z_1) = 1 \iff G_{\text{partial}}(x, z_1) = 1 \;\wedge\; \left(\hat{s} = \sum_{j=0}^{k-1} c_j\right).$$

**Theorem 6 (Partial-Guard Visibility Gap & False-Green Kernel — derived with `claude-fable-5-1`, `msg_011Cg74HxZqarY627LKcRzQa`).**
For every directed $k$-cycle $x = (c, w)$:

1. **Infinite False-Green Kernel under $G_{\text{partial}}$:** The set of false-green
   Stage-1 tuples admitted by $G_{\text{partial}}$ is
   $$\mathcal{K}_{\text{false}}(x) := \left\{z_1 \in \mathbb{Z}^4 : G_{\text{partial}}(x, z_1) = 1 \;\wedge\; z_1 \ne z_1^*(x)\right\} \cong \mathbb{Z} \setminus \{0\},$$
   parameterized bijectively by the non-zero cycle-sum error $\Delta s := \hat{s} - s(c) \in \mathbb{Z} \setminus \{0\}$ via
   $$z_1(\Delta s) = \left(s(c) + \Delta s,\; i^*(w),\; c_{i^*},\; c_{i^*} - s(c) - \Delta s\right).$$
2. **Induced Stage-2 Cochain Residual (Local Green / Global Red):** If Stage 2
   substitutes a false-green tuple $z_1(\Delta s) \in \mathcal{K}_{\text{false}}(x)$
   into edge $i^* = i^*(w)$ while preserving $c'_j = c_j$ for $j \ne i^*$, the
   resulting Stage-2 edge cochain $c'(\Delta s)$ has non-zero cycle holonomy
   $$\sum_{j=0}^{k-1} c'_j(\Delta s) = -\Delta s \ne 0, \qquad \Gamma_2\bigl(c'(\Delta s)\bigr) = |\Delta s| > 0, \qquad \Phi_{1, w}\bigl(c'(\Delta s)\bigr) = w_{i^*}|\Delta s| > 0,$$
   and is therefore rejected by the Layer-3 cochain verifier as
   `NonClosedEdgeData` / `ClosedNonExactClass`.
3. **Kernel Closure under $G_{\text{complete}}$:** Adjoining $\hat{s} = \sum_{j=0}^{k-1} c_j$
   forces $\Delta s = 0$, collapsing the false-green kernel to the empty set
   ($\mathcal{K}_{\text{false}}^{\text{complete}}(x) = \emptyset$) and making
   $G_{\text{complete}}(x, z_1) = 1 \iff z_1 = z_1^*(x)$.

**Proof.** (1) Any $z_1 = (\hat{s}, \hat{i}^*, \hat{c}_{i^*}, \hat{c}'_{i^*}) \in \mathbb{Z}^4$
satisfying $G_{\text{partial}}(x, z_1) = 1$ has $\hat{i}^* = i^*(w)$ and
$\hat{c}_{i^*} = c_{i^*}$ uniquely fixed, while $\hat{c}'_{i^*} = c_{i^*} - \hat{s}$
is uniquely determined by $\hat{s} \in \mathbb{Z}$. Setting $\Delta s = \hat{s} - s(c) \in \mathbb{Z}$
gives the bijection $\Delta s \mapsto z_1(\Delta s)$, with $\Delta s = 0 \iff z_1 = z_1^*(x)$.
(2) Substituting $c'_{i^*} = c_{i^*} - s(c) - \Delta s$ into $c$ yields cycle sum
$\sum_{j \ne i^*} c_j + (c_{i^*} - s(c) - \Delta s) = s(c) - s(c) - \Delta s = -\Delta s \ne 0$,
so Theorem 2 gives $\Gamma_2(c'(\Delta s)) = |\Delta s| > 0$ and
$\Phi_{1,w}(c'(\Delta s)) = w_{i^*}|\Delta s| > 0$. (3) Adding $\hat{s} = s(c)$
forces $\Delta s = 0$. $\square$

### 5.5 Theorem 7: Triangular chord-induced cycle decoupling and multi-cycle partial-guard visibility gap $\mathcal{K}_{\text{false}}^{\text{C006}}(x) \cong \mathbb{Z}^{|V|-1+b_1} \setminus \{0\}$

Let $G = (V, E)$ be a finite connected directed graph with $|V|$ vertices,
$|E|$ edges, spanning tree $T \subset E$ ($|T| = |V| - 1$) rooted at $v_0 \in V$,
and first Betti number $b_1 := \dim H_1(G; \mathbb{Q}) = |E \setminus T| \ge 2$
chords $g_1, \dots, g_{b_1} \in E \setminus T$, where $g_m = (u_m \to v_m)$.
Each chord $g_m$ closes a unique chord-induced oriented cycle $\gamma_m$ whose
support lies in $T \cup \{g_m\}$ with $+1$ orientation on $g_m$ and signed tree
path $-\pi_T(u_m \to v_m)$, even when multiple cycles $\gamma_1, \dots, \gamma_{b_1}$
share high-incidence tree edges $e_{\text{shared}} \in T$ (for example, on
$K_4$ with a non-star spanning tree $T$, $|V|=4, |E|=6, b_1=3$, and a shared
tree edge traversed by all $3$ chord-induced cycles).

For any edge claim vector $c \in \mathbb{Z}^E$, define the unique tree-integrated
vertex potential $p_T^* \in \mathbb{Z}^V$ by $p_T^*(v_0) = 0$ and
$p_T^*(v) - p_T^*(u) = c_{(u,v)}$ for every tree edge $(u,v) \in T$, and define
the canonical Stage-1 $(|V|-1+2 b_1)$-slot tuple ($9$ slots on $K_4$) in causal
dependency order:
$$z_1^*(x) := \Bigl(\bigl(p_T^*(v_j)\bigr)_{j=1}^{|V|-1},\; \bigl(c_{g_m}^{\prime *}\bigr)_{m=1}^{b_1},\; \bigl(r_m^*\bigr)_{m=1}^{b_1}\Bigr) \in \mathbb{Z}^{|V|-1+2 b_1},$$
where $c_{g_m}^{\prime *} := p_T^*(v_m) - p_T^*(u_m)$ and
$r_m^* := \sum_{e \in \gamma_m} \sigma_{m,e} c_e = c_{g_m} - c_{g_m}^{\prime *}$.
Compare the **partial chord-subtraction guard**
$$G_{\text{partial}}^{\text{C006}}(x, z_1) = 1 \iff \bigwedge_{m=1}^{b_1} \left(\hat{c}'_{g_m} + \hat{r}_m = c_{g_m}\right)$$
against the **complete triangular-basis guard**
$$G_{\text{complete}}^{\text{C006}}(x, z_1) = 1 \iff \bigwedge_{(u,v) \in T} \bigl(\hat{p}(v) - \hat{p}(u) = c_{(u,v)}\bigr) \;\wedge\; \bigwedge_{m=1}^{b_1} \bigl(\hat{c}'_{g_m} = \hat{p}(v_m) - \hat{p}(u_m)\bigr) \;\wedge\; \bigwedge_{m=1}^{b_1} \bigl(\hat{c}'_{g_m} + \hat{r}_m = c_{g_m}\bigr).$$

**Theorem 7 (Triangular Chord-Induced Cycle Decoupling & Multi-Cycle Visibility Gap).**
For every connected graph $G = (V, E)$ with spanning tree $T$ and $b_1 = |E \setminus T| \ge 2$ chords:

1. **Exact Triangular Chord Decoupling:** The cycle-chord incidence matrix of the
   chord-induced cycle basis $\{\gamma_1, \dots, \gamma_{b_1}\}$ restricted to
   the chord coordinates $\{g_1, \dots, g_{b_1}\} = E \setminus T$ is the
   $b_1 \times b_1$ identity matrix $I_{b_1}$ ($\sigma_{m, g_\ell} = \delta_{m,\ell}$).
   Consequently, regardless of how many cycles $\gamma_m$ overlap on shared
   spanning-tree edges $e \in T$, fixing the tree claims $c'_e = c_e$ ($e \in T$)
   and setting $c'_{g_m} = c_{g_m}^{\prime *} = p_T^*(v_m) - p_T^*(u_m) = c_{g_m} - r_m^*$
   for each chord $m \in \{1, \dots, b_1\}$ yields an exact coboundary
   $c' = d_0 p_T^* \in \operatorname{im}(d_0)$ with zero defect across all cycles
   simultaneously ($\Phi_{1,w}(c') = 0$ and $\Gamma_2(c') = 0$). Moreover, if
   each tree edge weight satisfies $w_e \ge \sum_{m : e \in \gamma_m} w_{g_m}$
   (the tree-dominant weight regime), then $c'$ is a global minimum-weight
   $\ell_1$ coboundary repair of $c$ with $\|c' - c\|_{1,w} = \sum_{m=1}^{b_1} w_{g_m} |r_m^*|$.
2. **Rank-$(|V|-1+b_1)$ Partial-Guard Visibility Gap:** The false-green kernel
   of tuples passing $G_{\text{partial}}^{\text{C006}}$ while failing
   $G_{\text{complete}}^{\text{C006}}$ is canonically isomorphic to the punctured
   free $\mathbb{Z}$-module of rank $|V| - 1 + b_1$ ($= 2 b_1 = 6$ on $K_4$):
   $$\mathcal{K}_{\text{false}}^{\text{C006}}(x) := \left\{z_1 \in \mathbb{Z}^{|V|-1+2 b_1} : G_{\text{partial}}^{\text{C006}}(x, z_1) = 1 \;\wedge\; z_1 \ne z_1^*(x)\right\} \cong \mathbb{Z}^{|V|-1+b_1} \setminus \{0\},$$
   parameterized bijectively by $(\Delta p, \Delta r) \in \mathbb{Z}^{|V|-1} \times \mathbb{Z}^{b_1} \setminus \{(0, 0)\}$ via
   $$\hat{p}(v_j) = p_T^*(v_j) + \Delta p_j, \qquad \hat{r}_m = r_m^* + \Delta r_m, \qquad \hat{c}'_{g_m} = c_{g_m} - r_m^* - \Delta r_m = c_{g_m}^{\prime *} - \Delta r_m.$$
   In particular, any non-zero chord-residual error $\Delta r \ne 0$ induces
   non-zero post-repair cycle holonomy $(d_1 c'(\Delta r))_{\gamma_m} = -\Delta r_m$
   ($\Gamma_2(c'(\Delta r)) = \|\Delta r\|_1 > 0$), while any non-zero potential
   error $\Delta p \ne 0$ with $\Delta r = 0$ causes Stage-2 `VERIFY` to fail on
   the tree-edge coboundary check $\hat{p}(v) - \hat{p}(u) = c'_{(u,v)}$.
3. **Complete-Guard Closure:** $G_{\text{complete}}^{\text{C006}}(x, z_1) = 1 \iff z_1 = z_1^*(x)$,
   collapsing $\mathcal{K}_{\text{false}}^{\text{C006}}$ to $\emptyset$ and ensuring
   that every Stage-2 admitted session plan (`ASSERT` $\to$ `CUT` $\to$ `VERIFY`)
   carries an exact zero-defect coboundary $c' = d_0 \hat{p}$ and its matching
   vertex potential $\hat{p} = p_T^*$.

**Proof.** (1) By construction of the spanning-tree cycle basis, chord $g_\ell$
belongs to $\gamma_m$ if and only if $\ell = m$. Since $p_T^*$ integrates $c$
along the unique path in $T$ from $v_0$, for every tree edge $e = (u,v) \in T$ we
have $c'_e = c_e = p_T^*(v) - p_T^*(u)$, and for every chord $g_m = (u_m, v_m) \in E \setminus T$
we have $c'_{g_m} = p_T^*(v_m) - p_T^*(u_m)$. Thus $c' = d_0 p_T^*$, so
$\Phi_{1,w}(c') = 0$ and $\Gamma_2(c') = 0$. For any alternative potential
$p = p_T^* + \delta p$, $\|c - d_0 p\|_{1,w} = \sum_{e \in T} w_e |(d_0 \delta p)_e| + \sum_{m=1}^{b_1} w_{g_m} |r_m^* - (d_0 \delta p)_{g_m}|$.
Expanding $(d_0 \delta p)_{g_m} = \sum_{e \in \gamma_m \cap T} \sigma_{m,e} (d_0 \delta p)_e$
and applying the triangle inequality shows that whenever $w_e \ge \sum_{m : e \in \gamma_m} w_{g_m}$
for all $e \in T$, setting $d_0 \delta p = 0$ on $T$ ($\delta p = \text{const}$)
achieves the global minimum $\sum_{m=1}^{b_1} w_{g_m} |r_m^*|$.
(2) Under $G_{\text{partial}}^{\text{C006}}$, the $|V|-1$ tree-potential slots
$\hat{p} = p_T^* + \Delta p \in \mathbb{Z}^{|V|-1}$ and the $b_1$ residual slots
$\hat{r} = r^* + \Delta r \in \mathbb{Z}^{b_1}$ are arbitrary integers, and
$\hat{c}'_{g_m} = c_{g_m} - \hat{r}_m = c_{g_m}^{\prime *} - \Delta r_m$ is uniquely
determined by $\hat{r}_m$. Thus $(\Delta p, \Delta r) \mapsto z_1(\Delta p, \Delta r)$
is a bijection from $\mathbb{Z}^{|V|-1+b_1} \setminus \{0\}$ onto
$\mathcal{K}_{\text{false}}^{\text{C006}}(x)$. Around cycle $\gamma_m$, the
repaired cochain $c'(\Delta r)$ sums to
$(p_T^*(u_m) - p_T^*(v_m)) + c'_{g_m} = -c_{g_m}^{\prime *} + (c_{g_m}^{\prime *} - \Delta r_m) = -\Delta r_m$.
(3) Under $G_{\text{complete}}^{\text{C006}}$, tree-edge integration forces
$\hat{p}(v_j) = p_T^*(v_j)$ ($\Delta p = 0$) by induction along $T$ from
$p(v_0) = 0$; chord potential difference then forces
$\hat{c}'_{g_m} = \hat{p}(v_m) - \hat{p}(u_m) = c_{g_m}^{\prime *}$; and chord
subtraction forces $\hat{r}_m = c_{g_m} - \hat{c}'_{g_m} = r_m^*$ ($\Delta r = 0$). $\square$

### 5.6 Theorem 8: Two-stage tree-then-chord `P*` factorization and slot-arity reduction on higher-Betti graphs ($b_1 \in \{4, \dots, 7\}$)

On higher-Betti graphs ($b_1 = |E \setminus T| \ge 4$, such as $K_{3,3}$ with
$b_1 = 4$, $Q_3$ with $b_1 = 5$, $K_5$ and $\text{Petersen}$ with $b_1 = 6$, and
$W_7$ with $b_1 = 7$), single-stage triangular basis materialization requires
emitting $A_{\text{1-stage}}(G) := (|V| - 1) + 2 b_1 \in \{13, 17, 16, 21, 21\}$
signed integer slots in a single autoregressive turn while tracking multi-hop
spanning-tree paths and chord subtractions simultaneously.

Instead, we factorize the exact sequence
$$0 \longrightarrow C^0_{\text{root}=0}(G; \mathbb{Z}) \xrightarrow[\cong]{\;d_0|_T\;} C^1(T; \mathbb{Z}) \longrightarrow 0, \qquad C^1(G; \mathbb{Z}) = C^1(T; \mathbb{Z}) \oplus C^1(E \setminus T; \mathbb{Z}),$$
into two sequential guarded `P*` Stage-1 cuts before Stage 2:
- **Stage 1a (Spanning-Tree Potential Materialization, slot arity $A_{1a} = |V| - 1$):**
  Proposes $\hat{p}_T = (\hat{p}(v_1), \dots, \hat{p}(v_{|V|-1})) \in \mathbb{Z}^{|V|-1}$
  under `gbnf_slots = |V|-1`, checked by the deterministic **tree-integration guard**
  $$G_T(x, \hat{p}_T) = 1 \iff \bigwedge_{e=(u,v) \in T} \bigl(\hat{p}(v) - \hat{p}(u) = c_e\bigr), \qquad \hat{p}(v_0) := 0.$$
  If $G_T = 0$ after at most $R_{1a} \ge 1$ attempts, $\pi_{\mathcal{I}}$ projects
  the pipeline to `NullTree` ($\mathbf{0}$), saving both Stage 1b and all 3 Stage-2 turns.
- **Stage 1b (Grafted Chord-Coboundary Materialization, slot arity $A_{1b} = b_1$):**
  Conditioned on $G_T(x, \hat{p}_T) = 1$ (so $\hat{p}_T = p_T^*$ is verified),
  the host grafts $p_T^*$ as an immutable `LeafTextSpan` (`PromptColour.SubstitutionStep`)
  into the Stage-1b prompt, listing for each chord $g_m = (u_m \to v_m) \in E \setminus T$
  its already-verified endpoint potentials $p_T^*(v_m)$ and $p_T^*(u_m)$, and
  proposes $\hat{c}'_{E \setminus T} = (\hat{c}'_{g_1}, \dots, \hat{c}'_{g_{b_1}}) \in \mathbb{Z}^{b_1}$
  under `gbnf_slots = b_1`, checked by the **chord-coboundary guard**
  $$G_C\bigl(x, p_T^*, \hat{c}'_{E \setminus T}\bigr) = 1 \iff \bigwedge_{m=1}^{b_1} \Bigl(\hat{c}'_{g_m} = p_T^*(v_m) - p_T^*(u_m)\Bigr).$$

**Theorem 8 (Two-Stage Tree-Then-Chord `P*` Slot-Arity Reduction & Kernel Closure).**
For every connected graph $G = (V, E)$ with spanning tree $T$ ($|T| = |V| - 1$)
and $b_1 = |E \setminus T| \ge 1$ chords:

1. **Per-Turn Slot-Arity Reduction:** The maximum integer-slot arity across
   Stage 1a and Stage 1b satisfies
   $$A_{\text{2-stage}}(G) := \max\bigl(|V| - 1,\; b_1\bigr) \le (|V| - 1) + 2 b_1 - \min(|V| - 1, b_1) - b_1 < A_{\text{1-stage}}(G),$$
   yielding strict arity reductions of $2 b_1$ slots in Stage 1a and $|V| - 1 + b_1$
   slots in Stage 1b (specifically $(13, 17, 16, 21, 21) \to (5, 7, 6, 9, 7)$ across
   $K_{3,3}, Q_3, K_5, \text{Petersen}, W_7$).
2. **Depth-1 Chord Factorization Conditioned on $G_T = 1$:** Once Stage 1a passes
   $G_T(x, \hat{p}_T) = 1$, $\hat{p}_T = p_T^* = (d_0|_T)^{-1}(c|_T)$ is uniquely
   fixed in the Stage-1b prompt context. Consequently, each Stage-1b slot
   $\hat{c}'_{g_m}$ depends only on a single depth-1 two-integer subtraction
   $p_T^*(v_m) - p_T^*(u_m)$ of literals already present in the Stage-1b prompt,
   with zero multi-hop path accumulation and zero cross-chord coupling.
3. **Two-Stage False-Green Kernel Closure:** The joint two-stage guard satisfies
   $$G_T(x, \hat{p}_T) = 1 \;\wedge\; G_C\bigl(x, \hat{p}_T, \hat{c}'_{E \setminus T}\bigr) = 1 \iff \bigl(\hat{p}_T, \hat{c}'_{E \setminus T}\bigr) = \bigl(p_T^*, d_0|_{E \setminus T} p_T^*\bigr),$$
   so the two-stage false-green kernel is empty ($\mathcal{K}_{\text{false}}^{\text{2-stage}}(x) = \emptyset$),
   and every pair admitted to Stage 2 defines an exact zero-defect coboundary
   $c' = c|_T \oplus \hat{c}'_{E \setminus T} = d_0 p_T^*$ with $\Phi_{1,w}(c') = 0$
   and $\Gamma_2(c') = 0$.

**Proof.** (1) Since $|V| - 1 \ge 1$ and $b_1 \ge 1$, both $|V| - 1 \le (|V| - 1) + 2 b_1 - 2$
and $b_1 \le (|V| - 1) + 2 b_1 - 2$, so $\max(|V|-1, b_1) < (|V|-1) + 2 b_1$.
(2)–(3) Because $T$ is a spanning tree rooted at $v_0$ with $p(v_0) = 0$, the
restriction $d_0|_T: C^0_{\text{root}=0}(G; \mathbb{Z}) \to C^1(T; \mathbb{Z})$
is a $\mathbb{Z}$-module isomorphism; hence $G_T(x, \hat{p}_T) = 1 \iff d_0|_T \hat{p}_T = c|_T \iff \hat{p}_T = p_T^*$.
Conditioned on $\hat{p}_T = p_T^*$, $G_C(x, p_T^*, \hat{c}'_{E \setminus T}) = 1$
holds if and only if $\hat{c}'_{g_m} = p_T^*(v_m) - p_T^*(u_m) = (d_0 p_T^*)_{g_m}$
for each $m \in \{1, \dots, b_1\}$ independently. Combining $c'|_T = c|_T = d_0|_T p_T^*$
and $c'|_{E \setminus T} = d_0|_{E \setminus T} p_T^*$ gives $c' = d_0 p_T^*$,
so $\Phi_{1,w}(c') = 0$ and $\Gamma_2(c') = 0$. $\square$

### 5.7 Theorem 9: Dichotomic Fredholm-alternative `P*` guarding and elimination of the lazy false-refusal attractor (`C005`)

Consider the dichotomic relational consistency task (`C005`): given a finite
connected directed graph $G = (V, E)$ with integer edge differences $d \in \mathbb{Z}^E$,
a participant must decide whether the system $n_v - n_u = d_{(u,v)}$ ($(u,v) \in E$)
is `CONSISTENT` (returning an exact vertex potential $n \in \mathbb{Z}^V$ with
$d_0 n = d$) or `INCONSISTENT` (returning a simple directed cycle $\gamma$ whose
signed edge sum $\langle \gamma, d \rangle = \sum_{e \in \gamma} \sigma_{\gamma, e} d_e \ne 0$).

In un-staged one-shot generation, small and medium language models exhibit a
systematic **lazy false-refusal (`INCONSISTENT`) attractor**: whenever a model
makes a single sign or addition mistake while integrating potentials along $G$,
it encounters a chord $g_m = (u_m \to v_m)$ where its erroneous potentials fail
$\hat{n}_{v_m} - \hat{n}_{u_m} = d_{g_m}$, and therefore declares `INCONSISTENT`
on consistent boards (`0/4 = 0.0%` accuracy on consistent boards in both Panel 1
and un-staged Panel 2; see Subsection 6.6).

To eliminate this failure mode, fix a rooted spanning tree $T \subset E$
($|T| = |V| - 1$) and $b_1 = |E \setminus T|$ chords $g_1, \dots, g_{b_1}$, and
require Stage 1 to materialize the $(|V| - 1 + b_1)$-slot tuple
$z_1 = (\hat{p}_T, \hat{r}_{E \setminus T}) \in \mathbb{Z}^{|V|-1} \times \mathbb{Z}^{b_1}$
subject to the **Dichotomic Fredholm-Alternative Guard**:
$$G_{\text{Fredholm}}\bigl(x, \hat{p}_T, \hat{r}_{E \setminus T}\bigr) = 1 \iff \bigwedge_{e=(u,v) \in T} \bigl(\hat{p}_T(v) - \hat{p}_T(u) = d_e\bigr) \;\wedge\; \bigwedge_{m=1}^{b_1} \Bigl(\hat{r}_m = d_{g_m} - \bigl(\hat{p}_T(v_m) - \hat{p}_T(u_m)\bigr)\Bigr).$$

**Theorem 9 (Dichotomic Fredholm-Alternative `P*` Guard & False-Verdict Elimination).**
For every connected directed graph $G = (V, E)$ with spanning tree $T$, chords
$g_1, \dots, g_{b_1} \in E \setminus T$, and edge differences $d \in \mathbb{Z}^E$:

1. **Discrete Fredholm Alternative on $(T, E \setminus T)$:** Let
   $p_T^* = (d_0|_T)^{-1}(d|_T) \in \mathbb{Z}^V$ ($p_T^*(v_0) = 0$) and let
   $r_m^* := \langle \gamma_m, d \rangle = d_{g_m} - (p_T^*(v_m) - p_T^*(u_m))$
   be the holonomy of the $m$-th chord-induced cycle $\gamma_m$. Then:
   $$d \in \operatorname{im}(d_0) \iff r_1^* = \dots = r_{b_1}^* = 0 \iff d = d_0 p_T^*,$$
   and conversely $d \notin \operatorname{im}(d_0)$ if and only if there exists
   $m^* \in \{1, \dots, b_1\}$ with $r_{m^*}^* \ne 0$, in which case $\gamma_{m^*}$
   is an explicit simple-cycle contradiction witness with $\langle \gamma_{m^*}, d \rangle = r_{m^*}^* \ne 0$.
2. **Elimination of the Lazy False-Refusal Attractor ($\mathcal{K}_{\text{false-verdict}}^{\text{C005}}(x) = \emptyset$):**
   For every proposal $z_1 = (\hat{p}_T, \hat{r}_{E \setminus T}) \in \mathbb{Z}^{|V|-1+b_1}$,
   $$G_{\text{Fredholm}}\bigl(x, \hat{p}_T, \hat{r}_{E \setminus T}\bigr) = 1 \iff \bigl(\hat{p}_T, \hat{r}_{E \setminus T}\bigr) = \bigl(p_T^*, r_{E \setminus T}^*\bigr).$$
   Consequently, under the deterministic Stage-2 branch map
   $$\mathcal{B}\bigl(\hat{p}_T, \hat{r}_{E \setminus T}\bigr) := \begin{cases} (\mathsf{CONSISTENT},\; \hat{p}_T) & \text{if } \hat{r}_{E \setminus T} = 0, \\ (\mathsf{INCONSISTENT},\; \gamma_{m^*},\, \hat{r}_{m^*}) & \text{if } m^* = \min\{m : \hat{r}_m \ne 0\}, \end{cases}$$
   no Stage-1 proposal admitted by $G_{\text{Fredholm}} = 1$ can emit a false
   `INCONSISTENT` verdict on a consistent board or a false `CONSISTENT` verdict
   on an inconsistent board: the admitted false-verdict set is empty
   ($\mathcal{K}_{\text{false-verdict}}^{\text{C005}}(x) = \emptyset$).

**Proof.** (1) Because $\{\gamma_1, \dots, \gamma_{b_1}\}$ is a $\mathbb{Z}$-basis
for $H_1(G; \mathbb{Z}) = \ker(\partial_1)$, $d \in \operatorname{im}(d_0) = \ker(d_1)$
holds if and only if $\langle \gamma_m, d \rangle = 0$ for every $m = 1, \dots, b_1$.
Along $\gamma_m = g_m - \pi_T(u_m \to v_m)$, telescoping $d|_T = d_0|_T p_T^*$
along the unique tree path $\pi_T(u_m \to v_m)$ gives
$\sum_{e \in \pi_T(u_m \to v_m)} \sigma_{e} d_e = p_T^*(v_m) - p_T^*(u_m)$, so
$\langle \gamma_m, d \rangle = d_{g_m} - (p_T^*(v_m) - p_T^*(u_m)) = r_m^*$.
Thus $r_{E \setminus T}^* = 0 \iff d = d_0 p_T^*$, and if $r_{m^*}^* \ne 0$ then
$\gamma_{m^*}$ is a simple cycle in $T \cup \{g_{m^*}\}$ with non-zero signed sum $r_{m^*}^*$.
(2) Under $G_{\text{Fredholm}} = 1$, the first conjunction forces $\hat{p}_T = p_T^*$
by tree-path induction from $v_0$, and substituting $\hat{p}_T = p_T^*$ into the
second conjunction forces $\hat{r}_m = d_{g_m} - (p_T^*(v_m) - p_T^*(u_m)) = r_m^*$
for every $m = 1, \dots, b_1$. Hence $\hat{r}_{E \setminus T} = 0 \iff r_{E \setminus T}^* = 0 \iff d \in \operatorname{im}(d_0)$,
so $\mathcal{B}(\hat{p}_T, \hat{r}_{E \setminus T})$ agrees with the exact
cohomological truth on every admitted instance. $\square$

### 5.8 Theorem 10: Cohomological syndrome decoding $\mathbf{r}^* = S\mathbf{c}$ across Verdict, Single-Edge Repair, and Audit (`C001`)

Consider the distractor-contaminated rank-difference witness game (`C001`): a
natural-language prompt contains bracketed distractor notes (`[Note k: ...]`,
which belong to the congruence ideal $\mathcal{I}_{\text{distractor}}$) mixed
with directed integer rank-difference claims $c_{u,v} \in \mathbb{Z}$ (`B - A = c_{A,B}`,
$|V| \in \{8, \dots, 11\}, |E| \in \{12, \dots, 16\}, b_1 \in \{5, 7\}, c_{u,v} \in [-5000, 5000]$)
and one of three task obligations:
- `verdict`: emit `CONSISTENT` with an exact potential $p: V \to \mathbb{Z}$, or
  `CONTRADICTION` with an explicit simple cycle whose signed edge sum is non-zero;
- `repair`: identify a single corrupted edge $e^* \in E$, its replacement value
  $c'_{e^*} \in \mathbb{Z}$, and the resulting exact potential $p': V \to \mathbb{Z}$
  on $(E \setminus \{e^*\}) \cup \{(e^*, c'_{e^*})\}$;
- `audit`: inspect a proposed submission (which may contain adversarial
  off-by-one cycle claims, flipped edge orientations, or deceptive `CONTRADICTION`
  claims on consistent graphs) and emit `ACCEPT` or `REJECT` with a verified
  correction witness.

Fix a rooted spanning tree $T \subset E$ ($|T| = |V| - 1$) and chord set
$E \setminus T = \{e_1, \dots, e_{b_1}\}$ ($e_m = u_m \to v_m$). For each chord
$e_m \in E \setminus T$ and each tree edge $e \in T$, define the signed
tree-path incidence
$$S_{m, e} := \begin{cases} +1 & \text{if } e \text{ is traversed forward along the unique path } \pi_T(u_m \to v_m), \\ -1 & \text{if } e \text{ is traversed backward along } \pi_T(u_m \to v_m), \\ 0 & \text{if } e \notin \pi_T(u_m \to v_m), \end{cases}$$
and form the **chord-induced cycle-edge incidence matrix**
$$S := \bigl[\,S_T \;\big|\; -I_{b_1}\,\bigr] \in \{-1, 0, +1\}^{b_1 \times |E|},$$
whose $m$-th row $S_{m, \cdot}$ is the signed indicator of the chord-induced
simple cycle $\mathcal{C}_T(e_m) = \pi_T(u_m \to v_m) \cup \{v_m \to u_m\}$.

**Theorem 10 (Cohomological Syndrome Decoding Across Verdict, Single-Edge Repair, and Audit).**
Suppose Stage 1a materializes $\hat{p}_T \in \mathbb{Z}^{|V|-1}$ passing
$G_T(\mathbf{c}, \hat{p}_T) = 1$ (so $\hat{p}_T = p_T^* = B_T^{-1} \mathbf{c}|_T$),
and Stage 1b materializes $\hat{\mathbf{c}}_{E \setminus T} \in \mathbb{Z}^{b_1}$
passing $G_C(p_T^*, \hat{\mathbf{c}}_{E \setminus T}) = 1$ (so
$\hat{c}_m = \hat{c}_m^* := p_T^*(v_m) - p_T^*(u_m)$ for $m = 1, \dots, b_1$).
Define the **cohomological syndrome vector**
$$\mathbf{r}^* := \hat{\mathbf{c}}^* - \mathbf{c}|_{E \setminus T} \in \mathbb{Z}^{b_1}.$$
Then:

1. **Exact Cycle-Space Parity Check:** $\mathbf{r}^* = S\mathbf{c}$ identically,
   and $\ker(S) = \operatorname{im}(d_0) = \{\mathbf{c} \in \mathbb{Z}^E : \Phi_1(\mathbf{c}) = 0\}$.
   Consequently, for `verdict` tasks, $\mathbf{r}^* = \mathbf{0} \iff \Phi_1(\mathbf{c}) = 0$
   (`CONSISTENT` with exact potential $p_T^*$), and $\mathbf{r}^* \ne \mathbf{0} \iff \Phi_1(\mathbf{c}) > 0$
   (`CONTRADICTION`, where any $m^*$ with $r_{m^*}^* \ne 0$ yields the certified
   simple cycle $\mathcal{C}_T(e_{m^*})$ with signed discrepancy $r_{m^*}^* \ne 0$).
2. **Single-Edge Syndrome Decoding (Chord & Spanning-Tree Perturbations):** Let
   $\mathbf{c} = \mathbf{c}^{\text{true}} + \delta \mathbf{e}_{e^*}$ be obtained
   from a consistent cochain $\mathbf{c}^{\text{true}} = d_0 p^{\text{true}} \in \operatorname{im}(d_0)$
   by corrupting a single edge $e^* \in E$ by $\delta = c_{e^*} - c^{\text{true}}_{e^*} \ne 0$.
   Then a candidate single-edge replacement $(e, c'_e)$ with shift
   $\hat{\delta} := c_e - c'_e \in \mathbb{Z} \setminus \{0\}$ yields a globally
   consistent repaired cochain $\mathbf{c}' = \mathbf{c} - \hat{\delta}\mathbf{e}_e \in \operatorname{im}(d_0)$
   if and only if the syndrome $\mathbf{r}^*$ is the $\hat{\delta}$-scaled
   $e$-th column of $S$:
   $$\mathbf{r}^* = \hat{\delta}\,S_{\cdot, e}.$$
   In particular:
   - **Case 2a (Chord Perturbation, $e^* = e_m \in E \setminus T$):** Since
     $S_{\cdot, e_m} = -\mathbf{e}_m \in \mathbb{Z}^{b_1}$, a chord corruption
     has unit Hamming support $\operatorname{supp}(\mathbf{r}^*) = \{m\}$ with
     $r_m^* = -\delta$, and is repaired by $c'_{e_m} = c_{e_m} + r_m^* = \hat{c}_m^*$
     with unchanged potential $p' = p_T^*$.
   - **Case 2b (Spanning-Tree Perturbation, $e^* \in T$):** A tree-edge
     corruption propagates across the tree-cut incidence set
     $\operatorname{supp}(\mathbf{r}^*) = \{m \in \{1, \dots, b_1\} : e^* \in \pi_T(u_m \to v_m)\}$
     with $r_m^* = \delta S_{m, e^*} \in \{\pm \delta\}$, and is decoded by matching
     $\mathbf{r}^* = \hat{\delta} S_{\cdot, e^*}$ ($c'_{e^*} = c_{e^*} - \hat{\delta}$)
     and shifting the subtree potential $p' = B_T^{-1}(\mathbf{c}|_T - \hat{\delta}\mathbf{e}_{e^*})$.
3. **Adversarial Audit Completeness:** For any `audit` submission proposing a
   potential, contradiction cycle, or single-edge repair, re-evaluating the
   proposal against $(p_T^*, \mathbf{r}^* = S\mathbf{c})$ rejects all off-by-one
   cycle claims, flipped-sign edge traversals, and deceptive `CONTRADICTION`
   claims on $\mathbf{r}^* = \mathbf{0}$ graphs.

**Proof.** (1) Along each chord $e_m = (u_m \to v_m)$, telescoping $d_0 p_T^* = \mathbf{c}|_T$
along $\pi_T(u_m \to v_m)$ gives $\hat{c}_m^* = p_T^*(v_m) - p_T^*(u_m) = \sum_{e \in T} S_{m,e} c_e = (S_T \mathbf{c}|_T)_m$.
Subtracting $c_{e_m}$ gives $r_m^* = (S_T \mathbf{c}|_T)_m - c_{e_m} = (S\mathbf{c})_m$.
Since the rows of $S$ form a basis of the cycle space $Z_1(G; \mathbb{Z})$,
$S\mathbf{c} = \mathbf{0} \iff \mathbf{c} \in \operatorname{im}(d_0)$.
(2) By linearity of $S$, for $\mathbf{c}' = \mathbf{c} - \hat{\delta}\mathbf{e}_e$,
we have $S\mathbf{c}' = S\mathbf{c} - \hat{\delta} S_{\cdot, e} = \mathbf{r}^* - \hat{\delta} S_{\cdot, e}$.
Thus $\mathbf{c}' \in \operatorname{im}(d_0) = \ker(S) \iff \mathbf{r}^* = \hat{\delta} S_{\cdot, e}$.
When $e = e_m \in E \setminus T$, column $S_{\cdot, e_m} = -\mathbf{e}_m$, so
$\mathbf{r}^* = -\hat{\delta}\mathbf{e}_m$ and $c'_{e_m} = c_{e_m} - \hat{\delta} = c_{e_m} + r_m^* = \hat{c}_m^*$.
When $e \in T$, column $S_{\cdot, e}$ has non-zero entries $\pm 1$ on every chord
cycle whose tree path traverses $e$. (3) follows immediately from (1) and (2). $\square$

### 5.9 Theorem 11: Tree-coboundary defect migration vs. path-integrated $B_T^{-1}$ guard diagnostics

Why does Stage 1a require a **path-integrated** diagnostic guard rather than an
**edge-local** coboundary diagnostic on multi-hop spanning trees with 4-digit
claims? Order the non-root vertices $V \setminus \{v_0\} = \{v_1, \dots, v_{|V|-1}\}$
in BFS topological order along the rooted spanning tree $T$, and let
$B_T := d_0|_T \in \{-1, 0, +1\}^{(|V|-1) \times (|V|-1)}$ be the rooted tree
coboundary matrix. Its inverse $B_T^{-1} \in \{0, +1\}^{(|V|-1) \times (|V|-1)}$
is the lower-triangular **root-to-vertex path-incidence matrix**:
$$(B_T^{-1})_{w, e} = \mathbb{1}\bigl[e \in \pi_T(v_0 \to w)\bigr], \qquad p_T^*(w) = \bigl(B_T^{-1} \mathbf{c}|_T\bigr)_w = \sum_{e \in \pi_T(v_0 \to w)} c_e.$$

For any Attempt-1 proposal $\hat{p}_T^{(1)} \in \mathbb{Z}^{|V|-1}$, define its
**edge-local coboundary residual** $\mathbf{e}_T^{(1)} \in \mathbb{Z}^{|V|-1}$
and its **path-integrated potential residual** $\boldsymbol{\delta}_T^{(1)} \in \mathbb{Z}^{|V|-1}$ by
$$\mathbf{e}_T^{(1)} := B_T \hat{p}_T^{(1)} - \mathbf{c}|_T, \qquad \boldsymbol{\delta}_T^{(1)} := \hat{p}_T^{(1)} - B_T^{-1} \mathbf{c}|_T = B_T^{-1} \mathbf{e}_T^{(1)}.$$

**Theorem 11 (Tree-Coboundary Defect Migration Under Edge-Local Retry vs. One-Step Convergence Under Path-Integrated $B_T^{-1}$ Diagnostics).**
Suppose Attempt 1 commits a single arithmetic integration error $\Delta_{v^*} \ne 0$
at an internal tree edge $e^* = (\operatorname{parent}(v^*) \to v^*) \in T$ while
integrating all remaining tree edges accurately:
$(\mathbf{e}_T^{(1)})_{e^*} = \Delta_{v^*} \ne 0$ and $(\mathbf{e}_T^{(1)})_e = 0$
for all $e \in T \setminus \{e^*\}$. Let $\operatorname{Subtree}_T(v^*) := \{w \in V \setminus \{v_0\} : e^* \in \pi_T(v_0 \to w)\}$
be the descendant subtree rooted at $v^*$, and suppose $|\operatorname{Subtree}_T(v^*)| \ge 2$
(so $v^*$ has at least one child in $T$). Then:

1. **Subtree Shift vs. Single-Edge Local Syndrome:** Although the potential error
   $\delta_T^{(1)}(w) = (B_T^{-1} \mathbf{e}_T^{(1)})_w = \Delta_{v^*} \ne 0$ is
   non-zero at **every** descendant $w \in \operatorname{Subtree}_T(v^*)$, the
   edge-local coboundary residual $\mathbf{e}_T^{(1)}$ is non-zero **only** at
   $e^*$: for every strict descendant edge $e = (u \to w)$ inside
   $\operatorname{Subtree}_T(v^*)$, both endpoints are shifted by $+\Delta_{v^*}$,
   so the local difference cancels:
   $$\hat{p}_T^{(1)}(w) - \hat{p}_T^{(1)}(u) = \bigl(p_T^*(w) + \Delta_{v^*}\bigr) - \bigl(p_T^*(u) + \Delta_{v^*}\bigr) = c_e \implies (\mathbf{e}_T^{(1)})_e = 0.$$
2. **Coboundary Defect Migration Under Coordinate-Local Retry:** If a retry diagnostic
   reports only the coordinates where $\mathbf{e}_T^{(1)} \ne 0$ (namely slot $v^*$)
   and the model updates only the flagged slot $\hat{p}_T^{(2)}(v^*) = p_T^*(v^*)$
   while retaining its unflagged slots $\hat{p}_T^{(2)}(w) = \hat{p}_T^{(1)}(w) = p_T^*(w) + \Delta_{v^*}$
   for $w \in \operatorname{Subtree}_T(v^*) \setminus \{v^*\}$, then Retry 1
   **fails** $G_T$: the coboundary defect migrates from $e^*$ to every child edge
   $e_{\text{child}} = (v^* \to w)$ of $v^*$:
   $$(\mathbf{e}_T^{(2)})_{e^*} = 0, \qquad (\mathbf{e}_T^{(2)})_{(v^* \to w)} = \bigl(p_T^*(w) + \Delta_{v^*}\bigr) - p_T^*(v^*) - c_{(v^* \to w)} = \Delta_{v^*} \ne 0.$$
   More generally, coordinate-local repair of $\mathbf{e}_T \ne 0$ requires at
   least $\operatorname{depth}(\operatorname{Subtree}_T(v^*)) + 1$ sequential rounds
   to push the coboundary defect off the leaves of $T$.
3. **One-Retry Convergence Under Path-Integrated $B_T^{-1}$ Diagnostics:** Because
   $\operatorname{supp}(\boldsymbol{\delta}_T^{(1)}) = \operatorname{Subtree}_T(v^*)$,
   the path-integrated guard diagnostic $\hat{p}_T^{(1)}(w) \ne (B_T^{-1}\mathbf{c}|_T)_w$
   flags $v^*$ and all of its affected descendants $w \in \operatorname{Subtree}_T(v^*)$
   simultaneously in a single diagnostic turn, eliminating subtree defect migration.

**Proof.** (1) Since $\mathbf{e}_T^{(1)} = \Delta_{v^*} \mathbf{e}_{e^*}$, multiplying
by $B_T^{-1}$ gives $\delta_T^{(1)}(w) = (B_T^{-1})_{w, e^*} \Delta_{v^*} = \Delta_{v^*} \mathbb{1}[w \in \operatorname{Subtree}_T(v^*)]$.
Applying $B_T$ recovers $\mathbf{e}_T^{(1)} = B_T \boldsymbol{\delta}_T^{(1)} = \Delta_{v^*} \mathbf{e}_{e^*}$,
which vanishes on every edge $e \ne e^*$. (2) Updating only coordinate $v^*$ sets
$\delta_T^{(2)}(v^*) = 0$ while leaving $\delta_T^{(2)}(w) = \Delta_{v^*}$ for
$w \in \operatorname{Subtree}_T(v^*) \setminus \{v^*\}$. Applying $B_T$ to
$\boldsymbol{\delta}_T^{(2)}$ gives $(\mathbf{e}_T^{(2)})_{(u \to w)} = \delta_T^{(2)}(w) - \delta_T^{(2)}(u)$,
which equals $\Delta_{v^*} - 0 = \Delta_{v^*} \ne 0$ for every child edge $(v^* \to w)$
with $w \in \operatorname{Subtree}_T(v^*)$. By induction on subtree depth, each
coordinate-local retry advances the zero-error wavefront by one tree level,
requiring $\operatorname{depth}(\operatorname{Subtree}_T(v^*)) + 1$ rounds.
(3) Directly from $\operatorname{supp}(\boldsymbol{\delta}_T^{(1)}) = \{w : \hat{p}_T^{(1)}(w) \ne p_T^*(w)\} = \operatorname{Subtree}_T(v^*)$. $\square$

### 5.10 Theorem 12: Independent exact cohomology certificate verification across `C011`–`C020` and elimination of status-label false-`SOLVED` admissions

Consider the ten-challenge cohomology suite `b_cohomology` (`C011`–`C020`:
$\ell_1$ cycle-rank coboundary repair `C011`, cellular sheaf cohomology `C012`,
simplicial Smith Normal Form torsion `C013`, weighted 2-complex discrete Hodge
decomposition `C014`, $\mathbb{F}_2$ persistent homology $R = D \cdot V$ `C015`,
Alexander–Whitney cup-product ring `C016`, non-abelian lattice gauge holonomy
`C017`, signed-graph switching frustration `C018`, $H^2$ cochain extension
obstruction `C019`, and $\mathbb{F}_2$ double-complex spectral sequences `C020`).
For each challenge $m \in \{11, \dots, 20\}$ and instance $x$, a candidate
JSON certificate $z = (\hat{\sigma}, \hat{w})$ pairs a self-reported status
label $\hat{\sigma} \in \{\mathsf{SOLVED}, \mathsf{OUT\_OF\_SCOPE}, \mathsf{UNKNOWN}\}$
with a structured witness payload $\hat{w}$.

Let $G_{\text{status}}(x, z) := \mathbb{1}[\hat{\sigma} = \mathsf{SOLVED}]$ be
the **status-label guard** that trusts the model's self-reported `"status": "SOLVED"`
field once JSON schema parsing succeeds, and let
$G_{\text{cert}}^{(m)}(x, z) \in \{0, 1\}$ (`check_certificate`) be the
**independent exact certificate guard** that recomputes the defining algebraic
identities of challenge $m$ from $(x, \hat{w})$ over $\mathbb{Q}$, $\mathbb{Z}$,
$\mathbb{F}_2$, or finite group tables without calling the solver and without
trusting $\hat{\sigma}$.

**Theorem 12 (Status-Label False-`SOLVED` Kernel vs. Independent Exact Certificate Closure Across `C011`–`C020`).**
For every cohomology challenge $m \in \{11, \dots, 20\}$ and valid solvable
instance $x \in \mathcal{D}_{\text{solved}}^{(m)}$:

1. **Unbounded Status-Label False-`SOLVED` Kernel:** The set of schema-valid
   JSON replies that pass $G_{\text{status}}(x, z) = 1$ while violating the
   algebraic witness relation $R^{(m)}(x, \hat{w})$,
   $$\mathcal{K}_{\text{false-status}}^{(m)}(x) := \bigl\{z = (\mathsf{SOLVED}, \hat{w}) : G_{\text{status}}(x, z) = 1 \;\wedge\; \neg R^{(m)}(x, \hat{w})\bigr\},$$
   is non-empty (and infinite whenever $\hat{w}$ carries integer or rational
   cochain fields). On accounted 7B open-weight evaluation (`B-COH-S1`,
   `qwen/qwen-2.5-7b-instruct`), Attempt 1 lands in $\mathcal{K}_{\text{false-status}}^{(m)}(x)$
   on **`10/10` (`100.0%`)** of challenges `C011`–`C020`.
2. **Exact Certificate Guard Closure:** Under the independent verifier
   $G_{\text{cert}}^{(m)}(x, z) = 1 \iff \hat{\sigma} = \mathsf{SOLVED} \wedge R^{(m)}(x, \hat{w})$
   (and for out-of-scope inputs $x \in \mathcal{D}_{\text{oos}}^{(m)}$,
   $\hat{\sigma} = \mathsf{OUT\_OF\_SCOPE} \wedge R_{\text{oos}}^{(m)}(x, \hat{w})$),
   the admitted false-`SOLVED` kernel is empty:
   $$\bigl\{z : G_{\text{cert}}^{(m)}(x, z) = 1 \;\wedge\; \neg R^{(m)}(x, \hat{w})\bigr\} = \emptyset,$$
   and any persistent certificate failure after $R \ge 1$ bounded diagnostic
   attempts is absorbed by $\pi_{\mathcal{I}}$ into `NullTree` ($\mathbf{0}$)
   with zero false `SOLVED` admissions to Stage 2.

**Proof.** (1) Changing any numerical coordinate of a valid witness $w^*$ (e.g.,
replacing $R = D \cdot V \pmod 2$ by $R = 0$ in `C015`, or reporting
`frustration_index = 0` with an unbalanced switching assignment $\sigma \in \{\pm 1\}^V$
in `C018`) while keeping `"status": "SOLVED"` preserves $G_{\text{status}}(x, z) = 1$
and violates $R^{(m)}(x, \hat{w})$. (2) By definition of `check_certificate`,
$G_{\text{cert}}^{(m)}(x, z) = 1$ holds only when every defining equation of
$R^{(m)}(x, \hat{w})$ holds identically; if $G_{\text{cert}}^{(m)} = 0$ on all
$R$ attempts, Theorem 3's ideal absorption maps the Stage-2 graft to `NullTree`. $\square$

## 6. Historical mechanism results: causal slot-factorization and guarded retry across six C004 trials, three C006 multi-cycle trials, one C005 dichotomic trial, one C001 syndrome trial, and one `b_cohomology` (`C011`–`C020`) campaign

**Current evidence status (2026-10-23):** The original mechanism receipt files
referenced by the companion are unavailable in this checkout and the original
working directory. The values retained in this section and the empirical
conclusions below are historical assertions, not revalidated measurements.
They supply no evidence for the new harness campaign. The finite examples can
be checked separately with `code/replay.py --finite-only`; that command reports
`internal_interventions: NOT_REPLAYED`. Missing historical evidence is not a pass.

### 6.1 Why single-turn zero-scratchpad operad prompts fail and `P*` cuts help

Consider an autoregressive transformer $P_\theta$ tasked with emitting the
$k$-slot repaired cochain $y = (c'_0, \dots, c'_{k-1}) \in \mathcal{L}_k$ for a
directed $k$-cycle $x = (c, w)$. Under Theorem 2, computing $y$ requires latent
intermediate invariants $z = (s, i^*, c_{i^*}, c'_{i^*})$ where $s = \sum_i c_i$,
$i^* = \arg\min_i w_i$, $c_{i^*} = c[i^*]$, and $c'_{i^*} = c_{i^*} - s$.

- **Single-Turn Zero-Scratchpad Regime (`operad_grafted_grammar_projection`):**
  When the entire operad tree is rendered in a single turn under Layer-2 grammar
  mask $\mathcal{L}_k$ (`gbnf_slots=k`), the first output token $y_0 = c'_0$
  must be emitted before any token of $z$ has been written to the causal context:
  $$P_{\text{1-turn}}(y \mid x) = P_\theta(y_0 \mid x)\prod_{t=1}^{k-1} P_\theta(y_t \mid x, y_{<t}).$$
  Whenever $i^* = 0$, $y_0 = c_0 - s$ already depends on the global cycle sum
  $s$ and minimum-weight index $i^*$, forcing the model to compute both inside a
  single forward pass while decoding an ASCII operad tree container.
- **Multi-Turn `P*` Staged Operad Materialization (`p_star_operad_slot_materialization`):**
  Cutting the operad tree at an intermediate `SubstitutionStep` operator $f_1$
  (Stage 1, grammar $\mathcal{L}_m$) and grafting the materialized output $z$
  as an immutable `LeafTextSpan` into Stage 2 ($f_2 \circ_i z$, grammar
  $\mathcal{L}_k$) factorizes the conditional generation law in topological
  dependency order:
  $$P_{\text{P*}}(z, y \mid x) = P_\theta(z_0 \mid x)\prod_{j=1}^{m-1} P_\theta(z_j \mid x, z_{<j}) \cdot \mathbb{1}[z \notin \mathcal{I}] \cdot \prod_{t=0}^{k-1} P_\theta(y_t \mid x, f_2 \circ_i z, y_{<t}).$$
  Each intermediate slot $z_j$ is conditioned via causal self-attention on the
  already-emitted prefix $z_{<j}$, and Stage 2 reduces to substituting the
  grafted value $c'_{i^*}$ at index $i^*$ while copying $c_t$ for $t \ne i^*$.

### 6.2 Empirical results across five bounded C004 trials

We evaluated this hierarchy across $N = 8$ deterministic C004 directed $k$-cycle
cases ($k \in \{3, 4, 5, 6\}$, two cases per slot count) on two strictly
separated panels (never pooled):

- **Panel 1 (Local HF Checkpoint):** Pinned `Qwen/Qwen2.5-0.5B-Instruct`
  (revision `7ae557604adf67be50417f59c2c2f167def9a775`, CPU `torch.float32`,
  0 provider calls, `$0`).
- **Panel 2 (Accounted OpenRouter):** `openai/gpt-4o-mini` at `temperature=0.0`
  under strict `json_schema` regex slot projection and native Rust
  `verify_decode_receipt` attestation.

#### Table 1: Panel 1 — Pinned local `Qwen/Qwen2.5-0.5B-Instruct` ($N = 8$ C004 cases)

| Trial & Arm | Layer-2 Parseable (`parse_integer_slots`) | Certified `ExactCoboundary` ($\Phi_1 = 0, \Gamma_2 = 0$) | Exact $\ell_1$-Optimal Repair | Key Mechanism Observation |
| --- | --- | --- | --- | --- |
| **Trial 1 (`c004_paired_benchmark_receipt.json`)** | | | | |
| `free` (unconstrained greedy) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | Emits prose explanations (`To find the minimum...`). |
| `f_null` (no-op logit hook) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | `8/8` (`100.0%`) token-for-token identical to `free` (Proposition 4.3). |
| `carrier` (`[0-9\- ]` vocab filter) | `6/8` (`75.0%`) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | Fails slot count on `2/8` cases (`15` slots for $k=3$; `20` slots for $k=6$). |
| `grammar` (`gbnf_slots=k` DFA mask) | `8/8` (`100.0%`) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | `100%` syntax admissibility (Proposition 4.1); `0/8` zero holonomy. |
| **Trial 2 (`operad_cochain_ablation_receipt.json`)** | | | | |
| `operad_grafted_grammar_projection` (1-turn) | `8/8` (`100.0%`) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | Zero-scratchpad 1-turn operad tree (`0/8` coboundary). |
| **Trial 3 (`p_star_operad_materialization_receipt.json`)** | | | | |
| `multi_turn_p_star_operad_slot_materialization` (3-slot Stage 1 `(s, i*, c'_{i*})`) | `8/8` (`100.0%`) | **`1/8` (`12.5%`)** | **`1/8` (`12.5%`)** | Solved `c004_k3_01` (`-1 -1 2`, $\Phi_1 = 0$, optimal cost `5`). |
| **Trial 4 (`p_star_4slot_binding_receipt.json`)** | | | | |
| `p_star_4slot_index_value_binding` (4-slot Stage 1 `(s, i*, c_{i*}, c'_{i*})`) | `8/8` (`100.0%`) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | `0.5B` model failed cycle-sum arithmetic in slot 0 (`0/8` sum exact). |
| **Trial 5 (`p_star_verified_guard_receipt.json`, C004-S5)** | | | | |
| `p_star_verified_stage1_complete_guard` ($G_{\text{complete}}$ + 1 retry + `NullTree` abstention) | `8/8` Stage 1 (`0/8` Stage 2 admitted) | `0/8` (`0.0%`) | `0/8` (`0.0%`) | **Prevented `8/8` (`100%`) wasted Stage-2 calls** via `STAGE1_GUARD_NULL_TREE_ABSTENTION` (Theorem 5.4). |
| `no_model_exact_cochain_baseline` (`NO_LLM` oracle) | `8/8` (`100.0%`) | `8/8` (`100.0%`) | `8/8` (`100.0%`) | Deterministic host lightest-edge coboundary control (Theorem 2). |

#### Table 2: Panel 2 — Accounted OpenRouter `openai/gpt-4o-mini` ($N = 8$ C004 cases)

| Trial & Arm | Calls / Settled Spend | Parseable | Stage-1 Invariant Accuracy | Certified `ExactCoboundary` ($\Phi_1 = 0, \Gamma_2 = 0$) | Exact $\ell_1$-Optimal Repair |
| --- | --- | --- | --- | --- | --- |
| **Trial 1 (`c004_paired_benchmark_receipt.json`)** | | | | | |
| `hosted_unconstrained` | 8 calls / `$0.0011` | `0/8` (`0.0%`) | N/A | `0/8` (`0.0%`) | `0/8` (`0.0%`) |
| `hosted_slot_constrained` (`gbnf_slots=k`) | 8 calls / `$0.0012` | `8/8` (`100.0%`) | N/A | `2/8` (`25.0%`) | `0/8` (`0.0%`) |
| **Trial 2 (`operad_cochain_ablation_receipt.json`)** | | | | | |
| `plain_grammar_projection` (1-turn) | 8 calls / `$0.0011` | `8/8` (`100.0%`) | N/A | `5/8` (`62.5%`) | `1/8` (`12.5%`) |
| `operad_grafted_grammar_projection` (1-turn, 0 intermediate slots) | 8 calls / `$0.0018` | `8/8` (`100.0%`) | N/A (0 intermediate slots) | `0/8` (`0.0%`) | `0/8` (`0.0%`) |
| **Trial 3 (`p_star_operad_materialization_receipt.json`)** | | | | | |
| `plain_grammar_projection` (1-turn matched control) | 8 calls / `$0.0011` | `8/8` (`100.0%`) | N/A | `6/8` (`75.0%`) | `1/8` (`12.5%`) |
| `multi_turn_p_star_operad_slot_materialization` (2-turn `P*`, 3-slot `(s, i*, c'_{i*})`) | 16 calls / `$0.0031` | `8/8` (`100.0%`) | `s`: `7/8` (`87.5%`), `i*`: `5/8` (`62.5%`), `c'_{i*}`: `2/8` (`25.0%`), all 3: `2/8` (`25.0%`) | `3/8` (`37.5%`) | **`2/8` (`25.0%`)** |
| **Trial 4 (`p_star_4slot_binding_receipt.json`)** | | | | | |
| `p_star_4slot_index_value_binding` (2-turn `P*`, 4-slot `(s, i*, c_{i*}, c'_{i*})`, unverified) | 16 calls / `$0.002994` | `8/8` (`100.0%`) | `s`: `7/8` (`87.5%`), `i*`: `5/8` (`62.5%`), `c_{i*}`: `5/8` (`62.5%`), `c'_{i*}`: `4/8` (`50.0%`), all 4: `3/8` (`37.5%`) | `5/8` (`62.5%`) | **`3/8` (`37.5%`)** |
| **Trial 5 (`p_star_verified_guard_receipt.json`, C004-S5)** | | | | | |
| **`p_star_verified_stage1_complete_guard` ($G_{\text{complete}}$ + 1 diagnostic retry, $R=2$)** | 7 incremental calls / `$0.001472` | `5/5` admitted (`3` abstained via `NullTree`) | `s`: **`7/8` (`87.5%`)**, `i*`: **`7/8` (`87.5%`)**, `c_{i*}`: **`7/8` (`87.5%`)**, `c'_{i*}`: **`5/8` (`62.5%`)**, all 4: **`5/8` (`62.5%`)** | **`5/8` (`62.5%`)** (`5/5` = **`100%` of admitted**) | **`5/8` (`62.5%`)** (`5/5` = **`100%` conditional precision**) |

### 6.3 Diagnostic analysis of the 5-trial C004 progression

1. **Layer 2 (`gbnf_slots=k`) is necessary for syntax admissibility but insufficient for mathematical validity:**
   Across both local `Qwen2.5-0.5B-Instruct` and hosted `openai/gpt-4o-mini`,
   unconstrained decoding (`free` / `hosted_unconstrained`) achieved `0/8`
   (`0.0%`) parseable integer-slot tuples, whereas Layer-2 grammar projection
   achieved `8/8` (`100.0%`) parseable tuples. However, grammar compliance alone
   yielded `0/8` $\ell_1$-optimal repairs in Trial 1, confirming Theorem 1's
   separation between surface decoding ($D$) and Layer-3 mathematical checking
   ($C$).
2. **Single-turn zero-scratchpad operad trees induce a causal ordering failure:**
   In Trial 2, rendering a 6-operator `ColouredOperadPrompt` tree inside a
   single zero-scratchpad turn (`operad_grafted_grammar_projection`) collapsed
   `openai/gpt-4o-mini` from `5/8` `ExactCoboundary` (`1/8` optimal) down to
   `0/8` `ExactCoboundary` (`0/8` optimal), with `4/8` cases copying the
   unrepaired input claims verbatim (`weighted_l1 = 0`).
3. **2-turn `P*` staged operad slot materialization (`(s, i*, c'_{i*})`) restores and doubles $\ell_1$-optimal repair:**
   In Trial 3, cutting the operad tree so Stage 1 materializes `(s, i*, c'_{i*})`
   (`gbnf_slots=3`) before host slot-grafting ($\circ_i$) into Stage 2
   (`gbnf_slots=k`) raised `openai/gpt-4o-mini` from `0/8 -> 3/8`
   `ExactCoboundary` and `0/8 -> 2/8` (`25.0%`) $\ell_1$-optimal (`c004_k3_02`,
   `c004_k4_02`), and raised local `Qwen2.5-0.5B-Instruct` from `0/8 -> 1/8`
   (`12.5%`) optimal (`c004_k3_01`). Crucially, Stage-1 grading exposed the
   exact remaining bottleneck: `openai/gpt-4o-mini` computed $s$ accurately on
   `7/8` (`87.5%`) cases and $i^*$ accurately on `5/8` (`62.5%`) cases, but
   failed on slot 2 ($c'_{i^*} = c_{i^*} - s$) on `3/5` of the exact-`(s, i*)`
   cases because it had to dereference $c_{i^*}$ at the just-emitted index $i^*$
   and subtract $s$ in a single token step.
4. **4-slot Stage-1 index-value binding (`(s, i*, c_{i*}, c'_{i*})`) resolves the dereference bottleneck and raises $\ell_1$-optimality to `3/8` (`37.5%`):**
   In Trial 4, inserting an explicit slot for the looked-up claim value $c_{i^*}$
   (`gbnf_slots=4`) yielded `5/5` (`100%`) exact lookup of $c_{i^*}$ whenever
   $i^*$ was exact (and `8/8` / `100%` consistent dereferencing $c[\hat{i}^*]$
   at the model's chosen index $\hat{i}^*$). This doubled Stage-1 $c'_{i^*}$
   accuracy from `2/8` (`25.0%`) to `4/8` (`50.0%`), raised Stage-2
   `ExactCoboundary` certification from `3/8` (`37.5%`) to `5/8` (`62.5%`), and
   raised exact $\ell_1$-optimal repair from `2/8` (`25.0%`) to `3/8` (`37.5%`)
   (`c004_k4_01`, `c004_k4_02`, `c004_k5_01`), with `3/3` (`100%`) Stage-2
   $\ell_1$-optimality whenever Stage 1 materialized all 4 slots accurately.
5. **Evaluator-verified Stage-1 guard filtering + 1 diagnostic retry (`C004-S5`) raises exact $\ell_1$-optimality to `5/8` (`62.5%`) with `5/5` (`100%`) conditional precision and witnesses Theorem 6:**
   In Trial 5 (`p_star_verified_guard_receipt.json`), applying the deterministic
   complete Stage-1 guard $G_{\text{complete}}$ with $R = 2$ (at most 1 diagnostic
   retry on the 5 cases that failed Attempt 1):
   - Repaired `c004_k3_01` from Attempt 1 `5 1 -1 -6` (`GUARD_FAIL_MIN_WEIGHT_INDEX`)
     to Retry 1 **`5 0 4 -1`**, whose admitted Stage-2 graft emitted **`-1 -1 2`**
     (certified `ExactCoboundary` and $\ell_1$-optimal at cost `5`).
   - Repaired `c004_k3_02` from Attempt 1 `4 1 6 -2` (`GUARD_FAIL_SUBTRACTION_INVARIANT`:
     $-2 + 4 = 2 \ne 6$) to Retry 1 **`4 1 6 2`**, whose admitted Stage-2 graft
     emitted **`-3 2 1`** (certified `ExactCoboundary` and $\ell_1$-optimal at cost `4`).
   - Raised Stage-1 all-4-slot accuracy from `3/8` (`37.5%`) to **`5/8` (`62.5%`)**,
     achieved **`5/5` (`100.0%`) conditional $\ell_1$-optimal precision** across
     all admitted Stage-2 grafts (Theorem 5.2), raised unconditional $\ell_1$-optimal
     repair from `3/8` (`37.5%`) to **`5/8` (`62.5%`)** (Theorem 5.3), and
     abstained via `NullTree` on the remaining `3/8` Panel-2 cases and `8/8`
     Panel-1 cases, preventing `3` and `8` wasted Stage-2 calls respectively
     (Theorem 5.4).
   - **Concrete Local Green / Global Red Witness for Theorem 6 (`c004_k6_01` retry):**
     On `c004_k6_01` ($c = (3, -2, 4, -1, 2, -3)$, $w = (3, 2, 1, 2, 3, 2)$,
     true sum $s(c) = 3$, $i^* = 2$, $c_2 = 4$), Attempt 1 emitted `-1 1 -2 1`
     (failing `GUARD_FAIL_MIN_WEIGHT_INDEX`, `GUARD_FAIL_SUBTRACTION_INVARIANT`,
     and `GUARD_FAIL_CYCLE_SUM`). On Retry 1, `openai/gpt-4o-mini` emitted
     **`z_1 = (0, 2, 4, 4)`**, which **passed the partial guard
     $G_{\text{partial}}(x, z_1) = 1$** (since $w_2 = 1 = \min_j w_j$,
     $\hat{c}_2 = 4 = c_2$, and $\hat{c}'_2 + \hat{s} = 4 + 0 = 4 = c_2$), yet
     belonged to the false-green kernel $\mathcal{K}_{\text{false}}(x)$ at
     $\Delta s = 0 - 3 = -3 \ne 0$ (Theorem 6.1)! Because $G_{\text{complete}}$
     checked $\hat{s} = \sum_j c_j = 3$, it caught `GUARD_FAIL_CYCLE_SUM` and
     projected Retry 1 to `NullTree` before Stage 2.

### 6.4 Trial 6 (`C006-S6`): Paired multi-cycle overlap-basis cochain repair on $K_4$ ($b_1 = 3 \ge 2$)

To test whether `P*` staged slot materialization and complete Stage-1 guard
filtering extend from single cycles ($b_1 = 1$) to overlapping multi-cycle
complexes ($b_1 = \dim H_1(G) \ge 2$), we executed a bounded paired trial
(`c006_overlap_basis_p_star_receipt.json`) across $N = 4$ deterministic $K_4$
multi-cycle overlap boards (`round5-K4-diagnostic` at $\Phi_1 = 6$,
`C006-v2-r3-s6030` at $\Phi_1 = 16$, `C006-v2-r3-s6031` at $\Phi_1 = 9$, and
weighted board `C006-v2-r3-s6032-weighted` at $\Phi_1 = 12$ with $w_T = 3, w_{E \setminus T} = 1$).
Each board has $|V|=4, |E|=6, b_1 = 3$, and an explicit non-star spanning tree
$T$ whose central edge is shared by all $3$ chord-induced cycles
(`max_tree_edge_cycle_incidence = 3`).

#### Table 3: Trial 6 (`C006-S6`, $N = 4$ $K_4$ multi-cycle overlap boards, $b_1 = 3$)

| Panel & Arm | Calls / Reserved Spend | Stage-1 $G_{\text{partial}}^{\text{C006}}$ Pass (`Att 1`) | Stage-1 $G_{\text{complete}}^{\text{C006}}$ Pass (`Att 1 -> Retry 1`) | Stage-2 `NullTree` Abstentions / Saved Turns | Solved `ACCEPTED_ZERO_DEFECT` ($\Phi_1 = 0$) | Conditional Stage-2 Solve Rate |
| --- | --- | --- | --- | --- | --- | --- |
| **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local)** | | | | | | |
| `c006_unstaged_action_generation` (3-turn session) | 0 provider calls / `$0` | N/A | N/A | `0/4` (`0` turns saved) | `0/4` (`0.0%`) | `0/4` (`12/12` turns failed `TASK_ENVELOPE`) |
| `c006_p_star_staged_guarded_overlap_repair` (`P*` + $G_{\text{complete}}^{\text{C006}}$, $R=2$) | 0 provider calls / `$0` | `0/4` (`0.0%`) | `0/4 -> 0/4` (`0.0%`) | **`4/4` (`12` Stage-2 turns saved)** | `0/4` (`0.0%`) | N/A (`0` corrupted Stage-2 admits) |
| `no_model_exact_c006_baseline` (`NO_LLM` oracle) | 0 provider calls / `$0` | `4/4` (`100.0%`) | `4/4` (`100.0%`) | `0/4` | **`4/4` (`100.0%`)** | **`4/4` (`100.0%`, `4/4` replay verified)** |
| **Panel 2 (`openai/gpt-4o-mini`, OpenRouter)** | | | | | | |
| `c006_unstaged_action_generation` (3-turn session) | 12 calls / `$0.0044` | N/A | N/A | `0/4` (`0` turns saved) | **`0/4` (`0.0%`)** | `0/4` (`12/12` rejected: `NO_STRICT_DESCENT` / `AM-4-STATIONARY-REPEAT`) |
| **`c006_p_star_staged_guarded_overlap_repair` (`P*` + $G_{\text{complete}}^{\text{C006}}$, $R=2$)** | 14 calls / `$0.0049` (`$0.009252` total reserved) | **`2/4` (`50.0%` false-green witnesses)** | **`0/4 -> 2/4` (`50.0%`)** | **`2/4` (`6` Stage-2 turns saved)** | **`2/4` (`50.0%`)** | **`2/2` (`100.0%`, `2/2` replay verified)** |

**Key multi-cycle findings from Trial 6 (`C006-S6`):**

1. **Un-staged multi-cycle action generation (`0/4` solved) stalls in stationary repetition:**
   Without a Stage-1 basis-materialization turn, `openai/gpt-4o-mini` emitted
   `{"move": "CUT", "claims": <unchanged initial claims>}` on all 12 turns across
   all 4 $K_4$ boards, triggering `NO_STRICT_DESCENT` and `AM-4-STATIONARY-REPEAT`
   at $\Phi_1 \in \{6, 16, 9, 12\}$.
2. **Three empirical multi-cycle Local Green / Global Red witnesses for Theorem 7.2:**
   On Attempt 1, `openai/gpt-4o-mini` produced two 9-slot tuples in the
   partial-guard visibility gap $\mathcal{K}_{\text{false}}^{\text{C006}}(x) \cong \mathbb{Z}^6 \setminus \{0\}$
   that satisfied $\hat{c}'_{g_m} + \hat{r}_m = c_{g_m}$ on all 3 chords
   ($G_{\text{partial}}^{\text{C006}} = 1$) while failing $G_{\text{complete}}^{\text{C006}}$:
   `round5-K4-diagnostic` Attempt 1 (`"1 3 5 -2 -2 -4 5 3 6"`) and
   `C006-v2-r3-s6030` Attempt 1 (`"28 -27 16 16 27 12 8 -23 8"`). Moreover, on
   `round5-K4-diagnostic` Retry 1, it emitted **`"1 3 4 -2 -1 -3 5 2 5"`**, where
   the tree potentials $(1, 3, 4)$ were exact ($\Delta p = (0, 0, 0)$) and
   $\hat{c}'_{g_m} + \hat{r}_m = c_{g_m}$ held on all 3 chords ($-2+5=3$,
   $-1+2=1$, $-3+5=2$, so $G_{\text{partial}}^{\text{C006}} = 1$), yet
   $\Delta r = (-1, 4, -1) \ne 0$ so $\hat{c}'_{g_m} \ne \hat{p}(v_m) - \hat{p}(u_m)$!
   Checking $G_{\text{complete}}^{\text{C006}}$ caught all 3 false-green tuples
   before Stage 2.
3. **Triangular chord decoupling + 1 diagnostic retry lifts multi-cycle zero-defect repair from `0/4` to `2/4` (`50.0%`) with `2/2` (`100%`) conditional Stage-2 precision:**
   On Retry 1, `openai/gpt-4o-mini` repaired its sign-subtraction errors on both
   `C006-v2-r3-s6031` (`"-4 0 -2 4 2 2 -1 5 1"` $\to$ **`"-4 0 -2 0 -2 2 3 -5 1"`**)
   and weighted board `C006-v2-r3-s6032-weighted` (`"2 1 3 1 3 2 3 -1 1"` $\to$
   **`"2 1 3 -1 3 1 5 -5 2"`**). Both passed $G_{\text{complete}}^{\text{C006}}$,
   were grafted via $\circ_i$ into Stage 2 (`ASSERT` $\to$ `CUT` $\to$ `VERIFY`),
   and achieved certified `ACCEPTED_ZERO_DEFECT` ($\Phi_1 = 0$, primal-dual
   certificate verified, zero-send `replay_session` verified), while `NullTree`
   abstention prevented `6` hosted (`12` local) wasted Stage-2 turns.

### 6.5 Trial 7 (`C006-S7`): Higher-Betti ($b_1 \in \{4, 5, 6, 7\}$) two-stage tree-then-chord `P*` factorization across $K_{3,3}, Q_3, K_5, \text{Petersen}, W_7$

To test Theorem 8 across non-planar and higher-Betti multi-cycle topologies, we
executed a bounded paired trial (`c006_higher_betti_p_star_receipt.json`) across
$N = 5$ deterministic boards from `c006.panels.v2`:
- `C006-v2-r4-s6040` ($K_{3,3}$, $|V|=6, |E|=9, b_1=4$, initial $\Phi_1 = 14$, single-stage arity $13 \to$ two-stage max arity $5$)
- `C006-v2-r5-s6050` ($Q_3$, $|V|=8, |E|=12, b_1=5$, initial $\Phi_1 = 22$, single-stage arity $17 \to$ two-stage max arity $7$)
- `C006-v2-r6-s6060` ($K_5$, $|V|=5, |E|=10, b_1=6$, initial $\Phi_1 = 18$, single-stage arity $16 \to$ two-stage max arity $6$)
- `C006-v2-r6-s6061` ($\text{Petersen}$, $|V|=10, |E|=15, b_1=6$, initial $\Phi_1 = 24$, single-stage arity $21 \to$ two-stage max arity $9$)
- `C006-v2-r7-s6070` ($W_7$, $|V|=8, |E|=14, b_1=7$, initial $\Phi_1 = 28$, single-stage arity $21 \to$ two-stage max arity $7$)

#### Table 4: Trial 7 (`C006-S7`, $N = 5$ higher-Betti boards, $b_1 \in \{4, 5, 6, 7\}$)

| Panel & Arm | Calls / Reserved Spend | Stage-1a $G_T$ Pass (`Att 1 -> Retry 1`) | Stage-1b $G_C$ Pass (`Att 1`) | `NullTree` Abstentions / Saved Turns | Solved `ACCEPTED_ZERO_DEFECT` ($\Phi_1 = 0$) | Conditional Stage-2 Solve Rate |
| --- | --- | --- | --- | --- | --- | --- |
| **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local)** | | | | | | |
| `c006_unstaged_action_generation` (3-turn session) | 0 provider calls / `$0` | N/A | N/A | `0/5` (`0` turns saved) | `0/5` (`0.0%`) | `0/5` (`0.0%`) |
| `c006_p_star_2stage_tree_chord_guarded_repair` (`C006-S7`, $R_{1a}=2, R_{1b}=2$) | 0 provider calls / `$0` | `0/5 -> 0/5` (`0.0%`) | `0/0` | **`5/5` (`20` downstream turns saved)** | `0/5` (`0.0%`) | N/A (`0` corrupted admits) |
| `no_model_exact_c006_higher_betti_baseline` (`NO_LLM` oracle) | 0 provider calls / `$0` | `5/5` (`100.0%`) | `5/5` (`100.0%`) | `0/5` | **`5/5` (`100.0%`)** | **`5/5` (`100.0%`, `5/5` replay verified)** |
| **Panel 2 (`openai/gpt-4o-mini`, OpenRouter)** | | | | | | |
| `c006_unstaged_action_generation` (3-turn session) | 15 calls | N/A | N/A | `0/5` (`0` turns saved) | **`0/5` (`0.0%`, final $\Phi_1 = (14, 22, 18, 24, 28)$)** | `0/5` (`0.0%`) |
| **`c006_p_star_2stage_tree_chord_guarded_repair` (`C006-S7`, $R_{1a}=2, R_{1b}=2$)** | 26 calls (`$0.02294` total reserved $\le \$0.050$ cap) | **`4/5 -> 5/5` (`100.0%`; Petersen recovered on Retry 1)** | **`5/5` (`100.0%` on Attempt 1, `0` retries)** | **`0/5` (`5/5` admitted)** | **`5/5` (`100.0%` across $K_{3,3}, Q_3, K_5, \text{Petersen}, W_7$)** | **`5/5` (`100.0%`, `5/5` replay verified)** |

**Key higher-Betti findings from Trial 7 (`C006-S7`):**

1. **Two-stage tree-then-chord factorization lifts higher-Betti solve rate from `0/5` (`0.0%`) to `5/5` (`100.0%`) on `openai/gpt-4o-mini`:**
   In un-staged action generation, `openai/gpt-4o-mini` solved `0/5` boards across
   $b_1 \in \{4, 5, 6, 7\}$, leaving every board at its initial compatibility defect
   $\Phi_1 \in \{14, 22, 18, 24, 28\}$. Under two-stage `P*` factorization
   (Theorem 8.1), Stage 1a (`G_T`, arity $|V|-1 \in \{5, 7, 4, 9, 7\}$) passed on
   Attempt 1 for $K_{3,3}, Q_3, K_5,$ and $W_7$ (`4/5 = 80.0%`), and on the
   10-vertex Petersen cage (`C006-v2-r6-s6061`, 9 tree-potential slots) a single
   targeted tree-edge retry (`build_c006_stage1a_retry_turn`) repaired the failed
   tree-edge slots to pass $G_T$ (`5/5 = 100.0%`).
2. **`100%` Attempt-1 chord-coboundary accuracy once verified tree potentials are grafted (Theorem 8.2):**
   Once $p_T^*$ was verified by $G_T$ and grafted into Stage 1b, `openai/gpt-4o-mini`
   computed all $b_1 \in \{4, 5, 6, 6, 7\}$ repaired chord claims
   $\hat{c}'_{g_m} = p_T^*(v_m) - p_T^*(u_m)$ with **`5/5` (`100.0%`) exactness
   on Attempt 1** (`0` Stage-1b retries needed), and all `5/5` (`100.0%`)
   Stage-2 3-turn sessions (`ASSERT` $\to$ `CUT` $\to$ `VERIFY`) terminated in
   certified `ACCEPTED_ZERO_DEFECT` ($\Phi_1 = 0$).

### 6.6 Trial 8 (`C005-S1`): Dichotomic Fredholm-alternative `P*` guarded separation across 8 public difference boards

To test Theorem 9 on dichotomic (`CONSISTENT` vs. `INCONSISTENT`) verification,
we executed a bounded paired trial (`c005_dichotomic_fredholm_p_star_receipt.json`)
across all $N = 8$ public `C005` difference boards (`pub_cons_01`..`pub_cons_08`,
`4` `CONSISTENT` and `4` `INCONSISTENT`, $|V| \in \{4, 5, 6\}, b_1 \in \{1, 2\}$).

#### Table 5: Trial 8 (`C005-S1`, $N = 8$ public `C005` difference boards, `4` consistent + `4` inconsistent)

| Panel & Arm | Calls / Reserved Spend | Stage-1 $G_{\text{Fredholm}}$ Pass (`Att 1 -> Retry 1`) | Consistent Solved (`4` boards) | Inconsistent Solved (`4` boards) | Total Solved (`8` boards) | Lazy False `INCONSISTENT` Count | Admitted False Verdicts | Conditional Stage-2 Precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local)** | | | | | | | | |
| `c005_unstaged_consistency_verdict` | 0 calls / `$0` | N/A | **`0/4` (`0.0%`)** | `4/4` (`100.0%`) | `4/8` (`50.0%`) | **`4/4` (`100.0%`)** | `4/8` (`50.0%`) | `4/8` (`50.0%`) |
| `c005_p_star_dichotomic_fredholm_guarded` (`C005-S1`, $R=2$) | 0 calls / `$0` | `0/8 -> 0/8` (`0.0%`) | `0/4` (`4/4` `NullTree`) | `0/4` (`4/4` `NullTree`) | `0/8` | **`0` (`0.0%`)** | **`0` (`0.0%`)** | N/A (`8/8` `NullTree` abstentions) |
| `no_model_exact_c005_baseline` (`NO_LLM` oracle) | 0 calls / `$0` | `8/8` (`100.0%`) | `4/4` (`100.0%`) | `4/4` (`100.0%`) | **`8/8` (`100.0%`)** | `0` | `0` | **`8/8` (`100.0%`)** |
| **Panel 2 (`openai/gpt-4o-mini`, OpenRouter)** | | | | | | | | |
| `c005_unstaged_consistency_verdict` | 8 calls | N/A | **`0/4` (`0.0%`)** | `3/4` (`75.0%`) | **`3/8` (`37.5%`)** | **`3` (`75.0%` of consistent boards)** | **`5/8` (`62.5%`)** | `3/8` (`37.5%`) |
| **`c005_p_star_dichotomic_fredholm_guarded` (`C005-S1`, $R=2$)** | 21 calls (`$0.003636` total reserved $\le \$0.050$ cap) | **`1/8 -> 6/8` (`75.0%`; `2/8` `NullTree`)** | **`3/4` (`75.0%`)** | **`3/4` (`75.0%`)** | **`6/8` (`75.0%`)** | **`0` (`0.0%`)** | **`0` (`0.0%`)** | **`6/6` (`100.0%`, `6/6` replay verified)** |

**Key dichotomic findings from Trial 8 (`C005-S1`):**

1. **Empirical confirmation of the lazy false-refusal attractor in un-staged generation:**
   In un-staged generation, both `Qwen/Qwen2.5-0.5B-Instruct` (`0/4` consistent,
   `4/4` lazy false `INCONSISTENT`) and `openai/gpt-4o-mini` (`0/4` consistent,
   `3/4` lazy false `INCONSISTENT`) solved **`0.0%` of consistent boards**,
   defaulting to `INCONSISTENT` whenever their unverified mental tree integration
   encountered a chord discrepancy.
2. **Elimination of admitted false verdicts and `2x` overall solve-rate improvement under $G_{\text{Fredholm}}$ (Theorem 9):**
   Enforcing $G_{\text{Fredholm}}$ with at most 1 equation-specific diagnostic
   retry lifted `openai/gpt-4o-mini`'s Stage-1 pass rate from `1/8` (`12.5%`) on
   Attempt 1 to **`6/8` (`75.0%`)** after Retry 1 (`3` consistent + `3`
   inconsistent boards admitted; `2/8` projected to `NullTree`), raised consistent
   board accuracy from **`0/4` (`0.0%`) to `3/4` (`75.0%`)**, doubled overall
   accuracy from **`3/8` (`37.5%`) to `6/8` (`75.0%`)** (`6/6 = 100.0%`
   conditional precision), and reduced both `lazy_false_inconsistent_count` and
   `admitted_false_verdict_count` to **`0`** across both panels.

### 6.7 Trial 9 (`C001-S1`): Distractor-filtered cochain & cohomological syndrome `P*` factorization across 12 public and poisoned cases

To test Theorems 10 and 11 on larger graphs with 4-digit integer claims
($c_{u,v} \in [-5000, 5000]$, $|V| \in \{8, 9, 10, 11\}$, $|E| \in \{12, \dots, 16\}$,
$b_1 \in \{5, 7\}$) and bracketed natural-language distractors (`[Note k: ...]`),
we executed a bounded paired trial (`c001_distractor_cochain_p_star_receipt.json`)
across $N = 12$ cases from `c001/public_cases.json` and `c001/poisoned_cases.json`:
- `4` public `verdict` cases (`c001_verdict_1000`..`1003`: `2` `CONSISTENT`, `2` `CONTRADICTION`),
- `3` public `repair` cases (`c001_repair_1100`..`1102`: chord perturbations `['H','C'] -> -30` and `['A','G'] -> -3387`, plus spanning-tree perturbation `['D','C'] -> 2408` propagating across 4 chord cycles),
- `2` public `audit` cases (`c001_audit_1200` `ACCEPT`, `c001_audit_1201` `REJECT`), and
- `3` adversarial `poisoned` cases (`c001_poisoned_almost_valid_4000` with an off-by-one `+1` cycle discrepancy, `c001_poisoned_flipped_sign_4100` with a flipped edge orientation, and `c001_poisoned_deceptive_verdict_4200` with a deceptive `CONTRADICTION` claim on a consistent graph).

#### Table 6: Trial 9 (`C001-S1`, $N = 12$ distractor-filtered 4-digit rank-difference cases, $b_1 \in \{5, 7\}$)

| Panel & Arm | Calls / Reserved Spend | Stage-1a $G_T$ Pass (`Att 1 -> Retry 1`) | Stage-1b $G_C$ Pass (`Att 1 -> Retry 1`) | Solved Verdict (`6`) | Solved Repair (`3`) | Solved Audit (`3`) | Solved Public (`9`) / Poisoned (`3`) | Total Solved (`12`) | False `SOLVED` Verdicts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local)** | | | | | | | | | |
| `c001_unstaged_witness_generation` (1-shot JSON) | 0 calls / `$0` | N/A | N/A | `0/6` | `0/3` | `0/3` | `0/9` / `0/3` | `0/12` (`0.0%`) | `1/12` (`8.3%`) |
| `c001_p_star_carrier_cochain_syndrome_guarded` (`C001-S1`, $R_{1a}=2, R_{1b}=2$) | 0 calls / `$0` | `0/12 -> 0/12` | `0/0` (`12` saved) | `0/6` | `0/3` | `0/3` | `0/9` / `0/3` | `0/12` (`12/12` `NullTree`) | **`0/12` (`0.0%`)** |
| `no_model_exact_c001_baseline` (`NO_LLM` oracle) | 0 calls / `$0` | `12/12` (`100%`) | `12/12` (`100%`) | `6/6` (`100%`) | `3/3` (`100%`) | `3/3` (`100%`) | `9/9` / `3/3` (`100%`) | **`12/12` (`100.0%`)** | **`0/12` (`0.0%`)** |
| **Panel 2 (`openai/gpt-4o-mini`, OpenRouter)** | | | | | | | | | |
| `c001_unstaged_witness_generation` (1-shot JSON) | 12 calls | N/A | N/A | **`0/6` (`0.0%`)** | **`0/3` (`0.0%`)** | `1/3` (`33.3%`) | `1/9` (`11.1%`) / **`0/3` (`0.0%`)** | **`1/12` (`8.3%`)** | **`11/12` (`91.7%`)** |
| **`c001_p_star_carrier_cochain_syndrome_guarded` (`C001-S1`, $R_{1a}=2, R_{1b}=2$)** | 41 calls (`$0.012427` total reserved $\le \$0.050$ cap) | **`1/12 -> 12/12` (`100.0%`)** | **`6/12 -> 12/12` (`100.0%`)** | **`6/6` (`100.0%`)** | **`3/3` (`100.0%`)** | **`3/3` (`100.0%`)** | **`9/9` (`100.0%`) / `3/3` (`100.0%`)** | **`12/12` (`100.0%`)** | **`0/12` (`0.0%`)** |

**Key findings from Trial 9 (`C001-S1`):**

1. **Collapse of un-staged 1-shot witness generation under 4-digit arithmetic and adversarial distractors (`1/12 = 8.3%`):**
   In un-staged generation, `openai/gpt-4o-mini` solved `0/6` `verdict` cases,
   `0/3` `repair` cases, and `0/3` adversarial `poisoned` cases (`1/12 = 8.3%`
   overall, solving only `c001_audit_1200`), emitting **`11/12` (`91.7%`) false
   `SOLVED` verdicts** whose potentials failed $B\mathbf{p} = \mathbf{c}$ or
   whose cycles failed simple-cycle non-zero holonomy verification.
2. **Empirical verification of Theorem 11 (Edge-local coboundary defect migration vs. path-integrated $B_T^{-1}$ retry convergence):**
   Because the spanning-tree claims $c_{u,v} \in [-5000, 5000]$ are 4-digit
   signed integers across $7$ to $10$ tree hops, `openai/gpt-4o-mini` passed
   Stage 1a ($G_T$) on Attempt 1 on only `1/12` (`8.3%`) cases (`c001_poisoned_almost_valid_4000`).
   Under an initial edge-local retry diagnostic ($B_T \hat{p}_T^{(1)} \ne \mathbf{c}|_T$),
   fixing a flagged parent slot $v^*$ while retaining its unflagged descendants
   $w \in \operatorname{Subtree}_T(v^*) \setminus \{v^*\}$ caused the coboundary
   defect to migrate to the child edges $(v^* \to w)$ (`2/12 = 16.7%` convergence).
   Switching to the path-integrated diagnostic $\hat{p}_T^{(1)}(w) \ne (B_T^{-1}\mathbf{c}|_T)_w$
   (Theorem 11.3) flagged the entire shifted subtree simultaneously and lifted
   Stage-1a retry convergence from `1/12` (`8.3%`) on Attempt 1 (and `2/12` under
   edge-local retry) to **`12/12` (`100.0%`)** on Retry 1!
3. **Cohomological syndrome decoding $\mathbf{r}^* = S\mathbf{c}$ solves `12/12` (`100.0%`) across `verdict`, chord/tree `repair`, `audit`, and `poisoned` traps (Theorem 10):**
   Stage 1b ($G_C$) converged from `6/12` (`50.0%`) on Attempt 1 to **`12/12`
   (`100.0%`)** after Retry 1. From the verified pair $(p_T^*, \hat{\mathbf{c}}^*)$,
   the syndrome $\mathbf{r}^* = \hat{\mathbf{c}}^* - \mathbf{c}|_{E \setminus T} = S\mathbf{c}$
   decoded:
   - all `6/6` `verdict` cases (including `c001_poisoned_almost_valid_4000` and
     `c001_poisoned_deceptive_verdict_4200`),
   - all `3/3` single-edge `repair` cases—both unit-support chord perturbations
     (`c001_repair_1100`: `['H', 'C'] -> -30`; `c001_repair_1102`: `['A', 'G'] -> -3387`,
     Theorem 10.2a) and the multi-cycle spanning-tree perturbation
     (`c001_repair_1101`: `['D', 'C'] -> 2408` with cutset support of size $4$,
     Theorem 10.2b), and
   - all `3/3` `audit` cases (including `c001_poisoned_flipped_sign_4100`),
   with **`0/12` false `SOLVED` verdicts** across both panels.

### 6.8 Trial 10 (`C004-S6`): Held-out 40-case directed cycle ladder ($k \in \{3, \dots, 12\}$)

To test Theorem 5 and Theorem 6 beyond $k \le 6$ on a held-out 7B open-weight
checkpoint (`qwen/qwen-2.5-7b-instruct` on OpenRouter, with local hardware VRAM
boundary recorded at `4.0 GB` RTX 3050 vs. `15.24 GB` bf16 requirement alongside
local `Qwen/Qwen2.5-0.5B-Instruct`), we executed the held-out 40-case `C004`
ladder (`c004_40case_hidden_p_star_receipt.json`, `4` cases per cycle length
$k \in \{3, \dots, 12\}$):

- **`NO_LLM` exact baseline (`no_model_exact_c004_40case_baseline`):** `40/40`
  (`100.0%`) certified `ExactCoboundary` and $\ell_1$-optimal (`16/16` in
  $k \in \{3..6\}$, `16/16` in $k \in \{7..10\}$, `8/8` in $k \in \{11, 12\}$).
- **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local):** Un-staged slot-constrained
  decoding admitted all `40/40` proposals with `3/40` (`7.5%`) `ExactCoboundary`
  and `1/40` (`2.5%`) $\ell_1$-optimal (`39/40` suboptimal admissions). Under
  `P*` complete guard $G_{\text{complete}}$, all `40/40` failed Stage 1 after
  1 retry and abstained via `NullTree` (`0` suboptimal Stage-2 admissions).
- **Panel 2 (`qwen/qwen-2.5-7b-instruct`, OpenRouter, `121` calls at `$0.018452`):**
  Un-staged slot-constrained decoding admitted all `40/40` proposals with `9/40`
  (`22.5%`) `ExactCoboundary` and **`0/40` (`0.0%`) $\ell_1$-optimal**. Under
  `P*` complete guard $G_{\text{complete}}$, Attempt 1 produced `4` partial-guard
  passes ($G_{\text{partial}} = 1$), of which **`3` were concrete Local Green /
  Global Red witnesses** ($\hat{s} \ne \sum_j c_j$, Theorem 6) caught only by
  $G_{\text{complete}}$. After 1 diagnostic retry, `2/40` cases passed
  $G_{\text{complete}}$ and were admitted to Stage 2, and **both (`2/2 = 100.0%`
  conditional Stage-2 precision)** achieved certified `ExactCoboundary` and
  exact $\ell_1$-optimality (`38/40` `NullTree` abstentions, `0` suboptimal
  admissions).

### 6.9 Trial 11 (`C006-S8`): Held-out 60-board multi-cycle campaign ($b_1 \in \{3, \dots, 8\}$ across 7 graph families)

To test Theorem 8 across 60 held-out multi-cycle boards spanning cycle ranks
$b_1 \in \{3, 4, 5, 6, 7, 8\}$ (`10` boards per cycle rank across `K4`, `K3,3`,
`cube-Q3`, `K5`, `Petersen`, `wheel-7-rim`, and `wheel-8-rim`), we executed
`c006_60board_hidden_p_star_receipt.json`:

- **`NO_LLM` exact baseline (`no_model_exact_c006_60board_baseline`):** `60/60`
  (`100.0%`) `ACCEPTED_ZERO_DEFECT` ($\Phi_1 = 0$) and `60/60` zero-send
  `replay_session` verified across all 6 cycle ranks and 7 graph families.
- **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local 6-board stratified anchor panel
  across $b_1 \in \{3..8\}$):** Un-staged 3-turn session solved `0/6` (`0.0%`);
  Two-Stage Tree-Then-Chord `P*` abstained at Stage 1a via `NullTree` on `6/6`,
  preventing **`24` wasted downstream turns** (`0` corrupted Stage-2 admissions).
- **Panel 2 (`qwen/qwen-2.5-7b-instruct`, OpenRouter, all 60 hidden boards, `301`
  calls at `$0.097765`):** Un-staged 3-turn action generation solved **`0/60`
  (`0.0%`)** across all cycle ranks $b_1 \in \{3..8\}$. Under Two-Stage
  Tree-Then-Chord `P*`, Stage 1a ($G_T$) passed on `8/60` boards (`4/10` on
  $K_4$ at $b_1 = 3$, `1/10` on `wheel-7-rim` at $b_1 = 7$, and `3/10` on
  `wheel-8-rim` at $b_1 = 8$) and abstained via `NullTree` on `52/60`,
  preventing **`208` wasted downstream turns (`52 \times 4`)**. Stage 1b ($G_C$)
  passed on `7/8` on Attempt 1 and `8/8` (`100.0%`) after 1 retry. All `8/8`
  admitted boards (**`100.0%` conditional Stage-2 precision; `8/60 = 13.3%`
  unconditional**) terminated in certified `ACCEPTED_ZERO_DEFECT` ($\Phi_1 = 0$)
  and passed zero-send `replay_session`.

### 6.10 Trial 12 (`B-COH-S1`): Multi-stage `P*` cohomology certificate verification across `C011`–`C020`

To test Theorem 12 across all ten cohomology challenges (`C011`–`C020`), we
extended `check_certificate` in `omega_engine_pfp/domain/cohomology/` to
independently verify all `328` JSON benchmark cases (`278/278` `SOLVED`, `36/36`
`OUT_OF_SCOPE`, `14/14` `UNKNOWN` rejected) and executed the paired multi-stage
`P*` campaign (`b_cohomology_p_star_receipt.json`):

- **`NO_LLM` exact baseline (`no_model_exact_b_cohomology_baseline`):** `10/10`
  (`100.0%`) `SOLVED` certificates verified + `10/10` (`100.0%`) `OUT_OF_SCOPE`
  certificates verified across `C011`–`C020`.
- **Panel 1 (`Qwen/Qwen2.5-0.5B-Instruct`, local):** Un-staged `0/10` verified;
  `P*` certificate-guarded caught `1` false `SOLVED` claim on Attempt 1 and
  abstained via `NullTree` on `10/10` (`0` admitted false `SOLVED` verdicts).
- **Panel 2 (`qwen/qwen-2.5-7b-instruct`, OpenRouter, `30` calls at `$0.020035`):**
  On Attempt 1, `qwen/qwen-2.5-7b-instruct` emitted well-formed JSON with
  `"status": "SOLVED"` on **`10/10` (`100.0%`)** of challenges `C011`–`C020`,
  every one of which violated the exact algebraic identities of its challenge
  (confirming Theorem 12.1). Independent `check_certificate` caught all `10/10`
  false `SOLVED` claims on Attempt 1, triggered 1 diagnostic retry, and
  projected all 10 persistent failures to `NullTree`
  (`admitted_false_solved_count = 0`, `conditional_stage2_precision = 1.0`).

## 7. Executable replay and limitations

The [replay script](code/replay.py) uses only the Python standard library and
executes twelve deterministic verification suites with zero model calls:

1. **Glyph code round trips and rejection controls:** Verifies all four Boolean
   code/assignment round trips (`<00>`, `<01>`, `<10>`, `<11>`), refuses
   malformed strings, and confirms that only `<01>` and `<10>` satisfy $x+y=1$.
2. **Cochain primal-dual identity (Theorem 2):** Verifies $d_1 d_0 = 0$,
   $\Phi_1(c) = \Gamma_2(c) = |s|$, node-potential integration $d_0 a = c'$, and
   lightest-edge weighted $\ell_1$ optimality across all 8 C004 cycle cases.
3. **Coloured operad `NullTree` absorption (Theorem 3):** Verifies that valid
   colour-matched grafts succeed while colour mismatches, out-of-bounds slot
   indices, and `NullTree` children or parents are absorbed to `NullTree`
   ($f \circ_i \mathbf{0} = \mathbf{0}$ and $\mathbf{0} \circ_i g = \mathbf{0}$).
4. **BPE prefix-automaton viability (Proposition 4):** Verifies that the
   integer-slot prefix DFA admits multi-character BPE boundary tokens (`' -'`),
   blocks premature `<eos>` before slot $k$, and accepts completed $k$-slot
   tuples.
5. **Single-cycle guarded Stage-1 retry and partial-guard false-green kernel (Theorems 5 & 6):**
   Verifies the exact bijection $\Delta s \mapsto z_1(\Delta s) \in \mathcal{K}_{\text{false}}(x)$
   with Stage-2 residual $\Phi_{1,w}(c'(\Delta s)) = w_{i^*}|\Delta s| > 0$,
   confirms the `c004_k6_01` retry witness `(0, 2, 4, 4)` at $\Delta s = -3$,
   and checks that $G_{\text{complete}}$ closes the false-green kernel to $\emptyset$.
6. **Multi-cycle $K_4$ triangular chord decoupling and rank-6 visibility gap (Theorem 7):**
   Verifies across all 4 $K_4$ multi-cycle overlap boards ($b_1 = 3$, shared tree
   edge incidence 3) that $G_{\text{complete}}^{\text{C006}}$ implies exact zero
   cochain defect ($c' = d_0 p_T^*$, $\Phi_1(c') = 0, \Gamma_2(c') = 0$), and
   verifies the 3 empirical multi-cycle Local Green / Global Red witnesses in
   $\mathcal{K}_{\text{false}}^{\text{C006}}(x) \cong \mathbb{Z}^6 \setminus \{0\}$.
7. **Higher-Betti ($b_1 \in \{4, \dots, 8\}$) two-stage tree-then-chord slot-arity reduction and kernel closure (Theorem 8):**
   Verifies across $K_{3,3}, Q_3, K_5, \text{Petersen},$ and $W_7$ that two-stage
   factorization strictly reduces maximum integer-slot arity from
   $(|V|-1)+2 b_1 \in \{13, 17, 16, 21, 21\}$ to $\max(|V|-1, b_1) \in \{5, 7, 6, 9, 7\}$
   and that $G_T \wedge G_C = 1 \iff (\hat{p}_T, \hat{c}'_{E \setminus T}) = (p_T^*, d_0|_{E \setminus T} p_T^*)$.
8. **Dichotomic Fredholm-alternative guard closure and false-verdict elimination (Theorem 9):**
   Verifies across all 8 public `C005` difference boards (`pub_cons_01`..`pub_cons_08`)
   that $G_{\text{Fredholm}} = 1$ uniquely determines $(\hat{p}_T, \hat{r}_{E \setminus T}) = (p_T^*, r_{E \setminus T}^*)$
   and rejects lazy false-`INCONSISTENT` and false-`CONSISTENT` perturbations.
9. **Cohomological syndrome decoding $\mathbf{r}^* = S\mathbf{c}$ across Verdict, Single-Edge Chord/Tree Repair, and Audit (Theorem 10):**
   Verifies on `C001` rank-difference graphs that $\mathbf{r}^* = S\mathbf{c}$
   vanishes if and only if $\mathbf{c} \in \operatorname{im}(d_0)$ and decodes
   both chord perturbations ($\mathbf{r}^* = -\hat{\delta}\mathbf{e}_m$) and
   spanning-tree perturbations ($\mathbf{r}^* = \hat{\delta} S_{\cdot, e^*}$,
   including `c001_repair_1101` `['D','C'] -> 2408` across 4 chord cycles).
10. **Tree-coboundary defect migration vs. path-integrated $B_T^{-1}$ guard diagnostics (Theorem 11):**
    Verifies on rooted spanning trees of depth $\ge 2$ that an internal tree-edge
    integration error $\Delta_{v^*} \ne 0$ shifts $\operatorname{Subtree}_T(v^*)$
    while leaving descendant edge-local residuals zero, so updating only $v^*$
    migrates the coboundary defect to child edges $(v^* \to w)$, whereas
    $\boldsymbol{\delta}_T = B_T^{-1}\mathbf{e}_T$ flags the entire subtree
    $\operatorname{Subtree}_T(v^*)$ simultaneously.
11. **Independent exact cohomology certificate verification (`C011`–`C020`, Theorem 12):**
    Verifies on finite `C015` ($\mathbb{F}_2$ persistence $R = D \cdot V$) and
    `C018` (signed-graph switching frustration) instances that status-label-only
    acceptance admits invalid `"status": "SOLVED"` payloads whereas independent
    algebraic recomputation rejects them.
12. **Offline recount of all 13 committed C001, C004, `claude-fable-5-1`, C005, C006, and `b_cohomology` receipts:**
    Replays all six committed C004 benchmark receipts (including the 40-case
    hidden ladder `C004-S6`), the accounted `claude-fable-5-1` theorem-derivation
    receipt, all three C006 receipts (`C006-S6` $K_4$, `C006-S7` higher-Betti,
    and `C006-S8` 60-board hidden campaign), the `C005-S1` dichotomic Fredholm
    receipt, the `C001-S1` distractor-filtered syndrome receipt, and the
    `B-COH-S1` (`C011`–`C020`) cohomology certificate receipt from disk (when
    run inside the repository checkout) with zero network or provider calls.

### Claim hygiene summary

1. **What this paper supports:**
   - Theorem 1 (channel-independent host checking soundness), Theorem 2
     (single-cycle prompt-to-cochain $\ell_1$ primal-dual coboundary identity),
     Theorem 3 (two-sided `NullTree` ideal absorption in $\mathcal{O} / \mathcal{I}$),
     Proposition 4 (BPE prefix-automaton logit-mask viability and `F-null`
     token identity), Theorem 5 (guarded Stage-1 slot retry admission rate,
     conditional precision, and Stage-2 call savings), Theorem 6
     (single-cycle partial-guard visibility gap $\mathcal{K}_{\text{false}}(x) \cong \mathbb{Z} \setminus \{0\}$),
     Theorem 7 (multi-cycle triangular chord decoupling and rank-$(|V|-1+b_1)$
     partial-guard visibility gap $\mathcal{K}_{\text{false}}^{\text{C006}}(x) \cong \mathbb{Z}^{|V|-1+b_1} \setminus \{0\}$),
     Theorem 8 (two-stage tree-then-chord `P*` slot-arity reduction from
     $|V|-1+2 b_1$ to $\max(|V|-1, b_1)$ and two-stage false-green kernel closure),
     Theorem 9 (dichotomic Fredholm-alternative `P*` guard closure and
     elimination of the lazy false-refusal attractor), Theorem 10 (cohomological
     syndrome decoding $\mathbf{r}^* = S\mathbf{c}$ across `verdict`, chord/tree
     single-edge `repair`, and `audit`), Theorem 11 (tree-coboundary defect
     migration under coordinate-local retry vs. one-step subtree identification
     under path-integrated $B_T^{-1}$ diagnostics), and Theorem 12 (independent
     exact certificate verification across `C011`–`C020` closing the status-label
     false-`SOLVED` kernel) under their declared finite assumptions.
   - Across all 12 empirical mechanism and cohomology trials (`C004-S1`..`S6`,
     `C006-S6`..`S8`, `C005-S1`, `C001-S1`, and `B-COH-S1` across `C011`–`C020`),
     `P*` staged slot materialization with complete deterministic Stage-1 guards
     and `NullTree` abstention achieved **`40/40` (`100.0%`) conditional Stage-2
     precision** (`0` admitted false `SOLVED` verdicts across `242` guarded
     board/challenge evaluations), caught `3` additional Local Green / Global Red
     witnesses on the 40-case hidden `C004` ladder and `10/10` false `SOLVED`
     status claims on `B-COH-S1`, and prevented `208` wasted downstream turns on
     the 60-board hidden `C006` campaign.
2. **What this paper does not support:**
   - Does not claim that Coloured Operad slot-grafting, Layer-2 grammar
     projection, or a single Stage-1 retry gives small or 7B models general
     symbolic competence: on the 40-case hidden `C004` ladder (`C004-S6`),
     `qwen/qwen-2.5-7b-instruct` passed `G_complete` on `2/40` (`5.0%`) cases; on
     the 60-board hidden `C006` campaign (`C006-S8`), it passed $G_T \wedge G_C$
     on `8/60` (`13.3%`) boards; and on `B-COH-S1` (`C011`–`C020`), it passed
     `check_certificate` on `0/10` (`0.0%`) challenges (`10/10` abstained via
     `NullTree`).
   - Does not claim that local `15.24 GB` bf16 7B execution fits within `4.0 GB`
     laptop GPU VRAM without quantized GGUF/AWQ backends or remote provider
     routing.
3. **The narrowest defensible claim:**
   - Decomposing multi-constraint algebraic and cohomological tasks into
     bounded-arity `P*` Stage-1 slot-materialization cuts guarded by complete
     deterministic linear/coboundary, path-integrated $B_T^{-1}$, and independent
     certificate predicates ($G_{\text{complete}}, G_{\text{complete}}^{\text{C006}}, G_T \wedge G_C, G_{\text{Fredholm}}, G_{\text{cert}}^{(m)}$)
     with `NullTree` abstention enforces **`100%` conditional Stage-2 precision**
     (`40/40` across all admitted grafts in `C004-S5`, `C004-S6`, `C006-S6`,
     `C006-S7`, `C006-S8`, `C005-S1`, `C001-S1`, and `B-COH-S1`, with `0`
     admitted false verdicts) while converting unrecoverable model arithmetic or
     witness failures into zero-downstream-cost `NullTree` abstentions.
4. **The next test needed:**
   - Evaluate whether per-challenge multi-stage `P*` operator decomposition for
     `C012` (sheaf coboundary matrix $d_0$ materialization before $H^0/H^1$
     kernel/cokernel extraction) and `C015` (column-by-column $\mathbb{F}_2$
     pivot reduction $R = D \cdot V$) lifts 7B/frontier verified solve rates above
     `0/10` under the same fail-closed `check_certificate` gate.

## 8. Sources and relation to the programme

This draft builds on the [WDP manuscript](../../../../../omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/witnessed_difference_programme.md),
[Paper 021 (source and execution audit)](../021_recreated_demos_and_proposal_fidelity_evidence/paper.md),
[Corrected challenge findings](../symbol_game_challenge_and_demos_findings/README.md),
[Paper 022 (frontier research)](../022_pfp_frontier_research/paper.md),
the [Categorical Operad Prompt Architecture](../../../prompts/categorical_operad_prompt_architecture.md),
and the [bounded C001/C004/C005/C006/`b_cohomology` mechanism sessions](../../../../../omega_engine_education/documentation/004_oepfp/docs/19_bounded_mechanism_sessions.md).
The [two-level teaching packet](prompts/example.yaml) is retained as an
unexecuted structural example. Genesis and MSS-N presentation stages do not
license a new mathematical or physical carrier.


## Research extension: evolving the proposal harness

Prompt, workflow, search-policy and context-policy rewrites are additional
proposal-channel interventions. The host's task and checking obligations remain
fixed. A strategy label, root-cause explanation or compressed context can change
the distribution of submitted candidates without changing what a valid
certificate must satisfy. This is the operational use of channel-independent
checking; it does not establish a theorem about empirical improvement.

The new campaign uses named Anthropic deployments with frozen role configurations.
Its interface supplies adaptive-thinking and output limits; it does not expose
provider seeds, arbitrary logit interventions or attention weights. Local seeds
reproduce scheduling choices only. Every paid attempt, including an unusable
response, is bound to the original budget and retained raw evidence. Changed
candidate code is executed only within the declared isolated surface.

The historical mechanism trials and finite proofs above retain their own source
and evidence identities. They are not training data or measured outcomes for the
new held-out panel. Paper 029 supplies the separate protocol, ablations and
exploratory ignition design. Those new model effects remain NOT_MEASURED pending
the verified remote host.

The source and page references for this extension are collected in
[Paper 029](../029_pfp_evidence_bound_harness_evolution/paper.md) and its
[source-to-claim map](../029_pfp_evidence_bound_harness_evolution/docs/source_to_claim_map.md).
The author-review rendering does not replace a historical deposit or archive.


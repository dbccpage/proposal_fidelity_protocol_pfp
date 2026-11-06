---
title: "The PFP Workflow DAG: Process and Mathematics of WF1–WF49"
author: "Jeremy H. Carroll"
date: "2026-11-05"
status: "author-review draft; not a deposit"
---

# The PFP Workflow DAG: Process and Mathematics of WF1–WF49

**AuthorityEffect:** None. **Status:** author-review draft, 2026-11-05.
This paper summarises procedures and the mathematics their checks rely on.
It reports no new model run and no performance result.

## Abstract

The Proposal Fidelity Protocol (PFP) separates a model's proposal from the
host check that decides whether to accept it. Five workflows (WF1–WF5) are
implemented as offline-verified runners over a finite integer-sum task.
The retained pilot estate of the Omega Engine research repository
(`omega_engine_woland/tests/pilots`, pilots `0000000`–`0000203` and their
auxiliary folders) contains many more procedures that were designed, and in
some cases run, but never named as workflows. This paper reads that estate
and names eighteen further families, WF6–WF23, as nodes of one acyclic
dependency graph. For each family we give the process, the mathematics of
its acceptance rule, and its source evidence. We also give a team design for
running each family with model agents: a measurable goal, roles assigned to
model tiers (Sonnet for coding, Opus for deep research, Fable for
adversarial research), a teamwork pattern, and a bounded *boost* step.

The machine-readable graph is `workflows/dag/workflow_dag.json` in this
repository. The paper is a summary: it does not reproduce the pilots.

## 1. Common structure

Every workflow is a tuple
$$\mathcal{W} = (T, \Pi, C, B, R),$$
where $T$ is a frozen task, $\Pi$ a procedure that produces proposals,
$C$ a deterministic host check, $B$ a budget, and $R$ the retained record.
A run produces proposals $p_1, p_2, \dots$ and stops at the first $t$ with
$C(T, p_t) = \mathsf{accept}$, at a typed refusal, or when $B$ is exhausted.

Three invariants hold for every node:

1. **Authority separation.** Only $C$ accepts. A proposal, an agent's
   agreement or a reviewer's prose is never evidence by itself.
2. **Freeze before use.** Any artifact $a$ read by a later step is recorded
   as $h(a) = \mathrm{SHA\text{-}256}(a)$ before that step starts.
3. **Charged attempts.** Every call, including failures and boosts, is
   counted against $B$.

An edge $\mathcal{W}_i \to \mathcal{W}_j$ in the DAG means that $\Pi_j$ or
$C_j$ uses $\Pi_i$ or $C_i$ as a step. Topological order is the reading
order.

## 2. The implemented base (WF1–WF5)

**WF1 (typed answer).** One reply $r$; accept iff it parses to a value
$v$ in the declared schema and $v = f(x)$ for the host-computed $f$.

**WF2 (full slots).** The reply fills a declared slot catalogue
$S = \{s_1,\dots,s_m\}$ (operations, missing information, repair moves).
Coverage requires each $s_i$ to have a typed value or an explicit absence.

**WF3 (mine, then solve).** A mining call proposes guidance $g$; the host
screens it and records $h(g)$; the solver then runs with $g$ frozen.

**WF4 (five agents + LGGR).** One shared mining call, five isolated
solvers, local checks $C_\ell(a_k)$ and one global check. "Local green,
global red" (LGGR) is the case where every $C_\ell$ passes but the answers
fail to glue: global acceptance requires
$\bigwedge_k C_\ell(a_k) \wedge (a_1 = \dots = a_5 = f(x))$.

**WF5 (checked rewrite).** A rewrite $\rho$ of the seed $s$ is admitted
only if $\mathrm{decode}(\rho(s)) = q(s)$ on the declared finite language,
where $q$ is the protected query; then WF4 runs against the original input.

## 3. Derived families (WF6–WF23)

Pilot numbers refer to directories in the source estate. "Planned" means the
pilot stores prompt capsules and a declared checker id but no model reply.

### WF6 — Dialect sweep (pilots 0–19)

*Process.* Freeze one seed and its host answer; compile $P^*$ and $k$
rewrites (dialects) of both the seed and $P^*$; dispatch each capsule under
the same model and parameters; grade with one checker; compare per item.

*Mathematics.* Each dialect $\rho_k$ must satisfy the WF5 preservation
condition. With replies $r_{ik}$ on items $i = 1..N$, acceptance is
$A_k = \tfrac1N \sum_i \mathbf 1[C(r_{ik})]$, and dialects are compared on
the same items (paired), not by pooled averages. The pilots also log an
exact structure delta $\mathrm{Net} = \Delta_{\text{created}} - \Delta_{\text{removed}}$.

*Evidence.* Pilots 0–10 hold 53–83 test capsules each (seed, $P^*$, ten seed
rewrites, ten $P^*$ rewrites); a few capsules hold manual live replies.

### WF7 — Typed refusal (pilots 3, 7, 11, 15, 19, 34, 175)

*Process.* Declare an answerability predicate and refusal codes; pose
underdetermined or undefined tasks; accept only the correct code or a
checked answer.

*Mathematics.* For $Ax = b$ with $n$ unknowns, the task is answerable iff
$\operatorname{rank} A = \operatorname{rank}[A \mid b] = n$. Otherwise the
correct outcome is `ANSWER: UNRESOLVED <code>`. The bluff rate is
$\beta = \#\{\text{answered} \wedge \text{unanswerable}\} / \#\{\text{unanswerable}\}$.

### WF8 — Staged sealed packets (pilots 1–25, 33)

*Process.* Choose a mode contract and wire encoding (EBNF wire, S(n) wire,
boundary packets, glyph alphabets); split the task into $k$ typed stages;
seal each output before the next stage reads it.

*Mathematics.* The procedure is a composition
$F = f_k \circ \dots \circ f_1$ with typed interfaces. The seal chain is
$h_0 = H(\text{seed})$, $h_i = H(h_{i-1} \,\|\, \text{payload}_i)$, so an
edit to stage $i$ changes every $h_j$, $j \ge i$.

*Evidence.* Mode trials `mode_01`–`mode_20`; pilot 20 runs two local stages
with zero provider calls; pilot 33 records that an advertised two-pass loop
was not implemented by its single-call runner, and keeps both files.

### WF9 — Bounded check-and-repair (pilots 2, 6, 10, 26, 49, 55, 62, 96)

*Process.* On rejection, return only the typed residual; allow at most $L$
attempts; stop on the first accepted reply or at the limit.

*Mathematics.* For a binary constraint system on a cycle with edge labels
$w_e \in \mathbb F_2$, a consistent vertex assignment exists iff
$\sum_{e \in \text{cycle}} w_e = 0$. In general, repair seeks
$\min \|\Delta\|_1$ subject to $\omega + \Delta \in \operatorname{im}\delta_0$.
Pilot 26 retains all three least-cost one-edge repairs of an odd triangle.
Termination is by construction: attempts $\le L$.

*Evidence.* Pilot 49 is a deterministic mock (41 then 42 for $19 + 23$; two
mock calls, zero provider cost); it is not evidence that a model improves.

### WF10 — Local-to-global obstruction certificate (pilots 29, 39–45, 51, 56–64, 83)

*Process.* Declare the cover, cochains and restrictions; agents certify
local sections; the host computes the global class; accept a gluing witness
or an obstruction certificate.

*Mathematics.* The first cohomology
$H^1 = \ker \delta_1 / \operatorname{im} \delta_0$ measures the failure to
glue. Pilot 51 (paper PO-000, §7.4) uses three patches, six covering edges
with fibres $\mathbb R^3$ under $\ell^1$, identity restrictions, and three
observers that each delete one coordinate. Each observer's tally
$J^\alpha(s) = \sum_{e \in E_\alpha} \|\pi_\alpha((\delta_0 s)_e)\|_1$
vanishes on its own edges while the glued section has non-zero coboundary:
local green, global red, with no recovery modulus. The exact Hodge
decomposition $\omega = \delta\alpha + \delta^{*}\beta + h$ (pilots 40, 42)
and integer lifts (pilot 29: an integer obstruction can survive a rational
lift) complete the toolkit.

### WF11 — Dual-certificate synthesis (pilots 27, 53, 54, 95, 115–124, 171, 180; c051–c055, c059)

*Process.* Publish a participant packet and seal the judge packet; the team
writes a solver that emits certificates; it commits $H(\text{salt}\,\|\,\text{solver})$
before hidden cases are revealed; the judge checks each certificate.

*Mathematics.* For $\max c^\top x$ s.t. $Ax \le b$, $x \ge 0$:
**optimal** iff $x \ge 0$, $Ax \le b$, $y \ge 0$, $A^\top y \ge c$ and
$c^\top x = b^\top y$ (weak duality closes the gap); **infeasible** iff some
$y \ge 0$ has $A^\top y \ge 0$ and $b^\top y < 0$ (Farkas); **unbounded**
iff a feasible point and an improving ray exist. Sister challenges use
max-flow = min-cut, assignment potentials ($u_i + v_j \le c_{ij}$ with
equality on the matching), Bareiss fraction-free elimination, and SQL
three-valued logic with NULL-total semantics.

### WF12 — Mechanism-control arms (pilot 52)

*Process.* Hold one carrier fixed and vary only a mechanism note; run
baseline, typed-witness and mechanism arms on the same items.

*Mathematics.* The carrier is an integer rank-difference system with three
distractor spans. Ranks are defined up to gauge $r \mapsto r + c\mathbf 1$,
so only differences $r_i - r_j$ are checkable. The paired effect is
$d_i = \mathbf 1[C(\text{arm}_B, i)] - \mathbf 1[C(\text{arm}_A, i)]$.

*Evidence.* Ten planned capsules (c001–c010); no model call; checker id not
yet registered.

### WF13 — Exact-domain capsule battery (pilots 65–114, 176–178, 187)

*Process.* One catalog challenge becomes one capsule with a registered
domain checker; one reply or refusal each; results stay per domain.

*Mathematics (examples).* Pauli stabilizer generators commute iff their
symplectic product $\langle u, v \rangle = u_x \cdot v_z + u_z \cdot v_x$
is $0 \bmod 2$. U(1) anomaly freedom requires $\sum_i q_i = 0$ and
$\sum_i q_i^3 = 0$. A Regge hinge has deficit
$\varepsilon = 2\pi - \sum \theta_{\text{dihedral}}$. A group commutator is
$[g,h] = g^{-1}h^{-1}gh$, checked in the declared finite group.

*Evidence.* Fifty planned capsules; none dispatched.

### WF14 — Immune failure classification (pilots 125–134)

*Process.* Seal a self panel of known-good outputs; propose detectors from
observed failures; reject any detector that fires on the panel; admit only
with two signals.

*Mathematics.* Negative selection keeps detector $d$ iff
$\forall s \in \mathrm{Self}: \mathrm{match}(d, s) < \theta$. The two-signal
gate admits iff a pattern signal and a host-evidence signal both hold.
Self-tolerance is $1 - \mathrm{FP}_{\mathrm{Self}} / |\mathrm{Self}|$.

### WF15 — Adversary tribunal (pilots 35, 135–144)

*Process.* Prosecutor and defender submit independently and are frozen
before seeing each other; the host checks each claim on a finite model.
(The source estate calls this the Woland tribunal; this repository names the
role "adversary".)

*Mathematics.* For a Kripke model $M = (W, R, V)$,
$M, w \models \Box\varphi$ iff $\varphi$ holds at every $R$-successor of $w$.
Argument acceptance is the grounded extension of the attack graph, computed
by the host. Pilot 35's finite predicate is $\sum \text{left} \le \sum
\text{right}$ on 1–16 integers bounded by $10^6$.

### WF16 — Substrate crosswalk (pilots 145–169)

*Process.* Translate generators and relations between substrates (prose,
Lean, finite tables); check every relation on the target; record every
non-unique choice.

*Mathematics.* A crosswalk $F: \mathcal C \to \mathcal D$ is accepted iff
$F(r)$ holds in $\mathcal D$ for each relation $r$ of $\mathcal C$. If $F$
and $F'$ both pass yet differ on a generator, both are recorded (G01 studies
this non-uniqueness in Lean).

### WF17 — Witnessed-difference programme (pilots 170–187, W01–W18)

*Process.* State two artifacts and a claimed difference or equivalence;
require a witness for a difference and a certificate for an equivalence;
pair every theorem with countermodels.

*Mathematics (examples).* Behavioural equivalence by a bisimulation $B$
with $(p, q) \in B$ and matching transitions; Fenchel–Rockafellar duality
$\inf_x f(x) + g(Ax) = \sup_y -f^{*}(A^\top y) - g^{*}(-y)$ under the
stated qualification; Čech gluing obstructions in $\check H^1$; LGGR I–VI
on evaluated path kernels; countermodels CE1–CE5.

### WF18 — Dossier replay campaign (pilots 188–191)

*Process.* Cross five finite carriers with five wrapped representations
(including emoji and Egyptian glyph carrier encodings with an explicit
legend), then five matched guidance trials; replay every grade from stored
bytes.

*Mathematics.* The frustrated spin triangle has no $s \in \{\pm1\}^3$ with
$s_i s_j = -1$ on all three edges (odd cycle). Weighted cycle duality: a
feasible potential exists iff there is no negative cycle. The design has
$5 \times 5 + 5 = 30$ cells per pilot, compared per carrier.

### WF19 — Failure-derived rule transfer (pilots 192–198)

*Process.* Compare baseline, typed-witness and failure-derived rule prompts
on disjoint held-out cases; at most two stages; checker disagreement halts.

*Mathematics.* Transfer gain
$\gamma = \mathrm{acc}(\text{rule}, H) - \mathrm{acc}(\text{baseline}, H)$
on held-out $H$ disjoint from the cases that produced the rule. A rule is
admitted only if $\gamma > 0$ and WF14 self-tolerance holds.

### WF20 — Derivation loop with lift grants (pilots 199–203)

*Process.* Five loops, each: proposal against named obligations; lift grant
(the host licenses which higher structure may be used); witness check on an
exact finite control; negative control; learning refinement.

*Mathematics.* State $(P_t, G_t, W_t)$ with
$P_{t+1} = \mathrm{refine}(P_t, \text{residual}_t)$, $t \le 5$. Halting is
the first of: certificate, budget, loop limit. Pilot 202 separates additive
curvature from metric Regge holonomy; pilot 203 states exact obstruction
certificates and operational halting conditions (source paper PO035).

*Evidence.* Five provider trials and twenty host stages per pilot, capped at
USD 0.05, 120,000 tokens and 180 s; analytical status remains unverified
until independent proof review.

### WF21 — Structural prompt rewriting (pilots 28, 30, 50; ACSet pilots)

*Process.* Represent the prompt as an attributed graph with protected task,
constraint and output nodes; rewrite only through explicit injective
matches; refuse a rewrite whose normal form drops the question.

*Mathematics.* A double-pushout rule $L \leftarrow K \rightarrow R$ applies
at an injective match $m: L \to G$ only when the pushout complement exists
(the gluing condition). The invariant is
$\mathrm{bytes}(\mathrm{protected}(G')) = \mathrm{bytes}(\mathrm{protected}(G))$.

### WF22 — Certified cost ladder (certified ladder design, H0–H13)

*Process.* Pre-register items, arms and fourteen hypotheses; every arm ends
with one canonical `ANSWER:` line; run every item under every arm.

*Mathematics.* Cost to certified correct
$C_{\text{arm}} = \text{spend} / \#\text{accepted}$; paired comparison on
discordant items $b = \#(A\,\text{ok}, B\,\text{fail})$,
$c = \#(A\,\text{fail}, B\,\text{ok})$ with an exact McNemar test; WF7 bluff
rate per arm.

### WF23 — Judge-packet custody audit

*Process.* Canonicalise participant and judge packets, hash every file,
test for leakage, and verify that the judge executes the sealed checker.

*Mathematics.* Leakage: the expected answer is not present in, and not a
declared function of, participant bytes. Custody: recorded SHA-256 equals
the hash of executed bytes.

## 3b. Families added from the findings and the papers (WF24–WF49)

These were extracted on 2026-11-06 from the certified-challenge findings notes
(`workflows/certified_challenges/findings/`) and from Papers 000–033. Each is a
proposal with cited sources; the findings carry errata, so their live figures
are historical. Kinds follow the committee classification.

**WF24 — Pinned-token operational scratchpad** (procedure extension; extends WF2). *Process:* pin canonical coordinate tokens in the reply grammar; require an operational scratchpad of the exact computation (e.g. path products); check the final answer with dual independent checkers. *Mathematics:* holonomy along a loop: g_acc <- g_acc * U(e) for each edge e, compared with the identity. *Evidence:* Live, 5 cases: 0/5 became 3/5 on a 70B model and on a reasoning model. Historical; the findings carry errata.

**WF25 — Hierarchical decimation** (procedure extension; extends WF24). *Process:* certify trivially flat sub-blocks at zero tokens; evaluate only the non-contractible loops; check that the remaining holonomies commute; optional second pass aggregates macro-blocks. *Mathematics:* flat blocks contribute the identity; global flatness reduces to the cycle holonomies of the quotient. *Evidence:* Live on one torus case: tokens fell from over 8,000 to 2,810 and overall 4/5 passed. Two-pass quad-tree aggregation is proposed, not run.

**WF26 — Multi-round antibody dialogue** (procedure extension; extends WF9, WF14). *Process:* run up to R dialogue rounds on one task; turn each recorded hallucination into a typed negative-constraint antibody; carry accumulated antibodies into the next round; accept only on the exact oracle. *Mathematics:* antibody set A_{t+1} = A_t ∪ {typed constraint from failure_t}; stop when check passes or t = R. *Evidence:* Live: 5 models, 22 calls, $0.015; two models reached 4/4 by round 2-3. The prompts leaked the answer (erratum), so this is plumbing evidence only.

**WF27 — Hinted retraction with a stationary-loop detector** (procedure extension; extends WF9). *Process:* inject the residual vector and the non-zero cell ids each turn; detect a stationary loop after 3 repeats; force a structural lift or reframe; stop at the turn cap. *Mathematics:* residual r_t = d c_t; stationary if r_t = r_{t-3}; path-integrated retry uses B_T^{-1}, not edge-local B_T. *Evidence:* Live, 28 trials on 7-8B models: baseline 0%, hinted 100% (the hint was the full repair, so only copying is shown).

**WF28 — Eight-role audit dialogue** (procedure extension; extends WF15). *Process:* proposer, adversary, solver, overconfidence probe, stabilizer, schema auditor, truth repair, terminal arbiter in sequence; each role sees only frozen earlier outputs; host check decides; the arbiter cannot accept. *Mathematics:* strict descent of the l1 defect across the role sequence. *Evidence:* 6 run folders; verdict counts are reference self-scores.

**WF29 — Checker synthesis scored by mutation kill rate** (task preset; extends WF11). *Process:* the model writes a checker for a declared certificate; run it against valid cases and a hostile mutation suite; score by kills and by false rejections. *Mathematics:* kill rate = killed / mutants; soundness requires zero false rejections on valid cases. *Evidence:* Live: reasoning model 10/10, 70B 5/10, 8B 0/10.

**WF30 — Constraint-forcing anti-recitation** (procedure extension; extends WF1). *Process:* add task constraints that break memorised textbook answers (forced prefix, forbidden step); check with the exact property (e.g. the 0-1 principle). *Mathematics:* a comparator network sorts all inputs iff it sorts all 2^n binary inputs. *Evidence:* Live: 70B and 8B recited the textbook network and failed every constrained case.

**WF31 — Multi-agent tournament with held-out cross-validation** (experiment design; extends WF1). *Process:* several proposers answer the same packet each round; include a random-baseline negative control; proposers see a training share of the instance; the host scores the held-out share; rank per budget. *Mathematics:* exact referee: SO(4N), det = +1, defect <= tolerance; held-out score on the 30% the proposer never saw. *Evidence:* Offline deterministic strategies and live-capable; the earlier rates were withdrawn. Held-out split: random baseline 0/16, others 16/16 (offline).

**WF32 — Claim-scoped receipt** (procedure extension; extends WF1, WF2). *Process:* record the exact set of admitted claims J_checked; check each claim with its own checker; a correct witness admits nothing around it (prose, universals, quotes); quotes need source bytes and a span. *Mathematics:* admitted(J) = {j : C_j(witness_j) = accept}; everything else stays unadmitted. *Evidence:* Proof and finite replay; no model runs.

**WF33 — Recursive re-entry with shared fuel** (procedure extension; extends WF9, WF20). *Process:* an output becomes the next proposal; check a backward solution map and a forward coverage map per edge; bind the parent receipt; charge every prefix against one original budget. *Mathematics:* at most floor(B / delta) operations under budget B; stale parent, changed task or fuel reset is refused. *Evidence:* Replay only.

**WF34 — Future-faithful compression and bounded context** (procedure extension; extends WF8, WF22). *Process:* compress state only if enablement, cost, successors and terminal labels all survive; stage boundaries require equal states, not equal diagnostics; bounded context keeps root, champion, two recent attempts and evidence references; compare with a full-history arm at the same ceiling. *Mathematics:* coarsest stable refinement; states equal under every finite continuation. *Evidence:* Proof and replay; the bounded-context harness arm is implemented and NOT_RUN.

**WF35 — Proposal-channel comparison** (experiment design; extends WF6, WF12). *Process:* fix the host check; vary only the channel: prompt, glyph code, logit mask, grammar mask, typed tree, attention or activation bias; compare per item. *Mathematics:* channel invariance: the accept set depends on the reply, never on the channel that produced it. *Evidence:* Offline receipts; attention, activation and steering channels were not exercised on live models. Qwen-0.5B: 0/8 exact on every channel; the null channel matched free decoding token for token.

**WF36 — Guarded staged slot materialisation** (procedure extension; extends WF8). *Process:* stage 1 emits typed slots; a complete guard with one retry gates stage 2 or abstains; two-stage tree-then-chord for higher cycle rank; a dichotomic guard removes the lazy false-refusal attractor. *Mathematics:* syndrome r* = S c shared across verdict, repair and audit; a partial guard leaves a false-green kernel. *Evidence:* Live on a local 0.5B model, gpt-4o-mini and a 7B model; 40-case ladder: 7B unstaged 9/40 exact, guarded 2/40 admitted and both optimal.

**WF37 — Evidence-bound harness evolution** (meta workflow; extends WF19, WF22). *Process:* an outer model rewrites a small harness (prompt, workflow, search and context policy); uCB1 plus softmax search over strategies; scoped failure memory; public and private grading split; fresh confirmation before replacing the incumbent; untouched transfer and ablation panels. *Mathematics:* paired bootstrap, exact sign test, Holm correction over transfer and ablation contrasts. *Evidence:* Implemented offline; NOT_RUN live ($40 plan).

**WF38 — Diagnostic-trace proposal selection** (procedure extension; extends WF9). *Process:* the model proposes candidates; it never reports its own score; the host recomputes Phi, Gamma and other channels; filter by strict lexicographic decrease and a ratio ceiling; rank with fixed weights; ties by name; every observer must pass in the multi-observer form. *Mathematics:* primal-dual witness: B^T phi = 0, ||phi||_inf <= 1, phi . c = ||h||_1; Gamma <= ||D|| Phi. *Evidence:* Host checks have code and tests; no model runs.

**WF39 — Authority firewall gate** (harness gate; extends WF1, WF23). *Process:* a rejected or obstructed reply can only become residual evidence, never an accept; accept requires every guard: replay hash, replay match, terminaliser, exhaustion, zero defect, descent witness, freshness; packet gates C1-C8 keep tool halt separate from authority; witness must be bound to a registered verifier and the exact payload hash. *Mathematics:* accept iff AllGuardsPass; a non-zero obstruction class cannot satisfy a truthful zero-defect guard. *Evidence:* Code, tests and Lean; no model runs.

**WF40 — Restart boundary after exhausted repair** (procedure extension; extends WF9, WF20). *Process:* when bounded repair ends with a positive residual, choose exactly one of: typed refusal, lift request, restart seed carrying the residual; a lift needs a preservation witness; a changed claim set is a new problem, not a repair. *Mathematics:* cochain trichotomy: exact / unclosed / closed non-exact; lift authorised only with Delta > 0. *Evidence:* Code and tests; offline scripted demos only.

**WF41 — Detector adequacy and two-signal admission** (meta workflow; extends WF14). *Process:* admit a detector only with positive, negative, collision and metamorphic cases plus one representative per class; two signals: pattern match and structural defect; pattern alone is diagnostic only; bind a human decision to the receipt digest; report effective diversity of the self panel. *Mathematics:* finite calibration completeness: D = A iff D = A on a class-representative set R (sharp). *Evidence:* Lemmas checked exhaustively offline; no detector admitted; the six-arm effectiveness experiment is proposed (~299 opportunities needed for a <1% bound).

**WF42 — Reasoning-trace validation** (procedure extension; extends WF10, WF21). *Process:* a fixed extractor turns the model's text into a claim, citation or tool graph; the host computes the obstruction and a dual witness; emit a typed status; run an adversarial battery against the extractor. *Mathematics:* Exact only describes the extractor's image; a three-claim cycle with Phi = 1 and phi = (1,1,1) is the worked obstruction. *Evidence:* Code and tests; the extractor adequacy battery is specified, not certified.

**WF43 — Gate-honesty and answer-free leak audit** (harness gate; extends WF23). *Process:* ask which operation produced each verdict; probe with input replacement, keyword adjudication, phantom evidence and templated receipts; replay constant refusals, empty objects and constant verdicts against both checkers. *Mathematics:* a gate is honest only if no answer-free reply passes and every verdict traces to a check. *Evidence:* Executed offline: a bare refusal passed 10/10 on two challenges before identifiers were neutralised.

**WF44 — Exact certificate presets** (task preset; extends WF11, WF10). *Process:* the model emits a certificate: l1 potential, residual and dual circulation; a sparse representative; an equal-weight pairing involution; or a typed DSL program; the host checks it exactly; ill-typed programs are refused before evaluation. *Mathematics:* r = w + B f, B^T z = 0, |z_e| <= w_e, w . z = ||r||_1 (weak duality). *Evidence:* Host checks have code and tests; no model runs.

**WF45 — Finite terminal selector and plenitude test** (procedure extension; extends WF7). *Process:* check every candidate against evidence with tolerances; return Accepted, Underdetermined, Refuted or Refused for the family; add indistinguishable candidates and check the survivor count rises; deleting competitors is not evidence. *Mathematics:* unique acceptance is only relative to the declared family. *Evidence:* Code and tests; stress test with 100 candidates.

**WF46 — Boundary sufficiency and gluing diagnostic** (procedure extension; extends WF4). *Process:* check that the handoff object between isolated agents keeps everything the global evaluator needs; report NGD over runs; undefined when no run is locally accepted; report completed share and backlog. *Mathematics:* NGD = Pr(global fail | all locals pass). *Evidence:* Theory plus finite Lean split; NGD code not yet run on WF4 data.

**WF47 — Resumable bounded frontier search** (procedure extension; extends WF9). *Process:* deterministic lexicographic batches; statuses: verified, unknown with suffix, restricted obstruction; continuing requires replaying the contiguous chain from index 0. *Mathematics:* the presentation key includes basis and representation, so a resumed search cannot silently change problem. *Evidence:* Offline worked trace; no benchmark.

**WF48 — Commit-reveal with a hostile mutation gate** (harness gate; extends WF11, WF23). *Process:* commit the judge manifest; freeze the solver and commit its hash; reveal hidden cases (base, relabel/gauge controls, poison bait) and score; kill a hostile certificate-mutation suite with both checkers. *Mathematics:* commit H(salt || artifact) before reveal; both checkers must reject every mutant. *Evidence:* All C043-C060 reference solvers passed 64/64 and killed 48/48 mutants; these are reference self-scores, not model results.

**WF49 — Query-preservation stage and mode campaign** (experiment design; extends WF8, WF22). *Process:* run declared stages and mode contracts over task families; independent oracle per family; stop a lane on any safety regression. *Mathematics:* a stage passes only if the decoded query is unchanged. *Evidence:* Proposed: zero campaign cases executed; 17 live records from earlier rounds.

**Perturbations.** Forty-six variations of existing workflows (for example
scratchpad arms, completion ceilings, hint and masking levels, norm families for
certificates, cover and complex choices, calibration-set coverage and neutral
case identifiers) are listed under their target workflow in
`workflows/dag/workflow_dag.json` (`perturbations`). They are settings of a run,
not new procedures.

## 4. Teams, goals and boost

Each node carries a team design. Write a run as
$(\text{goal}, \mathcal R, \pi, \beta)$: the goal is the predicate
$C(T, p) = \mathsf{accept}$ with a stop rule; $\mathcal R$ is a set of roles
with model tiers; $\pi$ is a teamwork pattern; $\beta = (\tau, \alpha, \lambda)$
is a boost with trigger $\tau$, action $\alpha$ and limit $\lambda$.

**Tiers.** Sonnet holds coding, encoding, running and custody roles; Opus
holds deep-research roles (derivation, checker and certificate design,
analysis, the boost); Fable holds adversarial roles (countermodels, leak
tests, prosecution). Across WF6–WF23 the design has 23 Sonnet seats,
14 Opus seats and 13 Fable seats (counting a variable seat as one).

**Patterns.** `solo`, `relay`, `parallel_isolated_then_global`,
`sweep_with_shared_judge`, `red_team_pair`,
`proposer_with_residual_feedback`, `tribunal` and `research_cell`. The
isolation rule is formal: in parallel and tribunal patterns, the input of
agent $k$ is a function of frozen shared artifacts only, never of another
agent's reply before that reply is frozen.

**Boost.** After a failed check matching $\tau$, at most $\lambda$
escalations run action $\alpha$, usually an Opus call that receives the typed
residual $\rho_t = C(T, p_t)$ but never the expected answer. Boost calls are
charged against $B$. A boost changes the proposer, never $C$. Families whose
comparison would be broken by escalation (WF22) or whose correct response is
to stop (WF18, WF23) set $\lambda = 0$.

## 5. Limits

- WF6–WF23 are designs derived from the estate, not runners.
- Many source pilots (52–187) are planned capsules with no reply bytes and,
  in several cases, an unregistered checker id.
- The tier assignments are design choices, not measurements of model
  ability.
- Nothing here extends a finite check to a general mathematical or physical
  claim.

The next test is the smallest: run WF9 with and without its boost on the
same items, with costs recorded.

## Sources

- Pilot estate: `omega_engine_woland/tests/pilots/` (README, MODUS_OPERANDI,
  `pilot_*/spec.yaml` and `README.md`, `certified_ladder/design.md`,
  `c051_exact_lp_solver_with_duals/docs/`, `relational_spacetime/`).
- This repository: `workflows/dag/workflow_dag.json`,
  `workflows/dag/ORCHESTRATION.md`, `workflows/library/` (WF1–WF5 evidence),
  `pfp/workflows/` (runners).

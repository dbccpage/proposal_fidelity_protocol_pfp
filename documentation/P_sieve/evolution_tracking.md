# Prompt Sieve: Evolution Tracking, Lamarckian Cochains & Exact Pareto Frontiers

**AuthorityEffect:** None  
**Module References:** `code/rust/core_prompt_civilization/src/prompt_family.rs`, `code/rust/core_prompt_civilization/src/lamarckian.rs`, `code/rust/core_prompt_civilization/src/fitness.rs`  
**Status:** Implemented in Rust sovereign engine  

---

## 1. Executive Summary & Purpose

In Prompt Sieve, prompt evolution is not an unconstrained, heuristic search. Rather, prompt repairs are modeled as discrete transitions across a topological cochain complex. Each repair cycle must witness:
1. **A Lawful DDC Step**: Bound to one of eight closed letters in the Discrete Deformation Calculus ($\mathcal{D} = \{E, R, C, I, \Lambda, D, M, T\}$).
2. **Residual Transition**: Progression from unverified or obstructed states to exact resolution (`Open` $\to$ `Closed` $\to$ `Exact`).
3. **Lamarckian Cochain Descent**: Strict monotonic non-increase of defect cochain residual norms ($\Delta \Phi_1 \le 0$) accompanied by protected core invariance and distance attenuation $w(\alpha, d) = (1/2)^d$.
4. **Exact Rational Pareto Optimization**: Multicriteria fitness evaluation over $\mathbb{Q}$ without composite scalar collapse, preventing arbitrary scalar weight hacking.
5. **Terminal Repair Integrity**: A terminal status of `"Repaired"` is refused unless the final step is corroborated by an independent checker oracle emitting `checker_verdict: "ACCEPT"` with an `Exact` residual.

---

## 2. The `RepairStep` Data Structure

Defined in `code/rust/core_prompt_civilization/src/prompt_family.rs` (lines 178–186):

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairStep {
    pub input_node_id: String,
    pub output_node_id: String,
    pub ddc_letter: Option<String>,
    pub residual_before: Option<String>,
    pub residual_after: Option<String>,
    pub call_ids: Vec<String>,
    pub fitness: Fitness,
}
```

Where `Fitness` (lines 168–175) captures:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Fitness {
    pub cost_microusd: Value,
    pub input_tokens: Value,
    pub output_tokens: Value,
    pub checker_verdict: String,
    pub checker_id: Option<String>,
    pub obstruction_removed: Option<bool>,
}
```

### 2.1 The 8 Closed DDC Letters (`FAMILY_DDC_LETTER`)

When declared, `step.ddc_letter` must strictly belong to the 8-letter DDC alphabet (`prompt_family.rs`, lines 398–411):

| DDC Letter | Name | Operational Semantics | Effect on Residual |
|---|---|---|---|
| **`E`** | Exact Repair | Directly discharges defect; demonstrates obstruction is zero | $\text{Residual} \to \text{Exact}$ |
| **`R`** | Residual Projection | Projects irreducible obstruction mass into residual | $\text{Residual} \to \text{Closed}$ |
| **`C`** | Context Exposure | Declares carrier boundary and active 2-window | Preserves boundary |
| **`I`** | Integration | Appends verified delta into local history ledger | Monotonic cochain update |
| **`Λ`** | Structural Lift | Elevates representation complex upon obstruction certificate | Controlled complexity increase |
| **`D`** | Descent | Refines coordinate window or parameter indices | Focuses sub-domain |
| **`M`** | Refusal | Emits closed refusal code when obstruction is insurmountable | Safe termination |
| **`T`** | Terminalize | Seals final lifecycle state without sovereign authority mint | Freezes evolution |

Any letter outside this closed set triggers refusal `FAMILY_DDC_LETTER`.

### 2.2 Residual State Transitions (`FAMILY_RESIDUAL_COLOUR`)

The residual state of a prompt is typed as one of three discrete colours:
1. `"Open"`: The prompt contains unmeasured or unresolved obstructions.
2. `"Closed"`: Obstructions have been bounded and isolated, but not fully discharged.
3. `"Exact"`: All declared obstructions have been mathematically discharged and verified by an independent checker oracle.

Any residual value outside `"Open" | "Closed" | "Exact"` triggers `FAMILY_RESIDUAL_COLOUR`.

---

## 3. Lamarckian Cochain Tracking (`lamarckian.rs`)

Normative specification: `urn:core:nf:prompt_civilization:lamarckian_pfp_adversary_loop:v1.0.0`.  
Implemented in `code/rust/core_prompt_civilization/src/lamarckian.rs`.

Lamarckian evolution transfers phenotypic adaptations (successful prompt repairs) into the hereditary genome only when accompanied by verified mathematical descent.

### 3.1 Cochain Residual Triad: $\Phi_1, \Gamma_2, \Xi$

The cochain residual vector is represented by `CochainResidualV1`:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainResidualV1 {
    pub phi1: String,   // Primary obstruction norm in Q
    pub gamma2: String, // Secondary boundary curvature in Q
    pub xi: String,     // Transverse defect coupling in Q
}
```

All values must conform to exact rational string representation: `^-?[0-9]+/[1-9][0-9]*$`. Floating-point values are rejected (`Zero-Float Law`).

### 3.2 The Three Fundamental Lamarckian Laws

1. **Rule 1: Monotonic Defect Reduction ($\Delta \Phi_1 \le 0$)**
   The primary defect norm of the mutated prompt must not exceed that of the parent:
   $$\Delta \Phi_1 = \Phi_1(\text{child}) - \Phi_1(\text{parent}) \le 0$$
   If $\Delta \Phi_1 > 0$, `LamarckianCochainTrackerV1::verify_mutation` halts immediately with:
   `REGRESSION_RESIDUAL_INCREASE: delta_phi1 is {delta_phi} > 0`.

2. **Rule 2: Attenuated Influence Law**
   The inheritance weight of an evolutionary adaptation attenuates exponentially with topological graph hop distance $d$:
   $$w(\alpha, d) = \left(\frac{1}{2}\right)^d \quad \text{for } 1 \le d \le 10$$
   If $d < 1$ or $d > 10$, the mutation is out of bounds (`HOP_DISTANCE_OUT_OF_BOUNDS`). Adaptations beyond distance 10 are completely evaporated to prevent ancestral bloat.

3. **Rule 3: Protected Core Invariance**
   The immutable core byte spans defined during forge ingestion must be byte-for-byte identical between parent and child genomes:
   $$\text{Core}(G_{g+1}) == \text{Core}(G_g)$$
   If any byte within `protected_spans` differs, verification fails with:
   `PROTECTED_CORE_TAMPERED: Byte mismatch in protected span [{start}, {end}]`.

### 3.3 Lamarckian Mutation Receipt: `LamarckianMutationReceiptV1`

Each verified mutation produces an immutable cryptographic receipt:
$$\text{receipt\_id} = \text{sha256}(\text{sort\_json\_keys}(\{\dots\}))$$
Binding `parent_genome_id`, `child_genome_id`, `falsification_witness_sha256`, `cochain_residual`, `antibody_id`, `hop_distance`, and `attenuation_weight`.

---

## 4. Exact Rational Pareto Frontiers (`fitness.rs`)

Defined in `code/rust/core_prompt_civilization/src/fitness.rs`.

In complex prompt optimization, combining multiple objectives (such as correctness, cost, and robustness) into a single scalar fitness score ($F = w_1 C + w_2 K + \dots$) introduces arbitrary scalar preference bias. Prompt Sieve mandates **Non-Dominated Pareto Sorting over $\mathbb{Q}$** (`compute_pareto_fronts_rational`).

### 4.1 The Three-Dimensional Objective Vector: `CandidateRational`

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateRational {
    pub id: String,
    pub correctness: Rational64, // Higher is better
    pub cost: Rational64,        // Lower is better
    pub robustness: Rational64,  // Higher is better
}
```

### 4.2 The Law of Exact Rational Domination

A candidate $A$ strictly dominates candidate $B$ ($A \succ B$) if and only if $A$ is weakly dominating across all three objectives and strictly superior in at least one (`fitness.rs`, lines 243–247):

$$\begin{aligned}
A \succeq B &\iff (\text{corr}_A \ge \text{corr}_B) \land (\text{cost}_A \le \text{cost}_B) \land (\text{rob}_A \ge \text{rob}_B) \\
A \succ B &\iff (A \succeq B) \land \big((\text{corr}_A > \text{corr}_B) \lor (\text{cost}_A < \text{cost}_B) \lor (\text{rob}_A > \text{rob}_B)\big)
\end{aligned}$$

### 4.3 Front Partitioning & Deterministic Tiebreaking

`compute_pareto_fronts_rational` partitions candidates into ordered non-dominated fronts:
$$[F_0, F_1, F_2, \dots]$$
Where $F_0$ is the un-dominated Pareto frontier (`pareto_frontier_rational`).

**Deterministic Lexicographic Tiebreak:** Within any front $F_k$, candidates are sorted by:
1. `correctness` descending (highest correctness first).
2. `cost` ascending (lowest cost first).
3. `id` ascending (deterministic alphabetical tiebreak).

This enforces that front ordering is completely deterministic across all host architectures.

---

## 5. Terminal Conditions & The Refusal Gate

A prompt family's lifecycle concludes with an explicit `Terminal` state (`prompt_family.rs`, lines 189–192):

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Terminal {
    pub kind: String,
    pub detail: String,
}
```

Validation (`validate_terminal`, lines 433–473) enforces strict exit conditions:

### 5.1 Terminal `"Repaired"`: Strict Gate

A family cannot claim to be repaired solely on the basis of completed model generation. The terminal kind `"Repaired"` is refused (`FAMILY_REPAIRED_UNSUPPORTED`) unless:
1. The family contains at least one repair step (`family.steps.last().is_some()`).
2. The final repair step carries `fitness.checker_verdict == "ACCEPT"`.
3. The final repair step carries `residual_after == Some("Exact")`.

If either condition fails, the family cannot terminate as `"Repaired"`.

### 5.2 Terminal `"BudgetExhausted"`

If resource or turn limits are reached, `kind` must be `"BudgetExhausted"`, and `detail` must explicitly specify an approved budget code beginning with `"BUDGET_"` (e.g. `BUDGET_MAX_CALLS_REACHED`, `BUDGET_COST_LIMIT_EXCEEDED`). Otherwise, it fails with `FAMILY_TERMINAL_DETAIL`.

### 5.3 Terminal `"TypedResidual"`

If evolution terminates due to an irreducible obstruction or valid domain refusal, `kind` must be `"TypedResidual"`, and `detail` must specify the closed refusal identifier.

---

## 6. Claim Hygiene & Formal Boundaries

### What This Artifact Supports
- Confirms that `RepairStep` records DDC operational transitions, residual color changes, and cost/token deltas in `core_prompt_civilization`.
- Confirms that `LamarckianCochainTrackerV1` enforces monotonic defect reduction ($\Delta \Phi_1 \le 0$), distance attenuation, and protected core byte identity.
- Confirms that Pareto fronts are computed using exact rational arithmetic (`Rational64`) without scalar weighting.
- Confirms that `"Repaired"` status requires an independent `"ACCEPT"` verdict and `"Exact"` residual.

### What This Artifact Does Not Support
- Does not claim that Pareto optimization ensures convergence to global optima in arbitrary non-convex prompt spaces.
- Does not grant task success credit or sovereign authority (`AuthorityEffect: None`).
- Does not claim biological realism; "Lamarckian" refers strictly to the inheritance of verified defect repairs across prompt generations under the declared cochain rules.

### Narrowest Defensible Claim
Prompt Sieve provides an exact rational, cochain-monitored evolutionary state machine that verifies non-increasing defect residuals and requires external non-circular checker acceptance for terminal repair status.

### Next Test Needed
A benchmark measuring Pareto frontier stability under adversarial perturbations to candidate cost and token metrics to verify resistance to tiebreak exploitation.

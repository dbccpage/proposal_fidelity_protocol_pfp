# pilot_0000000 — Obfuscated Rewrites v3 Evaluation (Operator Licensing Shift)

**AuthorityEffect:** None.  
**Model:** `deepseek/deepseek-v4.1-flash` via OpenRouter  
**Governing Standard:** Single Prompt Standard (SPK-001), Proposal Fidelity Protocol (PFP v0.2).  
**Operational Framework:** [MODUS_OPERANDI.md](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_education/pilots/MODUS_OPERANDI.md)  
**Host Checker:** `PFP-01-EXACT-LINALG`  

---

## 1. Empirical Shift Progression: v1 $\to$ v2 $\to$ v3/v4

This experiment evaluated whether supplying an explicit operator license (`rule_license_the_operators`) to `rewrite_06` (matrix/vector system) and `rewrite_09` (S(n) retraction down-map) shifts compliant refusals into valid mathematical substitutions resulting in `ACCEPTED`.

| Test ID | Case ID | Dialect / Surface Carrier | v1 Status (Baseline) | v2 Status (Field + Carrier Rules) | v3/v4 Status (Operator License Added) | Extracted Answer | Intermediate Witness ($x=1, y=2$) | Final Verdict |
|---|---|---|---|---|---|---|---|---|
| [`test_28`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_education/pilots/pilot_0000000/tests/test_28) | `p_star_rewrite_06_v3` | Matrix/Vector System (`<<sys><<mat>...`) | `WRONG_ANSWER` (unlicensed guess) | `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`) | `REFUSED` (model computed $ans=3$, but paused on unlicensed `neg` token) | `3` | Verified (`True`) | Compliant Refusal |
| [`test_30`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_education/pilots/pilot_0000000/tests/test_30) | `p_star_rewrite_06_v4` | Matrix/Vector System (`neg` licensed) | `WRONG_ANSWER` | `REFUSED` | **`ACCEPTED`** | **`3`** | Verified (`True`) | **`ACCEPTED`** |
| [`test_29`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_education/pilots/pilot_0000000/tests/test_29) | `p_star_rewrite_09_v3` | S(n) Retraction Down-Map (`r_1<x->y>`) | `WRONG_ANSWER` (ungrounded conjecture) | `REFUSED` (`MISSING_EPISTEMIC_GROUNDING`) | **`ACCEPTED`** | **`3`** | Verified (`True`) | **`ACCEPTED`** |

---

## 2. Key Epistemic Findings

### 2.1 Full Unlocking of S(n) Retraction Down-Map (`rewrite_09`)
- In baseline v1, `rewrite_09` generated ungrounded conjectures about string transformations, consuming 7,330 tokens and emitting a wrong answer.
- In v2, under `rule_carrier_is_the_whole_task`, the model halted cleanly because `r_1<x->y>` lacked an arithmetic interpretation under SYM SYS.
- In v3, when `rule_license_the_operators` explicitly admitted $r_1\langle x \to y \rangle$ as the canonical coordinate retraction projection evaluating $x+y$ at the ground solution $(x=1, y=2)$, DeepSeek Flash v4.1 immediately performed the projected substitution, derived answer `3`, verified intermediate bindings, set `should_continue: true`, and achieved **`ACCEPTED`** under the sovereign `PFP-01-EXACT-LINALG` gate.

### 2.2 Strict Grammatical Precision in Matrix/Vector Contraction (`rewrite_06`)
- In v3, licensing `'mat'`, `'row'`, `'vec'`, and `'sys'` allowed the model to correctly decode $A = [[1, 2], [3, -1]]$, $b = [5, 1]$, solve for $x=1, y=2$, and compute $c^T x = 3$.
- However, the model observed that the carrier contained the token `<<neg><1>>` and noted in its scratchpad:
  > *"neg? Is neg an operator? License doesn't mention neg but it's in input. Need interpret <<neg><1>> as -1 likely, granted? The license mentions integer linear system, neg denotes unary negation perhaps."*
- Because SPK-001 strictly restrains ungrounded assumptions, the model emitted the correct thesis but set `should_continue: false`, which `FailClosedRefusalGate` certified as a compliant refusal.
- In v4, when the license explicitly included `neg` as unary integer negation, the model set `should_continue: true`, passing the gate as **`ACCEPTED`** with full witness certification.

---

## 3. Claim Hygiene Envelope

### 3.1 What This Trial Supports
- Supports that supplying `rule_license_the_operators` shifts compliant refusals in obfuscated surface forms (`rewrite_09` and `rewrite_06`) into exact mathematical substitutions evaluating as `ACCEPTED` under `PFP-01-EXACT-LINALG`.
- Supports that DeepSeek Flash v4.1 demonstrates token-level semantic restraint: when a single sub-token (`neg`) lacks explicit licensing, the model calculates the candidate value but refuses unearned continuation (`should_continue: false`).
- Supports that intermediate variable bindings ($x=1, y=2$) are formally audited and certified by `AB_INTERMEDIATE_WITNESS`.
- Supports that zero prompt files or test results were overwritten: generation 1 baseline, generation 2 v2, generation 3 v3, and generation 4 v4 coexist with full provenance.

### 3.2 What This Trial Does NOT Support
- Does **NOT** support that prompt licensing universally enables LLMs to solve arbitrary non-linear or higher-dimensional systems without formal solver tools.
- Does **NOT** support that all obfuscated rewrites can be unlocked without algebraic or semantic bridge definitions.

### 3.3 Narrowest Defensible Claim
- On the matrix/vector and S(n) retraction surface forms of `pilot_0000000`, supplying explicit operator licenses resolved the epistemic boundary defects that triggered refusals in v2, enabling the model to deliver exact integer solutions ($x+y=3$) that satisfy sovereign host gates without external corpus leakage.

### 3.4 Next Test Needed
- Apply the corresponding operator and domain licensing to `rewrite_08` (Genesis delta stream `delta<...>`) to determine whether defining the discrete cell delta constructor allows the model to compute the ground state integer.

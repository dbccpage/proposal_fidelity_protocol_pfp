# Why packetization exists -- 9 stages (MSS-μ)

**AuthorityEffect:** None  

## Canon path

`omega_engine/crates/symbol_game/_docs/_the_symbol_game_history/`

| File                                | Stage                                       |
| ----------------------------------- | ------------------------------------------- |
| `stage_0_mss_mu_controller(1).yaml` | **0 controller** -- prepended to ALL stages |
| `stage_1_compression_gate.yaml`     | 1                                           |
| `stage_2_ideation.yaml`             | 2                                           |
| `stage_3_audit.yaml`                | 3                                           |
| `stage_4_l2_extraction.yaml`        | 4                                           |
| `stage_5_mss_mu_evaluator.yaml`     | 5                                           |
| `stage_6_adversarial.yaml`          | 6                                           |
| `stage_7_countermodel.yaml`         | 7 (refine; near-dup of 6 in archive)        |
| `stage_8_evidence_plan.yaml`        | 8                                           |

Also: `controller.yaml` (full SPK-001 / MSS-0 38-symbol grammar).

---

## 1. Stage 0 is the whole point of packetization

From `stage_0_mss_mu_controller(1).yaml`:

```text
T finite terms
Ctx finite contexts
R repair edges → ~ transitive → Q = T/~
C1 chain space basis T (F2 in original MSS-μ)
d1 : C1 → C2
ρ : Ctx × T → T
chain lock: if d0 exists, d1∘d0 = 0 else CHAIN_FAIL

```

### Witness obligations (not vibes)

| Class             | Meaning                      | Required witness                                                              |
| ----------------- | ---------------------------- | ----------------------------------------------------------------------------- |
| **Ex** Exact      | \(e_t \in \mathrm{im}(d_0)\) | C0 linear combination                                                         |
| **Surv** Survivor | closed, not exact            | \(d_1(e_t)=0\), not in im(d0); φ>0, γ=0                                       |
| **Open**          | \(d_1(e_t)\neq 0\)           | nonempty d1_image                                                             |
| Lift trigger      | separate                     | context witness \(w=(x,y,c)\): \(x\sim y\) but \(\rho(c,x)\not\sim\rho(c,y)\) |

**Oracle scope:**cargo / SymPy / Lean promote**only** what they test.  

### LLM may propose/compress/classify/route. LLM may not upgrade claim status

### No prose promotes evidence level. No multi-model agreement promotes evidence

That is packetization: **finite algebraic objects + witnesses + host upgrade only**.

---

## 2. The 9-stage machine (DAG, not a chat)

```text
0 CONTROLLER (MSS-μ kernel) ───────────────────────────────────── always on
        │
1 COMPRESSION GATE
   no quotient until word problem finite + decidable equality
   REFUSE: unbounded domain, non-mechanical predicate, undeclared arity
        │ PASS → finite grammar
2 IDEATION
   5-7 candidates; F0 only; at least 2 non-LLM-implementable; 1 weakens theory
        │
3 AUDIT
   kill imported priors, face-without-cell, OP overloading, evidence smuggling
   route: escalate | hold | kill | refuse
        │ escalate
4 L2 EXTRACTION
   prose → typed finite (T, ~, ρ, d0, d1, license) OR refuse
   does NOT evaluate algebra
        │ extracted
5 MSS-μ EVALUATOR
   Ex / Surv / Open + φ / γ + witnesses
   CHAIN_FAIL, SEPARABILITY_FAIL, OBSERVER_FAIL
        │ classified
6 ADVERSARIAL
   separating context w=(x,y,c); repair proposed not authorized
        │
7 COUNTERMODEL REFINE
   stress again (archive near-dup of 6)
        │ survives
8 EVIDENCE PLAN
   name evaluator O0-O5; caps on F-levels; rank usefulness not "truth"
   lift only after external checker -- Stage 8 proposes, does not license alone

```

**TOE one-shot replies skip 1-4 and fake 5.** That is why "magic" was fixture restatement: no compression gate, no extraction packet, no witness obligations.

---

## 3. Map to our live GATE11 / Fable 2

| MSS-μ / packetization        | Live cookbook / Fable 2                                         |
| ---------------------------- | --------------------------------------------------------------- |
| Stage 0 chain lock d1∘d0=0   | `f2step0` nilp; host G2                                         |
| Ex / Surv / Open + witnesses | Exact / StabilizedSurvivor / OpenObstruction + α*, y*           |
| φ, γ gauges                  | Phi, Gamma over Q (not only F2)                                 |
| LLM cannot promote           | AuthorityEffect None; host only                                 |
| Stage 1 compression          | **missing** if we free-prompt Flash with essay God prompts      |
| Stage 4 extraction           | **missing** when model emits markdown prose instead of matrices |
| Stage 5 evaluator            | `gate11_residual_dual` Q host                                   |
| Stage 6 adversarial context  | Open dual / lift witnesses still thin                           |
| Stage 8 evidence plan        | batch summary + oracle routing not fully wired                  |

**Golden `deepseek_reply_000`:**jumped to Stage-5-shaped**wire** with host checks -- that is packetization working.  
**Flash live reply:** failed Stage 1/4 (no finite parseable packet) → 0/0.

---

## 4. Why you invented packetization (one sentence)

### To force every claim through a finite grammar, typed extraction, witness-bearing trichotomy, and oracle-scoped promotion -- so LLMs can only propose, never green-light

Not to write better essays about solvers.

---

## 5. Regge pick-apart = run stages, not monologue

```text
seed → S1 admit grammar
    → S2 candidates (optional for pure dual work)
    → S3 audit
    → S4 extract (T,d0,d1) packet
    → S5 classify Ex/Surv/Open + witnesses   [Fable2 / GATE11 host]
    → S6 context attack
    → S8 evidence / Route plan               [Fable3]

```

For residual dual long shot: **S0+S4+S5** are load-bearing; S2 chat ideation is optional noise.

---

## 6. Next build (honest)

| Priority | Work                                                                                        |
| -------- | ------------------------------------------------------------------------------------------- |
| P0       | Treat Stage 0 controller as required preamble for any model call (wire), not English README |
| P0       | Host refuse without Stage-4-shaped extraction (matrices / T / d0 / d1)                      |
| P1       | Wire Fable2 `f2step` = S5 slice of MSS-μ                                                    |
| P1       | Fable3 Route = S8 legality after class                                                      |
| P2       | Rehydrate Rust CLI "prepend controller to every stage" path if still archived               |

---

## 7. Files to open with brothers

```text
_the_symbol_game_history/stage_0_mss_mu_controller(1).yaml
_the_symbol_game_history/stage_1_compression_gate.yaml
... stage_8_evidence_plan.yaml
_the_symbol_game_history/controller.yaml
_the_symbol_game_history/00_symbol_game_packetization_protocol_architecture.md
prompts/fable_02_gate11_fw8_dual_HARDEST.md

```

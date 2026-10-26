# Formal Rewriting Architecture, Polygraph Diagrams, and Strategy Definitions over the PFP Wire Substrate

**AuthorityEffect:** None.  
**Framework:** Proposal Fidelity Protocol (PFP), Genesis & S(n) Epistemic Architecture, and Minimal Symbol System (MSS-N).  
**Substrate Alphabet:** $\Gamma_{38} = \{a..z\} \cup \{0..9\} \cup \{<, >\}$ and $S(n)$ Enclosures $\{u_k, r_k, \to, [, ]\}$.  
**Normative Status:** Active Architectural Specification and Master PFP Rewriting Engine Reference.  
**Consolidation Notice:** Supersedes and fully replaces legacy files (`adr_reuse_decision.md`, `prompt_rewriting_readme.md`, `review.md`, `rewrite_models.json`, `verification.json`).  
**Companion Documents:**
- [`PKT-00: Packet Wire Grammar`](../packetization/00_packet_wire_grammar_and_ground.md)
- [`S(n) Rewriting Strategies`](../../002_s_n/rewriting/rewriting_strategies_sn_wire.md)
- [`MSS-N Rewriting Strategies`](../../003_minimal_symbol_system_n_mssn/rewriting/rewriting_strategies_mssn_wire.md)
- [`PFP Prompt Hierarchy Domain Models`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_operads/domain/prompt_hierarchy/models.py): Canonical addressable URI taxonomy (`PromptUri`), `PromptTreeNode`, procedural `AntiOpBinding`, empirical `AntibodyBinding`, and typed `PromptGateReceipt`.
- [`PFP Prompt Hierarchy Application Gate`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_operads/application/prompt_gates.py): Two-Signal Danger Gate evaluation (`evaluate_prompt_gates`) enforcing fail-closed gate disposition.
- [`PFP Root Seed Prompt Family Template`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_pfp/infrastructure/yaml/prompts/p_star_family_template.yaml): Canonical YAML prompt packet definition (`PromptPacketV0_1`).
- [`LinkedIn Article 005: What the Hell Is a Prompt`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_atlas/coda_atlas/F004_papers/014_linkedin_articles/linkedin_article_005_what_the_hell_is_a_prompt_v001.md): Pedagogical foundation linking the 5-Stratum ladder and BQNF normal forms to polygraph rewriting over $\Gamma_{38}$.

---

## 1. The Expressive Universe of the PFP Wire Substrate ($\Gamma_{38}$)

The Proposal Fidelity Protocol (PFP) rewriting engine operates on the strict 38-glyph terminal alphabet:

$$\Gamma_{38} = \Sigma_{\text{latin}} \cup \Sigma_{\text{digit}} \cup \Sigma_{\text{boundary}}$$

where:
- $\Sigma_{\text{latin}} = \{a..z\}$ ($|\Sigma_{\text{latin}}| = 26$)
- $\Sigma_{\text{digit}} = \{0..9\}$ ($|\Sigma_{\text{digit}}| = 10$)
- $\Sigma_{\text{boundary}} = \{<, >\}$ ($|\Sigma_{\text{boundary}}| = 2$)

### 1.1 Structural Stratification: Wire Substrate vs. PFP Constructor Profile

PFP separates raw recursive wire syntax from typed constructor profiles:

$$\mathrm{RawNode} ::= \mathsf{Void} \mid \mathsf{Atom}(w) \mid \mathsf{App}(c_1, c_2, \dots, c_m)$$

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PFP WIRE SYNTAX STRATIFICATION                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

 [Tier S: Strict Wire]  ──►  [Tier H: Head-Word]  ──►  [Tier D: PFP Directive]
  <<op><1><<arg><a>>>>       lp<var<x>, dom<0,10>>         <assume p1 <ab>>
  (Zero-Whitespace)          (Human Trace Inspection)     (Host Session Directive)
```

1. **Tier S (Strict Boundary Wire)**: $\Gamma_{38}$ strictly (no spaces or commas). Machine-verified wire substrate for canonical receipts.
2. **Tier H (Head-Word Presentation)**: Human-legible trace inspection for debugging and pedagogical walkthroughs.
3. **Tier D (PFP Directive Protocol)**: Space-delimited session directives (`<assume p1 <ab>>`, `<refusal ERR_EMPTY>`).

---

## 2. PFP Prompt Expansion & Sub-Prompt Tree Rewriting ($P \to P^\star \to \{ P^\star_{\text{sub } ij} \}$)

PFP rewriting governs the transformation of raw prompt packets $P$ into structured prompt trees $P^\star$, unified under the canonical addressable URI scheme ([`PromptUri`](file:///c:/Users/a343o/source/repos/the_symbol_game/omega_engine_operads/domain/prompt_hierarchy/models.py)):

$$\mathsf{URI} ::= \mathtt{prompt://}\langle\text{domain}\rangle/\langle\text{subdomain}\rangle/\langle\text{task}\rangle/\langle\text{stage}\rangle/\langle\text{prompt\_id}\rangle[/\langle\text{subprompt\_id}\rangle]$$

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             PFP PROMPT REWRITING & DECOMPOSITION GRAPH                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

   Raw Packet P (Raw Text / ASCII)
         │
         ▼
   Template Mapping: P ──► P* = InjectTemplate(P, Template, GenID)
         │  (Instantiates root PromptTreeNode with AuthorityEffect: None)
         │
         ├──► Sub-Prompt Tree Expansion: P* ──► { P*_{sub ij} }
         │    Each child node bound to PromptUri:
         │    prompt://<domain>/<subdomain>/<task>/<stage>/<prompt_id>/<sub_id>
         │    Attached negative guards: AntiOpBinding & AntibodyBinding
         │
         ▼
   Stage Sequence Traversal: (P*, S_k, M) ──► Candidate Move
         │
         ▼
   Two-Signal Danger Gate Evaluation:
         ├─ Signal 1: Epitope Pattern Match (Anti-Ops & Admitted Antibodies)
         └─ Signal 2: Host Danger Verification (Coboundary Defect ∂_k ≠ 0)
         │
         ▼
   Retraction Down-Map Reduction: r_k(u_k(P*)) ──► PromptGateReceipt
         ├─ status: PASS (Clearance verified in host code)
         └─ status: REFUSED (NON_DESCENT if ∂_k ≠ 0 or signals fire)
```

### 2.1 Formal Transformation Rules

1. **Template Expansion $P \to P^\star$**:
   $$P^\star = \text{InjectTemplate}(P, \text{PromptTemplate}, \text{GenerationID})$$
   Yields root node with content-addressed lineage (`generation_id: 0`, `PromptPacketV0_1`), declaring invariant `AuthorityEffect: None`.

2. **Sub-Prompt Extraction $P^\star \to \{ P^\star_{\text{sub } ij} \}$**:
   $$\text{cardinality}(P^\star) = 1 + \sum_{c \in \text{children}(P^\star)} \text{cardinality}(c)$$
   Each child $P^\star_{\text{sub } ij}$ is instantiated as a typed `PromptTreeNode` indexed by its canonical `PromptUri`. It inherits parent generation ID $\text{g0}$ and binds:
   - Procedural Anti-Ops (`AntiOpBinding`): inspecting target slots for syntax violations, unlicensed imports, or missing intermediate variable bindings.
   - Empirical Antibodies (`AntibodyBinding`): guarding against known historical failure shapes (`minimum_status: admitted`).

3. **Stage Traversal & Two-Signal Gate Evaluation**:
   Dispatches prompt tree $P^\star$ through stages $S_1 \dots S_8$ under mode $M$. Candidate outputs are evaluated by `evaluate_prompt_gates` prior to terminal admittance:
   - **Signal 1 (Epitope Match):** Triggers if candidate syntax matches an armed negative pattern.
   - **Signal 2 (Host Danger Trigger):** Confirmed by host testing, linter, or compiler. Unadmitted candidate antibodies remain inert.
   - Emits an immutable `PromptGateReceipt` recording evaluated/fired anti-ops, evaluated/fired antibodies, and status (`PASS` or `REFUSED`).

4. **$S(n)$ Retraction Identity & Non-Descent Rule**:
   $$r_k(u_k(P^\star)) \rightsquigarrow P^\star \implies \text{Receipt}(\text{status: PASS})$$
   $$r_k(P^\star) \rightsquigarrow \text{NON\_DESCENT} \quad \text{if } \partial_k(P^\star) \neq 0 \implies \text{Receipt}(\text{status: REFUSED})$$

---

## 3. Polygraph Rewriting Architecture & 3-Cell Confluence

The PFP rewrite system forms a 3-polygraph $(\mathcal{P}_0, \mathcal{P}_1, \mathcal{P}_2, \mathcal{P}_3)$:
- **0-cells ($\mathcal{P}_0$)**: Base glyph alphabet $\Gamma_{38}$.
- **1-cells ($\mathcal{P}_1$)**: Strict boundary packets and prompt tree nodes $P^\star$.
- **2-cells ($\mathcal{P}_2$)**: Elementary rewrite reductions $L \rightsquigarrow R$ (e.g., $r_k(u_k(x)) \rightsquigarrow x$).
- **3-cells ($\mathcal{P}_3$)**: Confluence syzygies resolving critical peaks $(L \rightsquigarrow_1 R_1, L \rightsquigarrow_2 R_2)$.

```
                            [ Critical Peak: L ]
                               /            \
                              /              \
                             ▼                ▼
                         [ R_1 ]            [ R_2 ]
                            \                /
                             \              /
                              ▼            ▼
                         [ Confluent Join: C ]
```

### 3.1 Confluence & Termination Invariants

1. **Local Confluence (Newman's Lemma)**: Every critical peak $(L \rightsquigarrow R_1, L \rightsquigarrow R_2)$ resolves to a unique confluent join $C$.
2. **Strict Termination**: All rewrite reductions descend monotonically under weight function $W(p) = |p|_{\text{boundary}} + \sum \text{depth}(p_i)$, ensuring finite termination under the declared metric.

---

## 4. Woland Retinue 13-Gate Verification Protocol

Every PFP rewrite sequence is audited by the 13 Woland Retinue character gates:

| Gate ID | Character | Verification Rule | Disposition |
|---|---|---|---|
| `01_hella_cold_syntax` | Hella | UTF-8 zero-BOM, lowercase filenames, syntax cleanliness | `REQUIRED` |
| `02_koroviev_nocebo_plunge` | Koroviev | Nocebo/placebo dialectic surprise auditor | `REQUIRED` |
| `03_begemot_gauge_break` | Begemot | Gauge break detector & discrete cochain boundary check | `REQUIRED` |
| `04_azazello_scope_assassin` | Azazello | Scope creep assassin & dead code hunter | `REQUIRED` |
| `05_abadonna_terminal_gaze` | Abadonna | Silent skip hunter & falsification verifier | `REQUIRED` |
| `06_margarita_primal_dual` | Margarita | Dual LP feasibility & Primal/Dual circulation auditor | `REQUIRED` |
| `07_the_master_manuscript_truth` | The Master | Canonical manuscript tie-out & Lean 4 proof checker | `REQUIRED` |
| `08_bezdomny_scar_chronicler` | Bezdomny | Historical evidence chronicler & audit log validator | `REQUIRED` |
| `09_bengalsky_anti_hype` | Bengalsky | Anti-hype claim hygiene linter (banning "proves", "flawless") | `REQUIRED` |
| `10_annushka_oil_spill` | Annushka | Memory leak, resource leak & exception spill detector | `REQUIRED` |
| `11_stravinsky_quarantine` | Stravinsky | Stravinsky quarantine isolation for legacy/experimental tests | `QUARANTINED` |
| `12_pilate_anti_cowardice` | Pilate | Anti-cowardice gate enforcing fail-closed assertions | `REQUIRED` |
| `13_woland_terminal_reality` | Woland | Terminal reality referee issuing final signed receipt | `REQUIRED` |

---

## 5. Consolidated ADR & Legacy Module Mapping

This single canonical document consolidates and retires the following legacy specification files:

1. **`adr_reuse_decision.md`**: Consolidated into Section 1.1 (Tier S/H/D structural stratification and AST component reuse).
2. **`prompt_rewriting_readme.md`**: Consolidated into Section 2 (PFP prompt expansion $P \to P^\star \to \{P^\star_{\text{sub } ij}\}$ and sub-process trees).
3. **`review.md`**: Consolidated into Section 3 (Polygraph rewriting architecture, Newman's Lemma confluence, and 3-cell critical peaks).
4. **`rewrite_models.json` & `verification.json`**: Consolidated into Section 4 (Woland Retinue 13-gate verification matrix and signed receipt schemas).

---

## 6. Claim Hygiene Summary

1. **What it supports:** Provides the master PFP rewriting specification, polygraph diagrams, $S(n)$ stage integration, and Woland Retinue 13-gate verification rules.
2. **What it does not support:** Does not self-certify compliance through markdown text alone; execution requires verified Python/Rust test suites in `omega_engine_operations.tests.cicd`.
3. **Narrowest defensible claim:** This document serves as the single canonical rewriting specification for the Proposal Fidelity Protocol.
4. **Next test needed:** Execute gate verifiers via `py -3.12 -m pytest omega_engine_operads/tests/unit/test_prompt_hierarchy.py` and `py -3.12 -m pytest omega_engine_operations/tests/cicd/test_cicd_suite.py`.

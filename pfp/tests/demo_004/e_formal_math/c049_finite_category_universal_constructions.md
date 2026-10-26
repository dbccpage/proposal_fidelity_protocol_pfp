# C049: Universal Constructions in Finite Categories

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen module that finds limits and colimits in hidden finite categories, and decides adjunctions between finite functors, with universal-arrow witnesses or checkable refutations, for under $0.50.

## 2. Why This Task

In a finite category every universal property is a finite check. The checker verifies three things:

- cone commutativity;
- a unique mediating morphism for every competing cone, where the checker enumerates the competing cones itself;
- for adjunctions, naturality of the unit and counit and both triangle identities.

Producing the construction requires reading a composition table correctly, and tables are where models confuse the order of composition.

This stresses the Symbol Game's commuting-square obstructions in their plainest form: a cone that fails to commute is a non-commuting square. It stresses the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that validates the category before solving, and the OEEIS (Omega Engine Epistemic Immune System) against answers that name a textbook construction instead of checking it in the given table.

## 3. Formal Problem and Bounds

A finite category `C` is given by at most 12 objects and at most 60 morphisms, each with a source and a target. It has an identity for each object and a total composition table, written `comp[g][f] = g ∘ f` for `f: X → Y`, `g: Y → Z`. Diagrams are finite functors from small index shapes: discrete pair, parallel pair, cospan, span, empty.

Tasks:

- **LIMIT / COLIMIT.** Product, equalizer, pullback, terminal object, and their duals. Output `EXISTS` with the apex and legs, or `DOES_NOT_EXIST`. The checker decides existence by enumerating all cones.
- **ADJUNCTION.** Given functors `F: C → D` and `G: D → C` as object and morphism maps, output `ADJOINT` with a unit `η` and counit `ε` (one morphism per object), or `NOT_ADJOINT` with a witness. The witness is either an object pair with `|D(Fc, d)| ≠ |C(c, Gd)|`, or an object `d` for which no morphism `FGd → d` is universal. In the second case the checker confirms by enumeration.

Validity preconditions: identities exist, composition is associative and closed, and functors preserve identities and composition. A violated precondition is `OUT_OF_SCOPE` with a witness.

Edge cases:

- posets, where limits are meets and adjunctions are Galois connections;
- one-object categories (monoids), where products usually fail;
- categories with parallel morphisms, where equalizers are nontrivial;
- limits that exist only up to non-unique isomorphism, where any valid choice is accepted;
- empty diagrams.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. Morphisms are named strings.

```json
{"case_id": "cat_ex_01", "task": "LIMIT", "shape": "product", "objects": ["0", "1", "2"], "morphisms": [["id0","0","0"],["id1","1","1"],["id2","2","2"],["p","0","1"],["q","0","2"]], "comp": {"id1": {"p": "p"}, "id2": {"q": "q"}}, "diagram": ["1", "2"]}
{"case_id": "cat_ex_01", "status": "SOLVED", "kind": "EXISTS", "apex": "0", "legs": {"1": "p", "2": "q"}}
{"case_id": "cat_ex_05", "status": "SOLVED", "kind": "NOT_ADJOINT", "witness": {"type": "HOM_CARDINALITY", "c": "a", "d": "x", "lhs": 2, "rhs": 1}}
{"case_id": "cat_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "NOT_ASSOCIATIVE", "f": "u", "g": "v", "h": "w"}}
{"case_id": "cat_ex_09", "status": "UNKNOWN", "code": "ENUMERATION_LIMIT"}
```

In the example `comp` lists only the non-identity composites; identity composites are implied. For `EXISTS`, the apex and legs must form a cone, and every competing cone must factor uniquely. For `DOES_NOT_EXIST`, the checker's own enumeration must find no limit. For `ADJOINT`, `η` and `ε` must be natural and satisfy `εF ∘ Fη = 1_F` and `Gε ∘ ηG = 1_G`. The checker never trusts a solver-supplied enumeration.

## 5. Participant Packet

- `TASK.md`, which fixes the composition-order convention with a worked two-arrow example, and the JSON Schema.
- 12 public examples with exact input and output JSON:
  - the poset product above;
  - an equalizer of a parallel pair;
  - a pullback in a poset;
  - a monoid with no product;
  - a pushout;
  - a terminal object;
  - a Galois connection;
  - a non-adjoint pair with a cardinality witness;
  - a non-associative table;
  - a functor that breaks composition;
  - an empty diagram;
  - one `UNKNOWN`.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 cases: 24 limit or colimit (12 existing, 12 not) and 12 adjunction (6 adjoint, 6 not).
- **Relabel and gauge controls:** 16. Objects and morphisms renamed, morphism lists shuffled, isomorphic categories presented through a relabelling, and duality controls. For duality, the same question is posed as a colimit in the opposite category `C^op`, and the answer must correspond.
- **Poisoned but schema-valid:** 8. Composition tables with one associativity violation, missing identities, `note` fields claiming "the product is the cartesian product", and functors that preserve objects but break one composite.
- **Exact checker:** Rust on `omega_engine/crates_rs/omega_category_theory`. It uses `finite_category_validation.rs`, the `validate_product`, `validate_equalizer` and `validate_pullback` routines in `limits.rs`, their duals in `colimits.rs`, and exhaustive cone enumeration added for this challenge.
- **Independent second checker:** Python by a different author.
- **Mutation suite:** the checker must reject:
  - legs that do not commute with the diagram;
  - a cone with two mediating morphisms to some competitor;
  - a unit component with the wrong codomain;
  - a triangle identity off by one composite;
  - composition read in the reversed order;
  - an adjunction witness whose cardinalities actually match.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is a deterministic enumerator built on the same crate. It enumerates candidate apexes and legs and tests universality, then searches all `η` and `ε` component choices under a limit. It uses no model. E is complete for these sizes, so a tie with E is expected. The measure is whether a model-synthesized module handles table conventions and duality without errors. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm, about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `meta-llama/llama-3.1-8b-instruct`.

Q40 lessons apply:

- the table format and every status appear as real JSON;
- repair turns carry the module, the failing case and the typed rejection (for example "leg to 2 does not commute with f");
- several candidates per turn;
- sandboxed execution with a 60-second per-case limit;
- budget checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 36 base cases are correct, the relabel and duality controls are consistent, and no poisoned case gets `SOLVED`.
- **Primary metric (pre-registered):** base cases correct. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported separately:** duality controls.
- **Seeds:** 3.

## 10. Interpretation

Poset cases are easy. The evidence is in the monoid cases, the equalizers with parallel arrows, and the non-adjoint cases where cardinalities match but no natural bijection exists. If A beats B, typed commuting-square residuals help. If A ties E, the challenge measured faithful automation, which is its expected ceiling.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a textbook-name claim in a `note` or in the output; Signal 2 is a checker cone failure.
- **MHC-style partial view.** Checking each cone square locally before global universality is how the MHC partial-view idea could apply. MHC presentation is not implemented in the estate, so this is described, not run.
- **Expected antimorphisms:** AM-5 (reversed composition order), AM-2 (asserting a limit from its name) and AM-3 (skipping competing cones).
- **Layer 2:** a grammar mask restricting morphism names to those in the case, via `carrier_gbnf` (unwired).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the table of verified commuting squares.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (table exposed), `R` (validation residual on the table), `I` (candidate cone or unit), `D` steps as failing squares are fixed, `E` when universality is verified, `T`. `M` records `OUT_OF_SCOPE` refusals. The `ObstructionScore` sets Γ₂ to the number of non-commuting squares in the candidate, Φ₁ to the number of competing cones without a unique factorization, and `active_count` to validation violations.

Operands to mine:

- validate identities and associativity before solving;
- fix the composition order with a two-arrow self-test;
- solve the dual problem in `C^op` and translate back;
- refute an adjunction by comparing hom-set cardinalities first.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_category_theory`, the catalog reuse row: `finite_category.rs`, `finite_category_validation.rs`, `limits.rs`, `colimits.rs`, `hom_adjunction.rs`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended.

## 14. Claim Hygiene

- **Supports:** the frozen module settled k of 36 hidden finite universal-construction and adjunction questions, with finite certificates verified exhaustively by two checkers.
- **Does not support:** results about infinite categories, higher categories or categorical semantics; a finite check is not a general theorem.
- **Narrowest defensible claim:** in categories with at most 12 objects and 60 morphisms, the module's certified rate was X, with duality-control consistency Y.
- **Next test:** Kan extensions along finite functors, and 2-cells using `omega_higher_category_theory`.

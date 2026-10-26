# Operadic Semantics Map

> **HISTORICAL.** Paths in this note that name `.agents/operad/` are not the live tree. The executable tree is `skill_operad/`. The consolidation record is [chapter 23](../../../omega_engine_education/documentation/008_oewas/atlas/23_plan_oewas_consolidation_oeeis_and_demo_integration.md).

**AuthorityEffect: None.** Read this before typing a skill or composing a pipeline.

For the atlas and current nonclaims, see the
[OEWAS Atlas and Encyclopedia](../../../omega_engine_education/documentation/008_oewas/atlas/00_oewas_atlas_encyclopedia.md).

This file tells a model that has never seen the repo what the skill signatures mean.
It is descriptive: where the implementation and the theory disagree, this file records
what is actually true today, in Honest limits.

---

## 1. The ten colours

A **colour** is the kind of residual object a skill consumes or produces. There are ten,
and no more may be invented without a skill that inhabits it.

| Colour     | In practice                                                                  |
| ---------- | ---------------------------------------------------------------------------- |
| `State`    | Repository, session worktree, git ref, or execution-environment state        |
| `Proof`    | Lean 4 proof term, math derivation, or step-truth assertion                  |
| `Paper`    | OEARS paper package, LaTeX source, Pandoc AST, or claim ledger               |
| `Code`     | Rust/Python implementation, AST, solver module, or Pydantic schema           |
| `Contract` | Nomos governance contract, prime rule YAML, or API boundary specification    |
| `Receipt`  | Evidence receipt, CI report, swarm review, or SHA256 manifest                |
| `Ledger`   | Claim-queue row, refusal store, hypothesis tree, or issue register entry     |
| `Diagram`  | DIME figure, quick-start card, AST graph, or visualization artifact          |
| `Audit`    | Symmetry audit, red-team diagnostic, compliance report, or defect escalation |
| `Post`     | Public math post, Glossa dialect draft, or forum cadence item                |

---

## 2. Reading a skill signature

A skill with declared invocation grading carries this in its `SKILL.md` frontmatter:

```yaml
operad_source_colours: ["Paper", "Proof"]   # what it consumes, in slot order

operad_target_colour: "Paper"               # what it produces (exactly one)

operad_arity: 2                             # MUST equal len(source_colours)

operad_residual: "unknown"                  # only admitted value in this compatibility layer

invocation: entry                           # entry | discipline
```

Default residual is **`unknown`**. The current `evidence_trace.json` rows are
diagnostic residual observations, not contractivity certificates. They cannot
justify `contractive`; `residual_honesty.py` enforces this fail-closed ceiling.

Read as `rip-papers : (Paper, Proof) → Paper`. Slot order matters: no operation is
declared `equivariant`, so inputs may **not** be permuted.

---

## 3. The grading law: `entry` vs `discipline`

This is the composition rule that actually holds across the corpus, and it was
discovered independently twice.

- **`entry`** -- a single point of entry a human invokes. The `rip-*` family calls itself
  "SINGLE POINT OF ENTRY"; `0-oe-commit` is one too.
- **`discipline`** -- a reusable stage another skill invokes. `paper-build` calls itself
  "OEARS stage_5"; `thanatos-old-man-chatgpt-red-team` runs "at the very end of EVERY
  /rip-* workflow".

**The law: an `entry` skill may invoke `discipline` skills, but never another `entry`.**
Discipline skills may invoke each other. This makes the entry layer terminal -- nothing
composes on top of it.

`github.com/mattpocock/skills` states the identical rule for an unrelated 27-skill corpus
("A user-invoked skill may invoke model-invoked skills, but never another user-invoked
one"). Two independent corpora converging on one grading is stronger evidence than any
colour assignment currently has.

---

## 4. Composition and typed refusal

`B ∘ᵢ A` is legal iff **A's target colour equals B's i-th source colour**. The resulting
signature is `B.source[:i] + A.source + B.source[i+1:] → B.target`.

Three typed refusals, defined in `coloured_operad.py`:

- `IllTypedCompositionRefusal` -- output colour ≠ the slot's input colour.
- `MissingColourRefusal` -- a required colour has no inhabitant.
- `NonMonotoneResidualRefusal` -- residual mass failed to decrease where a decrease was promised.

A pipeline is well-typed iff every adjacent pair type-checks **and** the grading law holds.
Colour agreement alone is not sufficient: `github` and `0-oe-commit` are both
`[State] → State` and are not interchangeable.

---

## 5. `residual_effect` and `evidence_trace`

- `contractive` -- reserved for a future independently verified certificate path.
- `exact` -- residual eliminated. Reserved for identity operations.
- `unknown` -- no measurement. **This is the correct default.**

Rows without the current recorder schema are classified as
`LegacyResidualObservation`; rows from the current content-addressed recorder are
`RecordedResidualObservation`. Both preserve diagnostic scalars, and both have
zero claim effect for contractivity, equivalence, quotienting, or promotion. No
finite count crosses that boundary. Meta-skills remain `status: provisional`.

**Quotienting on signature shape alone is wrong.** `github` (a 16 KB git-operations
manual) and `0-oe-commit` (a commit workflow) share the signature `[State] → State`; the
quotient marks one redundant. Signature is a necessary condition for merging, never a
sufficient one. Real factoring looks like `grilling` in the mattpocock corpus: extracted
because two entry points needed the same inner loop, not because two signatures matched.

---

## Honest limits

What is **not** true today, stated plainly so no one builds on it:

1. **Typing is broad; behavioral coverage is not.** The live signature has typing
   metadata for all 128 operations, but only 16 carry invocation grading and the
   composition matrix contains only one declared edge. Missing grading is not
   evidence that an operation is a discipline.
2. **All non-identity operations must remain non-contractive without independent
   evidence.** Existing scalar rows are observations only and cannot certify
   `residual_effect=contractive`. The live registry's custom residual vocabulary is
   drift, not an authorization to widen this rule.
3. **All three synthesized meta-skills are `provisional`.** No observation count
   mints them.
4. **No current skill frontmatter declares `equivariant`.** The live registry
   preserves one stale equivariant flag. Operational composition is planar; do not
   infer a symmetric action or equivariance law from that registry field.
5. **Associativity remains open on the live workflow corpus.** The former witness
   depended on the deleted `panepistimion-paper-build` operation. The matrix now
   declares no associativity law, and `operad_law_audit.py` refuses to report
   zero-of-zero as confirmed. A replacement requires a workflow-supported triple;
   colour-compatible operations are not interchangeable.
6. **`bulk_operad_ingest.py` is DEF-OP-01 quarantined.** Dry-run by default; writes require
   `OMEGA_BULK_OPERAD_INGEST=1`. `infer_colours()` is still heuristic -- treat any colour it
   produced as unverified. Residual is always forced to `unknown` on ingest.
7. **`operad_signature.json` identities/compositions layout** is not fully round-trip
   consistent with `to_signature_dict()`; compositions live primarily in
   `composition_matrix.json`.
8. **Many `ext-*` skill packages are thin shells** -- not proof of operad soundness.

---

## PROPOSED_DESIGN (not execution authority)

The following are **explicitly out of execution scope** until residual honesty + skill
compiler eval bank are the default path for procedural change:

| Proposal                                                      | Status                   |
| ------------------------------------------------------------- | ------------------------ |
| ∞-operad / higher operad re-foundation of the skill garden    | `PROPOSED_DESIGN`        |
| HoTT univalent skill minting / path-type skill identity       | `PROPOSED_DESIGN`        |
| Auto-admit NEW_SKILL from HIGH confidence alone               | **Forbidden** (ooutwire) |
| Claiming `contractive` from `evidence_trace.json` scalar rows | **Forbidden**            |

Do not implement the first two as blockers for Phase 0-2 compiler work.

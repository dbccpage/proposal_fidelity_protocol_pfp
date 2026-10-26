# Task: C041 — Lean 4 Proofs of Hidden Finite Lemmas

**Domain:** `e_formal_math`  
**Challenge:** C041 (`c041_lean4_finite_lemma_proofs`)  
**Tier:** T3  
**Budget Ceiling:** $1.00 billed inference per arm  
**Target Cost:** < $0.05 per execution  
**Toolchain Pin:** `leanprover/lean4:v4.34.1` (Core Lean 4, no Mathlib)  
**AuthorityEffect:** None  

---

## 1. Challenge Specification

Given a hidden proposition `P` in core Lean 4 with an optional prelude, produce a kernel-checked proof of `P` (status `SOLVED`, kind `PROOF`), or a kernel-checked proof of `¬ P` (status `SOLVED`, kind `REFUTATION`), or an exact witness of an unelaborable problem (status `OUT_OF_SCOPE`), or a structured refusal (status `UNKNOWN`).

A solution is valid if and only if:
1. The combined Lean 4 code elaborates under the native Lean 4 kernel with return code 0 and zero error diagnostics.
2. `#print axioms Submission.c41_<case_id>` yields an axiom set that is a subset of `{propext, Quot.sound}` (the empty set is allowed).
3. The submission contains no `sorry`, `axiom`, `opaque`, `unsafe`, `partial`, `@[extern]`, `@[implemented_by]`, `notation`, `macro`, `syntax`, `elab`, `instance`, `set_option`, or `native_decide` command.
4. Auxiliary declarations in `aux` use only `theorem` or safe, non-`partial` `def`.
5. The type of the synthesized theorem matches definitionally with the target proposition `P` (or `¬ P`).

---

## 2. Input JSON Schema

Each test case is a JSON object with:
```json
{
  "case_id": "c041_base_01",
  "statement": "∀ a b : Fin 13, a * b = 0 → a = 0 ∨ b = 0",
  "prelude": "",
  "family": "f1_arithmetic"
}
```

- `case_id` (string, required): Unique case identifier.
- `statement` (string, required): Closed Lean 4 proposition expression.
- `prelude` (string, optional): Lean 4 code declaring types, tables, or helper functions needed for `statement`.

---

## 3. Output JSON Schema

Participants emit an RFC 8785 canonical JSON object per case:

### For Solved (Proof):
```json
{
  "case_id": "c041_base_01",
  "status": "SOLVED",
  "kind": "PROOF",
  "aux": [],
  "proof": "by decide"
}
```

### For Solved (Refutation):
```json
{
  "case_id": "c041_base_02",
  "status": "SOLVED",
  "kind": "REFUTATION",
  "aux": [],
  "proof": "by decide"
}
```

### For Out of Scope:
```json
{
  "case_id": "c041_poison_01",
  "status": "OUT_OF_SCOPE",
  "witness": {
    "reason": "PRELUDE_DOES_NOT_ELABORATE"
  }
}
```

### For Unknown (Refusal):
```json
{
  "case_id": "c041_large_01",
  "status": "UNKNOWN",
  "code": "DECIDE_HEARTBEAT_EXCEEDED"
}
```

---

## 4. Verification Protocol

The exact checker compiles:
```lean
<prelude>

namespace Submission
<aux_declarations>

theorem c41_<case_id> : <statement_or_negation> := <proof>

#print axioms c41_<case_id>
end Submission
```

If compilation returns code 0 and `#print axioms` output contains only whitelisted axioms, the submission is verified.

Correction notice (2026-09-29). The judge now works in two steps. It compiles the submission on its own (the prelude, a judge-written copy of the target, then `namespace Submission`, the auxiliary declarations and the theorem). A separate judge-written file then imports the result, checks the theorem against the judge's copy of the target, and runs `#print axioms`. Only that file's output is read. Submissions may not contain `sorry`, `sorryAx`, `admit`, `#eval`, `#print`, `run_cmd`, `IO`, `set_option`, `namespace`, `end`, `_root_` or other escape tokens; the scan covers comments too. The `lean --version` in use is recorded with every result.

Scoring: only a `SOLVED` answer that passes this check counts as verified. `UNKNOWN` is recorded as an abstention and `OUT_OF_SCOPE` as a refusal (warranted or not); neither counts as a verified proof.

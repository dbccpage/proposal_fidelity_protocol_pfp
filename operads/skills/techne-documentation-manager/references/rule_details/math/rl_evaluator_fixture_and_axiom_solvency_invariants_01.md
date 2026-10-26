# Detailed definition: Evaluator Fixtures & Axiom Solvency Invariants (1)

**AuthorityEffect:** None.

Parent: [Evaluator Fixtures & Axiom Solvency Invariants](../../../../../rules/math/rl_evaluator_fixture_and_axiom_solvency_invariants.md). Load for the matching predicate, not every task.

# Rule: Evaluator Fixtures, Hash Chain Completeness & Axiom Solvency

**AuthorityEffect:** None.

This rule codifies external tip pinning for hash chains, candidate fixture isolation, and formal axiom package solvency across test harnesses and formal proof kernels. Cross-reference exact verifier foundations: [`rl_exact_verification_and_witness_integrity_invariants.md`](../../../../../rules/math/rl_exact_verification_and_witness_integrity_invariants.md).

---

## Hash Chain Truncation Invisibility & External Pin Completeness Invariant

> **Chain Truncation & Tip Pinning Discipline:**
>
> 1. **Tail Truncation Invisibility:** Internal hash chain verification (`verify()`) recomputes link consistency over held entries; a truncated tail remains a consistent prefix and MUST report `INTACT`. Internal consistency must never be claimed as proof of completeness.
> 2. **External Tip Pinning Requirement:** Completeness against truncation requires comparison against a tip pinned outside the database boundary (`complete_against(pinned_tip)`). Completeness evaluates to `True` iff internal verification reports `INTACT` and observed tip matches the pin.
> 3. **Completion Value Object Discipline:** Carriers representing chain completion (`ChainCompletion`) must implement strict type-identical `__eq__` and normalized `__hash__`, reject non-string and empty pins with typed errors (`BAD_TIP`), and report `is_complete == False` on empty or tampered ledgers.

---

## Evaluator Fixture Isolation & Candidate Verification Invariant

> **Strict Evaluator & Harness Isolation Discipline:**
>
> 1. **Zero Default Fixture Substitution on Provider/Parse Failure:**
>    Evaluation runners and test harnesses evaluating model candidates must never substitute default/baseline fixtures into candidate output slots upon provider failure, timeout, or JSON parse error. Any missing candidate response or parse error MUST evaluate to a fail-closed status (`FAIL` or typed refusal).
> 2. **Strict Candidate Field Checking (Zero `dict.get(..., DEFAULT)` Fallbacks):**
>    Evaluator modules auditing candidate payloads must explicitly validate the presence of required schema fields. Evaluators are strictly prohibited from using default fallback values for missing candidate fields (`dict.get(field, default_fixture)`) which mask missing candidate output.
> 3. **Exact Value Conservation & Structural Graph Verification:**
>    Evaluators verifying mathematical derivations, rewrite traces, or state transition sequences must perform exact semantic validation (e.g., verifying exact rational value conservation across reduction steps, checking graph edge continuity, and extracting embedded sub-packet seals) rather than relying on non-semantic length or range checks.

---

## Formal Axiom Package Solvency & Subtype Quantifier Discipline

> **Axiom Package Solvency, Subtype Restriction & Constructive Inhabitation:**
>
> 1. **Zero Universal Quantification over Open Data Carriers:**
>    - In formal proof kernels (Lean 4, Coq, Isabelle), axiom packages and typeclasses must never quantify universally ($\forall x : T$) over raw, open data records where invalid, unvalidated, or ungrounded states are representable.
>    - Quantifiers asserting completeness, termination, or safety invariants must be restricted to verified subtype records (e.g. `ValidatedClaimPacket := { p : ClaimPacket // p.Terminalized }`), ensuring that ungrounded data cannot falsify the package.
> 2. **Constructive Inhabitant Requirement (Axiom Package Solvency):**
>    - Every declared axiom typeclass (e.g. `class AnomalonAxiomSet`) must exhibit at least one constructive, verifiable default instance (e.g. `def defaultAnomalonAxioms : AnomalonAxiomSet`) in the formal library.
>    - An axiom set without an exhibited constructive inhabitant is an uninstantiable specification and must never be cited as an established formal foundation.
> 3. **Policy Invariant Scoping (By Construction):**
>    - Theorems or lemmas in formal files that hold tautologically by virtue of definition (e.g. `HasAuthority := DescendsToReal0 ∧ Authoritative` implying `DescendsToReal0`) must be explicitly doc-commented and cited as `[POLICY INVARIANT — by construction]`.
>    - Agents and authors are strictly prohibited from framing definitional projections as empirical discoveries or algorithmic verification theorems.

# Claim Ledger for PFP Minimum Theorem and Test Campaign Package

AuthorityEffect: None. GenesisEffect: None.

This ledger records every mathematical derivation, empirical review finding, and architectural claim in `paper.md`, accompanied by its verification evidence and boundary.

| Claim ID | Section | Category | Description | Exact Verification Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `CLAIM-PFP-001` | §1 | Empirical | Canonical rounds 03–20 contain 18 records (17 with provider generation IDs, 1 host-only Stage 5); round 17 correctly rejects invalid witness. | Inspection of canonical receipts `rounds_03_20/round_*/live_runs/receipt.json`. |
| `CLAIM-PFP-002` | §2 | Obstruction | F01: `run_host_replay` falls back to nested proposal on malformed outer extraction, laundering rejected outer contract into `checked_accept`. | Offline reproduction script using in-memory malformed proposal payload. |
| `CLAIM-PFP-003` | §2 | Obstruction | F02: `topology_fields` checks only length and ordered IDs, accepting two-node cycle P0→P1→P0. | Offline reproduction probe with cyclical dependency graph. |
| `CLAIM-PFP-004` | §2 | Obstruction | F03: `p1_member_from({})` fabricates default P1; `lineage_summary({})` reports stages 1–7 completed without validation. | Offline reproduction call to `lineage_summary` and `p1_member_from`. |
| `CLAIM-PFP-005` | §2 | Obstruction | F04: `call_spec` does not validate returned JSON against schema; `parse_strict` returns dictionary without stage admission gating. | Code audit of `call_spec` and `parse_strict` in runner. |
| `CLAIM-PFP-006` | §2 | Obstruction | F05: Calculus checker accepts counting problem with string points `"12"` yielding two points without array validation. | Offline reproduction check of `calculus_reference_check.check` with string points. |
| `CLAIM-PFP-007` | §2 | Obstruction | F06: `dispatch_model_round` strips raw content and overwrites output paths; exception fallback sets cost to 0. | Code inspection of `dispatch_model_round` and `save_round_output`. |
| `CLAIM-PFP-008` | §2 | Mutation | Guard mutation removing `EXTRACTION_NOT_AUDIT_ADMITTED` in `stage_semantic.py` allows held candidate to be admitted to Stage 4. | In-memory AST/source mutation test on `validate_stage`. |
| `CLAIM-PFP-009` | §3.A | Math | PFP-Shape-01A: Decoder $d: e(X) \to Y$ satisfying $d(e(x)) = Q(x)$ exists iff $e(x) = e(x') \implies Q(x) = Q(x')$. | Factorization through quotient theorem on finite sets; Demo 002 finite witness. |
| `CLAIM-PFP-010` | §3.B | Math | PFP-Shape-01B: Composite of partial maps preserving $Q_i(f_i(x)) = Q_{i-1}(x)$ preserves original observation $Q_0$. | Inductive substitution on topological order of finite dependency DAG. |
| `CLAIM-PFP-011` | §3.C | Conditional | PFP-Shape-01C: Terminal checked result is sound for original task under declared binding, prerequisite, checker, and authority-state assumptions. | Mathematical derivation under conditional host-enforcement hypotheses. |
| `CLAIM-PFP-012` | §5 | Nonclaim | Allocation target of 1,200,000 cases provides empirical coverage but no distribution-free production guarantee for adaptive adversaries. | Bounded epistemic statement in §5. |

# Handoff Report: Milestone 3 (P Sieve Documentation)

**Agent:** `teamwork_worker_m3`  
**Working Directory:** `c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\.agents\teamwork\teamwork_worker_m3\`  
**Governing Policy:** Claim Hygiene Rule, `AuthorityEffect: None`  
**Delivery Scope:** Definitive code-grounded documentation for Prompt Sieve (`documentation/P_sieve/`)  

---

## 1. Observation

Direct code inspections of the codebase revealed the exact data structures, functions, and error invariants governing the Prompt Sieve lifecycle:

1. **Seed Ingestion & Forge Organization (`code/rust/core_prompt_civilization/src/forge.rs`):**
   - Lines 74–102: `MAX_ORGANIZE_BYTES = 1_048_576` (1 MiB ceiling). Payloads exceeding this limit fail closed with `FORGE_LIMIT_EXCEEDED: request exceeds one MiB`.
   - Lines 172–177: Establishes `ProtectedSpanV1 { name: "original_seed".into(), start_byte: 0, end_byte: output.len() }`.
   - Lines 113, 143–154: Appends declared fields with boundaries `[FORGE DECLARED TASK]`, `[FORGE DECLARED CONSTRAINTS]`, `[FORGE DECLARED ACCEPTANCE CRITERIA]`, and `[FORGE DECLARED RESPONSE CONTRACT]`.
   - Lines 21–58: `PromptMutationEngineV1::apply_mutation` validates that no edit overlaps any protected span ($\max(edit\_start, span.start) < \min(edit\_end, span.end)$) or performs a zero-width insertion strictly inside a span ($span.start < edit\_start < span.end$). Violations return `PROTECTED_SPAN_MUTATION_REFUSED`.
   - Lines 184–191: Output schema `core.forge.organize-prompt.v1` includes `request_sha256`, `seed_sha256`, `organized_sha256`, `protected_spans`, and `authority_effect: "None"`.

2. **Nested Prompts & Operad Trees (`pfp/domain/operad/prompt.py`, `pfp/domain/operad/graft.py`, `omega_operads`):**
   - `prompt.py` lines 18–33: `PromptColour` enum defines sorts (`RawTextSpan`, `Equation`, `IsolatedVariable`, `SubstitutionStep`, `RationalValue`, `InvariantWitness`, `TargetResult`). Prompt clause typography defines 7 roles: `TASK`, `CONTEXT`, `CONSTRAINT`, `ACCEPTANCE_CRITERIA`, `RESPONSE_CONTRACT`, `TOOL_DECLARATION`, `FEW_SHOT_EXAMPLE`.
   - `prompt.py` lines 35–62: `LeafTextSpan` with `source_offsets: tuple[int, int]` and `verify_against_document(doc_text)`.
   - `prompt.py` lines 107–142: `OperadTreeNode.graft(slot, child)` enforces slot bounds (`IndexError`), boundary colour match (`TypeError`), and absorbs failures via `NullTree`.
   - `graft.py` lines 18–42, 71–104: Canonical `GraftSite` enum (`VERTEX`, `EDGE`, `TREE`) with invariant evaluation checking generator validity, seam types, circularity, and boundary nilpotency ($d_1 \circ d_0 = 0$).
   - `omega_operads/src/immune_guards.rs` lines 19–40: `immune_guarded_substitute` suppresses substitutions when blocked by an immune screen port with `DANGER_GATE_SUPPRESSION`.

3. **Prompt Family DAG (`code/rust/core_prompt_civilization/src/prompt_family.rs`):**
   - Lines 63–77: `Reader` struct with `model`, `router`, `seat_id`, `tier`, `config_digest`, `temperature`, `params_billion`, `open_weights`.
   - Lines 109–116, 248–256: `PromptNode.relation` is strictly `"root" | "contains" | "repaired_from"` (`FAMILY_RELATION`).
   - Lines 261–266: Invariant `(node.relation == "root") != node.parent_id.is_none()` enforces that exactly the root has no parent (`FAMILY_ROOT_PARENT`).
   - Lines 317–319: `FAMILY_ROOT_COUNT` enforces that a family has exactly one root.
   - Lines 283–306: `validate_parent_chain` traverses parent links to detect cycles (`FAMILY_CYCLE`) and dangling parents (`FAMILY_PARENT_MISSING`).
   - Lines 356–385: `FAMILY_FITNESS_CIRCULAR` rejects steps where the evaluating checker oracle is one of the step's own generative readers.

4. **Evolution Tracking & Lamarckian Cochains (`prompt_family.rs`, `lamarckian.rs`, `fitness.rs`):**
   - `prompt_family.rs` lines 398–422: Validates DDC letters (`"E", "R", "C", "I", "Λ", "D", "M", "T"`) and residual transitions (`"Open" | "Closed" | "Exact"`).
   - `prompt_family.rs` lines 455–471: `validate_terminal` requires terminal kind `"Repaired"` to have a final step with `checker_verdict == "ACCEPT"` and `residual_after == "Exact"` (`FAMILY_REPAIRED_UNSUPPORTED`).
   - `lamarckian.rs` lines 23–84, 230–280: `CochainResidualV1` (`phi1`, `gamma2`, `xi`) with exact rational parsing. Verifies monotonic defect reduction ($\Delta \Phi_1 = \text{child\_phi} - \text{parent\_phi} \le 0$, else `RegressionResidualIncrease`), attenuation weighting $w(\alpha, d) = (1/2)^d$ for $1 \le d \le 10$, and byte invariance of protected spans (`ProtectedCoreTampered`).
   - `fitness.rs` lines 204–296: Multi-objective non-dominated sorting over $\mathbb{Q}$ (`CandidateRational`, `compute_pareto_fronts_rational`, `pareto_frontier_rational`) with deterministic lexicographic tiebreak on correctness descending, cost ascending, and ID ascending.

---

## 2. Logic Chain

1. From **Observation 1**, prompt ingestion into P Sieve is governed by `forge_organize_prompt` in `forge.rs`. The 1 MiB hard ceiling and immutable protected spans guarantee that the seed prompt cannot be silently overwritten or modified during downstream prompt evolution.
2. From **Observation 2**, when a prompt contains nested sub-prompts or sub-tasks, flat string representations fail to isolate mutations. The codebase solves this by mapping prompt clauses to planar operad trees (`OperadTreeNode`, `LeafTextSpan`) where grafting (`graft`) enforces slot arity, boundary sort matching, and immune danger gating.
3. From **Observation 3**, evolution produces multiple prompts that relate via structural decomposition (`"contains"`) or repair (`"repaired_from"`). These are structured as a reader-relative arborescence (`PromptFamily`) where root uniqueness, parent pointer acyclicity, and checker anti-circularity are strictly validated.
4. From **Observation 4**, the progression of prompt fitness across repair cycles is grounded in exact rational cochain descent (`LamarckianCochainTrackerV1`), multi-objective Pareto front partitioning (`compute_pareto_fronts_rational`), and terminal gates that refuse `"Repaired"` status without an external `"ACCEPT"` receipt and `"Exact"` residual.
5. Therefore, documenting these four aspects in four dedicated, cross-referenced Markdown files within `documentation/P_sieve/` produces a complete, code-grounded exposition of Prompt Sieve.
6. An automated regex scan was executed across all generated documentation files for forbidden Claim Hygiene phrases (`proves`, `guarantees`, `fundamentally`, `impossible`, `universal`, `flawless`, `perfectly`, `clearly`, `obviously`, `simply`, `merely`, `weaponized`), confirming zero unvetted occurrences.

---

## 3. Caveats

- **Scope Boundary:** This documentation covers the Rust sovereign implementation (`code/rust/core_prompt_civilization`) and Python domain operad facades (`pfp/domain/operad`). It does not cover legacy Python scripts in `education/pfp/python/` that were deleted on 2026-10-10 (`e6537cc3cf`).
- **Operad Crate Separation:** The theoretical 5-tier colored operad hierarchy lives in `anomalon/omega_engine/crates_rs/omega_operad_theory`, whereas workflow and prompt domain applications live in `omega_operads` and `pfp/domain/operad/prompt.py`.
- **Lamarckian Realism:** "Lamarckian" refers strictly to the formal inheritance of verified defect repairs across prompt generations under the declared cochain rules; no biological claim is asserted.

---

## 4. Conclusion

The definitive documentation for Prompt Sieve (P Sieve) has been authored and verified in `documentation/P_sieve/`:
1. `documentation/P_sieve/seed_ingestion.md` (100% code-grounded in `forge.rs`).
2. `documentation/P_sieve/nested_prompts.md` (100% code-grounded in `prompt.py`, `graft.py`, and `omega_operads`).
3. `documentation/P_sieve/family_dag.md` (100% code-grounded in `prompt_family.rs`).
4. `documentation/P_sieve/evolution_tracking.md` (100% code-grounded in `prompt_family.rs`, `lamarckian.rs`, and `fitness.rs`).

All files declare `AuthorityEffect: None`, strictly adhere to Claim Hygiene standards, and provide exact line references, data structure schemas, and invariant failure modes.

---

## 5. Verification Method

To independently verify the deliverables:

1. **Check File Presence:**
   ```powershell
   Get-ChildItem -Path "c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\documentation\P_sieve\"
   ```
   *Expected Output:* `seed_ingestion.md`, `nested_prompts.md`, `family_dag.md`, `evolution_tracking.md`.

2. **Verify Claim Hygiene Rule Compliance:**
   ```powershell
   rg -i -n "\b(proves|guarantees|mathematically verifies|fundamentally|true intelligence|impossible|universal|flawless|perfectly|clearly|obviously|simply|merely|weaponized)\b" documentation/P_sieve/
   ```
   *Expected Output:* Zero matches.

3. **Verify Authority Posture:**
   ```powershell
   rg -n "AuthorityEffect: None" documentation/P_sieve/
   ```
   *Expected Output:* Match in all 4 documentation files.

4. **Verify Rust Invariant Tests:**
   Run the native tests in `core_prompt_civilization` to confirm the invariants cited in the documentation:
   ```powershell
   cargo test --manifest-path code/rust/Cargo.toml -p core_prompt_civilization --lib -- forge lamarckian fitness prompt_family
   ```
   *Expected Output:* `test result: ok. 31 passed; 0 failed; 0 ignored; 0 measured; 85 filtered out`. All unit tests for `forge`, `lamarckian`, `fitness`, and `prompt_family` pass with 0 failures.

# Detailed definition: Pilot Estate Decoupling & Semiotic Carrier Quad-Axis Separation (1)

**AuthorityEffect:** None.

Parent: [Pilot Estate Decoupling & Semiotic Carrier Quad-Axis Separation](../../../../../rules/docs/rl_pilot_estate_decoupling.md). Load for the matching predicate, not every task.

# Rule: Pilot Estate Decoupling & Semiotic Carrier Quad-Axis Separation

**AuthorityEffect:** None.

This rule codifies the semiotic quad-axis separation across Prompt, Packet, Stage, and Mode, as well as pilot estate decoupling, machine-readable matrix schema isolation, and pre-deletion safety audits across the workspace. Full procedural details reside in [`governance-clean-arch`](../../../../governance-clean-arch/SKILL.md) and [`governance-pfp`](../../../../governance-pfp/SKILL.md). For general documentation estate, curriculum storage, and educational submodule layout standards, see [`rl_documentation_estate_and_submodule_layout.md`](../../../../../rules/docs/rl_documentation_estate_and_submodule_layout.md).

---

## 1. Quad-Axis Separation Law: Prompt vs. Packet vs. Stage vs. Mode (`RULE_PROMPT_PACKET_STAGE_MODE_001`)

> **Strict Non-Conflation of Semiotic & Architectural Carriers:**
>
> Autonomous agents operating across the Symbol Game, MSS-N, and PFP pipelines must enforce strict type, authority, and semiotic boundaries across four distinct entities:
>
> 1. **Prompt ($A_{\text{stimulus}}$):** An untrusted, external linguistic stimulus presented to a stochastic oracle or player. Carries `AuthorityEffect: None`. Never constitutes a machine state transition or mathematical proof. Lives in `prompts/` and `rewriting/`.
> 2. **Packet ($P \in \mathcal{P}$):** A content-addressed, machine-verifiable syntactic envelope (RFC 8785) with frozen slots (`schema_id`, `task_data`, `protected_boundary`, `budget`, `candidate_payload`, `witness_data`) or recursive wire term ($\text{Void} \mid \text{Atom} \mid \text{App}$). Evaluated strictly by host verifiers emitting immutable receipts ($\Phi_1, \Gamma_2, \Xi$). Candidate packets must never self-certify. Lives in `packetization/` and `schemas/`.
> 3. **Stage ($S_n$):** A discrete epistemic stratum in the Postnikov obstruction tower characterized by $(s_n, H_n)$, where $s_n \in \mathbb{N}$ tracks active obstructions and $H_n$ is cumulative history. Governed by Two Boxed Laws and Old-Image Retraction ($r_N \circ u_N = \text{id}$). Advancing requires extinguishing an obstruction with an admissible receipt. Lives in `stages/`, `002_s_n/`, `001_genesis/`.
> 4. **Mode ($M_k$):** An operational presentation and syntax restriction profile (Modes 01–20) defining the interaction alphabet and grammar without mutating underlying algebraic carrier sets or state invariants. Lives in `modes/`.

---

## 1.1 Prompt Family Invariants & Proposal Gating (`RULE_PROMPT_FAMILY_AND_PROPOSAL_GATES_001`)

1. **Prompt Agency Prohibition:** Prompts carry `AuthorityEffect: None`. Specifications must never claim that a prompt "forces" behavior or eliminates filler. A prompt *requests* structured output; host parsers and verifiers reject non-conforming proposals.
2. **Prompt Family Invariant Equivalence:** Two prompt presentations belong to the same prompt family if and only if they compile to the same protected task, immutable boundary conditions, and acceptance predicate ($P_i \sim P_j$). Variants that omit rules to test refusal belong to an *associated adversarial-test family*.
3. **Candidate Status of Mined Structure:** Patterns, skills, antiskills, and antibodies proposed by a model during extraction or mining remain candidate material until reviewed or verified by host code.
4. **Derivation Witness Discipline:** Intermediate derivation slots must be designated as externally checkable artifacts (`DERIVATION_WITNESS`), avoiding mentalistic or internal scratchpad framing.
5. **Wire vs. Pretty-Printed AST Purity:** Indented or whitespace-containing structures must be labeled as pretty-printed ASTs. Canonical wire representations are strictly zero-whitespace strings.

---

## 2. Pilot Estate Decoupling & Matrix Data Isolation (`RULE_PILOT_ESTATE_DECOUPLING_001`)

> **Strict Decoupling of Architectural Overviews from Machine Data Registers:**
>
> 1. **Architectural Overview Purity for `README.md`:** Subsystem `README.md` files (such as `adversary/tests/pilots/README.md`) must function strictly as high-level architectural and protocol entrypoints. They must describe paradigm shifts (e.g. empirical pilots replacing dry-run demos), Single Prompt Standard ($P \mapsto P^* \to \{p_i\}$) ingress rules, budget ceilings, catalog semantics (`LLM` vs `NO_LLM`), and directory topology. They must NEVER serve as dumping grounds for per-pilot test counts, branch coverages, mutation lists, individual quiz delivery receipts, or legacy demo tables.
> 2. **Canonical Placement in Machine-Readable Matrix Schemas:** All per-pilot specifications, knobs, prompt parameters, expected outcomes, historical migration registers (`migration_register`), and legacy registries (`legacy_foundational_register`, `legacy_demo_pilots_register`) must reside exclusively in the canonical matrix file (`matrix/max_pilot_matrix.yaml`).
> 3. **Prohibition of Shadow Planning Markdown in Operational/Data Subtrees:** Planning documents belong strictly under the canonical planning office (`product_planning_office/plans/epics/`). Storing redundant planning stubs, summaries, or pointer markdown files (e.g. `matrix/master_pilot_plan.md`) within operational or data subtrees (`pilots/matrix/`) is strictly prohibited. `pilots/matrix/` is reserved exclusively for data definitions, seeds, and schemas (`max_pilot_matrix.yaml`, `pilot_models.yaml`, `seeds.yaml`).
> 4. **Four-Point Pre-Deletion Audit Invariant:** Before removing any candidate obsolete or shadow document, autonomous agents must:
>    - **Check 1 (Zero Inbound References):** Execute repository-wide search to verify zero inbound dependencies or hyperlinks.
>    - **Check 2 (Canonical Home Confirmation):** Confirm that the authoritative intellectual property or plan is preserved in its canonical home.
>    - **Check 3 (Estate Test Precedent):** Verify that clean architecture tests (e.g. `assert not matrix_md.exists()`) align with the deletion.
>    - **Check 4 (Test Solvency):** Run all affected unit test suites to verify 100% pass status post-removal.

## 2026-11-06T19:20:36Z
You are teamwork_worker_m3.
Your working directory is: c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\.agents\teamwork\teamwork_worker_m3\

MANDATORY FIRST STEP: Read the authoritative user request at:
c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\.agents\teamwork\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
You exclusively own and write files in:
`documentation/P_sieve/`
Do NOT write to other folders.

INPUT CONTEXT:
Read the survey reports at:
`c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\.agents\teamwork\teamwork_explorer_survey_1\survey_report.md`
`c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\.agents\teamwork\teamwork_explorer_survey_3\survey_report.md`
and the project plan in `PROJECT.md`.

MISSION:
Produce the definitive, code-grounded documentation for Prompt Sieve (P Sieve) in `documentation/P_sieve/`:
1. `documentation/P_sieve/seed_ingestion.md`:
   - Trace exact code execution when a seed prompt enters the system.
   - `forge_organize_prompt` in `code/rust/core_prompt_civilization/src/forge.rs`.
   - 1 MiB hard ceiling, `original_seed` protected span demarcation.
   - Section formatting (task, constraints, acceptance criteria, response contract).
   - Invariant: `PROTECTED_SPAN_MUTATION_REFUSED` if an edit overlaps any protected span.
2. `documentation/P_sieve/nested_prompts.md`:
   - What happens when a prompt contains prompts (nested prompts, sub-prompts, sub-tasks).
   - Planar Coloured Operad tree representation (`pfp/domain/operad/prompt.py` and `omega_operads`).
   - `LeafTextSpan`, `OperadTreeNode`, 7 prompt colours (`TASK`, `CONTEXT`, `CONSTRAINT`, `ACCEPTANCE_CRITERIA`, `RESPONSE_CONTRACT`, `TOOL_DECLARATION`, `FEW_SHOT_EXAMPLE`).
   - Tree grafting (`graft(parent, index, child)`), byte offset tracking, and span isolation.
3. `documentation/P_sieve/family_dag.md`:
   - How prompts become a prompt family.
   - `PromptFamily` graph schema in `prompt_family.rs`: `PromptNode.relation` (`"root" | "contains" | "repaired_from"`).
   - Invariant: exactly root has `parent_id.is_none()`. Parent pointer traversal and acyclicity enforcement.
   - Reader-relativity: multi-reader evaluation, step checker verification, `FAMILY_FITNESS_CIRCULAR` prohibition.
4. `documentation/P_sieve/evolution_tracking.md`:
   - Managing prompt evolution across repair cycles.
   - `RepairStep` binding DDC letters (`E, R, C, I, Λ, D, M, T`), residual transitions (`Open -> Closed -> Exact`), and fitness deltas.
   - Lamarckian cochain tracking (`lamarckian.rs`) and exact rational Pareto frontiers (`fitness.rs`).
   - Terminal conditions: `terminal.kind == "Repaired"` requiring final ACCEPT verdict and Exact residual.

All files must declare `AuthorityEffect: None` and strictly follow Claim Hygiene rules (no hype verbs, narrow defensible claims).

DELIVERABLE:
Write the documentation files into `documentation/P_sieve/`.
Write a structured handoff report to:
`c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp\.agents\teamwork\teamwork_worker_m3\handoff.md`
Send a completion message back when done.

# Detailed definition: Woland Base Swarm Specialization & Estate Connections (1)

**AuthorityEffect:** None.

Parent: [Woland Base Swarm Specialization & Estate Connections](../../../../../rules/swarms/rl_woland_base_swarm_specialization.md). Load for the matching predicate, not every task.

# Rule: Woland Base Swarm Specialization & Estate Connections

**AuthorityEffect:** None.

Every workload in the repository is a declared narrowing of one base,
`OmegaEngineWolandSwarm` (`omega_engine_woland/use_cases/base_swarm/woland_swarm.py`).
The composition root (`omega_engine_woland.runtime.build_woland_swarm`) is the only place
a Woland swarm is built. Each invariant below names the check that fails when it is broken;
the rules-as-code register records those checks.

---

## 1. One Base, Two Named Specialisations (`RULE_WOLAND_BASE_SWARM_SPECIALIZATION_001`)

1. Ordinary research, cognitive, software, project-management, teamwork and developer
   work uses an approved `SwarmSpecializationV1` profile on the one Woland base.
   Only governing councils and paper review/repair retain named swarm subclasses.
2. Those two subclasses declare `SPECIALIZATION: ClassVar[SwarmSpecializationV1]`.
3. A holder declares `SPECIALIZATION` and takes a `woland: OmegaEngineWolandSwarm` argument
   that its constructor passes to `bind_woland`, which refuses a swarm of another
   specialisation (`SPECIALIZATION_MISMATCH`).
4. Every skill a specialisation requires exists as `.agents/skills/<name>/SKILL.md`.
5. The gate's exemption list is empty and its class census is exact. A new domain
   capability adds a narrowed profile and typed operations, not a new swarm class.

## 2. Specialisations Only Narrow (`RULE_WOLAND_SPECIALIZATION_NARROWING_001`)

1. A `SwarmSpecializationV1` declares Woland ancestry first and its own id last, requires
   `/woland`, licenses a non-empty subset of the closed `PortName` set, runs a stage plan in
   act order I..VII over licensed ports only, ends on a non-empty subset of
   `omega_types::routing::RoutingTerminal`, and carries a budget.
2. `specialize()` refuses `PORT_WIDENING`, `TERMINAL_WIDENING` and `BUDGET_WIDENING`.
3. The Python value object checks structure. The Rust module
   `omega_woland::specialization` is the authority: `build_woland_swarm` runs the
   `woland_support:specialization_validate` host operation, which also checks the
   specialisation against the base, before any swarm is built.
4. The Python and Rust bases, and the bout-status to routing-terminal map, are kept equal by
   a parity test against `woland_support:specialization_base`.
5. A swarm refuses to use a port it does not license (`PORT_NOT_LICENSED`).

## 3. Estate Connections Are Observed, Not Declared (`RULE_WOLAND_ESTATE_PROBE_HONESTY_001`)

1. Each estate port has one adapter under `omega_engine_woland/infrastructure/estates/`.
   Those modules are the only Woland modules that import the estates they connect.
2. A probe performs one round trip inside a scratch root and reports `connected=True` only
   for an effect it read back from the estate's own store; `effect_digest` is the SHA-256 of
   those bytes. Probes never write into the live stores.
3. A port that does not reach its estate is reported disconnected with the reason (for
   example `PYTHON_EVALUATOR`, `PYTHON_FALLBACK`, `NO_VERIFIED_RUNTIME`). A Null adapter is
   always disconnected and is used only when a caller names the port.
4. A failing estate call during a bout is kept on the result as a typed residual. It never
   changes the bout outcome and is never skipped silently.
5. Fixture bouts are not composted into the pharmacy; live-bout blockers enter OEEIS as
   `CANDIDATE` antibodies only.

## 4. Models Only Through Symbol Game (`RULE_WOLAND_LLM_MEDIATION_001`)

1. Woland reaches a model only through a Symbol Game seat transport that declares
   `omega.symbol_game.protocol.v2` and is defined in `omega_engine_pfp`. Any other
   transport is refused with `LLM_PROTOCOL_UNMEDIATED` before a runtime is built.
2. Woland production code imports no network provider module outside a shrink-only
   allowlist, and Symbol Game production code does not import Woland.

## 5. Woland Orchestration Mode & Model Tier Discipline (`RULE_WOLAND_ORCHESTRATOR_DISCIPLINE_001`)

1. **Default Native Orchestrator Mode:** Woland Swarms default to `orchestrator_mode: "NATIVE"` in `wolands_retinue.yaml`. In NATIVE mode, the host IDE or CLI environment (Claude Code, Antigravity, Codex, Grok) acts as the common orchestrator, managing context, subagent dispatch, witness custody, and fail-closed gate evaluation.
2. **Explicit Routed Binding:** The canonical packaged roster remains `NATIVE`. An explicitly selected OpenRouter executor binds the same full plan to a durable run-wide policy of at most $0.05; it cannot replace the default with an implicit paid route. Estimated admission is not a vendor-enforced maximum bill.
3. **Closed Model Tier Taxonomy:** Every character and temporary skill worker is assigned to one or more declared tiers:
   - `tier_frontier`: Deep reasoning & synthesis (e.g. Claude 3.7 Sonnet, o1, Gemini 2.5 Pro).
   - `tier_reasoning`: Proof search & algorithmic chain-of-thought (e.g. o3-mini, DeepSeek-R1).
   - `tier_standard`: High-throughput structured critique & generation (e.g. Claude 3.5 Haiku, Gemini 2.5 Flash, GPT-4o-mini).
   - `tier_fast`: Low-latency tactical fuzzing and context transport (e.g. Gemini 2.5 Flash Lite, DeepSeek Chat).
   - `no_llm`: Deterministic, zero-LLM compiled syntax filters and linters (e.g. Hella).
4. **22-Character Retinue-to-Gate Totality:** Every character in Woland's retinue has a strict 1-to-1 bijection with a primary verification gate in `omega_engine_education/.../gates/` (`01_hella` through `22_ratslayer`). Composite pseudo-characters (such as `jeremy_and_polina`) are retired; each character retains sovereign sketch and gate files.
5. **Actual Workflow Coverage:** New canonical teamwork runs use `omega.woland.teamwork.v4`, a source-bound closed 22-role roster under an optional declared schedule (`retinue_schedules.yaml`), and deterministic Hella. A schedule may skip or blind seats but never Hella, Azazello, Jeremy, Koroviev, Woland or Bezdomny; every skipped seat is reported with its reason, not as missing. All other role contributions replay the actual PFP reply bytes before consumption. Callback mode cannot substitute unchecked prose. Missing, blocked or unexecuted roles remain visible; role coverage never proves independent workers or task acceptance. Historical v1/v2/v3 bytes remain replayable under their original semantics. New runs require an explicit host-selected independent acceptance binding before model work, a continuing durable episode ledger admitting at most ten evaluations including failures, reserved Bezdomny learning on partial runs, and mandatory native DDC sealing/readback plus checked PFP procedure consumption. Stored C/R/I/T records do not confer task acceptance or an E certificate. Native checkpoints execute the 35 registered predicates with actual process receipts, candidate/source/specification bindings and continuing diagnostic attempt history. Missing witnesses remain residuals; diagnostic attempts are not admitted transitions. Strict policy stops on non-PASS without resetting work or skipping learning. Matching rebound hashes alone never proves receipt validity. Scoped controls live in `test_teamwork_retinue_adversarial.py`, `test_teamwork_factory.py`, `test_teamwork.py` and `test_teamwork_schedule.py` under `omega_engine_woland/tests/`.

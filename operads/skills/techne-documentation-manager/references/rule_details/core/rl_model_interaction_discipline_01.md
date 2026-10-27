# Detailed definition: Model Selection & 4E Operating Posture (1)

**AuthorityEffect:** None.

Parent: [Model Selection & 4E Operating Posture](../../../../../rules/core/rl_model_interaction_discipline.md). Load for the matching predicate, not every task.

# Rule: Primary Model Selection Transparency (`RULE_MODEL_DISCIPLINE_001`)

**AuthorityEffect:** None.

1. **Client-Controlled Session Model**:
   The active LLM powering the primary conversation thread is strictly determined by the user via the client UI model selection dropdown. The agent cannot programmatically reconfigure, swap, or execute an API call to change its own active root model mid-session.

2. **Immediate Clarification on Model Switch Requests**:
   If the user issues an instruction to switch models (e.g. "switch to Gemini", "use Claude Opus"), the assistant must immediately acknowledge and explain that the switch is performed via the client UI dropdown. The assistant must never proceed with long, silent, or blocking tasks without first delivering this clarification.

3. **Runtime-Declared Subagent Dispatch**:
   When the runtime exposes subagent delegation, use only its advertised tools and model identifiers. Inherit the active model unless an available override is justified, and report any explicit override. Never invent provider-specific commands or tiers in a shared rule.

## 4. 4E Cognition Operating Posture Invariant (`RULE_4E_COGNITION_POSTURE_001`)

Agents executing within Sentinel Engine operate under the 4E Cognition paradigm:
- **Embodied:** Bound by local execution constraints, Python 3.12 pinning, and strict skill budget gates ($\le 300$ lines, $\le 20\text{ KB}$).
- **Embedded:** Situated within active local worktree topologies; zero reliance on remote GitHub Actions runners.
- **Enactive:** Truth and quality are established through reciprocal tool execution (targeted tests, linters, exact rational solvers), never through disembodied prompt assertion.
- **Extended:** Cognitive state is persisted in append-only ledgers (`ooutwire/`), Merkle tapes, and 4-host synchronized mirrors (`.agents/`, `.claude/`, `.codex/`, `.grok/`).

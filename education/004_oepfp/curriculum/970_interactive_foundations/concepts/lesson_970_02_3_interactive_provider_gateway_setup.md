# Lesson 970.02 -- 3. Interactive Provider & Gateway Setup

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_02_3_interactive_provider_gateway_setup.ipynb](../notebooks/lesson_970_02_3_interactive_provider_gateway_setup.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 3. Interactive Provider & Gateway Setup

Use the interactive widget below to configure your LLM provider.
- **Offline Deterministic Mock**: Runs 100% locally with zero API keys or network access, replaying Paper 032's audited benchmark receipts.
- **OpenRouter API**: Connects to OpenRouter using your `OPENROUTER_API_KEY`.
- **Local Endpoint**: Connects to an OpenAI-compatible local server (Ollama, vLLM, LocalAI) at `http://localhost:11434/v1`.

## 4. Master Curriculum Map

| NB | Title | Focus | Primary Verifier |
|---|---|---|---|
| **00** | How to Read & Play | Orientation, Wager, Provider Setup | `llm_client.py` |
| **01** | MSS-0 to S(N) Relational Foundations | Void, carrier sets, diagonal excision, irreflexivity | `governor_adapter.py` |
| **02** | Arity Filtration & ARS Rewriting | Redex matching, substitution modulo group action | `arity_rewrite_engine.py` |
| **03** | Three-Layer Sovereignty | Train time (L1), Decode time (L2), Verify time (L3) | `llm_client.py` |
| **04** | The Three Firewalls | FW-CARRIER, FW-MOVE, FW-REPLAY fail-closed | `packet_firewall_host.py` |
| **05** | Discrete L1 Coboundary Projection | Simplicial cochains, Phi_1 primary obstruction | `l1_symbol_game_governor.py` |
| **06** | Total Unimodularity & LP Duality | Incidence matrix TUM, rational dual certificates | `scaling_benchmark_v20.py` |
| **07** | Constructive HoTT Identity Paths | Identity types, Primitive Difference setoid | `hott_symbol_game.py` |
| **08** | L1 Sparsity & Fluff Excision | Conversational fluff excision, unpriced density | `l1_sparsity_bullshit_benchmark.py` |
| **09** | Transformer Mechanics | Attention concentration (3.14x), KV norm invariance | `attention_entropy_kv_norm_benchmark.py` |
| **10** | Interactive Lean 4 Governor | Topology-50 benchmark, 46% retractions, 100% solved | `interactive_lean4_governor.py` |
| **11** | Build Your Own Agent | Capstone workshop: live LLM + Layer 3 Governor | `governor_adapter.py` |

## 5. Student Exercises

### Exercise 00.1: Claim Verification
Why does the Symbol Game require that an assertion like `ASSERT e1 -> residue_0` cite an explicit evidence source or parent hash?

<details>
<summary><b>Click to reveal solution</b></summary>
Because without an explicit evidence citation or parent hash, the rewrite is unpriced. Under the Woland Swarm operational axiom ("An unpriced rewrite is a smuggled axiom"), unpriced steps allow models to silently smuggle unwarranted mathematical assumptions into a derivation.
</details>

## 6. Anchors

- **Paper 032 Sections**: §1, §10
- **Ledger IDs**: `PO032-C01`, `PO032-C02`
- **Code**: `notebook_lib/llm_client.py`
- **Audit Receipt**: `papers/032.../code/l1_sparsity_benchmark_receipt.json`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.

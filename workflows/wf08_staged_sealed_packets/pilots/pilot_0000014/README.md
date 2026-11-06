# pilot_0000014 — Graph Repair (Rung 4)

**AuthorityEffect:** None.  
**Governing Standard:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).  
**Task Family:** `graph_repair`  
**Host Checker:** `PFP-03-GRAPH-REPAIR`  
**Structure Delta Metric:** `rank_change`  

---

## 1. Description & Protocol Execution
This pilot implements a hermetic, oracle-grounded evaluation instance for `graph_repair` under difficulty rung `4`. Ingress stimuli are compiled into typed `$P^*$ envelopes via`p_star_builder.py` according to SPK-001. Model outputs are strictly sanitized by `pilot_response_sanitizer.py` to preserve verbatim byte custody while recording non-schema commentary to `residual_text_ledger.json`.

Host gate verification evaluates candidate proposals against sovereign mathematical truth, distinguishing exact solutions from false certainty and malformed inputs.

---

## 2. Claim Hygiene Envelope

### 2.1 What This Pilot Supports
- Supports that the host evaluation harness deterministically computes ground truth for `graph_repair` and enforces the `PFP-03-GRAPH-REPAIR` gate without data leakage.
- Supports that `$P \mapsto P^*$ assembly under SPK-001 constructs a valid`PromptPacketV0_1` envelope preserving root lineage and containment cardinality.
- Supports that `pilot_response_sanitizer.py` strips markdown code fences, enforces duplicate key rejection, and logs structure leakage debt.
- Supports that at least four distinct compiled semantic mutants are caught and killed by the test oracle.

### 2.2 What This Pilot Does NOT Support
- Does **NOT** support any claim that LLMs universally or reliably solve `graph_repair` problems. Offline fixture dry runs verify software plumbing and host gates only; they provide zero empirical evidence regarding model capability or behavior.
- Does **NOT** authorize live provider dispatch without explicit budget allocation and authentic cryptographic receipts.

### 2.3 Narrowest Defensible Claim
- Under the declared assumptions, the host verification suite deterministically distinguishes valid mathematical solutions from invalid, malformed, or ambiguous proposals on the scoped `graph_repair` benchmark, enforces zero-spend boundaries during offline execution, and catches 100% of tested mutant discrepancies.

### 2.4 Next Test Needed
- Deploy live model trial through `live_gateway` under strictly preflighted budget constraints (`budget <= $0.001`) with authentic provider receipts to record empirical proposal fidelity across model classes.

## 3. Mode trial
Local execution of `mode_15` against `omega_engine_education/pfp/infrastructure/yaml/modes/mode_15_interactive_tui_repl_board/contract.yaml`.
The packet is the four-object seal in `packet.yaml`. `pilot_0000000/prompt_template.yaml` is a generated empty shell and is not copied into this pilot.
`results/execution.yaml` records 3 variations. Provider calls: 0. Spend: 0.
Winning condition executed: `false`.
Limit: No terminal renderer was started. The live-board winning condition was not executed.

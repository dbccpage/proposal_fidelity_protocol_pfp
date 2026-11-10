# TASK.md: Challenge C005 (Hosted Decoding Controls Bake-off)

## 1. Objective
Compare the effectiveness, parseability, host-verified accuracy, and cost per verified success of four decoding controls:
1. `none`: Unconstrained generation.
2. `logit_bias`: Bounded token bias steering (-100 on prose starters, +5 on digits, signs, and structural JSON tokens).
3. `json_schema`: Strict JSON schema structured outputs (`response_format={"type": "json_schema", ...}`).
4. `gbnf`: Formal context-free grammar constraint admitting only admissible carrier strings.

Evaluated across open weights and hosted frontier models (>70B, e.g. Llama-3.1-405B, Qwen2.5-72B, Claude 3.5 Sonnet, Gemini 1.5 Pro) under strict budget control ($0.10 ceiling per arm).

## 2. Tasks
1. **Consistency Verdict with Potential Certificate (C001 Family):**
   - Output must be strict JSON:
     ```json
     {
       "verdict": "CONSISTENT",
       "certificate": {"n0": "0", "n1": "2", "n2": "-3"}
     }
     ```
   - For `INCONSISTENT`, `"verdict": "INCONSISTENT"` and certificate must be `{}`.
   - Exact host check: $\pi(v) - \pi(u) = c_{uv}$ for all directed edges.

2. **k-Integer Cycle Repair (C004 Family):**
   - Output must be strict JSON:
     ```json
     {
       "status": "SOLVED",
       "repaired": ["1", "3", "-4"],
       "weighted_l1": "1"
     }
     ```
   - Exact host check: $\sum c'_i = 0$, exact weighted L1 calculation $\sum w_i |c_i - c'_i| = \text{host\_cost}$, and optimality check $\text{host\_cost} = |s| \cdot \min_i w_i$.

## 3. Protocol Rules & Operands
- **`operand probe_before_trust.v1`**: 10 probe requests must be tested on the route first. If any probe fails to honor the active control, the arm is downgraded and reported as `UNCONSTRAINED`.
- **`operand schema_is_shape_only.v1`**: A schema-valid response is checked unconditionally for exact mathematical correctness. Passing the schema is not correctness.
- **Budget Ceiling**: Strictly $\le \$0.10$ per arm. Pre-call budget check fails closed on unknown or missing costs.

## Current execution route

`GovernedClient` is retained for explicit `mock_mode=True` fixture checks only.
Without that flag it raises `PFP_LIVE_ROUTE_REQUIRED` before provider construction,
regardless of credentials. Fixture costs and token counts are synthetic and do
not measure paid inference.

Use the canonical C005 PFP adapter; inspect
`python -m omega_engine_education.pilots.challenge_suite --help` for its current
live and checking commands. General Woland challenge composition remains open.
Its independent
mathematical checker remains authoritative for the finite answer. Hosted decoding
controls are separate research conditions: they require support in the shared
PFP route and actual honored-control probes. An ordinary schema-checked PFP
answer does not establish that `logit_bias`, JSON-schema decoding or GBNF was
honored by a provider.

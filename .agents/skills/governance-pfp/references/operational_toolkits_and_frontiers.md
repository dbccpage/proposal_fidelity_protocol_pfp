# Operational Toolkits & Token Frontier

AuthorityEffect: None.

## 1. Carrier Projection Specification

- **UTF-8 Strict Decoding:** Reject non-canonical UTF-8 sequences and byte-order marks (`\xef\xbb\xbf`).
- **Interval Containment & Normalization:** Invariant validation of Unicode NFC vs NFKC normalization boundaries.

## 2. Prompt Contract & Linter

- **Soundness Classes:** Partition prompts into deterministic contract classes (Syntactic, Semantic, Closed-Form).
- **Examiner Trap Avoidance:** Strict prohibition against unconstrained conversational preambles and sycophantic praise. Enforces direct RFC 8785 JSON or packet input.

## 3. Receipt Replay & Terminal Ladder

Four-tier execution outcome ladder:

| Outcome | Exit | Meaning | Action |
| :--- | :--- | :--- | :--- |
| `DeclaredUnverified` | 0 | Candidate passed verification gates | Proceed; candidate is unverified, never GlobalGreen |
| `TypedRefusal` | 0 | Gate refused candidate cleanly | Read run root for refusal reason; do not retry unchanged |
| `StageRefused` | 2 | Run incomplete | Inspect trace, fix input, re-run into fresh output directory |
| `Incomplete` | 1 | Unhandled execution fault | Audit log trace |

## 4. Mutation Testing & Verification Gaps

Four-tier mutation testing model (M1–M4):
- **M1 (Premature Stage Mutation):** Verify rejection of opcodes before activation level.
- **M2 (Opcode Collision Mutation):** Verify detection of overlapping opcode bases.
- **M3 (Repeated Generator ID Mutation):** Verify detection of duplicate generator instances.
- **M4 (Domain Near-Miss Mutation):** Verify rejection of perturbed metric or cochain instances.

## 5. Token Frontier & Expected Future Grammaticality (EFG)

- **Incremental Parsing:** Continuous token-by-token state tracking without reparsing full prefixes.
- **Byte-Level Token Custody:** Direct custody of raw byte streams for token-to-symbol boundary verification.
- **EFG Licensing Oracles:** Ahead-of-time filtering of vocabularies ensuring candidate tokens can be completed to valid Symbol Game expressions.
- **Cycle Trap Avoidance:** Falsification filters detecting infinite recursive loops in prospective grammars.

## 6. 9-Dot Gauge Break Dialectic

When local cycle deadlocks occur ($\Phi_1 > 0$ under locked gauge), Act IV executes a 9-Dot Gauge Break:
1. **Nocebo Plunge:** Relentlessly expose worst-case failure modes and unexamined carrier assumptions.
2. **Placebo Rebound:** Invert polarity into high-agency constructive confidence, channeling failure analysis into an orthogonal solution.
3. **Terminal Reality Gate:** Monotonic descent to exact certificates ($\Phi_1 = 0, \Gamma_2 = 0$) under Adversary tribunal supervision.

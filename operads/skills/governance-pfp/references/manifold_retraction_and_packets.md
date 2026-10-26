# Manifold Retraction & Packet Envelopes

AuthorityEffect: None.

## 1. Discrete Manifold Retraction Protocol

The Symbol Game is a deterministic control spine where candidate algebraic and discrete proposals are retracted onto admissible invariant manifolds through multi-agent cognitive debate.

### Core Terminology

- **Retraction Turn:** A single discrete step in the symbol game manifold retraction process that evaluates candidates and computes strict descent metrics. Avoid terms like "chat iteration" or "retry cycle".
- **Obstruction Score:** A three-tuple $(\Gamma_2, \Phi_1, \text{defect\_count})$ measuring topological curvature, boundary defect L1 norm, and active defect count.
- **Strict Descent:** The mathematical invariant that successive retraction turns monotonically decrease or maintain obstruction norms without boundary leakage:
  $$\Delta \text{Obstruction} \le 0$$
- **Elimination Receipt:** A verifiable certificate proving that an identified obstruction or defect was contractively resolved or eliminated under declared regime constraints.

## 2. Packet Envelopes & RFC 8785 Serialization

All wire transport in the Symbol Game uses immutable, content-addressed cryptographic envelopes:

- **`PacketEnvelopeV2`:** Top-level cryptographic envelope carrying typed payloads, timestamp, producer signature, and digest.
- **`PromptArtifactV1`:** Content-addressed prompt specification packaging objective, carrier graph, and constraints.
- **`CandidateArtifactV1`:** Sealed candidate proposal carrying cochain adjustments, vertex potential shifts, or code diffs.

### Serialization Invariants

1. **RFC 8785 Canonical JSON:** All dictionary keys sorted alphabetically at all depths; float exponential notation prohibited; integers rendered without trailing decimals.
2. **Deterministic Digests:** Blake3 and SHA-256 digests computed over raw UTF-8 canonical byte streams.
3. **Wire Syntax Rules:**
   - Delimiters `<>` strictly balanced.
   - Sibling elements are self-delimiting; no commas or extra whitespace.
   - Atom words restricted strictly to $\Sigma_{36} = [0-9a-z]+$; no underscores, dashes, or punctuation.
   - Base distinction `<>` classified as `Diff`, never an `Atom`.

## 3. Output Storage Layout

Every Symbol Game run writes 9 canonical files into `_intelligence/symbol_game/runs/<task_id>/`:

| File | Content |
| :--- | :--- |
| `prompt_packet.json` | Sealed `PacketEnvelopeV2` (Prompt envelope) |
| `prompt_artifact.json` | Content-addressed `PromptArtifactV1` |
| `response_packet.json` | Sealed `CandidateArtifactV1` (Response candidate) |
| `candidate_artifact.json` | Content-bound Candidate Turn Artifact |
| `turn_outcome.json` | Step purity, L1 obstruction, and verdict (`SELECT` \| `HOLD`) |
| `receipt.json` | Canonical execution receipt with `AuthorityEffect: None` |
| `trace.jsonl` | Step-by-step trace log |
| `dda_actions.jsonl` | Discrete deformation actions |
| `summary.md` | Markdown summary rendered with claim hygiene |

## 4. Zero Data-Loss & Cemetery DAG Mining

1. **Zero Data-Loss Invariant:** No candidate turn, LLM prompt, or model response is ever discarded. Even when a candidate proposal fails strict descent or triggers an immediate typed refusal ($M$), the complete raw token stream, prompt parameters, cochain projection, and evaluation delta are permanently committed to the Symbol Game JSON-L DAG (`_intelligence/symbol_game/` and `CemeterySink`).
2. **Retrospective Hallucination Mining:** Periodically traverses dead-end branches in the Cemetery DAG to identify out-of-distribution framing breaks, topological shortcuts, and novel conjectures without contaminating active execution state tapes. Mined insights are committed to hypothesis ledgers under `_intelligence/hypotheses/`.

## 5. Railway-Oriented Programming (ROP) Execution Track

All domain evaluation pipelines propagate monadic `Result[T, E]` containers (`Success[T]` / `Failure[E]`) with short-circuiting composition (`bind`, `map`, `map_err`), eliminating untyped exception bubbles in core retraction loops.

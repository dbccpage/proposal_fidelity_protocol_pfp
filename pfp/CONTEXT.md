# Symbol Game Bounded Context

A deterministic sparse manifold retraction engine that coordinates multi-agent cognitive debate, verifies discrete coboundary descent, and produces cryptographically verifiable, zero-authority execution receipts.

## Language

### Core Retraction & Topology

**Symbol Game**:
A deterministic control spine where candidate algebraic and discrete proposals are retracted onto admissible invariant manifolds through multi-agent cognitive debate.
_Avoid_: State machine, conversational chat loop, pipeline runner

**Retraction Turn**:
A single discrete step in the symbol game manifold retraction process that evaluates candidates and computes strict descent metrics.
_Avoid_: Chat iteration, retry cycle, turn prompt

**Obstruction Score**:
A three-tuple measuring topological and cochain resistance: Gamma-2 curvature, Phi-1 boundary defect norm, and active defect count.
_Avoid_: Error rate, loss metric, score penalty

**Strict Descent**:
The mathematical guarantee that successive retraction turns monotonically decrease or maintain obstruction norms without boundary leakage.
_Avoid_: Improvement, progress, heuristic optimization

### Artifacts & Envelopes

**Packet Envelope**:
An immutable, content-addressed envelope carrying structured domain payloads with the domain canonical encoder and SHA-256 digests.
_Avoid_: Message payload, wire DTO, wrapper dict

**Elimination Receipt**:
A verifiable certificate proving that an identified obstruction or defect was contractively resolved or eliminated under declared regime constraints.
_Avoid_: Success response, confirmation token, status receipt

**Candidate Artifact**:
A provisional proposal, prompt compilation, or code patch submitted to the symbol game for invariant verification and debate.
_Avoid_: Draft payload, tentative suggestion, unverified input

### Evaluation & Codecs

**Proposal Evaluator**:
A pure domain evaluator that scores candidate proposals for contractive mass drops, applies registered kill conditions, and enforces zero authority.
_Avoid_: Validator service, checker middleware, guard function

**Packet Codec**:
The value object kernel responsible for domain canonical serialization, SHA-256 digest computation, and tamper verification.
_Avoid_: Serializer helper, JSON util, parser class

### Railway-Oriented Programming & Events

**Result Track (`Result[T, E]`)**:
Monadic computation track partitioning execution into pure `Success[T]` and `Failure[E]` paths with short-circuiting composability (`bind`, `map`, `map_err`).
_Avoid_: Try/except branching, sentinel None return, exit error code

**Domain Event**:
An immutable, past-tense occurrence within the bounded context (`TurnExecutedEvent`, `ProposalEvaluatedEvent`, `RunRootCreatedEvent`) published to in-process subscribers and transactional outboxes.
_Avoid_: Webhook payload, message queue packet, async notification callback

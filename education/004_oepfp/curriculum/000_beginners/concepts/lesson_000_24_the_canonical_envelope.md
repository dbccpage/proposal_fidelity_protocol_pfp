# Lesson 000.24 -- The Canonical Envelope: Local JSON, SHA-256, and the Trust Boundary

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_24_the_canonical_envelope.ipynb](../notebooks/lesson_000_24_the_canonical_envelope.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Tamper-Evident Packaging of Discrete State
- 2. The 4-Field PacketEnvelope Kernel
- 3. Local JSON Serialization and SHA-256 Receipts
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reserved for a cited checked-in specification; this lesson's illustrative class is not the production packet schema.
> - **[Executed]**: a finite code-check label, not a learner outcome or general conformance proof; a run needs its own evidence.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Tamper-Evident Packaging of Discrete State

[Declared] When two players or distributed agents play the Symbol Game, moves and verdicts cannot be exchanged as informal text. If an untrusted proposer claims `host_verdict = 'ADMITTED'`, how does the ecosystem detect forgery?

This lesson illustrates a **Canonical Envelope**: a frozen four-field record serialized by a local Python JSON helper and committed via SHA-256. It is not the complete production packet schema or a general standards-conformance example.

## 2. The 4-Field PacketEnvelope Kernel

[Declared] The worked example uses this illustrative four-field immutable record:
```python
@dataclass(frozen=True)
class PacketEnvelope:
    carrier: str         # e.g., 'MSS-1', 'Grammar000'
    input_state: str     # e.g., '<0>', 'c=(2, -1, 0)'
    candidate_move: str  # e.g., 'op<<0><1>>', 'phi=(0, -1, 0)'
    host_verdict: str    # e.g., 'ADMITTED', 'REFUSED_DEFECT_INCREASE'
```

1. **`carrier`**: Declares the formal carrier type or stage level under evaluation.
2. **`input_state`**: The verified prior state of the board or cochain before the move.
3. **`candidate_move`**: The exact transition proposed by the external agent.
4. **`host_verdict`**: The referee's binding evaluation (`ADMITTED` or `REFUSED_...`).

## 3. Envelope Canonicalization and Digest Consistency vs. Host Authority

[Declared] The helper uses this **local four-string-field Python JSON profile**, not a general standards-conformance implementation:
1. **Sorted Keys:** Python `sort_keys=True` sorts these four ASCII field names (`'carrier'`, `'candidate_move'`, `'host_verdict'`, `'input_state'`). This does not test general Unicode-key or cross-language ordering.
2. **Whitespace Stripping:** No whitespace outside of string literals (`separators=(',', ':')`).
3. **String-Field Fixture:** The four illustrated fields contain strings. The helper uses `ensure_ascii=False`; numeric serialization is not exercised by this example.

The envelope's cryptographic digest is computed as:
$$\text{receipt\_hash} = \text{SHA-256}(\text{canonical\_envelope\_json}(\text{envelope})).$$

### Digest Consistency vs. Host Authorization (The Forgery Warning)

Crucially, **a matching SHA-256 digest does not establish host authority on its own.**
If a verifier only tests `compute_digest(env) == declared_receipt`, an adversary can forge an invalid state transition, write `host_verdict = 'ADMITTED'`, and freshly recompute the digest. That forged pair will match!

Establishing genuine host origin requires two orthogonal verification fences:
1. **Schema and Domain Validation:** The envelope must be parsed and verified against the closed host grammar and vocabulary. Fields must be strings, carrier must match a registered carrier (e.g. `'MSS-1'`), and verdict must belong to the closed referee vocabulary (`'ADMITTED'`, `'REFUSED_...'`).
2. **Trusted Commitment Verification:** The computed digest must be checked against an independently authenticated *trusted host commitment* (such as an append-only signed host ledger, cryptographic signature, or pre-established receipt registry). Formatting, digest agreement and authentication are separate checks. This worked example constructs its commitment locally and assumes the trust relationship; it does not authenticate a host, verify a signature or authorize a move.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If an external proposer submits a `PacketEnvelope` whose calculated SHA-256 digest matches its accompanying receipt string, why is that check alone insufficient to certify that the Host referee admitted the move?

- **A:** Because SHA-256 has too many hash collisions.
- **B:** Because anyone can alter the fields of an untrusted envelope (such as writing `host_verdict = 'ADMITTED'`) and freshly recompute its SHA-256 digest; authorization requires checking schema validity and matching against an independently authenticated, trusted host commitment.
- **C:** Because JSON strings cannot be hashed.

*(Correct answer: **B**. Cryptographic digest consistency only proves data integrity against a known commitment; it does not prove origin or authority without a trusted host commitment and schema validation.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** You put a secret drawing into an envelope and stamp it with a wax seal. If someone brings in a different envelope with their own new seal, why do you check your list of registered seals? *(Answer: Because anyone can buy their own wax! Only the registered seal proves it came from the trusted sender!)*
2. **Exercise 2 (Age 15):** In Python, construct a `PacketEnvelope` and demonstrate that a forged envelope with freshly recomputed digest is rejected when verified against the trusted genuine commitment.
3. **Exercise 3 (Age 500):** Implement `verify_envelope_against_commitment` with schema validation enforcing string types, valid carrier, and closed verdict vocabulary.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Set

ALLOWED_CARRIERS = {"MSS-1", "MSS-000-CAPSTONE"}
ALLOWED_VERDICTS = {
    "ADMITTED",
    "REFUSED_DEFECT_INCREASE",
    "REFUSED_SYNTAX",
    "REFUSED_DOMAIN",
    "REFUSED_CARRIER",
    "REFUSED_COHOMOLOGY_BREACH",
}

@dataclass(frozen=True)
class PacketEnvelope:
    carrier: str
    input_state: str
    candidate_move: str
    host_verdict: str

def canonical_envelope_json(envelope: PacketEnvelope) -> str:
    """Local sorted-compact Python JSON for the illustrated string-field record."""
    data = asdict(envelope)
    # The fixture's field names are ASCII; check existing key/value string types
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise TypeError(f"Envelope field {k} must have string value, got {type(v)}")
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def compute_digest(envelope: PacketEnvelope) -> str:
    serialized = canonical_envelope_json(envelope)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def validate_envelope_schema(envelope: PacketEnvelope) -> None:
    if not isinstance(envelope, PacketEnvelope):
        raise TypeError("Object is not a PacketEnvelope")
    for f in ("carrier", "input_state", "candidate_move", "host_verdict"):
        val = getattr(envelope, f, None)
        if not isinstance(val, str):
            raise TypeError(f"Field '{f}' must be str, got {type(val)}")
    if envelope.carrier not in ALLOWED_CARRIERS:
        raise ValueError(f"Unrecognized carrier '{envelope.carrier}'")
    if envelope.host_verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"Unrecognized host_verdict '{envelope.host_verdict}'")

def verify_envelope_against_commitment(envelope: PacketEnvelope, trusted_commitment: str) -> bool:
    """
    Checks the illustrated fields and digest equality with the supplied
    commitment. Caller authentication is not performed here.
    """
    try:
        validate_envelope_schema(envelope)
    except (TypeError, ValueError):
        return False
    return compute_digest(envelope) == trusted_commitment

# 1. Locally constructed genuine fixture, not a live host receipt
env_genuine = PacketEnvelope(
    carrier='MSS-1',
    input_state='c=(2, -1, 0)',
    candidate_move='phi=(0, -1, 0)',
    host_verdict='ADMITTED'
)
# Local fixture commitment; authentication is assumed, not demonstrated:
trusted_host_commitment = compute_digest(env_genuine)

# 2. Genuine envelope passes verification against trusted commitment
assert verify_envelope_against_commitment(env_genuine, trusted_host_commitment)

# 3. Forged envelope: adversary attempts move (2, 2, 2) and asserts ADMITTED
forged_env = PacketEnvelope(
    carrier='MSS-1',
    input_state='c=(2, -1, 0)',
    candidate_move='c=(2, 2, 2)',
    host_verdict='ADMITTED'  # False claim!
)
forged_fresh_digest = compute_digest(forged_env)

# Forged envelope fails when checked against trusted host commitment!
assert not verify_envelope_against_commitment(forged_env, trusted_host_commitment)

# 4. Schema validation prevents forged envelopes with invalid verdicts or carriers
invalid_verdict_env = PacketEnvelope(
    carrier='MSS-1',
    input_state='c=(2, -1, 0)',
    candidate_move='c=(2, 2, 2)',
    host_verdict='WEAPONIZED_BYPASS'  # Invalid vocabulary
)
assert not verify_envelope_against_commitment(invalid_verdict_env, compute_digest(invalid_verdict_env))

print("Local fixture schema and commitment-comparison checks passed.")
```
</details>

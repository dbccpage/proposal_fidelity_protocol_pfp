---
documentation_contract: symbol-game-documentation/v1
title: "Data Type Specification: Canonical Serialization and Domain Digest"
kind: reference
audience:
  - engineers
  - coding-agents
  - researchers
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - omega_engine_pfp/domain/packet_codec.py
  - omega_engine_pfp/domain/shared_kernel/canonical.py
  - omega_engine/crates_rs/omega_symbol_game_runtime/src/canonical.rs
last_verified: 2026-10-22
verification_scope: PacketCodec.seal and canonical marker read in source; the integer-2 framing hashes recomputed with hashlib; jcs.rs header read as an RFC 8785 module; no cross-language execution. Pin 305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d. jcs.rs was dirty in the worktree; the RFC 8785 header comment was present in the file as read.
---

# 01. Data Type Specification: Domain Digest & Canonical Serialization

**Status:** Canonical Data Type Reference  
**AuthorityEffect:** `None` (Defines byte-level encoding, length-delimited framing, and cryptographic digest calculation)  
**Governing Standard:** Landau Theoretical Minimum & Claim Hygiene Rule  

---

## 1. Overview & Role in PFP

In the **Proposal Fidelity Protocol (PFP)**, digests bind proposals and receipts to specific encoded content. First identify the producer: different producers use different framing. A hexadecimal digest alone does not identify its encoding profile.

A SHA-256 **Digest** is a deterministic 64-character lowercase hexadecimal string. It may hash bare canonical bytes or a domain-framed stream, according to the named producer:

$$\operatorname{Digest} \in \mathtt{[a\text{-}f0\text{-}9]}^{64}$$

> **Claim discipline:** A matching digest supports integrity relative to the expected digest and the specified encoding. It does not establish the truth of a mathematical claim. NFC-normalized packet hashes identify normalized content; they do not preserve distinctions between every pair of original source byte strings.

| Producer | Bytes hashed | Meaning |
| --- | --- | --- |
| [PacketCodec](../../../../omega_engine_pfp/domain/packet_codec.py) | Bare SHA-256 of NFC-normalized, tagged canonical bytes | `payload_sha256` binds the payload; `envelope_sha256` binds the envelope with that digest field omitted. |
| [Domain canonical kernel](../../../../omega_engine_pfp/domain/shared_kernel/canonical.py) | Length-delimited domain tag followed by tagged canonical bytes | `domain_digest(domain, value)` binds a value within a named domain. This helper does not itself apply PacketCodec's NFC preprocessing. |
| [Rust canonical kernel](../../../../omega_engine/crates_rs/omega_symbol_game_runtime/src/canonical.rs) | Domain framing around `CanonicalValue` bytes | Inspect the actual producer and representation before asserting Python/Rust parity. |
| [Pydantic `PacketEnvelope`](../../../../omega_engine_pfp/domain/prompts/packets.py) (added 2026-10-20) | Bare SHA-256 of `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)` over eight fields | `envelope_hash` binds `schema_id`, `version`, `task_data`, `protected_boundary`, `budget`, `candidate_payload`, `witness_data` and `authority_effect`. This is neither the tagged kernel nor RFC 8785: it is the plain `json.dumps` form that section 2.1 warns against, and it does not refuse floats. |

**Source check (2026-10-20, pin `c419cc6beb`).** `PacketCodec.seal` ([packet_codec.py](../../../../omega_engine_pfp/domain/packet_codec.py), lines 64-92) emits six fields: `schema_version: "2.0.0"`, `packet_family`, `payload_schema`, `payload_sha256`, `payload` and `authority_effect: "None"`, plus optional `parent_id` and `carrier_id`, then adds `envelope_sha256`. The YAML contract [packet_envelope_v2.schema.yaml](../../../../omega_engine_pfp/infrastructure/yaml/schemas/packet_envelope_v2.schema.yaml) requires 18 fields, sets `schema_version` to the constant `omega.symbol-game.packet-envelope.v2` and forbids additional properties. A sealed PacketCodec envelope is therefore not an instance of that schema, even though both are called "envelope v2". `PacketCodec.verify` (lines 96-138) also treats a missing `authority_effect` as `"None"`. Treat the two as separate formats until an owner reconciles them. The Pydantic `PacketEnvelope` in the table above is a third record with yet another field set and hash profile.

Earlier versions of this page called all three paths RFC 8785 and described every hash as domain-framed. Those descriptions do not apply to PacketCodec. Historical receipts must be replayed with their original producer and profile.

---

## 2. Canonical Serialization Profiles

A payload needs a specified representation before hashing. The profiles below serve different purposes; they are not interchangeable encodings.

### 2.1 Tagged canonical JSON (`omega-canonical-v1`)

The [shared kernel](../../../../omega_engine_pfp/domain/shared_kernel/canonical.py) encodes a closed type algebra as `[marker, tag, body]` arrays. For example, integer `2` becomes `["omega-canonical-v1","int","2"]`; string `"2"` has a different tag. This retains distinctions that an ordinary JSON display may hide.

1. **Deterministic Mapping Order:** Exact string mapping keys are sorted by the kernel and encoded as tagged entries, rather than emitted as an ordinary JSON object.
2. **Zero Floats:** Binary floats are refused. Integers use decimal strings inside integer tags; `Fraction` values retain normalized numerator/denominator data inside fraction tags. A decimal-looking string remains a string.
3. **Minimal Whitespace:** No whitespace outside string literals (no spaces after colons or commas: `separators=(',', ':')`).
4. **Encoding:** Pure UTF-8 without Byte Order Mark (`\xef\xbb\xbf`).

PacketCodec first normalizes strings and mapping keys to NFC, rejecting keys that collapse to the same normalized key. It then computes bare SHA-256 over these tagged bytes. Its envelope hash includes the payload hash and envelope metadata and excludes `envelope_sha256` itself.

This is **not RFC 8785/JCS**. Separate JCS helpers and the [Rust JCS module](../../../../omega_engine/crates_rs/omega_symbol_game_runtime/src/jcs.rs) have their own contracts. Their names do not change PacketCodec's implementation. Do not substitute `json.dumps(payload, sort_keys=True)` for the tagged kernel.

**Check:** Do integer `2`, string `"2"`, and a rational `2/1` necessarily have the same digest? No: their type tags differ. Conversely, canonically equivalent Unicode spellings can share a PacketCodec hash after NFC.

### 2.2 Profile B: Minimal Carrier Wire ($\Gamma_{38}$)
Used for AST trees, primitive differences, and rewrite operators.

- **Alphabet:** $\Gamma_{38} = \{\mathtt{a\text{-}z}\} \cup \{\mathtt{0\text{-}9}\} \cup \{\mathtt{<}, \mathtt{>}\}$.
- **Scope:** The following is a teaching grammar sketch, not the PacketCodec envelope schema. Angle brackets are delimiters; the alphabet has no whitespace. Use the selected [grammar entrypoint](../grammar/README.md) for its actual admission rules.
  ```ebnf
  Packet      ::= Diff | Atom | Application
  Diff        ::= "<>"
  Atom        ::= "<" [a-z0-9]+ ">"
  Application ::= "op<" Packet+ ">"
  ```

---

## 3. Length-Delimited Domain Framing Algorithm

The `domain_digest` helper separates message types with a non-empty **Domain Tag** and explicit big-endian length framing. PacketCodec's payload and envelope hashes do not call this helper:

$$\operatorname{Framed}(D, P) = \operatorname{len}(D)_{4\text{ bytes, big-endian}} \parallel D \parallel \operatorname{len}(P)_{8\text{ bytes, big-endian}} \parallel P$$

$$\operatorname{domain\_digest}(D, P) = \operatorname{SHA256}(\operatorname{Framed}(D, P)).\operatorname{hexdigest}()$$

### 3.1 Field Layout

| Offset | Length | Field | Encoding | Description |
|---|---|---|---|---|
| `0` | 4 bytes | `domain_length` | Big-endian uint32 | Byte length of the domain separator string $D$ |
| `4` | $L_D$ bytes | `domain_bytes` | UTF-8 | Domain identifier (e.g. `omega.symbol-game.packet-envelope.v2`) |
| $4 + L_D$ | 8 bytes | `payload_length` | Big-endian uint64 | Byte length of the canonically serialized payload $P$ |
| $12 + L_D$ | $L_P$ bytes | `payload_bytes` | Canonical bytes | Byte stream produced by canonical serialization |

### 3.2 Worked example: framing the integer `2`

Take domain $D$ = `omega.symbol-game.packet-envelope.v2` and value `2`.

1. Canonical payload: `canonical_bytes(2)` is the UTF-8 encoding of `["omega-canonical-v1","int","2"]` (`_wire` in [canonical.py](../../../../omega_engine_pfp/domain/shared_kernel/canonical.py) returns `[CANONICAL_MARKER, "int", str(value)]`; `canonical_json` uses `separators=(",", ":")`). That string has $L_P = 32$ bytes.
2. Domain bytes: the tag has $L_D = 36$ ASCII bytes.
3. Length prefixes: `len(D)` as 4 big-endian bytes is `00000024` (hex 24 = 36); `len(P)` as 8 big-endian bytes is `0000000000000020` (hex 20 = 32).
4. Total framed length: $4 + 36 + 8 + 32 = 80$ bytes. The payload starts at offset $12 + L_D = 48$.
5. Digests: SHA-256 of the 80 framed bytes is `0497e3c9b8bd228d8043f5c3645c1bffdf1cc01775f554ced565b80f74aa182b`. Bare SHA-256 of the 32 payload bytes alone is `fc605a0ab9dbf93dfbd3cf572d9fc1a85f89302a5ab8ecf92e060aff45b60408`.

These two hex values were computed on 2026-10-20 with a standalone `hashlib` re-implementation of the algorithm above, not by calling the repository function. The same steps were repeated on 2026-10-22. Both hex strings were unchanged. They show that the same value gives different digests under the framed and bare profiles. Before relying on them in a receipt, recompute with `omega_engine_pfp.domain.shared_kernel.canonical.domain_digest`.

### 3.3 Hear and watch the integer 2

The sealer a learner should name first is PacketCodec. It normalizes strings to Unicode normalization form C, which is said "N F C". It then writes the marker `omega-canonical-v1`, said "omega canonical version one". It then takes SHA-256, said "SHA two hundred fifty six", of those bytes. The module `jcs.rs` is a different program. It implements RFC 8785. Its name does not change PacketCodec.

Take the integer 2 before the general rule. Its tagged payload is the 32-byte text `["omega-canonical-v1","int","2"]`. Bare SHA-256 of those bytes begins `fc605a0a`. Framing that payload with the 36-byte domain `omega.symbol-game.packet-envelope.v2` produces 80 bytes. SHA-256 of those 80 bytes begins `0497e3c9`. The full hex strings are in section 3.2.

**Check.** Do the 32-byte hash and the 80-byte hash name the same digest? No. A procedure that prints one hex string for both profiles fails this check.

#### Spoken segment

About 40 seconds. One idea: two lengths, two digests. No screen is required.

"The integer two is sealed as omega canonical version one, tag int, body two. That text is thirty-two bytes. Its bare SHA two hundred fifty six digest is not the digest of the eighty framed bytes. The framed form puts a thirty-six byte domain in front. If someone reports one digest for both forms, the check fails."

#### Video beats

Worked example: integer 2, bare versus framed. Narration matches the spoken segment.

| Time | On screen | Narration |
| --- | --- | --- |
| 00:00 | integer 2 | The integer two is sealed as omega canonical version one, tag int, body two. |
| 00:10 | 32 bytes | That text is thirty-two bytes. |
| 00:18 | bare digest fc605a0a | Its bare SHA two hundred fifty six digest is not the digest of the eighty framed bytes. |
| 00:28 | 80 bytes, domain 36 | The framed form puts a thirty-six byte domain in front. |
| 00:36 | two digests | If someone reports one digest for both forms, the check fails. |

---

## 4. Domain-tag reference register

The following retained names describe domain-framed artifacts. They do not supply a tag to PacketCodec, and this source inspection does not freshly validate every listed producer or historical version.

| Domain Tag | Target Payload | Active Path |
|---|---|---|
| `omega.symbol-game.packet-envelope.v2` | Candidate proposal packet identity | `omega_symbol_game::protocol` (`PACKET_ID_DOMAIN`, [protocol.rs](../../../../omega_engine/crates_rs/omega_symbol_game/src/protocol.rs) line 27) |
| `omega.symbol-game.execution-receipt.v3` | Local CI verification receipt | Historical. No `omega_symbol_game::receipt` module and no producer of this tag were found at the 2026-10-20 pin. |
| `omega.symbol-game.state.v1` | Machine state representation | Historical. No producer of this tag was found in Python or Rust source at the 2026-10-20 pin. |
| `omega.symbol-game.retained-profile-problem.v1` | CEC retained-difference problem | [`retained_profile_cec_bridge.py`](../../../../omega_engine_pfp/infrastructure/adapters/retained_profile_cec_bridge.py) line 296 |
| `omega.symbol-game.active-obstruction.v1` | Active obstruction record | same file, line 384 |
| `omega.symbol-game.cec-child-packet.v1` | CEC conservative extension proposal | same file, line 859 |
| `omega.oesos.rust-prime-host-request.v1`, `...-outcome.v1`, `...-registry.v1` | Rust Prime host request, outcome and registry | `omega_symbol_game::protocol` (`REQUEST_DOMAIN`, `OUTCOME_DOMAIN`, `HOST_REGISTRY_DOMAIN`, lines 24-26) |

---

## 5. Reference Implementation

### Python: actual domain-framing helper

```python
import hashlib
from typing import Any
from omega_engine_pfp.domain.shared_kernel.canonical import canonical_bytes, CanonicalizationError

def domain_digest(domain: str, value: Any) -> str:
    """SHA-256 digest with an explicit, length-delimited domain separator."""
    if not domain:
        raise CanonicalizationError("digest domain must be non-empty")
    domain_bytes = domain.encode("utf-8")
    payload = canonical_bytes(value)
    framed = (
        len(domain_bytes).to_bytes(4, "big")
        + domain_bytes
        + len(payload).to_bytes(8, "big")
        + payload
    )
    return hashlib.sha256(framed).hexdigest()
```

### Rust: illustrative framing equivalent

This snippet illustrates the framing only. The current source exposes `framed_sha256(domain, payload)` and a `domain_digest(domain, &CanonicalValue)` wrapper ([canonical.rs](../../../../omega_engine/crates_rs/omega_symbol_game_runtime/src/canonical.rs) lines 541-567). `framed_sha256` converts lengths with `u32::try_from(..).expect(..)` and `u64::try_from(..).expect(..)`, so an oversized domain panics instead of returning an error. It is not a verbatim current API signature.

```rust
use sha2::{Digest as ShaDigest, Sha256};

pub fn domain_digest(domain: &str, payload: &[u8]) -> Result<String, CanonicalError> {
    if domain.is_empty() {
        return Err(CanonicalError::EmptyDomain);
    }
    let mut hasher = Sha256::new();
    hasher.update(&(domain.len() as u32).to_be_bytes());
    hasher.update(domain.as_bytes());
    hasher.update(&(payload.len() as u64).to_be_bytes());
    hasher.update(payload);
    Ok(format!("{:x}", hasher.finalize()))
}
```

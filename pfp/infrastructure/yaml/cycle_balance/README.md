# Symbol Game Genesis Cycle Balance (four-object lifecycle)

**AuthorityEffect:** None.

Vocabulary: [`../packet_and_prompt.md`](../packet_and_prompt.md).

The files in this directory are fixtures of one cycle-balance family. Schemas live in [`../schemas/`](../schemas/). Grammar copies and the packetization chapters live in [`../03_packetization/`](../03_packetization/). There is no `../packetization/` directory.

The four objects are:
>
> $$P_{\text{problem}} \longrightarrow P'_{\text{proposal}} \longrightarrow V_{\text{verifier}} \longrightarrow R_{\text{receipt}}$$

---

## Canonical Naming Convention

Every problem family instantiated under this directory adheres to the standard 5-part file naming convention:

```text
00_<family>_wire.mssn                                         -> Terse MSS-N AST wire payload
01_<family>_problem.json                                      -> Object 1: Problem / Carrier Contract
02_<family>_candidate.json                                    -> Object 2: Candidate Proposal Packet
03_<family>_verifier.json                                     -> Object 3: Host Verifier Contract
04_<family>_receipt.json                                      -> Object 4: Verifier Receipt Envelope
```

---

## Canonical Packet Family Instances: Genesis Cycle Balance Repair

1. **[`00_genesis_cycle_balance_wire.mssn`](00_genesis_cycle_balance_wire.mssn)**: Terse MSS-N wire AST representation (`cycle_repair<...>`) designed for low-overhead token transmission.
2. **[`01_genesis_cycle_balance_problem.json`](01_genesis_cycle_balance_problem.json)** (**Object 1: Problem Carrier Contract**):
   - Carrier complex $K_0 = (V, E, B)$, cell bounds $N_{\max} = (64, 128, 64)$, boundary operators $\partial_1, \partial_2$, and obstructed 1-cycle $z = [0, 0, 1, 1, 1]^T \in \ker \partial_1$.
   - Content-addressed by SHA-256 `problem_digest`.
3. **[`02_genesis_cycle_balance_candidate.json`](02_genesis_cycle_balance_candidate.json)** (**Object 2: Candidate Proposal Packet**):
   - Untrusted candidate proposal attaching 2-cell $f_1$ with boundary column $[0, 0, 1, 1, 1]^T$.
   - References `problem_digest`. Strictly non-self-certifying (`authority_effect: "None"`).
4. **[`03_genesis_cycle_balance_verifier.json`](03_genesis_cycle_balance_verifier.json)** (**Object 3: Verifier Contract**):
   - Deterministic verification specification enforcing static cell bounds, chain complex nilpotency ($\partial_1 \circ \partial_2' \equiv 0$), and exact integer Smith Normal Form ($U \cdot \partial_2' \cdot V = D$).
5. **[`04_genesis_cycle_balance_receipt.json`](04_genesis_cycle_balance_receipt.json)** (**Object 4: Verifier Receipt Envelope**):
   - **UNVERIFIED receipt skeleton**, with content digests but null terminal status, residuals, and exact witness. Parsing a claimed preimage does not verify it. The former automatic `VERIFIED / EXACT` receipt has been removed.

## Supported wire projection

The transcoder supports the fixed oriented K0 chorded-square incidence matrices
and declared dimensions (4 vertices, 5 edges, 1 original face). Other carriers
are refused instead of being silently replaced with K0. Integer candidate vectors
must have the declared lengths; values and intermediate cycle diagnostics must
fit signed 64-bit arithmetic in both implementations. Unsupported, duplicate, or malformed wire clauses
are refused. The wire's `qed<exact>` remains an untrusted candidate claim.

Wire-to-suite-to-wire preserves this projection, not arbitrary JSON metadata or
host evidence. Serialization uses candidate fields, never a receipt as a replacement
for the submitted witness. The checked-in JSON files are generated from the wire
and checked against both Python and Rust implementations.

Digest encoding is sorted-key, compact UTF-8 JSON, not a claim of general RFC 8785
compliance. Compute the receipt digest with `receipt_digest` set to `""`; object
digests link the problem, candidate, and verifier. Content hashes are not signatures
and do not establish that mathematical verification occurred. An independent host
must check the original problem, chain laws, and submitted preimage before emitting
a separate verified receipt.

## Typed Contracts

- [`pfp_cycle_balance_quartet.py`](pfp_cycle_balance_quartet.py): strict Pydantic v2 models for the problem, candidate, verifier and receipt objects, with the chain-law, cell-bound and digest-binding checks stated above. Parse with `model_validate_json`.
- [`pfp_cycle_balance_quartet.yaml`](pfp_cycle_balance_quartet.yaml): matching type catalog.
- Test: [`../code/tests/test_packets_types.py`](../code/tests/test_packets_types.py).

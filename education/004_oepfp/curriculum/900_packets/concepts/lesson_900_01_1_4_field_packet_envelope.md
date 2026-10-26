# Lesson 900.01 -- 1. The 4-Field Packet Envelope

> [!WARNING]
> **Status: Historical / Superseded.** Not the normative packet contract.
> This lesson documents an early 4-field prototype $(\text{contract}, \text{task}, \text{payload}, \text{parent\_hash})$ for pedagogical demonstration.
> Canonical packet specifications are defined in [`2_symbol_game_packets`](../../../../documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/2_symbol_game_packets/README.md) under the 4-object contract (Problem/Carrier $\to$ Candidate $\to$ Verifier $\to$ Receipt) and `PacketReceiptEnvelope`.
> The checks in this notebook demonstrate character whitelisting and operator prefix parsing on single instances; they do not establish general multi-agent security or universal contract compliance.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_900_01_1_4_field_packet_envelope.ipynb](../notebooks/lesson_900_01_1_4_field_packet_envelope.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 04 - The Three Firewalls: Carrier, Move, and Replay

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*The 4-Field Packet Kernel, Closed Operators, and Fail-Closed Verification Gates*

---

## 1. The 4-Field Packet Envelope

Communication between the proposer (LLM) and the host verifier occurs via discrete, content-addressed **Packets**:
$$\text{Packet} = (\text{contract}, \text{task}, \text{payload}, \text{parent\_hash})$$

The hash of the packet is computed deterministically via SHA-256 over its canonical JSON serialization:
$$h_t = \text{SHA-256}(\text{CanonicalJson}(\text{Packet}_t))$$

## 2. The Three Sovereign Firewalls

1. **FW-CARRIER**: Asserts that every character in the packet belongs strictly to the declared Unicode codepoint whitelist (ASCII 32..126, Greek alphabet, declared logic arrows $\to, \vdash, \bot$).
2. **FW-MOVE**: Asserts that the payload operation begins with an approved closed verb from `DECLARED_OPERATORS` (ASSERT, CUT, REDUCE, PROVE, VERIFY, RETRACT, REFUSE, LAND).
3. **FW-REPLAY**: Asserts that the parent hash $h_{t-1}$ matches the previous ledger head and that the state transition can be deterministically re-executed in $O(K)$ host cycles.

## Anchors

- Former notebook: `04_packet_firewall_host`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

This cell checks a host refusal of the operator `SPECULATE` and of a forbidden character. The void wire `<>` is lesson 800.01. This cell does not parse that wire.

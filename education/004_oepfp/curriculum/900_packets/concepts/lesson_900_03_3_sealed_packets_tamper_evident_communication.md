# Lesson 900.03 -- 3. Sealed Packets: Tamper-Evident Communication

> [!WARNING]
> **Status: Historical / Superseded.** Not the normative packet contract.
> This lesson illustrates canonical JSON serialization and single-packet SHA-256 digest hashing.
> Canonical packet specifications reside in [`2_symbol_game_packets`](../../../../documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/2_symbol_game_packets/README.md).
> Demonstrating hash mismatch on a local dictionary does not eliminate multi-agent receipt forgery without host-pinned ground data and edge-bound carrier verification.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_900_03_3_sealed_packets_tamper_evident_communication.ipynb](../notebooks/lesson_900_03_3_sealed_packets_tamper_evident_communication.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 3. Sealed Packets: Tamper-Evident Communication

In multi-agent systems and LLM pipelines, an agent might attempt to rewrite the user prompt, omit constraints, or forge execution receipts.

In the Symbol Game prototype, single-packet tamper detection is illustrated with **Sealed Packets**:
- Any prompt, candidate response, or evaluation receipt is serialized to canonical JSON (sorted keys, compact delimiters).
- The payload is hashed with SHA-256 to produce an immutable `digest`.
- If an attacker or buggy agent alters even a single bit (e.g. changing `"difference": 1` to `"difference": 0`), the cryptographic digest breaks, and the host refuses the packet immediately.
- *Boundary:* Local hash checks detect bit flips in transit; they do not by themselves prevent carrier spoofing or verify semantic validity without independent host verifiers.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `00_symbol_game_for_beginners`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

This cell checks one canonical JSON digest. The level-0 wire `<>` is lesson 800.01.

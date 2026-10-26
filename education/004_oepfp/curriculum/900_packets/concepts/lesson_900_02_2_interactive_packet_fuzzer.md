# Lesson 900.02 -- 2. Interactive Packet Fuzzer

> [!WARNING]
> **Status: Historical / Superseded.** Not the normative packet contract.
> This lesson demonstrates prototype single-token mutation fuzzing against an early 4-field envelope.
> Canonical packet specifications reside in [`2_symbol_game_packets`](../../../../documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/2_symbol_game_packets/README.md).
> Testing single-token mutators illustrates local firewall rejection; it does not demonstrate universal fail-closed semantics across arbitrary multi-step protocols.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_900_02_2_interactive_packet_fuzzer.ipynb](../notebooks/lesson_900_02_2_interactive_packet_fuzzer.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Interactive Packet Fuzzer

Inject candidate moves below and inspect the Layer 3 Host Firewall verdict:

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that the Three Firewalls intercept non-whitelisted characters, undeclared operators, and broken hash links on tested examples.
> - Demonstrates that valid sample packets produce deterministic SHA-256 digests.
>
> **CANNOT-Show**:
> - A pass on tested fuzzing mutations does not establish universal fail-closed security across un-enumerated inputs or multi-party distributed environments.
> - Does not evaluate semantic validity of mathematical claims or solver outputs.

## 4. Student Exercises

### Exercise 04.1: Fail-Closed Semantics
What does it mean for a firewall to operate "fail-closed"?

<details>
<summary><b>Click to reveal solution</b></summary>
A fail-closed firewall defaults to refusing admission whenever any check fails or whenever an unexpected input or exception occurs. Admission requires every required check to explicitly pass.
</details>

## 5. Anchors

- **Paper 032 Sections**: §4.1–§4.4
- **Ledger IDs**: `PO032-C22` through `PO032-C28`
- **Code**: `papers/032.../code/packet_firewall_host.py`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `04_packet_firewall_host`
- The code checks one finite example. It is not a general proof.

This cell checks one firewall refusal. The level-0 wire `<>` is lesson 800.01.

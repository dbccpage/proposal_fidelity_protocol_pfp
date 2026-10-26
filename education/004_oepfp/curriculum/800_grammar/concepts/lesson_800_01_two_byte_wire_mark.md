# Lesson 800.01 -- The two-byte wire mark

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_800_01_two_byte_wire_mark.ipynb](../notebooks/lesson_800_01_two_byte_wire_mark.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# The two-byte wire mark

Grammar 0 and Grammar 1 both name one legal level-0 wire, `<>`.
Grammar 1, `research/mssn_sn_tower/grammar/1_grammar.md`, is the normative machine grammar.
Grammar 0 keeps the historical sketch. Packet level 0, `research/mssn_sn_tower/packets/0_packets.md`, says the same two bytes are the only level-0 packet.

This sitting parses that wire with `research/mssn_sn_tower/code/python/packet_contracts.py`.
The check is this string on this machine. It is not a proof of the whole grammar.

The frontier lesson [N0](../../600_mssn_frontier/N0_the_genesis_distinction/N0_the_genesis_distinction.md) already teaches the genesis distinction on its own board. This folder does not replace it.

## Exercise

Change `<>` to an empty string. `parse` should refuse it. Put the two-byte wire back and the check should pass again.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- New sitting. Not copied from a former 500 notebook.
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/grammar/readme.md](../../../../../research/mssn_sn_tower/grammar/readme.md)
- [research/mssn_sn_tower/grammar/0_grammar.md](../../../../../research/mssn_sn_tower/grammar/0_grammar.md)
- [research/mssn_sn_tower/grammar/1_grammar.md](../../../../../research/mssn_sn_tower/grammar/1_grammar.md)

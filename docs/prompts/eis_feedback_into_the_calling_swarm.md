# EIS feedback into the calling swarm

AuthorityEffect: None.

You are working in the Proposal Fidelity Protocol repository. This repository is the product. The mega-engine checkout is a foreign briefing, not a place to implement. Do not invent a design. Read the code, run the tests that touch this path, and return instructions for implementing the missing loop here.

## The job

Say how the Epistemic Immune System feeds back into the caller.

The caller may be the adversary swarm, an operative seat, or no swarm at all. The answer has to work in all three cases. A prompt that arrives with no retinue still has to be screened, and a failure on that prompt still has to be recorded against that prompt.

Trace four motions, in this order:

1. Collection. What observation is stored, from which bytes, under which identity.
2. Feedback. What the next caller receives, and which function returns it.
3. The prompt sieve. How that feedback changes which prompt text survives Act III.
4. Immunity of a line. How a sick prompt, its family, its society, and its civilization acquire, keep, or lose a constraint.

If a motion is not implemented, say so and name the file that stops. Do not fill the gap with a story.

## What the mega-engine currently does

Treat this as a claim from outside the repository. Confirm it only if this checkout contains the same objects. Do not import the mega-engine to make the claim true.

A pharmacy antibody is a pattern record: failure class, target pattern, negative fixture, positive fixture, `source_run_id`, `source_task_id`. The farm constructor does not take a prompt id, a family id, a society id, or a civilization id. Harvesting writes a `CANDIDATE`. It does not admit the antibody. Authority effect stays `None`.

The adversary swarm's immune port farms defect strings from a run into that catalog. The patient on the record is the run and the task, not a prompt. Admitted guidance, when read, is a list of `id: description` lines. It is not applied to the next prompt.

Two bodies are defined separately from that cabinet. A prompt genome is a content hash of its packets, domain, parents, and generation. An execution of a genome is a different record: occurrence, prompt id, session, input packet, output packet. A society holds `family_ids` as strings. There is no family type. A civilization holds society ids and a string named `global_immune_registry`. In the schema test that string is `oeeis:registry:v1`. It does not open the pharmacy file.

The one object that binds an antibody to prompt bodies is a Lamarckian mutation receipt: `antibody_id`, parent genome id, child genome id, and the hash of a falsification witness. Hop distance is 1 to 10. That receipt is not what the pharmacy files are.

A second store, `AntibodyEntryV1`, hashes a failure sentence and counts sightings. A repeated sighting does not activate it.

`pharmacy_detect` can say whether one candidate text matches a known failure class. That is a scan. It is not a society treating its own members.

The gap to close: farming a defect is discovery. Learning is this prompt failed, the failure was reproduced, the antibody is bound to that genome, the next child is checked against it, and the child is kept only when the failure does not return.

## What this repository already has

Start here. These are entry points, not a verdict.

- `pfp_core/immunity.py`. `screen_rules` runs thymic negative selection over a self panel. `decide` is the two-signal table: a rule match alone does not block; a witnessed host failure holds. `AntibodyRegistry.observe` stores a pattern with model, scaffold, precedent, and lineage root. Provisional custody needs at least three observations that do not share those roots. Authority effect stays `None`.
- `pfp_core/immune_host.py`. Python harness to the `pfp_immune` binary: `screen`, `decide`, `taint`, `select`, `exclusion`. If the binary is absent, say so and use the Python fallback the module already has. Do not pretend a missing binary ran.
- `pfp_core/funnel_v1rc.py`. `StrandGenomeV1` and the autoimmune screen. A verified survivor is refused when `autoimmune_violations` is not zero.
- `pfp_core/outer_loop_v1rc.py`. Where a strand genome is adopted or tainted.
- `ops/adversary/use_cases/act_helpers.py`. `execute_act3_epistemic_sieve`. Act III currently marks `PASS` when any candidate exists and computes synthetic SBE metrics. The comment in that function says the metrics are not verification. `execute_act4_sandbox_verification` accepts an `antibody_store`.
- `ops/adversary/use_cases/bout_service.py`. The swarm bout that calls Act III.
- `eis/`. Thymus, danger signals, pharmacy files under `eis/antibodies/`.
- `pciv/`. Prompt civilization types in this checkout.
- Atlas claim `ATL-P006-018` in `atlas/atlas_claim_ledger.md`. It says that at the baseline no code matches proposals against catalog fixtures or derives a repair from a positive fixture. Re-check that claim against the current tree. Keep it if it is still true. Narrow it if a caller now exists.

## What you must run

Run the tests that cover these modules before you write the instructions. Name the command, the result, and any test that did not run because a binary or fixture was missing.

Minimum set, plus whatever those tests import:

- The `pfp_core` immune and funnel tests.
- The adversary bout tests that reach Act III and Act IV.
- The `eis` thymus, danger-signal, and pharmacy tests.
- The `pciv` tests that construct a society, a civilization, or a genome.

If a test passes without ever loading `eis/antibodies/` or without ever changing Act III's disposition, say that. A green test that does not touch the loop is not evidence that the loop exists.

## Questions the instructions have to answer

Answer each with a file, a function, and the type of the value that crosses the boundary. If the function does not exist, the answer is the function to add, its inputs, and the test that kills a fake version.

1. Whose immune system is it? One registry for the whole civilization, one registry per society, or one store per prompt lineage? `PromptCivilizationV1.global_immune_registry` is a string today. Either bind that string to a real store or stop calling it a registry.
2. What is a family? Either define the type that `family_ids` point at, or stop claiming families until that type exists. A family is the smallest group that shares an antibody.
3. When a prompt arrives, wild, with no swarm: which function screens it, which store it reads, and what it returns to the caller? The return is a disposition plus the identities of the antibodies that fired. It is not a prose note.
4. When the adversary swarm runs a bout: where does Act III call that same function? `execute_act3_epistemic_sieve` must change its disposition because of an immune result, or it is still a purity sketch. Show the call.
5. When an operative seat runs without the full retinue: which seats are required for collection, and which seats are optional? Collection of a reproduced failure must not require the whole swarm.
6. What bytes are hashed into the evidence? The atlas claim says many stored digests hash an identifier, not the receipt. A learning record hashes the prompt text, the failure, and the checker output. State the exact preimage.
7. How does a candidate become active, and who is allowed to do that? Recurrence is not admission. Name the human or operator act and the field it writes.
8. How does an active antibody change the next child of that prompt? Parent genome, child genome, antibody id, witness hash. If the Lamarckian receipt is the carrier, show the function that writes it and the function that reads it on the next sieve. If it is not, name the carrier you will use instead and why the receipt is the wrong one.
9. How does a line get well? The child is kept when the same failure does not reproduce. State the check and the record that says the antibody fired and the failure was absent.
10. What happens to a detector that fires on healthy prompts? Thymus already kills a rule that matches the self panel. The instructions must say where a prompt-line antibody is submitted to that screen before it can hold a stranger.

## Output

Write one implementation brief for this repository. No mega-engine patches. No new mathematics.

Use this shape:

- Current call chain, as run, with file and function.
- Tests run, with pass, fail, or not run, and why.
- The gap, as missing calls rather than missing essays.
- Types to add or fields to put on types that already exist. Include prompt id, family id, society id, and civilization id only where a value will be stored.
- Functions to add, in call order, from an incoming prompt to a stored antibody and back to the next prompt.
- The Act III change. Quote the disposition rule that replaces "PASS if any candidate exists".
- The no-swarm path and the swarm path, side by side, calling the same screen.
- The tests that fail on a detached cabinet: a pharmacy write that does not name a prompt, a sieve that ignores an active antibody, an antibody that fires on the self panel and is still allowed to hold, a child kept after the parent failure reproduces.
- What you will not build. In particular, do not build a second pharmacy beside `eis/antibodies/` and `AntibodyRegistry` unless a test shows they cannot carry a prompt id.

End with a numbered build order. Each step names the file it edits and the test that goes red before the edit and green after it.

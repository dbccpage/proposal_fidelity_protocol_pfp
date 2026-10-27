# pfp: find what your prompt and your model's reply leave to chance

AuthorityEffect: None.

![pfp check finding nine problems in a release-agent prompt and its JSON reply](demo/demo.gif)

`pfp` is one small binary (about 600 KB) with no network access, no
subprocesses and no writes unless you ask for one. It checks a prompt and the
text or JSON a model produced from it, and it seals files into packets that
anyone can replay.

```sh
cargo install --locked --git https://github.com/dbccpage/proposal_fidelity_protocol_pfp pfp-cli
pfp demo                                         # see it work on a bundled example
pfp check --prompt prompt.md reply.json          # your own files
```

## Commands

| Command | What it does | Writes? |
| --- | --- | --- |
| `pfp check [FILE ...] [--prompt FILE] [--json]` | Runs 13 detectors over model outputs (text or JSON) and the prompt. `-` reads stdin | Never |
| `pfp seal FILE ... [--out PACKET]` | Prints a packet with the SHA-256 of each file | Only with `--out`, and never over an existing file |
| `pfp replay PACKET [--root DIR]` | Checks that the files still match the packet | Never |
| `pfp explain [CODE]` | What a code means, why it matters, what to do, where to read more | Never |
| `pfp demo` | `check` on a bundled prompt and reply | Never |

Exit codes: **0** nothing found, **1** findings or mismatches, **2** could not
run (bad arguments, unreadable or non-UTF-8 input, input over 10 MiB).

## What it finds

Text is checked line by line, JSON field by field. Each finding names a code;
`pfp explain CODE` teaches it.

| Code | Means |
| --- | --- |
| `SELF_CERTIFICATION` | The model certifies its own work (`"verified": true`, `receipt`, `admitted`, ...) |
| `FAKE_RECEIPT` | A digest the model made up in a field only your code should fill |
| `PERSONA_AUTHORITY_LEAK` | A role field claims authority (admin, executive, ...), in several languages |
| `CONCLUSION_PRELOAD` | The prompt dictates the answer ("it must be verified") |
| `NO_REFUSAL_PATH` | The prompt never says what to do when the task can't be done |
| `OPTIMALITY_HALLUCINATION` | "Optimal", "fastest", ... with no objective or bound |
| `COMPLEXITY_HALLUCINATION` | "O(n)", "linear time", ... with no basis |
| `THEOREM_NAME_LAUNDERING` | "By the ... theorem" with no assumptions stated |
| `PRIVATE_COT_DEPENDENCY` | The answer leans on hidden reasoning |
| `SCHEMA_SEMANTIC_LAUNDERING`, `DETECT_REPAIR_COUPLING`, `BRANCH_DROP_EXHAUSTION`, `VERSION_DUPLICATION` | Agent-protocol checks for `proposed_claim_deltas`, `objections` and search claims |

Severity is a routing hint: **REFUSE** (do not act on it), **HOLD** (needs more
evidence), **FINDING** (worth a look).

The detectors are deterministic word and structure checks from the
[anti-skill pharmacy](../core_prompt_civilization/src/pharmacy.rs). They miss
things, and they can flag a sentence that is fine in context. **No findings
means these detectors found nothing. It is not proof the text is right.**

## Packets

```sh
pfp seal prompt.md reply.json --out packet.json   # record exactly what was proposed
pfp replay packet.json                            # later, or on another machine
```

Paths must be relative and stay below the current folder. `replay` refuses a
packet whose paths climb out (`..`), whose fields are unknown, or whose own
hashes do not match. The hashes catch edits; they are not a signature, so a
match proves the bytes are unchanged, not who sealed them.

## Use it in CI

```yaml
- run: cargo install --locked --git https://github.com/dbccpage/proposal_fidelity_protocol_pfp pfp-cli
- run: pfp check --prompt prompts/agent.md fixtures/agent_reply.json
```

## Add a check

Implement `pfp_cli::Check` (a list of codes and a `run` function that returns
findings), add it to `builtin_checks()` in [`src/check.rs`](src/check.rs), and
give each code an entry in [`src/catalog.rs`](src/catalog.rs). A test fails if a
code has no entry. Checks must be deterministic and must never repair: a
finding names the problem and nothing else.

## Build and test

```sh
cargo test                                           # includes the safety-contract tests
cargo build --lib --target wasm32-unknown-unknown    # the core runs in a browser
vhs demo/demo.tape                                   # re-render the GIF
```

The crate is standalone (its own workspace) so it does not build the engine
crates next door; it depends only on `core_prompt_civilization`.

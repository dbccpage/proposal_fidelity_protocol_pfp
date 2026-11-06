# PO035 compact contract rerun

`AuthorityEffect: None.` All five pilots completed under their existing per-run
$0.05, 120000-provider-token and 180-second limits. The campaign made 15 calls,
used 56450 reported tokens and recorded $0 provider cost. Every reply ended with
`stop`; none was truncated. The largest run used 13063 tokens and 46.922 seconds.
The freshly captured catalog admitted only the zero-price Nemotron route.

The empirical result is **failure of the compact output contract**: all 15 replies
were strict-schema refused. No final certificate reached the unchanged mathematical
judge. A useful calculation inside a malformed answer is not a host-accepted result.
This candidate is not promoted to a universal or production PFP default.

Two independently blinded Codex reviews cover all ten final replies. Both found
nine with critical mathematical errors and one with correct finite causal values
but an incomplete refinement theorem and other misstated implications. None met
the full analytical goal. The correct finite values are an informal partial-content
observation, not a repaired packet or a host pass.

| Role | Replies | Schema valid | Joint successes | Truncated |
| --- | ---: | ---: | ---: | ---: |
| Single shot | 5 | 0 | 0 | 0 |
| Public workpad | 5 | 0 | Not applicable | 0 |
| Final from workpad | 5 | 0 | 0 | 0 |

All five workpads failed ingress. Consequently every final received the fixed
missing-workpad note, with no workpad, control reply or host feedback. This round
cannot establish an effect of valid workpad assistance. The preregistered target
of two additional joint successes was not met. Historical workpad truncation is
absent here, but shorter refused replies do not establish improved task success.

## What changed

The full original seeds and their difficult analytical obligations remain intact.
One typed YAML input profile serves all five tasks. A workpad has at most three
short public field records and no full certificate. Finals have one certificate
and corresponding calculation records with a fixed carrier, expression and typed
result for each field. Strict checks require exact native-type equality between
each result and certificate field before acceptance. Expressions themselves are
not automatically evaluated or proved; the original finite judges remain separate.

The common roles are registered in
[the prompt version guide](../../../pfp/infrastructure/yaml/prompts/versioned/README.md):

| Exact role version | Purpose |
| --- | --- |
| `PFP-T0001-v1.0.0` | Single-shot seed-to-final control. |
| `PFP-T0002-v1.0.0` | Optional short public calculation workpad. |
| `PFP-T0003-v1.0.0` | Final answer using only a validated own-run workpad. |
| `PFP-R0001-v1.0.0` | Measurement recipe binding those three exact versions. |

Stable `T####` role IDs and separate `R####` recipe IDs use immutable semantic
versions. Registry entries define ownership, compatibility, supersession and
deprecation. Seed/context/run-ID changes are hashed instances, not new template
versions. Instruction, schema or renderer changes require a new version with old
bytes preserved. There are no `latest` aliases. Logit, glyph and semantic-rewrite
variants are explicitly off in this recipe rather than hidden prompt options.

## Observed design failure and next goals

Our compact layout description used explanatory keys such as
`root_required_only` and `row_required_only`. The model copied those descriptions
into its response instead of assembling the actual nested object. Independent
format review of the first two pilots also found misplaced summary fields,
incorrect nesting and arrays serialized as strings or type descriptions. Merely
unwrapping the extra keys would not recover valid packets. The original replies
remain unchanged, and no such repair was counted.

The next small candidate should replace that response-shaped metadictionary with
the actual compact role schema and one exact placement instruction. This can be
a separately numbered PATCH if it preserves the existing output contract; a
flatter output schema would require a MAJOR version. No successor template or
additional provider campaign was silently added after observing these results.

The next round should first require five valid single-shot packets with no
truncation under the same caps. Keep the model, seed, mathematical judge and
decoding fixed while changing only the representation of the contract. Then
check all field bindings and finite predicates, followed by independent analytical
review. Test a workpad offshoot only after its short ingress reliably succeeds.
Use decoding enforcement only on a separately verified route that supports it;
typing the input alone does not enforce the provider's output tokens. Logit and
glyph experiments remain separate opt-in variants, not additions to the default.

The research target remains a seed inside one easy-to-learn typed input profile,
with a direct final answer as the default and a small explicit workpad offshoot.
These five tasks do not establish a universal optimum. There are no Rust execution
or general mathematical-proof claims from this round, and no learning artifact
is automatically admitted.

## Evidence and local validation

- [Preregistration](spec.yaml), [measured results](results.json) and [source pins](sources.json).
- [Preflight code review](architecture_agent_review.json),
  [observed format review](format_agent_review.json) and
  [independent evidence audit](closeout_agent_review.json).
- [Derivation review](derivation_agent_review.json) and
  [execution review](execution_agent_review.json): all ten final replies, with
  current arm/model and host verdicts withheld. Reviewers had prior task knowledge;
  these informal analyses are not formal proofs.
- [Seven learning candidates](learning_candidates.json), all `UNADMITTED`, with
  no fixture answers in their guidance and future controls required before promotion.
- [Updated player and engineering guide](../../../documentation/004_oepfp/docs/16_numbered_prompt_roles_and_po035_play.md)
  documents discoveries, experimental types, numbered roles and game variants.
- [Targeted local validation](local_validation.json): 171 distinct checks passed;
  the two initial preflight failures and their successful fix are recorded.
- All 15 original raw replies, request wires, receipts, verdicts and durable budget
  ledgers are retained under the five `pilot_*` folders. All 32 frozen source files
  are retained under `source_snapshot`. The 23 historical runtime pins are unchanged.
- Three additional eager-import dependencies are retained separately in
  [replay dependency custody](replay_dependencies.json). These were captured at
  closeout with clean Git-base provenance, not claimed as dispatch-time snapshots.
- [Replay receipt](replay.json): all 15 captured calls replayed without provider calls.
  Replay reproduces the retained evidence interpretation, not future hosted generations.

Run from the repository root with Python 3.12.10, PyYAML 6.0.3 and jsonschema 4.25.1:

```powershell
.venv/Scripts/python.exe -m omega_engine_education.pilots.evidence.po035_simplified_20261012.replay
.venv/Scripts/python.exe -m omega_engine_education.pilots.evidence.po035_simplified_20261012.verify_manifest
```

The snapshot replayer uses the retained source tree so later append-only prompt
versions cannot invalidate historical replay. The manifest checks exact artifact
inventory and bytes. Only targeted local checks and offline replay were run;
there was no full canonical or hosted CI.

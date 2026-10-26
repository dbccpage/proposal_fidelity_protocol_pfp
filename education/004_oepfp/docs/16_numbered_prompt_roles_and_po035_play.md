---
documentation_contract: symbol-game-documentation/v1
title: "Numbered Prompt Roles, Calculation Bindings and PO035 Play"
kind: reference
audience:
  - players
  - engineers
  - coding-agents
status: active
maturity: experimental
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - omega_engine_pfp/infrastructure/numbered_prompts.py
  - omega_engine_woland/tests/pilots/relational_spacetime/compact_checks.py
  - omega_engine_woland/tests/pilots/relational_spacetime/compact_trials.py
  - omega_engine_pfp/infrastructure/yaml/prompts/templates/template_role_registry.yaml
  - omega_engine_pfp/infrastructure/adapters/pfp_frozen_replay.py
  - omega_engine_pfp/infrastructure/yaml/taxonomy/task_families.yaml
  - omega_engine_woland/tests/pilots/evidence/po035_simplified_20261012
  - omega_engine_woland/tests/pilots/evidence/po035_experiments_20261012
last_verified: 2026-10-20
verification_scope: paths, registry version and refusal codes checked against source at c419cc6beb; PO035 results are historical and were not replayed
---

# 16. Numbered prompt roles, calculation bindings and PO035 play

`AuthorityEffect: None.` The current research target is a small, reusable recipe:
put the complete seed in typed YAML, request one typed final answer, and check it
independently. A short public workpad is an optional offshoot. The PO035 results
below do not establish that this recipe is effective across tasks. They identify
specific ways a plausible prompt can fail.

## Discoveries from the bounded trials

The [compact rerun](../../../../omega_engine_woland/tests/pilots/evidence/po035_simplified_20261012/README.md)
covered pilots 199–203: five runs, three calls per run, 56450 reported tokens and
$0 reported provider cost. All calls and host stages shared each pilot's $0.05,
120000-token and 180-second ceilings. All 15 replies ended normally, with no
truncation. All 15 nevertheless failed strict schema validation. The ten finals
never reached the unchanged finite mathematical judge.

Our layout description contained explanatory keys such as `root_required_only`
and `row_required_only`. Models copied them as literal response fields. Some
answers also emitted vectors as bracketed strings or copied type descriptions
instead of values. The replies copied the layout description despite its placement
instructions. No reply hit its token ceiling, so truncation does not explain these
failures; the effect of a higher ceiling is untested. A candidate correction is
the actual compact role schema with one precise nesting instruction; that
correction has not yet been dispatched or demonstrated.

All five public workpads were refused, so every final received only the declared
missing-workpad note. This round supplies no evidence for valid workpad assistance.
Two independent Codex agents reviewed all ten finals without current arm/model or
host-verdict metadata. None met its full analytical goal. One causal answer had
all six finite witness values correct, but a malformed contract and an incomplete
refinement theorem. Useful arithmetic in an invalid packet is retained as partial
evidence, never converted into an accepted result.

The [preceding experiment](../../../../omega_engine_woland/tests/pilots/evidence/po035_experiments_20261012/README.md)
ran five scratchpad, five temperature and five logit-bias cases: 40 calls,
198952 tokens and $0.017035 reported cost, all within their per-run caps. Eight of
ten larger public workpads were truncated. Only five of thirty final packets were
schema valid; independent review found critical mathematical errors in all five.
Format-only logit bias was requested, not internally attested, and did not produce
an accepted finite witness. Temperature samples do not establish a preferred
temperature. Five attention-head cases were unavailable and made no calls; they
were not simulated into results. The compact rerun changes a bundle of ingredients,
so historical differences cannot isolate the cause of an improvement or failure.

Typing an input defines a contract and can narrow accepted outputs. It does not
by itself constrain the provider's decoding. Provider-enforced structured output,
host schema validation, mathematical checking and informal analytical review are
different mechanisms and must have separate receipts.

## New experimental types and their limits

These are runtime schema profiles and metadata from the compact PO035 experiment,
not additions to the canonical PFP EBNF or new globally admitted policies.

| Type or identity | Shape and invariant | What it does not establish |
| --- | --- | --- |
| Prompt role | Stable `PFP-T####` plus immutable semantic version. | A new role is not a new mathematical task family. |
| Recipe | Separate `PFP-R####` binding exact role versions, order and limits. | A recipe does not silently select the newest template. |
| Rendered instance | Pilot, role/recipe version, validated run ID and hashes of seed, system, user and schema. | A new seed or run ID is not a new template version. |
| Public workpad | `derived_under_policy`, own `prompt_id`, up to three records and bounded `open` obligations. Each record has `field`, `expression`, `result`. | Schema validity does not make a workpad's public calculation correct. |
| Calculation binding | For each certificate field: exact `carrier`, bounded public `expression`, and a `result` with the original field type. | Matching results do not evaluate the expression or establish a theorem. |
| Typed final | SPK envelope with one derivation row, one certificate and corresponding calculations. A typed refusal has both nullable witness fields set to null. | Refusal is a useful scoped outcome, not task success. |
| Split verdict | Separate schema, binding, finite-certificate and analytical statuses. | Valid JSON or repeated values do not imply finite acceptance. |

The ingress rejects duplicate keys, markdown fences, additional fields, wrong
identities and native-type substitutions. An integer cannot be a float or boolean;
a rational vector cannot be a string that only looks like a list. Each final
calculation result must agree exactly in type and value with its certificate field.
The field's carrier distinguishes, for example, a metric star from a separate
cochain triangle, or projected full dynamics from residual-only dynamics.

No private reasoning channel is required. Workpads are short public calculation
records. Invalid, cross-pilot or cross-run workpads cannot become final context.
Host mutations separately test a broken calculation binding and a wrong finite
value with matching fields. Those targeted fixture checks passed; no live packet
in this rerun passed ingress, so they are not live-model success receipts.

## Choose a role without multiplying templates

The former `prompts/versioned/` directory and its README are no longer on disk at the
2026-10-20 pin. The current owner is the unversioned
[template role registry](../../../../omega_engine_pfp/infrastructure/yaml/prompts/templates/template_role_registry.yaml)
(`version: 1.0.4`, profile `RELATIONAL_SPACETIME_EXPERIMENTAL_CANDIDATE`), which names
`template_pfp_t0001.yaml` to `template_pfp_t0003.yaml` and `template_pfp_r0001.yaml`; the
[prompts README](../../../../omega_engine_pfp/infrastructure/yaml/prompts/README.md) says
historical versions are kept in Git history rather than version directories. The table below names the frozen experiment's
original v1.0.0 identities; versions 1.0.1, 1.0.2 and 1.0.3 remain separate profiles:

| Exact ID | Role | Input and carry |
| --- | --- | --- |
| `PFP-T0001-v1.0.0` | `SINGLE_SHOT` | Verbatim seed, task contract and bounded procedural hints; no prior reply. |
| `PFP-T0002-v1.0.0` | `PUBLIC_WORKPAD` | Same seed, at most three short public field records; no control output. |
| `PFP-T0003-v1.0.0` | `FINAL_FROM_WORKPAD` | Same seed and only a validated own-run workpad, if present. |
| `PFP-R0001-v1.0.0` | Measurement recipe | One single-shot control and a two-call workpad/final arm sharing one cap. |

This is an experimental candidate, not a new production default. Use a new
semantic role ID only for a genuinely different role. Preserve published versions
and implementations. Breaking schema, scope or carrier changes increment MAJOR;
compatible capabilities increment MINOR; contract-preserving wording or renderer
corrections increment PATCH. Even PATCH changes require fresh hashes and evidence.
There are no `latest` aliases. Supersession and deprecation are recorded in a new
registry version rather than rewriting the old one.

For offline inspection of the actual registered input:

```python
from omega_engine_pfp.infrastructure.numbered_prompts import build_prompt

prompt = build_prompt("pilot_0000199", 1, run_id="documentation_example")
print(prompt["user_prompt"])
```

This performs no provider call. The current renderer accepts the five registered
PO035 pilot IDs; it is not a general arbitrary-seed API. A broader reusable seed
wrapper remains a research target. Never overwrite a historical seed or renderer
to make a retained experiment appear successful.

The six frozen v1.0.0 files moved byte for byte to the canonical resource owner;
the old Education PFP application directory no longer exists. At the 2026-10-20 pin
those v1.0.0 resources are no longer in the working tree either:
`read_frozen_prompt_source` reads packaged data when present and otherwise the Git
object at commit `56e1e552c5`, and returns `FROZEN_SOURCE_UNAVAILABLE` when neither
exists ([pfp_frozen_replay.py](../../../../omega_engine_pfp/infrastructure/adapters/pfp_frozen_replay.py)
lines 53-75). Copies also remain inside the evidence bundles under `frozen_sources/`
and `source_snapshot/`. Original paths in
retained receipts and snapshots remain historical identities. Explicit readback
uses `read_frozen_prompt_source` in the existing frozen replay adapter; it checks
the original digest and refuses missing or altered resources. Full historical
replay still uses its retained implementation and evidence bundle.

The displayed current API selects v1.0.3 and renders with the current Atlas PO035
paper, including the unchanged section-5 excerpt used by pilot 201. It has new
registry/role/recipe identities and the separate
`po035_simplified_v1_0_3_20261012` run namespace. Instructions, schemas, original
seeds, scope and limits are unchanged; no new model result is claimed.

> **Status at `201dc8d` (2026-10-15).** `omega_engine_pfp/infrastructure/numbered_prompts.py`
> now selects v1.0.4 (`PFP-R0001-v1.0.4`, run namespace
> `po035_simplified_v1_0_4_20261013`), while the versioned prompts README still
> names v1.0.3. See the [pilot status](../README.md#pilot-status-at-201dc8d-2026-10-15).
>
> **Status at `c419cc6beb` (2026-10-20).** `numbered_prompts.py` lines 33-41 still select
> `PFP-R0001-v1.0.4` and pin the registry by SHA-256 (`REGISTRY_SHA256`). The versioned
> README is gone, so the v1.0.3 mismatch no longer exists on disk. The registry lists
> only v1.0.4 roles, each superseding v1.0.3.

Version 1.0.2 retained its older full-paper pin and refused current-paper drift
with `VERSIONED_PROMPT_INPUT_CHANGED` (historical; no v1.0.2 profile is on disk at the
2026-10-20 pin). In the current code `_registry()` raises `PROMPT_ROLE_REGISTRY_CHANGED`
when the registry digest differs and `VERSIONED_PROMPT_INPUT_CHANGED:<path>` when any file
listed in its `file_sha256` map differs (`numbered_prompts.py` lines 128-137). Never repin it, substitute the current
profile for an old run, or silently load old paper bytes. The current-source
checks and installed-wheel exercise are offline construction evidence only;
historical campaign replay still requires its bound source and runtime.

## Ways to play with these findings

Each row below states whether it was played, checked locally or only proposed.
Keep one declared carrier, seed, checking rule and budget for each game.

| Game | Player's move | Referee and current status |
| --- | --- | --- |
| Same seed, single shot | Answer the complete seed once inside the typed contract. | Played on five PO035 tasks; all contracts refused. Repair the prompt representation before claiming a default. |
| Short public workpad | Record up to three calculations, then answer using only the valid own-run record. | Played on five tasks, but all workpads refused; assistance was unavailable. |
| Calculation/carrier matching | Bind each answer field to its stated carrier and calculation; challenge a copied value or mismatched type. | Strict local positive and negative controls passed. Displayed expressions still need mathematical checking. |
| Conservation counterexample | Derive residual-only balance and full projected dynamics on the same fixture; locate a source term before claiming conservation. | Existing `microscopic_defect_current_derivation` family, pilot 200. Live analytical attempts remain incomplete or incorrect. |
| Transport and curvature | Compare direct and composite typed transports, then separate an identity control from curvature. | Existing `covariant_relational_spine_derivation` family, pilot 201; positive obstruction is not supplied by terminology alone. |
| Two-carrier metric game | Change an intrinsic triangle-star metric while separately checking a cochain quotient and its degree. | Existing `metric_cochain_bridge_derivation` family, pilot 202; mixing the two carriers remains an observed failure. |
| Obstruction versus stopping | Supply exact primal/dual witnesses, one continuing system and a separately declared stopping policy. | Existing `obstruction_terminal_policy_derivation` family, pilot 203; static obstruction alone is not a halting rule. |
| Temperature or logit variant | Change only the declared decoding parameter; keep seed, contract and judge fixed. | Earlier cases ran; no accepted finite result or preferred setting was established. Logit enforcement was not internally attested. |
| Emoji or hieroglyph variant | Propose an explicit reversible symbol map, pin its decoding, and compare with the ordinary-text control. | Proposed offshoot only in this round. No new glyph or head-intervention result is claimed. |

The fifth existing PO035 family, `causal_refinement_derivation` in pilot 199,
asks for a conditional limiting cone statement and a separate exact witness.
An upper bound is not a sharp propagation theorem. The five family tokens are
already present in the runtime taxonomy; this documentation does not mint new
bedrock tokens or promote experimental types into grammar rules.

## Replay, learning and the next small round

From the repository root:

```powershell
.venv/Scripts/python.exe -m omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay --bundle omega_engine_woland/tests/pilots/evidence/pfp_ownership_migration_20261012 --profile compact-three-stage
.venv/Scripts/python.exe -m omega_engine_woland.tests.pilots.evidence.po035_simplified_20261012.verify_manifest
```

Replay uses the 32 dispatch-pinned source files plus three separately retained
eager-import dependencies captured at closeout with clean Git-base provenance.
It preserves old prompt versions even after the registry grows. It verifies the
15 retained calls without contacting a provider; it does not promise identical
future hosted text. The [evidence report](../../../../omega_engine_woland/tests/pilots/evidence/po035_simplified_20261012/README.md)
links raw replies, receipts, reviews, replay and the full manifest.

First test the exact-output-contract correction on five single-shot packets under
the same caps, with the same seeds and judge. Require valid shapes before adding
a workpad comparison. Then count typed field bindings, finite acceptance and full
analytical obligations separately. Candidate antibodies should target a measured
failure, avoid fixture answers and pass new-task positive/negative controls before
admission. No learning was automatically admitted in these campaigns. Only targeted
local checks and offline replay were run; no full canonical or hosted CI was run.

The recorded results above use frozen version `1.0.0`. The ownership cleanup added an undispatched `1.0.1` relocation version and moved active research code beside the pilots. See [runtime ownership and replay](17_runtime_ownership_and_replay.md).

# PFP type register

**AuthorityEffect:** None.

One file records every PFP data type: [type_register.yaml](type_register.yaml), typed by
[type_register.py](type_register.py). The test
[test_type_register_types.py](../code/tests/test_type_register_types.py) reads the source
tree with `ast` and fails when the register and the tree disagree.

A *type* is a Pydantic model or an `Enum` defined at module level in a tracked `.py` file
under this directory. Test files and `demos/` are outside the census.

## Layout rules

1. **Two import worlds.** A type that validates a file lives beside that file (for example
   [host_packets/pfp_host_packet.py](../host_packets/pfp_host_packet.py)). Runtime records
   (pilot runs, provider calls, verdicts) live in [python/domain/](../python/domain/).
   Runtime code reaches a co-located type through
   [colocated_types.py](../python/infrastructure/pilots/colocated_types.py), never through a
   second copy.
2. **One source of shape per module.** Each row says which side states the shape:
   `pydantic`, `yaml` (the `.py` is generated), `both_parity_tested`, or `both_unchecked`.
   `both_unchecked` rows are marked `review`; each needs a parity test or one side removed.
3. **No public type name defined twice.** `name_collisions` lists the names that are, and
   `overlaps` lists types that describe one fact under different names. Both lists may only
   shrink: the census fails on a new collision and on a row that no longer applies.
4. **Derived types become views.** `derived` lists stored types that are a projection, join,
   aggregate or computed value of another type. A row with `checked_by` names the test that
   compares the two. A derived type is deleted only after such a test passes.
5. **New schemas are JSON Schema 2020-12.** The custom field-spec dialect
   (`schema_id` / `meta_version` files) is converted when a file in it is next changed.

## Adding a type

1. Put the model beside the file it validates, or in `python/domain/` if it is a runtime
   record.
2. Add a row to `modules` in sorted position: `world`, `source`, the YAML files with their
   role, and the tests that cover it.
3. If the census reports `NEW_NAME_COLLISION`, rename the type. Add a `name_collisions` row
   only when the owner accepts the duplicate for now.
4. Run `python -m pytest code/tests/test_type_register_types.py -q`.

## Awaiting the owner

These change files that `main` added, so this branch does not make them. The `gate_spec.py` row is the exception: this branch added that file, but moving it edits main's `gates/gate_types.py`.

| File | Finding |
|:---|:---|
| [modes/mode_catalog.yaml](../modes/mode_catalog.yaml) | 11 of 20 mode names differ from the mode contracts; mode 13's name holds a TAB. Which names are canonical, the contracts' or the README's? |
| [python/domain/gate_spec.py](../python/domain/gate_spec.py) | Types the gate file bodies; belongs beside [gates/gate_types.py](../gates/gate_types.py), whose `PrimaryGate` is its projection. |
| [python/domain/mode.py](../python/domain/mode.py) | `gen_modes_and_stages_types.py --check` fails: the committed file lacks two imports the generator writes. |
| [gen_prompt_template_types.py](../python/infrastructure/generators/gen_prompt_template_types.py) | Reads `prompt_templates/`, which the reorganisation moved to `prompts/`. |
| [gen_rewrite_schema.py](../python/infrastructure/generators/gen_rewrite_schema.py) | Writes `prompt_rewriting/rewrite_models.json`, a path that no longer exists. |
| [openrouter_adapter.py](../python/infrastructure/providers/openrouter_adapter.py) | Cost labels are swapped on errors: an HTTP 200 error reply with a reported cost is labelled `ZERO_FOR_PROVIDER_ERROR`, and an HTTP 500 with no cost is labelled `PROVIDER_REPORTED` at `0.00`. `ProviderCallResult` refuses the first; the second passes unnoticed. |
| [openrouter_adapter.py](../python/infrastructure/providers/openrouter_adapter.py) | When the HTTP call raises, `complete()` settles `0.00`, then calls `_settle`, which raises `REQUEST_ALREADY_TERMINAL` out of `complete()`. The pilot runner records it as `PROVIDER_RAISED` and holds the family. |
| [pilots/pilot_output/](../pilots/pilot_output/) | Eight typed files with no tests; money is a float; `result` and `summary` store aggregates of `observations.json`. |
| [filtrations/](../filtrations/) | `four_axis_separation` and `pfp_filtration` state their shape twice with no parity test; money is a float. |
| `name_collisions`, `overlaps` | Five collisions and five overlap groups; the register names a candidate base for each. |

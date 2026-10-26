---
pattern_id: AP_MD_059
name: prompt_agency_and_self_authorizing_miner
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_059_prompt_requests_host_verifies
language: markdown
authority_effect: None
---

# Anti-Pattern: Prompt Agency, Self-Authorizing Mining, and Conflated Families (`AP_MD_059`)

## Description

Occurs when prompt descriptions, essays, or protocol specifications attribute autonomous enforcement agency to natural language prompts, treat model-mined structural components as self-authorizing ground truth, group non-isomorphic negative controls into the same prompt family, conflate pretty-printed ASTs with zero-whitespace wire representations, or use mentalistic terminology for checkable derivation artifacts.

## Failure Modes

1. **Prompt Agency:** Claiming that a prompt "forces" intermediate derivations, "ensures the model emits no filler," or "checks equations." Prompts only condition proposals; host code parses, verifies, or rejects.
2. **Self-Authorizing Mining:** Treating model outputs from extraction probes (mined rules, skills, patterns, antibodies) as established facts rather than unverified candidate proposals requiring host gate admission (`AuthorityEffect: None`).
3. **Prompt Family Conflation:** Classifying negative controls or refusal probes under the primary prompt family when they omit admitted rules or alter boundary conditions, thereby changing the acceptance predicate.
4. **Wire Representation Mislabeling:** Displaying an indented, multiline, or spaced syntax tree while labeling it an "exact zero-whitespace wire."
5. **Mentalistic Witness Slots:** Using internal cognitive labels (`SCRATCHPAD_WITNESS`, `thinking_trace`) instead of artifact-oriented checkable labels (`DERIVATION_WITNESS`).

## Prevention & Resolution

See dual pattern [HP_MD_059_prompt_requests_host_verifies](../../helpful/markdown/HP_MD_059_prompt_requests_host_verifies.md).

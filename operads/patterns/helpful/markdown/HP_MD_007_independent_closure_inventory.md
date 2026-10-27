---
pattern_id: HP_MD_007
name: independent_closure_inventory
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_007_self_compared_package_list
language: markdown
authority_effect: None
---

# Healthy Pattern: Independent Closure Inventory (`HP_MD_007`)

## Description

A dependency-custody check enumerates the local closure independently of the submitted inventory, then compares the submitted file set to that enumeration. Omitting a whole local package refuses. Agreement of a list with itself is not closure evidence.

## Construction

- Enumerate local packages from the package graph or from manifests on disk. Do not take the package universe from the receipt's own manifest list.
- Compare the submitted file inventory with that enumeration, including each package manifest.
- Refuse a receipt that drops an entire local package. A receipt that lists the reconstructed closure may pass.
- Keep one unchanged valid receipt and one whole-package omission on the same consumer. Record the refusal reason.
- Call the result source custody. It does not select a mathematical terminal, and it does not refute the bounded statement.
- Bind the receipt to the bytes that were checked. A success line that names different bytes is a post-audit mutation race, owned by `/adversarial-receipt-audit`, not by this comparison.

## Limit

The witness in [AP_MD_007_self_compared_package_list](../../anti/markdown/AP_MD_007_self_compared_package_list.md) is historical. This digest did not open the current custody implementation and did not rerun the omitted-dependency reproduction. The review's report that a later checker rejected the omission is historical too.

`/declared-vs-actual-gate` already derives skill host roots from the filesystem and refuses a declared mirror list that is a strict subset. This pattern does not replace that gate and does not decide skill-mirror parity.

`/adversary-check-sensitivity-pattern` still requires naming the consumer. Another check may already hash a path outside the submitted list; identify it instead of calling the whole pipeline unsound. One omission does not prove every missing file is caught.

A certificate changed after parse, and a null root that selects certificate construction, are different defects. An independent package enumeration does not repair them. Finite controls do not prove a universal closure theorem, and they do not verify native or original program source.

## Dual Anti-Pattern

See [AP_MD_007_self_compared_package_list](../../anti/markdown/AP_MD_007_self_compared_package_list.md).

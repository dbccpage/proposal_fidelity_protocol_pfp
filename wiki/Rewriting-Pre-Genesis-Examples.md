# Pre-Genesis rewriting: examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Pre-Genesis.md) · [Strategies](Rewriting-Pre-Genesis-Strategies.md)

## Example 1: asked for a step, nothing happens

A prompt supplies `<>` and asks for one step.

1. The rule set is empty.
2. PG1 applies: no redex, no transition.

```text
<>
```

Receipt:

```text
<<cert><<token><>>><<status><quiescent>><<steps><0>>>>
```

**The point.** The correct answer is zero steps. Any "next token" would be an
invented rule.

## Example 2: a task that needs a split

Task: route `<a>` left and `<ab>` right. No observations are available yet.

1. **PG4.** With no observations, `<a>` and `<ab>` are equivalent. The task
   cannot be done on the current classes.
2. **PG5.** Choose an observation: *payload length is 1*. It gives true for
   `a` and false for `ab`.
3. The classes split, and the routing follows.

```text
<<partition><<left><a>><<right><ab>>><<obs><len1>>>
```

Receipt:

```text
<<cert><<status><separated>><<predicate><len1>><<canonical_lift><false>>>>
```

**The point.** `canonical_lift` is false. "Contains b" or payload parity would
have worked too, and the receipt says this choice was not forced.

## Example 3: from prose to a regime

Prompt: *"Two initial states: alpha has no mark, beta has mark a."*

1. Move the prose into codebook slots: `s0` = "alpha has no mark" ↦ `<>`,
   `s1` = "beta has mark a" ↦ `<a>`.
2. Apply PG2 and PG3 to get a pure regime: `{<>,<a>}`.
3. Check it against the grammar: it conforms.

```text
<<regime><tokens><<ground><>><<occupied><a>>><<codebook><s0><s1>>>
```

**The point.** The prose stays in the codebook. Only the four-glyph wire enters
the regime.

## Mistakes to refuse

| Mistake | What goes wrong | Error |
| --- | --- | --- |
| Alphabet leakage | A character outside `{<, >, a, b}` | `ERR_LEXICAL_ALPHABET` |
| Nested container | `<<>>` breaks flat adjacency | `ERR_NESTING_DISALLOWED` |
| Spontaneous step | Continuing from `<>` with no rule | `ERR_SPONTANEOUS_STEP` |
| Smuggled counting | Treating marks as numbers before any observation allows it | `ERR_UNLICENSED_COUNTING` |
| One-turn certification | Certifying a state from the last step alone | `ERR_ONE_TURN_BLINDNESS` |
| Unique-lift promotion | Presenting one chosen separation as forced | `ERR_UNEARNED_UNIQUENESS` |

## What this does not show

These strategies are a checkable specification. They do not show that a model
finds them unprompted, and they report no model performance.

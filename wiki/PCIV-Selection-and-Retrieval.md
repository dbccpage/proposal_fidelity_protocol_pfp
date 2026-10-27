# Selection and retrieval

Part of [Prompt Civilization](PCIV.md). Previous: [Mutation and inheritance](PCIV-Mutation-and-Inheritance.md) · Next: [Safety and persistence](PCIV-Safety-and-Persistence.md)

This page covers Levels 04 to 07: how prompts are compared, how credit flows
back to ancestors, how a precedent is chosen for a new task, and how the working
population is kept diverse. Every number here is an exact rational, and every
result licenses inspection only.

## Fitness without a single score

`use_cases/fitness.py` measures each prompt on several dimensions, for example
verification pass rate, contract compliance, cost efficiency, precedent reuse
and active descendants. They are never added into one composite number.

**Exact values.** Each dimension is a pair of integers `n/d` with `d > 0`. A
zero denominator is undefined, never coerced to zero. Floats are barred.

**Receipts must match the task (`F-SELECT-03`).** A verifier receipt counts
toward fitness only if its obligation id matches the prompt's declared task
obligation. A verified topology theorem cannot raise arithmetic fitness. A
receipt supplied by the caller, or a body that seals itself, is not success.

**Honest refusals are not failures (`F-RES-06`).** A response that ends in a
certified refusal, or correctly reports an exact obstruction (`phi1 > 0`,
`gamma2 > 0`), counts as compliant. Validity alone earns nothing: an empty
packet or trivial output scores zero progress.

**Comparisons need held-out data (`F-RES-09`).** A comparative claim requires a
held-out split and a correction for multiple comparisons.

### Pareto fronts

`u` **dominates** `v` when `u` is at least as good on every dimension and
strictly better on one. The population is split into fronts: front 0 holds the
undominated prompts, front 1 those dominated only by front 0, and so on. Within
a front, order is a declared, versioned lexicographic tie-break, never a
weighted sum (`F-SELECT-01`).

Prompts with no executions yet are `Unmeasured`. A fixed fraction (1/4) of
front-0 slots is reserved for them, so new mutations get evaluated at all
(`F-SELECT-02`).

## Inverse lineage PageRank

Which ancestors produced useful descendants? Level 05 runs PageRank on the
inheritance graph with edges reversed (child to parent), so credit flows from
offspring back to the prompts they came from:

```text
r_inv = (17/20) · P_invᵀ · r_inv + (3/20) · u
```

`P_inv` is the reversed transition matrix, weighted by how well each child did,
and `u` is the uniform vector. The fixed point is solved exactly over the
rationals by Gaussian elimination, and returned with a paired certificate of the
forward and inverse ranks. Reference edges do not count as offspring.

The rank allocates **inspection budget**. It does not promote anything.

## Precedent retrieval

When a task starts, it asks for relevant precedents. Ranking by raw citation
count rewards whatever came first; ranking by popularity drags general prompts
into specialised formal contexts. Level 06 uses a seven-key lexicographic
order instead:

1. Retrieval eligibility: active only (dormant as a fallback, shelved never).
2. Hard domain eligibility for the query's domain (`F-DOMAIN-01`).
3. Pareto front, front 0 first, including the unmeasured quota.
4. Structural Jaccard similarity over domain atoms.
5. Inverse lineage PageRank.
6. Evaporated usage weight.
7. The canonical prompt id, as the final tie-break.

### Evaporation

Each use of a precedent ages on its own, with a half-life measured in epochs
(`F-BIO-04`). Example: 100 uses at epoch 0, aged by ten half-lives, weigh
`100 / 1024 = 25/256`. One new use at epoch 100 adds 1. The total is
`1 + 25/256 = 281/256`, **not** 101. A fresh use does not rejuvenate old ones.
Evaporation changes only the derived view; the usage history itself is kept.

## Population reserves

An unbounded population exhausts memory; pruning purely by fitness causes
"competitive release", where one specialised variant takes over and the
monoculture collapses when conditions shift. Level 07 caps the retained working
population at `N` and splits it into buckets by **largest-remainder
allocation** (`F-BIO-05`):

| Bucket | Share | Exact quota at N = 10 | Slots |
| --- | --- | --- | --- |
| Front (Pareto-optimal) | 3/5 | 6 | 6 |
| Unmeasured (new mutations) | 1/4 | 5/2 | 3 |
| Baseline (generalists, dormant fallback) | 3/20 | 3/2 | 1 |

Floors give 6 + 2 + 1 = 9; the tenth slot goes to the largest remainder, and the
1/2 versus 1/2 tie is broken in favour of the unmeasured bucket, giving 6/3/1.
The buckets always sum to `N`.

Candidates that do not fit are moved to **shelved**. Their custody is never
changed and nothing is deleted.

## Check your understanding

1. Prompt A scores (pass 4/5, cost efficiency 1/2); B scores (3/5, 3/4). Does
   either dominate? *No: A is better on pass rate, B on cost. Both can sit in
   front 0.*
2. A prompt answers "this system has a nonzero obstruction" and the host
   confirms it. Is that a failure? *No. A correct obstruction report is a valid,
   compliant outcome.*

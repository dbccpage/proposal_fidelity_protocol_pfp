# Test: DFA Minimality Certificates

A challenge about regular expressions. Given one expression, the proposer must return the smallest deterministic finite automaton (DFA) for it, together with a certificate that it is the smallest. Given two expressions, the proposer must say whether they describe the same language: if they differ, by giving a word that one accepts and the other rejects; if they agree, by giving the two minimal DFAs and a state-by-state matching between them. Every claim, including "this is minimal", is checked from short strings the proposer supplies.

## What it tests and why it matters to PFP

"This automaton is minimal" sounds like a claim only an expert, or a rerun of the minimization algorithm, could check. The Myhill-Nerode theorem turns it into two lists of short words:

- **Access words.** For each state `q`, a word that leads from the start state to `q`. This shows every state is reachable.
- **Separators.** For each pair of states `p, q`, a suffix that leads one of them to an accepting state and the other not. This shows no two states can be merged.

If both lists check out and the automaton accepts exactly the expression's language, no smaller DFA exists. The checker only has to run the automaton on the given words.

```python
from c056_dfa_minimization_equivalence.judge_packet.exact_checker import check_exact

case = {"case_id": "d", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "(a|b)*abb"}
answer = {"case_id": "d", "status": "SOLVED", "states": 4, "accept": [3],
          "delta": [[1, 0], [1, 2], [1, 3], [1, 0]],
          "access": ["", "a", "ab", "abb"],
          "separators": {"0,1": "bb", "0,2": "b", "0,3": "", "1,2": "b", "1,3": "", "2,3": ""}}
check_exact(case, answer)
# (True, 'Valid minimal DFA: L(DFA) == L(regex), states reachable and pairwise separated')
# with separators["0,1"] = "b":  (False, "Separator 'b' fails to distinguish (0, 1)")
# with access[0] = "a":          (False, "access[0] = 'a' reaches state 1 instead of 0")
```

Equivalence works the same way. `(a|b)*` and `a*b*` differ, and the certificate is the word `ba`. `(ab)*a` and `a(ba)*` agree, and the certificate is a bijection between the states of their minimal DFAs that fixes the start state, keeps accepting states accepting and commutes with every transition.

The two checkers are written differently on purpose. The exact checker compares languages with Brzozowski derivatives of the expression; the independent checker builds an automaton from the expression by subset construction and compares with the Hopcroft-Karp equivalence algorithm. A wrong answer has to fool both.

## Inputs

64 judge cases over alphabets of up to four letters:

- 32 base cases: the empty language (`#`), the empty word (`%`), all words, fixed suffixes and prefixes, substrings, parity and length conditions, "second (or third) letter from the end is `a`" (whose minimal DFA needs 2^k states for the k-th letter), nested stars, eight equal pairs (commutativity, idempotent star, distributivity and similar laws) and eight different pairs.
- 16 "gauge" cases: the same languages with letters relabelled, the alphabet renamed, harmless rewrites and extra parentheses.
- 16 poisoned cases: two with a note that lies about whether a pair is equal, and 14 malformed inputs (unclosed or unmatched parentheses, a letter outside the alphabet, a leading star, an empty alphabet, a missing key, a non-string expression, an unknown task) that must be refused as `OUT_OF_SCOPE`.

The 48 corrupted answers include redirected transitions, an extra unreachable state, a dropped or added accepting state, wrong access words, a separator that does not separate, malformed tables, `EQUAL` claimed on different languages and the reverse, a word in neither or both languages, and broken bijections.

## How to run

From the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges/c056_dfa_minimization_equivalence -q

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c056_dfa_minimization_equivalence/participant_packet/runner.py

## Expected output

`12 passed`. The runner prints `Result: 14/14 passed`. Both checkers accept all 64 reference answers (50 solved, 14 refused as malformed) and reject all 48 corrupted ones. One test feeds random strings to both expression parsers and checks that they agree with the reference grammar.

## What a failure means

- A separator rejected: those two states may in fact be equivalent, so the automaton is not minimal.
- An access word rejected: a state is unreachable or the transition table is wrong.
- The two checkers disagreeing: one of the two language comparisons has a bug, which is why there are two.

## How to modify it

- Add a case with a new expression; the public examples in `participant_packet/examples` show the format.
- To see the certificate grow, try `(a|b)*a(a|b)(a|b)` (third letter from the end): the minimal DFA has 8 states and needs 28 separators.

## Where it lives

`demos/certified_challenges/c056_dfa_minimization_equivalence`. Moved from the internal challenge suite; imports now use the package name. The script that ran language models on this challenge, and the one test that read that script's prompt, were left behind because they need the unpublished runtime. Model results are in the [findings notes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/findings) with their notices.

See also [Sorting Network Zero-One Principle](Test-Sorting-Network-Zero-One-Principle.md), [Rewrite Normal Form Loss](Test-Rewrite-Normal-Form-Loss.md) and [Core Concepts](Core-Concepts.md).

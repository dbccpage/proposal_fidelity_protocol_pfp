# pilot_0000030 — A normal form can lose the question

Origin: Quiz 18; four related exercises (quiz18.1–quiz18.4).
Deterministic rewrite and retained-original codec checks; no model call.

## Question and result

With rules ab -> d and bc -> e, abc has two irreducible descendants:
dc and ae. Selecting one does not resolve the other branch.

A separately named extended presentation also admits dc -> e and ae -> e.
The displayed peak now joins at e. Every rule reduces length, so every
reduction terminates. This pilot does not run the complete critical-pair
analysis needed for a global confluence conclusion about the extended system.

Under the extended rules, abc and e have the same normal form e, while the
number of occurrences of a in their original inputs is 1 versus 0. That query
cannot be recovered from this common normal form alone. Retaining the original
bytes makes the pair reversible; it does not make its first component lossless.

## Run

From the repository root:

~~~powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000030"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --input word.bin --presentation original
py -3.12 "$pilot/run.py" --input word.bin --presentation extended --max-states 2
~~~

The no-argument command executes all four cases. Custom input is a raw file,
not a JSON string. Input and presentation must be supplied together. The empty
word is allowed; whitespace, Unicode lookalikes and unknown letters are not
trimmed, normalized or repaired.

Outputs go into unique directories under ../pilot_output/pilot_0000030/.
input.bin, result.json, receipt.json and summary.md share the same run. The
receipt binds raw input bytes, runner bytes and the normalized JSON result.
For the worked-case command, input.bin is a mode descriptor; each computed
exploration carries its actual word bytes in input_hex.

Exit 0: worked cases computed or custom exploration complete.
Exit 1: state budget exhausted; retained exploration is incomplete.
Exit 2: input/presentation/budget contract violation or I/O error. Oversized
input is not truncated and claimed as fully retained.

## Bounded domain and evidence

Words use exactly ASCII a,b,c,d,e, length 0–32 bytes. The two presentations are
immutable rule tuples. Every applicable rule at every position is explored,
including overlaps. States and individual rule/offset edges are retained.
The search admits 1–1,024 states, with 1,024 as default. On a cutoff it retains
the rejected next edge as cut_step, marks complete=false and leaves
unique_normal_form=null. normal_forms on an incomplete run is only the
irreducible descendants already observed, not an exhaustive set.

Multiple distinct observed normal forms disprove global confluence by this
one counterexample. A unique normal form for one input does not prove global
confluence; the latter remains NOT_CHECKED. Finite exhaustive test alphabets
are likewise regression evidence, not an all-strings theorem.

The replay function checks every submitted rule, source, offset and target
against the selected presentation. A stopped trace returns its endpoint; it
does not independently claim irreducibility or completeness.

## Retained-original codec

encode(original_bytes, normal_form, presentation) requires a complete bounded
exploration and a reachable, irreducible first component. It produces a local
record containing presentation, normal_form, original_hex and original_sha256.
decode validates the same conditions and digest before returning the original
bytes. It refuses missing originals, altered bindings, fabricated normal forms
and reducible first components.

The round trip uses the retained original by design. No inverse is claimed
for normal_form alone, arbitrary packet languages, or inputs whose search
exceeds the declared bound. The field names describe this pilot's record,
not a new external codec standard.

## Tests

~~~powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$pilot = "omega_engine_woland/tests/pilots/pilot_0000030"
py -3.12 -m pytest "$pilot/tests" --basetemp=scratch/pytest_tmp_pfp_rewrite --cov=$pilot --cov-config="$pilot/.coveragerc" --cov-report=term-missing
py -3.12 -m ruff check $pilot
~~~

Tests include an independently recursive oracle for all 3,906 words of lengths
0–5 in each presentation, multiple-redex examples, stopped searches, graph
edges, forged traces, codec tampering, actual CLI/custody checks, and seven
implementation mutations. The mutations omit branches, silently extend the
rules, overclaim global confluence, lose the protected query, hide a cutoff,
admit a fabricated normal form, or decode from the normal form alone.

Final-location verification: 75 tests passed; 120/121 statements and 19/20
branches covered (98.58% combined); seven implementation mutations killed.
See the [verification files](../pilot_output/pilot_0000030/verification_20261007_r1/)
and [executed worked cases](../pilot_output/pilot_0000030/a2e894cc29d54d8fb6aed082bb9ed81b/).
Candidate and final-location evidence are retained separately.

AuthorityEffect: None. GenesisEffect: None.

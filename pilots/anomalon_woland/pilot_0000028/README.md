# pilot_0000028 — Select the grammar; preserve the bytes

Origin: Quiz 15, four exercises (quiz15.1–quiz15.4).
Deterministic host experiment; no model call or external action.

## Question

Does a named syntax profile recognize the complete submitted document without
trimming whitespace, dropping empty items, discarding a trailing root, or
turning syntactic acceptance into semantic validation?

Four profiles are implemented: mss-boundary-v1, historical-packet-v1,
quiz-packet-v1 and glyph-graph-v1. These names come from the retained grammar
sources; this pilot does not define a new language or standard.

## Run

From the repository root:

~~~powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000028"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --input packet.bin --profile mss-boundary-v1
~~~

The default command runs all four exercises. Custom input is a raw byte file,
not JSON. The exact input is saved as input.bin; each inspection also retains
its hexadecimal bytes and SHA-256 digest. Output directories are unique under
../pilot_output/pilot_0000028/. Result JSON, receipt and summary come from the
same run; the receipt binds the runner, input bytes and normalized result.
It does not bind raw result-file formatting.

Exit 0: worked cases computed or custom syntax accepted.
Exit 1: custom input rejected or declared structural budget exceeded.
Exit 2: invalid CLI pairing, unreadable file, oversized file or output I/O
failure. An oversized file is not truncated and then claimed as fully retained.

## Exact scope

The implementation accepts ASCII documents up to 65,536 bytes, 4,096 parser
nodes and nesting depth 64 (root depth zero). Limits bound this experiment;
they do not make a deeper well-formed EBNF expression syntactically invalid.
LIMIT_EXCEEDED is distinct from syntax refusal.

The local AST is declared here, not claimed as an existing runtime API:

- Boundary nodes: difference, atom (literal word), composite (ordered children).
- Historical nodes: difference, atom, application (ordered children, possibly
  empty). An opcode-looking atom remains an atom.
- Quiz nodes: message, word, tag, packet and root refusal_code. Nested ref<7>
  is a generic tag; the root ref form alone limits codes to 1–6.
- Graph items retain order and duplicates. Edges retain literal spelling,
  direction and weight suffix alongside source/target orientation. A weight
  suffix is a string, not an inferred numerical weight.

Every inspection leaves interpretation NOT_CHECKED and authority_effect None.
A separately proposed repair retains both byte strings and is never applied.
Seal checks distinguish a 64-character lowercase-hex shape from recomputing
the bound artifact's digest. Neither operation validates a theorem or grants
permission.

## Tests and provenance

~~~powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$pilot = "omega_engine_woland/tests/pilots/pilot_0000028"
py -3.12 -m pytest "$pilot/tests" --basetemp=scratch/pytest_tmp_pfp_profiles --cov=$pilot --cov-config="$pilot/.coveragerc" --cov-report=term-missing
py -3.12 -m ruff check $pilot
~~~

The suite contains 75 retained profile-conformance cases, 20 additional
reviewer fixtures, seeded comparisons against an independent EBNF-subset
recognizer, explicit byte/depth/node limits, real CLI/custody checks and four
implementation mutations. The defects trim input, accept a prefix, drop empty
graph entries, or allow a trailing newline after a digest.

Grammar snapshots live under tests/grammars. Boundary grammar originated at
omega_engine_education/code/python/domain/boundary.ebnf; the other three came
from this PFP collection's grammar directory. The 75 cases are the four-profile
subset of grammar/conformance_cases.json. The reference tokenizer and Grammar
class were retained from grammar/check_grammars.py without its unrelated
runtime adapters; this is that tool's documented EBNF subset, not all ISO EBNF.
Text snapshots normalize line endings for portable tests.

Final-location verification: 116 tests passed; 190/191 statements and 35/36
branches covered (99.12% combined); four implementation mutations killed.
See the [verification files](../pilot_output/pilot_0000028/verification_20261006_r1/)
and the [executed worked cases](../pilot_output/pilot_0000028/9105385a6aec4caa866a72e3a7502282/).
The evidence covers run.py, not the production runtimes or all possible
strings in an unbounded grammar.

AuthorityEffect: None. GenesisEffect: None.

# Grammar contracts

**AuthorityEffect: None. GenesisEffect: None.** Select a profile before parsing.
Every start below consumes one complete input. Syntax acceptance supplies no
mathematical witness, level activation, fidelity judgment or execution permission.

## Retained profiles

| Profile | Canonical EBNF / start | Implementation and scope |
|---|---|---|
| `mss-boundary-v1` | [`../python/domain/boundary.ebnf`](../python/domain/boundary.ebnf) / `packet` | [`parse_boundary`](../python/domain/rewrite.py): ground, atom or packet-only composite. The checker reads the existing receipt-bound EBNF directly. |
| `historical-packet-v1` | [`historical_packet.ebnf`](historical_packet.ebnf) / `packet` | Existing [tower parser](../../../omega_engine_pfp/domain/tower/grammar.py): ground, atom or `op<…>` application. Opcode/arity/activation checks follow parsing. |
| `pkt00-k0-v1` | [`cycle_repair.ebnf`](cycle_repair.ebnf) / `cycle_repair` | Rendered K0 candidates from the [cycle transcoder](../python/infrastructure/mssn_transcoder.py). Fixed incidence, dimensions, field order and claim literals; runtime also checks edge uniqueness, integer range and diagnostic overflow. |
| `quiz-packet-v1` | [`quiz_packet.ebnf`](quiz_packet.ebnf) / `quiz_message` | Teaching `ask`, `ans`, `ref` packets. Tested syntax specification; the legacy quiz helper is not a conforming parser. |
| `glyph-graph-v1` | [`glyph_graph.ebnf`](glyph_graph.ebnf) / `glyph_graph` | Quiz 11/13 single-glyph vertices and edges. Tested syntax specification; graph filling and mathematical checks are separate. |
| `ddc-tape-shape-v1` | [`ddc_trace.ebnf`](ddc_trace.ebnf) / `ddc_trace` | Quiz 09 tape shape. Repeated C is allowed; event-state replay and licensing are outside this language. |

`Sigma36` is ASCII `a-z0-9`; `Gamma38` adds `<` and `>`. Graph arrows also use
these glyphs but do not form boundary packets. Punctuation, layout and underscores
are accepted only by the profile that explicitly includes them.

## Source and wire boundaries

Boundary, historical, quiz, graph and tape inputs are checked byte for byte:
no trimming, fence extraction, comment removal, guessed profile or accepted suffix.
`<a><b>` is two packets and fails both single-packet parsers.

PKT-00 is a source format. Its sole checked-in example is
[`cycle_balance/00_genesis_cycle_balance_wire.mssn`](../cycle_balance/00_genesis_cycle_balance_wire.mssn).
The fixture reader removes `#` line comments only for explicitly declared source
paths. Raw conformance cases receive no preprocessing. The EBNF covers the
transcoder's rendered form; its source adapter also accepts some other layout,
such as spaces between vector entries. That adapter's result must render back
into the declared grammar and preserve the parsed four-object suite on replay.
This round trip applies to suites produced by the parser, not arbitrary external
verifier or receipt metadata.

The grammar fixes K0's 4 vertices, 5 edges, 1 existing face, incidence matrices,
5-entry obstruction/repair columns and 2-entry preimage. It rejects unknown edge
names, missing or reordered clauses, empty numeric fields, leading zeros and
negative zero. Carrier/face labels are identifiers; relabeling cannot change the
pinned incidence. Duplicate edges and out-of-range integers remain well-formed
syntax but are rejected by the runtime. A false preimage can still parse:
`qed<exact>` is a submitted claim, and parsing must leave the receipt `UNVERIFIED`
with no terminal decision or exact witness.

## EBNF convention

The retained files use `,` for concatenation, `|` for alternatives, `[]` for
optional syntax, `{}` for repetition, `()` for grouping and `(* … *)` for grammar
comments. Quoted terminals use JSON-style escapes. There is no implicit input
whitespace. There are no external productions or unspecified payload fallbacks.
This is a small documented subset, not a full ISO 14977 implementation.

[`check_grammars.py`](check_grammars.py) is a development recognizer for trusted,
bounded fixtures. It checks defined/unique productions and full consumption;
it is not a production intake parser, ambiguity proof or resource governor.
The boundary runtime separately limits input to 65,536 bytes, 4,096 nodes and
depth 32 (root depth 0). Other profiles do not inherit those limits.

## Verification

From the repository root, Python 3.12 or later:

```sh
python ow/omega_engine_pfp_v0.2/grammar/check_grammars.py
python ow/omega_engine_pfp_v0.2/grammar/check_grammars.py --runtime
```

The default run needs only the standard library. `--runtime` also needs Pydantic 2
for the existing boundary module. It compares all declared boundary, historical
and PKT-00 cases with their real parsers, replays the historical golden corpus,
checks boundary budget edges and verifies accepted PKT-00 round trips and
unverified receipt fields. Quiz/graph/tape cases are specification checks only.

[`conformance_cases.json`](conformance_cases.json) records `profile`, `text` and
`accept` for each unique case ID. PKT-00 may additionally declare `runtime_accept`
when a source-layout or semantic restriction intentionally differs from the
rendered syntax. The checker rejects unknown profiles, undeclared grammar/source
files and profiles without both positive and negative cases. Add or rename a
source fixture only together with its explicit `SOURCE_STARTS` declaration.

## Retired drafts and migration

The cleanup closes this directory around the six contracts above:

| Removed surface | Replacement |
|---|---|
| Mixed `mssn.ebnf`, including stream/opcode/number sub-starts | Select the canonical boundary, historical or K0 entry above. Numeric codecs and opcode typing stay with their existing owners. No stream entry is published. |
| `pure_mss_packet` and five `level_*.mssn` examples | The atlas remains curriculum/presentation material. No tagged all-level parser or evaluator is claimed here. Ground/atom examples remain in the conformance corpus. |
| `pfp.ebnf` and its duplicate `symgame_v0.n.ebnf` | The unimplemented directional-envelope draft is retired. Current [Gate 01](../python/use_cases/gate_01_syntax_and_schema.py) uses JSON extraction and schema checks, not that angle-bracket envelope. |
| Duplicate `00_terse_wire_packet.mssn` | The existing packet fixture linked above. |

Retired drafts can be recovered from [PR 495](https://github.com/dbccpage/the_symbol_game/pull/495)
and Git history. They are not retained as compatibility grammars. No runtime
parser, pinned boundary grammar or receipt digest definition changes in this
refactor. Broader atlas semantics and old teaching-helper findings remain outside
these syntax contracts. The dated quiz review was removed with `5_quizzes_and_puzzles`. Recover it from git history. Plan acceptance `P07` requires each removed artifact to become its own pilot.

The [MSS-N research paper](../../../../omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/paper.md)
explains how to choose and interpret these formats.

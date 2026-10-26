<div align="center">

# PFP VI: Retained Failure Evidence and Controlled Reuse

Jeremy H. Carroll\
2026-10-02 · Version 0.1.0 · Systems methods paper · Author-review revision

</div>

Code baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

## Abstract

A rejected proposal can explain a defect, reveal a mistaken assumption, or supply
a useful negative test. Keeping it also creates new obligations: the record must
remain interpretable, its integrity must be checkable, and future reuse must not
turn rejection into authority. This paper examines those obligations in the
Proposal Fidelity Protocol (PFP), previously called the Symbol Game. The
implementation contribution is a source-audited JSONL failure ledger that
records structured refusals, chains entry digests, verifies restart state, and
emits a count-and-head receipt. We describe exactly which modifications its
checks detect and why an independently retained anchor is needed when an
attacker can rewrite the whole file. A worked two-record example separates
local replay, snapshot comparison, and authorized retention. We then specify a
controlled reuse procedure using existing detector checks for benign examples,
false-suppression thresholds, invalid patterns, and affinity decay. A retained
catalog of 61 harvested detector candidates is described only as a data file;
no code at the audited commit applies its fixtures. The record store is
logically append-only through its API; it does not provide immutable media,
authenticated provenance, concurrent-writer safety, or a power-loss durability
theorem. No improvement in model accuracy, cost, or discovery yield is inferred
from retaining records.

## 1. Why preserve a failed attempt?

Suppose a candidate code patch edits a protected file, or a proposed
mathematical witness refers to the wrong carrier. A host refuses the transition.
If the refusal is recorded only as “failed,” the next investigator cannot tell
which proposal was evaluated, which condition failed, or whether the same
failure has already been reproduced.

A useful failure record keeps enough authorized information to reconstruct the
attempt. That record can support a regression test and a later comparison of
detectors. It is still evidence about an event. It does not establish that the
proposal is false under every interpretation, or that a recurring phrase is a
reliable detector of future errors.

This paper contributes a concrete storage contract, a retained-anchor
integrity argument, and a bounded procedure for promoting a stored example into
a proposed reusable rule. The procedure distinguishes three actions: retaining
an event, reproducing its failure, and admitting a detector for a declared
scope. None of these actions follows automatically from the previous one.

The audited implementation is fixed at commit
`52cb5457f6c485ba548cfd292f6012a941ed22cf`. The main sources are
[`CemeterySink`][sink], its [domain record types][entries], and the
[storage regression suite][sink-tests]. The inherited “cemetery” name means a
store for rejected attempts. The concrete data structure is an ordered
predecessor chain with a header, not a general graph of arbitrary dependencies.

## 2. Related work and the threat being addressed

Secure audit logging has long distinguished ordinary local logging from logs
designed to retain protections after the logging machine is compromised.
Schneier and Kelsey's construction explicitly addresses compromise and uses
cryptographic mechanisms beyond an unkeyed local digest chain. The current PFP
store does not implement that construction or inherit its security properties.
[Schneier and Kelsey, 1999][secure-logs]

Certificate Transparency specifies signed tree heads and Merkle inclusion and
consistency proofs for a public logging setting. Those mechanisms provide a
useful reference for identifying what a local count-and-head record omits:
signed producer identity, public witnesses, and a protocol for comparing log
views. The PFP store is not a Certificate Transparency log.
[Laurie, Messeri, and Stradling, 2021][ct]

Reflexion uses remembered linguistic feedback to guide later attempts. PFP's
retained failure records can be inputs to a future feedback experiment, but
record integrity and improved reasoning are different experimental questions.
The present paper studies the former contract and proposes constraints on
reuse. [Shinn et al., 2023][reflexion]

The immediate threats are accidental mutation, partial truncation, stale
records, and inconsistent reconstruction. A stronger adversary may rewrite
both the entries and the local header. A still stronger adversary controls the
application and any separately retained anchors. Each level needs an explicit
interpretation; a checksum alone does not resolve them all.

## 3. What the store records

`record_refusal` accepts a turn envelope, a refusal reason, optional prompt
parameters, and an optional cochain projection. It normalizes supported values,
assigns an index and timestamp, and hashes the payload together with the
previous entry digest. Fractions are serialized into rational strings in this
storage path. The following fields are central:

| Field | Meaning and limitation |
| --- | --- |
| `entry_index` | Nonnegative position in the ordered chain |
| `turn_envelope` | Supplied proposal context; not independently authenticated by storage |
| `refusal_reason` | Nonempty text identifying why the caller recorded the event |
| `prompt_parameters` | Retained parameters supplied by the caller |
| `cochain_projection` | Supplied structured values; not a native calculation performed by the sink |
| `prev_digest` | Commitment to the preceding entry, or the genesis marker |
| `entry_digest` | SHA-256 of the normalized entry payload |
| Fixed marker field | Must hold the string `None`; any other value is rejected when an entry is created or reloaded |

Each payload also carries a record type and the assigned timestamp. A header
records the entry count and current head digest. The exported `TailReceipt`
contains those two values, a schema identifier, the same fixed marker, and a
SHA-256 digest over those four values. The sink can check consistency of its
entries; it cannot determine whether the caller honestly described an external
event.

This distinction matters for mathematical values. A caller can store
`{"phi1": "0"}` as text. Its presence and hash do not make it a native
functional measurement. A record intended to support such a claim must also
identify the actual verifier, input bytes, output bytes, and source/binary
bindings, and a separate evaluator must check that relationship.

The store does not enforce a general data-handling policy. The caller must
decide which prompts, responses, and parameters it is authorized to retain
before calling it. Rejection is not a retention license. Sensitive fields
should be excluded, transformed, or handled by an appropriate authorized
storage mechanism. A redacted record can support only the evidence claim that
its remaining information permits.

## 4. Logical append and physical persistence

The public API adds entries in increasing order. Physical persistence is
different: `_write_file` serializes the header and all retained entries to a
temporary file, then replaces the destination with `os.replace`.
Consequently “append-only” describes the API's logical history. The file is
rewritten on every append.

This design is simple to inspect and supports restart verification, but has
clear operational limits. It retains the entries in memory, writes the
accumulated contents again, and provides no concurrent-writer lock. Two
independent writers can operate from stale snapshots and interfere through the
same temporary path. There is no explicit `fsync` call in this path. Process
restart tests therefore do not demonstrate persistence through every power
failure or storage-device fault.

The encoding helper uses ordinary compact `json.dumps` with sorted keys.
Its docstring calls that RFC 8785, but the implementation does not establish
the full serialization and Unicode rules required by that specification.
This paper calls it the sink's sorted-JSON encoding and binds its source.
Interoperability claims require tests against the actual profile and supported
value domain. [RFC 8785][jcs]

The returned record is a frozen dataclass, but nested mappings are not thereby
made transitively immutable. Consumers should reconstruct evidence from
verified persisted bytes and avoid treating an in-memory tuple of records as
an immutable storage medium. These limitations do not invalidate a scoped
restart check; they define its scope.

## 5. A retained-anchor integrity argument

Let P_i be the normalized payload of entry i, including its predecessor digest,
and let h_i be SHA-256 of that payload's encoded bytes. The header claims a
length n and a head h_(n-1). Verification reparses each entry, checks its index
and predecessor link, recomputes h_i, and compares the resulting count and head
to the header. Empty or inconsistent files produce typed integrity or
truncation errors.

Under the assumptions that the encoding is deterministic for admitted values,
the parser checks the relevant fields, and a changed payload cannot be made
to collide with the expected digest, changing a protected entry payload while
keeping its original downstream anchor is detectable. Reordering or removing
an interior record also breaks an index, predecessor link, or the expected
head. This is a conditional integrity argument, not a formal verification of
all parser and filesystem behavior.

The location of the anchor matters. If an attacker removes the last record
but leaves the header unchanged, the local count/head comparison detects
truncation. If the attacker rewrites the header to match a shorter consistent
prefix, that prefix can pass local verification. If the attacker rewrites
every entry and recalculates every digest, local self-consistency can also
hold.

Retaining a prior `TailReceipt` independently enables a caller to ask whether
a reconstructed file has the same ordered normalized-entry count and head.
It does not establish raw-file or complete header identity. For example, the
sink normalizes a refusal reason through `str`, so the JSON number `42` and
string `"42"` can produce the same protected payload; header genesis metadata
and unknown header fields are not committed by this comparison. A caller
requiring exact file bytes must retain and check an independent raw-file
digest as well. The current sink exposes the receipt, but it does not
automatically retrieve an independently trusted copy or perform a signed
freshness protocol. The consumer must preserve the anchor and compare count and
head. A valid later extension intentionally has a different head; proving
ancestry of that extension requires inspecting the chain against the retained
prefix. Unequal heads alone show only that the two snapshots differ.

The same boundary applies to dates. A timestamp records a value written by
the application. The store does not authenticate a clock or prove that the
event happened at that time.

## 6. Worked example: two refusals and three modifications

Use a fresh writable directory and synthetic, nonsensitive data. The following
example calls the actual storage API:

```python
from pathlib import Path
from omega_engine_pfp.infrastructure.persistence.cemetery_sink import CemeterySink

path = Path("fresh-failure-ledger") / "failures.jsonl"
sink = CemeterySink(path)
sink.record_refusal(
    {"task_id": "toy-1", "candidate": "edit README.md"},
    "PROTECTED_PATH",
    prompt_parameters={"transport": "scripted_fixture"},
)
sink.record_refusal(
    {"task_id": "toy-1", "candidate": "use an absent route"},
    "NO_NATIVE_PORT",
    prompt_parameters={"transport": "scripted_fixture"},
)
anchor = sink.emit_tail_receipt()
reopened = CemeterySink(path)
observed = reopened.emit_tail_receipt()
assert (observed.entry_count, observed.head_digest) == (
    anchor.entry_count, anchor.head_digest
)
```

The example compares the normalized-entry snapshot after reopening; it does not
run a code ownership checker or native route. The refusal reasons are
deliberately constructed labels. A real campaign must bind the host decisions
from which those reasons were derived. Timestamp-dependent digests are obtained
from execution, not hardcoded in the manuscript.

In the first modification, change `PROTECTED_PATH` in the first persisted
entry while leaving its digest unchanged. Reopening rejects the changed payload
with `LedgerIntegrityError`. In the second, delete the final entry while
retaining the original header. Reopening rejects the count/head discrepancy
with `LedgerTruncationError`. The [storage tests][sink-tests] contain these
classes of restart and tamper checks, along with extra-key, malformed UTF-8,
invalid-count, and fixed-marker cases.

In the third modification, construct a complete internally consistent shorter
file. It reopens without error, so local integrity is no longer enough. A
caller comparing its count and head with the independently held two-entry
anchor can observe that the file does not match the retained snapshot. The anchor must actually be held outside
the rewriting adversary's control; saving it beside the file under the same
untrusted custody does not provide that assumption automatically.

This example is small enough for a new reader to inspect every record. It also
shows why the useful output is a specific comparison, such as “these entries
match this retained snapshot,” rather than a blanket claim that the storage is
immutable.

## 7. From a retained event to a reusable detector

A proposed reuse pipeline starts with a query over retained records, groups
events by a declared key, and selects candidates for reproduction. Grouping by
a digest establishes byte identity. Grouping by a normalized feature or
presentation key establishes only that chosen equivalence relation. Semantic
equivalence needs a separate checker.

The next step reproduces the failure using the original input and checker
bindings. A failure caused by missing infrastructure must remain a missing
infrastructure case. It should not become a detector that declares similar
mathematical witnesses invalid. If the original bytes were not retained under
policy, record the replay limitation rather than filling them in from memory.

A reproduced defect can become a proposed rule. The rule is tested on the
failing case and on valid near misses before any enforcement action is
considered. Its provenance includes the source records, predicate, fixture
bank, permitted action, and scope. Reuse is a new evaluation event, with a new
receipt. The current sources supply individual checks for this process; this
paper does not claim an integrated automatic miner with measured discovery
yield.

The [clonal-selection module][clonal] illustrates one such check. It compiles a
candidate regular expression and compares it with benign self-panel examples.
A matching clone produces a kill-condition record naming both clone and
parent. An invalid expression returns `INVALID_MATCH_PATTERN`; a Boolean
“not killed” value must not be misread as admission when that refusal is
present. A clean result means only no match on the supplied panel.

The [self-panel regression][immune-tests] identifies 40 distinct base contents
inside 1,000 stored examples. A publication must report that effective
diversity, rather than presenting synthetic repetitions as independent coverage.
Adding new domains needs new valid examples and a renewed check.

### 7.1 The retained detector-candidate catalog

The repository retains a JSON file of harvested detector candidates,
[`_intelligence/_antibodies/pharmacy_catalog.json`][catalog]. Its inherited
name, pharmacy catalog, is a label for a file of records; the file is not an
active filter. At the audited commit it holds 61 entries with 14 distinct
`failure_class` values. Its `pharmacy_status` field is `candidate` for 56
entries and `active` for 5.

| `failure_class` value | Entries | `pharmacy_status` |
| --- | --- | --- |
| `defect:defect:0` to `defect:defect:4` (five classes) | 9 each, 45 in total | candidate |
| `defect:h_boundary` | 4 | candidate |
| `general_obstruction` | 3 | candidate |
| `architecture:clean_arch_inward_dependency_violation` | 3 | candidate |
| `architecture:circular_dependency` | 1 | candidate |
| `algebraic_defect:energy_projector_sign_inversion` | 1 | active |
| `algebraic_defect:minimizer_bitmask_convention_inversion` | 1 | active |
| `resource_exhaustion:reasoning_trace_exceeds_completion_window` | 1 | active |
| `syntax_error:unterminated_string_literal` | 1 | active |
| `type_error:unsupported_operand_int_and_list` | 1 | active |

Each entry has 15 fields, including `negative_fixture`, `positive_fixture`,
and `evidence_sha256`; every entry has all three. The fixtures are short
strings. In 49 entries they are placeholder comments: a `# Triggering defect:`
line that repeats the defect label, and `# Repaired exact state`. The other
12 entries hold a descriptive phrase or a code fragment of at most four lines.
The file binds no fixture to a checker, to input bytes, or to a test that
reproduces the failure, and it records no reproduction or near-miss result.

Each `evidence_sha256` value is a distinct 64-digit hexadecimal SHA-256 digest.
The file does not record which bytes a digest covers or which code wrote an
entry. The two harvesting implementations at the audited commit hash short
identifying strings: [one][seeder-run] joins the defect label with the run and
task identifiers, and [the other][seeder] also prefixes the entry identifier.
For 19 entries, namely 15 of the `defect:defect:N` entries and the four
`defect:h_boundary` entries, the stored value equals the SHA-256 of the defect
label joined with a run identifier and task identifier that appear in run
records retained at that commit. None of these inputs is a reproduction receipt.
As with the head digest in Section 5, such a value supports comparison only
against an independently retained anchor. It does not make an entry immutable,
and it does not show that a reproduction exists.

No code at the audited commit matches incoming proposals against these
fixtures, executes a fixture, or derives a repair from a positive fixture. The
nearest code found, a [prompt-diagnosis service][prompt-doctor], tests whether
an entry's `target_pattern` occurs as a substring of a prompt; it reads neither
fixture. The counts above therefore describe the file. They are not measures
of detector coverage or effectiveness. Admitting any entry as a detector would
require the reproduction and near-miss steps described above.

## 8. Monitoring overactive rules and decay

The [regulatory supervisor][treg] computes a toxicity index from trigger
records. With the explicit trigger interface, each supplied record states
whether the rule's pattern matched and whether the second signal of the
two-signal gate was also present. The index is the number of pattern-only
records divided by the number of supplied records. At the default threshold
1/5, toxicity at or above the threshold synthesizes a downgrade to
`DIAGNOSTIC_ONLY`. Five records containing one pattern-only case give exactly
1/5 and therefore meet the threshold. One such case among six gives 1/6 and
remains below it.

These are policy arithmetic, not an estimated population false-positive rate.
The trigger labels must themselves be justified. A different input interface
using an unlabelled prompt corpus has different information available: every
match counts as pattern-only, so the score is 0 when nothing matches and 1
otherwise. That score cannot be substituted for an oracle-labeled error rate.
The regression suite makes this distinction observable.

Affinity decay provides another bounded mechanism. For idle count t and
positive interval tau, the implementation halves a rule's score once for each
newly completed interval: a call that moves the idle count from t to t' applies
the factor (1/2)^k with k = floor(t'/tau) − floor(t/tau). Twelve idle runs with
tau=5 multiply the starting score by 1/4, whether recorded in one call or
batches of 3, 4, and 5. This batching invariance follows from telescoping the
differences of completed interval counts and is checked by the tests. Activity
expiry is a separate policy: the rule is marked inactive once its idle count
reaches its configured `half_life_runs` value.

Neither thresholding nor decay establishes that a rule improves reasoning.
They regulate a proposed detector repertoire. Effectiveness and safety require
the held-out, independently labeled experiment specified in PFP III. A retained
failure can be valuable for diagnosis even when the proposed detector derived
from it is rejected.

## 9. Reproducibility and evidence classification

Collect and run the focused suites from the root of a full repository checkout,
using Python 3.12 (on Windows, `py -3.12` in place of `python`):

```powershell
python -m pytest omega_engine_pfp/tests/test_cemetery_sink.py --collect-only -q
python -m pytest omega_engine_pfp/tests/test_cemetery_sink.py -q
python -m pytest omega_engine_pfp/tests/test_immune_defect_regressions.py --collect-only -q
python -m pytest omega_engine_pfp/tests/test_immune_defect_regressions.py -q
```

The first suite tests the production sink; the second targets concrete rule
maintenance defects and boundary cases. Use an explicit writable temporary
location where required. Record commands, exits, interpreter, source hashes,
and exact test outcomes. No provider call or model download is required for
these focused checks.

The package test `code/tests/test_006_worked_example.py` executes the Section 6
block as printed, the three modifications described there, and the
number-versus-string reason case from Section 5 against the repository sink.
It needs the full repository checkout and skips, stating that reason, when the
sink source is absent. It writes ledgers only under pytest's temporary
directory. The package test `code/tests/test_006_catalog_file.py` recomputes
the Section 7.1 counts, fields, placeholder fixtures, and digest
reconstructions from the catalog bytes read through Git at the audited commit.
It needs the full repository checkout with that commit and a `git` executable,
and skips otherwise.

The paper-local `code/tests/test_006_epistemic_immune.py` defines independent
toy classes. It is retained as an educational illustration and is not evidence
that the production sink or immune pipeline behaves the same way. Its copied
positive/zero-defect rule also differs from the actual two-signal gate. It
must not supply production integration counts.

Current execution receipts must identify which checks actually ran.
Historical receipts and stored outputs remain historical. A successful restart
test establishes the exercised process/reconstruction behavior; no
crash-consistency, power-failure, or concurrent-writer campaign is claimed.
There is also no empirical corpus of mined conjectures presented as a
validated result in this paper.

## 10. Limitations and next experiments

The storage implementation is suitable for bounded, inspectable local runs
with a single writer and controlled custody. Its trust boundary is too weak
for claims of permanent immutable retention or authenticated multi-party
logging. Source inspection also identifies a naming mismatch between the
sorted-JSON encoder and RFC 8785; interoperability should be resolved before
using a different implementation as a verifier.

The proposed reuse procedure has meaningful unresolved work: retain anchors
under an explicit trust policy, bind actual host decisions into entries,
demonstrate a deterministic reproduction path for each mined case, and measure
rule behavior on independent valid near misses. Any future integrated miner
must report both useful discoveries and harmful suppressions under a frozen
evaluation plan.

The practical result is narrower and useful: a failed attempt can become an
inspectable, source-bound research object. Preserving that object supports
reproduction and review while leaving its mathematical meaning and future
utility open to independent evaluation.

This paper assigns no authorization and changes no jurisdiction. It carries no
operational authority or institutional standing.

## Verification for this revision

The package verifier (`verify_deposit.py`) checks the manifest and the two-way
file census, and `tools/rebuild_release.py --check` checks the release archive
against both manifests. The package tests and lint are executed by the dated
review receipt recorded with this revision; that receipt lists each command,
tool version, exit status, and tested scope. Historical receipts in this
package keep their original dates and scope and are not current execution
evidence.

## References

- Schneier, B., and Kelsey, J. (1999).
  [Secure Audit Logs to Support Computer Forensics][secure-logs].
  ACM Transactions on Information and System Security 2(2), 159–176.
  DOI 10.1145/317087.317089.
- Laurie, B., Messeri, E., and Stradling, R. (2021).
  [Certificate Transparency Version 2.0][ct]. RFC 9162 (Experimental),
  Internet Engineering Task Force, December. DOI 10.17487/RFC9162.
- Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., and Yao, S.
  (2023). [Reflexion: Language Agents with Verbal Reinforcement Learning][reflexion].
  arXiv preprint arXiv:2303.11366, version 4.
- Rundgren, A., Jordan, B., and Erdtman, S. (2020).
  [JSON Canonicalization Scheme (JCS)][jcs]. RFC 8785 (Informational),
  Internet Engineering Task Force, June. DOI 10.17487/RFC8785.

Implementation links throughout the paper bind the storage and detector claims
to the stated source baseline. They do not replace independently retained
execution or integrity anchors.

[secure-logs]: https://www.schneier.com/academic/archives/1999/05/secure_audit_logs_to.html
[ct]: https://www.rfc-editor.org/rfc/rfc9162.html
[reflexion]: https://arxiv.org/abs/2303.11366v4
[jcs]: https://www.rfc-editor.org/rfc/rfc8785.html
[sink]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/infrastructure/persistence/cemetery_sink.py
[entries]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/domain/entities/cemetery_entry.py
[sink-tests]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/tests/test_cemetery_sink.py
[clonal]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/domain/immune/clonal_selection.py
[immune-tests]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/tests/test_immune_defect_regressions.py
[treg]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_pfp/domain/immune/treg.py
[catalog]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/_intelligence/_antibodies/pharmacy_catalog.json
[seeder]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_operations/domain/symbol_game_bridge/pharmacy_seeder.py
[seeder-run]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_woland/domain/immune/seeder.py
[prompt-doctor]: https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/omega_engine_external_application/prompt_doctor/use_cases/repair_service.py

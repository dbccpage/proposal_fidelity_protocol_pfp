# Instructor key: Paper 004 theoretical minimum

Instructor key for v0.1.0. Keep this separate from the student guide. These answers concern the declared finite problems and named interfaces. They do not supply a native execution receipt or learner-study result.

## Round 1

1. `ab` and `ba` have different byte sequences; length carries no digest-equality guarantee. Under the encoding and cryptographic assumptions, matching an independently retained expected digest supports an integrity comparison with the committed representation. It does not establish mathematical truth, producer identity, source-to-binary provenance, freshness, or operational admission. Digest equality is not an unconditional mathematical proof that two arbitrary byte strings are identical: collision assumptions matter.
2. Execution: `EXECUTED_REPLAYED_EXACT_LAB_EVIDENCE`. Admission: `Refused`. Codes: `PRIME000_CONFORMANCE_PARTIAL`, `UNSIGNED_LAB_ATTESTATION`. The exact zero summaries and replayed candidate relation concern the finite calculation. Admission concerns additional policy/evidence obligations; it remains refused. Three conformance laws are unchecked and attestation is `unsigned_lab`.
3. Tagged encoding preserves type information, so integer and string images differ. A parser or consumer may apply different arithmetic, validation or comparison rules to the two values. Erasing their distinction can bind ambiguous data to one apparent identity.
4. The face set, face operator `d1`, closure problem and carrier manifest change. For this before vector, the remaining face sum is 7 rather than the pair of sums 7 and 5. Recomputing the outer request ID cannot repair a mismatch with the old expected carrier manifest/hash. The restricted host must refuse `CARRIER_MANIFEST_MISMATCH` after rebuilding the declared carrier's manifest.
5. No. `OMEGA_SYMBOL_GAME_HOST` selects through the host seam; the graph tutorial needs `OMEGA_FUNCTIONAL_GRAPH_BIN` and `OMEGA_FUNCTIONAL_GRAPH_SHA256`. An adapter name is discovery information. It is not configuration of the other binary, a digest comparison, an executed calculation, or a verified result.
6. Warranted: named local Lean declarations and their reported axiom dependencies concern the source statements in those modules, subject to successful replay with the pinned toolchain. Unwarranted: the census proves the native host's correctness; or it establishes an end-to-end correspondence between every Python object, Rust action and exported receipt field. A topology lemma is not a test of transport serialization.

## Round 2

7. `d0f=(-2,0,2,1,1)`; residual `(5,2,0,0,0)`; unit-weight L1 cost 7. This is a feasible potential, so `Phi1≤7`. Optimality needs a lower bound valid for every potential.
8. Use `y=(1,1,1,0,0)`. At vertex 0, outgoing 01 and incoming 20 cancel; at 1, incoming 01 and outgoing 12 cancel; at 2, incoming 12 and outgoing 20 cancel; vertex 3 has zero flow. Thus `d0ᵀy=0`; every `|y_e|≤1`; `y·c=7`. For any potential `g`, `Σ|c-d0g|≥y·(c-d0g)=7`. Together with question 7, `Phi1=7`. Check orientation signs; changing one edge's direction requires changing the corresponding circulation coordinate.
9. Face 012: `3+2+2=7`. Face 013: `3+1+1=5`. Gamma2=`|7|+|5|=12`. The face-boundary vectors `(1,1,1,0,0)` and `(1,0,0,1,1)` are independent. The connected graph's cycle-space dimension is `E−V+1=2`, so they span it. Under the declared solve, no first-cohomology direction remains in the final normal form. The original `c` is not a gradient: gradients telescope to zero on each cycle, while `c` has nonzero cycle sums. Do not confuse the solver's final normal form with an arbitrary gauge change of the original data.
10. The cycle sum is 3. For penalties `(1,2,2)`, cost is at least `min(a)·|3|=3`; residual `(3,0,0)` attains it. Projected cochain `c-r=(-2,1,1)` sums to zero. An attaining potential in vertex order is `(0,-2,-1)`. The cheapest edge is unique, so the residual/projected cochain is unique; potentials differ by an additive constant. With unit penalties, residuals `(3,0,0)` and `(0,3,0)` are distinct, both have sum 3 and cost 3. Uniqueness fails.
11. Composed UTF-8 is `c3 a9`; decomposed UTF-8 is `65 cc 81`. NFC sends both to the composed string. RFC 8785 preserves supplied Unicode string data; its primitive/sorting rules also differ from the tagged helper. The function name and visually identical output establish no standards-conformance claim.
12. Recomputing the root demonstrates consistency between an edited record and that newly supplied unkeyed root. It does not demonstrate a fresh replay or authenticated producer. Nor does it fulfill admission requirements. Comparison against a separately retained original root can detect an edit; replacing that anchor defeats this particular comparison. The host's internal solve/replay evidence is a separate object and event.
13. Products: `d0=2048×512=1,048,576`; `d1=1×2048=2,048`; augmented=`2048×513=1,050,624`; closed-system=`1×513=513`. The augmented matrix exceeds the cell ceiling, so the carrier fails the preallocation fence despite satisfying every individual dimension limit. The host returns `RESOURCE_FENCE_EXCEEDED` before allocating the fenced matrices. Timeout metadata alone cannot kill a process; enforce a deadline in the process owner and record a timeout as such.
14. `"0"` and `"-7"` are minimal signed i128 strings and are permitted. `"+7"` and `"007"` are nonminimal encodings of 7; `"-0"` is a nonminimal encoding of 0; `"1/2"` is not an integer string. Their inclusion in the before vector causes `BEFORE_RESIDUAL_INVALID`; in the candidate vector, `CANDIDATE_RESIDUAL_INVALID`, assuming earlier checks pass. `BigRational` internally does not widen these restricted wire fields. Any purported dispatcher alternative must name its own action/input contract.

## Final challenge rubrics

15. One valid construction copies an outcome, changes a claimed exact final value, and derives a new outcome root using the protocol's exact framing/canonicalization. A root-only checker can accept the new root without rerunning the computation. The attacker need not invert a digest; it computes a commitment to its own forged bytes. If it can replace the expected anchor too, matching those two attacker-controlled values adds no independent assurance.

    To resist this, a consumer must preserve independent anchors and obtain trustworthy producer/execution evidence or rerun the selected checker on the declared request. A pinned executable hash establishes selected bytes under the execution assumptions; source provenance and reproducible build require more. A challenge alone is not authentication, and an unsigned record that echoes a nonce does not prove who executed anything. Authentic replay still leaves the fixture's three unchecked conformance laws and unsigned attestation, so admission remains refused. Full credit requires an actual false field or event claim, the check that would still pass, and the unmet obligations; “hashes are weak” is insufficient.

16. The partial CUT is refused as `IncompleteProposal`, with state unchanged. Exactly one exact value for every declared edge is required. A complete all-zero proposal can be scored on the declared carrier; its cycle minimum is zero. It changes the problem's claims. Whether that edit is a permissible representation repair or a false rewriting of observations requires the task's independent semantics/policy. Zero cost in the altered instance supplies no evidence that immutable external data was incorrect. Do not interpret an omitted edge as zero.

17. For rational directed cycles, use the independently derived identity `min_f Σa_i|c_i−d0f_i|=min(a_i)|Σc_i|`. Check the solver's scalar against that value and check its returned potential's cost; include negative/zero sums, unique/tied minimum penalties, exact fractional data, and reversed orientations handled consistently. A tie permits different valid potentials; equality of full output vectors is not the correct universal criterion.

    On another graph, retain a feasible potential `f` and dual vector `y`. Independently check `Bᵀy=0`, `|y_e|≤a_e`, residual `r=c−Bf`, and exact equality `Σa_e|r_e|=y·c`. These checks certify optimality for that declared graph because the primal and dual bounds meet. The four-vertex graph in questions 7–8 is one such example. If bounds do not meet, the certificate has not established optimality. Certificate checks do not prove universal solver correctness, physical fidelity, producer authenticity or source-to-binary custody. Full credit requires distinct computation/check paths rather than calling the same routine twice.

18. A strong evidence plan includes the following:

    | Item | Required content |
    | --- | --- |
    | Obtainable source | Immutable public source revision, relevant workspace/supporting crates, Cargo lockfile, license and instructions |
    | Declared fixture | Ordered vertices/edges/faces, unit penalties, before/candidate vectors, coefficient domain and budgets |
    | Trusted anchors | Expected carrier manifest, registry/source bindings and packet/request identities; provenance of independently retained anchors |
    | Encoding | Exact named profile, tagged payload rules, minimal i128 inputs, hash framing and field exclusions |
    | Executable and execution | Toolchain/platform, actual binary selection and SHA-256, environment override, command, exits and launcher-enforced wall-clock limit |
    | Results | Exact summaries 7/12 then 0/0, candidate match, execution status, partial laws, E/T writes, unsigned attestation and refused admission codes |
    | Receipt custody | Input/source/log hashes, commands and timestamps, separate passed/failed/skipped counts, and a clear declaration of checks not executed |

    Suitable hostile controls include:

    | Mutation | Expected observation |
    | --- | --- |
    | Delete a face, retain old carrier anchor, recompute request ID | `CARRIER_MANIFEST_MISMATCH` |
    | Change candidate to another vector, recompute outer identity | `CANDIDATE_NOT_REPLAYED_NORMAL_FORM`, if earlier checks pass |
    | Alter a returned field without replacing its root | Root check fails |
    | Alter a returned field and recompute unkeyed root | Root consistency can pass; fresh replay/authentication remain unestablished |
    | Duplicate a JSON key | Intake refusal under duplicate-key rejection |
    | Add an unknown request field | Intake refusal under the declared schema |
    | Add one byte beyond the interface's request ceiling | Interface-specific intake refusal; preserve which ceiling was tested |
    | Use nonminimal coefficient `"007"` with all earlier identities updated | Exact input parse refusal |
    | Replace a configured graph executable with a digest-mismatched file | Graph tutorial adapter refuses; no numerical fallback |

    Require at least five controls with predicted checks and ordered preconditions. A test with a stale outer request ID that fails early does not demonstrate the deeper carrier or candidate check. Scripted hosts are labeled as adapter tests. Historical September results retain their dates; a fresh run records its actual revision and bytes; an unavailable executable is not counted as a pass. A private GitHub path alone does not meet this question's public-deposit requirement.

## Marking advice

Reward exact witnesses, declared assumptions and precise missing obligations. Deduct for promoting source expectations into execution, treating a recomputed root as a signature, presenting a Python fallback as native evidence, or using a changed carrier without disclosing the change. Accept different valid primal/dual witnesses and sensible alternative custody plans when their domains and checks are explicit.

# PFP012–021 supporting package review

Completed the frozen 104-file support slice at 8050c66900899771766f33e8f5fdd200b7dd9120. This supplements the primary manuscript reviews; it does not complete the repository-wide audit.

All text sources were read, including three TeX bodies and every preamble difference, ten claim ledgers, five teaching packets and release/verification tools. All eleven pages of the three current package PDFs and three pages of the older archived PFP013 PDF were visually inspected and read. Both ZIPs (49 members) were reviewed through fully read current bases, every textual difference, exact member hashes and embedded-manifest checks. ZIP/PDF object-level security is outside this review.

## Useful contribution

PFP013 retains an elementary but useful scope rule: sound invoked predicates imply their conjunction, with explicit task/witness binding. PFP015 retains finite assignment gluing under pairwise overlap agreement and full coverage where global uniqueness is claimed. PFP018 documents a supplied-patch execution boundary; it does not prove arbitrary callback semantics or autonomous improvement. These are reusable workflow obligations. Generic cochain terminology without defined groups/maps adds no further mathematical result.

## Findings

### PAPER-SUPPORT-12-21-LEDGER-GAP

PFP014/015/016/018 claim ledgers contain the same generic extension table and no per-paper mathematical premise/proof/counterexample mapping. This is not evidence against the conditional mathematics, but the files do not function as complete claim ledgers.

Evidence: `papers/pfp/014_pfp_recursive_reentry_and_evidence_scope/paper_claim_ledger.md`, `papers/pfp/015_pfp_local_to_global_agent_composition/paper_claim_ledger.md`, `papers/pfp/016_pfp_future_faithful_compression_and_cost/paper_claim_ledger.md`, `papers/pfp/018_pfp_operadic_composition_and_bounded_ddc_repair/paper_claim_ledger.md`.

### PAPER-SUPPORT-12-21-STALE-RENDERINGS

PFP013,015,018 PDFs retain 2026-10-21 editions while their Markdown sources have 2026-10-23 revisions. All three PDF hashes still match the dated rendering records; all six current Markdown/TeX bindings differ even after LF normalization. These records cannot certify current Markdown/TeX-to-PDF correspondence or later harness additions. The reason for each historical source change is not inferred from hash mismatch alone. Readmes/changelogs explicitly state that older package PDFs are intentionally preserved and later renderings belong in a dated author-review collection; the mismatch is not itself evidence of fabrication.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/docs/rendering.json`, `papers/pfp/015_pfp_local_to_global_agent_composition/docs/rendering.json`, `papers/pfp/018_pfp_operadic_composition_and_bounded_ddc_repair/docs/rendering.json`.

### PAPER-SUPPORT-12-21-UNDEVELOPED-COCHAIN-TABLE

PFP013 renders a cochain/quotient mechanism inventory without defining the cochain groups, a linear differential, or the quotient equivalence relation. Its actual scoped-checker theorem uses ordinary conjunction under assumed soundness; the inventory supplies no additional cohomological foundation.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/paper.pdf`.

### PAPER-SUPPORT-12-21-TEST-CLAIM-MISMATCH

The PFP020 ledger cites deterministic sweep/entrypoint/all-target tests for malformed-parameter rejection, SO constraints and semantic gate synthesis, but those specific assertions check counts, labels, receipt identities or nonempty schedules. The live-adapter test uses a mock. These tests do not by themselves establish the stronger advertised predicates or live-model outcomes.

Evidence: `papers/pfp/020_pfp_frontier_research/code/tests/test_adaptive_braid_tournament_demo.py`, `papers/pfp/020_pfp_frontier_research/code/tests/test_l8_n4_cross_validation.py`, `papers/pfp/020_pfp_frontier_research/paper_claim_ledger.md`.

### PAPER-SUPPORT-12-21-BROKEN-NAVIGATION

PFP013/015 README links retain old 028 sibling names, and PFP021 workflow links resolve under papers/workflows rather than repository workflows. These five links do not exist in the pinned checkout.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/README.md`, `papers/pfp/015_pfp_local_to_global_agent_composition/README.md`, `papers/pfp/021_pfp_workflow_dag_process_and_mathematics/README.md`.

### PAPER-SUPPORT-12-21-GENERIC-DESCRIPTION

PFP013 descriptions.md advertises discrete cochain monograph, Lean formalizations and companion notebooks, although its actual scoped-claim paper explicitly claims no new Lean proof and its executable example is finite Boolean checking. Its Apache-2.0 code-license line also conflicts with LICENSE-CODE/pyproject metadata. Replace this generic package prose; retain the useful conditional conjunction argument.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/docs/descriptions.md`, `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/paper.tex`, `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/LICENSE-CODE`.

### PAPER-SUPPORT-12-21-WITHDRAWN-MITIGATION-METADATA

PFP020 current metadata/description and retained historical archive preserve adaptive-mitigation superiority rhetoric that current manuscript/source withdrew: inserting a gate and its inverse leaves the same braid action, hence the same commutation defect. The historical 2/3 and 1/3 per-agent rates also cannot describe a four-round table. Preserve archive as history; do not count it as model-improvement evidence.

Evidence: `papers/pfp/020_pfp_frontier_research/zenodo_metadata.json`, `papers/pfp/020_pfp_frontier_research/docs/descriptions.md`, `papers/pfp/020_pfp_frontier_research/022_pfp_frontier_research_2026-10-03.zip`.

### PAPER-SUPPORT-12-21-CURRENT-MANIFEST-DRIFT

Current paper13 and paper20 SHA256SUMS checks report 18 and 13 raw-byte mismatches. Universal LF normalization explains many, but four and six entries respectively remain unmatched. Both historical ZIPs have valid CRCs, unique casefolded names, and all embedded manifest hashes match. A current draft requires its own corrected custody manifest; do not rewrite historical ZIPs to hide version differences.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/SHA256SUMS`, `papers/pfp/020_pfp_frontier_research/SHA256SUMS`.

### PAPER-SUPPORT-12-21-EMPTY-AXIOM-CENSUS

PFP013 check_lean returns no errors when both fake build/Lean processes succeed with empty stdout. It neither requires a nonempty census nor checks expected declaration coverage; compiling a Core.lean without #print axioms would similarly provide no axiom lines to reject. This is a wrapper countercontrol, not a new Lean execution or proof that this manuscript contains an unsupported axiom.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/verify_deposit.py`.

### PAPER-SUPPORT-12-21-MANIFEST-WRITER-SELF-REFERENCE

PFP020 write_manifests sweeps the existing MANIFEST.sha256, then writes identical content to both controls. An isolated synthetic package demonstrates that the newly written MANIFEST includes its own old hash and read_manifest rejects a circular entry. Original package sources were not mutated.

Evidence: `papers/pfp/020_pfp_frontier_research/verify_deposit.py`.

### PAPER-SUPPORT-12-21-RENDER-HEADER-DRIFT

PFP013 renderer extracts bold Author/Date/Version fields, but current paper.md uses centered plain header lines; rerunning that local tool would fall back to 2026-10-05 v0.1.0 metadata. No actual rendering or source overwrite was performed.

Evidence: `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/tools/render_paper.py`, `papers/pfp/013_pfp_task_bound_claims_and_hallucination_control/paper.md`.

## Validation and disposition

Four bounded controls ran: current manifest verifiers read both source packages without modification, a fake-process census countercontrol, and a synthetic temporary-package manifest-writer countercontrol. No actual Lean process, provider, live campaign or release refresh was executed. Original sources and historical archives remain unchanged.

Both archives pass CRC and all embedded hash bindings. Current SHA256SUMS has 18/13 raw mismatches; after universal LF diagnostics, four/six remain. Version differences and old paths explain concrete differences; a mismatch alone is not fabrication. Current PFP013–016 replay script hashes match their historical receipts, but a matching script hash does not authenticate an execution.

The DOI string in PFP013 references could not be corroborated through a direct resolver tool call and targeted search. It remains unresolved; neither existence nor nonexistence is asserted. The broader external AIDE2 paper is referenced by exact historical PDF/page digests, not newly replicated here.

Retain bounded mathematical examples and historical evidence. Replace generic/misleading descriptions, reconcile current claim ledgers and metadata, repair current navigation/rendering/manifests, and keep historical archive identities intact. These are review findings; no original package repair is claimed.

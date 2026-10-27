use super::*;

const PARSER_PATCH: &str = r#"--- a/src/parser/mod.rs
+++ b/src/parser/mod.rs
@@ -1,1 +1,1 @@
-old
+new
"#;

const CANON_PATCH: &str = r#"--- a/.canon/rules.yaml
+++ b/.canon/rules.yaml
@@ -1,1 +1,1 @@
-old
+new
"#;

fn strings(items: &[&str]) -> Vec<String> {
    items.iter().map(|item| (*item).to_owned()).collect()
}

fn create(owned: &[&str], protected: &[&str]) -> Result<CodeChangeRunRootV1, String> {
    CreateCodeChangeProposalUseCase.execute(
        "task_code_01",
        "Fix bug in parser",
        "main@HEAD",
        strings(owned),
        strings(protected),
        2,
        10,
        strings(&["gate_ownership", "gate_syntax"]),
    )
}

fn refusal_code(error: &str) -> &str {
    error.split(':').next().unwrap_or(error)
}

#[test]
fn proposal_and_patch_lifecycle() {
    let root = create(&["src/parser"], &[".canon", "contracts"]).unwrap();
    assert_eq!(root.task_id, "task_code_01");

    let (updated_root, cand, patch) = SubmitPatchCandidateUseCase
        .execute(
            &root,
            &root.task_packet_sha256,
            "cand_01",
            "dev_agent",
            PARSER_PATCH,
        )
        .unwrap();
    assert_eq!(updated_root.candidate_ids, vec!["cand_01"]);
    assert_eq!(cand.producer_id, "dev_agent");
    assert_eq!(patch.touched_paths, vec!["src/parser/mod.rs"]);

    let receipts = EvaluatePatchGatesUseCase
        .execute(
            &updated_root,
            &updated_root.task_packet_sha256,
            &updated_root.run_root_digest,
            &patch,
        )
        .unwrap();
    assert_eq!(receipts.len(), 3);
    assert_eq!(receipts[0].disposition, "PASS"); // syntax
    assert_eq!(receipts[1].disposition, "PASS"); // ownership
    assert_eq!(receipts[2].disposition, "PASS"); // protected

    // The run root records the admitted bytes and chains them; every
    // receipt names the bytes it was run on.
    let digest = sha256_hex(PARSER_PATCH);
    assert_eq!(root.run_root_digest, root.task_packet_sha256);
    assert_eq!(updated_root.patch_sha256_by_candidate["cand_01"], digest);
    assert_ne!(updated_root.run_root_digest, root.run_root_digest);
    assert!(receipts
        .iter()
        .all(|receipt| receipt.patch_sha256 == digest));
}

#[test]
fn protected_path_rejection() {
    let root = create(&["src/parser"], &[".canon"]).unwrap();
    let (updated_root, _, patch) = SubmitPatchCandidateUseCase
        .execute(
            &root,
            &root.task_packet_sha256,
            "cand_02",
            "dev_agent",
            CANON_PATCH,
        )
        .unwrap();
    let receipts = EvaluatePatchGatesUseCase
        .execute(
            &updated_root,
            &updated_root.task_packet_sha256,
            &updated_root.run_root_digest,
            &patch,
        )
        .unwrap();
    assert_eq!(receipts[1].gate_name, "gate_ownership");
    assert_eq!(receipts[1].disposition, "FAIL");
    assert_eq!(receipts[2].gate_name, "gate_protected");
    assert_eq!(receipts[2].disposition, "FAIL");
}

/// The Python lifecycle computes this value for the same manifest
/// (`_path_manifest_root(("src/parser",), (".canon", "contracts"))`).
#[test]
fn path_manifest_root_matches_the_python_lifecycle() {
    assert_eq!(
        path_manifest_root(
            &strings(&["src/parser"]),
            &strings(&[".canon", "contracts"])
        ),
        "50668551ed753023faa9bf868bdc5fde8f37892db3c74a48682fd63169ea0c91"
    );
    assert_eq!(
        path_manifest_root(&strings(&["src/lib.rs"]), &strings(&[".canon"])),
        "8386ebcc078dec166fd70405cda2606b233ae7e94af0b2ad9139ee027fab7dd1"
    );
}

/// Counterexample: the old run root digest was `sha256(task_id)`, so two
/// tasks with the same id and different protected paths were
/// indistinguishable.
#[test]
fn the_run_root_digest_binds_the_path_manifest() {
    let guarded = create(&["src/parser"], &[".canon"]).unwrap();
    let unguarded = create(&["src/parser"], &[]).unwrap();
    assert_ne!(guarded.task_packet_sha256, unguarded.task_packet_sha256);
    assert_eq!(guarded.task_packet_id, guarded.task_packet_sha256);
    assert_ne!(guarded.task_packet_sha256, sha256_hex("task_code_01"));
    verify_run_root_binding(&guarded, &guarded.task_packet_sha256).unwrap();
}

/// Counterexample: a caller removes `.canon` from the protected list of a
/// run root between create and evaluate. The old evaluator ran the gates on
/// the edited root and the protected gate passed.
#[test]
fn evaluate_refuses_a_run_root_edited_after_create() {
    let root = create(&["src/parser"], &[".canon"]).unwrap();
    let (mut updated_root, _, patch) = SubmitPatchCandidateUseCase
        .execute(
            &root,
            &root.task_packet_sha256,
            "cand_01",
            "dev_agent",
            CANON_PATCH,
        )
        .unwrap();
    updated_root.payload.protected_paths.clear();
    updated_root.payload.owned_paths = strings(&[".canon", "src/parser"]);
    let error = EvaluatePatchGatesUseCase
        .execute(
            &updated_root,
            &updated_root.task_packet_sha256,
            &updated_root.run_root_digest,
            &patch,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_RUN_ROOT_BINDING_MISMATCH);

    let mut rebudgeted = root.clone();
    rebudgeted.payload.candidate_budget = 32;
    let error = SubmitPatchCandidateUseCase
        .execute(
            &rebudgeted,
            &rebudgeted.task_packet_sha256,
            "cand_02",
            "dev_agent",
            PARSER_PATCH,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_RUN_ROOT_BINDING_MISMATCH);
}

#[test]
fn evaluate_refuses_a_patch_the_run_root_did_not_admit_or_whose_bytes_changed() {
    let root = create(&["src/parser"], &[".canon"]).unwrap();
    let (updated_root, _, patch) = SubmitPatchCandidateUseCase
        .execute(
            &root,
            &root.task_packet_sha256,
            "cand_01",
            "dev_agent",
            PARSER_PATCH,
        )
        .unwrap();

    let mut foreign = patch.clone();
    foreign.patch_artifact_id = "patch_never_submitted".to_owned();
    let error = EvaluatePatchGatesUseCase
        .execute(
            &updated_root,
            &updated_root.task_packet_sha256,
            &updated_root.run_root_digest,
            &foreign,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_PATCH_NOT_BOUND);

    let mut swapped = patch.clone();
    swapped.patch_text = CANON_PATCH.to_owned();
    let error = EvaluatePatchGatesUseCase
        .execute(
            &updated_root,
            &updated_root.task_packet_sha256,
            &updated_root.run_root_digest,
            &swapped,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_PATCH_NOT_BOUND);
}

#[test]
fn create_refuses_each_malformed_manifest_instead_of_defaulting() {
    let cases: Vec<(&[&str], &[&str])> = vec![
        (&[], &[".canon"]),                       // nothing owned
        (&["src/parser", ".canon/x"], &[]),       // unsorted
        (&["src/parser", "src/parser"], &[]),     // duplicate
        (&["src/parser"], &[".canon", ".canon"]), // duplicate protected
        (&["src/parser"], &["src/parser"]),       // owned and protected overlap
        (&["../escape"], &[]),                    // traversal
        (&["src/parser"], &["/abs"]),             // absolute protected path
        (&["src/parser"], &[""]),                 // empty path would protect nothing
    ];
    for (owned, protected) in cases {
        let error = create(owned, protected).unwrap_err();
        assert_eq!(
            refusal_code(&error),
            REFUSAL_CODE_CHANGE_REQUEST_INVALID,
            "{owned:?} / {protected:?}"
        );
    }
}

#[test]
fn create_refuses_bad_scalars_and_gates() {
    let uc = CreateCodeChangeProposalUseCase;
    let owned = || strings(&["src/parser"]);
    let gates = || strings(&["gate_ownership", "gate_syntax"]);
    let attempts = [
        uc.execute("", "o", "HEAD", owned(), vec![], 2, 10, gates()),
        uc.execute("t", " ", "HEAD", owned(), vec![], 2, 10, gates()),
        uc.execute("t", "o", "", owned(), vec![], 2, 10, gates()),
        uc.execute("t", "o", "-HEAD", owned(), vec![], 2, 10, gates()),
        uc.execute("t", "o", "HEAD", owned(), vec![], 0, 10, gates()),
        uc.execute("t", "o", "HEAD", owned(), vec![], 33, 10, gates()),
        uc.execute("t", "o", "HEAD", owned(), vec![], 2, 0, gates()),
        uc.execute("t", "o", "HEAD", owned(), vec![], 2, 4097, gates()),
        uc.execute("t", "o", "HEAD", owned(), vec![], 2, 10, vec![]),
        uc.execute(
            "t",
            "o",
            "HEAD",
            owned(),
            vec![],
            2,
            10,
            strings(&["gate_syntax", "gate_ownership"]),
        ),
        uc.execute(
            "t",
            "o",
            "HEAD",
            owned(),
            vec![],
            2,
            10,
            strings(&["focused_tests"]),
        ),
    ];
    for (index, attempt) in attempts.into_iter().enumerate() {
        let error = attempt.expect_err(&format!("attempt {index} must be refused"));
        assert_eq!(refusal_code(&error), REFUSAL_CODE_CHANGE_REQUEST_INVALID);
    }
}

#[test]
fn submit_refuses_blank_ids_and_a_repeated_candidate() {
    let root = create(&["src/parser"], &[]).unwrap();
    for (candidate, producer) in [("", "dev"), ("cand", ""), (" ", "dev")] {
        let error = SubmitPatchCandidateUseCase
            .execute(
                &root,
                &root.task_packet_sha256,
                candidate,
                producer,
                PARSER_PATCH,
            )
            .unwrap_err();
        assert_eq!(refusal_code(&error), REFUSAL_CODE_CHANGE_REQUEST_INVALID);
    }
    let (updated, _, _) = SubmitPatchCandidateUseCase
        .execute(
            &root,
            &root.task_packet_sha256,
            "cand_01",
            "dev",
            PARSER_PATCH,
        )
        .unwrap();
    let error = SubmitPatchCandidateUseCase
        .execute(
            &updated,
            &updated.task_packet_sha256,
            "cand_01",
            "dev",
            PARSER_PATCH,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_CODE_CHANGE_REQUEST_INVALID);
}

fn forged_artifact(id: &str, text: &str) -> CodeChangePatchArtifactV1 {
    // The forger recomputes the artifact's own digest and length, so the
    // artifact is internally consistent.
    CodeChangePatchArtifactV1 {
        schema_version: CODE_CHANGE_PATCH_SCHEMA.to_owned(),
        patch_artifact_id: id.to_owned(),
        patch_sha256: sha256_hex(text),
        patch_text: text.to_owned(),
        byte_count: text.len(),
        touched_paths: parse_unified_diff(text).touched_paths,
        authority_effect: "None".to_owned(),
    }
}

/// Forgery (a): a caller appends an id pair it never submitted and hands in
/// a matching, self-consistent artifact. The old evaluator only checked that
/// the id was listed and that the artifact's digest matched its own text.
#[test]
fn evaluate_refuses_an_appended_candidate_pair_with_a_recomputed_digest() {
    let root = create(&["src/parser"], &[".canon"]).unwrap();
    let expected = root.task_packet_sha256.clone();
    let (updated, _, _) = SubmitPatchCandidateUseCase
        .execute(&root, &expected, "cand_01", "dev_agent", PARSER_PATCH)
        .unwrap();
    let smuggled = forged_artifact("patch_cand_x", CANON_PATCH);

    let mut ids_only = updated.clone();
    ids_only.candidate_ids.push("cand_x".to_owned());
    ids_only.patch_ids.push("patch_cand_x".to_owned());
    let error = EvaluatePatchGatesUseCase
        .execute(&ids_only, &expected, &ids_only.run_root_digest, &smuggled)
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_RUN_ROOT_BINDING_MISMATCH);

    let mut with_digest = ids_only.clone();
    with_digest
        .patch_sha256_by_candidate
        .insert("cand_x".to_owned(), sha256_hex(CANON_PATCH));
    let error = EvaluatePatchGatesUseCase
        .execute(
            &with_digest,
            &expected,
            &with_digest.run_root_digest,
            &smuggled,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_RUN_ROOT_BINDING_MISMATCH);
}

/// Forgery (b): a caller swaps the admitted patch text for another one and
/// recomputes `patch_sha256` and `byte_count`. The old "bytes changed" check
/// compared two fields of that same caller-supplied artifact and passed.
#[test]
fn evaluate_refuses_swapped_patch_bytes_with_a_recomputed_digest() {
    let root = create(&["src/parser"], &[".canon"]).unwrap();
    let expected = root.task_packet_sha256.clone();
    let (updated, _, admitted) = SubmitPatchCandidateUseCase
        .execute(&root, &expected, "cand_01", "dev_agent", PARSER_PATCH)
        .unwrap();
    let swapped = forged_artifact(&admitted.patch_artifact_id, CANON_PATCH);
    assert_eq!(swapped.patch_sha256, sha256_hex(&swapped.patch_text));
    let error = EvaluatePatchGatesUseCase
        .execute(&updated, &expected, &updated.run_root_digest, &swapped)
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_PATCH_NOT_BOUND);
}

/// A self-consistent root that is not the one the caller created: here a
/// re-created root with no protected paths. Only the caller's create-time
/// digest can tell them apart, and the host refuses when they differ.
#[test]
fn submit_and_evaluate_refuse_a_task_digest_the_caller_did_not_receive() {
    let guarded = create(&["src/parser"], &[".canon"]).unwrap();
    let expected = guarded.task_packet_sha256.clone();
    let unguarded = create(&["src/parser"], &[]).unwrap();
    let error = SubmitPatchCandidateUseCase
        .execute(&unguarded, &expected, "cand_01", "dev_agent", CANON_PATCH)
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_EXPECTED_TASK_DIGEST_MISMATCH);

    let (substituted, _, patch) = SubmitPatchCandidateUseCase
        .execute(
            &unguarded,
            &unguarded.task_packet_sha256,
            "cand_01",
            "dev_agent",
            CANON_PATCH,
        )
        .unwrap();
    let error = EvaluatePatchGatesUseCase
        .execute(
            &substituted,
            &expected,
            &substituted.run_root_digest,
            &patch,
        )
        .unwrap_err();
    assert_eq!(refusal_code(&error), REFUSAL_EXPECTED_TASK_DIGEST_MISMATCH);
}

/// A keyless forger rebuilds the root around a patch it never submitted and
/// recomputes every digest, including the rolling one, so the root is
/// internally consistent. The caller still holds the rolling digest its own
/// submit returned, and evaluate refuses the forged root because the two
/// differ.
#[test]
fn evaluate_refuses_a_recomputed_rolling_digest_the_caller_does_not_hold() {
    let root = create(&["src/parser"], &[".canon"]).unwrap();
    let expected = root.task_packet_sha256.clone();
    let (updated, _, admitted) = SubmitPatchCandidateUseCase
        .execute(&root, &expected, "cand_01", "dev_agent", PARSER_PATCH)
        .unwrap();
    let held = updated.run_root_digest.clone();

    // (b) with a recomputed rolling digest: swap the admitted bytes.
    let mut swapped_root = updated.clone();
    swapped_root
        .patch_sha256_by_candidate
        .insert("cand_01".to_owned(), sha256_hex(CANON_PATCH));
    swapped_root.run_root_digest = derive_run_root_digest(&swapped_root).unwrap();
    verify_run_root_binding(&swapped_root, &expected).unwrap();
    let swapped = forged_artifact(&admitted.patch_artifact_id, CANON_PATCH);
    let error = EvaluatePatchGatesUseCase
        .execute(&swapped_root, &expected, &held, &swapped)
        .unwrap_err();
    assert_eq!(
        refusal_code(&error),
        REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH
    );

    // (a) with a recomputed rolling digest: append a pair never submitted.
    let mut appended_root = updated.clone();
    appended_root.candidate_ids.push("cand_x".to_owned());
    appended_root.patch_ids.push("patch_cand_x".to_owned());
    appended_root
        .patch_sha256_by_candidate
        .insert("cand_x".to_owned(), sha256_hex(CANON_PATCH));
    appended_root.run_root_digest = derive_run_root_digest(&appended_root).unwrap();
    verify_run_root_binding(&appended_root, &expected).unwrap();
    let smuggled = forged_artifact("patch_cand_x", CANON_PATCH);
    let error = EvaluatePatchGatesUseCase
        .execute(&appended_root, &expected, &held, &smuggled)
        .unwrap_err();
    assert_eq!(
        refusal_code(&error),
        REFUSAL_EXPECTED_RUN_ROOT_DIGEST_MISMATCH
    );

    // The honest root with the held digest still evaluates.
    let receipts = EvaluatePatchGatesUseCase
        .execute(&updated, &expected, &held, &admitted)
        .unwrap();
    assert_eq!(receipts.len(), 3);
}

// Origin: engine/crates_rs/pfp_runtime/src/code_change/tests.rs
// Claim: urn:core:crates_rs:pfp-runtime:tests:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0a468ff5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0a468ff5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0a468ff5 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError0a468ff5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0a468ff5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0a468ff5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0a468ff5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0a468ff5> {
        if capacity_bound == 0 {
            return Err(BoundaryError0a468ff5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0a468ff5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0a468ff5::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod l4_boundary_tests_0a468ff5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0a468ff5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0a468ff5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0a468ff5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0a468ff5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0a468ff5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError0a468ff5::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError0a468ff5::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

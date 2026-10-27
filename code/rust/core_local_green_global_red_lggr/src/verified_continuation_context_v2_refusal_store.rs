//! `AppendLogRefusalStore` — the third real v2 verifier.
//!
//! # The defect this closes
//!
//! In v1, prior refusals were a **caller-supplied packet field**. A caller who
//! wanted to continue simply omitted them, and nothing could tell the difference
//! between "no refusal was ever recorded" and "a refusal was recorded and left
//! out". The field was deleted; [`RefusalStore`] replaced it. This is the first
//! implementation that actually stores anything.
//!
//! Omission is now **inexpressible**: `standing_refusals` reads the store, the
//! store is append-only, and there is deliberately **no removal method** on this
//! type. Not a private one, not a `#[cfg(test)]` one. A refusal that was recorded
//! can only be un-recorded by editing the file on disk — which is what the pin
//! below is for.
//!
//! # Durability is the point, not a bonus
//!
//! Backed by [`core_replay::append_log::AppendLogV1`], a hash-chained JSONL log
//! that `fsync`s before acknowledging an append. `open` re-verifies the entire
//! chain — sequence continuity, parent linkage, and per-record digest — and
//! refuses wholesale on any mismatch. The in-memory index is rebuilt **from
//! disk**, never carried across, so a process restart cannot lose a refusal.
//!
//! # What this does NOT establish — the truncation gap
//!
//! **A hash chain detects modification, not tail truncation.** Delete the last
//! `n` lines and what remains is still a perfectly valid chain: sequences start
//! at 0, parents link, digests verify. [`AppendLogRefusalStore::open`] will
//! succeed and silently report fewer refusals than were recorded.
//!
//! That is precisely the forgetting this type exists to prevent, so it is not
//! papered over: [`AppendLogRefusalStore::open_pinned`] takes a
//! [`RefusalStorePin`] captured earlier and refuses if the log has lost records
//! or diverged from it. The residual does not vanish — it **moves** to "the pin
//! must live somewhere the caller cannot rewrite", which is a narrower and more
//! honest problem than "trust the file". Where that pin lives is not solved here.
//!
//! `open` (unpinned) is retained for first-run bootstrap, where there is no
//! earlier pin by construction. Its blind spot is asserted by a test rather than
//! described in prose, so it cannot rot into a false claim.
//!
//! **AuthorityEffect: None.** A standing refusal blocks continuation; nothing
//! here mints permission to continue.

use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

use core_replay::append_log::{AppendLogError, AppendLogRecordV1, AppendLogV1};
use serde::{Deserialize, Serialize};

use crate::verified_continuation_context_v2::{ContinuationBlockerV2, RefusalStore};

/// Payload schema tag. Present in every record so a foreign log cannot be
/// mistaken for a refusal log.
const REFUSAL_RECORD_SCHEMA: &str = "core.epk.v2.refusal.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RefusalRecordV1 {
    schema: String,
    run_id: String,
    blocker: ContinuationBlockerV2,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RefusalStoreError {
    #[error("refusal log: {0}")]
    Log(String),
    #[error("refusal log record {sequence} is not a v2 refusal record: {reason}")]
    ForeignRecord { sequence: u64, reason: String },
    #[error(
        "refusal log lost records: pin expected at least {pinned_count}, found {found}. \
         An append-only log cannot shrink; this is truncation, not a normal state."
    )]
    Truncated { pinned_count: u64, found: u64 },
    #[error(
        "refusal log diverged from its pin at record {sequence}: pinned {pinned_head}, \
         found {found}. History was rewritten after the pin was taken."
    )]
    Diverged {
        sequence: u64,
        pinned_head: String,
        found: String,
    },
}

impl From<AppendLogError> for RefusalStoreError {
    fn from(e: AppendLogError) -> Self {
        Self::Log(e.to_string())
    }
}

/// A witness to how much of the log had been written at a point in time.
///
/// Carrying one forward is what turns "the chain is internally consistent" into
/// "the chain still contains everything it contained before".
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RefusalStorePin {
    record_count: u64,
    head_sha256: Option<String>,
}

impl RefusalStorePin {
    pub fn record_count(&self) -> u64 {
        self.record_count
    }
    pub fn head_sha256(&self) -> Option<&str> {
        self.head_sha256.as_deref()
    }
}

/// Append-only, hash-chained, per-run refusal store.
#[derive(Debug)]
pub struct AppendLogRefusalStore {
    log: AppendLogV1,
    by_run: BTreeMap<String, BTreeSet<ContinuationBlockerV2>>,
    record_count: u64,
    head_sha256: Option<String>,
}

impl AppendLogRefusalStore {
    /// Open (creating if absent) and rebuild the index from disk.
    ///
    /// Does **not** detect tail truncation — see the module docs and
    /// [`Self::open_pinned`]. Use this only where no earlier pin can exist.
    pub fn open(path: impl Into<PathBuf>) -> Result<Self, RefusalStoreError> {
        let (log, records) = AppendLogV1::open(path.into())?;
        Self::index(log, records)
    }

    /// Open and verify the log still contains everything `pin` witnessed.
    ///
    /// Refuses on truncation (fewer records than pinned) and on divergence (the
    /// record at the pinned position no longer has the pinned digest).
    pub fn open_pinned(
        path: impl Into<PathBuf>,
        pin: &RefusalStorePin,
    ) -> Result<Self, RefusalStoreError> {
        let (log, records) = AppendLogV1::open(path.into())?;
        let found = records.len() as u64;
        if found < pin.record_count {
            return Err(RefusalStoreError::Truncated {
                pinned_count: pin.record_count,
                found,
            });
        }
        if let (Some(pinned_head), true) = (pin.head_sha256.as_deref(), pin.record_count > 0) {
            let at = &records[(pin.record_count - 1) as usize];
            if at.record_sha256 != pinned_head {
                return Err(RefusalStoreError::Diverged {
                    sequence: at.sequence,
                    pinned_head: pinned_head.to_string(),
                    found: at.record_sha256.clone(),
                });
            }
        }
        Self::index(log, records)
    }

    fn index(log: AppendLogV1, records: Vec<AppendLogRecordV1>) -> Result<Self, RefusalStoreError> {
        let mut by_run: BTreeMap<String, BTreeSet<ContinuationBlockerV2>> = BTreeMap::new();
        let mut head_sha256 = None;
        let record_count = records.len() as u64;
        for record in records {
            // A payload we cannot read is NOT skipped. Skipping would silently
            // drop a refusal, which is the whole failure mode being prevented.
            let parsed: RefusalRecordV1 =
                serde_json::from_value(record.payload.clone()).map_err(|e| {
                    RefusalStoreError::ForeignRecord {
                        sequence: record.sequence,
                        reason: e.to_string(),
                    }
                })?;
            if parsed.schema != REFUSAL_RECORD_SCHEMA {
                return Err(RefusalStoreError::ForeignRecord {
                    sequence: record.sequence,
                    reason: format!(
                        "schema {:?}, expected {REFUSAL_RECORD_SCHEMA:?}",
                        parsed.schema
                    ),
                });
            }
            by_run
                .entry(parsed.run_id)
                .or_default()
                .insert(parsed.blocker);
            head_sha256 = Some(record.record_sha256);
        }
        Ok(Self {
            log,
            by_run,
            record_count,
            head_sha256,
        })
    }

    /// Append one refusal and return the pin that now witnesses the log.
    ///
    /// There is no counterpart that removes one. Recording the same refusal for
    /// the same run twice is idempotent in the index, but both appends are kept
    /// on the chain — the log is a history, not a set.
    pub fn record(
        &mut self,
        run_id: &str,
        blocker: ContinuationBlockerV2,
    ) -> Result<RefusalStorePin, RefusalStoreError> {
        let payload = serde_json::to_value(RefusalRecordV1 {
            schema: REFUSAL_RECORD_SCHEMA.to_string(),
            run_id: run_id.to_string(),
            blocker,
        })
        .map_err(|e| RefusalStoreError::Log(e.to_string()))?;
        let sealed = self.log.append(payload)?;
        self.by_run
            .entry(run_id.to_string())
            .or_default()
            .insert(blocker);
        self.record_count += 1;
        self.head_sha256 = Some(sealed.record_sha256);
        Ok(self.pin())
    }

    /// Witness the current extent of the log, to be checked by a later
    /// [`Self::open_pinned`].
    pub fn pin(&self) -> RefusalStorePin {
        RefusalStorePin {
            record_count: self.record_count,
            head_sha256: self.head_sha256.clone(),
        }
    }

    pub fn path(&self) -> &Path {
        self.log.path()
    }
}

impl RefusalStore for AppendLogRefusalStore {
    fn standing_refusals(&self, run_id: &str) -> Vec<ContinuationBlockerV2> {
        self.by_run
            .get(run_id)
            .map(|s| s.iter().copied().collect())
            .unwrap_or_default()
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    /// Per-test scratch path. No `Date::now`/rand available, so the caller
    /// supplies a distinct name.
    fn scratch(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join("core_epk_v2_refusal_store_tests");
        let _ = fs::create_dir_all(&dir);
        let p = dir.join(format!("{name}.jsonl"));
        let _ = fs::remove_file(&p);
        p
    }

    #[test]
    fn a_recorded_refusal_stands() {
        let p = scratch("stands");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        assert!(s.standing_refusals("run-1").is_empty());
        s.record("run-1", ContinuationBlockerV2::DetectorInadequate)
            .unwrap();
        assert_eq!(
            s.standing_refusals("run-1"),
            vec![ContinuationBlockerV2::DetectorInadequate]
        );
    }

    #[test]
    fn a_refusal_survives_reopening_because_it_is_rebuilt_from_disk() {
        // The load-bearing property. A restart must not clear a refusal.
        let p = scratch("survives");
        let pin = {
            let mut s = AppendLogRefusalStore::open(&p).unwrap();
            s.record("run-1", ContinuationBlockerV2::CodaGtlaRefusal)
                .unwrap()
        };
        let reopened = AppendLogRefusalStore::open_pinned(&p, &pin).unwrap();
        assert_eq!(
            reopened.standing_refusals("run-1"),
            vec![ContinuationBlockerV2::CodaGtlaRefusal]
        );
    }

    #[test]
    fn refusals_are_isolated_per_run() {
        let p = scratch("isolated");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        s.record("run-1", ContinuationBlockerV2::BudgetExhausted)
            .unwrap();
        assert!(s.standing_refusals("run-2").is_empty());
        assert_eq!(s.standing_refusals("run-1").len(), 1);
    }

    #[test]
    fn the_standing_set_only_ever_grows() {
        let p = scratch("monotone");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        let mut prev: Vec<ContinuationBlockerV2> = vec![];
        for b in [
            ContinuationBlockerV2::WitnessMissing,
            ContinuationBlockerV2::DetectorInadequate,
            ContinuationBlockerV2::BudgetExhausted,
        ] {
            s.record("run-1", b).unwrap();
            let now = s.standing_refusals("run-1");
            assert!(
                prev.iter().all(|old| now.contains(old)),
                "a previously standing refusal disappeared: {prev:?} -> {now:?}"
            );
            prev = now;
        }
        assert_eq!(prev.len(), 3);
    }

    #[test]
    fn recording_the_same_refusal_twice_is_idempotent_in_the_index() {
        let p = scratch("idempotent");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        s.record("run-1", ContinuationBlockerV2::WitnessMissing)
            .unwrap();
        let pin = s
            .record("run-1", ContinuationBlockerV2::WitnessMissing)
            .unwrap();
        assert_eq!(s.standing_refusals("run-1").len(), 1);
        // ...but the history keeps both appends.
        assert_eq!(pin.record_count(), 2);
    }

    #[test]
    fn tail_truncation_is_detected_against_a_pin() {
        // THE attack: delete the last lines so a refusal is forgotten. The
        // remaining chain is still internally valid, so only the pin catches it.
        let p = scratch("truncated");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        s.record("run-1", ContinuationBlockerV2::WitnessMissing)
            .unwrap();
        let pin = s
            .record("run-1", ContinuationBlockerV2::DetectorInadequate)
            .unwrap();
        drop(s);

        let text = fs::read_to_string(&p).unwrap();
        let kept: Vec<&str> = text.lines().take(1).collect();
        fs::write(&p, format!("{}\n", kept.join("\n"))).unwrap();

        // The truncated log still opens cleanly on its own terms...
        let blind = AppendLogRefusalStore::open(&p).unwrap();
        assert_eq!(blind.standing_refusals("run-1").len(), 1);

        // ...and the pin is what refuses it.
        assert!(matches!(
            AppendLogRefusalStore::open_pinned(&p, &pin),
            Err(RefusalStoreError::Truncated {
                pinned_count: 2,
                found: 1
            })
        ));
    }

    #[test]
    fn unpinned_open_cannot_see_truncation() {
        // Executable statement of the residual. If someone later makes `open`
        // truncation-safe, this test fails and the module docs get corrected --
        // which is the point of asserting a gap rather than describing it.
        let p = scratch("residual");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        s.record("run-1", ContinuationBlockerV2::WitnessMissing)
            .unwrap();
        s.record("run-1", ContinuationBlockerV2::CodaGtlaRefusal)
            .unwrap();
        drop(s);

        let text = fs::read_to_string(&p).unwrap();
        fs::write(&p, format!("{}\n", text.lines().next().unwrap())).unwrap();

        let blind = AppendLogRefusalStore::open(&p).expect("truncation is invisible here");
        assert_eq!(
            blind.standing_refusals("run-1"),
            vec![ContinuationBlockerV2::WitnessMissing],
            "unpinned open reports the truncated history as if complete"
        );
    }

    #[test]
    fn a_rewritten_history_is_detected_against_a_pin() {
        let p = scratch("diverged");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        let pin = s
            .record("run-1", ContinuationBlockerV2::DetectorInadequate)
            .unwrap();
        drop(s);

        // Same length, different content: rebuild the log with another blocker.
        fs::remove_file(&p).unwrap();
        let mut rewritten = AppendLogRefusalStore::open(&p).unwrap();
        rewritten
            .record("run-1", ContinuationBlockerV2::WitnessMissing)
            .unwrap();
        drop(rewritten);

        assert!(matches!(
            AppendLogRefusalStore::open_pinned(&p, &pin),
            Err(RefusalStoreError::Diverged { .. })
        ));
    }

    #[test]
    fn a_tampered_record_is_refused_wholesale() {
        let p = scratch("tampered");
        let mut s = AppendLogRefusalStore::open(&p).unwrap();
        s.record("run-1", ContinuationBlockerV2::DetectorInadequate)
            .unwrap();
        drop(s);

        // Flip the blocker without resealing: the chain digest no longer matches.
        let text = fs::read_to_string(&p).unwrap();
        fs::write(&p, text.replace("DetectorInadequate", "BudgetExhausted")).unwrap();

        assert!(matches!(
            AppendLogRefusalStore::open(&p),
            Err(RefusalStoreError::Log(_))
        ));
    }

    #[test]
    fn a_foreign_payload_is_refused_not_skipped() {
        // Skipping an unreadable record would silently drop a refusal -- exactly
        // the failure mode this store exists to prevent.
        let p = scratch("foreign");
        let mut raw = AppendLogV1::open(p.clone()).unwrap().0;
        raw.append(serde_json::json!({"something": "else"}))
            .unwrap();
        drop(raw);

        assert!(matches!(
            AppendLogRefusalStore::open(&p),
            Err(RefusalStoreError::ForeignRecord { sequence: 0, .. })
        ));
    }

    #[test]
    fn a_wrong_schema_tag_is_refused() {
        let p = scratch("schema");
        let mut raw = AppendLogV1::open(p.clone()).unwrap().0;
        raw.append(serde_json::json!({
            "schema": "core.epk.v1.refusal",
            "run_id": "run-1",
            "blocker": "WitnessMissing"
        }))
        .unwrap();
        drop(raw);

        assert!(matches!(
            AppendLogRefusalStore::open(&p),
            Err(RefusalStoreError::ForeignRecord { .. })
        ));
    }
}

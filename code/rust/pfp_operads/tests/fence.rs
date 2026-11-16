//! Fences: where a pair of marks fences a statement, what a text must carry to keep the fence,
//! and what a byte range may not touch.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-fence-tests:v1

use pfp_operads::families::fence::{locate, Fence, Marks};

const QUESTION: Marks = Marks {
    begin: "<<Q>>",
    end: "<</Q>>",
    name: "question",
};

fn marks(begin: &'static str, end: &'static str) -> Marks {
    Marks {
        begin,
        end,
        name: "span",
    }
}

fn fence(statement: &str) -> Fence {
    locate(statement, &QUESTION).expect("a fence")
}

#[test]
fn a_fence_runs_from_the_begin_mark_to_the_end_of_the_end_mark() {
    assert_eq!(
        fence("Read <<Q>>2+2<</Q>> now."),
        Fence {
            name: "question",
            start: 5,
            end: 19,
            text: "<<Q>>2+2<</Q>>".to_owned(),
        }
    );
}

#[test]
fn offsets_count_bytes_and_not_characters() {
    let found = fence("é<<Q>>x<</Q>>");
    assert_eq!((found.start, found.end), (2, 14));
    assert_eq!(found.text, "<<Q>>x<</Q>>");
}

#[test]
fn the_first_end_mark_after_the_begin_mark_closes_the_fence() {
    assert_eq!(fence("<<Q>>a<</Q>>b<</Q>>").text, "<<Q>>a<</Q>>");
}

#[test]
fn a_begin_mark_that_occurs_twice_makes_no_fence() {
    let error = locate("<<Q>>a<</Q>> <<Q>>b<</Q>>", &QUESTION).expect_err("two begin marks");
    assert!(error.starts_with("FENCE_MARKERS_NOT_UNIQUE"), "{error}");
    assert!(error.contains("question"), "{error}");
}

#[test]
fn a_missing_mark_makes_no_fence() {
    for statement in [
        "no marks at all",
        "<<Q>>no end mark",
        "no begin mark<</Q>>",
        "<</Q>> before <<Q>> only",
    ] {
        assert!(locate(statement, &QUESTION).is_err(), "{statement}");
    }
}

#[test]
fn the_end_mark_may_start_inside_the_begin_mark() {
    let found = locate("x<a>y", &marks("<a", "a>")).expect("a fence");
    assert_eq!((found.start, found.end), (1, 4));
    assert_eq!(found.text, "<a>");
}

#[test]
fn one_mark_cannot_open_and_close_a_fence() {
    assert!(locate("x@@y", &marks("@@", "@@")).is_err());
    assert!(locate("x@@y@@z", &marks("@@", "@@")).is_err());
}

#[test]
fn a_text_keeps_a_fence_when_it_carries_the_fenced_text_once() {
    let found = fence("Read <<Q>>2+2<</Q>> now.");
    assert!(found.kept_by("<<Q>>2+2<</Q>>"));
    assert!(found.kept_by("Work: <<Q>>2+2<</Q>> and more"));
    assert!(!found.kept_by("<<Q>>2+3<</Q>>"));
    assert!(!found.kept_by(""));
    assert!(!found.kept_by("<<Q>>2+2<</Q>> <<Q>>2+2<</Q>>"));
}

#[test]
fn occurrences_that_overlap_count_once() {
    let found = locate("xabba y", &marks("ab", "ba")).expect("a fence");
    assert_eq!(found.text, "abba");
    assert!(found.kept_by("abbabba"));
}

#[test]
fn a_range_touches_a_fence_when_they_share_a_byte() {
    let found = fence("0123456789<<Q>>xx<</Q>>");
    assert_eq!((found.start, found.end), (10, 23));
    assert!(!found.touches(0, 10));
    assert!(found.touches(0, 11));
    assert!(found.touches(12, 13));
    assert!(found.touches(22, 30));
    assert!(!found.touches(23, 30));
    assert!(found.touches(0, 100));
    assert!(!found.touches(15, 15));
    assert!(!found.touches(10, 10));
}

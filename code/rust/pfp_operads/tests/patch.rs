//! Tests of the strict unified-patch reader and its exact application.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:patch:tests:v1

use pfp_operads::patch::{parse, FilePatch, REFUSED, SCOPE_REFUSED};

const ADJUST: &str = "def adjust(n):\n    if n < 0:\n        return n\n    return n - 1\n";
const REPAIR: &str = "--- a/adjust.py\n+++ b/adjust.py\n@@ -3,2 +3,2 @@\n         return n\n-    return n - 1\n+    return n + 1\n";

fn one(patch: &str) -> FilePatch {
    let mut files = parse(patch).unwrap();
    assert_eq!(files.len(), 1);
    files.remove(0)
}

fn code(patch: &str) -> &'static str {
    parse(patch).unwrap_err().code
}

fn misfit(patch: &str, text: &str) -> String {
    let refusal = one(patch).apply(text).unwrap_err();
    assert_eq!(refusal.code, REFUSED);
    refusal.message
}

fn hunk(header: &str, rows: &str) -> String {
    format!("--- a/f\n+++ b/f\n{header}\n{rows}")
}

#[test]
fn the_worked_example_changes_one_line() {
    let edits = one(REPAIR);
    assert_eq!(edits.path, "adjust.py");
    assert_eq!(
        edits.apply(ADJUST).unwrap(),
        "def adjust(n):\n    if n < 0:\n        return n\n    return n + 1\n"
    );
}

#[test]
fn hunks_and_files_are_applied_in_the_order_written() {
    let patch = "diff --git a/one.txt b/one.txt\nindex 1111111..2222222 100644\n\
                 --- a/one.txt\t2026-10-23 10:00:00\n+++ b/one.txt\t2026-10-23 10:01:00\n\
                 @@ -1,2 +1,2 @@ fn first()\n-a\n+A\n b\n@@ -4 +4 @@\n-d\n+D\n\
                 --- a/dir/two.txt\n+++ b/dir/two.txt\n@@ -1 +1 @@\n-x\n+y\n";
    let files = parse(patch).unwrap();
    assert_eq!(
        files.iter().map(|f| f.path.as_str()).collect::<Vec<_>>(),
        ["one.txt", "dir/two.txt"]
    );
    assert_eq!(
        files[0].apply("a\nb\nc\nd\ne\n").unwrap(),
        "A\nb\nc\nD\ne\n"
    );
    assert_eq!(files[1].apply("x\n").unwrap(), "y\n");
}

#[test]
fn a_hunk_applies_only_at_the_line_it_names() {
    let shifted = REPAIR.replace("-3,2", "-2,2");
    assert_eq!(
        misfit(&shifted, ADJUST),
        "the hunk at old line 2 of adjust.py does not match the file"
    );
    let other_text = ADJUST.replace("n - 1", "n - 2");
    assert_eq!(
        misfit(REPAIR, &other_text),
        "the hunk at old line 3 of adjust.py does not match the file"
    );
    assert!(misfit(REPAIR, "def adjust(n):\n").contains("after the file"));
    assert!(misfit(&hunk("@@ -1 +1 @@", "-a\n+b\n"), "").contains("does not match"));
}

#[test]
fn a_changed_context_line_is_refused() {
    let patch = hunk("@@ -1,3 +1,3 @@", " a\n-b\n+B\n c\n");
    assert_eq!(one(&patch).apply("a\nb\nc\n").unwrap(), "a\nB\nc\n");
    assert!(misfit(&patch, "a\nb\nC\n").contains("does not match"));
    assert!(misfit(&patch, "A\nb\nc\n").contains("does not match"));
    assert!(misfit(&patch, "a\nb\n").contains("does not match"));
}

#[test]
fn hunks_must_follow_one_another() {
    let overlap = hunk("@@ -2,2 +2,2 @@", " b\n-c\n+C\n@@ -3 +3 @@\n-c\n+X\n");
    assert_eq!(
        misfit(&overlap, "a\nb\nc\nd\n"),
        "the hunk at old line 3 of f starts before the previous hunk ends or after the file"
    );
    let touching = hunk("@@ -1 +1 @@", "-a\n+A\n@@ -2 +2 @@\n-b\n+B\n");
    assert_eq!(one(&touching).apply("a\nb\nc\n").unwrap(), "A\nB\nc\n");
}

#[test]
fn lines_can_be_added_or_removed_alone() {
    let add = hunk("@@ -1,0 +2 @@", "+new\n");
    assert_eq!(one(&add).apply("a\nb\n").unwrap(), "a\nnew\nb\n");
    let top = hunk("@@ -0,0 +1,2 @@", "+one\n+two\n");
    assert_eq!(one(&top).apply("a\n").unwrap(), "one\ntwo\na\n");
    let end = hunk("@@ -2,0 +3 @@", "+z\n");
    assert_eq!(one(&end).apply("a\nb\n").unwrap(), "a\nb\nz\n");
    assert!(misfit(&end, "a\n").contains("after the file"));
    let cut = hunk("@@ -2,2 +1,0 @@", "-b\n-c\n");
    assert_eq!(one(&cut).apply("a\nb\nc\nd\n").unwrap(), "a\nd\n");
}

#[test]
fn a_missing_final_newline_is_part_of_the_line() {
    let patch = hunk(
        "@@ -2 +2 @@",
        "-b\n\\ No newline at end of file\n+B\n\\ No newline at end of file\n",
    );
    assert_eq!(one(&patch).apply("a\nb").unwrap(), "a\nB");
    assert!(misfit(&patch, "a\nb\n").contains("does not match"));
    let adds_newline = hunk("@@ -2 +2 @@", "-b\n\\ No newline at end of file\n+b\n");
    assert_eq!(one(&adds_newline).apply("a\nb").unwrap(), "a\nb\n");
    let keeps = hunk(
        "@@ -1,2 +1,2 @@",
        "-a\n+A\n b\n\\ No newline at end of file\n",
    );
    assert_eq!(one(&keeps).apply("a\nb").unwrap(), "A\nb");
    assert_eq!(
        code(&hunk("@@ -1 +1 @@", "\\ No newline\n-a\n+b\n")),
        REFUSED
    );
    assert_eq!(
        code(&hunk("@@ -1 +1 @@", "-a\n\\ one\n\\ two\n+b\n")),
        REFUSED
    );
}

#[test]
fn carriage_returns_and_blank_context_lines_are_kept_as_written() {
    let crlf = hunk("@@ -1,2 +1,2 @@", " a\r\n-b\r\n+B\r\n");
    assert_eq!(one(&crlf).apply("a\r\nb\r\n").unwrap(), "a\r\nB\r\n");
    assert!(misfit(&crlf, "a\nb\n").contains("does not match"));
    let blank = hunk("@@ -1,3 +1,3 @@", " a\n\n-b\n+B\n");
    assert_eq!(one(&blank).apply("a\n\nb\n").unwrap(), "a\n\nB\n");
}

#[test]
fn only_edits_to_existing_text_files_are_supported() {
    for marker in [
        "new file mode 100644",
        "deleted file mode 100644",
        "old mode 100644",
        "new mode 100755",
        "rename from a.txt",
        "rename to b.txt",
        "copy from a.txt",
        "copy to b.txt",
        "GIT binary patch",
        "Binary files a/x and b/x differ",
    ] {
        let patch = format!(
            "diff --git a/f b/f\n{marker}\n{}",
            hunk("@@ -1 +1 @@", "-a\n+b\n")
        );
        let refusal = parse(&patch).unwrap_err();
        assert_eq!(refusal.code, SCOPE_REFUSED, "{marker}");
        assert!(refusal.message.contains(marker), "{marker}");
    }
    let quoted = hunk("@@ -1 +1 @@", "-a\n+see new file mode 100644\n");
    assert_eq!(
        one(&quoted).apply("a\n").unwrap(),
        "see new file mode 100644\n"
    );
    assert_eq!(
        code("--- /dev/null\n+++ b/f\n@@ -0,0 +1 @@\n+a\n"),
        SCOPE_REFUSED
    );
    assert_eq!(
        code("--- a/f\n+++ /dev/null\n@@ -1 +0,0 @@\n-a\n"),
        SCOPE_REFUSED
    );
    let renamed = parse("--- a/f\n+++ b/g\n@@ -1 +1 @@\n-a\n+b\n").unwrap_err();
    assert_eq!(
        (renamed.code, renamed.message.as_str()),
        (SCOPE_REFUSED, "f is renamed to g")
    );
}

#[test]
fn a_malformed_patch_is_refused() {
    for (patch, why) in [
        ("garbage\n".to_owned(), "unexpected line \"garbage\""),
        (
            "--- a/f\n@@ -1 +1 @@\n-a\n+b\n".to_owned(),
            "no +++ line follows --- a/f",
        ),
        ("--- a/f\n".to_owned(), "no +++ line follows --- a/f"),
        (
            "--- a/f\n+++ b/f\n".to_owned(),
            "no hunk follows the header of f",
        ),
        (
            "--- f\n+++ b/f\n".to_owned(),
            "expected --- a/PATH, found \"--- f\"",
        ),
        (
            "--- a/f\n+++ f\n".to_owned(),
            "expected +++ b/PATH, found \"+++ f\"",
        ),
        (
            "--- a/\n+++ b/\n".to_owned(),
            "expected --- a/PATH, found \"--- a/\"",
        ),
        (hunk("@@ -1 +1", "-a\n+b\n"), "bad hunk header \"@@ -1 +1\""),
        (
            hunk("@@ -x +1 @@", "-a\n+b\n"),
            "bad hunk header \"@@ -x +1 @@\"",
        ),
        (hunk("@@ -1 +1 @@", "-a\n*b\n"), "bad hunk line \"*b\""),
        (
            hunk("@@ -1 +1 @@", "-a\n\u{e9}\n"),
            "bad hunk line \"\u{e9}\"",
        ),
        (
            hunk("@@ -1,2 +1,2 @@", "-a\n+b\n"),
            "the patch ends inside a hunk",
        ),
        (
            hunk("@@ -1,2 +1 @@", " a\n+b\n+c\n"),
            "a hunk has more lines than its header declares",
        ),
        (
            hunk("@@ -1 +1,2 @@", " a\n-b\n"),
            "a hunk has more lines than its header declares",
        ),
        (
            hunk("@@ -0 +1 @@", "-a\n+b\n"),
            "old lines are counted from 1",
        ),
        (
            hunk("@@ -99999999999999999999999 +1 @@", "-a\n+b\n"),
            "99999999999999999999999 is not a line count",
        ),
        (
            hunk("@@ -1,99999999999999999999999 +1 @@", "-a\n+b\n"),
            "99999999999999999999999 is not a line count",
        ),
        (
            hunk("@@ -1 +1,99999999999999999999999 @@", "-a\n+b\n"),
            "99999999999999999999999 is not a line count",
        ),
        (
            format!("{0}{0}", hunk("@@ -1 +1 @@", "-a\n+b\n")),
            "f is patched twice",
        ),
        (
            hunk("@@ -1 +1 @@", "-a\n+b\n stray\n"),
            "unexpected line \" stray\"",
        ),
    ] {
        let refusal = parse(&patch).unwrap_err();
        assert_eq!(
            (refusal.code, refusal.message.as_str()),
            (REFUSED, why),
            "{patch:?}"
        );
    }
}

#[test]
fn an_empty_patch_names_no_file() {
    assert_eq!(parse("").unwrap(), []);
    assert_eq!(
        parse("diff --git a/f b/f\nindex 1..2 100644\n").unwrap(),
        []
    );
}

#[test]
fn a_patch_does_not_change_text_it_does_not_name() {
    let text = "keep\n".repeat(40) + "old\n" + &"tail\n".repeat(40);
    let patch = hunk("@@ -41 +41 @@", "-old\n+new\n");
    assert_eq!(
        one(&patch).apply(&text).unwrap(),
        "keep\n".repeat(40) + "new\n" + &"tail\n".repeat(40)
    );
    assert_eq!(one(&patch).apply(&text).unwrap().len(), text.len());
}

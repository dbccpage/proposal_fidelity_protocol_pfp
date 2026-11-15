//! A text patch in unified format, read strictly and applied exactly where it says.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:patch:v1
//!
//! The format is the one `git diff` writes for an edit to an existing text file:
//!
//! ```text
//! --- a/adjust.py
//! +++ b/adjust.py
//! @@ -3,2 +3,2 @@
//!      return n
//! -    return n - 1
//! +    return n + 1
//! ```
//!
//! A hunk is applied at the old line it names and nowhere else: no offset, no fuzz. Every kept or
//! removed line must equal the file's line, line end included. A patch that creates, deletes,
//! renames or re-modes a file, or that carries binary data, is refused. Nothing here touches a
//! file; [`FilePatch::apply`] maps a file's text to its patched text.

use std::collections::BTreeSet;
use std::iter::Peekable;
use std::str::SplitInclusive;

use regex::Regex;

use crate::Refusal;

/// The patch is malformed or does not fit the text it is applied to.
pub const REFUSED: &str = "PATCH_REFUSED";
/// The patch asks for a kind of change this host does not make.
pub const SCOPE_REFUSED: &str = "PATCH_SCOPE_REFUSED";

const UNSUPPORTED: [&str; 10] = [
    "new file mode ",
    "deleted file mode ",
    "old mode ",
    "new mode ",
    "rename from ",
    "rename to ",
    "copy from ",
    "copy to ",
    "GIT binary patch",
    "Binary files ",
];
const SKIPPED: [&str; 2] = ["diff --git ", "index "];
const NO_FILE: &str = "/dev/null";
const HUNK: &str = r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,(\d+))? @@";

type Lines<'a> = Peekable<SplitInclusive<'a, char>>;

#[derive(Debug, Clone, PartialEq, Eq)]
enum Row {
    Keep(String),
    Drop(String),
    Add(String),
}

/// One block of changed lines and the old line it starts at.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Hunk {
    /// Index of the first old line the hunk covers, counted from zero.
    at: usize,
    rows: Vec<Row>,
}

/// The edits to one file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FilePatch {
    pub path: String,
    hunks: Vec<Hunk>,
}

fn refuse<T>(code: &'static str, message: impl Into<String>) -> Result<T, Refusal> {
    Err(Refusal::new(code, message))
}

fn bare(line: &str) -> &str {
    line.strip_suffix('\n').unwrap_or(line)
}

/// The path a header line names, without its `a/` or `b/` and without a trailing timestamp.
fn header_path<'a>(line: &'a str, marker: &str, side: &str) -> Result<&'a str, Refusal> {
    let named = bare(line).strip_prefix(marker).unwrap_or_default();
    let named = named.split('\t').next().unwrap_or_default().trim_end();
    if named == NO_FILE {
        return refuse(SCOPE_REFUSED, "only edits to existing files are supported");
    }
    match named.strip_prefix(side) {
        Some(path) if !path.is_empty() => Ok(path),
        _ => refuse(
            REFUSED,
            format!("expected {marker}{side}PATH, found {:?}", bare(line)),
        ),
    }
}

fn number(text: Option<&str>, default: usize) -> Result<usize, Refusal> {
    match text {
        None => Ok(default),
        Some(digits) => digits
            .parse()
            .map_err(|_| Refusal::new(REFUSED, format!("{digits} is not a line count"))),
    }
}

/// Read a hunk header: the first old line it names and its two line counts.
fn counts(header: &str) -> Result<(usize, usize, usize), Refusal> {
    let pattern = Regex::new(HUNK).map_err(|error| Refusal::new("ENCODING", error.to_string()))?;
    let Some(found) = pattern.captures(header) else {
        return refuse(REFUSED, format!("bad hunk header {:?}", bare(header)));
    };
    let part = |index| found.get(index).map(|m| m.as_str());
    let start = number(part(1), 0)?;
    let (old, new) = (number(part(2), 1)?, number(part(3), 1)?);
    if start == 0 && old > 0 {
        return refuse(REFUSED, "old lines are counted from 1");
    }
    Ok((start, old, new))
}

/// Read one hunk: its header, then rows until both declared counts are met.
fn hunk(header: &str, lines: &mut Lines<'_>) -> Result<Hunk, Refusal> {
    let (start, old, new) = counts(header)?;
    let (mut old_seen, mut new_seen) = (0, 0);
    let mut rows = Vec::new();
    while old_seen < old || new_seen < new {
        let Some(line) = lines.next() else {
            return refuse(REFUSED, "the patch ends inside a hunk");
        };
        let text = line.get(1..).unwrap_or_default().to_owned();
        let row = match line.chars().next() {
            Some(' ') => Row::Keep(text),
            Some('\n') => Row::Keep(line.to_owned()),
            Some('-') => Row::Drop(text),
            Some('+') => Row::Add(text),
            Some('\\') => {
                unterminate(&mut rows)?;
                continue;
            }
            _ => return refuse(REFUSED, format!("bad hunk line {:?}", bare(line))),
        };
        old_seen += usize::from(!matches!(row, Row::Add(_)));
        new_seen += usize::from(!matches!(row, Row::Drop(_)));
        if old_seen > old || new_seen > new {
            return refuse(REFUSED, "a hunk has more lines than its header declares");
        }
        rows.push(row);
    }
    if lines.next_if(|line| line.starts_with('\\')).is_some() {
        unterminate(&mut rows)?;
    }
    Ok(Hunk {
        at: if old == 0 { start } else { start - 1 },
        rows,
    })
}

/// Apply a "no newline at end of file" marker to the row before it.
fn unterminate(rows: &mut [Row]) -> Result<(), Refusal> {
    match rows.last_mut() {
        Some(Row::Keep(text) | Row::Drop(text) | Row::Add(text)) if text.ends_with('\n') => {
            text.pop();
            Ok(())
        }
        _ => refuse(REFUSED, "a no-newline marker follows no line"),
    }
}

/// Read one file's edits: the two header lines, then its hunks.
fn file(old_header: &str, lines: &mut Lines<'_>) -> Result<FilePatch, Refusal> {
    let old = header_path(old_header, "--- ", "a/")?;
    let new = match lines.next() {
        Some(line) if line.starts_with("+++ ") => header_path(line, "+++ ", "b/")?,
        _ => return refuse(REFUSED, format!("no +++ line follows --- a/{old}")),
    };
    if old != new {
        return refuse(SCOPE_REFUSED, format!("{old} is renamed to {new}"));
    }
    let mut hunks = Vec::new();
    while let Some(header) = lines.next_if(|line| line.starts_with("@@")) {
        hunks.push(hunk(header, lines)?);
    }
    if hunks.is_empty() {
        return refuse(REFUSED, format!("no hunk follows the header of {old}"));
    }
    Ok(FilePatch {
        path: old.to_owned(),
        hunks,
    })
}

/// Read a whole patch. Each file appears once; the result is in the patch's order.
pub fn parse(text: &str) -> Result<Vec<FilePatch>, Refusal> {
    if let Some(line) = text
        .lines()
        .find(|line| UNSUPPORTED.iter().any(|marker| line.starts_with(marker)))
    {
        return refuse(
            SCOPE_REFUSED,
            format!("only edits to existing text files are supported, found {line:?}"),
        );
    }
    let mut lines = text.split_inclusive('\n').peekable();
    let mut files: Vec<FilePatch> = Vec::new();
    let mut seen = BTreeSet::new();
    while let Some(line) = lines.next() {
        if SKIPPED.iter().any(|marker| line.starts_with(marker)) {
            continue;
        }
        if !line.starts_with("--- ") {
            return refuse(REFUSED, format!("unexpected line {:?}", bare(line)));
        }
        let edits = file(line, &mut lines)?;
        if !seen.insert(edits.path.clone()) {
            return refuse(REFUSED, format!("{} is patched twice", edits.path));
        }
        files.push(edits);
    }
    Ok(files)
}

impl FilePatch {
    /// The patched text of a file whose text is `text`.
    pub fn apply(&self, text: &str) -> Result<String, Refusal> {
        let lines: Vec<&str> = text.split_inclusive('\n').collect();
        let mut patched = String::new();
        let mut next = 0;
        for hunk in &self.hunks {
            let Some(untouched) = lines.get(next..hunk.at) else {
                return self.misfit(
                    hunk,
                    "starts before the previous hunk ends or after the file",
                );
            };
            patched.extend(untouched.iter().copied());
            next = self.rows(hunk, &lines, &mut patched)?;
        }
        patched.extend(lines.get(next..).unwrap_or_default().iter().copied());
        Ok(patched)
    }

    /// Write one hunk's new side to `patched` and return the index of the first old line after it.
    fn rows(&self, hunk: &Hunk, lines: &[&str], patched: &mut String) -> Result<usize, Refusal> {
        let mut next = hunk.at;
        for row in &hunk.rows {
            let old = match row {
                Row::Add(new) => {
                    patched.push_str(new);
                    continue;
                }
                Row::Keep(old) | Row::Drop(old) => old,
            };
            if lines.get(next) != Some(&old.as_str()) {
                return self.misfit(hunk, "does not match the file");
            }
            if matches!(row, Row::Keep(_)) {
                patched.push_str(old);
            }
            next += 1;
        }
        Ok(next)
    }

    fn misfit<T>(&self, hunk: &Hunk, why: &str) -> Result<T, Refusal> {
        refuse(
            REFUSED,
            format!(
                "the hunk at old line {} of {} {why}",
                hunk.at + 1,
                self.path
            ),
        )
    }
}

//! Fenced spans of a statement: a begin mark and an end mark round text that no rewrite and no
//! packet may change.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-fence:v1
//!
//! [`locate`] finds the fence a pair of marks makes in a statement. The begin mark must occur
//! exactly once, and the end mark must occur after the first byte of the begin mark. The fence
//! is the text from the start of the begin mark to the end of the end mark, both included.
//! Offsets are byte offsets into the statement.
//!
//! A text keeps a fence when the fenced text occurs in it exactly once, counting occurrences
//! that do not overlap ([`Fence::kept_by`]). A byte range touches a fence when the two share a
//! byte ([`Fence::touches`]).

/// The two marks that make a fence, and its name.
pub struct Marks {
    pub begin: &'static str,
    pub end: &'static str,
    pub name: &'static str,
}

/// One fence of a statement.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Fence {
    pub name: &'static str,
    /// The byte offset of the first byte of the begin mark.
    pub start: usize,
    /// The byte offset after the last byte of the end mark.
    pub end: usize,
    /// The fenced text, marks included.
    pub text: String,
}

/// The fence `marks` make in `statement`, or why there is none.
pub fn locate(statement: &str, marks: &Marks) -> Result<Fence, String> {
    let start = statement
        .find(marks.begin)
        .filter(|_| statement.matches(marks.begin).count() == 1);
    let stop = start
        .and_then(|start| statement.get(start + 1..).map(|rest| (start, rest)))
        .and_then(|(start, rest)| rest.find(marks.end).map(|found| (start, found)));
    let Some((start, found)) = stop else {
        return Err(format!(
            "FENCE_MARKERS_NOT_UNIQUE: the {} fence needs its begin mark once and then its end mark",
            marks.name
        ));
    };
    let end = start + 1 + found + marks.end.len();
    Ok(Fence {
        name: marks.name,
        start,
        end,
        text: statement.get(start..end).unwrap_or_default().to_owned(),
    })
}

impl Fence {
    /// Whether `text` carries the fenced text exactly once.
    pub fn kept_by(&self, text: &str) -> bool {
        text.matches(self.text.as_str()).count() == 1
    }

    /// Whether the bytes from `start` up to `end` include a byte of the fence.
    pub fn touches(&self, start: usize, end: usize) -> bool {
        start.max(self.start) < end.min(self.end)
    }
}

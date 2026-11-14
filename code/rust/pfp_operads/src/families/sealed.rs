//! The sealed-value guard: no prompt leaves the host with a value from the sealed part in it.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-sealed:v1
//!
//! Two kinds of sealed value are looked for. Any sealed number or text of four or more
//! characters is a leak wherever it occurs in the prompt. A value under an answer-like key (see
//! [`ANSWER_KEYS`]) is a leak at any length when it stands in the prompt as a whole word, so a
//! short answer such as `42` is caught and the `42` inside `1420` is not. Full stops, question
//! marks and exclamation marks at the end of a word may be closing marks, so the word is also
//! looked up with each of them taken off in turn: `the total is 42.` is caught too.
//!
//! The guard reads text only. It does not see a sealed value that the prompt paraphrases,
//! splits or encodes.

use std::collections::BTreeSet;

use crate::datum::Datum;

/// Keys whose values are answers, compared without regard to case.
pub const ANSWER_KEYS: &[&str] = &[
    "answer",
    "answers",
    "expected",
    "expected_answer",
    "solution",
    "key",
    "answer_key",
];

/// The shortest sealed value that is a leak anywhere in a prompt.
pub const SUBSTRING_LENGTH: usize = 4;

/// The characters that end a word in a prompt, besides white space.
const BREAKS: &[char] = &[',', ':', ';', '[', ']', '{', '}', '(', ')', '"', '\''];

/// The marks that close a sentence. At the end of a word they are not part of it.
const CLOSERS: &[char] = &['.', '!', '?'];

/// The sealed values of one run that must not occur in any of its prompts.
#[derive(Debug, Default)]
pub struct Guard {
    substrings: BTreeSet<String>,
    words: BTreeSet<String>,
}

impl Guard {
    pub fn new(sealed: &Datum) -> Self {
        let mut guard = Guard::default();
        guard.collect(sealed, false);
        guard
    }

    fn collect(&mut self, value: &Datum, answer: bool) {
        match value {
            Datum::Map(map) => {
                for (key, inner) in map {
                    let named = ANSWER_KEYS.contains(&key.to_lowercase().as_str());
                    self.collect(inner, answer || named);
                }
            }
            Datum::List(items) => {
                for inner in items {
                    self.collect(inner, answer);
                }
            }
            Datum::Null | Datum::Bool(_) => {}
            scalar => {
                let written = scalar.canonical();
                let literal = written.trim_matches('"');
                if answer && !literal.is_empty() {
                    self.words.insert(literal.to_owned());
                }
                if literal.chars().count() >= SUBSTRING_LENGTH {
                    self.substrings.insert(literal.to_owned());
                }
            }
        }
    }

    /// True when the prompt carries a sealed value.
    pub fn leaks(&self, prompt: &str) -> bool {
        self.substrings
            .iter()
            .any(|literal| prompt.contains(literal.as_str()))
            || prompt
                .split(|letter: char| letter.is_whitespace() || BREAKS.contains(&letter))
                .any(|word| self.names(word))
    }

    /// True when the word is a sealed answer, as it stands or with closing marks taken off its
    /// end one at a time.
    fn names(&self, word: &str) -> bool {
        let mut rest = word;
        loop {
            if self.words.contains(rest) {
                return true;
            }
            match rest.strip_suffix(CLOSERS) {
                Some(shorter) => rest = shorter,
                None => return false,
            }
        }
    }
}

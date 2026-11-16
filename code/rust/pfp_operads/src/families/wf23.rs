//! WF23, judge-packet custody audit: file hashes, participant bytes with no answer in them, a
//! sealed checker, and keyed tags on every line of the judge's output.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:families-wf23:v1
//!
//! The model's reply is `{"participant": {name: text, ...}, "run": {...}}`. The sealed part
//! holds what only the host knows: `manifest` (the SHA-256 of every participant file, as the
//! host recorded it when the packet was built), `expected_answer`, `checker_source`,
//! `recorded_checker_sha256` and `stdout_key`. A manifest in the reply is not read, so
//! recomputing one after an edit proves nothing. A run whose sealed part lacks any of them is
//! refused as `MALFORMED_CANDIDATE` before anything is asked.
//!
//! A file's hash is the SHA-256 of its text with each CRLF written as LF, in UTF-8. The host
//! records, in this order:
//!
//! * `manifest_complete`: the manifest and the reply name the same files.
//! * `file_hashes_match`: every file's hash is the manifest's.
//! * `answer_not_derivable`: the expected answer, written as an integer or as `p/q`, is in no
//!   view of any file. The views are the text, the text reversed by code point, the text with
//!   every white-space character taken out (those of Python's `str.split`), and every
//!   decoding to text of each token of four or more of `A-Za-z0-9+/=`, as strict base64 (a
//!   length that is a multiple of 4, at most two `=` and only at the end) and as hex.
//! * `recorded_hash_is_checker`: the recorded hash is that of the sealed checker source.
//! * `executed_checker_is_recorded`: `run.executed_checker_sha256` is the recorded hash.
//! * `stdout_lines_authentic`: `run.stdout` (a list of objects, empty when absent) has at least
//!   one line, and every line's `tag` is the SHA-256 of the sealed key, a zero byte and the
//!   line's `line` value in canonical form.
//!
//! All six passing certifies `CUSTODY_INTACT`, with the digest of the file hashes, the files
//! that held the answer, and the number of forged lines.

use std::collections::BTreeMap;
use std::iter::once;

use crate::datum::Datum;
use crate::exact::{rational, Rational};

use super::{no_reply, sha256_hex, Checks, Family, Run, Stop, Verdict};

pub const FAMILY: Family = Family {
    workflow: "WF23",
    name: "Judge-packet custody audit",
    host_check: "judge_packet_custody_audit",
    validate,
    walk,
};

/// What the host holds.
struct Custody<'s> {
    manifest: &'s BTreeMap<String, Datum>,
    /// The expected answer as the views are searched for it.
    answer: String,
    recorded: &'s str,
    /// The hash of the sealed checker source.
    checker: String,
    key: &'s str,
}

/// A file as it is hashed: UTF-8, every CRLF written as LF.
fn canonical_file(text: &str) -> String {
    text.replace("\r\n", "\n")
}

/// A rational as text: an integer on its own, anything else as `p/q`.
fn plain(value: &Rational) -> String {
    if value.is_integer() {
        value.numer().to_string()
    } else {
        format!("{}/{}", value.numer(), value.denom())
    }
}

fn custody(sealed: &Datum) -> Result<Custody<'_>, String> {
    let text = |key: &str| {
        sealed
            .get(key)
            .and_then(Datum::as_text)
            .ok_or_else(|| format!("{key} must be text"))
    };
    let Some(Datum::Map(manifest)) = sealed.get("manifest") else {
        return Err("the host-held manifest is missing from the sealed packet".to_owned());
    };
    let answer = sealed
        .get("expected_answer")
        .and_then(rational)
        .ok_or("expected_answer must be an exact rational")?;
    Ok(Custody {
        manifest,
        answer: plain(&answer),
        recorded: text("recorded_checker_sha256")?,
        checker: sha256_hex(&canonical_file(text("checker_source")?)),
        key: text("stdout_key")?,
    })
}

/// The task needs nothing. The sealed part is read in the walk, so that a run with no sealed
/// part still starts: the host holds it, and the caller who asks does not.
fn validate(_task: &Datum, _sealed: &Datum) -> Result<(), String> {
    Ok(())
}

/// Whether Python's `str.split` takes the character for white space.
fn is_space(letter: char) -> bool {
    letter.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&letter)
}

/// The value of a base64 digit.
fn sextet(digit: u8) -> Option<u32> {
    match digit {
        b'A'..=b'Z' => Some(u32::from(digit - b'A')),
        b'a'..=b'z' => Some(u32::from(digit - b'a') + 26),
        b'0'..=b'9' => Some(u32::from(digit - b'0') + 52),
        b'+' => Some(62),
        b'/' => Some(63),
        _ => None,
    }
}

/// The bytes of strict base64: digits, then at most two `=`, in a multiple of four characters.
/// Bits that do not fill a byte are dropped.
fn base64(token: &str) -> Option<Vec<u8>> {
    let digits = token.trim_end_matches('=');
    if token.len() - digits.len() > 2 || !token.len().is_multiple_of(4) {
        return None;
    }
    let mut out = Vec::new();
    let (mut held, mut width) = (0u32, 0u32);
    for digit in digits.bytes() {
        held = (held << 6) | sextet(digit)?;
        width += 6;
        if width >= 8 {
            width -= 8;
            out.push(u8::try_from(held >> width).ok()?);
            held &= (1 << width) - 1;
        }
    }
    Some(out)
}

/// The tokens of four or more characters that base64 and hex are written in.
fn tokens(text: &str) -> impl Iterator<Item = &str> {
    text.split(|letter: char| {
        !(letter.is_ascii_alphanumeric() || matches!(letter, '+' | '/' | '='))
    })
    .filter(|token| token.len() >= 4)
}

/// The text a token decodes to, as base64 and as hex.
fn decodings(token: &str) -> impl Iterator<Item = String> {
    [base64(token), hex::decode(token).ok()]
        .into_iter()
        .flatten()
        .filter_map(|bytes| String::from_utf8(bytes).ok())
}

/// Whether the answer is in the text, reversed, with white space taken out, or in the text a
/// token of it decodes to.
fn derivable(text: &str, answer: &str) -> bool {
    let reversed: String = text.chars().rev().collect();
    let squeezed: String = text.chars().filter(|&letter| !is_space(letter)).collect();
    once(text.to_owned())
        .chain([reversed, squeezed])
        .chain(tokens(text).flat_map(decodings))
        .any(|view| view.contains(answer))
}

/// The reply's files, as name and text, and its run record.
fn submission(reply: &Datum) -> Result<(BTreeMap<&str, &str>, &Datum), Stop> {
    let (Some(Datum::Map(files)), Some(run @ Datum::Map(_))) =
        (reply.get("participant"), reply.get("run"))
    else {
        return Err(Stop::Malformed("packet fields".to_owned()));
    };
    let texts: Option<BTreeMap<&str, &str>> = files
        .iter()
        .map(|(name, text)| text.as_text().map(|text| (name.as_str(), text)))
        .collect();
    let texts = texts.ok_or_else(|| Stop::Malformed("participant files are text".to_owned()))?;
    Ok((texts, run))
}

/// The lines of the run's stdout, when it is a list of objects.
fn lines(run: &Datum) -> Result<&[Datum], Stop> {
    let lines: &[Datum] = match run.get("stdout") {
        None => &[],
        Some(Datum::List(lines)) => lines.as_slice(),
        Some(_) => return Err(Stop::Malformed("stdout is a list of lines".to_owned())),
    };
    if lines.iter().all(Datum::is_map) {
        Ok(lines)
    } else {
        Err(Stop::Malformed("stdout is a list of lines".to_owned()))
    }
}

/// The tag of a line under the key.
fn tag(key: &str, line: &Datum) -> String {
    sha256_hex(&format!("{key}\u{0}{}", line.canonical()))
}

fn walk(run: &mut Run, checks: &mut Checks) -> Result<Verdict, Stop> {
    let held = custody(run.sealed).map_err(Stop::Malformed)?;
    let Some(reply) = run.ask("packet", run.prompt())? else {
        return Ok(no_reply());
    };
    let (files, record) = submission(reply)?;
    let hashes: BTreeMap<&str, String> = files
        .iter()
        .map(|(name, text)| (*name, sha256_hex(&canonical_file(text))))
        .collect();
    let named = held
        .manifest
        .keys()
        .map(String::as_str)
        .eq(files.keys().copied());
    checks.record("manifest_complete", named, &Datum::Null);
    let matching = hashes.iter().all(|(name, hash)| {
        held.manifest.get(*name).and_then(Datum::as_text) == Some(hash.as_str())
    });
    checks.record("file_hashes_match", matching, &Datum::Null);
    let leaked: Vec<&str> = files
        .iter()
        .filter(|(_, text)| derivable(text, &held.answer))
        .map(|(name, _)| *name)
        .collect();
    checks.record(
        "answer_not_derivable",
        leaked.is_empty(),
        &Datum::from(leaked.clone()),
    );
    checks.record(
        "recorded_hash_is_checker",
        held.recorded == held.checker,
        &Datum::Null,
    );
    let executed = record
        .get("executed_checker_sha256")
        .and_then(Datum::as_text);
    checks.record(
        "executed_checker_is_recorded",
        executed == Some(held.recorded),
        &Datum::Null,
    );
    let output = lines(record)?;
    let forged = output
        .iter()
        .filter(|line| {
            let expected = tag(held.key, line.get("line").unwrap_or(&Datum::Null));
            line.get("tag").and_then(Datum::as_text) != Some(expected.as_str())
        })
        .count();
    checks.record(
        "stdout_lines_authentic",
        !output.is_empty() && forged == 0,
        &Datum::from(forged),
    );
    let digest = Datum::Map(
        hashes
            .iter()
            .map(|(name, hash)| ((*name).to_owned(), Datum::text(hash.as_str())))
            .collect(),
    );
    let detail = Datum::map([
        (
            "participant_sha256",
            Datum::text(sha256_hex(&digest.canonical())),
        ),
        ("leaked_files", Datum::from(leaked)),
        ("forged_lines", Datum::from(forged)),
    ]);
    Ok(checks.judge("CUSTODY_INTACT", detail))
}

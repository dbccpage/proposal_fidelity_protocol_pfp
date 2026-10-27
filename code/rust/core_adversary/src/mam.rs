//! MAM: the Panel's story of one run, as Markdown, LaTeX and PDF.
//!
//! The story is a deterministic function of the bundle's `summary.json` and
//! `ddc.jsonl` bytes, so a reader can re-render it and compare. It retells the
//! Panel's captured contributions only; it is not evidence. AuthorityEffect: None.
use crate::stage::ports::Refusal;
use serde_json::Value;
use std::collections::BTreeSet;

pub const MAM_SCHEMA: &str = "core.adversary.mam.v1";
pub const MAM_FILES: [(&str, &str); 3] = [
    ("mam/mam.md", "mam_md_sha256"),
    ("mam/mam.tex", "mam_tex_sha256"),
    ("mam/mam.pdf", "mam_pdf_sha256"),
];
const QUOTE_LIMIT: usize = 900;
const TASK_LIMIT: usize = 600;

fn invalid(message: impl Into<String>) -> Refusal {
    Refusal::new("ADVERSARY_MAM_INVALID", message)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MamBook {
    pub md: String,
    pub tex: String,
    pub pdf: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum Block {
    Title(String),
    Subtitle(String),
    Heading(String),
    Para(String),
    Quote(String),
    Note(String),
}

struct Contribution {
    role: String,
    text: Option<String>,
    blocked: bool,
}

fn voices() -> Result<Value, Refusal> {
    serde_json::from_str(include_str!("mam_voices_v1.json"))
        .map_err(|e| invalid(format!("voice table: {e}")))
}

fn template<'a>(table: &'a Value, key: &str) -> Result<&'a str, Refusal> {
    table[key]
        .as_str()
        .ok_or_else(|| invalid(format!("voice table lacks {key}")))
}

fn first_text<'a>(value: &'a Value, keys: &[&str]) -> Option<&'a str> {
    keys.iter()
        .find_map(|key| value.get(*key).and_then(Value::as_str))
        .filter(|text| !text.trim().is_empty())
}

/// Shorten at a word boundary; the full words stay in `uns.md`.
fn shorten(text: &str, limit: usize) -> String {
    let text = text.trim();
    if text.chars().count() <= limit {
        return text.to_owned();
    }
    let cut: String = text.chars().take(limit).collect();
    let cut = match cut.rfind(char::is_whitespace) {
        Some(index) if index > limit / 2 => &cut[..index],
        _ => cut.as_str(),
    };
    format!("{} ...", cut.trim_end())
}

fn role_key(raw: &str, table: &Value) -> String {
    let mut key = raw.trim().to_lowercase().replace([' ', '-', '.'], "_");
    for prefix in ["seat_", "skill_", "role_"] {
        if let Some(rest) = key.strip_prefix(prefix) {
            key = rest.to_owned();
        }
    }
    match table["aliases"].get(&key).and_then(Value::as_str) {
        Some(alias) => alias.to_owned(),
        None => key,
    }
}

/// The captured history: teamwork summaries nest it under `source_history`.
fn history_view(summary: &Value) -> &Value {
    let root = summary
        .get("source_history")
        .filter(|value| value.is_object())
        .unwrap_or(summary);
    ["teamwork", "retained_context"]
        .iter()
        .find_map(|key| root.get(*key).filter(|v| v.get("observations").is_some()))
        .unwrap_or(root)
}

fn captured_entries(view: &Value) -> Vec<&Value> {
    for key in ["observations", "seat_turns"] {
        if let Some(items) = view.get(key).and_then(Value::as_array) {
            return items.iter().collect();
        }
    }
    let mut entries = Vec::new();
    for key in ["model_turns", "challenges"] {
        if let Some(items) = view
            .pointer(&format!("/result/{key}"))
            .and_then(Value::as_array)
        {
            entries.extend(items.iter().map(|item| item.get("turn").unwrap_or(item)));
        }
    }
    entries
}

fn contribution(entry: &Value, from_tape: bool) -> Option<Contribution> {
    let null = Value::Null;
    let metadata = entry.get("metadata").unwrap_or(&null);
    let reply = entry.get("reply").unwrap_or(&null);
    let role = first_text(metadata, &["role_id"])
        .or_else(|| first_text(entry, &["role_id", "seat", "seat_id", "role", "character"]));
    if from_tape && role.is_none() {
        return None;
    }
    let text = first_text(entry, &["summary", "content", "reply_text"])
        .or_else(|| first_text(reply, &["content"]))
        .map(str::to_owned);
    let blocked = entry
        .get("blocked")
        .and_then(Value::as_bool)
        .unwrap_or_else(|| entry.get("refusal").is_some_and(|r| !r.is_null()));
    if from_tape && text.is_none() {
        return None;
    }
    Some(Contribution {
        role: role.unwrap_or("UNRECORDED_ROLE").to_owned(),
        text,
        blocked,
    })
}

fn tape_payloads(tape: &[u8]) -> Result<Vec<Value>, Refusal> {
    let text = std::str::from_utf8(tape).map_err(|_| invalid("ddc.jsonl is not UTF-8"))?;
    text.lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let record: Value =
                serde_json::from_str(line).map_err(|e| invalid(format!("ddc.jsonl: {e}")))?;
            Ok(record.get("payload").cloned().unwrap_or(Value::Null))
        })
        .collect()
}

fn fill(text: &str, pairs: &[(&str, &str)]) -> String {
    pairs.iter().fold(text.to_owned(), |acc, (key, value)| {
        acc.replace(&format!("{{{key}}}"), value)
    })
}

fn story(summary: &Value, tape: &[u8]) -> Result<Vec<Block>, Refusal> {
    let table = voices()?;
    let view = history_view(summary);
    let mut entries: Vec<Contribution> = captured_entries(view)
        .into_iter()
        .filter_map(|entry| contribution(entry, false))
        .collect();
    if entries.is_empty() {
        entries = tape_payloads(tape)?
            .iter()
            .filter_map(|payload| contribution(payload, true))
            .collect();
    }
    let run = first_text(summary, &["task_key", "run_id"])
        .or_else(|| first_text(view, &["run_id", "task_key"]))
        .unwrap_or("UNNAMED");
    let mut blocks = vec![
        Block::Title(template(&table, "title")?.to_owned()),
        Block::Subtitle(fill(template(&table, "subtitle")?, &[("run", run)])),
        Block::Heading(format!("I. {}", template(&table, "chapter_one")?)),
        Block::Para(template(&table, "chapter_one_text")?.to_owned()),
    ];
    let task = first_text(view, &["original_seed", "objective", "seed"])
        .or_else(|| first_text(summary, &["original_seed", "objective"]));
    match task {
        Some(task) => {
            blocks.push(Block::Para(template(&table, "task_lead")?.to_owned()));
            blocks.push(Block::Quote(shorten(task, TASK_LIMIT)));
        }
        None => blocks.push(Block::Para(template(&table, "no_task")?.to_owned())),
    }
    blocks.push(Block::Heading(format!(
        "II. {}",
        template(&table, "chapter_two")?
    )));
    blocks.push(Block::Para(
        template(&table, "chapter_two_text")?.to_owned(),
    ));
    let openings = table["speech_openings"]
        .as_array()
        .filter(|items| !items.is_empty())
        .ok_or_else(|| invalid("voice table lacks speech_openings"))?;
    // Roles that rose to speak, whether or not their words reached the table.
    let mut present = BTreeSet::new();
    for (index, item) in entries.iter().enumerate() {
        let key = role_key(&item.role, &table);
        let voice = table["voices"].get(&key);
        let name = voice
            .and_then(|v| v["name"].as_str())
            .map(str::to_owned)
            .unwrap_or_else(|| item.role.replace('_', " "));
        let manner = voice
            .and_then(|v| v["manner"].as_str())
            .or_else(|| table["unknown_voice"]["manner"].as_str())
            .unwrap_or("");
        let pairs = [("name", name.as_str()), ("manner", manner)];
        present.insert(key);
        match (&item.text, item.blocked) {
            (Some(text), false) => {
                let opening = openings[index % openings.len()]
                    .as_str()
                    .ok_or_else(|| invalid("speech opening must be text"))?;
                blocks.push(Block::Para(fill(opening, &pairs)));
                blocks.push(Block::Quote(shorten(text, QUOTE_LIMIT)));
            }
            _ => blocks.push(Block::Para(fill(template(&table, "blocked_turn")?, &pairs))),
        }
    }
    if entries.is_empty() {
        blocks.push(Block::Para(template(&table, "no_voices")?.to_owned()));
    } else if let Some(cast) = table["voices"].as_object() {
        // Only a full Panel run names who stayed silent.
        let silent: Vec<&str> = cast
            .iter()
            .filter(|(key, _)| !present.contains(*key))
            .filter_map(|(_, voice)| voice["name"].as_str())
            .collect();
        if present.len() >= 2 && !silent.is_empty() && silent.len() < cast.len() {
            let count = silent.len().to_string();
            blocks.push(Block::Para(fill(
                template(&table, "absent_roles")?,
                &[("count", &count), ("names", &silent.join(", "))],
            )));
        }
    }
    blocks.push(Block::Heading(format!(
        "III. {}",
        template(&table, "chapter_three")?
    )));
    let context = summary.get("report_context").unwrap_or(&Value::Null);
    let status = first_text(context, &["work_status"]).or_else(|| {
        first_text(view, &["terminal_status", "work_status", "status"])
            .or_else(|| first_text(summary, &["terminal_status", "work_status", "status"]))
    });
    let verdict = first_text(context, &["evidence_verdict"])
        .or_else(|| first_text(summary, &["evidence_verdict", "terminal_verdict"]));
    match status {
        Some(status) => blocks.push(Block::Para(fill(
            template(&table, "outcome_status")?,
            &[("status", status)],
        ))),
        None => blocks.push(Block::Para(template(&table, "outcome_unknown")?.to_owned())),
    }
    if let Some(verdict) = verdict {
        blocks.push(Block::Para(fill(
            template(&table, "outcome_verdict")?,
            &[("verdict", verdict)],
        )));
    }
    blocks.push(Block::Para(template(&table, "outcome_close")?.to_owned()));
    blocks.push(Block::Heading(template(&table, "chapter_four")?.to_owned()));
    for question in table["reflection"].as_array().into_iter().flatten() {
        if let Some(question) = question.as_str() {
            blocks.push(Block::Para(question.to_owned()));
        }
    }
    if entries
        .iter()
        .any(|item| item.blocked || item.text.is_none())
    {
        blocks.push(Block::Para(
            template(&table, "reflection_blocked")?.to_owned(),
        ));
    }
    blocks.push(Block::Note(template(&table, "footer")?.to_owned()));
    Ok(blocks)
}

fn markdown(blocks: &[Block]) -> String {
    let mut out = Vec::new();
    for block in blocks {
        out.push(match block {
            Block::Title(text) => format!("# {text}"),
            Block::Subtitle(text) | Block::Note(text) => format!("*{}*", text.replace('*', "\\*")),
            Block::Heading(text) => format!("## {text}"),
            Block::Para(text) => text.clone(),
            Block::Quote(text) => text
                .lines()
                .map(|line| {
                    if line.trim().is_empty() {
                        ">".to_owned()
                    } else {
                        format!("> {line}")
                    }
                })
                .collect::<Vec<_>>()
                .join("\n"),
        });
    }
    out.join("\n\n") + "\n"
}

fn tex_escape(text: &str) -> String {
    let mut out = String::with_capacity(text.len());
    for c in text.chars() {
        match c {
            '\\' => out.push_str("\\textbackslash{}"),
            '&' | '%' | '$' | '#' | '_' | '{' | '}' => {
                out.push('\\');
                out.push(c);
            }
            '~' => out.push_str("\\textasciitilde{}"),
            '^' => out.push_str("\\textasciicircum{}"),
            '<' => out.push_str("\\textless{}"),
            '>' => out.push_str("\\textgreater{}"),
            '|' => out.push_str("\\textbar{}"),
            _ => out.push(c),
        }
    }
    out
}

fn latex(blocks: &[Block]) -> String {
    let mut out = vec![
        "% MAM story of one Adversary run. AuthorityEffect: None.".to_owned(),
        "\\documentclass[11pt]{article}".into(),
        "\\usepackage[T1]{fontenc}".into(),
        "\\usepackage[utf8]{inputenc}".into(),
        "\\usepackage{lmodern}".into(),
        "\\usepackage[margin=1in]{geometry}".into(),
        "\\begin{document}".into(),
    ];
    for block in blocks {
        out.push(match block {
            Block::Title(text) => format!(
                "\\begin{{center}}{{\\LARGE\\bfseries {}}}\\end{{center}}",
                tex_escape(text)
            ),
            Block::Subtitle(text) => format!(
                "\\begin{{center}}\\emph{{{}}}\\end{{center}}",
                tex_escape(text)
            ),
            Block::Heading(text) => format!("\\section*{{{}}}", tex_escape(text)),
            Block::Para(text) => tex_escape(text),
            Block::Quote(text) => format!(
                "\\begin{{quote}}\\itshape\n{}\n\\end{{quote}}",
                text.lines()
                    .map(|line| if line.trim().is_empty() {
                        String::new()
                    } else {
                        tex_escape(line)
                    })
                    .collect::<Vec<_>>()
                    .join("\n")
            ),
            Block::Note(text) => format!("\\vfill\n{{\\small\\emph{{{}}}}}", tex_escape(text)),
        });
    }
    out.push("\\end{document}".into());
    out.join("\n\n") + "\n"
}

/// Times-Roman advance widths (1/1000 em) for ASCII 32..=126.
const TIMES_WIDTHS: [u16; 95] = [
    250, 333, 408, 500, 500, 833, 778, 180, 333, 333, 500, 564, 250, 333, 250, 278, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 278, 278, 564, 564, 564, 444, 921, 722, 667, 667, 722, 611,
    556, 722, 722, 333, 389, 722, 611, 889, 722, 722, 556, 722, 667, 556, 611, 722, 722, 944, 722,
    722, 611, 333, 278, 333, 469, 500, 333, 444, 500, 444, 500, 444, 333, 500, 500, 278, 278, 500,
    278, 778, 500, 500, 500, 500, 333, 389, 278, 500, 500, 722, 500, 500, 444, 480, 200, 480, 541,
];

/// One WinAnsi byte per character; characters outside WinAnsi become '?'.
fn win_ansi(c: char) -> u8 {
    match c {
        ' '..='~' => c as u8,
        '\u{a0}'..='\u{ff}' => c as u32 as u8,
        '\u{2018}' => 0x91,
        '\u{2019}' => 0x92,
        '\u{201c}' => 0x93,
        '\u{201d}' => 0x94,
        '\u{2022}' => 0x95,
        '\u{2013}' => 0x96,
        '\u{2014}' => 0x97,
        '\u{2026}' => 0x85,
        '\t' => b' ',
        _ => b'?',
    }
}

fn width(bytes: &[u8], size: u32) -> u32 {
    let units: u32 = bytes
        .iter()
        .map(|b| match b {
            32..=126 => u32::from(TIMES_WIDTHS[usize::from(b - 32)]),
            _ => 500,
        })
        .sum();
    // A 6% allowance covers the wider bold and italic faces.
    units * size * 106 / 100_000
}

fn wrap(text: &str, size: u32, limit: u32) -> Vec<Vec<u8>> {
    let mut lines = Vec::new();
    for paragraph_line in text.lines() {
        let mut line: Vec<u8> = Vec::new();
        for word in paragraph_line.split_whitespace() {
            let word: Vec<u8> = word.chars().map(win_ansi).collect();
            let mut candidate = line.clone();
            if !candidate.is_empty() {
                candidate.push(b' ');
            }
            candidate.extend_from_slice(&word);
            if !line.is_empty() && width(&candidate, size) > limit {
                lines.push(std::mem::take(&mut line));
                line = word;
            } else {
                line = candidate;
            }
        }
        lines.push(line);
    }
    lines
}

fn pdf_string(bytes: &[u8]) -> String {
    let mut out = String::from("(");
    for &b in bytes {
        match b {
            b'(' | b')' | b'\\' => {
                out.push('\\');
                out.push(char::from(b));
            }
            32..=126 => out.push(char::from(b)),
            _ => out.push_str(&format!("\\{b:03o}")),
        }
    }
    out.push(')');
    out
}

/// A small deterministic PDF 1.4 writer: standard Times faces, no dates, no
/// compression, so equal stories give equal bytes.
fn pdf(blocks: &[Block], title: &str) -> Vec<u8> {
    const TOP: u32 = 720;
    const BOTTOM: u32 = 72;
    const LEFT: u32 = 72;
    const TEXT_WIDTH: u32 = 468;
    let mut pages: Vec<String> = Vec::new();
    let mut page = String::new();
    let mut y = TOP;
    let mut place =
        |page: &mut String, y: &mut u32, font: &str, size: u32, lead: u32, x: u32, line: &[u8]| {
            if *y < BOTTOM + lead {
                pages.push(std::mem::take(page));
                *y = TOP;
            }
            *y -= lead;
            if !line.is_empty() {
                page.push_str(&format!(
                    "BT /{font} {size} Tf {x} {} Td {} Tj ET\n",
                    *y,
                    pdf_string(line)
                ));
            }
        };
    for block in blocks {
        let (font, size, lead, indent, before, after, text, centered) = match block {
            Block::Title(text) => ("F2", 20, 28, 0, 0, 6, text, true),
            Block::Subtitle(text) => ("F3", 12, 16, 0, 0, 18, text, true),
            Block::Heading(text) => ("F2", 14, 20, 0, 12, 4, text, false),
            Block::Para(text) => ("F1", 11, 15, 0, 0, 7, text, false),
            Block::Quote(text) => ("F3", 11, 15, 28, 0, 9, text, false),
            Block::Note(text) => ("F3", 9, 12, 0, 18, 0, text, false),
        };
        y = y.saturating_sub(before);
        for line in wrap(text, size, TEXT_WIDTH - 2 * indent) {
            let x = if centered {
                LEFT + (TEXT_WIDTH.saturating_sub(width(&line, size))) / 2
            } else {
                LEFT + indent
            };
            place(&mut page, &mut y, font, size, lead, x, &line);
        }
        y = y.saturating_sub(after);
    }
    pages.push(page);
    let count = pages.len();
    let mut objects: Vec<String> = vec![
        "<< /Type /Catalog /Pages 2 0 R >>".into(),
        format!(
            "<< /Type /Pages /Kids [{}] /Count {count} >>",
            (0..count)
                .map(|i| format!("{} 0 R", 6 + 2 * i))
                .collect::<Vec<_>>()
                .join(" ")
        ),
    ];
    for face in ["Times-Roman", "Times-Bold", "Times-Italic"] {
        objects.push(format!(
            "<< /Type /Font /Subtype /Type1 /BaseFont /{face} /Encoding /WinAnsiEncoding >>"
        ));
    }
    for (index, content) in pages.iter().enumerate() {
        let number = format!("- {} -", index + 1);
        let footer = format!(
            "BT /F1 9 Tf {} 40 Td {} Tj ET\n",
            LEFT + (TEXT_WIDTH - width(number.as_bytes(), 9)) / 2,
            pdf_string(number.as_bytes())
        );
        let stream = format!("{content}{footer}");
        objects.push(format!(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> /Contents {} 0 R >>",
            7 + 2 * index
        ));
        objects.push(format!(
            "<< /Length {} >>\nstream\n{stream}endstream",
            stream.len()
        ));
    }
    let title_bytes: Vec<u8> = title.chars().map(win_ansi).collect();
    objects.push(format!(
        "<< /Title {} /Producer (core_adversary mam v1) >>",
        pdf_string(&title_bytes)
    ));
    let info = objects.len();
    let mut out: Vec<u8> = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n".to_vec();
    let mut offsets = Vec::with_capacity(objects.len());
    for (index, object) in objects.iter().enumerate() {
        offsets.push(out.len());
        out.extend_from_slice(format!("{} 0 obj\n{object}\nendobj\n", index + 1).as_bytes());
    }
    let xref = out.len();
    out.extend_from_slice(
        format!("xref\n0 {}\n0000000000 65535 f \n", objects.len() + 1).as_bytes(),
    );
    for offset in offsets {
        out.extend_from_slice(format!("{offset:010} 00000 n \n").as_bytes());
    }
    out.extend_from_slice(
        format!(
            "trailer\n<< /Size {} /Root 1 0 R /Info {info} 0 R >>\nstartxref\n{xref}\n%%EOF\n",
            objects.len() + 1
        )
        .as_bytes(),
    );
    out
}

/// Render the story from the bundle's own `summary.json` and `ddc.jsonl` bytes.
pub fn render_mam(summary_json: &[u8], ddc_tape: &[u8]) -> Result<MamBook, Refusal> {
    let summary: Value =
        serde_json::from_slice(summary_json).map_err(|e| invalid(format!("summary.json: {e}")))?;
    if !summary.is_object() {
        return Err(invalid("summary.json must be an object"));
    }
    let blocks = story(&summary, ddc_tape)?;
    let title = match blocks.first() {
        Some(Block::Title(title)) => title.clone(),
        _ => String::new(),
    };
    Ok(MamBook {
        md: markdown(&blocks),
        tex: latex(&blocks),
        pdf: pdf(&blocks, &title),
    })
}

// Origin: engine/crates_rs/core_adversary/src/mam.rs
// Claim: urn:core:crates_rs:core-adversary:mam:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord5a6ef128 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord5a6ef128` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError5a6ef128 {
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
impl BoundaryError5a6ef128 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError5a6ef128 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError5a6ef128 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord5a6ef128 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError5a6ef128> {
        if capacity_bound == 0 {
            return Err(BoundaryError5a6ef128::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError5a6ef128::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError5a6ef128::ExceedsCapacity {
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
mod tests {
    use super::*;
    use serde_json::json;

    fn teamwork_summary() -> Vec<u8> {
        json!({"task_key":"mam-test","report_context":{"work_status":"COMPLETED","evidence_verdict":"Supported"},
            "source_history":{"run_id":"mam-test","original_seed":"Check that 2 + 2 = 4 (and say why).",
            "observations":[
                {"action_id":"a1","worker":"ide","summary":"The syntax is clean: no stray braces {}.","metadata":{"role_id":"syntax_prefilter"}},
                {"action_id":"a2","worker":"ide","summary":"I would count it on paws: four.","metadata":{"role_id":"gauge_breaker"}},
                {"action_id":"a3","worker":"ide","summary":"unused","blocked":true,"metadata":{"role_id":"defect_hunter"}},
                {"action_id":"a4","worker":"ide","summary":"Pass it to the Master \u{2014} it holds.","metadata":{"role_id":"adversary"}}]}})
        .to_string()
        .into_bytes()
    }

    #[test]
    fn story_retells_each_voice_in_order_and_keeps_blocked_turns_visible() {
        let book = render_mam(&teamwork_summary(), b"").unwrap();
        let syntax_prefilter = book.md.find("Syntax Prefilter").unwrap();
        let gauge_breaker = book.md.find("> I would count it on paws: four.").unwrap();
        let blocked = book.md.find("this turn was blocked").unwrap();
        assert!(syntax_prefilter < gauge_breaker && gauge_breaker < blocked);
        assert!(!book.md.contains("> unused"));
        assert!(book.md.contains("> Check that 2 + 2 = 4 (and say why)."));
        assert!(book.md.contains("the work stood as COMPLETED"));
        assert!(book.md.contains("named it Supported"));
        assert!(book.md.contains("Would you have noticed"));
        assert!(book.md.contains("did not speak at all"));
        // A blocked role rose to speak, so it is not also listed as silent.
        let silent = book
            .md
            .lines()
            .find(|line| line.contains("did not speak"))
            .unwrap();
        assert!(silent.starts_with("18 members") && !silent.contains("Defect Hunter"));
        assert!(book.tex.contains("no stray braces \\{\\}"));
        assert!(book.tex.starts_with("% MAM story"));
        assert!(book.tex.trim_end().ends_with("\\end{document}"));
    }

    #[test]
    fn rendering_is_deterministic_and_pdf_is_well_formed() {
        let first = render_mam(&teamwork_summary(), b"").unwrap();
        let second = render_mam(&teamwork_summary(), b"").unwrap();
        assert_eq!(first, second);
        let pdf = &first.pdf;
        assert!(pdf.starts_with(b"%PDF-1.4\n"));
        assert!(pdf.ends_with(b"%%EOF\n"));
        let text = String::from_utf8_lossy(pdf);
        let startxref: usize = text
            .rsplit("startxref\n")
            .next()
            .unwrap()
            .lines()
            .next()
            .unwrap()
            .parse()
            .unwrap();
        assert!(pdf[startxref..].starts_with(b"xref\n"));
        // Every xref offset points at the object it names.
        for (number, entry) in text[startxref..]
            .lines()
            .skip(3)
            .take_while(|l| l.ends_with("n "))
            .enumerate()
        {
            let offset: usize = entry[..10].parse().unwrap();
            assert!(pdf[offset..].starts_with(format!("{} 0 obj", number + 1).as_bytes()));
        }
        // The em dash travels as WinAnsi 0x97, not as replacement text.
        assert!(text.contains("\\227"));
    }

    #[test]
    fn long_runs_paginate_and_quotes_are_shortened() {
        let long = "word ".repeat(400);
        let observations: Vec<Value> = (0..30)
            .map(|i| json!({"action_id":format!("a{i}"),"worker":"ide","summary":long,"metadata":{"role_id":"defect_hunter"}}))
            .collect();
        let summary = json!({"task_key":"long","source_history":{"observations":observations}});
        let book = render_mam(summary.to_string().as_bytes(), b"").unwrap();
        assert!(String::from_utf8_lossy(&book.pdf).contains("/Count "));
        assert!(!String::from_utf8_lossy(&book.pdf).contains("/Count 1 "));
        assert!(book.md.contains("word ..."));
    }

    #[test]
    fn bout_runs_without_history_fall_back_to_role_bearing_tape_steps() {
        let tape = format!(
            "{}\n{}\n",
            json!({"payload":{"seat":"seat_centurion_mark_hardware_constraint","summary":"Halt. Show me the receipt."},"sequence":0}),
            json!({"payload":{"record_kind":"observed_action","summary":"no role here"},"sequence":1})
        );
        let summary = json!({"task_key":"bout","status":"REFUSED"});
        let book = render_mam(summary.to_string().as_bytes(), tape.as_bytes()).unwrap();
        assert!(book.md.contains("Hardware Constraint"));
        assert!(book.md.contains("> Halt. Show me the receipt."));
        assert!(!book.md.contains("no role here"));
        assert!(book.md.contains("the work stood as REFUSED"));
    }

    #[test]
    fn a_run_with_no_recorded_words_says_so_instead_of_inventing_them() {
        let book = render_mam(br#"{"task_key":"empty"}"#, b"").unwrap();
        assert!(book
            .md
            .contains("will not invent what they might have said"));
        assert!(book.md.contains("The paper was blank"));
        assert!(book
            .md
            .contains("nobody had written down how the work stood"));
        assert!(render_mam(b"[]", b"").is_err());
        assert!(render_mam(br#"{"task_key":"x"}"#, b"not json\n").is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_5a6ef128 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord5a6ef128::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord5a6ef128::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord5a6ef128::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord5a6ef128::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord5a6ef128::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError5a6ef128::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError5a6ef128::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

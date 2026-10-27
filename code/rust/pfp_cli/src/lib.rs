//! pfp: offline, read-only checks for prompts and model replies, and
//! tamper-evident packets for the files you propose.
//!
//! AuthorityEffect: None. Nothing here grants, admits or approves anything. An
//! empty report means the named detectors found nothing in the named bytes.
//!
//! The library does no file or network I/O; `main.rs` reads files and prints.
//! That keeps the core portable to wasm32 for the browser playground.

pub mod catalog;
pub mod check;
pub mod packet;
pub mod skills;

pub use check::{
    builtin_checks, read_doc, run_checks, Check, Doc, Finding, Input, Report, Severity, Text,
};

/// `pfp-cli <version>`, recorded in every packet.
pub const TOOL: &str = concat!("pfp-cli ", env!("CARGO_PKG_VERSION"));

/// The bundled demo: a prompt and a reply with typical problems.
pub const DEMO_PROMPT: &str = include_str!("../demo/prompt.md");
pub const DEMO_REPLY: &str = include_str!("../demo/reply.json");

/// Render a report for a terminal. `color` adds ANSI colors.
pub fn render_report(report: &Report, color: bool) -> String {
    let paint = |code: &str, text: &str| {
        if color {
            format!("\x1b[{code}m{text}\x1b[0m")
        } else {
            text.to_owned()
        }
    };
    let place_of = |f: &Finding| match (f.line, f.pointer.as_str()) {
        (Some(line), "") => format!("line {line}"),
        (Some(line), pointer) => format!("line {line} {}", clean(pointer)),
        (None, pointer) => clean(pointer),
    };
    let code_width = report
        .findings
        .iter()
        .map(|f| f.code.len())
        .max()
        .unwrap_or(0);
    let place_width = report
        .findings
        .iter()
        .map(|f| place_of(f).chars().count())
        .max()
        .unwrap_or(0);
    let mut out = String::new();
    let mut current = "";
    for f in &report.findings {
        if f.source != current {
            current = &f.source;
            out.push_str(&paint("1", &clean(current)));
            out.push('\n');
        }
        let place = place_of(f);
        let severity = match f.severity {
            Severity::Refuse => paint("31", "REFUSE "),
            Severity::Hold => paint("33", "HOLD   "),
            Severity::Finding => paint("36", "FINDING"),
        };
        out.push_str(&format!(
            "  {severity}  {:<code_width$}  {:<place_width$}  {}\n",
            f.code,
            place,
            clean(catalog::find(&f.code).map_or(f.message.as_str(), |e| e.short))
        ));
    }
    let detectors = report.detectors_run.len();
    if report.findings.is_empty() {
        out.push_str(&format!(
            "No findings from {detectors} detectors. That is not proof the text is right.\n"
        ));
    } else {
        out.push_str(&format!(
            "\n{} from {detectors} detectors. Nothing was changed.\nLearn more: pfp explain {}\n",
            count(report.findings.len(), "finding"),
            report.findings[0].code
        ));
    }
    out
}

/// Escape control characters so text from a file or a model cannot move the
/// cursor, rewrite earlier lines, or retitle the terminal.
pub fn clean(text: &str) -> String {
    text.chars()
        .flat_map(|c| {
            let escaped: Vec<char> = if c.is_control() {
                c.escape_default().collect()
            } else {
                vec![c]
            };
            escaped
        })
        .collect()
}

/// `1 finding`, `2 findings`.
pub fn count(n: usize, noun: &str) -> String {
    if n == 1 {
        format!("1 {noun}")
    } else {
        format!("{n} {noun}s")
    }
}

/// Render one catalog entry for `pfp explain`.
pub fn render_explain(entry: &catalog::Entry) -> String {
    let mut out = format!("{}: {}\n\n", entry.code, entry.short);
    for (label, text) in [
        ("What", entry.what),
        ("Why", entry.why),
        ("Instead", entry.instead),
    ] {
        out.push_str(&wrap(&format!("{label}:"), text));
    }
    out.push_str(&format!("  Read:    {}\n", catalog::wiki_url(entry.wiki)));
    out
}

/// Word-wrap `text` at 78 columns under an 11-column hanging label.
fn wrap(label: &str, text: &str) -> String {
    const INDENT: usize = 11;
    const WIDTH: usize = 78;
    let mut out = format!("  {label:<width$}", width = INDENT - 2);
    let mut column = INDENT;
    for word in text.split_whitespace() {
        let len = word.chars().count();
        if column > INDENT && column + 1 + len > WIDTH {
            out.push('\n');
            out.push_str(&" ".repeat(INDENT));
            column = INDENT;
        } else if column > INDENT {
            out.push(' ');
            column += 1;
        }
        out.push_str(word);
        column += len;
    }
    out.push('\n');
    out
}

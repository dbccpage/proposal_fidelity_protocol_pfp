//! Checks: deterministic detectors over a prompt and the texts produced from it.
//!
//! AuthorityEffect: None. A check names what it found and nothing else: there is
//! no field for a repair, and an empty result is not a proof that a text is right.
//!
//! Every output is parsed once, by [`read_doc`], into a [`Doc`]; checks read
//! documents, never raw bytes. To add a check, implement [`Check`], list it in
//! [`builtin_checks`], and give each code an entry in [`crate::catalog`].

use core_prompt_civilization::pharmacy::semantic_payload_digest;
use core_prompt_civilization::{detect, DetectionContext, Disposition, FailureClass};
use serde::Serialize;
use serde_json::{Map, Value};

/// One text the user handed in: a prompt, a model reply, or an agent's JSON output.
#[derive(Debug, Clone)]
pub struct Text {
    /// The name shown in reports (usually the file path, `-` for stdin).
    pub name: String,
    pub body: String,
}

/// How an output was read.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Shape {
    /// The whole text is JSON: checked field by field.
    Json,
    /// Checked line by line; any ```json fenced blocks are checked as JSON.
    Text,
}

/// An output, parsed once.
#[derive(Debug, Clone)]
pub struct Doc {
    pub name: String,
    pub shape: Shape,
    /// JSON input as is; text as `{"lines": [...], "blocks": [...]}`.
    pub value: Value,
    /// 1-based line of each fenced JSON block's opening fence.
    pub block_lines: Vec<usize>,
    /// Problems found while reading, such as JSON that does not parse.
    pub notes: Vec<Finding>,
}

/// Why an output could not be read at all.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TooComplex {
    pub name: String,
    pub values: usize,
}

/// More JSON values than this are refused: the detectors are not linear in them.
pub const MAX_JSON_VALUES: usize = 20_000;

/// Everything one `pfp check` run looks at.
#[derive(Debug, Clone, Default)]
pub struct Input {
    pub prompt: Option<Text>,
    pub outputs: Vec<Doc>,
}

/// How strongly a finding should stop a pipeline. A routing hint, not a verdict.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Severity {
    Finding,
    Hold,
    Refuse,
}

/// What a check found, and where.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Finding {
    /// The text the evidence sits in.
    pub source: String,
    /// 1-based line, when the evidence has one.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub line: Option<usize>,
    /// JSON pointer, when the evidence sits in JSON.
    #[serde(skip_serializing_if = "String::is_empty")]
    pub pointer: String,
    pub code: String,
    pub severity: Severity,
    pub message: String,
}

/// A deterministic detector. Same input, same findings, every time, on every platform.
pub trait Check {
    /// The codes this check can emit.
    fn codes(&self) -> Vec<&'static str>;
    fn run(&self, input: &Input) -> Vec<Finding>;
}

/// The checks `pfp check` runs, in order.
pub fn builtin_checks() -> Vec<Box<dyn Check>> {
    vec![
        Box::new(Parse),
        Box::new(Pharmacy),
        Box::new(Preload),
        Box::new(RefusalPath),
    ]
}

/// The result of running every check once.
#[derive(Debug, Clone, Serialize)]
pub struct Report {
    pub authority_effect: &'static str,
    pub detectors_run: Vec<&'static str>,
    /// How each output was read.
    pub inputs: Vec<InputShape>,
    pub findings: Vec<Finding>,
}

#[derive(Debug, Clone, Serialize)]
pub struct InputShape {
    pub name: String,
    pub shape: Shape,
}

/// Run `checks` over `input`. Findings come back in a fixed order, without duplicates.
pub fn run_checks(checks: &[Box<dyn Check>], input: &Input) -> Report {
    let mut findings: Vec<Finding> = checks.iter().flat_map(|c| c.run(input)).collect();
    // Per source: strongest first, then by place, so REFUSE lines lead.
    findings.sort_by(|a, b| {
        let key = |f: &Finding| {
            (
                f.source.clone(),
                std::cmp::Reverse(f.severity),
                f.line,
                f.pointer.clone(),
                f.code.clone(),
            )
        };
        key(a).cmp(&key(b)).then_with(|| a.message.cmp(&b.message))
    });
    findings.dedup();
    Report {
        authority_effect: "None",
        detectors_run: checks.iter().flat_map(|c| c.codes()).collect(),
        inputs: input
            .outputs
            .iter()
            .map(|d| InputShape {
                name: d.name.clone(),
                shape: d.shape,
            })
            .collect(),
        findings,
    }
}

/// True when a text is meant to be JSON: it opens an object, or an array of values.
fn looks_like_json(trimmed: &str) -> bool {
    let mut chars = trimmed.chars();
    match chars.next() {
        Some('{') => true,
        Some('[') => chars.find(|c| !c.is_whitespace()).is_some_and(|c| {
            matches!(c, '{' | '[' | '"' | ']' | '-' | '0'..='9' | 't' | 'f' | 'n')
        }),
        _ => false,
    }
}

fn count_values(value: &Value) -> usize {
    1 + match value {
        Value::Array(items) => items.iter().map(count_values).sum(),
        Value::Object(map) => map.values().map(count_values).sum(),
        _ => 0,
    }
}

fn malformed(name: &str, line: Option<usize>, error: &str) -> Finding {
    Finding {
        source: name.to_owned(),
        line,
        pointer: String::new(),
        code: "MALFORMED_JSON".to_owned(),
        severity: Severity::Hold,
        message: format!(
            "JSON that does not parse strictly ({error}); its fields were not checked as JSON"
        ),
    }
}

/// Parse one output. JSON stays JSON; anything else becomes lines, with each
/// ```json fenced block parsed as JSON and blanked from the lines.
pub fn read_doc(text: &Text) -> Result<Doc, TooComplex> {
    let body = text.body.strip_prefix('\u{feff}').unwrap_or(&text.body);
    let name = text.name.clone();
    let trimmed = body.trim();
    let mut doc = if looks_like_json(trimmed) {
        match core_prompt_civilization::decode_candidate_bytes(trimmed.as_bytes()) {
            Ok(value) => Doc {
                name,
                shape: Shape::Json,
                value,
                block_lines: Vec::new(),
                notes: Vec::new(),
            },
            Err(e) => {
                let mut doc = read_lines(name, body);
                doc.notes.push(malformed(&text.name, None, &e.to_string()));
                doc
            }
        }
    } else {
        read_lines(name, body)
    };
    let values = count_values(&doc.value);
    if values > MAX_JSON_VALUES {
        return Err(TooComplex {
            name: text.name.clone(),
            values,
        });
    }
    doc.notes.sort_by_key(|f| f.line);
    Ok(doc)
}

fn read_lines(name: String, body: &str) -> Doc {
    let mut lines = Vec::new();
    let mut blocks = Vec::new();
    let mut block_lines = Vec::new();
    let mut notes = Vec::new();
    let mut fence: Option<(usize, String)> = None;
    for (index, line) in body.lines().enumerate() {
        let marker = line.trim();
        match &mut fence {
            None if marker.eq_ignore_ascii_case("```json") => {
                fence = Some((index + 1, String::new()));
                lines.push(Value::String(String::new()));
            }
            Some((start, json)) if marker == "```" => {
                match core_prompt_civilization::decode_candidate_bytes(json.trim().as_bytes()) {
                    Ok(value) => {
                        blocks.push(value);
                        block_lines.push(*start);
                    }
                    Err(e) => notes.push(malformed(&name, Some(*start), &e.to_string())),
                }
                fence = None;
                lines.push(Value::String(String::new()));
            }
            Some((_, json)) => {
                json.push_str(line);
                json.push('\n');
                lines.push(Value::String(String::new()));
            }
            None => lines.push(Value::String(line.to_owned())),
        }
    }
    // An unclosed fence: give its lines back to the text checks.
    if let Some((start, _)) = fence {
        for (index, line) in body.lines().enumerate().skip(start - 1) {
            lines[index] = Value::String(line.to_owned());
        }
    }
    let mut map = Map::new();
    map.insert("lines".to_owned(), Value::Array(lines));
    if !blocks.is_empty() {
        map.insert("blocks".to_owned(), Value::Array(blocks));
    }
    Doc {
        name,
        shape: Shape::Text,
        value: Value::Object(map),
        block_lines,
        notes,
    }
}

/// Reports what [`read_doc`] noticed, such as malformed JSON.
pub struct Parse;

impl Check for Parse {
    fn codes(&self) -> Vec<&'static str> {
        vec!["MALFORMED_JSON"]
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        input.outputs.iter().flat_map(|d| d.notes.clone()).collect()
    }
}

/// Map a pharmacy locus to a line and pointer in the user's file.
fn locate(doc: &Doc, locus: &str) -> (Option<usize>, String) {
    if doc.shape == Shape::Json {
        return (None, locus.to_owned());
    }
    if let Some(index) = locus
        .strip_prefix("/lines/")
        .and_then(|n| n.parse::<usize>().ok())
    {
        return (Some(index + 1), String::new());
    }
    if let Some(rest) = locus.strip_prefix("/blocks/") {
        let (index, pointer) = rest.split_once('/').unwrap_or((rest, ""));
        if let Some(line) = index
            .parse::<usize>()
            .ok()
            .and_then(|i| doc.block_lines.get(i))
        {
            return (Some(*line), format!("/{pointer}"));
        }
    }
    (None, locus.to_owned())
}

/// The anti-skill pharmacy from `core_prompt_civilization`, run on each output.
/// Only classes that can fire without scheduler context are listed.
pub struct Pharmacy;

const PHARMACY_CLASSES: [FailureClass; 10] = [
    FailureClass::SelfCertification,
    FailureClass::FakeReceipt,
    FailureClass::PersonaAuthorityLeak,
    FailureClass::SchemaSemanticLaundering,
    FailureClass::DetectRepairCoupling,
    FailureClass::PrivateCotDependency,
    FailureClass::OptimalityHallucination,
    FailureClass::ComplexityHallucination,
    FailureClass::TheoremNameLaundering,
    FailureClass::VersionDuplication,
];

/// True when `word` occurs in `text` with no letter or digit right before it
/// (and, when `whole`, none right after). Keeps "suboptimal" and "info(n" out.
fn has_word(text: &str, word: &str, whole: bool) -> bool {
    text.match_indices(word).any(|(at, _)| {
        let before = text[..at].chars().next_back();
        let after = text[at + word.len()..].chars().next();
        !before.is_some_and(char::is_alphanumeric)
            && !(whole && after.is_some_and(char::is_alphanumeric))
    })
}

const SUPERLATIVES: [&str; 6] = [
    "optimal",
    "minimal",
    "fastest",
    "smallest",
    "maximal",
    "best possible",
];
const COMPLEXITY: [&str; 5] = [
    "o(n",
    "o(1)",
    "polynomial time",
    "linear time",
    "constant time",
];

/// The pharmacy matches substrings; keep its word findings only on whole words.
fn confirmed(class: FailureClass, doc: &Doc, locus: &str) -> bool {
    let Some(text) = doc.value.pointer(locus).and_then(Value::as_str) else {
        return true;
    };
    let lower = text.to_ascii_lowercase();
    match class {
        FailureClass::OptimalityHallucination => {
            SUPERLATIVES.iter().any(|w| has_word(&lower, w, true))
        }
        FailureClass::ComplexityHallucination => {
            COMPLEXITY.iter().any(|w| has_word(&lower, w, false))
        }
        _ => true,
    }
}

fn severity_of(disposition: Disposition) -> Severity {
    match disposition {
        Disposition::Finding => Severity::Finding,
        Disposition::Hold => Severity::Hold,
        Disposition::Refuse => Severity::Refuse,
    }
}

impl Check for Pharmacy {
    fn codes(&self) -> Vec<&'static str> {
        PHARMACY_CLASSES.iter().map(|c| c.code()).collect()
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        let mut context = DetectionContext::default();
        let mut findings = Vec::new();
        for doc in &input.outputs {
            for f in detect(&doc.value, &context).findings {
                if !PHARMACY_CLASSES.contains(&f.class) || !confirmed(f.class, doc, &f.locus) {
                    continue;
                }
                let (line, pointer) = locate(doc, &f.locus);
                findings.push(Finding {
                    source: doc.name.clone(),
                    line,
                    pointer,
                    code: f.class.code().to_owned(),
                    severity: severity_of(f.disposition),
                    message: f.detail,
                });
            }
            // Later outputs are compared with earlier ones for relabelled duplicates.
            context
                .seen_semantic_digests
                .push(semantic_payload_digest(&doc.value));
        }
        findings
    }
}

/// Lower-case the prompt and straighten curly apostrophes.
fn normalize(prompt: &str) -> String {
    prompt.to_lowercase().replace('\u{2019}', "'")
}

/// The prompt states the verdict it asks for.
pub struct Preload;

const PRELOAD_PHRASES: [&str; 10] = [
    "conclude that it",
    "conclude that this",
    "confirm that it is",
    "confirm that this is",
    "confirm that it's",
    "confirm that it passes",
    "confirm that it works",
    "state that it is",
    "the answer must be",
    "the answer is yes",
];

impl Check for Preload {
    fn codes(&self) -> Vec<&'static str> {
        vec!["CONCLUSION_PRELOAD"]
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        let Some(prompt) = &input.prompt else {
            return Vec::new();
        };
        normalize(&prompt.body)
            .lines()
            .enumerate()
            .filter_map(|(index, line)| {
                let phrase = PRELOAD_PHRASES.iter().find(|p| has_word(line, p, false))?;
                Some(Finding {
                    source: prompt.name.clone(),
                    line: Some(index + 1),
                    pointer: String::new(),
                    code: "CONCLUSION_PRELOAD".to_owned(),
                    severity: Severity::Finding,
                    message: format!("the prompt states the verdict it asks for ({phrase:?})"),
                })
            })
            .collect()
    }
}

/// PFP law 4, "refuse with a type": a prompt should say what to do when the
/// task cannot be done, or the model will guess. Runs only when a prompt is given.
pub struct RefusalPath;

/// A clause gives a way out when it is conditional and names a blocker.
const CONDITIONS: [&str; 3] = ["if", "unless", "when"];
const BLOCKERS: [&str; 18] = [
    "cannot",
    "can't",
    "can not",
    "unable",
    "unsure",
    "not sure",
    "don't know",
    "do not know",
    "not enough",
    "insufficient",
    "missing",
    "not possible",
    "impossible",
    "unclear",
    "ambiguous",
    "not contain",
    "doesn't contain",
    "no answer",
];

fn gives_a_way_out(clause: &str) -> bool {
    let explicit = clause.contains("say you don't know") || clause.contains("say \"i don't know\"");
    let conditional = CONDITIONS.iter().any(|c| has_word(clause, c, true));
    explicit || (conditional && BLOCKERS.iter().any(|b| clause.contains(b)))
}

impl Check for RefusalPath {
    fn codes(&self) -> Vec<&'static str> {
        vec!["NO_REFUSAL_PATH"]
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        let Some(prompt) = &input.prompt else {
            return Vec::new();
        };
        let text = normalize(&prompt.body);
        if text.split(['.', '\n', '!', '?', ';']).any(gives_a_way_out) {
            return Vec::new();
        }
        vec![Finding {
            source: prompt.name.clone(),
            line: None,
            pointer: String::new(),
            code: "NO_REFUSAL_PATH".to_owned(),
            severity: Severity::Finding,
            message: "the prompt never says what to do when the task cannot be done".to_owned(),
        }]
    }
}

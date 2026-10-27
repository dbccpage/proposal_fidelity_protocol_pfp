//! Checks: deterministic detectors over a prompt and the texts produced from it.
//!
//! AuthorityEffect: None. A check names what it found and nothing else: there is
//! no field for a repair, and an empty result is not a proof that a text is right.
//!
//! To add a check, implement [`Check`] and list it in [`builtin_checks`]; give
//! each new code an entry in [`crate::catalog`] so `pfp explain` can teach it.

use core_prompt_civilization::{detect, DetectionContext, Disposition};
use serde::Serialize;
use serde_json::Value;

/// One text the user handed in: a prompt, a model reply, or an agent's JSON output.
#[derive(Debug, Clone)]
pub struct Text {
    /// The name shown in reports (usually the file path, `-` for stdin).
    pub name: String,
    pub body: String,
}

/// How a text was read. JSON is checked field by field; anything else line by line.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Shape {
    Json,
    Text,
}

/// Everything one `pfp check` run looks at.
#[derive(Debug, Clone, Default)]
pub struct Input {
    pub prompt: Option<Text>,
    pub outputs: Vec<Text>,
}

/// How strongly a finding should stop a pipeline. A routing hint, not a verdict.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Severity {
    Finding,
    Hold,
    Refuse,
}

impl Severity {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Finding => "FINDING",
            Self::Hold => "HOLD",
            Self::Refuse => "REFUSE",
        }
    }
}

/// What a check found, and where.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub struct Finding {
    /// The text the evidence sits in.
    pub source: String,
    /// 1-based line for text input; absent for JSON input and whole-text findings.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub line: Option<usize>,
    /// JSON pointer for JSON input; empty otherwise.
    #[serde(skip_serializing_if = "String::is_empty")]
    pub pointer: String,
    pub code: String,
    pub severity: Severity,
    pub message: String,
}

/// A deterministic detector. Same input, same findings, every time, on every platform.
pub trait Check {
    /// The codes this check can emit, in the order `pfp explain` lists them.
    fn codes(&self) -> &'static [&'static str];
    fn run(&self, input: &Input) -> Vec<Finding>;
}

/// The checks `pfp check` runs, in order.
pub fn builtin_checks() -> Vec<Box<dyn Check>> {
    vec![Box::new(Pharmacy), Box::new(RefusalPath)]
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
        (
            &a.source,
            std::cmp::Reverse(a.severity),
            a.line,
            &a.pointer,
            &a.code,
            &a.message,
        )
            .cmp(&(
                &b.source,
                std::cmp::Reverse(b.severity),
                b.line,
                &b.pointer,
                &b.code,
                &b.message,
            ))
    });
    findings.dedup();
    let inputs = input
        .outputs
        .iter()
        .map(|t| InputShape {
            name: t.name.clone(),
            shape: read_shape(&t.body).1,
        })
        .collect();
    Report {
        authority_effect: "None",
        detectors_run: checks
            .iter()
            .flat_map(|c| c.codes().iter().copied())
            .collect(),
        inputs,
        findings,
    }
}

/// Read a text as JSON when it is a JSON object or array, else as lines.
///
/// Text becomes `{"lines": [...]}` so the detectors see one string per line and
/// every finding maps back to a line number.
pub fn read_shape(body: &str) -> (Value, Shape) {
    let trimmed = body.trim_start();
    if trimmed.starts_with('{') || trimmed.starts_with('[') {
        if let Ok(value) = core_prompt_civilization::decode_candidate_bytes(trimmed.as_bytes()) {
            return (value, Shape::Json);
        }
    }
    let lines = body.lines().map(|l| Value::String(l.to_owned())).collect();
    let mut map = serde_json::Map::new();
    map.insert("lines".to_owned(), Value::Array(lines));
    (Value::Object(map), Shape::Text)
}

fn severity_of(disposition: Disposition) -> Severity {
    match disposition {
        Disposition::Finding => Severity::Finding,
        Disposition::Hold => Severity::Hold,
        Disposition::Refuse => Severity::Refuse,
    }
}

/// `/lines/7` -> line 8. Any other pointer stays a pointer.
fn locate(shape: Shape, pointer: &str) -> (Option<usize>, String) {
    if shape == Shape::Text {
        if let Some(index) = pointer
            .strip_prefix("/lines/")
            .and_then(|n| n.parse::<usize>().ok())
        {
            return (Some(index + 1), String::new());
        }
    }
    (None, pointer.to_owned())
}

/// The anti-skill pharmacy from `core_prompt_civilization`: twelve failure
/// classes with a mechanical test, run on each output, with the prompt as context.
pub struct Pharmacy;

const PHARMACY_CODES: [&str; 12] = [
    "SELF_CERTIFICATION",
    "FAKE_RECEIPT",
    "CONCLUSION_PRELOAD",
    "SCHEMA_SEMANTIC_LAUNDERING",
    "THEOREM_NAME_LAUNDERING",
    "OPTIMALITY_HALLUCINATION",
    "COMPLEXITY_HALLUCINATION",
    "BRANCH_DROP_EXHAUSTION",
    "PERSONA_AUTHORITY_LEAK",
    "PRIVATE_COT_DEPENDENCY",
    "VERSION_DUPLICATION",
    "DETECT_REPAIR_COUPLING",
];

impl Check for Pharmacy {
    fn codes(&self) -> &'static [&'static str] {
        &PHARMACY_CODES
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        let context = DetectionContext {
            prompt: input.prompt.as_ref().map(|p| p.body.clone()),
            ..DetectionContext::default()
        };
        // With no outputs, an empty candidate still lets the prompt-only detectors run.
        let empty = Text {
            name: String::new(),
            body: "{}".to_owned(),
        };
        let outputs: Vec<&Text> = if input.outputs.is_empty() {
            vec![&empty]
        } else {
            input.outputs.iter().collect()
        };
        let mut findings = Vec::new();
        for output in outputs {
            let (candidate, shape) = read_shape(&output.body);
            for f in detect(&candidate, &context).findings {
                // `/prompt` evidence belongs to the prompt file, not the output.
                let (source, line, pointer) = match (&input.prompt, f.locus.as_str()) {
                    (Some(prompt), "/prompt") => (prompt.name.clone(), None, String::new()),
                    _ => {
                        let (line, pointer) = locate(shape, &f.locus);
                        (output.name.clone(), line, pointer)
                    }
                };
                findings.push(Finding {
                    source,
                    line,
                    pointer,
                    code: f.class.code().to_owned(),
                    severity: severity_of(f.disposition),
                    message: f.detail,
                });
            }
        }
        findings
    }
}

/// PFP law 4, "refuse with a type": a prompt should say what to do when the
/// task cannot be done, or the model will guess. Runs only when a prompt is given.
pub struct RefusalPath;

/// Lower-case phrases that give the model a way out. Matching any one passes.
const REFUSAL_MARKERS: [&str; 20] = [
    "if you cannot",
    "if you can't",
    "if you can not",
    "if unsure",
    "if you are unsure",
    "if you're unsure",
    "if you don't know",
    "if you do not know",
    "if the answer is not",
    "say you don't know",
    "say that you don't know",
    "enough information",
    "enough context",
    "enough data",
    "cannot answer",
    "can't answer",
    "unable to",
    "cannot be determined",
    "refuse",
    "decline",
];

impl Check for RefusalPath {
    fn codes(&self) -> &'static [&'static str] {
        &["NO_REFUSAL_PATH"]
    }

    fn run(&self, input: &Input) -> Vec<Finding> {
        let Some(prompt) = &input.prompt else {
            return Vec::new();
        };
        let lower = prompt.body.to_lowercase().replace('\u{2019}', "'");
        if REFUSAL_MARKERS.iter().any(|m| lower.contains(m)) {
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

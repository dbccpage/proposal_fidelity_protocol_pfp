//! The teaching catalog: what each code means, why it matters, what to do, and
//! where to read more. `pfp explain CODE` prints one entry.
//!
//! AuthorityEffect: None.

pub struct Entry {
    pub code: &'static str,
    /// One short line for terminal reports.
    pub short: &'static str,
    pub what: &'static str,
    pub why: &'static str,
    pub instead: &'static str,
    pub wiki: &'static str,
}

const WIKI: &str = "https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/";

pub fn wiki_url(page: &str) -> String {
    format!("{WIKI}{page}")
}

pub const ENTRIES: &[Entry] = &[
    Entry {
        code: "SELF_CERTIFICATION",
        short: "the model certifies its own work",
        what: "The output fills a field only the host may fill (verified, admitted, receipt, ...), or a line is just \"verified\".",
        why: "A model cannot certify its own work. Downstream code that trusts `verified: true` from a model trusts a guess.",
        instead: "Let your code set verification fields after it checks. Ask the model for evidence, not a verdict.",
        wiki: "EIS",
    },
    Entry {
        code: "FAKE_RECEIPT",
        short: "a digest the model made up",
        what: "A host-only field holds a 64-hex-digit value that looks like a SHA-256 digest.",
        why: "Models produce digest-shaped strings that were never computed. They pass a glance and fail any check.",
        instead: "Compute digests in code. Never accept one from model output.",
        wiki: "EIS",
    },
    Entry {
        code: "CONCLUSION_PRELOAD",
        short: "the prompt states the verdict it asks for",
        what: "The prompt tells the model the outcome (\"confirm that it passes\", \"conclude that it is safe\", \"the answer must be ...\").",
        why: "A prompt that states the conclusion gets the conclusion back, whatever the evidence says.",
        instead: "Ask whether it holds and what evidence decides it. Allow \"no\" as an answer.",
        wiki: "Rewriting",
    },
    Entry {
        code: "SCHEMA_SEMANTIC_LAUNDERING",
        short: "unchecked changes presented as done",
        what: "The output proposes changes (`proposed_claim_deltas`) that no replay has checked.",
        why: "Well-formed JSON is not a checked result. Valid syntax can stand in for work that never happened.",
        instead: "Replay or test the proposed change before acting on it; until then treat it as parsed, not checked.",
        wiki: "Rewriting-PFP",
    },
    Entry {
        code: "THEOREM_NAME_LAUNDERING",
        short: "a theorem named, its assumptions not stated",
        what: "A line says \"by ... theorem\" without stating any assumption.",
        why: "Naming a theorem is not applying it. Its conditions may not hold here.",
        instead: "State the theorem's assumptions and show they hold, or drop the appeal.",
        wiki: "Rewriting",
    },
    Entry {
        code: "OPTIMALITY_HALLUCINATION",
        short: "\"optimal\" with no objective or bound",
        what: "A superlative (optimal, minimal, fastest, best possible, ...) with no stated objective or bound.",
        why: "\"Optimal\" is a claim about every alternative. Without a class and a bound it is unsupported.",
        instead: "Say what was compared, by which measure, and what bound shows nothing better exists.",
        wiki: "Rewriting",
    },
    Entry {
        code: "COMPLEXITY_HALLUCINATION",
        short: "a complexity claim with no basis",
        what: "A complexity claim (O(n), linear time, ...) with no algorithm, cost model or measurement.",
        why: "Complexity claims are easy to state and often wrong.",
        instead: "Name the algorithm and cost model, or measure.",
        wiki: "Rewriting",
    },
    Entry {
        code: "PERSONA_AUTHORITY_LEAK",
        short: "a role field claims authority",
        what: "A persona, role or actor field claims authority (admin, executive, authorize, ...), in any of several languages.",
        why: "A role name in a prompt grants no permission. Code that reads it as one can be talked into anything.",
        instead: "Keep permissions in code. Never derive them from model-written role fields.",
        wiki: "EIS",
    },
    Entry {
        code: "PRIVATE_COT_DEPENDENCY",
        short: "leans on reasoning nobody can see",
        what: "The output leans on hidden reasoning (<think>, \"my internal reasoning\", ...).",
        why: "A conclusion that rests on reasoning nobody can see cannot be checked.",
        instead: "Ask for the evidence and steps in the answer itself.",
        wiki: "Rewriting",
    },
    Entry {
        code: "VERSION_DUPLICATION",
        short: "the same payload under a new label",
        what: "The same payload appears again under another version label.",
        why: "A relabelled duplicate looks like progress and is not.",
        instead: "Keep one copy; change the content, not the label.",
        wiki: "PCIV",
    },
    Entry {
        code: "DETECT_REPAIR_COUPLING",
        short: "a finding and its fix in one artifact",
        what: "One output both reports problems (`objections`) and applies fixes (`proposed_claim_deltas`).",
        why: "A detector that also repairs can hide its own mistakes. Detection and repair must be reviewed separately.",
        instead: "Split the finding and the fix into two artifacts.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
    Entry {
        code: "NO_REFUSAL_PATH",
        short: "no instruction for when the task can't be done",
        what: "The prompt never says what to do when the task cannot be done.",
        why: "With no way out, a model guesses. PFP law 4: refuse with a type, leave the state unchanged.",
        instead: "Add a line like: \"If you cannot answer from the given material, reply exactly: CANNOT_ANSWER: <reason>.\"",
        wiki: "Rewriting",
    },
    Entry {
        code: "MALFORMED_JSON",
        short: "JSON that does not parse strictly",
        what: "The output looks like JSON (or has a ```json block) but does not parse strictly: a syntax error, a trailing comma, or a duplicate key.",
        why: "Lenient parsers disagree about such JSON, so two programs can read different values from it. Its fields were checked as plain text only.",
        instead: "Make the model emit strict JSON (structured output or a schema), and parse it strictly before use.",
        wiki: "EIS",
    },
    Entry {
        code: "DIGEST_MISMATCH",
        short: "the file changed since it was sealed",
        what: "A sealed file's bytes changed after sealing.",
        why: "The packet no longer describes what is on disk.",
        instead: "Restore the sealed bytes, or seal again and say why it changed.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
    Entry {
        code: "FILE_MISSING",
        short: "a sealed file is missing",
        what: "A file named in the packet is not there.",
        why: "Nothing can be replayed against a missing file.",
        instead: "Run replay from the folder you sealed in, or pass --root.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
    Entry {
        code: "ENVELOPE_TAMPERED",
        short: "the packet was edited after sealing",
        what: "The envelope does not match its own hashes.",
        why: "Someone edited the packet after sealing. The hashes catch naive edits; they are not a signature.",
        instead: "Get the original packet from its author.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
    Entry {
        code: "UNSUPPORTED_FORMAT",
        short: "not a pfp packet",
        what: "The file is not a pfp.packet.v1 envelope.",
        why: "Unknown fields and formats are refused rather than guessed at.",
        instead: "Pass the JSON that `pfp seal` printed.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
    Entry {
        code: "PATH_OUTSIDE_ROOT",
        short: "a path outside the folder",
        what: "A path is absolute, has a drive letter, or climbs out with `..`.",
        why: "Packets only name files below the folder they were sealed in, so replay never reads elsewhere.",
        instead: "Use relative paths below the current folder.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
    Entry {
        code: "DUPLICATE_PATH",
        short: "a file named twice",
        what: "The same file was named twice.",
        why: "Each file is sealed once.",
        instead: "Name each file once.",
        wiki: "Operads-Rewriting-and-Packetization",
    },
];

/// Look up a code, ignoring case and `-` versus `_`.
pub fn find(code: &str) -> Option<&'static Entry> {
    let wanted = code.trim().to_ascii_uppercase().replace('-', "_");
    ENTRIES.iter().find(|e| e.code == wanted)
}

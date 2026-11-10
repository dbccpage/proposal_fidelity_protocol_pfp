# Prompt Sieve: Seed Ingestion & Forge Organization

**AuthorityEffect**: None.  
**Module Reference:** `code/rust/core_prompt_civilization/src/forge.rs`  
**Schema Identifier:** `core.forge.organize-prompt.v1`  
**Status:** Implemented in Rust sovereign engine  

---

## 1. Executive Summary & Purpose

In the Proposal Fidelity Protocol (PFP) and Prompt Sieve architecture, raw, unvetted prompts cannot be injected directly into evaluation harnesses or model pipelines. When an external prompt arrives as stimulus, it enters the **Forge Organization Pipeline** (`organize_prompt` in `code/rust/core_prompt_civilization/src/forge.rs`).

The forge organization stage performs five concrete operations:
1. Validates strict transport-level payload size against a hard 1 MiB ceiling (`MAX_ORGANIZE_BYTES = 1_048_576`).
2. Isolates the raw text as an immutable protected byte slice labeled `original_seed` (`start_byte: 0, end_byte: seed.len()`).
3. Appends declared auxiliary sections (`task`, `constraints`, `acceptance criteria`, `response contract`) wrapped in explicit boundary markers `[FORGE DECLARED <SECTION>]`.
4. Enforces invariant `PROTECTED_SPAN_MUTATION_REFUSED` via `PromptMutationEngineV1::apply_mutation`, rejecting any mutation or zero-width insertion overlapping declared spans.
5. Emits content-addressed cryptographic SHA-256 digests (`request_sha256`, `seed_sha256`, `organized_sha256`) with `authority_effect: "None"`, conveying zero task acceptance or sovereign license.

---

## 2. Ingestion Execution Trace

When an untrusted payload reaches `organize_prompt(payload: &Value)`, execution follows the deterministic path below:

```
Untrusted Payload (&Value)
           │
           ▼
[extract_organize_request_bytes] ──► Checks length <= 1,048,576 bytes
           │                          (Refusal: FORGE_LIMIT_EXCEEDED)
           ▼
[serde_json::from_slice] ─────────► Deserializes into OrganizePromptInput
           │                          (Refusal: FORGE_INPUT_INVALID)
           ▼
[Byte Buffer Initialization] ─────► output = input.seed.as_bytes().to_vec()
           │                          ProtectedSpanV1 {"original_seed", 0, len}
           ▼
[append_declared_fields] ─────────► Appends sections with PromptMutationEngineV1
           │                          - [FORGE DECLARED TASK]
           │                          - [FORGE DECLARED CONSTRAINTS]
           │                          - [FORGE DECLARED ACCEPTANCE CRITERIA]
           │                          - [FORGE DECLARED RESPONSE CONTRACT]
           ▼
[Cryptographic Digest Calculation] ─► SHA-256(request), SHA-256(seed), SHA-256(output)
           │
           ▼
Emits Result JSON ────────────────► {"schema_version": "core.forge.organize-prompt.v1",
                                     "status": "ORGANIZED",
                                     "authority_effect": "None", ...}
```

### 2.1 The Payload Extraction Seam

In `code/rust/core_prompt_civilization/src/forge.rs` (lines 76–102), the helper `extract_organize_request_bytes` handles incoming payloads:

```rust
const MAX_ORGANIZE_BYTES: usize = 1_048_576; // 1 MiB hard ceiling

fn extract_organize_request_bytes(payload: &Value) -> Result<Vec<u8>, String> {
    let mut fields = payload.clone();
    if fields.get("operation") == Some(&json!("forge_organize_prompt")) {
        fields
            .as_object_mut()
            .ok_or("FORGE_INPUT_INVALID: object required")?
            .remove("operation");
    }
    let request = if fields.get("request_json").is_some() {
        if fields.as_object().is_none_or(|fields| fields.len() != 1) {
            return Err(
                "FORGE_INPUT_INVALID: request_json cannot be mixed with other fields".into(),
            );
        }
        fields["request_json"]
            .as_str()
            .ok_or("FORGE_INPUT_INVALID: request_json must be text")?
            .as_bytes()
            .to_vec()
    } else {
        serde_json::to_vec(&fields).map_err(|e| format!("FORGE_INPUT_INVALID: {e}"))?
    };
    if request.len() > MAX_ORGANIZE_BYTES {
        return Err("FORGE_LIMIT_EXCEEDED: request exceeds one MiB".into());
    }
    Ok(request)
}
```

**Key Invariants Enforced:**
- **Exact transport serialization:** If `request_json` text is supplied, the raw byte representation (including whitespace and numeric format) is preserved directly to ensure exact SHA-256 hash reproducibility.
- **Single-field exclusivity:** `request_json` cannot be combined with loose dictionary keys (`FORGE_INPUT_INVALID`).
- **Hard size cap:** Requests strictly exceeding $1,048,576$ bytes ($1\text{ MiB}$) fail closed with `FORGE_LIMIT_EXCEEDED`.

---

## 3. Data Structures & Schemas

### 3.1 Input Structure: `OrganizePromptInput`

Defined in `forge.rs` (lines 60–72):

```rust
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct OrganizePromptInput {
    seed: String,
    #[serde(default)]
    task: String,
    #[serde(default)]
    constraints: Vec<String>,
    #[serde(default)]
    acceptance: Vec<String>,
    #[serde(default)]
    response_contract: Option<Value>,
}
```

Unknown fields are rejected at parse time (`#[serde(deny_unknown_fields)]`), preventing parameter injection or unvetted configuration leakage.

### 3.2 Protected Span Marker: `ProtectedSpanV1`

Defined in `code/rust/core_prompt_civilization/src/record.rs` and consumed in `forge.rs`:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProtectedSpanV1 {
    pub name: String,
    pub start_byte: usize,
    pub end_byte: usize,
}
```

The protected span records a half-open byte interval `[start_byte, end_byte)` on the output buffer. The initial span is generated from the raw seed:
- `name: "original_seed"`
- `start_byte: 0`
- `end_byte: input.seed.len()`

---

## 4. Declared Section Formatting

Sections are appended through `append_declared_fields` (lines 138–156):

```rust
fn append_declared_fields(
    input: &OrganizePromptInput,
    output: &mut Vec<u8>,
    spans: &mut Vec<ProtectedSpanV1>,
) -> Result<(), String> {
    append_organized_section(output, spans, "task", &input.task)?;
    if !input.constraints.is_empty() {
        append_serialized_section(output, spans, "constraints", &input.constraints)?;
    }
    if !input.acceptance.is_empty() {
        append_serialized_section(output, spans, "acceptance criteria", &input.acceptance)?;
    }
    if let Some(ref contract) = input.response_contract {
        append_serialized_section(output, spans, "response contract", contract)?;
    }
    Ok(())
}
```

Each non-empty section is formatted as:
```
\n\n[FORGE DECLARED <NAME_IN_UPPERCASE>]\n<TEXT>
```

Where:
- `task` produces `\n\n[FORGE DECLARED TASK]\n<task_text>`
- `constraints` serializes JSON arrays: `\n\n[FORGE DECLARED CONSTRAINTS]\n["constraint 1", ...]`
- `acceptance criteria` serializes JSON arrays: `\n\n[FORGE DECLARED ACCEPTANCE CRITERIA]\n["criterion 1", ...]`
- `response contract` serializes JSON objects: `\n\n[FORGE DECLARED RESPONSE CONTRACT]\n{"type": "object", ...}`

**Section Serialization Rule:** Constraints, acceptance criteria, and response contracts are serialized via `serde_json::to_string` rather than loose string joining. This retains exact newline characters and string boundaries, preventing Markdown instruction injection attacks.

Each appended section adds a corresponding `ProtectedSpanV1` covering its byte offsets `[start, output.len())`, rendering the declared sections immutable.

---

## 5. Protected Span Mutation Refusal: Invariant `F-BIO-03`

The core invariant governing seed preservation is implemented in `PromptMutationEngineV1::apply_mutation` (`forge.rs`, lines 21–58):

```rust
impl PromptMutationEngineV1 {
    pub fn apply_mutation(
        original_bytes: &[u8],
        protected_spans: &[ProtectedSpanV1],
        edit_start: usize,
        edit_end: usize,
        replacement: &[u8],
    ) -> Result<Vec<u8>, String> {
        if edit_start > edit_end || edit_end > original_bytes.len() {
            return Err("INDEX_OUT_OF_BOUNDS: Edit boundaries invalid".to_string());
        }

        // Check if edit touches any protected span
        for span in protected_spans {
            // Overlapping non-empty interval
            if edit_start < edit_end {
                let overlap_start = max(edit_start, span.start_byte);
                let overlap_end = min(edit_end, span.end_byte);
                if overlap_start < overlap_end {
                    return Err(
                        "PROTECTED_SPAN_MUTATION_REFUSED: Edit overlaps protected span".to_string(),
                    );
                }
            } else {
                // Zero-width insertion strictly inside span
                if span.start_byte < edit_start && edit_start < span.end_byte {
                    return Err(
                        "PROTECTED_SPAN_MUTATION_REFUSED: Zero-width insertion inside protected span"
                            .to_string(),
                    );
                }
            }
        }

        let mut result = Vec::with_capacity(original_bytes.len() + replacement.len());
        result.extend_from_slice(&original_bytes[..edit_start]);
        result.extend_from_slice(replacement);
        result.extend_from_slice(&original_bytes[edit_end..]);

        Ok(result)
    }
}
```

### 5.1 Guard Conditions

The function checks two distinct collision modes:
1. **Interval Overlap ($edit\_start < edit\_end$):**
   $$\max(edit\_start, span.start\_byte) < \min(edit\_end, span.end\_byte)$$
   If true, the edit region overlaps the protected span. Execution halts immediately with:
   `PROTECTED_SPAN_MUTATION_REFUSED: Edit overlaps protected span`.
2. **Zero-Width Injection ($edit\_start == edit\_end$):**
   $$span.start\_byte < edit\_start < span.end\_byte$$
   If an insertion occurs strictly within the interior of a protected span, execution halts with:
   `PROTECTED_SPAN_MUTATION_REFUSED: Zero-width insertion inside protected span`.
   (Note: Insertions at exact boundaries $edit\_start == span.start\_byte$ or $edit\_start == span.end\_byte$ do not pierce the interior and are permitted as adjacent additions).

---

## 6. Output Schema & Verification Protocol

### 6.1 Output Format (`core.forge.organize-prompt.v1`)

Upon successful organization, `organize_prompt` emits:

```json
{
  "schema_version": "core.forge.organize-prompt.v1",
  "operation_id": "forge.organize-prompt.v1",
  "status": "ORGANIZED",
  "request_sha256": "3a5f...",
  "seed_sha256": "7c1b...",
  "organized_sha256": "9e2d...",
  "organized_text": "Do not change alpha.\n\n[FORGE DECLARED TASK]\n...",
  "protected_spans": [
    {
      "name": "original_seed",
      "start_byte": 0,
      "end_byte": 22
    },
    {
      "name": "task",
      "start_byte": 22,
      "end_byte": 68
    }
  ],
  "source_bytes": 22,
  "rendered_bytes": 68,
  "authority_effect": "None"
}
```

### 6.2 Deterministic Re-verification (`verify_organization`)

To audit an existing prompt artifact without creating a new mutation record, the host executes `verify_organization(payload: &Value)` (`forge.rs`, lines 194–224):
- Extracts the original `request` or `request_json`.
- Re-runs `organize_prompt(&request)`.
- Compares every declared output key (`request_sha256`, `seed_sha256`, `organized_sha256`, `organized_text`, `protected_spans`) against the persisted `preparation` dictionary.
- If any byte differs, it emits `FORGE_PREPARATION_MISMATCH: persisted organization differs from declared inputs`.
- If identical, it returns `{"status": "VALID", "operation_id": "forge.organize-prompt.v1", "authority_effect": "None"}`.

---

## 7. Claim Hygiene & Formal Boundaries

### What This Artifact Supports
- Confirms that `organize_prompt` deterministically enforces an immutable protected boundary over `original_seed` and all declared sections in `core_prompt_civilization`.
- Confirms that mutations attempting to overwrite or inject into protected spans are rejected with `PROTECTED_SPAN_MUTATION_REFUSED`.
- Confirms that requests exceeding $1\text{ MiB}$ are rejected with `FORGE_LIMIT_EXCEEDED`.

### What This Artifact Does Not Support
- Does not claim that organizing a prompt checks semantic consistency or model safety.
- Does not grant task success credit, sovereign authority, or execution licenses (`authority_effect: "None"`).
- Does not prevent adversarial instructions inside the seed text itself; it only prevents subsequent mutation operators from tampering with the seed once ingested.

### Narrowest Defensible Claim
The forge pipeline provides an append-only, byte-exact ingress boundary that demarks and protects seed spans from mutation, failing closed when size or span invariants are violated.

### Next Test Needed
A fuzzing suite submitting UTF-8 multibyte boundary split edits against `PromptMutationEngineV1::apply_mutation` to verify character boundary preservation during non-overlapping insertions.
